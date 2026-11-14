# Anatomy skill

A Claude Code skill that dissects a product (web app, repo, CLI, API, or hardware) into a clean-room reengineering blueprint, then proves it with a prototype: a running demo, an interactive viewer, or a full hardware build package (mechanics, KiCad PCB, firmware or controls, build instructions).

The first target is a 7.5 inch e-ink desk display (calendar and weather over wifi, battery powered).

## Layout

| Path | What it is |
|------|------------|
| `SKILL.md` | The skill itself: principles and the six-step workflow |
| `references/` | Detail the skill loads on demand (recon playbook, blueprint template, stack signals, prototype phase, hardware engineering, KiCad PCB) |
| `evals/` | Five test prompts with graders: e-ink display, HVAC system, fd, jq, Hacker News |
| `app/Anatomy.ps1` | The Anatomy desktop launcher (project list, new project, opens Claude Code) |
| `install-anatomy.ps1` | Windows installer for the skill, the launcher icon, and KiCad |
| `HANDOFF.md` | Notes and lessons from the first cloud test run |
| `test-results-summary.md` | Benchmark from that run (self-graded, so treat the delta as optimistic) |

The installer copies `SKILL.md` and `references/` into Claude's skills folder and `app/Anatomy.ps1` into `%LOCALAPPDATA%\Anatomy`. The rest stays in the repo.

## Install on Windows

From a PowerShell prompt in this folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-anatomy.ps1
```

`-ExecutionPolicy Bypass` is needed because Windows blocks unsigned scripts by default. The script:

1. Copies `SKILL.md` and `references\` to `%USERPROFILE%\.claude\skills\anatomy`, replacing any earlier install.
2. Looks for KiCad (`kicad-cli` on PATH, or `C:\Program Files\KiCad\<version>\bin`). If it is missing it installs KiCad with `winget`. It then prints the path to KiCad's bundled `python.exe` (which has `pcbnew`) and warns if Java is missing (Freerouting needs it).
3. Installs the Anatomy launcher to `%LOCALAPPDATA%\Anatomy` and puts an **Anatomy** icon on the desktop and in the Start menu.

Options:

- `-NoShortcut` skips the launcher and icons. `-ProjectsRoot D:\Somewhere` keeps projects somewhere other than `C:\Anatomy`.
- `-SkipKiCad` installs only the skill.
- `-Package` also builds `anatomy.skill` (a zip with an `anatomy\` root) next to the script. If you only have an `anatomy.skill` file and no `SKILL.md`, put it next to the script and it installs from that instead. `anatomy.skill` is git-ignored; rebuild it from source rather than committing it.

## Using the Anatomy app

Double-click the **Anatomy** icon. The window lists your projects in `C:\Anatomy`.

- **New project**: give it a name, a type and a short brief, then click **Create and start**. It makes `C:\Anatomy\<name>\` with a `CLAUDE.md` (which points Claude at the skill) and an `inputs\` folder, then opens Claude Code there and starts the anatomy run on your brief.
- **Open in Claude** (or double-click a project) reopens a project where you left off. **Show folder** opens it in Explorer.
- Put datasheets and reference files in the project's `inputs\` folder before or during a run.

The app needs Claude Code (`claude`) installed. It opens in Windows Terminal if you have it, otherwise in a PowerShell window.

## KiCad PCB step: experimental

`references/kicad-pcb.md` describes how to produce native KiCad schematic and board files, check them with `kicad-cli` ERC and DRC, and export Gerbers. **It is written but untested.** The only test run was in a cloud sandbox without KiCad, so no routed board or Gerbers came out of it. On a local PC, expect to debug:

- generating valid `.kicad_sch` and `.kicad_pcb` files,
- importing `pcbnew` (use KiCad's bundled `python.exe`, not a system Python),
- Freerouting, which needs Java.

The skill tells the user this up front and falls back to a netlist and layout spec labeled "specified only" if KiCad cannot run. Until a board has passed ERC and DRC on a real machine, treat any PCB output as unverified.

Also give Claude the datasheet PDFs for the panel and key parts at the start. In the cloud run, datasheet fetches were blocked and many pinouts came from memory.

## Suggested first local prompt

> Run the anatomy skill on a 7.5 inch e-ink desk display (calendar + weather over wifi, battery powered). Produce the full build package including real KiCad schematic and PCB files that pass kicad-cli ERC and DRC, Gerbers, enclosure STEP/STL, firmware, and build instructions. Stop and tell me if KiCad cannot run. I will provide the panel datasheet at `<path>`.
