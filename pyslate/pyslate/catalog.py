"""What the shop offers, shown on the main page.

"instant" services are priced by uploading a file. "print" services (color
and large format printing) and "request" services (design and documentation
work) go through the project request form with artwork attached, and the shop
replies with a quote.
"""

from __future__ import annotations

# Icons are 24x24 line drawings, drawn with currentColor.
ICONS = {
    "printer": '<path d="M5 4h14v4H5z"/><path d="M12 8v3"/><path d="M9 11h6l-1 3h-4z"/><path d="M4 20h16"/><path d="M7 20v-3h10v3"/>',
    "laser": '<path d="M12 2v7"/><path d="M9 6l3 3 3-3"/><path d="M12 13l-2 3h4z"/><path d="M3 20h18"/><path d="M6 17h12v3H6z"/>',
    "metal": '<path d="M4 18l6-12h4l6 12z"/><path d="M8 14h8"/><circle cx="12" cy="10" r="1"/>',
    "mill": '<path d="M9 3h6v5H9z"/><path d="M11 8h2v5h-2z"/><path d="M12 13v2"/><path d="M4 18h16v3H4z"/><path d="M7 15h10v3H7z"/>',
    "router": '<path d="M3 5h18"/><path d="M10 5v6h4V5"/><path d="M12 11v4"/><path d="M3 19h18"/><path d="M6 15h12v4H6z"/>',
    "plasma": '<path d="M12 2v8"/><path d="M10 10h4l-1 4h-2z"/><path d="M8 17l4-3 4 3"/><path d="M3 20h18"/>',
    "mold": '<rect x="3" y="5" width="7" height="14" rx="1"/><rect x="14" y="5" width="7" height="14" rx="1"/><path d="M10 12h4"/><path d="M6 9v6M18 9v6"/>',
    "system": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="8.5" y="14" width="7" height="7" rx="1"/><path d="M6.5 10v2h11v-2"/><path d="M12 12v2"/>',
    "blueprint": '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M7 16V9h6v7"/><path d="M7 12h6"/><path d="M16 8v8"/><path d="M15 8h2M15 16h2"/>',
    "schematic": '<path d="M2 12h4l2-4 3 8 3-8 2 4h6"/><circle cx="20" cy="12" r="1"/><circle cx="4" cy="12" r="1"/>',
    "colorprint": '<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="1.5"/><path d="M7 14h10v7H7z"/><circle cx="17.5" cy="12" r=".6"/>',
    "wideformat": '<path d="M2 6h20v5H2z"/><path d="M5 11v9h14v-9"/><path d="M8 15h8M8 18h5"/><path d="M18 8.5h1.5"/>',
    "design": '<path d="M4 20l4-1 11-11-3-3L5 16z"/><path d="M14 6l3 3"/>',
}

