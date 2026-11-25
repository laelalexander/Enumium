"""The fab shop's production side: per-machine queues, sending jobs to machines, and the
API the shop agent on the shop PC uses to pick up work and report machine status.

The server cannot reach machines on the shop's network, so the shop agent pulls: it
polls for pending runs, claims one, downloads its file, starts the machine and reports
progress. See shop_agent/README.md.
"""

from __future__ import annotations

import io
import secrets
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import jobfiles, services
from .models import (
    JOB_LABELS, RUN_ACTIVE_STATES, RUN_FINAL_STATES, Job, JobRun, MachineStatus, utcnow,
)
from .shop import LINE_LABELS, LINES, SHEET_LINES

AGENT_ONLINE_SECONDS = 90
REVIEW_LANE = "review"
AGENT_DIR = Path(__file__).resolve().parent / "shop_agent"  # zipped for the shop PC; imports nothing from pyslate


class ProductionError(services.ServiceError):
    pass


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:  # SQLite drops the zone
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ---- operations ------------------------------------------------------------


def _material(profile, job: Job) -> dict:
    return profile.material(job.quote_line.material_id) or {} if job.quote_line.material_id else {}


def machines_for(profile, job: Job) -> list[dict]:
    """Machines that can take this job: the same line, and the material's machines first."""
    same = [m for m in profile.data["machines"] if m["line"] == job.line]
    preferred = set(_material(profile, job).get("machines", []))
    return sorted(same, key=lambda m: (m["id"] not in preferred, m["name"]))


def default_settings(profile, job: Job) -> dict:
    mat = _material(profile, job)
    out: dict = {"material": mat.get("name", job.quote_line.material_id or "")}
    if job.line in SHEET_LINES:
        out.update(
            speed_mm_s=mat.get("cut_speed_mm_s"), passes=mat.get("passes", 1), power_pct=None,
            thickness_mm=mat.get("thickness_mm"), engrave_only=bool(mat.get("engrave_only")),
        )
    return out


def part_progress(profile, job: Job | None) -> dict:
    """What the customer sees for one part: a short status and a percentage when known."""
    if job is None:
        return {"text": "Waiting for payment", "pct": None, "step": 0}
    machine = (profile.machine(job.machine_id or "") or {}).get("name", "the shop")
    verb = services.PART_VERBS.get(job.line, "Making")
    made = job.copies_done
    run = job.active_run
    if job.state == "done":
        return {"text": f"Made · {job.quantity} of {job.quantity}", "pct": 100, "step": 3}
    if job.state == "running" or (run and run.state == "running"):
        pct = run.progress if run and run.progress else None
        extra = f" · {made} of {job.quantity} made" if made else ""
        return {"text": f"{verb} on the {machine}{extra}", "pct": pct, "step": 2}
    if job.state == "sent":
        return {"text": f"Loading onto the {machine}", "pct": None, "step": 2}
    if job.state == "review":
        return {"text": "The shop is choosing a machine", "pct": None, "step": 1}
    if made:
        return {"text": f"{made} of {job.quantity} made · next batch queued", "pct": int(made * 100 / job.quantity), "step": 2}
    return {"text": f"In the queue for the {machine}", "pct": None, "step": 1}


def file_kinds(job: Job) -> list[str]:
    return ["svg", "dxf", "original"] if job.line in SHEET_LINES else ["original"]


def job_file(cfg, db: Session, job: Job, kind: str, machine_id: str | None = None,
             copies: int | None = None) -> tuple[Path, str, dict | None]:
    """The file for a job: the customer's original, or a laid-out SVG/DXF sheet.

    Returns (path, download name, layout info)."""
    part = job.quote_line.part
    original = cfg.upload_dir / part.stored_name
    stem = f"order{job.order.number}-{Path(part.filename).stem}"
    if kind == "original":
        return original, f"{stem}{Path(part.filename).suffix}", None
    if kind not in ("svg", "dxf") or job.line not in SHEET_LINES:
        raise ProductionError("That file type is not available for this job")
    profile = services.get_profile(db)
    machine = profile.machine(machine_id or job.machine_id or "")
    if machine is None:
        raise ProductionError("Choose a machine first, so the sheet matches its bed")
    copies = max(1, min(copies or job.quantity, job.quantity))
    outline = jobfiles.outline_for(original, engrave_only=bool(_material(profile, job).get("engrave_only")))
    layout = jobfiles.plan_layout(outline.width, outline.height, machine["bed_mm"], copies)
    out_dir = cfg.upload_dir / "jobs"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{job.id}-{machine['id']}-{layout.per_sheet}.{kind}"
    if not target.exists():
        if kind == "svg":
            jobfiles.write_svg(outline, layout, target, title=f"Order {job.order.number} {part.filename}")
        else:
            jobfiles.write_dxf(outline, layout, target)
    sw, sh = jobfiles.sheet_size(outline, layout)
    info = {
        "per_sheet": layout.per_sheet, "sheets": layout.sheets, "sheet_mm": [round(sw, 1), round(sh, 1)],
        "part_mm": [round(outline.width, 1), round(outline.height, 1)], "rotated": layout.rotated,
    }
    return target, f"{stem}-x{layout.per_sheet}.{kind}", info


