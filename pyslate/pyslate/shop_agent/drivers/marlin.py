"""USB serial driver for Marlin-style printers (JG Maker A8S / A6).

Slices the model with the shop's slicer when needed, then streams the G-code line by line,
waiting for each "ok". Only one program can hold the COM port: close the printer's own
software (Nero 8 by Noitavonne) or disconnect it from the port while the agent prints.
"""

from __future__ import annotations

import time
from pathlib import Path

from . import Cancelled, Driver
from .slicer import needs_slicing, slice_model

# Sent when the shop cancels: stop heaters and fan, lift the nozzle clear, motors off.
STOP_GCODE = ["M108", "M104 S0", "M140 S0", "M107", "G91", "G1 Z10 F600", "G90", "M84"]
NO_REPLY_SECONDS = 600  # a G28 or M109 can take minutes; ten without a word is a dead link


def clean_lines(text: str) -> list[str]:
    out = []
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if line:
            out.append(line)
    return out


def checksum(line: str) -> int:
    cs = 0
    for ch in line.encode():
        cs ^= ch
    return cs


class MarlinDriver(Driver):
    name = "marlin"

    def __init__(self, cfg, workdir):
        super().__init__(cfg, workdir)
        self.active = None  # (percent, message) while printing

    def status(self) -> dict:
        if self.active:
            return {"state": "busy", "progress": self.active[0], "detail": self.active[1]}
        # Opening the port would reset the printer and fight the printer's own software,
        # so the agent only connects when a job starts.
        return {"state": "idle", "detail": f"{self.cfg.get('port', '?')}; connects when a job starts"}

    def open_port(self):
        import serial  # pyserial

        port = serial.Serial(self.cfg["port"], int(self.cfg.get("baud", 115200)), timeout=1)
        time.sleep(float(self.cfg.get("reset_wait_s", 2.5)))  # most boards reboot on connect
        port.reset_input_buffer()
        return port

    def run(self, run: dict, path: Path, ctx) -> str:
        if needs_slicing(path, ".gcode"):
            ctx.progress(0, "Slicing", force=True)
            path = slice_model(self.cfg.get("slicer"), path, int(run.get("copies", 1)))
        lines = clean_lines(path.read_text(encoding="utf-8", errors="replace"))
        if not lines:
            raise RuntimeError("The G-code file is empty")
        port = self.open_port()
        try:
            return self.stream(port, lines, ctx)
        finally:
            self.active = None
            port.close()

    def stream(self, port, lines: list[str], ctx) -> str:
        self._send(port, 0, "M110 N0")
        self._wait_ok(port)
        total = len(lines)
        n = 0
        while n < total:
            if ctx.cancelled():
                self.stop(port)
                raise Cancelled("Stopped by the shop; heaters off and nozzle raised")
            number = n + 1
            self._send(port, number, lines[n])
            resend = self._wait_ok(port)
            if resend is not None:
                n = max(0, resend - 1)  # the printer asks again from line `resend`
                continue
            n += 1
            pct = int(n * 100 / total)
            self.active = (pct, f"Line {n} of {total}")
            ctx.progress(pct, f"Printing, line {n} of {total}")
        return f"Printed {total} lines of G-code"

    def stop(self, port) -> None:
        for cmd in STOP_GCODE:
            port.write((cmd + "\n").encode())
            time.sleep(0.2)

    @staticmethod
    def _send(port, number: int, line: str) -> None:
        body = f"N{number} {line}"
        port.write(f"{body}*{checksum(body)}\n".encode())

    @staticmethod
    def _wait_ok(port) -> int | None:
        """Wait for "ok". Returns a line number if the printer asked for a resend."""
        deadline = time.monotonic() + NO_REPLY_SECONDS
        resend = None
        while time.monotonic() < deadline:
            reply = port.readline().decode(errors="replace").strip()
            if not reply:
                continue
            deadline = time.monotonic() + NO_REPLY_SECONDS  # busy/temperature reports keep it alive
            low = reply.lower()
            if low.startswith(("resend:", "rs:", "rs ")):
                digits = "".join(ch for ch in reply.split(":", 1)[-1] if ch.isdigit())
                resend = int(digits) if digits else None
            elif low.startswith("ok"):
                return resend
            elif low.startswith("error") and "checksum" not in low and "line number" not in low:
                if "kill" in low or "halted" in low or "printer stopped" in low:
                    raise RuntimeError(f"Printer stopped: {reply}")
        raise RuntimeError("The printer stopped answering on the serial port")
