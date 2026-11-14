# Procurement list (generated)

Everything to buy for one arm, with planning prices. **Prices are estimates from typical online listings, not quotes;** check each listing's dimensions against `arm/hardware.py` `HW` before ordering. Track orders in [`procurement.csv`](procurement.csv) (Status, Ordered from, Order #, Received columns).

| Category | Lines | Est. USD |
|---|---|---|
| Motors | 4 | 340 |
| Mechanical | 13 | 306 |
| Electronics | 6 | 227 |
| Materials | 8 | 182 |
| Fasteners | 32 | 67 |
| Wiring | 9 | 111 |
| **Total** | **72** | **1,233** |

## Order first (long lead, and their measurements set the printed parts)

1. The four NEMA 23 gearmotors, the turntable bearing and the four clamp hubs. Measure flange, pilot, shaft and bolt circles, update `HW`, run `python run.py build` and `python run.py print`, then start printing.
2. Pulleys, belts, shafts, bearings: check pulley bores against the gearbox output shaft (often 14 mm) and the 12 mm joint shaft.
3. Everything else can arrive while the parts print (about 50 h of printing).

## Motors

| Item | Qty | Unit | Est. each | Est. total | Search for | Used for |
|---|---|---|---|---|---|---|
| NEMA 23 2.8 A stepper + 20:1 planetary gearbox (yaw) | 1 | each | 85.00 | 85.00 | NEMA 23 stepper motor 20:1 planetary gearbox 2.8A | J1 yaw |
| NEMA 23 2.8 A stepper + 20:1 planetary gearbox (shoulder) | 1 | each | 85.00 | 85.00 | NEMA 23 stepper motor 20:1 planetary gearbox 2.8A | J2 shoulder; 100:1 total with belt stage |
| NEMA 23 2.8 A stepper + 20:1 planetary gearbox (elbow) | 1 | each | 85.00 | 85.00 | NEMA 23 stepper motor 20:1 planetary gearbox 2.8A | J3 elbow; 60:1 total with belt stage |
| NEMA 23 2.8 A stepper + 20:1 planetary gearbox (wrist) | 1 | each | 85.00 | 85.00 | NEMA 23 stepper motor 20:1 planetary gearbox 2.8A | J4 wrist |

## Mechanical

| Item | Qty | Unit | Est. each | Est. total | Search for | Used for |
|---|---|---|---|---|---|---|
| 1.5 in OD aluminium round tube, 0.065 in wall, 6061, 48 in length | 1 | 48 in length | 32.00 | 32.00 | 1.5 inch OD aluminum tube 0.065 wall 48 inch | all four tubes (TUBE-01..04) cut from one length; see fab/CUTLIST.md |
| Heavy-duty turntable bearing 12 in (rated >= 500 lb) | 1 | each | 38.00 | 38.00 | 12 inch heavy duty lazy susan turntable bearing 1000 lb | yaw bearing; check bolt circle then set HW.turntable_pcd |
| 12 mm hardened/stainless shaft rod, 150 mm | 3 | each | 9.00 | 27.00 | 12mm linear shaft rod 150mm (6 mm too small) | shoulder/elbow/wrist joint shafts |
| 6001-2RS ball bearing 12x28x8 | 8 | each (10-pack ~16) | 1.60 | 12.80 | 6001-2RS bearing 12x28x8 | 2 per pitch joint + spares |
| 12 mm shaft clamping hub with 4-hole flange (aluminium) | 4 | each | 9.00 | 36.00 | 12mm clamping shaft hub flange coupling aluminum (yaw one: bore = gearbox output) | 3 lock distal links to joint shafts, 1 locks base_top_plate to the yaw gearbox; check bolt circle -> HW.hub_pcd |
| Shaft collars 12 mm | 6 | each | 1.50 | 9.00 | 12mm shaft collar clamp type | axial retention |
| HTD 5M timing pulley, 15 mm belt, 16T (bore = gearbox output shaft) | 3 | each | 7.00 | 21.00 | HTD 5M 16 tooth pulley 15mm belt bore 14mm (check bore) | motor pulleys, one per pitch joint |
| HTD 5M pulley, 12 mm bore, large (see BOM table for teeth) | 3 | each | 14.00 | 42.00 | HTD 5M pulley 12mm bore 15mm belt | joint-shaft pulleys: teeth listed below |
| HTD 5M belt, 15 mm wide (lengths listed below) | 3 | each | 9.00 | 27.00 | HTD 5M timing belt 15mm closed loop | one per pitch joint, pick closest stock length |
| NEMA 17 stepper w/ T8 lead screw 150 mm + nut + 5->8 mm coupler | 1 | kit | 32.00 | 32.00 | NEMA 17 stepper motor T8 lead screw 150mm with nut | gripper drive |
| 8 mm linear rod 150 mm + LM8UU bearings | 2 | rod + LM8UU | 9.00 | 18.00 | 8mm linear rod 150mm LM8UU | gripper slides: 2 rods, 2 bearings |
| Cable glands PG9 (5) + PG7 (5), nylon | 1 | kit | 9.00 | 9.00 | PG9 PG7 cable gland kit | ENC-06 motor and limit cable entries |
| Rubber grommet 32 mm hole | 1 | each | 2.00 | 2.00 | rubber grommet 1-1/4 inch | BASE-01 harness pass-through |

