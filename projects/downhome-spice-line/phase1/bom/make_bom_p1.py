"""Phase 1 BOM, fabrication list, cost comparison with the Growth plant and the carry-over list.
Usage: python3 make_bom_p1.py   ->  phase1-bom.csv, phase1-bom.xlsx, phase1-cost.md
"""
import csv
import json
import pathlib
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = pathlib.Path(__file__).parent
P1 = HERE.parent
EQ = json.loads((P1 / "design" / "equipment.json").read_text())
GROWTH = json.loads((P1.parent / "design" / "equipment.json").read_text())
PARTS = {p["id"]: p for p in json.loads((P1 / "cad" / "parts.json").read_text())}
DOSING = json.loads((P1 / "design" / "out" / "dosing-plan.json").read_text())

COLS = ["tag", "area", "kind", "name", "maker", "model", "qty", "qty_basis", "unit_usd", "ext_usd", "price_src", "supplier", "source",
        "power", "dust_cfm", "product_contact", "sanitary", "growth_equiv", "reuse_in_growth", "confirm"]
HEAD = PatternFill("solid", fgColor="3E2723")


def growth_ext(e):
    p = e.get("price") or {}
    u = p.get("usd", 0) or 0
    return u * e["qty"] if p.get("per") else u


def rows():
    for e in EQ:
        p = e.get("price") or {}
        yield dict(tag=e["tag"], area=e["area"], kind=e["kind"].upper(), name=e["name"], maker=e["maker"], model=e["model"], qty=e["qty"],
                   qty_basis=e["qty_basis"], unit_usd=round(e["ext_usd"] / e["qty"], 2), ext_usd=e["ext_usd"], price_src=p.get("src", ""),
                   supplier=e["supplier"], source=e["source"], power=e.get("power") or "", dust_cfm=e.get("dust_cfm") or 0,
                   product_contact="yes" if e.get("product_contact") else "", sanitary=e.get("sanitary") or "",
                   growth_equiv=e.get("growth_equiv") or "", reuse_in_growth="yes" if e.get("reuse_in_growth") else "", confirm=e.get("confirm") or "")


def fab_rows():
    for e in EQ:
        if e["kind"] != "build":
            continue
        b = e["build"]
        files = []
        for f in b.get("files") or []:
            stem = pathlib.Path(f).name
            for cand in (f"dxf/{stem}_mm.dxf", f"dxf/{stem}_in.dxf", f"cad/step/{stem}.step", f"drawings/parts/{stem}.svg"):
                if (P1 / cand).exists():
                    files.append(cand)
            if f == "cad/print":
                files += [f"cad/print/{x.name}" for x in sorted((P1 / "cad" / "print").glob("*.stl"))]
        tag = e["tag"]
        if tag in PARTS:
            for k in ("step", "drawing"):
                if PARTS[tag].get(k) and PARTS[tag][k] not in files:
                    files.append(PARTS[tag][k])
        yield dict(tag=tag, name=e["name"], qty=e["qty"], material=b["material"], material_usd=b["material_usd"], labor_h=b["labor_h"],
                   process=b["process"], ext_usd=e["ext_usd"], mass_kg=PARTS.get(tag, {}).get("mass_kg", ""),
                   files="; ".join(dict.fromkeys(files)) or "MISSING: no model yet (fabricate from the equipment note)")


def sheet(wb, title, cols, data, widths=None, money=()):
    ws = wb.create_sheet(title)
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = HEAD; c.alignment = Alignment(wrap_text=True, vertical="top")
    for r in data:
        ws.append([r.get(c, "") if isinstance(r, dict) else r[i] for i, c in enumerate(cols)])
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(c, 14)
        if c in money:
            for cell in ws[get_column_letter(i)][1:]:
                cell.number_format = '"$"#,##0'
    ws.freeze_panes = "A2"
    return ws


