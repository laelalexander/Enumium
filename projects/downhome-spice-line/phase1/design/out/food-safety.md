# Food-safety design check

| Check | Result |
|---|---|
| zoning | PASS |
| sanitary | PASS |
| dust_airflow | PASS |
| shared_equipment_controlled | PASS |

## Allergen matrix

| Formula | Name | wheat |
|---|---|---|
| f-orig | Creole Chameleon Original |  |
| f-fire | Creole Chameleon Fire Blend |  |
| f-lemp | Creole Chameleon Lemon Pepper |  |
| f-garl | Creole Chameleon Garlic Herb |  |
| f-blkn | Creole Chameleon Blackened |  |
| f-caml | Creole Camilian Standard |  |
| f-ncgb | N-Constant GreenBoost Blend |  |
| f-ncnc | N-Constant NeuroClarity |  |
| f-lyrb | Lycopoise Red Pepper Boost |  |
| f-lthr | Lyco-Tomato Herb Rub |  |
| f-ngrb | Nitro-Green Rub |  |
| f-vfrb | Vascular Fire Rub |  |
| f-efap | EndoFlex All-Purpose Blend |  |
| f-batter | Creole Fish Fry Batter Mix (concept) | X |
| f-ncpm | N-Constant Protein Pancake & Waffle Mix | X |
| f-afcb | Air-Fry Crisp Batter | X |

## Shared product-contact equipment

| Tag | Machine | Families | Control |
|---|---|---|---|

## Claims

- **Gluten free (< 20 ppm, 21 CFR 101.91)** (all Phase 1 blends): protected by separation. No wheat in the building in Phase 1 (client 2026-11-17: blended seasonings only). Keep a supplier gluten statement for every spice; test one finished lot a quarter.

## Hygiene zoning of product-contact machines

| Tag | Room | Zone | OK |
|---|---|---|---|
| P1-206 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-211 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-213 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-214 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-220 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-223 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-224 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-302 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-305 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-307 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-308 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-320 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-321 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-322 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-304 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-301 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-212 | Dosing & blending room | Z3 high-care dry (exposed product) | yes |
| P1-401 | Pack room | Z3 high-care dry (exposed product) | yes |

## Combustible dust

Pickups total **1050 cfm**; P1-310 design **1400 cfm** (needs 25% margin): OK.

| Pickup | cfm | qty |
|---|---|---|
| P1-206 | 300 | 1 |
| P1-220 | 150 | 1 |
| P1-302 | 250 | 1 |
| P1-320 | 150 | 1 |
| P1-304 | 200 | 1 |

- NFPA 652 dust hazard analysis (DHA) before ordering DC-310; send Kst/Pmax and MIE samples of the 3 highest-volume blends to a test lab.
- NFPA 61 (agricultural/food dusts): collector outside the building, explosion vent directed away from people, isolation flap valve on the inlet duct.
- Bins vent back through the weigh hopper to P1-310; lids gasketed so bins do not puff dust at refill.
- Bond and ground the bins, feeders, flexible screw and blender (< 10 ohm); drums are conductive-lined or grounded with a clip at the drum-top sifter.
- Housekeeping: dust layer over 1/32 in triggers cleaning; vacuum P1-702 only, never compressed air.
- Electrical in the dosing and blending room per the DHA (Class II Div 2 Group G unless shown otherwise); controller P1-225 in a sealed SS enclosure.

## HACCP plan

| CCP | Step | Hazard | Critical limit | Monitoring | Corrective action | Verification | Records |
|---|---|---|---|---|---|---|---|
| CCP-1 | Metal detection P1-406 on every finished pack, after labeling | Physical: metal from raw spice or equipment wear | No pack passes containing Fe >= 2.0 mm, non-Fe >= 2.5 mm, 316 SS >= 3.0 mm spheres (set at validation with the jar's foil liner) | Test cards through the aperture at start, every 2 h, at end and after any stop; locked reject bin | Failed test: hold every pack since the last good test, re-run them, find the cause, record | QA reviews records daily; annual validation | MES pack run record, detector test log |

## Prerequisite programs (not CCPs)

- Supplier approval with COA per lot; spices bought steam-treated (no kill step in this plant); Salmonella negative in 375 g per COA.
- Bin lot control: every refill is scanned into the MES; bins run empty weekly so the lot set per batch stays small.
- Sieve (12 mesh) and grate magnet on every batch: screen and magnet checked and recorded per batch.
- Net contents: every unit weighed on P1-407; NIST HB 133 lot check in the MES.
- Label control: labels printed per run with the batch lot code; first-off label check signed in the MES.
- Pest control, glass and brittle plastic register, hygiene vestibule with hand sink P1-704.

## Sanitation schedule (SSOP)

| Task | When | Method | Verify | Who |
|---|---|---|---|---|
| Dry clean pack bench and filler | end of each pack day | vacuum (P1-702), dry brush (Vikan green) | visual + ATP < 150 RLU on 3 points | pack operator |
| Blender and flexible screw purge between blends | every blend change | run screw and blender empty, brush ribbons, vacuum valve; first 5 kg of the next blend back into its own drum | visual | blend operator |
| Bin run-empty and wipe | weekly per bin, at the low-level switch | feed to empty, vacuum, wipe cone with dry cloth | visual; MES closes the bin lot set | blend operator |
| Full dry clean of dosing and blending | end of each blending week | open blender (locked out), feeders screws out, hopper and drum-top sifter vacuumed | visual + ATP | blend operator |
| Wet clean (only if a wet event or pest finding) | as needed | disassemble, wash, sanitize (quat, no-rinse), dry 12 h before use | ATP + dryness check | sanitation |
| Environmental monitoring (Salmonella) | monthly, zones 2-4 | sponge swabs to lab | trend in QA | QA |
