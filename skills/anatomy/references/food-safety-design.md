# Food-safety design (dry food plants)

Tool: `tools/plant/foodsafety.py design-basis.json equipment.json layout.json foodsafety-config.json out_dir`. It writes `food-safety.json/.md` and exits 1 on any failed check.

## What the tool checks
1. **Allergen matrix**: formula × allergen, from the site data.
2. **Shared equipment**: every product-contact machine on more than one allergen route (from `routes` in the config) must have a validated clean in `validated_cleans`. Each free-from claim (for example gluten-free under 21 CFR 101.91, < 20 ppm) is marked AT RISK when an allergen shares a machine with it, and the config states the action, such as a finished-product ELISA, or dedicated equipment with its cost.
3. **Hygiene zoning**: product-contact machines sit in Z3 (exposed product). Allergen-only machines sit in Z3A.
   - Z0: outside
   - Z1: warehouse, closed product
   - Z2: controlled, closed packaging
   - Z3: high-care dry, exposed product
   - Z3A: allergen exposed
4. **Sanitary construction**: every product-contact machine states its construction, for example 304/316 SS, Ra ≤ 0.8 µm, tool-free disassembly, 3-A or EHEDG where offered.
5. **Combustible dust** (NFPA 652 / NFPA 61): the sum of the pickups (`dust_cfm` × qty) must not exceed the collector's `design_cfm` with a 25 % margin. The NFPA items are listed: a DHA before ordering, a collector outside with venting and isolation, transport velocity, bonding and grounding, housekeeping, and the electrical classification.

## What the package must include (written into the config, printed in the report)
- **HACCP plan**: each CCP with its hazard, critical limit, monitoring, corrective action, verification and records. For a dry spice plant with no kill step:
  - Metal detection is CCP-1.
  - Allergen changeover is CCP-2 where the HACCP team classifies it as one.
  - Pathogen control is a supplier prerequisite (treated spices and COA), not a plant CCP. Say so plainly.
- **Prerequisite programs**: supplier approval, sifting and screens, net contents (NIST HB 133), label control, pest control, glass register, hygiene vestibule.
- **SSOP schedule**: task, when, method, verification (ATP RLU limits and gluten swabs) and who does it.
- **MES enforcement** (see the software phase): only QC-released blend can be packed; allergen products only pack in their room; the first-off label check is required before the line runs.

## Things that go wrong
- A free-from claim on the front of pack while the same blender runs wheat. Flag it in the first reply.
- Compressed air used for cleaning dust. It is not allowed; use rated vacuums.
- The metal detector placed before the sifter. Put it after the sifter and magnet, as close to the pack as the layout allows, with a locked reject bin and a reject-confirm sensor.