## Electronics

| Item | Qty | Unit | Est. each | Est. total | Search for | Used for |
|---|---|---|---|---|---|---|
| Stepper driver DM542 (or DM556), 24-48 V | 5 | each | 28.00 | 140.00 | DM542 stepper driver 4.2A | 4 joints + gripper (gripper may use TB6600) |
| 24 V 15 A (360 W) power supply | 1 | each | 34.00 | 34.00 | 24V 15A power supply 360W | motors |
| Arduino Mega 2560 R3 | 1 | each (clone ~18) | 22.00 | 22.00 | Arduino Mega 2560 R3 | controller (firmware/arm_controller) |
| E-stop mushroom button, latching, NC | 1 | each | 14.00 | 14.00 | emergency stop switch latching NC 22mm | cuts 24 V to all drivers |
| Mechanical limit switches (NC) | 1 | 5-pack | 8.00 | 8.00 | micro limit switch lever 5 pack NC | homing, one per joint |
| Fuse holder + 20 A fuse, 14 AWG wire, ferrules | 1 | kit | 9.00 | 9.00 | inline fuse holder 20A 14awg | power distribution |

## Materials

| Item | Qty | Unit | Est. each | Est. total | Search for | Used for |
|---|---|---|---|---|---|---|
| PETG filament 1.75 mm, 1 kg (prints need 773 g; +25 % allowance) + 250 g TPU 95A for jaw pads | 1 | per 1 kg spool | 22.00 | 22.00 | PETG 1.75mm 1kg x2; TPU 95A | printed parts |
| Plywood or MDF board 18 x 18 in, 3/4 in | 1 | each | 18.00 | 18.00 | 3/4 inch plywood 18x18 | base; drill hole for yaw gearbox |
| 6061-T6 aluminium plate 6 mm (1/4 in), 12 x 12 in | 1 | each | 24.00 | 24.00 | 6061 aluminum plate 1/4 x 12 x 12 | YAW-01 turntable adapter disc |
| Aluminium sheet 5052, 3 mm (1/8 in), 24 x 48 in (or 3 mm acrylic) | 1 | each | 70.00 | 70.00 | 5052 aluminum sheet 1/8 24x48 | ENC-01..06 enclosure panels |
| Aluminium angle 10 x 10 x 1.5 mm (3/8 in), 1 m | 4 | per 1 m | 6.00 | 24.00 | aluminum angle 3/8 x 3/8 x 1/16 | enclosure corner angles (12 pieces) |
| Neoprene sheet 1.5 mm (1/16 in) 60A, 12 x 12 in | 1 | each | 9.00 | 9.00 | neoprene rubber sheet 1/16 12x12 | GSK-01 turntable seat gasket |
| Rubber sheet 3 mm (1/8 in) 60A, 12 x 12 in | 1 | each | 9.00 | 9.00 | rubber sheet 1/8 12x12 | GSK-02 jaw pads (if not printed), GSK-03 foot pads |
| Hardwood 2 x 2 (45 x 45 mm), 1 m | 1 | each | 6.00 | 6.00 | hardwood 2x2 36 inch | LEG-01 base legs, 4 x 200 mm |

## Fasteners

