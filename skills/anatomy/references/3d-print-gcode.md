# 3D printed parts: from model to verified G-code

Printed parts are often most of a prototype, so this is a major part of the prototype phase with a high bar. The deliverable for every printed part is **ready-to-print G-code for the user's printer**, plus the project file and settings that produced it, and evidence that the part will print and fit.

## 0. Know the printer and material
Read the user's printer and material settings from `C:\Anatomy\anatomy-settings.md` (or the project's `CLAUDE.md` / `inputs/`). You need: printer model, bed size, nozzle diameter, firmware flavor (Marlin, Klipper, Prusa, Bambu), available materials, and any slicer profile files the user supplied (`.ini`, `.3mf`, `.json`). If none is given, use the default **Bambu Lab, 256 x 256 x 256 mm plate, 0.4 mm nozzle, PLA/PETG** (the user's printer family; model not yet confirmed), mark the exact model `[assumed]`, and say clearly that the G-code must be re-sliced for their printer. Never silently assume.

## 1. Design for printing (in the parametric model)
- Wall thickness ≥ 3 perimeters of the nozzle width (≥ 1.2 mm at 0.4 mm), ribs and bosses sized for strength.
- Overhangs ≤ 45° or designed-in supports/chamfers; bridges ≤ ~20 mm; avoid supports on cosmetic or mating faces.
- Hole compensation: holes print undersize. Design clearance (e.g. +0.2 to +0.3 mm on diameter for fits, horizontal holes teardrop or flat-topped).
- Fits and joints: clearance 0.2-0.4 mm for sliding fits, heat-set insert holes per insert datasheet, snap-fits checked for strain against the material, threads printed only ≥ M6 (otherwise inserts or nuts).
- Orientation chosen for strength (layer lines across the load, not along it), accuracy of critical faces, and minimum support. Split parts that exceed the bed or need different orientations, with alignment pins/dowels and a fastening method.
- Elephant-foot chamfer (0.3-0.5 mm) on bed-facing edges of mating parts.

## 2. Export and check the mesh
- Export STL (or 3MF) in mm from the parametric source. One file per part, named by BOM line and part name.
- Check each mesh by script (trimesh or similar): watertight/manifold, no inverted normals, correct units and bounding box, fits the bed in the chosen orientation, minimum wall thickness, volume and estimated mass.

## 3. Slice to G-code (headless)
G-code comes only from a real slicer, never written by hand. If no slicer can run, stop at checked STL/3MF files plus the ready profile `.ini` files, label the parts "not sliced", and tell the user what to install. Use a slicer CLI so the result is reproducible.

**Bambu Lab printers (the default here):** deliver **Bambu Studio-ready project files**: one `.3mf` per plate with the parts placed, oriented, and the process/filament settings applied, so the user opens it in Bambu Studio and presses Print. Slice them with the Bambu Studio CLI when it is installed (`bambu-studio.exe`, typically `C:\Program Files\Bambu Studio\`; run `bambu-studio.exe --help` to confirm flags, e.g. `--slice 0 --export-3mf plate1.gcode.3mf --load-settings "machine.json;process.json" --load-filaments filament.json part.stl`), producing `.gcode.3mf` files the printer accepts. If Bambu Studio is not installed, use OrcaSlicer (which ships Bambu profiles) or PrusaSlicer with a Bambu-equivalent printer profile to check sliceability, time and weight, label that G-code "reference only, re-slice in Bambu Studio", and still deliver the Bambu `.3mf` projects.

Other printers: **PrusaSlicer** (`prusa-slicer-console.exe` on Windows, `prusa-slicer` elsewhere; install `winget install Prusa3D.PrusaSlicer` if missing, telling the user). OrcaSlicer or the user's own slicer is fine if they supply a profile.
```
prusa-slicer-console --export-gcode --load printer.ini --load print.ini --load filament.ini \
  --center X,Y --ensure-on-bed -o print/gcode/<part>.gcode print/stl/<part>.stl
prusa-slicer-console --export-3mf -o print/project/<part>.3mf ...   # project with settings, for the user to open and adjust
```
- build123d/CadQuery models are centred on the origin: always pass `--ensure-on-bed` and `--center X,Y` (bed centre), or PrusaSlicer rejects the part as outside the print volume.
- Pass `--filament-density` (PLA ≈ 1.24, PETG ≈ 1.27, ABS/ASA ≈ 1.05, TPU ≈ 1.21 g/cm³) or the G-code reports 0 g and the BOM filament weight is wrong.
- Store the exact `.ini` profiles used in `print/profiles/` and record the settings per part in `print/print-settings.csv`: material, layer height, perimeters, top/bottom layers, infill % and pattern, supports (type, where), brim, orientation, nozzle and bed temperature.
- Choose settings per part by function: structural parts (more perimeters, higher infill, PETG/ASA/PA where heat or load matters), cosmetic parts (finer layers, ironing), flexible parts (TPU).
- Plate multiple small parts together where sensible and produce plate G-code as well as per-part G-code.

## 4. Verify the G-code
Parse every G-code file by script and fail if anything is off:
- Moves stay inside the bed volume; the first layer height and temperatures match the profile; the flavor's start/end G-code is present.
- Extract estimated print time and filament length/weight from the slicer's footer; total them per material.
- Render a preview image of each part's toolpath or sliced layers (a layer at ~25%, 50%, 75% height, plus the first layer) and look at them for gaps, missing walls, floating islands and support where it should not be.

## 5. Deliver
```
print/
  stl/            one STL/3MF per part
  gcode/          per-part and per-plate G-code, named <bom-line>-<part>-<material>-<layer>.gcode
  project/        slicer project files (.3mf) the user can open and re-slice
  profiles/       exact printer/print/filament profiles used
  print-settings.csv
  print-plan.md   order to print, plates, totals (time, filament g and m, cost), material per part,
                  post-processing (supports to remove, inserts to set, sanding), test-fit checklist
  previews/       toolpath and layer previews
```
Every printed part is a BUILD line in `bom/bom.csv` whose `design_file` points to its source and whose STL and G-code exist (the BOM gate checks this). Filament is a BUY line.

## 6. Print report and first-article check
For each printed part write a short print report in `print-plan.md`: why this orientation, where supports go and why, why this material and infill. Add a first-article checklist: 3 to 5 critical dimensions to measure with calipers after the first print, each with nominal value and pass limits (e.g. insert bore Ø4.0 +0.1/-0.05), and what to change in the model if a check fails.

## 7. Say what is verified
G-code that slices and passes the checks is **checked by script**, not printed. List the fits most likely to need tuning (inserts, press fits, snap-fits, mating faces) and suggest a small test coupon to print first for each critical fit.
