"""The agent loop: report machine status, pick up pending runs, hand each to its driver."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import __version__
from .drivers import DRIVERS, Cancelled, Handoff, RunContext

log = logging.getLogger("shop_agent")


class ApiError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"{status}: {message}")
        self.status = status


class Api:
    """Talks to the Pyslate server over HTTPS. Only the standard library."""

    def __init__(self, server: str, token: str, name: str, timeout: float = 30):
        self.base = server.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}", "X-Agent-Name": name,
                        "User-Agent": f"pyslate-shop-agent/{__version__}"}
        self.timeout = timeout

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        headers = dict(self.headers)
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            raise ApiError(exc.code, detail) from exc

    def heartbeat(self, machines: list[dict]) -> dict:
        return self._call("POST", "/api/agent/heartbeat", {"machines": machines})

    def pending(self, machine_ids: list[str]) -> list[dict]:
        return self._call("GET", "/api/agent/runs?machines=" + ",".join(machine_ids))["runs"]

    def claim(self, run_id: str) -> dict:
        return self._call("POST", f"/api/agent/runs/{run_id}/claim")

    def get(self, run_id: str) -> dict:
        return self._call("GET", f"/api/agent/runs/{run_id}")

    def update(self, run_id: str, state: str, progress: int | None = None, message: str = "") -> dict:
        return self._call("POST", f"/api/agent/runs/{run_id}/update",
                          {"state": state, "progress": progress, "message": message})

    def download(self, run: dict, target: Path) -> Path:
        req = urllib.request.Request(self.base + f"/api/agent/runs/{run['id']}/file", headers=self.headers)
        with urllib.request.urlopen(req, timeout=120) as resp, open(target, "wb") as out:
            while chunk := resp.read(1 << 16):
                out.write(chunk)
        return target


class ServerContext(RunContext):
    """What a driver uses during a run: report progress, and learn if the shop cancelled."""

    def __init__(self, api, run: dict, report_seconds: float = 10):
        self.api, self.run, self.report_seconds = api, run, report_seconds
        self._last = 0.0
        self._cancel = False

    def progress(self, percent: int | None = None, message: str = "", force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last < self.report_seconds:
            return
        self._last = now
        try:
            state = self.api.update(self.run["id"], "running", percent, message)["state"]
            self._cancel = state == "cancel_requested"
        except (ApiError, OSError) as exc:  # keep the machine going if the internet blips
            log.warning("progress report failed: %s", exc)

    def cancelled(self) -> bool:
        if not self._cancel and time.monotonic() - self._last >= self.report_seconds:
            try:
                self._cancel = self.api.get(self.run["id"])["state"] == "cancel_requested"
            except (ApiError, OSError):
                pass
            self._last = time.monotonic()
        return self._cancel


class Agent:
    def __init__(self, config: dict, api=None, workdir: Path | None = None):
        self.config = config
        self.api = api or Api(config["server"], config["token"], config.get("name") or socket.gethostname())
        self.workdir = Path(workdir or config.get("workdir") or Path.home() / "Pyslate" / "work")
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.drivers = {}
        for m in config.get("machines", []):
            if not m.get("enabled", True):
                continue
            cls = DRIVERS.get(m.get("driver", ""))
            if cls is None:
                raise SystemExit(f"Machine {m.get('id')}: unknown driver {m.get('driver')!r}. "
                                 f"Use one of {', '.join(sorted(DRIVERS))}.")
            self.drivers[m["id"]] = cls(m, self.workdir)
        self.busy: dict[str, threading.Thread] = {}

    def statuses(self) -> list[dict]:
        out = []
        for mid, d in self.drivers.items():
            try:
                s = d.status()
            except Exception as exc:  # a status probe must never stop the agent
                s = {"state": "error", "detail": str(exc)}
            out.append({"id": mid, "driver": d.name, **s})
        return out

    def tick(self, wait: bool = False) -> int:
        """One pass: heartbeat, then start any pending runs for idle machines. Returns runs started."""
        self.api.heartbeat(self.statuses())
        for mid, t in list(self.busy.items()):
            if not t.is_alive():
                del self.busy[mid]
        free = [mid for mid in self.drivers if mid not in self.busy]
        if not free:
            return 0
        started = 0
        for run in self.api.pending(free):
            mid = run["machine_id"]
            if mid in self.busy or mid not in self.drivers:
                continue
            try:
                run = self.api.claim(run["id"])
            except ApiError as exc:
                if exc.status == 409:
                    continue  # another agent took it, or it was cancelled
                raise
            t = threading.Thread(target=self.execute, args=(run,), name=f"run-{mid}", daemon=True)
            self.busy[mid] = t
            t.start()
            started += 1
            if wait:
                t.join()
        return started

    def execute(self, run: dict) -> None:
        driver = self.drivers[run["machine_id"]]
        ctx = ServerContext(self.api, run)
        log.info("run %s: order %s %s on %s", run["id"][:8], run["job"]["order_number"],
                 run["job"]["part_name"], run["machine_id"])
        try:
            folder = self.workdir / run["id"]
            folder.mkdir(exist_ok=True)
            path = self.api.download(run, folder / Path(run["file_name"]).name)
            self.api.update(run["id"], "running", 0, f"Starting on {driver.label}")
            result = driver.run(run, path, ctx)
        except Cancelled as exc:
            self._final(run, "cancelled", str(exc) or "Stopped by the shop")
        except Handoff as exc:
            # The operator finishes on the machine and marks the run done in Pyslate.
            self._report(run, "running", None, str(exc))
        except Exception as exc:
            log.exception("run %s failed", run["id"][:8])
            self._final(run, "failed", f"{type(exc).__name__}: {exc}")
        else:
            self._final(run, "done", result or "Finished")

    def _report(self, run, state, progress, message):
        for attempt in range(5):
            try:
                return self.api.update(run["id"], state, progress, message[:2000])
            except (ApiError, OSError) as exc:
                if isinstance(exc, ApiError) and exc.status in (404, 409):
                    log.warning("server refused %s for run %s: %s", state, run["id"][:8], exc)
                    return None
                time.sleep(2 ** attempt)
        log.error("could not report %s for run %s", state, run["id"][:8])

    def _final(self, run, state, message):
        self._report(run, state, 100 if state == "done" else None, message)

    def serve_forever(self) -> None:
        poll = float(self.config.get("poll_seconds", 10))
        log.info("Pyslate shop agent %s: %d machine(s), server %s", __version__, len(self.drivers), self.api.base)
        while True:
            try:
                self.tick()
            except ApiError as exc:
                log.error("server said %s", exc)
                if exc.status in (401, 503):
                    log.error("check the token in agent.json and PYSLATE_AGENT_TOKEN on the server")
            except OSError as exc:
                log.warning("server unreachable: %s", exc)
            time.sleep(poll)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="shop_agent", description="Pyslate shop agent")
    p.add_argument("--config", default="agent.json")
    p.add_argument("--once", action="store_true", help="one heartbeat and poll, then wait for runs and exit")
    p.add_argument("--status", action="store_true", help="print each machine's status and exit")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if not config.get("token") or config["token"].startswith("PASTE"):
        print("Put the agent token from Pyslate > Shop console > Shop agent into agent.json first.")
        return 2
    agent = Agent(config)
    if args.status:
        for s in agent.statuses():
            print(f"{s['id']:>10}  {s.get('state', '?'):<8} {s.get('detail', '')}")
        return 0
    if args.once:
        agent.tick(wait=True)
        return 0
    try:
        agent.serve_forever()
    except KeyboardInterrupt:
        return 0