| Item | Qty | Unit | Est. each | Est. total | Search for | Used for |
|---|---|---|---|---|---|---|
| F01 M5 x 90 socket head cap screw, A2-70 stainless (ISO 4762) | 15 | each | 0.20 | 3.00 | M5 x 90 socket head cap screw, A2-70 stainless | cheek-block-cheek stack, 4 per pitch joint (12); tube cross pin through each tube block (3) |
| F01W M5 flat washer, A2 (ISO 7089) | 30 | each | 0.20 | 6.00 |  M5 flat washer, A2 | 2 per F01 |
| F01N M5 nyloc nut, A2 (ISO 10511) | 15 | each | 0.20 | 3.00 |  M5 nyloc nut, A2 | 1 per F01 |
| F02 M5 x 60 socket head cap screw, A2-70 (ISO 4762) | 3 | each | 0.20 | 0.60 | M5 x 60 socket head cap screw, A2-70 | cross pin through each tube_socket and its tube |
| F02W M5 flat washer, A2 (ISO 7089) | 6 | each | 0.20 | 1.20 |  M5 flat washer, A2 | 2 per F02 |
| F02N M5 nyloc nut, A2 (ISO 10511) | 3 | each | 0.20 | 0.60 |  M5 nyloc nut, A2 | 1 per F02 |
| F03 M5 x 16 socket head cap screw, A2-70 (ISO 4762) | 16 | each | 0.20 | 3.20 | M5 x 16 socket head cap screw, A2-70 | tube_socket to clamp-hub flange, 4 per pitch joint (12); base_top_plate to yaw clamp hub (4) |
| F03W M5 flat washer, A2 (ISO 7089) | 16 | each | 0.20 | 3.20 |  M5 flat washer, A2 | 1 per F03 |
| F04 M5 x 20 socket head cap screw, A2-70 (ISO 4762) | 12 | each | 0.20 | 2.40 | M5 x 20 socket head cap screw, A2-70 | gearmotor flange to motor cheek, through the tension slots, 4 per pitch joint |
| F04W M5 flat washer, A2 (ISO 7089) | 12 | each | 0.20 | 2.40 |  M5 flat washer, A2 | 1 per F04 |
| F05 M5 x 16 socket head cap screw, A2-70 (ISO 4762) | 4 | each | 0.20 | 0.80 | M5 x 16 socket head cap screw, A2-70 | yaw gearmotor to BASE-01 |
| F05W M5 fender washer 15 mm OD, A2 (ISO 7093) | 4 | each | 0.20 | 0.80 |  M5 fender washer 15 mm OD, A2 | spreads the load on the plywood |
| F06 M6 x 25 socket head cap screw, A2-70 (ISO 4762) | 8 | each | 0.20 | 1.60 | M6 x 25 socket head cap screw, A2-70 | base_top_plate to YAW-01 adapter disc |
| F06W M6 flat washer, A2 (ISO 7089) | 16 | each | 0.20 | 3.20 |  M6 flat washer, A2 | 2 per F06 |
| F06N M6 nyloc nut, A2 (ISO 10511) | 8 | each | 0.20 | 1.60 |  M6 nyloc nut, A2 | 1 per F06 |
| F07 M5 x 30 button head screw, A2-70 (ISO 7380) | 4 | each | 0.20 | 0.80 | M5 x 30 button head screw, A2-70 | turntable fixed ring to BASE-01 |
| F07T M5 four-prong tee nut, 8 mm barrel x 9 mm (DIN 1624) | 4 | each | 0.20 | 0.80 |  M5 four-prong tee nut, 8 mm barrel x 9 mm | pressed into BASE-01 from below |
| F08 M5 x 20 socket head cap screw, A2-70 (ISO 4762) | 4 | each | 0.20 | 0.80 | M5 x 20 socket head cap screw, A2-70 | turntable rotating ring to YAW-01 |
| F08W M5 flat washer, A2 (ISO 7089) | 4 | each | 0.20 | 0.80 |  M5 flat washer, A2 | 1 per F08 |
| F08N M5 nyloc nut, A2 (ISO 10511) | 4 | each | 0.20 | 0.80 |  M5 nyloc nut, A2 | 1 per F08 |
| F09 M4 x 14 socket head cap screw, A2-70 (ISO 4762) | 4 | each | 0.20 | 0.80 | M4 x 14 socket head cap screw, A2-70 | gripper_adapter to gripper_body |
| F09W M4 flat washer, A2 (ISO 7089) | 4 | each | 0.20 | 0.80 |  M4 flat washer, A2 | 1 per F09 |
| F10 M4 brass heat-set insert, OD 5.7-6.0 x 8.1 long (knurled, for plastics) | 4 | each | 0.30 | 1.20 | M4 brass heat-set insert, OD 5.7-6.0 x 8.1 long | gripper_body, for F09 |
| F11 M3 x 10 socket head cap screw, A2-70 (ISO 4762) | 4 | each | 0.20 | 0.80 | M3 x 10 socket head cap screw, A2-70 | NEMA 17 to gripper_body |
| F12 M3 x 40 socket head cap screw, A2-70 (ISO 4762) | 4 | each | 0.20 | 0.80 | M3 x 40 socket head cap screw, A2-70 | T8 lead-screw nut flange through gripper_jaw |
| F12N M3 nyloc nut, A2 (ISO 10511) | 4 | each | 0.20 | 0.80 |  M3 nyloc nut, A2 | 1 per F12 |
| F13 M3 x 12 pan head screw + M3 nut + 2 washers, A2 (ISO 7045 / ISO 4032) | 10 | each | 0.20 | 2.00 | M3 x 12 pan head screw + M3 nut + 2 washers, A2 | limit switches, 2 per switch (5 switches) |
| F14 No.10 x 3 in flat head wood screw (5 x 75 mm) (ASME B18.6.1) | 8 | each | 0.20 | 1.60 | No.10 x 3 in flat head wood screw | LEG-01 to BASE-01, 2 per leg |
| F15 M3 x 8 button head screw + M3 nyloc nut, A2 (ISO 7380 / ISO 10511) | 60 | each | 0.20 | 12.00 | M3 x 8 button head screw + M3 nyloc nut, A2 | enclosure panels to the 10 x 10 corner angles (count from the ENC drawings) |
| F16 M3 x 10 brass standoff M-F + M3 x 6 screw + M3 nut (-) | 4 | each | 0.50 | 2.00 | M3 x 10 brass standoff M-F + M3 x 6 screw + M3 nut | Arduino Mega to ENC-01 (drill from the board) |
| F17 M4 x 10 pan head screw + M4 nyloc + washer, A2 (ISO 7045) | 24 | each | 0.20 | 4.80 | M4 x 10 pan head screw + M4 nyloc + washer, A2 | DM542 drivers (4 each, 20) and PSU (4) to ENC-01: drill from the parts (patterns vary by maker) |
| F18 Rubber bumper foot 20 x 10 mm with M4 x 12 screw (-) | 4 | each | 0.50 | 2.00 | Rubber bumper foot 20 x 10 mm with M4 x 12 screw | under ENC-01 |

