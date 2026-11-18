"""P1-301 cover weldment 300 (+ flat patterns) and frame weldment 400 with cut list, frame plates 405-410 (+ DXF)."""
import math

from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

s5, s4, s2, s1 = SC(5), SC(4), SC(2), SC(1)
CX, CY = FL_OUT_X + 6, FL_OUT_Y + 6           # cover outside 1006 x 652
SK = 25.0                                     # skirt
OPEN = dict(x=-110.0, w=600.0, h=400.0)
INLET_X = 330.0
LATCH_X = (-350.0, 0.0, 350.0)
HINGE_X = (-300.0, 300.0)
T = 3.0; RB = 3.0; KF = 0.4
BA = math.pi / 2 * (RB + KF * T)              # bend allowance 90°
LO, LI = X_LEG + LEG / 2, X_LEG - LEG / 2
Z_TA = 1500.0                                  # torque-arm bracket centre
Z_PR = (1000.0, 1400.0)                        # panel rails


def cover_flat():
    fx = (CX - 2 * (RB + T)) + 2 * (SK - (RB + T)) + 2 * BA
    fy = (CY - 2 * (RB + T)) + 2 * (SK - (RB + T)) + 2 * BA
    rel = SK - (RB + T) + BA / 2
    return fx, fy, rel


