"""Quote, order and job operations, kept apart from the web layer so they are easy to test."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import geometry as geo
from .catalog import REQUEST_SERVICES, REQUEST_STATES
from .models import (
    JOB_TRANSITIONS, Job, Order, OrderEvent, Part, Quote, QuoteLine, ServiceRequest, Setting, new_id, utcnow,
)
from .pricing import price_line, total_quote
from .routing import REVIEW, compatible_materials, default_material, route
from .shop import Profile, default_profile, validate_profile

PROFILE_KEY = "shop_profile"
MAX_QUANTITY = 10_000
FIRST_ORDER_NUMBER = 1001


PART_VERBS = {"print": "Printing", "laser": "Cutting", "cnc": "Machining", "router": "Routing",
              "plasma": "Cutting", "molding": "Molding"}


class ServiceError(ValueError):
    pass


# ---- shop profile -------------------------------------------------------


def _with_new_machines(data: dict) -> dict:
    """Add machines and materials that shipped after the owner saved their profile
    (e.g. the F2, metal engraving, the Tormach).

    Each default is added once; "known_machine_ids" / "known_material_ids" record which
    ones the owner has seen, so one they delete later stays deleted. Missing top-level
    settings are filled from the defaults.
    """
    base = default_profile()
    data = {**{k: v for k, v in base.items() if k not in ("machines", "materials")}, **data}
    for key, known_key in (("machines", "known_machine_ids"), ("materials", "known_material_ids")):
        items = list(data.get(key, []))
        known = set(data.get(known_key) or [m["id"] for m in items])
        have = {m["id"] for m in items}
        items += [m for m in base[key] if m["id"] not in known and m["id"] not in have]
        data[key] = items
        data[known_key] = sorted(known | {m["id"] for m in base[key]})
    return data


def get_profile(db: Session) -> Profile:
    row = db.get(Setting, PROFILE_KEY)
    return Profile(_with_new_machines(dict(row.value)) if row else default_profile())


def save_profile(db: Session, data: dict) -> None:
    problems = validate_profile(data)
    if problems:
        raise ServiceError("; ".join(problems))
    row = db.get(Setting, PROFILE_KEY)
    if row:
        row.value = data
    else:
        db.add(Setting(key=PROFILE_KEY, value=data))
    db.commit()


# ---- parts and quotes ---------------------------------------------------


def _safe_filename(name: str) -> str:
    base = Path(name or "part").name
    return re.sub(r"[^A-Za-z0-9._ -]", "_", base)[:200] or "part"


def store_part(db: Session, upload_dir: Path, filename: str, src: Path) -> Part:
    """Analyse an uploaded file and save it as a part. `src` is a temp file the caller owns."""
    clean = _safe_filename(filename)
    ext = Path(clean).suffix.lower()
    if ext not in geo.SUPPORTED_EXTS:
        raise ServiceError(f"{clean}: Pyslate accepts {', '.join(sorted(geo.SUPPORTED_EXTS))} files")
    part = Part(id=new_id(), filename=clean, stored_name="", geometry={})
    stored = f"{part.id}{ext}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / stored
    shutil.copyfile(src, dest)
    try:
        g = geo.analyze(dest)
        preview = None
        if ext in geo.MESH_EXTS:
            preview = f"{part.id}.preview.stl"
            geo.export_preview_stl(dest, upload_dir / preview)
    except geo.GeometryError as exc:
        dest.unlink(missing_ok=True)
        raise ServiceError(f"{clean}: {exc}") from exc
    part.stored_name = stored
    part.preview_name = preview
    part.geometry = g.to_dict()
    db.add(part)
    return part


def add_part_to_quote(db: Session, quote: Quote, part: Part) -> QuoteLine:
    profile = get_profile(db)
    g = geo.PartGeometry.from_dict(part.geometry)
    line = QuoteLine(part=part, position=len(quote.lines), material_id=default_material(g, profile), quantity=1, line=REVIEW)
    quote.lines.append(line)
    reprice_line(line, profile)
    return line


def reprice_line(line: QuoteLine, profile: Profile) -> None:
    g = geo.PartGeometry.from_dict(line.part.geometry)
    r = route(g, line.material_id, profile)
    line.line = r.line
    line.machine_id = r.machine_id
    line.route_reason = r.reason
    p = price_line(g, line.material_id, r, line.quantity, profile) if line.material_id else None
    line.price = p.to_dict() if p else None


def update_line(db: Session, line: QuoteLine, material_id: str | None, quantity: int) -> None:
    if line.quote.order is not None:
        raise ServiceError("This quote has already been ordered")
    profile = get_profile(db)
    if not 1 <= quantity <= MAX_QUANTITY:
        raise ServiceError(f"Quantity must be between 1 and {MAX_QUANTITY}")
    allowed = {m["id"] for m in compatible_materials(geo.PartGeometry.from_dict(line.part.geometry), profile)}
    if material_id and material_id not in allowed:
        raise ServiceError("That material does not suit this part")
    line.material_id = material_id
    line.quantity = quantity
    reprice_line(line, profile)
    db.commit()


def quote_summary(db: Session, quote: Quote):
    profile = get_profile(db)
    totals = [line.price["total"] for line in quote.lines if line.price]
    return total_quote(totals, quote.lead_tier, profile)


def quote_is_orderable(quote: Quote) -> bool:
    return bool(quote.lines) and all(line.price for line in quote.lines)


# ---- orders -------------------------------------------------------------


def place_order(db: Session, quote: Quote, email: str, name: str, address: str, notes: str = "") -> Order:
    if quote.order is not None:
        return quote.order
    if not quote_is_orderable(quote):
        raise ServiceError("Every part needs a price before ordering. Remove or change parts marked for review.")
    if "@" not in email or len(email) > 255:
        raise ServiceError("Enter a valid email address")
    if not name.strip() or not address.strip():
        raise ServiceError("Name and shipping address are required")
    # Re-price with today's rates so a stale page cannot set the price.
    profile = get_profile(db)
    for line in quote.lines:
        reprice_line(line, profile)
    if not quote_is_orderable(quote):
        raise ServiceError("A part can no longer be made as quoted. Please review the quote.")
    summary = quote_summary(db, quote)
    number = (db.scalar(select(func.max(Order.number))) or FIRST_ORDER_NUMBER - 1) + 1
    order = Order(
        number=number,
        quote=quote,
        email=email.strip(),
        name=name.strip()[:255],
        shipping_address=address.strip(),
        notes=notes.strip(),
        total_cents=int(round(summary.total * 100)),
        lead_days=summary.lead_days,
    )
    order.events.append(OrderEvent(status="awaiting_payment", note="Order placed"))
    db.add(order)
    db.commit()
    return order


def mark_paid(db: Session, order: Order, note: str = "Payment received") -> None:
    """Record payment and put one job per quote line into the queue. Safe to call twice."""
    if order.status != "awaiting_payment":
        return
    order.status = "in_queue"
    order.paid_at = utcnow()
    order.events.append(OrderEvent(status="paid", note=note))
    order.events.append(OrderEvent(status="in_queue", note="Parts added to the production queue"))
    for line in order.quote.lines:
        order.jobs.append(
            Job(quote_line=line, line=line.line, machine_id=line.machine_id, quantity=line.quantity, state="queued")
        )
    db.commit()


def set_order_status(db: Session, order: Order, status: str, note: str = "", tracking: str = "") -> None:
    allowed = {"making", "finishing", "shipped", "delivered", "cancelled"}
    if status not in allowed:
        raise ServiceError(f"Status must be one of {', '.join(sorted(allowed))}")
    if order.status == "awaiting_payment" and status != "cancelled":
        raise ServiceError("Mark the order paid first")
    order.status = status
    if tracking:
        order.tracking = tracking[:255]
    order.events.append(OrderEvent(status=status, note=note))
    db.commit()


def move_job(db: Session, job: Job, new_state: str, note: str = "") -> None:
    if new_state not in JOB_TRANSITIONS.get(job.state, set()):
        raise ServiceError(f"A {job.state} job cannot move to {new_state}")
    old_state = job.state
    job.state = new_state
    if note:
        job.note = note
    order = job.order
    states = {j.state for j in order.jobs}
    part = job.quote_line.part.filename
    if new_state == "running" and order.status in ("paid", "in_queue"):
        order.status = "making"
        order.events.append(OrderEvent(status="making", note="Production started"))
    # Each part's journey on the customer's order page: started on which machine, and made.
    if new_state == "running" and old_state in ("queued", "sent"):
        machine = get_profile(db).machine(job.machine_id or "") or {}
        verb = PART_VERBS.get(job.line, "Making")
        order.events.append(OrderEvent(status=order.status, note=f"{part}: {verb.lower()} on the {machine.get('name', 'shop floor')}"))
    elif new_state == "done":
        order.events.append(OrderEvent(status=order.status, note=f"{part}: made, {job.quantity} of {job.quantity}"))
    if states == {"done"} and order.status in ("in_queue", "making"):
        order.status = "finishing"
        order.events.append(OrderEvent(status="finishing", note="All parts made; finishing and packing"))
    db.commit()


# ---- design and documentation requests ----------------------------------

REQUEST_FILE_EXTS = geo.SUPPORTED_EXTS | {
    ".pdf", ".png", ".jpg", ".jpeg", ".json", ".step", ".stp", ".blend", ".zip", ".svg", ".txt", ".csv", ".xlsx", ".docx",
}
FIRST_REQUEST_NUMBER = 501


def create_service_request(
    db: Session, upload_dir: Path, service: str, name: str, email: str, description: str,
    company: str = "", phone: str = "", budget: str = "", needed_by: str = "",
    files: list[tuple[str, Path]] | None = None,
) -> ServiceRequest:
    if service not in REQUEST_SERVICES:
        raise ServiceError("Choose a service")
    if not name.strip() or "@" not in email or len(email) > 255:
        raise ServiceError("Enter your name and a valid email address")
    if len(description.strip()) < 20:
        raise ServiceError("Tell us a little more about the project (at least a couple of sentences)")
    number = (db.scalar(select(func.max(ServiceRequest.number))) or FIRST_REQUEST_NUMBER - 1) + 1
    req = ServiceRequest(
        id=new_id(), number=number, service=service, name=name.strip()[:255], email=email.strip(),
        company=company.strip()[:255], phone=phone.strip()[:64], description=description.strip()[:20000],
        budget=budget.strip()[:64], needed_by=needed_by.strip()[:64], files=[],
    )
    for original, _ in files or []:
        if Path(_safe_filename(original)).suffix.lower() not in REQUEST_FILE_EXTS:
            raise ServiceError(f"{_safe_filename(original)}: this file type is not accepted")
    saved = []
    target_dir = upload_dir / "requests"
    target_dir.mkdir(parents=True, exist_ok=True)
    for original, src in files or []:
        clean = _safe_filename(original)
        ext = Path(clean).suffix.lower()
        stored = f"{req.id}-{len(saved)}{ext}"
        shutil.copyfile(src, target_dir / stored)
        saved.append({"name": clean, "stored": stored})
    req.files = saved
    db.add(req)
    db.commit()
    return req


def update_service_request(db: Session, req: ServiceRequest, status: str, shop_notes: str) -> None:
    if status not in REQUEST_STATES:
        raise ServiceError("Unknown status")
    req.status = status
    req.shop_notes = shop_notes.strip()[:20000]
    db.commit()
