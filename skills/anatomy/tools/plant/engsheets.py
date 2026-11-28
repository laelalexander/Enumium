"""Engineering sheet kit for plant projects (Anatomy plant tools): ARCH D frames, title blocks, tables, balloons,
dual-unit dimensions, hatching, and four sheet builders:

  pfd(...)        process flow diagram: unit operations as blocks, numbered streams, stream table with rates
  elevation(...)  true-scale side elevation of an equipment train: outlines from documented heights,
                  hatched sections, balloons, item list, connection/fit/torque table, height dimensions
  oneline(...)    power one-line (service, feeders, motors with NEC FLA, cables) + EtherNet/IP network
  iolist(...)     I/O list and cable schedule: every point with PLC address, wire number, cable, terminal

All dimensions are given as mm [in] or mm [ft-in]. Pure Python; SVG out. Render to PDF/PNG with any browser.
"""
from html import escape

import pathlib as _pl
import sys as _sys
for _p in (_pl.Path(__file__).resolve().parent, _pl.Path(__file__).resolve().parents[1]):
    if (_p / "branding.py").exists():
        _sys.path.insert(0, str(_p))
        break
import branding as B  # noqa: E402  Noitavonne / NERO Design Studios title block + footer

SW, SH = 3456, 2304          # ARCH D 36 x 24 in at 96 px/in
IN = 25.4
INK, DIM, HATCH, BAL = "#111", "#b00020", "#455a64", "#0d47a1"


def inch(mm, d=2):
    return f"{mm / IN:.{d}f}"


def mm_in(mm, d=0):
    return f"{mm:,.{d}f} [{mm / IN:.2f}]"