def cover():
    fx, fy, rel = cover_flat()
    S = sheet("P1-301-300", "COVER WELDMENT AND FLAT PATTERNS", scale="1:5, 1:1", material=SS316L + ", 3 [.118] sheet; knuckles 316 bar",
              finish="Underside (product) #4; top #4", mass=kg("P1-301-301", "P1-301-302", "P1-301-303", "P1-301-305"))
    p = S.view(620, 520, s5, "PLAN (top of cover, back = up)  1:5", (120, 120))
    p.rect(-CX / 2, -CY / 2, CX, CY); p.rect(-CX / 2 + T, -CY / 2 + T, CX - 2 * T, CY - 2 * T, "hid")
    p.rect(OPEN["x"] - OPEN["w"] / 2 - T, -OPEN["h"] / 2 - T, OPEN["w"] + 2 * T, OPEN["h"] + 2 * T); p.rect(OPEN["x"] - OPEN["w"] / 2, -OPEN["h"] / 2, OPEN["w"], OPEN["h"])
    p.circle(INLET_X, 0, TC4_FER_OD / 2); p.circle(INLET_X, 0, 98.3 / 2); p.cmark(INLET_X, 0, 60)
    for x in HINGE_X:
        for dx in (-41, 41):
            p.rect(x + dx - 19, CY / 2 - T + 1, 38, 20)
        p.rect(x - 19, CY / 2 + 1, 38, 20, "phan")
    for x in LATCH_X:
        p.rect(x - 20, -CY / 2 - 18, 40, 18, "thin")
    p.rect(400 - 15, -CY / 2 - 10, 30, 10, "thin")
    p.centre(-560, 0, 560, 0); p.centre(OPEN["x"], -260, OPEN["x"], 260)
    p.dim((-CX / 2, CY / 2), (CX / 2, CY / 2), 70, f"{mmi(CX)} OUTSIDE", "h")
    p.dim((CX / 2, -CY / 2), (CX / 2, CY / 2), -50, f"{mmi(CY)}", "v")
    p.dim((OPEN["x"] - OPEN["w"] / 2, -OPEN["h"] / 2), (OPEN["x"] + OPEN["w"] / 2, -OPEN["h"] / 2), -40, f"OPENING {mmi(OPEN['w'])}", "h")
    p.dim((OPEN["x"] - OPEN["w"] / 2, -OPEN["h"] / 2), (OPEN["x"] - OPEN["w"] / 2, OPEN["h"] / 2), 30, f"{mmi(OPEN['h'])}", "v")
    p.dim((0, -CY / 2), (OPEN["x"], -CY / 2), -95, f"{mmi(-OPEN['x'])}", "h")
    p.dim((0, -CY / 2), (INLET_X, -CY / 2), -95, f"{mmi(INLET_X)}", "h")
    p.dim((LATCH_X[0], -CY / 2 - 18), (LATCH_X[2], -CY / 2 - 18), -150, f"LATCHES 3 x at {mmi(350)}", "h")
    p.dim((HINGE_X[0], CY / 2 + 21), (HINGE_X[1], CY / 2 + 21), 30, f"HINGES {mmi(600)}", "h")
    p.leader((INLET_X + 40, 40), (430, 200), ["Ø98.3 [3.870] hole, 4 in TC ferrule (303)", "inlet for screw P1-224"])
    p.leader((400, -CY / 2 - 5), (470, -420), ["interlock actuator BPS 260 (P1-332) on skirt"])
    p.tag(-560, 300, 1, (-480, 280)); p.tag(OPEN["x"], 300, 2, (OPEN["x"] + 200, 203)); p.tag(INLET_X + 120, -150, 3, (INLET_X, -55)); p.tag(-300, 400, 4, (-300 - 41, CY / 2 + 10))
    # section through the cover (y, z), cut on x = 330 (inlet)
    e = S.view(1700, 700, SC(2.5), "SECTION E-E  (through the inlet, x = 330)  1:2.5", (1400, 120))
    e.hatch([(-CY / 2, 0), (CY / 2, 0), (CY / 2, -SK), (CY / 2 - T, -SK), (CY / 2 - T, -T), (98.3 / 2, -T), (98.3 / 2, 0)], "hC") if False else None
    for a, b in ((-CY / 2, -98.3 / 2), (98.3 / 2, CY / 2)):
        e.hatch([(a, 0), (b, 0), (b, T), (a, T)], "hC")
    for sy in (-1, 1):
        e.hatch([(sy * CY / 2, T), (sy * (CY / 2 - T), T), (sy * (CY / 2 - T), T - SK), (sy * CY / 2, T - SK)], "hC")
    for sy in (-1, 1):
        e.hatch([(sy * 98.3 / 2, T), (sy * TC4_OD / 2, T), (sy * TC4_OD / 2, T + TC4_FER_L - 4), (sy * TC4_FER_OD / 2, T + TC4_FER_L - 4), (sy * TC4_FER_OD / 2, T + TC4_FER_L), (sy * 98.3 / 2, T + TC4_FER_L)], "hB")
    e.rect(-CY / 2 + T, -6, 20, 6, "thin", "#90a4ae"); e.rect(CY / 2 - T - 20, -6, 20, 6, "thin", "#90a4ae")
    e.hatch([(-CY / 2 + 3, -6 - T_FL), (-W_IN / 2, -6 - T_FL), (-W_IN / 2, -6), (-CY / 2 + 3, -6)], "hC") if False else None
    e.circle(CY / 2 + 14, 4, 10, "vis", "#fff"); e.circle(CY / 2 + 14, 4, 5)
    e.dim((-CY / 2, T), (CY / 2, T), 90, f"{mmi(CY)}", "h")
    e.dim((-CY / 2, T - SK), (-CY / 2, T), 40, f"SKIRT {mmi(SK)}", "v")
    e.dim((TC4_FER_OD / 2, T), (TC4_FER_OD / 2, T + TC4_FER_L), -30, f"{mmi(TC4_FER_L)}", "v")
    e.leader((-CY / 2 + 13, -3), (-250, -80), ["GASKET P1-339 20 x 6 on the flange, under the cover land"])
    e.leader((CY / 2 + 14, 14), (200, 90), ["HINGE pin Ø10 (H10)"])
    e.weld((TC4_OD / 2, T), (150, 70), "fillet", "3", tail="ferrule outside; inside flush")
    e.weld((CY / 2 - T, -10), (180, -60), "fillet", "3", length="20-100", tail="skirt corners full, sides stitch") if False else None
    # flat pattern
    f = S.view(620, 1500, s5, f"P1-301-301  COVER FLAT PATTERN  3 [.118] 316L  1:5  (K {KF}, inside R{RB:.0f}, BA {BA:.2f})", (120, 1100))
    w2, h2, r = fx / 2, fy / 2, rel
    outline = [(-w2 + r, -h2), (w2 - r, -h2), (w2 - r, -h2 + r), (w2, -h2 + r), (w2, h2 - r), (w2 - r, h2 - r), (w2 - r, h2), (-w2 + r, h2), (-w2 + r, h2 - r), (-w2, h2 - r), (-w2, -h2 + r), (-w2 + r, -h2 + r)]
    f.poly(outline)
    bx, by = w2 - (SK - (RB + T)) - BA / 2, h2 - (SK - (RB + T)) - BA / 2
    for sg in (-1, 1):
        f.line(sg * bx, -h2, sg * bx, h2, "bend"); f.line(-w2, sg * by, w2, sg * by, "bend")
    f.rect(OPEN["x"] - OPEN["w"] / 2, -OPEN["h"] / 2, OPEN["w"], OPEN["h"]); f.circle(INLET_X, 0, 98.3 / 2)
    f.dim((-w2, h2), (w2, h2), 40, f"{mmi(fx, 1)}", "h"); f.dim((w2, -h2), (w2, h2), -40, f"{mmi(fy, 1)}", "v")
    f.dim((-w2, -h2 + r), (-w2 + r, -h2 + r), -60, f"RELIEF {mmi(r, 1)} SQ", "h")
    f.dim((-w2, 0), (-bx, 0), 0, f"{mmi(w2 - bx, 1)} to bend", "h", ext=False)
    f.note(0, -h2 - 70, ["bend skirt DOWN 90° all 4 sides on the brake; weld the 4 corners closed (fillet 3 inside, grind outside)"], 13, "middle")
    holes = [(INLET_X, 0, 98.3 / 2)]
    op = [(OPEN["x"] - OPEN["w"] / 2, -OPEN["h"] / 2), (OPEN["x"] + OPEN["w"] / 2, -OPEN["h"] / 2), (OPEN["x"] + OPEN["w"] / 2, OPEN["h"] / 2), (OPEN["x"] - OPEN["w"] / 2, OPEN["h"] / 2)]
    ms.dxf_profile(str(DXF / "P1-301-301_cover_flat"), [outline, op], holes=holes,
                   bends=[((sg * bx, -h2), (sg * bx, h2)) for sg in (-1, 1)] + [((-w2, sg * by), (w2, sg * by)) for sg in (-1, 1)], text="P1-301-301 3mm 316L x1 - bends DOWN 90 R3")
    up_L = 2 * (OPEN["w"] + T) + 2 * (OPEN["h"] + T)
    u = S.view(1500, 1520, s5, "P1-301-302  UPSTAND STRIP  3 [.118] 316L  1:5", (1400, 1400))
    u.rect(0, 0, up_L / 2, 25); u.note(up_L / 4, -25, [f"{mmi(up_L, 1)} x 25 [.98] (shown half length); 4 bends 90° at 603 / 403 [23.74 / 15.87] centres, close with one butt weld at a corner"], 13, "middle")
    ms.dxf_profile(str(DXF / "P1-301-302_upstand_strip"), [(0, 0), (up_L, 0), (up_L, 25), (0, 25)],
                   bends=[((x, 0), (x, 25)) for x in (603.0, 1006.0, 1609.0)], text="P1-301-302 3mm 316L strip; last corner is the weld seam")
    # hinge detail
    h = S.view(2850, 700, s1, "DETAIL H  HINGE (2 off)  1:1", (2600, 120))
    for x0, lab in ((-60, "305 cover"), (-19, "109 trough"), (22, "305 cover")):
        h.rect(x0, -10, 38, 20, "vis", "#fff"); h.text(x0 + 19, 18, lab, 11)
    h.line(-65, 0, 65, 0, "cen"); h.rect(-65, -5, 130, 10, "hid")
    h.dim((-60, -10), (60, -10), -40, f"{mmi(120)}", "h"); h.dim((-19, 10), (19, 10), 45, "38", "h")
    h.dim((19, -10), (22, -10), -20, "3", "h", ext=False)
    h.note(-65, -50, ["knuckles: Ø20 316 bar x 38, bore Ø10.2 [.402] ream Ø10 H9 not needed;", "pin H10 Ø10 h9 x 130 with R-clip; trough knuckle (109) on a", "6 x 38 x 45 leaf welded to the flange back edge (W6)"], 12)
    S.notes(1400, 1640, 1100, [
        "Laser the flat pattern (opening and inlet hole included), brake the 4 skirt bends DOWN, weld corners closed, grind and blend.",
        "Fold the upstand strip, butt-weld the seam, fit it on the opening edge (strip inside face flush with the opening), fillet 3 [.12] outside continuous and inside ground flush (product side).",
        "Weld the 4 in ferrule (P1-301-303, BPE 14WMP short) over the Ø98.3 hole: outside fillet 3, inside fusion ground flush, no ledge.",
        "Hang the cover on the trough with the hinge pins, then weld the cover knuckles to the skirt so the cover lands evenly on the gasket (feeler 3 ±0.5 compression).",
        "Fit latches P1-338 (3) and keepers, interlock actuator (P1-332): drill on assembly M5 / M4 (H8, H9). Cover must open to 105° and rest on the hinge stop.",
        "Flatness: cover land flat within 1.5 [.06] after welding. Passivate.",
    ], fs=13)
    S.table(2560, 1100, [("FILE", 380), ("QTY", 60)], [("P1-301-301_cover_flat_mm/_in.dxf", 1), ("P1-301-302_upstand_strip_mm/_in.dxf", 1)], "CUT FILES", 13, 23)
    S.table(2560, 1220, [("ITEM", 50), ("PART", 120), ("DESCRIPTION", 260), ("QTY", 40)], [
        (1, "P1-301-301", "cover plate, formed", 1), (2, "P1-301-302", "upstand 600 x 400", 1), (3, "P1-301-303", "4 in BPE ferrule 14WMP", 1),
        (4, "P1-301-305", "cover knuckle Ø20 x 38", 4), (5, "H10", "hinge pin Ø10 x 130 + R-clip", 2)], "ITEM LIST", 13, 23)
    S.save(DWG / "P1-301-300_cover.svg")


