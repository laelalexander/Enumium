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
| BB-302 | Bulk bag discharger for salt with flexible screw conveyor to blender | allergen-free, wheat | salt only, never sees wheat directly; screw tube dry-cleaned with the train |
| BD-301 | Bag dump station with integral dust collector and flexible screw conveyor to blender | allergen-free, wheat | wheat last; dry clean + wet clean of hopper and screw, swab |
| BF-306 | Bulk bag filler with load cells (one bag = one batch, held for QC release) | allergen-free, wheat | spout and seal wet clean, swab |
| BU-502 | Bulk bag discharger feeding NW-501 | allergen-free, wheat | station B in room B: allergen-free products packed on B only before the wheat campaign of the week, then full wet clean |
| FC-307 | Flexible screw conveyor: metal detector outlet hopper up to the bulk bag filler inlet | allergen-free, wheat | screw out, wet clean, swab |
| MD-305 | Gravity-fall metal detector with diverter reject | allergen-free, wheat | wet wipe aperture, swab |
| NW-501 | Net-weight auger filler for pouches, tubs and carton liners | allergen-free, wheat | same as BU-502 |
| PM-210 | Premix V-cone blender for minors (<2%) with carrier salt | allergen-free, wheat | wheat premix last; V-cone wet clean, swab |
| RB-303 | Ribbon blender, 36 cu ft working, sanitary | allergen-free, wheat | Friday wheat campaign last; full wet clean (CIP-less: open, scrape, wash, sanitize, dry), gluten swab at 5 points, first blend Monday tested for gluten |
| SC-304 | Sanitary vibratory sifter (scalping 12 mesh) with discharge magnet | allergen-free, wheat | screen out, wet clean, swab |

## Claims

- **Gluten free (< 20 ppm, 21 CFR 101.91)** (Creole Chameleon and launch seasonings): AT RISK: needs validated clean + finished-product test; shared: BB-302, BD-301, BF-306, BU-502, FC-307, MD-305, NW-501, PM-210, RB-303, SC-304. Hold first lot after every wheat campaign until an ELISA (R5) test of finished product reads < 10 ppm; or buy a dedicated small blender for the 3 wheat mixes (about $40-60k) and remove the risk.

## Hygiene zoning of product-contact machines

| Tag | Room | Zone | OK |
|---|---|---|---|
| PM-210 | Weigh & dispense | Z3 high-care dry (exposed product) | yes |
| BD-301 | Blending room | Z3 high-care dry (exposed product) | yes |
| BB-302 | Blending room | Z3 high-care dry (exposed product) | yes |
| RB-303 | Blending room | Z3 high-care dry (exposed product) | yes |
| SC-304 | Blending room | Z3 high-care dry (exposed product) | yes |
| MD-305 | Blending room | Z3 high-care dry (exposed product) | yes |
| BF-306 | Blending room | Z3 high-care dry (exposed product) | yes |
| FC-307 | Blending room | Z3 high-care dry (exposed product) | yes |
| BU-401 | Packing hall A | Z3 high-care dry (exposed product) | yes |
| FL-403 | Packing hall A | Z3 high-care dry (exposed product) | yes |
| NW-501 | Pack room B (wheat) | Z3A allergen (wheat) exposed | yes |
| BU-502 | Pack room B (wheat) | Z3A allergen (wheat) exposed | yes |

## Combustible dust

Pickups total **2900 cfm**; DC-310 design **3625 cfm** (needs 25% margin): OK.

| Pickup | cfm | qty |
|---|---|---|
| WS-204 | 400 | 2 |
| BB-302 | 300 | 1 |
| RB-303 | 200 | 1 |
| SC-304 | 200 | 1 |
| BF-306 | 300 | 1 |
| BU-401 | 300 | 1 |
| FL-403 | 250 | 1 |
| NW-501 | 250 | 1 |
| BU-502 | 300 | 1 |

