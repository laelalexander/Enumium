"""Line-rate balancing for batch + packaging plants (Anatomy plant tools).

Reads a project's design-basis.json (demand by SKU, formulas with bulk density) and a line config
(stations, rated speeds, cycle and changeover times) and answers:
  * available minutes per week, per area
  * blender sizing: batch size set by working volume x bulk density, batches per week, utilization
    for each candidate blender size, and the smallest size that fits under the utilization limit
  * pack lines: run time per SKU at rated speed and target OEE, changeovers from a sequenced
    weekly campaign (container groups, light to dark, allergens last), utilization
  * every station's required rate at line speed vs its rated rate, the bottleneck and the margin
  * a weekly campaign schedule (which batch and which SKU run on which day)

Usage: python linebal.py design-basis.json linebal-config.json out_dir
Writes line-balance.json and line-balance.md. Pure Python, no dependencies.
"""
import json, math, pathlib, sys

LB_PER_CUFT_PER_GML = 62.428


def avail_min(b):
    per_shift = b["shift_hours"]["v"] * 60 - b["breaks_and_startup_min"]["v"] - b["end_of_shift_clean_min"]["v"]
    return per_shift * b["shifts_per_day"]["v"], per_shift * b["shifts_per_day"]["v"] * b["days_per_week"]["v"]


def blend_campaign(basis, cfg, working_cuft):
    """Weekly blending plan for one blender size. Returns batches, minutes, utilization."""
    bl = cfg["blending"]
    by_f = {}
    for d in basis["demand"]:
        by_f.setdefault(d["formula"], 0.0)
        by_f[d["formula"]] += d["weekly_lb"]
    rows = []
    for fid, lb in by_f.items():
        f = basis["formulas"][fid]
        cap = working_cuft * f["blend_density"] * LB_PER_CUFT_PER_GML * bl["max_fill_frac"]
        lo = working_cuft * f["blend_density"] * LB_PER_CUFT_PER_GML * bl["min_fill_frac"]
        n = max(1, math.ceil(lb / cap))
        size = lb / n
        under = size < lo                      # too small to blend well in this size: flag it
        charge = size / bl["charge_lb_per_min"] + bl["premix_add_min"]
        discharge = size / bl["sift_lb_per_min"]
        cyc = charge + bl["mix_min"] + discharge + bl["sample_min"]
        rows.append(dict(formula=fid, name=f["name"], allergens=f["allergens"], density=f["blend_density"], weekly_lb=round(lb, 1),
                         max_batch_lb=round(cap), batches=n, batch_lb=round(size, 1), below_min_fill=under,
                         cycle_min=round(cyc, 1), week_min=round(cyc * n, 1)))
    # sequence: non-allergen light colors first (by density as a proxy is wrong; use configured order), allergen last
    order = {k: i for i, k in enumerate(cfg.get("color_order", []))}
    rows.sort(key=lambda r: (bool(r["allergens"]), order.get(r["formula"], 99)))
    # campaign frequency: low-volume formulas are blended every N weeks, so their changeovers count 1/N per week
    every = bl.get("campaign_every_weeks_if_lb_below", [0, 1])
    for r in rows:
        r["every_weeks"] = every[1] if r["weekly_lb"] < every[0] else 1
    co = 0.0
    for i in range(1, len(rows)):
        prev, cur = rows[i - 1], rows[i]
        # in the planned light-to-dark order a short purge is enough; an allergen boundary needs a full dry clean
        step = bl["dry_clean_min"] if prev["allergens"] != cur["allergens"] else bl.get("sequence_purge_min", bl["dry_clean_min"])
        co += step / cur["every_weeks"]
    if any(r["allergens"] for r in rows) and not bl.get("wet_clean_outside_shift", False):
        co += bl["wet_clean_after_allergen_min"]          # wet clean + dry before the next week's gluten-free run
    run = sum(r["week_min"] for r in rows)
    return dict(working_cuft=working_cuft, rows=rows, run_min=round(run, 1), changeover_min=round(co, 1),
                batches=sum(r["batches"] for r in rows), under_filled=[r["formula"] for r in rows if r["below_min_fill"]])


