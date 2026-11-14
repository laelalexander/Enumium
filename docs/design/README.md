# Robot arm design package (DRAFT rev A)

Blueprints, dimensioned part drawings and the wiring schematic for the 4-DOF desktop robot arm
(5 lb payload, 39.4 in reach, never beyond 48 in). Everything here is **generated** by the Python code in
[`3d-workflow/arm/`](../../3d-workflow/arm); edit the sources and rerun, don't hand-edit the drawings.

| What | Source of truth | Rendered output |
|---|---|---|
| Part geometry | [`arm/hardware.py`](../../3d-workflow/arm/hardware.py) (`HW` dimensions) | [`cad/step/`](../../3d-workflow/design/cad/step), [`cad/stl/`](../../3d-workflow/design/cad/stl) |
| Drive sizing | [`arm/design.py`](../../3d-workflow/arm/design.py), [`arm/build.py`](../../3d-workflow/arm/build.py) | [`design.json`](../../3d-workflow/design/design.json), [`BOM.md`](../../3d-workflow/design/BOM.md) |
| Drawings and schematic | [`arm/drawings.py`](../../3d-workflow/arm/drawings.py) | [`drawings/*.svg`](../../3d-workflow/design/drawings), [`schematics/*.svg`](../../3d-workflow/design/schematics) |
| PNG previews | [`arm/render.py`](../../3d-workflow/arm/render.py) | [`png/*.png`](../../3d-workflow/design/png) |

Related: [assembly guide](../../3d-workflow/docs/ASSEMBLY.md), [wiring pin table](../../3d-workflow/docs/WIRING.md),
[firmware](../../3d-workflow/firmware/arm_controller/arm_controller.ino). Click any preview for the full-resolution SVG.

## System sheets

| Sheet | Preview |
|---|---|
| **ELE-001** wiring schematic: PSU, fuse, E-stop, Arduino Mega, 5 stepper drivers, 5 motors<br>[SVG](../../3d-workflow/design/schematics/ELE-001_wiring.svg) · [PNG](../../3d-workflow/design/png/ELE-001_wiring.png) | [<img src="../../3d-workflow/design/png/ELE-001_wiring.png" width="480">](../../3d-workflow/design/schematics/ELE-001_wiring.svg) |
| **ASM-001** arm assembly elevation: link lengths, reach, worst-case pose<br>[SVG](../../3d-workflow/design/drawings/ASM-001_assembly.svg) · [PNG](../../3d-workflow/design/png/ASM-001_assembly.png) | [<img src="../../3d-workflow/design/png/ASM-001_assembly.png" width="480">](../../3d-workflow/design/drawings/ASM-001_assembly.svg) |
| **ASM-002** pitch-joint section: bearings, belt reduction, load path<br>[SVG](../../3d-workflow/design/drawings/ASM-002_joint_section.svg) · [PNG](../../3d-workflow/design/png/ASM-002_joint_section.png) | [<img src="../../3d-workflow/design/png/ASM-002_joint_section.png" width="480">](../../3d-workflow/design/drawings/ASM-002_joint_section.svg) |

## Printed parts

Each sheet is A3, third-angle, front/top/right views with overall dimensions. STEP for CAD/CAM, STL to slice.

