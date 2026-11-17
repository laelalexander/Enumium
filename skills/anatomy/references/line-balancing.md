# Line-rate balancing

Tool: `tools/plant/linebal.py design-basis.json linebal-config.json out_dir`. It writes `line-balance.json/.md`.

## Model
- **Available minutes** = shift hours × 60, minus breaks and start-up, minus the end-of-shift clean, × days.
- **Effective rate** of each machine = rated rate × `rate_factor` (0.8 for a new line), then × (1 − `unplanned_downtime`) (0.1). Changeovers are counted separately, not hidden inside OEE.
- **Batch process** (blender): batch kg = working volume × the formula's bulk density, never more. Bulk density is the harmonic mean of the ingredient densities, weighted by %. Cycle = charge + mix (site: 12 min) + discharge, where discharge is limited by the slowest of the valve, sifter and screw.
- **Campaigns**: SKUs or formulas below a weekly threshold run every two weeks, which halves the changeovers. A changeover between formulas is either a purge (same allergen class) or a full clean (allergen change).
- **Utilization limit**: 85 % of available minutes for any station, so a bad day can be caught up the same week. Anything over the limit is a finding, never rounded away.

## Process
1. Try every candidate size for the batch machine (the example tries 18, 25, 36 and 52 cu ft). Pick the smallest one that fits under the limit.
2. Load each pack line with its SKUs: run time = units ÷ effective upm, plus changeovers by container family (a change-part swap) and by formula (a purge).
3. Name the bottleneck and the next-worst station, and say what would fix each one (a faster model, a second shift on that line, or moving a SKU).
4. Write a weekly schedule that respects the allergen sequence: allergen-free first, then hotter blends, then allergens last before the wet clean.

## Reporting
Report the honest number. In the worked example line A came out at 88 %, over the 85 % limit, and that went to the client with two fixes: confirm 90 upm or more at FAT, or add a partial second shift.
