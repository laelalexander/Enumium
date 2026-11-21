# Precision engineering: real parts, not shapes

A part is not finished when it looks right. It is finished when a machinist, a printer bureau or a supplier can
make it from the package, and it will fit and carry its load. This file sets that bar for every part of a physical
product. It applies together with `hardware-engineering.md` (calculations, mechanism check), `drawings.md` (how it is
drawn), `industrial-design.md` (how it looks) and `parts-and-bom.md` (how it is bought).

**Where Blender fits.** Blender (and the Design Studio's sculpt round trip) is for looks and concept intent only:
renders, livery, a hand-sculpted target shape. It never produces a part. Every shape that comes from Blender is
rebuilt as feature-based CAD before it can be graded above Concept.

**The CAD.** Parts are built in parametric, feature-based B-rep CAD: build123d (OpenCascade) driven by the project's
parameter file, with FreeCAD (same kernel) for FEA (CalculiX) and checks when that is easier. Every BUILD part exports
STEP (AP214/AP242) from the script. Meshes (STL, GLB) are derived outputs, never the source.

## 1. Classify every part

| Class | What it is | Examples |
|---|---|---|
| `precision` | Has a fit, a bearing or seal seat, a locating feature, or a tolerance under ±0.1 mm | gimbal knuckle, hub node, shafts, collars, housings, gear blanks |
| `structural` | Carries a primary load; fit is secondary | wings, rails, pylons, brackets, frames, monocoque, skids |
| `cosmetic` | Covers, fairings, trim; no load beyond itself | nose cone, engine cover, consoles |
| `bought` | Purchased; the vendor owns its geometry | motors, bearings, fasteners, inverters, computers |

## 2. What each part needs

### All BUILD parts
- **Feature-based CAD.** The part is built from features (extrude/revolve/loft/sweep, then holes, pockets, fillets,
  chamfers, drafts), not as a union of boxes and cylinders. Every edge that is not a functional sharp edge has a
  fillet or chamfer of a stated size. Internal corners follow the tool radius of the process.
- **Real hole features.** Every hole is a feature with its spec in the CAD source and the drawing: diameter and
  tolerance, depth, thread (e.g. M8×1.25-6H, 16 deep, full thread 13), counterbore or countersink, and the fastener
  it takes. Holes exist in the CAD, not only on the drawing.
- **Material and process.** A full material specification (e.g. "Al 6061-T6 plate, ASTM B209", "Ti-6Al-4V ELI LPBF
  per ASTM F3001, HIP, stress relieved") and the process route (e.g. "LPBF → HIP → 5-axis finish machining of bores
  and faces → anodise"), with the stock size or build orientation.
- **Mass properties** from the CAD (volume × density), matched against the mass budget.
- **DFM check for the process.** Minimum wall and rib thickness, tool access and reach (length/diameter), internal
  corner radius ≥ tool radius, draft for moulded/cast/laid-up parts, overhang and support strategy for printed parts,
  bend radius and relief for sheet metal, weld access for weldments. Record the numbers checked.

### Additionally for `precision` parts
- **Datum scheme.** Primary/secondary/tertiary datums chosen from how the part is located in the assembly
  (e.g. A = bearing bore, B = flange face, C = dowel hole), written in the CAD source and on the drawing.
- **Fits.** Every mating cylindrical feature gets an ISO 286 fit chosen for its function (bearing seat on a rotating
  shaft: k5/k6; housing for an outer race: H7/J7; locating pin: H7/m6; sliding: H7/g6; clearance bolt holes per ISO
  273 medium). Give the limits in mm and inches.
- **GD&T (ASME Y14.5 / ISO 1101).** Position on hole patterns, perpendicularity/parallelism of mounting faces,
  concentricity/runout of bores and seats, flatness of sealing faces, profile for aerodynamic surfaces. Each control
  references the datums.
- **Surface finish.** Ra per surface (bearing seats Ra 0.4–0.8 µm, sealing faces Ra 0.8–1.6, general machined
  Ra 3.2, as-printed or as-cast noted).
- **Heat treatment, coating, and inspection** (hardness, anodise class and thickness, NDT for critical printed or
  welded parts).

### Additionally for `structural` parts (and `precision` parts in the load path)
- **Load cases** from the design basis (limit and ultimate, e.g. 2.6 g × 1.5), written down with their source.
- **FEA** on the real CAD: FreeCAD FEM with CalculiX (headless: `FreeCADCmd` script), or another solver you can run.
  Mesh convergence on the peak (two mesh sizes within 5 %), von Mises (metals) or ply failure index (composites),
  deflection, and the **margin of safety** = allowable / (applied × factor) − 1 ≥ 0. Save the input deck, the result
  summary and a stress plot image. Where FEA cannot run, do a hand calculation with the arithmetic shown, and say so.
- **Fatigue** for rotating or cyclically loaded parts (rotor hubs, shafts, gimbals): stress range, cycles, S-N source.

### `bought` parts
- The vendor's STEP in `mechanical/vendor/` with its source URL, or, only when none is published, a datasheet model
  with every interface feature at its datasheet dimension (flange, pilot, bolt circle, shaft, connector), with the
  datasheet page cited. A box is never acceptable for a bought part in an Engineered assembly.
- Interface checks: the mating part's fit, bolt pattern and clearance match the vendor's drawing.

### Assemblies
- **Tolerance stack-ups** (worst case and RSS) for every critical clearance or alignment: rotor tip gap, bearing
  preload, gear mesh, seal squeeze, anything that must line up across three or more parts. Show the chain, each
  contributor's tolerance, and the result against the requirement.
- The mechanism and interference check in `hardware-engineering.md` on the Engineered geometry.

## 3. The grade

Every part carries a grade in `prototype/mechanical/engineering.json`, keyed by the assembly mesh file name:

```json
{
  "parts": {
    "FL_knuckle.stl": {
      "part_no": "GM-04", "class": "precision", "grade": "engineered",
      "step": "mechanical/step/GM-04_FL_knuckle_mm.step",
      "material": "Ti-6Al-4V ELI, LPBF per ASTM F3001, HIP",
      "process": "LPBF (Z up, supports on flange back) → HIP → 5-axis finish of bores and faces",
      "datums": "A: bearing bore Ø125 H7; B: actuator flange face; C: Ø8 dowel hole",
      "fits": [{"feature": "outer-race bore", "fit": "Ø125 H7", "limits_mm": "125.000/125.040", "limits_in": "4.9213/4.9228"}],
      "gdt": ["bore Ø125: cylindricity 0.008; runout 0.010 A", "flange face: perpendicularity 0.02 A", "6× M10 holes: position Ø0.1 A B C"],
      "finish": "Ra 0.8 bore; Ra 1.6 flange face; Ra 3.2 elsewhere",
      "holes": [{"id": "H1", "qty": 6, "spec": "M10×1.5-6H, 20 deep, full thread 16, on PCD 160", "fastener": "ISO 4762 M10×30 12.9"}],
      "fea": {"tool": "FreeCAD 1.0 / CalculiX 2.22", "load_case": "2.6 g limit × 1.5 + actuator stall 940 N m",
              "max_stress_MPa": 412, "allowable_MPa": 830, "factor": 1.5, "margin": 0.34, "converged": true,
              "report": "mechanical/fea/GM-04/report.md"},
      "stackups": [{"name": "rotor tip gap", "worst_case_mm": "6.0 ± 1.4", "rss_mm": "6.0 ± 0.7", "requirement": "≥ 3.0", "pass": true, "report": "mechanical/stackups/tip-gap.md"}],
      "dfm": {"pass": true, "checks": ["min wall 4.0 ≥ 1.5 (LPBF Ti)", "overhang 38° ≥ 35°", "tool reach 3.2×D ≤ 4×D"]},
      "mass_kg": 2.41, "drawing": "HX-G-004", "inspection": "CMM on A/B/C and bore; FAI per AS9102",
      "open": []
    }
  }
}
```

Grades, checked by `tools/eng/check_engineering.py`:

- **Concept**: shape and position only. Allowed while exploring, never in a build package.
- **Engineered**: all of §2 for its class except FEA margins and stack-ups, and the STEP passes the feature scan
  (real holes and fillets present, not a bare primitive).
- **Verified**: Engineered, plus FEA with a margin ≥ 0 (structural, and precision in the load path), every fit
  covered by a stack-up that passes, and an inspection plan.

A project is **build-ready** only when every `precision` and `structural` part is Verified and every other part is
at least Engineered. The hand-off summary states the count per grade. The app's Design Studio shows each part's
grade and the evidence, and flags any part whose STEP still looks like a primitive.

## 4. Run the checks

```
python tools/eng/check_engineering.py prototype/mechanical/engineering.json --root <project> --out prototype/mechanical/engineering-report.md
```

It reads each part's STEP with build123d, measures the features (holes by diameter, fillet and chamfer counts, face
types, volume, bounding box), cross-checks them with the record (holes declared vs found, mass vs CAD), recomputes the
grade from the evidence, and writes the report. A part whose recorded grade is higher than the evidence supports is
reported as a failure. Fix the part, not the record.
