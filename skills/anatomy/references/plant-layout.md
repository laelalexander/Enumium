# Plant layout (production lines and factories)

Use this when the product to dissect and rebuild is a **production operation**, such as a food plant, a packaging line or an assembly cell, rather than a single device. The deliverable is a plant you could build: every machine bought or fabricated, laid out to scale, wired, controlled and checked.

Worked example: `projects/downhome-spice-line/` (Down Home Creole dry blending and packing plant, 6,000 lb/day).

## Inputs, in this order
1. **Design basis** (`design/design_basis.py` -> `design-basis.json`): volume, shifts, hours, OEE, building, batch rule, product mix and the weekly demand per SKU. Tag every number with where it came from: `site`, `client`, `documented`, `assumed` or `calculated`. Assumptions go in `open_questions`.
2. **Equipment list** (`design/equipment.py` -> `equipment.json`): one entry per tag, with maker, model, specs and sources, URL, supplier, qty and qty basis, price (marked as an estimate unless quoted), footprint, power, air, `sanitary`, `product_contact`, `dust_cfm`, alternates and what to confirm. The qty basis must trace to the design, for example "22 bays from storage.json" or "7 modules from io.json".
3. **Line balance** (`references/line-balancing.md`): pick the machine sizes before drawing anything.

## Layout tool: `tools/plant/layout.py`
`python3 layout.py layout.json equipment.json out_dir` draws an ARCH D sheet at the largest standard scale that fits. The sheet has a grid, rooms coloured by hygiene zone, racks, equipment footprints taken from `equipment.json`, material and people flows, dual-unit dimensions, an equipment schedule, a zone schedule and a checks block. It also writes DXF files in mm and inch for the architect, and `layout-check.json/.md`.

`layout.json` holds: `building`, `rules.min_clear_mm`, `rooms` (each with a zone), `racks`, `equipment` (tag, room, x, y, optional rotation), `lines` (chains of conveyor-linked tags), `linked` pairs, `doors`, `flows` (raw, finished, people, waste), `dims` and `notes`.

The checks must all pass before hand-off:
- **overlaps**: no two footprints intersect.
- **outside room**: every machine sits inside its room.
- **tight aisles**: at least 900 mm (OSHA 1910.22 / 1910.37 egress, and forklift aisles per the truck spec). Conveyor-linked machines are exempt.
- **zone violations**: a machine's zone must match its room (see food-safety-design.md).
- **flow crossings**: raw material and finished goods flows must not cross, and people do not enter high-care except through the hygiene vestibule.

## Storage sizing
Size racks from demand, not from the floor. The worked example uses 2 weeks of raw material, 1 week of packaging and 3 days of finished goods, in pallet positions, then bays. Write `storage.json` and use it for the rack qty in the equipment list.

## Drawings a plant package must include
Build these with `tools/plant/engsheets.py`. They are held to the same bar as the robot arm sheets.

| Sheet | Content |
|---|---|
| LAY-001 | Plant layout, true scale, zones, flows, schedules, checks |
| PFD-001 | Process flow with numbered streams and a stream table (material, design rate, basis) |
| ASM-0xx | One true-scale elevation per line, with balloons, an item list, joints/fits/torques (or a change-parts table) and a detail of the critical joint |
| ELE-001 | Power one-line with the NEC 430.250 FLA, the feeder per motor, and the control network |
| ELE-002 | I/O list and field cable schedule, every wire numbered as PLC-slot-channel |
| Custom parts | Each fabricated part as a part sheet (`partsheet.py`) from the CAD solid, with a DXF in mm and in |

## Things that go wrong
- The machine footprints were guessed but not marked `estimate`. Mark them, and ask for the OEM general arrangement drawings before construction.
- The layout was drawn before the line balance and then needed a bigger blender. Do the balance first.
- Dust collector pickups were added after the collector was sized. Use `foodsafety.py`, which re-sums them.
