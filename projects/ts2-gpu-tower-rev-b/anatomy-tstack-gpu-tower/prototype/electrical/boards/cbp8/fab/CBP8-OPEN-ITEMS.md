# CBP-8: items to close before release to RushPCB

The CBP-8 backplane (948 nets, 8 layers) is autorouted and cleaned by script. The KiCad DRC in `cbp8-drc.rpt` still lists the items below. Close them by hand in KiCad (about 30 to 60 minutes of work), then re-run DRC and re-export with `kgen/build.py cbp8 fab`. **Do not order this board until the list is empty.** The other three boards (CPD-1, CCM-1 and TCD-1) are clean.

| # | Check | What | Where (page mm) |
|---|---|---|---|
| 1 | copper_sliver |  |  |
| 2 | starved_thermal | Zone [GND] on F.Cu; PTH pad 9 [GND] of J905 | (50.6000, 483.8000); (314.5800, 262.0000) |
| 3 | starved_thermal | Zone [GND] on B.Cu; PTH pad 3 [GND] of J905 | (50.6000, 483.8000); (310.7700, 262.0000) |
| 4 | clearance | Track [S8_12V] on F.Cu; Track [S8_FB33] on F.Cu | (79.1625, 104.6844); (79.0967, 105.6454) |
| 5 | clearance | Track [S8_12V] on In2.Cu; Track [S8_3V3] on In2.Cu | (75.1436, 104.8128); (73.3113, 103.7609) |
| 6 | track_dangling | Track [S2_12V_SNS] on B.Cu | (269.5000, 406.5000) |
| 7 | track_dangling | Track [S3_12V] on B.Cu | (255.4000, 355.7000) |
| 8 | track_dangling | Track [S6_12V] on B.Cu | (268.2750, 203.7500) |
| 9 | track_dangling | Track [S7_12V] on B.Cu | (255.4000, 152.5000) |
| 10 | track_dangling | Track [S7_12V_SNS] on B.Cu | (270.7625, 140.2500) |
| 11 | track_dangling | Track [S8_12V] on B.Cu | (255.4000, 101.7000) |
| 12 | track_dangling | Track [S8_12V_SNS] on B.Cu | (270.7625, 89.4500) |
| 13 | unconnected_items | Pad 3 [+12V] of U402 on B.Cu; Zone [+12V] on B.Cu | (279.1375, 291.4500); (283.2000, 483.8000) |
| 14 | unconnected_items | Pad 3 [+12V] of U302 on B.Cu; Zone [+12V] on B.Cu | (279.1375, 342.2500); (283.2000, 483.8000) |
| 15 | unconnected_items | Track [+3V3] on B.Cu; Track [+3V3] on In2.Cu | (303.0500, 271.7750); (306.1217, 262.0000) |
| 16 | unconnected_items | Zone [GND] on F.Cu; Zone [GND] on F.Cu | (50.6000, 483.8000); (50.6000, 483.8000) |
| 17 | unconnected_items | Zone [GND] on F.Cu; Zone [GND] on F.Cu | (50.6000, 483.8000); (50.6000, 483.8000) |
| 18 | unconnected_items | Track [S3_12V] on B.Cu; Pad 1 [S3_12V] of C307 on B.Cu | (268.9000, 355.8000); (276.0750, 357.4500) |
| 19 | unconnected_items | Zone [S3_12V_SNS] on B.Cu; Pad 4 [S3_12V_SNS] of U302 on B.Cu | (269.6000, 355.6000); (276.8625, 342.2500) |
| 20 | unconnected_items | Zone [S4_12V_SNS] on B.Cu; Pad 4 [S4_12V_SNS] of U402 on B.Cu | (269.6000, 304.8000); (276.8625, 291.4500) |
| 21 | unconnected_items | Pad A11 [S4_PERST_C#] of J401 on F.Cu; Pad 4 [S4_PERST_C#] of U404 on B.Cu | (68.9000, 319.0500); (278.8125, 308.1500) |
| 22 | unconnected_items | Zone [S5_12V] on F.Cu; Zone [S5_12V] on F.Cu | (255.0000, 255.2000); (255.0000, 255.2000) |
| 23 | unconnected_items | Track [S6_12V] on B.Cu; Via [S6_12V] on F.Cu - B.Cu | (273.6450, 180.1300); (266.4000, 194.2000) |
| 24 | unconnected_items | Track [S7_12V_SNS] on In2.Cu; Track [S7_12V_SNS] on B.Cu | (276.6000, 144.6000); (270.7625, 140.2500) |

## Notes
- **Slot 3 and slot 4 INA181 IN+ (pin 3, +12V).** A +3V3 track on B blocks the direct path to the +12V pour. Route the Kelvin from U302/U402 pin 3 to the bus side of shunt R302/R402, or move that +3V3 track.
- **"Zone [GND] on F.Cu" pairs.** These are small F-side GND fill islands. Add one GND via inside each one, or delete it.
- **Dangling 0.14 mm stubs at the slot pour corners.** These are freerouter leftovers. Delete them.
- **INA181 pinout** was checked against TI SBOS793H Table 5-1: 1 OUT, 2 GND, 3 IN+, 4 IN-, 5 REF, 6 VS. The design matches it.
