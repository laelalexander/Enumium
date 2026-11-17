"""P1-301-001 general arrangement, -002 longitudinal section with seal/bearing detail, -003 cross section."""
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

LO = X_LEG + LEG / 2          # 644.1 leg outer face
LI = X_LEG - LEG / 2          # 567.9
YO, YI = Y_LEG + LEG / 2, Y_LEG - LEG / 2   # 438.1, 361.9
Z_CVT = Z_FLTOP + 3 + 3       # cover top 1,989
GM = dict(x0=695.0, x1=865.0, z0=Z_AX - 150, z1=Z_AX + 110, mot_c=(780.0, Z_AX - 60), mot_r=95.0, mot_len=330.0)
PNL = dict(x0=LO + 16, x1=LO + 16 + 203, z0=895.0, z1=1505.0, w=508.0)


def front(v, hidden=True):
    """front elevation (viewer at -y): x right, z up."""
    v.line(-900, 0, 1000, 0, "thin")
    for sx in (-1, 1):
        x = sx * X_LEG
        v.rect(x - LEG / 2, 12, LEG, Z_RAIL - 15, fill="#fff")                 # front leg
        v.rect(x - FOOT / 2, 0, FOOT, 12)
        v.centre(x, -40, x, 120)
    v.rect(-LI, Z_RAIL - LEG, 2 * LI, LEG); v.rect(-LI, Z_LOW - LEG, 2 * LI, LEG)
    # trough
    v.rect(-L_IN / 2 - T_EP, Z_AX - (R_IN + T_SH + EP_OFF), L_IN + 2 * T_EP, R_IN + T_SH + EP_OFF + H_SIDE, fill="#fff")
    v.line(-L_IN / 2, Z_TB, L_IN / 2, Z_TB, "thin")
    v.rect(-FL_OUT_X / 2, Z_AX + H_SIDE, FL_OUT_X, T_FL, fill="#eee")
    for sx in (-1, 1):                                                          # lugs on the rails
        v.rect(sx * 300 - LUG["w"] / 2, Z_RAIL, LUG["w"], LUG["t"])
    # stuffing boxes, followers, bearings, shaft
    for sx in (-1, 1):
        a, b = sorted((sx * (L_IN / 2 + T_EP), sx * (L_IN / 2 + BOX["x_face"])))
        v.rect(a, Z_AX - 75, b - a, 150)
        a, b = sorted((sx * (L_IN / 2 + BOX["x_face"] + 10), sx * (L_IN / 2 + BOX["x_face"] + 22)))
        v.rect(a, Z_AX - 75, b - a, 150)
        a, b = sorted((sx * (BP["x_in"] + BP["t"]), sx * (BP["x_in"] + BP["t"] + 48)))
        v.rect(a, Z_AX - 87.5, b - a, 175, fill="#dde3ea")
    v.rect(X_FREE_END, Z_AX - D_SH / 2, X_SHOULDER - X_FREE_END, D_SH, "thin") if hidden else None
    v.rect(X_SHOULDER, Z_AX - D_DRV / 2, X_DRV_END - X_SHOULDER, D_DRV, "thin")
    v.centre(X_FREE_END - 40, Z_AX, X_DRV_END + 60, Z_AX)
    # gearmotor + motor (axis toward the viewer)
    v.rect(GM["x0"], GM["z0"], GM["x1"] - GM["x0"], GM["z1"] - GM["z0"], fill="#dde3ea")
    v.circle(*GM["mot_c"], GM["mot_r"], fill="#cfd8dc")
    v.note(GM["mot_c"][0], GM["mot_c"][1] - 8, "M", 18, "middle")
    # cover
    v.rect(-FL_OUT_X / 2 - 3, Z_FLTOP + 3, FL_OUT_X + 6, 3, fill="#eee")
    v.rect(-FL_OUT_X / 2 - 3, Z_FLTOP + 6 - 25, 3, 22); v.rect(FL_OUT_X / 2, Z_FLTOP + 6 - 25, 3, 22)
    v.rect(-413, Z_CVT, 606, 25)
    v.rect(330 - TC4_FER_OD / 2, Z_CVT + TC4_FER_L - 4, TC4_FER_OD, 4); v.rect(330 - TC4_OD / 2, Z_CVT, TC4_OD, TC4_FER_L - 4)
    # discharge ferrule + valve
    v.rect(-TC4_FER_OD / 2, Z_TB - TC4_FER_L, TC4_FER_OD, 4); v.rect(-TC4_OD / 2, Z_TB - TC4_FER_L + 4, TC4_OD, TC4_FER_L - 4)
    v.rect(-70, Z_TB - TC4_FER_L - 110, 140, 110, fill="#dde3ea"); v.rect(70, Z_TB - 145, 160, 110, fill="#cfd8dc")
    # level switch
    v.circle(-300, Z_AX + 200, 25.25); v.circle(-300, Z_AX + 200, 15, "thin")
    # panel
    v.rect(PNL["x0"], PNL["z0"], PNL["x1"] - PNL["x0"], PNL["z1"] - PNL["z0"], fill="#eceff1")
    v.note((PNL["x0"] + PNL["x1"]) / 2, (PNL["z0"] + PNL["z1"]) / 2, "CP-301", 15, "middle")
    # torque arm
    v.line(780, Z_AX - 150, 780, 1450, "thin"); v.rect(LO, 1400, 10, 100)


