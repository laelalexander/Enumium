"""Shop-floor HUD: a full-screen terminal board for the workshop screens.

    py -3 -m shop_agent hud --config agent.json                  # everything
    py -3 -m shop_agent hud --config agent.json --line laser --title "LASER BAY"
    py -3 -m shop_agent hud --demo                               # sample data, no server

Shows each machine's status, the job on it with a progress bar, its queue with start
times, a schedule strip for the next hours, orders by due date and what just finished.
It only reads from Pyslate; it never starts or stops anything. Needs: pip install rich
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Phosphor palette: green is fine, amber needs a look, red needs a person.
OK, WARN, BAD, DIM, INK, HOT = "bright_green", "yellow", "bright_red", "grey50", "grey85", "orange1"
STATE_STYLE = {
    "busy": (HOT, "RUNNING"), "running": (HOT, "RUNNING"), "idle": (OK, "IDLE"), "paused": (WARN, "PAUSED"),
    "error": (BAD, "ERROR"), "offline": (BAD, "OFFLINE"), "manual": (DIM, "MANUAL"), "unknown": (DIM, "UNKNOWN"),
}
BLOCKS = ("▓", "▒")


def _t(iso: str | None) -> datetime | None:
    if not iso:
        return None
    dt = datetime.fromisoformat(iso)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _local(dt: datetime) -> datetime:
    return dt.astimezone()  # the shop PC's own time zone


def _hm(dt: datetime | None) -> str:
    return _local(dt).strftime("%H:%M") if dt else "--:--"


def _span(minutes: float) -> str:
    minutes = max(0, int(round(minutes)))
    if minutes < 60:
        return f"{minutes}m"
    h, m = divmod(minutes, 60)
    if h < 48:
        return f"{h}h{m:02d}"
    return f"{h // 24}d{h % 24:02d}h"


def _due(dt: datetime | None, now: datetime) -> tuple[str, str]:
    if dt is None:
        return "no date", DIM
    left = (dt - now).total_seconds() / 60
    if left < 0:
        return f"LATE {_span(-left)}", BAD
    style = WARN if left < 24 * 60 else OK
    return f"{_local(dt):%a %d} · {_span(left)}", style


def bar(pct: float | None, width: int, style: str = HOT) -> "Text":
    from rich.text import Text

    width = max(4, width)
    if pct is None:
        return Text("·" * width, style=DIM)
    fill = pct / 100 * width
    full = int(fill)
    partial = "▏▎▍▌▋▊▉"[int((fill - full) * 7)] if full < width and fill - full >= 1 / 7 else ""
    t = Text("█" * full + partial, style=style)
    t.append("░" * (width - full - len(partial)), style="grey23")
    return t


def _trim(text: str, width: int) -> str:
    return text if len(text) <= width else text[: max(1, width - 1)] + "…"


# ---- panels ----------------------------------------------------------------------


def header(feed: dict, title: str, link_ok: bool, width: int):
    from rich.table import Table
    from rich.text import Text

    now = _local(_t(feed["now"]) or datetime.now(timezone.utc))
    tot = feed["totals"]
    left = Text()
    left.append(" PYSLATE ", style="bold black on " + HOT)
    left.append(f" {title} ", style="bold " + INK)
    mid = Text()
    for label, value, style in (("QUEUED", tot["queued"], INK), ("RUNNING", tot["running"], HOT),
                                ("LATE", tot["late"], BAD if tot["late"] else DIM), ("DONE 24H", tot["done_24h"], OK)):
        mid.append(f" {label} ", style=DIM)
        mid.append(f"{value:>2} ", style="bold " + style)
    right = Text()
    right.append("● LINK " if link_ok else "● NO LINK ", style=OK if link_ok else "blink " + BAD)
    right.append(now.strftime("%a %d %b  "), style=DIM)
    right.append(now.strftime("%H:%M:%S "), style="bold " + INK)
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="center")
    grid.add_column(justify="right")
    grid.add_row(left, mid if width >= 100 else Text(""), right)
    return grid


def at_operator(cur: dict) -> bool:
    """Hand-off runs (xTool Studio, folders) wait for a person to finish them at the machine."""
    return "done in pyslate" in (cur.get("message") or "").lower()


def machine_panel(m: dict, now: datetime, width: int, max_queue: int, height: int | None = None):
    from rich import box
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    cur = m["current"]
    state = "busy" if cur and cur.get("run_state") == "running" else m["state"]
    style, word = STATE_STYLE.get(state, (DIM, state.upper()))
    if cur and cur.get("run_state") == "running" and at_operator(cur):
        style, word = WARN, "AT MACHINE"
    elif cur and cur.get("run_state") in ("pending", "claimed"):
        style, word = WARN, "SENDING"
    elif cur and cur.get("run_state") == "cancel_requested":
        style, word = BAD, "STOPPING"
    inner = width - 4
    rows = []
    top = Text()
    top.append(f"■ {word}", style="bold " + style)
    if cur and not at_operator(cur):
        top.append(f"  {cur['progress']:>3}%", style="bold " + INK)
        if cur.get("minutes_left"):
            top.append(f"  {_span(cur['minutes_left'])} left", style=DIM)
    elif m["detail"]:
        top.append("  " + _trim(m["detail"], inner - len(word) - 4), style=DIM)
    rows.append(top)
    if cur:
        if at_operator(cur):
            rows.append(Text("▚" * inner, style=WARN))
        else:
            rows.append(bar(cur["progress"], inner, style))
        job = Text()
        job.append(f"#{cur['order']} ", style="bold " + HOT)
        job.append(_trim(cur["part"], inner - 22), style=INK)
        job.append(f" ×{cur['copies']} {cur['material']}", style=DIM)
        rows.append(job)
        if cur.get("run_state") not in ("running",) or cur.get("message"):
            rows.append(Text(_trim(f"{cur['run_label']}: {cur.get('message') or ''}".rstrip(": "), inner), style=WARN
                             if cur.get("run_state") in ("pending", "claimed", "cancel_requested") else DIM))
    queue = m["queue"]
    if height:  # fit the queue into the panel: border, status, run lines, table header, footer
        used = 2 + 1 + (3 if cur else 0) + 1 + 1
        max_queue = max(1, height - used - (1 if len(queue) > height - used else 0))
    if queue:
        t = Table(box=None, show_header=True, header_style=DIM, pad_edge=False, padding=(0, 1), expand=True)
        t.add_column("ORD", style="bold " + INK, no_wrap=True, width=5)
        t.add_column("PART", ratio=1, no_wrap=True, overflow="ellipsis")
        t.add_column("QTY", justify="right", no_wrap=True, width=5)
        t.add_column("START", justify="right", no_wrap=True, width=5)
        t.add_column("DUE", justify="right", no_wrap=True, width=15)
        for q in queue[:max_queue]:
            due_txt, due_style = _due(_t(q["due"]), now)
            part_style = BAD if q["state"] == "failed" else INK
            left = q["quantity"] - q["made"]
            t.add_row(str(q["order"]), Text(q["part"] + (" ✖ FAILED" if q["state"] == "failed" else ""), style=part_style),
                      f"{left}" if not q["made"] else f"{left}/{q['quantity']}",
                      _hm(_t(q["start"])), Text(due_txt, style=BAD if q["late"] else due_style))
        rows.append(t)
        if len(queue) > max_queue:
            rows.append(Text(f"  + {len(queue) - max_queue} more", style=DIM))
    elif not cur:
        rows.append(Text("queue empty", style=DIM))
    foot = Text()
    if m["queued_minutes"]:
        foot.append(f"busy until {_hm(_t(m['busy_until']))}  ·  {_span(m['queued_minutes'])} of work", style=DIM)
    if foot:
        rows.append(foot)
    title = Text(f" {m['name'].upper()} ", style="bold " + (INK if state != "offline" else BAD))
    return Panel(Group(*rows), title=title, title_align="left", border_style=style if state != "idle" else "green4",
                 box=box.HEAVY if cur else box.ROUNDED, width=width, height=height, padding=(0, 1))


def schedule(machines: list[dict], now: datetime, width: int, hours: int):
    """A strip per machine: █ the current run, ▓▒ queued jobs, ┃ now."""
    from rich.text import Text

    label_w = min(16, max(len(m["name"]) for m in machines) if machines else 8)
    cols = max(10, width - label_w - 3)
    per_col = hours * 60 / cols  # minutes per character
    out = Text()
    axis = [" "] * cols
    for h in range(hours + 1):
        c = int(h * 60 / per_col)
        stamp = _hm(now + timedelta(hours=h))[:2] if h else "now"
        if c + len(stamp) <= cols and all(ch == " " for ch in axis[c:c + len(stamp) + 1]):
            axis[c:c + len(stamp)] = list(stamp)
    out.append(" " * (label_w + 1) + "".join(axis) + "\n", style=DIM)
    for m in machines:
        row = [("·", "grey23")] * cols
        segs = []
        if m["current"]:
            segs.append((now, now + timedelta(minutes=m["current"]["minutes_left"] or per_col),
                         "█", HOT, m["current"]["order"]))
        for i, q in enumerate(m["queue"]):
            segs.append((_t(q["start"]), _t(q["end"]), BLOCKS[i % 2], BAD if q["late"] else OK, q["order"]))
        for start, end, ch, style, order in segs:
            a = int((start - now).total_seconds() / 60 / per_col)
            b = max(a + 1, math.ceil((end - now).total_seconds() / 60 / per_col))
            for c in range(max(0, a), min(cols, b)):
                row[c] = (ch, style)
            tag = f"#{order}"
            if b - a >= len(tag) + 2 and 0 <= a and a + 1 + len(tag) < cols:
                for k, chx in enumerate(tag):
                    row[a + 1 + k] = (chx, "bold " + ("black on orange1" if ch == "█" else "white on dark_green" if style == OK else "white on red3"))
        out.append(_trim(m["name"], label_w).ljust(label_w) + " ", style=INK)
        for ch, style in row:
            out.append(ch, style=style)
        out.append("\n")
    return out


def orders_table(orders: list[dict], now: datetime, limit: int):
    from rich.table import Table
    from rich.text import Text

    t = Table(box=None, show_header=True, header_style=DIM, pad_edge=False, padding=(0, 1), expand=True)
    t.add_column("ORDER", style="bold " + INK, no_wrap=True)
    t.add_column("CUSTOMER", ratio=1, no_wrap=True, overflow="ellipsis")
    t.add_column("PARTS", no_wrap=True)
    t.add_column("DUE", justify="right", no_wrap=True)
    for o in orders[:limit]:
        due_txt, style = _due(_t(o["due"]), now)
        pct = o["jobs_done"] * 100 / o["jobs"] if o["jobs"] else 0
        parts = bar(pct, 8, OK)
        parts.append(f" {o['jobs_done']}/{o['jobs']}", style=DIM)
        t.add_row(f"#{o['order']}", o["customer"], parts, Text(due_txt, style=("blink " + BAD) if o["late"] else style))
    if not orders:
        t.add_row("", Text("no open orders", style=DIM), "", "")
    return t


def ticker(events: list[dict], review: list[dict]):
    from rich.text import Text

    out = Text()
    for r in review[:3]:
        out.append(f" ◆ NEEDS MACHINE #{r['order']} {r['part']} ", style="bold black on yellow")
        out.append("  ")
    for e in events[:6]:
        mark, style = {"done": ("✔", OK), "failed": ("✖", BAD), "cancelled": ("■", DIM)}.get(e["state"], ("·", DIM))
        at = _hm(_t(e["at"]))
        out.append(f"{mark} {at} {e['machine_id'].upper()} #{e['order']} {e['part']} ×{e['copies']}", style=style)
        out.append("   ")
    if not out:
        out.append("nothing finished in the last 24 hours", style=DIM)
    return out


def render(feed: dict, width: int, height: int, title: str = "SHOP FLOOR", lines: list[str] | None = None,
           show_all: bool = False, link_ok: bool = True, hours: int = 12):
    from rich.console import Group
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box

    now = _t(feed["now"]) or datetime.now(timezone.utc)
    machines = [m for m in feed["machines"] if not lines or m["line"] in lines]
    if not show_all:  # hide hand-run machines with nothing on them
        machines = [m for m in machines if m["current"] or m["queue"] or m["state"] != "manual"]
    if lines:  # count only this area's machines in the header
        feed = {**feed, "totals": {**feed["totals"], "queued": sum(len(m["queue"]) for m in machines),
                                   "running": sum(1 for m in machines if m["current"])}}

    sched_h = min(len(machines), 10) + 3
    bottom_h = max(sched_h, 9)
    body_h = max(8, height - 3 - bottom_h - 1)
    # As few columns as the height allows, so names and parts have room to read from across the shop.
    max_rows = max(1, body_h // 10)
    ncols = min(max(1, width // 40), max(1, math.ceil(len(machines) / max_rows)))
    panel_w = width // ncols
    nrows = max(1, math.ceil(len(machines) / ncols))
    per_row_h = body_h // nrows
    max_queue = max(1, per_row_h - 7)

    grid = Table.grid(expand=True)
    for _ in range(ncols):
        grid.add_column(width=panel_w)
    for r in range(nrows):
        cells = [machine_panel(m, now, panel_w, max_queue, per_row_h) for m in machines[r * ncols:(r + 1) * ncols]]
        grid.add_row(*cells)

    layout = Layout()
    layout.split_column(
        Layout(Panel(header(feed, title, link_ok, width), box=box.HEAVY, border_style=HOT, padding=0), name="head", size=3),
        Layout(grid if machines else Text("No machines on this board.", style=DIM), name="body", ratio=1),
        Layout(name="bottom", size=bottom_h),
        Layout(ticker(feed["events"], feed["review"]), name="tick", size=1),
    )
    sched_w = int(width * 0.62) if width >= 110 else width
    sched = Panel(schedule(machines[:10], now, sched_w - 4, hours) if machines else Text(""),
                  title=Text(f" SCHEDULE · NEXT {hours}H ", style="bold " + INK), title_align="left",
                  border_style="grey37", box=box.ROUNDED, padding=(0, 1))
    if width >= 110:
        layout["bottom"].split_row(
            Layout(sched, size=sched_w),
            Layout(Panel(orders_table(feed["orders"], now, bottom_h - 3), title=Text(" ORDERS BY DUE DATE ", style="bold " + INK),
                         title_align="left", border_style="grey37", box=box.ROUNDED, padding=(0, 1))),
        )
    else:
        layout["bottom"].update(sched)
    return layout


# ---- running it --------------------------------------------------------------------


def demo_feed() -> dict:
    """Sample data, so the screen can be checked without a server."""
    now = datetime.now(timezone.utc)

    def iso(minutes: float = 0, days: float = 0) -> str:
        return (now + timedelta(minutes=minutes, days=days)).isoformat()

    def q(order, part, qty, start, end, due_days, made=0, state="queued", late=False):
        return {"order": order, "part": part, "material": "pla", "quantity": qty, "made": made, "state": state,
                "start": iso(start), "end": iso(end), "due": iso(days=due_days), "late": late, "minutes_each": 30}

    def cur(order, part, pct, left, copies=1, state="running", msg="", material="pla"):
        return {"order": order, "part": part, "material": material, "progress": pct, "minutes_left": left,
                "copies": copies, "run_state": state, "run_label": state.title(), "message": msg}

    def mach(mid, name, line, state, detail, current=None, queue=(), until=0):
        return {"id": mid, "name": name, "line": line, "state": state, "detail": detail, "current": current,
                "queue": list(queue), "busy_until": iso(until), "queued_minutes": until, "online": state != "offline"}

    machines = [
        mach("bambu", "Bambu Lab printer", "print", "busy", "Running", cur(1003, "bracket-base.stl", 46, 38),
             [q(1003, "knob.stl", 3, 38, 128, 2), q(1007, "planter-small.3mf", 2, 128, 410, 1.2, late=True)], 410),
        mach("a8s", "JG Maker A8S", "print", "idle", "COM4; connects when a job starts", None,
             [q(1006, "robot-arm-link.stl", 4, 0, 260, 4, made=1)], 260),
        mach("x1", "xTool X1", "laser", "idle", "On the network", cur(1002, "sign-panel.dxf", 0, 12, 2, "running",
             "Opened order1002-sign-panel.svg for xTool Studio: speed 8 mm/s, 1 pass(es). Frame, start on the "
             "machine, then mark done in Pyslate.", "plywood-3"), [q(1001, "gear-plate.stl", 6, 12, 40, 3)], 40),
        mach("m2", "xTool M2", "laser", "idle", "On the network", None, [q(1008, "coasters.dxf", 12, 0, 70, 5)], 70),
        mach("f2", "xTool F2", "laser", "offline", "Not answering at 192.168.1.62", None,
             [q(1009, "dog-tag.dxf", 2, 0, 8, 0.4, state="failed")], 8),
        mach("24r", "Tormach 24R router", "router", "manual", "3 file(s) in \\\\pathpilot\\gcode", None,
             [q(1010, "shelf-side.dxf", 2, 0, 95, 6)], 95),
    ]
    return {
        "now": now.isoformat(), "machines": machines,
        "review": [{"order": 1011, "part": "big-frame.stl"}],
        "orders": [
            {"order": 1009, "customer": "Ada Park", "status": "In queue", "due": iso(days=-0.1), "late": True, "jobs_done": 0, "jobs": 1},
            {"order": 1007, "customer": "Northside Makers", "status": "Making", "due": iso(days=1.2), "late": False, "jobs_done": 1, "jobs": 2},
            {"order": 1003, "customer": "Jordan Lee", "status": "Making", "due": iso(days=2), "late": False, "jobs_done": 0, "jobs": 2},
            {"order": 1001, "customer": "Bayou Signs", "status": "In queue", "due": iso(days=3), "late": False, "jobs_done": 0, "jobs": 1},
            {"order": 1006, "customer": "Enumium robot arm", "status": "Making", "due": iso(days=4), "late": False, "jobs_done": 2, "jobs": 5},
        ],
        "events": [
            {"at": iso(-14), "state": "done", "machine_id": "m2", "order": 1004, "part": "name-tags.dxf", "copies": 8},
            {"at": iso(-55), "state": "failed", "machine_id": "bambu", "order": 1005, "part": "vase.stl", "copies": 1},
            {"at": iso(-90), "state": "done", "machine_id": "x1", "order": 1000, "part": "box-lid.dxf", "copies": 4},
        ],
        "totals": {"queued": 8, "running": 2, "late": 1, "done_24h": 2},
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="shop_agent hud", description="Shop-floor HUD for a workshop screen")
    p.add_argument("--config", default="agent.json")
    p.add_argument("--line", default="", help="only these lines, e.g. laser or print,laser")
    p.add_argument("--title", default="", help="name on the screen, e.g. LASER BAY")
    p.add_argument("--hours", type=int, default=12, help="how far ahead the schedule looks")
    p.add_argument("--refresh", type=float, default=5, help="seconds between updates")
    p.add_argument("--all", action="store_true", help="also show idle hand-run machines")
    p.add_argument("--demo", action="store_true", help="sample data, no server needed")
    args = p.parse_args(argv)
    try:
        from rich.console import Console
        from rich.live import Live
    except ImportError:
        print("The HUD needs the rich package: py -3 -m pip install rich")
        return 2
    lines = [x.strip() for x in args.line.split(",") if x.strip()]
    title = (args.title or (" + ".join(lines).upper() if lines else "SHOP FLOOR"))
    api = None
    if not args.demo:
        from .agent import Api

        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        api = Api(config["server"], config["token"], (config.get("name") or "shop") + "-hud", timeout=15)
    console = Console()
    feed, link_ok = (demo_feed(), True) if args.demo else (None, False)

    def frame():
        f = feed or {"now": datetime.now(timezone.utc).isoformat(), "machines": [], "review": [], "orders": [],
                     "events": [], "totals": {"queued": 0, "running": 0, "late": 0, "done_24h": 0}}
        f = {**f, "now": datetime.now(timezone.utc).isoformat()} if args.demo else f
        return render(f, console.width, console.height, title, lines, args.all, link_ok, args.hours)

    last = 0.0
    with Live(frame(), console=console, screen=True, auto_refresh=False) as live:
        try:
            while True:
                if api and time.monotonic() - last >= args.refresh:
                    last = time.monotonic()
                    try:
                        feed = api._call("GET", "/api/agent/board")
                        link_ok = True
                    except Exception:  # keep showing the last board, flag the link
                        link_ok = False
                live.update(frame(), refresh=True)
                time.sleep(1)  # the clock ticks every second
        except KeyboardInterrupt:
            return 0