## Wiring

| Item | Qty | Unit | Est. each | Est. total | Search for | Used for |
|---|---|---|---|---|---|---|
| 4-core shielded stepper cable 18 AWG | 1 | 10 m | 22.00 | 22.00 | 4-core shielded stepper cable 18 AWG | motor phases, twisted/shielded per ELE-001 |
| 14 AWG silicone wire, red + black | 1 | 5 m each | 14.00 | 14.00 | 14 AWG silicone wire, red + black | 24 V and GND distribution |
| 22 AWG hookup wire kit | 1 | kit | 12.00 | 12.00 | 22 AWG hookup wire kit | STEP/DIR/ENA and limit switch signals |
| Wire ferrule kit + crimper | 1 | kit | 25.00 | 25.00 | Wire ferrule kit + crimper | driver and PSU screw terminals |
| IEC C14 inlet with switch and fuse | 1 | each | 8.00 | 8.00 | IEC C14 inlet with switch and fuse | mains input to the PSU |
| Lever terminal blocks (Wago 221 style) | 1 | 10-pack | 9.00 | 9.00 | Lever terminal blocks (Wago 221 style) | 24 V / GND bus |
| USB-B cable 2 m | 1 | each | 6.00 | 6.00 | USB-B cable 2 m | Mega to PC |
| 100 nF ceramic capacitors | 1 | pack | 5.00 | 5.00 | 100 nF ceramic capacitors | across each limit switch (ELE-001 note) |
| Cable chain or spiral wrap | 1 | 2 m | 10.00 | 10.00 | Cable chain or spiral wrap | motor cables along the arm |

## Tools (not costed)

| Tool | For |
|---|---|
| Calipers | check every HW dimension |
| 12 mm reamer or drill | shaft bores |
| 8 mm reamer or drill | rod bores |
| Hacksaw or chop saw + deburr tool | cut tubes |
| Drill press, V-block, 5.5 / 3.0 / 8.0 mm bits, 90° countersink | cross-pin holes, BASE-01, legs |
| Jigsaw or CNC router; or send fab/dxf to a laser / waterjet shop | plates and panels |
| Torque screwdriver 0.5-5 N·m | fastener torques in fab/FASTENERS.md |
| Soldering iron with heat-set insert tip | F10 M4 inserts |
| Multimeter | motor phase pairs, wiring checks |
| Hex keys, blue threadlocker | assembly |

Optional upgrades: NEMA 23 motors with 24 V holding brakes on shoulder and elbow (the arm drops on power loss), a Teensy 4.1 instead of the Mega if you need all joints at full speed together.