| Part | Qty and files | Preview |
|---|---|---|
| **base_top_plate**<br>Rotating plate: yaw hub + turntable + riser socket | x1<br>[SVG](../../3d-workflow/design/drawings/base_top_plate.svg) · [PNG](../../3d-workflow/design/png/base_top_plate.png) · [STEP](../../3d-workflow/design/cad/step/base_top_plate.step) · [STL](../../3d-workflow/design/cad/stl/base_top_plate.stl) | [<img src="../../3d-workflow/design/png/base_top_plate.png" width="360">](../../3d-workflow/design/drawings/base_top_plate.svg) |
| **elbow_cheek_motor**<br>Motor-side cheek plate | x1<br>[SVG](../../3d-workflow/design/drawings/elbow_cheek_motor.svg) · [PNG](../../3d-workflow/design/png/elbow_cheek_motor.png) · [STEP](../../3d-workflow/design/cad/step/elbow_cheek_motor.step) · [STL](../../3d-workflow/design/cad/stl/elbow_cheek_motor.stl) | [<img src="../../3d-workflow/design/png/elbow_cheek_motor.png" width="360">](../../3d-workflow/design/drawings/elbow_cheek_motor.svg) |
| **elbow_cheek_plain**<br>Plain cheek plate | x1<br>[SVG](../../3d-workflow/design/drawings/elbow_cheek_plain.svg) · [PNG](../../3d-workflow/design/png/elbow_cheek_plain.png) · [STEP](../../3d-workflow/design/cad/step/elbow_cheek_plain.step) · [STL](../../3d-workflow/design/cad/stl/elbow_cheek_plain.stl) | [<img src="../../3d-workflow/design/png/elbow_cheek_plain.png" width="360">](../../3d-workflow/design/drawings/elbow_cheek_plain.svg) |
| **elbow_tube_block**<br>Spacer block that clamps the incoming tube | x1<br>[SVG](../../3d-workflow/design/drawings/elbow_tube_block.svg) · [PNG](../../3d-workflow/design/png/elbow_tube_block.png) · [STEP](../../3d-workflow/design/cad/step/elbow_tube_block.step) · [STL](../../3d-workflow/design/cad/stl/elbow_tube_block.stl) | [<img src="../../3d-workflow/design/png/elbow_tube_block.png" width="360">](../../3d-workflow/design/drawings/elbow_tube_block.svg) |
| **gripper_adapter**<br>Tube-stub socket + plate bolting to gripper body (M4 heat-set inserts) | x1<br>[SVG](../../3d-workflow/design/drawings/gripper_adapter.svg) · [PNG](../../3d-workflow/design/png/gripper_adapter.png) · [STEP](../../3d-workflow/design/cad/step/gripper_adapter.step) · [STL](../../3d-workflow/design/cad/stl/gripper_adapter.stl) | [<img src="../../3d-workflow/design/png/gripper_adapter.png" width="360">](../../3d-workflow/design/drawings/gripper_adapter.svg) |
| **gripper_body**<br>NEMA17 lead-screw gripper body + fixed jaw | x1<br>[SVG](../../3d-workflow/design/drawings/gripper_body.svg) · [PNG](../../3d-workflow/design/png/gripper_body.png) · [STEP](../../3d-workflow/design/cad/step/gripper_body.step) · [STL](../../3d-workflow/design/cad/stl/gripper_body.stl) | [<img src="../../3d-workflow/design/png/gripper_body.png" width="360">](../../3d-workflow/design/drawings/gripper_body.svg) |
| **gripper_jaw**<br>Sliding jaw on 2x8 mm rods | x1<br>[SVG](../../3d-workflow/design/drawings/gripper_jaw.svg) · [PNG](../../3d-workflow/design/png/gripper_jaw.png) · [STEP](../../3d-workflow/design/cad/step/gripper_jaw.step) · [STL](../../3d-workflow/design/cad/stl/gripper_jaw.stl) | [<img src="../../3d-workflow/design/png/gripper_jaw.png" width="360">](../../3d-workflow/design/drawings/gripper_jaw.svg) |
| **shoulder_cheek_motor**<br>Motor-side cheek plate | x1<br>[SVG](../../3d-workflow/design/drawings/shoulder_cheek_motor.svg) · [PNG](../../3d-workflow/design/png/shoulder_cheek_motor.png) · [STEP](../../3d-workflow/design/cad/step/shoulder_cheek_motor.step) · [STL](../../3d-workflow/design/cad/stl/shoulder_cheek_motor.stl) | [<img src="../../3d-workflow/design/png/shoulder_cheek_motor.png" width="360">](../../3d-workflow/design/drawings/shoulder_cheek_motor.svg) |
| **shoulder_cheek_plain**<br>Plain cheek plate | x1<br>[SVG](../../3d-workflow/design/drawings/shoulder_cheek_plain.svg) · [PNG](../../3d-workflow/design/png/shoulder_cheek_plain.png) · [STEP](../../3d-workflow/design/cad/step/shoulder_cheek_plain.step) · [STL](../../3d-workflow/design/cad/stl/shoulder_cheek_plain.stl) | [<img src="../../3d-workflow/design/png/shoulder_cheek_plain.png" width="360">](../../3d-workflow/design/drawings/shoulder_cheek_plain.svg) |
| **shoulder_tube_block**<br>Spacer block that clamps the incoming tube | x1<br>[SVG](../../3d-workflow/design/drawings/shoulder_tube_block.svg) · [PNG](../../3d-workflow/design/png/shoulder_tube_block.png) · [STEP](../../3d-workflow/design/cad/step/shoulder_tube_block.step) · [STL](../../3d-workflow/design/cad/stl/shoulder_tube_block.stl) | [<img src="../../3d-workflow/design/png/shoulder_tube_block.png" width="360">](../../3d-workflow/design/drawings/shoulder_tube_block.svg) |
| **tube_socket**<br>Distal link end: hub flange + tube socket (shoulder, elbow, wrist) | x3<br>[SVG](../../3d-workflow/design/drawings/tube_socket.svg) · [PNG](../../3d-workflow/design/png/tube_socket.png) · [STEP](../../3d-workflow/design/cad/step/tube_socket.step) · [STL](../../3d-workflow/design/cad/stl/tube_socket.stl) | [<img src="../../3d-workflow/design/png/tube_socket.png" width="360">](../../3d-workflow/design/drawings/tube_socket.svg) |
| **wrist_cheek_motor**<br>Motor-side cheek plate | x1<br>[SVG](../../3d-workflow/design/drawings/wrist_cheek_motor.svg) · [PNG](../../3d-workflow/design/png/wrist_cheek_motor.png) · [STEP](../../3d-workflow/design/cad/step/wrist_cheek_motor.step) · [STL](../../3d-workflow/design/cad/stl/wrist_cheek_motor.stl) | [<img src="../../3d-workflow/design/png/wrist_cheek_motor.png" width="360">](../../3d-workflow/design/drawings/wrist_cheek_motor.svg) |
| **wrist_cheek_plain**<br>Plain cheek plate | x1<br>[SVG](../../3d-workflow/design/drawings/wrist_cheek_plain.svg) · [PNG](../../3d-workflow/design/png/wrist_cheek_plain.png) · [STEP](../../3d-workflow/design/cad/step/wrist_cheek_plain.step) · [STL](../../3d-workflow/design/cad/stl/wrist_cheek_plain.stl) | [<img src="../../3d-workflow/design/png/wrist_cheek_plain.png" width="360">](../../3d-workflow/design/drawings/wrist_cheek_plain.svg) |
| **wrist_tube_block**<br>Spacer block that clamps the incoming tube | x1<br>[SVG](../../3d-workflow/design/drawings/wrist_tube_block.svg) · [PNG](../../3d-workflow/design/png/wrist_tube_block.png) · [STEP](../../3d-workflow/design/cad/step/wrist_tube_block.step) · [STL](../../3d-workflow/design/cad/stl/wrist_tube_block.stl) | [<img src="../../3d-workflow/design/png/wrist_tube_block.png" width="360">](../../3d-workflow/design/drawings/wrist_tube_block.svg) |

