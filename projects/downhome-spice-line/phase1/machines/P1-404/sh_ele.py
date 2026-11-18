"""P1-404 electrical E01: 120 V and 24 V schematic, enclosure layout, components, wire list, cables, I/O map, motor settings."""
import math
from common import *  # noqa: F401,F403
from mechsheet import Sch, BLU, GRY
from design import calcs, ELE, ENC, ENC_OPS, LAB, ROL, MOT, ROLLER_T, CONT, BASE

INK, RED, GRN = "#111", "#b00020", "#2e7d32"
C = calcs()
MM_PER_REV = math.pi * ROL["d"] * MOT["T"] / ROLLER_T          # container surface travel per motor rev
STEPS = 800

COMPONENTS = [
    ("X0", "Cord SJOOW 14/3 3 m + NEMA 5-15P, gland M20 (P1-456)", "plant receptacle on the bench, 15/20 A", "-y end, low"),
    ("TB1", "DIN terminals 2.5 mm²: 1, 5, N + PE (P1-456)", "AutomationDirect DN-T12 + DN-G12 class", "back wall, rail"),
    ("F1", "Fuse holder 5 x 20 + 3 A time-delay (P1-456)", "DN-F6 + Bussmann GDC-3A", "back wall, rail"),
    ("S0", "E-stop 40 mm mushroom, twist release, 2 NC (P1-456)", "AutomationDirect GCX1131 + 2 NC", "-y end, top"),
    ("S1", "Selector 2-pos maintained OFF / ON, 1 NO (P1-456)", "GCX1100 class", "-y end, left"),
    ("S2", "Selector 2-pos maintained S / J, 1 NO (P1-456)", "GCX1100 class", "-y end, right"),
    ("S3/H1", "FEED push button illuminated green 24 V, 1 NO (P1-456)", "GCX3101-24 class", "-y end, bottom"),
    ("G1", "Power supply 120 V AC → 24 V DC 6.5 A (P1-426)", "Mean Well LRS-150-24", "back wall, top"),
    ("TB2", "DIN terminals 24 V: +24 x 6, 0 V x 6 (P1-456)", "DN-T12 class, red / blue", "back wall, rail"),
    ("A1", "I/O controller, 24 V (P1-426)", "Teknic ClearCore CLCR-4-13", "floor"),
    ("M1", "Integrated servo-stepper NEMA 23, 24 V DC (P1-426)", "Teknic ClearPath CPM-SDSK-2311S-RLN", "-x plate, inside"),
    ("B1", "Gap sensor fork 40, PNP NO (dark = gap), M8 4-pin (P1-427)", "SICK WFS3-40P415", "peel plate edge"),
    ("B2", "Start sensor inductive M12 PNP NO 4 mm (P1-457)", "Turck Bi4U-M12-AP6X-H1141 class", "+x plate, arm"),
]

