"""Plant layout drawing + checks (Anatomy plant tools).

Input: a layout JSON (building, rooms with hygiene zones, equipment placements, rack rows, doors, flows,
       utilities) and the project's equipment.json (footprints, names, product-contact flags).
Output (to out_dir):
  LAY-001_plant_layout.svg   true-scale plan on an ARCH D sheet (36 x 24 in), grid in m and ft,
                             overall and grid dimensions in mm [ft-in], equipment balloons + schedule,
                             room / zone schedule, material, people and waste flows, legend, title block
  LAY-001_plant_layout_mm.dxf / _in.dxf   the same plan as CAD (layers: WALLS, ROOMS, EQUIP, RACKS, FLOW, TEXT)
  layout-check.json / .md    overlaps, out-of-room equipment, aisle clearances, zone rules, flow crossings
Usage: python layout.py layout.json equipment.json out_dir
"""
import json, math, pathlib, sys
from html import escape

import pathlib as _pl
import sys as _sys
for _p in (_pl.Path(__file__).resolve().parent, _pl.Path(__file__).resolve().parents[1]):
    if (_p / "branding.py").exists():
        _sys.path.insert(0, str(_p))
        break
import branding as B  # noqa: E402  Noitavonne / NERO Design Studios title block + footer

IN = 25.4
FT = 304.8

ZONE_COLORS = {  # hygiene zones, colors chosen to read in print and greyscale
    "Z0 outside": "#f4f4f4", "Z1 warehouse": "#eef3fb", "Z2 controlled (packaging, non-exposed)": "#eaf6ee",
    "Z3 high-care dry (exposed product)": "#fff4e0", "Z3A allergen (wheat) exposed": "#fde8e8", "support": "#f3eef8",
}
FLOW_STYLE = {"raw": ("#1565c0", "10,4"), "product": ("#e65100", ""), "finished": ("#2e7d32", "14,4"),
              "people": ("#6a1b9a", "3,4"), "waste": ("#5d4037", "2,3"), "packaging": ("#00838f", "8,3,2,3")}


