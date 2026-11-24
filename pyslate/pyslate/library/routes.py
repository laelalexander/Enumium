"""Web routes for the design library at /designs."""

from __future__ import annotations

import math
import re
import shutil
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from .. import services, studio
from ..models import Quote
from . import shapes as S
from .catalog import CATEGORIES, LASER, LICENSES, PRINT, SOURCES, Catalog, Design
from .providers import ICON_VARIANTS, default_providers, machine_for

CACHE = "public, max-age=86400"
NASA_HOSTS = ("https://raw.githubusercontent.com/nasa/NASA-3D-Resources/",)


def register(app: FastAPI, render, get_db, cfg, catalog: Catalog | None = None) -> Catalog:
    catalog = catalog or Catalog(default_providers())
    app.state.library = catalog

    def load(slug: str) -> Design:
        d = catalog.get(slug)
        if d is None:
            raise HTTPException(404, "Design not found")
        return d

    def variant_of(d: Design, variant: str | None) -> str | None:
        if not d.variants:
            return None
        return variant if variant in d.variants else d.variants[0]

    def laser_shapes(d: Design, variant: str | None) -> list[dict]:
        if d.process != LASER:
            raise HTTPException(404, "This design is a 3D model")
        return catalog.shapes(d, variant_of(d, variant))

    def thumb_url(d: Design) -> str:
        if d.preview_url:
            return d.preview_url
        if d.source == "game-icons":
            return f"/designs/{d.slug}/art.svg"
        return f"/designs/{d.slug}/preview.svg"

    def filename(d: Design, variant: str | None, ext: str) -> str:
        return f"{d.slug}{'-' + variant if variant else ''}.{ext}"

    # ---- pages ----

    @app.get("/designs", response_class=HTMLResponse)
    def library_page(request: Request, q: str = "", category: str = "", process: str = "", source: str = "", page: int = 1):
        q = q[:80]
        category = category if category in CATEGORIES else ""
        process = process if process in (LASER, PRINT) else ""
        source = source if source in SOURCES else ""
        found = catalog.search(q, category, process, source)
        pages = max(1, math.ceil(len(found) / catalog.PAGE))
        page = max(1, min(page, pages))
        items = found[(page - 1) * catalog.PAGE: page * catalog.PAGE]
        params = {k: v for k, v in (("q", q), ("category", category), ("process", process), ("source", source)) if v}

        def page_url(n: int) -> str:
            return "/designs?" + urlencode({**params, "page": n})

        def filter_url(**over) -> str:
            merged = {k: v for k, v in {**params, **over}.items() if v}
            return "/designs" + ("?" + urlencode(merged) if merged else "")

        counts = catalog.counts("category")
        return render(
            request, "library/index.html",
            items=[(d, thumb_url(d)) for d in items], total=len(found), all_total=len(catalog.items),
            q=q, category=category, process=process, source=source, page=page, pages=pages, page_url=page_url, filter_url=filter_url,
            categories=[(c, counts[c]) for c in CATEGORIES if counts.get(c)],
            sources=[(k, v["name"]) for k, v in SOURCES.items() if v["status"] == "included"],
            filtered=bool(params),
        )

    @app.get("/designs/sources", response_class=HTMLResponse)
    def library_sources(request: Request):
        counts = catalog.counts("source")
        return render(request, "library/sources.html", sources=SOURCES, licenses=LICENSES, counts=counts)

    @app.get("/designs/{slug}", response_class=HTMLResponse)
    def design_page(request: Request, slug: str, variant: str = ""):
        d = load(slug)
        ctx = {"d": d, "thumb": thumb_url(d), "related": [(r, thumb_url(r)) for r in catalog.related(d)]}
        if d.process == LASER:
            v = variant_of(d, variant or None)
            shapes = catalog.shapes(d, v)
            w, h = S.size_mm(shapes)
            ctx.update(
                variant=v, variants=[(k, ICON_VARIANTS.get(k, k)) for k in d.variants],
                size=(w, h), machine=machine_for(w, h), has_text=S.has_text(shapes),
                preview=S.preview_svg(shapes, d.title), studio_url=_studio_url(d, v),
            )
        return render(request, "library/design.html", **ctx)

    def _studio_url(d: Design, variant: str | None) -> str:
        path = f"/designs/{d.slug}/studio.json" + (f"?as={variant}" if variant else "")
        return "/studio?" + urlencode({"design": path})

    # ---- files ----

    @app.get("/designs/{slug}/preview.svg")
    def design_preview(request: Request, slug: str):
        d = load(slug)
        svg = S.preview_svg(laser_shapes(d, request.query_params.get("as")), d.title)
        return Response(svg, media_type="image/svg+xml", headers={"Cache-Control": CACHE})

    @app.get("/designs/{slug}/art.svg")
    def design_art(slug: str):
        d = load(slug)
        provider = catalog.providers[d.source]
        if not hasattr(provider, "icon_svg"):
            raise HTTPException(404)
        return Response(provider.icon_svg(d), media_type="image/svg+xml", headers={"Cache-Control": CACHE})

    @app.get("/designs/{slug}/studio.json")
    def design_studio_json(request: Request, slug: str):
        d = load(slug)
        v = variant_of(d, request.query_params.get("as"))
        shapes = laser_shapes(d, v)
        w, h = S.size_mm(shapes)
        body = {"name": d.title, "shapes": shapes, "source": d.source, "license": d.license, "credit": d.attribution}
        if machine_for(w, h):
            body["machine"] = machine_for(w, h)
        return JSONResponse(body, headers={"Cache-Control": CACHE})

    @app.get("/designs/{slug}/download.svg")
    def design_svg(request: Request, slug: str):
        d = load(slug)
        v = variant_of(d, request.query_params.get("as"))
        svg = S.preview_svg(laser_shapes(d, v), d.title)
        credit = f"<desc>{_xml(d.attribution)} Licence: {_xml(d.license_info['name'])} {_xml(d.license_info['url'])}</desc>"
        svg = svg.replace("</title>", "</title>" + credit, 1) if "</title>" in svg else svg
        # Real-world size, so laser software imports it at 1:1.
        vw, vh = (float(x) for x in re.search(r'viewBox="\S+ \S+ (\S+) (\S+)"', svg).groups())
        svg = re.sub(r'width="\d+" height="\d+"', f'width="{vw:.2f}mm" height="{vh:.2f}mm"', svg, count=1)
        return Response(svg, media_type="image/svg+xml",
                        headers={"Content-Disposition": f'attachment; filename="{filename(d, v, "svg")}"'})

    @app.get("/designs/{slug}/download.dxf")
    def design_dxf(request: Request, slug: str):
        d = load(slug)
        v = variant_of(d, request.query_params.get("as"))
        try:
            design = S.server_design(laser_shapes(d, v))
        except studio.DesignError as exc:
            raise HTTPException(400, str(exc)) from None
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "design.dxf"
            studio.design_to_dxf(design, path)
            data = path.read_bytes()
        return Response(data, media_type="application/dxf",
                        headers={"Content-Disposition": f'attachment; filename="{filename(d, v, "dxf")}"'})

    # ---- order it ----

    @app.post("/designs/{slug}/quote")
    def design_quote(slug: str, variant: str = Form(""), file: int = Form(0), db: Session = Depends(get_db)):
        d = load(slug)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmpdir = Path(tmp)
                if d.process == LASER:
                    v = variant_of(d, variant or None)
                    shapes = laser_shapes(d, v)
                    if S.has_text(shapes):
                        return RedirectResponse(_studio_url(d, v), status_code=303)
                    path = tmpdir / filename(d, v, "dxf")
                    studio.design_to_dxf(S.server_design(shapes), path)
                else:
                    if not 0 <= file < len(d.files):
                        raise HTTPException(404, "File not found")
                    path = fetch_model(cfg.data_dir / "library-cache", d, file)
                part = services.store_part(db, cfg.upload_dir, path.name, path)
        except (studio.DesignError, services.ServiceError, OSError) as exc:
            db.rollback()
            raise HTTPException(400, f"We couldn't price this design: {exc}") from None
        quote = Quote()
        db.add(quote)
        services.add_part_to_quote(db, quote, part)
        db.commit()
        return RedirectResponse(f"/quote/{quote.token}", status_code=303)

    return catalog


def fetch_model(cache_dir: Path, d: Design, index: int) -> Path:
    """Download a 3D print file from its source once, then reuse the cached copy."""
    info = d.files[index]
    url = info["url"]
    if not url.startswith(NASA_HOSTS):
        raise services.ServiceError("This file can't be fetched automatically. Send us a design request instead.")
    if info.get("bytes", 0) > 45 * 1024 * 1024:
        raise services.ServiceError("This model is too large for an instant price. Send us a design request instead.")
    target = cache_dir / d.slug / Path(info["name"]).name
    if target.exists() and target.stat().st_size:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=90) as resp, open(tmp, "wb") as fh:  # noqa: S310 - fixed https host above
        shutil.copyfileobj(resp, fh, length=1024 * 1024)
    tmp.replace(target)
    return target


def _xml(text: str) -> str:
    from html import escape

    return escape(text, quote=False)
