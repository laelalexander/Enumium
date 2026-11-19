# PCBA order package (turnkey, RushPCB-ready)

Any custom board ends in one zip that a turnkey PCBA house (RushPCB, Bittele, PCBWay, JLCPCB and similar) can quote and build from, with nothing to ask back. Gerbers alone are a bare-board order; a turnkey assembler also needs a BOM it can buy from, a placement file it can trust, drawings that show polarity, and instructions. Run this as the last PCB step, after `kicad-pcb.md` has produced a board that passes ERC/DRC, and put the zip in `build/3-fabricate/pcb/`.

What RushPCB asks for (rushpcb.com FAQ, checked 2026-11-15): Gerber RS-274X with copper, silkscreen and paste layers; an NC Excellon drill file (ASCII); a BOM in Excel format (.xls, .xlsx, .csv or tab-delimited) with reference designator, quantity, manufacturer, part number (Digi-Key numbers accepted), description and package; and a centroid/XY file with X, Y, rotation, side and reference designator. Special assembly instructions go in a PDF or text file. The package below covers all of it and adds a fab drawing, an assembly drawing and test notes.

## Run it
```
python <skill>/tools/pcba/pcba_export.py <board>.kicad_pcb          # reads pcba.json next to the board
python <skill>/tools/pcba/pcba_export.py <board>.kicad_pcb --sch <board>.kicad_sch --bom old-bom.csv --qty 5 --rev A
```
`<skill>` is this skill's folder (installed at `%USERPROFILE%\.claude\skills\anatomy`; in the repo, `skills/anatomy`). Needs KiCad 8 or newer (`kicad-cli`; found on PATH, in `KICAD_CLI`, or in the standard Windows/macOS/Linux install folders, including `%LOCALAPPDATA%\Programs\KiCad\<ver>\bin`) and Python 3 with matplotlib. Use a normal Python, not KiCad's bundled one. No other packages are needed; the .xlsx is written with the standard library. Exit code 0 = ready, 2 = not ready (blockers listed).

## pcba.json (next to the board)
```json
{
  "project": "TwinArm bimanual robot", "board_name": "rcb1", "revision": "A", "quantity": 5,
  "schematic": "rcb1.kicad_sch", "bom": "../fab/rcb1-bom.csv", "out": "../fab/pcba",
  "fab": {"copper_outer_oz": 2, "finish": "ENIG", "mask_color": "Green", "silk_color": "White",
          "thickness_mm": 1.6, "material": "FR-4, Tg 150", "impedance_control": "None"},
  "assembly": {"notes": ["anything special the assembler must know"]},
  "rails": {"+3V3": "3.20-3.40 V"},
  "power_up": "how to apply first power, voltage and current limit",
  "tests": [{"step": "what to do", "expect": "pass criterion with numbers"}],
  "programming": "how firmware gets on the board"
}
```
Copper weight comes from the power budget, never from a default. Put MPN, Manufacturer and supplier numbers (Digi-Key_PN, Mouser, LCSC) in the schematic symbol fields where possible. An older BOM CSV can be merged with `--bom`; its column names are matched loosely.

## What it writes (`<board>-PCBA-rev<rev>.zip`)
| Folder | Files |
|---|---|
| `01-fabrication/` | `<board>-gerbers.zip` (RS-274X without X2 extensions, Protel names, mask subtracted from silk, every copper layer plus mask, paste, silk and Edge.Cuts; Excellon drill in mm with PTH and NPTH separate), drill map PDFs, `FAB-DRAWING.pdf` (outline with overall dims, datum, drill table, mounting/tooling hole table, stackup and fab notes, all in mm [in]), `FAB-NOTES.md` |
| `02-assembly/` | `<board>-BOM.xlsx` and `.csv` (item, qty, refdes, manufacturer, MPN, Digi-Key/Mouser/LCSC PN, description, value, package, SMD/THT, side, DNP, notes), `<board>-centroid.csv` and `.xlsx` (refdes, X/Y in mm and inches, rotation, side, value, package, mount, DNP), `ASSEMBLY-DRAWING.pdf` (top and, if used, bottom seen from below; pin 1, cathode and + pads in red, body outlines, refdes, origin arrows, orientation check list), `ASSEMBLY-NOTES.md` |
| `03-test/` | `TEST-NOTES.md`: AOI, unpowered short check per power rail, power-up, test points with coordinates, functional tests, programming |
| `04-reference/` | schematic PDF, board STEP with 3D models, top/bottom renders, DRC/ERC reports (json and text), KiCad's own pos file, `kicad-cli.log` |
| root | `README.md` (READY / NOT READY with blockers and warnings), `QUOTE-SHEET.md` (values to type into the quote form, with the assembly breakdown: PTH, QFN, BGA, fine pitch, large devices, standard SMD, smallest pitch, holes and slots), `rushpcb-quote.json` (the same answers keyed by RushPCB's field names), `status.json` |

The centroid origin is the lower-left corner of the board outline seen from the top, X right, Y up. Bottom-side parts keep top-view coordinates. Positions are cross-checked against KiCad's own pos export; a difference over 0.01 mm is reported.

## Blockers (package is NOT READY)
DRC errors, unconnected items or schematic-parity issues; ERC errors; a placed part without an MPN; duplicate or unannotated reference designators; Gerber or drill export failure; kicad-cli or matplotlib missing.

## Warnings (READY, but say them to the user)
DRC/ERC warnings (each must be justified in the board README), supplier numbers marked `[verify]`, copper weight not set, parts on both sides (costs more), no functional tests, leadless or module parts that need X-ray.

## Getting the quote
When the user wants a price or wants to order, follow `pcba-quote.md`: Claude fills in RushPCB's online quote in the user's Chrome from `rushpcb-quote.json` and stops at the price table.

## Rules
- Never place an order, click a price or enter payment without the user's go-ahead in chat. Filling in a quote they pointed you to is fine (`pcba-quote.md`).
- A READY package still says "machine-generated, not reviewed by a person" in the board README until someone has reviewed the schematic and layout. Say so when you hand it over.
- Do not hand-edit the outputs. Fix the board, the schematic fields or `pcba.json`, and run it again.
- Add the zip to `build/build.json` `fabricate[]`: `{"part": "<board> PCBA", "process": "PCB fab + turnkey assembly", "files": ["build/3-fabricate/pcb/<board>-PCBA-revA.zip"], "vendor": "RushPCB (or any turnkey house)", "settings": "<from QUOTE-SHEET.md>", "qty": 5}`.
- If the product uses only off-the-shelf boards (Arduino, driver modules) and a wiring harness, there is no PCBA order. Say so plainly, and deliver the harness as a cut list and wire list instead (see `hardware-engineering.md`).
