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
    "mill": '<path d="M9 3h6v5H9z"/><path d="M11 8h2v5h-2z"/><path d="M12 13v2"/><path d="M4 18h16v3H4z"/><path d="M7 15h10v3H7z"/>',
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
        "blurb": "Wood, acrylic and MDF cut and engraved on the xTool X1, M2 and F2, plus engraving on metal.",
    },
    {
        "slug": "metal-fabrication",
        "title": "Metal Laser Fabrication",
        "icon": "metal",
        "kind": "instant",
        "blurb": "Stainless steel sheet parts cut on the xTool MetalFab.",
    },
    {
        "slug": "cnc-machining",
        "title": "CNC Machining",
        "icon": "mill",
        "kind": "instant",
        "blurb": "Aluminium, steel and Delrin parts milled on Tormach CNC machines in our metal shop.",
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


# Page content for each capability, shown at /capabilities/<slug>.
DETAILS = {
    "3d-printing": {
        "headline": "3D printed parts, from one prototype to a production run.",
        "intro": "We print on Bambu Lab printers and our own custom-built machines. Upload a model and you get a price, a lead time and a printability check in seconds.",
        "points": [
            "PLA for prototypes, fixtures and display parts",
            "PETG for tougher, heat- and moisture-resistant parts",
            "Overhang and thin-wall checks before you order",
            "Quantity discounts from 10 parts",
        ],
        "specs": [("Build volume", "256 × 256 × 256 mm"), ("Layer height", "0.20 mm standard"),
                  ("Files", "STL, 3MF, OBJ, PLY"), ("Lead time", "About 7 days, 3 with rush")],
        "line": "print",
    },
    "laser-cutting": {
        "headline": "Laser cut and engraved parts in wood, acrylic and MDF, and engraving on metal.",
        "intro": "Flat parts go to our xTool X1 and M2 lasers, and small parts and metal engraving to the xTool F2. Upload a DXF or a flat model and we measure the cut length, nest it on the sheet and price it.",
        "points": [
            "Signs, panels, enclosures, inlays and templates",
            "Engraving for logos, labels and serial numbers",
            "Metal engraving on stainless, anodized aluminium and brass blanks (xTool F2 IR laser)",
            "Cut length and sheet use priced line by line",
            "Parts thicker or larger than our stock go to review",
        ],
        "specs": [("Work area", "X1: 615 × 320 mm · M2: 426 × 320 mm · F2: 400 × 115 mm"), ("Materials", "Plywood, cast acrylic, MDF; metal blanks for engraving"),
                  ("Files", "DXF, or a flat STL / 3MF"), ("Lead time", "About 7 days, 3 with rush")],
        "line": "laser",
        "machines": ["x1", "m2", "f2"],
    },
    "metal-fabrication": {
        "headline": "Stainless steel sheet parts, cut on the xTool MetalFab.",
        "intro": "Brackets, plates, shims and panels cut from stainless sheet. Upload a DXF and the price includes cutting time and material.",
        "points": [
            "Brackets, mounting plates, gaskets and shims",
            "Clean edges with no tooling cost",
            "Small batches priced the same way as single parts",
            "Parts larger than the bed go to review",
        ],
        "specs": [("Work area", "610 × 610 mm"), ("Material", "Stainless steel 1 mm"),
                  ("Files", "DXF"), ("Lead time", "About 7 days, 3 with rush")],
        "line": "laser",
        "machines": ["metalfab"],
    },
    "cnc-machining": {
        "headline": "Machined parts in aluminium, steel and Delrin.",
        "intro": "Our metal shop runs Tormach CNC mills. Upload a 3D model and you get an estimate built from the stock block and the time to mill it. An engineer checks every machined part before we cut, and confirms the price if fixturing or tolerances change it.",
        "points": [
            "Brackets, housings, fixtures, adapters and plates",
            "Aluminium 6061, mild steel 1018 and Delrin from stock",
            "Engineer review of every part before machining",
            "Tight tolerances, threads and finishes: add a note and we'll quote them",
        ],
        "specs": [("Travel", "457 × 279 × 413 mm"), ("Materials", "Aluminium, mild steel, Delrin"),
                  ("Files", "STL, 3MF, OBJ (send STEP to an engineer)"), ("Lead time", "About 7 days, 3 with rush")],
        "line": "cnc",
        "machines": ["tormach"],
    },
    "system-design": {
        "headline": "Complete systems, designed and built under one roof.",
        "intro": "Tell us what the machine or system has to do. Our engineers design the mechanical structure, the electrical and the controls, document it, and build the parts in our own shop.",
        "points": [
            "Concept, layout and part selection",
            "Mechanical design with 3D models and drawings",
            "Electrical design, wiring and control panels",
            "Prototype parts printed and cut in house",
        ],
        "specs": [("You send", "A description, sketches or photos"), ("You get", "Models, drawings, schematics and parts"),
                  ("Quote", "Usually within two business days"), ("Pricing", "Fixed quote per project")],
    },
    "mechanical-blueprints": {
        "headline": "Engineering drawings you can build from.",
        "intro": "We produce dimensioned drawings, assembly drawings, cut lists and bills of materials, for new designs or for parts and machines you already have.",
        "points": [
            "Part drawings with dimensions and tolerances",
            "Assembly drawings and exploded views",
            "Cut lists and bills of materials",
            "Drawings made from existing parts or sketches",
        ],
        "specs": [("Formats", "PDF, DXF, STEP"), ("Standards", "Dimensioned to your units"),
                  ("Quote", "Usually within two business days"), ("Pricing", "Per drawing set")],
    },
    "electrical-schematics": {
        "headline": "Schematics and wiring diagrams for your electrical and control systems.",
        "intro": "We draw schematics, wiring diagrams and panel layouts so a system can be built, wired and maintained, whether it is new or already running.",
        "points": [
            "Schematics for power, control and signal circuits",
            "Wiring diagrams with wire numbers and terminals",
            "Control panel layouts and enclosure cutouts",
            "Documentation for systems already in service",
        ],
        "specs": [("Formats", "PDF, DXF"), ("Includes", "Parts list and wire schedule"),
                  ("Quote", "Usually within two business days"), ("Pricing", "Per drawing set")],
    },
    "product-design": {
        "headline": "Bring an idea. Leave with a part you can hold.",
        "intro": "Send a sketch, a photo or a description. We model it, check that it can be made on our machines, and quote the design and the parts together.",
        "points": [
            "3D modelling from sketches, photos or descriptions",
            "Design for 3D printing or laser cutting",
            "A first prototype made in our shop",
            "Changes until it fits and works",
        ],
        "specs": [("You send", "A sketch, photo or description"), ("You get", "A model, files and a prototype"),
                  ("Quote", "Usually within two business days"), ("Pricing", "Fixed quote per project")],
    },
}

CAPABILITY_BY_SLUG = {c["slug"]: c for c in CAPABILITIES}
