"""Bambu Lab printers in LAN mode: upload the sliced .gcode.3mf over FTPS, start it over MQTT.

Turn on LAN mode on the printer (Settings > Network) and copy its access code and serial
number into agent.json. The printer must be on the same network as the shop PC.
Needs: pip install paho-mqtt
"""

from __future__ import annotations

import ftplib
import json
import socket
import ssl
import threading
import time
from pathlib import Path

from . import Cancelled, Driver
from .slicer import needs_slicing, slice_model

FINISHED, FAILED = "FINISH", "FAILED"
ACTIVE = {"PREPARE", "RUNNING", "PAUSE", "SLICING"}


def _insecure_tls() -> ssl.SSLContext:
    # The printers use a self-signed certificate on the local network.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class ImplicitFTPS(ftplib.FTP_TLS):
    """FTP over TLS from the first byte (port 990), which the printers use."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, value):
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        conn = self.context.wrap_socket(conn, server_hostname=self.host, session=self.sock.session)
        return conn, size


class BambuDriver(Driver):
    name = "bambu"

    def __init__(self, cfg, workdir):
        super().__init__(cfg, workdir)
        self.report: dict = {}
        self.client = None
        self.lock = threading.Lock()

    # -- MQTT --

    def _connect(self):
        if self.client is not None:
            return self.client
        import paho.mqtt.client as mqtt

        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except AttributeError:  # paho-mqtt 1.x
            client = mqtt.Client()
        client.username_pw_set("bblp", self.cfg["access_code"])
        client.tls_set_context(_insecure_tls())
        serial = self.cfg["serial"]

        def on_connect(c, *_):
            c.subscribe(f"device/{serial}/report")
            c.publish(f"device/{serial}/request", json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))

        def on_message(c, userdata, msg):
            try:
                data = json.loads(msg.payload)
            except ValueError:
                return
            with self.lock:
                self.report.update(data.get("print") or {})

        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(self.cfg["host"], 8883, keepalive=60)
        client.loop_start()
        self.client = client
        return client

    def _command(self, payload: dict) -> None:
        self._connect().publish(f"device/{self.cfg['serial']}/request", json.dumps({"print": payload}))

    def status(self) -> dict:
        try:
            self._connect()
        except (OSError, KeyError) as exc:
            return {"state": "offline", "detail": f"Cannot reach the printer: {exc}"}
        with self.lock:
            r = dict(self.report)
        state = r.get("gcode_state", "")
        if not state:
            return {"state": "unknown", "detail": "Connected; waiting for the printer's first report"}
        mapped = "busy" if state in ACTIVE else "error" if state == FAILED else "idle"
        if state == "PAUSE":
            mapped = "paused"
        detail = state.title()
        if r.get("mc_remaining_time") and state in ACTIVE:
            detail += f", {r['mc_remaining_time']} min left"
        return {"state": mapped, "detail": detail, "progress": r.get("mc_percent")}

    # -- a run --

    def upload(self, path: Path) -> str:
        ftp = ImplicitFTPS(context=_insecure_tls(), timeout=60)
        ftp.connect(self.cfg["host"], 990)
        ftp.login("bblp", self.cfg["access_code"])
        ftp.prot_p()
        with open(path, "rb") as fh:
            ftp.storbinary(f"STOR {path.name}", fh)
        ftp.quit()
        return path.name

    def run(self, run: dict, path: Path, ctx) -> str:
        if needs_slicing(path, ".gcode.3mf"):
            ctx.progress(0, "Slicing", force=True)
            path = slice_model(self.cfg.get("slicer"), path, int(run.get("copies", 1)))
        if not path.name.lower().endswith(".3mf"):
            raise RuntimeError("Bambu printers take a sliced .gcode.3mf; check the slicer's output_ext")
        state = self.status()
        if state["state"] in ("busy", "paused"):
            raise RuntimeError("The printer is busy with another print")
        ctx.progress(0, "Uploading to the printer", force=True)
        name = self.upload(path)
        self._command({
            "sequence_id": "0", "command": "project_file", "param": f"Metadata/plate_{self.cfg.get('plate', 1)}.gcode",
            "project_id": "0", "profile_id": "0", "task_id": "0", "subtask_id": "0",
            "subtask_name": Path(name).stem, "url": f"{self.cfg.get('url_prefix', 'file:///sdcard/')}{name}",
            "timelapse": False, "bed_type": "auto", "bed_levelling": True, "flow_cali": False,
            "vibration_cali": True, "layer_inspect": False,
            "use_ams": bool(self.cfg.get("use_ams", False)), "ams_mapping": self.cfg.get("ams_mapping", []),
        })
        return self.watch(ctx)

    def watch(self, ctx, start_timeout: float = 300) -> str:
        started = False
        begin = time.monotonic()
        while True:
            if ctx.cancelled():
                self._command({"sequence_id": "0", "command": "stop"})
                raise Cancelled("Stopped by the shop")
            with self.lock:
                r = dict(self.report)
            state = r.get("gcode_state", "")
            if state in ACTIVE:
                started = True
                ctx.progress(r.get("mc_percent"), state.title()
                             + (f", {r['mc_remaining_time']} min left" if r.get("mc_remaining_time") else ""))
            elif started and state == FINISHED:
                return "Print finished"
            elif started and state == FAILED:
                raise RuntimeError(f"The printer reported a failed print (error {r.get('print_error', '?')})")
            elif not started and time.monotonic() - begin > start_timeout:
                raise RuntimeError("The printer did not start the print within 5 minutes")
            time.sleep(5)


def reachable(host: str, port: int, timeout: float = 2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
