"""AON-1 BOM: bom.csv, bom.xlsx, bom.md, order-list.md from drawings/common.py (BOUGHT, HARDWARE, MADE) + design/elec.py, then check_bom.

Board-level BOMs (components on E01-E07) come with each board's KiCad/PCBA package; here each board is one BUILD line.
Prices are estimates and no supplier page was fetched from this environment: every BUY line says "not verified".
"""
import csv
import pathlib
import sys
import urllib.parse

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "drawings"))
sys.path.insert(0, str(ROOT / "design"))
import common as C  # noqa: E402
import elec as EL  # noqa: E402

COLS = ["line", "type", "ref", "qty", "description", "manufacturer", "mpn_or_standard", "key_spec", "supplier", "supplier_url", "unit_price", "price_date",
        "alt_mpn", "datasheet_url", "verified", "design_file", "drawing", "status"]
DATE = "2026-11-18"
SUP = {"Azur Space Solar Power GmbH": ("Azur Space (direct quote)", "https://www.azurspace.com/index.php/en/products/products-space/space-solar-cells"),
       "LG Energy Solution": ("Digi-Key / battery distributor (18650 MJ1)", "https://www.digikey.com/en/products/result?keywords=INR18650MJ1"),
       "Omron": ("Digi-Key", "https://www.digikey.com/en/products/result?keywords=D2F-01L"),
       "McMaster-Carr": ("McMaster-Carr", "https://www.mcmaster.com/"),
       "Samtec": ("Samtec / Digi-Key", "https://www.samtec.com/products/esq"),
       "TE Connectivity (Raychem)": ("Mouser / Newark", "https://www.mouser.com/c/?q=M22759%2F32-26"),
       "Harwin": ("Digi-Key / Harwin", "https://www.harwin.com/products/gecko-sl/"),
       "Hirose": ("Digi-Key", "https://www.digikey.com/en/products/result?keywords=U.FL-2LP-04N1T-A-(150)"),
       "Murata": ("Digi-Key", "https://www.digikey.com/en/products/result?keywords=NCP18XH103F03RB"),
       "3M": ("Digi-Key / McMaster", "https://www.digikey.com/en/products/result?keywords=3M%202216"),
       "3M / Dunmore": ("Dunmore / 3M distributor", "https://www.dunmore.com/"),
       "Stanley / Komelon": ("hardware store", "https://www.mcmaster.com/"),
       "generic (e.g. Spectra 50 lb braid)": ("fishing / McMaster", "https://www.mcmaster.com/")}
ALT = {"BP-02": "Samsung INR18650-35E", "BP-03": "Omron D2FW-G01... (sealed) or Cherry DB2C (confirm lever)", "BP-01": "Spectrolab XTJ Prime CIC",
       "BP-07": "Samtec TFM/SFM 1.27 mm with screw locks", "BP-05": "Samtec ESQ-126-38-G-D", "BP-13": "TDK NTCG163JF103FT1"}


def search(q):
    return "https://www.mcmaster.com/products/" + urllib.parse.quote(q)


def rows():
    out = []
    for ln, d, m, p, q, sp, u, n in C.BOUGHT:
        sup, url = SUP.get(m, (m, "https://www.digikey.com/"))
        out.append(dict(line=ln, type="BUY", ref=ln, qty=q + sp, description=d, manufacturer=m, mpn_or_standard=p, key_spec=d.split(",")[0], supplier=sup, supplier_url=url,
                        unit_price=f"{u:.2f}", price_date=DATE + " (estimate)", alt_mpn=ALT.get(ln, ""), datasheet_url=url, verified="not verified: no supplier page fetched; confirm MPN and price",
                        design_file="", drawing="AON-600", status="open: confirm"))
    for h, d, g, q, w, t in C.HARDWARE:
        if not q:
            continue
        out.append(dict(line=h, type="BUY", ref=h, qty=q + max(2, round(q * 0.1 + 0.5)), description=d, manufacturer="any (standard part)", mpn_or_standard=f"{g} {d.split(',')[0]}",
                        key_spec=f"torque {t}", supplier="McMaster-Carr / Bossard / Accu", supplier_url=search(d.split(",")[0]), unit_price="0.40", price_date=DATE + " (estimate)",
                        alt_mpn="", datasheet_url="", verified="not verified: pick the SKU", design_file="", drawing="AON-002 / AON-600", status="open: SKU"))
    raw = [("RM-1", "6061-T6 aluminium square bar 10 x 10 mm [3/8 in], 1.0 m (4 rails + spare)", "ASTM B211 6061-T6 10 mm square", 1, 18.0),
           ("RM-2", "6061-T6 aluminium plate 10 mm [.394], 120 x 360 mm (3 frames)", "ASTM B209 6061-T6 plate 10 mm", 1, 35.0),
           ("RM-3", "5052-H32 aluminium sheet 1.0 mm [.040], 100 x 100 mm (brackets)", "ASTM B209 5052-H32 1.0 mm", 1, 6.0),
           ("RM-4", "6061-T6 round bar Ø6 mm, 1.0 m (spacers)", "ASTM B211 6061-T6 Ø6", 1, 5.0)]
    for ln, d, std, q, u in raw:
        out.append(dict(line=ln, type="BUY", ref=ln, qty=q, description=d, manufacturer="mill stock", mpn_or_standard=std, key_spec="cert EN 10204 3.1", supplier="McMaster-Carr / OnlineMetals",
                        supplier_url=search(d.split(",")[0]), unit_price=f"{u:.2f}", price_date=DATE + " (estimate)", alt_mpn="7075-T73 equivalent size", datasheet_url="",
                        verified="not verified", design_file="", drawing="AON-101/103-105/106/107", status="open: SKU"))
    files = {"AON-101": ("cad/step/AON-101.step", "drawings/AON-101_rails.svg"), "AON-102": ("cad/step/AON-102.step", "drawings/AON-101_rails.svg"),
             "AON-103": ("cad/step/AON-103.step", "drawings/AON-103_zminus_frame.svg"), "AON-104": ("cad/step/AON-104.step", "drawings/AON-104_mid_frame.svg"),
             "AON-105": ("cad/step/AON-105.step", "drawings/AON-105_zplus_frame.svg"), "AON-106": ("dxf/AON-106_flat_mm.dxf", "drawings/AON-106_switch_bracket.svg"),
             "AON-107": ("cad/model.py", "drawings/AON-107_stack.svg")}
    for pid, name, q, mat, proc in C.MADE:
        f, dwg = files.get(pid, (f"design/elec.py", "drawings/AON-B00_boards.svg"))
        out.append(dict(line=pid, type="BUILD", ref=pid, qty=q, description=name, manufacturer="Ambient (in house) / CNC shop", mpn_or_standard=pid, key_spec=mat, supplier=proc,
                        supplier_url="", unit_price="", price_date="", alt_mpn="", datasheet_url="", verified="design file checked in",
                        design_file=f, drawing=dwg, status="board: KiCad layout pending" if pid.startswith("E") else "ready for quote"))
    return out