def ga():
    S = sheet("P1-301-001", "RIBBON BLENDER GENERAL ARRANGEMENT", scale="1:10", material="see item list", finish="see details",
              mass=f"{sum(MASS.values()) + 95:.0f} kg [{(sum(MASS.values()) + 95) * 2.2046:.0f} lb] empty incl. bought", sheet="2 of 22")
    s = SC(10)
    vf = S.view(1080, 1880, s, "FRONT ELEVATION (from the operator side)", (300, 960))
    front(vf)
    vf.dim((-LO, 0), (LO, 0), -70, f"FRAME {mmi(2 * LO)}", "h")
    vf.dim((X_FREE_END, Z_AX), (max(X_DRV_END, PNL["x1"]), Z_AX), -330, f"OVERALL {mmi(max(X_DRV_END, PNL['x1']) - X_FREE_END)}", "h")
    vf.dim((-X_LEG, 0), (X_LEG, 0), -125, f"LEG CENTRES {mmi(2 * X_LEG)} (anchors)", "h")
    vf.dim((-LO, 0), (-LO, Z_AX), 120, f"SHAFT AXIS {mmi(Z_AX)}", "v")
    vf.dim((-LO, 0), (-LO, Z_TB - TC4_FER_L - 110), 60, f"VALVE OUTLET {mmi(Z_TB - TC4_FER_L - 110, 0)}", "v")
    vf.dim((-L_IN / 2, 0), (-L_IN / 2, Z_CVT + 25), 260, f"TOP OF UPSTAND {mmi(Z_CVT + 25)}", "v")
    vf.dim((LO, 0), (LO, Z_RAIL), -60, f"RAIL TOP {mmi(Z_RAIL)}", "v")
    vf.dim((-FL_OUT_X / 2, Z_FLTOP), (FL_OUT_X / 2, Z_FLTOP), 90, f"FLANGE {mmi(FL_OUT_X)}", "h")
    vf.dim((0, Z_CVT), (330, Z_CVT), 50, f"{mmi(330)}", "h")
    vf.leader((330, Z_CVT + TC4_FER_L), (420, 2150), ["SCREW INLET 4 in TC (P1-224)", f"top {mmi(Z_CVT + TC4_FER_L, 0)}"])
    vf.leader((-110, Z_CVT + 25), (-250, 2190), ["BAG-DUMP OPENING 600 x 400 [23.62 x 15.75]", "grate P1-302 drops in"])
    vf.leader((-300, Z_AX + 200), (-760, 2060), ["HIGH LEVEL SWITCH P1-337", f"1-1/2 in TC at {mmi(Z_AX + 200)}"])
    vf.leader((0, Z_TB - TC4_FER_L - 110), (-330, 1150), ["DISCHARGE 4 in TC, valve P1-331", "sock to drum-top sifter P1-304"])
    vf.leader((-LI + 40, Z_LOW - 30), (-500, 520), ["FREE END OPEN: drum on dolly rolls in", f"under {mmi(BP['z0'])} bearing plate, {mmi(2 * YI)} between legs"])
    tags = [(1, (-200, Z_AX + 100), (-560, 2330)), (2, (150, Z_AX), (40, 2330)), (3, (200, Z_FLTOP + 5), (200, 2400)), (4, (-X_LEG, 900), (-830, 1000)),
            (5, (L_IN / 2 + BOX["x_face"] + 16, Z_AX + 75), (560, 2150)), (6, (BP["x_in"] + 36, Z_AX + 87), (690, 2050)), (7, GM["mot_c"], (930, 1950)),
            (9, (0, 1300), (-200, 1150)), (10, (400, Z_FLTOP - 10), (560, 2420)), (11, (-300, Z_AX + 200), (-500, 1950)), (12, (PNL["x0"] + 100, 1300), (1020, 1300)),
            (13, (-480, Z_FLTOP), (-640, 2280))]
    for n, at, b in tags:
        vf.tag(*b, n, at)

    # end view from the drive end (viewer at +x): screen right = +y
    ve = S.view(2000, 1880, s, "END VIEW (from the drive end)", (1780, 960))
    ve.line(-560, 0, 560, 0, "thin")
    for sy in (-1, 1):
        ve.rect(sy * Y_LEG - LEG / 2, 12, LEG, Z_RAIL - 15, fill="#fff"); ve.rect(sy * Y_LEG - FOOT / 2, 0, FOOT, 12)
        ve.rect(sy * Y_LEG - LEG / 2, Z_LOW - LEG, LEG, LEG)
        ve.rect(sy * Y_LEG - LEG / 2, Z_RAIL - LEG, LEG, LEG)
    ve.rect(-YI, Z_LOW - LEG, 2 * YI, LEG)
    ve.rect(-YI, BP["z0"], 2 * YI, BP["z1"] - BP["z0"])
    ve.rect(-87.5, Z_AX - 87.5, 175, 175, fill="#dde3ea")
    for dy in (-1, 1):
        for dz in (-1, 1):
            ve.circle(dy * 71.5, Z_AX + dz * 71.5, 9)
    ve.rect(-115, GM["z0"], 230, GM["z1"] - GM["z0"], fill="#dde3ea")
    ve.rect(-115 - GM["mot_len"], GM["mot_c"][1] - GM["mot_r"], GM["mot_len"], 2 * GM["mot_r"], fill="#cfd8dc")
    ve.rect(-PNL["w"] / 2, PNL["z0"], PNL["w"], PNL["z1"] - PNL["z0"], fill="#eceff1")
    ve.note(0, (PNL["z0"] + PNL["z1"]) / 2, "CP-301 door (E03)", 14, "middle")
    # trough behind (hidden)
    r = R_IN + T_SH + EP_OFF
    ve.arc(0, Z_AX, r, 180, 360, "hid"); ve.line(-r, Z_AX, -r, Z_AX + H_SIDE, "hid"); ve.line(r, Z_AX, r, Z_AX + H_SIDE, "hid")
    ve.rect(-FL_OUT_Y / 2, Z_AX + H_SIDE, FL_OUT_Y, T_FL); ve.rect(-FL_OUT_Y / 2 - 3, Z_FLTOP + 3, FL_OUT_Y + 6, 3)
    for sy in (-1, 1):
        ve.rect(min(sy * (R_IN + T_SH), sy * 430), Z_RAIL, 147, LUG["t"])
    ve.circle(FL_OUT_Y / 2 + 14, Z_FLTOP + 7, 10)
    ve.dim((-YO, 0), (YO, 0), -70, f"FRAME {mmi(2 * YO)}", "h")
    ve.dim((-YI, Z_LOW + 40), (YI, Z_LOW + 40), -40, f"CLEAR {mmi(2 * YI)} (drum dolly 640 [25.2])", "h")
    ve.dim((-Y_LEG, 0), (Y_LEG, 0), -125, f"LEG CENTRES {mmi(2 * Y_LEG)}", "h")
    ve.dim((-FL_OUT_Y / 2, Z_FLTOP), (FL_OUT_Y / 2, Z_FLTOP), 80, f"FLANGE {mmi(FL_OUT_Y)}", "h")
    ve.dim((YO, 0), (YO, BP["z0"]), -60, f"BEARING PLATE U/S {mmi(BP['z0'])}", "v")
    ve.dim((YO, 0), (YO, PNL["z1"]), -170, f"PANEL TOP {mmi(PNL['z1'])}", "v")
    ve.leader((FL_OUT_Y / 2 + 14, Z_FLTOP + 7), (520, 2150), ["HINGES (back)", "cover opens 105° to a stop"])

    # plan
    vp = S.view(1080, 600, s, None)
    S.text(300, 380, "PLAN (cover closed)", 20, bold=True)
    vp.rect(-FL_OUT_X / 2 - 3, -FL_OUT_Y / 2 - 3, FL_OUT_X + 6, FL_OUT_Y + 6, fill="#f5f5f5")
    vp.rect(-413, -203, 606, 406); vp.rect(-410, -200, 600, 400, "thin")
    vp.circle(330, 0, TC4_FER_OD / 2); vp.circle(330, 0, TC4_OD / 2 - 1.65, "thin")
    for sx in (-1, 1):
        for sy in (-1, 1):
            vp.rect(sx * X_LEG - LEG / 2, sy * Y_LEG - LEG / 2, LEG, LEG)
        vp.rect(sx * 300 - 60, FL_OUT_Y / 2 + 4, 120, 20)                       # hinges
    for x in (-350, 0, 350):
        vp.rect(x - 20, -FL_OUT_Y / 2 - 23, 40, 20)                              # latches
    for sy in (-1, 1):
        vp.rect(-LI, sy * Y_LEG - LEG / 2, 2 * LI, LEG, "hid")
    vp.rect(GM["x0"], -115, GM["x1"] - GM["x0"], 230, fill="#dde3ea"); vp.rect(GM["mot_c"][0] - GM["mot_r"], -115 - GM["mot_len"], 2 * GM["mot_r"], GM["mot_len"], fill="#cfd8dc")
    vp.rect(PNL["x0"], -PNL["w"] / 2, PNL["x1"] - PNL["x0"], PNL["w"], fill="#eceff1")
    vp.rect(-X_BRG - 24, -87.5, 48, 175, fill="#dde3ea"); vp.rect(X_FREE_END, -30, 49 - 0, 60, "thin")
    vp.centre(-760, 0, 900, 0)
    vp.note(-760, -470, "FRONT (operator side, latches)", 14, "start"); vp.note(-760, 470, "BACK (hinges)", 14, "start")
    vp.leader((400, -FL_OUT_Y / 2 - 3), (520, -560), ["INTERLOCK P1-332 at x = 400 [15.75]"])

    rows = [[str(n), t, d, str(q), src] for n, t, d, q, src in ITEMS]
    S.table(2480, 120, [("ITEM", 50), ("PART / TAG", 130), ("DESCRIPTION", 450), ("QTY", 45), ("DRAWING / SOURCE", 255)], rows, "ITEM LIST", 13, 23)
    S.notes(2480, 560, 930, [
        "Shaft turns CLOCKWISE seen from the drive end at 40 rpm: outer ribbons carry product to the centre (discharge), inner ribbons to the ends.",
        f"Working volume 6.0 cu ft [170 L]; total {D.calcs()['vol_total_l']:.0f} L; design batch {BATCH_L:.0f} L = {D.calcs()['batch_kg']:.0f} kg at 0.51 kg/L ({D.calcs()['fill'] * 100:.0f} % full).",
        f"Design torque {D.calcs()['torque_nm']:.0f} N·m at 40 rpm, 2 x for starting; drive 1.5 kW via VFD (soft start).",
        "Anchor the 4 feet with H4 after levelling: shaft axis level within 1 mm over its length.",
        "Free end has no lower cross rail so a 55 gal drum on dolly P1-309 rolls under the valve; keep it clear.",
        "Product contact: trough inside, agitator, cover underside, ferrules: 316L, #4 finish, welds ground flush.",
        "Lifting: sling the trough under the bowl or lift the whole machine by the top rails at the legs; never by the shaft or cover.",
        "Read with P1-301-002 (section and fits), -003 (assembly sequence), -600 (hardware) and E01..E04 (electrical)."], fs=14)
    S.save(DWG / "P1-301-001_GA.svg")



