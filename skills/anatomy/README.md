# Anatomy skill

A Claude Code skill that dissects a product (web app, repo, CLI, API, or hardware) into a clean-room reengineering blueprint, then proves it with a prototype: a running demo, an interactive viewer, or a full hardware build package (mechanics, KiCad PCB, firmware or controls, build instructions).

The first target is a 7.5 inch e-ink desk display (calendar and weather over wifi, battery powered).

## Layout

| Path | What it is |
|------|------------|
| `SKILL.md` | The skill itself: principles and the six-step workflow |
| `references/` | Detail the skill loads on demand: recon playbook, blueprint template, stack signals, prototype phase, hardware engineering, KiCad PCB, parts and BOM (buy or build), drawings, 3D print to G-code, firmware/software phase |
| `evals/` | Five test prompts with graders: e-ink display, HVAC system, fd, jq, Hacker News |
| `app/` | The Anatomy desktop app: `server.js` (local server, runs Claude Code headless), `public/index.html` (the UI), `Start-Anatomy.ps1` and `Anatomy.vbs` (launch with no console) |
| `tools/` | `pcba/pcba_export.py` (turnkey PCBA order zip) and `supply/supply.js` (quantity audit, stock checks, alternates, source switches and engineering changes) |
| `install-anatomy.ps1` | Windows installer for the skill, the app and its icon, Node.js, and KiCad |
| `HANDOFF.md` | Notes and lessons from the first cloud test run |
| `test-results-summary.md` | Benchmark from that run (self-graded, so treat the delta as optimistic) |

The installer copies `SKILL.md` and `references/` into Claude's skills folder and the app into `%LOCALAPPDATA%\Anatomy`. The rest stays in the repo.

## Install on Windows

