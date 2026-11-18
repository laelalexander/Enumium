"""Phase 1 build package for the Anatomy Build wizard (references/build-package.md).

Usage: python3 make_build.py   (from phase1/build)
Reads design/equipment.json, cad/parts.json and design/out/dosing-plan.json, writes:
  build.json                       the wizard's plan (paths relative to the downhome-spice-line project root)
  1-purchase/purchase-list.csv     every BUY line, plus one <supplier>-cart.csv per supplier
  2-print/print-list.csv           the PETG fixtures (STL; G-code is sliced on the user's PC, see README)
  3-fabricate/fab-list.csv         every BUILD line with its cut files, STEP and drawing
  README.md                        what is built, cost, time, the stages and the check result
and runs the consistency check (every purchase / print / fabricate line traces to equipment.json and every
assembly part exists in one of them). Exit 1 if the check fails.
"""
import csv
import json
import pathlib
import re
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).parent
P1 = HERE.parent
ROOT = P1.parent                      # downhome-spice-line: paths in build.json are relative to this
REL = "phase1"
EQ = json.loads((P1 / "design" / "equipment.json").read_text())
PARTS = {p["id"]: p for p in json.loads((P1 / "cad" / "parts.json").read_text())}
PARTS.update({p["id"]: p for p in json.loads((P1 / "cad" / "machines.json").read_text())["parts"]})
DOSING = json.loads((P1 / "design" / "out" / "dosing-plan.json").read_text())
BY = {e["tag"]: e for e in EQ}


def rp(p):
    return f"{REL}/{p}"


def unit(e):
    return round(e["ext_usd"] / e["qty"], 2)


def purchase():
    out = []
    for e in EQ:
        if e["kind"] != "buy":
            continue
        out.append(dict(line=e["tag"], desc=e["name"], mfr=e["maker"], mpn=e["model"], qty=e["qty"], supplier=e["supplier"], url=e["source"],
                        unit_price=unit(e), price_src=(e.get("price") or {}).get("src", ""),
                        alt="; ".join(a if isinstance(a, str) else f"{a.get('maker', '')} {a.get('model', '')}".strip() for a in e.get("alternates") or []),
                        notes="; ".join(x for x in [e.get("confirm") or "", "carries over to Growth" if e.get("reuse_in_growth") else ""] if x)))
    # bought hardware inside fabricated items (named in the fabrication notes)
    out += [
        dict(line="P1-309-HW", desc="Swivel plate caster 3 in, stainless, 2 with brake (4 per dolly)", mfr="Colson", mpn="2 Series 3 in SS (confirm plate 2.5 x 3.6 in)",
             qty=12, supplier="Grainger", url="https://www.grainger.com/category/material-handling/casters-and-wheels/casters", unit_price=38.0,
             price_src="estimate", alt="Albion 16 series", notes="for P1-309 drum dollies (3)"),
        dict(line="P1-408-HW", desc="Lazy-susan bearing 12 in, 500 lb", mfr="Lee Valley / Shepherd", mpn="12 in square turntable bearing (confirm hole pattern)",
             qty=1, supplier="Amazon / Grainger", url="https://www.grainger.com/search?searchQuery=lazy+susan+bearing+12", unit_price=24.0,
             price_src="estimate", alt="", notes="for P1-408 turntable"),
        dict(line="P1-208-HW", desc="Flange bearing 1 in bore, stainless 2-bolt", mfr="Dodge / AMI", mpn="UCFL205-16 SS class (confirm)", qty=4,
             supplier="Motion Industries", url="https://www.motion.com/", unit_price=42.0, price_src="estimate", alt="", notes="for P1-208 tumbler"),
        dict(line="P1-208-GM", desc="Gearmotor 1/8 HP 90 V DC, about 30 rpm output, with speed control", mfr="Bodine Electric", mpn="type 33A-5N + WPM control (confirm)",
             qty=1, supplier="Bodine dealer", url="https://www.bodine-electric.com/", unit_price=420.0, price_src="estimate", alt="Leeson DC gearmotor", notes="for P1-208 tumbler"),
    ]
    return out


