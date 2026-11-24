"""Turn a routed part into a price the customer can see broken down.

    unit price = (material + machine time) x (1 + margin) x quantity break
    line total = unit price x quantity + setup fee
    quote total = sum of lines, x rush multiplier for rush, at least the minimum order
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .geometry import PartGeometry
from .routing import Route
from .shop import CNC, LASER, PRINT, Profile


@dataclass
class LinePrice:
    material: float
    machine_minutes: float
    machine: float
    setup: float
    unit_price: float
    quantity: int
    quantity_multiplier: float
    total: float

    def to_dict(self) -> dict:
        return asdict(self)


def _money(value: float) -> float:
    return round(value + 1e-9, 2)


def price_line(geom: PartGeometry, material_id: str, route: Route, quantity: int, profile: Profile) -> LinePrice | None:
    if not route.makeable or route.machine_id is None:
        return None
    material = profile.material(material_id)
    machine = profile.machine(route.machine_id)
    if material is None or machine is None:
        return None
    data = profile.data

    if route.line == PRINT:
        grams = geom.volume_mm3 / 1000.0 * material["density_g_cm3"] * data["print_fill_factor"]
        material_cost = grams / 1000.0 * material["cost_per_kg"]
        minutes = grams / data["print_grams_per_hour"] * 60.0 + 6.0  # plus heat-up and first layer
    elif route.line == LASER:
        margin = data["laser_sheet_margin_mm"]
        w, h = (geom.outline_mm or geom.extents_mm[:2])[:2]
        sheet_m2 = (w + 2 * margin) * (h + 2 * margin) / 1e6
        material_cost = sheet_m2 * material["cost_per_m2"]
        passes = material.get("passes", 1)
        minutes = geom.cut_length_mm / material["cut_speed_mm_s"] * passes / 60.0 + data["laser_overhead_minutes"]
    elif route.line == CNC:
        # Rough estimate: buy a block a little larger than the part, mill away the rest.
        m = data.get("cnc_stock_margin_mm", 3.0)
        dims = [d + 2 * m for d in geom.extents_mm[:3]]
        stock_cm3 = dims[0] * dims[1] * dims[2] / 1000.0
        part_cm3 = max(0.0, geom.volume_mm3 / 1000.0)
        material_cost = stock_cm3 * material["density_g_cm3"] / 1000.0 * material["cost_per_kg"]
        removed = max(0.0, stock_cm3 - part_cm3)
        minutes = removed / material["removal_cm3_per_min"] + data.get("cnc_program_minutes", 20.0)
    else:
        return None

    machine_cost = minutes / 60.0 * machine["rate_per_hour"]
    mult = profile.quantity_multiplier(quantity)
    unit = (material_cost + machine_cost) * (1 + data["margin"]) * mult
    setup = machine["setup_fee"]
    return LinePrice(
        material=_money(material_cost),
        machine_minutes=round(minutes, 1),
        machine=_money(machine_cost),
        setup=_money(setup),
        unit_price=_money(unit),
        quantity=quantity,
        quantity_multiplier=mult,
        total=_money(_money(unit) * quantity + setup),
    )


@dataclass
class QuoteTotal:
    subtotal: float
    rush_fee: float
    minimum_top_up: float
    total: float
    lead_days: int


def total_quote(line_totals: list[float], lead_tier: str, profile: Profile) -> QuoteTotal:
    data = profile.data
    subtotal = _money(sum(line_totals))
    rush_fee = _money(subtotal * (data["rush_multiplier"] - 1)) if lead_tier == "rush" else 0.0
    before_min = subtotal + rush_fee
    top_up = _money(max(0.0, data["minimum_order"] - before_min)) if line_totals else 0.0
    return QuoteTotal(
        subtotal=subtotal,
        rush_fee=rush_fee,
        minimum_top_up=top_up,
        total=_money(before_min + top_up),
        lead_days=int(data["lead_days"].get(lead_tier, data["lead_days"]["standard"])),
    )
