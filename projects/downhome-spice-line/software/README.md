# Control and automation software

Three layers, matching ISA-95: PLCs run the machines, the HMIs show and command them, and the MES owns recipes, lots and records.

| Layer | Where | What |
|---|---|---|
| PLC | `plc/` | IEC 61131-3 Structured Text for PLC-601 (blending batch phase) and PLC-602 (pack line A PackML). Tags generated from the I/O list. |
| HMI | PanelView 5510 HMI-601 and HMI-602 | Screens listed below; built in FactoryTalk Optix/View ME from the PLC tags. |
| MES | `mes/` | Python, standard library only. Recipes, batches, weigh and dispense, QC release, pack runs, GS1 labels, NIST HB 133 checks, lot genealogy, electronic batch record, plant-floor web UI. |

## MES quick start

```
cd software/mes
python3 -m unittest discover -s tests -t .      # 9 end-to-end tests
python3 -m dhmes.server --db plant.db --port 8080
```

Then open `http://<server>:8080` on a panel PC. The server loads formulas and SKUs from `data/site.json` on first start.

### What the MES enforces

- **Batch size** never above RB-303 working volume x formula bulk density, and never under 30 % fill.
- **Weigh and dispense:** every scan is checked for the right ingredient, a released and in-date lot, and enough stock. Majors must be within +/-0.5 % and minors within +/-0.2 %. Minors under 2 % are routed to the PM-210 premix (the site rule).
- **PLC download** (`/api/batch/<id>/plc`) is only possible once every line of the pick list is weighed.
- **QC release:** the salt tracer CV must be 5 % or less over at least 10 samples, and micro must pass. Only released bags can be scanned at BU-401 or BU-502, and the bag must match the SKU's formula.
- **Allergens:** wheat formulas only pack at station B (room B). The weekly sequence puts wheat last, before the wet clean.
- **First-off label check:** the label UPC and the coder's lot code must match before the line PLC gets a valid job.
- **Net contents:** CW-409 rejects every unit under declared (the site rule). `hb133_check` verifies each lot's average and MAV afterwards.
- **Traceability:**
  - Trace back from a finished lot to the supplier lots.
  - Trace forward from a supplier lot to the batches, runs, pallets (SSCC) and customers.
  - Every action is in an append-only audit table with the operator's badge.

### Interfaces

| To | How | Data |
|---|---|---|
| PLC-601 / PLC-602 | OPC UA or CIP (pycomm3) | `MES_Download`, `MES_Job`, the bag and label confirmations, counts and the first-out stop reason |
| Scales WS-201/202/203 | Mettler SICS over TCP (`S` command) | stable weight |
| Zebra ZT411 / CTM 360a ZE511 | raw TCP 9100 | ZPL from `gs1.py`: bag tag, GS1-128 case label, SSCC pallet label |
| Videojet 6330 / 8610 | Videojet text protocol over TCP | lot and best-by lines |
| CW-409 | OPC UA | gross weights per unit |

The GS1 company prefix in `gs1.py` is a placeholder (`0000000`) until Down Home Creole gives theirs.

## HMI screens (HMI-601 blending, HMI-602 line A)

1. **Overview:** machine states, PackML state, stack-light mirror, the active batch or job, and the lot code.
2. **Batch:** step, kg in blender vs target, mix time left, salt charged, metal reject count.
3. **Alarms:** first-out reason, alarm history, and the acknowledge button.
4. **Line A:** good, weight rejects and vision rejects, speed setpoint (read-only, from the MES job), and starve/block.
5. **Changeover:** a checklist per container, taken from the ASM-002 change-parts table. Every step must be signed before reset.
6. **Sanitation:** the dry clean and wet clean checklists from the SSOP, signed by an operator and verified with ATP.
7. **Maintenance:** motor hours, blender amps trend, and dust collector dP trend.

## Phase 1 prototype (bins)

Start the MES with `--blender P1-301` for the Phase 1 plant. It then knows the 6 cu ft blender's limits and the bin ring:
`/api/bin/assign`, `/api/bin/refill` (scan the bag lot; the wrong ingredient, a quarantined or expired lot, or an overfill is refused), `/api/bin/empty`,
`GET /api/batch/<id>/doselist` for the dosing PLC (`plc/DosingStation.st`) and `/api/dose` for each finished dose (±1 %, 20 g minimum).
A dose writes a dispense record for every lot in the bin since it last ran empty, so trace back and forward work through the bins.