def send_job(cfg, db: Session, job: Job, machine_id: str, copies: int, settings: dict) -> JobRun:
    if job.state not in ("queued",):
        raise ProductionError(f"Only queued jobs can be sent (this one is {JOB_LABELS.get(job.state, job.state)})")
    if job.order.status in ("awaiting_payment", "cancelled"):
        raise ProductionError("This order is not paid or was cancelled")
    profile = services.get_profile(db)
    if machine_id not in {m["id"] for m in machines_for(profile, job)}:
        raise ProductionError("That machine is not on this job's production line")
    remaining = job.quantity - job.copies_done
    if not 1 <= copies <= remaining:
        raise ProductionError(f"Copies must be between 1 and {remaining}")
    kind = "svg" if job.line in SHEET_LINES else "original"
    layout = None
    if kind == "svg":
        try:
            _, _, layout = job_file(cfg, db, job, "svg", machine_id, copies)
        except jobfiles.JobFileError as exc:
            raise ProductionError(str(exc)) from exc
        copies = layout["per_sheet"]  # one run is one sheet
    run = JobRun(job=job, machine_id=machine_id, copies=copies, file_kind=kind,
                 settings={**settings, **({"layout": layout} if layout else {})})
    db.add(run)
    job.machine_id = machine_id
    services.move_job(db, job, "sent", f"Sent to {profile.machine(machine_id)['name']}")
    db.expire(job, ["runs"])
    return run


def assign_machine(db: Session, job: Job, machine_id: str) -> None:
    if job.state not in ("queued", "review", "failed"):
        raise ProductionError("Move the job back to the queue before changing its machine")
    profile = services.get_profile(db)
    machine = profile.machine(machine_id)
    if machine is None:
        raise ProductionError("Unknown machine")
    job.machine_id = machine_id
    job.line = machine["line"]
    if job.state == "review":
        services.move_job(db, job, "queued", f"Assigned to {machine['name']}")
    else:
        db.commit()


def _sync_job(db: Session, run: JobRun) -> None:
    """Carry a run's new state over to its job (and through it, the order)."""
    job = run.job
    db.expire(job, ["runs"])
    if run.state == "running" and job.state == "sent":
        services.move_job(db, job, "running", "")
    elif run.state == "done":
        if job.state == "sent":
            services.move_job(db, job, "running", "")
        made = job.copies_done
        if made >= job.quantity:
            services.move_job(db, job, "done", f"{made} of {job.quantity} made")
        else:
            from .models import OrderEvent

            job.order.events.append(OrderEvent(status=job.order.status,
                                               note=f"{job.quote_line.part.filename}: {made} of {job.quantity} made"))
            services.move_job(db, job, "queued", f"{made} of {job.quantity} made; send the rest")
    elif run.state == "failed" and job.state in ("sent", "running"):
        services.move_job(db, job, "failed", run.message[:500] or "Run failed")
    elif run.state == "cancelled" and job.state in ("sent", "running"):
        services.move_job(db, job, "queued", "Run cancelled")
    else:
        db.commit()


AGENT_MOVES = {
    "claimed": {"running", "done", "failed", "cancelled"},
    "running": {"running", "done", "failed", "cancelled"},
    "cancel_requested": {"cancelled", "failed", "done", "running"},
}


