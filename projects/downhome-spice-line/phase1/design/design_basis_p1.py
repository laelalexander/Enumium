"""Phase 1 prototype design basis: 1,000 lb a week, semi-automatic, smallest footprint.

Reuses the Growth design basis (../../design/design_basis.py) and the site data, and overrides
volume, shifts and scope. Running it writes design-basis.json for the Phase 1 tools.
Scope (client 2026-11-17): blended seasonings only, no wheat mixes. Launch with 5 blends (the Creole
Chameleon line, assumed until the client names them); the plant is laid out to grow to all 13 seasonings.
Run with "all13" to size for the full seasoning range: python3 design_basis_p1.py all13
"""
import copy, json, pathlib, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "design"))
import design_basis as G  # noqa: E402

WHEAT = False
SET = sys.argv[1] if len(sys.argv) > 1 else "launch5"
LAUNCH5 = {"Creole Chameleon 4 oz shakers", "Creole Chameleon 12 oz jars", "Creole Chameleon 12 oz pouch", "Food-service 5 lb tub"}
B = copy.deepcopy(G.BASIS)
B.update({
    "volume_option": "Phase 1 prototype",
    "daily_output_lb": {"v": 200, "src": "client", "note": "client asked 2026-11-17 for 1,000 lb/week as a phase 1 prototype"},
    "days_per_week": {"v": 5, "src": "assumed", "note": "work is batched into 2-3 production days; the rest is receiving, QC and cleaning"},
    "oee_target": {"v": 0.5, "src": "assumed", "note": "semi-automatic, operator-paced"},
    "building": {"length_ft": 50, "width_ft": 40, "clear_height_ft": 12, "src": "assumed",
                 "note": "about 2,000 sq ft light-industrial or food-grade unit; no bulk bags, so no high clear height"},
    "batch_rule": "batch = blender working volume x bulk density, never above; min 35 % fill",
})
MIX = [m for m in G.MIX if (WHEAT or "wheat" not in m[0].lower()) and (SET == "all13" or m[0] in LAUNCH5)]
tot = sum(m[1] for m in MIX)
MIX = [(f, s / tot, ids) for f, s, ids in MIX]

G.BASIS.clear(); G.BASIS.update(B)
G.MIX[:] = MIX
G.OPEN_QUESTIONS[:] = [
    "Which 5 blends launch first: assumed Original, Fire, Lemon Pepper, Garlic Herb, Blackened.",
    "Sales mix by SKU: the weekly split is the Growth assumption scaled down.",
    "Space: about 2,000 sq ft with a 3-phase or 240 V 1-phase service (Phase 1 needs ~60 A at 240 V).",
    "Who fabricates: the stainless tables and hoods are TIG-welded 304; a local food-equipment fabricator if not in-house.",
]

if __name__ == "__main__":
    d = G.build()
    d["phase"] = f"Phase 1 prototype ({SET})"
    (HERE / ("design-basis.json" if SET == "launch5" else f"design-basis-{SET}.json")).write_text(json.dumps(d, indent=1))
    u = sum(x["weekly_units"] for x in d["demand"]); c = sum(x["weekly_cases"] for x in d["demand"])
    print(round(u), "units/week,", round(c), "cases/week,", len({x['formula'] for x in d['demand']}), "formulas,", len(d["demand"]), "SKUs")
