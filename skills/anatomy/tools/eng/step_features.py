"""Measure the real features of a STEP part: what a machinist would see, not what the mesh looks like.

    python step_features.py part.step [--json]

Prints JSON: bounding box, volume and area, face counts by surface type, holes (internal cylindrical faces grouped by
diameter and axis, with through/blind and depth), external cylinders (bosses, shafts), fillets and chamfers (blend
faces), threads (only if modelled), and a `primitive` flag for a part that is still a bare box or cylinder.
Needs build123d (OpenCascade). Used by check_engineering.py and by the Anatomy Design Studio.
"""
import json
import math
import sys
from collections import defaultdict

from build123d import import_step, GeomType, Vector

R = lambda v, n=3: round(float(v), n)


def _axis_key(d):
    d = Vector(d).normalized()
    # orient the axis consistently so +Z and -Z are the same axis
    for c in (d.Z, d.Y, d.X):
        if abs(c) > 1e-6:
            if c < 0:
                d = -d
            break
    return (R(d.X, 3), R(d.Y, 3), R(d.Z, 3))


def _cyl(face):
    """(radius, axis_dir, axis_point) of a cylindrical face, from OpenCascade."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    s = BRepAdaptor_Surface(face.wrapped).Cylinder()
    ax = s.Axis()
    d, p = ax.Direction(), ax.Location()
    return s.Radius(), Vector(d.X(), d.Y(), d.Z()), Vector(p.X(), p.Y(), p.Z())


def _is_internal(face, axis_dir, axis_pt):
    """A hole's surface faces its axis: the normal at the face centre points toward the axis."""
    c = face.center()
    n = face.normal_at(c)
    v = c - axis_pt
    radial = v - axis_dir * v.dot(axis_dir)
    if radial.length < 1e-9:
        return False
    return n.dot(radial.normalized()) < 0


def _extent_along(face, axis_dir):
    bb = face.bounding_box()
    pts = [Vector(x, y, z) for x in (bb.min.X, bb.max.X) for y in (bb.min.Y, bb.max.Y) for z in (bb.min.Z, bb.max.Z)]
    proj = [p.dot(axis_dir) for p in pts]
    return min(proj), max(proj)


def measure(path):
    shape = import_step(path)
    solids = shape.solids()
    bb = shape.bounding_box()
    size = [bb.size.X, bb.size.Y, bb.size.Z]
    L = max(size) or 1.0
    faces = shape.faces()
    by_type = defaultdict(int)
    holes = defaultdict(lambda: {"count": 0, "depths": []})
    bosses = defaultdict(int)
    blends = {"fillet": 0, "chamfer": 0, "fillet_radii": set()}
    threads = 0
    for f in faces:
        gt = f.geom_type
        name = gt.name if hasattr(gt, "name") else str(gt)
        by_type[name] += 1
        if gt == GeomType.CYLINDER:
            try:
                r, d, p = _cyl(f)
            except Exception:
                continue
            lo, hi = _extent_along(f, d.normalized())
            length = hi - lo
            if _is_internal(f, d.normalized(), p):
                key = (R(2 * r, 3), _axis_key(d))
                holes[key]["count"] += 1
                holes[key]["depths"].append(R(length, 2))
            elif r < 0.08 * L and length < 2.5 * r:
                # small convex cylinder patch along an edge: a fillet
                blends["fillet"] += 1
                blends["fillet_radii"].add(R(r, 2))
            else:
                bosses[R(2 * r, 3)] += 1
        elif gt == GeomType.TORUS:
            blends["fillet"] += 1
        elif gt == GeomType.CONE:
            bb_f = f.bounding_box()
            if max(bb_f.size.X, bb_f.size.Y, bb_f.size.Z) < 0.1 * L:
                blends["chamfer"] += 1  # countersinks and conical chamfers
        if "thread" in (getattr(f, "label", "") or "").lower():
            threads += 1
    # planar chamfers: thin planar strips meeting two faces at ~45 deg are hard to tell from ribs; count narrow strips
    for f in shape.faces().filter_by(GeomType.PLANE):
        fb = f.bounding_box()
        dims = sorted([fb.size.X, fb.size.Y, fb.size.Z])
        if dims[1] > 0 and dims[1] < 0.03 * L and dims[2] > 4 * dims[1]:
            n = f.normal_at(f.center())
            if all(abs(c) < 0.95 for c in (n.X, n.Y, n.Z)):
                blends["chamfer"] += 1
    vol = sum(s.volume for s in solids) if solids else 0.0
    nf = len(faces)
    box_vol = size[0] * size[1] * size[2] or 1.0
    primitive = (nf <= 6 and by_type.get("PLANE", 0) == nf) or (nf <= 3 and by_type.get("CYLINDER", 0) >= 1) or \
                (vol / box_vol > 0.97 and nf <= 10)
    hole_list = []
    for (dia, axis), h in sorted(holes.items(), key=lambda kv: -kv[0][0]):
        hole_list.append({"diameter_mm": dia, "diameter_in": R(dia / 25.4, 4), "axis": axis, "faces": h["count"],
                          "depth_mm": max(h["depths"]) if h["depths"] else None})
    return {
        "file": path,
        "solids": len(solids),
        "bbox_mm": [R(v, 2) for v in size],
        "volume_mm3": R(vol, 1),
        "area_mm2": R(shape.area, 1),
        "faces": nf,
        "edges": len(shape.edges()),
        "face_types": dict(by_type),
        "holes": hole_list,
        "hole_count": sum(h["faces"] for h in hole_list),
        "bosses": [{"diameter_mm": d, "faces": n} for d, n in sorted(bosses.items(), key=lambda kv: -kv[0])],
        "fillets": blends["fillet"],
        "fillet_radii_mm": sorted(blends["fillet_radii"]),
        "chamfers": blends["chamfer"],
        "threads_modelled": threads,
        "primitive": bool(primitive),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    out = [measure(p) for p in sys.argv[1:] if not p.startswith("--")]
    print(json.dumps(out[0] if len(out) == 1 else out, indent=1))
