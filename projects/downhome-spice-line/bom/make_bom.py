"""Equipment BOM and procurement list from design/equipment.json -> equipment-bom.csv and equipment-bom.xlsx.
Usage: python3 make_bom.py
"""
import csv, json, pathlib
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

HERE = pathlib.Path(__file__).parent
EQ = json.loads((HERE.parent / "design" / "equipment.json").read_text())
COLS = ["tag", "area", "kind", "name", "maker", "model", "qty", "qty_basis", "unit_usd", "ext_usd", "price_src", "supplier", "source",
        "power", "air_cfm", "dust_cfm", "product_contact", "sanitary", "footprint_mm", "footprint_src", "alternates", "confirm"]


def rows():
    for e in EQ:
        p = e.get("price") or {}
        unit = p.get("usd", 0) or 0
        per = p.get("per")          # priced per unit (each, bay, m); otherwise the price is the line total
        ext = unit * e["qty"] if per else unit
        unit = unit if per else unit / e["qty"]
        yield dict(tag=e["tag"], area=e["area"], kind=e["kind"], name=e["name"], maker=e["maker"], model=e["model"], qty=e["qty"],
                   qty_basis=e["qty_basis"], unit_usd=unit, ext_usd=ext, price_src=p.get("src", ""), supplier=e["supplier"],
                   source=e["source"], power=e.get("power") or "", air_cfm=e.get("air_cfm") or 0, dust_cfm=e.get("dust_cfm") or 0,
                   product_contact="yes" if e.get("product_contact") else "", sanitary=e.get("sanitary") or "",
                   footprint_mm=" x ".join(str(x) for x in e.get("footprint_mm") or []), footprint_src=e.get("footprint_src", ""),
                   alternates="; ".join(a if isinstance(a, str) else f"{a.get('maker', '')} {a.get('model', '')}".strip() for a in e.get("alternates") or []),
                   confirm=e.get("confirm") or "")


def main():
    data = list(rows())
    with open(HERE / "equipment-bom.csv", "w", newline="") as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(data)
    wb = Workbook(); ws = wb.active; ws.title = "Equipment BOM"
    ws.append(COLS)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="3E2723"); c.alignment = Alignment(wrap_text=True)
    for r in data:
        ws.append([r[c] for c in COLS])
    n = len(data) + 1
    ws.cell(n + 2, COLS.index("name") + 1, "TOTAL (estimates unless price_src says documented/quote)").font = Font(bold=True)
    col = get_column_letter(COLS.index("ext_usd") + 1)
    ws.cell(n + 2, COLS.index("ext_usd") + 1, f"=SUM({col}2:{col}{n})").font = Font(bold=True)
    for c in ("unit_usd", "ext_usd"):
        L = get_column_letter(COLS.index(c) + 1)
        for i in range(2, n + 3):
            ws[f"{L}{i}"].number_format = '"$"#,##0'
    widths = dict(tag=9, area=14, kind=7, name=44, maker=20, model=36, qty=5, qty_basis=30, supplier=24, source=40, sanitary=30, confirm=30)
    for i, c in enumerate(COLS, 1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(c, 13)
    ws.freeze_panes = "C2"; ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{n}"
    s = wb.create_sheet("By area")
    s.append(["area", "line items", "ext_usd"])
    areas = {}
    for r in data:
        a = areas.setdefault(r["area"], [0, 0]); a[0] += 1; a[1] += r["ext_usd"]
    for a, (k, v) in areas.items():
        s.append([a, k, v])
    s.append(["TOTAL", f"=SUM(B2:B{len(areas) + 1})", f"=SUM(C2:C{len(areas) + 1})"])
    for i in range(2, len(areas) + 3):
        s[f"C{i}"].number_format = '"$"#,##0'
    s.column_dimensions["A"].width = 22; s.column_dimensions["C"].width = 14
    wb.save(HERE / "equipment-bom.xlsx")
    print(len(data), "lines, $", sum(r["ext_usd"] for r in data))


if __name__ == "__main__":
    main()
