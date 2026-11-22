# Line-rate balancing

Tool: `tools/plant/linebal.py design-basis.json linebal-config.json out_dir`. It writes `line-balance.json/.md`.

## Model
- **Available minutes** = shift hours × 60, minus breaks and start-up, minus the end-of-shift clean, × days.
- **Effective rate** of each machine = rated rate × `rate_factor` (0.8 for a new line), then × (1 − `unplanned_downtime`) (0.1). Changeovers are counted separately, not hidden inside OEE.
- **Batch process** (blender): batch kg = working volume × the formula's bulk density, never more. Bulk density is the harmonic mean of the ingredient densities, weighted by %. Cycle = charge + mix (site: 12 min) + discharge, where discharge is limited by the slowest of the valve, sifter and screw.
- **Campaigns**: SKUs or formulas below a weekly threshold run every two weeks, which halves the changeovers. A changeover between formulas is either a purge (same allergen class) or a full clean (allergen change).
- **Utilization limit**: 85 % of available minutes for any station, so a bad day can be caught up the same week. Anything over the limit is a finding, never rounded away.

## Process
1. Try every candidate size for the batch machine (the example tries 18, 25, 36 and 52 cu ft). Pick the smallest one that fits under the limit. Set `blending.choose_cuft` to override the pick when another reason decides the size (the Phase 1 example takes 6 cu ft because a used unit of that size is available and leaves room to grow).
2. Load each pack line with its SKUs: run time = units ÷ effective upm, plus changeovers by container family (a change-part swap) and by formula (a purge).
3. Name the bottleneck and the next-worst station, and say what would fix each one (a faster model, a second shift on that line, or moving a SKU).
4. Write a weekly schedule that respects the allergen sequence: allergen-free first, then hotter blends, then allergens last before the wet clean.

## Reporting
Report the honest number. In the worked example line A came out at 88 %, over the 85 % limit, and that went to the client with two fixes: confirm 90 upm or more at FAT, or add a partial second shift.

## Ingredient bins and dosing: `tools/plant/dosing.py`
When ingredients are stored in bins ("silos") and dosed automatically, run
`dosing.py design-basis.json line-balance.json dosing-config.json out_dir [growth-basis.json growth-line-balance.json]`.
- A line is dosed from a bin only when its batch target is at least `min_dose_kg` = 2 × weigh-hopper accuracy ÷ dosing tolerance (20 g at 1 % gives 4 kg); lines under `minor_pct` go to the hand premix.
- Bins go to the ingredients with the most doseable kg a week; ties go to the one more products use.
- Each bin is sized for days of stock, refills per week and bags per refill; the feeder is the smallest in the config that finishes the largest dose inside `max_dose_min`; low-density powders get a flow aid.
- Every product gets its recipe: BIN, HAND or PREMIX per line with its tolerance and the dosing order.
- With a growth basis it shows how many bins the full range needs and what would still be hand-weighed.
- A topped-up bin mixes lots. The MES must record every lot poured in and trace a batch to all lots present since the bin last ran empty (see `projects/downhome-spice-line/software/mes`, `refill_bin` / `record_dose`).
The worked example is `projects/downhome-spice-line/phase1/design/out/dosing-plan.md`.
