# Down Home Creole: automated dry blending and packing plant

This is the design package for automating Down Home Creole's spice plant in Baton Rouge, LA, from receiving to the labeled, palletized case. It was built with the Anatomy skill, using the plant toolkit in `skills/anatomy/tools/plant/`.

- **Source:** the client's factory site (https://silocloud.dev/factory/#/floor), read page by page on 2026-11-17 and extracted to `data/site.json`. The site marks nearly all of its numbers as placeholders, so every value here carries a source tag.
- **Sized for:** 6,000 lb a day on one 8-hour shift, 5 days a week (30,000 lb and about 82,000 units a week). The client chose this "Growth" option.
- **Phase 1 first:** a smaller prototype plant (1,000 lb a week, seasonings only, 5 launch blends laid out for 13, bins with automatic dosing, about $184k with in-house stainless fabrication) is in [`phase1/`](phase1/README.md). Its Anatomy build package is `phase1/build/build.json`.
- **Scope:** the dry line only: 16 blends and 23 SKUs (shakers, jars, pouch, 5 lb tub, boxed wheat mixes). Sauces and the canned concept are not in this package.

## The plant in one paragraph

Ingredients are received and checked against their COA, then quarantined or released in the MES. They are stored with wheat in a locked cage.

Weighing and dispensing happen on scanned scales: majors on WS-201 and WS-202, and minors on WS-203 into a V-cone premix (PM-210).

Blending and screening:
- Salt is metered from a bulk bag (BB-302).
- The batch is mixed in a 36 cu ft Ross ribbon blender (RB-303) with a 12-minute mix and a salt-tracer CV of 5 % or less.
- It is sifted on a Kason 48 in screener with a magnet, then passes the metal detector, which is CCP-1.
- It is filled into one bulk bag per batch and held until QC releases it.

Line A packs the shakers and jars, in this order:
1. Spee-Dee rotary auger filler.
2. Kaps-All capper.
3. Enercon induction sealer.
4. Pack Leader labeler with a Videojet lot and best-by coder.
5. Cognex vision and reject.
6. Mettler-Toledo checkweigher, which rejects every unit under declared weight.
7. Wexxar erector.
8. Cobot case packer.
9. Sealer.
10. GS1-128 case label.
11. Robotiq cobot palletizer.
12. Lantech wrapper.

Station B, in its own room, packs the pouch, the tub and the three boxed wheat mixes.

## What is in this folder

| Path | What |
|---|---|
| `data/site_extract.py`, `site.json` | Everything read from the client's site: 45 ingredients, 16 formulas, 23 dry SKUs, packaging and the process |
| `design/design_basis.py` | Volume, shifts, OEE, building, product mix, ECOs, open questions, each tagged `site`, `client`, `documented`, `assumed` or `calculated` |
| `design/equipment.py` -> `equipment.json` | **71 line items**, each a real market machine or part with maker, model, specs, source URL, supplier, qty with its basis, price, footprint, power, air, dust and sanitary notes |
| `bom/equipment-bom.xlsx`, `.csv` | The same list as a procurement spreadsheet. **About $1.51M**, mostly estimates; the line items say which prices are published |
| `design/out/line-balance.md` | Blender sizing and pack-line loads, with bottlenecks |
| `design/out/food-safety.md` | Allergen matrix, shared-equipment controls, the gluten-free claim risk, zoning, sanitary, dust (NFPA 61/652), HACCP plan and SSOP schedule |
| `drawings/DH-drawing-set.pdf` | 11 sheets: LAY-001 plant layout (1:75), PFD-001, ASM-001 blending train (1:20), ASM-002 pack line A (1:40), ELE-001 power and network, ELE-002 I/O and cables, DH-101 to DH-105 custom parts |
| `drawings/LAY-001_plant_layout_mm.dxf`, `_in.dxf` | Layout for the architect, in mm and inch |
| `cad/` | STEP and STL of the custom parts DH-101 to DH-105 (cadquery `parts.py`) |
| `dxf/` | Laser cut files in mm and inch for DH-101 flange, DH-103, DH-104, DH-105 and the DH-106 gasket |
| `design/io.json` | 117 I/O points, 31 field cables, 16 motors with NEC FLA, the feeders and the network |
| `software/plc/` | Structured Text for PLC-601 (blending batch sequence) and PLC-602 (PackML line A), plus a Studio 5000 tag import generated from the I/O list |
| `software/mes/` | MES in Python (standard library only, 9 tests pass) covering recipes, batch capacity rule, weigh and dispense lot checks, PLC downloads, QC release, pack runs, first-off label check, GS1/ZPL bag, case and SSCC pallet labels, NIST HB 133, trace back/forward, the electronic batch record, and a web UI |

## Findings the client needs to see

1. **Line A runs at 88 %**, over the 85 % planning limit. The filler at 80 upm is the bottleneck. There are two ways to fix it: get the filler rated at 90 upm or more at FAT, or pack about 3 hours a week on a partial second shift.
2. **The gluten-free claim on the seasonings is at risk.** The three wheat mixes share the blender, the weigh room and the premixer. They pack only at station B, and the wheat campaign runs last on Friday, followed by a validated wet clean with gluten swabs. Even so, the claim needs the first lot after every wheat campaign tested below 10 ppm. The clean alternative is a dedicated small blender for the wheat mixes, which costs about $40k to $60k.
3. **ECO-001:** the 12 oz Original is set up on the site in a 235 mL shaker, which is 264 % of brimful. It is moved to the 12 oz jar that the other four 12 oz SKUs already use.
4. **ECO-002:** three SKUs fill to 93 to 95 % of brimful. Pilot-fill them before buying change parts.
5. **Dust:** a dust hazard analysis (NFPA 652) is required before ordering the dust collector. It is sized at 3,625 cfm, which is the sum of the pickups plus 25 %.

## Open questions for the client
- The sales mix by SKU. The weekly split in `design_basis.py` is assumed.
- The building: size, clear height (bulk bag frames need at least 20 ft), dock doors and power service. The design assumes 140 x 90 ft, 22 ft clear, and 480 V 400 A.
- Their GS1 company prefix. The labels use a placeholder.
- Whether sauces and canning should be added as a second phase.

## Regenerate everything

```
cd data && python3 site_extract.py
cd ../design && python3 design_basis.py && python3 plant_layout.py && python3 io_list.py && python3 equipment.py
python3 ../../../skills/anatomy/tools/plant/linebal.py design-basis.json linebal-config.json out
python3 ../../../skills/anatomy/tools/plant/layout.py layout.json equipment.json ../drawings
python3 ../../../skills/anatomy/tools/plant/foodsafety.py design-basis.json equipment.json layout.json foodsafety-config.json out
python3 make_sheets.py && (cd ../cad && python3 parts.py) && python3 ../bom/make_bom.py
cd ../software/plc && python3 gen_tags.py
cd ../mes && python3 -m unittest discover -s tests -t .
```

Prices are budget estimates unless the item says `documented`. Footprints marked `estimate` must be replaced with OEM general arrangement drawings before construction drawings are issued. A licensed electrical engineer stamps the final electrical design, and a PE reviews the dust-collector design and the structure.
