"""P1-401-100 cabinet weldment, -101 sheet-metal flat patterns, -200 column weldment, -400 hopper, -500 agitator, -700 container stage."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
from mechsheet import dxf_profile

SS = "#f4f6f8"
BLU = "#dfe7f1"
WELD_TXT = "GTAW, ER308LSi (304), argon"
WELD_316 = "GTAW, ER316LSi, argon, back purge"
X0, X1 = -CAB["w"] / 2, CAB["w"] / 2
Y0, Y1 = CAB["y0"], CAB["y0"] + CAB["d"]
TY0, TY1 = Y0 - (TOP["d"] - CAB["d"]) / 2, Y1 + (TOP["d"] - CAB["d"]) / 2
T = CAB["t"]
R_O = HOP["r"] + T14
R_RIM = R_O + RIM["w"]
# bend deduction, 1.5 mm 304, inside R 1.5, K 0.44 (confirm with the brake shop)
BA = math.pi / 2 * (1.5 + 0.44 * T)
BD = 2 * (1.5 + T) - BA


def P(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def circ(r, n=144, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def arc_pts(r, a0, a1, n=60, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def rect_pts(w, h, cx=0.0, cy=0.0):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def rr(v, x0, y0, x1, y1, k="vis", fill="none"):
    v.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0), k, fill)


COL_PTS = [(sx * CBASE["pcd"] / 2, COL["y"] + sy * CBASE["pcd"] / 2) for sx in (-1, 1) for sy in (-1, 1)]
ROD_PTS = [(0.0, -STAGE["rod_y"]), (0.0, STAGE["rod_y"])]
BUSH_HOLES = [(x + dx, y + dy) for x, y in ROD_PTS for dx in (-22, 22) for dy in (-22, 22)]
FOOT_PTS = [(sx * FEET["x"], FEET["yc"] + sy * FEET["y"]) for sx in (-1, 1) for sy in (-1, 1)]
POD = dict(x0=200.0, x1=320.0, y0=-200.0, y1=-80.0, h0=60.0, h1=130.0)
POD["slope"] = math.hypot(POD["y1"] - POD["y0"], POD["h1"] - POD["h0"])
POD["ang"] = math.degrees(math.atan2(POD["h1"] - POD["h0"], POD["y1"] - POD["y0"]))
SB_PTS = [(-85.0, STAGE["d"] / 2 - 15), (-70.0, STAGE["d"] / 2 - 15)]


# ================================================================== 100 cabinet weldment
def cabinet():
    S = sheet("P1-401-100", "CABINET WELDMENT (BASE OF THE FILLER, CONTROLS INSIDE)", scale="1:5 · 1:4 · 1:1", material=SS304 + ", 1.5 mm [16 ga] / 3 mm / 10 mm",
              finish=FIN_NPC, mass=kg(*[f"P1-401-10{i}" for i in range(1, 8)]))
    s5 = SC(5)
    # ---- front view (x, z)
    v = S.view(780, 1300, s5, "FRONT VIEW (1:5)", (440, 470))
    rr(v, X0, Z_FOOT, X1, ZC, "vis", SS)
    rr(v, -DOOR["w"] / 2, DOOR["z0"], DOOR["w"] / 2, DOOR["z0"] + DOOR["h"], "vis", "#fff")
    rr(v, -TOP["w"] / 2, ZC, TOP["w"] / 2, Z_TOP, "vis", SS)
    v.poly([(POD["x0"], Z_TOP), (POD["x1"], Z_TOP), (POD["x1"], Z_TOP + POD["h0"]), (POD["x0"], Z_TOP + POD["h0"])], "vis", True, SS)
    v.line(POD["x0"], Z_TOP + POD["h1"], POD["x1"], Z_TOP + POD["h1"], "hid")
    for x in (-35, 0, 35):
        v.circle((POD["x0"] + POD["x1"]) / 2 + x, Z_TOP + 30, 11.25)
    v.circle(DOOR["w"] / 2 - 40, DOOR["z0"] + DOOR["h"] / 2, 11); v.text(DOOR["w"] / 2 - 40, DOOR["z0"] + DOOR["h"] / 2 - 35, "latch", 11)
    for zh in (150.0, 650.0):
        rr(v, X0 + 2, zh - 30, X0 + 14, zh + 30, "vis", "#cfd8dc")
    for x, y in FOOT_PTS[:2] + FOOT_PTS[2:]:
        rr(v, x - FEET["pad"] / 2, 0, x + FEET["pad"] / 2, 12, "vis", "#cfd8dc"); rr(v, x - 6, 12, x + 6, Z_FOOT, "vis", "#eceff1")
    for x, w in ((0.0, 40.0), (STAGE["bar_x"], 16.0)):
        pass
    v.centre(0, Z_FOOT - 20, 0, Z_TOP + 60)
    v.dim((X0, Z_FOOT), (X1, Z_FOOT), -60, f"{mmi(CAB['w'])} SHELL", "h")
    v.dim((-TOP["w"] / 2, Z_TOP), (TOP["w"] / 2, Z_TOP), 170, f"{mmi(TOP['w'])} TOP", "h")
    v.dim((-DOOR["w"] / 2, DOOR["z0"] + DOOR["h"]), (DOOR["w"] / 2, DOOR["z0"] + DOOR["h"]), 40, f"{mmi(DOOR['w'])} DOOR", "h")
    v.dim((X0, 0), (X0, Z_TOP), 120, f"{mmi(Z_TOP)} TOP SURFACE", "v")
    v.dim((X0, Z_FOOT), (X0, ZC), 60, f"{mmi(CAB['h'])} SHELL", "v")
    v.dim((X1, 0), (X1, Z_FOOT), -50, f"{mmi(FEET['h'])} ±25 [1] FEET", "v")
    v.dim((X1, DOOR["z0"]), (X1, DOOR["z0"] + DOOR["h"]), -140, f"{mmi(DOOR['h'])}", "v")
    v.leader((POD["x0"] + 10, Z_TOP + 40), (-60, Z_TOP + 115), ["HMI POD 106: reset, green, red Ø22.5 on the front,", "E-stop on the right side, HMI on the 30° face"], anchor="end")
    v.leader((X0 + 8, 650), (-380, 820), ["2 LIFT-OFF HINGES P1-444 on the", "left return, 2 x M5 each"], anchor="end")
    v.leader((FOOT_PTS[0][0], 6), (-380, -60), ["4 LEVELLING FEET P1-443 M12 into", "weld nuts H14 under base 103"], anchor="end")
    # ---- side section on x = 0 (y, z): front at the left
    vs = S.view(1640, 1300, s5, "SECTION A-A ON X = 0 (1:5), OPERATOR AT THE LEFT", (1300, 470))
    vs.hatch([(TY0, ZC), (TY1, ZC), (TY1, Z_TOP), (TY0, Z_TOP)], "hA")
    vs.hatch([(Y0 + T, Z_FOOT), (Y1 - T, Z_FOOT), (Y1 - T, Z_FOOT + 3), (Y0 + T, Z_FOOT + 3)], "hA")
    vs.hatch([(Y1 - T, Z_FOOT), (Y1, Z_FOOT), (Y1, ZC), (Y1 - T, ZC)], "hA")
    vs.hatch([(Y0 - 3.5, DOOR["z0"]), (Y0 - 2, DOOR["z0"]), (Y0 - 2, DOOR["z0"] + DOOR["h"]), (Y0 - 3.5, DOOR["z0"] + DOOR["h"])], "hA")
    vs.poly([(Y0 - 2, DOOR["z0"] + T), (Y0 + 13, DOOR["z0"] + T)], "vis", False); vs.poly([(Y0 - 2, DOOR["z0"] + DOOR["h"] - T), (Y0 + 13, DOOR["z0"] + DOOR["h"] - T)], "vis", False)
    vs.hatch([(COL["y"] - 90, ZC - CBASE["back_t"]), (COL["y"] - 30, ZC - CBASE["back_t"]), (COL["y"] - 30, ZC), (COL["y"] - 90, ZC)], "hB")
    vs.hatch([(COL["y"] + 30, ZC - CBASE["back_t"]), (COL["y"] + 90, ZC - CBASE["back_t"]), (COL["y"] + 90, ZC), (COL["y"] + 30, ZC)], "hB")
    rr(vs, Y1 - T - 27, Z_FOOT + 40, Y1 - T - 25, ZC - 40, "vis", BLU)
    rr(vs, Y1 - T - 25, 150, Y1 - T, 160, "hid"); rr(vs, Y1 - T - 25, 650, Y1 - T, 660, "hid")
    for y in ROD_PTS:
        rr(vs, y[1] - 30, ZC - STAGE["bush_L"], y[1] + 30, ZC, "phan")
    rr(vs, COL["y"] - CBASE["a"] / 2, Z_TOP, COL["y"] + CBASE["a"] / 2, Z_TOP + CBASE["t"], "phan")
    vs.circle(Y1 + 1, 110, 12.75, "hid")
    vs.dim((Y0, Z_FOOT), (Y1, Z_FOOT), -60, f"{mmi(CAB['d'])} SHELL", "h")
    vs.dim((TY0, Z_TOP), (TY1, Z_TOP), 120, f"{mmi(TOP['d'])} TOP", "h")
    vs.dim((0, Z_TOP), (COL["y"], Z_TOP), 60, f"{mmi(COL['y'])} AUGER AXIS TO COLUMN AXIS", "h")
    vs.dim((Y1, ZC - CBASE["back_t"]), (Y1, ZC), -40, None, "v")
    vs.centre(0, Z_FOOT, 0, Z_TOP + 60)
    vs.leader((COL["y"] - 60, ZC - 5), (COL["y"] - 200, ZC - 140), ["BACKING PLATE 107 10 mm, fillet 3 x 30 @ 80", "under the top; column bolts H1"], anchor="end")
    vs.leader((Y1 - T - 26, 400), (Y1 - 230, 330), ["BACK PANEL 105 on 4 weld studs", "M6 + 25 spacers (H14)"], anchor="end")
    vs.leader((Y0 - 3, 300), (Y0 - 60, 220), ["DOOR 104 + FDA gasket"], anchor="end")
    vs.leader((ROD_PTS[0][1] - 30, ZC - 40), (-150, ZC - 330), ["UHMW BUSHINGS 703 (phantom)"], anchor="end")
    vs.weld((Y1, ZC), (Y1 + 60, ZC + 70), "fillet", "1.5", allround=True, tail="W1 seal, ground")
    vs.weld((Y1 - T, Z_FOOT + 3), (Y1 - 120, Z_FOOT + 90), "fillet", "2", tail="W2 25 @ 100")
    # ---- plan of the top (x, y)
    s4 = SC(4)
    vp = S.view(2560, 860, s4, "TOP 102: PLAN, HOLES FROM THE AUGER AXIS (1:4)", (2200, 400))
    rr(vp, -TOP["w"] / 2, TY0, TOP["w"] / 2, TY1, "vis", SS)
    rr(vp, X0, Y0, X1, Y1, "hid")
    for x, y in ROD_PTS:
        vp.circle(x, y, 12); vp.cmark(x, y, 18)
    for x, y in BUSH_HOLES:
        vp.circle(x, y, 3.3); vp.circle(x, y, 6.5, "thin")
    rr(vp, STAGE["bar_x"] - 8, -24, STAGE["bar_x"] + 8, 24, "vis", "#fff")
    for x, y in COL_PTS:
        vp.circle(x, y, 6.5); vp.cmark(x, y, 10)
    vp.circle(0, COL["y"], 30); vp.cmark(0, COL["y"], 40)
    for y in (-12.0, 12.0):
        vp.circle(PLG["x"], y, 3.3)
    vp.circle(260, -140, 12.5)
    rr(vp, POD["x0"], POD["y0"], POD["x1"], POD["y1"], "phan")
    rr(vp, COL["y"] * 0 - 90, COL["y"] - 90, 90, COL["y"] + 90, "hid")
    vp.dim((-TOP["w"] / 2, TY0), (TOP["w"] / 2, TY0), -50, f"{mmi(TOP['w'])} ±1", "h")
    vp.dim((-TOP["w"] / 2, TY0), (-TOP["w"] / 2, TY1), 60, f"{mmi(TOP['d'])} ±1", "v")
    vp.dim((-TOP["w"] / 2, TY0), (-TOP["w"] / 2, 0), 120, f"{mmi(-TY0)}", "v")
    vp.dim((0, ROD_PTS[0][1]), (0, ROD_PTS[1][1]), 140, f"{mmi(2 * STAGE['rod_y'])} ±0.1", "v")
    vp.dim((-CBASE["pcd"] / 2, COL["y"] + CBASE["pcd"] / 2), (CBASE["pcd"] / 2, COL["y"] + CBASE["pcd"] / 2), 60, f"{mmi(CBASE['pcd'])} ±0.2", "h")
    vp.leader((12, -85), (350, -250), ["2 x Ø24 [.945] THRU (rods Ø20, 2 clearance)"])
    vp.leader(BUSH_HOLES[2], (350, -20), ["8 x Ø6.6 csk 90° to Ø13 from the top", "(bushings 703, H10)"])
    vp.leader((STAGE["bar_x"], 24), (190, 110), ["SLOT 16 x 48 THRU (pin bar 704)"])
    vp.leader(COL_PTS[1], (-400, 380), ["4 x Ø13 [.512] THRU on 140 sq (H1)", "Ø60 THRU cable pass on the column axis"], anchor="end")
    vp.leader((PLG["x"], 12), (240, 60), ["2 x Ø6.6 (plunger block 705, H13)"])
    vp.leader((260, -152), (200, -320), ["Ø25 THRU pod cable hole; POD 106 seal-welded on"], anchor="end")
    # ---- hole table
    rows = [("A1-A2", "Ø24.0 THRU", "0", "∓85.0", "stage rods 702 pass"),
            ("B1-B8", "Ø6.6 csk 90° Ø13", "±22.0", "∓85 ±22", "bushings 703, M6 x 16 csk (H10)"),
            ("C1", "slot 16 x 48 THRU", f"{STAGE['bar_x']:.1f}", "0", "pin bar 704 (R8 ends)"),
            ("D1-D4", "Ø13.0 THRU", "±70.0", "230.0 / 370.0", "column base 202, M12 (H1)"),
            ("D5", "Ø60.0 THRU", "0", f"{COL['y']:.1f}", "cable pass to the column"),
            ("E1-E2", "Ø6.6 THRU", f"{PLG['x']:.1f}", "±12.0", "plunger block 705 (H13)"),
            ("F1", "Ø25.0 THRU", "260.0", "-140.0", "HMI pod cables")]
    S.table(2000, 1200, [("HOLE", 80), ("SIZE", 200), ("X", 90), ("Y", 130), ("FOR", 320)], rows, "TOP 102 HOLE TABLE (datum: auger axis, ±0.2 unless noted)", 13, 22)
    # ---- parts + welds
    S.table(130, 1460, [("PART", 120), ("DESCRIPTION", 330), ("QTY", 40), ("STOCK / BLANK", 420), ("DRG / DXF", 250)], [
        ("P1-401-101", "Shell wrap (sides, back, front returns)", 1, f"304 1.5 mm, flat {1850 - 4 * BD:.1f} x {CAB['h']:.0f}, 4 bends", "-101, dxf"),
        ("P1-401-102", "Top plate", 1, f"304 3 mm {TOP['w']:.0f} x {TOP['d']:.0f}, #4 top", "this sheet, dxf"),
        ("P1-401-103", "Base plate + 4 weld nuts M12", 1, f"304 3 mm {CAB['w'] - 2 * T:.0f} x {CAB['d'] - T:.1f}", "-101, dxf"),
        ("P1-401-104", "Door (2 bends) + gasket", 1, f"304 1.5 mm, flat {DOOR['w']:.0f} x {DOOR['h'] + 30 - 2 * BD:.1f}", "-101, dxf"),
        ("P1-401-105", "Back (mounting) panel", 1, "304 2 mm 540 x 617, DIN rails + duct", "-101, dxf"),
        ("P1-401-106", "HMI pod (wrap + 2 sides)", 1, "304 1.5 mm", "-101, dxf"),
        ("P1-401-107", "Column backing plate", 1, "304 10 mm 180 x 180", "-101, dxf"),
    ], "PARTS", 13, 22)
    S.table(130, 1680, [("WELD", 60), ("JOINT", 420), ("PROCESS", 300), ("NOTES", 450)], [
        ("W1", "Top 102 to shell, outside", WELD_TXT, "continuous seal fillet 1.5, ground smooth (washdown)"),
        ("W2", "Base 103 to shell, inside", WELD_TXT, "fillet 2, 25 long @ 100, both sides"),
        ("W3", "Backing plate 107 to top underside", WELD_TXT, "fillet 3, 30 @ 80 all round"),
        ("W4", "Pod 106 to top, and its seams", WELD_TXT, "continuous outside, ground; inside tack"),
        ("W5", "Weld nuts H14 to base; studs M6 to back", "GTAW / stud welder", "nuts fillet 2 all round"),
    ], "WELD SCHEDULE", 13, 22)
    S.notes(1600, 1460, 960, [
        "Shell, door, pod: laser cut from -101 DXF, then brake. Bend the wrap on a 600 x 600 square gauge: diagonals equal within 2.",
        "Lay the top face down on a flat table, fit the shell, tack 8 places, then weld W1 in 100 mm runs skipping round. Top flat 1.0 after welding.",
        "Weld the backing plate 107 before drilling D1-D5 through both: match drill the 4 x Ø13 and the Ø60 from the top.",
        "Door gasket FDA silicone on the return flanges (P1-444). Earth stud M6 on the back wall at the gland plate, bonded to the door.",
        "Cable glands (P1-446) in the back wall: M25 supply, 2 x M20 (foot switch, spare), see -101.",
    ], "FABRICATION", 13)
    dxf_profile(str(DXF / "P1-401-102_top"), rect_pts(TOP["w"], TOP["d"], 0, (TY0 + TY1) / 2),
                holes=[(x, y, 12.0) for x, y in ROD_PTS] + [(x, y, 3.3) for x, y in BUSH_HOLES] + [(x, y, 6.5) for x, y in COL_PTS] + [(0, COL["y"], 30.0)] +
                [(PLG["x"], -12.0, 3.3), (PLG["x"], 12.0, 3.3), (260.0, -140.0, 12.5)],
                lines=[((STAGE["bar_x"] - 8, -16), (STAGE["bar_x"] - 8, 16)), ((STAGE["bar_x"] + 8, -16), (STAGE["bar_x"] + 8, 16))],
                arcs=[(STAGE["bar_x"], 16, 8, 0, 180), (STAGE["bar_x"], -16, 8, 180, 360)], text="P1-401-102 TOP 3mm 304 (origin = auger axis)")
    S.save(DWG / "P1-401-100_cabinet_weldment.svg")


# ================================================================== 101 flat patterns
def flats():
    S = sheet("P1-401-101", "CABINET SHEET METAL: FLAT PATTERNS AND BEND DATA", scale="1:6 · 1:3 · 1:2 · 1:1", material=SS304, finish=FIN_NPC, mass="see -100")
    # ---- shell wrap, seen from the outside; right return at the left
    L = 1850 - 4 * BD
    a = 25 - BD / 2; b = a + 600 - BD; c = b + 600 - BD; d = c + 600 - BD
    H = CAB["h"]
    s8 = SC(6)
    v = S.view(170, 800, s8, f"101 SHELL WRAP: FLAT, OUTSIDE FACE (1:6), {mmi(L, 1)} x {mmi(H)}", (170, 240))
    rr(v, 0, 0, L, H, "vis", SS)
    for u in (a, b, c, d):
        v.line(u, -10, u, H + 10, "cen")
    v.text((a + b) / 2, H + 25, "RIGHT SIDE", 12); v.text((b + c) / 2, H + 25, "BACK", 12); v.text((c + d) / 2, H + 25, "LEFT SIDE", 12)
    v.text(a / 2, H + 25, "R RET", 10); v.text((d + L) / 2, H + 25, "L RET", 10)
    glands = [(-200.0, 12.75), (-140.0, 10.25), (-90.0, 10.25)]
    gl = [(b + (300 - x) - BD / 2, 110 - Z_FOOT, r) for x, r in glands]
    for u, z, r in gl:
        v.circle(u, z, r)
    hinge = [(d + (L - d) / 2, zh - Z_FOOT + dz, 2.75) for zh in (150.0, 650.0) for dz in (-20, 20)]
    for u, z, r in hinge:
        v.circle(u, z, r)
    disc = [(a + 200 - BD / 2, 600 - Z_FOOT, 11.25), (a + 200 - BD / 2 - 18, 600 - Z_FOOT, 2.75), (a + 200 - BD / 2 + 18, 600 - Z_FOOT, 2.75)]
    for u, z, r in disc:
        v.circle(u, z, r)
    v.dim((0, 0), (L, 0), -50, f"{mmi(L, 1)} FLAT", "h")
    v.dim((0, H), (a, H), 60, None, "h"); v.dim((a, H), (b, H), 60, None, "h"); v.dim((b, H), (c, H), 60, None, "h"); v.dim((c, H), (d, H), 60, None, "h")
    v.dim((L, 0), (L, H), -40, f"{mmi(H)}", "v")
    v.leader((gl[0][0], gl[0][1] + 12), (gl[0][0] + 80, 260), ["M25 Ø25.5, 2 x M20 Ø20.5 glands at 50 [1.97] up", "x = -200 / -140 / -90 from the auger axis"])
    v.leader((disc[0][0], disc[0][1] + 11), (disc[0][0] + 40, 660), ["DISCONNECT HANDLE P1-439: Ø22.5 + 2 x Ø5.5 on 36,", "at y 0, z 600 (ABB template, confirm)"])
    v.leader((hinge[3][0], hinge[3][1]), (L - 250, 480), ["HINGES: 4 x Ø5.5 on the L return", "centre 12.5, z 150 / 650 ± 20"], anchor="end")
    S.table(170, 940, [("BEND", 70), ("FROM LEFT EDGE", 170), ("DIR", 80), ("ANGLE", 70)], [
        ("1", f"{a:.2f}", "up 90°", "90°"), ("2", f"{b:.2f}", "up 90°", "90°"), ("3", f"{c:.2f}", "up 90°", "90°"), ("4", f"{d:.2f}", "up 90°", "90°")],
        f"BEND LINES (inside R1.5, K 0.44, BD {BD:.2f})", 13, 22)
    dxf_profile(str(DXF / "P1-401-101_shell_wrap"), rect_pts(L, H, L / 2, H / 2), holes=gl + hinge + disc,
                bends=[((u, 0), (u, H)) for u in (a, b, c, d)], text="P1-401-101 SHELL WRAP 1.5mm 304, bends up, outside face shown")
    # ---- door
    s4 = SC(6)
    DH = DOOR["h"] + 30 - 2 * BD
    vd = S.view(400, 1720, s4, f"104 DOOR: FLAT (1:6), {mmi(DOOR['w'])} x {mmi(DH, 1)}", (170, 1180))
    rr(vd, -DOOR["w"] / 2, 0, DOOR["w"] / 2, DH, "vis", SS)
    for u in (15 - BD / 2, DH - 15 + BD / 2):
        vd.line(-DOOR["w"] / 2 - 10, u, DOOR["w"] / 2 + 10, u, "cen")
    dh = [(DOOR["w"] / 2 - 40, DH / 2, 11.0)] + [(-DOOR["w"] / 2 + 20, DH / 2 + zz, 2.75) for zz in (-250 - 20, -250 + 20, 250 - 20, 250 + 20)]
    for x, y, r in dh:
        vd.circle(x, y, r)
    vd.dim((-DOOR["w"] / 2, 0), (DOOR["w"] / 2, 0), -40, None, "h")
    vd.dim((DOOR["w"] / 2, 0), (DOOR["w"] / 2, DH), -40, None, "v")
    vd.leader((DOOR["w"] / 2 - 40, DH / 2 + 11), (DOOR["w"] / 2 + 60, DH / 2 + 120), ["Ø22 latch P1-444 (E3)"])
    vd.leader((-DOOR["w"] / 2 + 20, DH / 2 + 270), (-DOOR["w"] / 2 - 40, DH / 2 + 160), ["4 x Ø5.5 hinge leaves"], anchor="end")
    vd.note(-DOOR["w"] / 2 + 10, -130, ["2 bends 90° in (15 returns, top and bottom)"], 12)
    dxf_profile(str(DXF / "P1-401-104_door"), rect_pts(DOOR["w"], DH, 0, DH / 2), holes=dh,
                bends=[((-DOOR["w"] / 2, u), (DOOR["w"] / 2, u)) for u in (15 - BD / 2, DH - 15 + BD / 2)], text="P1-401-104 DOOR 1.5mm 304")
    # ---- base plate
    BW, BDp = CAB["w"] - 2 * T, CAB["d"] - T
    vb = S.view(1080, 1520, s4, f"103 BASE (1:6), 3 mm, {mmi(BW)} x {mmi(BDp, 1)}", (850, 1180))
    rr(vb, -BW / 2, -BDp / 2, BW / 2, BDp / 2, "vis", SS)
    bh = [(x, y - FEET["yc"] - T / 2, 6.5) for x, y in FOOT_PTS]
    for x, y, r in bh:
        vb.circle(x, y, r); vb.circle(x, y, 10, "hid")
    vb.dim((-BW / 2, -BDp / 2), (BW / 2, -BDp / 2), -40, None, "h")
    vb.dim((BW / 2, -BDp / 2), (BW / 2, BDp / 2), -40, None, "v")
    vb.dim((bh[1][0], bh[1][1]), (bh[3][0], bh[1][1]), 40, f"{mmi(2 * FEET['x'])}", "h")
    vb.dim((bh[2][0], bh[2][1]), (bh[2][0], bh[3][1]), -110, f"{mmi(2 * FEET['y'])}", "v")
    vb.leader((bh[0][0] + 5, bh[0][1] + 5), (bh[0][0] + 80, bh[0][1] + 80), ["4 x Ø13 + M12 weld nut H14 under"])
    dxf_profile(str(DXF / "P1-401-103_base"), rect_pts(BW, BDp), holes=[(x, y, 6.5) for x, y, _ in bh], text="P1-401-103 BASE 3mm 304 (front edge at -y)")
    # ---- back panel 105, backing plate 107
    s4b = SC(6)
    vk = S.view(1900, 800, s4b, "105 BACK PANEL (1:6), 2 mm", (1680, 240))
    rr(vk, -270, 0, 270, 617, "vis", SS)
    kh = [(sx * 250, z, 3.5) for sx in (-1, 1) for z in (20.0, 597.0)]
    for x, y, r in kh:
        vk.circle(x, y, r)
    for z in (480.0, 330.0, 180.0):
        rr(vk, -250, z - 17.5, 250, z + 17.5, "phan")
    vk.text(0, 485, "DIN 35 rails at z 180 / 330 / 480 (on the panel)", 11)
    vk.dim((-270, 0), (270, 0), -40, None, "h"); vk.dim((270, 0), (270, 617), -40, None, "v")
    vk.dim((-250, 597), (250, 597), 50, f"{mmi(500)}", "h"); vk.dim((-270, 20), (-270, 597), 50, f"{mmi(577)}", "v")
    vk.leader((250, 597), (310, 680), ["4 x Ø7 (weld studs M6)"])
    dxf_profile(str(DXF / "P1-401-105_back_panel"), rect_pts(540, 617, 0, 308.5), holes=kh, text="P1-401-105 BACK PANEL 2mm 304")
    s2 = SC(2)
    vbk = S.view(2750, 600, s2, None)
    S.text(2500, 300, "107 BACKING PLATE (1:2), 10 mm", 20, bold=True)
    rr(vbk, -90, -90, 90, 90, "vis", SS)
    bkh = [(sx * 70, sy * 70, 6.5) for sx in (-1, 1) for sy in (-1, 1)] + [(0, 0, 30.0)]
    for x, y, r in bkh:
        vbk.circle(x, y, r)
    vbk.dim((-90, -90), (90, -90), -30, None, "h"); vbk.dim((90, -90), (90, 90), -30, None, "v")
    vbk.dim((-70, 70), (70, 70), 40, f"{mmi(140)}", "h")
    vbk.leader((70, 76.5), (120, 120), ["4 x Ø13 (match drill with the top)", "Ø60 cable pass"])
    dxf_profile(str(DXF / "P1-401-107_backing"), rect_pts(180, 180), holes=bkh, text="P1-401-107 BACKING 10mm 304")
    # ---- HMI pod: wrap (front + 30° face + back) and 2 sides
    PW = POD["x1"] - POD["x0"]
    segs = [POD["h0"], POD["slope"], POD["h1"]]
    a1, a2 = segs[0] - BD / 2, segs[0] + segs[1] - BD
    PL = sum(segs) - 2 * BD
    vpw = S.view(1640, 1720, SC(3), f"106 POD WRAP: FLAT (1:3), {mmi(PW)} x {mmi(PL, 1)}", (1500, 1180))
    rr(vpw, 0, 0, PW, PL, "vis", SS)
    for u in (a1, a2):
        vpw.line(-10, u, PW + 10, u, "cen")
    ph = [(PW / 2 + x, 30.0, 11.25) for x in (-35, 0, 35)]
    for x, y, r in ph:
        vpw.circle(x, y, r)
    hmi = rect_pts(87.0, 69.0, PW / 2, (a1 + a2) / 2)
    vpw.poly(hmi)
    vpw.dim((0, 0), (PW, 0), -40, None, "h"); vpw.dim((PW, 0), (PW, PL), -40, None, "v")
    vpw.dim((PW, 0), (PW, a1), -110, None, "v"); vpw.dim((PW, a1), (PW, a2), -110, None, "v")
    vpw.leader((PW / 2 + 35, 41), (PW + 90, 20), ["3 x Ø22.5 reset, green, red"])
    vpw.leader((PW / 2 + 43.5, (a1 + a2) / 2), (PW + 90, PL - 20), ["HMI cut-out 87 x 69 [3.43 x 2.72]", "EA3-S3ML (confirm in its manual)"])
    vpw.note(0, PL + 20, [f"bend 1 up 90°-{POD['ang']:.1f}° = {90 - POD['ang']:.1f}°... see table"], 11) if False else None
    S.table(2000, 1830, [("BEND", 60), ("AT", 100), ("ANGLE", 90)], [("1", f"{a1:.2f}", f"{180 - 90 - POD['ang']:.1f}°" if False else f"{90 + POD['ang']:.1f}° incl."),
                                                               ("2", f"{a2:.2f}", f"{180 - POD['ang']:.1f}° incl.")], "POD BENDS", 12, 20)
    vps = S.view(2280, 1720, SC(3), "106 POD SIDE x 2 (1:3)", (2260, 1180))
    side = [(0, 0), (POD["y1"] - POD["y0"], 0), (POD["y1"] - POD["y0"], POD["h1"]), (0, POD["h0"])]
    vps.poly(side, "vis", True, SS)
    vps.circle(60, 35, 11.25)
    vps.dim((0, 0), (120, 0), -40, None, "h"); vps.dim((0, 0), (0, POD["h0"]), 40, None, "v"); vps.dim((120, 0), (120, POD["h1"]), -40, None, "v")
    vps.leader((60, 46), (150, 150), ["Ø22.5 E-STOP (right side only)", "GCX1131 40 mm mushroom"])
    dxf_profile(str(DXF / "P1-401-106_pod_wrap"), rect_pts(PW, PL, PW / 2, PL / 2), holes=ph, lines=list(zip(hmi, hmi[1:] + hmi[:1])),
                bends=[((0, u), (PW, u)) for u in (a1, a2)], text="P1-401-106 POD WRAP 1.5mm 304")
    dxf_profile(str(DXF / "P1-401-106_pod_side_R"), side, holes=[(60.0, 35.0, 11.25)], text="P1-401-106 POD SIDE RIGHT (E-stop)")
    dxf_profile(str(DXF / "P1-401-106_pod_side_L"), side, text="P1-401-106 POD SIDE LEFT")
    S.notes(2450, 1150, 900, [
        "Flat sizes are for 1.5 mm 304 with a 1.5 inside radius and K 0.44. Bend a test strip first and correct BD before cutting the wrap.",
        "All DXF files are full size in mm and inch, layers CUT (white), BEND (red, centre of bend), MARK (green, etch the part number).",
        "Deburr all cut edges. Grain (#4) runs vertically on the shell and door, front to back on the top.",
    ], "NOTES", 13)
    S.save(DWG / "P1-401-101_flat_patterns.svg")


# ================================================================== 200 column weldment
def horseshoe_outline():
    ro, ri, ho, a = HSH["ri"] + HSH["w"], HSH["ri"], HSH["open"] / 2, COL["a"] / 2
    yf = COL["y"] - a
    ao0 = math.degrees(math.atan2(-math.sqrt(ro ** 2 - ho ** 2), ho)); ai0 = math.degrees(math.atan2(-math.sqrt(ri ** 2 - ho ** 2), ho))
    an = math.degrees(math.atan2(math.sqrt(ro ** 2 - a ** 2), a))
    pts = [(ho, -math.sqrt(ri ** 2 - ho ** 2)), (ho, -math.sqrt(ro ** 2 - ho ** 2))]
    pts += arc_pts(ro, ao0, an, 60)[1:]
    pts += [(a, yf), (-a, yf)]
    pts += arc_pts(ro, 180 - an, 180 - ao0, 60)
    pts += [(-ho, -math.sqrt(ri ** 2 - ho ** 2))]
    pts += arc_pts(ri, 180 - ai0, ai0, 120)[1:-1]
    return pts


def column():
    S = sheet("P1-401-200", "COLUMN WELDMENT (TUBE, BASE, CAP, HORSESHOE)", scale="1:4 · 1:2", material=SS304 + "; tube ASTM A554 4 in sq x 11 ga",
              finish=FIN_NPC, mass=kg("P1-401-201", "P1-401-202", "P1-401-203", "P1-401-204"))
    s5 = SC(4)
    a, t = COL["a"], COL["t"]
    zb, zc = Z_TOP + CBASE["t"], Z_HP - CAP["t"]
    zh1 = Z_RIM - RIM["t"]; zh0 = zh1 - HSH["t"]
    # ---- side elevation (y, z): the horseshoe arm runs to the front (-y, left)
    v = S.view(700, 380 + Z_HP * s5, s5, "SIDE ELEVATION, SECTION ON X = 0 (1:4), OPERATOR AT THE LEFT", (250, 250))
    v.hatch([(COL["y"] - a / 2, zb), (COL["y"] - a / 2 + t, zb), (COL["y"] - a / 2 + t, zc), (COL["y"] - a / 2, zc)], "hA")
    v.hatch([(COL["y"] + a / 2 - t, zb), (COL["y"] + a / 2, zb), (COL["y"] + a / 2, zc), (COL["y"] + a / 2 - t, zc)], "hA")
    v.hatch([(COL["y"] - CBASE["a"] / 2, Z_TOP), (COL["y"] - 30, Z_TOP), (COL["y"] - 30, zb), (COL["y"] - CBASE["a"] / 2, zb)], "hA")
    v.hatch([(COL["y"] + 30, Z_TOP), (COL["y"] + CBASE["a"] / 2, Z_TOP), (COL["y"] + CBASE["a"] / 2, zb), (COL["y"] + 30, zb)], "hA")
    v.hatch([(COL["y"] - CAP["a"] / 2, zc), (COL["y"] - 25, zc), (COL["y"] - 25, Z_HP), (COL["y"] - CAP["a"] / 2, Z_HP)], "hA")
    v.hatch([(COL["y"] + 25, zc), (COL["y"] + CAP["a"] / 2, zc), (COL["y"] + CAP["a"] / 2, Z_HP), (COL["y"] + 25, Z_HP)], "hA")
    v.hatch([(-HSH["ri"] - HSH["w"], zh0), (-HSH["ri"], zh0), (-HSH["ri"], zh1), (-HSH["ri"] - HSH["w"], zh1)], "hA")
    v.hatch([(HSH["ri"], zh0), (COL["y"] - a / 2, zh0), (COL["y"] - a / 2, zh1), (HSH["ri"], zh1)], "hA")
    v.rect(-HSH["ri"] - 30, zh1, 5, 12, "vis", SS) if False else None
    rr(v, -R_RIM, zh1, R_RIM, Z_RIM, "phan")
    rr(v, HPL["y0"], Z_HP, HPL["y1"], Z_HPT, "phan")
    v.text(0, Z_HPT + 25, "head plate 301 (phantom)", 11, color="#607d8b"); v.text(-120, Z_RIM + 25, "hopper rim (phantom)", 11, color="#607d8b")
    v.centre(COL["y"], Z_TOP - 30, COL["y"], Z_HP + 40); v.centre(0, zh0 - 60, 0, Z_RIM + 60)
    v.dim((COL["y"] + CBASE["a"] / 2, Z_TOP), (COL["y"] + CBASE["a"] / 2, Z_HP), -60, f"{mmi(Z_HP - Z_TOP)} ±1 OVERALL", "v")
    v.dim((COL["y"] + a / 2, zb), (COL["y"] + a / 2, zc), -150, f"{mmi(COL['L'])} TUBE CUT", "v")
    v.dim((-HSH["ri"] - HSH["w"], Z_TOP), (-HSH["ri"] - HSH["w"], zh1), 60, f"{mmi(zh1 - Z_TOP)} ±0.5 TO HORSESHOE TOP", "v")
    v.dim((COL["y"] - CBASE["a"] / 2, zb), (COL["y"] - CBASE["a"] / 2, Z_TOP), 40, None, "v")
    v.dim((0, zh0), (COL["y"], zh0), -60, f"{mmi(COL['y'])} ±0.5 AXIS TO COLUMN", "h")
    v.dim((-HSH["ri"], zh0), (HSH["ri"], zh0), -150, f"Ø{mmi(2 * HSH['ri'])} ±0.3", "h")
    v.datum((COL["y"] - 60, Z_TOP), "A", (0, -1))
    v.fcf(COL["y"] + 120, Z_HP + 40, ["∥", "0.5", "A"]); v.note(COL["y"] + 120, Z_HP + 10, ["CAP TOP ∥ A"], 12)
    v.fcf(-HSH["ri"] - 60, zh1 + 120, ["∥", "0.5", "A"]); v.note(-HSH["ri"] - 60, zh1 + 90, ["HORSESHOE TOP ∥ A"], 12)
    v.weld((COL["y"] - a / 2, zb), (COL["y"] - 200, zb + 120), "fillet", "6", allround=True, tail="W1")
    v.weld((COL["y"] - a / 2, zc), (COL["y"] - 200, zc - 100), "fillet", "6", allround=True, tail="W2")
    v.weld((COL["y"] - a / 2, zh0), (COL["y"] - 150, zh0 - 120), "fillet", "6", other="fillet", tail="W3 3 sides of the notch")
    # ---- horseshoe plan
    s4 = SC(4)
    vh = S.view(2050, 640, s4, "204 HORSESHOE PLAN (1:4), 20 mm 304 PLATE", (1720, 240))
    hs = horseshoe_outline()
    vh.poly(hs, "vis", True, SS)
    rr(vh, -a / 2, COL["y"] - a / 2, a / 2, COL["y"] + a / 2, "phan")
    pins = [P(HSH["ri"] + 12, ang) for ang in HSH["pin_a"]]
    for x, y in pins:
        vh.circle(x, y, 4); vh.cmark(x, y, 8)
    vh.cmark(0, 0, HSH["ri"] + HSH["w"] + 15)
    vh.dia(0, 0, HSH["ri"], 135, (-330, 250), f"Ø{mmi(2 * HSH['ri'])} ±0.3")
    vh.dia(0, 0, HSH["ri"] + HSH["w"], 160, (-360, 150), f"Ø{mmi(2 * (HSH['ri'] + HSH['w']))}")
    vh.dim((-HSH["open"] / 2, -HSH["ri"] - HSH["w"]), (HSH["open"] / 2, -HSH["ri"] - HSH["w"]), -40, f"{mmi(HSH['open'])} OPENING (tooling passes)", "h")
    vh.dim((a / 2, COL["y"] - a / 2), (-a / 2, COL["y"] - a / 2), 0, None, "h") if False else None
    vh.dim((-a / 2, COL["y"] - a / 2), (a / 2, COL["y"] - a / 2), -20, f"{mmi(a)} +0.5 NOTCH", "h")
    vh.leader(pins[0], (330, 120), ["2 x Ø8 H7 at 30° / 150° on R244", "dowel ISO 8734 8 x 30, 12 proud"])
    vh.text(0, -HSH["ri"] - HSH["w"] - 70, "operator side (-y); 0° = +x", 12)
    dxf_profile(str(DXF / "P1-401-204_horseshoe"), hs, holes=[(x, y, 4.0) for x, y in pins], text="P1-401-204 HORSESHOE 20mm 304 (pin holes ream Ø8 H7)")
    # ---- base and cap plates 1:2
    s2 = SC(2)
    vb = S.view(1820 + 90 * s2, 1250, s2, "202 BASE PLATE (1:2), 12 mm", (1650, 1010))
    rr(vb, -90, -90, 90, 90, "vis", SS); rr(vb, -a / 2, -a / 2, a / 2, a / 2, "phan")
    bh = [(sx * 70, sy * 70, 6.5) for sx in (-1, 1) for sy in (-1, 1)] + [(0, 0, 30.0)]
    for x, y, r in bh:
        vb.circle(x, y, r)
    vb.dim((-90, -90), (90, -90), -30, f"{mmi(180)}", "h"); vb.dim((90, -90), (90, 90), -30, f"{mmi(180)}", "v")
    vb.dim((-70, 70), (70, 70), 40, f"{mmi(140)} ±0.2", "h")
    vb.leader((70, 76.5), (120, 125), ["4 x Ø13 THRU, Ø60 THRU"])
    vc = S.view(2560 + 80 * s2, 1250, s2, "203 CAP PLATE (1:2), 12 mm", (2440, 1010))
    rr(vc, -80, -80, 80, 80, "vis", SS); rr(vc, -a / 2, -a / 2, a / 2, a / 2, "phan")
    ch = [(sx * 60, sy * 60, 4.25) for sx in (-1, 1) for sy in (-1, 1)] + [(0, 0, 25.0)]
    for x, y, r in ch:
        vc.circle(x, y, r); vc.circle(x, y, 5.0, "thin") if r < 5 else None
    vc.dim((-80, -80), (80, -80), -30, f"{mmi(160)}", "h"); vc.dim((80, -80), (80, 80), -30, f"{mmi(160)}", "v")
    vc.dim((-60, 60), (60, 60), 40, f"{mmi(120)} ±0.1", "h")
    vc.leader((60, 64.3), (100, 115), ["4 x M10 THRU (drill Ø8.5)", "Ø50 THRU cable pass"])
    vc.note(-80, -120, ["drill + tap AFTER welding, from the head plate", "301 as a template (match)"], 12)
    dxf_profile(str(DXF / "P1-401-202_base_plate"), rect_pts(180, 180), holes=bh, text="P1-401-202 COLUMN BASE 12mm 304")
    dxf_profile(str(DXF / "P1-401-203_cap_plate"), rect_pts(160, 160), holes=[(0, 0, 25.0)], text="P1-401-203 CAP 12mm 304 (M10 tapped after welding)")
    S.table(130, 1500, [("PART", 120), ("DESCRIPTION", 300), ("QTY", 40), ("STOCK", 420)], [
        ("P1-401-201", "Column tube", 1, f"304 4 in sq x 11 ga (101.6 x 3.05) x {COL['L']:.0f}, square cut ±0.5"),
        ("P1-401-202", "Base plate", 1, "304 12 mm 180 x 180, laser"),
        ("P1-401-203", "Cap plate", 1, "304 12 mm 160 x 160, laser"),
        ("P1-401-204", "Horseshoe + 2 dowels", 1, "304 20 mm plate, laser (DXF), dowels 8 x 30"),
    ], "PARTS", 13, 22)
    S.table(130, 1660, [("WELD", 60), ("JOINT", 380), ("PROCESS", 280), ("NOTES", 450)], [
        ("W1", "Tube to base plate, all round", WELD_TXT, "fillet 6; plate ⟂ tube 0.3 before welding"),
        ("W2", "Tube to cap plate, all round", WELD_TXT, "fillet 6; cap ∥ base 0.5 (jig)"),
        ("W3", "Horseshoe to tube, 3 sides, top + bottom", WELD_TXT, "fillet 6, top ground flat (rim seat)"),
    ], "WELD SCHEDULE", 13, 22)
    S.notes(1300, 1500, 1250, [
        "Jig the base and cap on a column fixture: both plates square to the tube 0.3, cap ∥ base 0.5, cap holes clocked to the base holes ±0.3.",
        f"Horseshoe at {zh1 - Z_TOP:.0f} ±0.5 above the base underside, its axis {COL['y']:.0f} ±0.5 from the column axis, centred on x 0 ±0.3. Weld top and bottom alternately.",
        "After welding: stress-relieve not needed. Check the cap and horseshoe against datum A with the column bolted to a surface plate; shim faces if over.",
        "Calcs (P1-401-900): bending 6 MPa in the tube, tip deflection 0.27 mm; horseshoe arm 20.6 MPa and 0.32 mm with a full hopper (radial auger clearance 0.75).",
    ], "FABRICATION AND CHECKS", 13)
    S.save(DWG / "P1-401-200_column_weldment.svg")


# ================================================================== 700 container stage
def stage():
    S = sheet("P1-401-700", "CONTAINER STAGE AND INDEX", scale="1:2 · 1:1", material=SS304 + "; bushings UHMW-PE",
              finish=FIN_NPC + "; plate top #4 (container contact)", mass=kg(*[f"P1-401-70{i}" for i in range(1, 7)]))
    s2 = SC(2)
    # plate plan
    vp = S.view(640, 700, s2, "701 STAGE PLATE (1:2), 6 mm", (180, 330))
    rr(vp, -STAGE["w"] / 2, -STAGE["d"] / 2, STAGE["w"] / 2, STAGE["d"] / 2, "vis", SS)
    for x, y in ROD_PTS:
        vp.circle(x, y, 5.25); vp.circle(x, y, 10.25, "thin"); vp.cmark(x, y, 14)
    nest = [(sx * 70, sy * 70) for sx in (-1, 1) for sy in (-1, 1)]
    for x, y in nest + SB_PTS:
        vp.circle(x, y, 2.1); vp.circle(x, y, 2.5, "thin")
    rr(vp, STAGE["bar_x"] - 6, -20, STAGE["bar_x"] + 6, 20, "hid")
    vp.cmark(0, 0, 30)
    vp.dim((-STAGE["w"] / 2, -STAGE["d"] / 2), (STAGE["w"] / 2, -STAGE["d"] / 2), -40, f"{mmi(STAGE['w'])}", "h")
    vp.dim((STAGE["w"] / 2, -STAGE["d"] / 2), (STAGE["w"] / 2, STAGE["d"] / 2), -40, f"{mmi(STAGE['d'])}", "v")
    vp.dim((0, -STAGE["rod_y"]), (0, STAGE["rod_y"]), 160, f"{mmi(2 * STAGE['rod_y'])} ±0.05", "v")
    vp.dim((-70, 70), (70, 70), 60, f"{mmi(140)}", "h")
    vp.dim((0, -20), (STAGE["bar_x"], -20), -110, f"{mmi(STAGE['bar_x'])}", "h")
    vp.leader(ROD_PTS[1], (-60, 150), ["2 x Ø10.5 csk 90° to Ø20.5 (M10 x 20, H15)"], anchor="end")
    vp.leader(nest[3], (150, 150), ["4 x M5 THRU on 140 sq (nests)"])
    vp.leader(SB_PTS[0], (-150, 160) if False else (-170, 100), ["2 x M5 (706)"], anchor="end")
    vp.note(STAGE["bar_x"] + 10, -40, ["pin bar 704", "welded under"], 11)
    dxf_profile(str(DXF / "P1-401-701_stage_plate"), rect_pts(STAGE["w"], STAGE["d"]), holes=[(x, y, 5.25) for x, y in ROD_PTS] + [(x, y, 2.1) for x, y in nest + SB_PTS],
                text="P1-401-701 STAGE 6mm 304 (M5 tap, csk rods)")
    # section through the rods (y, z) with pin bar and plunger block (x, z)
    zst = Z_TOP + STAGE_POS["jar-12"]
    vs = S.view(1500, 640 + zst * s2, s2, "SECTION ON X = 0 THROUGH THE RODS, JAR POSITION (1:2)", (1150, 330))
    vs.hatch([(-STAGE["d"] / 2, zst), (STAGE["d"] / 2, zst), (STAGE["d"] / 2, zst + STAGE["t"]), (-STAGE["d"] / 2, zst + STAGE["t"])], "hA")
    for y in (-STAGE["rod_y"], STAGE["rod_y"]):
        rr(vs, y - 10, zst - STAGE["rod_L"], y + 10, zst, "vis", "#eceff1")
        vs.line(y - 5, zst - 20, y + 5, zst - 20, "hid"); rr(vs, y - 4.25, zst - 20, y + 4.25, zst, "hid")
        vs.hatch([(y - 30, ZC - STAGE["bush_L"]), (y - 10, ZC - STAGE["bush_L"]), (y - 10, ZC), (y - 30, ZC)], "hD" if False else "hB")
        vs.hatch([(y + 10, ZC - STAGE["bush_L"]), (y + 30, ZC - STAGE["bush_L"]), (y + 30, ZC), (y + 10, ZC)], "hB")
    vs.hatch([(-160, ZC), (-STAGE["rod_y"] - 12, ZC), (-STAGE["rod_y"] - 12, Z_TOP), (-160, Z_TOP)], "hA")
    vs.hatch([(-STAGE["rod_y"] + 12, ZC), (STAGE["rod_y"] - 12, ZC), (STAGE["rod_y"] - 12, Z_TOP), (-STAGE["rod_y"] + 12, Z_TOP)], "hA")
    vs.hatch([(STAGE["rod_y"] + 12, ZC), (160, ZC), (160, Z_TOP), (STAGE["rod_y"] + 12, Z_TOP)], "hA")
    vs.rect(-CONT["jar-12"]["d"] / 2, zst + STAGE["t"], CONT["jar-12"]["d"], CONT["jar-12"]["h"], "phan")
    vs.dim((STAGE["rod_y"] + 10, zst - STAGE["rod_L"]), (STAGE["rod_y"] + 10, zst), -50, f"{mmi(STAGE['rod_L'])} RODS", "v")
    vs.dim((-STAGE["rod_y"] - 30, ZC - STAGE["bush_L"]), (-STAGE["rod_y"] - 30, ZC), 40, f"{mmi(STAGE['bush_L'])}", "v")
    vs.dim((-STAGE["rod_y"] - 30, ZC - STAGE["bush_L"]), (-STAGE["rod_y"] + 30, ZC - STAGE["bush_L"]), -40, f"{mmi(STAGE['bush_a'])} SQ", "h")
    vs.leader((STAGE["rod_y"], zst - 150), (STAGE["rod_y"] + 70, zst - 210), ["702 ROD Ø20 h8 x 290, 316 ground,", "M10 x 20 deep tapped top end"])
    vs.leader((STAGE["rod_y"] + 20, ZC - 40), (STAGE["rod_y"] + 80, ZC - 120) if False else (STAGE["rod_y"] + 90, ZC - 90), ["703 UHMW BUSHING 60 sq x 80,", "bore Ø20.05 +0.05, 4 x M6 tapped 15 deep"])
    vs.text(0, zst + STAGE["t"] + 90, "JAR-12", 12, color="#607d8b")
    # pin bar + plunger block (x, z)
    vb = S.view(2150, 520 + zst * SC(1), SC(1), "PIN BAR 704 + PLUNGER BLOCK 705, SECTION ON Y = 0 (1:1)", (2170, 330))
    vb.hatch([(STAGE["bar_x"] - 60, zst), (STAGE["bar_x"] + 6, zst), (STAGE["bar_x"] + 6, zst + STAGE["t"]), (STAGE["bar_x"] - 60, zst + STAGE["t"])], "hA")
    vb.hatch([(STAGE["bar_x"] - 6, zst - STAGE["bar_L"]), (STAGE["bar_x"] + 6, zst - STAGE["bar_L"]), (STAGE["bar_x"] + 6, zst), (STAGE["bar_x"] - 6, zst)], "hB")
    for k, dd in PINBAR_HOLES.items():
        vb.rect(STAGE["bar_x"] - 6, zst - dd - PIN["hole"] / 2, 12, PIN["hole"], "vis", "#fff")
        vb.text(STAGE["bar_x"] - 20, zst - dd + 4, f"{k.split('-')[0]} {dd:.0f}", 11, "end")
    vb.hatch([(STAGE["bar_x"] - 60, ZC), (STAGE["bar_x"] - 8, ZC), (STAGE["bar_x"] - 8, Z_TOP), (STAGE["bar_x"] - 60, Z_TOP)], "hA")
    vb.hatch([(STAGE["bar_x"] + 8, ZC), (PLG["x"] + 60, ZC), (PLG["x"] + 60, Z_TOP), (STAGE["bar_x"] + 8, Z_TOP)], "hA")
    vb.hatch([(PLG["x"] - 20, Z_TOP), (PLG["x"] + 20, Z_TOP), (PLG["x"] + 20, Z_TOP + 40), (PLG["x"] - 20, Z_TOP + 40)], "hA")
    vb.rect(PLG["x"] - 20, Z_TOP + PLG["h"] - 7.25, 40, 14.5, "vis", "#fff")
    vb.rect(STAGE["bar_x"] - 6, Z_TOP + PLG["h"] - 5, PLG["x"] - 20 - STAGE["bar_x"] + 6, 10, "vis", "#eceff1")
    vb.rect(PLG["x"] + 20, Z_TOP + PLG["h"] - 12, 20, 24, "vis", BLU); vb.circle(PLG["x"] + 55, Z_TOP + PLG["h"], 15, "vis", BLU)
    vb.dim((STAGE["bar_x"] - 6, zst), (STAGE["bar_x"] - 6, zst - STAGE["bar_L"]), 170, f"{mmi(STAGE['bar_L'])}", "v")
    vb.dim((PLG["x"] + 20, Z_TOP), (PLG["x"] + 20, Z_TOP + 40), -110, f"{mmi(40)}", "v")
    vb.dim((PLG["x"] - 20, Z_TOP), (PLG["x"] - 20, Z_TOP + PLG["h"]), 20, None, "v") if False else None
    vb.dim((PLG["x"] - 20, Z_TOP + 40), (PLG["x"] + 20, Z_TOP + 40), 30, f"{mmi(40)}", "h")
    vb.leader((STAGE["bar_x"] + 6, zst - 120), (STAGE["bar_x"] + 60, zst - 190), ["704 PIN BAR 304 flat 40 x 12 x 150,", "4 x Ø10.2 H9 across, ream after welding", "fillet 4 both sides to 701 (W1)"])
    vb.leader((PLG["x"], Z_TOP + PLG["h"] + 7), (PLG["x"] + 20, Z_TOP + 120), ["705 BLOCK 40 x 50 x 40 304, M16 x 1.5 THRU", "at 20 above the top; 2 x M6 x 12 deep from below"])
    vb.weld((STAGE["bar_x"] - 6, zst), (STAGE["bar_x"] - 70, zst - 60), "fillet", "4", other="fillet", tail="W1")
    # sensor bracket + hole table
    s1 = SC(1)
    vsb = S.view(300, 1720, s1, "706 SENSOR BRACKET (1:1), 3 mm 304, FLAT", (170, 1330))
    flat_h = 40 + 45 - BD
    rr(vsb, 0, 0, 30, flat_h, "vis", SS); vsb.line(-5, 40 - BD / 2, 35, 40 - BD / 2, "cen")
    vsb.circle(15, 15, 2.75); vsb.circle(15, 30, 2.75) if False else None
    sbh = [(7.5, 20.0, 2.75), (22.5, 20.0, 2.75), (15.0, 40 - BD / 2 + 25, 9.25)]
    for x, y, r in sbh:
        vsb.circle(x, y, r)
    vsb.dim((0, 0), (30, 0), -30, None, "h"); vsb.dim((30, 0), (30, flat_h), -30, f"{mmi(flat_h, 1)}", "v")
    vsb.leader((24, 40 - BD / 2 + 25), (60, flat_h - 10), ["Ø18.5 for QS18 (P1-435), 2 nuts"])
    vsb.leader((22.5, 22.75), (60, 5), ["2 x Ø5.5 on 15 (H11)"])
    dxf_profile(str(DXF / "P1-401-706_sensor_bracket"), rect_pts(30, flat_h, 15, flat_h / 2), holes=sbh, bends=[((0, 40 - BD / 2), (30, 40 - BD / 2))],
                text="P1-401-706 SENSOR BKT 3mm 304, bend 90")
    S.table(900, 1500, [("CONTAINER", 160), ("STAGE STOP", 140), ("PIN HOLE", 130), ("NEST", 330), ("TOOLING", 100)], [
        (k, f"{STAGE_POS[k]:.0f} [{STAGE_POS[k] / 25.4:.2f}]", f"{PINBAR_HOLES[k]:.0f}", f"Ø{CONT[k]['d'] + 2:.0f} ring, UHMW 10 mm (P1-401-707, by trial)", CONT[k]["tool"]) for k in CONT],
        "INDEX POSITIONS (stage underside above the top / hole below the plate)", 13, 22)
    S.table(900, 1680, [("PART", 120), ("DESCRIPTION", 280), ("QTY", 40), ("STOCK", 430)], [
        ("P1-401-701", "Stage plate", 1, "304 6 mm 240 x 240, laser + csk + tap"),
        ("P1-401-702", "Guide rod", 2, "316 ground bar Ø20 h8 x 290, M10 tapped 20 deep one end"),
        ("P1-401-703", "Linear bushing block", 2, "UHMW-PE 60 x 60 x 80, bore Ø20.05 +0.05/-0"),
        ("P1-401-704", "Pin bar", 1, "304 flat 40 x 12 x 150"),
        ("P1-401-705", "Plunger block", 1, "304 bar 40 x 50 x 40"),
        ("P1-401-706", "Sensor bracket", 1, "304 3 mm, 30 x 82.4 flat"),
    ], "PARTS", 13, 22)
    S.notes(1900, 1500, 1000, [
        "Rods square to the top within 0.2 over 200: fit the bushings with the rods in place and the stage at the shaker stop, then tighten H10.",
        "Ream the 4 pin holes after welding the bar so they stay square to the plunger axis; the plunger GN 617-10 needs Ø10 H9 holes.",
        "Set the stops on the first build with the real containers: rim 10 [.39] below the tube outlet (GAP 10) at each stop.",
        "Nest rings are UHMW-PE turned to each container, held by the 4 M5 screws; one ring per container, kept with the change parts.",
    ], "ASSEMBLY", 13)
    dxf_profile(str(DXF / "P1-401-704_pin_bar"), rect_pts(40, STAGE["bar_L"], 0, -STAGE["bar_L"] / 2), text="P1-401-704 PIN BAR 12mm 304 (holes drilled across after welding)")
    S.save(DWG / "P1-401-700_container_stage.svg")


if __name__ == "__main__":
    cabinet(); flats(); column(); stage()
    print("ok")
