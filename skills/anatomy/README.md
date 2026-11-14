# Anatomy skill

A Claude Code skill that dissects a product (web app, repo, CLI, API, or hardware) into a clean-room reengineering blueprint, then proves it with a prototype: a running demo, an interactive viewer, or a full hardware build package (mechanics, KiCad PCB, firmware or controls, build instructions).

The first target is a 7.5 inch e-ink desk display (calendar and weather over wifi, battery powered).

## Layout

| Path | What it is |
|------|------------|
| `SKILL.md` | The skill itself: principles and the six-step workflow |
| `references/` | Detail the skill loads on demand (recon playbook, blueprint template, stack signals, prototype phase, hardware engineering, KiCad PCB) |
| `evals/` | Five test prompts with graders: e-ink display, HVAC system, fd, jq, Hacker News |
| `install-anatomy.ps1` | Windows installer for the skill, plus KiCad |
| `HANDOFF.md` | Notes and lessons from the first cloud test run |
| `test-results-summary.md` | Benchmark from that run (self-graded, so treat the delta as optimistic) |

Only `SKILL.md` and `references/` are installed. The rest stays in the repo.

## Install on Windows

From a PowerShell prompt in this folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-anatomy.ps1
```

`-ExecutionPolicy Bypass` is needed because Windows blocks unsigned scripts by default. The script:

1. Copies `SKILL.md` and `references\` to `%USERPROFILE%\.claude\skills\anatomy`, replacing any earlier install.
2. Looks for KiCad (`kicad-cli` on PATH, or `C:\Program Files\KiCad\<version>\bin`). If it is missing it installs KiCad with `winget`. It then prints the path to KiCad's bundled `python.exe` (which has `pcbnew`) and warns if Java is missing (Freerouting needs it).

Options:

- `-SkipKiCad` installs only the skill.
- `-Package` also builds `anatomy.skill` (a zip with an `anatomy\` root) next to the script. If you only have an `anatomy.skill` file and no `SKILL.md`, put it next to the script and it installs from that instead. `anatomy.skill` is git-ignored; rebuild it from source rather than committing it.

Then start Claude Code and ask it to run anatomy on a product.

## KiCad PCB step: experimental

`references/kicad-pcb.md` describes how to produce native KiCad schematic and board files, check them with `kicad-cli` ERC and DRC, and export Gerbers. **It is written but untested.** The only test run was in a cloud sandbox without KiCad, so no routed board or Gerbers came out of it. On a local PC, expect to debug:

- generating valid `.kicad_sch` and `.kicad_pcb` files,
- importing `pcbnew` (use KiCad's bundled `python.exe`, not a system Python),
- Freerouting, which needs Java.

The skill tells the user this up front and falls back to a netlist and layout spec labeled "specified only" if KiCad cannot run. Until a board has passed ERC and DRC on a real machine, treat any PCB output as unverified.

Also give Claude the datasheet PDFs for the panel and key parts at the start. In the cloud run, datasheet fetches were blocked and many pinouts came from memory.

## Suggested first local prompt

> Run the anatomy skill on a 7.5 inch e-ink desk display (calendar + weather over wifi, battery powered). Produce the full build package including real KiCad schematic and PCB files that pass kicad-cli ERC and DRC, Gerbers, enclosure STEP/STL, firmware, and build instructions. Stop and tell me if KiCad cannot run. I will provide the panel datasheet at `<path>`.
