"""Read an uploaded part file and measure what quoting and routing need.

Meshes (STL, 3MF, OBJ, PLY) are read with trimesh; 2D drawings (DXF) with ezdxf.
All lengths are millimetres. STL files carry no units, so they are taken as mm.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

MESH_EXTS = {".stl", ".3mf", ".obj", ".ply"}
DRAWING_EXTS = {".dxf"}
SUPPORTED_EXTS = MESH_EXTS | DRAWING_EXTS

# A mesh counts as a flat sheet part when every vertex lies on one of two
# parallel planes, within this tolerance (mm).
FLAT_TOLERANCE_MM = 0.02
# Thickest part the laser line will consider.
MAX_SHEET_THICKNESS_MM = 12.0

# DXF $INSUNITS code -> millimetres per drawing unit.
DXF_UNITS_TO_MM = {0: 1.0, 1: 25.4, 2: 304.8, 4: 1.0, 5: 10.0, 6: 1000.0}


class GeometryError(ValueError):
    """The file could not be read as a part."""


@dataclass
class PartGeometry:
    kind: str  # "mesh" or "drawing"
    extents_mm: list[float]  # bounding box size, x y z (z is 0 for drawings)
    volume_mm3: float = 0.0
    flat: bool = False  # a sheet part: one thickness, straight sides
    thickness_mm: float | None = None
    outline_mm: list[float] | None = None  # 2D size of a sheet part, sorted large to small
    cut_length_mm: float = 0.0
    watertight: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PartGeometry":
        return cls(**data)


def analyze(path: Path) -> PartGeometry:
    ext = path.suffix.lower()
    if ext in MESH_EXTS:
        return _analyze_mesh(path, ext)
    if ext in DRAWING_EXTS:
        return _analyze_dxf(path)
    raise GeometryError(f"Unsupported file type {ext}")


def load_mesh(path: Path):
    import trimesh

    try:
        loaded = trimesh.load(str(path), file_type=path.suffix.lower().lstrip("."), force="mesh")
    except Exception as exc:  # trimesh raises many exception types on bad files
        raise GeometryError(f"Could not read the model: {exc}") from exc
    if loaded is None or len(getattr(loaded, "vertices", [])) == 0:
        raise GeometryError("The model has no geometry")
    return loaded


def _analyze_mesh(path: Path, ext: str) -> PartGeometry:
    mesh = load_mesh(path)
    extents = [float(v) for v in mesh.extents]
    issues: list[str] = []

    watertight = bool(mesh.is_watertight)
    volume = float(abs(mesh.volume)) if watertight else float(abs(mesh.convex_hull.volume))
    if not watertight:
        issues.append("The model has holes in its surface, so its volume is estimated. Printing may fail.")
    if min(extents) < 0.8:
        issues.append("A dimension is under 0.8 mm, which is thinner than the printers can make reliably.")

    geom = PartGeometry(
        kind="mesh",
        extents_mm=extents,
        volume_mm3=volume,
        watertight=watertight,
        issues=issues,
    )

    axis = _flat_axis(mesh.vertices, extents)
    if axis is not None:
        thickness = extents[axis]
        outline = sorted((extents[i] for i in range(3) if i != axis), reverse=True)
        geom.flat = True
        geom.thickness_mm = round(thickness, 3)
        geom.outline_mm = outline
        geom.cut_length_mm = _mesh_cut_length(mesh, axis)
    return geom


def _flat_axis(vertices: np.ndarray, extents: list[float]) -> int | None:
    """Axis along which every vertex sits on the top or bottom face, if any."""
    candidates = []
    for axis in range(3):
        thickness = extents[axis]
        if thickness <= 0 or thickness > MAX_SHEET_THICKNESS_MM:
            continue
        coords = vertices[:, axis]
        lo, hi = coords.min(), coords.max()
        on_faces = (np.abs(coords - lo) <= FLAT_TOLERANCE_MM) | (np.abs(coords - hi) <= FLAT_TOLERANCE_MM)
        if bool(on_faces.all()):
            candidates.append((thickness, axis))
    if not candidates:
        return None
    return min(candidates)[1]


def _mesh_cut_length(mesh, axis: int) -> float:
    normal = [0.0, 0.0, 0.0]
    normal[axis] = 1.0
    origin = mesh.bounds.mean(axis=0)
    section = mesh.section(plane_origin=origin, plane_normal=normal)
    if section is None:
        return 0.0
    return float(section.length)


def _analyze_dxf(path: Path) -> PartGeometry:
    import ezdxf
    from ezdxf import bbox
    from ezdxf import path as ezpath

    try:
        doc = ezdxf.readfile(str(path))
    except (IOError, ezdxf.DXFStructureError) as exc:
        raise GeometryError(f"Could not read the drawing: {exc}") from exc

    scale = DXF_UNITS_TO_MM.get(int(doc.header.get("$INSUNITS", 0)), 1.0)
    msp = doc.modelspace()
    cut_types = ("LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC", "ELLIPSE", "SPLINE")
    length = 0.0
    count = 0
    for entity in msp.query(" ".join(cut_types)):
        try:
            pts = list(ezpath.make_path(entity).flattening(0.05))
        except (TypeError, ValueError):
            continue
        count += 1
        for a, b in zip(pts, pts[1:]):
            length += math.dist((a.x, a.y), (b.x, b.y))

    if count == 0:
        raise GeometryError("The drawing has no lines, arcs or curves to cut")

    box = bbox.extents(msp.query(" ".join(cut_types)))
    width = float(box.size.x) * scale
    height = float(box.size.y) * scale
    outline = sorted([width, height], reverse=True)
    issues = []
    if scale == 1.0 and int(doc.header.get("$INSUNITS", 0)) == 0:
        issues.append("The drawing has no units set, so it was read as millimetres.")
    return PartGeometry(
        kind="drawing",
        extents_mm=[width, height, 0.0],
        flat=True,
        outline_mm=outline,
        cut_length_mm=length * scale,
        issues=issues,
    )


def dxf_preview_svg(path: Path, max_px: int = 480) -> str:
    """A simple SVG outline of a DXF for the quote page."""
    import ezdxf
    from ezdxf import path as ezpath

    doc = ezdxf.readfile(str(path))
    polylines = []
    for entity in doc.modelspace().query("LINE LWPOLYLINE POLYLINE CIRCLE ARC ELLIPSE SPLINE"):
        try:
            polylines.append([(p.x, p.y) for p in ezpath.make_path(entity).flattening(0.1)])
        except (TypeError, ValueError):
            continue
    points = [p for line in polylines for p in line]
    if not points:
        return ""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    w, h = max(max_x - min_x, 1e-6), max(max_y - min_y, 1e-6)
    s = max_px / max(w, h)
    pad = 8
    paths = []
    for line in polylines:
        d = " ".join(
            f"{'M' if i == 0 else 'L'}{(x - min_x) * s + pad:.2f} {(max_y - y) * s + pad:.2f}"
            for i, (x, y) in enumerate(line)
        )
        paths.append(f'<path d="{d}"/>')
    vw, vh = w * s + 2 * pad, h * s + 2 * pad
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.0f} {vh:.0f}" class="dxf-preview">'
        f'<g fill="none" stroke="currentColor" stroke-width="1.2">{"".join(paths)}</g></svg>'
    )


def export_preview_stl(source: Path, target: Path) -> None:
    """Write an STL copy of any mesh so the browser viewer only needs one loader."""
    load_mesh(source).export(str(target), file_type="stl")


def dxf_to_mesh(path: Path, thickness_mm: float):
    """Extrude a DXF drawing into a sheet part, so drawings get a 3D view too.

    Closed outlines are filled even-odd: an outline inside another becomes a hole.
    """
    import ezdxf
    import trimesh
    from ezdxf import path as ezpath
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    doc = ezdxf.readfile(str(path))
    scale = DXF_UNITS_TO_MM.get(int(doc.header.get("$INSUNITS", 0)), 1.0)
    rings = []
    for entity in doc.modelspace().query("LWPOLYLINE POLYLINE CIRCLE ELLIPSE SPLINE ARC LINE"):
        if entity.dxf.layer.upper() == "ENGRAVE":
            continue  # engraving marks the surface; it doesn't change the solid
        try:
            pts = [(p.x * scale, p.y * scale) for p in ezpath.make_path(entity).flattening(0.05)]
        except (TypeError, ValueError):
            continue
        if len(pts) >= 3 and math.dist(pts[0], pts[-1]) < 0.01:
            poly = Polygon(pts).buffer(0)
            if poly.area > 0:
                rings.append(poly)
    if not rings:
        # Open line work only: show a thin plate the size of the drawing.
        g = _analyze_dxf(path)
        w, h = g.extents_mm[:2]
        return trimesh.creation.box(extents=(w, h, thickness_mm))
    rings.sort(key=lambda p: p.area, reverse=True)
    shape = rings[0]
    for ring in rings[1:]:
        shape = shape.symmetric_difference(ring)
    shape = unary_union(shape)
    polys = list(shape.geoms) if hasattr(shape, "geoms") else [shape]
    meshes = [trimesh.creation.extrude_polygon(p, height=thickness_mm) for p in polys if p.area > 0]
    return trimesh.util.concatenate(meshes)
