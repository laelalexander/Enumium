# Cut list and fabrication package (generated)

Everything that is cut, drilled or machined rather than printed. Each part has a DXF in **mm and inch** (`fab/dxf/mm`, `fab/dxf/inch`), a 1:1 drill template (`fab/templates`, print at 100 %), a production drawing (`fab/drawings`, mm [in], hole and fastener tables) and a STEP model (`fab/step`).

DXF layers: `CUT_OUTSIDE` profile, `CUT_INSIDE` holes and cutouts, `POCKET_<depth>MM_<side>` pockets, `MARK` engrave or centre-punch only (drill these from the real part), `NOTES` never cut. Origin is the part's lower-left corner.

## Tube (1.5 in OD x 0.065 in wall 6061-T6)

All four pieces come out of **one 48 in (1219 mm) length**: 897 mm including 3 mm saw kerf per cut, 322 mm left over. A 36 in length is too short for all four.

| Part | Description | Cut length mm [in] | Cross-pin holes from left end | Mates with |
|---|---|---|---|---|
| TUBE-01 | Upper Arm Tube | 295 [11.614] | 27 [1.063], 270 [10.630] | Shoulder end in tube_socket (pin 27 from end), elbow end in elbow_tube_block (pin 25) |
| TUBE-02 | Forearm Tube | 320 [12.598] | 27 [1.063], 295 [11.614] | Elbow end in tube_socket (pin 27 from end), wrist end in wrist_tube_block (pin 25) |
| TUBE-03 | Riser Tube | 150 [5.906] | 125 [4.921] | Bottom bonded in base_top_plate (66 deep, epoxy); top end in shoulder_tube_block (pin 25) |
| TUBE-04 | Wrist Stub Tube | 120 [4.724] | 27 [1.063] | Wrist tube_socket end (pin 27); gripper_adapter end bonded 55 deep |

Cut square (within 0.5°), deburr inside and out. Drill one pin hole Ø5.5 [.217] on a V-block, assemble into the printed part, then drill the printed part's hole through the tube as a guide for any second hole so both line up.

## Sheet and plate parts

| Part | Description | Qty | Size mm [in] | Material | Process | Features |
|---|---|---|---|---|---|---|
| BASE-01 | Base Board | 1 | 457.2 x 457.2 x 19 [18.000 x 18.000 x 0.748] | 3/4 in Baltic birch plywood (18-19 mm) | CNC router or jigsaw + drill press | 21 |
| YAW-01 | Turntable Adapter Disc | 1 | 300.0 x 300.0 x 6 [11.811 x 11.811 x 0.236] | 6061-T6 aluminium plate 6 mm [.236] (or 12 mm Baltic birch) | Waterjet / CNC, or saw + drill from the 1:1 template | 15 |
| GSK-01 | Turntable Seat Gasket | 1 | 305.0 x 305.0 x 1.5 [12.008 x 12.008 x 0.059] | Neoprene 60A sheet 1.5 mm [1/16 in] | Knife, laser or drag-knife plotter | 5 |
| GSK-02 | Gripper Jaw Pad | 2 | 56.0 x 50.0 x 3 [2.205 x 1.969 x 0.118] | TPU 95A (print flat) or 3 mm neoprene with adhesive back | Knife or laser; or print | 0 |
| GSK-03 | Leg Foot Pad | 4 | 45.0 x 45.0 x 3 [1.772 x 1.772 x 0.118] | Rubber sheet 3 mm [1/8 in], 60A | Knife | 0 |
| ENC-01 | Enclosure Base Plate | 1 | 480.0 x 320.0 x 3 [18.898 x 12.598 x 0.118] | 5052 aluminium 3 mm (earth it) or 3 mm acrylic | Laser / waterjet / CNC | 14 |
| ENC-02 | Enclosure Lid | 1 | 480.0 x 320.0 x 3 [18.898 x 12.598 x 0.118] | 5052 aluminium 3 mm or 3 mm acrylic | Laser / waterjet / CNC | 23 |
| ENC-03 | Enclosure Front Wall | 1 | 480.0 x 110.0 x 3 [18.898 x 4.331 x 0.118] | 5052 aluminium 3 mm or 3 mm acrylic | Laser / waterjet / CNC | 28 |
| ENC-04 | Enclosure Back Wall | 1 | 480.0 x 110.0 x 3 [18.898 x 4.331 x 0.118] | 5052 aluminium 3 mm or 3 mm acrylic | Laser / waterjet / CNC | 14 |
| ENC-05 | Enclosure Left Wall | 1 | 314.0 x 110.0 x 3 [12.362 x 4.331 x 0.118] | 5052 aluminium 3 mm or 3 mm acrylic | Laser / waterjet / CNC | 16 |
| ENC-06 | Enclosure Right Wall (Arm Side) | 1 | 314.0 x 110.0 x 3 [12.362 x 4.331 x 0.118] | 5052 aluminium 3 mm or 3 mm acrylic | Laser / waterjet / CNC | 19 |