def ft_in(mm):
    t = mm / IN; f = int(t // 12); i = t - 12 * f
    return f"{f}'-{i:.1f}\"" if f else f"{i:.2f}\""


def frame(title, number, project, scale="NTS", rev="A", date="2026-11-17", sheet="1 of 1", extra=""):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" viewBox="0 0 {SW} {SH}" font-family="Helvetica,Arial,sans-serif">',
         '<rect width="100%" height="100%" fill="#fff"/>',
         f'<rect x="24" y="24" width="{SW - 48}" height="{SH - 48}" fill="none" stroke="{INK}" stroke-width="3"/>',
         '<defs><pattern id="h45" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="9" stroke="#455a64" stroke-width="1.2"/></pattern>'
         '<pattern id="h135" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(135)"><line x1="0" y1="0" x2="0" y2="9" stroke="#455a64" stroke-width="1.2"/></pattern>'
         '<marker id="arr" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto"><path d="M0,0 L12,5 L0,10 z" fill="#111"/></marker></defs>']
    for i in range(8):
        x = 24 + (SW - 48) * (i + 0.5) / 8
        o.append(f'<text x="{x}" y="18" font-size="14" text-anchor="middle">{8 - i}</text>')
    x, y, w, h = SW - 820, SH - 300, 796, 276
    o.append(f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="{INK}" stroke-width="2"/>'
             f'<text x="{x + 12}" y="{y + 36}" font-size="28" font-weight="bold">{escape(title)}</text>'
             f'<text x="{x + 12}" y="{y + 62}" font-size="16">{escape(project)}</text><line x1="{x}" y1="{y + 80}" x2="{x + w}" y2="{y + 80}" stroke="{INK}"/>')
    cells = [("DRAWING NO.", number), ("REV", rev), ("SCALE", scale), ("UNITS", "mm [in]"), ("SHEET", f"ARCH D · {sheet}"),
             ("DRAWN", B.DRAWN_BY), ("DATE", date), ("STATUS", "FOR REVIEW")]
    for i, (a, b) in enumerate(cells):
        cx = x + 12 + (i % 4) * 196; cy = y + 106 + (i // 4) * 78
        o.append(f'<text x="{cx}" y="{cy}" font-size="12" fill="#555">{a}</text><text x="{cx}" y="{cy + 26}" font-size="18" font-weight="bold">{escape(str(b))}</text>')
    o.append('</g>' + extra)
    o.append(B.svg_footer(SW, SH, 13))
    return o


def table(x, y, cols, rows, title=None, fs=13, rh=20, zebra=True):
    """cols: [(header, width_px)], rows: list of lists of str. Returns (svg, height)."""
    o = []
    if title:
        o.append(f'<text x="{x}" y="{y - 8}" font-size="{fs + 6}" font-weight="bold">{escape(title)}</text>')
    W = sum(w for _, w in cols)
    o.append(f'<rect x="{x}" y="{y}" width="{W}" height="{rh + 2}" fill="#eceff1" stroke="{INK}"/>')
    cx = x
    for hname, w in cols:
        o.append(f'<text x="{cx + 5}" y="{y + rh - 5}" font-size="{fs}" font-weight="bold">{escape(hname)}</text>'); cx += w
    yy = y + rh + 2
    for i, r in enumerate(rows):
        o.append(f'<rect x="{x}" y="{yy}" width="{W}" height="{rh}" fill="{"#fafafa" if zebra and i % 2 else "#fff"}" stroke="#b0bec5" stroke-width="0.6"/>')
        cx = x
        for (hname, w), v in zip(cols, r):
            maxc = int(w / (fs * 0.52))
            s = str(v); s = s if len(s) <= maxc else s[: maxc - 1] + "…"
            o.append(f'<text x="{cx + 5}" y="{yy + rh - 6}" font-size="{fs - 1}">{escape(s)}</text>'); cx += w
        yy += rh
    return "".join(o), yy - y


def balloon(x, y, n, tx, ty):
    return (f'<line x1="{tx}" y1="{ty}" x2="{x}" y2="{y}" stroke="{BAL}" stroke-width="1.2"/><circle cx="{tx}" cy="{ty}" r="4" fill="{BAL}"/>'
            f'<circle cx="{x}" cy="{y}" r="19" fill="#fff" stroke="{BAL}" stroke-width="2"/><text x="{x}" y="{y + 6}" font-size="17" font-weight="bold" text-anchor="middle" fill="{BAL}">{n}</text>')


def vdim(x, y1, y2, label, ext=None):
    e = ""
    if ext is not None:
        e = f'<line x1="{ext}" y1="{y1}" x2="{x + 8}" y2="{y1}"/><line x1="{ext}" y1="{y2}" x2="{x + 8}" y2="{y2}"/>'
    return (f'<g stroke="{DIM}" fill="{DIM}" stroke-width="1">{e}<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" marker-start="url(#arr)" marker-end="url(#arr)"/>'
            f'<text transform="translate({x - 8},{(y1 + y2) / 2}) rotate(-90)" font-size="15" text-anchor="middle" stroke="none">{escape(label)}</text></g>')


def hdim(x1, x2, y, label, ext=None):
    e = ""
    if ext is not None:
        e = f'<line x1="{x1}" y1="{ext}" x2="{x1}" y2="{y + 8}"/><line x1="{x2}" y1="{ext}" x2="{x2}" y2="{y + 8}"/>'
    return (f'<g stroke="{DIM}" fill="{DIM}" stroke-width="1">{e}<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" marker-start="url(#arr)" marker-end="url(#arr)"/>'
            f'<text x="{(x1 + x2) / 2}" y="{y - 7}" font-size="15" text-anchor="middle" stroke="none">{escape(label)}</text></g>')


def notes(x, y, w, lines, title="NOTES"):
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{30 + 19 * len(lines)}" fill="#fff" stroke="{INK}"/><text x="{x + 10}" y="{y + 22}" font-size="16" font-weight="bold">{title}</text>']
    for i, l in enumerate(lines):
        o.append(f'<text x="{x + 10}" y="{y + 44 + 19 * i}" font-size="13">{i + 1}. {escape(l)}</text>')
    return "".join(o)


# ------------------------------------------------------------------ PFD
def pfd(units, streams, title, number, project, notes_lines=()):
    """units: [{id, name, x, y, w, h, tag}] in px; streams: [{n, frm, to, name, rate, pts?}]"""
    o = frame(title, number, project)
    U = {u["id"]: u for u in units}
    for u in units:
        o.append(f'<rect x="{u["x"]}" y="{u["y"]}" width="{u["w"]}" height="{u["h"]}" rx="10" fill="{u.get("fill", "#fff8e1")}" stroke="{INK}" stroke-width="2"/>'
                 f'<text x="{u["x"] + u["w"] / 2}" y="{u["y"] + 28}" font-size="17" font-weight="bold" text-anchor="middle">{escape(u["tag"])}</text>')
        for i, line in enumerate(u["name"].split("\n")):
            o.append(f'<text x="{u["x"] + u["w"] / 2}" y="{u["y"] + 52 + 19 * i}" font-size="14" text-anchor="middle">{escape(line)}</text>')
    for s in streams:
        a, b = U[s["frm"]], U[s["to"]]
        pts = s.get("pts") or [(a["x"] + a["w"], a["y"] + a["h"] / 2), (b["x"], b["y"] + b["h"] / 2)]
        o.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="{s.get("color", INK)}" stroke-width="2.4" marker-end="url(#arr)" stroke-dasharray="{s.get("dash", "")}"/>')
        mx, my = pts[len(pts) // 2 - 1] if len(pts) > 2 else ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
        o.append(f'<g><path d="M{mx - 16},{my} L{mx},{my - 14} L{mx + 16},{my} L{mx},{my + 14} Z" fill="#fff" stroke="{INK}"/><text x="{mx}" y="{my + 5}" font-size="13" font-weight="bold" text-anchor="middle">{s["n"]}</text></g>')
    rows = [[s["n"], s["name"], s.get("material", ""), s.get("rate", ""), s.get("basis", "")] for s in streams]
    t, h = table(60, SH - 120 - 21 * (len(rows) + 1), [("#", 40), ("STREAM", 380), ("MATERIAL / FORM", 420), ("DESIGN RATE", 420), ("BASIS", 1300)], rows, "STREAM TABLE", fs=13, rh=21)
    o.append(t)
    if notes_lines:
        o.append(notes(SW - 820, 1340, 796, list(notes_lines)))
    o.append("</svg>")
    return "\n".join(o)


# ------------------------------------------------------------------ elevation
def elevation(spec, title, number, project):
    """spec: {scale (paper mm per real mm), origin (px x, px y of floor), items:[{n, tag, name, shapes:[...]}], conn:[...], dims:[...], notes:[...]}
    shapes in real mm: rect(x,y,w,h), poly(pts), circle(cx,cy,r); y up from floor; style keys fill/hatch/dash."""
    k = spec["scale"] * 96 / IN
    ox, oy = spec["origin"]
    X = lambda x: ox + x * k
    Y = lambda y: oy - y * k
    o = frame(title, number, project, scale=f"1:{round(1 / spec['scale'])}")
    o.append(f'<line x1="{X(spec.get("floor_from", -500))}" y1="{oy}" x2="{X(spec.get("floor_to", 20000))}" y2="{oy}" stroke="{INK}" stroke-width="3"/>')
    o.append(f'<rect x="{X(spec.get("floor_from", -500))}" y="{oy}" width="{(spec.get("floor_to", 20000) - spec.get("floor_from", -500)) * k}" height="14" fill="url(#h45)"/>')
    if spec.get("ceiling"):
        o.append(f'<line x1="{X(spec.get("floor_from", -500))}" y1="{Y(spec["ceiling"])}" x2="{X(spec.get("floor_to", 20000))}" y2="{Y(spec["ceiling"])}" stroke="#78909c" stroke-width="2" stroke-dasharray="24,8"/>'
                 f'<text x="{X(spec.get("floor_from", -500)) + 8}" y="{Y(spec["ceiling"]) - 8}" font-size="15" fill="#546e7a">UNDERSIDE OF ROOF STRUCTURE {mm_in(spec["ceiling"])}</text>')
    for it in spec["items"]:
        for sh in it["shapes"]:
            st = f'fill="{sh.get("fill", "none")}" stroke="{sh.get("stroke", INK)}" stroke-width="{sh.get("sw", 2)}" stroke-dasharray="{sh.get("dash", "")}"'
            if sh["t"] == "rect":
                x, y, w, h = sh["xywh"]
                o.append(f'<rect x="{X(x)}" y="{Y(y + h)}" width="{w * k}" height="{h * k}" {st}/>')
                if sh.get("hatch"):
                    o.append(f'<rect x="{X(x)}" y="{Y(y + h)}" width="{w * k}" height="{h * k}" fill="url(#{sh["hatch"]})" stroke="none"/>')
            elif sh["t"] == "poly":
                pts = " ".join(f"{X(a)},{Y(b)}" for a, b in sh["pts"])
                o.append(f'<polygon points="{pts}" {st}/>' if sh.get("closed", True) else f'<polyline points="{pts}" {st}/>')
                if sh.get("hatch"):
                    o.append(f'<polygon points="{pts}" fill="url(#{sh["hatch"]})" stroke="none"/>')
            elif sh["t"] == "circle":
                o.append(f'<circle cx="{X(sh["c"][0])}" cy="{Y(sh["c"][1])}" r="{sh["r"] * k}" {st}/>')
            elif sh["t"] == "text":
                o.append(f'<text x="{X(sh["at"][0])}" y="{Y(sh["at"][1])}" font-size="{sh.get("fs", 14)}" text-anchor="middle" fill="#37474f">{escape(sh["s"])}</text>')
        bx, by = it["balloon"]; tx, ty = it["target"]
        o.append(balloon(X(bx), Y(by), it["n"], X(tx), Y(ty)))
    for d in spec.get("dims", []):
        if d["dir"] == "v":
            o.append(vdim(X(d["x"]), Y(d["y1"]), Y(d["y2"]), d.get("label", mm_in(d["y2"] - d["y1"])), X(d["ext"]) if "ext" in d else None))
        else:
            o.append(hdim(X(d["x1"]), X(d["x2"]), Y(d["y"]), d.get("label", mm_in(d["x2"] - d["x1"])), Y(d["ext"]) if "ext" in d else None))
    for dt in spec.get("details", []):
        o.append(dt)
    tx = SW - 1290
    rows = [[it["n"], it["tag"], it["name"], it.get("qty", 1), it.get("src", "")] for it in spec["items"]]
    t, h = table(tx, 70, [("ITEM", 50), ("TAG", 130), ("DESCRIPTION", 690), ("QTY", 50), ("SOURCE", 340)], rows, None, fs=13, rh=21)
    o.append(f'<text x="{tx}" y="60" font-size="20" font-weight="bold">ITEM LIST</text>' + t)
    cy = 70 + h + 50
    if spec.get("conn"):
        cols = spec.get("conn_cols", [("JOINT", 70), ("BETWEEN", 300), ("CONNECTION / FIT", 470), ("GASKET / SEAL", 230), ("TORQUE", 190)])
        t2, h2 = table(tx, cy, cols, spec["conn"], None, fs=12, rh=20)
        o.append(f'<text x="{tx}" y="{cy - 10}" font-size="20" font-weight="bold">{spec.get("conn_title", "CONNECTIONS, FITS AND TORQUES")}</text>' + t2)
        cy += h2 + 40
    if spec.get("notes"):
        nx, ny = spec.get("notes_at", (tx, cy))
        o.append(notes(nx, ny, 1260, spec["notes"]))
    o.append("</svg>")
    return "\n".join(o)


# ------------------------------------------------------------------ power one-line + network
def oneline(io, title, number, project):
    o = frame(title, number, project)
    sv = io["service"]
    x0, y0 = 120, 150
    o.append(f'<text x="{x0}" y="{y0 - 50}" font-size="22" font-weight="bold">POWER ONE-LINE</text>')
    o.append(f'<rect x="{x0}" y="{y0}" width="300" height="70" fill="#fff" stroke="{INK}" stroke-width="2"/><text x="{x0 + 150}" y="{y0 + 30}" font-size="16" font-weight="bold" text-anchor="middle">UTILITY SERVICE</text>'
             f'<text x="{x0 + 150}" y="{y0 + 54}" font-size="14" text-anchor="middle">{escape(sv["voltage"])}</text>')
    o.append(f'<line x1="{x0 + 150}" y1="{y0 + 70}" x2="{x0 + 150}" y2="{y0 + 130}" stroke="{INK}" stroke-width="3"/>'
             f'<rect x="{x0 + 120}" y="{y0 + 130}" width="60" height="40" fill="#fff" stroke="{INK}" stroke-width="2"/><text x="{x0 + 200}" y="{y0 + 156}" font-size="14">MAIN {sv["main_a"]} A, MDP-1 ({escape(sv["src"])})</text>')
    bus_y = y0 + 230
    feeders = [("CP-300 blending MCC/panel", [m for m in io["motors"] if m["panel"] == "CP-300"]),
               ("CP-400 line panel", [m for m in io["motors"] if m["panel"] == "CP-400"]),
               ("Local", [m for m in io["motors"] if "local" in m["panel"]])]
    o.append(f'<line x1="{x0 + 150}" y1="{y0 + 170}" x2="{x0 + 150}" y2="{bus_y}" stroke="{INK}" stroke-width="3"/>'
             f'<line x1="{x0}" y1="{bus_y}" x2="{x0 + 2050}" y2="{bus_y}" stroke="{INK}" stroke-width="6"/><text x="{x0 + 2060}" y="{bus_y + 6}" font-size="15">480 V BUS MDP-1</text>')
    fx = x0 + 40
    for name, ms in feeders:
        amps = sum(m["fla_460"] for m in ms)
        big = max((m["fla_460"] for m in ms), default=0)
        need = 1.25 * big + (amps - big)
        brk = next(b for b in (15, 20, 30, 40, 50, 60, 70, 80, 100, 125) if b >= need * 1.25)
        o.append(f'<line x1="{fx}" y1="{bus_y}" x2="{fx}" y2="{bus_y + 60}" stroke="{INK}" stroke-width="3"/><rect x="{fx - 22}" y="{bus_y + 60}" width="44" height="30" fill="#fff" stroke="{INK}" stroke-width="2"/>'
                 f'<text x="{fx + 30}" y="{bus_y + 80}" font-size="13">{brk} A</text><line x1="{fx}" y1="{bus_y + 90}" x2="{fx}" y2="{bus_y + 130}" stroke="{INK}" stroke-width="3"/>'
                 f'<rect x="{fx - 110}" y="{bus_y + 130}" width="560" height="34" fill="#e3f2fd" stroke="{INK}"/><text x="{fx - 100}" y="{bus_y + 153}" font-size="15" font-weight="bold">{escape(name)} · FLA sum {amps:.1f} A · NEC 430.24 {need:.1f} A</text>')
        my = bus_y + 190
        for m in ms:
            o.append(f'<line x1="{fx}" y1="{my - 10}" x2="{fx}" y2="{my + 8}" stroke="{INK}" stroke-width="2"/><circle cx="{fx}" cy="{my + 24}" r="16" fill="#fff" stroke="{INK}" stroke-width="2"/>'
                     f'<text x="{fx}" y="{my + 29}" font-size="13" text-anchor="middle">M</text>'
                     f'<text x="{fx + 26}" y="{my + 20}" font-size="13" font-weight="bold">{m["tag"]} {escape(m["load"])}</text>'
                     f'<text x="{fx + 26}" y="{my + 37}" font-size="12">{m["hp"]} HP · {m["fla_460"]} A · {m["starter"]} · {m["cable"]}: {escape(m["conductor"])}</text>')
            my += 56
        fx += 700
    ox = x0
    oy = 1300
    o.append(f'<text x="{ox}" y="{oy - 20}" font-size="20" font-weight="bold">OEM MACHINE FEEDERS FROM MDP-1 / PANEL LP-1 (breaker per OEM nameplate; values here are placeholders until nameplates arrive)</text>')
    rows = [[f["cable"], f["tag"], f["supply"], f'{f["breaker_a"]} A'] for f in io["feeders"]]
    t, h = table(ox, oy, [("CABLE", 90), ("MACHINE", 140), ("SUPPLY", 260), ("BREAKER", 110)], rows, fs=13, rh=21)
    o.append(t)
    # network
    nx, ny = 1500, 1300
    o.append(f'<text x="{nx}" y="{ny - 20}" font-size="20" font-weight="bold">CONTROL NETWORK (EtherNet/IP star, VLAN per area)</text>')
    sws = ["SWI-1", "SWI-2", "SWI-3"]
    labels = {"SWI-1": "SWI-1 Stratix 1783-LMS8 · CP-300 blending", "SWI-2": "SWI-2 Stratix 1783-LMS8 · CP-400 line", "SWI-3": "SWI-3 · MES rack / IT"}
    for i, sw in enumerate(sws):
        sx = nx + i * 470
        o.append(f'<rect x="{sx}" y="{ny}" width="430" height="36" fill="#ede7f6" stroke="{INK}" stroke-width="2"/><text x="{sx + 10}" y="{ny + 24}" font-size="14" font-weight="bold">{escape(labels[sw])}</text>')
        nodes = [n for n in io["network"] if n["switch"] == sw]
        for j, n in enumerate(nodes):
            yy = ny + 60 + j * 34
            o.append(f'<line x1="{sx + 20}" y1="{ny + 36}" x2="{sx + 20}" y2="{yy + 13}" stroke="#5e35b1" stroke-width="1.5"/><line x1="{sx + 20}" y1="{yy + 13}" x2="{sx + 40}" y2="{yy + 13}" stroke="#5e35b1" stroke-width="1.5"/>'
                     f'<rect x="{sx + 40}" y="{yy}" width="390" height="26" fill="#fff" stroke="#5e35b1"/><text x="{sx + 46}" y="{yy + 18}" font-size="12"><tspan font-weight="bold">{escape(n["tag"])}</tspan> {escape(n["device"])} · {escape(n["protocol"])}</text>')
    for i in range(2):
        o.append(f'<line x1="{nx + 430 + i * 470}" y1="{ny + 18}" x2="{nx + 470 + i * 470}" y2="{ny + 18}" stroke="#5e35b1" stroke-width="4"/>')
    o.append(notes(SW - 820, 1500, 796, ["Motor FLA from NEC Table 430.250 at 460 V; conductors sized at 125% FLA, 75 °C column.",
                                         "Feeder breaker = (125% of largest motor + sum of others) x 1.25, next standard size; confirm in stamped design.",
                                         "OEM machines arrive with their own panels; F-2xx feeders end at their disconnects.",
                                         "Dust collector fan and isolation valve interlock with blending (stop on vent burst).",
                                         "Panels CP-300/CP-400 are SS Type 4X; dry-clean area, no washdown hoses.",
                                         "A licensed electrical engineer stamps the final design (NEC 2023, NFPA 79 for machines)."]))
    o.append("</svg>")
    return "\n".join(o)


def iolist(io, title, number, project):
    o = frame(title, number, project)
    rows = [[p["wire"], p["tag"], p["type"], p["address"], p["device"], p["desc"], p.get("cable", "")] for p in io["io"]]
    cols = [("WIRE NO.", 110), ("TAG", 230), ("T", 32), ("PLC ADDRESS", 165), ("DEVICE", 95), ("DESCRIPTION", 380), ("CABLE", 70)]
    half = (len(rows) + 1) // 2
    rh = 16
    t1, _ = table(40, 90, cols, rows[:half], f"I/O LIST · PLC-601 and PLC-602 · {len(rows)} points", fs=11, rh=rh)
    t2, _ = table(40 + 1100, 90, cols, rows[half:], None, fs=11, rh=rh)
    o += [t1, t2]
    crow = [[c["cable"], c["device"], c["cores"], c["spec"], c["from_"], c["to"]] for c in io["cables"]]
    t3, h3 = table(SW - 1150, 90, [("CABLE", 80), ("DEVICE", 100), ("CORES", 60), ("SPEC", 470), ("FROM", 150), ("TO", 260)], crow, "FIELD CABLE SCHEDULE", fs=11, rh=17)
    o.append(t3)
    mrows = [[k, v["points"], v["modules"], v["catalog"], f'{v["spare_pct"]}%'] for k, v in io["modules"].items() if v["points"]]
    t4, h4 = table(SW - 1150, 90 + h3 + 60, [("PLC-TYPE", 140), ("POINTS", 90), ("MODULES", 100), ("CATALOG", 160), ("SPARE", 90)], mrows, "I/O MODULES (25% spare minimum)", fs=12, rh=19)
    o.append(t4)
    o.append(notes(SW - 1150, 90 + h3 + 60 + h4 + 40, 1120, ["Wire number = PLC-slot-channel; both ends ferruled and labelled with the same number.",
                                                          "Field device terminal = cable number + core number (e.g. W-305/3).",
                                                          "24 V DC from PS-608, 0 V bonded to PE at one point per panel.",
                                                          "Analog cables shielded, shield grounded at the panel end only.",
                                                          "E-stops are hard-wired dual channel to SR-607; PLC sees SRxxx_OK status only."]))
    o.append("</svg>")
    return "\n".join(o)
