"""xTool lasers (X1, M2, F2, MetalFab).

Today this is a hand-off through xTool Studio: the agent saves the laid-out SVG sheet
(red = cut, blue = engrave) and opens it in xTool Studio on the shop PC, with the power,
speed and passes in the run's message. The operator frames it and presses start on the
machine, which xTool requires anyway for safety.

Status: the agent checks the machine answers on its control port (28900) on the network.

Sending jobs straight to the machine over its WebSocket API (mode "direct") needs the
file-upload framing captured from xTool Studio first; until then "direct" is refused.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import Driver, Handoff
from .bambu import reachable
from .folder import open_file, settings_text

CONTROL_PORT = 28900


class XToolDriver(Driver):
    name = "xtool"

    def status(self) -> dict:
        host = self.cfg.get("host")
        if not host:
            return {"state": "manual", "detail": "No IP address set; hand-off through xTool Studio"}
        if reachable(host, CONTROL_PORT):
            return {"state": "idle", "detail": f"On the network at {host}"}
        return {"state": "offline", "detail": f"Not answering at {host}:{CONTROL_PORT} (off, asleep, or new IP)"}

    def run(self, run: dict, path: Path, ctx) -> str:
        if self.cfg.get("mode", "studio") == "direct":
            raise RuntimeError("Direct sending to xTool machines is not ready yet; set mode to \"studio\"")
        folder = Path(self.cfg.get("folder") or self.workdir / "xtool")
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / path.name
        shutil.copyfile(path, target)
        cfg = dict(self.cfg)
        cfg.setdefault("open", True)  # open with the app that handles .svg, or a command list
        open_file(cfg, target)
        extra = settings_text(run)
        lay = (run.get("settings") or {}).get("layout") or {}
        sheets = f" Sheet holds {lay['per_sheet']} part(s)." if lay else ""
        raise Handoff(f"Opened {target.name} for xTool Studio" + (f": {extra}." if extra else ".") + sheets
                      + " Red lines cut, blue lines engrave. Frame, start on the machine, then mark done in Pyslate.")
