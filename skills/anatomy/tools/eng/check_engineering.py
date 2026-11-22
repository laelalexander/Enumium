"""Grade every part from its evidence: Concept, Engineered or Verified (references/precision-engineering.md).

    python check_engineering.py <engineering.json> --root <project dir> [--out report.md] [--json out.json]
    python check_engineering.py --init <assembly.json> --root <project dir> --out <engineering.json>

--init writes a starting engineering.json from assembly.json: every part at grade "concept", its class guessed
(bought for BUY parts, else structural) and its STEP found by name. Fill it in as each part is engineered.

The check measures each part's STEP with step_features.py, recomputes the grade from the record plus the
measurements, and reports what is missing. Exit code 1 when any part claims a higher grade than its evidence,
or when a STEP file is missing.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ORDER = {"concept": 0, "engineered": 1, "verified": 2}
NAMES = ["concept", "engineered", "verified"]


def find_step(root, stem, part_no=""):
    stem_l = stem.lower()
    best = None
    for d, _, fs in os.walk(root):
        if any(x in d for x in (".venv", "node_modules", ".anatomy", "__pycache__", "/print", "\\print")):
            continue
        for f in fs:
            if not f.lower().endswith((".step", ".stp")):
                continue
            fl = f.lower()
            # mirrored / repeated parts (FR_ of an FL_ part, _R of an _L part) share the STEP of their BOM line
            core = re.sub(r"^(fl|fr|rl|rr)_|_(l|r|a|b)$", "", stem_l)
            if stem_l in fl or (part_no and fl.startswith(part_no.lower() + "_") and core in fl):
                p = os.path.join(d, f)
                if best is None or len(p) < len(best):
                    best = p
    return os.path.relpath(best, root).replace("\\", "/") if best else None


def init(asm_path, root, out):
    asm = json.load(open(asm_path, encoding="utf-8-sig"))
    parts = {}
    for p in asm.get("parts", []):
        stem = os.path.splitext(p["file"])[0]
        kind = (p.get("kind") or "").lower()
        parts[p["file"]] = {
            "part_no": p.get("line", ""), "name": p.get("name", stem),
            "class": "bought" if kind == "buy" else "structural",
            "grade": "concept", "step": find_step(root, stem, p.get("line", "")),
            "open": ["not yet engineered: see references/precision-engineering.md"],
        }
    json.dump({"parts": parts}, open(out, "w", encoding="utf-8"), indent=1)
    print(f"wrote {out}: {len(parts)} parts at grade concept")


def evidence(rec, feat):
    """(grade the evidence supports, list of what is missing for the next grade)."""
    cls = rec.get("class", "structural")
    miss_e, miss_v = [], []
    if feat is None:
        miss_e.append("no STEP file (the CAD must export one)")
    elif feat.get("error"):
        miss_e.append("STEP could not be read: " + feat["error"][:120])
    elif feat.get("primitive"):
        miss_e.append("STEP is still a bare primitive (box/cylinder): model the real part")
    if cls == "bought":
        if not (rec.get("vendor_step") or rec.get("geometry") in ("vendor STEP", "datasheet model")):
            miss_e.append("vendor STEP (or a cited datasheet model) for the bought part")
        if not (rec.get("mpn") or rec.get("part_no")):
            miss_e.append("manufacturer part number")
        if not rec.get("interfaces"):
            miss_v.append("interface check against the vendor drawing (fit, bolt pattern, clearance)")
    else:
        for k, label in (("material", "full material specification"), ("process", "process route"),
                         ("drawing", "detail drawing")):
            if not rec.get(k):
                miss_e.append(label)
        if rec.get("mass_kg") in (None, ""):
            miss_e.append("mass from the CAD")
        dfm = rec.get("dfm") or {}
        if not dfm.get("pass"):
            miss_e.append("DFM check for the process (recorded and passing)")
        if feat and not feat.get("error") and cls != "cosmetic" and (feat.get("fillets", 0) + feat.get("chamfers", 0)) == 0 \
                and not rec.get("sharp_edges_reason"):
            miss_e.append("no fillets or chamfers in the CAD (or a stated reason for sharp edges)")
        declared = sum(int(h.get("qty", 1)) for h in rec.get("holes", []) or [])
        if feat and not feat.get("error") and declared and feat.get("hole_count", 0) == 0:
            miss_e.append(f"{declared} holes declared but none are modelled in the STEP")
        if cls == "precision":
            for k, label in (("datums", "datum scheme"), ("finish", "surface finish")):
                if not rec.get(k):
                    miss_e.append(label)
            if not rec.get("fits"):
                miss_e.append("ISO 286 fits on mating features")
            if not rec.get("gdt"):
                miss_e.append("GD&T controls referencing the datums")
        if cls in ("precision", "structural"):
            fea = rec.get("fea") or {}
            m = fea.get("margin")
            if m is None:
                miss_v.append("FEA (or hand calc) with a margin of safety")
            elif m < 0:
                miss_v.append(f"FEA margin {m} < 0: the part fails its load case")
            elif fea.get("converged") is False:
                miss_v.append("FEA mesh convergence")
            if rec.get("fits"):
                st = rec.get("stackups") or []
                if not st:
                    miss_v.append("tolerance stack-up for the fits")
                elif not all(s.get("pass") for s in st):
                    miss_v.append("a tolerance stack-up fails its requirement")
            if not rec.get("inspection"):
                miss_v.append("inspection plan")
    if miss_e:
        return "concept", miss_e
    if miss_v:
        return "engineered", miss_v
    return "verified", []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("eng", nargs="?")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--init")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    if a.init:
        return init(a.init, root, a.out or "engineering.json")
    data = json.load(open(a.eng, encoding="utf-8-sig"))
    try:
        from step_features import measure
    except Exception as e:  # build123d missing
        measure = None
        print("warning: build123d not available, STEP features not measured:", e)
    rows, fail = [], False
    counts = {"concept": 0, "engineered": 0, "verified": 0}
    results = {}
    for key, rec in data.get("parts", {}).items():
        step = rec.get("step")
        feat = None
        if step:
            p = os.path.join(root, step)
            if not os.path.exists(p):
                feat = {"error": "missing file " + step}
            elif measure:
                try:
                    feat = measure(p)
                except Exception as e:
                    feat = {"error": str(e)}
        g, missing = evidence(rec, feat)
        claimed = (rec.get("grade") or "concept").lower()
        bad = ORDER.get(claimed, 0) > ORDER[g]
        fail |= bad or (feat or {}).get("error", "").startswith("missing")
        counts[g] += 1
        results[key] = {"claimed": claimed, "evidence": g, "missing": missing, "features": feat, "overclaimed": bad}
        rows.append((rec.get("part_no", ""), rec.get("name", key), rec.get("class", ""), claimed, g, bad, missing, feat))
    total = len(rows)
    ready = all(r[4] == "verified" for r in rows if r[2] in ("precision", "structural")) and \
        all(r[4] != "concept" for r in rows)
    lines = ["# Engineering grade report", "",
             f"{total} parts: **{counts['verified']} verified**, {counts['engineered']} engineered, {counts['concept']} concept. "
             + ("**Build-ready.**" if ready else "**Not build-ready** (every precision and structural part must be Verified, every other part at least Engineered)."), "",
             "| Part | Name | Class | Claimed | Evidence | Holes / fillets / chamfers in STEP | Missing for the next grade |", "|---|---|---|---|---|---|---|"]
    for pn, name, cls, claimed, g, bad, missing, feat in sorted(rows, key=lambda r: (ORDER[r[4]], r[0])):
        f = "" if not feat or feat.get("error") else f"{feat.get('hole_count', 0)} / {feat.get('fillets', 0)} / {feat.get('chamfers', 0)}" + (" · primitive" if feat.get("primitive") else "")
        lines.append(f"| {pn} | {name} | {cls} | {claimed}{' ⚠ over-claimed' if bad else ''} | **{g}** | {f} | {'; '.join(missing)} |")
    rep = "\n".join(lines) + "\n"
    if a.out:
        open(a.out, "w", encoding="utf-8").write(rep)
    if a.json:
        json.dump({"counts": counts, "build_ready": ready, "parts": results}, open(a.json, "w", encoding="utf-8"), indent=1)
    print(rep if not a.out else f"wrote {a.out}: {counts}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
