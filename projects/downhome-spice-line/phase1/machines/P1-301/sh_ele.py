"""P1-301 electrical: E01 power, E02 control and safety, E03 panel layout + components, E04 wire / terminal / cable list + VFD settings."""
from html import escape

from common import *  # noqa: F401,F403
import elec as E

INK, RED, BLU, GRY = "#111", "#b00020", "#0d47a1", "#607d8b"


class Sch:
    """schematic primitives in sheet px."""

    def __init__(self, S):
        self.S = S

    def w(self, x1, y1, x2, y2, col=INK, wd=1.6, no=None, side=1):
        self.S.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{wd}"/>')
        if no:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if x1 == x2:
                self.t(mx + 6 * side, my, no, 12, "start" if side > 0 else "end", BLU)
            else:
                self.t(mx, my - 5, no, 12, "middle", BLU)

    def t(self, x, y, s, fs=13, anchor="start", col=INK, bold=False):
        self.S.add(f'<text x="{x}" y="{y}" font-size="{fs}" text-anchor="{anchor}" fill="{col}"{" font-weight=\"bold\"" if bold else ""}>{escape(str(s))}</text>')

    def dot(self, x, y):
        self.S.add(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{INK}"/>')

    def term(self, x, y, lab=None):
        self.S.add(f'<circle cx="{x}" cy="{y}" r="5" fill="#fff" stroke="{INK}" stroke-width="1.3"/>')
        if lab:
            self.t(x + 9, y - 8, lab, 11, "start", GRY)

    def box(self, x, y, w, h, tag=None, sub=None, dash=False):
        self.S.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="{INK}" stroke-width="1.6"{" stroke-dasharray=\"10,5\"" if dash else ""}/>')
        if tag:
            self.t(x + 6, y + 18, tag, 14, "start", INK, True)
        if sub:
            for i, l in enumerate(sub if isinstance(sub, list) else [sub]):
                self.t(x + 6, y + 36 + 15 * i, l, 11, "start", GRY)

    # vertical devices (current flows down), centred at x between y and y + 50
    def fuse_v(self, x, y, tag):
        self.w(x, y, x, y + 12); self.S.add(f'<rect x="{x - 7}" y="{y + 12}" width="14" height="26" fill="#fff" stroke="{INK}" stroke-width="1.4"/>')
        self.w(x, y + 12, x, y + 38, INK, 0.8); self.w(x, y + 38, x, y + 50); self.t(x + 12, y + 30, tag, 12)

    def sw_v(self, x, y, tag=None, nc=False):
        self.w(x, y, x, y + 15); self.w(x, y + 35, x, y + 50)
        self.w(x, y + 35, x - 12, y + 15) if not nc else (self.w(x, y + 35, x + 10, y + 13), self.w(x, y + 15, x + 12, y + 15))
        if tag:
            self.t(x + 14, y + 30, tag, 12)

    def coil_h(self, x, y, tag):            # horizontal rung coil centred at x
        self.S.add(f'<rect x="{x - 18}" y="{y - 11}" width="36" height="22" fill="#fff" stroke="{INK}" stroke-width="1.5"/>'); self.t(x, y - 16, tag, 12, "middle", INK, True)

    def no_h(self, x, y, tag=None, nc=False):  # contact on a horizontal rung, 40 wide
        self.w(x - 20, y, x - 6, y); self.w(x + 6, y, x + 20, y)
        self.w(x - 6, y - 12, x - 6, y + 12); self.w(x + 6, y - 12, x + 6, y + 12)
        if nc:
            self.w(x - 10, y + 12, x + 10, y - 12)
        if tag:
            self.t(x, y - 17, tag, 11, "middle")

    def pb_h(self, x, y, tag, nc=False):
        self.no_h(x, y, tag, nc); self.w(x, y - 12, x, y - 24, INK, 1); self.w(x - 7, y - 24, x + 7, y - 24, INK, 1.4)

    def lamp_h(self, x, y, tag):
        self.S.add(f'<circle cx="{x}" cy="{y}" r="12" fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
        self.w(x - 8, y - 8, x + 8, y + 8, INK, 1); self.w(x - 8, y + 8, x + 8, y - 8, INK, 1); self.t(x, y - 17, tag, 11, "middle", INK, True)

    def motor(self, x, y, tag):
        self.S.add(f'<circle cx="{x}" cy="{y}" r="34" fill="#fff" stroke="{INK}" stroke-width="1.8"/>'); self.t(x, y - 2, "M", 20, "middle", INK, True); self.t(x, y + 18, "3~", 13, "middle"); self.t(x + 44, y + 4, tag, 13)


def e01():
    S = sheet("P1-301-E01", "ELECTRICAL: POWER SCHEMATIC", scale="NTS", material="see E03 component list", finish="UL 508A practice, NEC 430; wire 75 °C Cu",
              mass="-")
    c = Sch(S)
    S.text(120, 110, "SUPPLY: " + E.SUPPLY, 15, bold=True)
    xL1, xL2 = 400, 470
    y = 170
    c.t(xL1 - 6, y - 8, "L1", 14, "end", INK, True); c.t(xL2 + 6, y - 8, "L2", 14, "start", INK, True)
    c.term(xL1, y, "X1:L1"); c.term(xL2, y, "X1:L2"); c.term(250, y, "")
    c.t(240, y - 8, "PE", 14, "end", "#2e7d32", True)
    c.w(250, y + 5, 250, 1260, "#2e7d32", 2.2); c.t(260, 1280, "PE bar -> enclosure, back panel, VFD PE, motor PE (W-M1 green/yellow + shield 360° at the gland)", 12, "start", "#2e7d32")
    for x, n in ((xL1, "1L1"), (xL2, "1L2")):
        c.w(x, y + 5, x, 250, INK, 2.4, n, -1 if x == xL1 else 1)
        c.sw_v(x, 250)
        c.w(x, 300, x, 360, INK, 2.4, "2" + n[1:], -1 if x == xL1 else 1)
        c.fuse_v(x, 360, "")
        c.w(x, 410, x, 520, INK, 2.4, "3" + n[1:], -1 if x == xL1 else 1)
    S.add(f'<line x1="{xL1 - 12}" y1="{265}" x2="{xL2 - 12}" y2="{265}" stroke="{INK}" stroke-dasharray="5,4"/>')
    c.t(xL2 + 30, 280, "Q1  disconnect 40 A, door handle, lockable (ABB OT40F3)", 13)
    c.t(xL2 + 30, 390, "F1, F2  Class J 35 A time delay (Mersen AJT35) in FH1", 13)
    c.t(xL2 + 30, 408, "SCCR: Class J + GS21 listed combination (confirm 5 kA at the MS-P1 bus)", 12, "start", GRY)
    # branch to 24 V
    for x, n in ((xL1, "4L1"), (xL2, "4L2")):
        c.dot(x, 460); c.w(x, 460, x + 420, 460) if False else None
    c.w(xL1, 460, 900, 460, INK, 1.4); c.w(xL2, 475, 960, 475, INK, 1.4); c.dot(xL1, 460); c.dot(xL2, 475)
    c.t(700, 452, "4L1", 12, "middle", BLU); c.t(700, 469, "4L2", 12, "middle", BLU)
    c.w(900, 460, 900, 520); c.w(960, 475, 960, 520)
    c.sw_v(900, 520, None); c.sw_v(960, 520, "Q2 2-pole C2 (S202-C2)")
    c.w(900, 570, 900, 640, INK, 1.4, "5L1", -1); c.w(960, 570, 960, 640, INK, 1.4, "5L2", 1)
    c.box(860, 640, 160, 120, "G1", ["Mean Well HDR-150-24", "230 V AC in", "24 V DC 6.3 A out"])
    c.w(940, 760, 940, 820, BLU, 1.4); c.t(950, 800, "+24 V (wire 100) / 0 V (wire 0) -> E02", 12, "start", BLU)
    # VFD
    c.box(330, 520, 210, 230, "U1  VFD", ["AutomationDirect GS21-22P0", "2 HP, 230 V 1-ph in", "STO1 / STO2 / SCM (E02)", "DI1 FWD, DI3 EF (E02)", "R1 run, R2 fault (E02)", "RS-485 Modbus (E04)"])
    c.t(xL1 - 6, 540, "R/L1", 11, "end", GRY); c.t(xL2 + 6, 540, "S/L2", 11, "start", GRY)
    for x, n in ((370, "U"), (435, "V"), (500, "W")):
        c.w(x, 750, x, 960, INK, 2.2, n, 1); c.term(x, 960, f"X2:{n}")
        c.w(x, 965, x, 1060, INK, 2.2)
    c.t(520, 1020, "W-M1  4 x 14 AWG shielded VFD cable (Lapp ÖLFLEX VFD 2XL), 4 m", 12, "start", GRY)
    c.w(370, 1060, 500, 1060, INK, 2.2); c.w(435, 1060, 435, 1100, INK, 2.2)
    c.motor(435, 1134, "")
    c.t(480, 1090, "P1-333  NORD 90LP/4, 1.5 kW [2 HP], 230 V Δ / 460 V Y, ≈ 6.2 A at 230 V (confirm), gearbox i ≈ 43.7 -> 40 rpm at 60 Hz", 13)
    c.t(435, 1190, "terminal box: connect for 230 V (low voltage)", 12, "middle", GRY)
    c.w(480, 1150, 640, 1150, RED, 1.2, "TP1"); c.w(480, 1165, 640, 1165, RED, 1.2); c.t(650, 1162, "PTC thermistors -> X2:TP1/TP2 -> K2 (E02), cable W-M2 2 x 18 AWG shielded", 12, "start", RED)
    rows = [("Motor FLA (230 V)", "≈ 6.2 A (nameplate)"), ("VFD input current, 1-ph", "≈ 24 A (GS21-22P0 table, confirm)"), ("Fuses F1/F2", "Class J 35 A TD (maker max for the drive)"),
            ("Supply conductors", "8 AWG Cu 75 °C (125 % of input)"), ("Feeder breaker at MS-P1", "40 A 2-pole"), ("Motor overload", "VFD electronic, P05.01 = FLA"),
            ("Motor cable", "14 AWG VFD cable, < 30 m (no output filter)"), ("24 V load", "≈ 1.5 A (relays, lamps, sensors, actuator 1 A peak)")]
    S.table(1700, 160, [("ITEM", 330), ("VALUE", 420)], rows, "LOAD AND PROTECTION", 14, 26)
    S.notes(1700, 420, 1150, [
        "Feed CP-301 from its own breaker in MS-P1 (update the ELE load schedule: P1-301 = 230 V 1-ph, 40 A 2-pole, 8 AWG).",
        "VFD output goes direct to the motor: no contactor or switch between U1 and the motor (STO stops the motor). Keep motor cable separate from 24 V wiring in the duct (≥ 100 mm or a divider).",
        "Bond the motor cable shield 360° at both ends (EMC gland at the panel, metal gland at the motor box). Earth the gearmotor through the cable PE, not the frame alone.",
        "Label every wire at both ends with the wire number shown; every terminal with its strip and number (E04).",
    ], fs=14)
    S.save(DWG / "P1-301-E01_power.svg")


def e02():
    S = sheet("P1-301-E02", "ELECTRICAL: CONTROL AND SAFETY SCHEMATIC", scale="NTS", material="see E03", finish="24 V DC control; safety: PL d / Cat 3 (ISO 13849-1), confirm with the risk assessment", mass="-")
    c = Sch(S)
    xa, xb = 160, 1700                     # +24 V rail, 0 V rail
    c.w(xa, 120, xa, 1720, BLU, 2.4); c.w(xb, 120, xb, 1720, BLU, 2.4)
    c.t(xa, 110, "+24 V (101, fused F3 4 A)", 13, "middle", BLU, True); c.t(xb, 110, "0 V (0)", 13, "middle", BLU, True)
    rungs = []

    def rung(y, n, text):
        c.t(60, y + 4, str(n), 13, "start", GRY, True); c.t(xb + 20, y + 4, text, 12, "start", GRY)

    # rung 1-3: safety relay input channels
    y = 190; rung(y, 1, "E-stop S0 ch1 + cover interlock P1-332 ch1 -> K0 S11/S12")
    c.dot(xa, y); c.w(xa, y, 300, y, INK, 1.4, "110"); c.pb_h(320, y, "S0 11-12", True); c.w(340, y, 460, y, INK, 1.4, "111")
    c.no_h(480, y, "P1-332 ch1 (X4:3-4)", True); c.w(500, y, 640, y, INK, 1.4, "112")
    c.box(640, 160, 320, 230, "K0  PNOZ s4 750104", ["S11-S12 ch1 / S21-S22 ch2", "S33-S34 monitored manual reset", "13-14, 23-24, 33-34 safety NO", "41-42 aux NC", "A1 +24 V / A2 0 V"])
    y = 260; rung(y, 2, "E-stop S0 ch2 + cover interlock ch2 -> K0 S21/S22")
    c.dot(xa, 190); c.w(xa, y, 300, y, INK, 1.4, "113"); c.dot(xa, y); c.pb_h(320, y, "S0 21-22", True); c.w(340, y, 460, y, INK, 1.4, "114")
    c.no_h(480, y, "P1-332 ch2 (X4:5-6)", True); c.w(500, y, 640, y, INK, 1.4, "115")
    y = 330; rung(y, 3, "RESET S3 (blue) after E-stop or cover open")
    c.dot(xa, y); c.w(xa, y, 300, y, INK, 1.4); c.pb_h(320, y, "S3 RESET"); c.w(340, y, 640, y, INK, 1.4, "116/117")
    c.w(960, 370, xb, 370, BLU, 1.4); c.t(1330, 364, "K0 A2", 11, "middle", GRY)
    # rung 4-5: STO
    for i, (y, ch, wn, k) in enumerate(((440, "STO1", "120", "13-14"), (500, "STO2", "121", "23-24"))):
        rung(y, 4 + i, f"Safe torque off channel {i + 1}: K0 {k} -> U1 {ch} (motor cannot make torque unless both are on)")
        c.dot(xa, y); c.w(xa, y, 600, y, INK, 1.4, "122"); c.no_h(620, y, f"K0 {k}"); c.w(640, y, 1200, y, INK, 1.4, wn)
        c.box(1200, y - 16, 150, 32, f"U1 {ch}"); c.w(1350, y, xb, y, INK, 1.4, "123 SCM")
    # rung 6: safety OK to plant
    y = 570; rung(y, 6, "SAFETY OK to plant PLC (X5:4): cover closed and E-stop released")
    c.dot(xa, y); c.w(xa, y, 600, y, INK, 1.4); c.no_h(620, y, "K0 33-34"); c.w(640, y, 1200, y, INK, 1.4, "180"); c.term(1210, y, "X5:4 -> CP-P1 P1_301_SafetyOK")
    # rung 7-8: run logic
    y = 680; rung(y, 7, "LOCAL: START S1 / STOP S2 with K1 seal-in; REMOTE: run request from the plant PLC (X4:9)")
    c.dot(xa, y); c.w(xa, y, 260, y, INK, 1.4, "130"); c.no_h(280, y, "S4 LOCAL 13-14"); c.w(300, y, 380, y, INK, 1.4, "131")
    c.pb_h(400, y, "S2 STOP", True); c.w(420, y, 500, y, INK, 1.4, "132"); c.pb_h(520, y, "S1 START"); c.w(540, y, 720, y, INK, 1.4, "133")
    c.dot(460, y); c.w(460, y, 460, y + 60, INK, 1.4); c.w(460, y + 60, 500, y + 60, INK, 1.4); c.no_h(520, y + 60, "K1 11-14"); c.w(540, y + 60, 600, y + 60); c.w(600, y + 60, 600, y); c.dot(600, y)
    c.no_h(740, y, "K0 aux 41-42", True); c.w(760, y, 1100, y, INK, 1.4, "133"); c.coil_h(1120, y, "K1"); c.w(1138, y, xb, y, INK, 1.4)
    y2 = 820; rung(y2, 8, "REMOTE run request (dry contact in CP-P1) through S4 REMOTE")
    c.dot(xa, y2); c.w(xa, y2, 260, y2, INK, 1.4); c.no_h(280, y2, "S4 REMOTE 23-24"); c.w(300, y2, 380, y2, INK, 1.4, "134"); c.term(400, y2, "X4:9 / W-P04 RUN REQ"); c.w(405, y2, 700, y2, INK, 1.4)
    c.w(700, y2, 700, y); c.dot(700, y)
    # rung 9: VFD FWD
    y = 920; rung(y, 9, "VFD FWD (DI1) from K1 (sink, VFD internal 24 V; DCM common)")
    c.box(250, y - 20, 160, 40, "U1 DCM"); c.w(410, y, 600, y, INK, 1.4, "140"); c.no_h(620, y, "K1 21-24"); c.w(640, y, 900, y, INK, 1.4, "141"); c.box(900, y - 20, 160, 40, "U1 DI1 FWD")
    # rung 10: thermistor
    y = 1010; rung(y, 10, "Motor PTC (X2:TP1/TP2) -> K2 EMT6; K2 trips -> U1 DI3 external fault (motor stops, FAULT lamp)")
    c.dot(xa, y); c.w(xa, y, 600, y, INK, 1.4); c.box(600, y - 30, 200, 60, "K2 EMT6-DB", ["T1-T2: motor PTC"]); c.w(800, y, xb, y, INK, 1.4)
    c.box(250, y + 50, 160, 40, "U1 DCM"); c.w(410, y + 70, 600, y + 70, INK, 1.4, "143"); c.no_h(620, y + 70, "K2 13-14"); c.w(640, y + 70, 900, y + 70, INK, 1.4, "142"); c.box(900, y + 50, 160, 40, "U1 DI3 EF")
    # rung 11-12: lamps
    for i, (y, r, lamp, txt) in enumerate(((1170, "R1", "H1 RUN (green)", "VFD relay 1 = running"), (1240, "R2", "H2 FAULT (red)", "VFD relay 2 = fault"))):
        rung(y, 11 + i, txt)
        c.dot(xa, y); c.w(xa, y, 600, y, INK, 1.4, "152"); c.no_h(620, y, f"U1 {r}A-{r}C"); c.w(640, y, 1100, y, INK, 1.4, "150" if i == 0 else "151"); c.lamp_h(1120, y, lamp.split()[0]); c.w(1132, y, xb, y)
    # rung 13: running to plant
    y = 1310; rung(y, 13, "RUNNING to plant (X5:8) from K1 (+ VFD READY MO1 to X5:5 over the same cable)")
    c.dot(xa, y); c.w(xa, y, 600, y, INK, 1.4); c.no_h(620, y, "K1 (spare 2nd CO)"); c.w(640, y, 1200, y, INK, 1.4); c.term(1210, y, "X5:8 RUNNING  /  X5:5 READY (U1 MO1)")
    # rung 14: level switch
    y = 1400; rung(y, 14, "High-level switch P1-337 (FTM20, PNP): +24 V on X4:1, signal X4:2 -> X5:3 HIGH; blender also inhibits loading in the PLC")
    c.dot(xa, y); c.w(xa, y, 400, y, INK, 1.4, "160"); c.box(400, y - 25, 200, 50, "P1-337", ["FTM20 PNP, 1-1/2 in TC"]); c.w(600, y, 1200, y, INK, 1.4, "161"); c.term(1210, y, "X5:3 HIGH")
    c.w(500, y + 25, 500, y + 50, INK, 1); c.w(500, y + 50, xb, y + 50, BLU, 1.2)
    # rung 15-16: valve
    y = 1520; rung(y, 15, "Valve P1-331: plant PLC output (X5:1) energises K331; K331 NO = OPEN, NC = CLOSE (actuator 24 V DC, 2-wire + common)")
    c.term(250, y, "X5:1 VALVE CMD (from CP-P1)"); c.w(255, y, 1100, y, INK, 1.4, "170"); c.coil_h(1120, y, "K331"); c.w(1138, y, xb, y)
    y = 1600; rung(y, 16, "")
    c.dot(xa, y); c.w(xa, y, 600, y, INK, 1.4); c.no_h(620, y, "K331 11-14"); c.w(640, y, 900, y, INK, 1.4, "171"); c.term(910, y, "X6:1 OPEN")
    c.dot(560, y); c.w(560, y, 560, y + 60); c.w(560, y + 60, 600, y + 60); c.no_h(620, y + 60, "K331 11-12", True); c.w(640, y + 60, 900, y + 60, INK, 1.4, "172"); c.term(910, y + 60, "X6:2 CLOSE")
    c.t(1100, y + 30, "limits: X6:3 OPEN -> X5:6, X6:4 CLOSED -> X5:7 (wires 173, 174)", 12, "start", GRY)
    S.notes(120, 1780, 1550, [
        "Stop categories: E-stop and cover open = STO via K0 (stop category 0, IEC 60204-1); STOP button = VFD ramp stop (cat 1 not required, cat 0 by removing FWD is acceptable: coast + 3 s decel).",
        "The cover interlock is coded-magnetic, dual channel, monitored by K0 with a manual reset: opening the cover stops the agitator; closing it does NOT restart it (RESET, then START or a new remote request).",
        "K0 aux 41-42 in the run rung drops K1 on a safety stop so the seal-in cannot hold through a reset. Remote run is a maintained request from the plant PLC; the PLC must drop it on any safety-OK loss.",
        "Validate per P1-301-900 T20..T26 before the first product batch. Keep the PNOZ s4 response time (< 30 ms) and the agitator run-down (< 2 s at 40 rpm) on the validation record.",
    ], fs=13)
    S.save(DWG / "P1-301-E02_control.svg")


def e03():
    S = sheet("P1-301-E03", "ELECTRICAL: PANEL LAYOUT AND COMPONENTS", scale="1:2, 1:4", material="Enclosure 304 SS NEMA 4X 24 x 20 x 8 in", finish="Panel UL 508A practice", mass="≈ 32 kg [70 lb] complete")
    s4, s2 = SC(4), SC(2)
    PW, PH = 432.0, 533.0
    v = S.view(220, 200 + PH * s2, s2, "BACK PANEL 432 x 533 [17 x 21] (24 x 20 enclosure)  1:2  sizes per maker data: confirm", (120, 120))
    v.rect(0, 0, PW, PH, "vis", "#f5f5f5")
    for y0, y1, x0, x1 in ((475, 515, 15, 417), (238, 270, 15, 290), (105, 127, 15, 417)):
        v.rect(x0, y0, x1 - x0, y1 - y0, "thin", "#eceff1"); v.text((x0 + x1) / 2, (y0 + y1) / 2 - 4, "wire duct 40 x 60 [1.5 x 2.4]" if y0 > 400 else "duct", 11)
    for y in (403, 182, 65):
        v.rect(15, y - 17.5, 402 if y != 403 else 275, 35, "thin", "#cfd8dc")
    items = [(20, 360, 45, 87, "Q1"), (80, 345, 60, 110, "FH1"), (310, 285, 100, 175, "U1 GS21-22P0"),
             (20, 140, 36, 85, "Q2"), (62, 152, 9, 60, "F3"), (78, 137, 105, 90, "G1 HDR-150"), (195, 135, 23, 94, "K0"),
             (226, 142, 7, 80, "K1"), (238, 142, 7, 80, "K331"), (252, 145, 23, 75, "K2"),
             (20, 40, 60, 50, "X1 X2"), (90, 40, 320, 50, "X3  X4  X5  X6  X7")]
    for x, y, w, h, tag in items:
        v.rect(x, y, w, h, "vis", "#fff"); v.text(x + w / 2, y + h / 2 - 4, tag, 12 if w > 20 else 10, rot=0 if w > 20 else -90)
    v.rect(305, 135, 110, 95, "phan"); v.text(360, 180, "spare", 11)
    v.dim((0, PH), (PW, PH), 30, f"{mmi(PW)}", "h"); v.dim((PW, 0), (PW, PH), -30, f"{mmi(PH)}", "v")
    v.note(PW / 2, -25, ["glands in the BOTTOM of the enclosure only (washdown):", "M25 x 2 (supply, motor W-M1), M20 x 5 (W-M2, W-F1, W-P04, W-P07, W-P30)"], 13, "middle")
    d = S.view(1200, 200 + 610 * s4, s4, "DOOR (outside)  1:4", (1150, 120))
    d.rect(0, 0, 508, 610, "vis", "#fafafa")
    for x, y, r, tag in ((254, 470, 30, "S0 E-STOP"), (130, 330, 14, "H1 RUN"), (254, 330, 14, "H2 FAULT"), (378, 330, 14, "S4 L/O/R"), (130, 200, 14, "S1 START"), (254, 200, 14, "S2 STOP"), (378, 200, 14, "S3 RESET")):
        d.circle(x, y, r); d.text(x, y - r - 40, tag, 12)
    d.rect(40, 520, 60, 60, "thin"); d.text(70, 545, "Q1", 11)
    d.note(254, 80, ["22 mm holes Ø22.3; legend plates engraved", "E-stop yellow backplate ZBY9330"], 12, "middle")
    d.dim((0, 610), (508, 610), 30, "508 [20]", "h"); d.dim((508, 0), (508, 610), -30, "610 [24]", "v")
    rows = [(t, dsc[:62], mk, pn[:44], q, f"${u:,.0f}", f"${u * q:,.0f}") for t, dsc, mk, pn, q, u, _ in E.COMPONENTS]
    tot = sum(u * q for *_, q, u, _ in E.COMPONENTS)
    rows.append(("", "TOTAL (estimates; confirm with quotes)", "", "", "", "", f"${tot:,.0f}"))
    S.table(1950, 140, [("TAG", 70), ("DESCRIPTION", 450), ("MAKER", 120), ("PART NUMBER", 330), ("QTY", 40), ("EACH", 70), ("EXT", 80)], rows, "COMPONENT LIST CP-301", 12, 22)
    S.notes(1150, 1100, 1400, [
        "Build to UL 508A practice: SCCR label, wire 75 °C Cu, ferrules on all stranded ends, green/yellow earth to the PE bar, door earth strap.",
        "Mount the panel on the two frame rails P1-301-410 with the Hoffman foot kit; top of panel at 1,505 [59.25] above the floor, gauges/lamps at eye level for the operator on the drive end.",
        "Keep the VFD heat sink vertical with 100 [4] clear above and below; the enclosure needs no fan at 1.5 kW (≈ 60 W loss) in a 25 °C room: confirm with the Hoffman thermal calculator for the room temperature.",
    ], fs=13)
    S.save(DWG / "P1-301-E03_panel.svg")


def e04():
    S = sheet("P1-301-E04", "ELECTRICAL: WIRES, TERMINALS, CABLES, VFD SETTINGS", scale="NTS", material="-", finish="-", mass="-")
    S.table(120, 140, [("WIRE", 60), ("FROM", 170), ("TO", 190), ("SIZE", 95), ("COL", 60), ("FUNCTION", 330)], [list(w) for w in E.WIRES[:36]], "WIRE LIST (1 of 2)", 12, 21)
    S.table(1100, 140, [("WIRE", 60), ("FROM", 170), ("TO", 190), ("SIZE", 95), ("COL", 60), ("FUNCTION", 330)], [list(w) for w in E.WIRES[36:]], "WIRE LIST (2 of 2)", 12, 21)
    S.table(1100, 620, [("STRIP", 60), ("TERMINALS", 520), ("TYPE", 170), ("USE", 380)], [list(t) for t in E.TERMINALS], "TERMINAL STRIPS", 12, 23)
    cab = [(t, d[:70], pn[:40]) for t, d, mk, pn, q, u, w in E.COMPONENTS if t.startswith("W-")]
    S.table(1100, 860, [("CABLE", 80), ("DESCRIPTION", 560), ("PART", 340)], cab, "CABLE SCHEDULE", 12, 23)
    S.table(120, 1000, [("PARAM", 90), ("NAME", 280), ("UNIT / OPTIONS", 230), ("SETTING", 370)], [list(r) for r in E.VFD], "VFD U1 GS21-22P0 SETTINGS (parameter numbers per the GS20/GS21 manual: confirm)", 12, 22)
    S.table(1100, 1060, [("SIGNAL", 230), ("DIR", 50), ("TYPE", 190), ("CABLE / TERMINAL", 170), ("PLC TAG (CP-P1)", 220)], [list(r) for r in E.IO_PLANT], "PLANT INTERFACE (to the line PLC)", 12, 22)
    S.save(DWG / "P1-301-E04_lists.svg")


if __name__ == "__main__":
    e01(); e02(); e03(); e04()
