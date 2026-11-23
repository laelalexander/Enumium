"""What the shop offers, shown on the main page.

"instant" services are priced by uploading a file. "request" services
(design and documentation work) go through the project request form and
the shop replies with a quote.
"""

from __future__ import annotations

# Icons are 24x24 line drawings, drawn with currentColor.
ICONS = {
    "printer": '<path d="M5 4h14v4H5z"/><path d="M12 8v3"/><path d="M9 11h6l-1 3h-4z"/><path d="M4 20h16"/><path d="M7 20v-3h10v3"/>',
    "laser": '<path d="M12 2v7"/><path d="M9 6l3 3 3-3"/><path d="M12 13l-2 3h4z"/><path d="M3 20h18"/><path d="M6 17h12v3H6z"/>',
    "metal": '<path d="M4 18l6-12h4l6 12z"/><path d="M8 14h8"/><circle cx="12" cy="10" r="1"/>',
    "system": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="8.5" y="14" width="7" height="7" rx="1"/><path d="M6.5 10v2h11v-2"/><path d="M12 12v2"/>',
    "blueprint": '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M7 16V9h6v7"/><path d="M7 12h6"/><path d="M16 8v8"/><path d="M15 8h2M15 16h2"/>',
    "schematic": '<path d="M2 12h4l2-4 3 8 3-8 2 4h6"/><circle cx="20" cy="12" r="1"/><circle cx="4" cy="12" r="1"/>',
    "design": '<path d="M4 20l4-1 11-11-3-3L5 16z"/><path d="M14 6l3 3"/>',
}

CAPABILITIES = [
    {
        "slug": "3d-printing",
        "title": "3D Printing",
        "icon": "printer",
        "kind": "instant",
        "blurb": "Prototypes and end-use parts in PLA and PETG on Bambu Lab and our custom printers.",
    },
    {
        "slug": "laser-cutting",
        "title": "Laser Cutting and Engraving",
        "icon": "laser",
        "kind": "instant",
        "blurb": "Wood, acrylic and MDF cut and engraved on the xTool X1 and M2.",
    },
    {
        "slug": "metal-fabrication",
        "title": "Metal Laser Fabrication",
        "icon": "metal",
        "kind": "instant",
        "blurb": "Stainless steel sheet parts cut on the xTool MetalFab.",
    },
    {
        "slug": "system-design",
        "title": "Custom System Design",
        "icon": "system",
        "kind": "request",
        "blurb": "Full systems designed for you, from mechanical structure to electrical and controls, then built in our shop.",
    },
    {
        "slug": "mechanical-blueprints",
        "title": "Mechanical Blueprints",
        "icon": "blueprint",
        "kind": "request",
        "blurb": "Engineering drawings, assemblies, cut lists and bills of materials, ready to build from.",
    },
    {
        "slug": "electrical-schematics",
        "title": "Electrical Schematics",
        "icon": "schematic",
        "kind": "request",
        "blurb": "Wiring diagrams, schematics and panel layouts for your electrical and control systems.",
    },
    {
        "slug": "product-design",
        "title": "Product Design from Your Idea",
        "icon": "design",
        "kind": "request",
        "blurb": "Bring a sketch, photo or idea. We model it, check it can be made, and quote it.",
    },
]

REQUEST_SERVICES = {c["slug"]: c["title"] for c in CAPABILITIES if c["kind"] == "request"}

REQUEST_STATES = ["new", "reviewing", "quoted", "in_progress", "delivered", "declined"]
REQUEST_LABELS = {
    "new": "New",
    "reviewing": "Reviewing",
    "quoted": "Quote sent",
    "in_progress": "In progress",
    "delivered": "Delivered",
    "declined": "Declined",
}


def icon_svg(name: str) -> str:
    body = ICONS.get(name, ICONS["design"])
    return (
        '<svg class="cap-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )
