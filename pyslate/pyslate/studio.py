"""Design studio: turn a customer's 2D design into a DXF (to laser cut) or an STL (to 3D print).

A design is a list of shapes in millimetres, drawn in screen coordinates (y points down).
Every shape is a closed cut path. Shapes inside other shapes become holes (even-odd fill),
which is also how a laser cuts them.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

SHAPE_TYPES = {"rect", "circle", "slot", "polygon", "poly"}
MAX_POLY_POINTS = 5000
MAX_TOTAL_POINTS = 80000
ENGRAVE_LAYER = "ENGRAVE"
MAX_SHAPES = 200
MIN_MM, MAX_MM = 0.5, 1000.0
MAX_COORD = 2000.0
LASER, PRINT, CNC, ROUTER, PLASMA = "laser", "print", "cnc", "router", "plasma"
PROCESSES = {LASER: "laser cut", PRINT: "3D print", CNC: "CNC machined", ROUTER: "CNC routed", PLASMA: "plasma cut"}
SOLID_PROCESSES = (PRINT, CNC)  # the outline is extruded to a height


class DesignError(ValueError):
    pass


def _num(value, name: str, lo: float, hi: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise DesignError(f"{name} must be a number") from None
    if not math.isfinite(v) or not lo <= v <= hi:
        raise DesignError(f"{name} must be between {lo:g} and {hi:g}")
    return v


def validate_design(raw: str | dict) -> dict:
    """Parse and check a design. Returns a clean copy with only known fields."""
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        raise DesignError("The design could not be read") from None
    if not isinstance(data, dict) or not isinstance(data.get("shapes"), list):
        raise DesignError("The design could not be read")
    shapes = data["shapes"]
    if not shapes:
        raise DesignError("Add at least one shape to your design")
    if len(shapes) > MAX_SHAPES:
        raise DesignError(f"A design can have up to {MAX_SHAPES} shapes")
    clean = []
    total_points = 0
    for i, s in enumerate(shapes, 1):
        if not isinstance(s, dict) or s.get("type") not in SHAPE_TYPES:
            raise DesignError(f"Shape {i} is not a shape the studio knows")
        t = s["type"]
        if t == "poly":
            pts = s.get("pts")
            if not isinstance(pts, list) or not 2 <= len(pts) <= MAX_POLY_POINTS:
                raise DesignError(f"Line {i} needs between 2 and {MAX_POLY_POINTS} points")
            total_points += len(pts)
            if total_points > MAX_TOTAL_POINTS:
                raise DesignError("The design has too much detail. Use shorter text or fewer lines.")
            clean_pts = []
            for p in pts:
                if not isinstance(p, (list, tuple)) or len(p) != 2:
                    raise DesignError(f"Line {i} has a bad point")
                clean_pts.append([_num(p[0], f"Line {i} point", -MAX_COORD, MAX_COORD),
                                  _num(p[1], f"Line {i} point", -MAX_COORD, MAX_COORD)])
            closed = bool(s.get("closed")) and len(clean_pts) >= 3
            clean.append({"type": "poly", "pts": clean_pts, "closed": closed, "engrave": bool(s.get("engrave"))})
            continue
        c = {
            "type": t,
            "x": _num(s.get("x"), f"Shape {i} position", -MAX_COORD, MAX_COORD),
            "y": _num(s.get("y"), f"Shape {i} position", -MAX_COORD, MAX_COORD),
            "rot": _num(s.get("rot", 0), f"Shape {i} rotation", -360, 360),
        }
        if t == "circle":
            c["d"] = _num(s.get("d"), f"Shape {i} diameter", MIN_MM, MAX_MM)
        elif t == "polygon":
            c["d"] = _num(s.get("d"), f"Shape {i} size", MIN_MM, MAX_MM)
            c["n"] = int(_num(s.get("n", 6), f"Shape {i} sides", 3, 24))
        else:
            c["w"] = _num(s.get("w"), f"Shape {i} width", MIN_MM, MAX_MM)
            c["h"] = _num(s.get("h"), f"Shape {i} height", MIN_MM, MAX_MM)
            if t == "rect":
                c["r"] = min(_num(s.get("r", 0), f"Shape {i} corner radius", 0, MAX_MM / 2), min(c["w"], c["h"]) / 2)
        clean.append(c)
    return {"shapes": clean}


def _rounded_rect(w: float, h: float, r: float, seg: int = 10) -> list[tuple[float, float]]:
    if r <= 1e-6:
        return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    pts = []
    corners = [(w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)]
    for cx, cy, start in corners:
        for k in range(seg + 1):
            a = math.radians(start + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def shape_points(s: dict) -> list[tuple[float, float]]:
    """Outline of a non-circle shape in drawing coordinates (y up), not closed."""
    t = s["type"]
    if t == "poly":
        return [(x, -y) for x, y in s["pts"]]
    if t == "rect":
        local = _rounded_rect(s["w"], s["h"], s["r"])
    elif t == "slot":
        local = _rounded_rect(s["w"], s["h"], min(s["w"], s["h"]) / 2)
    elif t == "polygon":
        n, r = s["n"], s["d"] / 2
        local = [(r * math.cos(math.radians(-90 + 360 * k / n)), r * math.sin(math.radians(-90 + 360 * k / n))) for k in range(n)]
    else:
        raise DesignError("Circles are drawn as circles")
    a = math.radians(s["rot"])
    ca, sa = math.cos(a), math.sin(a)
    # Rotate in screen space, then flip y so the drawing matches what the customer saw.
    return [(s["x"] + px * ca - py * sa, -(s["y"] + px * sa + py * ca)) for px, py in local]


def design_to_dxf(design: dict, target: Path) -> None:
    import ezdxf

    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # millimetres
    doc.layers.add(ENGRAVE_LAYER, color=5)
    msp = doc.modelspace()
    for s in design["shapes"]:
        if s["type"] == "circle":
            msp.add_circle((s["x"], -s["y"]), s["d"] / 2)
        elif s["type"] == "poly":
            attribs = {"layer": ENGRAVE_LAYER} if s["engrave"] else {}
            msp.add_lwpolyline(shape_points(s), close=s["closed"], dxfattribs=attribs)
        else:
            msp.add_lwpolyline(shape_points(s), close=True)
    doc.saveas(str(target))


def solid_shapes(design: dict) -> dict:
    """Only the closed cut outlines: what a 3D print is extruded from."""
    return {"shapes": [s for s in design["shapes"] if s["type"] != "poly" or (s["closed"] and not s["engrave"])]}


def design_to_stl(design: dict, height_mm: float, target: Path, work_dir: Path) -> None:
    from . import geometry as geo

    solid = solid_shapes(design)
    if not solid["shapes"]:
        raise DesignError("A 3D print needs at least one closed shape. Lines and engraving alone can't be printed.")
    dxf = work_dir / "studio-extrude.dxf"
    design_to_dxf(solid, dxf)
    mesh = geo.dxf_to_mesh(dxf, height_mm)
    mesh.export(str(target), file_type="stl")