def main():
    data = list(rows())
    fabs = list(fab_rows())
    with open(HERE / "phase1-bom.csv", "w", newline="") as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(data)

    buy = sum(r["ext_usd"] for r in data if r["kind"] == "BUY")
    build = sum(r["ext_usd"] for r in data if r["kind"] == "BUILD")
    g_total = sum(growth_ext(e) for e in GROWTH)
    by_area = defaultdict(lambda: [0.0, 0.0])
    for r in data:
        by_area[r["area"]][0 if r["kind"] == "BUY" else 1] += r["ext_usd"]
    reuse = [r for r in data if r["reuse_in_growth"]]
    labor = sum(f["labor_h"] for f in fabs)
    mat = sum(f["material_usd"] for f in fabs)
    # what fabricating saves: the same items bought from an OEM, at a typical 2.5 x shop price (stated assumption)
    oem_equiv = build * 2.5

    wb = Workbook(); wb.remove(wb.active)
    ws = wb.create_sheet("Summary")
    for row in [["Down Home Creole Phase 1 prototype: 1,000 lb/week, 5 launch blends, laid out for 13"], [],
                ["Bought equipment", buy], ["Fabricated in house (material + labor at $65/h)", build], ["Phase 1 total", buy + build], [],
                ["Fabrication material", mat], ["Fabrication labor hours", labor], ["Same fabricated items bought from an OEM (2.5 x estimate)", oem_equiv],
                ["Saved by fabricating (estimate)", oem_equiv - build], [],
                ["Growth plant (6,000 lb/day) equipment total", g_total], ["Phase 1 as a share of Growth", f"{(buy + build) / g_total:.0%}"],
                ["Phase 1 items that carry over to Growth", sum(r["ext_usd"] for r in reuse)], [],
                ["Bins used (of 12 positions)", f"{len(DOSING['bins'])} of {DOSING['bin_positions']}"],
                ["Share of blend weight dosed automatically", f"{DOSING['auto_pct_overall']} %"],
                ["Prices", "dealer list or estimate per line (see price_src); used machines are estimates until a unit is inspected"]]:
        ws.append(row)
    ws["A1"].font = Font(bold=True, size=13)
    for r in ws.iter_rows(min_row=3, max_col=2):
        if isinstance(r[1].value, (int, float)) and "hours" not in str(r[0].value):
            r[1].number_format = '"$"#,##0'
    ws.column_dimensions["A"].width = 58; ws.column_dimensions["B"].width = 22

    sheet(wb, "Equipment BOM", COLS, data, {"name": 46, "model": 34, "qty_basis": 30, "source": 30, "sanitary": 30, "confirm": 30, "maker": 22},
          money=("unit_usd", "ext_usd"))
    sheet(wb, "Fabrication", ["tag", "name", "qty", "material", "material_usd", "labor_h", "process", "ext_usd", "mass_kg", "files"], fabs,
          {"name": 42, "material": 40, "process": 28, "files": 70}, money=("material_usd", "ext_usd"))
    sheet(wb, "Bins", ["bin", "name", "weekly_kg", "capacity_kg", "days_of_stock", "refills_per_week", "bags_per_refill", "max_dose_kg", "feeder",
                       "dose_min", "agitator"], DOSING["bins"], {"name": 24, "feeder": 30})
    rec = [dict(formula=r["name"], batch_kg=r["batch_kg"], per_week=r["batches_per_week"], auto_pct=r["auto_pct"], hand=r["hand_lines"],
                premix=r["premix_lines"], order=" > ".join(r["sequence"])) for r in DOSING["recipes"]]
    sheet(wb, "Recipes", ["formula", "batch_kg", "per_week", "auto_pct", "hand", "premix", "order"], rec, {"formula": 30, "order": 40})
    cmp_rows = [dict(area=a, buy=v[0], build=v[1], total=v[0] + v[1]) for a, v in by_area.items()]
    cmp_rows.append(dict(area="TOTAL Phase 1", buy=buy, build=build, total=buy + build))
    cmp_rows.append(dict(area="Growth plant total", buy="", build="", total=g_total))
    sheet(wb, "Cost by area", ["area", "buy", "build", "total"], cmp_rows, {"area": 28}, money=("buy", "build", "total"))
    sheet(wb, "Carry over to Growth", ["tag", "name", "ext_usd", "growth_equiv"], reuse, {"name": 50, "growth_equiv": 40}, money=("ext_usd",))
    wb.save(HERE / "phase1-bom.xlsx")

    L = ["# Phase 1 cost summary", "",
         f"Phase 1 equipment comes to **${buy + build:,.0f}**: ${buy:,.0f} bought and ${build:,.0f} fabricated in house "
         f"(${mat:,.0f} material and {labor} labor hours at $65/h). That is {(buy + build) / g_total:.0%} of the Growth plant's ${g_total:,.0f}.", "",
         f"Buying the fabricated items from an equipment maker would cost roughly ${oem_equiv:,.0f} (2.5 x shop cost, an estimate), "
         f"so fabricating saves about **${oem_equiv - build:,.0f}**.", "",
         "| Area | Buy | Build | Total |", "|---|---|---|---|"]
    money = lambda v: "" if v == "" else f"${v:,.0f}"
    L += [f"| {r['area']} | {money(r['buy'])} | {money(r['build'])} | {money(r['total'])} |" for r in cmp_rows]
    L += ["", f"Items that carry over to Growth: " + ", ".join(f"{r['tag']} ({r['growth_equiv']})" for r in reuse) + ".", "",
          "Not included: building fit-out (epoxy floor, walls, ceiling, drains), electrical service, compressed air, installation and freight, "
          "packaging stock and opening ingredient inventory."]
    (HERE / "phase1-cost.md").write_text("\n".join(L) + "\n")
    print(f"buy ${buy:,.0f}  build ${build:,.0f}  total ${buy + build:,.0f}  growth ${g_total:,.0f}  saved ~${oem_equiv - build:,.0f}  "
          f"fab {labor} h; missing models: {[f['tag'] for f in fabs if f['files'].startswith('MISSING')]}")


if __name__ == "__main__":
    main()
