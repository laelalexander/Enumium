"""Shared data for the P1-412 drawing set: sheet factory, item numbers, bought parts, hardware."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[4] / "skills" / "anatomy" / "tools" / "plant"))
sys.path.insert(0, str(HERE))
import mechsheet as ms  # noqa: E402
from mechsheet import mmi, fin, dxf_profile  # noqa: E402,F401
import design as D  # noqa: E402

PROJECT = "Down Home Creole · Phase 1 · P1-412 Bench spindle capper (built in house) · rev B"
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
ORDER = ["P1-412-000", "P1-412-001", "P1-412-002", "P1-412-003", "P1-412-100", "P1-412-200", "P1-412-300", "P1-412-400", "P1-412-500",
         "P1-412-800", "P1-412-E01", "P1-412-900"]


def sheet(number, title, **kw):
    SHEETS.append((number, title))
    kw["sheet"] = f"{ORDER.index(number) + 1} of {len(ORDER)}"
    kw.setdefault("qty", "1")
    kw.setdefault("rev", "B")
    kw.setdefault("date", "2026-11-18")
    return ms.Sheet(number=number, title=title, project=PROJECT, **kw)


SS304 = "SS 304 (ASTM A240 plate / A554 tube / A276 bar)"
FIN_NPC = "No product contact (caps on): #4 brushed or bead blast; passivate ASTM A967"
UHMW = "UHMW-PE natural, FDA (incidental contact with containers)"

# bought parts: tag, description, maker, part number, qty, unit USD (estimate unless noted), note
BOUGHT = [
    ("P1-422", "PMDC gearmotor 1/8 HP 130 V DC, about 190 rpm, 4.4 N·m [39 lbf·in], Ø1/2 in keyed output shaft down, face mount 4 x 10-32 on Ø60 [2.36 in] (confirm), "
     "with SCR speed control 120 V AC in, inhibit input, 10 kΩ pot", "Bodine Electric + KB Electronics", "42A-E series 1/8 HP parallel shaft (confirm ratio for 190 rpm) + KBMD-240D (9370)",
     1, 520, "on the carriage shelf; control in the enclosure P1-451"),
    ("P1-423", "Slip clutch adjustable 0.5-5 N·m, Ø1/2 in bores both ends, plus urethane cone chuck inserts for 53 mm and 89 mm caps (Ø100 OD x 20) and 12 mm float spring",
     "Zero-Max + capping-chuck maker", "Torq-Tender TT1 class (confirm range) + urethane inserts 53 / 89 mm (quote with caps)", 1, 520, "inserts swap with 3 set screws"),
    ("P1-424", "Linear guide MGN15H: rail 500 mm + 1 block, preload Z0; gas spring 200 N, 330 eye to eye, 120 stroke, M8 ball sockets", "HIWIN + Stabilus",
     "MGN15H1R500Z0CM (confirm) + LIFT-O-MAT 200 N 330 / 120 with M8 ball sockets", 1, 160, "rail on seat bar 106; spring base bracket 505 to shelf"),
    ("P1-450", "Push-pull toggle clamp, base mount, holding 1,360 N, 32 stroke, M10 spindle", "De-Sta-Co", "603-M (confirm)", 1, 55, "on bracket 404, pad 403 on the spindle"),
    ("P1-451", "Controls kit: polycarbonate enclosure 200 x 120 x 90 IP66 grey (stands on its end, lid toward the operator), E-stop 22 mm with 40 mm mushroom 2 NC, "
     "ON-OFF selector 1 NO, green pilot 120 V LED, DIN fuse holder 5 x 20 + 3 A T fuse, 6 DIN terminals + PE, M20 glands x 3, cord SJOOW 14/3 3 m with NEMA 5-15P",
     "Hammond + AutomationDirect", "1554 class 200 x 120 x 90 (confirm code) + GCX1131 + GCX1100 + GCX0101-120 + DN-F6 + DN-T12 (confirm)", 1, 190,
     "front-left of the base, holds the KB drive A1 on the back wall"),
    ("P1-452", "Limit switch, roller plunger, 1 NO + 1 NC, IP67, M20 entry", "Omron", "D4N-4120 class (confirm)", 1, 45, "on the column bracket, struck by the carriage at the top"),
    ("P1-453", "Lever knob DIN 319 Ø40 M10; 2 x rod end M8 female (igus KBRM-08); shoulder bolt Ø10 x 20 + 2 nylon washers", "Elesa + igus", "DIN 319-40-M10 + KBRM-08 + ISO 7379 10x20", 1, 40, ""),
    ("P1-402", "Cap torque tester (shared, see plant list)", "Mark-10", "TT03 class (plant item)", 0, 0, "check the clutch setting hourly"),
]

HARDWARE = [
    ("H1", "Hex bolt M8 x 30 A2-70 + 2 washers + nyloc", "ISO 4017 / 7089 / 7040", 4, "base 101 to the bench TBL-1", "18 N·m [13 lbf·ft]"),
    ("H2", "Socket cap screw M3 x 16 A2-70", "ISO 4762", 12, "rail to seat bar 106 (pitch 40)", "1.2 N·m"),
    ("H3", "Socket cap screw M3 x 12 A2-70 + Loctite 243", "ISO 4762", 4, "block to carriage plate 201", "1.2 N·m"),
    ("H4", "Pan screw 10-32 x 1/2 in 18-8 + split washer", "ASME B18.6.3", 4, "gearmotor face to shelf 202", "3 N·m"),
    ("H5", "Socket cap screw M5 x 25 A2 through standoffs 304", "ISO 4762", 3, "guard 303 to shelf", "3 N·m (PC: no more)"),
    ("H6", "Countersunk screw M8 x 70 A2", "ISO 10642", 2, "V-block 402 through nest 401 into base (S or J holes)", "10 N·m (UHMW)"),
    ("H7", "Socket cap screw M6 x 16 A2", "ISO 4762", 8, "toggle bracket 404 to base (4), toggle clamp to bracket (4)", "8 N·m"),
    ("H8", "Socket cap screw M8 x 16 A2", "ISO 4762", 2, "gas spring bracket 505 to base", "18 N·m"),
    ("H9", "Shoulder bolt Ø10 x 20 (M8) A2 + nyloc + 2 nylon washers", "ISO 7379", 1, "lever 501 pivot in clevis 105", "8 N·m on the thread only"),
    ("H10", "Socket cap screw M8 x 25 A2 + nyloc", "ISO 4762", 2, "rod ends to lug 204 and lever 501", "12 N·m"),
    ("H11", "Hex jam nut M16 x 1.5 A2", "ISO 8675", 1, "stop rod 503 under and over the base", "40 N·m"),
    ("H12", "Set screw M6 x 8 A2 cup point", "ISO 4029", 5, "clutch hubs on motor shaft and stub (2 + 2), chuck adapter on stub spigot (1, in the float slot)", "4 N·m + Loctite 243"),
    ("H13", "Socket cap screw M6 x 16 A2 + bonded sealing washer", "ISO 4762", 2, "enclosure bottom end wall to base (inside the box)", "3 N·m (PC)"),
    ("H14", "Socket cap screw M4 x 10 A2", "ISO 4762", 2, "limit switch to the column left face (2 x M4 rivnut)", "2 N·m"),
]

ITEMS = [
    (1, "P1-412-100", "Base weldment (base plate, column, gussets, top cap, clevis, rail seat bar)", 1, "drawing P1-412-100"),
    (2, "P1-412-200", "Carriage weldment (plate, shelf, gussets, link lug), machined after welding", 1, "drawing P1-412-200"),
    (3, "P1-412-301", "Stub shaft", 1, "drawing P1-412-300"),
    (4, "P1-412-302", "Chuck adapter", 1, "drawing P1-412-300"),
    (5, "P1-412-303", "Chuck guard, clear polycarbonate", 1, "drawing P1-412-300"),
    (6, "P1-412-304", "Guard standoffs", 3, "drawing P1-412-300"),
    (7, "P1-412-401", "Nest plate UHMW", 1, "drawing P1-412-400"),
    (8, "P1-412-402", "V-block UHMW", 1, "drawing P1-412-400"),
    (9, "P1-412-403", "Clamp pad UHMW", 1, "drawing P1-412-400"),
    (10, "P1-412-404", "Toggle clamp bracket", 1, "drawing P1-412-400"),
    (11, "P1-412-501", "Hand lever", 1, "drawing P1-412-500"),
    (12, "P1-412-502", "Link rod", 1, "drawing P1-412-500"),
    (13, "P1-412-503", "Stop rod", 1, "drawing P1-412-500"),
    (14, "P1-412-504", "Flip stop (jar)", 1, "drawing P1-412-500"),
    (15, "P1-412-505", "Gas spring base bracket", 1, "drawing P1-412-500"),
    (16, "P1-422", "Gearmotor + speed control", 1, "bought"),
    (17, "P1-423", "Slip clutch + chuck inserts", 1, "bought"),
    (18, "P1-424", "Rail + block, gas spring", 1, "bought"),
    (19, "P1-450", "Toggle clamp", 1, "bought"),
    (20, "P1-451", "Controls kit (enclosure, E-stop, switch, lamp, fuse, cord)", 1, "bought"),
    (21, "P1-452", "Carriage-up limit switch", 1, "bought"),
    (22, "P1-453", "Knob, rod ends, shoulder bolt", 1, "bought"),
    (23, "H1-H14", "Hardware", 1, "drawing P1-412-800"),
]
