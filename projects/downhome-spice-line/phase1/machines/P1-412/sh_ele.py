"""P1-412 electrical E01: 120 V schematic, enclosure layout, components, wire list, cables, drive settings."""
from common import *  # noqa: F401,F403
from mechsheet import Sch, BLU, GRY
import model as M
from design import calcs, GM, ELE

INK, RED, GRN = "#111", "#b00020", "#2e7d32"
C = calcs()

COMPONENTS = [
    ("X0", "Cord SJOOW 14/3 3 m + NEMA 5-15P, gland M20 (P1-451)", "plant receptacle on TBL-1, 20 A circuit", "left wall"),
    ("TB1", "DIN terminals 6 x 2.5 mm² + PE terminal (P1-451)", "AutomationDirect DN-T12 + DN-G12 class", "rail"),
    ("F1", "Fuse holder 5 x 20 + 3 A time-delay (P1-451)", "DN-F6 + 3 A T (Bussmann GDC-3A)", "rail"),
    ("S0", "E-stop 40 mm mushroom, twist release, 2 NC (P1-451)", "AutomationDirect GCX1131 + 2 x NC", "lid, top"),
    ("S1", "Selector 2-pos maintained OFF / ON, 1 NO (P1-451)", "GCX1100 class", "lid, left"),
    ("H1", "Pilot light green LED 120 V (P1-451)", "GCX0101-120 class", "lid, right"),
    ("R1", "Speed pot 10 kΩ with knob (with A1, P1-422)", "KB 9370 pot kit", "lid, bottom"),
    ("A1", "SCR DC drive 115 V AC in, 0-130 V DC out, inhibit (P1-422)", "KB Electronics KBMD-240D", "back wall"),
    ("M1", "PMDC gearmotor 1/8 HP 130 V DC 1.1 A, 190 rpm (P1-422)", "Bodine 42A-E class", "carriage shelf"),
    ("B1", "Limit switch roller plunger 1 NO + 1 NC (P1-452)", "Omron D4N-4120 class", "column left face"),
]

WIRES = [
    ("1", "X0 black (L)", "TB1:1", "cord 14 AWG", ""),
    ("N", "X0 white (N)", "TB1:N", "cord 14 AWG", ""),
    ("PE", "X0 green", "TB1:PE", "cord 14 AWG", "PE stud on the back plate"),
    ("1", "TB1:1", "F1:in", "16 AWG MTW black", ""),
    ("2", "F1:out", "S0 NC-1 : 11", "16 AWG black", "to the lid: 300 loop"),
    ("3", "S0 NC-1 : 12", "S0 NC-2 : 21", "16 AWG black", "jumper on the operator"),
    ("4", "S0 NC-2 : 22", "S1 : 13", "16 AWG black", ""),
    ("5", "S1 : 14", "A1 : L1, H1 : X1", "16 AWG black", "L switched"),
    ("N", "TB1:N", "A1 : L2, H1 : X2", "16 AWG white", ""),
    ("6 / 7", "A1 : A+ / A-", "TB1:6 / 7 → W1 → M1", "16 AWG red / black", "armature"),
    ("8 / 9", "A1 : I1 / I2", "TB1:8 / 9 → W2 → B1 NO 13-14", "18 AWG violet", "inhibit (closed = stop)"),
    ("10-12", "A1 : P1 / P2 / P3", "R1 : 1 / 2 / 3", "3C 22 AWG shielded", "shield to A1 COM only"),
    ("PE", "PE stud", "lid bond, M1 frame (W1 green), base (W0)", "16 AWG green / yellow", "base bonded via the shelf screws"),
]

CABLES = [
    ("W0", "TB1", "NEMA 5-15P (bench receptacle)", "SJOOW 14/3 600 V, 3 m (bought with P1-451)", "M20 left wall"),
    ("W1", "TB1:6 / 7 / PE", "M1 terminal box", "SJOOW 16/3, 1.2 m, 150 loop for the carriage stroke", "M20 left wall + strain relief on the shelf"),
    ("W2", "TB1:8 / 9", "B1 13-14", "2C 18 AWG shielded PUR, 1.0 m", "M20 left wall; M20 into B1"),
]


