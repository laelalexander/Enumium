"""Build every AON-1 sheet (SVG), then (with --pdf) render each to PDF and merge: drawings/AON-1-drawing-set.pdf."""
import subprocess
import sys

import common as C
import sh_parts
import sh_asm
import sh_doc

sh_asm.all_asm()
sh_parts.all_parts()
sh_doc.all_doc()
titles = dict(C.SHEETS)
sh_doc.cover([(n, titles.get(n, "")) for n in C.ORDER])
missing = [n for n in C.ORDER if n not in dict(C.SHEETS)]
print("sheets", len(C.ORDER), "missing", missing)
if "--pdf" in sys.argv:
    svgs = sorted(C.DWG.glob("AON-*.svg"), key=lambda p: C.ORDER.index(p.stem.split("_")[0]))
    subprocess.run(["node", str(C.HERE / "svg2pdf.js")] + [str(p) for p in svgs], check=True)
    from pypdf import PdfWriter
    w = PdfWriter()
    for p in svgs:
        w.append(str(p.with_suffix(".pdf")))
    w.write(str(C.DWG / "AON-1-drawing-set.pdf"))
    for p in svgs:
        p.with_suffix(".pdf").unlink()
    print("wrote", C.DWG / "AON-1-drawing-set.pdf", len(svgs), "pages")
