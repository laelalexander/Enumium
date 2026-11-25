# CBP-8: open items: none (closed 2026-11-25)

KiCad DRC on `cbp8.kicad_pcb`: **0 violations, 0 unconnected, 0 footprint errors** (`cbp8-drc.rpt`). The board is
cleared for release to RushPCB with `cbp8-rushpcb.zip`.

The last items were closed by `kgen/fix_cbp8.py`, a scripted touch-up that runs after `build.py cbp8 finish`:

| Item | Fix |
|---|---|
| S2_12V / S8_12V routed 1.0 mm wide next to BST, FB and a locked PCIe lane (clearance) | those four segments narrowed to 0.40-0.69 mm |
| RS485_DE ran through the slot-5 S5_12V F pour and split it | re-routed around the pour (2 vias) |
| Slot-5/8 shunt +12V pads (R502.1, R503.1, R802.1) and Kelvin IN+ (U502.3) cut off from the +12V B pour by +3V3 / sense routing | strip between the shunts and the pour cleared, +3V3 re-routed; IN- now goes straight into the Sk_12V_SNS pour |
| +12V B pour connected the shunt pads with thermal spokes | THT-thermal mode: SMD pads (shunts) now solid, PTH pads keep relief (also set in `design.py`) |
| U803.1 (slot-8 buck GND) boxed in by the switch-node trace, PCIe lanes underneath leave no room for a via | SW leg to L801 lifted 0.71 mm so the F GND fill reaches pin 1 |
| J905 pin 9 (GND) starved thermal | solid connection on that pad |
| Dangling stubs and two floating sense vias | removed |

Re-run order if the board is ever regenerated: `build.py cbp8 finish` -> `python3 fix_cbp8.py` -> `build.py cbp8 fab`.