def prints():
    out = []
    for pid, p in PARTS.items():
        if not p.get("print"):
            continue
        out.append(dict(part=pid, line="P1-410", title=p["title"], qty=p["qty"], material="PETG", stl=rp(p["stl"]), gcode="",
                        plate=1, time_min=None, grams=p.get("grams_est"), orientation="flat base down", supports="none",
                        after="wipe; never in the product zone (pack bench fixtures only)",
                        checks=[f"overall {p['size_mm'][0]} x {p['size_mm'][1]} x {p['size_mm'][2]} mm ±0.3", "container or cap drops in without force"],
                        status="NOT SLICED: open the STL in Bambu Studio on Yaeger, PETG, 0.2 mm, 3 walls, 25 % gyroid, then save .gcode.3mf beside it"))
    return out


def fabricate():
    out = []
    for e in EQ:
        if e["kind"] != "build" or e["tag"] == "P1-410":
            continue
        b = e["build"]
        files = []
        for f in b.get("files") or []:
            stem = pathlib.Path(f).name
            for cand in (f"dxf/{stem}_mm.dxf", f"dxf/{stem}_in.dxf", f"cad/step/{stem}.step", f"drawings/parts/{stem}.svg", f"drawings/png/{stem}.png"):
                if (P1 / cand).exists():
                    files.append(rp(cand))
        if b["drawing"].endswith("-GA"):
            for cand in (f"drawings/machines/{b['drawing']}.svg", f"drawings/png/{b['drawing']}.png", f"cad/step/{b['drawing'][:-3]}-ASM.step"):
                if (P1 / cand).exists():
                    files.append(rp(cand))
        for pid in re.findall(r"P1-\d{3}(?:-\d{2})?", b["drawing"]):
            for k in ("step", "drawing"):
                if pid in PARTS and PARTS[pid].get(k):
                    files.append(rp(PARTS[pid][k]))
            for d in PARTS.get(pid, {}).get("dxf", []):
                files.append(rp(d))
        out.append(dict(part=e["tag"], title=e["name"], process=b["process"], files=list(dict.fromkeys(files)), material=b["material"],
                        qty=e["qty"], vendor=e["supplier"], labor_h=b["labor_h"], material_usd=b["material_usd"],
                        settings="304/316L as noted; continuous welds ground flush, #4 finish on product contact, passivate; "
                                 "measure every VERIFY dimension on the bought part first"))
    return out


A = lambda *tags: [{"line": t, "qty": BY[t]["qty"] if t in BY else 1} for t in tags]
PNG = lambda t: rp(f"drawings/png/{t}.png")

