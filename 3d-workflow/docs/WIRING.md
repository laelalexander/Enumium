# Wiring (schematic `design/schematics/ELE-001_wiring.svg`, numbered wire list `ELE-002_wire_list.svg` and `fab/WIRELIST.csv`)

| Channel | Joint | STEP | DIR | Limit (NC to GND) | Driver | Motor |
|---|---|---|---|---|---|---|
| 0 | Yaw | D2 | D7 | D22 | DM542 | NEMA23 20:1 |
| 1 | Shoulder | D3 | D8 | D23 | DM542 | NEMA23 20:1 + 5:1 belt |
| 2 | Elbow | D4 | D9 | D24 | DM542 | NEMA23 20:1 + 3:1 belt |
| 3 | Wrist | D5 | D10 | D25 | DM542 | NEMA23 20:1 + 1:1 belt |
| 4 | Gripper | D6 | D11 | D26 | TB6600/DM542 | NEMA17 + T8 screw |

- ENABLE: Mega D12 -> ENA- on every driver (HIGH = disabled). Mega 5 V -> PUL+, DIR+, ENA+ (common anode).
- Power: PSU 24 V -> 20 A fuse -> NC E-stop -> VCC of all drivers; PSU V- -> GND bus -> driver GND.
- Motors: twist each phase pair (A+/A-, B+/B-); use shielded cable for runs over 30 cm. Confirm phase pairs with a
  multimeter (shorted pair = more resistance when turned by hand) before connecting.
- Drivers: DIP set current for the motor (NEMA23 about 3.0 A peak, NEMA17 about 1.5 A) and 800 pulses/rev
  (matches `MICROSTEP = 4` in `arm/control.py`). Change both together.
- Limit switches: COM to GND, NC to the pin shown; the firmware treats LOW as not-yet-triggered.
- Estimated peak draw: 4 x 2.8 A + 1.5 A at 24 V about 150 W; 360 W supply leaves margin for acceleration.
