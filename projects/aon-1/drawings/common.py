"""Shared data for the AON-1 drawing set: sheet factory, sheet order, bought parts and hardware (one place for the BOM too)."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parents[1] / "skills" / "anatomy" / "tools" / "plant"))
sys.path.insert(0, str(ROOT / "design"))
import mechsheet as ms  # noqa: E402
from mechsheet import mmi, fin  # noqa: E402,F401
import design as D  # noqa: E402

PROJECT = "Ambient · AON-1 (Ambient Orbital Node 1) 3U CubeSat · rev A"
DWG = HERE
DXF = ROOT / "dxf"
DXF.mkdir(exist_ok=True)
IMG = HERE / "img"
MASS = json.loads((ROOT / "cad" / "masses.json").read_text())
BASIS = json.loads((ROOT / "design" / "design-basis.json").read_text())
K = 96 / 25.4          # px per mm at 1:1 on the sheet


def SC(n):
    return K * n       # n = scale factor (2 -> 2:1, 0.5 -> 1:2)


def kg(*pids):
    m = sum(MASS.get(p, 0) for p in pids)
    return f"{m * 1000:.1f} g [{m * 2.2046 * 16:.2f} oz]"


SHEETS = []
ORDER = ["AON-000", "AON-001", "AON-002", "AON-003", "AON-101", "AON-103", "AON-104", "AON-105", "AON-106", "AON-107", "AON-B00",
         "AON-600", "AON-E01", "AON-E02", "AON-900"]

AL6061 = "6061-T6 aluminium, ASTM B211 bar / B209 plate (7075-T73 acceptable)"
ANOD = "Hard anodise MIL-A-8625 Type III Class 1, 25-50 µm; dimensions apply AFTER anodise; mask tapped holes"
CHEM = "Chromate-free conversion coat MIL-DTL-5541 Type II Class 3 (electrical bonding surfaces), tapped holes masked"
VAC = "All materials on NASA outgassing list: TML < 1.0 %, CVCM < 0.10 % (ASTM E595). No cadmium, zinc or tin plating (whiskers)."


def sheet(number, title, **kw):
    SHEETS.append((number, title))
    kw["sheet"] = f"{ORDER.index(number) + 1} of {len(ORDER)}"
    kw.setdefault("qty", "1")
    kw.setdefault("rev", "A")
    kw.setdefault("date", "2026-11-18")
    kw.setdefault("drawn", "Anatomy · aon-1/drawings")
    kw.setdefault("tol", "LINEAR X.X ±0.1 [±.004] · X.XX ±0.05 [±.002] · HOLES +0.1/-0 · ANGLES ±0.5° · THREADS ISO 965 6H")
    S = ms.Sheet(number=number, title=title, project=PROJECT, **kw)
    S.tb["qty"] = kw["qty"]
    return S


# bought parts: line, description, maker, part number, qty per satellite (+ spares), unit USD (estimate unless noted), where / note
BOUGHT = [
    ("BP-01", "Space solar cell CIC, triple junction GaInP/GaAs/Ge, 80 x 40 mm, 30 % BOL, with 100 µm CMX coverglass and interconnects", "Azur Space Solar Power GmbH",
     "3G30C-Advanced 80x40 CIC (quote: cell + coverglass + bypass diode)", 28, 4, 380.0, "7 per long face; order 32 (4 spares); laid up on E06 by a qualified bonding vendor or in house with Dow DC 93-500"),
    ("BP-02", "Li-ion cell 18650, 3.5 Ah, 3.635 V nominal, 10 A", "LG Energy Solution", "INR18650 MJ1", 4, 8, 6.50,
     "buy one lot of 12, screen per NASA JSC-20793 (capacity, DCIR, OCV match ±10 mV), fly the best matched 4"),
    ("BP-03", "Subminiature basic switch, hinge lever, 0.1 A-3 A 30 V DC, SPST-NC used", "Omron", "D2F-01L (confirm lever length on the datasheet)", 2, 2,
     4.20, "deployment switches SW1/SW2 on bracket AON-106; lever through the rail notch, stands 1.5 [.059] proud of the -Z rail end"),
    ("BP-04", "Spring plunger, 303 stainless, M3 x 0.5 body x 9 long, pin nose, light force 3-7 N", "McMaster-Carr", "threaded spring plunger M3 x 0.5, 9 mm (pick the light-force SKU, confirm)", 2, 2,
     9.00, "separation springs in the +Z ends of the AON-102 rails; nose stands 2.0 [.079] proud"),
    ("BP-05", "Board stack connector 2 x 26, 2.54 mm, long tail (through-board stacking)", "Samtec", "ESQ-126-39-G-D", 4, 2, 14.80,
     "CubeSat stack bus on E01-E04 (same part as the PC/104 CubeSat boards use)"),
    ("BP-06", "Wire, ETFE insulated, silver-plated copper, 26 AWG, 600 V (space grade)", "TE Connectivity (Raychem)", "M22759/32-26 (colours 0 black, 2 red, 9 white)", 1, 0, 120.0,
     "harness per AON-E02; 30 m of mixed colours"),
    ("BP-07", "Connector, 1.25 mm pitch, latching, 2 x 3 and 2 x 2, with crimp contacts", "Harwin", "Gecko-SL G125 series (G125-MV10605L0P plug / -FV10605 receptacle; confirm sizes)", 12, 4,
     6.00, "panel, end board and antenna harness"),
    ("BP-08", "Coax jumper U.FL to U.FL, 1.13 mm cable, 150 mm", "Hirose", "U.FL-2LP-04N1T-A-(150)", 1, 1, 9.50, "E04 RF out to the E05 antenna phasing network"),
    ("BP-09", "Antenna element: carbon-steel measuring-tape blade 12.7 mm [1/2 in] wide, 0.13 mm, cut to length", "Stanley / Komelon", "1/2 in blade tape measure (strip the blade)", 2, 2, 8.00,
     f"two λ/4 elements, {299.792458 / 401.5 / 4 * 1000:.0f} mm each, trimmed on the VSWR bench"),
    ("BP-10", "Dyneema SK78 braided line 0.5 mm (antenna restraint)", "generic (e.g. Spectra 50 lb braid)", "0.5 mm UHMWPE braid", 1, 0, 12.00, "one loop per element, through the burn resistor"),
    ("BP-11", "Remove-before-flight plug: 4-way latching plug with a factory loop and a red streamer", "Harwin", "Gecko-SL 4-way plug + red RBF flag", 1, 1, 18.00,
     "fitted = INHIBIT (pulls EPS INHIBIT to ground); RBF port on the +X panel sensor zone"),
    ("BP-12", "Titanium threaded rod M3 x 0.5, Ti-6Al-4V grade 5, 1 m", "McMaster-Carr", "grade 5 titanium threaded rod M3 (confirm SKU)", 2, 0, 38.00, "cut 4 stack rods AON-107-R"),
    ("BP-13", "Thermistor 10 kΩ NTC, ±1 %, 0603 (panel, battery, OBC)", "Murata", "NCP18XH103F03RB", 8, 4, 0.30, "on E02, E03, E06 x 4, E07"),
    ("BP-14", "Kapton tape 25 µm + aluminised Kapton MLI patch (battery side)", "3M / Dunmore", "3M 5413 / Dunmore DE245", 1, 0, 40.00, "thermal"),
    ("BP-15", "Staking compound, low outgassing (secures fasteners, wire tie-downs)", "3M", "Scotch-Weld 2216 B/A Gray", 1, 0, 30.00, "no thread locker that is not on the outgassing list"),
]

# hardware: item, description, standard, qty, where, torque
HARDWARE = [
    ("H1", "Countersunk screw M2.5 x 14, Torx T8, A4-70 (316)", "ISO 14581", 24, "rails to frames (8 per frame), flush or 0.05 below the rail face", "0.45 N·m [4.0 lbf·in], stake"),
    ("H2", "Pan head screw M2 x 5, Torx, A4-70 + flat washer M2 A4", "ISO 14583 / ISO 7089", 16, "solar panels E06 to the -Z and +Z frame bars", "0.20 N·m [1.8 lbf·in], stake"),
    ("H3", "Hex nut M3 thin, A4-70 + flat washer M3 A4", "ISO 4035 / ISO 7089", 4, "on the stack rod ends under the -Z end board E07", "0.5 N·m [4.4 lbf·in], stake"),
    ("H4", "Pan head screw M2 x 4, Torx, A4-70", "ISO 14583", 4, "switch brackets AON-106 to the -Z frame bars", "0.20 N·m [1.8 lbf·in], stake"),
    ("H5", "Pan head screw M2 x 10, A4-70 + hex nut M2 A4 + flat washers", "ISO 14583 / ISO 4032", 4, "switches BP-03 to the brackets", "0.10 N·m [0.9 lbf·in], do not crush the switch body"),
    ("H7", "Hex standoff M3 F-F, 5.5 AF x 5.0 long, aluminium 6061 (E05 mount + rod nut)", "Keystone 24318-type (confirm)", 4, "on the stack rods above the +Z frame; E05 sits on them", "0.6 N·m [5.3 lbf·in] against the frame"),
    ("H8", "Pan head screw M3 x 5, A4-70 + flat washer", "ISO 14583 / ISO 7089", 4, "E05 antenna board to the standoffs H7", "0.5 N·m [4.4 lbf·in], stake"),
    ("H9", "Silicone pad 82 x 8 x 0.8, Shore A 40, low outgassing (Dow DC 93-500 cast or Bergquist Gap Pad TGP 1000)", "-", 4, "between each panel and the mid-frame bar (mid-span support, 0.2 preload)", "-"),
]

# made parts (BUILD lines): id, name, qty per satellite, material, process
MADE = [
    ("AON-101", "Rail, -Z switch notch (positions +X+Y and -X-Y)", 2, AL6061, "CNC mill from 10 mm [.394] square bar, hard anodise"),
    ("AON-102", "Rail, +Z spring plunger bore (positions +X-Y and -X+Y)", 2, AL6061, "CNC mill + tap M3, hard anodise"),
    ("AON-103", "-Z frame", 1, AL6061, "CNC mill from 10 mm plate, chem film"),
    ("AON-104", "Mid frame", 1, AL6061, "CNC mill from 10 mm plate, chem film"),
    ("AON-105", "+Z frame", 1, AL6061, "CNC mill from 10 mm plate, chem film"),
    ("AON-106", "Deployment switch bracket", 2, "5052-H32 aluminium sheet 1.0 mm [.040]", "laser/punch from DXF, 1 bend, chem film"),
    ("AON-107", "Stack spacers and rods (tabulated)", 1, "6061-T6 Ø6 bar (spacers); Ti-6Al-4V M3 rod (rods)", "lathe; rod cut to length"),
    ("E01", "EPS board (MPPT, regulators, load switches, inhibits)", 1, "FR4 4-layer 1.6 mm, IPC-6012 Class 3", "PCBA (RushPCB turnkey)"),
    ("E02", "Battery board (2S2P 18650, protection, heater)", 1, "FR4 4-layer 1.6 mm, IPC-6012 Class 3", "PCBA"),
    ("E03", "OBC + ADCS board (STM32H743, FRAM, NOR, magnetometer, IMU, torquer drivers)", 1, "FR4 6-layer 1.6 mm, IPC-6012 Class 3", "PCBA"),
    ("E04", "COM UHF transceiver (400-403 MHz, 2 W)", 1, "FR4 4-layer 1.6 mm (RF layer stack, controlled impedance)", "PCBA + shield can"),
    ("E05", "Antenna deployer board (+Z face)", 1, "FR4 4-layer 1.6 mm", "PCBA"),
    ("E06", "Solar panel (+X variant E06A with RBF/umbilical port; E06B x 3)", 4, "FR4 4-layer 1.6 mm with embedded torquer coil", "PCBA + CIC lay-up"),
    ("E07", "-Z end board (Z torquer coil, -Z sun sensor)", 1, "FR4 4-layer 1.6 mm", "PCBA"),
]
