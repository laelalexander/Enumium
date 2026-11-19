# Real PCB files with KiCad

> **Experimental, untested.** This step has not yet completed end to end: the only test run was in a cloud sandbox without KiCad, so no routed board, ERC/DRC report or Gerbers were produced. Tell the user up front that the PCB step is experimental, expect to debug `.kicad_sch`/`.kicad_pcb` generation, the `pcbnew` import (use KiCad's bundled `python.exe`, not a system Python) and Freerouting (needs Java), and stop and report if KiCad cannot run rather than presenting an unchecked board.

A netlist and a layout spec are not a PCB design. When the product has a board, produce native KiCad files (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`), run KiCad's own checks, and export fabrication files. Do this on a machine that can actually run KiCad, normally the user's local PC. If KiCad cannot be installed or run (for example a restricted cloud sandbox), say so up front, fall back to netlist + placement spec, and label the PCB "specified only". Never present an unchecked board as done.

## 1. Find or install KiCad (KiCad 8 or newer)
Check first, install only if missing, and tell the user what you are installing.
- Windows: `where kicad-cli` or look in `C:\Program Files\KiCad\<ver>\bin\`. Install: `winget install --id KiCad.KiCad -e`. KiCad's bundled Python is `C:\Program Files\KiCad\<ver>\bin\python.exe` and has the `pcbnew` module.
- macOS: `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`; install with `brew install --cask kicad`. Bundled Python is under `.../Frameworks/Python.framework`.
- Linux: `kicad-cli` on PATH; install with `sudo apt install kicad` (or the KiCad PPA/Flatpak for a current version).
Record the version in the evidence log. Optional: Java for Freerouting (autorouter), and `pip install skidl kiutils` if you prefer those for generation.

## 2. Generate from one source of truth
Keep a single table (parts, footprints, nets, pin functions, placement) that drives the BOM, firmware pin header, schematic, and board. Never hand-edit these separately, because they drift.
- **Schematic**: generate `.kicad_sch` (s-expression text) with real library symbols from KiCad's installed libraries, proper pin-to-net connections, power flags, and net labels; or build with SKiDL and export. Add a title block, sheet per subsystem for large designs, and ERC-clean power/reset/programming nets.
- **Footprints**: use KiCad's standard libraries where a footprint exists. For parts without one (many modules, panel FPC connectors), draw the footprint from the manufacturer's recommended land pattern in the datasheet and cite it. Do not guess pad geometry.
- **Board**: create `.kicad_pcb` with the `pcbnew` Python API (headless): outline on Edge.Cuts matching the mechanical model, mounting holes, footprints placed per the placement plan, nets assigned, net classes (power width, signal width), copper pours (ground plane), keep-outs (antenna), silkscreen reference and polarity marks, fab layers.
- **Routing**: route with Freerouting (export Specctra DSN from `pcbnew`, route, import SES) or place tracks via the API for simple boards. Then clean up: check power trace widths against current, keep decoupling loops short, solid ground return, no acute angles near high-speed signals. Say which method was used.

## 3. Check with KiCad's own tools (these results, not your opinion, decide "done")
```
kicad-cli sch erc  --output erc.rpt  design.kicad_sch
kicad-cli pcb drc  --output drc.rpt  design.kicad_pcb
```
Fix every error; list any waived warning with the reason. Also run a netlist comparison (schematic vs board: no missing or extra nets/footprints, via the DRC "parity" check or `pcbnew` netlist diff).

## 4. Export fabrication and review outputs
```
kicad-cli pcb export gerbers --output gerbers/ design.kicad_pcb
kicad-cli pcb export drill   --output gerbers/ design.kicad_pcb
kicad-cli pcb export pos     --output centroid.csv design.kicad_pcb
kicad-cli sch export pdf     --output schematic.pdf design.kicad_sch
kicad-cli pcb export pdf     --layers F.Cu,B.Cu,F.SilkS,Edge.Cuts --output board.pdf design.kicad_pcb
kicad-cli pcb render         --output board-top.png design.kicad_pcb
kicad-cli pcb export step    --output board.step design.kicad_pcb
```
The board STEP goes into the mechanical assembly to check enclosure fit. View the rendered images yourself before presenting. Zip the Gerbers and drill files with fab notes (layers, thickness, copper weight, finish, min trace/space) ready to upload to a fab.

Then build the turnkey order package with `tools/pcba/pcba_export.py` (see `pcba-export.md`): Gerbers + drill, an Excel BOM with MPNs, a centroid file in mm and inches from the board's lower-left corner, assembly and fab drawings in mm [in] with polarity marked, assembly and test notes, and a quote sheet, zipped and ready for RushPCB or any turnkey PCBA house.

## 5. Part verification gate
Before calling the board done, build a table of every critical part with: manufacturer part number, the datasheet URL actually fetched, and the facts relied on (pinout, absolute max voltage, footprint, required external parts). A fact from memory is marked `[assumed - verify]`, and a board that depends on unverified pinouts is "not ready to fabricate". If the datasheet cannot be fetched, ask the user for the PDF.

## 6. Report honestly
State in the README: KiCad version, ERC/DRC results with counts, how it was routed, and what remains: first articles to build, test points to probe, and anything checked only by script. A board that passes DRC can still be electrically wrong; say what was and was not reviewed by a human or simulated.

## Into the product
- Export the populated board as STEP (`kicad-cli pcb export step --subst-models`) and place it in the assembly: in `assembly.json`, the 3D build-along and the mechanism check (standoffs on its mounting holes, connectors reachable through their cutouts, no collisions).
- Decide on a custom PCBA from the design's needs, not by default: use one when off-the-shelf modules would need hand wiring that a board removes, or when space, reliability or cost call for it. Record the decision and the reason in the blueprint.
