"""Direct carrier connections: UPS, FedEx and USPS with the shop's own accounts."""

from __future__ import annotations

from .base import (  # noqa: F401
    Address, CarrierError, Http, Label, NotConfigured, Parcel, Rate, TrackInfo, parse_us_address,
)


def registry(http: Http | None = None) -> dict:
    from .fedex import FedEx
    from .ups import UPS
    from .usps import USPS

    http = http or Http()
    return {c.code: c for c in (UPS(http), FedEx(http), USPS(http))}


def configured(carriers: dict | None = None) -> dict:
    return {k: c for k, c in (carriers or registry()).items() if c.configured()}


def shop_rates(carriers: dict, ship_from: Address, ship_to: Address, parcels: list[Parcel]) -> tuple[list[Rate], dict]:
    """Rates from every connected carrier, cheapest first, plus each carrier's error if any."""
    rates, errors = [], {}
    for code, c in carriers.items():
        try:
            rates += c.rates(ship_from, ship_to, parcels)
        except CarrierError as exc:
            errors[code] = str(exc)
    rates.sort(key=lambda r: r.amount)
    return rates, errors