ASSEMBLY = [
    dict(step=1, title="Prepare the rooms and mark the layout", image=PNG("LAY-P1"), parts=[], tools=["tape measure", "chalk line", "laser level"],
         text="Before any equipment: sealed epoxy floor with coved base in the two Z3 rooms, washable ceiling, 208 V 3-phase and 120 V circuits per the layout, "
              "hand sink at the vestibule. Snap the equipment outlines from drawing DH-LAY-P1 (1:50) onto the floor.",
         check="every outline matches DH-LAY-P1 within 25 mm [1 in]; 900 mm [36 in] aisles clear"),
    dict(step=2, title="Receiving and storage", image=PNG("LAY-P1"), parts=A("P1-101", "P1-102", "P1-103"), tools=["hex keys", "level"],
         text="Set the floor scale with its ramp at the receiving door and level it. Build the six NSF shelving units 6 in off the floor and 18 in from walls.",
         check="floor scale reads a 50 lb test weight within 0.2 lb"),
    dict(step=3, title="Anchor the bin ring frame", image=PNG("ASM-P1-001"), parts=A("P1-210", "P1-227"), tools=["hammer drill 1/2 in", "torque wrench", "laser level"],
         text="Stand the ring frame on its marks (ring top 2,235 mm [88.0 in], drawing ASM-P1-001), shim the foot plates level and anchor each with 1/2 in wedge anchors, 3 in embed. Seal the foot plates to the floor with food-grade silicone. Roll the 4-step platform to the bin side.",
         torque="1/2 in wedge anchors 60 N·m [45 lbf·ft]", check="ring top level within 2 mm across"),
    dict(step=4, title="Mount the load cells and weigh hopper", image=PNG("P1-220"), parts=A("P1-221", "P1-220", "P1-223"),
         tools=["torque wrench", "test weights 2 x 20 kg"], text="Bolt the three weigh modules to the frame brackets, lower the hopper onto them, fit the 4 in butterfly valve on the outlet Tri-Clamp. "
         "Nothing but the silicone sleeves may touch the hopper.", torque="M12 load-cell mount bolts 70 N·m (A2-70)",
         check="hopper rocks freely on the cells; nothing bridges to the frame"),
    dict(step=5, title="Build the feeders; hang the bins, feeders and level probes", image=PNG("P1-212-GA"),
         parts=A("P1-211", "P1-212", "P1-215", "P1-216", "P1-217", "P1-213", "P1-214", "P1-241", "P1-242", "P1-243", "P1-244", "P1-245", "P1-246", "P1-247", "P1-248"), tools=["torque wrench", "hex keys"],
         text="In the shop, build each of the 9 feeders per drawing set P1-212-000..900 (sheet 003 has the steps): drive cartridge (bearings, lip seal, pinned shaft), "
              "lantern, jaw coupling and 0.25 kW gearmotor, then hang the barrel and slide the screw in from the tail (it pulls out the tail end for cleaning). Fit the slow agitator kit on the herb and peel bins. "
              "On site, bolt each bin to its ring position with M12 bolts, the feeder to the bin outlet flange with an FDA gasket, "
              "and a silicone sleeve P1-214 from each vertical feeder spout over its hopper lid stub (2 band clamps). Fit a Soliphant in each bin's low-level port. Bins B01 to B09 in the order of dosing-plan.md "
              "(salt, garlic, paprika, onion, black pepper, coarse black pepper, cayenne, lemon peel, red pepper); positions 10 to 12 stay blanked for growth.",
         torque="M10 outlet flange 25 N·m; M12 bin lugs 70 N·m; M6 drive and lantern screws 8 N·m; sleeve clamps 3 N·m", check="each screw turns by hand without rubbing; every connector sits square; tag each bin"),
    dict(step=6, title="Build and set the ribbon blender, run the flexible screw", image=PNG("P1-301-GA"),
         parts=A("P1-301", "P1-333", "P1-334", "P1-335", "P1-331", "P1-332", "P1-336", "P1-302", "P1-224"), tools=["engine hoist", "torque wrench", "feeler gauges"],
         text="In the shop, per P1-301-GA: stand the frame, set the trough on its saddles and bolt the end plates; lower the agitator in, slide the UCF212 bearings on and bolt them to the end plates, "
              "pack the glands (4 PTFE rings each), slide the hollow-shaft gearmotor on the drive end with its torque arm. Clamp the discharge valve P1-331 to the bottom port, "
              "fit the cover with the interlock P1-332 and the bag-dump grate. Set the blender on its marks (no riser stand; trough bottom 1,400 mm [55.1 in], valve outlet 1,261 mm [49.6 in]) and anchor the feet. "
              "Run the flexible screw from the intake grate under the hopper valve (550 mm [21.7 in]) up to the 4 in inlet on the cover (1,983 mm [78.1 in]), supported at its midpoint; hand adds and premix are tipped into the intake grate.",
         torque="M12 end-plate and feet 70 N·m; UCF212 M16 bolts 120 N·m; gland follower M10 hand tight plus 1/4 turn",
         check="ribbons clear the trough by 3 to 6 mm all along; shaft turns by hand; glands do not weep; cover interlock stops the VFD; drum on its dolly rolls in between the legs"),
    dict(step=7, title="Drum-top sifter, magnet and drum dollies", image=PNG("ASM-P1-002"), parts=A("P1-304", "P1-305", "P1-306", "P1-307", "P1-308", "P1-309"),
         tools=["torque wrench"], text="Build the sifter per its own set P1-304-000..900 (assembly sheet P1-304-003): isolators into the seat ring, vibrator on its bracket "
         "(weights at 80 %), body onto the isolators, flex band and bond strap, grate magnet on the bars, 12 mesh deck on the ledge, lid on the 4 draw latches. "
         "Build the three drum dollies. Roll a lined drum in under the blender valve, set the sifter on the drum rim (seat 1,054 mm [41.5 in]) and pull the valve sock over its 4 in inlet (1,235 mm [48.6 in]).",
         torque="isolator nuts M8 12 N·m; vibrator M10 45 N·m + thread lock (re-check after 1 h)", check="gap body to upstand 4 ±1 all round; pads press the deck; magnet pull test card picks up; sifter sits level on the rim; ITP P1-304-900 T9-T18"),
    dict(step=8, title="Hammer mill, feed magnet and hopper", image=PNG("ASM-P1-002"), parts=A("P1-320", "P1-321", "P1-322"),
         tools=["torque wrench", "hammer drill 3/8 in", "IR thermometer"], text="Set the mill on its stand and anchor it. Bolt the feed hopper to the mill inlet with the FDA gasket, slide the grate magnet into "
         "the hopper slot, and fit the discharge transition with a sock into a lined 5 gal pail. Connect the 150 cfm dust pickup.",
         torque="M8 hopper and discharge flanges 18 N·m; 3/8 in stand anchors 34 N·m", check="a 1 kg peppercorn trial grinds through the 1/8 in screen with the product under 40 °C [104 °F]; magnet pull test passes"),
    dict(step=9, title="Weigh bench, hood and premix tumbler", image=PNG("P1-206"), parts=A("P1-206", "P1-208", "P1-201", "P1-202", "P1-203", "P1-204"),
         tools=["torque wrench"], text="Place the weigh bench, bolt the backdraft hood to its back edge, set the two Mettler scales and the label printer, and set the tumbler on the bench end.",
         torque="M6 hood bolts 6 N·m", check="both scales level (bubble) and calibrated with test weights"),
    dict(step=10, title="Dust collection", image=PNG("P1-207"), parts=A("P1-310"), tools=["duct tools", "anemometer"],
         text="Set the collector on its outside pad and run 4 in ducts to the weigh hood (300 cfm), weigh hopper vent (150 cfm), blender grate (250 cfm), drum-top sifter drum vent (200 cfm) and mill (150 cfm), with a blast gate at each.",
         check="measured airflow at each pickup within 10 % of its design value; total under the collector's 1,400 cfm"),
    dict(step=11, title="Build the pack machines", image=PNG("P1-401-GA"),
         parts=A("P1-401", "P1-413", "P1-414", "P1-415", "P1-416", "P1-417", "P1-430", "P1-431", "P1-432", "P1-433", "P1-434", "P1-435", "P1-436", "P1-437", "P1-438", "P1-439", "P1-440", "P1-441", "P1-442", "P1-443", "P1-444", "P1-445", "P1-446", "P1-412", "P1-422", "P1-423", "P1-424", "P1-450", "P1-451", "P1-452", "P1-453", "P1-404", "P1-425", "P1-426", "P1-427",
                 "P1-406", "P1-418", "P1-419", "P1-420", "P1-421"), tools=["torque wrench", "hex keys", "dial indicator"],
         text="In the shop, per the GA sheets. Filler P1-401 rev B per its own set P1-401-000..900 (assembly sheet P1-401-003, 14 steps): cabinet and back panel, column, stage, spindle cartridge and hub, drives and guards, hopper, agitator, tooling, HMI. "
              "Capper P1-412 rev B per its own set P1-412-000..900 (assembly sheet P1-412-003, 8 steps): base weldment, rail and gas spring, carriage, drive line and chuck, guard, lever and link, nest and toggle clamp, controls box and limit switch. Labeler P1-404-GA: rollers in their blocks, stepper and belt, spindles, peel plate, gap sensor. "
              "Detector conveyor P1-406-GA: frame, pulleys and belt, gearmotor; mount the used detector head over the belt with nothing metal within 1.5 x the aperture height, and the reject pusher after it.",
         torque="filler column M12 70 N·m, head plate M10 45 N·m, servo M6 8 N·m (full list P1-401-800); M8 to frames 18 N·m; auger tube clamp hand tight", check="filler ITP P1-401-900 T9-T18 (auger 0.25 TIR in the tube);  capper ITP P1-412-900 T6-T19 (chuck 0.1 TIR, clutch torque on the tester P1-402); detector conveyor belt tracks centred"),
    dict(step=12, title="Pack bench", image=PNG("ASM-P1-003"), parts=A("P1-409", "P1-402", "P1-403", "P1-405", "P1-407", "P1-408", "P1-410", "P1-411"),
         tools=["hex keys", "level"], text="Set the filler, then line up the four stainless tables: capper and sealer, printer and labeler, the detector conveyor, checkweigh and case pack, with the turntable at the end. "
         "Set the filler stage to the container (index plunger) and fit the printed nests on the capper.",
         check="metal detector rejects the Fe 1.5, non-Fe 2.0 and SS 2.5 mm test pieces in the leading, middle and trailing position"),
    dict(step=13, title="Controls and wiring", image=PNG("ELE-P1-003"), parts=A("P1-225", "P1-226", "P1-222"), tools=["electrician's tools", "multimeter"],
         text="Mount the WAGO panel and the nine GS21 drives, wire feeders, probes, both valve actuators, screw, blender VFD and cover interlock, sifter vibrator and mill per drawings ELE-P1-001 to 003 (every wire numbered slot-channel). "
              "E-stops and the hopper and screw guards go through the safety relay, not the PLC. A licensed electrician does the power wiring.",
         check="every I/O point toggles on the PLC watch list; e-stop drops all drives"),
    dict(step=14, title="MES computer and commissioning", image=PNG("LAY-P1"), parts=A("P1-205", "P1-701", "P1-702", "P1-703", "P1-704"), tools=["laptop"],
         text="Install the MES (software/mes) on the Dell, start it with --blender P1-301, assign B01 to B09 and load the first lots. Calibrate the hopper, tune the dosing in-flight, then run the acceptance tests below.",
         check="all acceptance tests pass and are signed"),
]


