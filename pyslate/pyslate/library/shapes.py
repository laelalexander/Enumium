"""Shape helpers for library designs.

Library designs use the design studio's client format (millimetres, y down,
x/y is the centre of each shape) so the studio can open them as they are:

    rect    {type, x, y, w, h, r, rot}
    circle  {type, x, y, d}
    slot    {type, x, y, w, h, rot}
    polygon {type, x, y, d, n, rot}
    path    {type, x, y, pts: [[dx, dy], ...] relative to x/y, closed, engrave}
    text    {type, x, y, text, size, font, engrave}

This module turns those shapes into the server format (for DXF quotes),
into outlines (for previews and bounds), and into an SVG preview.
"""

from __future__ import annotations

import math
from html import escape

from .. import studio

ROUND = 2  # decimals kept in coordinates


def r2(v: float) -> float:
    return round(float(v), ROUND)


def path(pts, closed: bool = True, engrave: bool = False) -> dict:
    """A path shape from absolute points, centred on its bounding box."""
    pts = [(float(x), float(y)) for x, y in pts]
    if closed and len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return {"type": "path", "x": r2(cx), "y": r2(cy), "rot": 0,
            "pts": [[r2(x - cx), r2(y - cy)] for x, y in pts], "closed": closed and len(pts) >= 3,
            "engrave": engrave}


def circle(x: float, y: float, d: float) -> dict:
    return {"type": "circle", "x": r2(x), "y": r2(y), "d": r2(d)}


def rect(x: float, y: float, w: float, h: float, r: float = 0, rot: float = 0) -> dict:
    return {"type": "rect", "x": r2(x), "y": r2(y), "w": r2(w), "h": r2(h), "r": r2(r), "rot": rot}


def ring(x: float, y: float, d: float, engrave: bool = True, seg: int = 96) -> dict:
    """A circle as a closed path, so it can be engraved."""
    return path([(x + d / 2 * math.cos(2 * math.pi * k / seg), y + d / 2 * math.sin(2 * math.pi * k / seg))
                 for k in range(seg)], closed=True, engrave=engrave)


def polygon_paths(geom, engrave: bool = False, min_area: float = 0.5) -> list[dict]:
    """Shapely polygon(s) to closed path shapes: exteriors and holes."""
    polys = getattr(geom, "geoms", [geom])
    out = []
    for p in polys:
        if p.is_empty or p.area < min_area:
            continue
        out.append(path(list(p.exterior.coords), True, engrave))
        for hole in p.interiors:
            out.append(path(list(hole.coords), True, engrave))
    return out


def to_server(shape: dict) -> dict:
    """Client shape to the studio's server format. Text can't be converted here."""
    t = shape["type"]
    if t == "path":
        x, y = shape["x"], shape["y"]
        a = math.radians(shape.get("rot", 0) or 0)
        ca, sa = math.cos(a), math.sin(a)
        pts = [[x + px * ca - py * sa, y + px * sa + py * ca] for px, py in shape["pts"]]
        return {"type": "poly", "pts": pts, "closed": bool(shape.get("closed")), "engrave": bool(shape.get("engrave"))}
    if t == "text":
        raise studio.DesignError("Designs with text are priced in the design studio")
    return dict(shape)


def has_text(shapes: list[dict]) -> bool:
    return any(s["type"] == "text" for s in shapes)


def server_design(shapes: list[dict]) -> dict:
    return studio.validate_design({"shapes": [to_server(s) for s in shapes]})


