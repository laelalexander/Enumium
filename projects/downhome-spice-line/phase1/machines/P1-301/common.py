"""Shared data for the P1-301 drawing set: sheet factory, scales, item numbers, bought parts and hardware."""
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[4] / "skills" / "anatomy" / "tools" / "plant"))
sys.path.insert(0, str(HERE))
import mechsheet as ms  # noqa: E402
from mechsheet import mmi, fin  # noqa: E402,F401
import design as D  # noqa: E402

PROJECT = "Down Home Creole · Phase 1 · P1-301 Ribbon blender 6 cu ft (built in house) · rev B"
DWG = HERE / "drawings"; DXF = HERE / "dxf"
DWG.mkdir(exist_ok=True); DXF.mkdir(exist_ok=True)
MASS = json.loads((HERE / "cad" / "masses.json").read_text()) if (HERE / "cad" / "masses.json").exists() else {}
K = 96 / 25.4                                    # px per paper mm


def SC(n):
    return K / n


def kg(*pids):
    m = sum(MASS.get(p, 0) for p in pids)
    return f"{m:.1f} kg [{m * 2.2046:.1f} lb]"


SHEETS = []                                      # (number, title) in order


ORDER = ["P1-301-000", "P1-301-001", "P1-301-002", "P1-301-003", "P1-301-100", "P1-301-101", "P1-301-102", "P1-301-108", "P1-301-104", "P1-301-200", "P1-301-201",
         "P1-301-202", "P1-301-300", "P1-301-400", "P1-301-405", "P1-301-600", "P1-301-E01", "P1-301-E02", "P1-301-E03", "P1-301-E04", "P1-301-900"]


def sheet(number, title, **kw):
    SHEETS.append((number, title))
    kw["sheet"] = f"{ORDER.index(number) + 1} of {len(ORDER)}"
    return ms.Sheet(number=number, title=title, project=PROJECT, **kw)


SS316L = "SS 316L (ASTM A240 / A276)"
SS304 = "SS 304 (ASTM A240 / A554)"
FIN_PC = "Product contact #4, Ra ≤ 0.8 µm [32 µin]; welds ground flush; passivate ASTM A967"
FIN_NPC = "Non-contact: #4 or bead blast; welds cleaned; passivate ASTM A967"

# bought parts used on the blender: tag, description, maker, part number, qty, unit USD (estimate unless noted), note
BOUGHT = [
    ("P1-333", "Helical-bevel gearmotor 1.5 kW [2 HP], 4-pole 230/460 V 3-ph with PTC thermistors, i ≈ 43.7 (40 rpm at 60 Hz), hollow output shaft Ø45 H7 with keyway, torque arm, washdown finish",
     "NORD Drivesystems", "SK 9022.1 A (hollow shaft) - 90LP/4 TF, Ø45 bore, torque-arm kit (confirm frame with the NORD quote)", 1, 2600, "bore and gearbox width set the shaft drive journal: check against the quote drawing"),
    ("P1-334", "Flanged ball bearing unit, 4-bolt square, Ø60 bore, stainless insert and housing, food grease", "NTN / FYH / AST", "SUCF212 (stainless UCF212: L 175, J 143, M16)", 2, 190, "J 143 checked against the UCF212 catalog"),
    ("P1-335", "Packing, braided PTFE, FDA, 10 mm square, cut rings for Ø60 shaft", "Chesterton", "1724 PTFE packing 10 mm [3/8 in] (8 rings + 4 spare)", 1, 120, ""),
    ("P1-331", "Sanitary butterfly valve 4 in Tri-Clamp, 316L, EPDM, 24 V DC electric actuator with open/closed limit switches", "Valworx", "4 in sanitary butterfly + 24 V DC actuator (same family as P1-223)", 1, 1400, ""),
    ("P1-332", "Cover interlock: coded magnetic safety sensor 2 NC + 1 NO with actuator, stainless", "Schmersal", "BNS 260-02/01Z + actuator BPS 260-1", 1, 260, "wired dual channel to the safety relay in CP-301"),
    ("P1-337", "Level switch, vibronic fork for powders, PNP, 1-1/2 in Tri-Clamp process connection (high level)", "Endress+Hauser", "Soliphant FTM20 with 1-1/2 in Tri-Clamp (configure on order)", 1, 520, ""),
    ("P1-338", "Draw latch, over-centre, stainless, with keeper", "DE-STA-CO / Southco", "stainless draw latch, 100 mm reach class (confirm)", 3, 45, "drill to the latch base on assembly"),
    ("P1-339", "Cover gasket, silicone sponge FDA, 20 x 6 mm, PSA back", "generic FDA silicone", "20 x 6 mm closed-cell silicone strip, 4 m", 1, 60, ""),
    ("P1-341", "End gasket sheet, silicone FDA 3 mm, 60 A, cut to DXF P1-301-111", "generic FDA silicone", "3 mm FDA silicone sheet 700 x 700 (cut 2: 1 + spare)", 1, 70, "die/knife cut from the DXF"),
    ("P1-340", "Tri-Clamp clamps 13MHHM + EPDM gaskets: 4 in x 2 (valve, screw inlet), 1-1/2 in x 1 (level switch)", "generic sanitary", "4 in 13MHHM, 1-1/2 in 13MHHM, EPDM gaskets", 1, 80, ""),
    ("CP-301", "Blender control panel (see P1-301-E01..E04 for every component)", "built in house", "see E03 component list", 1, 2450, "components priced in the E03 list"),
]

