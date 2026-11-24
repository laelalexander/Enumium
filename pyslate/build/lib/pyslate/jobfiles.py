"""Machine-ready files for a job.

Sheet jobs (laser, router, plasma) get the part's outline as true-size SVG and DXF, with
as many copies as fit on the machine's bed laid out in a grid. xTool Studio, LightBurn,
SheetCAM and Fusion all import these. Print, CNC and molding jobs use the customer's file
as it is; the shop agent slices prints on the shop PC.

Layers / SVG colours follow the shop's DXF convention: CUT (red) is cut through,
ENGRAVE (blue) is marked on the surface.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from . import geometry as geo

GAP_MM = 3.0  # space between copies and around the sheet edge
CUT, ENGRAVE = "CUT", "ENGRAVE"
SVG_COLOURS = {CUT: "#ff0000", ENGRAVE: "#0000ff"}


class JobFileError(ValueError):
    pass


@dataclass
class Outline:
    """A part's 2D line work in mm, origin at the bottom-left of its bounding box."""

    paths: list[tuple[str, list[tuple[float, float]]]]  # (layer, points)
    width: float
    height: float


@dataclass
class Layout:
    per_sheet: int
    sheets: int
    columns: int
    rows: int
    rotated: bool


def outline_for(part_file: Path, engrave_only: bool = False) -> Outline:
    ext = part_file.suffix.lower()
    if ext in geo.DRAWING_EXTS:
        paths = _dxf_paths(part_file)
    elif ext in geo.MESH_EXTS:
        paths = _mesh_paths(part_file)
    else:
        raise JobFileError(f"No 2D outline can be made from {ext} files")
    if engrave_only:
        # The design's outline is the blank's size: everything is marked, nothing is cut.
        paths = [(ENGRAVE, pts) for _, pts in paths]
    return _normalise(paths)


def _dxf_paths(path: Path):
    import ezdxf
    from ezdxf import path as ezpath

    doc = ezdxf.readfile(str(path))
    scale = geo.DXF_UNITS_TO_MM.get(int(doc.header.get("$INSUNITS", 0)), 1.0)
    out = []
    for entity in doc.modelspace().query("LINE LWPOLYLINE POLYLINE CIRCLE ARC ELLIPSE SPLINE"):
        layer = entity.dxf.layer.upper()
        kind = ENGRAVE if layer in ("ENGRAVE", "MARK") or layer.startswith("ENGRAVE") else CUT
        try:
            pts = [(p.x * scale, p.y * scale) for p in ezpath.make_path(entity).flattening(0.05)]
        except (TypeError, ValueError):
            continue
        if len(pts) >= 2:
            out.append((kind, pts))
    if not out:
        raise JobFileError("The drawing has no line work")
    return out


def _mesh_paths(path: Path):
    """Section a flat mesh through its middle to get the cut outline."""
    import numpy as np

    mesh = geo.load_mesh(path)
    extents = [float(v) for v in mesh.extents]
    axis = geo._flat_axis(mesh.vertices, extents)
    if axis is None:
        raise JobFileError("This model is not a flat sheet part, so it has no cut outline")
    normal = [0.0, 0.0, 0.0]
    normal[axis] = 1.0
    section = mesh.section(plane_origin=mesh.bounds.mean(axis=0), plane_normal=normal)
    if section is None:
        raise JobFileError("Could not find the part's outline")
    keep = [i for i in range(3) if i != axis]
    out = []
    for loop in section.discrete:
        pts = np.asarray(loop)[:, keep]
        out.append((CUT, [(float(x), float(y)) for x, y in pts]))
    return out


def _normalise(paths) -> Outline:
    xs = [x for _, pts in paths for x, _ in pts]
    ys = [y for _, pts in paths for _, y in pts]
    min_x, min_y = min(xs), min(ys)
    moved = [(kind, [(x - min_x, y - min_y) for x, y in pts]) for kind, pts in paths]
    return Outline(moved, max(xs) - min_x, max(ys) - min_y)