## Other cut parts

| Part | Description | Qty | Length mm [in] | Stock | Notes |
|---|---|---|---|---|---|
| ANG | enclosure corner angle, front/back walls, top and bottom | 4 | 470 [18.504] | 10 x 10 x 1.5 aluminium angle | deburr, transfer-drill from panels |
| ANG | enclosure corner angle, side walls, top and bottom | 4 | 294 [11.575] | 10 x 10 x 1.5 aluminium angle | deburr, transfer-drill from panels |
| ANG | enclosure corner angle, vertical corners | 4 | 90 [3.543] | 10 x 10 x 1.5 aluminium angle | deburr, transfer-drill from panels |
| LEG-01 | base leg | 4 | 200 [7.874] | Hardwood 45 x 45 | square ends |
| SHAFT-01 | joint shaft (as bought 150) | 3 | 150 [5.906] | 12 mm h6 rod | one flat, chamfer ends |

## Wire harness cut list

| Run | Cable | Cut length m [ft] | Ends |
|---|---|---|---|
| J1 yaw motor cable | 4-core shielded 18 AWG | 1.3 [4.3] | ferrules at driver; motor plug or solder + heatshrink at motor |
| J1 yaw limit switch | 2-core 22 AWG (twisted) | 1.3 [4.3] | ferrule at Mega terminal, 100 nF across switch |
| J2 shoulder motor cable | 4-core shielded 18 AWG | 1.8 [5.9] | ferrules at driver; motor plug or solder + heatshrink at motor |
| J2 shoulder limit switch | 2-core 22 AWG (twisted) | 1.8 [5.9] | ferrule at Mega terminal, 100 nF across switch |
| J3 elbow motor cable | 4-core shielded 18 AWG | 2.3 [7.5] | ferrules at driver; motor plug or solder + heatshrink at motor |
| J3 elbow limit switch | 2-core 22 AWG (twisted) | 2.3 [7.5] | ferrule at Mega terminal, 100 nF across switch |
| J4 wrist motor cable | 4-core shielded 18 AWG | 2.7 [8.9] | ferrules at driver; motor plug or solder + heatshrink at motor |
| J4 wrist limit switch | 2-core 22 AWG (twisted) | 2.7 [8.9] | ferrule at Mega terminal, 100 nF across switch |
| J5 gripper motor cable | 4-core shielded 18 AWG | 3.0 [9.8] | ferrules at driver; motor plug or solder + heatshrink at motor |
| J5 gripper limit switch | 2-core 22 AWG (twisted) | 3.0 [9.8] | ferrule at Mega terminal, 100 nF across switch |
| PSU V+ to fuse to E-stop to bus | 14 AWG red silicone | 0.6 [2.0] | ferrules |
| PSU V- to GND bus | 14 AWG black silicone | 0.4 [1.3] | ferrules |
| Bus to each driver VCC/GND (x5) | 18 AWG red + black | 1.8 [5.7] | ferrules, 350 mm each |
| Mega to drivers STEP/DIR/ENA | 22 AWG hookup, 3 colours | 4.5 [14.8] | 15 leads of 300 mm, ferrules at drivers |
| Mains IEC inlet to PSU L/N/PE | 18 AWG 3-core mains flex (H05VV-F 1.0 mm²) | 0.4 [1.3] | fork terminals at PSU; qualified person only |

Totals: 4-core shielded 18 AWG 11.1 m; 2-core 22 AWG (twisted) 11.1 m; 14 AWG red silicone 0.6 m; 14 AWG black silicone 0.4 m; 18 AWG red + black 1.8 m; 22 AWG hookup, 3 colours 4.5 m; 18 AWG 3-core mains flex (H05VV-F 1.0 mm²) 0.4 m. Cut lengths include a 300 mm service loop and 10 % drape.

## Stability check

At 5 lb and full reach the payload alone puts about 22 N·m of tipping moment on the base, plus about 10 N·m from the arm. BASE-01 with motors and legs resists only about 15 N·m about its front edge, so **clamp or bolt the base to the bench** (two C-clamps on the board edge, or screws through the GSK-03 pads into the bench top).

