"""P1-406 electrical E01: 120 V motor circuit, 24 V PLC control, reject pusher, enclosure layout, components, wire list, cables, I/O map, sequence."""
from common import *  # noqa: F401,F403
from mechsheet import Sch, BLU, GRY  # noqa: F401
from design import calcs, ELE, ENC, MOTOR, REJ, HEAD, PUL

INK, RED, GRN = "#111", "#b00020", "#2e7d32"
C = calcs()
ENC_W, ENC_H, ENC_D = ENC["x1"] - ENC["x0"], ENC["h"], ENC["y1"] - ENC["y0"]
LID_OPS = {"S0": (0.0, 190.0, 20.0, "#c62828", "E-STOP"), "S1": (-50.0, 115.0, 14.0, "#43a047", "START"),
           "S2": (50.0, 115.0, 14.0, "#c62828", "STOP"), "S3": (0.0, 55.0, 14.0, "#263238", "RESET (KEY)")}

COMPONENTS = [
    ("X0", "Cord SJOOW 14/3 3 m + NEMA 5-15P, gland M20 (P1-459)", "bench receptacle 15/20 A", "box, bottom"),
    ("TB1", "DIN terminals 2.5 mm²: 1, 2, N + PE (P1-459)", "AutomationDirect DN-T12 + DN-G12", "panel, rail 2"),
    ("F1", "Fuse holder 5 x 20 + 6 A time-delay (P1-459)", "DN-F6 + Bussmann GDC-6.3A", "panel, rail 2"),
    ("F2", "Fuse holder 5 x 20 + 3 A fast, pusher 24 V (P1-459)", "DN-F6 + GMA-3A", "panel, rail 2"),
    ("S0", "E-stop 40 mm mushroom, twist release, 2 NC (P1-459)", "GCX1131 + 2 NC blocks", "lid, top"),
    ("S1", "START push button flush green, 1 NO (P1-459)", "GCX1101", "lid, left"),
    ("S2", "STOP push button flush red, 1 NC (P1-459)", "GCX1103", "lid, right"),
    ("S3", "RESET key switch 2-pos spring return, 1 NO, QA key (P1-459)", "GCX1300-key class", "lid, bottom"),
    ("G1", "Power supply 120 V AC → 24 V DC 3.2 A (P1-459)", "Mean Well LRS-75-24", "panel, bottom"),
    ("TB2", "DIN terminals 24 V: +24 x 8, 0 V x 8 (P1-459)", "DN-T12 red / blue", "panel, rail 2"),
    ("A1", "PLC 8 DC in / 6 DC out sourcing, 24 V (P1-459)", "AutomationDirect CLICK C0-00DD2-D", "panel, rail 1"),
    ("A2", "Input module 8 DC in (P1-459)", "AutomationDirect C0-08ND3", "panel, rail 1"),
    ("K1", "Motor contactor 9 A, 24 V DC coil + diode (P1-459)", "DC1-09-10-24 class", "panel, rail 1"),
    ("K2, K3", "Relay DPDT 24 V DC, pusher out / in (P1-421)", "Omron G2R-2-SND-24 + P2RF-08-E", "panel, rail 1"),
    ("M1", "Gearmotor 1/8 HP 115 V 1-ph, 2 A, thermal protected (P1-420)", "Bison 017-656 class", "outfeed shaft, -y"),
    ("M2", "Linear actuator 24 V DC 150 stroke, internal limits (P1-421)", "Progressive Automations PA-14-6-35", "pusher bracket 301"),
    ("B1", "Photo eye retro-polarised M18 PNP, light-operate (P1-460)", "Banner QS18VP6LP + BRT-32X20AM", "outfeed -y plate"),
    ("B2", "Photo eye retro-polarised M18 PNP (bin entry) (P1-460)", "Banner QS18VP6LP + BRT-32X20AM", "bin slot"),
    ("B3", "Reed switch, closed with the lid shut (P1-460)", "SR class + magnet", "bin lid"),
    ("H1-H4", "Stack light G / A / R + buzzer 24 V DC (P1-461)", "Patlite LR4-302QJBW class", "pole 403"),
    ("A3", "Metal detector head + control, own 120 V cord (P1-418)", "Fortress Stealth class (used)", "head stand 104"),
]