WIRES = [
    ("1", "X0 black (L)", "TB1:1", "cord 14 AWG", ""),
    ("N", "X0 white (N)", "TB1:N", "cord 14 AWG", ""),
    ("PE", "X0 green", "TB1:PE", "cord 14 AWG", "PE stud on the back wall"),
    ("1", "TB1:1", "F1 in", "16 AWG MTW black", ""),
    ("2", "F1 out", "S0 NC-1 : 11", "16 AWG black", "to the end wall: 200 loop"),
    ("3", "S0 : 12", "S0 : 21", "16 AWG black", "jumper on the operator"),
    ("4", "S0 : 22", "S1 : 13", "16 AWG black", ""),
    ("5", "S1 : 14", "TB1:5 → G1 L", "16 AWG black", "L switched"),
    ("N", "TB1:N", "G1 N", "16 AWG white", ""),
    ("PE", "TB1:PE", "G1 ⏚, PE stud, M1 (W1 green)", "16 AWG green / yellow", "base bonded via the bench bolts"),
    ("10", "G1 +V", "TB2:+24", "16 AWG red", "both +V screws"),
    ("11", "G1 -V", "TB2:0V", "16 AWG blue", "both -V screws; 0 V to PE at TB2 (one point)"),
    ("12 / 13", "TB2:+24 / 0V", "A1 24 VDC IN + / -", "18 AWG red / blue", ""),
    ("14 / 15", "TB2:+24 / 0V", "W1 → M1 DC power", "16 AWG (in W1)", "CPM-CABLE-PWR, Molex 2-pin"),
    ("M-0", "A1 M-0", "W2 → M1 control", "Teknic M0P6 cable", "enable, step, dir, HLFB"),
    ("20", "TB2:+24", "S2 : 13, S3 : 13", "18 AWG red", "button commons"),
    ("21", "S2 : 14", "A1 A-9", "18 AWG white", "closed = J setting"),
    ("22", "S3 : 14", "A1 DI-8", "18 AWG white", "FEED"),
    ("23", "A1 IO-0", "H1 X1 (+)", "18 AWG white", "lamp output 24 V"),
    ("24", "H1 X2 (-)", "TB2:0V", "18 AWG blue", ""),
    ("30-33", "TB2 / A1", "W3 → B2: brown +24, blue 0V, black → A1 DI-6", "M12 4-pin, PUR 2 m", "start (arm down)"),
    ("34-37", "TB2 / A1", "W4 → B1: brown +24, blue 0V, black → A1 DI-7, white (teach) n.c.", "M8 4-pin, PUR 2 m", "gap"),
]

CABLES = [
    ("W0", "TB1", "NEMA 5-15P (bench receptacle)", "SJOOW 14/3 600 V, 3 m (bought with P1-456)", "G1 gland M20, -y end low"),
    ("W1", "TB2:+24 / 0V / PE", "M1 power", "Teknic CPM-CABLE-PWR-MS120 (3 m) + PE lead", "G2 M20, along the base under the -x plate"),
    ("W2", "A1 M-0", "M1 control", "Teknic CPM-CABLE-M0P6-120 (3 m)", "G3 M20 (split grommet for the plug)"),
    ("W3", "TB2 / A1 DI-6", "B2 start sensor", "M12 4-pin PUR 2 m (with P1-457)", "G4 M20 multi-hole insert"),
    ("W4", "TB2 / A1 DI-7", "B1 gap sensor", "SICK DOL-0804-G02M (with P1-427)", "G4 M20 multi-hole insert"),
]