def ft_in(mm):
    t = mm / IN
    f = int(t // 12); i = t - 12 * f
    if round(i) == 12:
        f, i = f + 1, 0
    return f"{f}'-{i:.0f}\""


def dual(mm):
    return f"{mm:,.0f} [{ft_in(mm)}]"


def rect_of(p, eqs):
    e = eqs.get(p["tag"], {})
    L, W = (p.get("size") or e.get("footprint_mm", [1000, 1000, 0]))[:2]
    if p.get("rot", 0) in (90, 270):
        L, W = W, L
    return p["x"], p["y"], L, W


def overlap(a, b, gap=0.0):
    return not (a[0] + a[2] + gap <= b[0] or b[0] + b[2] + gap <= a[0] or a[1] + a[3] + gap <= b[1] or b[1] + b[3] + gap <= a[1])


def seg_intersect(p1, p2, p3, p4):
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


def checks(L, eqs):
    res = {"overlaps": [], "outside_room": [], "tight_aisles": [], "zone_violations": [], "flow_crossings": [], "ok": []}
    places = L["equipment"]
    rects = {p["tag"]: rect_of(p, eqs) for p in places}
    linked = {tuple(sorted(x)) for x in L.get("linked", [])}
    for chain in L.get("lines", []):            # machines joined by conveyor: neighbours sit close on purpose
        linked |= {tuple(sorted(p)) for p in zip(chain, chain[1:])}
    tags = list(rects)
    room_of = {p["tag"]: p["room"] for p in places}
    for i, a in enumerate(tags):
        for b in tags[i + 1:]:
            if overlap(rects[a], rects[b]) and tuple(sorted((a, b))) not in linked:
                res["overlaps"].append([a, b])
            elif (overlap(rects[a], rects[b], L["rules"]["min_clear_mm"]) and tuple(sorted((a, b))) not in linked
                  and room_of[a] == room_of[b]):     # a wall between two rooms is not an aisle
                res["tight_aisles"].append([a, b])
    rooms = {r["name"]: r for r in L["rooms"]}
    for p in places:
        x, y, w, h = rects[p["tag"]]
        r = rooms.get(p["room"])
        if not r or x < r["x"] - 1 or y < r["y"] - 1 or x + w > r["x"] + r["w"] + 1 or y + h > r["y"] + r["h"] + 1:
            res["outside_room"].append([p["tag"], p["room"]])
        e = eqs.get(p["tag"], {})
        z = r["zone"] if r else "?"
        if e.get("product_contact") and not z.startswith("Z3"):
            res["zone_violations"].append(f"{p['tag']} touches exposed product but sits in {z}")
        if p.get("allergen") == "wheat" and z != "Z3A allergen (wheat) exposed":
            res["zone_violations"].append(f"{p['tag']} handles open wheat product outside the allergen room ({z})")
    fl = L["flows"]
    for i, a in enumerate(fl):
        for b in fl[i + 1:]:
            pair = {a["type"], b["type"]}
            if pair in ({"raw", "finished"}, {"waste", "product"}, {"waste", "finished"}):
                for s1 in zip(a["pts"], a["pts"][1:]):
                    for s2 in zip(b["pts"], b["pts"][1:]):
                        if seg_intersect(*s1, *s2):
                            res["flow_crossings"].append(f"{a['name']} x {b['name']}")
    res["flow_crossings"] = sorted(set(res["flow_crossings"]))
    res["ok"] = [k for k in ("overlaps", "outside_room", "zone_violations", "flow_crossings") if not res[k]]
    return res


# ------------------------------------------------------------------ SVG sheet (ARCH D, px = 1/0.0254 mm * k)
SW, SH = 3456, 2304            # 36 x 24 in at 96 px/in


def svg(L, eqs, chk):
    B = L["building"]
    draw_w, draw_h = 2470, 2000
    s = min(draw_w / (B["w"] + 5500), draw_h / (B["h"] + 8000))     # px per mm, with margin for dims
    nice = [1 / 50, 1 / 75, 1 / 100, 1 / 125, 1 / 150, 1 / 200]
    paper = s / (96 / IN)
    k = max(n for n in nice if n <= paper + 1e-12)
    s = k * 96 / IN
    ox, oy = 110 + 4300 * s, 60 + 4300 * s
    X = lambda x: ox + x * s
    Y = lambda y: oy + (B["h"] - y) * s
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" viewBox="0 0 {SW} {SH}" font-family="Helvetica,Arial,sans-serif">',
         '<rect width="100%" height="100%" fill="#fff"/>',
         f'<rect x="24" y="24" width="{SW - 48}" height="{SH - 48}" fill="none" stroke="#111" stroke-width="3"/>',
         '<defs><marker id="ar" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="context-stroke"/></marker>'
         '<pattern id="hz" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="10" stroke="#c62828" stroke-width="1"/></pattern></defs>']
    # grid every 5 m, labelled in m and ft
    g = 5000
    for gx in range(0, int(B["w"]) + 1, g):
        o.append(f'<line x1="{X(gx)}" y1="{Y(0) + 60}" x2="{X(gx)}" y2="{Y(B["h"]) - 60}" stroke="#cfd8dc" stroke-width="1" stroke-dasharray="20,6,4,6"/>')
        o.append(f'<circle cx="{X(gx)}" cy="{Y(B["h"]) - 90}" r="22" fill="#fff" stroke="#607d8b"/><text x="{X(gx)}" y="{Y(B["h"]) - 84}" font-size="18" text-anchor="middle" fill="#37474f">{gx // g + 1}</text>')
    for i, gy in enumerate(range(0, int(B["h"]) + 1, g)):
        o.append(f'<line x1="{X(0) - 60}" y1="{Y(gy)}" x2="{X(B["w"]) + 60}" y2="{Y(gy)}" stroke="#cfd8dc" stroke-width="1" stroke-dasharray="20,6,4,6"/>')
        o.append(f'<circle cx="{X(0) - 90}" cy="{Y(gy)}" r="22" fill="#fff" stroke="#607d8b"/><text x="{X(0) - 90}" y="{Y(gy) + 6}" font-size="18" text-anchor="middle" fill="#37474f">{"ABCDEFGH"[i]}</text>')
    # rooms
    for r in L["rooms"]:
        col = ZONE_COLORS.get(r["zone"], "#fff")
        o.append(f'<rect x="{X(r["x"])}" y="{Y(r["y"] + r["h"])}" width="{r["w"] * s}" height="{r["h"] * s}" fill="{col}" stroke="#263238" stroke-width="{5 if r.get("wall", True) else 1.5}"/>')
        if r.get("hatch"):
            o.append(f'<rect x="{X(r["x"])}" y="{Y(r["y"] + r["h"])}" width="{r["w"] * s}" height="{r["h"] * s}" fill="url(#hz)" opacity="0.35"/>')
        lx, ly = r.get("label_at", (r["x"] + 300, r["y"] + r["h"] - 300))
        # narrow rooms: "label" may hold line breaks and "compact" puts the zone and the area on separate lines
        heads = r.get("label", r["name"]).upper().split("\n")
        area = f'{r["w"] * r["h"] / 1e6:,.0f} m² [{r["w"] * r["h"] / FT ** 2:,.0f} ft²]'
        subs = [r["zone"], area] if r.get("compact") else [f'{r["zone"]} · {area}']
        fs = 16 if r.get("compact") else 20
        yy = Y(ly) + fs
        for h in heads:
            o.append(f'<text x="{X(lx)}" y="{yy}" font-size="{fs}" font-weight="bold" fill="#263238">{escape(h)}</text>')
            yy += fs + 3
        for t in subs:
            o.append(f'<text x="{X(lx)}" y="{yy + 2}" font-size="13" fill="#455a64">{escape(t)}</text>')
            yy += 16
    # outer walls
    o.append(f'<rect x="{X(0)}" y="{Y(B["h"])}" width="{B["w"] * s}" height="{B["h"] * s}" fill="none" stroke="#111" stroke-width="9"/>')
    # doors
    for d in L.get("doors", []):
        x, y, w, side = d["x"], d["y"], d["w"], d["side"]
        if side in ("S", "N"):
            o.append(f'<line x1="{X(x)}" y1="{Y(y)}" x2="{X(x + w)}" y2="{Y(y)}" stroke="#fff" stroke-width="11"/>')
            o.append(f'<text x="{X(x + w / 2)}" y="{Y(y) + (34 if side == "S" else -16)}" font-size="14" text-anchor="middle" fill="#37474f">{escape(d["name"])}</text>')
        else:
            o.append(f'<line x1="{X(x)}" y1="{Y(y)}" x2="{X(x)}" y2="{Y(y + w)}" stroke="#fff" stroke-width="11"/>')
            o.append(f'<text x="{X(x) + (12 if side == "E" else -12)}" y="{Y(y + w / 2)}" font-size="13" text-anchor="{"start" if side == "E" else "end"}" fill="#37474f">{escape(d["name"])}</text>')
    # racks
    for rr in L.get("racks", []):
        for i in range(rr["bays"]):
            if rr["dir"] == "x":
                x, y, w, h = rr["x"] + i * rr["bay_mm"], rr["y"], rr["bay_mm"], rr["depth_mm"]
            else:
                x, y, w, h = rr["x"], rr["y"] + i * rr["bay_mm"], rr["depth_mm"], rr["bay_mm"]
            o.append(f'<rect x="{X(x)}" y="{Y(y + h)}" width="{w * s}" height="{h * s}" fill="#fff" stroke="#78909c" stroke-width="1.5"/>'
                     f'<line x1="{X(x)}" y1="{Y(y + h)}" x2="{X(x + w)}" y2="{Y(y)}" stroke="#b0bec5" stroke-width="1"/>')
        o.append(f'<text x="{X(rr["x"])}" y="{Y(rr["y"]) + 18}" font-size="13" fill="#455a64">{escape(rr["name"])}: {rr["bays"]} bays x {rr["positions_per_bay"]} = {rr["bays"] * rr["positions_per_bay"]} positions</text>')
    # equipment
    num = {}
    for n, p in enumerate(L["equipment"], 1):
        x, y, w, h = rect_of(p, eqs)
        e = eqs.get(p["tag"], {})
        num[p["tag"]] = n
        fill = "#ffe0b2" if e.get("product_contact") else "#e3f2fd"
        o.append(f'<rect x="{X(x)}" y="{Y(y + h)}" width="{w * s}" height="{h * s}" fill="{fill}" stroke="#0d47a1" stroke-width="2.4"/>')
        fs = max(9, min(15, w * s / 6.5))
        o.append(f'<text x="{X(x + w / 2)}" y="{Y(y + h / 2) + 5}" font-size="{fs}" text-anchor="middle" font-weight="bold" fill="#0d47a1">{escape(p["tag"])}</text>')
        bx, by = X(x + w) + 4, Y(y + h) - 4
        o.append(f'<circle cx="{bx + 13}" cy="{by - 13}" r="14" fill="#fff" stroke="#0d47a1" stroke-width="1.6"/><text x="{bx + 13}" y="{by - 8}" font-size="14" text-anchor="middle" fill="#0d47a1">{n}</text>')
    # flows
    for f in L["flows"]:
        col, dash = FLOW_STYLE[f["type"]]
        pts = " ".join(f"{X(a)},{Y(b)}" for a, b in f["pts"])
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="4" stroke-dasharray="{dash}" marker-end="url(#ar)" opacity="0.9"/>')
    # dimensions: overall + room walls along the south and west
    def hdim(x1, x2, y, lab):
        return (f'<g stroke="#b00020" fill="#b00020" stroke-width="1.2"><line x1="{X(x1)}" y1="{Y(y)}" x2="{X(x2)}" y2="{Y(y)}"/>'
                f'<line x1="{X(x1)}" y1="{Y(y) - 10}" x2="{X(x1)}" y2="{Y(y) + 10}"/><line x1="{X(x2)}" y1="{Y(y) - 10}" x2="{X(x2)}" y2="{Y(y) + 10}"/>'
                f'<text x="{(X(x1) + X(x2)) / 2}" y="{Y(y) - 8}" font-size="17" text-anchor="middle" stroke="none">{lab}</text></g>')
    def vdim(x, y1, y2, lab):
        return (f'<g stroke="#b00020" fill="#b00020" stroke-width="1.2"><line x1="{X(x)}" y1="{Y(y1)}" x2="{X(x)}" y2="{Y(y2)}"/>'
                f'<line x1="{X(x) - 10}" y1="{Y(y1)}" x2="{X(x) + 10}" y2="{Y(y1)}"/><line x1="{X(x) - 10}" y1="{Y(y2)}" x2="{X(x) + 10}" y2="{Y(y2)}"/>'
                f'<text transform="translate({X(x) - 10},{(Y(y1) + Y(y2)) / 2}) rotate(-90)" font-size="17" text-anchor="middle" stroke="none">{lab}</text></g>')
    o.append(hdim(0, B["w"], -3200, "OVERALL " + dual(B["w"])))
    o.append(vdim(-3200, 0, B["h"], "OVERALL " + dual(B["h"])))
    xs = sorted({0, B["w"]} | {r["x"] for r in L["rooms"] if r["y"] == 0} | {r["x"] + r["w"] for r in L["rooms"] if r["y"] == 0})
    for a, b in zip(xs, xs[1:]):
        o.append(hdim(a, b, -1500, dual(b - a)))
    ys = sorted({0, B["h"]} | {r["y"] for r in L["rooms"] if r["x"] == 0} | {r["y"] + r["h"] for r in L["rooms"] if r["x"] == 0})
    for a, b in zip(ys, ys[1:]):
        o.append(vdim(-1500, a, b, dual(b - a)))
    for d in L.get("dims", []):
        o.append(hdim(d["x1"], d["x2"], d["y"], d.get("label", dual(d["x2"] - d["x1"]))) if d["dir"] == "h" else vdim(d["x"], d["y1"], d["y2"], d.get("label", dual(d["y2"] - d["y1"]))))
    # north arrow + scale bar
    nx, ny = 2560, 150
    o.append(f'<g transform="translate({nx},{ny})"><path d="M0,-40 L16,20 L0,8 L-16,20 Z" fill="#111"/><text x="0" y="48" font-size="20" text-anchor="middle" font-weight="bold">N</text></g>')
    sb = 10000 * s
    o.append(f'<g transform="translate({X(0)},{SH - 90})"><rect width="{sb / 2}" height="10" fill="#111"/><rect x="{sb / 2}" width="{sb / 2}" height="10" fill="#fff" stroke="#111"/>'
             f'<text y="-8" font-size="15">0</text><text x="{sb / 2}" y="-8" font-size="15" text-anchor="middle">5 m</text><text x="{sb}" y="-8" font-size="15" text-anchor="middle">10 m [32\'-10"]</text>'
             f'<text x="{sb + 30}" y="10" font-size="16">SCALE 1:{round(1 / k)} on ARCH D (36 x 24 in)</text></g>')
    # right column: equipment schedule, room schedule, legend, checks, title block
    cx, cy = 2640, 230
    o.append(f'<text x="{cx}" y="{cy}" font-size="20" font-weight="bold">EQUIPMENT SCHEDULE</text>')
    cy += 12
    o.append(f'<rect x="{cx}" y="{cy}" width="780" height="22" fill="#eceff1" stroke="#111"/>')
    for t, dx in (("#", 6), ("TAG", 36), ("EQUIPMENT", 136), ("FOOTPRINT mm [in]", 560)):
        o.append(f'<text x="{cx + dx}" y="{cy + 16}" font-size="13" font-weight="bold">{t}</text>')
    cy += 22
    for p in L["equipment"]:
        e = eqs.get(p["tag"], {})
        x, y, w, h = rect_of(p, eqs)
        name = (e.get("name") or p.get("name", ""))[:58]
        o.append(f'<rect x="{cx}" y="{cy}" width="780" height="19" fill="{"#fff8e1" if e.get("product_contact") else "#fff"}" stroke="#90a4ae" stroke-width="0.6"/>'
                 f'<text x="{cx + 6}" y="{cy + 14}" font-size="12">{num[p["tag"]]}</text><text x="{cx + 36}" y="{cy + 14}" font-size="12" font-weight="bold">{p["tag"]}</text>'
                 f'<text x="{cx + 136}" y="{cy + 14}" font-size="11.5">{escape(name)}</text>'
                 f'<text x="{cx + 560}" y="{cy + 14}" font-size="11.5">{w:,.0f} x {h:,.0f} [{w / IN:.0f} x {h / IN:.0f}]</text>')
        cy += 19
    cy += 26
    o.append(f'<text x="{cx}" y="{cy}" font-size="20" font-weight="bold">HYGIENE ZONES</text>')
    cy += 10
    for z, col in ZONE_COLORS.items():
        if not any(r["zone"] == z for r in L["rooms"]):
            continue
        o.append(f'<rect x="{cx}" y="{cy}" width="34" height="18" fill="{col}" stroke="#263238"/><text x="{cx + 44}" y="{cy + 14}" font-size="13">{escape(z)}</text>')
        cy += 24
    cy += 10
    o.append(f'<text x="{cx}" y="{cy}" font-size="20" font-weight="bold">FLOWS</text>')
    cy += 10
    for t, (col, dash) in FLOW_STYLE.items():
        if not any(f["type"] == t for f in L["flows"]):
            continue
        o.append(f'<line x1="{cx}" y1="{cy + 9}" x2="{cx + 60}" y2="{cy + 9}" stroke="{col}" stroke-width="4" stroke-dasharray="{dash}"/><text x="{cx + 72}" y="{cy + 14}" font-size="13">{t}</text>')
        cy += 22
    o.append(f'<rect x="{cx}" y="{cy + 6}" width="34" height="18" fill="#ffe0b2" stroke="#0d47a1"/><text x="{cx + 44}" y="{cy + 20}" font-size="13">equipment with product contact</text>')
    cy += 40
    o.append(f'<text x="{cx}" y="{cy}" font-size="20" font-weight="bold">LAYOUT CHECKS (layout.py)</text>')
    cy += 22
    for key, lab in (("overlaps", "Equipment overlaps"), ("outside_room", "Equipment outside its room"), ("zone_violations", "Zone rule violations"),
                     ("flow_crossings", "Raw/finished or waste/product flow crossings"), ("tight_aisles", f"Gaps under {L['rules']['min_clear_mm']} mm (linked pairs excluded)")):
        v = chk[key]
        o.append(f'<text x="{cx}" y="{cy}" font-size="13" fill="{"#2e7d32" if not v else "#b00020"}">{"PASS" if not v else "CHECK"} · {lab}: {len(v)}</text>')
        cy += 19
        for item in v[:3]:
            o.append(f'<text x="{cx + 20}" y="{cy}" font-size="11.5" fill="#555">{escape(str(item))[:90]}</text>'); cy += 16
    # notes
    ny0 = SH - 470
    o.append(f'<rect x="{cx}" y="{ny0}" width="780" height="150" fill="none" stroke="#111"/><text x="{cx + 10}" y="{ny0 + 22}" font-size="15" font-weight="bold">NOTES</text>')
    for i, n in enumerate(L.get("notes", [])[:7]):
        o.append(f'<text x="{cx + 10}" y="{ny0 + 42 + 16 * i}" font-size="11.5">{escape(n)[:120]}</text>')
    # title block
    ty = SH - 310
    t = L["title"]
    o.append(f'<g><rect x="{cx}" y="{ty}" width="780" height="262" fill="none" stroke="#111" stroke-width="2"/>'
             f'<text x="{cx + 12}" y="{ty + 34}" font-size="26" font-weight="bold">{escape(t["title"])}</text>'
             f'<text x="{cx + 12}" y="{ty + 60}" font-size="16">{escape(t["project"])}</text>'
             f'<line x1="{cx}" y1="{ty + 76}" x2="{cx + 780}" y2="{ty + 76}" stroke="#111"/>')
    cells = [("DRAWING NO.", t["number"]), ("REV", t.get("rev", "A")), ("SCALE", f"1:{round(1 / k)}"), ("UNITS", "mm [ft-in]"),
             ("SHEET", "ARCH D 36 x 24 in"), ("DRAWN", B.DRAWN_BY), ("DATE", t["date"]), ("STATUS", t.get("status", "FOR REVIEW"))]
    for i, (a, b) in enumerate(cells):
        x = cx + 12 + (i % 4) * 192; y = ty + 100 + (i // 4) * 74
        o.append(f'<text x="{x}" y="{y}" font-size="12" fill="#555">{a}</text><text x="{x}" y="{y + 26}" font-size="18" font-weight="bold">{escape(str(b))}</text>')
    o.append('</g>' + B.svg_footer(SW, SH, 13) + '</svg>')
    return "\n".join(o), k


def dxf(L, eqs, path, unit):
    try:
        import ezdxf
    except ImportError:
        return False
    f = 1.0 if unit == "mm" else 1 / IN
    doc = ezdxf.new("R2010"); doc.units = 4 if unit == "mm" else 1
    msp = doc.modelspace()
    for name, col in (("WALLS", 7), ("ROOMS", 8), ("EQUIP", 5), ("RACKS", 9), ("FLOW", 1), ("TEXT", 7), ("DOORS", 3)):
        doc.layers.add(name, color=col)
    B = L["building"]
    rect = lambda x, y, w, h, layer: msp.add_lwpolyline([(x * f, y * f), ((x + w) * f, y * f), ((x + w) * f, (y + h) * f), (x * f, (y + h) * f)], close=True, dxfattribs={"layer": layer})
    rect(0, 0, B["w"], B["h"], "WALLS")
    th = 250 * f
    for r in L["rooms"]:
        rect(r["x"], r["y"], r["w"], r["h"], "ROOMS")
        msp.add_text(r["name"], dxfattribs={"layer": "TEXT", "height": th}).set_placement(((r["x"] + 300) * f, (r["y"] + r["h"] - 600) * f))
    for p in L["equipment"]:
        x, y, w, h = rect_of(p, eqs)
        rect(x, y, w, h, "EQUIP")
        msp.add_text(p["tag"], dxfattribs={"layer": "TEXT", "height": th * 0.6}).set_placement(((x + 100) * f, (y + h / 2) * f))
    for rr in L.get("racks", []):
        for i in range(rr["bays"]):
            if rr["dir"] == "x":
                rect(rr["x"] + i * rr["bay_mm"], rr["y"], rr["bay_mm"], rr["depth_mm"], "RACKS")
            else:
                rect(rr["x"], rr["y"] + i * rr["bay_mm"], rr["depth_mm"], rr["bay_mm"], "RACKS")
    for fl in L["flows"]:
        msp.add_lwpolyline([(a * f, b * f) for a, b in fl["pts"]], dxfattribs={"layer": "FLOW"})
    doc.saveas(path)
    return True


def run(layout_path, equipment_path, out_dir):
    L = json.loads(pathlib.Path(layout_path).read_text())
    eqs = {e["tag"]: e for e in json.loads(pathlib.Path(equipment_path).read_text())}
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    chk = checks(L, eqs)
    s, k = svg(L, eqs, chk)
    (out / "LAY-001_plant_layout.svg").write_text(s)
    dxf(L, eqs, out / "LAY-001_plant_layout_mm.dxf", "mm")
    dxf(L, eqs, out / "LAY-001_plant_layout_in.dxf", "in")
    rooms = [dict(name=r["name"], zone=r["zone"], area_m2=round(r["w"] * r["h"] / 1e6, 1), area_ft2=round(r["w"] * r["h"] / FT ** 2)) for r in L["rooms"]]
    chk["rooms"] = rooms; chk["scale"] = f"1:{round(1 / k)}"
    (out / "layout-check.json").write_text(json.dumps(chk, indent=1))
    md = ["# Layout check", "", f"Scale {chk['scale']} on ARCH D.", ""]
    for key in ("overlaps", "outside_room", "zone_violations", "flow_crossings", "tight_aisles"):
        md.append(f"- **{key}**: {len(chk[key])}" + ("" if not chk[key] else " — " + "; ".join(map(str, chk[key]))))
    md += ["", "| Room | Zone | m² | ft² |", "|---|---|---|---|"] + [f"| {r['name']} | {r['zone']} | {r['area_m2']} | {r['area_ft2']:,} |" for r in rooms]
    (out / "layout-check.md").write_text("\n".join(md) + "\n")
    return chk


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    c = run(*sys.argv[1:])
    print({k: len(v) for k, v in c.items() if isinstance(v, list)})
