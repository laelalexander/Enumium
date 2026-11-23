"""Decide which production line and machine makes a part.

The rule is the shop's: sort first, then route.
  1. A sheet part (one thickness, straight sides) or a 2D drawing, in a
     laser material whose thickness matches, that fits a laser bed -> laser line.
  2. Anything with real 3D shape, in a print material, that fits a printer -> print line.
  3. A part that cannot be made as chosen -> manual review by the shop.
"""

from __future__ import annotations

from dataclasses import dataclass

from .geometry import PartGeometry
from .shop import LASER, PRINT, Profile

THICKNESS_TOLERANCE_MM = 0.25
REVIEW = "review"


@dataclass
class Route:
    line: str  # "print", "laser" or "review"
    machine_id: str | None
    reason: str

    @property
    def makeable(self) -> bool:
        return self.line != REVIEW


def _fits(part_dims: list[float], bed: list[float]) -> bool:
    """Part fits the bed in some axis-aligned orientation."""
    part = sorted(part_dims, reverse=True)
    space = sorted(bed, reverse=True)
    return len(part) <= len(space) and all(p <= s for p, s in zip(part, space))


def compatible_materials(geom: PartGeometry, profile: Profile) -> list[dict]:
    """Materials a customer may pick for this part, in profile order."""
    options = []
    for mat in profile.data["materials"]:
        if mat["line"] == PRINT and geom.kind == "mesh":
            options.append(mat)
        elif mat["line"] == LASER and geom.flat:
            if geom.kind == "drawing" or abs(mat["thickness_mm"] - (geom.thickness_mm or 0)) <= THICKNESS_TOLERANCE_MM:
                options.append(mat)
    return options


def default_material(geom: PartGeometry, profile: Profile) -> str | None:
    """Laser first for sheet parts (faster and cheaper), print otherwise."""
    options = compatible_materials(geom, profile)
    laser = [m for m in options if m["line"] == LASER]
    if laser:
        return laser[0]["id"]
    return options[0]["id"] if options else None


def route(geom: PartGeometry, material_id: str | None, profile: Profile) -> Route:
    material = profile.material(material_id) if material_id else None
    if material is None:
        return Route(REVIEW, None, "No material fits this part. The shop will review it and contact you.")

    if material["line"] == LASER:
        if not geom.flat:
            return Route(REVIEW, None, f"{material['name']} is cut from sheet, but this part is not flat.")
        if geom.kind == "mesh" and abs(material["thickness_mm"] - (geom.thickness_mm or 0)) > THICKNESS_TOLERANCE_MM:
            return Route(
                REVIEW,
                None,
                f"The part is {geom.thickness_mm:.1f} mm thick but {material['name']} is "
                f"{material['thickness_mm']:.1f} mm.",
            )
        for machine_id in material["machines"]:
            machine = profile.machine(machine_id)
            if machine and _fits(geom.outline_mm or geom.extents_mm[:2], machine["bed_mm"][:2]):
                return Route(LASER, machine_id, f"Flat part, cut on the {machine['name']}.")
        return Route(REVIEW, None, "The part is larger than the laser bed. The shop will review it.")

    if geom.kind != "mesh":
        return Route(REVIEW, None, "A 2D drawing can only be laser cut. Pick a sheet material.")
    for machine_id in material["machines"]:
        machine = profile.machine(machine_id)
        if machine and _fits(geom.extents_mm, machine["bed_mm"]):
            return Route(PRINT, machine_id, f"3D part, printed on the {machine['name']}.")
    return Route(REVIEW, None, "The part is larger than the printer's build volume. The shop will review it.")