def pack_line(basis, line, oee, cfg):
    rows = [d for d in basis["demand"] if d["format"] in line["formats"]]
    order = {k: i for i, k in enumerate(line.get("container_order", []))}
    rows.sort(key=lambda d: (bool(basis["formulas"][d["formula"]]["allergens"]), order.get(d["container"], 99), d["formula"]))
    out, co, prev = [], 0.0, None
    for d in rows:
        rated = line["rated_upm"][d["format"]]
        # run time at rated speed x (performance x quality); unplanned stops added on top; changeovers counted explicitly
        run = d["weekly_units"] / (rated * cfg.get("rate_factor", oee)) * (1 + cfg.get("unplanned_downtime_frac", 0))
        every = line.get("campaign_every_weeks_if_units_below", [0, 1])
        n = every[1] if d["weekly_units"] < every[0] else 1
        if prev:
            step = line["product_change_min"]
            if prev["container"] != d["container"]:
                step += line["container_change_min"]
            if basis["formulas"][prev["formula"]]["allergens"] != basis["formulas"][d["formula"]]["allergens"]:
                step += line.get("allergen_change_min", 0)
            co += step / n
        out.append(dict(sku=d["sku"], format=d["format"], container=d["container"], formula=d["formula"], units=d["weekly_units"],
                        cases=d["weekly_cases"], rated_upm=rated, run_min=round(run, 1), every_weeks=n))
        prev = d
    run = sum(r["run_min"] for r in out)
    return dict(name=line["name"], rows=out, run_min=round(run, 1), changeover_min=round(co, 1))


def station_check(line, peak_upm, case_count_min):
    res = []
    peak_cpm = peak_upm / case_count_min
    for st in line["stations"]:
        need = peak_upm if st["unit"] == "upm" else peak_cpm
        res.append(dict(tag=st["tag"], name=st["name"], unit=st["unit"], need=round(need, 2), rated=st["rated"],
                        load=round(need / st["rated"], 2), src=st.get("src", "")))
    res.sort(key=lambda r: -r["load"])
    return res


def run(basis_path, cfg_path, out_dir):
    basis = json.loads(pathlib.Path(basis_path).read_text())
    cfg = json.loads(pathlib.Path(cfg_path).read_text())
    b = basis["basis"]
    day_min, week_min = avail_min(b)
    oee = b["oee_target"]["v"]
    limit = cfg.get("utilization_limit", 0.85)
    # ---- blending
    cands = [blend_campaign(basis, cfg, c) for c in cfg["blending"]["candidate_working_cuft"]]
    for c in cands:
        c["utilization"] = round((c["run_min"] + c["changeover_min"]) / week_min, 3)
    fits = [c for c in cands if c["utilization"] <= limit and not c["under_filled"]]
    chosen = min(fits, key=lambda c: c["working_cuft"]) if fits else max(cands, key=lambda c: c["working_cuft"])
    pick = cfg["blending"].get("choose_cuft")          # designer override (e.g. fewer batches for a manual plant), stated in notes
    if pick:
        chosen = next(c for c in cands if c["working_cuft"] == pick)
    # ---- pack lines
    lines = []
    for ln in cfg["pack_lines"]:
        p = pack_line(basis, ln, oee, cfg)
        p["utilization"] = round((p["run_min"] + p["changeover_min"]) / week_min, 3)
        peak = max(ln["rated_upm"].values())
        cc = min(r["cases"] and basis_case(basis, r["sku"]) for r in p["rows"]) if p["rows"] else 12
        p["stations"] = station_check(ln, peak, cc) if ln.get("stations") else []
        p["bottleneck"] = p["stations"][0] if p["stations"] else None
        lines.append(p)
    # ---- weekly schedule: fill days in campaign order
    sched = schedule(chosen, lines, day_min, b["days_per_week"]["v"], cfg)
    res = dict(available=dict(min_per_day=day_min, min_per_week=week_min, oee=oee, utilization_limit=limit),
               weekly_lb=sum(d["weekly_lb"] for d in basis["demand"]), weekly_units=sum(d["weekly_units"] for d in basis["demand"]),
               blending=dict(candidates=[{k: v for k, v in c.items() if k != "rows"} for c in cands], chosen=chosen), pack_lines=lines,
               schedule=sched, notes=cfg.get("notes", []))
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "line-balance.json").write_text(json.dumps(res, indent=1))
    (out / "line-balance.md").write_text(report(res, cfg))
    return res


def basis_case(basis, sku):
    for d in basis["demand"]:
        if d["sku"] == sku:
            return d["case_count"]
    return 12


