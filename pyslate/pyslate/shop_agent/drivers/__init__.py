"""Machine drivers. Each one takes a run and its downloaded file and makes the machine do it.

A driver's run() returns a message when the machine finished, raises Handoff when a person
finishes the job at the machine (the run stays running until they mark it done in Pyslate),
or raises Cancelled after stopping the machine because the shop cancelled.
"""

from __future__ import annotations

from pathlib import Path


class Cancelled(Exception):
    pass


class Handoff(Exception):
    """The file is on the machine or in its software; an operator takes it from here."""


class RunContext:
    def progress(self, percent: int | None = None, message: str = "", force: bool = False) -> None: ...

    def cancelled(self) -> bool:
        return False


class Driver:
    name = "base"

    def __init__(self, cfg: dict, workdir: Path):
        self.cfg = cfg
        self.workdir = workdir
        self.label = cfg.get("label") or cfg["id"]

    def status(self) -> dict:
        return {"state": "unknown", "detail": ""}

    def run(self, run: dict, path: Path, ctx: RunContext) -> str:
        raise NotImplementedError


from .bambu import BambuDriver  # noqa: E402
from .folder import FolderDriver  # noqa: E402
from .marlin import MarlinDriver  # noqa: E402
from .xtool import XToolDriver  # noqa: E402

DRIVERS = {d.name: d for d in (FolderDriver, MarlinDriver, BambuDriver, XToolDriver)}
