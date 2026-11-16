# Anatomy skill: handoff for a local restart

## What it is
A Claude skill that dissects a product (web app, repo, CLI, API, hardware) into a clean-room blueprint, then builds a prototype: running demo, interactive viewer, or a full hardware package (mechanics, KiCad PCB, firmware/controls, build instructions).

## Files
- `anatomy.skill` and `install-anatomy.ps1`: install on Windows (PowerShell: `.\install-anatomy.ps1`). It unpacks to `%USERPROFILE%\.claude\skills\anatomy` and installs KiCad with winget if missing.
- `anatomy-skill-source/`: editable source (SKILL.md, references/, evals/ with 5 test prompts).
- `test-results-summary.md`: benchmark from the cloud test run.

## Lessons from the cloud test run
1. Strongest value: verifying the rebuild against the real tool (fd 20/20, jq 176/176 diffs) and labeling every deliverable verified / calculated / specified only.
2. Weakest point: PCB. No routed board or Gerbers were produced because KiCad was not installed in the cloud sandbox. The KiCad step (`references/kicad-pcb.md`) is written but UNTESTED. Expect to debug: .kicad_sch/.kicad_pcb generation, pcbnew module (use KiCad's bundled python.exe), Freerouting needs Java.
3. Pinouts and many part numbers were recalled from memory (datasheet fetches were blocked). Provide the panel and key-part datasheet PDFs to Claude up front.
4. The grading in the cloud run was self-graded and overstated the gap (100% vs 60%).
5. Sites can be blocked (Hacker News returned 403 in the cloud); locally this should not matter.

## Suggested first local prompt
Run the anatomy skill on a 7.5 inch e-ink desk display (calendar + weather over wifi, battery powered). Produce the full build package including real KiCad schematic and PCB files that pass kicad-cli ERC and DRC, Gerbers, enclosure STEP/STL, firmware, and build instructions. Stop and tell me if KiCad cannot run. I will provide the panel datasheet at <path>.
