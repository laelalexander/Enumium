# Fastener schedule (generated from arm/fasteners.py)

Every screw in the arm, with its standard, length, what it clamps and its torque. Drawings call these numbers out in their hole tables. Stainless A2-70 throughout; blue threadlocker on metal threads without a nyloc nut. Torque values for screws bearing on printed PETG are deliberately low (the plastic creeps): snug with washers, then the value shown.

| No. | Fastener | Standard | Qty | Torque N·m [lbf·in] | Length check (stack) | Where |
|---|---|---|---|---|---|---|
| F01 | M5 x 90 socket head cap screw, A2-70 stainless | ISO 4762 | 15 | 2.5 [22] | 12 cheek + 56 block + 12 cheek + 2 x 1.0 washer + 5.0 nyloc + 2 thread = 89 | cheek-block-cheek stack, 4 per pitch joint (12); tube cross pin through each tube block (3) |
| F01W | M5 flat washer, A2 | ISO 7089 | 30 | - |  | 2 per F01 |
| F01N | M5 nyloc nut, A2 | ISO 10511 | 15 | - |  | 1 per F01 |
| F02 | M5 x 60 socket head cap screw, A2-70 | ISO 4762 | 3 | 2.5 [22] | 50 socket OD + 2 x 1.0 washer + 5.0 nyloc + 2 thread = 59 | cross pin through each tube_socket and its tube |
| F02W | M5 flat washer, A2 | ISO 7089 | 6 | - |  | 2 per F02 |
| F02N | M5 nyloc nut, A2 | ISO 10511 | 3 | - |  | 1 per F02 |
| F03 | M5 x 16 socket head cap screw, A2-70 | ISO 4762 | 16 | 2.5 [22] | 10 printed flange + 1.0 washer + 5 thread engagement in hub flange (MEASURE hub flange: need >= 5) | tube_socket to clamp-hub flange, 4 per pitch joint (12); base_top_plate to yaw clamp hub (4) |
| F03W | M5 flat washer, A2 | ISO 7089 | 16 | - |  | 1 per F03 |
| F04 | M5 x 20 socket head cap screw, A2-70 | ISO 4762 | 12 | 2.5 [22] | 12 cheek + 1.0 washer + 7 thread engagement in gearbox flange (check gearbox thread depth >= 8) | gearmotor flange to motor cheek, through the tension slots, 4 per pitch joint |
| F04W | M5 flat washer, A2 | ISO 7089 | 12 | - |  | 1 per F04 |
| F05 | M5 x 16 socket head cap screw, A2-70 | ISO 4762 | 4 | 4 [35] | 7 board left under the flange pocket + 1.5 fender washer + 7.5 thread in gearbox flange | yaw gearmotor to BASE-01 |
| F05W | M5 fender washer 15 mm OD, A2 | ISO 7093 | 4 | - |  | spreads the load on the plywood |
| F06 | M6 x 25 socket head cap screw, A2-70 | ISO 4762 | 8 | 3.5 [31] | 10 printed plate + 6 YAW-01 + 2 x 1.6 washer + 6.0 nyloc + 2 thread = 24.2 | base_top_plate to YAW-01 adapter disc |
| F06W | M6 flat washer, A2 | ISO 7089 | 16 | - |  | 2 per F06 |
| F06N | M6 nyloc nut, A2 | ISO 10511 | 8 | - |  | 1 per F06 |
| F07 | M5 x 30 button head screw, A2-70 | ISO 7380 | 4 | 3 [27] | turntable fixed ring 3 + GSK-01 1.5 + 19 board, into M5 tee nut from below (MEASURE ring holes) | turntable fixed ring to BASE-01 |
| F07T | M5 four-prong tee nut, 8 mm barrel x 9 mm | DIN 1624 | 4 | - |  | pressed into BASE-01 from below |
| F08 | M5 x 20 socket head cap screw, A2-70 | ISO 4762 | 4 | 4 [35] | 6 YAW-01 + 3 turntable ring + 1.0 washer + 5.0 nyloc + 2 thread = 17 (MEASURE ring thickness) | turntable rotating ring to YAW-01 |
| F08W | M5 flat washer, A2 | ISO 7089 | 4 | - |  | 1 per F08 |
| F08N | M5 nyloc nut, A2 | ISO 10511 | 4 | - |  | 1 per F08 |
| F09 | M4 x 14 socket head cap screw, A2-70 | ISO 4762 | 4 | 1.2 [11] | 8 adapter plate + 0.8 washer + 5 into the insert | gripper_adapter to gripper_body |
| F09W | M4 flat washer, A2 | ISO 7089 | 4 | - |  | 1 per F09 |
| F10 | M4 brass heat-set insert, OD 5.7-6.0 x 8.1 long | knurled, for plastics | 4 | - | hole Ø5.60 x 11 deep in gripper_body; set with 230-250 °C iron tip | gripper_body, for F09 |
| F11 | M3 x 10 socket head cap screw, A2-70 | ISO 4762 | 4 | 1 [9] | 5 printed wall + 5 thread engagement in NEMA 17 face | NEMA 17 to gripper_body |
| F12 | M3 x 40 socket head cap screw, A2-70 | ISO 4762 | 4 | 0.6 [5] | 30 jaw + 3.5 T8 nut flange + 0.5 washer + 2.4 nyloc + 2 thread = 38.4 | T8 lead-screw nut flange through gripper_jaw |
| F12N | M3 nyloc nut, A2 | ISO 10511 | 4 | - |  | 1 per F12 |
| F13 | M3 x 12 pan head screw + M3 nut + 2 washers, A2 | ISO 7045 / ISO 4032 | 10 | 0.5 [4] | switch body 6.4 + bracket 3 + nut | limit switches, 2 per switch (5 switches) |
| F14 | No.10 x 3 in flat head wood screw (5 x 75 mm) | ASME B18.6.1 | 8 | - | 19 board + 56 into the leg; drill 3.0 pilot in the leg, countersink the board | LEG-01 to BASE-01, 2 per leg |
| F15 | M3 x 8 button head screw + M3 nyloc nut, A2 | ISO 7380 / ISO 10511 | 60 | 0.6 [5] | 3 panel + 1.5 angle leg + nut | enclosure panels to the 10 x 10 corner angles (count from the ENC drawings) |
| F16 | M3 x 10 brass standoff M-F + M3 x 6 screw + M3 nut | - | 4 | 0.4 [4] |  | Arduino Mega to ENC-01 (drill from the board) |
| F17 | M4 x 10 pan head screw + M4 nyloc + washer, A2 | ISO 7045 | 24 | 1.2 [11] |  | DM542 drivers (4 each, 20) and PSU (4) to ENC-01: drill from the parts (patterns vary by maker) |
| F18 | Rubber bumper foot 20 x 10 mm with M4 x 12 screw | - | 4 | - |  | under ENC-01 |

Hole sizes: M3 clearance Ø3.4 [.134], M4 Ø4.5 [.177], M5 Ø5.5 [.217], M6 Ø6.5 [.256] (ISO 273 medium). Heat-set M4 insert pilot Ø5.6 [.220]. Tee nut barrel Ø8.0 [.315].

