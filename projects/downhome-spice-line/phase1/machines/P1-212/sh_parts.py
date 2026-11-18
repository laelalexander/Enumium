"""P1-212-100 barrel weldment, -101 barrel parts + flat patterns, -200 screw, -300 drive parts, -306 tail parts, -400 lantern, guard, gasket."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
from mechsheet import dxf_profile
import sh_ga

R_O, R_I = B_OD / 2, B_ID / 2
L_TUBE = X_TUBE1 - X_TUBE0
ZB = math.sqrt(R_O ** 2 - 25 ** 2)                      # tube surface under the side walls
SLANT = math.hypot(35.0, Z_FL_BOT - ZB)


def arcpts(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def rrect(w, h, r, cx=0.0, cy=0.0):
    pts = []
    for (x, y, a) in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        pts += arcpts(cx + x, cy + y, r, a, a + 90, 6)
    return pts


# ================================================================== 100 barrel weldment
def weldment():
    S = sheet("P1-212-100", "BARREL WELDMENT", scale="1:4 · 1:1", material=SS316L, finish=FIN_PC,
              mass=kg("P1-212-101", "P1-212-102", "P1-212-104", "P1-212-105", "P1-212-106", "P1-212-107"))
    s = SC(4)
    v = S.view(700, 820, s, "ELEVATION (weldment only)", (120, 420))
    v.rect(X_TUBE0, -R_O, L_TUBE, B_OD, fill="#fff")
    v.rect(X_FL_OUT, -EF["sq"] / 2, T_EF, EF["sq"], fill="#f4f6f8")
    v.rect(X_TAIL - 8, -FER["fl_od"] / 2, 8, FER["fl_od"], fill="#f4f6f8"); v.rect(X_TAIL - FER["L"], -R_O, FER["L"] - 8, B_OD, fill="#f4f6f8")
    v.poly([(-61.9, R_O - 2), (-61.9, Z_FL_BOT), (61.9, Z_FL_BOT), (61.9, R_O - 2)], fill="#fff")
    v.rect(-BIN_FL["sq"] / 2, Z_FL_BOT, BIN_FL["sq"], T_FL, fill="#f4f6f8")
    v.rect(X_SPOUT - R_O, Z_SPOUT_END, B_OD, -Z_SPOUT_END - R_O + 1, fill="#fff")
    v.rect(-INLET["lx"] / 2, R_I, INLET["lx"], 2, "hid")
    v.centre(X_FL_OUT - 40, 0, X_TAIL + 40, 0); v.centre(X_SPOUT, 30, X_SPOUT, Z_SPOUT_END - 30); v.centre(0, -40, 0, Z_FL_TOP + 30)
    v.datum((500, -R_O), "A", (0, -1))
    v.dim((X_FL_OUT, -EF["sq"] / 2), (X_TAIL, -EF["sq"] / 2), -60, f"{mmi(X_TAIL - X_FL_OUT)} ±1", "h")
    v.dim((X_FL_OUT, EF["sq"] / 2), (0, EF["sq"] / 2), 40, None, "h")
    v.dim((0, Z_FL_TOP), (X_SPOUT, Z_FL_TOP), 40, f"{mmi(X_SPOUT)} ±1", "h")
    v.dim((X_SPOUT, -R_O), (X_TAIL, -R_O), -110, None, "h")
    v.dim((BIN_FL["sq"] / 2, 0), (BIN_FL["sq"] / 2, Z_FL_TOP), -40, f"{mmi(Z_FL_TOP)} ±0.5", "v")
    v.dim((X_SPOUT + R_O, 0), (X_SPOUT + R_O, Z_SPOUT_END), -40, f"{mmi(-Z_SPOUT_END)} ±1", "v")
    v.weld((X_FL_IN, R_O), (-260, 170), "fillet", "2", allround=True, tail="W1")
    v.weld((-61.9, R_O + 4), (-420, 110), "fillet", "2", allround=True, tail="W3")
    v.weld((-61.9, 120), (-430, 250), "sq", "", tail="W2 (4 corners)")
    v.weld((-100, Z_FL_BOT), (-430, 310), "fillet", "2", allround=True, tail="W4")
    v.weld((X_SPOUT - R_O, -R_O - 3), (X_SPOUT - 350, -150), "fillet", "2", allround=True, tail="W5")
    v.weld((X_TUBE1, R_O), (X_TUBE1 - 260, 150), "sq", "", allround=True, contour="flush", tail="W6")
    v.fcf(X_FL_OUT - 140, -110, ["⟂", "0.1", "A"]) if False else None
    v.leader((X_FL_OUT, -40), (X_FL_OUT - 160, -150), ["END FLANGE FACE: machine after welding", "⟂ 0.1 to A; recess Ø70 H8 x 3 coaxial Ø0.1 to A"])
    v.leader((X_TAIL, 30), (X_TAIL + 30, 140), ["TAIL FERRULE FACE ⟂ 0.2 to A"], anchor="end")
    # end flange face view 1:1
    s1 = SC(1)
    ve = S.view(600, 1600, s1, "VIEW F (1:1): END FLANGE AFTER MACHINING", (300, 1340))
    ve.poly(rrect(EF["sq"], EF["sq"], 5), fill="#f4f6f8")
    ve.circle(0, 0, EF["recess"] / 2); ve.circle(0, 0, R_I, fill="#fff")
    for k in range(4):
        a = math.radians(45 + 90 * k)
        ve.circle(EF["pcd"] / 2 * math.cos(a), EF["pcd"] / 2 * math.sin(a), 2.5); ve.circle(EF["pcd"] / 2 * math.cos(a), EF["pcd"] / 2 * math.sin(a), 3.0, "thin")
    ve.circle(0, 0, EF["pcd"] / 2, "cen"); ve.cmark(0, 0, 60)
    ve.dim((-EF["sq"] / 2, EF["sq"] / 2), (EF["sq"] / 2, EF["sq"] / 2), 30, None, "h")
    ve.dim((EF["sq"] / 2, -EF["sq"] / 2), (EF["sq"] / 2, EF["sq"] / 2), -30, None, "v")
    ve.dia(0, 0, EF["recess"] / 2, 340, (75, -30), f"Ø{mmi(EF['recess'])} H8 x 3 [.118] DEEP", "+0.046/0")
    ve.dia(0, 0, R_I, 300, (75, -65), f"Ø{mmi(B_ID, 1)} THRU (= tube ID, blend flush)")
    ve.leader((EF["pcd"] / 2 * 0.7071, EF["pcd"] / 2 * 0.7071), (80, 75), ["4 x M6 x 1 - 6H ▽ 8 [.31]", f"drill Ø5.0 ▽ 10 on PCD {mmi(EF['pcd'])} at 45°"], anchor="start")
    ve.fcf(20, -78, ["⌖", "Ø0.1", "A"])
    # weld schedule + parts
    S.table(1500, 1120, [("WELD", 60), ("JOINT", 380), ("PROCESS / FILLER", 330), ("PRODUCT SIDE", 330), ("NOTES", 300)], [
        ("W1", "Tube in end-flange socket", "GTAW, ER316LSi, argon back purge", "fuse root, grind flush to ID", "fillet 2 outside all round"),
        ("W2", "Transition corner seams (4)", "GTAW autogenous corner, full pen.", "inside corners ground R3 min", "tack, check 120 sq / 120 x 50 first"),
        ("W3", "Transition to tube (saddle)", "GTAW, ER316LSi, purge inside tube", "full pen., ground flush", "fillet 2 outside all round"),
        ("W4", "Inlet flange to transition", "GTAW, ER316LSi", "seal weld, ground flush", "fillet 2 outside all round; flange flat 0.3"),
        ("W5", "Spout to tube (saddle)", "GTAW, ER316LSi, purge", "full pen., R1 blend, flush", "fillet 2 outside all round"),
        ("W6", "Tail ferrule butt (14WMP)", "orbital or manual GTAW autogenous", "full pen., ID flush, no concavity > 0.1", "per ASME BPE MJ; borescope"),
    ], "WELD SCHEDULE (AWS D18.1 / ASME BPE MJ; weld log per joint)", fs=13, rh=22)
    S.table(1500, 1400, [("PART", 130), ("DESCRIPTION", 520), ("QTY", 45), ("STOCK / SIZE", 410), ("DRG", 100)], [
        ("P1-212-101", "Barrel tube", 1, f"A270 316L 2.5 in x 16 ga (63.5 x 1.65) x {L_TUBE:.1f}", "-101"),
        ("P1-212-102", "Transition end wall", 2, "316L 14 ga (1.9) laser cut", "-101"),
        ("P1-212-103", "Transition side wall", 2, f"316L 14 ga (1.9) {123.8} x {SLANT:.1f}", "-101"),
        ("P1-212-104", "Inlet flange", 1, "316L plate 6 laser cut", "-101"),
        ("P1-212-105", "Drive-end flange (machined after weld)", 1, "316L plate 12 (finish 10) 110 sq", "-101"),
        ("P1-212-106", "Spout", 1, "A270 316L 2.5 in x 16 ga, saddle cut", "-101"),
        ("P1-245", "Short weld ferrule 14WMP 2.5 in", 1, "bought, 316L", "-"),
    ], "WELDMENT PARTS", fs=13, rh=22)
    S.notes(1500, 1600, 1000, [
        "Weld the transition (W2) as a box first, then W3 to the tube with the slot cut; then the inlet flange (W4) square to the tube axis within 0.5 over 200.",
        "Weld W1 and W6 with the tube clamped in V-blocks; straightness of the finished barrel 0.5 [.02] over its length (checked with the screw: it must turn by hand).",
        "Machine the end flange outer face, Ø70 H8 recess and M6 holes AFTER all welding, set up on the barrel axis (datum A from the tube OD at both ends).",
        "Pickle and passivate the whole weldment (ASTM A967 nitric 2) after machining; rinse with RO water; inspect the ID with a borescope (ITP T3).",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-212-100_barrel_weldment.svg")


# ================================================================== 101 barrel parts + flat patterns
def parts_flat():
    S = sheet("P1-212-101", "BARREL PARTS AND FLAT PATTERNS", scale="1:4 · 1:2 · 1:1", material=SS316L, finish=FIN_PC, mass="see 100")
    # tube 101 at 1:4
    s = SC(4)
    v = S.view(250 + 124 * s, 330, s, "P1-212-101 BARREL TUBE (1:4) · cut from 20 ft A270 stick", (150, 180))
    x0 = X_TUBE0
    v.rect(x0, -R_O, L_TUBE, B_OD)
    v.rect(-INLET["lx"] / 2, R_O - 6, INLET["lx"], 6, "vis", "#fff")
    v.circle(X_SPOUT, 0, R_I, "hid")
    v.centre(x0 - 30, 0, X_TUBE1 + 30, 0)
    v.dim((x0, -R_O), (X_TUBE1, -R_O), -60, f"{mmi(L_TUBE, 1)} ±0.5", "h")
    v.dim((x0, R_O), (-INLET["lx"] / 2, R_O), 40, None, "h")
    v.dim((-INLET["lx"] / 2, R_O), (INLET["lx"] / 2, R_O), 40, None, "h")
    v.dim((x0, -R_O), (X_SPOUT, -R_O), -110, None, "h")
    v.leader((0, R_O), (150, 110), ["SLOT 120 x 50 [4.72 x 1.97] TOP, laser or plasma + file", "corners R3; deburr inside"], anchor="start")
    v.leader((X_SPOUT, -R_I), (X_SPOUT + 120, -60), anchor="start", lines=[f"Ø{mmi(B_ID, 1)} BOTTOM, on the axis (spout bore)", "hole saw + deburr, after W1"])
    # end wall 102 at 1:1 flat
    s1 = SC(1)
    ew = [(-60, Z_FL_BOT), (60, Z_FL_BOT), (25, ZB)] + [(R_O * math.sin(math.radians(a)), R_O * math.cos(math.radians(a))) for a in [math.degrees(math.asin(25 / R_O)) - i * 2 * math.degrees(math.asin(25 / R_O)) / 20 for i in range(21)]] + [(-25, ZB)]
    ew = [(x, z - ZB) for x, z in ew]
    v2 = S.view(520, 1300, s1, "P1-212-102 END WALL x2 (1:1) · 14 ga 316L", (250, 580))
    v2.poly(ew)
    v2.dim((-60, Z_FL_BOT - ZB), (60, Z_FL_BOT - ZB), 30, None, "h")
    v2.dim((-25, 0), (25, 0), -60, None, "h")
    v2.dim((60, 0), (60, Z_FL_BOT - ZB), -60, None, "v")
    v2.dim((-60, Z_FL_BOT - ZB), (-60, R_O - ZB), 80, None, "v")
    v2.leader((0, R_O - ZB), (90, -40), [f"R{mmi(R_O, 2)} SADDLE (fits the tube OD)"], anchor="start")
    dxf_profile(str(DXF / "P1-212-102_end_wall"), ew, text="P1-212-102 END WALL x2 14ga 316L")
    # side wall 103
    v3 = S.view(1300, 1300, s1, "P1-212-103 SIDE WALL x2 (1:1) · 14 ga 316L", (1060, 545))
    sw = [(-61.9, 0), (61.9, 0), (61.9, SLANT), (-61.9, SLANT)]
    v3.poly(sw)
    v3.dim((-61.9, SLANT), (61.9, SLANT), 30, None, "h")
    v3.dim((61.9, 0), (61.9, SLANT), -40, f"{mmi(SLANT, 1)}", "v")
    v3.note(0, SLANT / 2, [f"slope {math.degrees(math.atan2(35, Z_FL_BOT - ZB)):.1f}° from vertical", "bottom edge sits on the tube at y = ±25"], 13, "middle")
    dxf_profile(str(DXF / "P1-212-103_side_wall"), sw, text="P1-212-103 SIDE WALL x2 14ga 316L")
    # inlet flange 104 1:2
    s2 = SC(2)
    v4 = S.view(2050, 1100, s2, "P1-212-104 INLET FLANGE (1:2) · 6 mm 316L", (1820, 640))
    of = rrect(200, 200, 8)
    v4.poly(of); v4.poly(rrect(120, 120, 3))
    for sx in (-1, 1):
        for sy in (-1, 1):
            v4.circle(sx * 80, sy * 80, 5.5)
    v4.cmark(0, 0, 100)
    v4.dim((-100, 100), (100, 100), 30, None, "h"); v4.dim((-80, -100), (80, -100), -30, "160 [6.299] BOLT SQ", "h")
    v4.note(0, -10, "OPENING 120 [4.724] SQ, R3", 12, "middle")
    v4.leader((80 + 5.5 * 0.7, 80 + 5.5 * 0.7), (130, 130), ["4 x Ø11 [.433] THRU", "match bin P1-211 flange"], anchor="start")
    dxf_profile(str(DXF / "P1-212-104_inlet_flange"), [of, rrect(120, 120, 3)], holes=[(sx * 80, sy * 80, 5.5) for sx in (-1, 1) for sy in (-1, 1)], text="P1-212-104 INLET FLANGE 6mm 316L")
    # end flange blank 105
    v5 = S.view(2900, 1100, s2, "P1-212-105 END FLANGE BLANK (1:2) · 12 mm 316L", (2700, 640))
    v5.poly(rrect(EF["sq"], EF["sq"], 5)); v5.circle(0, 0, 25)
    v5.dim((-55, 55), (55, 55), 30, "110 [4.331] (+2 machine)", "h")
    v5.dia(0, 0, 25, 225, (-60, -80), "Ø50 PILOT (bore after weld)")
    v5.note(0, -100, ["socket Ø63.6 x 4 deep for the tube, machined BEFORE welding;", "face, recess and tap AFTER (see -100 view F)"], 12, "middle")
    dxf_profile(str(DXF / "P1-212-105_end_flange_blank"), rrect(EF["sq"] + 2, EF["sq"] + 2, 5), holes=[(0, 0, 25)], text="P1-212-105 END FLANGE BLANK 12mm 316L")
    # spout 106 + saddle template
    v6 = S.view(250, 2160, s1, "P1-212-106 SPOUT (1:1) + SADDLE TEMPLATE (wrap round the tube, 1:1)", (150, 1620))
    circ = math.pi * B_OD
    pts = [(circ * i / 72, -Z_SPOUT_END - R_O * abs(math.cos(2 * math.pi * i / 72))) for i in range(73)]
    tmpl = [(0, 0)] + pts + [(circ, 0)]
    v6.poly(tmpl)
    v6.dim((0, 0), (circ, 0), -30, f"{mmi(circ, 1)} = π x 63.5", "h")
    v6.dim((0, 0), (0, -Z_SPOUT_END - R_O), 40, None, "v")
    v6.dim((circ / 4, 0), (circ / 4, -Z_SPOUT_END), -30, None, "v")
    v6.note(circ + 40, 60, ["L(θ) = 132 - 31.75 |cos θ|", "θ from the tube axis direction", "cut from 2.5 in tube; length at the", "sides 132 [5.197], front/back 100.25"], 13)
    dxf_profile(str(DXF / "P1-212-106_spout_saddle_template"), tmpl, text="P1-212-106 SADDLE TEMPLATE print 1:1")
    # gasket 501 (on this sheet's cut list too)
    S.table(1500, 1700, [("CUT FILE", 380), ("PART", 120), ("MATERIAL", 300), ("QTY / FEEDER", 110)], [
        ("P1-212-102_end_wall_mm/_in.dxf", "102", "316L 14 ga", 2), ("P1-212-103_side_wall_mm/_in.dxf", "103", "316L 14 ga", 2),
        ("P1-212-104_inlet_flange_mm/_in.dxf", "104", "316L 6 mm", 1), ("P1-212-105_end_flange_blank_mm/_in.dxf", "105", "316L 12 mm", 1),
        ("P1-212-106_spout_saddle_template_mm/_in.dxf", "106", "paper template", 1), ("P1-212-501_inlet_gasket_mm/_in.dxf", "501", "FDA silicone 3 mm", 1)],
        "CUT FILES (dxf/)", fs=13, rh=22)
    S.save(DWG / "P1-212-101_barrel_parts.svg")


# ================================================================== 200 screw
def screw():
    c = calcs()
    S = sheet("P1-212-200", "SCREW: SHAFT, FLIGHT, WELDING", scale="1:2 · 2:1 · 1:1", material=SS316 + " shaft; flight 316 formed", finish=FIN_PC,
              mass=kg("P1-212-201", "P1-212-202"))
    s = SC(2)
    v = S.view(250 - X_S0 * s, 480, s, "P1-212-200 SCREW ASSEMBLY (1:2)", (150, 260))
    v.rect(X_S0, -S_D / 2, X_SP0 - X_S0, S_D); v.rect(X_SP0, -SPIGOT_D / 2, X_SP1 - X_SP0, SPIGOT_D)
    v.rect(X_F0, -S_OD / 2, X_F1 - X_F0, S_OD, "thin")
    sh_ga.flight_lines(v, X_F0, X_F1, S_OD / 2, "vis")
    v.centre(X_S0 - 30, 0, X_SP1 + 30, 0)
    v.dim((X_S0, -S_OD / 2), (X_SP1, -S_OD / 2), -70, f"{mmi(X_SP1 - X_S0)} ±0.5", "h")
    v.dim((X_S0, S_OD / 2), (X_F0, S_OD / 2), 40, None, "h", fs=12)
    v.dim((X_F0, S_OD / 2), (X_F1, S_OD / 2), 40, f"FLIGHT {mmi(X_F1 - X_F0)} ({(X_F1 - X_F0) / S_P:.1f} turns)", "h")
    v.dim((X_F1, -S_OD / 2), (X_SP1, -S_OD / 2), -30, None, "h", fs=12)
    v.dim((X_F0 + S_P * 3.25, -S_OD / 2), (X_F0 + S_P * 4.25, -S_OD / 2), -120, f"PITCH {mmi(S_P)}", "h")
    v.leader((300, S_OD / 2), (360, 120), [f"FLIGHT Ø{mmi(S_OD)} +0/-0.3, RIGHT HAND, t = {S_T:.0f}", "P1-215 formed; ends tapered over 1/4 turn, ground"], anchor="start")
    v.weld((500, S_D / 2), (600, -130), "fillet", "2", other="fillet", length="continuous", tail="W7 both sides")
    # shaft 201 detail 1:1 ends
    s1 = SC(0.5)
    vd = S.view(300 - X_S0 * s1, 1100, s1, "P1-212-201 SHAFT DRIVE END (2:1): SOCKET + SLOT", (150, 850))
    xs1 = X_S0 + 80
    vd.poly([(X_S0, -S_D / 2), (xs1, -S_D / 2), (xs1, S_D / 2), (X_S0, S_D / 2)], closed=False)
    vd.line(X_S0, -S_D / 2, X_S0, S_D / 2)
    vd.rect(X_S0, -SOCKET["d"] / 2, SOCKET["depth"], SOCKET["d"], "hid")
    vd.rect(X_S0, -SOCKET["slot_w"] / 2, SOCKET["slot_d"], SOCKET["slot_w"], "vis", "#fff")
    vd.circle(X_S0 + SOCKET["slot_d"] - SOCKET["slot_w"] / 2, 0, SOCKET["slot_w"] / 2, "thin")
    vd.centre(X_S0 - 10, 0, xs1 + 10, 0)
    vd.dim((X_S0, S_D / 2), (X_S0 + SOCKET["depth"], S_D / 2), 30, f"{mmi(SOCKET['depth'])} DEEP", "h", fs=12)
    vd.dim((X_S0, -S_D / 2), (X_S0 + SOCKET["slot_d"], -S_D / 2), -30, None, "h", fs=12)
    vd.dim((xs1, -S_D / 2), (xs1, S_D / 2), -30, f"Ø{mmi(S_D)} h9", "v", fs=12)
    vd.leader((X_S0 + 10, SOCKET["d"] / 2), (X_S0 + 60, 40), [f"Ø{mmi(SOCKET['d'], 1)} H9 BORE", "Ra 1.6, chamfer 1 x 45°"], anchor="start")
    vd.leader((X_S0 + 8, -SOCKET["slot_w"] / 2), (X_S0 + 30, -40), anchor="start", lines= [f"SLOT {mmi(SOCKET['slot_w'], 1)} +0.1/0 THRU BOTH WALLS", "full-round end R3.25, deburr"])
    vd.datum((X_S0 + 60, -S_D / 2), "B", (0, -1))
    vt = S.view(1150 - (X_SP0 - 60) * s1, 1100, s1, "P1-212-201 TAIL SPIGOT (2:1)", (1150, 850))
    vt.poly([(X_SP0 - 60, S_D / 2), (X_SP0, S_D / 2), (X_SP0, SPIGOT_D / 2), (X_SP1 - 1, SPIGOT_D / 2), (X_SP1, SPIGOT_D / 2 - 1), (X_SP1, -SPIGOT_D / 2 + 1),
             (X_SP1 - 1, -SPIGOT_D / 2), (X_SP0, -SPIGOT_D / 2), (X_SP0, -S_D / 2), (X_SP0 - 60, -S_D / 2)], closed=False)
    vt.centre(X_SP0 - 70, 0, X_SP1 + 10, 0)
    vt.dim((X_SP0, SPIGOT_D / 2), (X_SP1, SPIGOT_D / 2), 40, None, "h", fs=12)
    vt.dim((X_SP1, -SPIGOT_D / 2), (X_SP1, SPIGOT_D / 2), -30, f"Ø{mmi(SPIGOT_D)} f7", "v", fs=12)
    vt.fcf(X_SP0 + 5, -30, ["↗", "0.05", "B"])
    vt.finish((X_SP0 + 15, SPIGOT_D / 2), "0.8")
    # flight blank (alternate)
    sb = SC(1)
    vb = S.view(2650, 1000, sb, "P1-212-202 ALTERNATE: SECTIONAL FLIGHT BLANK (1:1), 20 per screw", (2350, 820))
    gap = c["cut"]
    a0, a1 = 90 + gap / 2, 90 + 360 - gap / 2
    blank = arcpts(0, 0, c["Ro"], a0, a1, 90) + arcpts(0, 0, c["Ri"], a1, a0, 90)
    vb.poly(blank)
    vb.cmark(0, 0, c["Ro"])
    vb.dia(0, 0, c["Ro"], 200, (-60, -50), f"Ø{mmi(2 * c['Ro'], 1)}")
    vb.dia(0, 0, c["Ri"], 20, (60, 45), f"Ø{mmi(2 * c['Ri'], 1)}")
    vb.angle((0, 0), c["Ro"] + 12, 90 - gap / 2 + 180 - 180 + 0, 90 + gap / 2, f"{gap:.1f}° GAP")
    dxf_profile(str(DXF / "P1-212-202_flight_blank"), blank, text="P1-212-202 FLIGHT BLANK x20 3mm 316")
    S.table(1500, 1270, [("QUANTITY", 360), ("VALUE", 300), ("NOTE", 640)], [
        ("Flight OD / ID / pitch / t", f"{S_OD:.0f} / {S_D:.0f} / {S_P:.0f} / {S_T:.0f}", "barrel ID 60.2: radial clearance 2.1 [.083]"),
        ("Helix length outer / inner per turn", f"{c['Lo']:.1f} / {c['Li']:.1f}", "√((πD)² + P²)"),
        ("Blank Ro / Ri / gap", f"{c['Ro']:.2f} / {c['Ri']:.2f} / {gap:.1f}°", "Ri = w·Li/(Lo-Li), w = 15.5; stretch on a 56-pitch jig"),
        ("Volume per turn (full / 40 % fill)", f"{c['vol_rev']:.3f} L / {c['q_rev']:.4f} L", "dosing table P1-212-900"),
        ("Screw mass", f"{c['mass_screw']:.1f} kg [{c['mass_screw'] * 2.2046:.1f} lb]", "one person lifts it out"),
    ], "SCREW DATA", fs=13, rh=22)
    S.notes(1500, 1430, 1000, [
        "Order the flight from P1-215 with ID 25.5 to slide on; fix the start 5 from the socket end, stretch to 56 pitch, tack every 1/2 turn, then weld W7 continuous both sides (GTAW ER316LSi, 2 fillet), grind smooth, no crevices.",
        "Straighten after welding: shaft TIR ≤ 0.3 [.012] and flight OD TIR ≤ 0.5 [.02] between centres B and spigot. Then turn the spigot Ø20 f7 to finish.",
        "Polish flight faces and shaft to Ra ≤ 0.8 µm; passivate; check the screw slides through the barrel by hand along its full length before fitting.",
        "Sectional blanks (DXF) are an alternate to the formed flight only: butt-weld 20 blanks, full penetration, ground both sides.",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-212-200_screw.svg")


# ================================================================== 300 drive parts
def drive():
    S = sheet("P1-212-300", "DRIVE END: HOUSING, DRIVE SHAFT, SPACERS", scale="2:1", material=SS316, finish="Ra 1.6 unless noted; bores Ra 0.8",
              mass=kg("P1-212-301", "P1-212-302", "P1-212-304"))
    s1 = SC(0.5)
    v = S.view(350 - X_H_REAR1 * s1, 730, s1, "P1-212-301 DRIVE HOUSING (2:1): upper half in section", (150, 100))
    top = [(X_H_FACE, HSG["seal_bore"] / 2), (X_H_FACE, HSG["spig_d"] / 2), (X_FL_OUT, HSG["spig_d"] / 2), (X_FL_OUT, HSG["collar_d"] / 2),
           (X_FL_OUT - HSG["collar_t"], HSG["collar_d"] / 2), (X_FL_OUT - HSG["collar_t"], HSG["body_d"] / 2), (X_H_REAR0, HSG["body_d"] / 2),
           (X_H_REAR0, HSG["rear_d"] / 2), (X_H_REAR1, HSG["rear_d"] / 2), (X_H_REAR1, HSG["brg_bore"] / 2), (X_BRG_A0, HSG["brg_bore"] / 2),
           (X_BRG_A0, 15), (X_H_FACE - HSG["seal_w"], 15), (X_H_FACE - HSG["seal_w"], HSG["seal_bore"] / 2)]
    v.hatch(top, "hA")
    outer = [(x, -y) for x, y in top[1:9]]
    v.poly([(X_H_FACE, 0)] + outer + [(X_H_REAR1, 0)], closed=False)
    for x0, x1, r in ((X_H_REAR1, X_BRG_A0, HSG["brg_bore"] / 2), (X_BRG_A0, X_H_FACE - HSG["seal_w"], 15), (X_H_FACE - HSG["seal_w"], X_H_FACE, HSG["seal_bore"] / 2)):
        v.line(x0, -r, x1, -r, "hid")
    v.rect(X_BRG_B1 - 1.85, HSG["brg_bore"] / 2, 1.85, 1.25, "thin", "#fff")
    v.rect(X_H_FACE - 0.6, 23, 0.6 + 0.01, 3.3, "thin", "#fff")
    v.centre(X_H_REAR1 - 8, 0, X_H_FACE + 8, 0)
    v.datum((X_BRG_A0 - 30, -HSG["brg_bore"] / 2), "A", (0, 1))
    v.dim((X_H_REAR1, HSG["rear_d"] / 2), (X_H_FACE, HSG["rear_d"] / 2), 110, f"{mmi(X_H_FACE - X_H_REAR1)}", "h")
    v.dim((X_FL_OUT, HSG["collar_d"] / 2), (X_H_FACE, HSG["collar_d"] / 2), 40, None, "h", fs=12)
    v.dim((X_FL_OUT, HSG["collar_d"] / 2), (X_FL_OUT - HSG["collar_t"], HSG["collar_d"] / 2), 40, None, "h", fs=12)
    v.dim((X_H_REAR0, HSG["rear_d"] / 2), (X_H_REAR1, HSG["rear_d"] / 2), 40, None, "h", fs=12)
    v.dim((X_H_FACE, -15), (X_H_FACE - HSG["seal_w"], -15), -150, f"SEAL {mmi(HSG['seal_w'])}", "h", fs=12)
    v.dim((X_BRG_A0, -21), (X_BRG_B1, -21), -260, f"{mmi(X_BRG_A0 - X_BRG_B1)} TO DIN 472 GROOVE", "h", fs=12)
    for d_, x_ in ((HSG["rear_d"], X_H_REAR1 - 4), (HSG["body_d"], -190.0), (HSG["collar_d"], X_FL_OUT - 4), (HSG["spig_d"], X_H_FACE + 3)):
        pass
    v.dim((X_H_REAR1, -HSG["rear_d"] / 2), (X_H_REAR1, HSG["rear_d"] / 2), 60, f"Ø{mmi(HSG['rear_d'])}", "v", fs=12)
    v.dim((-190, -HSG["body_d"] / 2), (-190, HSG["body_d"] / 2), 0.001, f"Ø{mmi(HSG['body_d'])}", "v", fs=12, ext=False)
    v.dim((X_FL_OUT - HSG["collar_t"], -HSG["collar_d"] / 2), (X_FL_OUT - HSG["collar_t"], HSG["collar_d"] / 2), 0.001, f"Ø{mmi(HSG['collar_d'])}", "v", fs=12, ext=False)
    v.leader((X_H_FACE, HSG["spig_d"] / 2 - 2), (X_H_FACE + 14, 50), [f"Ø{mmi(HSG['spig_d'])} f7 SPIGOT -0.030/-0.060"], anchor="start")
    v.leader((X_H_FACE, 25), (X_H_FACE + 14, 32), ["O-RING FACE GROOVE ID 46 / OD 52.6 ▽ 1.9", "for P1-243 46 x 2.5"], anchor="start")
    v.leader((X_H_FACE - 3, HSG["seal_bore"] / 2), (X_H_FACE + 14, 12), [f"Ø{mmi(HSG['seal_bore'])} H8 x {HSG['seal_w']:.0f} SEAL BORE +0.039/0", "Ra 0.8, lead-in 15° x 1"], anchor="start")
    v.leader((X_BRG_A1, HSG["brg_bore"] / 2), (X_BRG_A1 + 4, 44), [f"Ø{mmi(HSG['brg_bore'])} J7 BEARING BORE +0.014/-0.011, Ra 0.8"], anchor="start") if False else None
    v.leader((X_BRG_A1 + 10, -HSG["brg_bore"] / 2), (X_H_FACE + 14, -14), [f"Ø{mmi(HSG['brg_bore'])} J7 BEARING BORE +0.014/-0.011, Ra 0.8"], anchor="start")
    v.leader((X_BRG_B1 - 1, HSG["brg_bore"] / 2 + 1), (X_H_REAR1 + 20, 66), ["DIN 472 GROOVE Ø44.5 x 1.85"], anchor="start")
    v.leader((X_FL_OUT - 4, 40), (X_H_FACE + 14, 66), ["4 x Ø6.6 THRU PCD 80 at 45° (H2 to the end flange)"], anchor="start")
    v.leader((X_H_REAR1 + 5, -45), (X_H_REAR1 - 5, -66), ["4 x M6 - 6H ▽ 9 PCD 90 at 45°", "(lantern H3)"])
    v.fcf(X_H_FACE + 14, -32, ["◎", "Ø0.03", "A"]); v.note(X_H_FACE + 30, -32, "  spigot Ø70 + seal bore", 12)
    v.fcf(X_H_FACE + 14, -44, ["⟂", "0.02", "A"]); v.note(X_H_FACE + 30, -44, "  spigot face", 12)
    # drive shaft 2:1
    vs = S.view(300 - SHAFT["x_end"] * s1, 1480, s1, "P1-212-302 DRIVE SHAFT (2:1) · Ø25 316 bar", (150, 1170))
    vs.poly([(SHAFT["x_end"] + 1, -10), (SHAFT["x_tip"] - 1, -10), (SHAFT["x_tip"], -9), (SHAFT["x_tip"], 9), (SHAFT["x_tip"] - 1, 10), (SHAFT["x_end"] + 1, 10), (SHAFT["x_end"], 9), (SHAFT["x_end"], -9)])
    for g in (X_BRG_A0 + 1.3, X_BRG_B1):
        for sg in (-1, 1):
            vs.rect(g - 1.3, sg * 9.5, 1.3, sg * 0.5, "thin", "#fff")
    vs.rect(SHAFT["x_key1"], 10 - 3.5, SHAFT["x_key0"] - SHAFT["x_key1"], 3.5, "thin", "#eceff1")
    vs.circle(X_PIN, 0, 3); vs.centre(SHAFT["x_end"] - 6, 0, SHAFT["x_tip"] + 6, 0)
    vs.dim((SHAFT["x_end"], 10), (SHAFT["x_tip"], 10), 90, f"{mmi(SHAFT['x_tip'] - SHAFT['x_end'])} ±0.2", "h")
    vs.dim((X_PIN, -10), (SHAFT["x_tip"], -10), -40, None, "h", fs=12)
    vs.dim((SHAFT["x_key1"], 10), (SHAFT["x_key0"], 10), 40, "KEYWAY 32 [1.260]", "h", fs=12)
    vs.dim((SHAFT["x_end"], -10), (SHAFT["x_key1"], -10), -40, None, "h", fs=12)
    vs.dim((X_BRG_B1, -10), (X_BRG_A0, -10), -100, f"BEARING SEATS Ø20 k6, DIN 471 GROOVES {mmi(X_BRG_A0 - X_BRG_B1)} APART", "h", fs=12)
    vs.dim((X_H_FACE - 7, -10), (X_H_FACE, -10), -40, None, "h", fs=12)
    vs.dim((SHAFT["x_tip"], -10), (SHAFT["x_tip"], 10), -50, "Ø20 g6 / k6 / h9 (zones)", "v", fs=12)
    vs.leader((X_PIN, 3), (X_PIN + 6, 32), ["Ø6 N7 CROSS HOLE THRU (press pin H5, 2 proud each side)"], anchor="start")
    vs.leader((SHAFT["x_key1"] + 10, 10), (SHAFT["x_key1"] + 6, 32), ["KEYWAY 6 P9 x 3.5 deep, DIN 6885"], anchor="start")
    vs.leader((X_H_FACE - 3, 10), (X_H_FACE - 40, 32), ["LIP JOURNAL Ø20 h9, Ra 0.4, plunge ground"], anchor="end")
    vs.leader((X_BRG_B1 - 0.6, -10), (X_BRG_B1 - 12, -34), ["DIN 471 GROOVE Ø19 x 1.3 (2)"])
    # spacers 2:1
    vp = S.view(2950, 600, s1, "P1-212-304 SPACERS (2:1), section", (2600, 330))
    for (ro, ri, y0, lab) in ((HSG["brg_bore"] / 2, 18.5, 0, "OUTER: Ø42 g6 x Ø37 x 64"), (12.0, 10.05, -60, "INNER: Ø24 x Ø20.1 x 64")):
        for sg in (-1, 1):
            vp.hatch([(-32, y0 + sg * ri), (32, y0 + sg * ri), (32, y0 + sg * ro), (-32, y0 + sg * ro)], "hA")
        vp.centre(-38, y0, 38, y0)
        vp.note(0, y0 - ro - 6, lab, 13, "middle")
    vp.dim((-32, 21), (32, 21), 30, "64 [2.520] +0.05/0, PAIR TO ±0.01", "h", fs=12)
    S.table(2150, 1520, [("FEATURE", 260), ("SIZE", 120), ("LIMITS mm", 170), ("LIMITS in", 170), ("CHECK", 220)], [
        ("Seal bore", "Ø35 H8", "35.000 / 35.039", "1.3780 / 1.3795", "bore gauge"),
        ("Bearing bore", "Ø42 J7", "41.989 / 42.014", "1.6531 / 1.6541", "bore gauge"),
        ("Spigot", "Ø70 f7", "69.940 / 69.970", "2.7535 / 2.7547", "micrometer"),
        ("Shaft at bearings", "Ø20 k6", "20.002 / 20.015", ".7875 / .7880", "micrometer"),
        ("Shaft at lip", "Ø20 h9", "19.948 / 20.000", ".7854 / .7874", "Ra 0.4 check"),
        ("Shaft in socket", "Ø20 g6", "19.980 / 19.993", ".7866 / .7871", "slip in Ø20.2 H9"),
        ("Outer spacer OD", "Ø42 g6", "41.975 / 41.991", "1.6526 / 1.6532", "micrometer"),
    ], "LIMITS OF SIZE", fs=13, rh=22)
    S.save(DWG / "P1-212-300_drive_parts.svg")


# ================================================================== 306 tail parts
def tail():
    S = sheet("P1-212-306", "TAIL END CAP AND BUSH", scale="2:1", material=SS316 + " cap; UHMW-PE FDA bush", finish="Product side Ra 0.8; TC face per ASME BPE DT-7",
              mass=kg("P1-212-306", "P1-212-307"))
    s = SC(0.5)
    v = S.view(500, 900, s, "P1-212-306 TAIL END CAP (2:1), half section", (200, 420))
    u = lambda x: x - X_TAIL
    top = [(0, CAP["bush_od"] / 2), (0, FER["fl_od"] / 2 - 4), (2, FER["fl_od"] / 2), (8, FER["fl_od"] / 2), (10, FER["fl_od"] / 2 - 6), (10, CAP["boss_d"] / 2),
           (CAP["boss_l"], CAP["boss_d"] / 2), (CAP["boss_l"], 0), (CAP["bush_l"] + 1, 0), (CAP["bush_l"], CAP["bush_od"] / 2)]
    v.hatch(top, "hA")
    v.poly([(x, -y) for x, y in top], closed=False)
    v.line(0, -CAP["bush_od"] / 2, 0, -(FER["fl_od"] / 2 - 4))
    v.rect(0, -CAP["bush_od"] / 2, CAP["bush_l"], CAP["bush_od"], "hid")
    v.centre(-10, 0, CAP["boss_l"] + 10, 0)
    v.datum((CAP["boss_l"] / 2 + 10, -CAP["boss_d"] / 2), "C", (0, -1))
    v.dim((0, FER["fl_od"] / 2), (CAP["boss_l"], FER["fl_od"] / 2), 40, None, "h")
    v.dim((0, -FER["fl_od"] / 2), (CAP["bush_l"], -FER["fl_od"] / 2), -40, f"{mmi(CAP['bush_l'])} DEEP", "h")
    v.dim((CAP["boss_l"], -CAP["boss_d"] / 2), (CAP["boss_l"], CAP["boss_d"] / 2), -60, None, "v")
    v.dim((-5, -FER["fl_od"] / 2), (-5, FER["fl_od"] / 2), 60, f"Ø{mmi(FER['fl_od'])} TC 2.5 in", "v")
    v.leader((5, CAP["bush_od"] / 2), (-20, 30), [f"Ø{mmi(CAP['bush_od'])} H7 BUSH BORE (blind)", "+0.021/0, coaxial Ø0.05 to the TC spigot"])
    v.leader((1, FER["fl_od"] / 2 - 10), (-20, 46), ["TC face + gasket groove per DT-7 2.5 in", "(copy a 16AMP-2.5 heavy end cap)"])
    v.finish((CAP["boss_l"], CAP["boss_d"] / 2 - 5), "1.6")
    vb = S.view(2000, 900, s, "P1-212-307 TAIL BUSH (2:1), UHMW-PE FDA", (1750, 420))
    vb.hatch([(0, CAP["bush_id"] / 2), (CAP["bush_l"], CAP["bush_id"] / 2), (CAP["bush_l"], CAP["bush_od"] / 2), (0, CAP["bush_od"] / 2)], "hC")
    vb.hatch([(0, -CAP["bush_id"] / 2), (CAP["bush_l"], -CAP["bush_id"] / 2), (CAP["bush_l"], -CAP["bush_od"] / 2), (0, -CAP["bush_od"] / 2)], "hC")
    vb.centre(-10, 0, CAP["bush_l"] + 10, 0)
    vb.dim((0, CAP["bush_od"] / 2), (CAP["bush_l"], CAP["bush_od"] / 2), 30, None, "h")
    vb.dim((CAP["bush_l"], -CAP["bush_od"] / 2), (CAP["bush_l"], CAP["bush_od"] / 2), -40, "Ø30.15 [1.187] +0.05/0 (press 0.15)", "v")
    vb.dim((-2, -CAP["bush_id"] / 2), (-2, CAP["bush_id"] / 2), 40, "Ø20.30 [.799] +0.10/0 AFTER PRESS", "v")
    S.notes(1500, 1250, 1000, [
        "Cap: turn from Ø85 316 bar; the TC face and 2.5 in clamp taper must match ASME BPE DT-7 (check with a standard ferrule and gasket: no gap at the clamp).",
        "Press the bush in flush, then ream to Ø20.30-20.40. Clearance on the Ø20 f7 spigot 0.32-0.46 (UHMW swells and creeps; this runs dry at ≤ 150 rpm).",
        "Replace the bush when the screw tail drops more than 1 [.04] (ITP maintenance M2). Keep a spare bush per 3 feeders.",
        "Clamp: hex-nut 13MHHS only. The cap is the guard over the screw end: removing it needs a tool and the isolator locked off.",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-212-306_tail_parts.svg")


# ================================================================== 400 lantern, guard, gasket
def lantern():
    S = sheet("P1-212-400", "LANTERN WELDMENT, COUPLING GUARD, INLET GASKET", scale="1:2 · 1:1", material=SS304 + " (non-contact); gasket FDA silicone",
              finish=FIN_NPC, mass=kg("P1-212-400", "P1-212-404"))
    s = SC(1)
    t = LANT["t"]
    v = S.view(450 - (X_GM) * s, 750, s, "P1-212-400 LANTERN (1:1) side view", (150, 470))
    xf0, xr1 = X_H_REAR1 - t, X_GM + t
    v.rect(xf0, -LANT["front_sq"] / 2, t, LANT["front_sq"], fill="#f4f6f8")
    v.rect(X_GM, -LANT["rear_sq"] / 2, t, LANT["rear_sq"], fill="#f4f6f8")
    v.rect(xr1, 55 - t, xf0 - xr1, t, fill="#eef1f3"); v.rect(xr1, -55, xf0 - xr1, t, fill="#eef1f3")
    v.centre(X_GM - 15, 0, X_H_REAR1 + 15, 0)
    v.datum((xf0 + t, -40), "D", (1, 0))
    v.dim((X_GM, LANT["rear_sq"] / 2), (X_H_REAR1, LANT["rear_sq"] / 2), 30, f"{mmi(X_H_REAR1 - X_GM)} ±0.1", "h")
    v.dim((xr1, 55), (xf0, 55), 70, f"BARS {mmi(xf0 - xr1)}", "h")
    v.dim((X_GM, -LANT["rear_sq"] / 2), (X_GM, LANT["rear_sq"] / 2), 50, None, "v")
    v.dim((X_H_REAR1, -55), (X_H_REAR1, 55), -40, "110 [4.331]", "v")
    v.weld((xr1 + 1, 55), (xr1 + 30, 100), "fillet", "4", other="fillet", tail="W8 (8 places)")
    v.fcf(X_GM - 40, -80, ["∥", "0.1", "D"])
    v.note(X_GM - 40, -92, "rear face to D", 12)
    v.leader((X_GM + 4, -30), (X_GM + 30, -100), ["Ø80 H8 SPIGOT BORE (machine after welding,", "coaxial Ø0.05 to the PCD 90 holes)"], anchor="start")
    vf = S.view(1500, 750, s, "FRONT PLATE (from the housing)", (1300, 500))
    vf.poly(rrect(110, 110, 4)); vf.circle(0, 0, 26)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        vf.circle(45 * math.cos(a), 45 * math.sin(a), 3.3)
    vf.circle(0, 0, 45, "cen"); vf.cmark(0, 0, 55)
    vf.dia(0, 0, 26, 200, (-80, -70), "Ø52 [2.047]")
    vf.leader((45 * 0.707 + 2, 45 * 0.707 + 2), (60, 70), ["4 x Ø6.6 THRU PCD 90 at 45°"], anchor="start")
    vr = S.view(2050, 750, s, "REAR PLATE (from the motor)", (1800, 450))
    vr.poly(rrect(140, 140, 5)); vr.circle(0, 0, 40)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        vr.circle(50 * math.cos(a), 50 * math.sin(a), 3.3)
    vr.circle(0, 0, 50, "cen"); vr.cmark(0, 0, 70)
    vr.dia(0, 0, 40, 200, (-100, -85), "Ø80 H8 [3.150] +0.046/0")
    vr.leader((50 * 0.707 + 2, 50 * 0.707 + 2), (75, 85), ["4 x Ø6.6 THRU PCD 100 at 45°", "= NORD B14 C120 (confirm)"], anchor="start")
    for st, pts, holes in (("P1-212-401_front_plate", rrect(110, 110, 4), [(0, 0, 26)] + [(45 * math.cos(math.radians(45 + 90 * k)), 45 * math.sin(math.radians(45 + 90 * k)), 3.3) for k in range(4)]),
                           ("P1-212-402_rear_plate", rrect(140, 140, 5), [(0, 0, 38)] + [(50 * math.cos(math.radians(45 + 90 * k)), 50 * math.sin(math.radians(45 + 90 * k)), 3.3) for k in range(4)]),
                           ("P1-212-403_bar", [(-45, -51.5), (45, -51.5), (45, 51.5), (-45, 51.5)], [(0, sy * 30, 2.1) for sy in (-1, 1)])):
        dxf_profile(str(DXF / st), pts, holes=holes, text=st + (" 8mm 304 (bore Ø80 H8 after weld)" if "rear" in st else " 8mm 304"))
    # guard flat pattern
    vg = S.view(400, 1650, s, "P1-212-404 GUARD x2 FLAT (1:1) · 1.5 mm 304 perforated Ø5 on 8 stagger", (150, 1380))
    gw, gh, fl = 74.0, 94.0, 12.0
    gp = [(-gw / 2, -gh / 2 - fl), (gw / 2, -gh / 2 - fl), (gw / 2, gh / 2 + fl), (-gw / 2, gh / 2 + fl)]
    vg.poly(gp)
    for sy in (-1, 1):
        vg.line(-gw / 2, sy * gh / 2, gw / 2, sy * gh / 2, "bend"); vg.circle(0, sy * (gh / 2 + 6), 2.75)
    for i in range(-4, 5):
        for j in range(-5, 6):
            x, y = i * 8 + (4 if j % 2 else 0), j * 8 * 0.866
            if abs(x) < gw / 2 - 5 and abs(y) < gh / 2 - 5:
                vg.circle(x, y, 2.5, "thin")
    vg.dim((-gw / 2, gh / 2 + fl), (gw / 2, gh / 2 + fl), 30, None, "h")
    vg.dim((gw / 2, -gh / 2 - fl), (gw / 2, gh / 2 + fl), -30, None, "v")
    vg.note(gw / 2 + 50, 0, ["2 bends 90° UP 10 [.39] flanges", "(BEND lines), K 0.4, inside R1.5", "Ø5.5 holes for M5 (H9) into the bars", "reach: Ø5 holes ≥ 20 from the coupling", "(ISO 13857 Table 4)"], 13)
    dxf_profile(str(DXF / "P1-212-404_guard"), gp, holes=[(0, sy * (gh / 2 + 6), 2.75) for sy in (-1, 1)], bends=[((-gw / 2, sy * gh / 2), (gw / 2, sy * gh / 2)) for sy in (-1, 1)],
                text="P1-212-404 GUARD x2 1.5mm 304 PERF Ø5")
    # gasket 501
    vk = S.view(1300, 1650, SC(2), "P1-212-501 INLET GASKET (1:2) · 3 mm FDA silicone 60A", (1150, 1380))
    gk = [rrect(200, 200, 8), rrect(120, 120, 3)]
    vk.poly(gk[0]); vk.poly(gk[1])
    for sx in (-1, 1):
        for sy in (-1, 1):
            vk.circle(sx * 80, sy * 80, 5.5)
    vk.dim((-100, 100), (100, 100), 30, None, "h"); vk.dim((-80, -100), (80, -100), -30, "160 [6.299]", "h")
    dxf_profile(str(DXF / "P1-212-501_inlet_gasket"), gk, holes=[(sx * 80, sy * 80, 5.5) for sx in (-1, 1) for sy in (-1, 1)], text="P1-212-501 GASKET 3mm FDA silicone")
    S.notes(2000, 1350, 900, [
        "Lantern: tack plates to the bars on a fixture with a Ø20 pin through both centres, weld W8 (GTAW 4 fillet both sides of each bar end), then machine the Ø80 H8 bore and face the rear plate parallel to D within 0.1.",
        "Bars carry tapped M5 holes 2 per bar (from DXF P1-212-403 pilot Ø4.2) for the guards.",
        "Alignment of gearmotor to drive shaft is set by the spigots: no shims. Coupling gap 1.6 [1/16 in] per Lovejoy.",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-212-400_lantern_guard_gasket.svg")


if __name__ == "__main__":
    weldment(); parts_flat(); screw(); drive(); tail(); lantern()
