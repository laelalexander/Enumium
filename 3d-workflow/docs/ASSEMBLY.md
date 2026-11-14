# Assembly guide: 4-DOF desktop arm, 5 lb payload, 39 in reach

**Read first**
- This is a first-revision design. The torque numbers are static estimates from vendor
  listings; the printed geometry is draft and has not been printed or loaded by us.
  Prototype and test-fit before trusting it with weight or people.
- **The arm will fall when power is cut or E-stop is pressed.** The belt/planetary stages
  are back-drivable. Lower it to its rest pose before powering down, keep hands and face out
  of the swing area, and consider motors with 24 V holding brakes on shoulder and elbow
  (search "NEMA 23 stepper motor with brake").
- Do not exceed 1.219 m (4 ft) extension; default build is 1.0 m (39.4 in).
- Full-reach rating assumes a 5 lb load held static with the arm horizontal. Move slowly.

## Build plan at a glance

| Stage | What | Where it's defined | Time |
|---|---|---|---|
| A. Order | Long-lead parts first: gearmotors, turntable, clamp hubs | `docs/PROCUREMENT.md`, `procurement.csv` | 1-3 weeks |
| B. Measure | Calipers on the arrived parts, set `HW` in `arm/hardware.py`, `python run.py build` | drawings in `design/` | 1 h |
| C. Print | `python run.py print`, then the 5 plates in `print/plates/` | `print/REPORT.md` | ~50 h printer time |
| D. Prepare | Cut and drill tubes, ream bores, fit inserts and bearings | sections 2, 4, 5 | 3 h |
| E. Assemble | Base, three pitch joints, gripper | sections 3-5 | 5 h |
| F. Wire | Bench electronics per ELE-001 | section 6, `docs/WIRING.md` | 3 h |
| G. Commission | Firmware, rehearse in the twin, home, calibrate, load test | sections 7-8, `python run.py ui` | 2 h + |

Order everything in `docs/PROCUREMENT.md`, then **measure** the arrived parts and update
`HW` in `arm/hardware.py` (gearbox flange/pilot, shaft sizes, hub bolt circle, turntable bolt
circle) and rebuild before printing.

## 0. Tools
Hex keys, calipers, drill press or hand drill (5 mm, 12 mm), hacksaw/chop saw, soldering iron or
crimp tool, multimeter, M4 heat-set insert tip, blue threadlocker, 3D printer with >=230 mm bed
(shoulder motor cheek is ~223 mm long; the print plates are laid out for a 256 mm Bambu bed).

## 1. Print
`python run.py print` orients every part, lays the 16 prints out on 5 plates, slices each plate and
checks it. Open `print/plates/plate_N.3mf` in Bambu Studio, choose PETG, apply the settings table in
`print/REPORT.md` (0.2 mm layers, 5 perimeters, 40% gyroid, supports only on plates 3 and 4), slice
and send. Cheek plates print **flat** so layers run parallel to the plate; bores print vertical
wherever possible. Print one `tube_block` first and test-fit the tube before the rest. Print the
gripper jaw pads from TPU. Ream 12 mm and 8 mm bores after printing.

## 2. Prepare tubes
Cut (see BOM.md): upper arm, forearm, riser (~150 mm), wrist stub (~120 mm). Deburr. Mark the
cross-pin holes: 5.5 mm, 20 mm from each tube end that goes into a printed block/socket, drilled
through both tube walls, matching the printed cross holes.

## 3. Yaw base
1. Drill a hole in the base board for the yaw gearbox body; bolt the gearbox to the underside of
   the board, shaft up.
2. Bolt the turntable bearing's fixed ring to the board, concentric with the gearbox shaft.
3. Fit a clamping hub on the gearbox shaft. Bolt `base_top_plate` to the hub (4 bolts) and to
   the turntable's rotating ring (8 bolts, threadlocker).
4. Insert the riser tube into the plate's socket; fit a cross pin.

## 4. Pitch joints (repeat for shoulder, elbow, wrist)
Each joint = two cheek plates + one tube block, a 12 mm shaft, two 6001 bearings, a belt stage.
1. Press a 6001 bearing into the recess of each cheek plate (outer faces).
2. Bolt the tube block between the two cheeks with four M5 bolts. The incoming tube slides into the
   block and takes a cross pin.
