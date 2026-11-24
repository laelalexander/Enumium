"""Shop operations after production: customers, packing and shipping."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import quote as urlquote

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import barcode, services
from .models import (
    Customer, CustomerFlag, CustomerOrder, Order, OrderEvent, SavedDesign, SavedQuote, Shipment, utcnow,
)

CARRIERS = {
    "usps": ("USPS", "https://tools.usps.com/go/TrackConfirmAction?tLabels={t}"),
    "ups": ("UPS", "https://www.ups.com/track?tracknum={t}"),
    "fedex": ("FedEx", "https://www.fedex.com/fedextrack/?trknbr={t}"),
    "dhl": ("DHL", "https://www.dhl.com/us-en/home/tracking/tracking-express.html?submit=1&tracking-id={t}"),
    "pickup": ("Local pickup", None),
    "delivery": ("Hand delivery", None),
}
PAID_STATES = ("in_queue", "making", "finishing", "shipped", "delivered")


def tracking_url(carrier: str, tracking: str) -> str | None:
    pattern = CARRIERS.get(carrier, ("", None))[1]
    return pattern.format(t=urlquote(tracking.strip())) if pattern and tracking.strip() else None


def carrier_name(carrier: str) -> str:
    return CARRIERS.get(carrier, (carrier or "", None))[0]


class OpsError(services.ServiceError):
    pass


# ---- customers -----------------------------------------------------------------


def customer_rows(db: Session, q: str = "") -> list[dict]:
    """Every buyer: accounts, plus guests who ordered without one, keyed by email."""
    rows: dict[str, dict] = {}
    flags = {f.customer_id: f for f in db.scalars(select(CustomerFlag)).all()}
    for c in db.scalars(select(Customer)).all():
        rows[c.email.lower()] = {"email": c.email, "name": c.name, "company": c.company, "account": c,
                                 "disabled": bool(flags.get(c.id) and flags[c.id].disabled),
                                 "orders": 0, "spent_cents": 0, "last": None, "open": 0}
    linked = {(co.order_id): co.customer_id for co in db.scalars(select(CustomerOrder)).all()}
    accounts = {c["account"].id: key for key, c in rows.items() if c["account"]}
    for o in db.scalars(select(Order)).all():
        key = accounts.get(linked.get(o.id, ""), o.email.lower())
        row = rows.setdefault(key, {"email": o.email, "name": o.name, "company": "", "account": None,
                                    "disabled": False, "orders": 0, "spent_cents": 0, "last": None, "open": 0})
        row["orders"] += 1
        if not row["name"]:
            row["name"] = o.name
        if o.status in PAID_STATES:
            row["spent_cents"] += o.total_cents
        if o.status not in ("delivered", "cancelled"):
            row["open"] += 1
        created = o.created_at if o.created_at.tzinfo else o.created_at.replace(tzinfo=timezone.utc)
        if row["last"] is None or created > row["last"]:
            row["last"] = created
    out = list(rows.values())
    if q:
        ql = q.lower().strip()
        out = [r for r in out if ql in r["email"].lower() or ql in (r["name"] or "").lower()
               or ql in (r["company"] or "").lower()]
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    out.sort(key=lambda r: (r["last"] or epoch, r["email"]), reverse=True)
    return out


def customer_orders(db: Session, email: str, account: Customer | None) -> list[Order]:
    ids = set()
    if account is not None:
        ids |= {co.order_id for co in db.scalars(select(CustomerOrder).where(CustomerOrder.customer_id == account.id))}
    found = db.scalars(select(Order).where(func.lower(Order.email) == email.lower())).all()
    ids |= {o.id for o in found}
    if not ids:
        return []
    return db.scalars(select(Order).where(Order.id.in_(ids)).order_by(Order.number.desc())).all()


# ---- packing and shipping -----------------------------------------------------------


def shipment_for(db: Session, order: Order) -> Shipment:
    s = db.get(Shipment, order.id)
    if s is None:
        s = Shipment(order_id=order.id)
        db.add(s)
    return s


def mark_packed(db: Session, order: Order, packages: int, weight_g: int | None, dims: str, notes: str) -> None:
    if order.status not in ("finishing", "making", "in_queue"):
        raise OpsError("Only orders still in the shop can be packed")
    if not 1 <= packages <= 50:
        raise OpsError("Packages must be between 1 and 50")
    s = shipment_for(db, order)
    s.packages, s.weight_g, s.dims_mm, s.notes = packages, weight_g, dims.strip()[:64], notes.strip()[:2000]
    s.packed_at = utcnow()
    if order.status != "finishing":
        order.status = "finishing"
    order.events.append(OrderEvent(status="finishing", note=f"Packed in {packages} box{'es' if packages > 1 else ''}"))
    db.commit()


def unpack(db: Session, order: Order) -> None:
    s = db.get(Shipment, order.id)
    if s is None or order.status != "finishing":
        raise OpsError("This order isn't waiting to ship")
    s.packed_at = None
    db.commit()


def mark_shipped(db: Session, order: Order, carrier: str, service: str, tracking: str) -> None:
    if carrier not in CARRIERS:
        raise OpsError("Choose a carrier")
    if order.status != "finishing":
        raise OpsError("Pack the order before shipping it")
    if CARRIERS[carrier][1] and not tracking.strip():
        raise OpsError(f"Enter the {carrier_name(carrier)} tracking number")
    s = shipment_for(db, order)
    if s.packed_at is None:
        s.packed_at = utcnow()
    s.carrier, s.service, s.tracking = carrier, service.strip()[:64], tracking.strip()[:255]
    s.shipped_at = utcnow()
    label = carrier_name(carrier) + (f" {s.service}" if s.service else "")
    verb = "Ready for pickup" if carrier == "pickup" else "Out for delivery" if carrier == "delivery" else f"Shipped with {label}"
    services.set_order_status(db, order, "shipped", verb, s.tracking)


def mark_delivered(db: Session, order: Order) -> None:
    if order.status != "shipped":
        raise OpsError("Only shipped orders can be marked delivered")
    s = shipment_for(db, order)
    s.delivered_at = utcnow()
    note = "Picked up" if s.carrier == "pickup" else "Delivered"
    services.set_order_status(db, order, "delivered", note)


def shipping_board(db: Session) -> dict:
    shipments = {s.order_id: s for s in db.scalars(select(Shipment)).all()}
    finishing = db.scalars(select(Order).where(Order.status == "finishing").order_by(Order.paid_at)).all()
    to_pack = [o for o in finishing if not (shipments.get(o.id) and shipments[o.id].packed_at)]
    packed = [o for o in finishing if shipments.get(o.id) and shipments[o.id].packed_at]
    shipped = db.scalars(select(Order).where(Order.status == "shipped").order_by(Order.number.desc()).limit(50)).all()
    since = utcnow() - timedelta(days=14)
    delivered = [o for o in db.scalars(select(Order).where(Order.status == "delivered")
                                       .order_by(Order.number.desc()).limit(50)).all()
                 if shipments.get(o.id) is None or shipments[o.id].delivered_at is None
                 or _aware(shipments[o.id].delivered_at) >= since]
    coming = db.scalars(select(Order).where(Order.status.in_(("in_queue", "making"))).order_by(Order.paid_at)).all()
    return {"to_pack": to_pack, "packed": packed, "shipped": shipped, "delivered": delivered[:20],
            "coming": coming, "shipments": shipments}


def _aware(dt):
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def due_date(order: Order):
    paid = _aware(order.paid_at)
    return paid + timedelta(days=order.lead_days) if paid else None


# ---- web routes -------------------------------------------------------------------------


def register(app: FastAPI, render, get_db, cfg, require_admin) -> None:
    admin = [Depends(require_admin)]
    ctx_common = {"carriers": CARRIERS, "tracking_url": tracking_url, "carrier_name": carrier_name,
                  "due_date": due_date, "now": lambda: datetime.now(timezone.utc)}

    def get_order(db: Session, number: int) -> Order:
        order = db.scalar(select(Order).where(Order.number == number))
        if order is None:
            raise HTTPException(404)
        return order

    def back(to: str, error: str = "") -> RedirectResponse:
        to = to if to.startswith("/admin") else "/admin/shipping"
        if error:
            to += ("&" if "?" in to else "?") + "error=" + urlquote(error)
        return RedirectResponse(to, status_code=303)

    # -- customers --

    @app.get("/admin/customers", dependencies=admin)
    def customers(request: Request, q: str = "", db: Session = Depends(get_db)):
        rows = customer_rows(db, q)
        return render(request, "admin/customers.html", rows=rows, q=q,
                      accounts=sum(1 for r in rows if r["account"]), guests=sum(1 for r in rows if not r["account"]))

    @app.get("/admin/customers/{email}", dependencies=admin)
    def customer_detail(request: Request, email: str, db: Session = Depends(get_db)):
        account = db.scalar(select(Customer).where(func.lower(Customer.email) == email.lower()))
        orders = customer_orders(db, email, account)
        if account is None and not orders:
            raise HTTPException(404)
        flag = db.get(CustomerFlag, account.id) if account else None
        saved = {
            "quotes": db.scalar(select(func.count()).select_from(SavedQuote).where(SavedQuote.customer_id == account.id)) if account else 0,
            "designs": db.scalar(select(func.count()).select_from(SavedDesign).where(SavedDesign.customer_id == account.id)) if account else 0,
        }
        spent = sum(o.total_cents for o in orders if o.status in PAID_STATES)
        return render(request, "admin/customer.html", email=email, account=account, orders=orders, flag=flag,
                      saved=saved, spent=spent, display_name=(account.name if account and account.name else
                                                       orders[0].name if orders else email),
                      error=request.query_params.get("error", "")[:300], saved_ok=request.query_params.get("saved") == "1")

    @app.post("/admin/customers/{email}", dependencies=admin)
    def customer_update(email: str, action: str = Form(...), shop_notes: str = Form(""), db: Session = Depends(get_db)):
        account = db.scalar(select(Customer).where(func.lower(Customer.email) == email.lower()))
        to = f"/admin/customers/{urlquote(email)}"
        if account is None:
            return back(to, "Guest buyers have no account to change")
        flag = db.get(CustomerFlag, account.id) or CustomerFlag(customer_id=account.id)
        db.add(flag)
        if action == "notes":
            flag.shop_notes = shop_notes.strip()[:20000]
        elif action == "signout":
            account.session_version += 1
        elif action == "close":
            flag.disabled = True
            account.session_version += 1
        elif action == "reopen":
            flag.disabled = False
        else:
            return back(to, "Unknown action")
        db.commit()
        return RedirectResponse(to + "?saved=1", status_code=303)

    # -- pack and ship --

    @app.get("/admin/shipping", dependencies=admin)
    def shipping(request: Request, db: Session = Depends(get_db)):
        return render(request, "admin/shipping.html", **shipping_board(db), **ctx_common,
                      error=request.query_params.get("error", "")[:300])

    @app.post("/admin/order/{number}/pack", dependencies=admin)
    def pack(number: int, packages: int = Form(1), weight_g: str = Form(""), dims: str = Form(""),
             notes: str = Form(""), back_to: str = Form("/admin/shipping", alias="back"), db: Session = Depends(get_db)):
        try:
            w = int(float(weight_g)) if weight_g.strip() else None
            mark_packed(db, get_order(db, number), packages, w, dims, notes)
        except ValueError as exc:
            return back(back_to, str(exc) if isinstance(exc, services.ServiceError) else "Weight must be a number")
        return back(back_to)

    @app.post("/admin/order/{number}/unpack", dependencies=admin)
    def unpack_route(number: int, back_to: str = Form("/admin/shipping", alias="back"), db: Session = Depends(get_db)):
        try:
            unpack(db, get_order(db, number))
        except services.ServiceError as exc:
            return back(back_to, str(exc))
        return back(back_to)

    @app.post("/admin/order/{number}/ship", dependencies=admin)
    def ship(number: int, carrier: str = Form(...), service: str = Form(""), tracking: str = Form(""),
             back_to: str = Form("/admin/shipping", alias="back"), db: Session = Depends(get_db)):
        try:
            mark_shipped(db, get_order(db, number), carrier, service, tracking)
        except services.ServiceError as exc:
            return back(back_to, str(exc))
        return back(back_to)

    @app.post("/admin/order/{number}/delivered", dependencies=admin)
    def delivered(number: int, back_to: str = Form("/admin/shipping", alias="back"), db: Session = Depends(get_db)):
        try:
            mark_delivered(db, get_order(db, number))
        except services.ServiceError as exc:
            return back(back_to, str(exc))
        return back(back_to)

    @app.get("/admin/order/{number}/labels", dependencies=admin)
    def labels(request: Request, number: int, size: str = "4x6", db: Session = Depends(get_db)):
        """Pyslate's own label for every box: ship-to, carrier, tracking and box barcodes."""
        order = get_order(db, number)
        s = db.get(Shipment, order.id)
        boxes = s.packages if s else 1
        tracking_svg = None
        if s and s.tracking:
            try:
                tracking_svg = barcode.svg(s.tracking, height=70, module=2, font_size=16)
            except barcode.BarcodeError:
                tracking_svg = None
        items = [{"n": n, "code": barcode.box_code(order.number, n, boxes),
                  "svg": barcode.svg(barcode.box_code(order.number, n, boxes), height=56, module=2, font_size=15)}
                 for n in range(1, boxes + 1)]
        return render(request, "admin/labels.html", order=order, shipment=s, boxes=items, count=boxes,
                      tracking_svg=tracking_svg, ship_from=services.get_profile(db).data.get("ship_from") or {},
                      size="letter" if size == "letter" else "4x6", **ctx_common)

    @app.get("/admin/barcode.svg", dependencies=admin)
    def barcode_svg(code: str):
        from fastapi.responses import Response

        try:
            return Response(barcode.svg(code[:80]), media_type="image/svg+xml")
        except barcode.BarcodeError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/admin/scan", dependencies=admin)
    def scan(request: Request, code: str = "", db: Session = Depends(get_db)):
        """Scan station: a handheld scanner types a box code (or order number) and Enter."""
        found = barcode.parse_code(code) if code.strip() else None
        order = None
        if code.strip() and found is None:
            # A carrier tracking number scanned off a box.
            order = db.scalar(select(Order).where(Order.tracking == code.strip()))
        elif found:
            order = db.scalar(select(Order).where(Order.number == found["order"]))
        missing = bool(code.strip()) and order is None
        return render(request, "admin/scan.html", code=code.strip(), found=found or {}, order=order,
                      shipment=db.get(Shipment, order.id) if order else None, missing=missing,
                      error=request.query_params.get("error", "")[:300], **ctx_common)

    @app.get("/admin/order/{number}/packing-slip", dependencies=admin)
    def packing_slip(request: Request, number: int, db: Session = Depends(get_db)):
        order = get_order(db, number)
        profile = services.get_profile(db)
        names = {ln.material_id: (profile.material(ln.material_id) or {}).get("name", ln.material_id)
                 for ln in order.quote.lines if ln.material_id}
        return render(request, "admin/packing_slip.html", order=order, shipment=db.get(Shipment, order.id),
                      material_names=names, **ctx_common)
