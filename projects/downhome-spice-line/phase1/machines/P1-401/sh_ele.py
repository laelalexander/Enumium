"""P1-401 electrical: E01 power, E02 safety + control + PLC I/O, E03 panel layout, wire list, cables, terminals."""
from common import *  # noqa: F401,F403
from mechsheet import Sch, BLU, GRY
from design import calcs

INK, RED, GRN = "#111", "#b00020", "#2e7d32"
C = calcs()

COMPONENTS = [
    ("Q1", "Disconnect 25 A 2-pole, lockable OFF, side handle (P1-439)", "ABB OT25F3 + OHB45J6", "right side"),
    ("F1", "MCB 2-pole C10, servo drive supply (P1-441)", "ABB S202-C10", "rail 1"),
    ("F2", "MCB 2-pole D8, T1 primary (inrush)", "ABB S202-D8", "rail 1"),
    ("T1", "Control transformer 750 VA 208 / 120 V (P1-440)", "Hammond PH750MQMJ", "panel bottom"),
    ("F3", "MCB 1-pole C8, 120 V secondary", "ABB S201-C8", "rail 1"),
    ("Q2", "Motor protector 2.5-4.0 A, 3 poles in series (1-ph) + aux", "ABB MS116-4.0 + HKF1-11", "rail 1"),
    ("KM1", "Contactor 9 A, 24 V DC coil, 1 NO aux", "ABB AF09-30-10-13", "rail 1"),
    ("G1", "Power supply 24 V DC 2.5 A (P1-442)", "AutomationDirect PSB24-060S", "rail 2"),
    ("K1", "Safety relay, dual channel, monitored reset (P1-436)", "Pilz PNOZ s4 24 V DC", "rail 1"),
    ("A1", "Servo drive 750 W 1-ph 230 V, STO, RS-485 (P1-413)", "SureServo2 SV2A-2075", "panel right"),
    ("M1", "Servo motor 750 W (P1-413)", "SureServo2 SV2L-207B", "bridge 307"),
    ("M2", "Agitator gearmotor 1/4 HP 115 V (P1-414)", "Bison 011-series", "head plate"),
    ("A2", "PLC CPU + 8 DI / 8 DO module (P1-416)", "CLICK C2-03CPU-2 + C0-16CDD2", "rail 2"),
    ("A3", "HMI 3 in (P1-416)", "C-more Micro EA3-S3ML", "pod 106"),
    ("S0 / S1 / H1 / H2", "E-stop 2 NC, reset blue, green + red pilots (P1-437)", "GCX1131-24, GCX1102, GCX0102", "pod 106"),
    ("S2", "Foot switch 1 NO + 1 NC (P1-417)", "Linemaster 632-S", "floor"),
    ("B1", "Flap interlock, coded magnetic 2 NC (P1-438)", "Schmersal BNS 260-02z-ST", "lid 405"),
    ("B2", "Container sensor, diffuse PNP (P1-435)", "Banner QS18VP6D", "bracket 706"),
]