3. Slide the 12 mm shaft through both bearings. Fit the large HTD pulley and a shaft collar in the
   cavity (pulley key/set screw on the flat of the shaft; use a shaft with a flat or add a
   keyed hub). Fit a collar on the other side to stop axial slide.
4. Mount the gearmotor to the **motor cheek** through its slotted holes (motor body on the outside,
   output shaft toward the cavity). Fit the small pulley on its output shaft, loop the belt,
   and tension by sliding the motor along the slots (belt should deflect ~3 mm at mid-span with
   finger pressure); tighten bolts + threadlocker.
5. On the free end of the shaft (outside the plain cheek), fit the aluminium clamping hub, then bolt
   a `tube_socket` to the hub flange. Insert the next tube and fit the cross pin.
Order: shoulder joint on top of the riser, upper arm into shoulder `tube_socket`, elbow joint at
the far end of upper arm, forearm, wrist joint, wrist stub, then gripper adapter.

## 5. Gripper
1. Press LM8UU bearings into the jaw's two bores. Slide 8 mm rods through the body and jaw, fixed
   jaw end first. Retain rods with hot glue or a small set screw.
2. Mount the NEMA 17 on the back face; couple the T8 lead screw (5 mm to 8 mm coupler); screw the T8
   nut onto the screw and bolt its flange to the jaw (4x M3).
3. Glue TPU pads on both jaw faces. Bolt the body to `gripper_adapter` with M4 screws into
   heat-set inserts, and slide the adapter onto the wrist stub with a cross pin.
Required holding force at 5 lb with pad friction 0.5 is about 45 N with a 2x margin; the lead screw
provides >100 N at 0.45 N·m motor torque, and it self-locks when unpowered.

## 6. Electronics
- 24 V PSU -> fuse (20 A) -> E-stop (NC) -> VCC of the five drivers.
- Arduino Mega: STEP pins 2-6, DIR pins 7-11, ENABLE pin 12 (to ENA- on all drivers, common
  PUL+/DIR+/ENA+ to the Mega 5 V), limit switches to pins 22-26 and GND (normally closed).
  Channels: 0 yaw, 1 shoulder, 2 elbow, 3 wrist, 4 gripper.
- Set driver current to each motor's rating (2.8 A motors, about 3.0 A peak setting; NEMA 17 about 1.5 A) and
  microstep to 800 pulses/rev (DIP switches).
- Common grounds only through the Mega USB/signal GND; keep motor wires twisted and away from signals.

## 7. Firmware and first run
1. Open `firmware/arm_controller/arm_controller.ino` in the Arduino IDE, install AccelStepper, upload.
   Rehearse every move first in the control surface (`python run.py ui`, simulation mode), then
   connect it to the Mega (Link tab, Chrome or Edge) with the motors unpowered to check the protocol.
2. `pip install pyserial`. In Python:
   ```python
   from arm.control import Arm, SerialDriver
   arm = Arm.from_design(SerialDriver("/dev/ttyACM0"), "out/arm/design.json")
   ```
3. **Dry run first with `SimDriver`** to check the motion script. Then power the motors with the arm
   resting on a support and no payload.
4. Test each joint alone with `driver.move(ch, small_steps)`. If a joint turns the wrong way, flip
   its DIR wiring pair or negate its sign in `control.py`.
5. Home: `arm.home()` moves each joint at low speed toward its limit switch and sets the step
   counter to zero there. Measure the real joint angle at each switch and set it in
   `Arm.HOME_DEG` (and in the control surface's Motors tab, "Limit switch at"); adjust `LIMITS` and
   `HOME_DIR` for your build.

## 8. Load test
0 lb across the full range -> 1 lb -> 2.5 lb -> 5 lb, first with the arm at 50% extension, then increasing.
Stop if you see: belt skipping (retension or lower speed), cracking/creep in printed parts
(reprint thicker or in nylon-CF/aluminium), tube twisting in a socket (add a second cross pin),
motors stalling (lower speed/accel in `max_dps`, or reduce reach).

## Known limits
- Open-loop steppers: lost steps are not detected. Use closed-loop steppers or encoders for precision.
- Backlash of the planetary stage is ~0.3 deg at the motor side before the belt, so expect a few mm of
  slop at the gripper at full reach.
- Printed hub plates carry an eccentric load. Inspect them under load; swap in machined aluminium if they flex.
- Arduino Mega step rate (~4 kHz combined) limits joint speed; defaults in `Arm.max_dps` are conservative.
