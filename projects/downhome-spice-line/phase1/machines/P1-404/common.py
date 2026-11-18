"""Shared data for the P1-404 drawing set: sheet factory, item numbers, bought parts, hardware."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[4] / "skills" / "anatomy" / "tools" / "plant"))
sys.path.insert(0, str(HERE))
import mechsheet as ms  # noqa: E402
from mechsheet import mmi, fin, dxf_profile  # noqa: E402,F401
import design as D  # noqa: E402

PROJECT = "Down Home Creole · Phase 1 · P1-404 Wrap labeler for round containers (built in house) · rev B"
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
ORDER = ["P1-404-000", "P1-404-001", "P1-404-002", "P1-404-003", "P1-404-100", "P1-404-200", "P1-404-300", "P1-404-400",
         "P1-404-800", "P1-404-E01", "P1-404-900"]


def sheet(number, title, **kw):
    SHEETS.append((number, title))
    kw["sheet"] = f"{ORDER.index(number) + 1} of {len(ORDER)}"
    kw.setdefault("qty", "1")
    kw.setdefault("rev", "B")
    kw.setdefault("date", "2026-11-18")
    return ms.Sheet(number=number, title=title, project=PROJECT, **kw)


SS304 = "SS 304 (ASTM A240 plate / A276 bar)"
FIN_NPC = "No product contact (container closed): #4 brushed or bead blast; passivate ASTM A967"
UHMW = "UHMW-PE natural, FDA"

# bought parts: tag, description, maker, part number, qty, unit USD (estimate unless noted), note
BOUGHT = [
    ("P1-425", "Drive rollers: Ø50 x 240 face, urethane 70A 6 thick on a 304 core, Ø12 h6 shaft ends 45 (drive end, 1 x 3 key flat) and 20 (free end), "
     "run-out 0.05 TIR", "Misumi (or a roller recoverer)", "custom urethane-covered roller to drawing P1-404-200 view R (quote)", 2, 180, "both rollers alike; key flat at -x"),
    ("P1-426", "Integrated servo-stepper NEMA 23 + I/O controller + 24 V supply: ClearPath-SDSK 23 frame, Ø8 shaft, step/dir/enable/HLFB, 24-75 V DC (run at 24 V); "
     "ClearCore I/O controller; M-0 control cable 3 m; DC power cable 3 m; Mean Well LRS-150-24 (24 V 6.5 A)", "Teknic + Mean Well",
     "CPM-SDSK-2311S-RLN + CLCR-4-13 + CPM-CABLE-M0P6-120 + CPM-CABLE-PWR-MS120 + LRS-150-24 (confirm)", 1, 640, "motor on the -x plate; controller and supply in the box P1-456"),
    ("P1-427", "Label gap sensor, fork 40 wide x 40 deep, PNP 24 V, teach-in, M8 4-pin", "SICK", "WFS3-40P415 + DOL-0804-G02M (confirm)", 1, 260,
     "on the peel plate edge, window under the web"),
    ("P1-454", "Drive kit: 8 x 6001-2RS bearings; HTD 3M 9 wide pulleys: 2 x 30T Ø12 bore (rollers, belt 1), 1 x 30T Ø12 bore (roller B, belt 2), "
     "1 x 15T Ø8 bore (motor), 1 x 18T Ø12 bore (liner drive); belts 375-3M-9 and 261-3M-9; 2 x Ø40 O-ring pulleys + Ø5 PU round belt",
     "SKF / B&B Manufacturing / Misumi", "6001-2RSH + 30-3M-09 / 15-3M-09 / 18-3M-09 + 375-3M-09 + 261-3M-09 + PU round belt 5 mm (confirm)", 1, 210, ""),
    ("P1-455", "Idler roller: silicone 40A 4 thick on an aluminium tube, Ø30 x 220, 2 x 6001-2RS inside, Ø12 shaft", "Misumi (or a roller recoverer)",
     "custom silicone-covered idler Ø30 x 220 (quote)", 1, 120, "wipes the label onto the container"),
    ("P1-456", "Controls kit: PC enclosure ≈ 250 x 200 x 130 IP66 with opaque lid; E-stop 40 mm 2 NC; OFF-ON selector; S / J selector; FEED illuminated push button green 24 V; "
     "fuse holder + 3 A T fuse, DIN rail, terminals, M20 glands x 4, cord SJOOW 14/3 3 m + 5-15P", "Fibox / Spelsberg + AutomationDirect",
     "PC box 250 x 200 x 130 class (confirm) + GCX1131 + GCX1100 x2 + GCX3101-24 class + DN-F6 + DN-T12 (confirm)", 1, 230, "on the +x end of the base"),
    ("P1-457", "Start sensor: inductive M12, PNP NO, 4 mm, 24 V, M12 connector + 2 m cable", "Banner / Turck", "Bi4U-M12-AP6X-H1141 class (confirm)", 1, 55,
     "senses the +x idler arm down"),
    ("P1-458", "Knob Ø28 M8 on the idler arm; extension spring 20 N (pinch lever); 2 nylon washers Ø16; felt pad 30 x 30 x 5", "Elesa + Lee Spring + McMaster",
     "VB.639-28-M8 + LE 038E 04 S class + felt (confirm)", 1, 35, ""),
    ("LABELS", "Label rolls: 3 in core, 200 OD max, shaker 80 x 190 (web 86), jar 100 x 255 (web 106), 3 gap, wound out, permanent adhesive",
     "label printer P1-405 output / printer stock", "printed in house on P1-405 (see plant list)", 0, 0, "label roll is a consumable"),
]

HARDWARE = [
    ("H1", "Socket cap screw M6 x 20 A2-70 + washer", "ISO 4762", 4, "base 101 to the bench TBL-2", "8 N·m"),
    ("H2", "Socket cap screw M5 x 25 A2-70 (counterbored from below)", "ISO 4762", 6, "base into the side plate bottom edges (3 each)", "5 N·m"),
    ("H3", "Socket cap screw M8 x 20 A2 + washer", "ISO 4762", 4, "tie rod 104 and pivot shaft 403 ends", "15 N·m"),
    ("H4", "Socket cap screw M5 x 12 A2", "ISO 4762", 4, "motor flange to the -x plate (slots, belt 1 tension)", "4 N·m"),
    ("H5", "Socket cap screw M5 x 16 A2", "ISO 4762", 6, "bearing housings 201 to the -x plate (3 each, slots for belt 2)", "4 N·m"),
    ("H6", "Set screw M4 x 5 A2 cup point + Loctite 243", "ISO 4029", 10, "pulleys (2 each) on the rollers, motor, liner drive", "1.5 N·m"),
    ("H7", "Retaining ring DIN 471 Ø12", "DIN 471", 6, "roller shafts outside the bearings, liner drive and rewind shafts", "-"),
    ("H8", "Socket cap screw M4 x 10 A2", "ISO 4762", 3, "unwind spindle flange to the -x plate", "2.5 N·m"),
    ("H9", "Socket cap screw M5 x 10 A2", "ISO 4762", 4, "peel bracket 402 at S or J (2), peel plate to bracket (2)", "4 N·m"),
    ("H10", "Socket cap screw M5 x 12 A2", "ISO 4762", 2, "end fence 105 to the base at S or J", "3 N·m (UHMW)"),
    ("H11", "Hex nut M8 A2 + washer", "ISO 4032", 2, "guide roller shaft 307 and pinch pivot through the -x plate", "10 N·m"),
    ("H12", "Button head screw M4 x 8 A2", "ISO 7380", 6, "belt guard 204 to the -x plate on 3 standoffs", "1.5 N·m"),
    ("H13", "Socket cap screw M6 x 16 A2 + bonded sealing washer", "ISO 4762", 2, "enclosure bottom wall to the base at x 255, y ±60 (inside the box)", "3 N·m (PC)"),
    ("H14", "Set screw M5 x 6 A2 + Loctite 243", "ISO 4029", 4, "idler shaft in the arms (2), rewind hub (1), collars (1)", "2 N·m"),
]

ITEMS = [
    (1, "P1-404-101", "Base plate", 1, "drawing P1-404-100"),
    (2, "P1-404-102", "Side plate, drive side (-x)", 1, "drawing P1-404-100"),
    (3, "P1-404-103", "Side plate, free side (+x)", 1, "drawing P1-404-100"),
    (4, "P1-404-104", "Tie rod", 1, "drawing P1-404-100"),
    (5, "P1-404-105", "End fence UHMW", 1, "drawing P1-404-100"),
    (6, "P1-404-201", "Bearing housing (liner drive, rewind)", 2, "drawing P1-404-200"),
    (7, "P1-404-202", "Liner drive roller", 1, "drawing P1-404-200"),
    (8, "P1-404-203", "Pinch lever with roller", 1, "drawing P1-404-200"),
    (9, "P1-404-204", "Belt guard", 1, "drawing P1-404-200"),
    (10, "P1-404-301", "Unwind spindle", 1, "drawing P1-404-300"),
    (11, "P1-404-302", "Core hubs UHMW (unwind with flange, rewind)", 2, "drawing P1-404-300"),
    (12, "P1-404-303", "Core collars UHMW", 2, "drawing P1-404-300"),
    (13, "P1-404-304", "Brake leaf with felt", 1, "drawing P1-404-300"),
    (14, "P1-404-305", "Rewind shaft", 1, "drawing P1-404-300"),
    (15, "P1-404-306", "O-ring pulleys UHMW", 2, "drawing P1-404-300"),
    (16, "P1-404-307", "Guide roller + shaft", 1, "drawing P1-404-300"),
    (17, "P1-404-401", "Peel plate", 1, "drawing P1-404-400"),
    (18, "P1-404-402", "Peel bracket", 1, "drawing P1-404-400"),
    (19, "P1-404-403", "Pivot shaft (tie)", 1, "drawing P1-404-400"),
    (20, "P1-404-404", "Idler arms", 2, "drawing P1-404-400"),
    (21, "P1-404-405", "Idler shaft", 1, "drawing P1-404-400"),
    (22, "P1-404-406", "Start sensor bracket", 1, "drawing P1-404-400"),
    (23, "P1-425", "Drive rollers", 2, "bought"),
    (24, "P1-426", "Servo-stepper, controller, supplies", 1, "bought"),
    (25, "P1-427", "Gap sensor", 1, "bought"),
    (26, "P1-454", "Bearings, pulleys, belts", 1, "bought"),
    (27, "P1-455", "Idler roller", 1, "bought"),
    (28, "P1-456", "Controls kit", 1, "bought"),
    (29, "P1-457", "Start sensor", 1, "bought"),
    (30, "P1-458", "Knob, spring, washers, felt", 1, "bought"),
    (31, "H1-H14", "Hardware", 1, "drawing P1-404-800"),
]