def agent_update(db: Session, run: JobRun, state: str, progress: int | None, message: str) -> None:
    if state not in AGENT_MOVES.get(run.state, set()):
        raise ProductionError(f"A {run.state} run cannot move to {state}")
    if run.state == "cancel_requested" and state == "running":
        state = "cancel_requested"  # progress report while stopping; keep asking it to stop
    if progress is not None:
        run.progress = max(0, min(100, int(progress)))
    if message:
        run.message = message[:2000]
    if state == "running" and run.started_at is None:
        run.started_at = utcnow()
    if state in RUN_FINAL_STATES:
        run.finished_at = utcnow()
        if state == "done":
            run.progress = 100
    run.state = state
    _sync_job(db, run)


def claim_run(db: Session, run: JobRun, agent: str) -> None:
    if run.state != "pending":
        raise ProductionError("This run was already claimed or cancelled")
    run.state = "claimed"
    run.agent = agent[:64]
    db.commit()


def cancel_run(db: Session, run: JobRun) -> None:
    if run.state == "pending":
        run.state = "cancelled"
        run.finished_at = utcnow()
        _sync_job(db, run)
    elif run.state in ("claimed", "running"):
        run.state = "cancel_requested"
        db.commit()
    elif run.state != "cancel_requested":
        raise ProductionError("This run has already finished")


def close_run(db: Session, run: JobRun, state: str, message: str = "") -> None:
    """The shop marks a run finished by hand: hand-off runs, or a run the agent lost."""
    if state not in ("done", "failed") or run.state in RUN_FINAL_STATES:
        raise ProductionError("This run cannot be closed that way")
    if message:
        run.message = message[:2000]
    if state == "done":
        run.progress = 100
    run.state = state
    run.finished_at = utcnow()
    _sync_job(db, run)


def heartbeat(db: Session, agent: str, machines: list[dict]) -> None:
    now = utcnow()
    for m in machines[:100]:
        mid = str(m.get("id", ""))[:64]
        if not mid:
            continue
        row = db.get(MachineStatus, mid) or MachineStatus(machine_id=mid)
        row.state = str(m.get("state", "unknown"))[:20]
        row.detail = str(m.get("detail", ""))[:2000]
        p = m.get("progress")
        row.progress = max(0, min(100, int(p))) if isinstance(p, (int, float)) else None
        row.driver = str(m.get("driver", ""))[:32]
        row.agent = agent[:64]
        row.seen_at = now
        db.add(row)
    db.commit()


def machine_states(db: Session) -> dict[str, dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=AGENT_ONLINE_SECONDS)
    out = {}
    for row in db.scalars(select(MachineStatus)).all():
        seen = _aware(row.seen_at)
        online = seen is not None and seen >= cutoff
        out[row.machine_id] = {
            "state": row.state if online else "offline",
            "detail": row.detail if online else f"Shop agent last seen {seen:%b %d %H:%M} UTC",
            "progress": row.progress if online else None,
            "driver": row.driver, "agent": row.agent, "online": online,
            "seen": seen.isoformat() if seen else None,
        }
    return out


def run_json(run: JobRun, base: str = "") -> dict:
    job = run.job
    part = job.quote_line.part
    return {
        "id": run.id, "state": run.state, "label": run.label, "machine_id": run.machine_id,
        "copies": run.copies, "progress": run.progress, "message": run.message,
        "file_kind": run.file_kind, "file_url": f"{base}/api/agent/runs/{run.id}/file",
        "file_name": (f"order{job.order.number}-{Path(part.filename).stem}.svg" if run.file_kind == "svg"
                      else f"order{job.order.number}-{part.filename}"),
        "settings": run.settings or {},
        "job": {
            "id": job.id, "line": job.line, "quantity": job.quantity, "copies_done": job.copies_done,
            "material_id": job.quote_line.material_id, "order_number": job.order.number,
            "part_name": part.filename, "geometry": part.geometry,
        },
    }


