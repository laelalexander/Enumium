"""Shared data for the P1-212 drawing set: sheet factory, item numbers, bought parts, hardware."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[4] / "skills" / "anatomy" / "tools" / "plant"))
sys.path.insert(0, str(HERE))
import mechsheet as ms  # noqa: E402
from mechsheet import mmi, fin  # noqa: E402,F401
import design as D  # noqa: E402

PROJECT = "Down Home Creole · Phase 1 · P1-212 Bin screw feeder (built in house, 9 off) · rev B"
DWG = HERE / "drawings"; DXF = HERE / "dxf"
DWG.mkdir(exist_ok=True); DXF.mkdir(exist_ok=True)
MASS = json.loads((HERE / "cad" / "masses.json").read_text()) if (HERE / "cad" / "masses.json").exists() else {}
K = 96 / 25.4


def SC(n):
    return K / n


def kg(*pids):
    m = sum(MASS.get(p, 0) for p in pids)
    return f"{m:.2f} kg [{m * 2.2046:.2f} lb]"


SHEETS = []
ORDER = ["P1-212-000", "P1-212-001", "P1-212-002", "P1-212-003", "P1-212-100", "P1-212-101", "P1-212-200", "P1-212-300", "P1-212-306",
         "P1-212-400", "P1-212-600", "P1-212-E01", "P1-212-E02", "P1-212-900"]


def sheet(number, title, **kw):
    SHEETS.append((number, title))
    kw["sheet"] = f"{ORDER.index(number) + 1} of {len(ORDER)}"
    kw.setdefault("qty", "1 per feeder · 9 feeders")
    return ms.Sheet(number=number, title=title, project=PROJECT, **kw)


SS316L = "SS 316L (ASTM A270 tube / A240 plate)"
SS316 = "SS 316 bar (ASTM A276), annealed"
SS304 = "SS 304 (ASTM A240)"
FIN_PC = "Product contact: ID Ra ≤ 0.8 µm [32 µin] (A270 S2 tube); welds ground flush; passivate ASTM A967"
FIN_NPC = "Non-contact: #4 or bead blast; passivate ASTM A967"

# bought parts per feeder: tag, description, maker, part number, qty, unit USD (estimate unless noted), note
BOUGHT = [
    ("P1-215", "Formed (cold-rolled) continuous screw flight, 316, OD 56 x ID 25 x pitch 56 x 3 thick, 1,110 long (20 turns), right hand",
     "Spirotech / Kase Conveyors", "continuous helicoid flight 56 x 25 x 56 x 3, 316 (quote; alternate: 20 sectional blanks per DXF P1-212-202)", 1, 180, "welded to shaft P1-212-201 in house"),
    ("P1-216", "Helical in-line gearmotor 0.25 kW 4-pole 230/460 V 3-ph, i ≈ 10.25 (165 rpm at 60 Hz), solid shaft Ø20 j6 x 40 keyed, B14 face flange (spigot Ø80, 4 x M6 on PCD 100), IP66 washdown",
     "NORD Drivesystems", "SK 072.1 - 71S/4, B14 flange C120 (confirm flange code and shaft with the NORD quote drawing)", 1, 520, "flange holes and spigot in lantern P1-212-402 follow this; check before cutting"),
    ("P1-241", "Deep-groove ball bearing, stainless, 20 x 42 x 12, sealed both sides, food grease", "SKF", "W 6004-2RS1 (stainless)", 2, 38, ""),
    ("P1-242", "Rotary lip seal 20 x 35 x 7, FDA PTFE lip, stainless case, dry-running", "Trelleborg / AHP Seals", "PTFE lip seal 20x35x7 FDA, SS case (confirm series)", 1, 45, "lip toward the product (x+)"),
    ("P1-243", "O-ring 46 x 2.5, EPDM, FDA 21 CFR 177.2600", "generic", "O-ring 46 x 2.5 EPDM 70 FDA", 2, 3, "1 fitted + 1 spare"),
    ("P1-244", "Jaw coupling, cast iron hubs, 20 mm bore 6 mm key both hubs, Hytrel spider", "Lovejoy (Timken)", "L-075 hubs 20 mm x 6 kw (2) + L-075 Hytrel spider", 1, 55, "gap per Lovejoy, 1/16 in"),
    ("P1-245", "Sanitary short weld ferrule 2.5 in, 316L, A270 tube end", "generic sanitary (14WMP)", "14WMP-2.5 316L", 1, 9, "tail end, part of barrel weldment"),
    ("P1-246", "Tri-Clamp gasket 2.5 in EPDM, FDA", "generic sanitary", "40MP-2.5 EPDM", 2, 2, "tail cap + spare"),
    ("P1-247", "Tri-Clamp clamp 2.5 in, single pin, HEX-NUT closure (tool needed: the cap guards the screw)", "generic sanitary", "13MHHS-2.5 304", 1, 14, "wing-nut clamp NOT allowed here"),
    ("P1-214", "Flexible sleeve, FDA silicone, ID 63.5 x 3 wall x 200 long, with 2 stainless band clamps (scale isolation spout to lid stub)", "generic FDA silicone", "silicone sleeve 2.5 in ID x 200 + 2 SS worm clamps 60-80", 1, 25,
     "replaces the BFM 100 boot; hopper lid P1-220 rev B: Ø64 holes on R280 with 2.5 in x 25 tube stubs"),
    ("P1-248", "Motor isolator, 3-pole 16 A, lockable OFF, stainless or polycarbonate IP66 enclosure, 1 early-break NO aux contact", "ABB", "OTP16T3M + OA1G10 aux, IP66 (confirm enclosure code)", 1, 95,
     "on the ring leg beside the bin; aux contact to the drive enable (E01)"),
]

HARDWARE = [
    ("H1", "Hex bolt M10 x 30 A2-70, 2 flat washers, nyloc nut", "ISO 4017 / 7089 / 7040", 4, "inlet flange to bin flange (gasket P1-212-501 3 mm)", "25 N·m [18 lbf·ft], cross pattern"),
    ("H2", "Socket head cap screw M6 x 16 A4-70 + spring washer", "ISO 4762", 4, "drive housing collar to end flange (tapped)", "8 N·m [6 lbf·ft]"),
    ("H3", "Socket head cap screw M6 x 20 A4-70 + spring washer", "ISO 4762", 4, "lantern front plate to housing rear flange (tapped)", "8 N·m [6 lbf·ft]"),
    ("H4", "Socket head cap screw M6 x 20 A4-70 + flat washer", "ISO 4762", 4, "gearmotor B14 flange to lantern rear plate", "8 N·m [6 lbf·ft]"),
    ("H5", "Parallel pin Ø6 m6 x 24, A1 stainless", "ISO 2338", 1, "drive pin in shaft P1-212-302 (press)", "press, 2 mm proud each side"),
    ("H6", "Retaining ring, external, 20 x 1.2, stainless", "DIN 471", 2, "bearing inner rings on the drive shaft", "-"),
    ("H7", "Retaining ring, internal, 42 x 1.75, stainless", "DIN 472", 1, "bearing outer ring in the housing", "-"),
    ("H8", "Parallel key 6 x 6 x 32, stainless", "DIN 6885 A", 2, "coupling hubs (drive shaft + gearmotor shaft if not supplied)", "-"),
    ("H9", "Button head screw M5 x 10 A4 + nyloc", "ISO 7380", 4, "coupling guard P1-212-404 to lantern bars", "3 N·m"),
    ("H10", "Set screw M6 x 8 cup point A4 (in coupling hubs)", "ISO 4029", 2, "coupling hubs over keys", "5 N·m"),
]

ITEMS = [
    (1, "P1-212-100", "Barrel weldment (tube, transition, inlet flange, end flange, spout, tail ferrule)", 1, "drawing P1-212-100"),
    (2, "P1-212-200", "Screw (shaft + formed flight), removable from the tail end", 1, "drawing P1-212-200"),
    (3, "P1-212-301", "Drive housing", 1, "drawing P1-212-300"),
    (4, "P1-212-302", "Drive shaft with drive pin", 1, "drawing P1-212-300"),
    (5, "P1-212-304", "Bearing spacers, outer + inner", 1, "drawing P1-212-300"),
    (6, "P1-212-306", "Tail end cap", 1, "drawing P1-212-306"),
    (7, "P1-212-307", "Tail bush, UHMW-PE FDA", 1, "drawing P1-212-306"),
    (8, "P1-212-400", "Lantern weldment (housing to gearmotor)", 1, "drawing P1-212-400"),
    (9, "P1-212-404", "Coupling guard, perforated", 1, "drawing P1-212-400"),
    (10, "P1-212-501", "Inlet gasket 3 mm FDA silicone", 1, "drawing P1-212-400 (DXF)"),
    (11, "P1-216", "Gearmotor 0.25 kW i ≈ 10.25", 1, "bought"),
    (12, "P1-241", "Bearing W 6004-2RS1", 2, "bought"),
    (13, "P1-242", "Lip seal 20 x 35 x 7 FDA", 1, "bought"),
    (14, "P1-243", "O-ring 46 x 2.5 EPDM FDA", 1, "bought"),
    (15, "P1-244", "Jaw coupling L-075 20/20", 1, "bought"),
    (16, "P1-247", "TC clamp 2.5 in hex nut + P1-246 gasket", 1, "bought"),
    (17, "P1-214", "Flexible sleeve 2.5 in x 200 + 2 bands", 1, "bought"),
    (18, "P1-248", "Motor isolator 16 A lockable", 1, "bought, on ring leg"),
    (19, "H1-H10", "Hardware", 1, "drawing P1-212-600"),
]