def e01():
    S = sheet("P1-404-E01", "ELECTRICAL: SCHEMATIC, PANEL, WIRING", scale="NTS · 1:2 (enclosure)", material="see component list",
              finish="NEC 430, UL 508A practice; 75 °C Cu; cord-and-plug; 24 V SELV control", mass="-")
    c = Sch(S)
    c.t(120, 110, f"SUPPLY 120 V 1-ph 60 Hz, cord and plug, 15/20 A receptacle on the bench (≈ {ELE['A']:.1f} A max); control and motor 24 V DC", 20, bold=True)
    xL, xN = 250, 900
    c.box(150, 140, 280, 60, "X0 CORD SJOOW 14/3 + 5-15P", ["L black / N white / PE green"])
    c.w(xL, 200, xL, 250, no="1", side=-1); c.w(330, 200, 330, 230); c.w(330, 230, xN, 230, no="N"); c.w(175, 200, 175, 640, GRN); c.w(175, 640, 520, 640, GRN)
    c.t(168, 450, "PE", 13, "end", GRN, True)
    c.term(xL, 250, "TB1:1"); c.term(xN, 230, "TB1:N")
    c.fuse_v(xL, 255, "F1  3 A T")
    c.w(xL, 305, xL, 340, no="2", side=-1)
    c.sw_v(xL, 340, "S0 E-STOP NC-1 (11-12)", nc=True)
    c.w(xL, 390, xL, 410, no="3", side=-1)
    c.sw_v(xL, 410, "S0 E-STOP NC-2 (21-22)", nc=True)
    c.w(xL, 460, xL, 480, no="4", side=-1)
    c.sw_v(xL, 480, "S1 OFF / ON (13-14)")
    c.w(xL, 530, xL, 560, no="5", side=-1)
    c.w(xL, 560, 560, 560, no="5"); c.w(xN, 230, xN, 590); c.w(xN, 590, 760, 590, no="N")
    c.box(560, 520, 200, 140, "G1 LRS-150-24", ["L ← 5   N ← N   ⏚ ← PE", "out 24 V 6.5 A (156 W)", "+V / -V → TB2"])
    c.w(520, 640, 560, 640, GRN)
    # 24 V bus
    y24, y0 = 760, 1120
    c.w(600, 660, 600, y24, RED, no="10 +24", side=-1); c.w(720, 660, 720, 700, BLU); c.w(720, 700, 1900, 700, BLU, no="11 0V")
    c.w(600, y24, 1720, y24, RED); c.t(560, y24 + 5, "+24", 13, "end", RED, True)
    c.w(1900, 700, 1900, y0, BLU); c.w(380, y0, 1900, y0, BLU); c.t(370, y0 + 5, "0V", 13, "end", BLU, True)
    c.t(1150, 690, "0V bonded to PE at TB2 (one point)", 11, "start", GRN)
    # A1 ClearCore
    c.box(980, 800, 420, 280, "A1 CLEARCORE CLCR-4-13", ["24 VDC IN + / - (12 / 13)", "DI-6 ← B2 start (arm down)", "DI-7 ← B1 gap (dark = gap)",
                                                         "DI-8 ← S3 FEED", "A-9 ← S2 (closed = J)", "IO-0 → H1 FEED lamp", "M-0 → M1 (W2): enable, step, dir, HLFB",
                                                         "USB: program load (Arduino / C++)", "program P1-404-FW-01"])
    c.w(1000, y24, 1000, 800, RED, no="12", side=-1); c.dot(1000, y24); c.w(1040, 1080, 1040, y0, BLU, no="13", side=1); c.dot(1040, y0)
    # M1
    c.w(1400, 960, 1560, 960, no="M-0 (W2)")
    c.box(1560, 880, 300, 160, "M1 CLEARPATH SDSK 23", ["DC power 24 V (W1: 14 / 15)", "step/dir 800 pulses/rev", f"{C['n_mot']:.0f} rpm at {LAB['speed']:.0f} mm/s", "HLFB → A1 (ready / move done)"])
    c.w(1700, y24, 1700, 880, RED, no="14", side=-1); c.dot(1700, y24); c.w(1760, 1040, 1760, y0, BLU, no="15", side=1); c.dot(1760, y0)
    # inputs: sensors and buttons hanging off +24 on the left
    def sensor(x, tag, sub, no_sig, sig_y):
        c.box(x - 70, 820, 140, 90, tag, sub)
        c.w(x - 40, y24, x - 40, 820, RED); c.dot(x - 40, y24)
        c.w(x + 40, 910, x + 40, y0, BLU); c.dot(x + 40, y0)
        c.w(x, 910, x, sig_y, INK); c.w(x, sig_y, 980, sig_y, INK, no=no_sig)
    sensor(440, "B2 START", ["M12 PNP NO", "brown / blue / black"], "30 → DI-6", 980)
    sensor(640, "B1 GAP", ["WFS3 PNP", "dark = gap"], "31 → DI-7", 1000)
    # S2, S3 on the right side of the bus? keep on a short rung below the bus to A1 left edge
    c.w(820, y24, 820, 780, RED); c.dot(820, y24)
    c.sw_v(820, 780, None); c.t(800, 805, "S2 S/J", 11, "end"); c.w(820, 830, 820, 1020); c.w(820, 1020, 980, 1020, INK, no="21 → A-9")
    c.w(880, y24, 880, 780, RED); c.dot(880, y24)
    c.sw_v(880, 780, None); c.t(900, 805, "S3 FEED", 11); c.w(880, 830, 880, 1040); c.w(880, 1040, 980, 1040, INK, no="22 → DI-8")
    c.w(1400, 1060, 1480, 1060, INK, no="23 IO-0"); c.lamp_h(1500, 1060, "H1"); c.w(1512, 1060, 1530, 1060); c.w(1530, 1060, 1530, y0, BLU); c.dot(1530, y0)
    c.t(380, y0 + 35, "PE: cord green → TB1 PE → PE stud → G1 earth, M1 body (W1), base via the bench bolts, lid and end-wall operators via the strap. < 0.1 Ω PE stud to the -x plate (ITP).", 12, "start", GRN)
    # how it works
    c.t(120, 1210, "HOW THE CIRCUIT AND PROGRAM WORK", 15, bold=True)
    lab_S, lab_J = CONT["shaker-250"]["lab_L"] + LAB["gap"], CONT["jar-12"]["lab_L"] + LAB["gap"]
    for i, l in enumerate([
        "S1 ON powers G1; A1 boots and enables M1 (HLFB high = ready). H1 flashes until a gap has been found: press FEED, the web advances slowly to the next gap and stops (H1 steady).",
        "The operator lays the container on the rollers against the fence and lowers the idler arm: B2 closes (arm down), and after 0.3 s A1 runs M1 up to speed (ramp 0.15 s) for one label.",
        f"A1 counts steps from the start and arms the gap input only after 90 % of the label pitch (S {lab_S:.0f} / J {lab_J:.0f}); the first dark pulse on B1 then stops M1 with a 0.1 s ramp.",
        "If no gap appears by 120 % of the pitch, A1 stops M1 and flashes H1 fast (web broken, roll empty or wrong S/J setting). FEED clears the fault after the web is fixed.",
        "E-stop S0 opens the AC feed to G1 (two NC contacts in series, stop category 0); the 24 V bus falls in < 0.1 s, M1 de-energises and coasts (< 0.1 s, low inertia). Twist to release, then FEED.",
        "Lifting the arm mid-label (B2 opens) stops M1 at once (hand-safe: the nip is between the rollers and the container, 0.07 N·m motor torque, no pinch force > 15 N).",
    ]):
        c.t(120, 1240 + 22 * i, l, 12)
    # enclosure layout (1:2)
    s2 = SC(2)
    Wd, Hh, Ln = ENC["x1"] - ENC["x0"], ENC["h"], ENC["y1"] - ENC["y0"]
    xm = (ENC["x0"] + ENC["x1"]) / 2
    vl = S.view(2140, 1080, s2, "END WALL -Y (1:2)", (2140, 680))
    vl.rect(-Wd / 2, 0, Wd, Hh, "vis", "#eceff1")
    names = {"estop": "S0 E-STOP", "sel": "S1 OFF/ON", "sj": "S2 S / J", "feed": "S3 FEED (H1)"}
    for k, (x, z) in ENC_OPS.items():
        r = 20.0 if k == "estop" else 14.0
        vl.circle(x - xm, z, r, "vis", {"estop": "#c62828", "feed": "#43a047"}.get(k, "#263238")); vl.circle(x - xm, z, 11.25, "hid")
        vl.text(x - xm, z - r - 10, names[k], 9)
    vl.dim((-Wd / 2, 0), (Wd / 2, 0), -40, None, "h"); vl.dim((Wd / 2, 0), (Wd / 2, Hh), -35, None, "v")
    vl.dim((ENC_OPS["sel"][0] - xm, 110), (ENC_OPS["sj"][0] - xm, 110), 0, None, "h")
    vl.note(-Wd / 2 - 20, -30, ["4 x Ø22.5 [.886] in the end wall; 50 pitch rows", "glands G1-G4 M20 low on the same wall"], 11)
    vb = S.view(2560, 1080, s2, "INSIDE, BACK WALL -X (1:2)", (2560, 680))
    vb.rect(-Ln / 2, 0, Ln, Hh, "vis", "#f4f6f8")
    vb.rect(-40 + 0, 85, 159, 97, "vis", "#dfe7f1"); vb.text(40, 136, "G1 LRS-150-24", 9); vb.text(40, 124, "159 x 97 x 30, 4 x M3", 8)
    vb.rect(-112, 22, 70, 35, "phan")
    for i, t in enumerate(["F1", "1", "5", "N", "PE", "+", "+", "0", "0"]):
        x0 = -110 + i * 7.4
        vb.rect(x0, 25, 6.2, 29, "vis", "#c5e1a5" if t == "PE" else ("#ef9a9a" if t == "+" else ("#90caf9" if t == "0" else "#cfd8dc")))
    vb.text(-77, 64, "DIN 35: F1, TB1, TB2", 8)
    vb.rect(-18, 2, 136, 40, "hid"); vb.text(50, 46, "A1 CLEARCORE on the floor (136 x 106), 4 x M3", 8)
    vb.rect(-Ln / 2, 70, 50, 120, "phan"); vb.text(-Ln / 2 + 25, 194, "operators", 8)
    vb.dim((-Ln / 2, 0), (Ln / 2, 0), -40, None, "h"); vb.dim((-40, 85), (119, 85), 25, None, "h")
    S.table(2050, 160, [("TAG", 70), ("DESCRIPTION", 440), ("PART", 260), ("WHERE", 110)], COMPONENTS, "COMPONENTS", fs=11, rh=19)
    S.table(2050, 450 - 0, [("I/O", 70), ("SIGNAL", 280), ("LOGIC", 300)], [
        ("DI-6", "B2 start: arm down", "rising edge + 0.3 s → run one label"),
        ("DI-7", "B1 gap: dark", "armed after 90 % pitch → stop"),
        ("DI-8", "S3 FEED", "jog to next gap; clears faults"),
        ("A-9", "S2: closed = J", f"pitch S {CONT['shaker-250']['lab_L'] + LAB['gap']:.0f} / J {CONT['jar-12']['lab_L'] + LAB['gap']:.0f} mm"),
        ("IO-0", "H1 lamp", "flash = no gap yet; fast = fault"),
        ("M-0", "M1 step / dir / enable / HLFB", f"{STEPS} steps/rev = {MM_PER_REV / STEPS:.3f} mm/step"),
    ], "I/O MAP (A1)", fs=11, rh=19)
    S.table(120, 1400, [("WIRE", 60), ("FROM", 140), ("TO", 360), ("TYPE", 170), ("NOTE", 260)], WIRES, "WIRE LIST", fs=11, rh=19)
    S.table(1150, 1400, [("CABLE", 60), ("FROM", 140), ("TO", 130), ("SPEC", 300), ("GLAND / ROUTE", 280)], CABLES, "CABLES", fs=11, rh=19)
    S.table(1150, 1560, [("SETTING (M1, MSP software)", 200), ("VALUE", 200), ("WHY", 520)], [
        ("Mode", "Step and Direction", "A1 M-0 drives it"),
        ("Input resolution", f"{STEPS} counts/rev", f"{MM_PER_REV:.1f} mm of container surface per rev"),
        ("Max speed", "300 rpm", f"run speed {C['n_mot']:.0f} rpm = {LAB['speed']:.0f} mm/s"),
        ("Torque limit", "60 %", f"needed ≈ {C['T_mot']:.2f} N·m; limit keeps a jam soft"),
        ("HLFB", "ASG-position", "A1 waits for 'move done'"),
        ("Supply", "24 V", "SDSK runs 24-75 V; 24 V caps top speed well above the need"),
    ], "MOTOR SETTINGS", fs=11, rh=19)
    S.notes(1150, 1720, 1300, [
        f"Load: G1 156 W max → ≈ {ELE['A']:.1f} A at 120 V; F1 3 A time-delay protects the cord and G1 (inrush < 65 A cold, T fuse rides it).",
        "Keep W2/W3/W4 apart from W0 inside the box; sensor cables on the base in a 304 clip under the -x plate edge, clear of the rollers and belts.",
        "E-stop removes AC from G1 (two NC). The 24 V bus discharges in < 0.1 s with M1 enabled; a monitored stop is not needed at 0.07 N·m (risk assessment in the ITP).",
        "Program P1-404-FW-01 (ClearCore Arduino) is kept with the plant software; the S/J pitch and step scale come from design.py at build time.",
    ], "NOTES", fs=12)
    S.save(DWG / "P1-404-E01_electrical.svg")


if __name__ == "__main__":
    e01()
