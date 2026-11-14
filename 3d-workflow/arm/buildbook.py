"""Build book: one document with everything needed to build the arm.   python run.py book

Writes docs/design/robot-arm-build-book.html at the repo root (open it in a browser; print to PDF from
there) and, if Python Playwright is installed, robot-arm-build-book.pdf next to it.
Sections: overview, procurement, BOM, print plan, assembly plan, wiring, blueprints (every drawing)."""
import base64, json, re
from datetime import date
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUTDIR = HERE.parent / "docs" / "design"


def md(text):
    """Small Markdown subset: headings, tables, lists, code, bold/italic, links."""
    try:
        import markdown
        return markdown.markdown(text, extensions=["tables", "fenced_code"])
    except ImportError:
        pass
    out, lines, i = [], text.splitlines(), 0
    inline = lambda s: re.sub(r"`([^`]+)`", r"<code>\1</code>", re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", escape(s, quote=False))))
    while i < len(lines):
        l = lines[i]
        if l.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"): j += 1
            out.append("<pre>" + escape("\n".join(lines[i + 1:j])) + "</pre>"); i = j + 1; continue
        if l.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-| :]+\|$", lines[i + 1]):
            rows = [l]; j = i + 2
            while j < len(lines) and lines[j].startswith("|"): rows.append(lines[j]); j += 1
            cells = lambda r: [c.strip() for c in r.strip("|").split("|")]
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells(rows[0])) + "</tr>" +
                       "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells(r)) + "</tr>" for r in rows[1:]) + "</table>")
            i = j; continue
        m = re.match(r"^(#{1,4}) (.*)", l)
        if m: out.append(f"<h{len(m.group(1)) + 1}>{inline(m.group(2))}</h{len(m.group(1)) + 1}>"); i += 1; continue
        if re.match(r"^\s*([-*]|\d+\.) ", l):
            tag = "ol" if re.match(r"^\s*\d+\.", l) else "ul"; items = []
            while i < len(lines) and (re.match(r"^\s*([-*]|\d+\.) ", lines[i]) or (lines[i].startswith("   ") and items)):
                if re.match(r"^\s*([-*]|\d+\.) ", lines[i]): items.append(re.sub(r"^\s*([-*]|\d+\.) ", "", lines[i]))
                else: items[-1] += " " + lines[i].strip()
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(t)}</li>" for t in items) + f"</{tag}>"); continue
        if l.strip(): out.append(f"<p>{inline(l)}</p>")
        i += 1
    return "\n".join(out)


def img(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def section(title, body, cls=""):
    return f'<section class="{cls}"><h1>{escape(title)}</h1>{body}</section>'


def main():
    d = json.loads((HERE / "design" / "design.json").read_text(encoding="utf-8"))
    read = lambda p: (HERE / p).read_text(encoding="utf-8") if (HERE / p).exists() else f"_{p} not generated yet_"
    strip_h1 = lambda t: re.sub(r"^# .*\n", "", t, count=1)
    png = HERE / "design" / "png"
    sheets = ["ELE-001_wiring", "ELE-002_wire_list", "ASM-001_assembly", "ASM-002_joint_section"] + sorted(
        p.stem for p in png.glob("*.png") if not p.stem.startswith(("ELE", "ASM")))
    rows = "".join(f"<tr><td>{j}</td><td>{v['drive']}</td><td>{v['required_nm']}</td><td>{v['rated_nm']}</td><td>{v['margin']}×</td></tr>" for j, v in d["joints"].items())
    toc = ["Overview", "Procurement list", "Bill of materials", "Print plan", "Cut list", "Fastener schedule", "Assembly plan", "Wiring", "Blueprints"]
    cover = f"""<section class="cover"><div class="eyebrow">Build book · DRAFT rev A · {date.today().isoformat()}</div>
      <h1 class="big">Desktop robot arm</h1>
      <p class="lede">4-DOF arm (yaw, shoulder, elbow, wrist pitch) with a lead-screw gripper. {d['payload_lb']} lb payload at
      {d['extension_in']} in reach, never beyond 48 in. Aluminium tube links, 3D-printed PETG joints, NEMA 23 planetary gearmotors with
      HTD 5M belt stages, Arduino Mega + DM542 drivers.</p>
      <img src="{img(png / 'ASM-001_assembly.png')}" class="hero">
      <ol class="toc">{''.join(f'<li>{t}</li>' for t in toc)}</ol></section>"""
    overview = section("Overview", f"""<h2>Drive sizing (static, arm horizontal)</h2>
      <table><tr><th>Joint</th><th>Drive</th><th>Required N·m</th><th>Rated N·m</th><th>Margin</th></tr>{rows}</table>
      <h2>Source of truth</h2><p>Everything in this book is generated from <code>3d-workflow/</code>: change the design there and run
      <code>python run.py build</code>, <code>print</code>, <code>procure</code> and <code>book</code> to regenerate it.
      The 3D control surface (<code>python run.py ui</code>) shows the same assembly and drives the real arm.</p>
      <h2>Safety</h2><ul><li>The arm drops when power is cut or E-stop is pressed. Lower it before powering down; keep out of the swing area.</li>
      <li>Rated for 5 lb held static at full reach. Load-test in steps (section 8 of the assembly plan).</li>
      <li>Mains wiring to the PSU must be done by someone qualified; the PSU and IEC inlet need a closed enclosure.</li></ul>""")
    proc = section("Procurement list", md(strip_h1(read("docs/PROCUREMENT.md"))), "small")
    bom = section("Bill of materials", md(strip_h1(read("design/BOM.md"))), "small")
    prt = section("Print plan", md(strip_h1(read("print/REPORT.md"))), "small")
    cut = section("Cut list", md(strip_h1(read("fab/CUTLIST.md"))), "small")
    fas = section("Fastener schedule", md(strip_h1(read("fab/FASTENERS.md"))), "small")
    asm = section("Assembly plan", md(strip_h1(read("docs/ASSEMBLY.md"))))
    wir = section("Wiring", md(strip_h1(read("docs/WIRING.md"))) + f'<img src="{img(png / "ELE-001_wiring.png")}" class="sheet">')
    bp = "".join(f'<section class="sheetpage"><div class="cap">{escape(s)}</div><img src="{img(png / (s + ".png"))}" class="sheet"></section>'
                 for s in sheets if (png / f"{s}.png").exists())
    fpng = HERE / "fab" / "png"
    bp += "".join(f'<section class="sheetpage"><div class="cap">{escape(p.stem)}</div><img src="{img(p)}" class="sheet"></section>'
                  for p in sorted(fpng.glob("*.png")))
    css = """@page{size:A4 landscape;margin:12mm}
    :root{--ink:#14181d;--muted:#5d6670;--line:#d5dae0;--accent:#c4561a;--paper:#fff}
    body{font:10.5pt/1.45 "Segoe UI",system-ui,sans-serif;color:var(--ink);background:var(--paper);margin:0}
    section{page-break-after:always;padding:0 4mm}
    h1{font-size:20pt;margin:0 0 8pt;border-bottom:2px solid var(--accent);padding-bottom:4pt}
    h2{font-size:13pt;margin:14pt 0 4pt} h3{font-size:11.5pt;margin:10pt 0 3pt}
    table{border-collapse:collapse;width:100%;margin:6pt 0;font-size:9pt} td,th{border:1px solid var(--line);padding:3pt 5pt;text-align:left;vertical-align:top}
    th{background:#f2f4f6} code{font:9pt Consolas,monospace;background:#f2f4f6;padding:0 2pt} pre{background:#f2f4f6;padding:6pt;font-size:9pt}
    .small table{font-size:8pt} .cover .big{font-size:40pt;border:0;margin:6pt 0}
    .eyebrow{color:var(--accent);text-transform:uppercase;letter-spacing:.08em;font-size:9pt;font-weight:600}
    .lede{font-size:12.5pt;max-width:200mm;color:var(--muted)} .hero{width:62%;float:right;margin-left:8mm;border:1px solid var(--line)}
    .toc{font-size:12pt;line-height:1.9} .sheet{width:100%;max-height:178mm;object-fit:contain;border:1px solid var(--line)}
    .sheetpage .cap{font-weight:600;margin:2pt 0 4pt;color:var(--muted)}"""
    html = f"<!doctype html><meta charset=utf-8><title>Robot arm build book</title><style>{css}</style>{cover}{overview}{proc}{bom}{prt}{cut}{fas}{asm}{wir}{bp}"
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "robot-arm-build-book.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out)
    from .pdfout import html_to_pdf
    how = html_to_pdf(out, out.with_suffix(".pdf"), landscape=True)
    print(f"wrote {out.with_suffix('.pdf')} ({how})" if how else "PDF skipped: no Playwright or Edge/Chrome found; open the HTML and print to PDF")


if __name__ == "__main__":
    main()
