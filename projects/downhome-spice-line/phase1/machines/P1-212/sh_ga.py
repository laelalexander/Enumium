"""P1-212-001 general arrangement, -002 sections and drive / tail details."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

R_O, R_I = B_OD / 2, B_ID / 2
GM_R = 60.0
X_GM_END = X_GM - GM_LEN
LF, LR = X_H_REAR1, X_GM               # lantern front / rear plate outer faces


def flight_lines(v, x0, x1, r, k="thin", front=True):
    """screw flight edges in side view: helix projected (sinusoid) between x0..x1 at radius r."""
    n = int((x1 - x0) / 2)
    pts = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        th = 2 * math.pi * (x - X_F0) / S_P
        pts.append((x, r * math.cos(th)))
    # draw only the visible half (front: sin(th) > 0)
    seg = []
    for i, (x, z) in enumerate(pts):
        th = 2 * math.pi * (x - X_F0) / S_P
        vis = math.sin(th) > 0 if front else True
        if vis:
            seg.append((x, z))
        elif seg:
            if len(seg) > 1:
                v.poly(seg, k, closed=False)
            seg = []
    if len(seg) > 1:
        v.poly(seg, k, closed=False)


def side(v, section=False, screw=True):
    """side elevation (viewer at -y): x right (toward hopper), z up. section=True: cut on y = 0."""
    hat = "hA"
    # barrel
    if section:
        v.hatch([(X_TUBE0, R_I), (X_TUBE1, R_I), (X_TUBE1, R_O), (X_TUBE0, R_O)], "hC")
        v.hatch([(X_TUBE0, -R_O), (X_SPOUT - R_O, -R_O), (X_SPOUT - R_O, -R_I), (X_TUBE0, -R_I)], "hC")
        v.hatch([(X_SPOUT + R_O, -R_O), (X_TUBE1, -R_O), (X_TUBE1, -R_I), (X_SPOUT + R_O, -R_I)], "hC")
        v.rect(X_TUBE0, -R_I, X_TUBE1 - X_TUBE0, 2 * R_I, "thin")
        # inlet slot gap in the top wall
        v.rect(-INLET["lx"] / 2, R_I, INLET["lx"], B_T + 0.5, "vis", "#fff")
    else:
        v.rect(X_TUBE0, -R_O, X_TUBE1 - X_TUBE0, B_OD, fill="#fff")
    # end flange (drive) and tail ferrule
    v.rect(X_FL_OUT, -EF["sq"] / 2, T_EF, EF["sq"], fill="url(#hA)" if section else "#f4f6f8")
    if section:
        v.rect(X_FL_OUT, -R_I, T_EF, 2 * R_I, "thin", "#fff")
        v.rect(X_FL_OUT, -EF["recess"] / 2, EF["recess_d"], EF["recess"], "thin", "#fff")
    v.rect(X_TAIL - 8, -FER["fl_od"] / 2, 8, FER["fl_od"], fill="#f4f6f8")
    v.rect(X_TAIL - FER["L"], -R_O, FER["L"] - 8, B_OD, fill="#f4f6f8")
    # transition + inlet flange
    zt = Z_FL_BOT
    zb = math.sqrt(R_O ** 2 - 25 ** 2)
    v.poly([(-INLET["lx"] / 2 - TR_T, R_O - 2), (-INLET["lx"] / 2 - TR_T, zt), (INLET["lx"] / 2 + TR_T, zt), (INLET["lx"] / 2 + TR_T, R_O - 2)],
           fill="url(#hC)" if section else "#fff")
    if section:
        v.rect(-INLET["lx"] / 2, R_O - 2, INLET["lx"], zt - R_O + 2, "thin", "#fff")
    v.rect(-BIN_FL["sq"] / 2, Z_FL_BOT, BIN_FL["sq"], T_FL, fill="url(#hA)" if section else "#f4f6f8")
    if section:
        v.rect(-BIN_FL["open"] / 2, Z_FL_BOT, BIN_FL["open"], T_FL, "thin", "#fff")
    # spout
    if section:
        v.hatch([(X_SPOUT - R_O, -R_O), (X_SPOUT - R_I, -R_O), (X_SPOUT - R_I, Z_SPOUT_END), (X_SPOUT - R_O, Z_SPOUT_END)], "hC")
        v.hatch([(X_SPOUT + R_I, -R_O), (X_SPOUT + R_O, -R_O), (X_SPOUT + R_O, Z_SPOUT_END), (X_SPOUT + R_I, Z_SPOUT_END)], "hC")
    else:
        v.rect(X_SPOUT - R_O, Z_SPOUT_END, B_OD, Z_SPOUT_END * -1 - zb + 2, fill="#fff")
    # screw
    if screw:
        v.rect(X_S0, -S_D / 2, X_SP0 - X_S0, S_D, "thin", "#e3e7ea" if section else "none")
        v.rect(X_SP0, -SPIGOT_D / 2, X_SP1 - X_SP0, SPIGOT_D, "thin", "#e3e7ea" if section else "none")
        v.rect(X_F0, -S_OD / 2, X_F1 - X_F0, S_OD, "phan")
        flight_lines(v, X_F0, X_F1, S_OD / 2, "thin")
    # drive housing
    hs = "url(#hB)" if section else "#f4f6f8"
    v.rect(X_FL_OUT - HSG["collar_t"], -HSG["collar_d"] / 2, HSG["collar_t"], HSG["collar_d"], fill=hs)
    v.rect(X_H_REAR0, -HSG["body_d"] / 2, X_FL_OUT - HSG["collar_t"] - X_H_REAR0, HSG["body_d"], fill=hs)
    v.rect(X_H_REAR1, -HSG["rear_d"] / 2, HSG["rear_t"], HSG["rear_d"], fill=hs)
    v.rect(X_H_FACE - HSG["spig_h"], -HSG["spig_d"] / 2, HSG["spig_h"], HSG["spig_d"], fill=hs)
    if section:
        v.rect(X_H_REAR1, -HSG["brg_bore"] / 2, X_BRG_A0 - X_H_REAR1, HSG["brg_bore"], "thin", "#fff")
        v.rect(X_BRG_A0, -15, X_H_FACE - HSG["seal_w"] - X_BRG_A0, 30, "thin", "#fff")
        v.rect(X_H_FACE - HSG["seal_w"], -HSG["seal_bore"] / 2, HSG["seal_w"], HSG["seal_bore"], "thin", "#fff")
        for a0 in (X_BRG_A1, X_BRG_B1):                                      # bearings
            for sg in (-1, 1):
                v.rect(a0, sg * 10, HSG["brg_w"], sg * 11, "thin", "#c8d3dc")
                v.circle(a0 + 6, sg * 15.5, 3.6, "thin")
        for sg in (-1, 1):
            v.rect(X_BRG_B0, sg * 18, X_BRG_A1 - X_BRG_B0, sg * 3, "thin", "url(#hS)")      # outer spacer
            v.rect(X_BRG_B0, sg * 10, X_BRG_A1 - X_BRG_B0, sg * 4, "thin", "url(#hS)")      # inner spacer
            v.rect(X_H_FACE - HSG["seal_w"], sg * 10, HSG["seal_w"] - 1, sg * 7.5, "thin", "#90a4ae")   # lip seal
    # drive shaft
    v.rect(SHAFT["x_end"], -SHAFT["d"] / 2, SHAFT["x_tip"] - SHAFT["x_end"], SHAFT["d"], "vis", "#eef1f3" if section else "#fff")
    v.rect(X_PIN - 3, -12, 6, 24, "thin", "#90a4ae")
    # lantern
    v.rect(LF - LANT["t"], -LANT["front_sq"] / 2, LANT["t"], LANT["front_sq"], fill="#eef1f3")
    v.rect(LR, -LANT["rear_sq"] / 2, LANT["t"], LANT["rear_sq"], fill="#eef1f3")
    v.rect(LR + LANT["t"], 47, LF - LANT["t"] - LR - LANT["t"], 8, fill="#eef1f3")
    v.rect(LR + LANT["t"], -55, LF - LANT["t"] - LR - LANT["t"], 8, fill="#eef1f3")
    v.rect(-305, -17, 55, 34, "thin", "#cfd8dc")                       # coupling
    # gearmotor
    v.rect(X_GM - 110, -62, 100, 132, fill="#dde3ea")
    v.rect(X_GM_END, -GM_R, X_GM - 40 - X_GM_END, 2 * GM_R, fill="#dde3ea")
    v.rect(X_GM - 220, GM_R, 90, 40, fill="#cfd8dc")
    v.note((X_GM_END + X_GM) / 2 - 40, -6, "M  P1-216", 14, "middle")
    # tail cap + clamp
    v.rect(X_TAIL, -FER["fl_od"] / 2, 10, FER["fl_od"], fill="url(#hB)" if section else "#f4f6f8")
    v.rect(X_TAIL + 10, -CAP["boss_d"] / 2, CAP["boss_l"] - 10, CAP["boss_d"], fill="url(#hB)" if section else "#f4f6f8")
    if section:
        v.rect(X_TAIL, -CAP["bush_od"] / 2, CAP["bush_l"], CAP["bush_od"], "thin", "#fffde7")
        v.rect(X_TAIL, -CAP["bush_id"] / 2, CAP["bush_l"], CAP["bush_id"], "thin", "#fff")
    v.poly([(X_TAIL - 8, FER["fl_od"] / 2), (X_TAIL - 8, FER["fl_od"] / 2 + 10), (X_TAIL + 10, FER["fl_od"] / 2 + 10), (X_TAIL + 10, FER["fl_od"] / 2)], "thin", fill="#cfd8dc")
    v.poly([(X_TAIL - 8, -FER["fl_od"] / 2), (X_TAIL - 8, -FER["fl_od"] / 2 - 10), (X_TAIL + 10, -FER["fl_od"] / 2 - 10), (X_TAIL + 10, -FER["fl_od"] / 2)], "thin", fill="#cfd8dc")
    v.centre(X_GM_END - 30, 0, X_SP1 + 40, 0)
    v.centre(X_SPOUT, 40, X_SPOUT, Z_SPOUT_END - 40)
    v.centre(0, -40, 0, Z_FL_TOP + 40)


def ga():
    tot = sum(MASS.values())
    S = sheet("P1-212-001", "BIN SCREW FEEDER GENERAL ARRANGEMENT", scale="1:4 (plan, elevation) · 1:2 (end)", material="see item list", finish="see details",
              mass=f"{tot + 9.5:.1f} kg [{(tot + 9.5) * 2.2046:.0f} lb] incl. gearmotor 8 kg (est.)")
    s = SC(4)
    vf = S.view(800, 860, s, "ELEVATION (from the ring centre side, looking at the feeder)", (120, 470))
    # interfaces in phantom: bin outlet, bin flange, hopper lid + stub, sleeve
    vf.poly([(-300, 204 + 400), (-60, 204 + 6), (60, 204 + 6), (300, 204 + 400)], "phan", closed=False)
    vf.rect(-100, 204, 200, 6, "phan")
    vf.note(160, 330, ["BIN P1-211 (phantom)", "outlet flange 200 sq"], 13, color="#607d8b")
    vf.line(X_SPOUT - 200, Z_LID, X_SPOUT + 150, Z_LID, "phan")
    vf.rect(X_SPOUT - R_O, Z_LID, B_OD, 25, "phan")
    vf.rect(X_SPOUT - R_O - 3, Z_LID - 5, B_OD + 6, (Z_SPOUT_END + 30) - (Z_LID - 5), "phan")
    vf.note(X_SPOUT + 60, Z_LID - 30, "HOPPER LID P1-220 (phantom)", 13, color="#607d8b")
    side(vf)
    vf.dim((X_GM_END, 0), (X_SP1, 0), -160, f"OVERALL {mmi(X_SP1 + 10 - X_GM_END)} (to clamp)", "h")
    vf.dim((0, Z_FL_TOP), (X_SPOUT, Z_FL_TOP), 50, f"BIN TO SPOUT {mmi(X_SPOUT)} (= R1,250 - R280)", "h")
    vf.dim((X_FL_OUT, -EF['sq'] / 2), (0, -EF['sq'] / 2), -70, None, "h")
    vf.dim((0, -R_O), (X_TAIL, -R_O), -110, None, "h")
    vf.dim((X_GM_END, 0), (X_FL_OUT, 0), -110, None, "h")
    vf.dim((BIN_FL["sq"] / 2, 0), (BIN_FL["sq"] / 2, Z_FL_TOP), -30, f"{mmi(Z_FL_TOP)} + 3 GASKET", "v")
    vf.dim((X_SPOUT + R_O, 0), (X_SPOUT + R_O, Z_SPOUT_END), -40, None, "v")
    vf.dim((X_SPOUT + 170, Z_LID), (X_SPOUT + 170, 0), -10, f"LID {mmi(-Z_LID)}", "v")
    vf.leader((-60, Z_FL_TOP), (-600, 330), anchor="start", lines=["INLET FLANGE 200 sq x 6, 4 x Ø11 on 160 sq", "= bin outlet flange; gasket P1-212-501, 4 x M10 (H1) 25 N·m"])
    vf.leader((X_TAIL + 30, 22), (X_TAIL - 150, 190), ["TAIL CAP: 2.5 in TC, HEX-NUT CLAMP (tool)", "remove to pull the screw out (LOTO first)"])
    vf.leader((X_SPOUT, Z_SPOUT_END - 10), (X_SPOUT - 400, -260), ["SPOUT 2.5 in, plain end", "sleeve P1-214 to the lid stub"])
    vf.leader((X_GM - 200, GM_R + 40), (-600, 190), anchor="start", lines=["GEARMOTOR P1-216 0.25 kW", "terminal box up"])
    for n, at, to in [(1, (500, R_O), (500, 120)), (2, (300, S_OD / 2 - 5), (300, -110)), (3, (-180, 30), (-185, 150)), (8, (-290, -55), (-300, -150)),
                      (11, (-450, -60), (-470, -150)), (6, (X_TAIL + 30, -20), (X_TAIL + 60, -110)), (17, (X_SPOUT + 34, Z_LID + 60), (X_SPOUT + 120, Z_LID + 40)),
                      (15, (-280, 17), (-330, 120)), (10, (90, Z_FL_TOP), (180, Z_FL_TOP + 60))]:
        vf.tag(to[0], to[1], n, at)
    # plan
    vp = S.view(800, 1720, s, "PLAN (bin removed)", (120, 1500))
    vp.rect(X_TUBE0, -R_O, X_TUBE1 - X_TUBE0, B_OD, fill="#fff")
    vp.rect(-BIN_FL["sq"] / 2, -BIN_FL["sq"] / 2, BIN_FL["sq"], BIN_FL["sq"], fill="#f4f6f8")
    vp.rect(-BIN_FL["open"] / 2, -BIN_FL["open"] / 2, BIN_FL["open"], BIN_FL["open"], fill="#fff")
    vp.poly([(-60, -60), (-60, -25), (60, -25), (60, -60)], "thin", closed=False); vp.poly([(-60, 60), (-60, 25), (60, 25), (60, 60)], "thin", closed=False)
    vp.rect(-60, -25, 120, 50, "thin")
    flight_lines(vp, -55, 55, S_OD / 2, "thin")
    for sx in (-1, 1):
        for sy in (-1, 1):
            vp.circle(sx * 80, sy * 80, 5.5)
    vp.rect(X_FL_OUT, -EF["sq"] / 2, T_EF, EF["sq"], fill="#f4f6f8")
    vp.rect(X_FL_OUT - HSG["collar_t"], -HSG["collar_d"] / 2, HSG["collar_t"], HSG["collar_d"], fill="#f4f6f8")
    vp.rect(X_H_REAR0, -HSG["body_d"] / 2, X_FL_OUT - HSG["collar_t"] - X_H_REAR0, HSG["body_d"], fill="#f4f6f8")
    vp.rect(X_H_REAR1, -HSG["rear_d"] / 2, HSG["rear_t"], HSG["rear_d"], fill="#f4f6f8")
    vp.rect(LF - 8, -55, 8, 110, fill="#eef1f3"); vp.rect(LR, -70, 8, 140, fill="#eef1f3")
    vp.rect(LR + 8, -51.5, LF - 8 - LR - 8, 103, "thin", "url(#hS)")
    vp.rect(X_GM - 110, -62, 100, 124, fill="#dde3ea"); vp.rect(X_GM_END, -GM_R, X_GM - 40 - X_GM_END, 2 * GM_R, fill="#dde3ea")
    vp.circle(X_SPOUT, 0, R_O, "hid")
    vp.rect(X_TAIL - 8, -FER["fl_od"] / 2, 18, FER["fl_od"], fill="#f4f6f8"); vp.rect(X_TAIL + 10, -CAP["boss_d"] / 2, 30, CAP["boss_d"], fill="#f4f6f8")
    vp.centre(X_GM_END - 30, 0, X_SP1 + 40, 0)
    vp.dim((-BIN_FL["sq"] / 2, BIN_FL["sq"] / 2), (BIN_FL["sq"] / 2, BIN_FL["sq"] / 2), 30, None, "h")
    vp.dim((-80, -80), (80, -80), -60, "160 [6.299] BOLT SQ", "h")
    vp.dim((LR, 70), (LR, -70), 40, None, "v")
    vp.leader((LR + 40, 51), (LR + 100, 190), ["GUARD P1-212-404 both sides", "perforated Ø5, no reach to the coupling"])
    vp.leader((X_SPOUT, R_O), (X_SPOUT - 80, 160), ["Ø63.5 SPOUT under (hidden)", f"centre on R{R_INLET:.0f} of the hopper lid"])
    vp.note(X_SPOUT + 60, -90, ["TO HOPPER CENTRE →", "feeder axis is radial (bin angle)"], 13)
    # end view from the drive end at 1:2
    ve = S.view(2840, 760, SC(2), "VIEW C: from the drive end", (2600, 420))
    ve.rect(-BIN_FL["sq"] / 2, Z_FL_BOT, BIN_FL["sq"], T_FL, fill="#f4f6f8")
    ve.rect(-LANT["rear_sq"] / 2, -LANT["rear_sq"] / 2, LANT["rear_sq"], LANT["rear_sq"], fill="#eef1f3")
    ve.circle(0, 0, GM_R, fill="#dde3ea"); ve.rect(-45, GM_R, 90, 40, fill="#cfd8dc")
    for k in range(4):
        a = math.radians(45 + 90 * k)
        ve.circle(LANT["pcd_gm"] / 2 * math.cos(a), LANT["pcd_gm"] / 2 * math.sin(a), 3.3)
    ve.poly([(-60 - TR_T, Z_FL_BOT), (-25 - TR_T, 20), (25 + TR_T, 20), (60 + TR_T, Z_FL_BOT)], "hid", closed=False)
    ve.cmark(0, 0, 60)
    ve.dim((-LANT["rear_sq"] / 2, -LANT["rear_sq"] / 2), (LANT["rear_sq"] / 2, -LANT["rear_sq"] / 2), -30, None, "h")
    ve.dim((-BIN_FL["sq"] / 2, Z_FL_BOT + T_FL), (BIN_FL["sq"] / 2, Z_FL_BOT + T_FL), 30, None, "h")
    ve.dim((LANT["rear_sq"] / 2, 0), (LANT["rear_sq"] / 2, Z_FL_TOP), -60, None, "v")
    ve.leader((-60 - TR_T, Z_FL_BOT - 40), (-170, 150), ["TRANSITION (hidden)", "120 sq to 120 x 50 slot"])
    # tables
    S.table(1880, 1130, [("ITEM", 50), ("PART", 120), ("DESCRIPTION", 520), ("QTY", 45), ("SOURCE / DRAWING", 260)],
            [(i, p, d, q, src) for i, p, d, q, src in ITEMS], "ITEM LIST (per feeder; 9 feeders)", fs=13, rh=22)
    S.table(1880, 1640, [("INTERFACE", 300), ("VALUE", 340), ("SET BY", 355)],
            [("Bin outlet flange underside", "1,730 [68.11] AFF", "ring P1-210, bin P1-211"),
             ("Barrel axis", f"{mmi(Z_AXIS_FFL)} AFF (flange - 204)", "this drawing"),
             ("Spout bottom", f"{mmi(Z_AXIS_FFL + Z_SPOUT_END)} AFF", "this drawing"),
             ("Hopper lid top / stub top", "1,231 / 1,256 AFF", "P1-220 (stub 2.5 in x 25 in Ø70 port)"),
             ("Spout centre", "R280 from the hopper axis, on the bin radius", "lid ports 12 x on Ø560"),
             ("Drive end radius (motor fan cowl)", f"R{R_BIN - X_GM_END:.0f} from the hopper axis", "ring legs moved to 15° (P1-210 rev B)"),
             ("Ring beam above the motor", "2,210 AFF (gap 600 over the motor)", "P1-210")],
            "PLANT INTERFACES (DH-ASM-P1-001)", fs=13, rh=22)
    S.notes(1880, 1850, 1000, [
        "Feeder hangs from the bin outlet flange only. Net moment at the flange 26 N·m [19 lbf·ft] (drive end balances the barrel); see calc on P1-212-900.",
        "The screw is supported at both ends: drive pin in the socket (x = -93) and the UHMW tail bush. No bearing in the product.",
        "Cleaning: LOTO at isolator P1-248, open the tail clamp (tool), pull the screw out of the tail end. The drive end stays put.",
        "Rotation: screw is RIGHT HAND; motor turns CW seen from the motor fan end to carry product +x. Check before filling (P1-212-900 T14).",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-212-001_general_arrangement.svg")


def section():
    S = sheet("P1-212-002", "SECTION A-A, DRIVE END AND TAIL END DETAILS", scale="1:5 · 1:1 · 1:2", material="see item list", finish="see details", mass="-")
    va = S.view(620, 560, SC(5), "SECTION A-A (vertical plane through the screw axis)", (120, 300))
    side(va, section=True)
    va.cut((X_SPOUT - 120, 0), (X_SPOUT - 120, 0), "") if False else None
    va.leader((0, R_I + 5), (-200, 260), ["INLET SLOT 120 x 50 [4.72 x 1.97]"])
    va.leader((X_SPOUT, -R_O - 10), (X_SPOUT - 360, -230), ["DISCHARGE: flights stop at x = 1,000 (spout far edge)"])
    va.detail(-170, 0, 110, "D")
    va.detail(1060, 0, 60, "E")
    va.cut((0, 230), (0, -100), "B", (1, 0))
    # detail D drive end 1:1
    s1 = SC(1)
    vd = S.view(2700, 720, s1, "DETAIL D (1:1): DRIVE END", (1400, 330))
    vd.S.add(f'<clipPath id="cD"><rect x="1380" y="360" width="1560" height="700"/></clipPath>')
    # draw only x -300..-60 by using a clip group
    S.add('<g clip-path="url(#cD)">')
    side(vd, section=True)
    S.add('</g>')
    vd.dim((X_FL_OUT, 60), (X_FL_IN, 60), 30, None, "h")
    vd.dim((X_H_FACE, -45), (X_BRG_A0, -45), -40, None, "h", fs=12)
    vd.dim((X_BRG_A1, -45), (X_BRG_B0, -45), -40, f"SPACER {mmi(HSG['spacer'])}", "h", fs=12)
    vd.dim((X_S0, -30), (X_PIN, -30), -100, None, "h", fs=12)
    vd.dim((X_H_REAR1, 0), (X_H_REAR1, HSG["rear_d"] / 2), 50, None, "v", fs=12)
    vd.leader((X_H_FACE - 3, 16), (-60, 115), ["LIP SEAL P1-242 20x35x7 PTFE", "lip toward the product, grease-free"])
    vd.leader((X_H_FACE - 1.5, 25), (-30, 88), ["O-RING P1-243 46x2.5 in face groove"])
    vd.leader((X_BRG_A1 + 6, 15), (-200, 118), ["BEARINGS P1-241 W 6004-2RS1 (2)", "DIN 471 rings on the shaft, DIN 472 in the housing"])
    vd.leader((X_PIN, -12), (-20, -78), ["DRIVE PIN Ø6 x 24 (H5) in the screw slot 6.5 wide", "screw slides off the pin to the tail end"])
    vd.leader((-280, 17), (-300, 110), ["COUPLING P1-244 L-075 20/20"])
    vd.leader((X_FL_OUT - HSG["collar_t"] + 4, 40), (-150, -112), ["4 x M6 x 16 (H2) on PCD 80, 8 N·m"])
    vd.leader((X_H_REAR1 + 5, -45), (-270, -112), ["4 x M6 x 20 (H3) on PCD 90, 8 N·m"])
    vd.weld((X_FL_IN + 1, R_O), (-95, 62), "fillet", "2", other=None, allround=True, tail="tube to flange, outside")
    vd.weld((X_FL_IN, -R_I - 0.5), (-80, -60), "sq", "", allround=True, contour="flush", tail="inside: fuse + grind flush")
    # detail E tail 1:2
    s2 = SC(2)
    ve = S.view(1930 - 1030 * s1, 1560, s1, "DETAIL E (1:1): TAIL END, SCREW PULL-OUT", (1400, 1250))
    S.add('<clipPath id="cE"><rect x="1380" y="1270" width="1000" height="560"/></clipPath><g clip-path="url(#cE)">')
    side(ve, section=True)
    S.add('</g>')
    ve.dim((X_SP0, -CAP['bush_id'] / 2), (X_SP1, -CAP['bush_id'] / 2), -60, None, "h", fs=12)
    ve.dim((X_TAIL, 50), (X_TAIL + CAP["boss_l"], 50), 30, None, "h", fs=12)
    ve.dim((X_F1, -40), (X_TAIL, -40), -80, None, "h", fs=12)
    ve.leader((X_TAIL + 15, -12), (X_TAIL + 20, -70), ["TAIL BUSH P1-212-307 UHMW FDA", "Ø20.3 bore on the Ø20 f7 spigot"])
    ve.leader((X_TAIL, FER["fl_od"] / 2 + 8), (X_TAIL - 60, 75), ["CLAMP P1-247 13MHHS hex nut", "gasket P1-246 EPDM"])
    # section B-B through the inlet 1:2
    vb = S.view(3000, 1680, s2, "SECTION B-B (1:2) at the inlet", (2700, 1180))
    vb.hatch([(-R_O, 0)] + [(R_O * math.cos(math.radians(a)), R_O * math.sin(math.radians(a))) for a in range(180, 361, 6)] + [(R_O, 0)], "hC") if False else None
    for a0, a1 in ((math.degrees(math.asin(25 / R_O)), 180 - math.degrees(math.asin(25 / R_O))),):
        pass
    # tube ring minus the slot
    ang = math.degrees(math.asin(25 / R_O))
    outer = [(R_O * math.cos(math.radians(a)), R_O * math.sin(math.radians(a))) for a in [90 + ang + i * (360 - 2 * ang) / 60 for i in range(61)]]
    inner = [(R_I * math.cos(math.radians(a)), R_I * math.sin(math.radians(a))) for a in [90 + ang + i * (360 - 2 * ang) / 60 for i in range(61)]][::-1]
    vb.hatch(outer + inner, "hC")
    zb = math.sqrt(R_O ** 2 - 25 ** 2)
    for sg in (-1, 1):
        vb.hatch([(sg * 25, zb - 1), (sg * (25 + TR_T), zb - 1), (sg * (60 + TR_T), Z_FL_BOT), (sg * 60, Z_FL_BOT)], "hC")
    vb.hatch([(-100, Z_FL_BOT), (-60, Z_FL_BOT), (-60, Z_FL_TOP), (-100, Z_FL_TOP)], "hA"); vb.hatch([(60, Z_FL_BOT), (100, Z_FL_BOT), (100, Z_FL_TOP), (60, Z_FL_TOP)], "hA")
    vb.circle(0, 0, S_OD / 2, "thin"); vb.circle(0, 0, S_D / 2, "thin", "#e3e7ea")
    vb.cmark(0, 0, 35)
    vb.dim((-60, Z_FL_TOP), (60, Z_FL_TOP), 30, None, "h", fs=12)
    vb.dim((-25, 0), (25, 0), -110, "SLOT 50 [1.969]", "h", fs=12)
    vb.dim((100, Z_FL_BOT), (100, Z_FL_TOP), -30, None, "v", fs=12)
    vb.dim((R_O, 0), (R_O, Z_FL_BOT), -70, None, "v", fs=12)
    vb.leader((S_OD / 2 * 0.7, -S_OD / 2 * 0.7), (70, -80), [f"SCREW Ø{S_OD:.0f}, CLEARANCE {(B_ID - S_OD) / 2:.1f} RADIAL"], fs=12)
    vb.angle((60 + TR_T, Z_FL_BOT), 50, 270, 270 - math.degrees(math.atan2(35, Z_FL_BOT - zb)), f"{math.degrees(math.atan2(35, Z_FL_BOT - zb)):.1f}° from vertical")
    S.notes(120, 1840, 1150, [
        "Seal and bearing fits: housing seal bore Ø35 H8, bearing bore Ø42 J7, shaft Ø20 k6 at the bearings, Ø20 h9 Ra 0.4 at the lip (P1-212-300).",
        "Screw socket Ø20.2 H9 on the drive shaft Ø20 g6: slip fit, the screw pulls off by hand.",
        "Assemble bearings + spacers on the shaft first (DIN 471 rings), push into the housing from the rear, fit the DIN 472 ring, then the lip seal from the front over the chamfered tip.",
        "Food-grade grease only (NSF H1) on the O-ring and lip seal at assembly.",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-212-002_sections.svg")


if __name__ == "__main__":
    ga(); section()
