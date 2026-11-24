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
LINES = (PRINT, LASER, CNC)

DEFAULT_PROFILE: dict[str, Any] = {
    "currency": "usd",
    "margin": 0.35,
    "minimum_order": 10.00,
    "rush_multiplier": 1.5,
    "lead_days": {"standard": 7, "rush": 3},
    # Quantity at or above the key gets the multiplier.
    "quantity_breaks": {"1": 1.0, "10": 0.9, "50": 0.8},
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
        {
            # Placeholder travel (Tormach 1100-class mill: 18 x 11 x 16.25 in). Confirm the models.
            "id": "tormach",
            "name": "Tormach CNC mill",
            "line": CNC,
            "bed_mm": [457, 279, 413],
            "rate_per_hour": 75.0,
            "setup_fee": 40.0,
        },
    ],
    "materials": [
        {
            "id": "pla",
            "name": "PLA",
            "line": PRINT,
            "density_g_cm3": 1.24,
            "cost_per_kg": 22.0,
            "machines": ["bambu"],
        },
        {
            "id": "petg",
            "name": "PETG",
            "line": PRINT,
            "density_g_cm3": 1.27,
            "cost_per_kg": 25.0,
            "machines": ["bambu"],
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
        # CNC machining on the Tormach. Price = stock block + time to remove material.
        {
            "id": "al-6061",
            "name": "Aluminium 6061",
            "line": CNC,
            "density_g_cm3": 2.70,
            "cost_per_kg": 12.0,
            "removal_cm3_per_min": 8.0,
            "machines": ["tormach"],
        },
        {
            "id": "steel-1018",
            "name": "Mild steel 1018",
            "line": CNC,
            "density_g_cm3": 7.87,
            "cost_per_kg": 6.0,
            "removal_cm3_per_min": 2.5,
            "machines": ["tormach"],
        },
        {
            "id": "delrin",
            "name": "Delrin (acetal)",
            "line": CNC,
            "density_g_cm3": 1.41,
            "cost_per_kg": 18.0,
            "removal_cm3_per_min": 15.0,
            "machines": ["tormach"],
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
            problems.append(f"machine {m.get('id', '?')}: line must be 'print', 'laser' or 'cnc'")
    for mat in data["materials"]:
        mid = mat.get("id", "?")
        if mat.get("line") not in LINES:
            problems.append(f"material {mid}: line must be 'print', 'laser' or 'cnc'")
            continue
        needed = {
            PRINT: ("density_g_cm3", "cost_per_kg"),
            LASER: ("thickness_mm", "cost_per_m2", "cut_speed_mm_s"),
            CNC: ("density_g_cm3", "cost_per_kg", "removal_cm3_per_min"),
        }[mat["line"]]
        for key in ("id", "name", "machines", *needed):
            if key not in mat:
                problems.append(f"material {mid}: missing '{key}'")
        for machine_id in mat.get("machines", []):
            if machine_id not in machine_ids:
                problems.append(f"material {mid}: unknown machine '{machine_id}'")
    return problems
