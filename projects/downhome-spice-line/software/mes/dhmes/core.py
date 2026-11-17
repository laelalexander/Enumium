"""Down Home Creole MES core: recipes, ISA-88 batches, weigh & dispense, QC
release, pack runs, labels, NIST HB 133 checks and lot genealogy.

Standard library only (sqlite3). Every change is written to an append-only
audit table with user and time, which is the electronic batch record.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sqlite3
import statistics
from pathlib import Path

from . import gs1

G_PER_LB = 453.592
SCHEMA = """
CREATE TABLE IF NOT EXISTS ingredient (id TEXT PRIMARY KEY, name TEXT, grp TEXT, density REAL, allergen TEXT);
CREATE TABLE IF NOT EXISTS formula (id TEXT PRIMARY KEY, name TEXT, density REAL, allergens TEXT, minors TEXT, rev INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS formula_line (formula TEXT, ingredient TEXT, pct REAL, PRIMARY KEY (formula, ingredient));
CREATE TABLE IF NOT EXISTS sku (id TEXT PRIMARY KEY, product TEXT, formula TEXT, format TEXT, net_g REAL, container TEXT,
    tare_g REAL, case_count INTEGER, upc TEXT, gtin14 TEXT);
CREATE TABLE IF NOT EXISTS lot (id TEXT PRIMARY KEY, ingredient TEXT, supplier TEXT, supplier_lot TEXT, kg REAL, kg_left REAL,
    received TEXT, expires TEXT, status TEXT, coa TEXT);
CREATE TABLE IF NOT EXISTS batch (id TEXT PRIMARY KEY, formula TEXT, formula_rev INTEGER, target_kg REAL, lot_code TEXT, best_by TEXT,
    status TEXT, created TEXT, cv_pct REAL, micro TEXT, md_rejects INTEGER DEFAULT 0, bag TEXT, bag_kg REAL);
CREATE TABLE IF NOT EXISTS dispense (batch TEXT, ingredient TEXT, lot TEXT, target_kg REAL, actual_kg REAL, scale TEXT, at TEXT, by TEXT);
CREATE TABLE IF NOT EXISTS pack_run (id TEXT PRIMARY KEY, sku TEXT, batch TEXT, line TEXT, units_ordered INTEGER, status TEXT,
    started TEXT, ended TEXT, good INTEGER DEFAULT 0, rej_weight INTEGER DEFAULT 0, rej_vision INTEGER DEFAULT 0, label_ok_by TEXT);
CREATE TABLE IF NOT EXISTS weight_sample (run TEXT, gross_g REAL, at TEXT);
CREATE TABLE IF NOT EXISTS pallet (sscc TEXT PRIMARY KEY, run TEXT, cases INTEGER, at TEXT, shipped_to TEXT);
CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, by TEXT, kind TEXT, ref TEXT, data TEXT);
CREATE TABLE IF NOT EXISTS counter (name TEXT PRIMARY KEY, value INTEGER);
CREATE TABLE IF NOT EXISTS bin (id TEXT PRIMARY KEY, ingredient TEXT, capacity_kg REAL, kg REAL DEFAULT 0, cycle INTEGER DEFAULT 1,
    status TEXT, assigned TEXT, emptied TEXT);
