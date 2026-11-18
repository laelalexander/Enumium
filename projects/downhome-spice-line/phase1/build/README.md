# Phase 1 build package

A 2,000 sq ft blended-seasoning plant for 1,000 lb a week on one shift, launching with 5 blends and laid out for all 13. Ingredients are dosed from 9 stainless bins (12 positions) into a weigh hopper and blended in a 6 cu ft ribbon blender we build, sifted on the drum, held for QC, then packed on a bench of machines we build: servo auger filler, spindle capper, wrap labeler and a detector conveyor. 82.5 % of blend weight is dosed automatically. Stainless frames, bins, hoppers, tables and most machines are fabricated in house to save money; scales, motors, drives, valves and a used metal detector head are bought.

**Cost:** $176,675 ($123,409 bought, $53,266 fabricated). **Fabrication:** 340.0 shop hours. **Install and commissioning:** about 120 hours. **Prints:** 4 PETG fixtures, about 857 g.

## Stages

1. **Purchase**: `1-purchase/purchase-list.csv` (69 lines) and one cart file per supplier.
2. **Print**: `2-print/print-list.csv` (4 fixtures). Not sliced yet: slice in Bambu Studio on Yaeger.
3. **Fabricate**: `3-fabricate/fab-list.csv` (17 items) with DXF cut files in mm and inch, STEP models and dimensioned drawings.
4. **Assemble**: 14 steps in `build.json`, from floor marking to commissioning.
5. **Software and tests**: `software/plc/DosingStation.st` on the WAGO, the MES with `--blender P1-301`, and the acceptance tests in `build.json`.

## Package check

PASS: every equipment line is purchased, printed or fabricated; every one is installed in an assembly step; every file exists.

## Gaps

- G-code for the 4 PETG fixtures is not sliced yet: slice the STLs in Bambu Studio on Yaeger and add the .gcode.3mf paths
- Assembly pictures are the part drawings and the layout, not rendered 3D assembly steps
- Bought parts for the built machines are catalog-class picks marked confirm: check each model and price before ordering; the used detector head P1-418 is an estimate until a unit is inspected
- Built machines are first articles: expect one round of fit-up changes (ECO) on the blender agitator and the filler auger tooling
