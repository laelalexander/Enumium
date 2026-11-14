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

Pipeline for a programmable 4-DOF arm (yaw, shoulder, elbow, wrist pitch) built on real actuators.

```bash
python -m arm.build --reach 300 --payload 0.1    # size actuators, generate + validate parts, BOM
```
1. `arm/actuators.py`: actuator catalog (dimensions, torque, mass, interface). Values are
   approximate; check datasheets and edit for the parts you own.
2. `arm/design.py`: worst-case (arm horizontal) torque per joint, 2× safety margin, picks the
   smallest actuator that passes, iterating because actuator mass adds load. It raises if
   nothing in the catalog is strong enough.
3. Parts (base, upper arm, forearm) are generated with pockets sized to the chosen actuator,
   then run through the validate/export pipeline above (STEP + STL in `out/arm/`, plus
   `design.json` with the BOM).
4. `arm/kinematics.py` (IK/FK) and `arm/control.py` (`Arm`, `SimDriver`, `PCA9685Driver`)
   are the programming layer:
   ```python
   from arm.control import Arm, SimDriver
   arm = Arm(SimDriver(), l1=150, l2=150)
   arm.move_to(180, 60, 40)
   ```
For freeform parts (gripper, custom brackets) use `pipeline.py` and put the actuator's
dimensions in the request.

Known limits: the example BOM mixes PWM and TTL-serial actuators, so restrict the catalog
to one interface before building. Joint zero/limits in `control.py` are placeholders for
your calibration. No Dynamixel driver is included. Torque model ignores dynamics, so it is
static only. Printed parts are untested physically.
