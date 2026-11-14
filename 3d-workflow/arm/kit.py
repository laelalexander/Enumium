"""Build kit: everything a person needs to actually build the arm, in one folder and one zip.

    python run.py kit [--arms N]

dist/kit/RobotArm-Build-Kit/
  START-HERE.html          the plan: totals, the six phases in order, tick boxes that remember your progress
  1-Buy/                   shopping list (HTML with search links, CSV order tracker), order-first notes
  2-Print/                 print list, Bambu 3MF plates, reference G-code, STL, settings
  3-Cut/                   shop request sheet, cut list, DXF mm + inch, 1:1 templates, drawings, STEP
  4-Assemble/              illustrated assembly guide, build book, every drawing, fastener schedule
  5-Wire-and-Firmware/     wiring notes, ELE-001 schematic, Arduino sketch and how to flash it
  6-Test/                  commissioning and load-test checklist
Everything is generated from the current design, so rerun after any change (the app's Build wizard does)."""
import argparse, csv, html, json, math, re, shutil, zipfile
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

HERE = Path(__file__).resolve().parent.parent
BOOKS = HERE.parent / "docs" / "design"
OUT = HERE / "dist" / "kit"
NAME = "RobotArm-Build-Kit"

CSS = """:root{--ink:#1b2027;--muted:#5d6670;--line:#d5dae0;--head:#f2f4f6;--accent:#c4561a;--ok:#2e7d4f}
body{font:14px/1.55 "Segoe UI",system-ui,sans-serif;color:var(--ink);margin:0;padding:24px 32px;max-width:1150px}
h1{font-size:26px;margin:0 0 4px} h2{font-size:19px;margin:26px 0 8px;border-bottom:2px solid var(--accent);padding-bottom:3px}
.muted{color:var(--muted)} a{color:var(--accent)} table{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0 12px}
td,th{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top} th{background:var(--head)}
.num{text-align:right;white-space:nowrap} .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:14px 0}
.tile{border:1px solid var(--line);border-radius:8px;padding:10px 12px}.tile b{display:block;font-size:22px}
.phase{border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:12px 0}.phase h3{margin:0 0 6px;font-size:17px}
.phase h3 span{display:inline-block;background:var(--accent);color:#fff;border-radius:5px;padding:0 8px;margin-right:8px}
label.chk{display:block;margin:3px 0;cursor:pointer} label.chk input{margin-right:8px} label.chk.done{color:var(--muted);text-decoration:line-through}
.bar{height:8px;background:var(--head);border-radius:4px;overflow:hidden}.bar i{display:block;height:100%;background:var(--ok)}
@media print{.noprint{display:none}}"""

TRACK_JS = """<script>
const K='robot-arm-kit:'+document.title;let S={};try{S=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
function upd(){const b=[...document.querySelectorAll('input[data-k]')],d=b.filter(x=>x.checked).length;
 b.forEach(x=>x.closest('label').classList.toggle('done',x.checked));const p=document.getElementById('prog');
 if(p)p.innerHTML=`<div class=bar><i style="width:${b.length?100*d/b.length:0}%"></i></div><div class=muted>${d} of ${b.length} done</div>`}
document.querySelectorAll('input[data-k]').forEach(x=>{x.checked=!!S[x.dataset.k];x.onchange=()=>{S[x.dataset.k]=x.checked;try{localStorage.setItem(K,JSON.stringify(S))}catch(e){}upd()}});upd();
</script>"""


def page(title, body, track=False):
    return (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>{html.escape(title)}</title>"
            f"<style>{CSS}</style>{body}{TRACK_JS if track else ''}")


def chk(key, text):
    return f'<label class=chk><input type=checkbox data-k="{html.escape(key)}">{text}</label>'


def _cp(src, dst):
    if not src.exists():
        return False
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return True


def _md(path):
    from .library import _md as md
    return md(path.read_text(encoding="utf-8")) if path.exists() else "<p class=muted>not generated</p>"


def plates():
    rep = HERE / "print" / "REPORT.md"
    out, total = [], {}
    if not rep.exists():
        return out, total
    t = rep.read_text(encoding="utf-8")
    for m in re.finditer(r"^\| (\d+)( \(supports\))? \| ([^|]+) \| ([\d.]+) mm \| ([\d.]+) g \| ([^|]+) \| (\w+) \|$", t, re.M):
        out.append(dict(n=int(m.group(1)), supports=bool(m.group(2)), parts=m.group(3).strip(), height=float(m.group(4)),
                        grams=float(m.group(5)), time=m.group(6).strip(), check=m.group(7)))
    m = re.search(r"Total: \*\*(\d+) g\*\*.*?\*\*(\d+)h (\d+)m\*\*", t)
    if m:
        total = dict(grams=float(m.group(1)), hours=int(m.group(2)) + int(m.group(3)) / 60)
    return out, total