CREATE TABLE IF NOT EXISTS bin_lot (bin TEXT, cycle INTEGER, lot TEXT, kg REAL, at TEXT, by TEXT);
CREATE TABLE IF NOT EXISTS dose (batch TEXT, ingredient TEXT, bin TEXT, cycle INTEGER, target_kg REAL, actual_kg REAL, at TEXT, by TEXT);
"""

# Blender limits (design basis: batch = working volume x bulk density, never above) and how each plant builds a batch.
#   RB-303 : Growth plant, 36 cu ft ribbon blender, hand dispense at WS-201/202, salt by the blender load cells.
#   P1-301 : Phase 1 prototype, 6 cu ft ribbon blender fed by the bin ring and weigh hopper P1-220 (see phase1/out/dosing-plan.md).
BLENDER = {
    "RB-303": {"working_cuft": 36, "min_fill_frac": 0.30, "bins": False, "tol_major": 0.005,
               "routes": {"minor": "WS-203 -> PM-210 premix", "salt": "BB-302 by blender load cells", "major": "WS-201/202 -> BD-301"}},
    "P1-301": {"working_cuft": 6, "min_fill_frac": 0.35, "bins": True, "tol_major": 0.01,
               "routes": {"minor": "P1-202 0.1 g scale -> P1-208 premix", "hand": "P1-201 hand weigh -> P1-302 grate",
                          "bin": "bin -> P1-220 weigh hopper -> P1-224 screw"}},
}
BIN_MIN_DOSE_KG = 4.0      # 2 x 20 g hopper accuracy / 1 % tolerance (dosing-config.json)
BIN_ACCURACY_KG = 0.02
CUFT_L = 28.3168
DISPENSE_TOL = {"major": 0.005, "minor": 0.002}   # fraction of target: majors +/-0.5 %, minors +/-0.2 %
MINOR_PCT = 2.0                                    # site premix rule: under 2 % goes to PM-210 premix
CV_SPEC = 5.0
# NIST HB 133 Table 2-5 MAV for net quantity by weight (selected rows, grams), used for lot acceptance
HB133_MAV = [(36, 3.6), (54, 5.4), (81, 7.2), (117, 9.0), (154, 10.8), (208, 12.6), (263, 14.4), (317, 16.2), (381, 18.0),
             (499, 19.8), (726, 22.4), (1360, 29.0), (2270, 36.3), (4540, 54.4)]


class MESError(Exception):
    pass


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


class MES:
    def __init__(self, path: str | Path = ":memory:", blender: str = "RB-303"):
        if blender not in BLENDER:
            raise MESError(f"unknown blender {blender}")
        self.blender = blender
        self.cfg = BLENDER[blender]
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    # ---------------- helpers ----------------
    def q(self, sql, *a):
        return [dict(r) for r in self.db.execute(sql, a).fetchall()]

    def one(self, sql, *a):
        r = self.db.execute(sql, a).fetchone()
        return dict(r) if r else None

    def audit(self, by, kind, ref, **data):
        self.db.execute("INSERT INTO audit (at, by, kind, ref, data) VALUES (?,?,?,?,?)", (now(), by, kind, ref, json.dumps(data)))
        self.db.commit()

    def next(self, name):
        cur = self.one("SELECT value FROM counter WHERE name=?", name)
        v = (cur["value"] if cur else 0) + 1
        self.db.execute("INSERT OR REPLACE INTO counter VALUES (?,?)", (name, v))
        return v

    # ---------------- master data ----------------
    def load_site(self, site: dict, by="system"):
        """Load ingredients, formulas and SKUs from data/site.json (the client's site extract)."""
        for k, i in site["ingredients"].items():
            self.db.execute("INSERT OR REPLACE INTO ingredient VALUES (?,?,?,?,?)", (k, i["name"], i["group"], i["density"], i.get("allergen", "")))
        for k, f in site["formulas"].items():
            self.db.execute("INSERT OR REPLACE INTO formula (id,name,density,allergens,minors) VALUES (?,?,?,?,?)",
                            (k, f["name"], f["blend_density"], ",".join(f["allergens"]), ",".join(f["minors"])))
            self.db.execute("DELETE FROM formula_line WHERE formula=?", (k,))
            for ing, pct in f["lines"].items():
                self.db.execute("INSERT INTO formula_line VALUES (?,?,?)", (k, ing, pct))
        for n, s in enumerate(site["skus"], 1):
            tare = site["packaging"].get(s["container"], {}).get("tare_g", 0)
            upc = gs1.gtin12(n)
            self.db.execute("INSERT OR REPLACE INTO sku VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (s["id"], s["product"], s["formula"], s["format"], s["net_g"], s["container"], tare, s["case_count"], upc, gs1.gtin14(upc)))
        self.db.commit()
        self.audit(by, "master.load", "site.json", formulas=len(site["formulas"]), skus=len(site["skus"]))

    def formula(self, fid):
        f = self.one("SELECT * FROM formula WHERE id=?", fid)
        if not f:
            raise MESError(f"unknown formula {fid}")
        f["lines"] = self.q("SELECT ingredient, pct FROM formula_line WHERE formula=? ORDER BY pct DESC", fid)
        total = sum(l["pct"] for l in f["lines"])
        if abs(total - 100) > 0.01:
            raise MESError(f"formula {fid} sums to {total:.2f} %, not 100 %")
        return f

    def max_batch_kg(self, fid, blender=None):
        f = self.formula(fid)
        return math.floor(BLENDER[blender or self.blender]["working_cuft"] * CUFT_L * f["density"])

    # ---------------- receiving ----------------
    def receive(self, ingredient, supplier, supplier_lot, kg, expires, coa_ok, by):
        if not self.one("SELECT id FROM ingredient WHERE id=?", ingredient):
            raise MESError(f"unknown ingredient {ingredient}")
        lid = f"RM{dt.date.today():%y%j}-{self.next('rm'):04d}"
        status = "QUARANTINE" if not coa_ok else "RELEASED"
        self.db.execute("INSERT INTO lot VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (lid, ingredient, supplier, supplier_lot, kg, kg, now(), expires, status, "ok" if coa_ok else "pending"))
        self.audit(by, "lot.receive", lid, ingredient=ingredient, kg=kg, status=status)
        return lid

    def release_lot(self, lid, by):
        self.db.execute("UPDATE lot SET status='RELEASED', coa='ok' WHERE id=?", (lid,))
        self.audit(by, "lot.release", lid)

    # ---------------- batches (ISA-88 control recipe) ----------------
    def create_batch(self, fid, target_kg, by, day: dt.date | None = None):
        f = self.formula(fid)
        cap = self.max_batch_kg(fid)
        if target_kg > cap:
            raise MESError(f"{target_kg} kg exceeds {self.blender} working capacity {cap} kg for {fid} (density {f['density']})")
        if target_kg < cap * self.cfg["min_fill_frac"]:
            raise MESError(f"{target_kg} kg is under the {self.blender} minimum fill ({cap * self.cfg['min_fill_frac']:.0f} kg)")
        day = day or dt.date.today()
        n = self.next(f"batch-{day:%y%j}")
        lot = gs1.lot_code(day, n)
        bb = gs1.best_by(day)
        self.db.execute("INSERT INTO batch (id, formula, formula_rev, target_kg, lot_code, best_by, status, created) VALUES (?,?,?,?,?,?,?,?)",
                        (lot, fid, f["rev"], target_kg, lot, bb.isoformat(), "DISPENSING", now()))
        self.audit(by, "batch.create", lot, formula=fid, target_kg=target_kg)
        return lot

    def pick_list(self, bid):
        b = self.batch(bid)
        f = self.formula(b["formula"])
        bins = {r["ingredient"]: r["id"] for r in self.q("SELECT id, ingredient FROM bin WHERE status='ACTIVE'")} if self.cfg["bins"] else {}
        out = []
        for l in f["lines"]:
            kg = b["target_kg"] * l["pct"] / 100
            if l["pct"] < MINOR_PCT:
                kind = "minor"
            elif self.cfg["bins"]:
                kind = "bin" if (l["ingredient"] in bins and kg >= BIN_MIN_DOSE_KG) else "hand"
            else:
                kind = "salt" if l["ingredient"] == "salt" else "major"
            tol = kg * (DISPENSE_TOL["minor"] if kind == "minor" else self.cfg["tol_major"])
            if kind == "bin":
                tol = max(tol, BIN_ACCURACY_KG)
            out.append(dict(ingredient=l["ingredient"], pct=l["pct"], target_kg=round(kg, 3), route=self.cfg["routes"][kind],
                            tol_kg=round(tol, 3), kind=kind, bin=bins.get(l["ingredient"]) if kind == "bin" else None))
        return out

    def dispense(self, bid, ingredient, lot_id, actual_kg, scale, by):
        b = self.batch(bid)
        if b["status"] != "DISPENSING":
            raise MESError(f"batch {bid} is {b['status']}")
        line = next((p for p in self.pick_list(bid) if p["ingredient"] == ingredient), None)
        if not line:
            raise MESError(f"{ingredient} is not in formula {b['formula']}")
        if line["kind"] == "bin":
            raise MESError(f"{ingredient} is dosed from bin {line['bin']}: record it with record_dose, not a hand dispense")
        lot = self.one("SELECT * FROM lot WHERE id=?", lot_id)
        if not lot or lot["ingredient"] != ingredient:
            raise MESError(f"wrong lot: {lot_id} is not {ingredient}")
        if lot["status"] != "RELEASED":
            raise MESError(f"lot {lot_id} is {lot['status']}")
        if lot["expires"] and lot["expires"] < dt.date.today().isoformat():
            raise MESError(f"lot {lot_id} expired {lot['expires']}")
        if lot["kg_left"] < actual_kg:
            raise MESError(f"lot {lot_id} has only {lot['kg_left']} kg")
        if abs(actual_kg - line["target_kg"]) > line["tol_kg"]:
            raise MESError(f"{ingredient} {actual_kg} kg outside {line['target_kg']} +/- {line['tol_kg']} kg")
        self.db.execute("INSERT INTO dispense VALUES (?,?,?,?,?,?,?,?)", (bid, ingredient, lot_id, line["target_kg"], actual_kg, scale, now(), by))
        self.db.execute("UPDATE lot SET kg_left = kg_left - ? WHERE id=?", (actual_kg, lot_id))
        self.audit(by, "dispense", bid, ingredient=ingredient, lot=lot_id, kg=actual_kg, scale=scale)
        self._check_dispensed(bid, by)

    def _check_dispensed(self, bid, by):
        done = {r["ingredient"] for r in self.q("SELECT ingredient FROM dispense WHERE batch=?", bid)}
        if done >= {p["ingredient"] for p in self.pick_list(bid)}:
            self.db.execute("UPDATE batch SET status='READY_TO_BLEND' WHERE id=?", (bid,))
            self.audit(by, "batch.dispensed", bid)

    # ---------------- ingredient bins (Phase 1 dosing station) ----------------
    def assign_bin(self, bin_id, ingredient, capacity_kg, by):
        """Give a bin position to one ingredient. A bin changes ingredient only when it is empty (after a clean)."""
        if not self.one("SELECT id FROM ingredient WHERE id=?", ingredient):
            raise MESError(f"unknown ingredient {ingredient}")
        cur = self.one("SELECT * FROM bin WHERE id=?", bin_id)
        if cur and cur["ingredient"] != ingredient and cur["kg"] > 0:
            raise MESError(f"bin {bin_id} still holds {cur['kg']:.1f} kg of {cur['ingredient']}: run it empty and clean before reassigning")
        other = self.one("SELECT id FROM bin WHERE ingredient=? AND status='ACTIVE' AND id<>?", ingredient, bin_id)
        if other:
            raise MESError(f"{ingredient} already has bin {other['id']}")
        if cur:
            self.db.execute("UPDATE bin SET ingredient=?, capacity_kg=?, status='ACTIVE', assigned=?, cycle=cycle+? WHERE id=?",
                            (ingredient, capacity_kg, now(), 1 if cur["ingredient"] != ingredient else 0, bin_id))
        else:
            self.db.execute("INSERT INTO bin (id, ingredient, capacity_kg, kg, cycle, status, assigned) VALUES (?,?,?,0,1,'ACTIVE',?)",
                            (bin_id, ingredient, capacity_kg, now()))
        self.audit(by, "bin.assign", bin_id, ingredient=ingredient, capacity_kg=capacity_kg)

    def bin(self, bin_id):
        b = self.one("SELECT * FROM bin WHERE id=?", bin_id)
        if not b:
            raise MESError(f"unknown bin {bin_id}")
        b["lots"] = self.q("SELECT lot, SUM(kg) AS kg FROM bin_lot WHERE bin=? AND cycle=? GROUP BY lot ORDER BY MIN(at)", bin_id, b["cycle"])
        return b

    def refill_bin(self, bin_id, lot_id, kg, by):
        """Pour bags of one lot into a bin. The scan of the bag lot is checked against the bin's ingredient."""
        b = self.bin(bin_id)
        if b["status"] != "ACTIVE":
            raise MESError(f"bin {bin_id} is {b['status']}")
        lot = self.one("SELECT * FROM lot WHERE id=?", lot_id)
        if not lot or lot["ingredient"] != b["ingredient"]:
            raise MESError(f"wrong ingredient: lot {lot_id} is not {b['ingredient']} (bin {bin_id})")
        if lot["status"] != "RELEASED":
            raise MESError(f"lot {lot_id} is {lot['status']}")
        if lot["expires"] and lot["expires"] < dt.date.today().isoformat():
            raise MESError(f"lot {lot_id} expired {lot['expires']}")
        if lot["kg_left"] < kg:
            raise MESError(f"lot {lot_id} has only {lot['kg_left']} kg")
        if b["kg"] + kg > b["capacity_kg"] + 1e-6:
            raise MESError(f"bin {bin_id} holds {b['kg']:.1f} of {b['capacity_kg']:.1f} kg: {kg} kg will not fit")
        self.db.execute("INSERT INTO bin_lot VALUES (?,?,?,?,?,?)", (bin_id, b["cycle"], lot_id, kg, now(), by))
        self.db.execute("UPDATE bin SET kg = kg + ? WHERE id=?", (kg, bin_id))
        self.db.execute("UPDATE lot SET kg_left = kg_left - ? WHERE id=?", (kg, lot_id))
        self.audit(by, "bin.refill", bin_id, lot=lot_id, kg=kg)

    def bin_empty(self, bin_id, by):
        """The bin ran empty (low-level switch, then the operator confirms it is visibly empty). Starts a new lot set."""
        b = self.bin(bin_id)
        self.db.execute("UPDATE bin SET kg=0, cycle=cycle+1, emptied=? WHERE id=?", (now(), bin_id))
        self.audit(by, "bin.empty", bin_id, cycle=b["cycle"], book_kg=round(b["kg"], 2))

    def dose_list(self, bid):
        """Payload for the dosing PLC (DosingStation.st, MES_DoseList): bin lines largest first, then hand adds and premix."""
        b = self.batch(bid)
        if b["status"] != "DISPENSING":
            raise MESError(f"batch {bid} is {b['status']}")
        steps = sorted([p for p in self.pick_list(bid) if p["kind"] == "bin"], key=lambda p: -p["target_kg"])
        for p in steps:
            if self.bin(p["bin"])["kg"] < p["target_kg"]:
                raise MESError(f"bin {p['bin']} ({p['ingredient']}) is short for {p['target_kg']} kg: refill first")
        return dict(BatchID=bid, FormulaID=b["formula"], Steps=[dict(Bin=int(p["bin"][1:]), BinID=p["bin"], Ingredient=p["ingredient"],
                    TargetKg=p["target_kg"], TolKg=p["tol_kg"]) for p in steps], Count=len(steps), Valid=bool(steps))

    def record_dose(self, bid, bin_id, actual_kg, by, scale="P1-220"):
        """The PLC reports a finished dose. Traceability: the batch is linked to every lot in the bin since it last ran empty."""
        b = self.batch(bid)
        if b["status"] != "DISPENSING":
            raise MESError(f"batch {bid} is {b['status']}")
        bn = self.bin(bin_id)
        line = next((p for p in self.pick_list(bid) if p["kind"] == "bin" and p["bin"] == bin_id), None)
        if not line:
            raise MESError(f"bin {bin_id} ({bn['ingredient']}) is not a dosing step of batch {bid}")
        if self.one("SELECT 1 AS x FROM dose WHERE batch=? AND bin=?", bid, bin_id):
            raise MESError(f"bin {bin_id} was already dosed for {bid}")
        if abs(actual_kg - line["target_kg"]) > line["tol_kg"]:
            raise MESError(f"{line['ingredient']} {actual_kg} kg outside {line['target_kg']} +/- {line['tol_kg']} kg: hold the hopper, correct by hand")
        if not bn["lots"]:
            raise MESError(f"bin {bin_id} has no lot on record since it was emptied")
        t = now()
        self.db.execute("INSERT INTO dose VALUES (?,?,?,?,?,?,?,?)", (bid, line["ingredient"], bin_id, bn["cycle"], line["target_kg"], actual_kg, t, by))
        total = sum(l["kg"] for l in bn["lots"])
        for l in bn["lots"]:   # share by kg poured: an estimate of mass, but the lot links are exact
            self.db.execute("INSERT INTO dispense VALUES (?,?,?,?,?,?,?,?)",
                            (bid, line["ingredient"], l["lot"], round(line["target_kg"] * l["kg"] / total, 3),
                             round(actual_kg * l["kg"] / total, 3), f"{scale} via {bin_id}#{bn['cycle']}", t, by))
        self.db.execute("UPDATE bin SET kg = MAX(kg - ?, 0) WHERE id=?", (actual_kg, bin_id))
        self.audit(by, "dose", bid, bin=bin_id, ingredient=line["ingredient"], kg=actual_kg, lots=[l["lot"] for l in bn["lots"]])
        self._check_dispensed(bid, by)

    def plc_download(self, bid):
        """Payload for PLC-601 MES_Download (BlendTrain.st)."""
        b = self.batch(bid)
        if b["status"] != "READY_TO_BLEND":
            raise MESError(f"batch {bid} not fully dispensed")
        salt = sum(d["actual_kg"] for d in self.q("SELECT * FROM dispense WHERE batch=? AND ingredient='salt'", bid))
        f = self.formula(b["formula"])
        return dict(BatchID=bid, FormulaID=b["formula"], TargetKg=b["target_kg"], SaltKg=round(salt, 2), MixTime_s=12 * 60,
                    AllergenClass=1 if "wheat" in (f["allergens"] or "").lower() else 0, Valid=True)

    def blend_complete(self, bid, bag_kg, md_rejects, by):
        bag = f"FB-{bid}"
        self.db.execute("UPDATE batch SET status='QC_HOLD', bag=?, bag_kg=?, md_rejects=? WHERE id=?", (bag, bag_kg, md_rejects, bid))
        self.audit(by, "batch.blended", bid, bag=bag, kg=bag_kg, md_rejects=md_rejects)
        return bag

    def qc_result(self, bid, tracer_results_pct: list[float], micro_ok: bool, by):
        """Blend uniformity: CV of the tracer (salt) over >= 10 samples, spec <= 5 % (site)."""
        if len(tracer_results_pct) < 10:
            raise MESError("CV needs at least 10 samples (top, middle, bottom of bag)")
        cv = statistics.stdev(tracer_results_pct) / statistics.mean(tracer_results_pct) * 100
        b = self.batch(bid)
        ok = cv <= CV_SPEC and micro_ok and b["md_rejects"] is not None
        status = "RELEASED" if ok else "REJECTED"
        self.db.execute("UPDATE batch SET status=?, cv_pct=?, micro=? WHERE id=?", (status, round(cv, 2), "pass" if micro_ok else "fail", bid))
        self.audit(by, "batch.qc", bid, cv=round(cv, 2), micro=micro_ok, status=status)
        return status, round(cv, 2)

    def batch(self, bid):
        b = self.one("SELECT * FROM batch WHERE id=?", bid)
        if not b:
            raise MESError(f"unknown batch {bid}")
        return b

    # ---------------- packing ----------------
    def start_run(self, sku_id, bag_scan, line, units, by):
        s = self.one("SELECT * FROM sku WHERE id=?", sku_id)
        if not s:
            raise MESError(f"unknown SKU {sku_id}")
        b = self.one("SELECT * FROM batch WHERE bag=?", bag_scan)
        if not b:
            raise MESError(f"bag {bag_scan} not found")
        if b["status"] != "RELEASED":
            raise MESError(f"bag {bag_scan} is {b['status']}: only QC-released blend can be packed")
        if b["formula"] != s["formula"]:
            raise MESError(f"bag holds {b['formula']} but {sku_id} needs {s['formula']}")
        f = self.formula(s["formula"])
        if "wheat" in (f["allergens"] or "").lower() and line != "B":
            raise MESError("wheat products pack only at station B (room B, allergen zone Z3A)")
        rid = f"PR{dt.date.today():%y%j}-{self.next('run'):03d}"
        self.db.execute("INSERT INTO pack_run (id, sku, batch, line, units_ordered, status, started) VALUES (?,?,?,?,?,?,?)",
                        (rid, sku_id, b["id"], line, units, "WAIT_LABEL_CHECK", now()))
        self.audit(by, "run.start", rid, sku=sku_id, batch=b["id"], line=line)
        return rid

    def label_check(self, rid, scanned_upc, printed_lot, by):
        """First-off check: label UPC matches SKU and coder prints the batch lot code."""
        r = self.run(rid)
        s = self.one("SELECT * FROM sku WHERE id=?", r["sku"])
        b = self.batch(r["batch"])
        if scanned_upc != s["upc"]:
            raise MESError(f"label UPC {scanned_upc} is not {s['upc']} ({s['id']}): wrong label roll")
        if printed_lot != b["lot_code"]:
            raise MESError(f"coder prints {printed_lot}, batch lot is {b['lot_code']}")
        self.db.execute("UPDATE pack_run SET status='RUNNING', label_ok_by=? WHERE id=?", (by, rid))
        self.audit(by, "run.label_ok", rid)

    def plc_job(self, rid, speed_upm, overfill_pct=1.5):
        r, s = self.run(rid), None
        s = self.one("SELECT * FROM sku WHERE id=?", r["sku"])
        b = self.batch(r["batch"])
        return dict(JobID=rid, SKU=s["id"], LotCode=f"{b['lot_code']} BB {b['best_by']}", BlendBagID=b["bag"], NetG=s["net_g"],
                    TargetG=round(s["net_g"] * (1 + overfill_pct / 100), 1), TareG=s["tare_g"], UnitsOrdered=r["units_ordered"],
                    CaseCount=s["case_count"], SpeedUPM=speed_upm, Valid=r["status"] == "RUNNING")

    def record_weights(self, rid, gross_g: list[float]):
        self.db.executemany("INSERT INTO weight_sample VALUES (?,?,?)", [(rid, g, now()) for g in gross_g])
        self.db.commit()

    def hb133_check(self, rid):
        """NIST HB 133 category A style check on the run's checkweigher data.
        Average net must be >= declared; no unit may be short by more than the MAV."""
        r = self.run(rid)
        s = self.one("SELECT * FROM sku WHERE id=?", r["sku"])
        nets = [w["gross_g"] - s["tare_g"] for w in self.q("SELECT gross_g FROM weight_sample WHERE run=?", rid)]
        if not nets:
            raise MESError("no checkweigher data")
        mav = next(m for lim, m in HB133_MAV if s["net_g"] <= lim) if s["net_g"] <= HB133_MAV[-1][0] else HB133_MAV[-1][1]
        avg = statistics.mean(nets)
        unreasonable = [n for n in nets if n < s["net_g"] - mav]
        under = [n for n in nets if n < s["net_g"]]
        return dict(declared_g=s["net_g"], mav_g=mav, n=len(nets), avg_net_g=round(avg, 2), under_declared=len(under),
                    beyond_mav=len(unreasonable), passed=avg >= s["net_g"] and not unreasonable,
                    note="site rule rejects every unit under declared at CW-409; this check verifies the lot after the fact")

    def end_run(self, rid, good, rej_weight, rej_vision, by):
        self.db.execute("UPDATE pack_run SET status='DONE', ended=?, good=?, rej_weight=?, rej_vision=? WHERE id=?",
                        (now(), good, rej_weight, rej_vision, rid))
        self.audit(by, "run.end", rid, good=good, rej_weight=rej_weight, rej_vision=rej_vision)

    def build_pallet(self, rid, cases, by):
        r = self.run(rid)
        s = self.one("SELECT * FROM sku WHERE id=?", r["sku"])
        b = self.batch(r["batch"])
        code = gs1.sscc(self.next("sscc"))
        self.db.execute("INSERT INTO pallet VALUES (?,?,?,?,?)", (code, rid, cases, now(), None))
        self.audit(by, "pallet.build", code, run=rid, cases=cases)
        return code, gs1.pallet_label_zpl(code, s["gtin14"], b["lot_code"], dt.date.fromisoformat(b["best_by"]), cases)

    def ship(self, sscc18, customer, by):
        self.db.execute("UPDATE pallet SET shipped_to=? WHERE sscc=?", (customer, sscc18))
        self.audit(by, "pallet.ship", sscc18, customer=customer)

    def run(self, rid):
        r = self.one("SELECT * FROM pack_run WHERE id=?", rid)
        if not r:
            raise MESError(f"unknown run {rid}")
        return r

    def case_label(self, rid):
        r = self.run(rid)
        s = self.one("SELECT * FROM sku WHERE id=?", r["sku"])
        b = self.batch(r["batch"])
        f = self.formula(s["formula"])
        return gs1.case_label_zpl(f["name"], s["id"], s["gtin14"], b["lot_code"], dt.date.fromisoformat(b["best_by"]), s["case_count"],
                                  f"{s['net_g'] / 28.3495:.2f} oz")

    # ---------------- traceability ----------------
    def trace_back(self, lot_code):
        """Finished lot -> blend batch -> every ingredient lot and supplier lot (FSMA 204 style one-up/one-back)."""
        b = self.batch(lot_code)
        ins = self.q("SELECT d.ingredient, d.lot, d.actual_kg, l.supplier, l.supplier_lot FROM dispense d JOIN lot l ON l.id=d.lot WHERE d.batch=?", lot_code)
        runs = self.q("SELECT id, sku, line, good FROM pack_run WHERE batch=?", lot_code)
        doses = self.q("SELECT ingredient, bin, cycle, actual_kg FROM dose WHERE batch=?", lot_code)
        return dict(batch=b, ingredients=ins, doses=doses, runs=runs)

    def trace_forward(self, rm_lot):
        """Ingredient lot -> batches -> runs -> pallets -> customers (for a supplier recall)."""
        batches = sorted({r["batch"] for r in self.q("SELECT batch FROM dispense WHERE lot=?", rm_lot)})
        out = []
        for bid in batches:
            for r in self.q("SELECT id, sku FROM pack_run WHERE batch=?", bid):
                pallets = self.q("SELECT sscc, cases, shipped_to FROM pallet WHERE run=?", r["id"])
                out.append(dict(batch=bid, run=r["id"], sku=r["sku"], pallets=pallets))
            if not self.q("SELECT id FROM pack_run WHERE batch=?", bid):
                out.append(dict(batch=bid, run=None, sku=None, pallets=[]))
        return out

    def batch_record(self, bid):
        """Electronic batch record: everything about one lot, with the audit trail."""
        rec = self.trace_back(bid)
        rec["pick_list"] = self.pick_list(bid)
        rec["audit"] = self.q("SELECT at, by, kind, data FROM audit WHERE ref=? OR data LIKE ? ORDER BY seq", bid, f'%"{bid}"%')
        return rec

    # ---------------- scheduling ----------------
    def allergen_sequence(self, formulas: list[str]) -> list[str]:
        """Order a week's blends: no-allergen first, mildest to hottest by name heuristics, wheat last (Friday) before the wet clean."""
        heat = lambda fid: (1 if any(k in fid for k in ("fire", "blkn", "caml")) else 0)
        def key(fid):
            f = self.formula(fid)
            return (1 if "wheat" in (f["allergens"] or "").lower() else 0, heat(fid), fid)
        return sorted(formulas, key=key)
