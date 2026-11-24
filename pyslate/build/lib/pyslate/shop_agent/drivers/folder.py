"""Hand-off driver: put the file in a folder (a network share, a USB stick, the CAM
software's inbox) and optionally open it. Used for the Tormach machines, the plasma
table and anything without a network API."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from . import Driver, Handoff


def open_file(cfg: dict, path: Path) -> None:
    """cfg["open"]: a command list with "{file}" (%VARS% are expanded), or true to open
    the file with its default app."""
    how = cfg.get("open")
    if not how:
        return
    if isinstance(how, list):
        subprocess.Popen([os.path.expandvars(str(c)).replace("{file}", str(path)) for c in how])
    elif hasattr(os, "startfile"):
        os.startfile(str(path))  # type: ignore[attr-defined]  # Windows


def settings_text(run: dict) -> str:
    s = run.get("settings") or {}
    bits = []
    if s.get("material"):
        bits.append(str(s["material"]))
    if s.get("speed_mm_s"):
        bits.append(f"speed {s['speed_mm_s']:g} mm/s")
    if s.get("power_pct"):
        bits.append(f"power {s['power_pct']:g}%")
    if s.get("passes"):
        bits.append(f"{s['passes']:g} pass(es)")
    lay = s.get("layout")
    if lay and lay.get("sheets", 1) > 1:
        bits.append(f"{lay['per_sheet']} per sheet")
    if s.get("notes"):
        bits.append(str(s["notes"]))
    return ", ".join(bits)


class FolderDriver(Driver):
    name = "folder"

    def status(self) -> dict:
        folder = Path(self.cfg.get("folder", ""))
        if not folder.exists():
            return {"state": "error", "detail": f"Folder {folder} not found"}
        waiting = len([p for p in folder.iterdir() if p.is_file()])
        return {"state": "manual", "detail": f"{waiting} file(s) in {folder}"}

    def run(self, run: dict, path: Path, ctx) -> str:
        folder = Path(self.cfg["folder"])
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / path.name
        shutil.copyfile(path, target)
        open_file(self.cfg, target)
        extra = settings_text(run)
        raise Handoff(f"File ready at {target}" + (f" ({extra})" if extra else "")
                      + ". Run it on the machine, then mark this run done in Pyslate.")
