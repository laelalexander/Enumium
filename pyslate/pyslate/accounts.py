"""Customer accounts: sign in, a dashboard of orders and saved jobs, and settings.

Passwords are stored as scrypt hashes. Card details never touch Pyslate: saved cards
and payment methods live in Stripe and are managed through Stripe's customer portal.
Orders join an account when they are placed while signed in, or when the customer
adds one using the order's private link, so nobody can claim an order by email alone.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from collections import defaultdict, deque
from urllib.parse import quote as urlquote

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Customer, CustomerOrder, Order, Quote, SavedDesign, SavedQuote

COOKIE = "pyslate_customer"
SESSION_SECONDS = 30 * 24 * 3600
MIN_PASSWORD = 10
MAX_SAVED_DESIGNS = 200
MAX_DESIGN_BYTES = 600_000
LOGIN_WINDOW, LOGIN_MAX_FAILS = 15 * 60, 8


class AccountError(ValueError):
    pass


# ---- passwords ----

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, digest = stored.split("$")
        got = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p),
                             dklen=len(bytes.fromhex(digest)))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(got.hex(), digest)


def normalise_email(email: str) -> str:
    email = (email or "").strip().lower()
    if "@" not in email or len(email) > 255 or " " in email:
        raise AccountError("Enter a valid email address")
    return email


def safe_next(target: str | None, default: str = "/account") -> str:
    """Only allow redirects back into this site."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return default


