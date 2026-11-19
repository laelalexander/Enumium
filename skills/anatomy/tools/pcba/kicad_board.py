"""Read a KiCad 8/9/10 .kicad_pcb file into plain Python data, with no KiCad install needed.

Only what a PCBA order package needs is read: layers, outline, footprints (reference,
value, properties, attributes, side, position, pads, fab graphics), vias and track widths.
Coordinates are KiCad board coordinates in mm (X right, Y down).
"""
import math
import re

_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')


class Str(str):
    """A quoted string atom (so "1" and 1 can be told apart)."""


def parse_sexpr(text):
    stack, cur = [], []
    pos, n = 0, len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("bad s-expression near offset %d" % pos)
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(Str(m.group(3).replace('\\"', '"').replace("\\\\", "\\")))
        else:
            cur.append(m.group(4))
    if len(cur) != 1:
        raise ValueError("expected one top-level expression")
    return cur[0]


def head(node):
    return node[0] if isinstance(node, list) and node else None


def kids(node, name):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def xy(node):
    return (num(node[1]), num(node[2])) if node and len(node) >= 3 else (0.0, 0.0)


def rotate(px, py, deg):
    """KiCad rotation: positive angle turns counter-clockwise on screen (Y down)."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return px * c + py * s, -px * s + py * c


def _layer_of(node):
    l = kid(node, "layer")
    return str(l[1]) if l else ""


def _graphic(node, fx=0.0, fy=0.0, frot=0.0):
    """Return a graphic item in board coordinates: dict(kind, layer, pts or center/radius, width)."""
    kind = node[0].split("_", 1)[1]  # line, rect, circle, arc, poly
    w = kid(node, "stroke")
    width = num(kid(w, "width")[1]) if w and kid(w, "width") else num((kid(node, "width") or [0, 0.1])[1], 0.1)
    filled = False
    f = kid(node, "fill")
    if f and len(f) > 1 and str(f[1]) in ("solid", "yes"):
        filled = True

    def tr(p):
        x, y = rotate(p[0], p[1], frot) if frot else p
        return (x + fx, y + fy)

    g = {"kind": kind, "layer": _layer_of(node), "width": width, "filled": filled}
    if kind in ("line", "arc"):
        pts = [xy(kid(node, "start")), xy(kid(node, "end"))]
        if kind == "arc" and kid(node, "mid"):
            pts.insert(1, xy(kid(node, "mid")))
        g["pts"] = [tr(p) for p in pts]
    elif kind == "rect":
        (x0, y0), (x1, y1) = xy(kid(node, "start")), xy(kid(node, "end"))
        g["pts"] = [tr(p) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))]
    elif kind == "circle":
        c, e = xy(kid(node, "center")), xy(kid(node, "end"))
        g["center"] = tr(c)
        g["radius"] = math.hypot(e[0] - c[0], e[1] - c[1])
    elif kind == "poly":
        p = kid(node, "pts")
        pts = [xy(q) for q in kids(p, "xy")] if p else []
        g["pts"] = [tr(q) for q in pts] + ([tr(pts[0])] if pts else [])
    else:
        return None
    return g


def arc_points(p0, pm, p1, steps=24):
    """Points along a 3-point arc."""
    (ax, ay), (bx, by), (cx, cy) = p0, pm, p1
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [p0, p1]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in (p0, pm, p1))

    def between(a, s, e):  # is a on the ccw sweep s->e
        return (a - s) % (2 * math.pi) <= (e - s) % (2 * math.pi)

    sweep = (a1 - a0) % (2 * math.pi)
    if not between(am, a0, a1):
        sweep -= 2 * math.pi
    return [(ux + r * math.cos(a0 + sweep * i / steps), uy + r * math.sin(a0 + sweep * i / steps)) for i in range(steps + 1)]


def load_board(path):
    with open(path, encoding="utf-8") as fh:
        root = parse_sexpr(fh.read())
    if head(root) != "kicad_pcb":
        raise ValueError("%s is not a .kicad_pcb file" % path)
    b = {"path": path, "version": str((kid(root, "version") or [0, "?"])[1])}
    gen = kid(root, "generator_version")
    b["generator_version"] = str(gen[1]) if gen else ""
    g = kid(root, "general")
    b["thickness_mm"] = num(kid(g, "thickness")[1], 1.6) if g and kid(g, "thickness") else 1.6

    layers = kid(root, "layers")
    b["copper_layers"] = [str(l[1]) for l in layers[1:] if isinstance(l, list) and str(l[1]).endswith(".Cu")] if layers else ["F.Cu", "B.Cu"]

    setup = kid(root, "setup") or ["setup"]
    st = kid(setup, "stackup")
    b["stackup"] = None
    if st:
        rows = []
        for l in kids(st, "layer"):
            rows.append({"name": str(l[1]), "type": str((kid(l, "type") or ["", ""])[1]),
                         "thickness": num((kid(l, "thickness") or [0, 0])[1]),
                         "material": str((kid(l, "material") or ["", ""])[1])})
        fin = kid(st, "copper_finish")
        b["stackup"] = {"layers": rows, "copper_finish": str(fin[1]) if fin else ""}
    ao = kid(setup, "aux_axis_origin")
    b["aux_origin"] = xy(ao) if ao else None

    # Outline
    edges = []
    for n in root[1:]:
        if isinstance(n, list) and n and str(n[0]).startswith("gr_") and _layer_of(n) == "Edge.Cuts":
            gi = _graphic(n)
            if gi:
                edges.append(gi)

    fps = []
    for f in kids(root, "footprint"):
        at = kid(f, "at")
        fx, fy = xy(at)
        frot = num(at[3]) if at and len(at) > 3 else 0.0
        props = {}
        for p in kids(f, "property"):
            props[str(p[1])] = str(p[2]) if len(p) > 2 else ""
        # KiCad 6/7 used fp_text reference/value
        for t in kids(f, "fp_text"):
            if str(t[1]) in ("reference", "value"):
                props.setdefault(str(t[1]).title(), str(t[2]))
        attr = kid(f, "attr")
        attrs = set(str(a) for a in attr[1:]) if attr else set()
        side = "bottom" if _layer_of(f) == "B.Cu" else "top"
        pads = []
        for p in kids(f, "pad"):
            pat = kid(p, "at")
            px, py = xy(pat)
            prot = num(pat[3]) if pat and len(pat) > 3 else 0.0
            bx, by = rotate(px, py, frot)
            size = kid(p, "size")
            drill = kid(p, "drill")
            dsize = None
            if drill:
                vals = [num(v) for v in drill[1:] if not isinstance(v, list) and str(v) != "oval"]
                if vals:
                    dsize = (vals[0], vals[1] if len(vals) > 1 else vals[0])
            net = kid(p, "net")
            lay = kid(p, "layers")
            pads.append({"num": str(p[1]), "type": str(p[2]), "shape": str(p[3]) if len(p) > 3 else "",
                         "x": fx + bx, "y": fy + by, "rot": prot,
                         "w": num(size[1]) if size else 0.0, "h": num(size[2]) if size and len(size) > 2 else 0.0,
                         "drill": dsize, "net": str(net[-1]) if net else "",
                         "layers": [str(x) for x in lay[1:]] if lay else []})
        gfx = []
        for n in f[1:]:
            if isinstance(n, list) and n and str(n[0]) in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
                gi = _graphic(n, fx, fy, frot)
                if gi:
                    if gi["layer"] == "Edge.Cuts":
                        edges.append(gi)
                    gfx.append(gi)
        lib = str(f[1]) if len(f) > 1 and not isinstance(f[1], list) else ""
        fps.append({"lib": lib, "footprint": lib.split(":")[-1], "ref": props.get("Reference", "?"),
                    "value": props.get("Value", ""), "props": props, "attrs": attrs, "side": side,
                    "x": fx, "y": fy, "rot": frot % 360.0, "pads": pads, "gfx": gfx})
    b["footprints"] = fps

    vias = []
    for v in kids(root, "via"):
        vias.append({"x": xy(kid(v, "at"))[0], "y": xy(kid(v, "at"))[1],
                     "size": num((kid(v, "size") or [0, 0])[1]), "drill": num((kid(v, "drill") or [0, 0])[1])})
    b["vias"] = vias
    widths = [num(kid(t, "width")[1]) for t in kids(root, "segment") + kids(root, "arc") if kid(t, "width")]
    b["track_count"] = len(widths)
    b["min_track_mm"] = min(widths) if widths else None
    b["zones"] = len(kids(root, "zone"))

    pts = []
    for e in edges:
        if e["kind"] == "circle":
            cx, cy, r = e["center"][0], e["center"][1], e["radius"]
            pts += [(cx - r, cy - r), (cx + r, cy + r)]
        elif e["kind"] == "arc" and len(e["pts"]) == 3:
            pts += arc_points(*e["pts"])
        else:
            pts += e.get("pts", [])
    b["edges"] = edges
    if pts:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        b["bbox"] = (min(xs), min(ys), max(xs), max(ys))
    else:
        b["bbox"] = None
    return b