- NFPA 652 dust hazard analysis (DHA) before ordering DC-310; send Kst/Pmax and MIE samples of the 3 highest-volume blends to a test lab.
- NFPA 61 (agricultural/food dusts): collector outside the building, explosion vent directed away from people, isolation flap valve on the inlet duct.
- Ducts sized for >= 4,000 ft/min transport velocity; no horizontal duct runs where avoidable; cleanouts every 3 m.
- Bond and ground every conveying element (< 10 ohm); flexible screws and FIBC spouts use Type C bags or grounded Type B with a grounding clamp on BB-302, BU-401 and BU-502.
- Housekeeping: dust layer on any surface over 1/32 in (0.8 mm) triggers cleaning; vacuum only with a Class II Div 2 rated vacuum (Nilfisk), never compressed air.
- Electrical in blending and weigh rooms: Class II Div 2 Group G unless the DHA shows otherwise; panels CP-300/CP-400 sit outside the exposed-product rooms.

## HACCP plan

| CCP | Step | Hazard | Critical limit | Monitoring | Corrective action | Verification | Records |
|---|---|---|---|---|---|---|---|
| CCP-1 | Metal detection MD-305 (after sifter, before bulk bag) | Physical: metal fragments from raw spice or equipment wear | No blend passes containing Fe >= 1.5 mm, non-Fe >= 2.0 mm, 316 SS >= 2.5 mm spheres (confirm at FAT with the product effect) | Test wands through the aperture at start, every 2 h, at end and after any stop; reject-confirm sensor and locked reject bin | Failed test: hold all blend since the last good test, re-run it through MD-305, find the cause, record | QA reviews records daily; annual validation by Mettler-Toledo | MES batch record (md_rejects), MD-305 test log |
| CCP-2 (allergen, if the HACCP team classifies it as a CCP) | Allergen changeover after the wheat campaign | Chemical/allergen: wheat gluten cross-contact into gluten-free seasonings | Gluten swab < 10 ppm at every listed point; first allergen-free lot < 10 ppm (ELISA R5) | Swabs after the wet clean; finished-product test of the first lot | Re-clean and re-swab; hold and test lots; no gluten-free claim on a failed lot | Quarterly validation study; QA review | SSOP log, swab results, ELISA certificate in MES |

## Prerequisite programs (not CCPs)

- Supplier approval with COA per lot; spices bought steam-treated or ETO-free validated (Salmonella log reduction by the supplier) because the plant has no kill step.
- Raw material micro: Salmonella negative in 375 g, per COA; skip-lot verification testing.
- Sifter SC-304 with a 12 mesh screen and the DH-102 magnet: screens checked for damage each shift (prerequisite, not a CCP).
- Net contents: CW-409 rejects every unit under declared (site rule); NIST HB 133 lot check in the MES.
- Label control: first-off UPC and lot code check signed in the MES before the line can run; label rolls stored per SKU.
- Pest control, glass and brittle plastic register, foreign-material policy, hygiene vestibule with hand wash and boot wash into Z3.

## Sanitation schedule (SSOP)

| Task | When | Method | Verify | Who |
|---|---|---|---|---|
| Dry clean pack line A contact parts | end of every shift (30 min) | vacuum (Nilfisk Class II), dry brush (Vikan color-coded), wipe | visual + ATP swab < 150 RLU on 3 points | line operators |
| Blender sequence purge between allergen-free formulas | every formula change | run blender empty, brush ribbons, vacuum valve, purge with 25 kg salt (reused as carrier salt) | visual | blend operator |
| Full dry clean of the blending train | end of each blender campaign | open RB-303 cover (locked out), scrape and vacuum; sifter screen out; magnet wiped | visual + ATP | blend operator |
| Wet clean after wheat | Friday after the wheat campaign (outside production minutes) | disassemble per the joints on ASM-001; wash, sanitize (quat, no-rinse), dry with forced air for 12 h | gluten swabs < 10 ppm; first Monday lot ELISA | sanitation crew |
| Station B wet clean | after the wheat campaign on B | same as above for BU-502 and NW-501 | gluten swabs | sanitation crew |
| Room clean (floors, ledges, overhead) | weekly; overhead monthly | vacuum top-down, no compressed air | visual; dust layer < 1/32 in | sanitation crew |
| Environmental monitoring (Salmonella) | monthly in Z3, zones 2-4 swabs | sponge swabs to lab | trend in QA | QA |
