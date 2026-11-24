"""The Pyslate web app: customer pages, admin console and the Stripe webhook."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import tempfile
import time
from pathlib import Path
from urllib.parse import quote as urlquote

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import __version__, catalog, payments, services, studio
from . import accounts, library
from . import geometry as geo
from .config import Settings, settings as default_settings
from .models import ORDER_LABELS, CustomerOrder, Job, Order, Part, Quote, QuoteLine, ServiceRequest, make_session_factory
from .routing import compatible_materials

HERE = Path(__file__).parent
ADMIN_COOKIE = "pyslate_admin"
ADMIN_SESSION_SECONDS = 12 * 3600
MAX_FILES_PER_UPLOAD = 20


def create_app(cfg: Settings | None = None) -> FastAPI:
    cfg = cfg or default_settings
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.upload_dir.mkdir(parents=True, exist_ok=True)
    SessionLocal = make_session_factory(cfg.db_url)

    app = FastAPI(title="Pyslate", version=__version__, docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    templates = Jinja2Templates(directory=HERE / "templates")
    templates.env.globals.update(
        order_labels=ORDER_LABELS, stripe_enabled=cfg.stripe_enabled, version=__version__,
        capabilities=catalog.CAPABILITIES, request_services=catalog.REQUEST_SERVICES,
        request_labels=catalog.REQUEST_LABELS, icon_svg=catalog.icon_svg,
    )
    templates.env.filters["money"] = lambda v: f"${v:,.2f}"
    templates.env.filters["cents"] = lambda v: f"${v / 100:,.2f}"
    templates.env.filters["mm"] = lambda v: f"{v:,.1f} mm"

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def render(request: Request, name: str, status_code: int = 200, **ctx) -> HTMLResponse:
        if "customer" not in ctx and not name.startswith("admin/"):
            ctx["customer"] = None
            if request.cookies.get(accounts.COOKIE):
                with SessionLocal() as db:
                    c = app.state.current_customer(request, db)
                    if c is not None:
                        db.expunge(c)
                    ctx["customer"] = c
        return templates.TemplateResponse(request, name, ctx, status_code=status_code)

    # ---- admin session (signed cookie, SameSite=Strict blocks cross-site form posts) ----

    def _sign(expires: int) -> str:
        mac = hmac.new(cfg.secret_key.encode(), str(expires).encode(), hashlib.sha256).hexdigest()
        return f"{expires}.{mac}"

    def _valid(cookie: str | None) -> bool:
        if not cookie or "." not in cookie:
            return False
        expires, _, mac = cookie.partition(".")
        if not expires.isdigit() or int(expires) < time.time():
            return False
        return hmac.compare_digest(_sign(int(expires)), cookie)

    def require_admin(request: Request) -> None:
        if not cfg.admin_token:
            raise HTTPException(503, "Admin is disabled. Set PYSLATE_ADMIN_TOKEN to turn it on.")
        if not _valid(request.cookies.get(ADMIN_COOKIE)):
            raise HTTPException(303, headers={"Location": "/admin/login"})

    # ---- helpers ----

    def load_quote(db: Session, token: str) -> Quote:
        quote = db.scalar(select(Quote).where(Quote.token == token))
        if quote is None:
            raise HTTPException(404, "Quote not found")
        return quote

    def load_order(db: Session, number: int, token: str) -> Order:
        order = db.scalar(select(Order).where(Order.number == number))
        if order is None or not secrets.compare_digest(order.access_token, token or ""):
            raise HTTPException(404, "Order not found")
        return order

    def quote_context(db: Session, quote: Quote) -> dict:
        profile = services.get_profile(db)
        rows = []
        for line in quote.lines:
            g = geo.PartGeometry.from_dict(line.part.geometry)
            rows.append(
                {
                    "line": line,
                    "geom": g,
                    "materials": compatible_materials(g, profile),
                    "machine": profile.machine(line.machine_id) if line.machine_id else None,
                }
            )
        return {
            "quote": quote,
            "rows": rows,
            "summary": services.quote_summary(db, quote),
            "orderable": services.quote_is_orderable(quote),
            "profile": profile.data,
        }

    async def _save_uploads(db: Session, files: list[UploadFile]) -> tuple[list[Part], list[str]]:
        parts, errors = [], []
        limit = cfg.max_upload_mb * 1024 * 1024
        for upload in files[:MAX_FILES_PER_UPLOAD]:
            if not upload.filename:
                continue
            with tempfile.NamedTemporaryFile(suffix=Path(upload.filename).suffix.lower()) as tmp:
                size = 0
                while chunk := await upload.read(1024 * 1024):
                    size += len(chunk)
                    if size > limit:
                        break
                    tmp.write(chunk)
                tmp.flush()
                if size > limit:
                    errors.append(f"{upload.filename}: larger than {cfg.max_upload_mb} MB")
                    continue
                try:
                    parts.append(services.store_part(db, cfg.upload_dir, upload.filename, Path(tmp.name)))
                except services.ServiceError as exc:
                    errors.append(str(exc))
        return parts, errors

    # ---- customer pages ----

    @app.get("/", response_class=HTMLResponse)
    def landing(request: Request, db: Session = Depends(get_db)):
        profile = services.get_profile(db).data
        return render(request, "landing.html", profile=profile, formats=sorted(geo.SUPPORTED_EXTS))

    @app.get("/quote", response_class=HTMLResponse)
    def quote_start(request: Request):
        return render(request, "quote_start.html", formats=sorted(geo.SUPPORTED_EXTS))

    # ---- design studio ----

    def studio_context(db: Session) -> dict:
        profile = services.get_profile(db).data
        machines = [{"id": m["id"], "name": m["name"], "line": m["line"], "bed": list(m["bed_mm"][:2])}
                    for m in profile["machines"] if m.get("kind") != "lathe" and m["line"] != "molding"]  # 2D outlines only
        mats = [{"id": m["id"], "name": m["name"], "line": m["line"], "thickness": m.get("thickness_mm"),
                 "engrave_only": bool(m.get("engrave_only")), "machines": m.get("machines", [])}
                for m in profile["materials"]]
        return {"studio_config": {"machines": machines, "materials": mats}}

    @app.get("/studio", response_class=HTMLResponse)
    def studio_page(request: Request, db: Session = Depends(get_db)):
        return render(request, "studio.html", **studio_context(db))

    def _studio_files(design: dict, process: str, height_mm: float, tmpdir: Path) -> tuple[str, Path]:
        if process in studio.SOLID_PROCESSES:
            target = tmpdir / "studio-design.stl"
            studio.design_to_stl(design, height_mm, target, tmpdir)
            return "studio-design.stl", target
        target = tmpdir / "studio-design.dxf"
        studio.design_to_dxf(design, target)
        return "studio-design.dxf", target

    @app.post("/studio/quote")
    def studio_quote(
        request: Request,
        design: str = Form(...),
        process: str = Form("laser"),
        material_id: str = Form(""),
        height_mm: float = Form(10.0),
        quantity: int = Form(1),
        db: Session = Depends(get_db),
    ):
        try:
            clean = studio.validate_design(design)
            if process not in studio.PROCESSES:
                raise studio.DesignError("Choose how the part is made")
            if process in studio.SOLID_PROCESSES and not 0.4 <= height_mm <= 256:
                raise studio.DesignError("Part height must be between 0.4 and 256 mm")
            with tempfile.TemporaryDirectory() as tmp:
                name, path = _studio_files(clean, process, height_mm, Path(tmp))
                part = services.store_part(db, cfg.upload_dir, name, path)
        except (studio.DesignError, services.ServiceError) as exc:
            db.rollback()
            return JSONResponse({"error": str(exc)}, status_code=400)
        quote = Quote()
        db.add(quote)
        line = services.add_part_to_quote(db, quote, part)
        db.commit()
        allowed = {m["id"] for m in compatible_materials(geo.PartGeometry.from_dict(part.geometry), services.get_profile(db))}
        try:
            services.update_line(db, line, material_id if material_id in allowed else line.material_id,
                                 max(1, min(quantity, services.MAX_QUANTITY)))
        except services.ServiceError:
            db.rollback()
        return JSONResponse({"url": f"/quote/{quote.token}"})

    @app.post("/studio/request")
    def studio_request(
        design: str = Form(...),
        process: str = Form("laser"),
        material_id: str = Form(""),
        height_mm: float = Form(10.0),
        name: str = Form(""),
        email: str = Form(""),
        description: str = Form(""),
        db: Session = Depends(get_db),
    ):
        try:
            clean = studio.validate_design(design)
            if process not in studio.PROCESSES:
                raise studio.DesignError("Choose how the part is made")
            note = (f"{description.strip()}\n\nFrom the design studio: {len(clean['shapes'])} shapes, "
                    f"{studio.PROCESSES[process] + ', ' + format(height_mm, 'g') + ' mm tall' if process in studio.SOLID_PROCESSES else studio.PROCESSES[process]}"
                    f"{', material ' + material_id if material_id else ''}.")
            with tempfile.TemporaryDirectory() as tmp:
                tmpdir = Path(tmp)
                dxf = tmpdir / "design.dxf"
                studio.design_to_dxf(clean, dxf)
                js = tmpdir / "design.json"
                js.write_text(json.dumps({**clean, "process": process, "material_id": material_id,
                                          "height_mm": height_mm}, indent=1))
                files = [("studio-design.dxf", dxf), ("studio-design.json", js)]
                if process in studio.SOLID_PROCESSES:
                    files.insert(1, _studio_files(clean, process, height_mm, tmpdir))
                req = services.create_service_request(
                    db, cfg.upload_dir, "product-design", name, email, note, files=files,
                )
        except (studio.DesignError, services.ServiceError) as exc:
            db.rollback()
            return JSONResponse({"error": str(exc)}, status_code=400)
        return JSONResponse({"ref": f"R-{req.number}"})

    @app.get("/capabilities", response_class=HTMLResponse)
    def capabilities_page(request: Request):
        return render(request, "capabilities.html")

    @app.get("/capabilities/{slug}", response_class=HTMLResponse)
    def capability_page(request: Request, slug: str, db: Session = Depends(get_db)):
        cap = catalog.CAPABILITY_BY_SLUG.get(slug)
        if cap is None:
            raise HTTPException(404, "No such capability")
        detail = catalog.DETAILS[slug]
        profile = services.get_profile(db).data
        materials = []
        if detail.get("line"):
            wanted = set(detail.get("machines", []))
            materials = [m for m in profile["materials"] if m["line"] == detail["line"]
                         and (not wanted or wanted & set(m.get("machines", [])))]
        others = [c for c in catalog.CAPABILITIES if c["slug"] != slug]
        return render(request, "capability.html", cap=cap, detail=detail, materials=materials,
                      others=others, formats=sorted(geo.SUPPORTED_EXTS))

    @app.get("/how-it-works", response_class=HTMLResponse)
    def how_page(request: Request, db: Session = Depends(get_db)):
        return render(request, "how.html", profile=services.get_profile(db).data)

    @app.get("/materials", response_class=HTMLResponse)
    def materials_page(request: Request, db: Session = Depends(get_db)):
        profile = services.get_profile(db).data
        names = {m["id"]: m["name"] for m in profile["machines"]}
        return render(request, "materials.html", profile=profile, machine_names=names)

    @app.get("/about", response_class=HTMLResponse)
    def about_page(request: Request, db: Session = Depends(get_db)):
        return render(request, "about.html", profile=services.get_profile(db).data,
                      machine_photos=[("/static/img/shop/noit1680iii.jpg", "Our Noitavonne NOIT1680III injection molder")])

    @app.post("/quote")
    async def upload(
        request: Request,
        files: list[UploadFile] = File(...),
        quote_token: str | None = Form(None),
        db: Session = Depends(get_db),
    ):
        quote = load_quote(db, quote_token) if quote_token else Quote()
        if quote.order is not None:
            raise HTTPException(400, "This quote has already been ordered")
        parts, errors = await _save_uploads(db, files)
        if not parts:
            db.rollback()
            profile = services.get_profile(db).data
            return render(
                request, "quote_start.html", 400,
                profile=profile, formats=sorted(geo.SUPPORTED_EXTS), errors=errors or ["Choose a file to upload"],
            )
        if quote.id is None:
            db.add(quote)
        for part in parts:
            services.add_part_to_quote(db, quote, part)
        db.commit()
        url = f"/quote/{quote.token}"
        if errors:
            url += "?errors=" + urlquote(json.dumps(errors))
        return RedirectResponse(url, status_code=303)

    @app.get("/quote/{token}", response_class=HTMLResponse)
    def show_quote(request: Request, token: str, errors: str | None = None, db: Session = Depends(get_db)):
        quote = load_quote(db, token)
        try:
            messages = json.loads(errors) if errors else []
            messages = [str(m) for m in messages][:20] if isinstance(messages, list) else []
        except ValueError:
            messages = []
        return render(request, "quote.html", errors=messages, just_saved=request.query_params.get("saved") == "1",
                      **quote_context(db, quote))

    @app.post("/quote/{token}/line/{line_id}")
    def change_line(
        request: Request,
        token: str,
        line_id: str,
        material_id: str = Form(""),
        quantity: int = Form(1),
        action: str = Form("update"),
        db: Session = Depends(get_db),
    ):
        quote = load_quote(db, token)
        line = next((ln for ln in quote.lines if ln.id == line_id), None)
        if line is None:
            raise HTTPException(404, "Part not found")
        if quote.order is not None:
            raise HTTPException(400, "This quote has already been ordered")
        try:
            if action == "remove":
                quote.lines.remove(line)
                db.commit()
            else:
                services.update_line(db, line, material_id or None, quantity)
        except services.ServiceError as exc:
            return render(request, "quote.html", 400, errors=[str(exc)], **quote_context(db, quote))
        return RedirectResponse(f"/quote/{token}#line-{line_id}", status_code=303)

    @app.post("/quote/{token}/lead")
    def change_lead(token: str, lead_tier: str = Form("standard"), db: Session = Depends(get_db)):
        quote = load_quote(db, token)
        if quote.order is None and lead_tier in ("standard", "rush"):
            quote.lead_tier = lead_tier
            db.commit()
        return RedirectResponse(f"/quote/{token}", status_code=303)

    @app.get("/parts/{part_id}/preview")
    def part_preview(part_id: str, db: Session = Depends(get_db)):
        part = db.get(Part, part_id)
        if part is None:
            raise HTTPException(404)
        if part.preview_name:
            return FileResponse(cfg.upload_dir / part.preview_name, media_type="model/stl")
        if part.stored_name.endswith(".dxf"):
            svg = geo.dxf_preview_svg(cfg.upload_dir / part.stored_name)
            return Response(svg, media_type="image/svg+xml")
        raise HTTPException(404)

    def _sheet_thickness(db: Session, line: QuoteLine) -> float:
        material = services.get_profile(db).material(line.material_id) if line.material_id else None
        return float(material.get("thickness_mm", 3.0)) if material else 3.0

    @app.get("/parts/{part_id}/model.stl")
    def part_model(part_id: str, thickness: float = 3.0, db: Session = Depends(get_db)):
        """The part as an STL for the 3D viewer. Drawings are extruded to the sheet thickness."""
        part = db.get(Part, part_id)
        if part is None:
            raise HTTPException(404)
        if part.preview_name:
            return FileResponse(cfg.upload_dir / part.preview_name, media_type="model/stl")
        if not part.stored_name.endswith(".dxf"):
            raise HTTPException(404)
        thickness = min(max(thickness, 0.1), 50.0)
        cached = cfg.upload_dir / f"{part.id}.sheet-{thickness:.2f}.stl"
        if not cached.exists():
            try:
                geo.dxf_to_mesh(cfg.upload_dir / part.stored_name, thickness).export(str(cached), file_type="stl")
            except Exception as exc:  # a drawing that cannot be filled still has its 2D preview
                raise HTTPException(422, "This drawing cannot be shown in 3D") from exc
        return FileResponse(cached, media_type="model/stl")

    @app.get("/quote/{token}/part/{line_id}", response_class=HTMLResponse)
    def part_view(request: Request, token: str, line_id: str, db: Session = Depends(get_db)):
        quote = load_quote(db, token)
        line = next((ln for ln in quote.lines if ln.id == line_id), None)
        if line is None:
            raise HTTPException(404, "Part not found")
        profile = services.get_profile(db)
        g = geo.PartGeometry.from_dict(line.part.geometry)
        material = profile.material(line.material_id) if line.material_id else None
        machine = profile.machine(line.machine_id) if line.machine_id else None
        thickness = _sheet_thickness(db, line)
        model_url = f"/parts/{line.part.id}/model.stl"
        if g.kind == "drawing":
            model_url += f"?thickness={thickness:.2f}"
        viewer_config = {
            "model_url": model_url,
            "name": line.part.filename,
            "kind": g.kind,
            "line": line.line,
            "material_name": material["name"] if material else "",
            "machine_name": machine["name"] if machine else "",
            "bed_mm": machine["bed_mm"] if machine else None,
            "volume_mm3": g.volume_mm3 if g.kind == "mesh" else None,
        }
        return render(
            request, "part_view.html", quote=quote, line=line, geom=g, material=material, machine=machine,
            thickness=thickness, viewer_config=viewer_config,
        )

    @app.post("/quote/{token}/checkout")
    def checkout(
        request: Request,
        token: str,
        email: str = Form(...),
        name: str = Form(...),
        address: str = Form(...),
        notes: str = Form(""),
        db: Session = Depends(get_db),
    ):
        quote = load_quote(db, token)
        try:
            order = services.place_order(db, quote, email, name, address, notes)
        except services.ServiceError as exc:
            return render(request, "quote.html", 400, errors=[str(exc)], **quote_context(db, quote))
        customer = app.state.current_customer(request, db)
        if customer is not None:
            app.state.link_order(db, customer, order)
        order_url = f"/order/{order.number}?t={order.access_token}"
        if cfg.stripe_enabled and order.status == "awaiting_payment":
            try:
                url = payments.create_checkout(order, cfg, customer)
                db.commit()
                return RedirectResponse(url, status_code=303)
            except payments.PaymentError:
                return RedirectResponse(order_url + "&payment_error=1", status_code=303)
        return RedirectResponse(order_url, status_code=303)

    @app.get("/order/{number}", response_class=HTMLResponse)
    def show_order(
        request: Request, number: int, t: str = "", paid: int = 0, payment_error: int = 0,
        db: Session = Depends(get_db),
    ):
        order = load_order(db, number, t)
        customer = app.state.current_customer(request, db)
        owned = customer is not None and db.get(CustomerOrder, (customer.id, order.id)) is not None
        profile = services.get_profile(db)
        names = {ln.material_id: (profile.material(ln.material_id) or {}).get("name", ln.material_id)
                 for ln in order.quote.lines if ln.material_id}
        return render(request, "order.html", order=order, just_paid=bool(paid), payment_error=bool(payment_error),
                      customer=customer, owned=owned, added=request.query_params.get("added") == "1",
                      material_names=names)

    @app.post("/stripe/webhook")
    async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
        try:
            _, order_id = payments.parse_webhook(
                await request.body(), request.headers.get("stripe-signature", ""), cfg
            )
        except payments.PaymentError as exc:
            raise HTTPException(400, str(exc)) from exc
        if order_id:
            order = db.get(Order, order_id)
            if order is not None:
                services.mark_paid(db, order, "Paid by card through Stripe")
        return JSONResponse({"received": True})

    @app.get("/request", response_class=HTMLResponse)
    def request_form(request: Request, service: str = ""):
        return render(request, "request.html", selected=service, form={})

    @app.post("/request", response_class=HTMLResponse)
    async def request_submit(
        request: Request,
        service: str = Form(""),
        name: str = Form(""),
        email: str = Form(""),
        company: str = Form(""),
        phone: str = Form(""),
        description: str = Form(""),
        budget: str = Form(""),
        needed_by: str = Form(""),
        files: list[UploadFile] = File(default=[]),
        db: Session = Depends(get_db),
    ):
        form = dict(service=service, name=name, email=email, company=company, phone=phone,
                    description=description, budget=budget, needed_by=needed_by)
        limit = cfg.max_upload_mb * 1024 * 1024
        with tempfile.TemporaryDirectory() as tmpdir:
            saved: list[tuple[str, Path]] = []
            for i, upload in enumerate(f for f in files[:MAX_FILES_PER_UPLOAD] if f.filename):
                dest = Path(tmpdir) / str(i)
                size = 0
                with dest.open("wb") as out:
                    while chunk := await upload.read(1024 * 1024):
                        size += len(chunk)
                        if size > limit:
                            break
                        out.write(chunk)
                if size > limit:
                    return render(request, "request.html", 400, selected=service, form=form,
                                  errors=[f"{upload.filename}: larger than {cfg.max_upload_mb} MB"])
                saved.append((upload.filename, dest))
            try:
                req = services.create_service_request(
                    db, cfg.upload_dir, service, name, email, description,
                    company=company, phone=phone, budget=budget, needed_by=needed_by, files=saved,
                )
            except services.ServiceError as exc:
                return render(request, "request.html", 400, selected=service, form=form, errors=[str(exc)])
        return render(request, "request_done.html", req=req)

    @app.get("/api/health")
    def health():
        return {"ok": True, "version": __version__}

    # ---- admin console ----

    @app.get("/admin/login", response_class=HTMLResponse)
    def admin_login_form(request: Request):
        if not cfg.admin_token:
            raise HTTPException(503, "Admin is disabled. Set PYSLATE_ADMIN_TOKEN to turn it on.")
        return render(request, "admin/login.html")

    @app.post("/admin/login")
    def admin_login(request: Request, token: str = Form(...)):
        if not cfg.admin_token:
            raise HTTPException(503)
        if not secrets.compare_digest(token.encode(), cfg.admin_token.encode()):
            return render(request, "admin/login.html", 401, error="Wrong password")
        resp = RedirectResponse("/admin", status_code=303)
        resp.set_cookie(
            ADMIN_COOKIE, _sign(int(time.time()) + ADMIN_SESSION_SECONDS),
            httponly=True, samesite="strict", secure=cfg.secure_cookies, max_age=ADMIN_SESSION_SECONDS,
        )
        return resp

    @app.post("/admin/logout")
    def admin_logout():
        resp = RedirectResponse("/", status_code=303)
        resp.delete_cookie(ADMIN_COOKIE)
        return resp

    @app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
    def admin_home(request: Request, db: Session = Depends(get_db)):
        profile = services.get_profile(db)
        jobs = db.scalars(select(Job).where(Job.state != "done").order_by(Job.updated_at)).all()
        orders = db.scalars(select(Order).order_by(Order.number.desc()).limit(100)).all()
        lanes = {}
        for machine in profile.data["machines"]:
            lanes[machine["id"]] = {"machine": machine, "jobs": []}
        lanes["review"] = {"machine": {"id": "review", "name": "Needs review", "line": "review"}, "jobs": []}
        for job in jobs:
            lanes.get(job.machine_id or "review", lanes["review"])["jobs"].append(job)
        return render(request, "admin/home.html", lanes=lanes.values(), orders=orders)

    @app.get("/admin/order/{number}", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
    def admin_order(request: Request, number: int, db: Session = Depends(get_db)):
        order = db.scalar(select(Order).where(Order.number == number))
        if order is None:
            raise HTTPException(404)
        return render(request, "admin/order.html", order=order, profile=services.get_profile(db).data)

    @app.post("/admin/order/{number}/paid", dependencies=[Depends(require_admin)])
    def admin_mark_paid(number: int, db: Session = Depends(get_db)):
        order = db.scalar(select(Order).where(Order.number == number))
        if order is None:
            raise HTTPException(404)
        services.mark_paid(db, order, "Payment recorded by the shop")
        return RedirectResponse(f"/admin/order/{number}", status_code=303)

    @app.post("/admin/order/{number}/status", dependencies=[Depends(require_admin)])
    def admin_order_status(
        request: Request, number: int, status: str = Form(...), note: str = Form(""), tracking: str = Form(""),
        db: Session = Depends(get_db),
    ):
        order = db.scalar(select(Order).where(Order.number == number))
        if order is None:
            raise HTTPException(404)
        try:
            services.set_order_status(db, order, status, note, tracking)
        except services.ServiceError as exc:
            return render(
                request, "admin/order.html", 400, order=order, profile=services.get_profile(db).data, error=str(exc)
            )
        return RedirectResponse(f"/admin/order/{number}", status_code=303)

    @app.post("/admin/job/{job_id}", dependencies=[Depends(require_admin)])
    def admin_job(job_id: str, state: str = Form(...), note: str = Form(""), back: str = Form("/admin"),
                  db: Session = Depends(get_db)):
        job = db.get(Job, job_id)
        if job is None:
            raise HTTPException(404)
        try:
            services.move_job(db, job, state, note)
        except services.ServiceError as exc:
            raise HTTPException(400, str(exc)) from exc
        return RedirectResponse(back if back.startswith("/admin") else "/admin", status_code=303)

    @app.get("/admin/requests", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
    def admin_requests(request: Request, db: Session = Depends(get_db)):
        reqs = db.scalars(select(ServiceRequest).order_by(ServiceRequest.number.desc()).limit(200)).all()
        return render(request, "admin/requests.html", reqs=reqs)

    @app.get("/admin/requests/{number}", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
    def admin_request(request: Request, number: int, db: Session = Depends(get_db)):
        req = db.scalar(select(ServiceRequest).where(ServiceRequest.number == number))
        if req is None:
            raise HTTPException(404)
        return render(request, "admin/request.html", req=req, states=catalog.REQUEST_STATES)

    @app.post("/admin/requests/{number}", dependencies=[Depends(require_admin)])
    def admin_request_update(number: int, status: str = Form(...), shop_notes: str = Form(""),
                             db: Session = Depends(get_db)):
        req = db.scalar(select(ServiceRequest).where(ServiceRequest.number == number))
        if req is None:
            raise HTTPException(404)
        try:
            services.update_service_request(db, req, status, shop_notes)
        except services.ServiceError as exc:
            raise HTTPException(400, str(exc)) from exc
        return RedirectResponse(f"/admin/requests/{number}", status_code=303)

    @app.get("/admin/requests/{number}/file/{index}", dependencies=[Depends(require_admin)])
    def admin_request_file(number: int, index: int, db: Session = Depends(get_db)):
        req = db.scalar(select(ServiceRequest).where(ServiceRequest.number == number))
        if req is None or not 0 <= index < len(req.files):
            raise HTTPException(404)
        f = req.files[index]
        return FileResponse(cfg.upload_dir / "requests" / f["stored"], filename=f["name"])

    @app.get("/admin/parts/{part_id}/file", dependencies=[Depends(require_admin)])
    def admin_part_file(part_id: str, db: Session = Depends(get_db)):
        part = db.get(Part, part_id)
        if part is None:
            raise HTTPException(404)
        return FileResponse(cfg.upload_dir / part.stored_name, filename=part.filename)

    @app.get("/admin/rates", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
    def admin_rates(request: Request, db: Session = Depends(get_db)):
        text = json.dumps(services.get_profile(db).data, indent=2)
        return render(request, "admin/rates.html", text=text)

    @app.post("/admin/rates", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
    def admin_save_rates(request: Request, profile: str = Form(...), db: Session = Depends(get_db)):
        try:
            services.save_profile(db, json.loads(profile))
        except (ValueError, services.ServiceError) as exc:
            return render(request, "admin/rates.html", 400, text=profile, error=str(exc))
        return render(request, "admin/rates.html", text=profile, saved=True)

    app.state.session_factory = SessionLocal
    app.state.settings = cfg
    library.register(app, render, get_db, cfg)
    accounts.register(app, render, get_db, cfg)

    return app