# ================================================================== 400 frame
def frame():
    S = sheet("P1-301-400", "FRAME WELDMENT AND CUT LIST", scale="1:8", material=SS304 + ", tube 76.2 x 76.2 x 3.05 [3 x 3 x .120], plates",
              finish=FIN_NPC, mass=kg("P1-301-401", "P1-301-402", "P1-301-403", "P1-301-405", "P1-301-406", "P1-301-408"))
    s10 = SC(8)
    F = S.view(560, 230 + Z_RAIL * s10, s10, "FRONT (from the front, y-)  1:8", (120, 120))
    for sx in (-1, 1):
        F.rect(sx * X_LEG - LEG / 2, 12, LEG, Z_RAIL - 15); F.rect(sx * X_LEG - FOOT / 2, 0, FOOT, 12); F.rect(sx * X_LEG - LEG / 2, Z_RAIL - 3, LEG, 3)
        F.rect(min(sx * BP["x_in"], sx * (BP["x_in"] + BP["t"])), BP["z0"], BP["t"], BP["z1"] - BP["z0"], "hid")
    F.rect(-LI, Z_RAIL - LEG, 2 * LI, LEG); F.rect(-LI, Z_LOW - LEG, 2 * LI, LEG)
    F.rect(LO, Z_TA - 50, 10, 100)
    for z in Z_PR:
        F.rect(LO, z - 25, 6, 50)
    for x in LUG["x"]:
        F.line(x, Z_RAIL, x, Z_RAIL - LEG, "hid")
    F.dim((-X_LEG, 0), (X_LEG, 0), -40, f"LEG CENTRES {mmi(2 * X_LEG)}", "h")
    F.dim((-LI, Z_RAIL), (LI, Z_RAIL), 30, f"RAIL {mmi(2 * LI, 1)}", "h")
    F.dim((-X_LEG - FOOT / 2, 0), (-X_LEG - FOOT / 2, Z_RAIL), 40, f"TOP OF RAILS {mmi(Z_RAIL)} ±1", "v")
    F.dim((-X_LEG - FOOT / 2, 0), (-X_LEG - FOOT / 2, Z_LOW), 0, f"{mmi(Z_LOW)}", "v", ext=False)
    F.dim((LO + 10, 0), (LO + 10, Z_TA), -60, f"{mmi(Z_TA)}", "v")
    F.dim((LO + 6, 0), (LO + 6, Z_PR[0]), -20, f"{mmi(Z_PR[0])}", "v")
    F.dim((-LUG["x"][1], Z_RAIL), (LUG["x"][1], Z_RAIL), 75, f"SLEEVES (409) {mmi(600)}", "h")
    F.leader((LO + 5, Z_TA), (LO + 60, Z_TA + 120), ["408 torque-arm bracket (front leg)"])
    F.leader((LO + 3, Z_PR[1]), (LO + 60, Z_PR[1] - 80), ["410 panel rails x 2"])
    F.tag(-X_LEG, 900, 1, (-X_LEG, 800)); F.tag(-200, Z_RAIL + 120, 2, (-200, Z_RAIL - 20)); F.tag(-200, Z_LOW + 150, 3, (-200, Z_LOW - 20))
    F.tag(-X_LEG - 140, 60, 6, (-X_LEG - 60, 6)); F.tag(BP["x_in"] - 120, BP["z0"] - 120, 5, (BP["x_in"], BP["z0"] + 50))
    F.weld((-LI, Z_RAIL - LEG / 2), (-400, Z_RAIL - 250), "fillet", "3", allround=True, tail="all tube joints")
    F.weld((-X_LEG, 12), (-350, 150), "fillet", "5", allround=True, tail="legs to feet")
    E = S.view(1650, 230 + Z_RAIL * s10, s10, "END (from the drive end)  1:8", (1300, 120))
    for sy in (-1, 1):
        E.rect(sy * Y_LEG - LEG / 2, 12, LEG, Z_RAIL - 15); E.rect(sy * Y_LEG - FOOT / 2, 0, FOOT, 12)
    E.rect(-(Y_LEG - LEG / 2), BP["z0"], 2 * (Y_LEG - LEG / 2), BP["z1"] - BP["z0"]); E.circle(0, Z_AX, BP["hole"] / 2)
    for dy in (-1, 1):
        for dz in (-1, 1):
            E.circle(dy * BP["bolt_sq"] / 2, Z_AX + dz * BP["bolt_sq"] / 2, BP["bolt_d"] / 2)
    E.rect(-(Y_LEG - LEG / 2), Z_LOW - LEG, 2 * (Y_LEG - LEG / 2), LEG)
    for z in Z_PR:
        E.rect(-Y_LEG - LEG / 2, z - 25, 2 * Y_LEG + LEG, 50, "thin")
    E.rect(-Y_LEG - 40, Z_TA - 50, 80, 100, "thin")
    E.dim((-Y_LEG, 0), (Y_LEG, 0), -40, f"LEG CENTRES {mmi(2 * Y_LEG)}", "h")
    E.dim((-(Y_LEG - LEG / 2), Z_RAIL), ((Y_LEG - LEG / 2), Z_RAIL), 30, f"CLEAR {mmi(2 * (Y_LEG - LEG / 2), 1)} (drum passes)", "h")
    E.dim((Y_LEG + LEG, Z_AX), (Y_LEG + LEG, Z_RAIL), -40, f"{mmi(Z_RAIL - Z_AX)}", "v")
    E.dim((Y_LEG + LEG, 0), (Y_LEG + LEG, Z_AX), -40, f"AXIS {mmi(Z_AX)}", "v")
    E.note(0, Z_LOW - LEG - 60, ["lower cross rail at the drive end only (free end open)"], 12, "middle")
    P = S.view(2700, 600, s10, "PLAN  1:8", (2300, 120))
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.rect(sx * X_LEG - LEG / 2, sy * Y_LEG - LEG / 2, LEG, LEG, "vis", "#eceff1")
        P.rect(min(sx * BP["x_in"], sx * (BP["x_in"] + BP["t"])), -(Y_LEG - LEG / 2), BP["t"], 2 * (Y_LEG - LEG / 2))
    for sy in (-1, 1):
        P.rect(-LI, sy * Y_LEG - LEG / 2, 2 * LI, LEG)
        for x in LUG["x"]:
            P.circle(x, sy * Y_LEG, 10)
    P.dim((-X_LEG, Y_LEG), (X_LEG, Y_LEG), 40, f"{mmi(2 * X_LEG)}", "h"); P.dim((X_LEG, -Y_LEG), (X_LEG, Y_LEG), -40, f"{mmi(2 * Y_LEG)}", "v")
    P.note(X_LEG, -Y_LEG - 90, ["DRIVE END"], 12, "middle")
    rows = [("401", "Leg", "tube 76.2 x 3.05", 4, f"{Z_RAIL - 15:.0f} [{fin(Z_RAIL - 15)}]", "square both ends"),
            ("402", "Top rail", "tube 76.2 x 3.05", 2, f"{2 * LI:.1f} [{fin(2 * LI)}]", "square; holes Ø20.5 x 2 top+bottom at x ±300"),
            ("403", "Lower rail, side", "tube 76.2 x 3.05", 2, f"{2 * LI:.1f} [{fin(2 * LI)}]", "square"),
            ("403", "Lower rail, drive end", "tube 76.2 x 3.05", 1, f"{2 * (Y_LEG - LEG / 2):.1f} [{fin(2 * (Y_LEG - LEG / 2))}]", "square"),
            ("405", "Bearing plate", "plate 12", 2, "723.8 x 240", "sheet P1-301-405, DXF"),
            ("406", "Foot", "plate 12", 4, "150 x 150", "4 x Ø14, DXF"),
            ("406", "Leg cap", "plate 3", 4, "76.2 x 76.2", "DXF"),
            ("408", "Torque-arm bracket", "plate 10", 1, "80 x 100", "drill on assembly to the NORD arm"),
            ("409", "Crush sleeve", "tube Ø20 x 2", 4, "76.2 [3.000]", "through the top rail, welded top and bottom"),
            ("410", "Panel rail", "flat 50 x 6", 2, f"{2 * Y_LEG + LEG:.1f} [{fin(2 * Y_LEG + LEG)}]", "on the drive-end legs, outer face")]
    S.table(120, 1560, [("PART", 60), ("NAME", 200), ("STOCK (304)", 170), ("QTY", 45), ("CUT LENGTH / SIZE", 190), ("NOTE", 380)], rows, "CUT LIST", 13, 23)
    S.notes(1300, 1560, 1200, [
        "Tack the two side frames (legs + top and lower rails) flat on the table, check diagonals equal within 2 [.08], then stand them up and add the bearing plates and the lower cross rail.",
        "Bearing plates: weld square to the rails and to each other: the two Ø80 holes on one axis within 0.5 [.02] (check with a string line or the Ø63.8 bar). Bearings are shimmed and shifted in the Ø17.5 holes (slots allowed to 17.5 x 22) at assembly.",
        "Top of rails and bearing plates coplanar within 1 [.04] (lug seats rest here). Feet level within 1 on the table before grouting/anchoring.",
        "All tube joints: fillet 3 [.12] all round, ends sealed (no open tube ends: caps on legs, rails closed by the legs). Clean, passivate.",
    ], fs=13)
    S.save(DWG / "P1-301-400_frame.svg")


