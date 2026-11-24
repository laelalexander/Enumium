"""The site's legal pages: terms of service, privacy, shop policies and copyright.

Company details come from the "legal" block of the shop profile (Admin > Rates and
machines), so the pages never need a code change when those details are filled in.
"""

from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from . import services

EFFECTIVE = date(2026, 11, 24)

PAGES = {
    "terms": ("Terms of Service", "legal/terms.html"),
    "privacy": ("Privacy Policy", "legal/privacy.html"),
    "policies": ("Shop Policies", "legal/policies.html"),
    "copyright": ("Copyright and IP", "legal/copyright.html"),
}


def company(profile_data: dict) -> dict:
    """The legal details, with safe wording wherever the shop hasn't filled one in yet."""
    raw = profile_data.get("legal") or {}
    name = (raw.get("company") or "Pyslate").strip()
    legal_name = (raw.get("legal_name") or "").strip()
    state = (raw.get("state") or "").strip()
    email = (raw.get("email") or "").strip()
    ship_from = profile_data.get("ship_from") or {}
    address = (ship_from.get("address") or "").strip()
    if "Set the shop" in address:
        address = ""
    return {
        "name": name,
        "legal_name": legal_name or name,
        "who": f"{legal_name} (doing business as {name})" if legal_name and legal_name != name else name,
        "state": state,
        "law": f"the State of {state}" if state else "the state where our shop is located",
        "email": email,
        "address": address,
        "agent": (raw.get("copyright_agent") or "").strip() or (email and f"Copyright Agent, {email}") or "",
    }


def register(app: FastAPI, render, get_db) -> None:
    def page(slug: str):
        title, template = PAGES[slug]

        def view(request: Request, db: Session = Depends(get_db)):
            profile = services.get_profile(db).data
            return render(request, template, title=title, slug=slug, pages=PAGES, co=company(profile),
                          profile=profile, effective=EFFECTIVE)

        view.__name__ = f"legal_{slug}"
        app.add_api_route(f"/{slug}", view, methods=["GET"], response_class=HTMLResponse)

    for slug in PAGES:
        page(slug)

    @app.get("/legal")
    def legal_index():
        return RedirectResponse("/terms", status_code=307)
