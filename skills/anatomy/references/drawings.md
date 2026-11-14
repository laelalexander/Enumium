# Blueprints and drawings: production quality

Drawings are what a machinist, a fab house or a person at a workbench builds from. Treat them as a primary deliverable, not an illustration. Generate them from the same parametric model as the STEP/STL so they cannot drift, and look at every rendered sheet yourself before presenting it.

## Tooling (in order of preference)
1. **FreeCAD TechDraw, headless** (`FreeCADCmd` / `freecadcmd` with a Python script): import the STEP, create pages from a template with title block, add projection groups, section and detail views, dimensions and balloons, export PDF and SVG. Install with `winget install FreeCAD.FreeCAD` if missing (tell the user).
2. **build123d / CadQuery** for the model, plus their 2D projection export (`ExportSVG`/`exporters.export(..., "svg")`) for views, with dimensions and title block added by script (svgwrite/matplotlib) when FreeCAD is not available.
3. **KiCad** for PCB fabrication and assembly drawings (`kicad-cli pcb export pdf`).
Say which tool produced each sheet.

## Every part drawing (BUILD parts)
- Title block: part name, drawing number, revision, material, finish, scale, units (mm), projection symbol (first or third angle, state which), date, sheet x of y.
- Views: front, top, right as needed, plus an isometric; section views through every internal feature (bosses, pockets, snap-fits); detail views for small features.
- Dimensions: fully defined, no double dimensioning, from functional datums. Hole callouts with thread spec (e.g. `M3 x 0.5 - 6H, 8 deep`, or `Ø4.0 for M3 heat-set insert`).
- Tolerances: general tolerance block (ISO 2768-m for machined parts; ±0.2 mm for FDM unless stated) and explicit tolerances or fits on mating features (`Ø8 H7`). GD&T (flatness, position, perpendicularity) where function needs it.
- Notes: material grade, print orientation and process (for printed parts), deburr/edge breaks, surface finish, inserts or hardware installed.

## Assembly drawings
- Exploded isometric with numbered balloons; the parts list on the sheet uses the same line numbers as `bom/bom.csv`.
- Sub-assembly sheets for anything with more than ~10 parts.
- Fastener callouts with torque, thread locker, and insertion order where it matters.
- Wiring/harness diagram as its own sheet: connectors, pins, wire gauge, color, length.
- Clearances and critical alignment dimensions (e.g. display window to panel active area, PCB connector to enclosure cutout) checked against the 3D assembly; state the tolerance stack-up for each.

## Blueprint package
- `drawings/` with one PDF per part and per assembly, plus a combined `drawings/drawing-set.pdf` with a cover sheet and index.
- `renders/`: shaded renders of the assembly (exploded and assembled), each part, and the PCB, from several angles.
- Check: convert each PDF page to PNG and view it. Fix overlapping dimensions, dimensions that are unreadable at A3/Tabloid, missing views, or balloons that do not match the BOM. Do not present a sheet you have not looked at.

## Use the strongest model
Drawings, tolerance stack-ups and the parts gate reward careful reasoning. When the user lets you choose, run hardware projects on the most capable model available and do not cut these steps short to save time.
