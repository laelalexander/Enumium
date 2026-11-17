"""Food-safety design checks for a dry food plant (Anatomy plant toolkit).

Usage: python3 foodsafety.py design-basis.json equipment.json layout.json foodsafety-config.json out_dir

Reads the design and writes food-safety.json and food-safety.md with:
  1. Allergen matrix: formula x allergen, and which machines each allergen touches.
  2. Shared-equipment risks: any product-contact machine that runs both allergen and
     allergen-free formulas, and any free-from claim (e.g. gluten-free) it puts at risk.
  3. Zoning check: every product-contact machine sits in an exposed-product zone; allergen
     machines sit in the allergen zone or are on the shared list with a validated clean.
  4. Sanitary check: every product-contact machine states its sanitary construction.
  5. Combustible dust: pickups summed against the collector design airflow, NFPA 61/652 items.
  6. HACCP plan table and the sanitation (SSOP) schedule from the config.
Exit code 1 if any check fails, so a build can stop on it.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def run(basis, equipment, layout, cfg):
    eq = {e["tag"]: e for e in equipment}
    room_zone = {r["name"]: r["zone"] for r in layout["rooms"]}
    placed = {p["tag"]: p["room"] for p in layout["equipment"]}
    formulas = basis["formulas"]
    checks, issues = [], []

    # 1. allergen matrix
    allergens = sorted({a.lower() for f in formulas.values() for a in f.get("allergens", [])})
    matrix = [{"formula": k, "name": f["name"], **{a: (a in [x.lower() for x in f.get("allergens", [])]) for a in allergens}}
              for k, f in formulas.items()]

    # which equipment each formula family uses (from config routes)
    routes = cfg["routes"]          # {"allergen-free": [tags], "wheat": [tags]}
    touched = defaultdict(set)
    for fam, tags in routes.items():
        for t in tags:
            touched[t].add(fam)

    # 2. shared equipment
    shared = []
    for t, fams in sorted(touched.items()):
        if len(fams) > 1 and eq.get(t, {}).get("product_contact"):
            clean = cfg["validated_cleans"].get(t)
            shared.append({"tag": t, "name": eq[t]["name"], "families": sorted(fams), "control": clean or "NONE"})
            if not clean:
                issues.append(f"{t} is shared by {sorted(fams)} with no validated allergen clean")
    claims = []
    for c in cfg.get("claims", []):
        at_risk = [s["tag"] for s in shared if c["allergen"] in s["families"]]
        claims.append({**c, "shared_equipment": at_risk,
                       "status": "AT RISK: needs validated clean + finished-product test" if at_risk else "protected by separation"})

    # 3. zoning
    zone_rows = []
    for t, e in eq.items():
        if not e.get("product_contact"):
            continue
        room = placed.get(t)
        zone = room_zone.get(room, "not placed")
        ok = zone.startswith("Z3")
        fams = touched.get(t, set())
        if "wheat" in fams and fams == {"wheat"} and not zone.startswith("Z3A"):
            ok = False
        zone_rows.append({"tag": t, "room": room, "zone": zone, "families": sorted(fams), "ok": ok})
        if not ok:
            issues.append(f"{t} product-contact machine in {zone} ({room})")
    checks.append(("zoning", all(r["ok"] for r in zone_rows)))

    # 4. sanitary construction stated
    san_rows = [{"tag": t, "sanitary": e.get("sanitary") or ""} for t, e in eq.items() if e.get("product_contact")]
    missing = [r["tag"] for r in san_rows if len(r["sanitary"]) < 8]
    for t in missing:
        issues.append(f"{t} has no sanitary construction note")
    checks.append(("sanitary", not missing))

    # 5. dust
    pickups = [{"tag": t, "cfm": e["dust_cfm"], "qty": e.get("qty", 1)} for t, e in eq.items() if e.get("dust_cfm")]
    total = sum(p["cfm"] * p["qty"] for p in pickups)
    coll = eq.get(cfg["dust"]["collector"], {})
    design = (coll.get("specs") or {}).get("design_cfm", 0)
    margin = cfg["dust"]["margin"]
    dust_ok = design >= total * (1 + margin) - 1
    if not dust_ok:
        issues.append(f"{cfg['dust']['collector']} design {design} cfm < pickups {total} cfm + {margin:.0%}")
    checks.append(("dust_airflow", dust_ok))
    checks.append(("shared_equipment_controlled", all(s["control"] != "NONE" for s in shared)))

    return {
        "allergens": allergens, "matrix": matrix, "shared_equipment": shared, "claims": claims,
        "zoning": zone_rows, "sanitary": san_rows,
        "dust": {"pickups": pickups, "total_cfm": total, "collector": cfg["dust"]["collector"], "design_cfm": design,
                 "margin": margin, "ok": dust_ok, "nfpa": cfg["dust"]["nfpa_items"]},
        "haccp": cfg["haccp"], "ssop": cfg["ssop"], "prerequisites": cfg.get("prerequisites", []),
        "checks": [{"check": c, "pass": p} for c, p in checks], "issues": issues,
    }


def md(r):
    L = ["# Food-safety design check", ""]
    L += ["| Check | Result |", "|---|---|"] + [f"| {c['check']} | {'PASS' if c['pass'] else 'FAIL'} |" for c in r["checks"]]
    if r["issues"]:
        L += ["", "**Issues**", ""] + [f"- {i}" for i in r["issues"]]
    L += ["", "## Allergen matrix", "", "| Formula | Name | " + " | ".join(r["allergens"]) + " |",
          "|---|---|" + "---|" * len(r["allergens"])]
    L += [f"| {m['formula']} | {m['name']} | " + " | ".join("X" if m[a] else "" for a in r["allergens"]) + " |" for m in r["matrix"]]
    L += ["", "## Shared product-contact equipment", "", "| Tag | Machine | Families | Control |", "|---|---|---|---|"]
    L += [f"| {s['tag']} | {s['name']} | {', '.join(s['families'])} | {s['control']} |" for s in r["shared_equipment"]]
    L += ["", "## Claims", ""] + [f"- **{c['claim']}** ({c['applies_to']}): {c['status']}"
                                   + (f"; shared: {', '.join(c['shared_equipment'])}" if c["shared_equipment"] else "") + f". {c.get('action', '')}" for c in r["claims"]]
    L += ["", "## Hygiene zoning of product-contact machines", "", "| Tag | Room | Zone | OK |", "|---|---|---|---|"]
    L += [f"| {z['tag']} | {z['room']} | {z['zone']} | {'yes' if z['ok'] else 'NO'} |" for z in r["zoning"]]
    d = r["dust"]
    L += ["", "## Combustible dust", "", f"Pickups total **{d['total_cfm']} cfm**; {d['collector']} design **{d['design_cfm']} cfm** "
          f"(needs {d['margin']:.0%} margin): {'OK' if d['ok'] else 'UNDERSIZED'}.", "",
          "| Pickup | cfm | qty |", "|---|---|---|"] + [f"| {p['tag']} | {p['cfm']} | {p['qty']} |" for p in d["pickups"]]
    L += [""] + [f"- {n}" for n in d["nfpa"]]
    L += ["", "## HACCP plan", "", "| CCP | Step | Hazard | Critical limit | Monitoring | Corrective action | Verification | Records |",
          "|---|---|---|---|---|---|---|---|"]
    L += [f"| {h['ccp']} | {h['step']} | {h['hazard']} | {h['limit']} | {h['monitor']} | {h['correct']} | {h['verify']} | {h['records']} |" for h in r["haccp"]]
    L += ["", "## Prerequisite programs (not CCPs)", ""] + [f"- {p}" for p in r["prerequisites"]]
    L += ["", "## Sanitation schedule (SSOP)", "", "| Task | When | Method | Verify | Who |", "|---|---|---|---|---|"]
    L += [f"| {s['task']} | {s['when']} | {s['method']} | {s['verify']} | {s['who']} |" for s in r["ssop"]]
    return "\n".join(L) + "\n"


def main(a):
    basis, equipment, layout, cfg = (json.loads(Path(p).read_text()) for p in a[:4])
    out = Path(a[4]); out.mkdir(parents=True, exist_ok=True)
    r = run(basis, equipment, layout, cfg)
    (out / "food-safety.json").write_text(json.dumps(r, indent=1))
    (out / "food-safety.md").write_text(md(r))
    for c in r["checks"]:
        print(f"{c['check']:<30} {'PASS' if c['pass'] else 'FAIL'}")
    for i in r["issues"]:
        print("  -", i)
    return 0 if all(c["pass"] for c in r["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
