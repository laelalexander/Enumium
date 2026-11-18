"""Design basis for the Down Home Creole dry blending and packing plant.

Every number is tagged with where it came from:
  site       read from the client's factory site (data/site.json)
  documented a manufacturer page or datasheet (URL in equipment.py)
  assumed    Claude's assumption, to be confirmed by the client (listed in open_questions)
  calculated derived by the tools from the numbers above
Running this file writes design-basis.json.
"""
import json, pathlib

HERE = pathlib.Path(__file__).parent

BASIS = {
    "volume_option": "Growth",
    "daily_output_lb": {"v": 6000, "src": "client", "note": "client chose Growth on 2026-11-17 (launch=2,000, scale=20,000 not chosen)"},
    "shifts_per_day": {"v": 1, "src": "assumed"},
    "shift_hours": {"v": 8.0, "src": "assumed"},
    "days_per_week": {"v": 5, "src": "assumed"},
    "breaks_and_startup_min": {"v": 60, "src": "assumed", "note": "2 x 15 min breaks + 30 min start-up and pre-op inspection"},
    "end_of_shift_clean_min": {"v": 30, "src": "assumed", "note": "daily dry clean of the pack line, inside the shift"},
    "oee_target": {"v": 0.65, "src": "assumed", "note": "typical for a new small-batch spice line in year 1"},
    "weekly_output_lb": {"v": 30000, "src": "calculated"},
    "building": {"length_ft": 140, "width_ft": 90, "clear_height_ft": 22, "src": "assumed",
                 "note": "leased light-industrial unit; bulk bag frames need >= 20 ft clear"},
    "batch_rule": "batch size is set by the blender's working volume and the blend's bulk density, never above it",
    "blend_cv_spec_pct": {"v": 5, "src": "site"},
    "mix_time_min": {"v": 12, "src": "site"},
    "fill_overfill_pct": {"v": 1.5, "src": "assumed", "note": "site uses a target overfill; checkweigher rejects any unit under declared"},
    "fill_loss_pct": {"v": 1.0, "src": "site"},
    "lot_code": {"v": "DHyyjjj-B## + BEST BY", "src": "site"},
}

# Weekly demand by SKU family, share of weekly lb (assumed until the client gives sales forecasts).
# Within a family the lb split equally across its SKUs.
MIX = [
    # family, share, SKU ids
    ("Creole Chameleon 4 oz shakers", 0.22, ["s-orig-4s", "s-fire-4s", "s-lemp-4s", "s-garl-4s", "s-blkn-4s"]),
    ("Creole Chameleon 12 oz jars", 0.20, ["s-orig-12j", "s-fire-12j", "s-lemp-12j", "s-garl-12j", "s-blkn-12j"]),
    ("Creole Chameleon 12 oz pouch", 0.08, ["s-orig-12p"]),
    ("Food-service 5 lb tub", 0.10, ["s-orig-80t"]),
    ("Camilian + launch shakers", 0.25, ["s-caml-4s", "s-ncgb-2", "s-ncnc-4", "s-lyrb-4", "s-lthr-3", "s-ngrb-175", "s-vfrb-4", "s-efap-35"]),
    ("Boxed dry mixes (wheat)", 0.15, ["s-batter-16b", "s-ncpm-16", "s-afcb-20"]),
]

# Engineering change proposals that follow from the site data (tracked as ECOs, not silently applied)
ECO = [
    {"id": "ECO-001", "sku": "s-orig-12j", "from": "shaker-4 (235 mL)", "to": "jar-12 (700 mL PET, 89 mm sifter cap)",
     "why": "12 oz of a 0.548 g/mL blend needs ~620 mL; the 235 mL shaker is 264% of brimful (the site flags it too). "
            "The other four 12 oz Creole Chameleon SKUs already use jar-12, so this also removes a change part set.",
     "status": "proposed"},
    {"id": "ECO-002", "sku": "s-caml-4s, s-blkn-12j, s-lyrb-4", "from": "fill 93-95% of brimful", "to": "confirm headspace",
     "why": "auger-filled blends settle; above ~92% brimful a sifter-cap insert can push product out at capping. "
            "Pilot-fill 50 units each and measure; if it spills, move to shaker-320.", "status": "proposed"},
]

OPEN_QUESTIONS = [
    "Daily or yearly volume target (volume card): sized at 6,000 lb/day, one shift.",
    "Sales mix by SKU: the weekly split in MIX is an assumption.",
    "Building: size, clear height, dock doors, power service (sized for 480 V 3-phase, ~400 A).",
    "Whether sauces and canned goods (kettle, hot fill, retort) are in scope: left out of this line.",
]


def build():
    site = json.loads((HERE.parent / "data" / "site.json").read_text())
    skus = {s["id"]: s for s in site["skus"]}
    for e in ECO:
        if e["id"] == "ECO-001":
            s = skus["s-orig-12j"]; s.update(container="jar-12", closure="cap-89", label="lbl-12", format="JAR", eco="ECO-001")
            f = site["formulas"][s["formula"]]
            s["fill_pct_of_brimful"] = round(100 * s["net_g"] / f["blend_density"] / site["packaging"]["jar-12"]["brimful_ml"], 1)
    wk = BASIS["weekly_output_lb"]["v"] = BASIS["daily_output_lb"]["v"] * BASIS["days_per_week"]["v"]
    demand = []
    for fam, share, ids in MIX:
        for i in ids:
            s = skus[i]
            lb = wk * share / len(ids)
            g_unit = s["net_g"] * (1 + BASIS["fill_overfill_pct"]["v"] / 100)
            units = lb * 453.592 / g_unit
            demand.append(dict(sku=i, family=fam, weekly_lb=round(lb, 1), weekly_units=round(units),
                               weekly_cases=round(units / s["case_count"], 1), **{k: s[k] for k in
                               ("product", "formula", "format", "net_g", "container", "closure", "label", "case_count", "category", "fill_pct_of_brimful")}))
    return dict(basis=BASIS, mix=[dict(family=f, share=s, skus=i) for f, s, i in MIX], demand=demand, eco=ECO,
                open_questions=OPEN_QUESTIONS, site_source=site["source"], skus=list(skus.values()),
                formulas=site["formulas"], packaging=site["packaging"], ingredients=site["ingredients"])


if __name__ == "__main__":
    d = build()
    (HERE / "design-basis.json").write_text(json.dumps(d, indent=1))
    print(sum(x["weekly_units"] for x in d["demand"]), "units/week,", sum(x["weekly_cases"] for x in d["demand"]), "cases/week")
