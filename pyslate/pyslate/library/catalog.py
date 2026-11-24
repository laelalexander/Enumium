"""The design library: every design customers can browse, with its source and licence.

Designs come from providers. Each provider knows one source, lists its designs and,
for laser designs, draws them as studio shapes. Today's providers are bundled with
the app (Pyslate originals, game-icons.net art, NASA 3D print models). The planned
marketplace adds a provider backed by the database, for designs that customers and
makers list themselves; that is what `seller` and `price_cents` are for.

A design is only bundled when its licence lets the shop share the file and sell what
it makes from it. LICENSES and SOURCES below are the record of what qualifies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import Iterable, Protocol

LASER, PRINT = "laser", "print"

LICENSES = {
    "pyslate": {
        "name": "Pyslate original",
        "url": "/designs/sources#pyslate",
        "short": "Free to make, change and sell what you make.",
        "attribution": False,
    },
    "cc0": {
        "name": "CC0 1.0 (public domain)",
        "url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "short": "No rights reserved. Use it for anything.",
        "attribution": False,
    },
    "cc-by-3.0": {
        "name": "CC BY 3.0",
        "url": "https://creativecommons.org/licenses/by/3.0/",
        "short": "Use it for anything, including selling what you make, as long as the artist is credited.",
        "attribution": True,
    },
    "cc-by-4.0": {
        "name": "CC BY 4.0",
        "url": "https://creativecommons.org/licenses/by/4.0/",
        "short": "Use it for anything, including selling what you make, as long as the artist is credited.",
        "attribution": True,
    },
    "nasa": {
        "name": "NASA media (no copyright)",
        "url": "https://www.nasa.gov/nasa-brand-center/images-and-media",
        "short": "Free to use. Don't use NASA's logos or suggest that NASA endorses the product.",
        "attribution": True,
    },
}

# status: "included" = in the library now; "qualifies" = licence allows it, not imported yet;
# "per-item" = only some items qualify, check each; "excluded" = licence doesn't allow it.
SOURCES = {
    "pyslate": {
        "name": "Pyslate originals", "url": "/designs?source=pyslate", "status": "included", "license": "pyslate",
        "note": "Drawn by the shop in code: finger-joint boxes, trays, coasters, ornaments, puzzles, gears, signs and more.",
    },
    "game-icons": {
        "name": "game-icons.net", "url": "https://game-icons.net", "status": "included", "license": "cc-by-3.0",
        "note": "About 4,000 silhouettes by many artists, under CC BY 3.0 (a few under CC0). Each design credits its artist.",
    },
    "nasa-3d": {
        "name": "NASA 3D Resources", "url": "https://github.com/nasa/NASA-3D-Resources", "status": "included", "license": "nasa",
        "note": "NASA's 3D printing models: spacecraft, rovers, asteroids, planets and landing sites. Insignia and emblems are left out.",
    },
    "openclipart": {
        "name": "Openclipart", "url": "https://openclipart.org", "status": "qualifies", "license": "cc0",
        "note": "Every file is CC0. Not imported yet because the site couldn't be reached from the build machine.",
    },
    "smithsonian": {
        "name": "Smithsonian Open Access 3D", "url": "https://www.si.edu/openaccess", "status": "qualifies", "license": "cc0",
        "note": "3D scans marked CC0 qualify. Not imported yet; the API needs a free api.data.gov key.",
    },
    "wikimedia": {
        "name": "Wikimedia Commons", "url": "https://commons.wikimedia.org", "status": "per-item", "license": "cc0",
        "note": "Only files tagged public domain, CC0 or CC BY qualify. Share-alike and non-commercial files don't.",
    },
    "thingiverse": {
        "name": "Thingiverse and Printables", "url": "https://www.thingiverse.com", "status": "per-item", "license": "cc-by-4.0",
        "note": "Only items under CC0 or CC BY qualify. Many items are CC BY-NC (no selling) or carry a site licence that forbids re-sharing.",
    },
    "creative-fabrica": {
        "name": "Creative Fabrica", "url": "https://www.creativefabrica.com", "status": "excluded", "license": None,
        "note": "Its licence, including for freebies, lets a member make products but not share or re-host the files. None of its designs are in the library.",
    },
    "marketplaces": {
        "name": "Design Bundles, Etsy shops, Cricut and Glowforge catalogs", "url": "", "status": "excluded", "license": None,
        "note": "Paid or proprietary files. Their licences don't allow sharing the files from another site.",
    },
    "personal-use": {
        "name": "\"Free for personal use\" files on any site", "url": "", "status": "excluded", "license": None,
        "note": "Personal-use files can't be made for paying customers, so they're never imported.",
    },
}

CATEGORIES = [
    "Boxes and storage", "Home decor", "Kitchen", "Wall art", "Seasonal", "Signs", "Gifts and accessories",
    "Games and puzzles", "Mechanical", "Garden", "Space", "Animals", "Nature", "Fantasy and magic",
    "Symbols and signs", "Food and drink", "People", "Tools and objects", "Vehicles", "Sports and games",
    "Weapons and armour", "Buildings", "Clothing", "Music", "Abstract and patterns", "Other art",
]


@dataclass
class Design:
    slug: str
    title: str
    summary: str
    category: str
    process: str  # LASER or PRINT
    source: str  # key of SOURCES
    license: str  # key of LICENSES
    tags: list[str] = field(default_factory=list)
    author: str = ""
    author_url: str = ""
    source_url: str = ""
    size_mm: tuple[float, ...] = ()
    files: list[dict] = field(default_factory=list)  # print models: [{name, bytes, url}]
    variants: list[str] = field(default_factory=list)  # laser art: product templates it can go on
    preview_url: str = ""
    # Marketplace fields. Bundled designs are free and listed by the shop.
    price_cents: int = 0
    seller: str | None = None
    rank: int = 0  # lower sorts first

    @cached_property
    def search_text(self) -> str:
        return " ".join([self.title, self.category, self.author, *self.tags]).lower()

    @property
    def license_info(self) -> dict:
        return LICENSES[self.license]

    @property
    def source_info(self) -> dict:
        return SOURCES[self.source]

    @property
    def attribution(self) -> str:
        """The credit line licences like CC BY ask for."""
        lic = LICENSES[self.license]["name"]
        if self.source == "game-icons":
            return f"“{self.title}” by {self.author}, from game-icons.net, licensed {lic}. Resized and placed on a blank by Pyslate."
        if self.source == "nasa-3d":
            return f"“{self.title}” 3D model courtesy of NASA (NASA 3D Resources). NASA does not endorse Pyslate or its products."
        if self.source == "pyslate":
            return f"“{self.title}”, a Pyslate original design."
        return f"“{self.title}” by {self.author or 'unknown'}, {lic}."


class Provider(Protocol):
    source: str

    def designs(self) -> Iterable[Design]: ...

    def shapes(self, design: Design, variant: str | None) -> list[dict]: ...


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class Catalog:
    """All designs from all providers, with search and filters."""

    PAGE = 48

    def __init__(self, providers: list[Provider]):
        self.providers = {p.source: p for p in providers}
        self.items: list[Design] = []
        self.by_slug: dict[str, Design] = {}
        for p in providers:
            for d in p.designs():
                if d.slug in self.by_slug or d.slug in RESERVED:
                    d.slug = f"{d.slug}-{d.source}"
                self.by_slug[d.slug] = d
                self.items.append(d)
        self.items.sort(key=lambda d: d.rank)  # stable: each provider keeps its own order

    def get(self, slug: str) -> Design | None:
        return self.by_slug.get(slug)

    def shapes(self, design: Design, variant: str | None = None) -> list[dict]:
        return self.providers[design.source].shapes(design, variant)

    def search(self, q: str = "", category: str = "", process: str = "", source: str = "") -> list[Design]:
        words = [w for w in re.split(r"\s+", q.lower().strip()) if w]
        out = []
        for d in self.items:
            if category and d.category != category:
                continue
            if process and d.process != process:
                continue
            if source and d.source != source:
                continue
            if words and not all(w in d.search_text for w in words):
                continue
            out.append(d)
        return out

    def counts(self, attr: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for d in self.items:
            key = getattr(d, attr)
            out[key] = out.get(key, 0) + 1
        return out

    def related(self, design: Design, n: int = 8) -> list[Design]:
        same = [d for d in self.items if d.category == design.category and d.slug != design.slug]
        if not same:
            return []
        start = abs(hash(design.slug)) % len(same)
        return (same[start:] + same[:start])[:n]


RESERVED = {"sources"}