def _hours(s):
    h = sum(float(x) for x in re.findall(r"([\d.]+) h", s)) + sum(float(x) for x in re.findall(r"(\d+) min", s)) / 60
    return h


KIT_REL = "app/dist/kit/" + NAME + "/"      # where the kit sits inside the desktop package (= the Anatomy project root)


def anatomy_build(N, R, total, PL, PT, manifest, fab, steps, asm_h, kdir=None):
    """build/build.json for the Anatomy app's Build wizard (skills/anatomy/references/build-package.md). Paths are relative
    to the package root, which is also the Anatomy project root."""
    k = KIT_REL
    by_part = {}
    for p in PL:
        for n in [x.strip() for x in p["parts"].split(",")]:
            by_part.setdefault(n, p)
    prn = []
    for i, (n, m) in enumerate(manifest.get("parts", {}).items(), 1):
        pl = by_part.get(n, {})
        prn.append(dict(part=n, line=f"P-{i:02d}", qty=m["qty"] * N, material="PETG", stl=f"{k}2-Print/{m.get('print_stl', 'stl/' + n + '.stl')}",
                        gcode=f"{k}2-Print/gcode/plate_{m.get('plates', [1])[0]}.gcode", project=f"{k}2-Print/plates/plate_{m.get('plates', [1])[0]}.3mf",
                        plate=m.get("plates", [None])[0], plate_time=pl.get("time", ""), plate_grams=pl.get("grams"),
                        orientation=m.get("why", ""), supports="yes" if m.get("supports") else "none",
                        drawing=f"{k}4-Assemble/drawings/{n}.svg", checks=["compare against the part drawing (dual units)"]))
    fb = [dict(part=f"{p['pid']} {p['title'].lower()}", line=p["pid"], qty=p["qty"] * N, material=p["material"], process=p["process"],
               files=[f for f in (f"{k}3-Cut/dxf/mm/{p['pid']}.dxf", f"{k}3-Cut/dxf/inch/{p['pid']}.dxf", f"{k}3-Cut/drawings/{p['pid']}.svg")
                      if kdir is None or (kdir / f[len(k):]).exists()])
          for p in fab]
    fb.append(dict(part="wiring harness", line="ELE-002", qty=N, process="cut, strip, ferrule and label per the wire list",
                   files=[f"{k}5-Wire-and-Firmware/wire-list.csv", f"{k}5-Wire-and-Firmware/ELE-002_wire_list.svg", f"{k}5-Wire-and-Firmware/ELE-001_wiring.svg"]))
    asm = []
    for i, st in enumerate(steps, 1):
        asm.append(dict(step=i, title=st["title"], image=f"docs/design/assembly/step-{i:02d}-{st['id']}.png",
                        parts=[{"line": a, "desc": b, "qty": q * N} for a, b, q in st.get("parts", [])] + [{"line": f, "qty": q * N} for f, q in st.get("fasteners", [])],
                        tools=[t.strip() for t in st.get("tools", "").split(",") if t.strip()], text=" ".join(st.get("do", [])),
                        torque="", check="; ".join(st.get("check", [])), time=st.get("time", "")))
    com = next((s for s in steps if s["id"] == "commission"), None)
    return {
        "title": "Robot arm test table", "summary": f"4-DOF desktop arm (yaw, shoulder, elbow, wrist) with a lead-screw gripper on a test table: "
                   f"5 lb payload, 39.4 in reach, NEMA 23 planetary gearmotors with HTD 5M belt stages, Arduino Mega + DM542 drivers. Kit for {N} arm{'s' if N > 1 else ''}.",
        "totals": {"parts_cost": round(total, 2), "currency": "USD", "print_hours": round(PT.get("hours", 0) * N, 1),
                   "filament_g": {"PETG": round(PT.get("grams", 0) * N)}, "build_hours": round(asm_h, 1)},
        "tools": sorted({t.strip() for st in steps for t in st.get("tools", "").split(",") if t.strip()}),
        "purchase": [dict(line=f"B-{i:02d}", desc=r["item"], qty=r["qty"], unit=r["unit"], supplier="Amazon / McMaster (search)",
                          url="https://www.amazon.com/s?k=" + quote_plus(r["search"]), unit_price=r["price"], category=r["cat"], notes=r["use"])
                     for i, r in enumerate(R, 1)],
        "print": prn, "fabricate": fb, "assembly": asm,
        "firmware": [dict(name="arm_controller (Arduino Mega 2560)", dir="app/firmware/arm_controller", build="Arduino IDE 2: verify",
                          flash="Arduino IDE 2: Tools > Board > Arduino Mega 2560, pick the COM port, Upload", binary="",
                          check="Robot Arm app > Link > Connect: status reads the firmware banner, HOME runs")],
        "tests": [dict(name=st["title"], steps=st.get("check", []), expect="every check passes") for st in steps if st.get("check")]
                 + ([dict(name="Power-up and load test", steps=com["do"], expect="arm homes, holds the 5 lb test load at full reach")] if com else []),
        "guides": {"start": f"{k}START-HERE.html", "assembly_pdf": f"{k}4-Assemble/robot-arm-assembly-guide.pdf"},
    }


def build(arms=1, out=OUT):
    from . import procure, assembly
    N = max(1, int(arms))
    kit = out / NAME
    if kit.exists():
        shutil.rmtree(kit)
    kit.mkdir(parents=True)
    today = date.today().isoformat()
    PL, PT = plates()
    manifest = json.loads((HERE / "print" / "manifest.json").read_text(encoding="utf-8")) if (HERE / "print" / "manifest.json").exists() else {"parts": {}}
    fab = json.loads((HERE / "fab" / "fab.json").read_text(encoding="utf-8")) if (HERE / "fab" / "fab.json").exists() else []

    # ---------------------------------------------------------------- 1 Buy
    B = kit / "1-Buy"; B.mkdir()
    grams = PT.get("grams")
    R = procure.rows(grams * N if grams else None)
    for r in R:
        if not re.search(r"filament", r["item"], re.I):
            r["qty"] *= N
        r["ext"] = round(r["qty"] * r["price"], 2)
    total = sum(r["ext"] for r in R)
    with open(B / "shopping-list.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Done", "Category", "Item", "Qty", "Unit", "Est. unit USD", "Est. total USD", "Search / spec", "Used for", "Ordered from", "Order #", "Received"])
        for r in R:
            w.writerow(["", r["cat"], r["item"], r["qty"], r["unit"], f"{r['price']:.2f}", f"{r['ext']:.2f}", r["search"], r["use"], "", "", ""])
    rows_html, cats = "", {}
    for r in R:
        cats.setdefault(r["cat"], []).append(r)
    for c, rs in cats.items():
        rows_html += f"<h2>{html.escape(c)} <span class=muted>({len(rs)} lines, about ${sum(x['ext'] for x in rs):,.0f})</span></h2><table><tr><th></th><th>Item</th><th class=num>Qty</th><th>Unit</th><th class=num>Est. each</th><th class=num>Est. total</th><th>Find it</th><th>Used for</th></tr>"
        for i, r in enumerate(rs):
            q = quote_plus(r["search"])
            links = f'<a href="https://www.amazon.com/s?k={q}" target=_blank>Amazon</a>'
            if r["cat"] == "Fasteners":
                links += f' · <a href="https://www.mcmaster.com/products/{q}" target=_blank>McMaster</a>'
            rows_html += (f"<tr><td>{chk('buy:' + r['item'], '')}</td><td>{html.escape(r['item'])}</td><td class=num>{r['qty']}</td><td>{html.escape(r['unit'])}</td>"
                          f"<td class=num>{r['price']:.2f}</td><td class=num>{r['ext']:.2f}</td><td>{links}</td><td>{html.escape(r['use'])}</td></tr>")
        rows_html += "</table>"
    (B / "shopping-list.html").write_text(page("Shopping list", f"""<h1>Shopping list</h1>
<p class=muted>For {N} arm{'s' if N > 1 else ''} · {len(R)} lines · about <b>${total:,.0f}</b> · {today}. Prices are planning estimates from typical
online listings, not quotes. Tick a line when it is ordered; <a href="shopping-list.csv">shopping-list.csv</a> is the same list for Excel.</p>
<div id=prog></div>
<h2>Order these first</h2><ol><li>The four NEMA 23 gearmotors, the 12 in turntable bearing and the four clamp hubs. Their real flange, pilot,
shaft and bolt-circle sizes set the printed parts: measure them, update the design in the app's Build wizard, then print.</li>
<li>Pulleys, belts, shafts and bearings: check the pulley bores against the gearbox shaft (often 14 mm) and the 12 mm joint shaft.</li>
<li>Everything else can arrive while the parts print.</li></ol>{rows_html}""", track=True), encoding="utf-8")

    # ---------------------------------------------------------------- 2 Print
    P = kit / "2-Print"; P.mkdir()
    for d in ("plates", "gcode", "stl", "profiles"):
        _cp(HERE / "print" / d, P / d)
    (P / "print-settings.html").write_text(page("Print settings", _md(HERE / "print" / "REPORT.md")), encoding="utf-8")
    plist = [(n, m) for n, m in manifest.get("parts", {}).items()]
    with open(P / "print-list.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["Part", "Qty", "Plates", "Supports", "Size on bed mm", "Orientation"])
        for n, m in plist:
            w.writerow([n, m["qty"] * N, " ".join(map(str, m.get("plates", []))), "yes" if m.get("supports") else "no",
                        " x ".join(f"{v:g}" for v in m.get("size", [])), m.get("why", "")])
    prow = "".join(f"<tr><td>{chk(f'plate:{p['n']}', '')}</td><td>Plate {p['n']}{' (supports)' if p['supports'] else ''}</td><td>{html.escape(p['parts'])}</td>"
                   f"<td class=num>{N}x</td><td class=num>{p['grams']:.0f} g</td><td>{p['time']}</td>"
                   f"<td><a href='plates/plate_{p['n']}.3mf'>plate_{p['n']}.3mf</a> · <a href='gcode/plate_{p['n']}.gcode'>G-code</a></td></tr>" for p in PL)
    part_rows = "".join(f"<tr><td>{html.escape(n)}</td><td class=num>{m['qty'] * N}</td><td>{', '.join(map(str, m.get('plates', [])))}</td>"
                        f"<td>{'yes' if m.get('supports') else 'no'}</td><td>{html.escape(m.get('why', ''))}</td></tr>" for n, m in plist)
    (P / "print-list.html").write_text(page("Print list", f"""<h1>Print list</h1>
<p class=muted>{len(plist)} parts on {len(PL)} plates, about <b>{(PT.get('grams', 0) * N) / 1000:.2f} kg</b> PETG and <b>{PT.get('hours', 0) * N:.0f} h</b>
of printing for {N} arm{'s' if N > 1 else ''} (PrusaSlicer estimate; Bambu printers run faster). Settings: <a href=print-settings.html>print-settings.html</a>.</p>
<h2>How to print</h2><ol><li>Open each <b>plates/plate_N.3mf</b> in Bambu Studio. Parts arrive oriented and laid out.</li>
<li>Printer: your Bambu, 0.4 mm nozzle, PETG (Bambu PETG HF), 0.20 mm layers, 5 walls, 40 % gyroid, supports only on plates marked supports.</li>
<li>Slice, check the preview, send. Print each plate {N} time{'s' if N > 1 else ''}. Tick it off below.</li></ol>
<p class=muted>The <b>gcode/</b> files are PrusaSlicer reference slices used to verify every plate (fit, height, filament, time). Use them on a
Prusa-style printer; on a Bambu printer slice the 3MF in Bambu Studio instead.</p><div id=prog></div>
<h2>Plates</h2><table><tr><th></th><th>Plate</th><th>Parts</th><th class=num>Print</th><th class=num>Filament</th><th>Time</th><th>Files</th></tr>{prow}</table>
<h2>Parts</h2><table><tr><th>Part</th><th class=num>Qty</th><th>Plate</th><th>Supports</th><th>Orientation</th></tr>{part_rows}</table>""", track=True), encoding="utf-8")

    # ---------------------------------------------------------------- 3 Cut
    C = kit / "3-Cut"; C.mkdir()
    for d in ("dxf", "templates", "drawings", "step"):
        _cp(HERE / "fab" / d, C / d)
    _cp(HERE / "fab" / "cutlist.csv", C / "cutlist.csv")
    (C / "cut-list.html").write_text(page("Cut list", _md(HERE / "fab" / "CUTLIST.md")), encoding="utf-8")
    shop = "".join(f"<tr><td>{chk('cut:' + p['pid'], '')}</td><td>{p['pid']}</td><td>{html.escape(p['title'])}</td><td>{html.escape(p['material'])}</td>"
                   f"<td class=num>{(str(p['t']) + ' mm') if p.get('t') else '-'}</td><td class=num>{p['qty'] * N}</td><td>{html.escape(p['process'])}</td>"
                   + (f"<td><a href='dxf/mm/{p['pid']}.dxf'>DXF mm</a> · <a href='dxf/inch/{p['pid']}.dxf'>DXF in</a> · <a href='drawings/{p['pid']}.svg'>drawing</a></td></tr>"
                      if p.get("kind") == "plate" else f"<td><a href='drawings/{p['pid']}.svg'>drawing</a></td></tr>") for p in fab)
    (C / "shop-request.html").write_text(page("Shop request", f"""<h1>Cut and machined parts: shop request</h1>
<p class=muted>Send this page with the <b>dxf/</b> folder to a laser, waterjet or CNC shop (SendCutSend, Xometry, OSH Cut, a local shop), or cut
them yourself from the 1:1 templates in <b>templates/</b> (print at 100 %, check the 100 mm scale bar). Quantities are for {N} arm{'s' if N > 1 else ''}.
DXF origin is lower-left; layers CUT_OUTSIDE, CUT_INSIDE, POCKET_*, MARK, NOTES. Every drawing is mm [inch] with hole and fastener tables.</p>
<div id=prog></div><table><tr><th></th><th>Part</th><th>Name</th><th>Material</th><th class=num>Thk</th><th class=num>Qty</th><th>Process</th><th>Files</th></tr>{shop}</table>
<p>Tubes, shafts, legs and the 12 corner angles are cut by hand: lengths and pin positions are in <a href=cut-list.html>cut-list.html</a>.</p>""", track=True), encoding="utf-8")

    # ---------------------------------------------------------------- 4 Assemble
    A = kit / "4-Assemble"; A.mkdir()
    for n in ("robot-arm-assembly-guide.pdf", "robot-arm-build-book.pdf"):
        _cp(BOOKS / n, A / n)
    _cp(HERE / "design" / "drawings", A / "drawings")
    (A / "fasteners.html").write_text(page("Fastener schedule", _md(HERE / "fab" / "FASTENERS.md")), encoding="utf-8")
    (A / "assembly-notes.html").write_text(page("Assembly notes", _md(HERE / "docs" / "ASSEMBLY.md")), encoding="utf-8")
    steps = assembly.STEPS
    asm_h = sum(_hours(s["time"]) for s in steps)
    step_rows = "".join(chk(f"asm:{s['id']}", f"<b>{i}. {html.escape(s['title'])}</b> <span class=muted>· {html.escape(s['time'])}</span>") for i, s in enumerate(steps, 1))

    # ---------------------------------------------------------------- 5 Wire + firmware
    W = kit / "5-Wire-and-Firmware"; W.mkdir()
    _cp(HERE / "firmware", W / "firmware")
    _cp(HERE / "design" / "schematics" / "ELE-001_wiring.svg", W / "ELE-001_wiring.svg")
    _cp(HERE / "design" / "schematics" / "ELE-002_wire_list.svg", W / "ELE-002_wire_list.svg")
    _cp(HERE / "fab" / "WIRELIST.csv", W / "wire-list.csv")
    (W / "wiring.html").write_text(page("Wiring", '<p><a href="ELE-001_wiring.svg">ELE-001 schematic</a> · <a href="ELE-002_wire_list.svg">ELE-002 wire list</a> · <a href="wire-list.csv">wire list spreadsheet (CSV)</a>. Every wire carries its Wxxx number: label both ends.</p>' + _md(HERE / "docs" / "WIRING.md") + """<h2>Flash the firmware</h2><ol>
<li>Install the Arduino IDE 2, open <b>firmware/arm_controller/arm_controller.ino</b>.</li><li>Tools > Board > Arduino Mega 2560; pick its COM port.</li>
<li>Upload. Then open the Robot Arm app, Link tab, Connect Arduino.</li></ol>"""), encoding="utf-8")

    # ---------------------------------------------------------------- 6 Test
    T = kit / "6-Test"; T.mkdir()
    checks = "".join(f"<h2>{i}. {html.escape(s['title'])}</h2>" + "".join(chk(f"test:{s['id']}:{j}", html.escape(c)) for j, c in enumerate(s["check"]))
                     for i, s in enumerate(steps, 1))
    com = next(s for s in steps if s["id"] == "commission")
    (T / "test-checklist.html").write_text(page("Test checklist", f"""<h1>Commissioning and load test</h1>
<p class=muted>Every check from the assembly guide in one list, then the power-up procedure. Keep the E-stop in reach.</p><div id=prog></div>{checks}
<h2>Power-up procedure</h2><ol>{''.join(f'<li>{html.escape(d)}</li>' for d in com['do'])}</ol>""", track=True), encoding="utf-8")

    # ---------------------------------------------------------------- START HERE
    ncut = sum(p["qty"] for p in fab) * N
    phases = [
        ("1", "Buy", "1-Buy/shopping-list.html", f"{len(R)} lines, about ${total:,.0f}. Order the gearmotors, turntable and hubs first and measure them when they arrive.",
         [chk("p:buy", "Everything ordered"), chk("p:measure", "Gearmotors, turntable and hubs measured; design updated if they differ")]),
        ("2", "Print", "2-Print/print-list.html", f"{len(PL)} plates, about {PT.get('grams', 0) * N / 1000:.2f} kg PETG, {PT.get('hours', 0) * N:.0f} h. Bambu 3MF plates and reference G-code.",
         [chk("p:print", "All plates printed and checked against the drawings")]),
        ("3", "Cut", "3-Cut/shop-request.html", f"{ncut} cut and machined parts. Send the DXF folder to a shop or cut from the 1:1 templates.",
         [chk("p:cut", "All plates, gaskets, tubes, shafts and legs cut")]),
        ("4", "Assemble", "4-Assemble/robot-arm-assembly-guide.pdf", f"{len(steps)} illustrated steps, about {asm_h:.0f} h of bench time.",
         [step_rows]),
        ("5", "Wire and flash", "5-Wire-and-Firmware/wiring.html", "Harness per the ELE-002 wire list (numbered wires, CSV), ELE-001 schematic, Arduino sketch.",
         [chk("p:wire", "Harness built and checked"), chk("p:flash", "Firmware flashed, app connects over USB")]),
        ("6", "Test", "6-Test/test-checklist.html", "Every check from the guide, power-up, homing and the 5 lb load test.",
         [chk("p:test", "Load test passed")]),
    ]
    ph = "".join(f"<div class=phase><h3><span>{n}</span><a href='{href}'>{t}</a></h3><div class=muted>{d}</div>{''.join(c)}</div>" for n, t, href, d, c in phases)
    (kit / "START-HERE.html").write_text(page("Robot arm build kit", f"""<h1>Robot arm build kit</h1>
<div class=muted>4-DOF desktop arm, 5 lb payload, 39.4 in reach · for {N} arm{'s' if N > 1 else ''} · generated {today} from the current design</div>
<div class=tiles><div class=tile><b>${total:,.0f}</b>parts to buy ({len(R)} lines)</div><div class=tile><b>{PT.get('hours', 0) * N:.0f} h</b>printing, {PT.get('grams', 0) * N / 1000:.2f} kg PETG</div>
<div class=tile><b>{ncut}</b>cut and machined parts</div><div class=tile><b>{len(steps)}</b>assembly steps, about {asm_h:.0f} h</div></div>
<p>Work through the six phases in order. Tick boxes here and on each page remember your progress in this browser.</p><div id=prog></div>{ph}
<h2>Safety</h2><p>The arm falls when power is cut or the E-stop is pressed. Keep hands and face out of its reach, test with the arm supported,
and have mains wiring checked by a qualified person. This is a first-revision design: prototype and test-fit before trusting it with weight.</p>""", track=True), encoding="utf-8")
    (kit / "build.json").write_text(json.dumps(anatomy_build(N, R, total, PL, PT, manifest, fab, steps, asm_h, kit), indent=1), encoding="utf-8")
    (kit / "kit.json").write_text(json.dumps(dict(arms=N, date=today, buy_usd=round(total), buy_lines=len(R), plates=len(PL),
                                                   print_hours=round(PT.get("hours", 0) * N, 1), filament_kg=round(PT.get("grams", 0) * N / 1000, 2),
                                                   cut_parts=ncut, steps=len(steps), assembly_hours=round(asm_h, 1)), indent=1), encoding="utf-8")
    zp = out / f"{NAME}-{today}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(kit.rglob("*")):
            if f.is_file():
                z.write(f, Path(NAME) / f.relative_to(kit))
    nf = sum(1 for f in kit.rglob("*") if f.is_file())
    print(f"kit: {N} arm(s), ${total:,.0f}, {len(PL)} plates, {ncut} cut parts, {len(steps)} steps -> {kit} ({nf} files)\n     {zp} ({zp.stat().st_size / 1e6:.1f} MB)")
    return kit


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", type=int, default=1)
    a = ap.parse_args(argv)
    build(a.arms)
    return 0


if __name__ == "__main__":
    main()