def outline(shape: dict) -> tuple[list[tuple[float, float]], bool]:
    """Points in screen coordinates (y down) and whether the outline is closed."""
    t = shape["type"]
    if t == "circle":
        r = shape["d"] / 2
        return [(shape["x"] + r * math.cos(2 * math.pi * k / 72), shape["y"] + r * math.sin(2 * math.pi * k / 72))
                for k in range(72)], True
    if t == "text":
        size = shape.get("size", 10)
        w = 0.6 * size * len(shape.get("text", ""))
        x, y = shape["x"], shape["y"]
        return [(x - w / 2, y - size / 2), (x + w / 2, y - size / 2), (x + w / 2, y + size / 2), (x - w / 2, y + size / 2)], True
    s = to_server(shape)
    if s["type"] == "poly":
        return [(px, py) for px, py in s["pts"]], s["closed"]
    clean = {**s, "rot": s.get("rot", 0) or 0}
    if t == "rect":
        clean.setdefault("r", 0)
    return [(px, -py) for px, py in studio.shape_points(clean)], True


def bounds(shapes: list[dict]) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for s in shapes:
        pts, _ = outline(s)
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def size_mm(shapes: list[dict]) -> tuple[float, float]:
    x0, y0, x1, y1 = bounds(shapes)
    return r2(x1 - x0), r2(y1 - y0)


def translate(shapes: list[dict], dx: float, dy: float) -> list[dict]:
    return [{**s, "x": r2(s["x"] + dx), "y": r2(s["y"] + dy)} for s in shapes]


def centre(shapes: list[dict]) -> list[dict]:
    """Move a design so its bounding box starts at a 10 mm margin from the board corner."""
    x0, y0, _, _ = bounds(shapes)
    return translate(shapes, 10 - x0, 10 - y0)


def _d(pts, closed: bool) -> str:
    if not pts:
        return ""
    d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
    return d + (" Z" if closed else "")


WOOD = "#e8c79a"
CUT = "#7a4a1f"
ENGRAVE = "#5b3a1a"


def preview_svg(shapes: list[dict], title: str = "", fill: str = WOOD) -> str:
    """A flat drawing of the design: cut parts filled with the material, engraving drawn on top."""
    x0, y0, x1, y1 = bounds(shapes)
    pad = max(x1 - x0, y1 - y0) * 0.04 + 1
    vb = f"{x0 - pad:.2f} {y0 - pad:.2f} {x1 - x0 + 2 * pad:.2f} {y1 - y0 + 2 * pad:.2f}"
    stroke = max(x1 - x0, y1 - y0) / 400
    solid, lines, fills, texts = [], [], [], []
    for s in shapes:
        if s["type"] == "text":
            texts.append(s)
            continue
        pts, closed = outline(s)
        if s.get("engrave"):
            (fills if closed and s.get("fill") else lines).append(_d(pts, closed))
        elif closed:
            solid.append(_d(pts, True))
        else:
            lines.append(_d(pts, False))
    vw, vh = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    k = 480 / max(vw, vh)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{vw * k:.0f}" height="{vh * k:.0f}" role="img">']
    if title:
        out.append(f"<title>{escape(title)}</title>")
    if solid:
        out.append(f'<path d="{" ".join(solid)}" fill="{fill}" fill-rule="evenodd" stroke="{CUT}" '
                   f'stroke-width="{stroke * 1.4:.3f}" stroke-linejoin="round"/>')
    if fills:
        out.append(f'<path d="{" ".join(fills)}" fill="{ENGRAVE}" fill-opacity=".85" fill-rule="evenodd"/>')
    if lines:
        out.append(f'<path d="{" ".join(lines)}" fill="none" stroke="{ENGRAVE}" stroke-width="{stroke * 1.6:.3f}" '
                   'stroke-linecap="round" stroke-linejoin="round"/>')
    for t in texts:
        family = "Allerta Stencil, sans-serif" if t.get("font") == "stencil" else "Inter, Arial, sans-serif"
        out.append(f'<text x="{t["x"]:.2f}" y="{t["y"]:.2f}" font-size="{t.get("size", 10):.2f}" '
                   f'font-family="{family}" font-weight="700" text-anchor="middle" dominant-baseline="central" '
                   f'fill="{ENGRAVE}">{escape(t.get("text", ""))}</text>')
    out.append("</svg>")
    return "".join(out)