def register(app: FastAPI, render, get_db, cfg) -> None:
    fails: dict[str, deque] = defaultdict(deque)

    # ---- session cookie: customer id, session version and expiry, signed ----

    def _mac(body: str) -> str:
        return hmac.new(cfg.secret_key.encode(), f"customer:{body}".encode(), hashlib.sha256).hexdigest()

    def _cookie_for(c: Customer) -> str:
        body = f"{c.id}.{c.session_version}.{int(time.time()) + SESSION_SECONDS}"
        return f"{body}.{_mac(body)}"

    def current_customer(request: Request, db: Session) -> Customer | None:
        raw = request.cookies.get(COOKIE) or ""
        parts = raw.split(".")
        if len(parts) != 4:
            return None
        cid, version, expires, mac = parts
        body = f"{cid}.{version}.{expires}"
        if not hmac.compare_digest(_mac(body), mac) or not expires.isdigit() or int(expires) < time.time():
            return None
        c = db.get(Customer, cid)
        if c is None or str(c.session_version) != version:
            return None
        return c

    app.state.current_customer = current_customer

    def require(request: Request, db: Session) -> Customer:
        c = current_customer(request, db)
        if c is None:
            raise HTTPException(303, headers={"Location": "/account/login?next=" + urlquote(request.url.path)})
        return c

    def signed_in(resp, c: Customer):
        resp.set_cookie(COOKIE, _cookie_for(c), httponly=True, samesite="lax", secure=cfg.secure_cookies,
                        max_age=SESSION_SECONDS)
        return resp

    def link_order(db: Session, c: Customer, order: Order) -> None:
        exists = db.get(CustomerOrder, (c.id, order.id))
        if exists is None:
            db.add(CustomerOrder(customer_id=c.id, order_id=order.id))
            db.commit()

    app.state.link_order = link_order

    def throttled(request: Request) -> bool:
        key = request.client.host if request.client else "?"
        q, now = fails[key], time.time()
        while q and q[0] < now - LOGIN_WINDOW:
            q.popleft()
        return len(q) >= LOGIN_MAX_FAILS

    def note_fail(request: Request) -> None:
        fails[request.client.host if request.client else "?"].append(time.time())

    # ---- sign up, sign in, sign out ----

    @app.get("/account/signup")
    def signup_page(request: Request, next: str = ""):
        return render(request, "account/signup.html", form={}, next=safe_next(next))

    @app.post("/account/signup")
    def signup(request: Request, email: str = Form(...), password: str = Form(...), name: str = Form(""),
               next: str = Form(""), db: Session = Depends(get_db)):
        form = {"email": email, "name": name}
        try:
            addr = normalise_email(email)
            if len(password) < MIN_PASSWORD:
                raise AccountError(f"Use a password of at least {MIN_PASSWORD} characters")
            if db.scalar(select(Customer).where(Customer.email == addr)):
                raise AccountError("There's already an account for that email. Sign in instead.")
        except AccountError as exc:
            return render(request, "account/signup.html", 400, errors=[str(exc)], form=form, next=safe_next(next))
        c = Customer(email=addr, password_hash=hash_password(password), name=name.strip()[:255])
        db.add(c)
        db.commit()
        return signed_in(RedirectResponse(safe_next(next), status_code=303), c)

    @app.get("/account/login")
    def login_page(request: Request, next: str = ""):
        return render(request, "account/login.html", form={}, next=safe_next(next))

    @app.post("/account/login")
    def login(request: Request, email: str = Form(...), password: str = Form(...), next: str = Form(""),
              db: Session = Depends(get_db)):
        ctx = {"form": {"email": email}, "next": safe_next(next)}
        if throttled(request):
            return render(request, "account/login.html", 429, errors=["Too many tries. Wait 15 minutes and try again."], **ctx)
        c = db.scalar(select(Customer).where(Customer.email == (email or "").strip().lower()))
        if c is None or not check_password(password, c.password_hash):
            note_fail(request)
            return render(request, "account/login.html", 401, errors=["That email and password don't match."], **ctx)
        return signed_in(RedirectResponse(safe_next(next), status_code=303), c)

    @app.post("/account/logout")
    def logout():
        resp = RedirectResponse("/", status_code=303)
        resp.delete_cookie(COOKIE)
        return resp

    # ---- dashboard ----

    @app.get("/account")
    def dashboard(request: Request, db: Session = Depends(get_db)):
        c = require(request, db)
        orders = db.scalars(
            select(Order).join(CustomerOrder, CustomerOrder.order_id == Order.id)
            .where(CustomerOrder.customer_id == c.id).order_by(Order.created_at.desc())
        ).all()
        quotes = db.scalars(select(SavedQuote).where(SavedQuote.customer_id == c.id)
                            .order_by(SavedQuote.saved_at.desc())).all()
        designs = db.scalars(select(SavedDesign).where(SavedDesign.customer_id == c.id)
                             .order_by(SavedDesign.saved_at.desc())).all()
        active = [o for o in orders if o.status not in ("delivered", "cancelled")]
        return render(request, "account/dashboard.html", customer=c, orders=orders, active=active,
                      quotes=quotes, designs=designs, saved=request.query_params.get("saved"))

    # ---- orders ----

    @app.post("/account/orders/add")
    def add_order(request: Request, number: int = Form(...), token: str = Form(...), db: Session = Depends(get_db)):
        c = require(request, db)
        order = db.scalar(select(Order).where(Order.number == number))
        if order is None or not secrets.compare_digest(order.access_token, token or ""):
            raise HTTPException(404, "Order not found")
        link_order(db, c, order)
        return RedirectResponse(f"/order/{order.number}?t={order.access_token}&added=1", status_code=303)

    # ---- saved quotes ----

    @app.post("/account/quotes/save")
    def save_quote(request: Request, token: str = Form(...), name: str = Form(""), db: Session = Depends(get_db)):
        c = require(request, db)
        q = db.scalar(select(Quote).where(Quote.token == token))
        if q is None:
            raise HTTPException(404, "Quote not found")
        existing = db.scalar(select(SavedQuote).where(SavedQuote.customer_id == c.id, SavedQuote.quote_id == q.id))
        if existing is None:
            label = name.strip() or ", ".join(ln.part.filename for ln in q.lines[:3]) or "Quote"
            db.add(SavedQuote(customer_id=c.id, quote_id=q.id, name=label[:255]))
            db.commit()
        return RedirectResponse(f"/quote/{q.token}?saved=1", status_code=303)

    @app.post("/account/quotes/{saved_id}/delete")
    def delete_quote(request: Request, saved_id: str, db: Session = Depends(get_db)):
        c = require(request, db)
        sq = db.get(SavedQuote, saved_id)
        if sq is None or sq.customer_id != c.id:
            raise HTTPException(404)
        db.delete(sq)
        db.commit()
        return RedirectResponse("/account#saved", status_code=303)

    # ---- saved studio designs ----

    @app.post("/account/designs")
    def save_design(request: Request, design: str = Form(...), name: str = Form(""), design_id: str = Form(""),
                    db: Session = Depends(get_db)):
        c = current_customer(request, db)
        if c is None:
            return JSONResponse({"error": "signin", "login": "/account/login?next=/studio"}, status_code=401)
        if len(design) > MAX_DESIGN_BYTES:
            return JSONResponse({"error": "This design is too large to save."}, status_code=400)
        try:
            data = json.loads(design)
            if not isinstance(data, dict) or not isinstance(data.get("shapes"), list) or not data["shapes"]:
                raise ValueError
        except ValueError:
            return JSONResponse({"error": "The design could not be read."}, status_code=400)
        keep = {k: data[k] for k in ("shapes", "machine", "material", "height", "quantity") if k in data}
        label = (name.strip() or "Untitled design")[:255]
        sd = db.get(SavedDesign, design_id) if design_id else None
        if sd is not None and sd.customer_id == c.id:
            sd.design, sd.name = keep, label
        else:
            count = len(db.scalars(select(SavedDesign.id).where(SavedDesign.customer_id == c.id)).all())
            if count >= MAX_SAVED_DESIGNS:
                return JSONResponse({"error": f"You can save up to {MAX_SAVED_DESIGNS} designs. Delete some first."}, status_code=400)
            sd = SavedDesign(customer_id=c.id, name=label, design=keep)
            db.add(sd)
        db.commit()
        return JSONResponse({"id": sd.id, "name": sd.name})

    @app.get("/account/designs/{design_id}.json")
    def design_json(request: Request, design_id: str, db: Session = Depends(get_db)):
        c = require(request, db)
        sd = db.get(SavedDesign, design_id)
        if sd is None or sd.customer_id != c.id:
            raise HTTPException(404)
        return JSONResponse({**sd.design, "name": sd.name, "id": sd.id})

    @app.post("/account/designs/{design_id}/delete")
    def delete_design(request: Request, design_id: str, db: Session = Depends(get_db)):
        c = require(request, db)
        sd = db.get(SavedDesign, design_id)
        if sd is None or sd.customer_id != c.id:
            raise HTTPException(404)
        db.delete(sd)
        db.commit()
        return RedirectResponse("/account#saved", status_code=303)

    # ---- settings ----

    def settings_ctx(c: Customer, **extra) -> dict:
        return {"customer": c, "stripe_on": cfg.stripe_enabled, **extra}

    @app.get("/account/settings")
    def settings_page(request: Request, db: Session = Depends(get_db)):
        c = require(request, db)
        return render(request, "account/settings.html", **settings_ctx(c, done=request.query_params.get("done")))

    @app.post("/account/settings/profile")
    def save_profile(request: Request, name: str = Form(""), company: str = Form(""), phone: str = Form(""),
                     shipping_address: str = Form(""), db: Session = Depends(get_db)):
        c = require(request, db)
        c.name, c.company, c.phone = name.strip()[:255], company.strip()[:255], phone.strip()[:64]
        c.shipping_address = shipping_address.strip()[:2000]
        db.commit()
        return RedirectResponse("/account/settings?done=profile", status_code=303)

    @app.post("/account/settings/password")
    def change_password(request: Request, current: str = Form(...), new: str = Form(...), db: Session = Depends(get_db)):
        c = require(request, db)
        if not check_password(current, c.password_hash):
            return render(request, "account/settings.html", 400, errors=["Your current password isn't right."], **settings_ctx(c))
        if len(new) < MIN_PASSWORD:
            return render(request, "account/settings.html", 400,
                          errors=[f"Use a new password of at least {MIN_PASSWORD} characters."], **settings_ctx(c))
        c.password_hash = hash_password(new)
        c.session_version += 1  # signs out other devices
        db.commit()
        return signed_in(RedirectResponse("/account/settings?done=password", status_code=303), c)

    @app.post("/account/settings/payments")
    def payment_portal(request: Request, db: Session = Depends(get_db)):
        """Send the customer to Stripe's portal to add, remove or change saved cards."""
        c = require(request, db)
        if not cfg.stripe_enabled:
            return render(request, "account/settings.html", 400,
                          errors=["Card payments aren't switched on yet. The shop emails payment details for each order."],
                          **settings_ctx(c))
        from . import payments

        try:
            url = payments.billing_portal(c, cfg)
            db.commit()  # keeps a newly created Stripe customer id
        except payments.PaymentError:
            return render(request, "account/settings.html", 502,
                          errors=["We couldn't open the payment settings. Try again in a minute."], **settings_ctx(c))
        return RedirectResponse(url, status_code=303)