def frame_plates():
    S = sheet("P1-301-405", "FRAME PLATES", scale="1:2, 1:5", material=SS304 + " plate 12, 10, 6, 3 [.472, .394, .236, .118]", finish=FIN_NPC,
              mass=kg("P1-301-405", "P1-301-406", "P1-301-408"))
    W, H = 2 * (Y_LEG - LEG / 2), BP["z1"] - BP["z0"]
    b = S.view(200 + W / 2 * s2, 230 + H * s2, s2, "P1-301-405  BEARING PLATE  12 [.472]  QTY 2  1:2", (120, 120))
    za = Z_AX - BP["z0"]
    pts = [(-W / 2, 0), (W / 2, 0), (W / 2, H), (-W / 2, H)]
    b.poly(pts); b.circle(0, za, BP["hole"] / 2); b.cmark(0, za, 45)
    holes = [(0, za, BP["hole"] / 2)]
    for dy in (-1, 1):
        for dz in (-1, 1):
            b.circle(dy * BP["bolt_sq"] / 2, za + dz * BP["bolt_sq"] / 2, BP["bolt_d"] / 2); holes.append((dy * BP["bolt_sq"] / 2, za + dz * BP["bolt_sq"] / 2, BP["bolt_d"] / 2))
    b.dim((-W / 2, H), (W / 2, H), 40, f"{mmi(W, 1)}", "h"); b.dim((W / 2, 0), (W / 2, H), -40, f"{mmi(H)}", "v")
    b.dim((-W / 2, 0), (-W / 2, za), 40, f"{mmi(za)}", "v")
    b.dim((-BP["bolt_sq"] / 2, za - 90), (BP["bolt_sq"] / 2, za - 90), 0, f"{mmi(BP['bolt_sq'])} (UCF212 J)", "h")
    b.dim((BP["bolt_sq"] / 2 + 40, za - BP["bolt_sq"] / 2), (BP["bolt_sq"] / 2 + 40, za + BP["bolt_sq"] / 2), 0, f"{mmi(BP['bolt_sq'])}", "v")
    b.dia(0, za, BP["hole"] / 2, 135, (-200, H + 30), "Ø80 [3.150] shaft clearance")
    b.leader((BP["bolt_sq"] / 2 + 6, za + BP["bolt_sq"] / 2 + 6), (220, H + 30), ["4 x Ø17.5 [.689] for M16 (H1)"])
    ms.dxf_profile(str(DXF / "P1-301-405_bearing_plate"), pts, holes=holes, text="P1-301-405 12mm 304 x2")
    f = S.view(2200, 420, s2, "P1-301-406  FOOT  12 [.472]  QTY 4  1:2", (1950, 120))
    fp = [(-75, -75), (75, -75), (75, 75), (-75, 75)]
    f.poly(fp); f.rect(-LEG / 2, -LEG / 2, LEG, LEG, "phan")
    fh = [(dx * 55, dy * 55, 7) for dx in (-1, 1) for dy in (-1, 1)]
    for x, y, r in fh:
        f.circle(x, y, r)
    f.dim((-75, 75), (75, 75), 30, f"{mmi(150)}", "h"); f.dim((75, -75), (75, 75), -30, f"{mmi(150)}", "v")
    f.dim((-55, -75), (55, -75), -30, f"{mmi(110)}", "h")
    f.leader((55 + 5, 55 + 5), (110, 110), ["4 x Ø14 [.551] for 1/2 in anchors (H4)"])
    ms.dxf_profile(str(DXF / "P1-301-406_foot"), fp, holes=fh, text="P1-301-406 foot 12mm 304 x4")
    ms.dxf_profile(str(DXF / "P1-301-406_leg_cap"), [(0, 0), (LEG, 0), (LEG, LEG), (0, LEG)], text="P1-301-406 cap 3mm 304 x4")
    t = S.view(2200, 950, s2, "P1-301-408  TORQUE-ARM BRACKET  10 [.394]  QTY 1  1:2", (1950, 640))
    tp = [(-40, -50), (40, -50), (40, 50), (-40, 50)]
    t.poly(tp); t.circle(0, 0, 8.5, "phan")
    t.dim((-40, 50), (40, 50), 30, "80 [3.150]", "h"); t.dim((40, -50), (40, 50), -30, "100 [3.937]", "v")
    t.note(-40, -80, ["hole Ø17 [.669] drilled on assembly at the", "NORD torque-arm bush centre (confirm)"], 12)
    ms.dxf_profile(str(DXF / "P1-301-408_torque_bracket"), tp, text="P1-301-408 10mm 304 x1 - drill on assembly")
    r = S.view(140 + 60, 1500, SC(5), "P1-301-410  PANEL RAIL  FLAT 50 x 6 [2 x .236]  QTY 2  1:5", (120, 1350))
    Lr = 2 * Y_LEG + LEG
    r.rect(0, 0, Lr, 50); r.dim((0, 50), (Lr, 50), 30, f"{mmi(Lr, 1)}", "h"); r.dim((Lr, 0), (Lr, 50), -30, "50", "v")
    r.note(0, -30, ["holes for the CP-301 mounting feet drilled on assembly (H11, M10); weld to the drive-end legs, outer face, at z 1000 and 1400"], 12)
    S.table(1950, 1300, [("FILE", 400), ("QTY", 60)], [("P1-301-405_bearing_plate_mm/_in.dxf", 2), ("P1-301-406_foot_mm/_in.dxf", 4), ("P1-301-406_leg_cap_mm/_in.dxf", 4),
                                                          ("P1-301-408_torque_bracket_mm/_in.dxf", 1)], "CUT FILES", 13, 23)
    S.notes(1950, 1470, 1100, ["Bearing plates: laser, then check the 143 square and Ø80 position with the bearing housing before welding into the frame.",
                               "Holes Ø17.5 may be elongated to 17.5 x 22 [.69 x .87] vertically if the shaft line needs shimming at assembly."], fs=13)
    S.save(DWG / "P1-301-405_frame_plates.svg")


if __name__ == "__main__":
    cover(); frame(); frame_plates()
