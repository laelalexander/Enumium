"""Run the shop's slicer from the command line to turn a model into a machine file."""

from __future__ import annotations

import subprocess
from pathlib import Path

MESH_EXTS = {".stl", ".3mf", ".obj", ".ply", ".step", ".stp"}


def needs_slicing(path: Path, ready_ext: str) -> bool:
    name = path.name.lower()
    return not name.endswith(ready_ext.lower()) and path.suffix.lower() in MESH_EXTS


def slice_model(cfg: dict | None, path: Path, copies: int, timeout: int = 1800) -> Path:
    """cfg = {"command": [..., "{input}", "{output}", "{copies}"], "output_ext": ".gcode"}."""
    if not cfg or not cfg.get("command"):
        raise RuntimeError("This machine has no slicer set up in agent.json, so models cannot be sliced")
    command = [str(c) for c in cfg["command"]]
    if copies > 1 and not any("{copies}" in c for c in command):
        raise RuntimeError(f"{copies} copies were sent, but the slicer command has no {{copies}} setting. "
                           "Send one copy per run, or add the slicer's duplicate option.")
    output = path.with_name(path.stem + cfg.get("output_ext", ".gcode"))
    args = [c.replace("{input}", str(path)).replace("{output}", str(output)).replace("{copies}", str(copies))
            for c in command]
    done = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if done.returncode != 0 or not output.exists():
        tail = (done.stderr or done.stdout or "").strip()[-600:]
        raise RuntimeError(f"Slicer failed (exit {done.returncode}): {tail}")
    return output
