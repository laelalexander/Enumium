# Down Home Creole: Phase 1 prototype plant

Blended seasonings only, **1,000 lb a week** on one shift, in about **2,000 sq ft** (50 x 40 ft, 12 ft clear).
It launches with **5 blends** (the Creole Chameleon line: Original, Fire, Lemon Pepper, Garlic Herb, Blackened) and is laid out for all **13 seasonings**.
We fabricate everything we can in stainless and buy only what has to be certified, legal-for-trade or precise.

| | Phase 1 | Growth plant (`../`) |
|---|---|---|
| Output | 1,000 lb/week | 6,000 lb/day |
| Building | 2,000 sq ft | 12,600 sq ft (140 x 90 ft) |
| Blender | used 6 cu ft ribbon, 7 batches/week (18 % used) | 36 cu ft ribbon |
| Ingredients | 12-position bin ring, weigh hopper, 82.5 % of blend weight auto-dosed | hand dispense to bulk bags |
| Packing | semi-automatic bench, 29 % loaded | two automatic lines |
| Equipment cost | **$183,900** ($158,080 buy, $25,820 fabricate) | $1,512,682 |

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
| `design/equipment_p1.py` → `equipment.json` | 48 lines, buy vs build, Growth equivalent and carry-over |
| `cad/p1_parts.py` | 11 fabricated stainless parts + 4 PETG fixtures: STEP, STL, drawings, DXF |
| `drawings/DH-P1-drawing-set.pdf` | layout DH-LAY-P1 (1:50) and 11 part sheets, dual units |
| `dxf/` | cut files in mm and inch |
| `design/plant_layout_p1.py`, `drawings/LAY-P1_*` | plant layout and check (all PASS) |
| `design/foodsafety-config.json`, `design/out/food-safety.md` | HACCP, SSOP, zoning, dust (all PASS) |
| `bom/phase1-bom.xlsx`, `bom/phase1-cost.md` | BOM, fabrication list, bins, recipes, cost by area, carry-over |
| `build/` | Anatomy build package: `build.json`, purchase carts, print and fab lists, 12 assembly steps, tests |
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
cd ../cad && python3 p1_parts.py
cd ../bom && python3 make_bom_p1.py
cd ../build && python3 make_build.py
```

## Open items

- Confirm the 5 launch blends (assumed to be the Creole Chameleon line).
- The used blender and used metal detector are estimates until a unit is inspected; flanges marked VERIFY are measured on them before cutting.
- PETG fixtures are STL only: slice in Bambu Studio on Yaeger.
- Costs exclude building fit-out (epoxy floor, walls, drains), electrical service, compressed air, freight and opening inventory.
