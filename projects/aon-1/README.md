# AON-1: Ambient Orbital Node 1 (3U CubeSat)

A 3U CubeSat to CubeSat Design Specification rev 14.1. It is 100 x 100 x 340.5 mm [3.94 x 3.94 x 13.41 in], about 1.6 kg current best estimate (1.93 kg with 20 % margin). It flies the EOR-1 store-and-forward flight software on UHF.

| Folder | What is in it | Regenerate |
|---|---|---|
| `design/` | design basis and budgets (mass, power, link, orbit life), electrical interface (connectors, wires, stack bus) | `python3 design/design.py` |
| `cad/` | parametric model, STEP per part, assembly STEP/GLB/STL, renders | `python3 cad/model.py` |
| `drawings/` | 15-sheet shop set in mm [in]: arrangement, section + item list, assembly steps, rails, frames, bracket, stack, boards, bought parts, power schematic, wire list, test plan | `python3 drawings/build_all.py --pdf` |
| `dxf/` | flat patterns and board/panel outlines, mm and inch | (from `cad/model.py`) |
| `bom/` | bom.csv / bom.xlsx / bom.md / order-list.md with the completeness check | `python3 bom/make_bom.py` |
| `firmware/eor1/` | EOR-1 flight software (C11): CCSDS, HMAC-SHA256 authenticated commands, store-and-forward, B-dot, safe mode, deploy ARM/FIRE | `make test` |
| `firmware/ground/` | ground script: build telecommands, decode telemetry | `python3 -m unittest test_ground` |
| `build/` | build package for the Anatomy Build wizard | `python3 build/make_build.py` |

Status: structure is ready for quote; boards E01-E07 still need KiCad layouts and RushPCB packages; every purchase line needs its supplier page and SKU confirmed; the STM32H743 flight port is written with the E03 board.
