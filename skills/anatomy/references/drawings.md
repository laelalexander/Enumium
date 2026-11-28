# Blueprints and drawings: production quality

> **Reference standard (approved by the user, 2026-11-14): "the level of detail we want on everything from now on."** The robot arm sheets in laelalexander/Enumium (PR #2, `3d-workflow/design/`) are the bar every project's drawing set must meet or exceed:
> - `drawings/ASM-001_assembly.svg`: general arrangement from hidden-line views of the real assembled model, with a parts list.
> - `drawings/ASM-002_joint_section.svg`: true-scale CAD section with hatching, balloons, an item list, fits, torques and notes.
> - `schematics/ELE-001_wiring.svg`: schematic with every wire numbered and colour-coded by function.
> - `schematics/ELE-002_wire_list.svg`: the matching from/to wire list.
> - `drawings/<part>.svg`: per-part sheets.
>
> Generators: `3d-workflow/arm/asmsheets.py`, `arm/elesheet.py` and `tools/ga.js`. A3, third-angle, mm [in], zone border, and a title block with part no. and material. When unsure how to lay out a sheet, open these and match them.

Drawings are what a machinist, a fab house or a person at a workbench builds from. Treat them as a primary deliverable, not an illustration. Generate them from the same parametric model as the STEP/STL so they cannot drift, and look at every rendered sheet yourself before presenting it.

## Branding (customer-facing, user rule 2026-11-28)

Every drawing, cover page and PDF is issued by **Noitavonne Manufacturing, NERO Design Studios CAD (Prototype / Mechanical / CAD / Industrial Design)**, the Noitavonne on-prem engineering system. Nero and Anatomy are both built by Noitavonne. Drawings go to customers and manufacturers, so:

- Import `tools/branding.py` (copy it next to a project's generator if the skill folder is not importable). Use `B.DRAWN_BY` for the title block DRAWN / PREPARED BY field, `B.svg_footer(...)` / `B.add_svgwrite_footer(...)` / `B.mpl_footer(fig)` for the footer on **every sheet**, `B.COVER_NOTE` on cover pages and `B.pdf_metadata(doc, title)` on every PDF.
- **Never** credit a tool, library or script in drawing text: no build123d, CadQuery, FreeCAD, svgwrite, PyMuPDF, matplotlib; no "Claude"; no "Generated from ... by make_drawings.py"; no internal paths (`prototype/mechanical/cad`, `bom/bom.csv`, `fab/WIRELIST.csv`, `thermal-fluid/thermal.md`). Refer to other documents by name ("BOM", "wire list CSV", "thermal analysis on file").
- Before presenting a set, run `python tools/rebrand_pdf.py --check <drawing-set.pdf>`; it must report no forbidden credits. For a set made before this rule, `python tools/rebrand_pdf.py <pdf>` fixes it in place (title-block credits replaced, footer and metadata added; a `.pre-branding.pdf` backup is kept).

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
These are built from the **real CAD solids** in their assembled positions, never redrawn by hand or from boxes. Every assembly gets at least:
- **General arrangement (GA)**: hidden-line views (front, side, top, plus an isometric) of the whole assembled model, rendered from the same meshes the 3D twin shows (part outlines, creases and depth steps), at a stated scale. Number every part with a balloon and put a parts list on the sheet whose item numbers match `bom/bom.csv` / `parts.json`.
- **A true-scale section through every joint, bearing stack, shaft or clamp**: cut on the functional plane at a stated scale (1:1 or 1:2), cut faces hatched (one hatch direction per part), with shafts, fasteners and bought gearmotors left unsectioned by convention. Add a second view (for example from the motor side) where belts, pulleys or hidden parts need it.
- **An item list on that sheet**: item, part no., description, qty, keyed to the balloons.
- **Callouts on the section, in red leaders, for every interface**:
  - bearing seats as Ø and depth with the fit (`Ø28.15 [1.108] x 8.2 DP, light press`);
  - shaft tolerances (`Ø12 h6 (0/-0.011)`) and bores (`Ø12 (0/-0.008)`);
  - fastener number, size and quantity with **torque in N·m** and washer/nyloc detail;
  - belt slots with travel, critical clearances (`clears the tube block by 4.8 [.190]`), and drill-through instructions.
- **Key centre distances and stack dimensions** in mm [in], drawn on the section.
- **A table for repeated assemblies**: when several joints are built the same way, give a table of what changes (ratio, pulleys, centre distance, belt).
- **A notes block (UNLESS OTHERWISE SPECIFIED)**: scale and source ("from the CAD solids"), press-fit method, set-screw and thread-locker rules, belt tension in mm deflection, torques per fastener, axial play, what to MEASURE on the bought part before building, and a functional check ("turns its full range by hand before wiring").
- **Sub-assembly sheets** for anything with more than ~10 parts. Clearances and alignments checked against the 3D assembly, with the tolerance stack-up stated.

## Electrical drawings
- **Schematic (ELE-001)**: every component with its reference designator (PSU1, F1, S1, A1, U1..Un, M1..Mn, TB1, X0, E1), every pin labelled, and **every wire numbered** (Wxxx, grouped by circuit: W0xx mains, W1xx power, W2xx signals, W3xx motor phases, W4xx sensors). Colour-code wires by function, with a legend giving each colour's function and AWG. Show fuses, the E-stop circuit, star ground, shields and earth. Numbered notes cover ferrules and labels, driver DIP settings, logic convention, enable/E-stop behaviour, the grounding scheme, gland entries, and safety (mains by a qualified person; never unplug a motor while powered).
- **Wire list (ELE-002)**: one row per wire number, giving from (ref:pin), to (ref:pin), function, AWG, colour, cut length mm [in], terminations both ends (ferrule, crimp, solder) and label. Also export it as `fab/WIRELIST.csv` so the build can be cut and labelled from it.

## Blueprint package
- `drawings/` with one PDF per part and per assembly, plus a combined `drawings/drawing-set.pdf` with a cover sheet and index.
- `renders/`: shaded renders of the assembly (exploded and assembled), each part, and the PCB, from several angles.
- Check: convert each PDF page to PNG and view it. Fix overlapping dimensions, dimensions that are unreadable at A3/Tabloid, missing views, or balloons that do not match the BOM. Do not present a sheet you have not looked at.

## Use the strongest model
Drawings, tolerance stack-ups and the parts gate reward careful reasoning. When the user lets you choose, run hardware projects on the most capable model available and do not cut these steps short to save time.