# ================================================================== -002 longitudinal section + drive-end detail
def ribbon_cuts(plane_angles=(0.0, 180.0)):
    """x positions where each ribbon crosses the vertical axial plane (theta = 0 top or 180 bottom)."""
    out = []
    for n, r in RIB.items():
        s = 1 if r["hand"] == "RH" else -1
        for tgt in plane_angles:
            for k in range(-3, 4):
                x = (tgt + 360 * k - r["ph"]) * r["p"] / (360 * s)
                if r["x0"] <= x <= r["x1"]:
                    dm = r["od"] - r["w"]
                    ax = r["t"] / math.cos(math.atan(r["p"] / (math.pi * dm)))
                    out.append((n, x, tgt, r["od"] / 2, r["w"], ax))
    return out


def seal_end(v, sx, rmax=999):
    """stuffing box, packing, follower, plate, bearing, shaft at one end, section in the plane y = 0 (z measured from the axis + Z_AX)."""
    xi = L_IN / 2
    f = lambda x: sx * x
    for sz in (1, -1):
        Z = lambda r: Z_AX + sz * r
        # end plate (cut)
        re = min(rmax, (R_IN + T_SH + EP_OFF if sx > 0 else RING["r_out"]) if sz < 0 else H_SIDE)
        v.hatch([(f(xi), Z(BOX["spig_d"] / 2)), (f(xi + T_EP), Z(BOX["spig_d"] / 2)), (f(xi + T_EP), Z(re)), (f(xi), Z(re))], "hA")
        if sx < 0:      # free end: shell end ring (108) behind the bolted plate (110), bolt on the radius
            v.hatch([(f(xi), Z(R_IN + T_SH)), (f(xi - RING["t"]), Z(R_IN + T_SH)), (f(xi - RING["t"]), Z(min(rmax, re))), (f(xi), Z(min(rmax, re)))], "hB")
        # stuffing box (cut)
        v.hatch([(f(xi), Z(32)), (f(xi + 10), Z(32)), (f(xi + 10), Z(40)), (f(xi + BOX["x_face"]), Z(40)), (f(xi + BOX["x_face"]), Z(75)),
                 (f(xi + T_EP), Z(75)), (f(xi + T_EP), Z(50)), (f(xi), Z(50))], "hB")
        # packing 4 rings
        for k in range(PACK["rings"]):
            v.hatch([(f(xi + 10 + 10 * k), Z(30)), (f(xi + 20 + 10 * k), Z(30)), (f(xi + 20 + 10 * k), Z(40)), (f(xi + 10 + 10 * k), Z(40))], "hS", "thin")
        # follower (cut): spigot 18 with 8 inside the bore, flange 12, 10 adjustment gap
        a = xi + BOX["x_face"] - 8
        v.hatch([(f(a), Z(31)), (f(a + 18), Z(31)), (f(a + 18), Z(31)), (f(a + 30), Z(31)), (f(a + 30), Z(75)), (f(a + 18), Z(75)), (f(a + 18), Z(40)), (f(a), Z(40))], "hA")
        # bearing plate (cut)
        v.hatch([(f(BP["x_in"]), Z(40)), (f(BP["x_in"] + BP["t"]), Z(40)), (f(BP["x_in"] + BP["t"]), Z(min(rmax, (BP["z1"] - Z_AX) if sz > 0 else (Z_AX - BP["z0"])))),
                 (f(BP["x_in"]), Z(min(rmax, (BP["z1"] - Z_AX) if sz > 0 else (Z_AX - BP["z0"]))))], "hB")
        # bearing (simplified ISO: rectangle with cross) + housing flange
        bx0, bx1 = X_BRG - 32.55, X_BRG + 32.55
        v.rect(min(f(bx0), f(bx1)), min(Z(30), Z(55)), abs(f(bx1) - f(bx0)), 25, "vis", "#fff")
        v.line(f(bx0), Z(30), f(bx1), Z(55), "thin"); v.line(f(bx0), Z(55), f(bx1), Z(30), "thin")
        v.hatch([(f(BP["x_in"] + BP["t"]), Z(55)), (f(BP["x_in"] + BP["t"] + 18), Z(55)), (f(BP["x_in"] + BP["t"] + 18), Z(87.5)), (f(BP["x_in"] + BP["t"]), Z(87.5))], "hC")
        v.rect(min(f(BP["x_in"] + BP["t"] + 18), f(BP["x_in"] + BP["t"] + 48)), min(Z(55), Z(68)), 30, 13, "vis")
        # stud (phantom, out of plane)
        v.line(f(xi + BOX["x_face"] - 20), Z(57.5), f(xi + BOX["x_face"] + 30), Z(57.5), "phan")


