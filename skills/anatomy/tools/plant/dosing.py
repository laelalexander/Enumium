"""Ingredient bin ("silo") assignment and per-product dosing plan (Anatomy plant toolkit).

Usage: python3 dosing.py design-basis.json line-balance.json dosing-config.json out_dir [growth-design-basis.json]

Decides which ingredients get their own bin with a metered feeder, and for every product works out how each
batch is built: which lines are dosed automatically from bins into the weigh hopper, which are hand-weighed,
and which go into the minors premix. Sizes each bin for its stock-holding time, gives the refill plan and the
feeder rate needed, and (with a growth basis) shows what the full range would need.

Rules (from the config):
  * an ingredient line is dosed from a bin only when its batch target >= min_dose_kg, which follows from the
    weigh-hopper resolution and the dosing tolerance: min_dose = 2 x accuracy / tolerance_frac;
  * lines under minor_pct % go to the hand-weighed premix (0.1 g scale) whatever their bin;
  * bins go to the ingredients with the most kg/week that can be bin-dosed; ties broken by how many products use it.
Writes dosing-plan.json and dosing-plan.md.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

LB = 0.453592
CUFT_L = 28.3168


def batches(basis, lbal):
    """(formula, batch_kg, batches_per_week) from the chosen blender in line-balance.json."""
    out = {}
    for r in lbal["blending"]["chosen"]["rows"]:
        out[r["formula"]] = dict(batch_kg=r["batch_lb"] * LB, per_week=r["batches"] / r.get("every_weeks", 1), name=r["name"])
    return out


def plan(basis, lbal, cfg):
    bt = batches(basis, lbal)
    acc = cfg["dose_accuracy_kg"]
    min_dose = cfg.get("min_dose_kg") or 2 * acc / cfg["dose_tolerance_frac"]
    minor = cfg["minor_pct"]
    lines = []
    for fid, b in bt.items():
        f = basis["formulas"][fid]
        for ing, pct in f["lines"].items():
            kg = b["batch_kg"] * pct / 100
            lines.append(dict(formula=fid, ingredient=ing, pct=pct, kg=kg, per_week=b["per_week"],
                              doseable=pct >= minor and kg >= min_dose))
    score = {}
    for l in lines:
        if l["doseable"]:
            s = score.setdefault(l["ingredient"], [0.0, set()])
            s[0] += l["kg"] * l["per_week"]; s[1].add(l["formula"])
    ranked = sorted(score.items(), key=lambda x: (-x[1][0], -len(x[1][1])))
    n = cfg["bin_positions"] - cfg.get("reserve_positions", 0)
    binned = [i for i, _ in ranked[:n]]
    not_binned = [i for i, _ in ranked[n:]]

    # recipes per product
    recipes = []
    for fid, b in bt.items():
        rows = []
        for l in [x for x in lines if x["formula"] == fid]:
            route = "BIN" if (l["doseable"] and l["ingredient"] in binned) else ("PREMIX" if l["pct"] < minor else "HAND")
            rows.append(dict(ingredient=l["ingredient"], pct=l["pct"], kg=round(l["kg"], 3), route=route,
                             bin=f"B{binned.index(l['ingredient']) + 1:02d}" if route == "BIN" else "",
                             tol_kg=round(max(l["kg"] * (cfg["dose_tolerance_frac"] if route != "PREMIX" else cfg["premix_tolerance_frac"]),
                                              acc if route == "BIN" else 0), 3)))
        rows.sort(key=lambda r: ("BIN", "HAND", "PREMIX").index(r["route"]) * 1000 - r["kg"])
        auto = sum(r["kg"] for r in rows if r["route"] == "BIN")
        recipes.append(dict(formula=fid, name=b["name"], batch_kg=round(b["batch_kg"], 2), batches_per_week=b["per_week"], lines=rows,
                            auto_pct=round(100 * auto / b["batch_kg"], 1),
                            hand_lines=sum(1 for r in rows if r["route"] == "HAND"), premix_lines=sum(1 for r in rows if r["route"] == "PREMIX"),
                            sequence=[r["bin"] for r in rows if r["route"] == "BIN"]))

    # bins: size and refill
    bin_l = cfg["bin_cuft"] * CUFT_L * cfg["bin_fill_frac"]
    bins = []
    for k, ing in enumerate(binned):
        dens = basis["ingredients"][ing]["density"]
        wk_kg = sum(l["kg"] * l["per_week"] for l in lines if l["ingredient"] == ing and l["doseable"])
        wk_l = wk_kg / dens
        cap_kg = bin_l * dens
        max_dose = max(l["kg"] for l in lines if l["ingredient"] == ing and l["doseable"])
        rate_l_h = max_dose / dens / (cfg["dose_time_min"] / 60)
        feeder = next((f for f in cfg["feeders"] if max_dose / dens / (f["max_l_h"] * 0.8) * 60 <= cfg.get("max_dose_min", cfg["dose_time_min"])),
                      cfg["feeders"][-1])
        dose_min = max_dose / dens / (feeder["max_l_h"] * 0.8) * 60
        flow = basis["ingredients"][ing].get("flow") or ("poor" if dens < 0.3 else "fair" if dens < 0.5 else "good")
        bins.append(dict(bin=f"B{k + 1:02d}", ingredient=ing, name=basis["ingredients"][ing]["name"], density=dens,
                         weekly_kg=round(wk_kg, 1), weekly_l=round(wk_l, 1), capacity_kg=round(cap_kg, 1),
                         days_of_stock=round(cap_kg / wk_kg * cfg["days_per_week"], 1) if wk_kg else None,
                         refills_per_week=round(wk_kg / cap_kg, 2), bags_per_refill=round(cap_kg / cfg["bag_kg"], 1),
                         max_dose_kg=round(max_dose, 2), rate_l_h=round(rate_l_h, 1), feeder=feeder["name"], dose_min=round(dose_min, 1),
                         flow=flow, agitator=flow != "good",
                         products=sorted(score[ing][1])))
    spare = cfg["bin_positions"] - len(bins)
    return dict(min_dose_kg=round(min_dose, 2), dose_accuracy_kg=acc, bin_positions=cfg["bin_positions"], spare_positions=spare,
                bins=bins, not_binned_but_doseable=not_binned, recipes=recipes,
                auto_pct_overall=round(100 * sum(r["auto_pct"] / 100 * r["batch_kg"] * r["batches_per_week"] for r in recipes)
                                        / sum(r["batch_kg"] * r["batches_per_week"] for r in recipes), 1))


def md(p, growth=None):
    L = ["# Ingredient bins and dosing plan", "",
         f"Dosed from a bin when the batch target is at least **{p['min_dose_kg']} kg** "
         f"(weigh-hopper accuracy {p['dose_accuracy_kg'] * 1000:.0f} g at the dosing tolerance). "
         f"**{p['auto_pct_overall']} %** of all blend weight is dosed automatically. "
         f"{len(p['bins'])} of {p['bin_positions']} bin positions are used, so **{p['spare_positions']}** are spare.", "",
         "## Bins", "", "| Bin | Ingredient | kg/week | Capacity kg | Days of stock | Refills/week | Bags (25 kg) per refill | Max dose kg | Feeder | Longest dose min | Flow aid | Products |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {b['bin']} | {b['name']} | {b['weekly_kg']} | {b['capacity_kg']} | {b['days_of_stock']} | {b['refills_per_week']} | {b['bags_per_refill']} | "
          f"{b['max_dose_kg']} | {b['feeder']} | {b['dose_min']} | {'agitator' if b['agitator'] else '-'} | {len(b['products'])} |" for b in p["bins"]]
    if p["not_binned_but_doseable"]:
        L += ["", f"Doseable but no bin position left (hand-weighed): {', '.join(p['not_binned_but_doseable'])}."]
    L += ["", "## Recipe per product (one batch)", ""]
    for r in p["recipes"]:
        L += [f"### {r['name']} ({r['formula']}): {r['batch_kg']} kg batch, {r['batches_per_week']:g}/week, {r['auto_pct']} % auto-dosed", "",
              "| Ingredient | % | kg | Route | Bin | Tolerance kg |", "|---|---|---|---|---|---|"]
        L += [f"| {x['ingredient']} | {x['pct']} | {x['kg']} | {x['route']} | {x['bin']} | ±{x['tol_kg']} |" for x in r["lines"]]
        L += ["", f"Dosing order: {' > '.join(r['sequence'])}, then the hand adds, then the premix last.", ""]
    if growth:
        L += ["## Growth to the full range", "",
              f"With every product running, the same rules use **{len(growth['bins'])}** bins "
              f"({', '.join(b['ingredient'] for b in growth['bins'])}); "
              f"{'it fits the bank.' if growth['spare_positions'] >= 0 else 'add positions.'} "
              f"Auto-dosed share {growth['auto_pct_overall']} %.", ""]
        if growth["not_binned_but_doseable"]:
            L += [f"Would still be hand-weighed for lack of positions: {', '.join(growth['not_binned_but_doseable'])}.", ""]
    L += ["## Lot traceability for bins", "",
          "A bin mixes lots when it is topped up. The MES records every lot poured into a bin, and a batch dosed from that bin is traced to "
          "every lot present since the bin was last run empty. Run each bin empty at least once a week, at the low-level switch, to keep that set small."]
    return "\n".join(L) + "\n"


def main(a):
    basis, lbal, cfg = (json.loads(Path(x).read_text()) for x in a[:3])
    out = Path(a[3]); out.mkdir(parents=True, exist_ok=True)
    p = plan(basis, lbal, cfg)
    g = None
    if len(a) > 4:
        gb = json.loads(Path(a[4]).read_text())
        gl = json.loads(Path(a[5]).read_text()) if len(a) > 5 else lbal
        g = plan(gb, gl, cfg)
        p["growth"] = {k: g[k] for k in ("bins", "spare_positions", "not_binned_but_doseable", "auto_pct_overall")}
    (out / "dosing-plan.json").write_text(json.dumps(p, indent=1))
    (out / "dosing-plan.md").write_text(md(p, g))
    print(f"{len(p['bins'])} bins used of {p['bin_positions']}; auto-dosed {p['auto_pct_overall']} %; min dose {p['min_dose_kg']} kg")
    for b in p["bins"]:
        print(f"  {b['bin']} {b['ingredient']:<20} {b['weekly_kg']:>6} kg/wk  stock {b['days_of_stock']} d  {b['feeder']}")
    if g:
        print(f"growth: {len(g['bins'])} bins, spare {g['spare_positions']}, auto {g['auto_pct_overall']} %")


if __name__ == "__main__":
    main(sys.argv[1:])
