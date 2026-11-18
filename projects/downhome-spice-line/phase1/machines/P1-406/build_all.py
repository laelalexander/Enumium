"""Build every P1-406 sheet (SVG), render each to PDF and merge: drawings/P1-406-drawing-set.pdf."""
import subprocess
import sys

import common as C
import sh_ga
mods = [sh_ga]
try:
    import sh_parts, sh_ele, sh_doc
    mods += [sh_parts, sh_ele, sh_doc]
except ImportError:
    sh_parts = sh_ele = sh_doc = None

sh_ga.ga(); sh_ga.section()
if sh_doc:
    sh_doc.assembly()
if sh_parts:
    sh_parts.frame(); sh_parts.belt(); sh_parts.reject(); sh_parts.drive()
if sh_doc:
    sh_doc.hardware()
if sh_ele:
    sh_ele.e01()
if sh_doc:
    sh_doc.itp()
    titles = dict(C.SHEETS)
    titles["P1-406-000"] = "P1-406 METAL DETECTOR CONVEYOR: DRAWING SET"
    sh_doc.cover_sheet([(n, titles.get(n, "")) for n in C.ORDER])
    print("sheets", len(C.ORDER), "missing", [n for n in C.ORDER if n not in titles])
if len(sys.argv) > 1:
    render = sys.argv[1]
    svgs = sorted(C.DWG.glob("P1-406-*.svg"), key=lambda p: C.ORDER.index("-".join(p.stem.split("_")[0].split("-")[:3])))
    pdfs = []
    for p in svgs:
        out = p.with_suffix(".pdf"); subprocess.run(["node", render, str(p), str(out), "1"], check=True); pdfs.append(out)
    from pypdf import PdfWriter
    w = PdfWriter()
    for p in pdfs:
        w.append(str(p))
    w.write(str(C.DWG / "P1-406-drawing-set.pdf"))
    for p in pdfs:
        p.unlink()
    print("wrote", C.DWG / "P1-406-drawing-set.pdf", len(pdfs), "pages")