CAPABILITIES = [
    {
        "slug": "3d-printing",
        "title": "3D Printing",
        "icon": "printer",
        "kind": "instant",
        "blurb": "Prototypes and end-use parts in PLA and PETG on Bambu Lab and Noitavonne printers.",
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
        "blurb": "Aluminium, steel and Delrin parts milled on Tormach 1100MX and 770M mills, and turned on the 8L lathe.",
    },
    {
        "slug": "cnc-routing",
        "title": "CNC Routing",
        "icon": "router",
        "kind": "instant",
        "blurb": "Large panels in plywood, MDF, HDPE and aluminium plate cut on the Tormach 24R router.",
    },
    {
        "slug": "plasma-cutting",
        "title": "Plasma Cutting",
        "icon": "plasma",
        "kind": "instant",
        "blurb": "Mild steel and aluminium plate cut on the Tormach 1300PL plasma table.",
    },
    {
        "slug": "color-printing",
        "title": "Color Printing",
        "icon": "colorprint",
        "kind": "print",
        "blurb": "Full color prints for posters, signs, photos, menus and labels, on paper, cardstock and vinyl.",
    },
    {
        "slug": "large-format-printing",
        "title": "Large Format Printing",
        "icon": "wideformat",
        "kind": "print",
        "blurb": "Banners, posters, blueprints and wall graphics up to 44 inches wide, in any length.",
    },
    {
        "slug": "injection-molding",
        "title": "Injection Molding",
        "icon": "mold",
        "kind": "request",
        "blurb": "Production runs in PP, ABS, PC and nylon on our Noitavonne molding machines. Quoted per project: mold plus per-part price.",
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

REQUEST_SERVICES = {c["slug"]: c["title"] for c in CAPABILITIES if c["kind"] in ("print", "request")}
KIND_LABELS = {"instant": "Instant quote", "print": "Priced from your artwork", "request": "Quoted by an engineer"}

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
        "intro": "We print on Bambu Lab printers and Noitavonne JG Maker printers, with the A8S taking parts up to 350 × 250 × 300 mm. Upload a model and you get a price, a lead time and a printability check in seconds.",
        "points": [
            "PLA for prototypes, fixtures and display parts",
            "PETG for tougher, heat- and moisture-resistant parts",
            "Overhang and thin-wall checks before you order",
            "Quantity discounts from 10 parts",
        ],
        "specs": [("Build volume", "Bambu: 256 × 256 × 256 mm · JG Maker A8S: 350 × 250 × 300 mm"), ("Layer height", "0.20 mm standard"),
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
        "intro": "Our metal shop runs a Tormach 1100MX and a 770M mill and an 8L lathe. Upload a 3D model and you get an estimate built from the stock block and the time to mill it. An engineer checks every machined part before we cut, and confirms the price if fixturing or tolerances change it.",
        "points": [
            "Brackets, housings, fixtures, adapters and plates",
            "Aluminium 6061, mild steel 1018 and Delrin from stock",
            "Engineer review of every part before machining",
            "Turned parts on the 8L lathe: up to 254 mm long and 100 mm across (send it to an engineer)",
            "Tight tolerances, threads and finishes: add a note and we'll quote them",
        ],
        "specs": [("1100MX travel", "457 × 279 × 413 mm"), ("770M travel", "356 × 191 × 337 mm"),
                  ("8L lathe", "254 mm long, 200 mm swing"), ("Materials", "Aluminium, mild steel, Delrin"),
                  ("Files", "STL, 3MF, OBJ (send STEP to an engineer)"), ("Lead time", "About 7 days, 3 with rush")],
        "line": "cnc",
        "machines": ["770m", "1100mx", "8l"],
    },
    "cnc-routing": {
        "headline": "Big flat parts, routed from thick sheet.",
        "intro": "The Tormach 24R router takes sheets up to 1416 × 628 mm and cuts parts too thick or too large for the lasers: cabinet panels, jigs, signs and aluminium plates. Upload a DXF or a flat model for an instant price.",
        "points": [
            "Furniture and cabinet panels, jigs, fixtures and signs",
            "Birch plywood 18 mm, MDF 12 mm, HDPE 12 mm, aluminium plate 6 mm",
            "Engraved lines are carved with a V-bit",
            "Inside corners keep the cutter's radius; tell us if they must be sharp",
        ],
        "specs": [("Work area", "1416 × 628 mm, 170 mm Z"), ("Spindle", "1.5 kW"),
                  ("Files", "DXF, or a flat STL / 3MF"), ("Lead time", "About 7 days, 3 with rush")],
        "line": "router",
        "machines": ["24r"],
    },
    "plasma-cutting": {
        "headline": "Steel plate parts, plasma cut.",
        "intro": "The Tormach 1300PL cuts brackets, base plates, gussets and signs from mild steel and aluminium plate up to a 4 × 4 ft sheet. Upload a DXF for an instant price.",
        "points": [
            "Brackets, base plates, gussets, flanges and signs",
            "Mild steel 3 mm and 6 mm, aluminium 3 mm",
            "Holes smaller than the plate thickness should be drilled: we'll flag them",
            "Pair it with our mills for tapped or precision holes",
        ],
        "specs": [("Cutting area", "1270 × 1232 mm"), ("Materials", "Mild steel, aluminium"),
                  ("Files", "DXF"), ("Lead time", "About 7 days, 3 with rush")],
        "line": "plasma",
        "machines": ["1300pl"],
    },
    "color-printing": {
        "headline": "Full color prints, from a single photo to a box of flyers.",
        "intro": "Send your artwork as a PDF or image, tell us the size, paper and quantity, and we reply with a price, usually the same business day. Prints ship with the rest of your order or are ready for pickup.",
        "points": [
            "Posters, flyers, menus, photos and presentation boards",
            "Product labels and stickers on vinyl",
            "Matte, satin and gloss paper, cardstock and adhesive vinyl",
            "We check your file for resolution and bleed before printing",
        ],
        "specs": [("Sizes", "Letter, tabloid and custom sizes"), ("Files", "PDF, PNG, JPG, TIFF, SVG"),
                  ("Artwork", "300 dpi at print size is best"), ("Quote", "Usually the same business day")],
    },
    "large-format-printing": {
        "headline": "Large format prints up to 44 inches wide.",
        "intro": "Our wide format printer takes rolls up to 44 inches (1118 mm) wide, so posters, banners, maps, blueprints and wall graphics come out in one piece at any length. Send your artwork with the size and media you want, and we reply with a price.",
        "points": [
            "Posters, trade show banners and backdrops",
            "Engineering drawings, blueprints and site plans",
            "Maps, photo enlargements and wall graphics",
            "Matte and photo paper, banner vinyl and adhesive vinyl",
            "Pair them with our design services: we draw it, then print it",
        ],
        "specs": [("Max width", "44 in (1118 mm), any length"), ("Files", "PDF, PNG, JPG, TIFF, SVG"),
                  ("Artwork", "150 dpi at full size is enough for most prints"), ("Quote", "Usually the same business day")],
    },
    "injection-molding": {
        "headline": "Injection molded parts, from mold to production run.",
        "intro": "For hundreds to thousands of identical plastic parts, molding beats printing on price per part. We run Noitavonne injection molding machines. Every project starts with an engineer's review of your part, then you get a quote for the mold and a price per part.",
        "points": [
            "Housings, caps, clips, knobs and enclosures",
            "PP, ABS, polycarbonate and nylon",
            "Design-for-molding review: draft, wall thickness, gates and ejector marks",
            "We can machine the mold in our own Tormach shop",
        ],
        "specs": [("Machine", "Noitavonne NOIT1680III, about 168 t clamp"), ("Materials", "PP, ABS, PC, PA6"),
                  ("Quote", "Mold + price per part"), ("Typical run", "500 parts and up")],
        "line": "molding",
        "machines": ["noit1680"],
        "photo": ("/static/img/shop/noit1680iii.jpg", "Our Noitavonne NOIT1680III injection molding machine"),
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
