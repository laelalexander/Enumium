"""Build every P1-401 sheet (SVG), render each to PDF and merge: drawings/P1-401-drawing-set.pdf."""
import subprocess
import sys

import common as C
import sh_ga, sh_parts, sh_hop, sh_head, sh_ele, sh_doc

sh_ga.ga(); sh_ga.section()
sh_doc.assembly()
sh_parts.cabinet(); sh_parts.flats(); sh_parts.column()
sh_head.head_asm(); sh_head.machined()
sh_hop.hopper(); sh_hop.agitator()
sh_head.tooling()
sh_parts.stage()
sh_doc.hardware()
sh_ele.e01(); sh_ele.e02(); sh_ele.e03()
sh_doc.itp()
titles = dict(C.SHEETS)
titles["P1-401-000"] = "P1-401 SERVO AUGER FILLER: DRAWING SET"
sh_doc.cover_sheet([(n, titles.get(n, "")) for n in C.ORDER])
missing = [n for n in C.ORDER if n not in titles]
print("sheets", len(C.ORDER), "missing", missing)
if len(sys.argv) > 1:
    render = sys.argv[1]
    svgs = sorted(C.DWG.glob("P1-401-*.svg"), key=lambda p: C.ORDER.index("-".join(p.stem.split("_")[0].split("-")[:3])))
    pdfs = []
    for p in svgs:
        out = p.with_suffix(".pdf"); subprocess.run(["node", render, str(p), str(out), "1"], check=True); pdfs.append(out)
    from pypdf import PdfWriter
    w = PdfWriter()
    for p in pdfs:
        w.append(str(p))
    w.write(str(C.DWG / "P1-401-drawing-set.pdf"))
    for p in pdfs:
        p.unlink()
    print("wrote", C.DWG / "P1-401-drawing-set.pdf", len(pdfs), "pages")
