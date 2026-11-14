# Parts: every part is BUY or BUILD

A hardware package is only buildable if someone can get every part on the list. The rule: **every physical item needed to assemble the product, down to screws, wire, glue and heat-shrink, is one BOM line, and every line is either BUY or BUILD.** There are no "generic", "suitable", "TBD" or "any" parts in a finished package.

## BUY lines (purchasable on the market)
Each BUY line must have:
- **Manufacturer and manufacturer part number (MPN)**, or for commodity hardware a full standard designation that any supplier can fill: e.g. `ISO 4762 M3x8 A2-70 socket head cap screw`, `DIN 934 M3 nut A2`, `heat-set insert M3 x 5.7 OD x 4.6 L brass (CNC Kitchen / Ruthex RX-M3x5.7)`, `608-2RS bearing 8x22x7`, `22 AWG UL1007 stranded, 7/0.25`.
- **Key specification** you relied on (rating, size, thread, voltage, current, tolerance, material, finish).
- **At least one supplier link** with the exact listing (Digi-Key, Mouser, LCSC, McMaster-Carr, Misumi, Adafruit, SparkFun, manufacturer store, Amazon only when nothing better exists), unit price, price date, and stock status when visible.
- **An alternate** (second source or equivalent MPN) for anything critical, single-source, or likely to go out of stock.
- **Datasheet URL** for anything electrical or load-bearing, and whether you actually fetched it.
- **Verified**: what you checked and where (e.g. "Digi-Key product page fetched 2026-11-14, in stock"). An honest "not verified" beats a plausible fake MPN.
- Standard hardware gets both its standard designation and a real orderable SKU, e.g. `ISO 4762 M3x8 A2-70` plus `McMaster-Carr 91292A112`.

Easily forgotten parts each get their own BUY line: crimp contacts and connector housings, wire by gauge and colour (in metres), heat-set inserts, heat-shrink, adhesive and thread locker, filament (in grams, per material), solder paste or stencil if used, and the PCB fabrication and assembly orders themselves. Words like "assorted", "as needed", "generic" or "TBD" fail the gate.

If you cannot confirm a part exists and is buyable, the line is not done: mark it `[assumed - verify]` and list it under open items. Do not invent MPNs.

## BUILD lines (made from a design file)
Each BUILD line must point to its source and its manufacturing file(s), checked in:
| Process | Required files |
|---|---|
| FDM / SLA / SLS print | parametric source (`.py`/`.scad`), `.step`, `.stl` or `.3mf`, sliced `.gcode` per `3d-print-gcode.md`, print settings |
| CNC | `.step`, toleranced drawing with material/finish; stock material is its own BUY line |
| Laser / waterjet / knife-cut (plates, gaskets, shims) | 1:1 `.dxf` in **both mm and inch**, material and thickness, kerf note, drawing with hole table (see `drawings.md`); sheet stock is a BUY line |
| Sheet metal | `.step` (flat + formed), `.dxf` flat pattern, bend table, drawing |
| PCB | KiCad project, Gerbers + drill zip, BOM + centroid for assembly (`kicad-pcb.md`) |
| Cable / harness | wiring diagram, pin-to-pin table, cut list (wire gauge, colour, length, strip length); housings and crimps are BUY lines |
| Firmware | source, build command, compiled binary if built |

Also give: material (e.g. PETG, 6061-T6, FR-4 1.6 mm), quantity, and the drawing number that defines it.

## The BOM files
- `bom/bom.csv` with columns: `line, type (BUY|BUILD), ref/designators, qty, description, manufacturer, mpn_or_standard, key_spec, supplier, supplier_url, unit_price, price_date, alt_mpn, datasheet_url, verified, design_file, drawing, status`
- `bom/bom.md`: the same, readable, grouped by sub-assembly, with totals (cost per unit, cost for 1 and for 10 units).
- `bom/order-list.md`: a shopping list grouped by supplier, with quantities rounded up to pack sizes and spares for small parts (+10% or +2, whichever is more).

## Completeness gate (run before calling the package done)
Write and run `bom/check_bom.py` (or equivalent) that fails if:
1. any line has an empty `type`, or BUY lines lack `mpn_or_standard` and `supplier_url`, or BUILD lines lack a `design_file` that exists on disk;
2. any BUILD print part lacks its `.stl`/`.3mf` and `.gcode`;
3. any part, fastener or connector named in the assembly instructions, drawings (balloons) or CAD assembly is missing from the BOM, or a BOM line is never used (count fasteners by walking the assembly steps);
4. any schematic reference designator is missing from the BOM, or vice versa.
Report the result in the README. Fix every failure or list it as an explicit open item with what is needed to close it.