def main():
    pur, pr, fab = purchase(), prints(), fabricate()
    buy_total = sum(p["unit_price"] * p["qty"] for p in pur)
    fab_total = sum(BY[f["part"]]["ext_usd"] for f in fab) + BY["P1-410"]["ext_usd"]
    hours = sum(f["labor_h"] for f in fab)
    grams = round(sum((p["grams"] or 0) * int(p["qty"]) for p in pr))
    build = dict(
        title="Down Home Creole spice plant: Phase 1 prototype",
        summary="A 2,000 sq ft blended-seasoning plant for 1,000 lb a week on one shift, launching with 5 blends and laid out for all 13. "
                f"Ingredients are dosed from {len(DOSING['bins'])} stainless bins (12 positions) into a weigh hopper and blended in a 6 cu ft ribbon blender we build, "
                f"sifted on the drum, held for QC, then packed on a bench of machines we build: servo auger filler, spindle capper, wrap labeler and a detector conveyor. {DOSING['auto_pct_overall']} % of blend weight is dosed automatically. "
                "Stainless frames, bins, hoppers, tables and most machines are fabricated in house to save money; scales, motors, drives, valves and a used metal detector head are bought.",
        totals=dict(parts_cost=round(buy_total + fab_total, 2), currency="USD", bought=round(buy_total, 2), fabricated=round(fab_total, 2),
                    fabrication_hours=hours, print_hours=None, filament_g={"PETG": grams}, build_hours=hours + 120,
                    note="build_hours = fabrication + about 120 h install and commissioning; excludes building fit-out and electrical service"),
        tools=["TIG welder and stainless consumables", "hammer drill 1/2 in", "torque wrench 5 to 100 N·m", "laser level", "hex keys", "test weights (2 x 20 kg, 1 kg, 100 g class F1)",
               "metal detector test pieces Fe 1.5 / non-Fe 2.0 / SS 2.5 mm", "anemometer", "multimeter", "laptop with CODESYS 3.5"],
        purchase=pur, print=pr, fabricate=fab, assembly=ASSEMBLY,
        firmware=[
            dict(name="Dosing station PLC (P1-225)", dir="software/plc", build="CODESYS 3.5: new WAGO PFC200 project, add DosingStation.st as a program, map the I/O", flash="CODESYS: Login, Download",
                 binary="", check="watch list shows Dose_Step = IDLE; HOLD alarms clear with HMI_Reset"),
            dict(name="Plant MES", dir="software/mes", build="python3 -m unittest discover -s tests -t .", flash="python3 -m dhmes.server --blender P1-301 --db p1.db --port 8080",
                 binary="", check="http://<mes-pc>:8080 shows Ingredient bins, Blend batches and Pack runs"),
        ],
        tests=[
            dict(name="Weigh hopper calibration", steps=["empty and zero the 880", "add 20 kg, then 40 kg of test weight at each load-cell corner"], expect="reads within ±20 g at every corner and load"),
            dict(name="Dose accuracy per bin", steps=["dose each bin's largest planned target 5 times (dosing-plan.md)", "record the hopper weight after settle"],
                 expect="every dose within ±1 % (20 g minimum); in-flight learned and stable"),
            dict(name="No-flow and bin-low holds", steps=["run a feeder with its bin empty", "cover then uncover the Soliphant"], expect="NO FLOW alarm within 8 s; BIN LOW stops the step"),
            dict(name="Blend uniformity", steps=["blend a full Original batch", "pull 10 samples top, middle and bottom", "test salt"], expect="CV ≤ 5 %"),
            dict(name="Metal detector (CCP-1)", steps=["pass each test piece in leading, middle and trailing position, 3 times"], expect="every pass rejected into the locked bin"),
            dict(name="Net contents (NIST HB 133)", steps=["fill 30 units of each launch size", "weigh on P1-407"], expect="average ≥ declared; no unit short by more than the MAV"),
            dict(name="Traceability drill", steps=["pick a salt lot", "trace forward in the MES", "trace a finished lot back"], expect="every batch and pallet found in under 2 hours"),
            dict(name="Food-safety design checks", steps=["python3 skills/anatomy/tools/plant/foodsafety.py ... (see README)"], expect="zoning, sanitary, dust airflow, shared equipment all PASS"),
        ],
        gaps=["G-code for the 4 PETG fixtures is not sliced yet: slice the STLs in Bambu Studio on Yaeger and add the .gcode.3mf paths",
              "Assembly pictures are the part drawings and the layout, not rendered 3D assembly steps",
              "Bought parts for the built machines are catalog-class picks marked confirm: check each model and price before ordering; the used detector head P1-418 is an estimate until a unit is inspected",
              "Built machines are first articles: expect one round of fit-up changes (ECO) on the blender agitator and the filler auger tooling"],
    )
    (HERE / "build.json").write_text(json.dumps(build, indent=1))

    for d in ("1-purchase", "2-print", "3-fabricate"):
        (HERE / d).mkdir(exist_ok=True)
    cols = ["line", "desc", "mfr", "mpn", "qty", "unit_price", "price_src", "supplier", "url", "alt", "notes"]
    with open(HERE / "1-purchase" / "purchase-list.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(pur)
    by_sup = defaultdict(list)
    for p in pur:
        by_sup[re.sub(r"[^A-Za-z0-9]+", "-", p["supplier"].split("(")[0].split("/")[0].strip()).strip("-").lower()].append(p)
    for s, rows in by_sup.items():
        with open(HERE / "1-purchase" / f"{s}-cart.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Manufacturer", "Part / model", "Quantity", "Description", "Line"])
            w.writerows([[r["mfr"], r["mpn"], r["qty"], r["desc"], r["line"]] for r in rows])
    with open(HERE / "2-print" / "print-list.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["part", "title", "qty", "material", "stl", "grams_est", "status"])
        w.writerows([[p["part"], p["title"], p["qty"], p["material"], p["stl"], p["grams"], p["status"]] for p in pr])
    with open(HERE / "3-fabricate" / "fab-list.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["part", "title", "qty", "material", "process", "labor_h", "material_usd", "files"])
        w.writerows([[x["part"], x["title"], x["qty"], x["material"], x["process"], x["labor_h"], x["material_usd"], "; ".join(x["files"])] for x in fab])

    # ---- check
    problems = []
    lines = {p["line"] for p in pur} | {p["part"] for p in fab} | {"P1-410"}
    for e in EQ:
        if e["tag"] not in lines:
            problems.append(f"{e['tag']} is in equipment.json but not in purchase, print or fabricate")
    for s in ASSEMBLY:
        for p in s["parts"]:
            if p["line"] not in lines:
                problems.append(f"assembly step {s['step']} uses {p['line']}, which is not in the package")
        if s["image"] and not (ROOT / s["image"]).exists():
            problems.append(f"assembly step {s['step']} image missing: {s['image']}")
    used = {p["line"] for s in ASSEMBLY for p in s["parts"]}
    for e in EQ:
        if e["tag"] not in used:
            problems.append(f"{e['tag']} is never installed in an assembly step")
    for f in fab:
        if not f["files"]:
            problems.append(f"{f['part']} has no fabrication file")
        for x in f["files"]:
            if not (ROOT / x).exists():
                problems.append(f"{f['part']} file missing: {x}")
    for p in pr:
        if not (ROOT / p["stl"]).exists():
            problems.append(f"{p['part']} STL missing")

    L = ["# Phase 1 build package", "",
         build["summary"], "",
         f"**Cost:** ${buy_total + fab_total:,.0f} (${buy_total:,.0f} bought, ${fab_total:,.0f} fabricated). "
         f"**Fabrication:** {hours} shop hours. **Install and commissioning:** about 120 hours. **Prints:** 4 PETG fixtures, about {grams} g.", "",
         "## Stages", "",
         f"1. **Purchase**: `1-purchase/purchase-list.csv` ({len(pur)} lines) and one cart file per supplier.",
         f"2. **Print**: `2-print/print-list.csv` ({len(pr)} fixtures). Not sliced yet: slice in Bambu Studio on Yaeger.",
         f"3. **Fabricate**: `3-fabricate/fab-list.csv` ({len(fab)} items) with DXF cut files in mm and inch, STEP models and dimensioned drawings.",
         f"4. **Assemble**: {len(ASSEMBLY)} steps in `build.json`, from floor marking to commissioning.",
         "5. **Software and tests**: `software/plc/DosingStation.st` on the WAGO, the MES with `--blender P1-301`, and the acceptance tests in `build.json`.", "",
         "## Package check", ""]
    L += [f"- {p}" for p in problems] if problems else ["PASS: every equipment line is purchased, printed or fabricated; every one is installed in an assembly step; every file exists."]
    L += ["", "## Gaps", ""] + [f"- {g}" for g in build["gaps"]]
    (HERE / "README.md").write_text("\n".join(L) + "\n")
    print(f"purchase {len(pur)}  print {len(pr)}  fabricate {len(fab)}  assembly {len(ASSEMBLY)}  total ${buy_total + fab_total:,.0f}")
    for p in problems:
        print("  -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
