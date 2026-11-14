# AI workflow: request → validated CAD part

```
request (+ optional sketch) ─► SPEC (LLM, JSON) ─► GENERATE (LLM, CadQuery code)
        ▲                                                   │
        │ errors fed back (max N iterations)                ▼
        └──────────── REPAIR ◄── VALIDATE ◄── EXECUTE (subprocess, timeout)
                                      │ pass
                                      ▼
                        out/<name>/ part.py · .step · .stl · report.json
```

Validation checks: valid B-rep, exactly one solid, positive volume, bounding box
matches the spec, minimum feature size (warning).

## Setup
```bash
pip install cadquery anthropic pytest
export ANTHROPIC_API_KEY=...
```

## Use
```bash
python pipeline.py "L-bracket 60x30 mm base, 25 mm tall flange, two M5 holes"
python pipeline.py --image sketch.png "bracket matching this sketch"
python pipeline.py --code examples/bracket.py --spec examples/bracket.json   # no LLM
python -m pytest -q tests
```

## Notes
- Generated code runs in a subprocess with timeout and memory/CPU limits. That is
  not a security sandbox; run in a container for untrusted input.
- Extension points: add checks in `runner.validate` (wall thickness, overhang
  analysis, mass), add a render-and-critique step (render STL, send to a vision
  model) between VALIDATE and PUBLISH, or add a retrieval step of example parts
  to the GENERATE prompt.
- The LLM stages (`make_spec`, `generate`) are untested here without an API key;
  the execute/validate/export stages are covered by `tests/`.

## Desktop robot arm (primary use case)

4-DOF arm (yaw, shoulder, elbow, wrist pitch + lead-screw gripper): Amazon-orderable parts,
3D-printed joints, 5 lb payload, never beyond 4 ft (default 39.4 in).

```bash
python -m arm.build                       # size drives, generate + validate parts, write BOM
python -m arm.build --extension-m 1.219   # full 4 ft (margin drops to ~2.15x at the shoulder)
```
- `docs/ASSEMBLY.md`: step-by-step build, wiring, firmware, load-test procedure; `docs/WIRING.md` pin table.
- `design/`: STEP + STL files, dimensioned drawings, assembly and joint-section sheets, wiring schematic (`python -m arm.drawings`).
- `docs/BOM.md`: generated bill of materials with Amazon search terms (verify specs; no ASINs).
- `arm/design.py`: static torque sizing with 2x margin; finds that 5 lb needs belt reduction
  (5:1 shoulder, 3:1 elbow) on top of NEMA 23 20:1 planetary gearmotors.
- `arm/hardware.py`: printed-part generators (draft geometry; set the `HW` dimensions from your parts).
- `firmware/arm_controller/`: Arduino Mega + AccelStepper (uncompiled/untested on hardware).
- `arm/control.py`: `Arm` (IK, limits, step conversion), `SimDriver`, `SerialDriver`.

Limits: gearbox ratings come from vendor listings and were not confirmed on Amazon; the arm drops
on power loss; printed parts and firmware are unverified on real hardware.
