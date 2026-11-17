# Down Home Creole: Phase 1 prototype plant

Blended seasonings only, **1,000 lb a week** on one shift, in about **2,000 sq ft** (50 x 40 ft, 12 ft clear).
It launches with **5 blends** (the Creole Chameleon line: Original, Fire, Lemon Pepper, Garlic Herb, Blackened) and is laid out for all **13 seasonings**.
We fabricate everything we can in stainless and buy only what has to be certified, legal-for-trade or precise.

| | Phase 1 | Growth plant (`../`) |
|---|---|---|
| Output | 1,000 lb/week | 6,000 lb/day |
| Building | 2,000 sq ft | 12,600 sq ft (140 x 90 ft) |
| Blender | used 6 cu ft ribbon on a riser stand, 7 batches/week (18 % used) | 36 cu ft ribbon |
| Sifting and grinding | 18 in 12 mesh sieve with magnet into 55 gal drums; small hammer mill for whole spices | sifters and mill per line |
| Ingredients | 12-position bin ring (2.2 m high), weigh hopper, 82.5 % of blend weight auto-dosed | hand dispense to bulk bags |
| Packing | semi-automatic bench: auger fill, cap, induction seal, label, metal detect, checkweigh; 29 % loaded | two automatic lines |
| Equipment cost | **$200,180** ($171,000 buy, $29,180 fabricate) | $1,512,682 |

## Silos (bins) and how each blend is built

`design/out/dosing-plan.md` decides which ingredients get a bin and builds every product's batch:
an ingredient line is dosed from a bin when its batch target is at least **4 kg** (2 x the hopper's 20 g accuracy at a 1 % tolerance);
lines under 2 % go to the hand-weighed premix; everything else is hand-weighed at the bench.

- 5 launch blends: **9 bins** (salt, garlic, paprika, onion, black pepper, coarse black pepper, cayenne, lemon peel, red pepper), 3 positions spare.
- All 13 blends: **12 bins**, 62 % auto-dosed; red bell pepper and turmeric would stay hand-weighed until positions are added.
- One feeder size (2 in screw, about 700 L/h) everywhere; the longest dose is under 8 minutes.
- The MES tracks every lot poured into a bin; a batch dosed from a bin is traced to every lot in it since it last ran empty.

## Files

| Path | What |
|---|---|
| `design/design_basis_p1.py` | Phase 1 design basis (`SET=launch5` or `all13`) |
| `design/linebal-config.json`, `design/out/line-balance.md` | blender size and pack-bench balance |
| `design/dosing-config.json`, `design/out/dosing-plan.md` | bins, feeders, recipe routes per product, growth to 13 |
| `design/equipment_p1.py` → `equipment.json` | 52 lines, buy vs build, Growth equivalent and carry-over |
| `cad/p1_parts.py` | 13 fabricated stainless parts + 4 PETG fixtures: STEP, STL, drawings, DXF |
| `drawings/DH-P1-drawing-set.pdf` | 27 sheets, dual units: cover, 5 3D views, layout 1:50, process flow, assemblies (dosing and blending 1:20 with height stack-up, sifting and grinding 1:10, pack bench 1:15), electrical (power one-line and network, I/O list with wire numbers and cable schedule, typical wiring), 13 part sheets |
| `cad/plant_3d.py` → `cad/plant/DH-P1-plant.step`, `.glb` | full 3D plant assembly: every machine placed from the layout at the ASM heights (592 solids); bought machines are catalog-size models, fabricated parts are our STEP models |
| `drawings/3d/` | rendered 3D views (whole plant, dosing and blending, blender and sieve, grinding and weighing, pack bench); also sheets 3D-P1-001 to 005 in the drawing set. Re-render with `cad/plant/render/` (three.js + Playwright) |
| `design/make_sheets_p1.py` | writes the cover, PFD, ASM and ELE sheets and `io_p1.json` |
| `dxf/` | cut files in mm and inch |
| `design/plant_layout_p1.py`, `drawings/LAY-P1_*` | plant layout and check (all PASS) |
| `design/foodsafety-config.json`, `design/out/food-safety.md` | HACCP, SSOP, zoning, dust (all PASS) |
| `bom/phase1-bom.xlsx`, `bom/phase1-cost.md` | BOM, fabrication list, bins, recipes, cost by area, carry-over |
| `build/` | Anatomy build package: `build.json`, purchase carts, print and fab lists, 13 assembly steps, tests |
| `../software/plc/DosingStation.st` | WAGO PFC200 dosing control |
| `../software/mes` | MES; run Phase 1 with `python3 -m dhmes.server --blender P1-301` |

## Regenerate

```
cd design && python3 design_basis_p1.py && SET=all13 python3 design_basis_p1.py
T=../../../../skills/anatomy/tools/plant
python3 $T/linebal.py design-basis.json linebal-config.json out
python3 $T/dosing.py design-basis.json out/line-balance.json dosing-config.json out design-basis-all13.json out-all13/line-balance.json
python3 equipment_p1.py && python3 plant_layout_p1.py
python3 $T/layout.py layout.json equipment.json ../drawings     # then rename LAY-001_* to LAY-P1_*
python3 $T/foodsafety.py design-basis.json equipment.json layout.json foodsafety-config.json out
python3 make_sheets_p1.py
cd ../cad && python3 p1_parts.py && python3 plant_3d.py
cd ../bom && python3 make_bom_p1.py
cd ../build && python3 make_build.py
```

## What the height stack-up changed

Drawing the dosing and blending train to true scale (ASM-P1-001) moved several things:
the bin ring went up to 2.2 m so feeders discharge above the hopper lid, the blender sits on a fabricated 1,150 mm riser stand (P1-311) so its valve clears chute, sieve and drum,
blend drums are 55 gal (one 131 L batch did not fit a 30 gal drum), the hopper valve is electrically actuated to match the PLC, hand adds go in at the flexible-screw intake grate,
a 4-step platform serves bin loading, and a small hammer mill (P1-320 with feed magnet P1-321 and hopper P1-322) grinds whole spices. The dust collector is sized at 1,400 cfm.

## Open items

- Confirm the 5 launch blends (assumed to be the Creole Chameleon line).
- The used blender and used metal detector are estimates until a unit is inspected; flanges marked VERIFY are measured on them before cutting.
- PETG fixtures are STL only: slice in Bambu Studio on Yaeger.
- Costs exclude building fit-out (epoxy floor, walls, drains), electrical service, compressed air, freight and opening inventory.