def section():
    S = sheet("P1-301-002", "SECTION A-A, SEAL AND BEARING DETAIL, SECTION B-B", scale="1:4, 1:2, 1:5", material="see item list", finish="see details",
              mass="-", sheet="3 of 22")
    s5 = SC(5); s4 = SC(4)
    v = S.view(140 + 700 * s4, 270 + 2060 * s4, s4, "SECTION A-A  (vertical plane through the shaft axis, seen from the front)  1:4", (120, 92))
    # shell bottom + port ferrule (cut)
    v.hatch([(-L_IN / 2, Z_TB), (-TC4_OD / 2, Z_TB), (-TC4_OD / 2, Z_TB + T_SH), (-L_IN / 2, Z_TB + T_SH)], "hA")
    v.hatch([(TC4_OD / 2, Z_TB), (L_IN / 2, Z_TB), (L_IN / 2, Z_TB + T_SH), (TC4_OD / 2, Z_TB + T_SH)], "hA")
    for sx in (-1, 1):
        x = sx * (TC4_OD / 2 - 0.8)
        v.hatch([(sx * (TC4_OD / 2 - 1.65), Z_TB + T_SH), (sx * TC4_OD / 2, Z_TB + T_SH), (sx * TC4_OD / 2, Z_TB - TC4_FER_L + 4), (sx * TC4_FER_OD / 2, Z_TB - TC4_FER_L + 4),
                 (sx * TC4_FER_OD / 2, Z_TB - TC4_FER_L), (sx * (TC4_OD / 2 - 1.65), Z_TB - TC4_FER_L)], "hB")
    # back wall (visible beyond): top edge, flange
    v.line(-L_IN / 2, Z_AX + H_SIDE, L_IN / 2, Z_AX + H_SIDE, "vis")
    v.line(-L_IN / 2, Z_AX, L_IN / 2, Z_AX, "thin")
    for sx in (-1, 1):
        v.hatch([(sx * L_IN / 2, Z_AX + H_SIDE), (sx * FL_OUT_X / 2, Z_AX + H_SIDE), (sx * FL_OUT_X / 2, Z_FLTOP), (sx * L_IN / 2, Z_FLTOP)], "hC")
        v.rect(min(sx * L_IN / 2, sx * FL_OUT_X / 2), Z_FLTOP, 50, 3, "thin", "#222")                     # gasket
        seal_end(v, sx)
    # cover (cut on y = 0): plate pieces either side of the opening and the inlet hole
    zc = Z_FLTOP + 3
    for a, b in ((-FL_OUT_X / 2 - 3, -410), (190, 279), (381, FL_OUT_X / 2 + 3)):
        v.hatch([(a, zc), (b, zc), (b, zc + 3), (a, zc + 3)], "hC")
    for x in (-413, 190):
        v.hatch([(x, zc + 3), (x + 3, zc + 3), (x + 3, zc + 28), (x, zc + 28)], "hC")
    for sx in (-1, 1):
        v.hatch([(sx * (FL_OUT_X / 2), zc + 3), (sx * (FL_OUT_X / 2 + 3), zc + 3), (sx * (FL_OUT_X / 2 + 3), zc - 22), (sx * (FL_OUT_X / 2), zc - 22)], "hC")
        x = 330 + sx * (TC4_OD / 2)
        v.hatch([(330 + sx * (TC4_OD / 2 - 1.65), zc + 3), (x, zc + 3), (x, zc + 3 + TC4_FER_L - 4), (330 + sx * TC4_FER_OD / 2, zc + 3 + TC4_FER_L - 4),
                 (330 + sx * TC4_FER_OD / 2, zc + 3 + TC4_FER_L), (330 + sx * (TC4_OD / 2 - 1.65), zc + 3 + TC4_FER_L)], "hB")
    # shaft (not sectioned), keyway, centre line
    v.rect(X_FREE_END, Z_AX - 30, X_SHOULDER - X_FREE_END, 60, "vis", "#fff"); v.rect(X_SHOULDER, Z_AX - 22.5, X_DRV_END - X_SHOULDER, 45, "vis", "#fff")
    v.line(KEY["x0"], Z_AX + 22.5 - KEY["t1"], KEY["x0"] + KEY["L"], Z_AX + 22.5 - KEY["t1"], "thin")
    v.centre(X_FREE_END - 40, Z_AX, X_DRV_END + 40, Z_AX)
    # ribbons cut by the plane and in-plane arms
    for n, x, tgt, ro, w, ax in ribbon_cuts():
        sz = 1 if tgt == 0 else -1
        v.hatch([(x - ax / 2, Z_AX + sz * (ro - w)), (x + ax / 2, Z_AX + sz * (ro - w)), (x + ax / 2, Z_AX + sz * ro), (x - ax / 2, Z_AX + sz * ro)], "hA" if n[0] == "O" else "hB")
    for a in D.arms():
        d = (a["ang"] + 180) % 360 - 180
        if abs(d) < 12 or abs(abs(d) - 180) < 12:
            sz = 1 if abs(d) < 12 else -1
            v.rect(a["x"] - a["d"] / 2, Z_AX + (30 if sz > 0 else -a["r1"]), a["d"], a["r1"] - 30, "vis", "#fff")
    # gearmotor and valve (phantom)
    v.poly([(GM["x0"], GM["z0"]), (GM["x1"], GM["z0"]), (GM["x1"], GM["z1"]), (GM["x0"], GM["z1"])], "phan")
    v.poly([(-70, Z_TB - TC4_FER_L), (70, Z_TB - TC4_FER_L), (70, Z_TB - TC4_FER_L - 110), (-70, Z_TB - TC4_FER_L - 110)], "phan")
    HIDC = "#607d8b"
    v.note(0, Z_TB - TC4_FER_L - 60, "P1-331", 13, "middle", HIDC)
    v.note(780, Z_AX + 40, "P1-333 (phantom)", 13, "middle", HIDC)
    # dimensions
    v.dim((-L_IN / 2, Z_TB + 3), (L_IN / 2, Z_TB + 3), -150, f"INSIDE {mmi(L_IN)}", "h")
    v.dim((-X_BRG, Z_TB), (X_BRG, Z_TB), -200, f"BEARING CENTRES {mmi(2 * X_BRG)}", "h")
    v.dim((X_FREE_END, Z_TB), (X_DRV_END, Z_TB), -250, f"SHAFT {mmi(X_DRV_END - X_FREE_END)}", "h")
    v.dim((-BP["x_in"], BP["z1"]), (BP["x_in"], BP["z1"]), 120, f"BEARING PLATES INSIDE {mmi(2 * BP['x_in'])}", "h")
    v.dim((-435, Z_AX + 275), (435, Z_AX + 275), 50, f"RIBBONS {mmi(870)}", "h")
    v.dim((-FL_OUT_X / 2, Z_FLTOP), (FL_OUT_X / 2, Z_FLTOP), 175, f"FLANGE {mmi(FL_OUT_X)}", "h")
    v.dim((X_DRV_END, Z_TB), (X_DRV_END, Z_AX), -90, f"{mmi(R_IN + T_SH)}", "v")
    v.dim((X_DRV_END, Z_AX), (X_DRV_END, Z_FLTOP), -90, f"{mmi(H_SIDE + T_FL)}", "v")
    v.leader((-L_IN / 2 + 8, Z_AX + 150), (-300, 1830), ["15 [.59] ribbon to end plate (both ends); free end plate bolted (P1-301-108)"])
    v.leader((TC4_OD / 2, Z_TB - 10), (250, 1300), ["4 in TC FERRULE, welded flush, see P1-301-100"])
    v.leader((-480, zc), (-380, 2090), ["GASKET 20 x 6 silicone, compressed to 3"])
    v.detail(560, Z_AX, 140, "B")
    S.text(120, 1180, "Hatching: A = 316L trough and follower, B = stuffing box, bearing plate and ferrules, C = sheet parts, cross = PTFE packing. Shaft, arms and bolts are not sectioned (ASME Y14.3).", 14)

    # ---- detail B 1:2 drive end
    s2 = SC(2)
    d = S.view(200 - 430 * s2, 1620 + Z_AX * s2, s2, "DETAIL B  DRIVE-END SEAL, BEARING AND DRIVE JOURNAL  1:2  (free end is the same without the journal)", (120, 1226))
    seal_end(d, 1, 120)
    d.rect(430, Z_AX - 30, X_SHOULDER - 430, 60, "vis", "#fff"); d.rect(X_SHOULDER, Z_AX - 22.5, X_DRV_END - X_SHOULDER, 45, "vis", "#fff")
    d.rect(KEY["x0"], Z_AX + 22.5 - KEY["t1"], KEY["L"], KEY["h"], "thin", "#e0e0e0")
    d.poly([(GM["x0"], Z_AX - 140), (GM["x1"], Z_AX - 140), (GM["x1"], Z_AX + 110), (GM["x0"], Z_AX + 110)], "phan")
    d.centre(430, Z_AX, 880, Z_AX)
    xi = L_IN / 2
    d.dim((xi, Z_AX - 75), (xi + BOX["x_face"], Z_AX - 75), -40, f"{mmi(BOX['x_face'])}", "h")
    d.dim((xi, Z_AX - 75), (xi + T_EP, Z_AX - 75), -80, f"{mmi(T_EP)}", "h")
    d.dim((xi + 10, Z_AX + 40), (xi + 50, Z_AX + 40), 55, "PACKING 4 x 10 sq", "h")
    d.dim((xi + BOX["x_face"], Z_AX + 75), (xi + BOX["x_face"] + 10, Z_AX + 75), 40, "GAP 10 [.39] adjust", "h")
    d.dim((BP["x_in"], Z_AX - 87), (BP["x_in"] + BP["t"], Z_AX - 87), -70, f"{mmi(BP['t'])}", "h")
    d.dim((BP["x_in"] + BP["t"], Z_AX + 55), (X_BRG, Z_AX + 55), 70, "A2 29 [1.14]", "h")
    d.dim((X_SHOULDER, Z_AX - 22.5), (X_DRV_END, Z_AX - 22.5), -150, f"JOURNAL {mmi(X_DRV_END - X_SHOULDER)}", "h")
    d.dim((KEY["x0"], Z_AX + 22.5), (KEY["x0"] + KEY["L"], Z_AX + 22.5), 80, f"KEYWAY {KEY['b']} N9 x {KEY['L']} [{fin(KEY['L'])}], t1 {KEY['t1']}", "h")
    d.dim((xi - 5, Z_AX - 30), (xi - 5, Z_AX + 30), 30, "Ø60 h7 [2.3622/2.3610]", "v")
    d.dim((xi + 5, Z_AX - 32), (xi + 5, Z_AX + 32), -15, "Ø64", "v", ext=False)
    d.dim((xi + 30, Z_AX - 40), (xi + 30, Z_AX + 40), -10, "Ø80 H8/f8", "v", ext=False)
    d.dim((xi + 54, Z_AX - 75), (xi + 54, Z_AX + 75), -200, "Ø150 [5.906]", "v")
    d.dim((xi + 4, Z_AX - 50), (xi + 4, Z_AX + 50), 80, "SPIGOT Ø100 f8 / PLATE Ø100 H9", "v")
    d.dim((X_DRV_END - 30, Z_AX - 22.5), (X_DRV_END - 30, Z_AX + 22.5), 30, "Ø45 j6 [1.7721/1.7714]", "v")
    d.leader((xi + BOX["x_face"] + 25, Z_AX - 57.5), (560, Z_AX - 215), ["4 x STUD M10 x 50 A4-70 (H2) on PCD 115 [4.528]", "tighten evenly, flats parallel to the box face"])
    d.leader((X_BRG, Z_AX + 30), (720, Z_AX + 172), ["SUCF212 (P1-334): 4 x M16 (H1) 120 N·m, A2 per maker", "set screws on the Ø60 after alignment"])
    d.leader((X_DRV_END, Z_AX), (880, Z_AX - 120), ["M16 retaining screw (H6) per NORD"])
    d.weld((xi + T_EP, Z_AX + 75), (xi + 25, Z_AX + 165), "fillet", "6", allround=True, tail="GTAW ER316L")
    d.weld((xi, Z_AX - 50), (xi + 60, Z_AX - 165), "fillet", "3", contour="flush", side="other", tail="inside, ground flush R3")

    # ---- section B-B (cross section at x = 0, looking toward the drive end): screen right = +y
    b = S.view(2500, 1720, s5, "SECTION B-B  (at the discharge, looking toward the drive end)  1:5", (2000, 800))
    r_o = R_IN + T_SH
    pts_out = [(-r_o, Z_AX + H_SIDE)] + [(r_o * math.cos(math.radians(a)), Z_AX + r_o * math.sin(math.radians(a))) for a in range(180, 361, 4)] + [(r_o, Z_AX + H_SIDE)]
    pts_in = [(R_IN, Z_AX + H_SIDE)] + [(R_IN * math.cos(math.radians(a)), Z_AX + R_IN * math.sin(math.radians(a))) for a in range(360, 179, -4)] + [(-R_IN, Z_AX + H_SIDE)]
    b.poly(pts_out + pts_in, "vis", True, "#37474f")
    for sy in (-1, 1):
        b.hatch([(sy * R_IN, Z_AX + H_SIDE), (sy * FL_OUT_Y / 2, Z_AX + H_SIDE), (sy * FL_OUT_Y / 2, Z_FLTOP), (sy * R_IN, Z_FLTOP)], "hC")
        b.rect(min(sy * R_IN, sy * (R_IN + 43)), Z_FLTOP, 43, 3, "thin", "#222")
        # lug beyond (visible) and rail (cut, hollow tube)
        b.poly([(sy * r_o, Z_RAIL + LUG["t"]), (sy * 430, Z_RAIL + LUG["t"]), (sy * 430, Z_RAIL), (sy * 355, Z_RAIL), (sy * 355, Z_RAIL - 20), (sy * r_o, Z_RAIL - 100)], "vis", True, "#fff")
        y0, y1 = sorted((sy * YI, sy * YO))
        b.hatch([(y0, Z_RAIL - LEG), (y1, Z_RAIL - LEG), (y1, Z_RAIL), (y0, Z_RAIL)], "hB")
        b.rect(y0 + LEG_T, Z_RAIL - LEG + LEG_T, LEG - 2 * LEG_T, LEG - 2 * LEG_T, "vis", "#fff")
        b.rect(sy * Y_LEG - 10.7, Z_RAIL - LEG + LEG_T, 21.4, LEG - 2 * LEG_T, "thin", "#e0e0e0")
        b.line(sy * Y_LEG, Z_RAIL + LUG["t"] + 25, sy * Y_LEG, Z_RAIL - LEG - 30, "phan")
        b.rect(sy * Y_LEG - LEG / 2, Z_RAIL - 380, LEG, 380 - LEG, "vis")
    b.circle(0, Z_AX, 30, "vis", "url(#hA)")
    b.circle(0, Z_AX, RIB["OL"]["od"] / 2, "phan"); b.circle(0, Z_AX, RIB["OL"]["od"] / 2 - RIB["OL"]["w"], "phan")
    b.circle(0, Z_AX, RIB["IL"]["od"] / 2, "phan"); b.circle(0, Z_AX, RIB["IL"]["od"] / 2 - RIB["IL"]["w"], "phan")
    for n in ("OR", "IR"):
        r = RIB[n]; th = math.radians(D.theta(n, 0.001)); tw = r["t"] / math.sin(math.atan(r["p"] / (math.pi * (r["od"] - r["w"]))))
        # screen right = +y; angle from top, CCW seen from +x -> seen from +x looking -x, +y is to the right... CCW about +x moves +z toward -y (left)
        def P(rr, dt):
            a = th + dt / rr
            return (-rr * math.sin(a), Z_AX + rr * math.cos(a))
        b.hatch([P(r["od"] / 2 - r["w"], -tw / 2), P(r["od"] / 2, -tw / 2), P(r["od"] / 2, tw / 2), P(r["od"] / 2 - r["w"], tw / 2)], "hA")
    b.hatch([(-TC4_OD / 2, Z_TB), (-TC4_OD / 2 + 1.65, Z_TB), (-TC4_OD / 2 + 1.65, Z_TB - TC4_FER_L), (-TC4_OD / 2, Z_TB - TC4_FER_L)], "hB")
    b.hatch([(TC4_OD / 2 - 1.65, Z_TB), (TC4_OD / 2, Z_TB), (TC4_OD / 2, Z_TB - TC4_FER_L), (TC4_OD / 2 - 1.65, Z_TB - TC4_FER_L)], "hB")
    zc = Z_FLTOP + 3
    b.hatch([(-FL_OUT_Y / 2 - 3, zc), (-200, zc), (-200, zc + 3), (-FL_OUT_Y / 2 - 3, zc + 3)], "hC")
    b.hatch([(200, zc), (FL_OUT_Y / 2 + 3, zc), (FL_OUT_Y / 2 + 3, zc + 3), (200, zc + 3)], "hC")
    for y in (-203, 200):
        b.hatch([(y, zc + 3), (y + 3, zc + 3), (y + 3, zc + 28), (y, zc + 28)], "hC")
    for sy in (-1, 1):
        b.hatch([(sy * FL_OUT_Y / 2, zc + 3), (sy * (FL_OUT_Y / 2 + 3), zc + 3), (sy * (FL_OUT_Y / 2 + 3), zc - 22), (sy * FL_OUT_Y / 2, zc - 22)], "hC")
    b.circle(FL_OUT_Y / 2 + 14, zc + 4, 10, "vis", "#fff"); b.circle(FL_OUT_Y / 2 + 14, zc + 4, 5, "vis")
    b.rect(-FL_OUT_Y / 2 - 35, zc - 30, 32, 40, "thin")
    b.note(-FL_OUT_Y / 2 - 40, zc - 60, "LATCH P1-338", 12, "end")
    b.centre(0, Z_TB - 60, 0, Z_FLTOP + 80); b.centre(-470, Z_AX, 470, Z_AX)
    b.dim((-R_IN, Z_AX + 120), (R_IN, Z_AX + 120), 0, f"INSIDE {mmi(W_IN)} (R{mmi(R_IN)})", "h", ext=False)
    b.dim((-FL_OUT_Y / 2, Z_FLTOP), (FL_OUT_Y / 2, Z_FLTOP), 110, f"FLANGE {mmi(FL_OUT_Y)}", "h")
    b.dim((-Y_LEG, Z_RAIL), (Y_LEG, Z_RAIL), 165, f"RAIL CENTRES {mmi(2 * Y_LEG)}", "h")
    b.dim((-460, Z_RAIL), (-460, Z_AX), 0, f"{mmi(Z_RAIL - Z_AX)}", "v")
    b.leader((0, Z_AX - RIB["OL"]["od"] / 2), (180, 1300), [f"OUTER RIBBON OD {mmi(550)}: 5 [.20] radial clearance", "set 4..6 with feelers, full length"])
    b.leader((-RIB["IL"]["od"] / 2 * 0.7, Z_AX - RIB["IL"]["od"] / 2 * 0.7), (-460, 1320), [f"INNER RIBBON OD {mmi(320)}"])
    b.leader((400, Z_RAIL + 5), (480, Z_RAIL + 210), ["LUG ON RAIL: M12 x 110 (H3) through", "crush sleeve, 70 N·m"])
    b.leader((FL_OUT_Y / 2 + 14, zc + 4), (430, 2120), ["HINGE Ø20 x 3 knuckles, pin Ø10 (H10)"])

    rows = [["Ø60 h7 shaft / SUCF212 insert", "60 -0.030/0", "insert bore per maker", "set screws after alignment"],
            ["Ø60 h7 shaft / box throat Ø64", "radial gap 2.0 [.079]", "-", "shaft must not touch: check with feelers"],
            ["Ø80 H8 box / Ø80 f8 follower", "+0.046/0 ; -0.030/-0.076", "clearance 0.030..0.122", "follower slides by hand"],
            ["Ø100 H9 end plate / Ø100 f8 box spigot", "+0.087/0 ; -0.036/-0.090", "clearance 0.036..0.177", "tack, check square, weld"],
            ["Ø45 j6 journal / gearmotor Ø45 H7", "+0.011/-0.005 ; +0.025/0", "-0.011..+0.030", "anti-seize (food-grade)"],
            ["Key 14 x 9 / shaft N9, hub JS9", "14 -0.043/0", "DIN 6885 A", "key 125 [4.92] long"],
            ["Packing 10 sq in 80/60 box", "4 rings, joints staggered 90°", "-", "run in: weep allowed 1st hour, then re-tighten"]]
    S.table(1880, 1160, [("FIT", 330), ("TOLERANCES", 300), ("RESULT", 220), ("ASSEMBLY", 340)], rows, "FITS AND CLEARANCES", 14, 25)
    S.notes(1880, 1390, 1190, ["Ribbon-to-trough clearance is set by the agitator OD grind and checked by turning the shaft by hand: 4..6 [.16..24] everywhere.",
                               "Shaft axis concentric with both stuffing-box throats within 0.5 [.02]: shift the bearings in their Ø17.5 holes before tightening H1.",
                               "Product zone ends at the box face; the 92 [3.6] gap to the bearing plate keeps bearing grease out and lets packing be changed without lifting the shaft.",
                               "All product-contact welds inside the trough: GTAW with ER316L, back-purged where full penetration, ground flush and blended R3 min, #4 finish."], fs=14)
    S.save(DWG / "P1-301-002_section.svg")


if __name__ == "__main__":
    ga()
    section()
