"""Shared data for the P1-304 drawing set: sheet factory, item numbers, bought parts, hardware."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[4] / "skills" / "anatomy" / "tools" / "plant"))
sys.path.insert(0, str(HERE))
import mechsheet as ms  # noqa: E402
from mechsheet import mmi, fin  # noqa: E402,F401
import design as D  # noqa: E402

PROJECT = "Down Home Creole · Phase 1 · P1-304 Drum-top vibratory sifter (built in house) · rev B"
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
ORDER = ["P1-304-000", "P1-304-001", "P1-304-002", "P1-304-003", "P1-304-100", "P1-304-200", "P1-304-201", "P1-304-300", "P1-304-400",
         "P1-304-600", "P1-304-E01", "P1-304-E02", "P1-304-900"]


def sheet(number, title, **kw):
    SHEETS.append((number, title))
    kw["sheet"] = f"{ORDER.index(number) + 1} of {len(ORDER)}"
    kw.setdefault("qty", "1")
    kw.setdefault("rev", "B")
    kw.setdefault("date", "2026-11-18")
    return ms.Sheet(number=number, title=title, project=PROJECT, **kw)


SS316L = "SS 316L (ASTM A240 sheet/plate)"
SS304 = "SS 304 (ASTM A240)"
FIN_PC = "Product contact: 2B sheet, #4 polish Ra ≤ 0.8 µm [32 µin]; welds ground flush; passivate ASTM A967"
FIN_NPC = "Non-contact: #4 or bead blast; passivate ASTM A967"

# bought parts: tag, description, maker, part number, qty, unit USD (estimate unless noted), note
BOUGHT = [
    ("P1-306", "Rotary electric vibrator, 2-pole 60 Hz (3,600 rpm), single-phase 115 V, max centrifugal force about 2.0 kN [450 lbf], adjustable eccentric weights, IP66, 4 feet",
     "OLI Vibrators (or Martin Engineering)", "MVE 200/36 class, 1-ph 115 V option (confirm voltage option, foot drilling 120 x 70 for 4 x M10, and FLA)", 1, 950,
     "bracket P1-304-206 is drilled to this; check the maker drawing before drilling"),
    ("P1-307", "Grate magnet 12 x 12 in, 5 x 1 in tubes, rare earth 10,000 G class, 316, no housing", "Industrial Magnetics, Inc.", "grate magnet 12 x 12 in, 1 in tubes (confirm)", 1, 650,
     "rests on bars P1-304-203; lifts out after the deck"),
    ("P1-305", "Woven wire cloth 12 x 12 mesh, 0.023 in [0.58 mm] 316 wire, 1.53 mm opening, 52 % open, 24 x 24 in piece", "McMaster-Carr / TWP Inc.", "316 SS woven cloth 12 mesh 0.023 wire (confirm)", 3, 45,
     "1 per deck + 1 spare deck + 1 re-screen"),
    ("P1-341", "Rubber vibration mount, type A (M8 stud both ends), Ø30 x 30, natural rubber 40 Shore A, compression rate about 60 N/mm, rated 400 N", "Paulstra / generic (McMaster vibration-damping mount)",
     "cylindrical mount M8 male-male Ø30 x 30 40 Sh (confirm rate curve)", 4, 9, "3 fitted + 1 spare"),
    ("P1-342", "Over-centre draw latch with keeper, 304 stainless, adjustable, 1,100 N [250 lbf] holding, padlockable", "Southco / DESTACO", "SS adjustable draw latch 250 lbf class (confirm)", 4, 32,
     "latch on plate P1-304-207 on the shell (2 x M5 on 20), keeper on the lid tab; check hole pitch"),
    ("P1-344", "Flex band, FDA silicone 2 mm, Ø484 ID x 60 wide (moulded or bonded loop), with 2 SS worm clamps 460-500 mm range", "generic FDA silicone", "silicone band 19 in ID x 2.4 in + 2 x #296 SS worm clamps (confirm)", 1, 40,
     "seals the 4 mm gap body to upstand; keep 10 mm slack"),
    ("P1-345", "Dust port kit: 3 in TC clamp (wing nut), EPDM FDA gasket, 3 in TC x 3 in hose barb 304", "generic sanitary", "13MHHM-3 + 40MP-3 + 3 in TC hose adapter", 1, 38,
     "to P1-310 drum-vent hose, blast gate set to about 100 cfm"),
    ("P1-346", "Inlet sock, food-grade cotton or PE, 4 in ID x 300 long, both ends with SS band", "generic", "4 in filter sock, FDA (confirm)", 3, 12, "valve outlet to inlet ferrule; spares"),
    ("P1-347", "Bonding strap, tinned copper braid 16 mm² x 250, M8 ring lugs both ends", "generic", "braid 16 mm² 250 mm M8/M8", 1, 14, "bridges the isolators: body to base (static, NFPA 77)"),
    ("P1-348", "Motor isolator, 2-pole 16 A, lockable OFF, IP66 enclosure, 1 early-break NO aux contact", "ABB", "OTP16T2M + OA1G10 aux, IP66 (confirm enclosure code)", 1, 90,
     "on the blender frame leg, within sight of the sifter"),
    ("P1-349", "Contactor 9 A 3-pole, 24 V DC coil, + manual motor protector 2.5-4.0 A (1-ph wiring through 3 poles)", "ABB", "AF09-30-10-13 (24 V DC coil) + MS116-4.0", 1, 115,
     "in panel MS-P1 (E01); FLA set to the vibrator nameplate"),
    ("P1-350", "Flexible cord SOOW 3 x 14 AWG 600 V, oil and wash resistant, 3 m, + M20 nylon cord grip (vibrating load)", "generic", "SOOW 14/3 + M20 cord grip IP68", 1, 18,
     "drip loop; tied to the bracket, never tight"),
]

HARDWARE = [
    ("H1", "Hex nut M8 nyloc A2 + flat washer (isolator lower stud)", "ISO 7040 / 7089", 3, "isolators to seat ring P1-304-101", "12 N·m [9 lbf·ft]"),
    ("H2", "Hex nut M8 nyloc A2 + flat washer (isolator upper stud)", "ISO 7040 / 7089", 3, "isolator brackets P1-304-205 to isolators", "12 N·m [9 lbf·ft]"),
    ("H3", "Hex bolt M10 x 35 A2-70 + spring washer + nyloc nut + thread lock", "ISO 4017 / 7040", 4, "vibrator feet to bracket P1-304-206", "45 N·m [33 lbf·ft], re-check after 1 h run"),
    ("H4", "Button head screw M5 x 12 A2 + nyloc nut", "ISO 7380 / 7040", 16, "latches to body tabs (8), keepers to lid tabs (8)", "4 N·m"),
    ("H5", "Hex bolt M8 x 16 A2 + 2 serrated washers (bonding)", "ISO 4017 / DIN 6798", 2, "bond strap P1-347: seat-ring tab and bracket", "12 N·m"),
    ("H6", "Cord grip M20 nylon + locknut", "EN 50262", 1, "vibrator terminal box (cord P1-350)", "hand + 1/4 turn"),
]

ITEMS = [
    (1, "P1-304-100", "Base weldment (seat ring, upstand, skirt, centring tabs)", 1, "drawing P1-304-100"),
    (2, "P1-304-200", "Body weldment (shell, top flange, magnet bars, screen ledge, isolator brackets, vibrator bracket)", 1, "drawing P1-304-200 / 201"),
    (3, "P1-304-300", "Lid weldment (disc, 4 in inlet + 3 in dust ferrules, 3 hold-down pads, keeper tabs)", 1, "drawing P1-304-300"),
    (4, "P1-304-400", "Screen deck 12 mesh (upper + lower ring, cloth)", 1, "drawing P1-304-400 (make 2: 1 spare)"),
    (5, "P1-304-501", "Lid gasket 3 mm FDA silicone", 1, "drawing P1-304-300 (DXF)"),
    (6, "P1-304-502", "Deck gasket 2 mm FDA silicone", 1, "drawing P1-304-400 (DXF)"),
    (7, "P1-304-503", "Hold-down pad cap, FDA silicone Ø30 x 8", 3, "drawing P1-304-300"),
    (8, "P1-306", "Vibrator 2.0 kN 1-ph 115 V", 1, "bought"),
    (9, "P1-307", "Grate magnet 12 x 12 in", 1, "bought"),
    (10, "P1-341", "Rubber mount M8 Ø30 x 30 40 Sh", 3, "bought"),
    (11, "P1-342", "Draw latch + keeper SS", 4, "bought"),
    (12, "P1-344", "Flex band + 2 clamps", 1, "bought"),
    (13, "P1-345", "Dust port kit 3 in TC", 1, "bought"),
    (14, "P1-346", "Inlet sock 4 in", 1, "bought"),
    (15, "P1-347", "Bond strap 16 mm²", 1, "bought"),
    (16, "H1-H6", "Hardware", 1, "drawing P1-304-600"),
]
