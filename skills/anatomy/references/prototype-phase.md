# Prototype phase

The blueprint proves you understand the product; the prototype proves the blueprint is buildable. Build the smallest thing that demonstrates the core of the rebuild spec, and make it viewable by the user without extra setup. Pick the mode from the product type (ask if ambiguous; combine modes for hybrid products).

Put everything in `anatomy-<slug>/prototype/` with a short `README.md` saying what it demonstrates, how to run or view it, and what it deliberately leaves out. Prototypes must be original work built from the spec, never copied code, CAD files, or assets from the original.

## Mode A: Software build demo (apps, sites, APIs, CLIs, libraries)
1. Choose the thinnest vertical slice: the one core flow from `20-ux-flows.md` working end to end (UI, logic, storage), with seeded sample data. Skip auth, billing and admin unless they are the point.
2. Use the stack from the rebuild spec. Prefer something that runs with one command (`npm run dev`, `python app.py`, `docker compose up`) or a single static HTML file when the product allows.
3. Run it for real. Start the app, drive the core flow (Playwright for web), and capture screenshots or a short screen recording. Fix what breaks; a demo that has never run is not a demo.
4. For APIs and CLIs, include a `demo.sh` that exercises the main operations and prints the results, plus recorded output in `prototype/demo-output.txt`.
5. Report which acceptance criteria from the spec the slice satisfies and which it does not.

## Mode B: Application viewer (interactive walkthrough)
Use when a runnable build is too heavy, the backend can't be reproduced, or the user mostly needs to see and click through the design.
1. Build a single self-contained interactive page (`prototype/viewer.html`) that lets the viewer step through the key flows with mocked data: clickable screens, state changes, and tabs for architecture diagram, data model and API surface alongside the UI.
2. Publish it with the Artifact tool when available so the user can open it directly; otherwise save the file and tell them the full path.
3. Mock data must be clearly sample data. Label anything simulated.

## Mode C: Physical product: 3D print
The full standard is in `3d-print-gcode.md`: every printed part ends in G-code sliced for the user's printer and checked by script. The steps below are the minimum.
Use for hardware or objects where a printable part makes sense (enclosures, brackets, mechanisms, fixtures, scale models).
1. Derive dimensions, tolerances, materials and assembly from the blueprint; mark each dimension `[observed]` (measured/spec sheet), `[inferred]` or `[assumed]`. If real measurements are missing, ask the user for them rather than inventing critical ones.
2. Model parametrically so dimensions can be adjusted: write OpenSCAD (`.scad`) or CadQuery/build123d Python with named parameters at the top.
3. Export `.stl` (and `.step` if the tool supports it). Check the mesh: watertight, correct units (mm), sensible orientation, wall thickness and overhangs suitable for FDM, split into printable parts with alignment features when the object is large.
4. Render preview images (OpenSCAD CLI, or matplotlib/trimesh/pyrender) from several angles so the user can see it without CAD software. Include a `print-notes.md`: layer height, infill, supports, material, orientation, estimated print time if known, and assembly steps.
5. State plainly that fit is unverified until physically printed and measured, and list the tolerances most likely to need tuning.

## Mode D: Physical product: drawings
The full standard is in `drawings.md`.
Use for products where manufacturing or review needs technical documents rather than a print file, or when no CAD tooling is available.
1. Produce dimensioned orthographic drawings (front, top, side, plus section and detail views where needed) as SVG or PDF, with title block, units, scale, tolerances and revision. Generate them from the same parametric model as Mode C when both are requested so they cannot drift.
2. Add an exploded assembly view and a bill of materials (part, quantity, material, source/spec) as CSV or markdown.
3. For electronics, add a block diagram and a netlist or schematic sketch (e.g. SVG or KiCad-compatible text) and a pin/interface table.
4. Check the drawings by viewing them rendered (convert SVG/PDF to PNG and look), not just by trusting the generator.

## Mode E: Full hardware build package
Use for any physical product that has mechanisms, electronics, or thermal/fluid systems. Modes C and D are building blocks of it, not substitutes. Follow `hardware-engineering.md`: mechanics, PCBA/circuit design, firmware or controls, thermal/fluid calculations, a unified BOM, and complete build instructions with bring-up and test procedures. Be explicit about what was verified and what was only specified.

## Choosing and combining
| Product | Default mode | Often add |
|---|---|---|
| Web/mobile app, SaaS | A (running slice) | B for a click-through of the whole product |
| API, library, CLI | A | |
| Large or backend-heavy system | B | A for one critical subsystem |
| Mechanical or consumer hardware | E | |
| Electronics (e-ink display, IoT, instrument) | E | |
| HVAC, appliances, thermal systems | E | |
| Simple printable part or fixture | C | D |

If the user did not say which they want, recommend the default from the table in one sentence and proceed unless they object. A prototype that cannot be shown to the user does not count: always finish by giving them something to look at (a running URL or screenshots, the viewer, rendered images or drawings).