def board_feed(db: Session, now: datetime | None = None) -> dict:
    """Everything the shop-floor HUD shows: each machine's status, current run and queue,
    a rough schedule from the quoted machine minutes, and orders by due date.

    The schedule runs each machine's queue back to back from now, earliest due first.
    It ignores shop hours and operator time, so read it as "if we kept going"."""
    from .models import Order, OrderEvent

    now = now or datetime.now(timezone.utc)
    profile = services.get_profile(db)
    states = machine_states(db)
    jobs = db.scalars(select(Job).where(Job.state.in_(("queued", "sent", "running", "failed", "review")))).all()

    def due(job: Job) -> datetime | None:
        paid = _aware(job.order.paid_at)
        return paid + timedelta(days=job.order.lead_days) if paid else None

    def minutes_each(job: Job) -> float:
        price = job.quote_line.price or {}
        return float(price.get("machine_minutes") or 0)

    def job_row(job: Job) -> dict:
        d = due(job)
        return {
            "job_id": job.id, "order": job.order.number, "part": job.quote_line.part.filename,
            "material": job.quote_line.material_id or "", "quantity": job.quantity,
            "made": job.copies_done, "state": job.state, "label": job.label, "note": job.note,
            "due": d.isoformat() if d else None, "minutes_each": round(minutes_each(job), 1),
        }

    machines = []
    for m in profile.data["machines"]:
        mine = [j for j in jobs if j.machine_id == m["id"] and j.state != "review"]
        clock = now
        current = None
        for job in mine:
            run = job.active_run
            if run is not None and job.state in ("sent", "running"):
                total = minutes_each(job) * run.copies
                left = total * (1 - (run.progress or 0) / 100)
                started = _aware(run.started_at)
                current = {
                    **job_row(job), "run_id": run.id, "run_state": run.state, "run_label": run.label,
                    "progress": run.progress, "message": run.message, "copies": run.copies,
                    "started": started.isoformat() if started else None,
                    "minutes_left": round(left, 1),
                }
                clock = now + timedelta(minutes=left)
                break
        queue = []
        waiting = [j for j in mine if current is None or j.id != current["job_id"]]
        waiting.sort(key=lambda j: (j.state == "failed", due(j) or now + timedelta(days=365), j.updated_at))
        for job in waiting:
            row = job_row(job)
            mins = minutes_each(job) * max(0, job.quantity - job.copies_done)
            row["start"] = clock.isoformat()
            clock = clock + timedelta(minutes=mins)
            row["end"] = clock.isoformat()
            d = due(job)
            row["late"] = bool(d and clock > d)
            queue.append(row)
        st = states.get(m["id"])
        machines.append({
            "id": m["id"], "name": m["name"], "line": m["line"],
            "line_label": LINE_LABELS.get(m["line"], m["line"]),
            "state": st["state"] if st else "manual", "detail": st["detail"] if st else "",
            "progress": st["progress"] if st else None, "online": bool(st and st["online"]),
            "current": current, "queue": queue, "busy_until": clock.isoformat(),
            "queued_minutes": round((clock - now).total_seconds() / 60, 1),
        })

    review = [job_row(j) for j in jobs if j.state == "review"]
    awaiting = [{"order": o.number, "customer": o.name, "total_cents": o.total_cents, "parts": len(o.quote.lines)}
                for o in db.scalars(select(Order).where(Order.status == "awaiting_payment").order_by(Order.number))]
    open_orders = db.scalars(select(Order).where(Order.status.in_(("in_queue", "making", "finishing")))).all()
    orders = []
    for o in open_orders:
        paid = _aware(o.paid_at)
        d = paid + timedelta(days=o.lead_days) if paid else None
        made = sum(1 for j in o.jobs if j.state == "done")
        orders.append({"order": o.number, "customer": o.name, "status": o.status_label,
                       "due": d.isoformat() if d else None, "late": bool(d and d < now),
                       "jobs_done": made, "jobs": len(o.jobs)})
    orders.sort(key=lambda o: o["due"] or "9999")
    day_ago = now - timedelta(hours=24)
    finished = db.scalars(
        select(JobRun).where(JobRun.state.in_(RUN_FINAL_STATES)).order_by(JobRun.finished_at.desc()).limit(12)
    ).all()
    events = [{
        "at": _aware(r.finished_at).isoformat() if r.finished_at else None, "state": r.state,
        "machine_id": r.machine_id, "order": r.job.order.number, "part": r.job.quote_line.part.filename,
        "copies": r.copies, "message": r.message[:200],
    } for r in finished if r.finished_at and _aware(r.finished_at) >= day_ago]
    return {
        "now": now.isoformat(), "machines": machines, "review": review, "orders": orders, "events": events,
        "awaiting_payment": awaiting,
        "totals": {
            "queued": sum(len(m["queue"]) for m in machines) + len(review),
            "running": sum(1 for m in machines if m["current"]),
            "late": sum(1 for o in orders if o["late"]),
            "done_24h": sum(1 for e in events if e["state"] == "done"),
            "to_ship": sum(1 for o in open_orders if o.status == "finishing"),
        },
    }