## Regenerating on Windows (your own terminal)

Tested in the cloud on Linux with Python 3.13 and CadQuery 2.8. The Windows steps below use the same commands;
the only Windows-specific parts are installing Python and a PNG renderer.

**1. One-time setup** (PowerShell, not as administrator):

```powershell
winget install -e --id Python.Python.3.12      # skip if `py -3.12 --version` already works
winget install -e --id Inkscape.Inkscape       # optional: PNG export (see step 3)
cd C:\path\to\Enumium\3d-workflow              # wherever you cloned the repo
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1                    # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py check                             # should print "ok" for Python, cadquery, pyserial
```

**2. Regenerate everything** (sizing, CAD, drawings, schematic, index, PNGs). Takes about a minute:

```powershell
.\.venv\Scripts\Activate.ps1
python run.py build
start design\index.html                         # opens the design package in your browser
```

**3. PNGs only** (after editing SVG-producing code, no CAD rebuild): `python run.py png`.
`arm/render.py` uses the first renderer it finds:

- **Inkscape** (simplest on Windows): installed by the winget line above, found on PATH or in `C:\Program Files\Inkscape`.
- **cairosvg**: `pip install cairosvg`. On Windows it also needs the Cairo DLL (for example from the GTK3 runtime
  installer) on PATH; if it is missing, the renderer is skipped automatically.
- **Playwright**: `pip install playwright` then `python -m playwright install chromium`.

If none is present, `build` still writes every SVG and prints how to enable PNGs.

**Changing the design:** measure your purchased gearboxes, hubs and turntable, set the `HW` values in
`3d-workflow/arm/hardware.py`, rerun `python run.py build`, then commit the changed files under `3d-workflow/design/`.
Other options: `python -m arm.build --extension-m 1.219` for the full 4 ft reach, `python run.py sim` to check
kinematics without hardware, `python run.py console` to drive the real arm over USB.

## Status and limits

- DRAFT rev A. Part sheets show overall dimensions and projected geometry; hole sizes are in the sheet notes and in
  `arm/hardware.py`. ASM-001, ASM-002 and ELE-001 are schematic, not to scale.
- The parts depend on `HW` dimensions that must be measured on the purchased parts before printing.
- Gearbox ratings come from vendor listings; printed parts and firmware are unverified on real hardware.
- CI (`.github/workflows/design.yml`) runs the tests, regenerates the package and renders the PNGs on every push
  that touches `3d-workflow/`, and uploads them as a build artifact.