def plan_layout(width: float, height: float, bed: list[float], copies: int) -> Layout:
    """How many copies fit on one bed in a simple grid, trying the part both ways round."""
    bed_w, bed_h = float(bed[0]), float(bed[1])
    best = None
    for rotated, (w, h) in ((False, (width, height)), (True, (height, width))):
        cols = int((bed_w - GAP_MM) // (w + GAP_MM))
        rows = int((bed_h - GAP_MM) // (h + GAP_MM))
        if cols >= 1 and rows >= 1 and (best is None or cols * rows > best[0] * best[1]):
            best = (cols, rows, rotated)
    if best is None:
        raise JobFileError(f"A {width:.0f} x {height:.0f} mm part does not fit the {bed_w:.0f} x {bed_h:.0f} mm bed")
    cols, rows, rotated = best
    per_sheet = min(copies, cols * rows)
    cols = min(cols, per_sheet)
    rows = math.ceil(per_sheet / cols)
    return Layout(per_sheet, math.ceil(copies / per_sheet), cols, rows, rotated)


def _placed(outline: Outline, layout: Layout):
    """Yield (layer, points) for every copy on one sheet, in bed millimetres (y up)."""
    w, h = (outline.height, outline.width) if layout.rotated else (outline.width, outline.height)
    for i in range(layout.per_sheet):
        col, row = i % layout.columns, i // layout.columns
        ox = GAP_MM + col * (w + GAP_MM)
        oy = GAP_MM + row * (h + GAP_MM)
        for kind, pts in outline.paths:
            if layout.rotated:  # quarter turn: (x, y) -> (h - y, x) within the copy's box
                pts = [(outline.height - y, x) for x, y in pts]
            yield kind, [(x + ox, y + oy) for x, y in pts]


def sheet_size(outline: Outline, layout: Layout) -> tuple[float, float]:
    w, h = (outline.height, outline.width) if layout.rotated else (outline.width, outline.height)
    return layout.columns * (w + GAP_MM) + GAP_MM, layout.rows * (h + GAP_MM) + GAP_MM


def write_svg(outline: Outline, layout: Layout, target: Path, title: str = "") -> None:
    sw, sh = sheet_size(outline, layout)
    parts = []
    for kind in (ENGRAVE, CUT):  # engrave first, then cut, so parts don't shift before marking
        ds = []
        for k, pts in _placed(outline, layout):
            if k != kind:
                continue
            closed = len(pts) > 2 and math.dist(pts[0], pts[-1]) < 0.01
            d = "M" + " L".join(f"{x:.3f} {sh - y:.3f}" for x, y in pts) + (" Z" if closed else "")
            ds.append(f'<path d="{d}"/>')
        if ds:
            parts.append(
                f'<g id="{kind.lower()}" fill="none" stroke="{SVG_COLOURS[kind]}" stroke-width="0.1">{"".join(ds)}</g>'
            )
    head = f"<title>{_xml(title)}</title>" if title else ""
    target.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sw:.3f}mm" height="{sh:.3f}mm" '
        f'viewBox="0 0 {sw:.3f} {sh:.3f}">{head}{"".join(parts)}</svg>\n',
        encoding="utf-8",
    )


def write_dxf(outline: Outline, layout: Layout, target: Path) -> None:
    import ezdxf

    doc = ezdxf.new(units=4)  # millimetres
    doc.layers.add(CUT, color=1)
    doc.layers.add(ENGRAVE, color=5)
    msp = doc.modelspace()
    for kind, pts in _placed(outline, layout):
        closed = len(pts) > 2 and math.dist(pts[0], pts[-1]) < 0.01
        msp.add_lwpolyline(pts[:-1] if closed else pts, close=closed, dxfattribs={"layer": kind})
    doc.saveas(target)


def _xml(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