WIRES = [
    ("1", "X0 black (L)", "TB1:1", "cord 14 AWG", ""),
    ("N", "X0 white (N)", "TB1:N", "cord 14 AWG", ""),
    ("PE", "X0 green", "TB1:PE → PE stud", "cord 14 AWG", "stud on the box floor"),
    ("1", "TB1:1", "F1 in", "16 AWG MTW black", ""),
    ("2", "F1 out", "TB1:2 → G1 L, S0 11", "16 AWG black", "G1 stays live in E-stop"),
    ("3", "S0 12", "K1 1L1", "16 AWG black", "S0 NC-1 breaks the motor line"),
    ("4", "K1 2T1", "W1 → M1 black", "16 AWG black", ""),
    ("N", "TB1:N", "G1 N, W1 → M1 white", "16 AWG white", ""),
    ("PE", "PE stud", "G1 ⏚, W1 green → M1 frame", "16 AWG green / yellow", "frame bonded via the leg"),
    ("10", "G1 +V", "TB2:+24", "16 AWG red", ""),
    ("11", "G1 -V", "TB2:0V", "16 AWG blue", "0 V to PE at TB2 (one point)"),
    ("12 / 13", "TB2", "A1 +24 / 0V, A2 C", "18 AWG red / blue", ""),
    ("20", "TB2:+24", "S1 13, S2 11, S3 13", "18 AWG red", "lid loop, 300 slack"),
    ("21", "S1 14", "A1 X1", "18 AWG white", "START"),
    ("22", "S2 12", "A1 X2", "18 AWG white", "STOP (NC: 0 = stop)"),
    ("23 / 24", "TB2:+24", "W5 → A3 DETECT C / FAULT C", "W5 4 x 18 AWG", "head dry contacts"),
    ("25", "W5 DETECT NO", "A1 X3", "W5", "head relay fail-safe: 1 = clear"),
    ("26", "W5 FAULT NO", "A1 X4", "W5", "1 = head healthy"),
    ("27-29", "TB2 / A1 X5", "W6 → B1 brown / blue / black", "M12 4-pin PUR 2 m", "pack at reject"),
    ("30-32", "TB2 / A1 X6", "W7 → B2 brown / blue / black", "M12 4-pin PUR 2 m", "bin entry"),
    ("33", "TB2:+24", "W8 → B3 → A1 X7", "W8 2 x 18 AWG", "1 = lid shut"),
    ("34", "S3 14", "A2 X101", "18 AWG white", "RESET (QA key)"),
    ("40", "TB2:+24", "S0 21", "18 AWG red", ""),
    ("41", "S0 22", "F2 in, A1 X8", "18 AWG red", "1 = E-stop healthy"),
    ("42", "F2 out", "K2 / K3 NO (12, 22)", "18 AWG red", "+24 S pusher supply"),
    ("43", "TB2:0V", "K2 / K3 NC (14, 24)", "18 AWG blue", ""),
    ("44 / 45", "K2 COM 11 / K3 COM 21", "W9 → M2 red / black", "W9 2 x 18 AWG", "both off = both 0 V (brake)"),
    ("50", "A1 Y1", "K1 A1 (coil)", "18 AWG white", "A2 to 0V; diode across"),
    ("51 / 52", "A1 Y2 / Y3", "K2 / K3 coils", "18 AWG white", "software interlock + both-on = no motion"),
    ("53-56", "A1 Y4 / Y5 / Y6", "W10 → H1 green / H2 amber / H3 red + H4 buzzer", "W10 6 x 20 AWG", "common 0V"),
]

CABLES = [
    ("W0", "TB1", "5-15P (bench)", "SJOOW 14/3 3 m (P1-459)", "G1 M20, box bottom"),
    ("W1", "K1 / TB1 / PE", "M1 gearmotor", "SJOOW 16/3 2 m", "G2 M20; under the spine to the outfeed leg"),
    ("W5", "TB2 / A1 X3-X4", "A3 head relays", "4 x 18 AWG shielded 3 m", "G3 M20; shield at the box end only"),
    ("W6, W7", "TB2 / A1 X5-X6", "B1, B2 eyes", "M12 4-pin PUR 2 m + 3 m ext.", "G4 M20 multi-hole insert"),
    ("W8, W9", "A1 X7 / K2-K3", "B3 lid, M2 pusher", "2 x 18 AWG PUR 3 m each", "G4 multi-hole; P-clips on the -y leg"),
    ("W10", "A1 Y4-Y6", "stack light", "6 x 20 AWG PUR 2 m", "G5 M20; inside pole 403"),
]