def e01():
    S = sheet("P1-412-E01", "ELECTRICAL: SCHEMATIC, PANEL, WIRING", scale="NTS · 1:2 (enclosure)", material="see component list",
              finish="NEC 430, UL 508A practice; 75 °C Cu; cord-and-plug", mass="-")
    c = Sch(S)
    c.t(120, 110, f"SUPPLY 120 V 1-ph 60 Hz, cord and plug, 15/20 A receptacle on the bench (≈ {ELE['A']:.1f} A full load)", 20, bold=True)
    xL, xN = 250, 1250
    # cord + TB1
    c.box(150, 140, 280, 60, "X0 CORD SJOOW 14/3 + 5-15P", ["L black / N white / PE green"])
    c.w(xL, 200, xL, 250, no="1", side=-1); c.w(330, 200, 330, 230); c.w(330, 230, xN, 230, no="N"); c.w(175, 200, 175, 1180, GRN); c.w(175, 1180, 400, 1180, GRN); c.t(168, 700, "PE", 13, "end", GRN, True)
    c.term(xL, 250, "TB1:1"); c.term(xN, 230, "TB1:N")
    # L rail: F1, S0 ch1, S0 ch2, S1
    c.fuse_v(xL, 255, "F1  3 A T")
    c.w(xL, 305, xL, 340, no="2", side=-1)
    c.sw_v(xL, 340, "S0 E-STOP NC-1 (11-12)", nc=True)
    c.w(xL, 390, xL, 410, no="3", side=-1)
    c.sw_v(xL, 410, "S0 E-STOP NC-2 (21-22)", nc=True)
    c.w(xL, 460, xL, 490, no="4", side=-1)
    c.sw_v(xL, 490, "S1 OFF / ON (13-14)")
    c.w(xL, 540, xL, 760, no="5", side=-1)
    c.w(xN, 230, xN, 760)
    c.t(150, 600, "L switched", 12, "start", BLU)
    # rung 1: pilot lamp
    c.dot(xL, 600); c.w(xL, 600, 720, 600); c.lamp_h(740, 600, "H1 green"); c.w(752, 600, xN, 600); c.dot(xN, 600)
    c.t(800, 590, "ON = drive powered", 11, "start", GRY)
    # rung 2: drive
    c.w(xL, 760, 520, 760, no="5"); c.w(980, 760, xN, 760, no="N"); c.dot(xN, 760)
    c.box(520, 690, 460, 230, "A1 KBMD-240D", ["L1 ← 5 (left)   L2 ← N (right)", "J1 = 115 V line, J2 = 130 V armature (confirm in the manual)",
                                               "plug-in HP resistor for 1/8 HP 130 V", "A+ / A- → M1", "I1 / I2 inhibit: closed = motor stopped",
                                               "P1 / P2 / P3 → R1 10 kΩ", "trimpots MIN / MAX / IR / CL / ACC (see settings)"])
    # armature to motor
    c.w(600, 920, 600, 1010, no="6 A+", side=-1); c.w(680, 920, 680, 1010, no="7 A-", side=1)
    c.S.add('<circle cx="640" cy="1050" r="38" fill="#fff" stroke="#111" stroke-width="1.8"/>'); c.t(640, 1048, "M1", 18, "middle", INK, True); c.t(640, 1068, "DC", 12, "middle")
    c.w(600, 1010, 615, 1020); c.w(680, 1010, 665, 1020)
    c.t(690, 1110, f"1/8 HP 130 V DC 1.1 A, {GM['rpm']:.0f} rpm, {GM['T']:.1f} N·m; frame to PE (W1 green)", 12)
    # inhibit to the limit switch
    c.w(800, 920, 800, 980, no="8 I1", side=-1); c.w(880, 920, 880, 980, no="9 I2", side=1)
    c.w(800, 980, 820, 980); c.w(860, 980, 880, 980); c.no_h(840, 980)
    c.t(840, 1015, "B1 NO 13-14 (closed with the carriage UP)", 11, "middle", INK, True)
    c.t(840, 1032, "roller struck by the carriage plate top", 11, "middle", GRY)
    # pot
    c.w(960, 860, 1060, 860, no="10-12"); c.box(1060, 835, 130, 50, "R1 10 kΩ", ["speed (lid)"])
    # PE
    c.t(410, 1175, "PE: cord green → TB1 PE → PE stud on the back plate → lid bond strap, M1 frame (W1), base via the bench bolts. Check < 0.1 Ω PE stud to the column (ITP).", 12, "start", GRN)
    # operation logic
    c.t(120, 1240, "HOW THE CIRCUIT WORKS", 15, bold=True)
    for i, l in enumerate([
        "S1 ON powers A1 (H1 lit). With the carriage UP, B1 NO is closed on I1-I2 so A1 is inhibited: the chuck does not turn while the operator loads the container.",
        "Pulling the lever lowers the carriage; B1 opens after ≈ 5 mm and A1 ramps the motor up (ACC ≈ 0.3 s) before the chuck reaches the cap (≈ 0.4 s at hand speed).",
        "The slip clutch limits the cap torque; the motor runs on while the clutch slips until the operator releases the lever; the gas spring lifts the carriage and B1 inhibits A1 at the top.",
        "E-stop S0 opens the AC line to A1 (two NC contacts in series, stop category 0); the motor coasts to rest in < 1 s (low inertia, clutch). Twist to release, then the lever returns the cycle.",
        "The lever is hold-to-run by nature: releasing it lifts the chuck away from the hands. The polycarbonate guard P1-412-303 surrounds the chuck at all heights.",
    ]):
        c.t(120, 1270 + 22 * i, l, 12)
    # enclosure layout (1:2): lid face and inside back wall
    s2 = SC(2)
    E = M.ENC
    W_, H_ = E["x1"] - E["x0"], E["h"]
    vl = S.view(1500, 560, s2, "LID (1:2), OPERATOR SIDE", (1500, 160))
    vl.rect(-W_ / 2, 0, W_, H_, "vis", "#eceff1")
    xc = (E["x0"] + E["x1"]) / 2
    for k, (x, z) in M.ENC_OPS.items():
        r = {"estop": 20.0, "pot": 8.0}.get(k, 11.0)
        vl.circle(x - xc, z, r, "vis", {"estop": "#c62828", "lamp": "#43a047"}.get(k, "#263238"))
        vl.circle(x - xc, z, 11.15, "hid") if k == "estop" else None
        vl.text(x - xc, z - r - 12, {"estop": "S0 E-STOP", "sel": "S1 OFF/ON", "lamp": "H1", "pot": "R1 SPEED"}[k], 10)
    vl.dim((-W_ / 2, 0), (W_ / 2, 0), -45, None, "h"); vl.dim((W_ / 2, 0), (W_ / 2, H_), -40, None, "v")
    vl.note(-W_ / 2, -32, ["lid holes: 3 x Ø22.5 [.886] (S0, S1, H1), 1 x Ø9.5 + anti-rotation (R1)", "drill from the lid template; deburr; keep 20 from the lid screws"], 11)
    vb = S.view(1880, 560, s2, "INSIDE, BACK WALL (1:2)", (1900, 160))
    vb.rect(-W_ / 2, 0, W_, H_, "vis", "#f4f6f8")
    vb.rect(-43, 80, 86, 109, "vis", "#dfe7f1"); vb.text(0, 140, "A1 KBMD-240D", 10); vb.text(0, 128, "109 x 86 on 4 x M3 x 10 standoffs", 8)
    vb.rect(-52, 22, 104, 35, "phan")
    for i, t in enumerate(["F1", "1", "N", "6", "7", "8", "9", "PE"]):
        x0 = -48 + i * 12
        vb.rect(x0, 25, 10, 29, "vis", "#c5e1a5" if t == "PE" else "#cfd8dc"); vb.text(x0 + 5, 14, t, 8)
    vb.text(0, 64, "DIN 35 rail, TB1 + F1", 9)
    for z in (40.0, 110.0, 170.0):
        vb.circle(-W_ / 2 - 6, z, 10, "vis", "#90a4ae")
    vl.note(-W_ / 2, -62, ["glands on the left wall: W0 cord (low), W1 motor (mid), W2 limit (high)", "2 x M6 + bonded washers down through the bottom wall into the base"], 11)
    vb.dim((-43, 80), (43, 80), -20, None, "h")
    S.table(2200, 160, [("TAG", 70), ("DESCRIPTION", 420), ("PART", 300), ("WHERE", 120)], COMPONENTS, "COMPONENTS", fs=11, rh=20)
    S.table(2200, 420, [("WIRE", 60), ("FROM", 170), ("TO", 260), ("TYPE", 170), ("NOTE", 250)], WIRES, "WIRE LIST", fs=11, rh=20)
    S.table(1450, 1180, [("CABLE", 70), ("FROM", 140), ("TO", 230), ("SPEC", 420), ("GLAND / ROUTE", 340)], CABLES, "CABLES", fs=11, rh=20)
    S.table(1450, 1330, [("SETTING (A1)", 160), ("VALUE", 300), ("HOW", 500)], [
        ("J1 line", "115 V", "jumper on the board"),
        ("J2 armature", "130 V", "jumper on the board (90 V position would cap the speed at ≈ 130 rpm)"),
        ("HP resistor", "1/8 HP at 130 V", "KB plug-in resistor per the KBMD table (confirm value)"),
        ("MAX", f"{GM['rpm']:.0f} rpm at the chuck", "R1 full CW; trim with a tach on the stub (ITP)"),
        ("MIN", "0", "R1 full CCW = stop"),
        ("CL", "≈ 1.6 A (150 %)", "the clutch, not CL, limits cap torque; CL protects the motor"),
        ("ACC", "≈ 0.3 s", "smooth start before the chuck lands on the cap"),
        ("IR", "mid", "trim for steady speed while the clutch slips"),
    ], "DRIVE SETTINGS", fs=11, rh=20)
    S.notes(2200, 720, 1180, [
        f"Load: motor 1.1 A DC → ≈ {ELE['A']:.1f} A AC (SCR form factor); F1 3 A time-delay protects the cord (14 AWG) and the drive; the bench circuit is 15/20 A.",
        "Inhibit and pot leads are low-level signals: shielded, kept apart from the AC and armature wires; shield to A1 COM at the drive end only.",
        "E-stop removes AC from A1 (two NC contacts). If a later risk assessment asks for a monitored stop, add a safety relay and contactor ahead of A1 (space on the rail).",
        "B1 fails safe for the hands only with the guard: a broken I1-I2 wire lets the motor run with the carriage up, so the guard P1-412-303 is required (ITP checks both).",
        "All lid devices bonded to PE via the lid strap; cord grip at the gland, 150 mm service loop for W1 at the carriage.",
    ], "NOTES", fs=12)
    S.save(DWG / "P1-412-E01_electrical.svg")


if __name__ == "__main__":
    e01()
