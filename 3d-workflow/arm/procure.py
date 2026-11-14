"""Procurement list: what to buy, how many, rough cost, and where it goes.   python run.py procure

Writes docs/PROCUREMENT.md and docs/procurement.csv (open the CSV in Excel/Sheets and use the Status
and Ordered columns to track orders). Quantities come from the same design data as BOM.md; fastener
counts are taken from the CAD (hole patterns per part). Prices are planning estimates in USD from
typical online listings in 2026, NOT quotes: check the current listing before ordering."""
import csv, json, math, re
from pathlib import Path
from . import build as B, hardware as H
from .actuators import BY_KEY

HERE = Path(__file__).resolve().parent.parent
DOCS = HERE / "docs"

# Planning prices (USD each, or per pack where the unit says so). Keyed by a regex on the BOM item.
PRICE = [
    (r"round tube", 32.0, "48 in length"), (r"turntable", 38.0, "each"), (r"12 mm hardened", 9.0, "each"),
    (r"6001", 1.6, "each (10-pack ~16)"), (r"clamping hub", 9.0, "each"), (r"collars", 1.5, "each"),
    (r"16T", 7.0, "each"), (r"pulley, 12 mm bore", 14.0, "each"), (r"belt, 15 mm", 9.0, "each"),
    (r"DM542", 28.0, "each"), (r"NEMA 17", 32.0, "kit"), (r"8 mm linear", 9.0, "rod + LM8UU"),
    (r"power supply", 34.0, "each"), (r"Arduino", 22.0, "each (clone ~18)"), (r"E-stop", 14.0, "each"),
    (r"limit switch", 8.0, "5-pack"), (r"Fuse", 9.0, "kit"), (r"Fasteners F01", 0.0, "see fastener lines"), (r"aluminium plate 6 mm", 24.0, "each"), (r"sheet 5052", 70.0, "each"), (r"angle 10 x 10", 6.0, "per 1 m"), (r"Neoprene", 9.0, "each"), (r"Rubber sheet", 9.0, "each"), (r"Hardwood 2 x 2", 6.0, "each"), (r"glands", 9.0, "kit"), (r"grommet", 2.0, "each"),
    (r"filament", 22.0, "per 1 kg spool"), (r"Plywood", 18.0, "each"),
]
GEARMOTOR_PRICE = {"n23_20": 85.0, "n23_20_b3": 85.0, "n23_20_b5": 85.0}   # gearmotor only; belt stage parts are separate lines


def fasteners():
    """From the fastener schedule (arm/fasteners.py), the same numbers the drawings call out."""
    from .fasteners import FASTENERS
    from .fab import fastener_count
    return [(f"{k} {d} ({std})", fastener_count(k), where) for k, (d, std, q, tq, stack, where) in FASTENERS.items()]


ELECTRICAL_EXTRA = [  # needed to wire ELE-001 but not itemised in BOM.md
    ("4-core shielded stepper cable 18 AWG", "10 m", 1, 22.0, "motor phases, twisted/shielded per ELE-001"),
    ("14 AWG silicone wire, red + black", "5 m each", 1, 14.0, "24 V and GND distribution"),
    ("22 AWG hookup wire kit", "kit", 1, 12.0, "STEP/DIR/ENA and limit switch signals"),
    ("Wire ferrule kit + crimper", "kit", 1, 25.0, "driver and PSU screw terminals"),
    ("IEC C14 inlet with switch and fuse", "each", 1, 8.0, "mains input to the PSU"),
    ("Lever terminal blocks (Wago 221 style)", "10-pack", 1, 9.0, "24 V / GND bus"),
    ("USB-B cable 2 m", "each", 1, 6.0, "Mega to PC"),
    ("100 nF ceramic capacitors", "pack", 1, 5.0, "across each limit switch (ELE-001 note)"),
    ("Cable chain or spiral wrap", "2 m", 1, 10.0, "motor cables along the arm"),
]
TOOLS = [("Calipers", "check every HW dimension"), ("12 mm reamer or drill", "shaft bores"), ("8 mm reamer or drill", "rod bores"),
         ("Hacksaw or chop saw + deburr tool", "cut tubes"), ("Drill press, V-block, 5.5 / 3.0 / 8.0 mm bits, 90° countersink", "cross-pin holes, BASE-01, legs"), ("Jigsaw or CNC router; or send fab/dxf to a laser / waterjet shop", "plates and panels"), ("Torque screwdriver 0.5-5 N·m", "fastener torques in fab/FASTENERS.md"),
         ("Soldering iron with heat-set insert tip", "F10 M4 inserts"), ("Multimeter", "motor phase pairs, wiring checks"),
         ("Hex keys, blue threadlocker", "assembly")]


def price_for(item):
    for rx, p, unit in PRICE:
        if re.search(rx, item, re.I):
            return p, unit
    return None, ""


