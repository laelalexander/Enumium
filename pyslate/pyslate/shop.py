"""The shop profile: machines, materials and rates.

These are starting values. The shop owner edits them in the admin console
(Admin > Rates and machines), and the edited copy is stored in the database.
Values marked "confirm" are placeholders until the owner checks them.
"""

from __future__ import annotations

import copy
from typing import Any

PRINT = "print"
LASER = "laser"
CNC = "cnc"
ROUTER = "router"
PLASMA = "plasma"
MOLDING = "molding"  # quoted per project by an engineer, never instant
LINES = (PRINT, LASER, CNC, ROUTER, PLASMA, MOLDING)
# Lines that cut a 2D outline from sheet stock (priced by cut length and sheet area).
SHEET_LINES = (LASER, ROUTER, PLASMA)
LINE_LABELS = {PRINT: "3D print", LASER: "Laser", CNC: "CNC", ROUTER: "CNC router", PLASMA: "Plasma", MOLDING: "Injection molding"}

DEFAULT_PROFILE: dict[str, Any] = {
    "currency": "usd",
    "margin": 0.35,
    "minimum_order": 10.00,
    "rush_multiplier": 1.5,
    "lead_days": {"standard": 7, "rush": 3},
    # Quantity at or above the key gets the multiplier.
    "quantity_breaks": {"1": 1.0, "10": 0.9, "50": 0.8},
    # Return address printed on Pyslate's own shipping and box labels. Set the real one in
    # Admin > Rates and machines.
    "ship_from": {"name": "Pyslate", "address": "Set the shop's return address\nin Rates and machines", "phone": ""},
    "machines": [
        {
            "id": "bambu",
            "name": "Bambu Lab printer",
            "line": PRINT,
            "bed_mm": [256, 256, 256],
            "rate_per_hour": 6.0,
            "setup_fee": 3.0,
        },
        {
            # JG Maker A8S by Noitavonne, run from "Nero 8 by Noitavonne" (Nero 8 profile, COM4).
            "id": "a8s",
            "name": "JG Maker A8S (Noitavonne)",
            "line": PRINT,
            "bed_mm": [350, 250, 300],
            "rate_per_hour": 6.0,
            "setup_fee": 3.0,
        },
        {
            "id": "x1",
            "name": "xTool X1",
            "line": LASER,
            "bed_mm": [615, 320],
            "rate_per_hour": 30.0,
            "setup_fee": 5.0,
        },
        {
            "id": "m2",
            "name": "xTool M2",
            "line": LASER,
            "bed_mm": [426, 320],
            "rate_per_hour": 30.0,
            "setup_fee": 5.0,
        },
        {
            # Small dual laser (15 W diode + 5 W IR): engraves metal, cuts thin wood and acrylic.
            # Field 115 x 115 mm; the shop has the slide extension, which gives 115 x 400 mm.
            "id": "f2",
            "name": "xTool F2",
            "line": LASER,
            "bed_mm": [400, 115],
            "rate_per_hour": 25.0,
            "setup_fee": 5.0,
        },
        {
            "id": "metalfab",
            "name": "xTool MetalFab",
            "line": LASER,
            "bed_mm": [610, 610],
            "rate_per_hour": 60.0,
            "setup_fee": 10.0,
        },
        # Tormach metal shop. Envelopes are the machines' travels from Tormach's spec pages.
        {
            "id": "770m",
            "name": "Tormach 770M mill",
            "line": CNC,
            "bed_mm": [356, 191, 337],  # 14 x 7.5 x 13.25 in
            "rate_per_hour": 65.0,
            "setup_fee": 35.0,
        },
        {
            "id": "1100mx",
            "name": "Tormach 1100MX mill",
            "line": CNC,
            "bed_mm": [457, 279, 413],  # 18 x 11 x 16.25 in
            "rate_per_hour": 75.0,
            "setup_fee": 40.0,
        },
        {
            # Turned parts: up to 254 mm long, 200 mm swing over the bed (100 mm over the
            # cross slide), 25 mm bar through the 5C spindle. Assigned by the shop, not auto-routed.
            "id": "8l",
            "name": "Tormach 8L lathe",
            "line": CNC,
            "kind": "lathe",
            "bed_mm": [254, 200, 200],
            "rate_per_hour": 60.0,
            "setup_fee": 35.0,
        },
        {
            "id": "24r",
            "name": "Tormach 24R CNC router",
            "line": ROUTER,
            "bed_mm": [1416, 628, 170],  # 55.75 x 24.75 x 6.7 in travel
            "rate_per_hour": 50.0,
            "setup_fee": 20.0,
        },
        {
            # Plasma source (Hypertherm Powermax model) not confirmed yet.
            "id": "1300pl",
            "name": "Tormach 1300PL plasma table",
            "line": PLASMA,
            "bed_mm": [1270, 1232],  # 50 x 48.5 in cutting area
            "rate_per_hour": 60.0,
            "setup_fee": 20.0,
        },
        {
            # Noitavonne NOIT1680III, ~168 t clamp. bed_mm is a placeholder for the space
            # between the tie bars; confirm from the machine's spec plate.
            "id": "noit1680",
            "name": "Noitavonne NOIT1680III injection molder",
            "line": MOLDING,
            "bed_mm": [470, 470],
            "rate_per_hour": 55.0,
            "setup_fee": 150.0,
        },
    ],
    "materials": [
        {
            "id": "pla",
            "name": "PLA",
            "line": PRINT,
            "density_g_cm3": 1.24,
            "cost_per_kg": 22.0,
            "machines": ["bambu", "a8s"],
        },
        {
            "id": "petg",
            "name": "PETG",
            "line": PRINT,
            "density_g_cm3": 1.27,
            "cost_per_kg": 25.0,
            "machines": ["bambu", "a8s"],
        },
        {
            "id": "plywood-3",
            "name": "Basswood plywood 3 mm",
            "line": LASER,
            "thickness_mm": 3.0,
            "cost_per_m2": 18.0,
            "cut_speed_mm_s": 8.0,
            "passes": 1,
            "machines": ["x1", "m2", "f2"],
        },
        {
            "id": "acrylic-3",
            "name": "Cast acrylic 3 mm",
            "line": LASER,
            "thickness_mm": 3.0,
            "cost_per_m2": 40.0,
            "cut_speed_mm_s": 5.0,
            "passes": 1,
            "machines": ["x1", "m2", "f2"],
        },
        {
            "id": "mdf-3",
            "name": "MDF 3 mm",
            "line": LASER,
            "thickness_mm": 3.0,
            "cost_per_m2": 12.0,
            "cut_speed_mm_s": 7.0,
            "passes": 1,
            "machines": ["x1", "m2", "f2"],
        },
        {
            "id": "steel-1",
            "name": "Stainless steel 1 mm",
            "line": LASER,
            "thickness_mm": 1.0,
            "cost_per_m2": 90.0,
            "cut_speed_mm_s": 10.0,
            "passes": 1,
            "machines": ["metalfab"],
        },
        # Metal engraving on the F2's 5 W IR laser. The design's outline is the blank's
        # size: it is marked, not cut. Price = blank + engrave time.
        {
            "id": "engrave-stainless",
            "name": "Engrave: stainless steel blank",
            "line": LASER,
            "engrave_only": True,
            "thickness_mm": 1.0,
            "cost_per_m2": 120.0,
            "cut_speed_mm_s": 20.0,
            "passes": 3,
            "machines": ["f2"],
        },
        {
            "id": "engrave-anodized",
            "name": "Engrave: anodized aluminium blank",
            "line": LASER,
            "engrave_only": True,
            "thickness_mm": 1.0,
            "cost_per_m2": 80.0,
            "cut_speed_mm_s": 40.0,
            "passes": 1,
            "machines": ["f2"],
        },
        {
            "id": "engrave-brass",
            "name": "Engrave: brass blank",
            "line": LASER,
            "engrave_only": True,
            "thickness_mm": 1.0,
            "cost_per_m2": 160.0,
            "cut_speed_mm_s": 20.0,
            "passes": 3,
            "machines": ["f2"],
        },
        # CNC router sheet stock (24R). Priced like the laser: sheet area + cut length / feed.
        {
            "id": "router-ply-18",
            "name": "Birch plywood 18 mm",
            "line": ROUTER,
            "thickness_mm": 18.0,
            "cost_per_m2": 45.0,
            "cut_speed_mm_s": 25.0,
            "passes": 3,
            "machines": ["24r"],
        },
        {
            "id": "router-mdf-12",
            "name": "MDF 12 mm",
            "line": ROUTER,
            "thickness_mm": 12.0,
            "cost_per_m2": 20.0,
            "cut_speed_mm_s": 30.0,
            "passes": 2,
            "machines": ["24r"],
        },
        {
            "id": "router-hdpe-12",
            "name": "HDPE 12 mm",
            "line": ROUTER,
            "thickness_mm": 12.0,
            "cost_per_m2": 90.0,
            "cut_speed_mm_s": 20.0,
            "passes": 2,
            "machines": ["24r"],
        },
        {
            "id": "router-al-6",
            "name": "Aluminium plate 6 mm",
            "line": ROUTER,
            "thickness_mm": 6.0,
            "cost_per_m2": 160.0,
            "cut_speed_mm_s": 8.0,
            "passes": 4,
            "machines": ["24r"],
        },
        # Plasma (1300PL). Cut speeds are placeholders until the Powermax model is confirmed.
        {
            "id": "plasma-steel-3",
            "name": "Mild steel 3 mm (11 ga)",
            "line": PLASMA,
            "thickness_mm": 3.0,
            "cost_per_m2": 40.0,
            "cut_speed_mm_s": 40.0,
            "passes": 1,
            "machines": ["1300pl"],
        },
        {
            "id": "plasma-steel-6",
            "name": "Mild steel 6 mm (1/4 in)",
            "line": PLASMA,
            "thickness_mm": 6.0,
            "cost_per_m2": 75.0,
            "cut_speed_mm_s": 22.0,
            "passes": 1,
            "machines": ["1300pl"],
        },
        {
            "id": "plasma-alu-3",
            "name": "Aluminium 3 mm",
            "line": PLASMA,
            "thickness_mm": 3.0,
            "cost_per_m2": 70.0,
            "cut_speed_mm_s": 45.0,
            "passes": 1,
            "machines": ["1300pl"],
        },
        # Injection molding resins: shown on the site; jobs are quoted per project.
        {"id": "mold-pp", "name": "Polypropylene (PP)", "line": MOLDING, "density_g_cm3": 0.90, "cost_per_kg": 3.0, "machines": ["noit1680"]},
        {"id": "mold-abs", "name": "ABS", "line": MOLDING, "density_g_cm3": 1.05, "cost_per_kg": 4.0, "machines": ["noit1680"]},
        {"id": "mold-pc", "name": "Polycarbonate (PC)", "line": MOLDING, "density_g_cm3": 1.20, "cost_per_kg": 6.0, "machines": ["noit1680"]},
        {"id": "mold-pa6", "name": "Nylon 6 (PA6)", "line": MOLDING, "density_g_cm3": 1.14, "cost_per_kg": 5.0, "machines": ["noit1680"]},
        # CNC machining on the Tormach mills. Price = stock block + time to remove material.
        {
            "id": "al-6061",
            "name": "Aluminium 6061",
            "line": CNC,
            "density_g_cm3": 2.70,
            "cost_per_kg": 12.0,
            "removal_cm3_per_min": 8.0,
            "machines": ["770m", "1100mx", "8l"],
        },
        {
            "id": "steel-1018",
            "name": "Mild steel 1018",
            "line": CNC,
            "density_g_cm3": 7.87,
            "cost_per_kg": 6.0,
            "removal_cm3_per_min": 2.5,
            "machines": ["770m", "1100mx", "8l"],
        },
        {
            "id": "delrin",
            "name": "Delrin (acetal)",
            "line": CNC,
            "density_g_cm3": 1.41,
            "cost_per_kg": 18.0,
            "removal_cm3_per_min": 15.0,
            "machines": ["770m", "1100mx", "8l"],
        },
    ],
    # Print estimate: grams of plastic per part = volume x density x fill factor.
    "print_fill_factor": 0.45,
    "print_grams_per_hour": 12.0,
    # Extra time per laser job for travel and focusing, in minutes.
    "laser_overhead_minutes": 1.0,
    # CNC: stock is the part's box plus this much on each side, in mm; plus programming time.
    "cnc_stock_margin_mm": 3.0,
    "cnc_program_minutes": 20.0,
    # Margin added around a laser part when charging for sheet use, in mm.
    "laser_sheet_margin_mm": 5.0,
}


