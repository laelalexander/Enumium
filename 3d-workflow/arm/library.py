"""In-app Library: every note, instruction, drawing and file, indexed for the twin's Library tab.

Writes control/lib/ (rendered Markdown and CSV pages, copies of the guide and build book PDFs) and
control/lib/library.json. Paths in the index are relative to the app root (the 3d-workflow folder,
or app/ inside the packaged desktop app), so the same index works in both.   python -m arm.library"""
import csv, html, io, json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # 3d-workflow
BOOKS = HERE.parent / "docs" / "design"
LIB = HERE / "control" / "lib"

CSS = """:root{color-scheme:light dark;--ink:#1b2027;--muted:#5d6670;--line:#d5dae0;--bg:#fff;--head:#f2f4f6;--accent:#c4561a}
@media (prefers-color-scheme:dark){:root{--ink:#e6e9ee;--muted:#9aa3ad;--line:#333a44;--bg:#14181d;--head:#1d232b}}
body{font:14px/1.55 "Segoe UI",system-ui,sans-serif;color:var(--ink);background:var(--bg);margin:0;padding:24px 32px;max-width:1100px}
h1{font-size:24px;border-bottom:2px solid var(--accent);padding-bottom:4px} h2{font-size:19px;margin-top:28px} h3{font-size:16px}
table{border-collapse:collapse;margin:8px 0;font-size:13px} td,th{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
th{background:var(--head)} code{background:var(--head);padding:1px 4px;border-radius:3px} pre{background:var(--head);padding:10px;overflow:auto}
a{color:var(--accent)} img{max-width:100%}"""


def _page(title, body):
    return f"<!doctype html><meta charset=utf-8><title>{html.escape(title)}</title><style>{CSS}</style>{body}"


def _md(text):
    try:
        import markdown
        return markdown.markdown(text, extensions=["tables", "fenced_code"])
    except ImportError:
        return f"<pre>{html.escape(text)}</pre>"


def _csv(text):
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return ""
    head = "".join(f"<th>{html.escape(c)}</th>" for c in rows[0])
    body = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
    return f"<table><tr>{head}</tr>{body}</table>"


def _render(src, name, title):
    """Render a .md or .csv file into control/lib/<name>.html; returns the item or None if the source is missing."""
    if not src.exists():
        return None
    t = src.read_text(encoding="utf-8")
    body = _md(t) if src.suffix == ".md" else f"<h1>{html.escape(title)}</h1>" + _csv(t)
    (LIB / f"{name}.html").write_text(_page(title, body), encoding="utf-8")
    return dict(title=title, kind="page", href=f"control/lib/{name}.html", file=str(src.relative_to(HERE)).replace("\\", "/"))


def _file(rel, title, kind=None):
    p = HERE / rel
    if not p.exists():
        return None
    k = kind or {".svg": "svg", ".pdf": "pdf", ".png": "image"}.get(p.suffix.lower(), "file")
    return dict(title=title, kind=k, href=rel, file=rel)


def _folder(rel, title, pattern="*", note=""):
    p = HERE / rel
    if not p.exists():
        return None
    files = sorted(f.relative_to(HERE).as_posix() for f in p.rglob(pattern) if f.is_file())
    return dict(title=title, kind="folder", href=rel, file=rel, files=files, note=note)


def _drawings(rel, prefix=""):
    p = HERE / rel
    return [dict(title=f"{prefix}{f.stem}", kind="svg", href=f"{rel}/{f.name}", file=f"{rel}/{f.name}")
            for f in sorted(p.glob("*.svg"))] if p.exists() else []


def build():
    if LIB.exists():
        shutil.rmtree(LIB)
    LIB.mkdir(parents=True)
    pdfs = []
    for name, title, note in (("robot-arm-assembly-guide.pdf", "Assembly guide (illustrated, 14 steps)", "One page per step: picture, parts, fasteners with torque, tools, checks"),
                              ("robot-arm-build-book.pdf", "Build book (everything in one PDF)", "Blueprints, assembly plan, BOM, procurement, print plan, cut list")):
        if (BOOKS / name).exists():
            shutil.copy2(BOOKS / name, LIB / name)
            pdfs.append(dict(title=title, kind="pdf", href=f"control/lib/{name}", file=f"control/lib/{name}", note=note))
    sections = [
        ("Start here", pdfs + [
            _render(HERE / "docs" / "ASSEMBLY.md", "assembly-notes", "Assembly notes and safety"),
            _render(HERE / "docs" / "WIRING.md", "wiring", "Wiring and electronics"),
            _file("design/schematics/ELE-001_wiring.svg", "ELE-001 wiring schematic"),
        ]),
        ("Buying", [
            _render(HERE / "design" / "BOM.md", "bom", "Bill of materials"),
            _render(HERE / "docs" / "PROCUREMENT.md", "procurement", "Procurement list with prices"),
            _render(HERE / "docs" / "procurement.csv", "procurement-table", "Procurement list (spreadsheet view)"),
            _render(HERE / "fab" / "FASTENERS.md", "fasteners", "Fastener schedule F01-F18"),
        ]),
        ("Assembly and section drawings", [d for d in _drawings("design/drawings") if d["title"].startswith(("ASM", "ELE"))]),
        ("Printed part drawings", [d for d in _drawings("design/drawings") if not d["title"].startswith(("ASM", "ELE"))]),
        ("Cut and machined part drawings", _drawings("fab/drawings")),
        ("Cut files for the shop", [
            _render(HERE / "fab" / "CUTLIST.md", "cutlist", "Cut list and harness lengths"),
            _render(HERE / "fab" / "cutlist.csv", "cutlist-table", "Cut list (spreadsheet view)"),
            _folder("fab/dxf/mm", "DXF cut files, mm", "*.dxf", "Layers CUT_OUTSIDE, CUT_INSIDE, POCKET_*, MARK, NOTES; origin lower-left"),
            _folder("fab/dxf/inch", "DXF cut files, inch", "*.dxf"),
            _folder("fab/templates", "1:1 drill templates (print at 100 %)", "*.svg"),
            _folder("fab/step", "STEP solids of cut parts", "*.step"),
        ]),
        ("3D printing (Bambu Lab, 256 mm bed)", [
            _render(HERE / "print" / "REPORT.md", "print-report", "Print plan and slicing report"),
            _folder("print/plates", "Bambu Studio plates (3MF)", "*.3mf", "Open a plate in Bambu Studio, check, slice and send"),
            _folder("print/stl", "STL in print orientation", "*.stl"),
            _folder("print/profiles", "Slicer profiles", "*"),
        ]),
        ("CAD", [
            _folder("design/cad/step", "STEP solids (printed parts)", "*.step"),
            _folder("design/cad/stl", "STL meshes (design orientation)", "*.stl"),
            _folder("design/cad/obj", "OBJ meshes", "*.obj"),
        ]),
    ]
    out = [dict(title=t, items=[i for i in items if i]) for t, items in sections]
    out = [s for s in out if s["items"]]
    (LIB / "library.json").write_text(json.dumps(dict(sections=out), indent=1), encoding="utf-8")
    n = sum(len(s["items"]) for s in out)
    print(f"library: {n} entries in {len(out)} sections -> {LIB}")
    return out


if __name__ == "__main__":
    build()