IO = [
    ("X1", "S1 START", "rising edge → run (if all OK)"),
    ("X2", "S2 STOP (NC)", "0 → stop belt"),
    ("X3", "A3 DETECT relay (fail-safe)", "0 → detect: track pack to reject"),
    ("X4", "A3 FAULT relay", "0 → head fault: stop, red"),
    ("X5", "B1 pack at reject", "tracked pack arrives → stop + push"),
    ("X6", "B2 bin entry", "must pulse within 2 s of push"),
    ("X7", "B3 lid shut", "0 → stop, amber; no start"),
    ("X8", "S0 healthy (after NC-2)", "0 → E-stop latch"),
    ("X101", "S3 RESET key (QA)", "clears a reject-fail latch"),
    ("Y1", "K1 motor contactor", "belt run"),
    ("Y2 / Y3", "K2 extend / K3 retract", "never both (software)"),
    ("Y4", "H1 green", "running, all OK"),
    ("Y5", "H2 amber", "stopped / lid open / test due"),
    ("Y6", "H3 red + H4 buzzer", "fault or reject-fail latch"),
]


def e01():
    S = sheet("P1-406-E01", "ELECTRICAL: SCHEMATIC, PANEL, WIRING", scale="NTS · 1:2.5 (enclosure)", material="see component list",
              finish="NEC 430, UL 508A practice; 75 °C Cu; cord-and-plug; 24 V SELV control", mass="-")
    c = Sch(S)
    c.t(120, 110, f"SUPPLY 120 V 1-ph 60 Hz, cord and plug, 15/20 A bench receptacle (≈ {ELE['A']:.1f} A max). The search head A3 has its own cord and receptacle.", 20, bold=True)
    xL, xN = 250, 1000
    c.box(150, 140, 280, 60, "X0 CORD SJOOW 14/3 + 5-15P", ["L black / N white / PE green"])
    c.w(xL, 200, xL, 250, no="1", side=-1); c.w(330, 200, 330, 230); c.w(330, 230, xN, 230, no="N")
    c.w(175, 200, 175, 720, GRN); c.w(175, 720, 640, 720, GRN); c.t(168, 470, "PE", 13, "end", GRN, True)
    c.term(xL, 250, "TB1:1"); c.term(xN, 230, "TB1:N")
    c.fuse_v(xL, 255, "F1  6 A T")
    c.w(xL, 305, xL, 340, no="2", side=-1); c.dot(xL, 340)
    c.w(xL, 340, 600, 340, no="2"); c.w(600, 340, 600, 380)
    c.box(560, 380, 220, 120, "G1 LRS-75-24", ["L ← 2   N ← N   ⏚ ← PE", "24 V 3.2 A (76 W)", "+V / -V → TB2"])
    c.w(xN, 230, xN, 680); c.w(740, 360, xN, 360, no="N"); c.w(740, 360, 740, 380); c.dot(xN, 360)
    c.w(640, 720, 640, 500, GRN)
    c.sw_v(xL, 360, "S0 E-STOP NC-1 (11-12)", nc=True)
    c.w(xL, 410, xL, 450, no="3", side=-1)
    c.sw_v(xL, 450, "K1 MAIN (1L1-2T1)")
    c.w(xL, 500, xL, 545, no="4", side=-1)
    S.add(f'<circle cx="{xL}" cy="580" r="34" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
    c.t(xL, 578, "M", 20, "middle", INK, True); c.t(xL, 596, "1~", 13, "middle")
    c.t(xL + 44, 575, "M1 GEARMOTOR P1-420", 13, bold=True); c.t(xL + 44, 593, f"1/8 HP 115 V {MOTOR['A']:.0f} A, {MOTOR['rpm']:.0f} rpm, thermal", 11)
    c.w(xL, 614, xL, 680); c.w(xL, 680, xN, 680, no="N (W1)"); c.dot(xN, 680)
    c.w(175, 640, xL - 34, 640, GRN); c.dot(175, 640)
    c.t(1060, 250, "A3 SEARCH HEAD (P1-418): own cord to its own receptacle, so it stays powered and stable;", 12)
    c.t(1060, 268, "only its dry relay contacts come into this box (W5). Configure both relays fail-safe (energised = OK).", 12)
    # 24 V bus
    y24, y0 = 780, 1130
    c.w(600, 500, 600, y24, RED, no="10 +24", side=-1); c.w(720, 500, 720, 740, BLU); c.w(720, 740, 1950, 740, BLU, no="11 0V")
    c.w(560, y24, 1950, y24, RED); c.t(550, y24 + 5, "+24", 13, "end", RED, True)
    c.w(1950, 740, 1950, y0, BLU); c.w(280, y0, 1950, y0, BLU); c.t(270, y0 + 5, "0V", 13, "end", BLU, True)
    c.t(760, 732, "0V bonded to PE at TB2 (one point)", 11, "start", GRN)
    # PLC
    px0, px1 = 1060, 1420
    c.box(px0, 820, px1 - px0, 290, "A1 CLICK C0-00DD2-D + A2 C0-08ND3", ["+24 / 0V (12 / 13)", "X1..X8 inputs (left)", "X101 RESET (A2)", "Y1..Y6 sourcing outputs (right)",
                                                                          "program P1-406-FW-01 (CLICK software)", "scan < 5 ms; belt position by timer", f"at {C['v']:.0f} mm/s (no encoder)"])
    c.w(1100, y24, 1100, 820, RED, no="12", side=-1); c.dot(1100, y24); c.w(1140, 1110, 1140, y0, BLU, no="13", side=1); c.dot(1140, y0)
    # inputs: x ascending → signal y descending (no crossings)
    ins = [("S1 START", "21 X1", False), ("S2 STOP", "22 X2", True), ("A3 DETECT", "25 X3", False), ("A3 FAULT", "26 X4", False),
           ("B1 PNP", "29 X5", False), ("B2 PNP", "32 X6", False), ("B3 LID", "33 X7", False), ("S3 RESET", "34 X101", False)]
    for i, (tag, no, nc) in enumerate(ins):
        x = 330 + i * 92; sy = 1100 - i * 26
        c.w(x, y24, x, 800, RED); c.dot(x, y24)
        c.sw_v(x, 800, None, nc=nc); c.t(x, 868, tag, 10, "middle", INK, True)
        c.w(x, 850, x, sy); c.w(x, sy, px0, sy, INK, no=no)
    c.t(330, 1150 + 8, "B1 / B2: brown +24, blue 0V (TB2), black → input. A3 relays: C ← +24 (23 / 24), NO → X3 / X4.", 11, "start", GRY)
    # outputs: y ascending → x descending
    outs = [("Y1", "50", "K1", "coil"), ("Y2", "51", "K2", "coil"), ("Y3", "52", "K3", "coil"), ("Y4", "53", "H1 G", "lamp"), ("Y5", "54", "H2 A", "lamp"), ("Y6", "55", "H3 R", "lamp")]
    for i, (y_, no, tag, kind) in enumerate(outs):
        yy = 840 + i * 44; xe = 1910 - i * 70
        c.w(px1, yy, xe - 60, yy, INK, no=f"{no} {y_}")
        (c.coil_h if kind == "coil" else c.lamp_h)(xe - 40, yy, tag)
        c.w(xe - 22 if kind == "coil" else xe - 28, yy, xe, yy); c.w(xe, yy, xe, y0, BLU); c.dot(xe, y0)
    c.dot(1460, 1060); c.w(1460, 1060, 1460, 1083); c.lamp_h(1460, 1095, ""); c.t(1478, 1100, "H4 BUZZER", 10, "start", INK, True)
    c.w(1460, 1107, 1460, y0, BLU); c.dot(1460, y0)
    # pusher circuit above the bus: +24 → S0 NC-2 → (X8) → F2 → K2 / K3 changeovers → M2
    xs = 1300
    c.w(xs, y24, xs, 700, RED, no="40", side=-1); c.dot(xs, y24)
    c.sw_v(xs, 650, "S0 NC-2 (21-22)", nc=True)
    c.w(xs, 650, xs, 610, RED, no="41", side=-1); c.dot(xs, 625)
    c.w(xs, 625, 1180, 625, RED); c.w(1180, 625, 1180, 820, RED, no="41 → X8", side=-1)
    c.fuse_v(xs, 560, "F2  3 A"); c.w(xs, 610, xs, 610)
    c.w(xs, 560, xs, 520, RED, no="42 +24 S", side=-1); c.w(xs, 520, 1820, 520, RED)
    c.w(1400, 700, 1860, 700, BLU, no="43 0V"); c.w(1860, 700, 1860, 740, BLU); c.dot(1860, 740)
    for k, (xk, tag, lead) in enumerate(((1460, "K2 EXTEND (11-12-14)", "44 → M2 red"), (1660, "K3 RETRACT (21-22-24)", "45 → M2 black"))):
        c.w(xk, 520, xk, 545); c.dot(xk, 520)
        c.box(xk - 60, 545, 120, 100, tag.split(" (")[0], ["NO ← +24 S", "NC ← 0V", "COM → M2"])
        c.w(xk + 40, 645, xk + 40, 700, BLU); c.dot(xk + 40, 700)
        c.w(xk - 60, 595, xk - 95 if k == 0 else xk - 95, 595)
    c.box(1500, 400, 200, 80, "M2 PUSHER PA-14 24 V", ["150 stroke, internal limits", "red + = extend"])
    c.w(1365, 595, 1365, 440, INK, no="44", side=-1); c.w(1365, 440, 1500, 440); c.w(1565, 595, 1565, 500); c.w(1565, 500, 1720, 500); c.w(1720, 500, 1720, 460); c.w(1700, 460, 1720, 460)
    c.t(1760, 455, "45", 11, "start")
    c.t(1100, 300, "Pusher: K2 on = M2 red at +24, black at 0V (out); K3 on = reversed (in); both off = both leads at 0V (motor braked).", 12)
    c.t(1100, 318, "S0 NC-2 removes +24 S from both relays: the pusher stops dead in E-stop (category 0) whatever the PLC does.", 12)
    c.t(170, 1185, "PE: cord green → TB1 PE → PE stud → G1 earth, M1 frame (W1), box door strap, conveyor frame via the gearmotor and leg; < 0.1 Ω stud to frame (ITP).", 12, "start", GRN)
    # sequence
    c.t(120, 1225, "HOW THE CIRCUIT AND PROGRAM WORK", 15, bold=True)
    for i, l in enumerate([
        "START runs the belt (Y1 → K1) only if: S0 healthy (X8), STOP closed (X2), lid shut (X7), head healthy (X4), no latch. Green on while running.",
        f"Detect (X3 opens): A1 stamps the time; the pack reaches B1 {REJ['x']:.0f} mm on ({C['t_track']:.1f} s at {C['v']:.0f} mm/s). The first B1 edge inside the window ±0.5 s is the suspect pack.",
        f"A1 stops the belt (Y1 off), waits 0.3 s, extends the pusher (Y2) for {REJ['stroke'] / REJ['speed']:.1f} s + 0.5 s, retracts (Y3) for the same, then restarts if B2 saw the pack enter the bin.",
        "No B2 pulse within 2 s of the push, two detects closer than one pack pitch, or a B1 miss in the window: red + buzzer latch, belt stays stopped; only the QA key S3 clears it.",
        "Head fault (X4 opens), lid open (X7), STOP or E-stop: belt stops at once. E-stop also breaks M1 (S0 NC-1) and the pusher supply (S0 NC-2) in hardware.",
        "Amber flashes every 4 h of run time: test-piece check due (Fe / NFe / SS through the centre). START acknowledges it after the QA check is logged (ITP T12).",
    ]):
        c.t(120, 1255 + 21 * i, l, 12)
    # tables
    S.table(2050, 140, [("TAG", 70), ("DESCRIPTION", 520), ("PART", 270), ("WHERE", 120)], COMPONENTS, "COMPONENTS", fs=10, rh=17)
    S.table(2050, 560, [("I/O", 60), ("SIGNAL", 260), ("LOGIC", 300)], IO, "I/O MAP (A1 + A2)", fs=10, rh=17)
    S.table(120, 1400, [("WIRE", 60), ("FROM", 150), ("TO", 330), ("TYPE", 160), ("NOTE", 250)], WIRES, "WIRE LIST", fs=10, rh=17)
    S.table(1120, 1400, [("CABLE", 60), ("FROM", 130), ("TO", 130), ("SPEC", 250), ("GLAND / ROUTE", 280)], CABLES, "CABLES", fs=10, rh=17)
    # enclosure views (1:2.5)
    s = SC(2.5)
    vl = S.view(2830, 1330, s, "LID (1:2.5), FROM -Y", (2700, 880))
    vl.rect(-ENC_W / 2, 0, ENC_W, ENC_H, "vis", "#eceff1")
    for tag, (x, z, r, col, nm) in LID_OPS.items():
        vl.circle(x, z, r, "vis", col); vl.circle(x, z, 11.25, "hid"); vl.text(x, z - r - 10, f"{tag} {nm}", 9)
    vl.dim((-ENC_W / 2, 0), (ENC_W / 2, 0), -35, None, "h"); vl.dim((ENC_W / 2, 0), (ENC_W / 2, ENC_H), -30, None, "v")
    vl.dim((-50, 115), (50, 115), 0, None, "h"); vl.dim((-ENC_W / 2, 0), (-ENC_W / 2, 55), 30, None, "v"); vl.dim((-ENC_W / 2, 55), (-ENC_W / 2, 115), 30, None, "v")
    vl.dim((-ENC_W / 2, 115), (-ENC_W / 2, 190), 30, None, "v")
    vl.note(-ENC_W / 2, -60, ["4 x Ø22.5 [.886] through the lid; legend plates under each", "glands G1-G5 M20 in the bottom face"], 10)
    vb = S.view(3200, 1330, s, "PANEL (1:2.5)", (3110, 880))
    vb.rect(-ENC_W / 2 + 10, 0, ENC_W - 20, ENC_H - 20, "vis", "#f4f6f8")
    for zr, items in ((185, [("A1", 25, "#dfe7f1"), ("A2", 25, "#dfe7f1"), ("K1", 45, "#cfd8dc"), ("K2", 16, "#cfd8dc"), ("K3", 16, "#cfd8dc")]),
                      (120, [("F1", 9, "#cfd8dc"), ("F2", 9, "#cfd8dc"), ("1", 6, "#cfd8dc"), ("2", 6, "#cfd8dc"), ("N", 6, "#cfd8dc"), ("PE", 6, "#c5e1a5")] +
                       [("+", 6, "#ef9a9a")] * 4 + [("0", 6, "#90caf9")] * 4)):
        vb.line(-ENC_W / 2 + 15, zr, ENC_W / 2 - 15, zr, "cen")
        x = -ENC_W / 2 + 18
        for t, w, col in items:
            vb.rect(x, zr - 32, w, 64 if zr == 185 else 40, "vis", col); vb.text(x + w / 2, zr - 44 if zr == 185 else zr - 30, t, 7); x += w + 3
    vb.rect(-49, 10, 99, 82, "vis", "#dfe7f1"); vb.text(0, 50, "G1 LRS-75-24", 8); vb.text(0, 38, "99 x 97 x 30, 4 x M3", 7)
    vb.note(-ENC_W / 2, -40, ["2 x DIN 35 rails; wire duct 25 x 40 between", "rails; PE stud on the floor"], 10)
    S.notes(2050, 1450, 860, [
        f"Load ≈ {ELE['A']:.1f} A at 120 V (M1 2 A run, ≈ 6 A start for 0.3 s; G1 0.8 A). F1 6.3 A time-delay rides the start current and protects the 14 AWG cord.",
        f"24 V budget: A1+A2 0.15 A, K1 0.1 A, K2/K3 0.04 A, eyes 0.05 A, stack light 0.1 A, M2 ≤ 2 A while moving → < {ELE['I_dc']:.1f} A G1.",
        "E-stop is hardware (S0 NC-1 in the motor line, NC-2 in the pusher supply) and also read by A1 (X8) so the restart needs START.",
        "Head relays are configured fail-safe: a dead head, a cut W5 or a detect all read as 0 and stop the line. Never jumper X3 / X4.",
        "Keep W5 (head) and W6 / W7 away from W1 (motor) and at least 500 from the head aperture; no cable loops round the head.",
        "Program P1-406-FW-01 (CLICK) is kept with the plant software; timers come from design.py (belt speed, reject position, stroke).",
    ], "NOTES", fs=11)
    S.save(DWG / "P1-406-E01_electrical.svg")


if __name__ == "__main__":
    e01()