def schedule(blend, lines, day_min, days, cfg):
    """Greedy weekly campaign: blending runs a day ahead of packing (QC release), allergen formulas last."""
    out = {"blending": [[] for _ in range(days)]}
    d, t = 0, 0.0
    for r in blend["rows"]:
        for k in range(r["batches"]):
            need = r["cycle_min"] + (cfg["blending"]["dry_clean_min"] if k == 0 else 0)
            if t + need > day_min and d < days - 1:
                d, t = d + 1, 0.0
            out["blending"][d].append(f'{r["formula"]} #{k + 1} ({r["batch_lb"]:.0f} lb)')
            t += need
    for p in lines:
        key = p["name"]; out[key] = [[] for _ in range(days)]
        d, t = 0, 0.0
        for r in p["rows"]:
            left = r["run_min"]
            while left > 0:
                room = day_min - t
                if room <= 1:
                    if d == days - 1:
                        out[key][d].append(f'{r["sku"]} OVERFLOW {left:.0f} min'); break
                    d, t = d + 1, 0.0; continue
                use = min(room, left)
                out[key][d].append(f'{r["sku"]} {use:.0f} min')
                t += use + 0; left -= use
            t += cfg["changeover_in_schedule_min"]
    return out


def report(r, cfg):
    a = r["available"]; c = r["blending"]["chosen"]
    L = ["# Line balance", "",
         f"Available time: {a['min_per_day']:.0f} min/day, {a['min_per_week']:.0f} min/week (after breaks, start-up and daily clean). "
         f"Run time uses rated speed x {cfg.get('rate_factor', a['oee'])} (performance x quality) plus {cfg.get('unplanned_downtime_frac', 0):.0%} unplanned stops; "
         f"changeovers are counted separately. Utilization limit {a['utilization_limit']:.0%}.", "",
         f"Weekly demand: {r['weekly_lb']:,.0f} lb, {r['weekly_units']:,} units.", "",
         "## Blender size", "", "| Working cu ft | Batches/week | Run min | Changeover min | Utilization | Under-filled formulas |", "|---|---|---|---|---|---|"]
    for k in r["blending"]["candidates"]:
        L.append(f"| {k['working_cuft']} | {k['batches']} | {k['run_min']:.0f} | {k['changeover_min']:.0f} | {k['utilization']:.0%} | {', '.join(k['under_filled']) or '-'} |")
    L += ["", f"**Chosen: {c['working_cuft']} cu ft working volume** ({c['batches']} batches/week).", "",
          "| Formula | Density g/mL | Weekly lb | Max batch lb | Batches | Batch lb | Cycle min | Campaign |", "|---|---|---|---|---|---|---|---|"]
    for x in c["rows"]:
        L.append(f"| {x['name']} | {x['density']} | {x['weekly_lb']:,.0f} | {x['max_batch_lb']:,} | {x['batches']} | {x['batch_lb']:,.0f} | {x['cycle_min']} | every {x['every_weeks']} wk |")
    for p in r["pack_lines"]:
        L += ["", f"## {p['name']}", "", f"Run {p['run_min']:.0f} min + changeovers {p['changeover_min']:.0f} min = utilization **{p['utilization']:.0%}**.", ""]
        if p["stations"]:
            L += ["| Station | Need at line speed | Rated | Load | Source |", "|---|---|---|---|---|"]
            for s in p["stations"]:
                L.append(f"| {s['tag']} {s['name']} | {s['need']} {s['unit']} | {s['rated']} {s['unit']} | {s['load']:.0%} | {s['src']} |")
            L += ["", f"Bottleneck at line speed: **{p['bottleneck']['tag']}** ({p['bottleneck']['load']:.0%} loaded)."]
        L += ["", "| SKU | Container | Units/week | Rated upm | Run min | Campaign |", "|---|---|---|---|---|---|"]
        for x in p["rows"]:
            L.append(f"| {x['sku']} | {x['container']} | {x['units']:,} | {x['rated_upm']} | {x['run_min']} | every {x['every_weeks']} wk |")
    L += ["", "## Weekly campaign", ""]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for area, ds in r["schedule"].items():
        L.append(f"**{area}**"); L.append("")
        for i, items in enumerate(ds):
            L.append(f"- {days[i]}: " + ("; ".join(items) if items else "-"))
        L.append("")
    L += ["## Notes", ""] + [f"- {n}" for n in r["notes"]]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    res = run(*sys.argv[1:])
    c = res["blending"]["chosen"]
    print("blender", c["working_cuft"], "cu ft:", c["batches"], "batches, util", c["utilization"])
    for p in res["pack_lines"]:
        print(p["name"], "util", p["utilization"], "bottleneck", p["bottleneck"]["tag"] if p["bottleneck"] else "-")
