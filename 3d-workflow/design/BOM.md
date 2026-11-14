# Bill of materials (generated)

Payload 5.0 lb, extension 39.4 in. **Verify every listing's dimensions and shaft sizes before buying; ASINs deliberately omitted because listings change.**

## Drives

| Joint | Amazon search | Required N·m | Rated N·m | Margin |
|---|---|---|---|---|
| shoulder | NEMA 23 20:1 planetary gearbox + 5:1 HTD 5M belt/pulley stage | 45.3 | 125.0 | 2.76x |
| elbow | NEMA 23 20:1 planetary gearbox + 3:1 HTD 5M belt/pulley stage | 19.57 | 75.0 | 3.83x |
| wrist | NEMA 23 stepper motor 20:1 planetary gearbox 2.8A | 2.98 | 25.0 | 8.39x |
| yaw | NEMA 23 stepper motor 20:1 planetary gearbox 2.8A | (inertia only) | 25.0 | n/a |

## Belt stages (HTD 5M, 15 mm)

| Joint | Ratio | Small / large teeth | Center dist (mm) | Belt teeth (approx) |
|---|---|---|---|---|
| shoulder | 5:1 | 16 / 80 | 107.9 | 96T |
| elbow | 3:1 | 16 / 48 | 78.6 | 65T |
| wrist | 1:1 | 16 / 16 | 49.3 | 36T |

## Tube lengths (cut)

- upper arm: 320 mm, forearm: 320 mm, riser: ~150 mm, wrist stub: ~120 mm

## Other purchased parts

| Item | Qty | Amazon search / check | Used for |
|---|---|---|---|
| 1.5 in OD aluminium round tube, 0.065 in wall, 6061 (36 in or 48 in length) | 4 | 1.5 inch OD aluminum tube 0.065 wall 48 inch | 2 links + riser + wrist stub (cut to length) |
| Heavy-duty turntable bearing 12 in (rated >= 500 lb) | 1 | 12 inch heavy duty lazy susan turntable bearing 1000 lb | yaw bearing; check bolt circle then set HW.turntable_pcd |
| 12 mm hardened/stainless shaft rod, 150 mm | 3 | 12mm linear shaft rod 150mm (6 mm too small) | shoulder/elbow/wrist joint shafts |
| 6001-2RS ball bearing 12x28x8 | 8 | 6001-2RS bearing 12x28x8 | 2 per pitch joint + spares |
| 12 mm shaft clamping hub with 4-hole flange (aluminium) | 4 | 12mm clamping shaft hub flange coupling aluminum (yaw one: bore = gearbox output) | 3 lock distal links to joint shafts, 1 locks base_top_plate to the yaw gearbox; check bolt circle -> HW.hub_pcd |
| Shaft collars 12 mm | 6 | 12mm shaft collar clamp type | axial retention |
| HTD 5M timing pulley, 15 mm belt, 16T (bore = gearbox output shaft) | 3 | HTD 5M 16 tooth pulley 15mm belt bore 14mm (check bore) | motor pulleys, one per pitch joint |
| HTD 5M pulley, 12 mm bore, large (see BOM table for teeth) | 3 | HTD 5M pulley 12mm bore 15mm belt | joint-shaft pulleys: teeth listed below |
| HTD 5M belt, 15 mm wide (lengths listed below) | 3 | HTD 5M timing belt 15mm closed loop | one per pitch joint, pick closest stock length |
| Stepper driver DM542 (or DM556), 24-48 V | 5 | DM542 stepper driver 4.2A | 4 joints + gripper (gripper may use TB6600) |
| NEMA 17 stepper w/ T8 lead screw 150 mm + nut + 5->8 mm coupler | 1 | NEMA 17 stepper motor T8 lead screw 150mm with nut | gripper drive |
| 8 mm linear rod 150 mm + LM8UU bearings | 2 | 8mm linear rod 150mm LM8UU | gripper slides: 2 rods, 2 bearings |
| 24 V 15 A (360 W) power supply | 1 | 24V 15A power supply 360W | motors |
| Arduino Mega 2560 R3 | 1 | Arduino Mega 2560 R3 | controller (firmware/arm_controller) |
| E-stop mushroom button, latching, NC | 1 | emergency stop switch latching NC 22mm | cuts 24 V to all drivers |
| Mechanical limit switches (NC) | 5 | micro limit switch lever 5 pack NC | homing, one per joint |
| Fuse holder + 20 A fuse, 14 AWG wire, ferrules | 1 | inline fuse holder 20A 14awg | power distribution |
| M5 screws 16/25/40/60 mm + nuts + washers, M3, M4 heat-set inserts | 1 | M5 socket head screw assortment; M4 heat set inserts | assembly |
| PETG or nylon-CF filament, 2 kg; TPU for gripper pads | 1 | PETG 1.75mm 1kg x2; TPU 95A | printed parts |
| Plywood or MDF board 18 x 18 in, 3/4 in | 1 | 3/4 inch plywood 18x18 | base; drill hole for yaw gearbox |

## Printed parts

| Part | Qty | Note |
|---|---|---|
| shoulder_cheek_motor | 1 | Motor-side cheek plate |
| shoulder_cheek_plain | 1 | Plain cheek plate |
| shoulder_tube_block | 1 | Spacer block that clamps the incoming tube |
| elbow_cheek_motor | 1 | Motor-side cheek plate |
| elbow_cheek_plain | 1 | Plain cheek plate |
| elbow_tube_block | 1 | Spacer block that clamps the incoming tube |
| wrist_cheek_motor | 1 | Motor-side cheek plate |
| wrist_cheek_plain | 1 | Plain cheek plate |
| wrist_tube_block | 1 | Spacer block that clamps the incoming tube |
| tube_socket | 3 | Distal link end: hub flange + tube socket (shoulder, elbow, wrist) |
| base_top_plate | 1 | Rotating plate: yaw hub + turntable + riser socket |
| gripper_body | 1 | NEMA17 lead-screw gripper body + fixed jaw |
| gripper_adapter | 1 | Tube-stub socket + plate bolting to gripper body (M4 heat-set inserts) |
| gripper_jaw | 1 | Sliding jaw on 2x8 mm rods |