def check(rs):
    bad = []
    for r in rs:
        if r["type"] not in ("BUY", "BUILD"):
            bad.append(f"{r['line']}: no type")
        if r["type"] == "BUY" and (not r["mpn_or_standard"] or not r["supplier_url"]):
            bad.append(f"{r['line']}: BUY without MPN/standard or supplier link")
        if r["type"] == "BUILD" and not (ROOT / r["design_file"]).exists():
            bad.append(f"{r['line']}: design file {r['design_file']} missing")
    import sh_asm
    lines = {r["line"] for r in rs} | {"AON-107-xx", "AON-107-R"}
    for n, p, d, q in sh_asm.ITEMS:
        if p not in lines and p.split("-xx")[0] not in lines:
            bad.append(f"item {n} {p} on AON-002 is not a BOM line")
    open_items = [r["line"] for r in rs if r["status"].startswith("open") or "pending" in r["status"]]
    return bad, open_items


def main():
    rs = rows()
    with open(HERE / "bom.csv", "w", newline="") as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rs)
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "AON-1 BOM"
        ws.append(COLS)
        for c in ws[1]:
            c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="DDE3EA")
        for r in rs:
            ws.append([r[c] for c in COLS])
        for col, wdt in zip("ABCDEFGHIJKLMNOPQR", (8, 7, 8, 5, 60, 24, 40, 30, 22, 40, 9, 18, 24, 30, 30, 30, 26, 22)):
            ws.column_dimensions[col].width = wdt
        ws.freeze_panes = "A2"
        wb.save(HERE / "bom.xlsx")
    except ImportError:
        pass
    buy = [r for r in rs if r["type"] == "BUY"]
    cost = sum(float(r["unit_price"] or 0) * int(r["qty"]) for r in buy)
    md = ["# AON-1 bill of materials (generated by bom/make_bom.py)", "",
          f"{len(buy)} BUY lines, {len(rs) - len(buy)} BUILD lines. Bought parts and stock ≈ ${cost:,.0f} per satellite including spares (estimates; boards' component BOMs and PCB fab come with the KiCad packages).", "",
          "| Line | Type | Qty | Description | Maker | MPN / standard | Status |", "|---|---|---|---|---|---|---|"]
    md += [f"| {r['line']} | {r['type']} | {r['qty']} | {r['description'][:90]} | {r['manufacturer']} | {r['mpn_or_standard'][:60]} | {r['status']} |" for r in rs]
    bad, open_items = check(rs)
    md += ["", "## Completeness check", "", "PASS: every line typed, every BUY has an MPN/standard and a link, every BUILD has its design file, every AON-002 item is a line." if not bad else
           "FAIL:\n" + "\n".join("- " + b for b in bad), "", f"Open items ({len(open_items)}): " + ", ".join(open_items) +
           ". BUY lines need the supplier page checked and the SKU picked; boards E01-E07 need their KiCad layouts and RushPCB packages.", ""]
    (HERE / "bom.md").write_text("\n".join(md))
    by = {}
    for r in buy:
        by.setdefault(r["supplier"], []).append(r)
    ol = ["# AON-1 order list (by supplier, spares included)", ""]
    for s, items in by.items():
        ol += [f"## {s}", ""] + [f"- {r['qty']} x {r['mpn_or_standard']} ({r['line']}) ~ ${float(r['unit_price']):.2f} ea" for r in items] + [""]
    (HERE / "order-list.md").write_text("\n".join(ol))
    print(f"{len(rs)} lines, buy ≈ ${cost:,.0f}; check: {'PASS' if not bad else bad}; open {len(open_items)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
