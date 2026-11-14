# Blueprints and drawings: production quality

Drawings are what a machinist, a fab house or a person at a workbench builds from. Treat them as a primary deliverable, not an illustration. Generate them from the same parametric model as the STEP/STL so they cannot drift, and look at every rendered sheet yourself before presenting it.

## Tooling (in order of preference)
1. **FreeCAD TechDraw, headless** (`FreeCADCmd` / `freecadcmd` with a Python script): import the STEP, create pages from a template with title block, add projection groups, section and detail views, dimensions and balloons, export PDF and SVG. Install with `winget install FreeCAD.FreeCAD` if missing (tell the user).
2. **build123d / CadQuery** for the model, plus their 2D projection export (`ExportSVG`/`exporters.export(..., "svg")`) for views, with dimensions and title block added by script (svgwrite/matplotlib) when FreeCAD is not available.
3. **KiCad** for PCB fabrication and assembly drawings (`kicad-cli pcb export pdf`).
Say which tool produced each sheet.

## Minimum is not acceptable
A sheet that shows only overall sizes (e.g. a plate with its outside diameter and height, and holes drawn but not dimensioned) is a sketch, not a drawing. The standard is the most complete detail a shop needs to make and inspect the part without asking a question: every feature located and sized, every hole specified, every tolerance stated.

## Dual units, everywhere
- Every dimension on every drawing shows **mm first, inches second in brackets**, e.g. `210.0 [8.268]`, `Ø5.5 [Ø.217] THRU`. Inches to 3 decimal places (4 for tolerances under ±0.005 in).
- Title block states "DIMENSIONS: MM [INCH]". Tolerances are given in both units too.
- Every cut file and CAD export is produced in **both mm and inch** versions (see Cut files below). STEP is unit-tagged; also state the units in the file name.

## Every part drawing (BUILD parts)
- **Hole table** on the sheet for any part with more than ~3 holes: hole ID (A1, A2...), X and Y from the datum in mm [in], diameter mm [in], THRU or depth, thread spec (`M5x0.8-6H` with tap drill), counterbore (`⌴ Ø10 [.394] ↧ 5 [.197]`) or countersink (`⌵ Ø10 x 90°`), tolerance, quantity, and what goes in it (screw, insert, dowel). Tag each hole on the views with its ID.
- Bolt circles: `6X Ø5.5 [.217] THRU EQ SP ON Ø180 [7.087] BC`, with the angular position of the first hole from a datum.
- Every feature dimensioned: pockets, bosses, counterbores, slots, chamfers and fillets (`R2 [.079] TYP`), wall thicknesses, rib sizes, insert bores, and the position of every feature from the datums. No feature may be readable only from the CAD model.
- Title block: part name, drawing number, revision, material, finish, scale, units (MM [INCH]), projection symbol (first or third angle, state which), date, sheet x of y.
- Views: front, top, right as needed, plus an isometric; section views through every internal feature (bosses, pockets, snap-fits); detail views for small features.
- Dimensions: fully defined, no double dimensioning, from functional datums. Hole callouts with thread spec (e.g. `M3 x 0.5 - 6H, 8 deep`, or `Ø4.0 for M3 heat-set insert`).
- Tolerances: general tolerance block (ISO 2768-m for machined parts; ±0.2 mm for FDM unless stated) and explicit tolerances or fits on mating features (`Ø8 H7`). GD&T (flatness, position, perpendicularity) where function needs it.
- Notes: material grade, print orientation and process (for printed parts), deburr/edge breaks, surface finish, inserts or hardware installed.

## Cut files (plates, gaskets, shims, panels, brackets)
Every flat part, whether laser, waterjet, CNC router or knife/plotter-cut (gaskets, seals, foam, rubber, acrylic, sheet metal blanks, shims), gets production cut files, tooled and ready:
- `cut/<bom-line>-<part>_mm.dxf` and `cut/<bom-line>-<part>_in.dxf`: true 1:1 scale, units set in the header (`$INSUNITS` 4 for mm, 1 for inch), closed polylines only, outer profile and inner cuts on separate layers (`CUT_OUTER`, `CUT_INNER`, `ENGRAVE`, `BEND`), no dimensions or title block in the cut layer.
- Material and thickness in the file name and on a matching drawing sheet with the hole table; kerf and whether it is compensated; grain or bend direction for sheet metal; compression allowance for gaskets.
- Check each DXF by reading it back (ezdxf): all profiles closed, units correct, overall size matches the model in both files, no duplicate or zero-length entities. Render each to PNG and look at it.
- Custom-length purchased stock (threaded rod, tube, extrusion, cord) gets a cut list: length mm [in], tolerance, end finish, quantity.

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