# ---- web routes ------------------------------------------------------------


def register(app: FastAPI, render, get_db, cfg, require_admin) -> None:
    admin = [Depends(require_admin)]

    def require_agent(request: Request) -> str:
        if not cfg.agent_token:
            raise HTTPException(503, "The shop agent API is off. Set PYSLATE_AGENT_TOKEN to turn it on.")
        auth = request.headers.get("authorization", "")
        token = auth[7:] if auth.lower().startswith("bearer ") else ""
        if not token or not secrets.compare_digest(token.encode(), cfg.agent_token.encode()):
            raise HTTPException(401, "Wrong agent token")
        return (request.headers.get("x-agent-name") or "shop-agent")[:64]

    def get_job(db: Session, job_id: str) -> Job:
        job = db.get(Job, job_id)
        if job is None:
            raise HTTPException(404)
        return job

    def get_run(db: Session, run_id: str) -> JobRun:
        run = db.get(JobRun, run_id)
        if run is None:
            raise HTTPException(404)
        return run

    def back(to: str) -> RedirectResponse:
        return RedirectResponse(to if to.startswith("/admin") else "/admin/production", status_code=303)

    # -- production board --

    def board(db: Session) -> dict:
        profile = services.get_profile(db)
        jobs = db.scalars(select(Job).where(Job.state != "done").order_by(Job.updated_at)).all()
        recent = db.scalars(select(Job).where(Job.state == "done").order_by(Job.updated_at.desc()).limit(20)).all()
        states = machine_states(db)
        lanes: dict[str, dict] = {}
        for m in profile.data["machines"]:
            lanes[m["id"]] = {"machine": m, "jobs": [], "status": states.get(m["id"])}
        review = {"machine": {"id": REVIEW_LANE, "name": "Needs a machine", "line": REVIEW_LANE}, "jobs": [], "status": None}
        for job in jobs:
            lane = lanes.get(job.machine_id or "") if job.state != "review" else None
            (lane or review)["jobs"].append(job)
        groups = []
        for line in LINES:
            ls = [lane for lane in lanes.values() if lane["machine"]["line"] == line]
            if ls:
                groups.append({"line": line, "label": LINE_LABELS[line], "lanes": ls,
                               "count": sum(len(lane["jobs"]) for lane in ls)})
        agents = sorted({s["agent"] for s in states.values() if s["online"] and s["agent"]})
        from .models import Order

        awaiting = db.scalars(select(Order).where(Order.status == "awaiting_payment").order_by(Order.number)).all()
        return {"awaiting": awaiting, "groups": groups, "review": review, "recent": recent, "profile": profile,
                "agents": agents, "agent_enabled": bool(cfg.agent_token)}

    @app.get("/admin/production", dependencies=admin)
    def production_page(request: Request, line: str = "", db: Session = Depends(get_db)):
        ctx = board(db)
        return render(
            request, "admin/production.html", **ctx, only_line=line if line in LINES else "",
            machines_for=lambda job: machines_for(ctx["profile"], job),
            default_settings=lambda job: default_settings(ctx["profile"], job),
            file_kinds=file_kinds, sheet_lines=SHEET_LINES, job_labels=JOB_LABELS,
            error=request.query_params.get("error", "")[:300],
        )

    @app.get("/admin/production/status.json", dependencies=admin)
    def production_status(db: Session = Depends(get_db)):
        runs = db.scalars(select(JobRun).where(JobRun.state.in_(RUN_ACTIVE_STATES))).all()
        return JSONResponse({
            "machines": machine_states(db),
            "runs": {r.id: {"state": r.state, "label": r.label, "progress": r.progress, "message": r.message}
                     for r in runs},
            "active": sorted(r.id for r in runs),
        })

    def _fail(to: str, exc: Exception) -> RedirectResponse:
        from urllib.parse import quote

        sep = "&" if "?" in to else "?"
        return back(f"{to}{sep}error={quote(str(exc))}")

    @app.post("/admin/job/{job_id}/send", dependencies=admin)
    async def send(request: Request, job_id: str, db: Session = Depends(get_db)):
        form = await request.form()
        job = get_job(db, job_id)
        to = str(form.get("back", "/admin/production"))
        settings = {}
        for key in ("speed_mm_s", "passes", "power_pct", "thickness_mm"):
            raw = str(form.get(key, "")).strip()
            if raw:
                try:
                    settings[key] = float(raw)
                except ValueError:
                    return _fail(to, ProductionError(f"{key} must be a number"))
        for key in ("notes", "slicer_profile"):
            raw = str(form.get(key, "")).strip()
            if raw:
                settings[key] = raw[:500]
        settings["material"] = default_settings(services.get_profile(db), job).get("material", "")
        try:
            copies = int(str(form.get("copies", job.quantity)) or job.quantity)
            send_job(cfg, db, job, str(form.get("machine_id", "")), copies, settings)
        except (ValueError, services.ServiceError) as exc:
            db.rollback()
            return _fail(to, exc)
        return back(to)

    @app.post("/admin/job/{job_id}/assign", dependencies=admin)
    def assign(job_id: str, machine_id: str = Form(...), back_to: str = Form("/admin/production", alias="back"),
               db: Session = Depends(get_db)):
        try:
            assign_machine(db, get_job(db, job_id), machine_id)
        except services.ServiceError as exc:
            return _fail(back_to, exc)
        return back(back_to)

    @app.get("/admin/job/{job_id}/file/{kind}", dependencies=admin)
    def download(job_id: str, kind: str, machine_id: str = "", copies: int = 0, db: Session = Depends(get_db)):
        job = get_job(db, job_id)
        try:
            path, name, _ = job_file(cfg, db, job, kind, machine_id or None, copies or None)
        except (services.ServiceError, jobfiles.JobFileError) as exc:
            raise HTTPException(422, str(exc)) from exc
        return FileResponse(path, filename=name)

    @app.post("/admin/run/{run_id}/cancel", dependencies=admin)
    def cancel(run_id: str, back_to: str = Form("/admin/production", alias="back"), db: Session = Depends(get_db)):
        try:
            cancel_run(db, get_run(db, run_id))
        except services.ServiceError as exc:
            return _fail(back_to, exc)
        return back(back_to)

    @app.post("/admin/run/{run_id}/close", dependencies=admin)
    def close(run_id: str, state: str = Form(...), message: str = Form(""),
              back_to: str = Form("/admin/production", alias="back"), db: Session = Depends(get_db)):
        try:
            close_run(db, get_run(db, run_id), state, message)
        except services.ServiceError as exc:
            return _fail(back_to, exc)
        return back(back_to)

    # -- shop agent setup page --

    @app.get("/admin/agent", dependencies=admin)
    def agent_page(request: Request, db: Session = Depends(get_db)):
        profile = services.get_profile(db)
        return render(request, "admin/agent.html", token=cfg.agent_token, public_url=cfg.public_url,
                      states=machine_states(db), machines=profile.data["machines"],
                      config=sample_config(cfg.public_url, profile.data["machines"]))

    @app.get("/admin/agent/download", dependencies=admin)
    def agent_download(db: Session = Depends(get_db)):
        import json

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(AGENT_DIR.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix in (".py", ".md", ".txt", ".bat"):
                    # The starter script and README sit next to agent.json; the code in shop_agent/.
                    top = path.suffix == ".bat" or path.name == "README.md"
                    z.write(path, path.name if top else Path("shop_agent") / path.relative_to(AGENT_DIR))
            config = sample_config(cfg.public_url, services.get_profile(db).data["machines"])
            config["token"] = cfg.agent_token or "PASTE-THE-AGENT-TOKEN-HERE"
            z.writestr("agent.json", json.dumps(config, indent=2))
        return Response(buf.getvalue(), media_type="application/zip",
                        headers={"Content-Disposition": 'attachment; filename="pyslate-shop-agent.zip"'})

    # -- shop agent API --

    @app.post("/api/agent/heartbeat")
    async def agent_heartbeat(request: Request, db: Session = Depends(get_db)):
        agent = require_agent(request)
        body = await request.json()
        machines = body.get("machines") if isinstance(body, dict) else None
        if not isinstance(machines, list):
            raise HTTPException(422, "machines must be a list")
        heartbeat(db, agent, [m for m in machines if isinstance(m, dict)])
        return {"ok": True, "server_time": utcnow().isoformat()}

    @app.get("/api/agent/runs")
    def agent_runs(request: Request, machines: str = "", db: Session = Depends(get_db)):
        require_agent(request)
        ids = [m for m in machines.split(",") if m][:100]
        q = select(JobRun).where(JobRun.state == "pending").order_by(JobRun.created_at)
        if ids:
            q = q.where(JobRun.machine_id.in_(ids))
        return {"runs": [run_json(r) for r in db.scalars(q).all()]}

    @app.get("/api/agent/board")
    def agent_board(request: Request, db: Session = Depends(get_db)):
        """Read-only feed for the shop-floor HUD (python -m shop_agent hud)."""
        require_agent(request)
        return board_feed(db)

    @app.get("/admin/hud", dependencies=admin)
    def admin_hud(request: Request, line: str = "", title: str = ""):
        """The shop-floor heads-up display in the browser: same feed as the terminal HUD."""
        return render(request, "admin/hud.html", line=line[:20], title=(title or "SHOP FLOOR")[:40].upper())

    @app.get("/admin/production/board.json", dependencies=admin)
    def admin_board(db: Session = Depends(get_db)):
        return board_feed(db)

    @app.get("/api/agent/runs/{run_id}")
    def agent_run(request: Request, run_id: str, db: Session = Depends(get_db)):
        require_agent(request)
        return run_json(get_run(db, run_id))

    @app.post("/api/agent/runs/{run_id}/claim")
    def agent_claim(request: Request, run_id: str, db: Session = Depends(get_db)):
        agent = require_agent(request)
        run = get_run(db, run_id)
        try:
            claim_run(db, run, agent)
        except services.ServiceError as exc:
            raise HTTPException(409, str(exc)) from exc
        return run_json(run)

    @app.get("/api/agent/runs/{run_id}/file")
    def agent_file(request: Request, run_id: str, db: Session = Depends(get_db)):
        require_agent(request)
        run = get_run(db, run_id)
        try:
            path, name, _ = job_file(cfg, db, run.job, run.file_kind, run.machine_id, run.copies)
        except (services.ServiceError, jobfiles.JobFileError) as exc:
            raise HTTPException(422, str(exc)) from exc
        return FileResponse(path, filename=name)

    @app.post("/api/agent/runs/{run_id}/update")
    async def agent_run_update(request: Request, run_id: str, db: Session = Depends(get_db)):
        require_agent(request)
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(422)
        run = get_run(db, run_id)
        try:
            agent_update(db, run, str(body.get("state", "")), body.get("progress"), str(body.get("message", "")))
        except services.ServiceError as exc:
            raise HTTPException(409, str(exc)) from exc
        return run_json(run)


# Which agent driver suits each machine, for the sample config.
DRIVER_HINTS = {
    "bambu": {"driver": "bambu", "host": "PRINTER-IP", "serial": "PRINTER-SERIAL", "access_code": "LAN-ACCESS-CODE",
              "slicer": {"command": ["C:/Program Files/Bambu Studio/bambu-studio.exe", "--slice", "0",
                                     "--export-3mf", "{output}", "{input}"], "output_ext": ".gcode.3mf"}},
    "a8s": {"driver": "marlin", "port": "COM4", "baud": 115200,
            "slicer": {"command": ["C:/Program Files/Prusa3D/PrusaSlicer/prusa-slicer-console.exe", "--export-gcode",
                                   "--load", "C:/Pyslate/a8s.ini", "--output", "{output}", "{input}"],
                       "output_ext": ".gcode"}},
}


def sample_config(public_url: str, machines: list[dict]) -> dict:
    out = []
    for m in machines:
        if m["id"] in DRIVER_HINTS:
            entry = {"id": m["id"], **DRIVER_HINTS[m["id"]]}
        elif m["line"] == "laser":
            entry = {"id": m["id"], "driver": "xtool", "host": "", "mode": "studio",
                     "folder": f"C:/Pyslate/jobs/{m['id']}",
                     "open": ["%LOCALAPPDATA%/Programs/xTool Studio/xTool Studio.exe", "{file}"]}
        else:
            entry = {"id": m["id"], "driver": "folder", "folder": f"C:/Pyslate/jobs/{m['id']}"}
        # Laser hand-off works with no setup; turn the others on once their details are filled in.
        entry["enabled"] = entry["driver"] == "xtool"
        out.append(entry)
    return {"server": public_url, "token": "", "name": "yaeger", "poll_seconds": 10, "machines": out}