# hardware: item, description, standard / grade, qty, where, torque
HARDWARE = [
    ("H1", "Hex bolt M16 x 50, A4-70, with 2 flat washers and nyloc nut", "ISO 4017 / ISO 7089 / ISO 7040", 8, "UCF212 to bearing plates", "120 N·m [88 lbf·ft]"),
    ("H2", "Stud M10 x 50, A4-70, with nut and washer", "DIN 976 / ISO 4032", 8, "gland studs (4 per box)", "hand tight + 1/4 turn, even; re-check after first run"),
    ("H3", "Hex bolt M12 x 110, A4-70, flat washers, nyloc nut", "ISO 4014", 4, "trough lugs through the top rails (crush sleeves)", "70 N·m [52 lbf·ft]"),
    ("H4", "Wedge anchor 1/2 in x 4-1/4 in, stainless 316", "ICC-ES listed", 16, "feet to slab, 3 in embed", "60 N·m [45 lbf·ft]"),
    ("H5", "Socket set screw (in the bearing insert)", "supplied with P1-334", 4, "bearing to shaft", "per bearing maker (typ. 13.6 N·m for M10)"),
    ("H6", "Hex bolt M16 x 40 + spring washer (gearmotor retaining screw on shaft end)", "per NORD kit", 1, "gearmotor hollow shaft to shaft end", "per NORD"),
    ("H7", "Hex bolt M16 x 70 A4-70 + rubber bushes (torque arm)", "per NORD torque-arm kit", 1, "torque arm to bracket P1-301-408", "until bushes just compress"),
    ("H8", "Pan head screw M5 x 12 A4-70 + nyloc nut", "ISO 7380", 12, "draw latches and keepers (drill on assembly)", "4 N·m"),
    ("H9", "Pan head screw M4 x 12 A4 + nyloc", "ISO 7380", 4, "interlock sensor and actuator", "1.5 N·m"),
    ("H10", "Hinge pin Ø10 h9 x 130, 316 + R-clip", "made from bar", 2, "cover hinges", "-"),
    ("H11", "Hex bolt M10 x 25 A4-70 + washers", "ISO 4017", 4, "CP-301 to panel brackets", "40 N·m"),
    ("H12", "Key DIN 6885 A 14 x 9 x 125, stainless", "DIN 6885", 1, "drive journal to gearmotor", "-"),
    ("H13", "Hex bolt M10 x 35 A4-70, 2 flat washers, nyloc nut", "ISO 4017 / ISO 7089 / ISO 7040", 15, "free-end plate to shell end ring (gasket 3 mm)", "25 N·m [18 lbf·ft], cross pattern, 2 passes"),
]

# top level item list (GA)
ITEMS = [
    (1, "P1-301-100", "Trough weldment", 1, "drawing P1-301-100"),
    (2, "P1-301-200", "Agitator weldment (shaft, 2 outer + 2 inner ribbons, 14 arms)", 1, "drawing P1-301-200"),
    (3, "P1-301-300", "Cover weldment (hinged, bag-dump opening, 4 in screw inlet)", 1, "drawing P1-301-300"),
    (4, "P1-301-400", "Frame weldment", 1, "drawing P1-301-400"),
    (5, "P1-301-501", "Gland follower", 2, "drawing P1-301-104"),
    (17, "P1-301-110", "Free-end plate with stuffing box (bolted)", 1, "drawing P1-301-108"),
    (6, "P1-334", "Flanged bearing SUCF212", 2, "bought"),
    (7, "P1-333", "Gearmotor 1.5 kW, hollow shaft Ø45", 1, "bought"),
    (8, "P1-335", "PTFE packing 10 sq, 4 rings per box", 8, "bought"),
    (9, "P1-331", "Discharge valve 4 in TC, 24 V actuator", 1, "bought"),
    (10, "P1-332", "Cover interlock sensor + actuator", 1, "bought"),
    (11, "P1-337", "High-level switch FTM20, 1-1/2 in TC", 1, "bought"),
    (12, "CP-301", "Blender control panel", 1, "drawings P1-301-E01..E04"),
    (13, "P1-338", "Draw latch with keeper", 3, "bought"),
    (14, "P1-339", "Cover gasket 20 x 6 silicone", 1, "bought, 4 m"),
    (15, "P1-340", "Tri-Clamp clamps and gaskets", 1, "bought, set"),
    (16, "H1-H12", "Hardware", 1, "drawing P1-301-600"),
]
