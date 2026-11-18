"""Shared data for the P1-406 drawing set: sheet factory, item numbers, bought parts, hardware."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[4] / "skills" / "anatomy" / "tools" / "plant"))
sys.path.insert(0, str(HERE))
import mechsheet as ms  # noqa: E402
from mechsheet import mmi, fin, dxf_profile  # noqa: E402,F401
import design as D  # noqa: E402

PROJECT = "Down Home Creole · Phase 1 · P1-406 Metal detector conveyor (built frame, used head) · rev B"
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
ORDER = ["P1-406-000", "P1-406-001", "P1-406-002", "P1-406-003", "P1-406-100", "P1-406-200", "P1-406-300", "P1-406-400",
         "P1-406-800", "P1-406-E01", "P1-406-900"]


def sheet(number, title, **kw):
    SHEETS.append((number, title))
    kw["sheet"] = f"{ORDER.index(number) + 1} of {len(ORDER)}"
    kw.setdefault("qty", "1")
    kw.setdefault("rev", "B")
    kw.setdefault("date", "2026-11-18")
    return ms.Sheet(number=number, title=title, project=PROJECT, **kw)


SS304 = "SS 304 (ASTM A240 sheet + plate / A554 tube / A276 bar)"
FIN_NPC = "No product contact (pack closed): #4 brushed or bead blast; passivate ASTM A967"
UHMW = "UHMW-PE natural, FDA"

# bought parts: tag, description, maker, part number, qty, unit USD (estimate unless noted), note
BOUGHT = [
    ("P1-418", "Metal detector search head, aperture 300 W x 250 H (12 x 10 in) or the nearest larger, integral control, relay outputs DETECT and FAULT, 120 V; "
     "used, refurbished, with test pieces Fe 1.5 / NFe 2.0 / SS 2.5 and the maker's validation", "Fortress Technology (or Mettler-Toledo Safeline, Loma)",
     "Stealth / Phantom head + control (used, Sigma Equipment) (confirm aperture, housing and lug positions before cutting P1-406-104)", 1, 8500,
     "head stand P1-406-104 is drawn for a 520 W x 480 H x 200 L housing with lugs at y ±290: re-dimension to the actual head"),
    ("P1-419", "Belt: PU 2 mm FDA white, 152 [6 in] wide, 3,035 + splice allowance, open ended, finger-spliced in place (the belt passes through the closed head aperture); 4 x flange bearing UCFL204 stainless, Ø20 bore, 4-bolt",
     "Ammeraal Beltech / Habasit + NTN or SKF", "Ropanyl FDA 2 mm 152 wide, on-site finger splice by the supplier or hot-press kit (quote) + SUCFL204 (confirm)", 1, 650, "no metal lacing (inside the head); length set at the tail take-up ±15"),
    ("P1-420", "Right-angle hollow-shaft gearmotor 1/8 HP 115 V 1-ph, ≈ 85 rpm, Ø20 mm bore with key, torque arm mount, IP55", "Bison / Nord / Bodine",
     "Bison 017-656 class or Nord SK 1SI31 + 1-ph motor (confirm bore 20 mm and speed)", 1, 520, "on the drive pulley shaft, -y side; torque arm P1-406-401"),
    ("P1-421", "Reject pusher: linear actuator 24 V DC, 150 stroke, ≈ 38 mm/s at 100 N, internal limits; 2 relays 24 V DPDT for run and reverse",
     "Progressive Automations + Omron", "PA-14-6-35 (150 mm, 35 lb high speed, 24 V option) + G2R-2-SND-24 x 2 with sockets (confirm)", 1, 180, "pushes the pack into the locked bin"),
    ("P1-459", "Controls kit: PC enclosure ≈ 250 x 200 x 130 IP66; CLICK PLC 8 DC in / 6 DC out 24 V; Mean Well LRS-75-24; motor contactor 24 V DC coil 9 A; E-stop 40 mm 2 NC; "
     "START green, STOP red, RESET key switch (supervisor), fuse 6 A T, terminals, M20 glands x 5, cord SJOOW 14/3 3 m + 5-15P", "AutomationDirect + Mean Well",
     "C0-00DD2-D + C0-08ND3 (confirm I/O) + LRS-75-24 + DC1-09-10-24 class + GCX1131 + GCX1101 / GCX1103 + GCX1300-key + DN-F6 + DN-T12", 1, 520, "on the infeed -y legs"),
    ("P1-460", "Sensors: 2 x retro-reflective photo eye M18 PNP polarised with reflectors (pack at reject, bin entry), lid reed switch NC, M12 cables 2 m",
     "Banner / AutomationDirect", "QS18VP6LP + BRT-32X20AM x 2 + reed switch SR class (confirm)", 1, 210, "B1 at the reject, B2 in the bin slot, B3 on the lid"),
    ("P1-461", "Stack light 3 colour red / amber / green + buzzer 24 V DC, Ø40, pole mount", "Patlite / AutomationDirect", "LR4-302QJBW class (confirm)", 1, 160, "on the pole P1-406-403"),
    ("P1-462", "Hardware kit: 4 levelling feet M16 Ø80 pad; padlock hasp + 2 padlocks keyed alike (QA holds the key); G10 pad 80 x 70 x 6 + 4 nylon shoulder bushes; "
     "nylon screws M5 x 16 (20); rubber bush for the torque arm", "Elesa + McMaster", "LV.F-80-M16 class + hasp + 2 padlocks + G10 + nylon (confirm)", 1, 140, ""),
]

HARDWARE = [
    ("H1", "Hex screw M8 x 20 A2-70 + 2 washers + nut", "ISO 4017", 8, "spine top plates to the leg braces (2 each); head stand beam to the spine (4)", "15 N·m"),
    ("H2", "Hex screw M10 x 25 A2-70 + washer + nyloc", "ISO 4017", 8, "flange bearings UCFL204 to the side plates (4 each end; tail in slots)", "25 N·m"),
    ("H3", "Hex screw M10 x 60 A2 + 2 nuts", "ISO 4017", 2, "tail take-up push screws in the lugs", "lock nut 20 N·m"),
    ("H4", "Socket cap screw M6 x 16 A2", "ISO 4762", 8, "FRP rail clips to the side plates (2 each)", "6 N·m"),
    ("H5", "Nylon screw M5 x 16 + nylon nut", "PA 6.6", 20, "UHMW bed to the FRP rails, FRP rails to the clips (inside the MFZ: no metal)", "hand tight"),
    ("H6", "Socket cap screw M5 x 12 A2", "ISO 4762", 12, "guide strips to the guide brackets; brackets to the side plates (slots S / J)", "4 N·m"),
    ("H7", "Socket cap screw M8 x 25 A2 + nylon shoulder bush + washer", "ISO 4762", 4, "head lugs to the stand top plates (insulated side on the G10 pad)", "10 N·m"),
    ("H8", "Socket cap screw M6 x 20 A2", "ISO 4762", 6, "pusher bracket (4) and B1 bracket (2) to the side plate", "8 N·m"),
    ("H9", "Clevis pin Ø6 + R-clip", "ISO 2341", 2, "actuator rear clevis and rod end to the paddle", "-"),
    ("H10", "Socket cap screw M6 x 16 A2", "ISO 4762", 4, "controls box bracket to the leg and box", "4 N·m (PC)"),
    ("H11", "U-bolt M6 for 25 tube + nuts", "DIN 3570", 2, "beacon pole to its bracket", "6 N·m"),
    ("H12", "Set screw M6 x 8 A2 + Loctite 243", "ISO 4029", 2, "gearmotor bore on the shaft key (+ key 6 x 6 x 30)", "4 N·m"),
    ("H13", "Hex screw M8 x 20 A2 + rubber bush", "ISO 4017", 1, "torque arm to the outfeed leg", "8 N·m (do not crush the bush)"),
]

ITEMS = [
    (1, "P1-406-101", "Infeed end frame weldment", 1, "drawing P1-406-100"),
    (2, "P1-406-102", "Outfeed end frame weldment", 1, "drawing P1-406-100"),
    (3, "P1-406-103", "Spine", 1, "drawing P1-406-100"),
    (4, "P1-406-104", "Head stand", 1, "drawing P1-406-100"),
    (5, "P1-406-201", "Drive pulley", 1, "drawing P1-406-200"),
    (6, "P1-406-202", "Tail pulley", 1, "drawing P1-406-200"),
    (7, "P1-406-203", "Take-up screws", 2, "drawing P1-406-200"),
    (8, "P1-406-204", "FRP rails", 2, "drawing P1-406-200"),
    (9, "P1-406-205", "Rail clips", 4, "drawing P1-406-200"),
    (10, "P1-406-206", "UHMW slider bed", 1, "drawing P1-406-200"),
    (11, "P1-406-207", "Guide strips UHMW", 6, "drawing P1-406-200"),
    (12, "P1-406-208", "Guide brackets", 6, "drawing P1-406-200"),
    (13, "P1-406-301", "Pusher bracket", 1, "drawing P1-406-300"),
    (14, "P1-406-302", "Pusher paddle UHMW", 1, "drawing P1-406-300"),
    (15, "P1-406-303", "Locked reject bin", 1, "drawing P1-406-300"),
    (16, "P1-406-304", "Eye and reflector brackets", 2, "drawing P1-406-300"),
    (17, "P1-406-401", "Torque arm", 1, "drawing P1-406-400"),
    (18, "P1-406-402", "Controls box bracket", 1, "drawing P1-406-400"),
    (19, "P1-406-403", "Beacon pole", 1, "drawing P1-406-400"),
    (20, "P1-418", "Metal detector head (used)", 1, "bought"),
    (21, "P1-419", "Belt + flange bearings", 1, "bought"),
    (22, "P1-420", "Gearmotor", 1, "bought"),
    (23, "P1-421", "Reject pusher + relays", 1, "bought"),
    (24, "P1-459", "Controls kit", 1, "bought"),
    (25, "P1-460", "Sensors", 1, "bought"),
    (26, "P1-461", "Stack light", 1, "bought"),
    (27, "P1-462", "Feet, locks, insulators", 1, "bought"),
    (28, "H1-H13", "Hardware", 1, "drawing P1-406-800"),
]