def rows(filament_g=None):
    d = json.loads((HERE / "design" / "design.json").read_text(encoding="utf-8"))
    out = []
    drives = {j: v["drive"] for j, v in d["joints"].items()}; drives["yaw"] = "n23_20"
    for j in ("yaw", "shoulder", "elbow", "wrist"):
        dr = BY_KEY[drives[j]]
        out.append(dict(cat="Motors", item=f"NEMA 23 2.8 A stepper + 20:1 planetary gearbox ({j})", qty=1, unit="each",
                        price=GEARMOTOR_PRICE[dr.key], search="NEMA 23 stepper motor 20:1 planetary gearbox 2.8A",
                        use=f"J{['yaw','shoulder','elbow','wrist'].index(j) + 1} {j}" + (f"; {dr.ratio:g}:1 total with belt stage" if dr.ratio > 20 else ""),
                        lead="1-3 weeks if shipped from overseas"))
    for item, qty, search, use in B.AMAZON_ITEMS:
        if re.search(r"Fasteners F01", item):
            continue
        p, unit = price_for(item)
        q = qty
        if re.search(r"filament", item) and filament_g:
            q = max(1, math.ceil(filament_g * 1.25 / 1000))   # +25 % for supports, brims, a reprint
            item = f"PETG filament 1.75 mm, 1 kg (prints need {filament_g:.0f} g; +25 % allowance) + 250 g TPU 95A for jaw pads"
        cat = "Electronics" if re.search(r"driver|supply|Arduino|E-stop|limit|Fuse", item, re.I) else "Mechanical"
        if re.search(r"filament|Plywood|plate 6 mm|sheet|angle|Neoprene|Hardwood", item, re.I):
            cat = "Materials"
        out.append(dict(cat=cat, item=item, qty=q, unit=unit or "each", price=p or 0, search=search, use=use, lead=""))
    for item, qty, use in fasteners():
        if qty:
            out.append(dict(cat="Fasteners", item=item, qty=qty, unit="each", price=0.3 if "insert" in item else (0.5 if "foot" in item or "standoff" in item else 0.2),
                            search=item.split(" (")[0][4:], use=use, lead=""))
    for item, unit, qty, p, use in ELECTRICAL_EXTRA:
        out.append(dict(cat="Wiring", item=item, qty=qty, unit=unit, price=p, search=item, use=use, lead=""))
    # limit switches are sold in packs: one pack covers all five
    for r in out:
        if re.search(r"limit switch", r["item"], re.I):
            r["qty"], r["unit"], r["price"] = 1, "5-pack", 8.0
    for r in out:
        r["ext"] = round(r["qty"] * r["price"], 2)
    return out


def main(argv=None):
    rep = HERE / "print" / "REPORT.md"
    grams = None
    if rep.exists():
        m = re.search(r"Total: \*\*(\d+) g\*\*", rep.read_text(encoding="utf-8"))
        grams = float(m.group(1)) if m else None
    R = rows(grams)
    DOCS.mkdir(exist_ok=True)
    with open(DOCS / "procurement.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Category", "Item", "Qty", "Unit", "Est. unit USD", "Est. total USD", "Search / spec", "Used for", "Status", "Ordered from", "Order #", "Received"])
        for r in R:
            w.writerow([r["cat"], r["item"], r["qty"], r["unit"], f"{r['price']:.2f}", f"{r['ext']:.2f}", r["search"], r["use"], "to order", "", "", ""])
    cats = {}
    for r in R:
        cats.setdefault(r["cat"], []).append(r)
    total = sum(r["ext"] for r in R)
    L = ["# Procurement list (generated)", "",
         "Everything to buy for one arm, with planning prices. **Prices are estimates from typical online listings, not quotes;** "
         "check each listing's dimensions against `arm/hardware.py` `HW` before ordering. Track orders in "
         "[`procurement.csv`](procurement.csv) (Status, Ordered from, Order #, Received columns).", "",
         "| Category | Lines | Est. USD |", "|---|---|---|"]
    L += [f"| {c} | {len(rs)} | {sum(r['ext'] for r in rs):,.0f} |" for c, rs in cats.items()]
    L += [f"| **Total** | **{len(R)}** | **{total:,.0f}** |", "",
          "## Order first (long lead, and their measurements set the printed parts)", "",
          "1. The four NEMA 23 gearmotors, the turntable bearing and the four clamp hubs. Measure flange, pilot, shaft and bolt circles, "
          "update `HW`, run `python run.py build` and `python run.py print`, then start printing.",
          "2. Pulleys, belts, shafts, bearings: check pulley bores against the gearbox output shaft (often 14 mm) and the 12 mm joint shaft.",
          "3. Everything else can arrive while the parts print (about 50 h of printing).", ""]
    for c, rs in cats.items():
        L += [f"## {c}", "", "| Item | Qty | Unit | Est. each | Est. total | Search for | Used for |", "|---|---|---|---|---|---|---|"]
        L += [f"| {r['item']} | {r['qty']} | {r['unit']} | {r['price']:.2f} | {r['ext']:.2f} | {r['search']} | {r['use']} |" for r in rs]
        L.append("")
    L += ["## Tools (not costed)", "", "| Tool | For |", "|---|---|"] + [f"| {t} | {u} |" for t, u in TOOLS]
    L += ["", "Optional upgrades: NEMA 23 motors with 24 V holding brakes on shoulder and elbow (the arm drops on power loss), "
          "a Teensy 4.1 instead of the Mega if you need all joints at full speed together."]
    (DOCS / "PROCUREMENT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {DOCS / 'PROCUREMENT.md'} and procurement.csv: {len(R)} lines, est. ${total:,.0f}")


if __name__ == "__main__":
    main()
