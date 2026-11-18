"""Shared data for the P1-401 drawing set: sheet factory, item numbers, bought parts, hardware."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[4] / "skills" / "anatomy" / "tools" / "plant"))
sys.path.insert(0, str(HERE))
import mechsheet as ms  # noqa: E402
from mechsheet import mmi, fin  # noqa: E402,F401
import design as D  # noqa: E402

PROJECT = "Down Home Creole · Phase 1 · P1-401 Servo auger filler (built in house) · rev B"
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
ORDER = ["P1-401-000", "P1-401-001", "P1-401-002", "P1-401-003", "P1-401-100", "P1-401-101", "P1-401-200", "P1-401-300", "P1-401-301",
         "P1-401-400", "P1-401-500", "P1-401-600", "P1-401-700", "P1-401-800", "P1-401-E01", "P1-401-E02", "P1-401-E03", "P1-401-900"]


def sheet(number, title, **kw):
    SHEETS.append((number, title))
    kw["sheet"] = f"{ORDER.index(number) + 1} of {len(ORDER)}"
    kw.setdefault("qty", "1")
    kw.setdefault("rev", "B")
    kw.setdefault("date", "2026-11-18")
    return ms.Sheet(number=number, title=title, project=PROJECT, **kw)


SS316L = "SS 316L (ASTM A240 sheet/plate, A270 tube)"
SS304 = "SS 304 (ASTM A240 / A276)"
FIN_PC = "Product contact: 2B sheet, #4 polish Ra ≤ 0.8 µm [32 µin]; welds ground flush; passivate ASTM A967"
FIN_NPC = "Non-contact: #4 brushed or bead blast; passivate ASTM A967"

# bought parts: tag, description, maker, part number, qty, unit USD (estimate unless noted), note
BOUGHT = [
    ("P1-413", "AC servo 750 W, 80 mm flange (Ø70 pilot, 4 x M6 on Ø90), Ø19 keyed shaft, 2.39 N·m rated / 7.16 peak, 3,000 rpm, with drive 200-230 V 1-ph, STO, RS-485 Modbus, 3 m motor + encoder cables",
     "AutomationDirect", "SureServo2 SV2L-207B motor + SV2A-2075 drive + SVC2 cables (confirm shaft and flange before machining the bridge)", 1, 1350, "drive on the back panel; motor on bridge P1-401-307"),
    ("P1-414", "Agitator gearmotor 1/4 HP 115 V 1-ph, about 60 rpm, face-mount, output shaft Ø5/8 in keyed, 4 x 1/4-20 on Ø3.75 in (confirm)", "Bison Gear & Engineering",
     "011-series parallel shaft 1/4 HP 60 rpm (confirm flange; head plate slots are 9 x 19 on 90 sq)", 1, 420, "on the head plate, shaft down, chain under the plate"),
    ("P1-415", "Auger tooling, 2 sets to drawing P1-401-600: S (shaker) 27 OD auger + 1.25 in tube, J (jar/pouch/tub) 46 OD auger + 2 in tube; 316, M16 x 1.5 LH top thread",
     "All-Fill Inc.", "custom auger + funnel tube to P1-401-600 (quote with blend samples)", 2, 650, "per set: auger + tube with 2.5 in TC top"),
    ("P1-416", "Filler controls: CLICK PLUS PLC C2-03CPU-2 + 8 in / 8 out DC module + C-more Micro 3 in HMI", "AutomationDirect", "C2-03CPU-2 + C0-16CDD2 + EA3-S3ML (confirm I/O module)", 1, 620,
     "PLC on the back panel DIN rail; HMI in pod P1-401-106"),
    ("P1-417", "Foot switch, guarded, 1 NO + 1 NC, IP68, 3 m cord", "Linemaster", "632-S class (confirm)", 1, 90, "cord through gland M20 in the cabinet back"),
    ("P1-430", "Ball bearings: 2 x 6205-2RS (spindle), 2 x 6008-2RS (agitator hub), food-grade grease", "SKF", "6205-2RSH/C3GJN + 6008-2RS1 (H1 grease)", 1, 85, "1 set"),
    ("P1-431", "Timing drive HTD 5M 15 wide: pulley 20T bore Ø19 key 6 (servo), pulley 40T bore Ø20 key 6 (spindle), belt 450-5M-15", "Gates / B&B Manufacturing",
     "20-5M-15 + 40-5M-15 (finished bore) + 450-5M-15 belt", 1, 95, "spindle pulley held by M10 end bolt + washer"),
    ("P1-432", "Roller chain drive #40 stainless: sprocket 15T (bore 5/8 in key), sprocket 30T plate (bored Ø81 H7, 4 x Ø6.5 on Ø100), chain #40 SS 52 links + connecting link",
     "Tsubaki / Martin Sprocket", "40SS 15T B-hub + 40SS 30T A-plate (bore to drawing) + RS40-SS x 52L", 1, 140, "30T plate bolts to hub P1-401-304"),
    ("P1-433", "Lip seals 25 x 40 x 7, FKM or PTFE, FDA", "SKF / Trelleborg", "25x40x7 HMSA10 V (FDA) or PTFE lip", 2, 18, "hub P1-401-304 bottom and cap P1-401-308"),
    ("P1-434", "Index plunger M16 x 1.5, pin Ø10, pull knob with rest position, stainless", "Elesa-Ganter", "GN 617-10-AK-NI (confirm)", 1, 38, "in block P1-401-705, engages bar P1-401-704"),
    ("P1-435", "Container sensor: diffuse photoelectric 18 mm, 24 V DC PNP, IP69K, 2 m M12 cable", "Banner Engineering", "QS18VP6D + MQDEC2-506 (confirm range ≈ 100 mm)", 1, 95,
     "bracket P1-401-706 on the stage; looks across the stage at 25 above it"),
    ("P1-436", "Safety relay 24 V DC, dual channel, 3 NO safety + 1 NC aux, monitored manual reset", "Pilz", "PNOZ s4 24VDC 3 n/o 1 n/c (750104)", 1, 230, "E-stop + flap interlock; STO to the servo, agitator contactor"),
    ("P1-437", "22 mm operators: E-stop 40 mm mushroom 2 NC, blue reset 1 NO, green and red LED pilot lights 24 V", "AutomationDirect", "GCX1131-24 (E-stop) + GCX1102 + GCX0102 x2 (confirm)", 1, 85,
     "in pod P1-401-106"),
    ("P1-438", "Coded magnetic safety switch 2 NC, M12 connector, IP69K, for the scoop flap", "Schmersal", "BNS 260-02z-ST + BPS 260-1 actuator (confirm)", 1, 120, "switch on the lid, actuator on the flap"),
    ("P1-439", "Disconnect switch 25 A 2-pole, lockable OFF, side-mount handle", "ABB", "OT25F3 + OHB45J6 handle + OXP6X shaft (confirm)", 1, 75, "on the cabinet right side"),
    ("P1-440", "Control transformer 750 VA 208 V / 120 V", "Hammond", "PH750MQMJ (confirm)", 1, 160, "120 V for the gearmotor and the 24 V supply (4.3 A load)"),
    ("P1-441", "Breakers and motor protection: F1 S202-C10 (servo drive), F2 S202-D8 (T1 primary), F3 S201-C8 (120 V), Q2 MS116-4.0 + HKF1-11 (agitator), KM1 AF09-30-10-13 24 V DC coil",
     "ABB", "S202-C10, S202-D8, S201-C8, MS116-4.0, HKF1-11, AF09-30-10-13", 1, 260, "on the back panel DIN rail"),
    ("P1-442", "Power supply 24 V DC 2.5 A, DIN rail", "AutomationDirect", "PSB24-060S (confirm)", 1, 45, ""),
    ("P1-443", "Levelling feet M12, Ø60 pad, stainless, 100 mm thread", "Elesa-Ganter", "LMT-60-M12x100 inox (confirm)", 4, 22, "into the base plate weld nuts"),
    ("P1-444", "Cabinet hardware: 2 lift-off hinges SS, 1 quarter-turn latch SS with handle, door gasket FDA silicone 2 m", "Southco", "C6-1-1 hinges + E3-5 latch + FDA gasket (confirm)", 1, 70, ""),
    ("P1-445", "TC clamps 2.5 in heavy-duty wing nut 304 + EPDM FDA gaskets (tooling and agitator)", "generic sanitary", "13MHHM-2.5 + 40MP-U250 (confirm)", 2, 18, "1 tooling, 1 agitator; spare gaskets x 4"),
    ("P1-446", "Cable glands M25 + 2 x M20 nylon IP68, 2 m DIN rail 35, wire duct, terminals", "Phoenix Contact", "UT 4 terminals + glands (confirm)", 1, 90, ""),
]

HARDWARE = [
    ("H1", "Hex bolt M12 x 40 A2-70 + 2 washers + nyloc", "ISO 4017 / 7089 / 7040", 4, "column base 202 through top 102 and backing 107", "70 N·m [52 lbf·ft]"),
    ("H2", "Hex bolt M10 x 30 A2-70 + spring washer", "ISO 4017 / DIN 127", 4, "head plate 301 to cap 203 (tapped)", "45 N·m [33 lbf·ft]"),
    ("H3", "Socket cap screw M8 x 25 A2-70", "ISO 4762", 4, "spindle housing 302 to head plate (tapped)", "20 N·m [15 lbf·ft]"),
    ("H4", "Socket cap screw M6 x 16 A2-70", "ISO 4762", 4, "servo to bridge flange 307", "8 N·m"),
    ("H5", "Hex bolt M10 x 25 A2-70 + washer, into the posts (M10 x 20 deep)", "ISO 4017 / 7089", 4, "bridge 307 to head plate from below (slots: belt tension)", "45 N·m"),
    ("H6", "Hex bolt 1/4-20 x 3/4 in 18-8 + washer + nyloc", "ASME B18.2.1", 4, "gearmotor to head plate (slots: chain tension)", "8 N·m [6 lbf·ft]"),
    ("H7", "Socket cap screw M6 x 16 A2-70 + thread lock", "ISO 4762", 4, "30T sprocket plate to hub 304", "8 N·m"),
    ("H8", "Hex bolt M10 x 25 A2 + Ø30 washer + thread lock", "ISO 4017 / 7093", 1, "40T pulley on the spindle (end bolt)", "35 N·m"),
    ("H9", "Retaining rings DIN 471 Ø25 (spindle), DIN 471 Ø40 (spigot), DIN 472 Ø52 (housing)", "DIN 471 / 472", 3, "bearing location", "-"),
    ("H10", "Countersunk screw M6 x 16 A2 + nyloc", "ISO 10642 / 7040", 8, "bushing blocks 703 under the top", "6 N·m"),
    ("H11", "Socket cap screw M4 x 16 A2 (cap 308, 4) / M5 x 10 A2 (sensor bracket 706, 2)", "ISO 4762", 6, "bearing cap; sensor bracket", "3 / 4 N·m"),
    ("H12", "Button head M6 x 12 A2", "ISO 7380", 6, "chain guard 306 to plate (4), belt guard 305 to bridge (2)", "5 N·m"),
    ("H13", "Socket cap screw M6 x 20 A2", "ISO 4762", 2, "plunger block 705 from under the top", "6 N·m"),
    ("H14", "Weld nut M12 A2 (base, 4) + weld stud M6 x 40 A2 with Ø10 x 25 spacer and nyloc (back wall, 4)", "DIN 929 / ISO 13918", 8, "feet; back panel 105", "6 N·m (studs)"),
    ("H15", "Countersunk screw M10 x 20 A2 + thread lock", "ISO 10642", 2, "stage plate 701 to rods 702", "25 N·m [18 lbf·ft]"),
]

ITEMS = [
    (1, "P1-401-100", "Cabinet weldment (shell, top, base, door, back panel, HMI pod, backing plate)", 1, "drawing P1-401-100 / 101"),
    (2, "P1-401-200", "Column weldment (tube, base plate, cap, horseshoe)", 1, "drawing P1-401-200"),
    (3, "P1-401-300", "Drive head (head plate, spindle cartridge + spacers, agitator hub, bridge, guards)", 1, "drawing P1-401-300 / 301"),
    (4, "P1-401-400", "Hopper weldment 42 L 316L + lid + flap", 1, "drawing P1-401-400"),
    (5, "P1-401-500", "Agitator weldment 316L", 1, "drawing P1-401-500"),
    (6, "P1-401-700", "Container stage (plate, rods, bushings, pin bar, plunger block, sensor bracket)", 1, "drawing P1-401-700"),
    (7, "P1-413", "Servo 750 W + drive", 1, "bought"),
    (8, "P1-414", "Agitator gearmotor 1/4 HP", 1, "bought"),
    (9, "P1-415", "Auger tooling S and J", 2, "bought to P1-401-600"),
    (10, "P1-416", "PLC + I/O + HMI", 1, "bought"),
    (11, "P1-417", "Foot switch", 1, "bought"),
    (12, "P1-430..433", "Bearings, belt drive, chain drive, seals", 1, "bought"),
    (13, "P1-434/435", "Index plunger, container sensor", 1, "bought"),
    (14, "P1-436..446", "Safety and electrical parts, feet, cabinet hardware, clamps", 1, "bought"),
    (15, "H1-H15", "Hardware", 1, "drawing P1-401-800"),
]