From a PowerShell prompt in this folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-anatomy.ps1
```

`-ExecutionPolicy Bypass` is needed because Windows blocks unsigned scripts by default. The script:

1. Copies `SKILL.md` and `references\` to `%USERPROFILE%\.claude\skills\anatomy`, replacing any earlier install.
2. Looks for KiCad (`kicad-cli` on PATH, or `C:\Program Files\KiCad\<version>\bin`). If it is missing it installs KiCad with `winget`. It then prints the path to KiCad's bundled `python.exe` (which has `pcbnew`) and warns if Java is missing (Freerouting needs it).
3. Installs Node.js if it is missing, installs the Anatomy app to `%LOCALAPPDATA%\Anatomy`, and puts an **Anatomy** icon on the desktop and in the Start menu.

Options:

- `-NoShortcut` skips the app and icons. `-ProjectsRoot D:\Somewhere` keeps projects somewhere other than `C:\Anatomy`.
- `-SkipKiCad` installs only the skill.
- `-Package` also builds `anatomy.skill` (a zip with an `anatomy\` root) next to the script. If you only have an `anatomy.skill` file and no `SKILL.md`, put it next to the script and it installs from that instead. `anatomy.skill` is git-ignored; rebuild it from source rather than committing it.

## Hardware standards

Every hardware package has to meet these before it's handed over:

- **Every part is BUY or BUILD.** A BUY part has a manufacturer, an MPN or a standard designation (e.g. `ISO 4762 M3x8 A2`), the spec relied on, and a supplier link. A BUILD part has its design files in the package. A script checks the BOM against the drawings, the CAD and the assembly steps. See `references/parts-and-bom.md`.
- **Production-quality drawings.** Part drawings have title blocks, full dimensions and tolerances, and section views. Assembly drawings are exploded with balloons that match the BOM. Everything is collected in one drawing set, and Claude checks each page. FreeCAD TechDraw is preferred. See `references/drawings.md`.
- **3D printed parts end in verified G-code.** Parts are designed for printing, the meshes are checked, and each part is sliced headless (PrusaSlicer CLI) for the printer in Settings. The G-code is checked by script and comes with previews and a print plan. See `references/3d-print-gcode.md`.
- **Every purchase line stays orderable, and every change is tracked.** Each order quantity is traced to the design count (for example 17S x 6P = 102, plus 4 spares) and checked by the quantity audit. Each line records the design requirements a substitute must meet and vetted alternates with live stock. A source switch or redesign is carried through the BOM, carts, CAD, drawings, G-code, firmware, PCBA package, guide and 3D twin as a logged change with a revision. See `references/supply-and-change.md`.
- **Firmware, BIOS and software are a full phase.** For each layer: requirements, architecture, buildable source, a real build, tests, and flashing and update instructions. See `references/software-phase.md`.

## Using the Anatomy app

Double-click the **Anatomy** icon. It opens in its own window, with no terminal.

1. Type what you want dissected and rebuilt in the prompt box (or pick an example). Attach datasheets, photos or specs with **Attach files**, or drag them in. Pick the model: Fable (default, the most capable, uses your plan's limits fastest), Opus or Sonnet. Use **Settings** to enter your 3D printer, materials, suppliers and tools. Claude reads them at the start of every project (stored in `C:\\Anatomy\\anatomy-settings.md`).
2. Click **Start anatomy**. The window switches to the live view:
   - **Progress** (left) walks through the six steps of the skill: Scope, Gather evidence, Analyze, Blueprint, Prototype, Verify. Claude's own plan appears under it.
   - **Activity** (center) shows what Claude is doing in plain sentences: files it reads and writes, commands it runs (click a row for the output), and a summary card at the end.
   - **Files produced** (right) updates as files are written. Click one to preview it (Markdown, images, PDFs, code). CAD, KiCad and Gerber files open in their own programs via **Show in folder**.
3. When a run finishes, the project opens on **Results**: Overview, **Build**, Try it (run the project's software), 3D model with a part inspector, Drawings, Renders, Parts (BOM), 3D printing (G-code toolpath preview), Electronics, Software, Assembly and Documents.
4. **Build** turns the design into an actual build. If the project has no build package yet, click **Prepare build package**: Claude produces `build/build.json` with the purchase list and supplier carts, the print list with G-code, fabrication and cut files, illustrated assembly steps, and firmware and test steps (`references/build-package.md`). The wizard then walks you through Order parts, Print parts, Fabricate, Assemble (one illustrated step at a time) and Firmware & test, and remembers what you've checked off. On **Order parts**, each line shows its live stock (**Check stock now**) and how its quantity compares with the design. **alternates** lists the other sources, each marked Drop-in or Needs a design change against the line's requirements. **sold out or changed?** records what a seller showed you and points to a drop-in replacement, or Claude can **Find a replacement**. **Add a source I found** and **Vet it** check a part you found yourself. **Use this source** switches a drop-in, and **Engineer this change** or **Engineer a cheaper or better version** runs a tracked engineering change across the whole package. The change log shows the revision history. Nothing is ever ordered for you.
5. Use the box at the bottom of Live to follow up ("go deeper on the PCB"). It continues the same session.

Projects live in `C:\Anatomy\<name>\` and show on the start screen.

How it works: `server.js` runs on `127.0.0.1:4377` (this PC only) and starts `claude -p --output-format stream-json` in the project folder, streaming events to the window. Claude runs with file edits and commands allowed in that folder (`--permission-mode acceptEdits` plus an allowed-tools list), because nobody is at a terminal to approve each step. The app needs Claude Code installed and signed in. If the sign-in has expired, the window shows a **Sign in to Claude** button.

## KiCad PCB step: experimental

`references/kicad-pcb.md` describes how to produce native KiCad schematic and board files, check them with `kicad-cli` ERC and DRC, and export Gerbers. **It is written but untested.** The only test run was in a cloud sandbox without KiCad, so no routed board or Gerbers came out of it. On a local PC, expect to debug:

- generating valid `.kicad_sch` and `.kicad_pcb` files,
- importing `pcbnew` (use KiCad's bundled `python.exe`, not a system Python),
- Freerouting, which needs Java.

The skill tells the user this up front and falls back to a netlist and layout spec labeled "specified only" if KiCad cannot run. Until a board has passed ERC and DRC on a real machine, treat any PCB output as unverified.

Also give Claude the datasheet PDFs for the panel and key parts at the start. In the cloud run, datasheet fetches were blocked and many pinouts came from memory.

## Suggested first local prompt

> Run the anatomy skill on a 7.5 inch e-ink desk display (calendar + weather over wifi, battery powered). Produce the full build package including real KiCad schematic and PCB files that pass kicad-cli ERC and DRC, Gerbers, enclosure STEP/STL, firmware, and build instructions. Stop and tell me if KiCad cannot run. I will provide the panel datasheet at `<path>`.
