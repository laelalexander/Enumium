"""GS1 identifiers, lot codes and ZPL label builders.

Lot code format comes from the client's site: DHyyjjj-B## (year, Julian day,
batch of the day) plus a BEST BY date 24 months out (site shelf_life_months).
The GS1 company prefix is a placeholder until Down Home Creole gives theirs.
"""
from __future__ import annotations

import datetime as dt

COMPANY_PREFIX = "0000000"   # PLACEHOLDER: replace with the client's GS1 company prefix (7-10 digits)
SSCC_EXTENSION = "0"


def check_digit(digits: str) -> str:
    """GS1 mod-10 check digit for GTIN-8/12/13/14 and SSCC-18 bodies."""
    if not digits.isdigit():
        raise ValueError(f"digits only: {digits!r}")
    total = 0
    for i, ch in enumerate(reversed(digits)):
        total += int(ch) * (3 if i % 2 == 0 else 1)
    return str((10 - total % 10) % 10)


def gtin12(item_ref: int, prefix: str = COMPANY_PREFIX) -> str:
    """UPC-A for the unit, built from the company prefix and an item reference."""
    body = prefix + str(item_ref).zfill(11 - len(prefix))
    if len(body) != 11:
        raise ValueError("prefix + item reference must be 11 digits")
    return body + check_digit(body)


def gtin14(upc12: str, indicator: int = 1) -> str:
    """Case GTIN-14 from the unit UPC-A: indicator digit + 0 + first 11 digits + new check."""
    body = str(indicator) + "0" + upc12[:11]
    return body + check_digit(body)


def sscc(serial: int, prefix: str = COMPANY_PREFIX, ext: str = SSCC_EXTENSION) -> str:
    body = ext + prefix + str(serial).zfill(16 - len(prefix))
    if len(body) != 17:
        raise ValueError("serial too long for this prefix")
    return body + check_digit(body)


def lot_code(day: dt.date, batch_of_day: int) -> str:
    return f"DH{day:%y}{day.timetuple().tm_yday:03d}-B{batch_of_day:02d}"


def best_by(day: dt.date, months: int = 24) -> dt.date:
    m = day.month - 1 + months
    y, m = day.year + m // 12, m % 12 + 1
    for d in (day.day, 30, 29, 28):
        try:
            return dt.date(y, m, d)
        except ValueError:
            continue
    raise ValueError(day)


def unit_code_lines(lot: str, bb: dt.date) -> list[str]:
    """Two lines the TTO coder (TT-407) prints on the label."""
    return [f"LOT {lot}", f"BEST BY {bb:%b %d %Y}".upper()]


def gs1_128(ais: list[tuple[str, str]]) -> str:
    """Human-readable GS1-128 string; FNC1 separators are added by the ZPL >8 below."""
    return "".join(f"({ai}){v}" for ai, v in ais)


def _zpl_gs1(ais: list[tuple[str, str]]) -> str:
    # ZPL code 128 with FNC1 start (>;>8) and FNC1 after each variable-length AI (10 = lot)
    out = ""
    for i, (ai, v) in enumerate(ais):
        out += ai + v
        if ai in ("10", "21", "37") and i < len(ais) - 1:
            out += ">8"
    return ">;>8" + out


def case_label_zpl(product: str, sku: str, gtin: str, lot: str, bb: dt.date, count: int, net_each: str) -> str:
    """4 x 6 in case label for CTM 360a / ZE511 (PA-414): GTIN-14, best-by (15), lot (10), count (30)."""
    ais = [("01", gtin), ("15", f"{bb:%y%m%d}"), ("10", lot)]
    return "\n".join([
        "^XA^CI28^PW812^LL1218",
        f"^FO40,40^A0N,60,60^FD{product}^FS",
        f"^FO40,115^A0N,36,36^FDSKU {sku}   {count} x {net_each}^FS",
        f"^FO40,170^A0N,36,36^FDLOT {lot}   BEST BY {bb:%Y-%m-%d}^FS",
        f"^FO40,260^BY3^BCN,220,N,N,N,D^FD{_zpl_gs1(ais)}^FS",
        f"^FO40,500^A0N,32,32^FD{gs1_128(ais)}^FS",
        f"^FO40,560^BY3^BCN,160,Y,N,N^FD(30){count:02d}^FS",
        "^XZ",
    ])


def pallet_label_zpl(sscc18: str, gtin: str, lot: str, bb: dt.date, cases: int) -> str:
    """GS1 logistics label: SSCC (00) as the bottom symbol, content block above."""
    top = [("02", gtin), ("15", f"{bb:%y%m%d}"), ("10", lot)]
    return "\n".join([
        "^XA^CI28^PW812^LL1218",
        "^FO40,30^A0N,40,40^FDDown Home Creole^FS",
        f"^FO40,90^A0N,34,34^FDSSCC {sscc18}^FS",
        f"^FO40,140^A0N,34,34^FDCONTENT {gtin}   COUNT {cases}^FS",
        f"^FO40,190^A0N,34,34^FDLOT {lot}   BEST BY {bb:%Y-%m-%d}^FS",
        f"^FO40,280^BY3^BCN,200,N,N,N,D^FD{_zpl_gs1(top + [('37', str(cases))])}^FS",
        f"^FO40,520^A0N,30,30^FD{gs1_128(top + [('37', str(cases))])}^FS",
        f"^FO40,820^BY4^BCN,240,N,N,N,D^FD>;>800{sscc18}^FS",
        f"^FO40,1080^A0N,34,34^FD(00){sscc18}^FS",
        "^XZ",
    ])


def bag_label_zpl(bag_id: str, formula: str, lot: str, kg: float, status: str, allergens: str) -> str:
    """Bulk bag (FIBC) tag printed at BF-306 by WS-206A, scanned at BU-401/BU-502."""
    return "\n".join([
        "^XA^CI28^PW812^LL1218",
        f"^FO40,40^A0N,70,70^FD{bag_id}^FS",
        f"^FO40,130^A0N,44,44^FD{formula}^FS",
        f"^FO40,190^A0N,44,44^FDLOT {lot}   {kg:.1f} kg^FS",
        f"^FO40,250^A0N,44,44^FDALLERGENS: {allergens or 'none'}^FS",
        f"^FO40,330^GB730,120,6^FS^FO60,350^A0N,90,90^FD{status}^FS",
        f"^FO40,500^BQN,2,8^FDQA,{bag_id}^FS",
        "^XZ",
    ])