def e01():
    S = sheet("P1-401-E01", "ELECTRICAL: POWER (208 V 1-PH, 120 V, 24 V DC)", scale="NTS", material="see component list",
              finish="UL 508A practice, NEC 430 / 450; 75 °C Cu; SCCR 5 kA", mass="-")
    c = Sch(S)
    c.t(120, 110, "SUPPLY 208 V 1-ph 2W + PE, 20 A branch from the plant panel (≈ 9.1 A full load)", 20, bold=True)
    xA, xB = 260, 400
    c.t(xA, 160, "L1", 14, "middle", INK, True); c.t(xB, 160, "L2", 14, "middle", INK, True)
    c.w(xA, 165, xA, 200); c.w(xB, 165, xB, 200)
    c.box(200, 200, 270, 70, "Q1 OT25 2P (lockable)", ["right side of the cabinet, in sight of the filler"])
    c.w(xA, 270, xA, 330, no="1L1", side=-1); c.w(xB, 270, xB, 330, no="1L2", side=1)
    c.w(xA, 330, 1700, 330); c.w(xB, 360, 1700, 360); c.w(xB, 330, xB, 360)
    c.dot(xA, 330); c.t(1710, 335, "1L1", 12, "start", BLU); c.t(1710, 365, "1L2", 12, "start", BLU)
    # servo branch
    for x, w in ((520, "1L1"), (600, "1L2")):
        c.w(x, 330 if x == 520 else 360, x, 420); c.dot(x, 330 if x == 520 else 360)
    c.box(480, 420, 160, 60, "F1 S202-C10", ["servo drive"])
    c.w(520, 480, 520, 560, no="2L1", side=-1); c.w(600, 480, 600, 560, no="2L2", side=1)
    c.box(440, 560, 380, 180, "A1 SERVO DRIVE SV2A-2075", ["L1 / L2 main + L1C / L2C control (jumpered)", "U V W → M1 (motor cable SVC2, shielded)", "CN2 encoder ← M1",
                                                              "STO1 / STO2 ← K1 13-14 / 23-24 (E02)", "CN3 RS-485 Modbus ← PLC port 3", "regen: internal resistor (check duty)"])
    c.w(560, 740, 560, 820, no="U/V/W", side=1)
    c.S.add('<circle cx="560" cy="860" r="40" fill="#fff" stroke="#111" stroke-width="1.8"/>'); c.t(560, 858, "M1", 18, "middle", INK, True); c.t(560, 878, "servo", 11, "middle")
    c.t(620, 865, "750 W, 2.39 N·m, 3,000 rpm; 2:1 belt to the auger", 12)
    # transformer branch
    for x in (900, 980):
        c.w(x, 330 if x == 900 else 360, x, 420); c.dot(x, 330 if x == 900 else 360)
    c.box(860, 420, 160, 60, "F2 S202-D8", ["T1 primary"])
    c.w(900, 480, 900, 540, no="3L1", side=-1); c.w(980, 480, 980, 540, no="3L2", side=1)
    c.box(860, 540, 160, 90, "T1 750 VA", ["H1-H4: 208 V", "X1-X2: 120 V", "X2 bonded to PE"])
    c.w(900, 630, 900, 690, no="X1", side=-1); c.w(980, 630, 980, 1090, no="X2 (N)", side=1)
    c.box(860, 690, 100, 50, "F3 S201-C8", [])
    c.w(900, 740, 900, 780, no="4L", side=-1)
    c.w(900, 780, 1500, 780); c.w(980, 1090, 1500, 1090)
    c.dot(900, 780); c.t(1510, 785, "120 V L (4L)", 12, "start", BLU); c.t(1510, 1095, "120 V N (4N), bonded at T1", 12, "start", BLU)
    c.w(1040, 780, 1040, 820); c.dot(1040, 780)
    c.box(990, 820, 150, 60, "Q2 MS116-4.0", ["set 3.6 A (FLA)", "3 poles in series"])
    c.w(1040, 880, 1040, 920, no="5L", side=-1)
    c.box(990, 920, 150, 50, "KM1 AF09", ["coil 24 V DC (E02)"])
    c.w(1040, 970, 1040, 1010, no="W2 1", side=-1)
    c.S.add('<circle cx="1110" cy="1040" r="32" fill="#fff" stroke="#111" stroke-width="1.8"/>'); c.t(1110, 1038, "M2", 16, "middle", INK, True); c.t(1110, 1056, "1~", 11, "middle")
    c.w(1040, 1010, 1080, 1030); c.w(1140, 1050, 1180, 1090, no="W2 2"); c.dot(1180, 1090)
    c.t(1150, 1000, "agitator gearmotor 1/4 HP 115 V 60 rpm", 12)
    c.w(1300, 780, 1300, 840); c.dot(1300, 780); c.w(1380, 1090, 1380, 900); c.dot(1380, 1090)
    c.box(1260, 840, 180, 60, "G1 PSB24-060S", ["120 V in → 24 V DC 2.5 A"])
    c.w(1300, 900, 1300, 960, no="+24", side=-1); c.t(1290, 980, "to E02 (+24 / 0 V, 0 V bonded to PE)", 12, "start", GRY)
    # PE
    c.w(150, 200, 150, 1150, GRN); c.w(150, 1150, 1500, 1150, GRN); c.t(140, 700, "PE", 14, "end", GRN, True)
    c.t(160, 1175, "PE bar on the back panel: supply PE, door bond, Q1, T1 X2, G1 0 V, A1, M1 (motor cable shield 360°), M2 frame, column + head (bonded through the bolts, check < 0.1 Ω).", 12, "start", GRN)
    S.table(1750, 150, [("TAG", 150), ("DESCRIPTION", 560), ("PART", 380), ("WHERE", 140)], COMPONENTS, "COMPONENTS", fs=12, rh=21)
    S.notes(1750, 600, 1580, [
        "Loads at 208 V: servo drive ≈ 5.5 A (rated input), T1 primary 3.6 A → 9.1 A; supply 12 AWG on a 20 A breaker (plant panel schedule M-401).",
        "T1 secondary 6.25 A FLA: gearmotor 3.6 A + G1 0.7 A + HMI/PLC on 24 V. F2 is D-curve for the transformer inrush (NEC 450.3(B) ≤ 250 %).",
        "Servo motor cable and encoder cable: factory SVC2 assemblies, 3 m, run in their own duct up the column; shields clamped 360° at the drive.",
        "Disconnect Q1 is in sight of the filler and lockable; it isolates everything in the cabinet and the head (LOTO point for tooling change and cleaning).",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-401-E01_power.svg")


def e02():
    S = sheet("P1-401-E02", "ELECTRICAL: SAFETY CIRCUIT, CONTROL 24 V, PLC I/O", scale="NTS", material="see E01", finish="EN ISO 13849-1 PL d target (cat. 3)", mass="-")
    c = Sch(S)
    c.t(120, 110, "+24 V / 0 V from G1 (E01)", 20, bold=True)
    c.w(150, 150, 3300, 150, RED); c.t(150, 140, "+24 V", 13, "start", RED, True)
    c.w(150, 1100, 3300, 1100, "#1565c0"); c.t(150, 1125, "0 V (bonded to PE at G1)", 13, "start", "#1565c0", True)
    # safety relay K1
    c.t(1050, 215, "SAFETY: E-STOP + FLAP INTERLOCK → STO + AGITATOR STOP (stop category 0, PL d target)", 15, bold=True)
    c.box(700, 250, 320, 330, "K1 PNOZ s4", ["A1 +24 / A2 0 V", "S11-S12 ch 1 / S21-S22 ch 2", "S33-S34 reset (monitored)", "13-14 / 23-24 / 33-34 safety NO", "Y32 status (semiconductor)"])
    for i, (x, lab) in enumerate(((300, "ch 1"), (450, "ch 2"))):
        c.w(x, 150, x, 260); c.sw_v(x, 260, "S0 E-STOP" if i == 0 else None, nc=True); c.w(x, 310, x, 360)
        c.sw_v(x, 360, "B1 FLAP" if i == 0 else None, nc=True); c.w(x, 410, x, 450)
        c.w(x, 450, 700, 300 + 40 * i, no=f"S{1 + i}2", side=1)
        c.t(x - 10, 250, lab, 11, "end", GRY)
    c.t(300, 470, "S0 + B1 both channels in series; cross-fault detection by K1 (S11/S21 pulsed)", 11, "start", GRY)
    c.w(860, 150, 860, 250)
    c.w(600, 520, 700, 520); c.pb_h(560, 520, "S1 RESET"); c.w(480, 520, 540, 520); c.w(480, 520, 480, 150)
    c.w(1020, 300, 1300, 300, no="K1 13-14 → STO1"); c.w(1020, 350, 1300, 350, no="K1 23-24 → STO2")
    c.box(1300, 270, 220, 110, "A1 servo CN1", ["STO1 / STO2 (24 V = run)", "SON / CTRG / ARST in", "SRDY / ALRM / TPOS out"])
    c.w(1020, 420, 1650, 420, no="K1 33-34"); c.w(1020, 470, 1200, 470, no="K1 Y32 → X3")
    c.w(860, 580, 860, 1100)
    # agitator rung: K1 33-34 then PLC Y3 then KM1 coil
    c.no_h(1700, 420, "PLC Y3"); c.w(1720, 420, 1800, 420); c.coil_h(1840, 420, "KM1")
    c.w(1858, 420, 1950, 420); c.w(1950, 420, 1950, 1100); c.t(1960, 470, "agitator runs only with K1 closed and Y3 on", 11, "start", GRY)
    # PLC I/O block
    c.t(150, 640, "PLC A2: CLICK C2-03CPU-2 + C0-16CDD2 (8 DI sinking/sourcing 24 V, 8 DO sourcing 0.3 A)", 15, bold=True)
    ins = [("X1", "S2 foot switch NO (start dose)"), ("X2", "B2 container present (PNP)"), ("X3", "K1 Y32 safety OK"), ("X4", "A1 SRDY servo ready"),
           ("X5", "A1 ALRM (1 = no alarm)"), ("X6", "A1 TPOS move done"), ("X7", "Q2 HKF1 13-14 (1 = not tripped)"), ("X8", "KM1 aux 13-14 (feedback)")]
    outs = [("Y1", "A1 SON servo enable"), ("Y2", "A1 CTRG start move (PR path = dose)"), ("Y3", "KM1 agitator (via K1 33-34)"), ("Y4", "A1 ARST alarm reset"),
            ("Y5", "H1 green: ready / dosing"), ("Y6", "H2 red: alarm / E-stop"), ("Y7", "spare"), ("Y8", "spare")]
    for i, (t, d) in enumerate(ins):
        y = 700 + 45 * i
        c.w(200, 150, 200, 700 + 45 * 7) if i == 0 else None
        c.w(200, y, 290, y); c.no_h(310, y); c.w(330, y, 560, y, no=f"{t}"); c.t(570, y + 4, f"{t}  {d}", 12)
    c.box(950, 680, 220, 380, "A2 PLC", ["X1-X8 → logic", "Y1-Y8 →", "port 2 RS-232: HMI A3", "port 3 RS-485: A1 Modbus", "Ethernet: MES Modbus TCP"])
    for i, (t, d) in enumerate(outs):
        y = 700 + 45 * i
        c.w(1170, y, 1450, y, no=t); c.t(1460, y + 4, f"{t}  {d}", 12)
    c.w(1060, 1060, 1060, 1100)
    for x, yy, t, tag in ((2300, 880, "Y5", "H1 green"), (2450, 925, "Y6", "H2 red")):
        c.w(x, yy, x, 1000); c.lamp_h(x, 1012, tag); c.w(x, 1024, x, 1100); c.t(x + 8, yy + 40, t, 11, "start", "#1565c0")
    c.w(1760, 880, 2300, 880); c.w(1760, 925, 2450, 925)
    c.t(2240, 840, "Y5 → H1, Y6 → H2 (pod 106), returns to 0 V", 11, "start", GRY)
    c.t(2200, 200, "DOSE SEQUENCE (PLC)", 15, bold=True)
    seq = ["1  Power on: K1 reset (S1) → X3 = 1; PLC sets Y1 SON; X4 SRDY = 1 → H1 on, Y3 agitator on.",
           "2  Operator selects the product on the HMI: PLC writes the PR path revs (servo counts) over Modbus.",
           "3  Container on the nest → X2 = 1; foot switch X1 (edge) → Y2 CTRG pulse 50 ms.",
           "4  Servo runs the dose (S 900 / J 600 rpm at the auger); X6 TPOS = 1 → dose done, count + 1.",
           "5  Remove the container (X2 = 0) before the next dose; no dose without a container.",
           "6  Hopper low (MES level) or X5 / X7 = 0 → stop, Y6 red, message on the HMI; Y4 ARST from the HMI.",
           "7  E-stop or flap open → K1 drops: STO removes motor torque at once, KM1 drops; Y1 off until reset.",
           f"Dose times: shaker {C['shaker-250']['t_dose']:.2f} s, jar {C['jar-12']['t_dose']:.2f} s, tub {C['tub-5lb']['t_dose']:.1f} s (P1-401-900)."]
    for i, l in enumerate(seq):
        c.t(2200, 240 + 26 * i, l, 12)
    S.notes(2200, 500, 1150, [
        "STO wiring per the SureServo2 manual: both channels from separate K1 contacts; the drive's STO status is not used for safety.",
        "Validate the safety function at commissioning (ITP T14): E-stop and flap each stop the auger and agitator; a single wire fault is detected by K1 on reset.",
        "Foot switch NC contact is spare (wired to the terminal X10 for a later 2-channel start if required).",
    ], "SAFETY NOTES", fs=13)
    S.save(DWG / "P1-401-E02_control.svg")


WIRES = [
    ("1L1 / 1L2", "supply TB X0 : 1 / 2", "Q1 : 1 / 3", "12 AWG MTW black", "20 A branch"),
    ("1L1 / 1L2", "Q1 : 2 / 4", "F1, F2 line (bridged)", "12 AWG MTW black", ""),
    ("2L1 / 2L2", "F1 : 2 / 4", "A1 : L1, L1C / L2, L2C", "14 AWG MTW black", "jumper L1-L1C, L2-L2C"),
    ("3L1 / 3L2", "F2 : 2 / 4", "T1 : H1 / H4 (H2-H3 linked)", "14 AWG MTW black", "208 V tap"),
    ("X1 / 4N", "T1 : X1 / X2", "F3 : 1 / N bar", "14 AWG MTW black / white", "X2 bonded to PE"),
    ("4L", "F3 : 2", "Q2 : 1, G1 : L", "14 AWG black", ""),
    ("5L", "Q2 : 6 (poles in series)", "KM1 : 1/L1", "14 AWG black", ""),
    ("W2 1 / 2 / PE", "KM1 : 2/T1, N bar, PE", "M2 L / N / PE", "SOOW 14/3, 4 m", "up the column, gland M20"),
    ("W1", "A1 : U V W PE", "M1", "SVC2 motor cable 3 m", "shield 360° at the drive"),
    ("W1E", "A1 : CN2", "M1 encoder", "SVC2 encoder cable 3 m", ""),
    ("+24 / 0", "G1 : + / -", "TB X1 : 1-10 / 11-20", "18 AWG red / blue", "0 V bonded to PE at G1"),
    ("S11-S22", "K1", "S0 → B1 → K1 (2 ch)", "18 AWG red / white", "pod + lid: 4C 18 AWG shielded"),
    ("K1 13-14 / 23-24", "K1", "A1 CN1 STO1 / STO2", "18 AWG grey", "separate channels"),
    ("K1 33-34", "K1", "PLC Y3 → KM1 A1", "18 AWG", "KM1 A2 → 0 V"),
    ("X1-X8", "field / A1 / K1", "PLC C0-16CDD2 X1-X8", "18 AWG white", "see E02"),
    ("Y1-Y6", "PLC C0-16CDD2", "A1 CN1, KM1, H1, H2", "18 AWG violet", ""),
    ("COM 485", "PLC port 3 (+/-/0)", "A1 CN3", "1 pair 24 AWG shielded", "120 Ω end resistor at A1"),
    ("ETH", "PLC RJ45", "plant switch (MES)", "Cat 6 S/FTP", "gland M20"),
]


def e03():
    S = sheet("P1-401-E03", "ELECTRICAL: PANEL LAYOUT, WIRE LIST, CABLES", scale="1:2 (panel)", material="back panel P1-401-105 2 mm", finish="labels both ends; ferrules; duct 40 x 60", mass="-")
    s = SC(2)
    v = S.view(180 + 270 * s, 260 + 617 * s, s, "BACK PANEL 105 (1:2), SEEN FROM THE FRONT (DOOR OPEN)", (170, 200))
    rr = lambda x0, y0, x1, y1, k="vis", fill="#fff": v.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0), k, fill)
    rr(-270, 0, 270, 617, "vis", "#f4f6f8")
    for z in (480.0, 330.0, 180.0):
        rr(-250, z - 17.5, 130, z + 17.5, "phan")
    for z in (550.0, 405.0, 255.0, 105.0):
        rr(-260, z - 20, 130, z + 20, "hid")
    items = [(-245, 480, 36, "F1"), (-205, 480, 36, "F2"), (-165, 480, 18, "F3"), (-140, 480, 45, "Q2"), (-90, 480, 45, "KM1"), (-35, 480, 45, "K1"),
             (-245, 330, 30, "A2 CPU"), (-213, 330, 70, "A2 I/O C0-16CDD2"), (-120, 330, 60, "G1"), (-55, 330, 40, "TB X0"),
             (-245, 180, 230, "TB X1 / X2 (UT 4)"), ]
    for x, z, w, t in items:
        rr(x, z - 45, x + w, z + 45, "vis", "#dfe7f1"); v.text(x + w / 2, z + 55, t, 10)
    rr(145, 120, 255, 560, "vis", "#dfe7f1"); v.text(200, 340, "A1 SERVO", 12); v.text(200, 320, "DRIVE", 12)
    rr(-250, 20, -110, 120, "vis", "#dfe7f1"); v.text(-180, 70, "T1 750 VA", 11)
    rr(-90, 20, 120, 60, "vis", "#cfd8dc"); v.text(15, 40, "PE bar + N bar", 10)
    v.dim((-270, 0), (270, 0), -30, None, "h"); v.dim((270, 0), (270, 617), -30, None, "v")
    v.note(-270, -60, ["DIN 35 rails at z 180 / 330 / 480; duct 40 x 60 between rows; A1 needs 50 above and below (airflow)"], 11)
    S.table(1350, 160, [("WIRE", 150), ("FROM", 280), ("TO", 330), ("TYPE", 280), ("NOTE", 320)], WIRES, "WIRE LIST", fs=12, rh=21)
    S.table(1350, 600, [("CABLE", 90), ("FROM", 170), ("TO", 230), ("SPEC", 380), ("LENGTH", 90), ("GLAND", 90)], [
        ("W0", "plant panel", "TB X0", "3C 12 AWG TC-ER + G/Y, 600 V", "≈ 15 m", "M25"),
        ("W1 / W1E", "A1", "M1 servo", "SVC2 motor + encoder (factory)", "3 m", "column"),
        ("W2", "KM1", "M2 gearmotor", "SOOW 14/3", "4 m", "column"),
        ("W3", "TB X1", "pod 106 (S0, S1, H1, H2, A3)", "12C 18 AWG shielded + RS-232", "1 m", "Ø25 top"),
        ("W4", "TB X1", "B1 flap switch (M12)", "M12 8-pin PUR, shielded", "3 m", "column"),
        ("W5", "TB X1", "B2 sensor (M12)", "MQDEC2-506 PUR 4-pin", "2 m", "M20"),
        ("W6", "TB X1", "S2 foot switch", "4C 18 AWG SOOW (factory cord)", "3 m", "M20"),
        ("W7", "PLC", "MES switch", "Cat 6 S/FTP", "≈ 20 m", "M20")], "CABLE SCHEDULE", fs=12, rh=21)
    S.table(1350, 830, [("TERMINAL", 120), ("FUNCTION", 330), ("TERMINAL", 120), ("FUNCTION", 330)], [
        ("X0 1-2", "208 V L1 / L2 in", "X1 1-10", "+24 V distribution"), ("X0 PE", "supply earth", "X1 11-20", "0 V distribution"),
        ("X2 1-4", "S0 E-stop 2 ch", "X2 5-8", "B1 flap 2 ch"), ("X2 9-10", "S1 reset", "X2 11-14", "H1, H2 lamps"),
        ("X2 15-16", "S2 foot switch NO / NC", "X2 17-19", "B2 sensor + / - / out")], "TERMINALS", fs=12, rh=21)
    S.notes(1350, 1350, 1650, [
        "Build to UL 508A practice: SCCR 5 kA marked on the door, wire colours: black power, white neutral, red +24, blue 0 V, green/yellow PE.",
        "Point-to-point check and hi-pot (500 V DC insulation ≥ 1 MΩ on power circuits, PLC and drive disconnected) before power-on (ITP T13).",
        "Head cables (W1, W1E, W2, W4) run up inside the column through the Ø60 passes and leave by the Ø40 hole in head plate 301; leave a 200 loop for head adjustment.",
    ], "BUILD NOTES", fs=13)
    S.save(DWG / "P1-401-E03_panel_lists.svg")


if __name__ == "__main__":
    e01(); e02(); e03()
    print("ok")