def default_profile() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_PROFILE)


class Profile:
    """Read-only helpers over a profile dict."""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    def material(self, material_id: str) -> dict[str, Any] | None:
        return next((m for m in self.data["materials"] if m["id"] == material_id), None)

    def machine(self, machine_id: str) -> dict[str, Any] | None:
        return next((m for m in self.data["machines"] if m["id"] == machine_id), None)

    def materials_for(self, line: str) -> list[dict[str, Any]]:
        return [m for m in self.data["materials"] if m["line"] == line]

    def quantity_multiplier(self, quantity: int) -> float:
        best = 1.0
        for threshold, mult in sorted(self.data["quantity_breaks"].items(), key=lambda kv: int(kv[0])):
            if quantity >= int(threshold):
                best = float(mult)
        return best


def validate_profile(data: dict[str, Any]) -> list[str]:
    """Return a list of problems with an edited profile; empty means it is usable."""
    problems: list[str] = []
    for key in ("margin", "minimum_order", "rush_multiplier", "machines", "materials", "quantity_breaks"):
        if key not in data:
            problems.append(f"missing '{key}'")
    if problems:
        return problems
    machine_ids = {m.get("id") for m in data["machines"]}
    for m in data["machines"]:
        for key in ("id", "name", "line", "bed_mm", "rate_per_hour", "setup_fee"):
            if key not in m:
                problems.append(f"machine {m.get('id', '?')}: missing '{key}'")
        if m.get("line") not in LINES:
            problems.append(f"machine {m.get('id', '?')}: line must be one of {', '.join(LINES)}")
    for mat in data["materials"]:
        mid = mat.get("id", "?")
        if mat.get("line") not in LINES:
            problems.append(f"material {mid}: line must be one of {', '.join(LINES)}")
            continue
        needed = {
            PRINT: ("density_g_cm3", "cost_per_kg"),
            LASER: ("thickness_mm", "cost_per_m2", "cut_speed_mm_s"),
            ROUTER: ("thickness_mm", "cost_per_m2", "cut_speed_mm_s"),
            PLASMA: ("thickness_mm", "cost_per_m2", "cut_speed_mm_s"),
            CNC: ("density_g_cm3", "cost_per_kg", "removal_cm3_per_min"),
            MOLDING: ("density_g_cm3", "cost_per_kg"),
        }[mat["line"]]
        for key in ("id", "name", "machines", *needed):
            if key not in mat:
                problems.append(f"material {mid}: missing '{key}'")
        for machine_id in mat.get("machines", []):
            if machine_id not in machine_ids:
                problems.append(f"material {mid}: unknown machine '{machine_id}'")
    return problems
