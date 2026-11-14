"""Executes generated CadQuery code in an isolated subprocess, validates the
solid and exports STEP + STL.  Invoked as:

    python -I runner.py <code.py> <outdir> <spec.json>

Prints one JSON report on stdout.  Never imports project code, so it is safe
to run with `-I`.  NOT a hardened sandbox: it only adds a timeout, memory/CPU
limits and a scratch cwd.  Run inside a container for untrusted prompts.
"""
import json, resource, sys, traceback
from pathlib import Path


def validate(shape, spec):
    import cadquery as cq
    errors, warnings, m = [], [], {}
    solid = shape.val() if hasattr(shape, "val") else shape
    if not solid.isValid():
        errors.append("Shape is not a valid B-rep (self-intersection or bad faces).")
    solids = shape.solids().vals() if hasattr(shape, "solids") else [solid]
    m["solid_count"] = len(solids)
    if len(solids) != 1:
        errors.append(f"Expected exactly 1 solid, got {len(solids)}; union/connect the pieces.")
    m["volume_mm3"] = round(solid.Volume(), 3)
    if m["volume_mm3"] <= 0:
        errors.append("Volume is non-positive.")
    bb = solid.BoundingBox()
    dims = sorted([bb.xlen, bb.ylen, bb.zlen])
    m["bbox_mm"] = [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)]
    m["face_count"] = len(solid.Faces())

    # Check against the spec's expected bounding box (order-independent).
    exp = spec.get("bbox_mm")
    tol = spec.get("bbox_tolerance_mm", 0.5)
    if exp:
        for got, want in zip(dims, sorted(exp)):
            if abs(got - want) > tol:
                errors.append(f"Bounding box {m['bbox_mm']} does not match spec {exp} (±{tol} mm).")
                break
    min_feat = spec.get("min_feature_mm", 0.8)
    if dims[0] < min_feat:
        warnings.append(f"Smallest dimension {dims[0]:.2f} mm < min feature {min_feat} mm.")
    if m["volume_mm3"] > 0:
        m["bbox_fill_ratio"] = round(m["volume_mm3"] / (bb.xlen * bb.ylen * bb.zlen), 3)
    return errors, warnings, m


def main(code_path, outdir, spec_path):
    resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    resource.setrlimit(resource.RLIMIT_CPU, (110, 110))
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(spec_path).read_text())
    report = {"ok": False, "errors": [], "warnings": [], "metrics": {}, "files": {}}
    try:
        import cadquery as cq
        ns = {"cq": cq, "__name__": "generated"}
        exec(compile(Path(code_path).read_text(), "generated.py", "exec"), ns)
        if "result" not in ns:
            raise ValueError("Code must assign the final cq.Workplane to a variable named `result`.")
        result = ns["result"]
        errors, warnings, metrics = validate(result, spec)
        report.update(errors=errors, warnings=warnings, metrics=metrics)
        if not errors:
            stem = spec.get("name", "part")
            cq.exporters.export(result, str(out / f"{stem}.step"))
            cq.exporters.export(result, str(out / f"{stem}.stl"), tolerance=0.01, angularTolerance=0.1)
            report["files"] = {"step": f"{stem}.step", "stl": f"{stem}.stl"}
            report["ok"] = True
    except BaseException:
        tb = traceback.format_exc().splitlines()
        report["errors"].append("Exception: " + " | ".join(tb[-4:]))
    print(json.dumps(report))


if __name__ == "__main__":
    main(*sys.argv[1:4])
