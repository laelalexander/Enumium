# Build package: from design to something a person can build

A finished prototype is not done until someone with no access to the designer can order, make and assemble it. The build package turns the design into that. The Anatomy app has a **Build** button that asks for this package and a wizard that walks the user through it, driven by `build/build.json`. Produce it at the end of every hardware project, and whenever the user asks to "prepare the build".

Everything below must already meet `parts-and-bom.md`, `drawings.md`, `3d-print-gcode.md` and `software-phase.md`. The build package collects and orders it; it does not lower the bar. Fix gaps (generic parts, missing G-code, undimensioned drawings) before writing the package, or list them as blockers.

## Folder
```
build/
  build.json            the machine-readable plan the app's wizard reads (schema below)
  README.md             one page: what you are building, cost, time, skills, tools, the 5 stages
  1-purchase/           purchase-list.csv (all BUY lines), one <supplier>-cart.csv per supplier in that
                        supplier's BOM-upload format (Digi-Key, Mouser, LCSC, McMaster), order-checklist.md
  2-print/              print-list.csv, gcode/ (per plate and per part, Bambu .gcode.3mf when the printer is Bambu),
                        project/ (.3mf for the slicer), print-plan.md with plates, order, time and filament totals
  3-fabricate/          cut/ DXF in mm and inch, pcb/ <board>-PCBA-rev<rev>.zip from tools/pcba/pcba_export.py
                        (references/pcba-export.md: Gerbers, Excel BOM, centroid, drawings, notes, quote sheet),
                        machined parts STEP + drawings, harness cut lists, vendor-notes.md (what to upload where, settings)
  4-assemble/           steps/ images, assembly-guide.html (self-contained) and .pdf, torque and tool lists
  5-firmware-test/      binaries and flash instructions, bring-up checklist, acceptance tests
```

## build.json schema
```json
{
  "title": "TwinArm robot",
  "summary": "one paragraph",
  "totals": { "parts_cost": 1536.20, "currency": "USD", "print_hours": 41.5, "filament_g": {"PETG": 1830}, "build_hours": 12 },
  "tools": ["hex keys 2/2.5/3 mm", "soldering iron", "multimeter", "M3 heat-set insert tip"],
  "purchase": [
    { "line": "SYS-1", "desc": "Jetson Orin Nano Super 8GB", "mfr": "NVIDIA", "mpn": "945-13766-0005-000", "qty": 1,
      "supplier": "Digi-Key", "url": "https://...", "unit_price": 249.00, "alt": "Seeed 102110767", "notes": "" }
  ],
  "print": [
    { "part": "base_top_plate", "line": "MK-3", "qty": 1, "material": "PETG", "stl": "path", "gcode": "path",
      "plate": 1, "time_min": 212, "grams": 186, "orientation": "flat face down", "supports": "none",
      "after": "set 6x M3 inserts", "checks": ["insert bore Ø4.0 +0.1/-0.05", "OD 210.0 ±0.3"] }
  ],
  "fabricate": [
    { "part": "rcb1 PCBA", "process": "PCB fab + turnkey assembly", "files": ["build/3-fabricate/pcb/rcb1-PCBA-revA.zip"],
      "vendor": "RushPCB (or any turnkey PCBA house)", "settings": "2 layer, 1.6 mm, 2 oz, HASL lead-free, 46 SMT + 9 THT, top only", "qty": 5 },
    { "part": "gasket", "process": "knife/laser cut", "files": ["cut/gasket_mm.dxf", "cut/gasket_in.dxf"], "material": "1.5 mm EPDM" }
  ],
  "assembly": [
    { "step": 1, "title": "Set the heat-set inserts in the base plate", "image": "build/4-assemble/steps/01.png",
      "parts": [{"line": "HW-4", "qty": 6}, {"line": "MK-3", "qty": 1}], "tools": ["soldering iron with insert tip"],
      "text": "plain instructions", "torque": "", "check": "inserts flush, square, no plastic bulge" }
  ],
  "firmware": [
    { "name": "RCB-1 firmware", "dir": "path", "build": "pio run", "flash": "pio run -t upload", "binary": "path", "check": "LED blinks, serial prints READY" }
  ],
  "tests": [ { "name": "Power-up", "steps": ["..."], "expect": "5.0 V ±0.1 on TP1" } ]
}
```
All paths are relative to the project root. Every `purchase` line comes from a BUY line in `bom/bom.csv`; every `print` part and `fabricate` part from a BUILD line. Every part used in an `assembly` step exists in purchase, print or fabricate. Check this with a script (extend `bom/check_bom.py`) and report the result in `build/README.md`.

## Parts sent to Xometry
The Build tab's Xometry stage routes a print or fabricate part to Xometry (xometry.com/quoting) when it is larger than the printer bed in Settings, needs a material that is not in "Materials on hand", or is a metal or engineering-plastic part that is machined or cut by a service; the user can move any part either way. Their choices and quote notes are saved in `build/xometry.json` (`parts.<part>.route` = `xometry` | `home`, plus `material`, `process`, `finish`, `tolerance`, `qty`, `notes`). When you rebuild the package, keep those choices, and make sure every part that goes to Xometry has:
- a STEP file (`print[].step` or `fabricate[].step`, or a `.step` with the same stem as the part or its STL). Xometry quotes CNC only from STEP, and it measures 3D-print quotes from CAD; never point it at a `.gcode.3mf`.
- a PDF drawing in `drawing` (threads, inserts and tight tolerances go on that drawing; Xometry takes it as the technical drawing),
- an exact material name in `material` for the intended service material (for example "PETG", "Nylon 12 (MJF)", "6061-T6 aluminium 6.35 mm").
The app never submits anything to Xometry; "Prepare upload folder" copies the files to `build/xometry/` with `XOMETRY-ORDER.md` and `xometry-parts.csv`.

## Quality bar
- The purchase list is orderable as written: exact SKUs, quantities rounded to pack sizes plus spares, links that go to the exact product.
- Every print entry has G-code that exists, was sliced for the user's printer (see Settings), and has its time and weight from the slicer.
- Every assembly step has a picture rendered from the CAD assembly, with the parts added in that step highlighted.
- An `assembly.json` (see SKILL.md step 6) whose `steps` match these assembly steps one-to-one, so the 3D viewer's Assemble button plays the same build the guide describes.
- Every custom board has a PCBA order package that `pcba_export.py` marks READY, or its blockers are listed in `build/README.md`.
- Nothing in the package says "TBD", "generic" or "see above".
