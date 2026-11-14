# Procurement list (generated)

Everything to buy for one arm, with planning prices. **Prices are estimates from typical online listings, not quotes;** check each listing's dimensions against `arm/hardware.py` `HW` before ordering. Track orders in [`procurement.csv`](procurement.csv) (Status, Ordered from, Order #, Received columns).

| Category | Lines | Est. USD |
|---|---|---|
| Motors | 4 | 340 |
| Mechanical | 11 | 391 |
| Electronics | 6 | 227 |
| Materials | 2 | 40 |
| Fasteners | 13 | 30 |
| Wiring | 9 | 111 |
| **Total** | **45** | **1,139** |

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
| 1.5 in OD aluminium round tube, 0.065 in wall, 6061 (36 in or 48 in length) | 4 | 48 in length | 32.00 | 128.00 | 1.5 inch OD aluminum tube 0.065 wall 48 inch | 2 links + riser + wrist stub (cut to length) |
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
| PETG filament 1.75 mm, 1 kg (prints need 774 g; +25 % allowance) + 250 g TPU 95A for jaw pads | 1 | per 1 kg spool | 22.00 | 22.00 | PETG 1.75mm 1kg x2; TPU 95A | printed parts |
| Plywood or MDF board 18 x 18 in, 3/4 in | 1 | each | 18.00 | 18.00 | 3/4 inch plywood 18x18 | base; drill hole for yaw gearbox |

## Fasteners

| Item | Qty | Unit | Est. each | Est. total | Search for | Used for |
|---|---|---|---|---|---|---|
| M5 x 90 socket head + nyloc nut | 15 | each | 0.25 | 3.75 | M5 x 90 socket head + nyloc nut | 4 through each cheek-block-cheek stack, 1 cross pin per tube block |
| M5 x 60 socket head + nyloc nut | 3 | each | 0.25 | 0.75 | M5 x 60 socket head + nyloc nut | cross pin through each tube_socket |
| M5 x 20 socket head | 16 | each | 0.25 | 4.00 | M5 x 20 socket head | tube_socket and base_top_plate to clamp-hub flanges (check hub thread) |
| M5 x 16 socket head + washer | 12 | each | 0.25 | 3.00 | M5 x 16 socket head + washer | gearmotor flange to motor cheek (slotted holes) |
| M5 x 35 socket head + washer + nut | 4 | each | 0.25 | 1.00 | M5 x 35 socket head + washer + nut | yaw gearmotor to the base board |
| M6 x 20 socket head + nyloc nut | 8 | each | 0.25 | 2.00 | M6 x 20 socket head + nyloc nut | turntable rotating ring to base_top_plate |
| M6 x 35 bolt + T-nut | 8 | each | 0.25 | 2.00 | M6 x 35 bolt + T-nut | turntable fixed ring to the base board |
| M4 x 14 socket head | 4 | each | 0.25 | 1.00 | M4 x 14 socket head | gripper body to gripper_adapter |
| M4 heat-set insert (5.7 mm OD, 4 mm long) | 4 | each | 0.30 | 1.20 | M4 heat-set insert (5.7 mm OD, 4 mm long) | in gripper_body for the adapter screws |
| M3 x 10 socket head | 8 | each | 0.25 | 2.00 | M3 x 10 socket head | NEMA17 to gripper body (4), T8 nut flange to jaw (4) |
| M3 nut | 4 | each | 0.25 | 1.00 | M3 nut | T8 nut flange |
| M3 x 12 screw + nut | 10 | each | 0.25 | 2.50 | M3 x 12 screw + nut | limit switches (2 each) |
| Wood screws 4 x 16 mm | 24 | each | 0.25 | 6.00 | Wood screws 4 x 16 mm | PSU, Mega standoffs, drivers, E-stop box to the bench board |

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
| Drill + 5.5 mm bit | cross-pin holes in tubes |
| Soldering iron with heat-set insert tip | M4 inserts |
| Multimeter | motor phase pairs, wiring checks |
| Hex keys, blue threadlocker | assembly |

Optional upgrades: NEMA 23 motors with 24 V holding brakes on shoulder and elbow (the arm drops on power loss), a Teensy 4.1 instead of the Mega if you need all joints at full speed together.
