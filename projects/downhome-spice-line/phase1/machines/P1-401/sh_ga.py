"""P1-401-001 general arrangement, -002 sections and details."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

C = calcs()
SS = "#f4f6f8"
BLU = "#dfe7f1"
R_O = HOP["r"] + T14
R_RIM = R_O + RIM["w"]
Z_SRV0 = Z_HPT + BRIDGE["h"] + BRIDGE["t"]          # servo flange face
Z_SRV1 = Z_SRV0 + 162.0                             # servo top (with connector)
Z_GM1 = Z_HPT + 110 + 150


def rv(v, x0, x1, z0, z1, k="vis", fill="none", u=0.0):
    """rect in a view; u shifts the horizontal coordinate"""
    v.rect(x0 + u, z0, x1 - x0, z1 - z0, k, fill)


def revolved(v, sec=False, u=0.0, stage_k="jar-12", hid_above=None):
    """everything on the auger axis (same in front and side views); u = axis position along the view's horizontal axis"""
    # container (phantom) and tooling
    zs = Z_TOP + STAGE_POS[stage_k] + STAGE["t"]
    c = CONT[stage_k]
    v.rect(u - c["d"] / 2, zs, c["d"], c["h"], "phan")
    T_ = TOOL["J"]
    tube = [(u - T_["tube_od"] / 2, Z_OUT), (u + T_["tube_od"] / 2, Z_OUT), (u + T_["tube_od"] / 2, Z_TC - 25), (u + TC25["od"] / 2, Z_TC - 6),
            (u + TC25["fl"] / 2, Z_TC - 6), (u + TC25["fl"] / 2, Z_TC), (u - TC25["fl"] / 2, Z_TC), (u - TC25["fl"] / 2, Z_TC - 6), (u - TC25["od"] / 2, Z_TC - 6),
            (u - T_["tube_od"] / 2, Z_TC - 25)]
    v.poly(tube, "vis", True, "#eceff1")
    # clamp
    v.rect(u - TC25["fl"] / 2 - 6, Z_TC - 8, TC25["fl"] + 12, 16, "vis", "#cfd8dc")
    # hopper
    fer = [(u - TC25["fl"] / 2, Z_TC), (u + TC25["fl"] / 2, Z_TC), (u + TC25["fl"] / 2, Z_TC + 6), (u + TC25["od"] / 2, Z_TC + 6), (u + TC25["od"] / 2, Z_CONE0),
           (u - TC25["od"] / 2, Z_CONE0), (u - TC25["od"] / 2, Z_TC + 6), (u - TC25["fl"] / 2, Z_TC + 6)]
    v.poly(fer, "vis", True, SS)
    hop = [(u - HOP["r_lo"] - T14, Z_CONE0), (u + HOP["r_lo"] + T14, Z_CONE0), (u + R_O, Z_CYL0), (u + R_O, Z_RIM - RIM["w"]), (u + R_O + RIM["t"], Z_RIM - RIM["w"]),
           (u + R_O + RIM["t"], Z_RIM - RIM["t"]), (u + R_RIM, Z_RIM - RIM["t"]), (u + R_RIM, Z_RIM), (u - R_RIM, Z_RIM), (u - R_RIM, Z_RIM - RIM["t"]),
           (u - R_O - RIM["t"], Z_RIM - RIM["t"]), (u - R_O - RIM["t"], Z_RIM - RIM["w"]), (u - R_O, Z_RIM - RIM["w"]), (u - R_O, Z_CYL0)]
    if sec:
        for sg in (-1, 1):
            wall = [(u + sg * HOP["r_lo"], Z_CONE0), (u + sg * (HOP["r_lo"] + T14), Z_CONE0), (u + sg * R_O, Z_CYL0), (u + sg * R_O, Z_RIM),
                    (u + sg * HOP["r"], Z_RIM), (u + sg * HOP["r"], Z_CYL0)]
            v.poly(wall, "vis", True, "#90a4ae")
            v.hatch([(u + sg * R_O, Z_RIM - RIM["t"]), (u + sg * R_RIM, Z_RIM - RIM["t"]), (u + sg * R_RIM, Z_RIM), (u + sg * R_O, Z_RIM)], "hC")
            v.hatch([(u + sg * R_O, Z_RIM - RIM["w"]), (u + sg * (R_O + RIM["t"]), Z_RIM - RIM["w"]), (u + sg * (R_O + RIM["t"]), Z_RIM), (u + sg * R_O, Z_RIM)], "hC")
        v.line(u - HOP["r"], Z_CYL0, u + HOP["r"], Z_CYL0, "thin")
        # auger (jar tooling) and spindle
        v.rect(u - T_["shaft"] / 2, Z_OUT + 5, T_["shaft"], SPN["Z_cpl"] - Z_OUT - 5, "vis", "#cfd8dc")
        p = T_["pitch"]; z = Z_OUT + 5
        while z + p / 2 < Z_TC + 30:
            v.line(u - T_["auger_od"] / 2, z, u + T_["auger_od"] / 2, z + p / 2, "thin"); v.line(u + T_["auger_od"] / 2, z + p / 2, u - T_["auger_od"] / 2, z + p, "thin")
            z += p
        v.rect(u - SPN["d"] / 2, SPN["Z_cpl"], SPN["d"], SPN["top"] - SPN["Z_cpl"], "vis", "#b0bec5")
        # agitator
        so, si = AGIT["sleeve_od"] / 2, AGIT["sleeve_od"] / 2 - AGIT["sleeve_t"]
        for sg in (-1, 1):
            v.hatch([(u + sg * si, AGIT["z_arm"]), (u + sg * so, AGIT["z_arm"]), (u + sg * so, Z_AGTC), (u + sg * si, Z_AGTC)], "hC")
            v.hatch([(u + sg * so, AGIT["z_arm"]), (u + sg * AGIT["r_tip"], AGIT["z_arm"]), (u + sg * AGIT["r_tip"], AGIT["z_arm"] + AGIT["arm_t"]),
                     (u + sg * so, AGIT["z_arm"] + AGIT["arm_t"])], "hC")
            rw = HOP["r"] - AGIT["clear"]
            v.hatch([(u + sg * (rw - AGIT["blade_t"]), Z_CYL0), (u + sg * rw, Z_CYL0), (u + sg * rw, AGIT["z_arm"]), (u + sg * (rw - AGIT["blade_t"]), AGIT["z_arm"])], "hC")
            z0 = AGIT["z_cone_end"]
            r0 = HOP["r_lo"] + (HOP["r"] - HOP["r_lo"]) * (z0 - Z_CONE0) / HOP["h_cone"] - AGIT["clear"] * 1.19
            v.poly([(u + sg * r0, z0), (u + sg * (r0 - AGIT["blade_t"] * 1.19), z0), (u + sg * (rw - AGIT["blade_t"]), Z_CYL0), (u + sg * rw, Z_CYL0)], "vis", True, "#cfd8dc")
    else:
        v.poly(hop, "vis", True, SS)
        v.line(u - R_O, Z_CYL0, u + R_O, Z_CYL0, "vis")
    # lid, collar
    v.rect(u - R_RIM, Z_RIM, 2 * R_RIM, LID["t"], "vis", SS)
    v.rect(u - R_RIM, Z_RIM - 15, LID["t"], 15, "vis"); v.rect(u + R_RIM - LID["t"], Z_RIM - 15, LID["t"], 15, "vis")
    v.rect(u - LID["bore"] / 2 - LID["t"], Z_RIM, LID["bore"] + 2 * LID["t"], 25, "vis", SS)
    # agitator TC (clamp) and hub
    v.rect(u - AGIT["sleeve_od"] / 2, Z_RIM + 25, AGIT["sleeve_od"], Z_AGTC - 21.5 - Z_RIM - 25, "vis", SS) if not sec else None
    v.rect(u - 77.5 / 2 - 6, Z_AGTC - 8, 77.5 + 12, 16, "vis", "#cfd8dc")
    v.rect(u - HUB["od"] / 2, HUB["z_seal"], HUB["od"], HUB["z1"] - HUB["z_seal"], "vis", SS)
    v.rect(u - HUB["fl_d"] / 2, HUB["z1"] - HUB["fl_t"], HUB["fl_d"], HUB["fl_t"], "vis", SS)
    v.rect(u - 61.1, HUB["z1"] - HUB["fl_t"] - 8, 122.2, 8, "vis", "#dfe7f1")
    # housing, cap, pulley, spindle top
    zb = Z_HPT
    v.rect(u - HOUS["fl_d"] / 2, zb, HOUS["fl_d"], HOUS["fl_t"], "vis", SS)
    v.rect(u - HOUS["body_d"] / 2, zb + HOUS["fl_t"], HOUS["body_d"], HOUS["h_up"], "vis", SS)
    v.rect(u - HOUS["body_d"] / 2, zb + HOUS["fl_t"] + HOUS["h_up"], HOUS["body_d"], 6, "vis", SS)
    v.rect(u - PD2 / 2 - 2, SPN["top"] - 30, PD2 + 4, 22, "vis", BLU)
    v.centre(u, Z_OUT - 40, u, SPN["top"] + 30)


def ga():
    S = sheet("P1-401-001", "SERVO AUGER FILLER GENERAL ARRANGEMENT", scale="1:5", material="see item list", finish="see parts",
              mass=f"{C['m_tot']:.0f} kg [{C['m_tot'] * 2.2046:.0f} lb] with full hopper")
    s = SC(5)
    # ---------------- front elevation (x, z)
    v = S.view(800, 1900, s, "FRONT ELEVATION (1:5), OPERATOR SIDE", (300, 300))
    v.line(-420, 0, 420, 0, "thin")
    for sx in (-1, 1):
        rv(v, sx * FEET["x"] - FEET["pad"] / 2, sx * FEET["x"] + FEET["pad"] / 2, 0, 12, "vis", "#cfd8dc"); rv(v, sx * FEET["x"] - 6, sx * FEET["x"] + 6, 12, Z_FOOT)
    rv(v, -CAB["w"] / 2, CAB["w"] / 2, Z_FOOT, ZC, "vis", SS)
    rv(v, -DOOR["w"] / 2, DOOR["w"] / 2, DOOR["z0"], DOOR["z0"] + DOOR["h"])
    v.circle(DOOR["w"] / 2 - 40, DOOR["z0"] + DOOR["h"] / 2, 11)
    for z in (DOOR["z0"] + 80, DOOR["z0"] + DOOR["h"] - 80):
        rv(v, -DOOR["w"] / 2 - 12, -DOOR["w"] / 2, z - 25, z + 25, "vis", "#cfd8dc")
    rv(v, -TOP["w"] / 2, TOP["w"] / 2, ZC, Z_TOP, "vis", SS)
    rv(v, 200, 320, Z_TOP, Z_TOP + 130, "vis", SS); v.line(200, Z_TOP + 60, 320, Z_TOP + 60, "thin")
    v.circle(260, Z_TOP + 100, 12, "vis", "#e53935"); v.circle(230, Z_TOP + 40, 8); v.circle(290, Z_TOP + 40, 8)
    zst = Z_TOP + STAGE_POS["jar-12"]
    rv(v, -STAGE["w"] / 2, STAGE["w"] / 2, zst, zst + STAGE["t"], "vis", SS)
    rv(v, -STAGE["rod_d"] / 2, STAGE["rod_d"] / 2, Z_TOP, zst, "vis")
    rv(v, STAGE["bar_x"] - PIN["bar_t"] / 2, STAGE["bar_x"] + PIN["bar_t"] / 2, Z_TOP, zst, "vis", SS)
    rv(v, PLG["x"] - 20, PLG["x"] + 20, Z_TOP, Z_TOP + 40, "vis", SS)
    rv(v, PLG["x"] + 20, PLG["x"] + 60, Z_TOP + PLG["h"] - 8, Z_TOP + PLG["h"] + 8, "vis", BLU)
    rv(v, -50.8, 50.8, Z_TOP + CBASE["t"], Z_HP - CAP["t"], "hid")
    rv(v, -CBASE["a"] / 2, CBASE["a"] / 2, Z_TOP, Z_TOP + CBASE["t"], "vis", SS)
    rv(v, -50.8, 50.8, Z_RIM + 25, Z_HP - CAP["t"], "vis", SS)
    rv(v, -CAP["a"] / 2, CAP["a"] / 2, Z_HP - CAP["t"], Z_HP, "vis", SS)
    rv(v, -(HSH["ri"] + HSH["w"]), HSH["ri"] + HSH["w"], Z_RIM - RIM["t"] - HSH["t"], Z_RIM - RIM["t"], "vis", SS)
    revolved(v, sec=False)
    for sx in (-1, 1):
        x = sx * R_O
        v.poly([(x, Z_CYL0 + 70), (x + sx * 40, Z_CYL0 + 70), (x + sx * 40, Z_CYL0 + 80), (x, Z_CYL0 + 80)], "vis", True, SS)
    rv(v, LID["port_x"] - LID["port_w"] / 2, LID["port_x"] + LID["port_w"] / 2, Z_RIM + LID["t"], Z_RIM + LID["up"], "vis", SS)
    rv(v, LID["port_x"] - LID["port_w"] / 2 - 5, LID["port_x"] + LID["port_w"] / 2 + 5, Z_RIM + LID["up"], Z_RIM + LID["up"] + LID["t"] + 1, "vis", SS)
    rv(v, HPL["x0"], HPL["x1"], Z_HP, Z_HPT, "vis", SS)
    rv(v, -75, GM_X + 45, Z_HP - 32, Z_HP, "vis", SS)
    for x in (SERVO_X - 55, SERVO_X + 55):
        rv(v, x - BRIDGE["post_d"] / 2, x + BRIDGE["post_d"] / 2, Z_HPT, Z_HPT + BRIDGE["h"], "vis", SS)
    rv(v, SERVO_X - BRIDGE["a"] / 2, SERVO_X + BRIDGE["a"] / 2, Z_HPT + BRIDGE["h"], Z_SRV0, "vis", SS)
    rv(v, SERVO_X - 40, SERVO_X + 40, Z_SRV0, Z_SRV1, "vis", "#37474f")
    rv(v, SERVO_X - 45, 50, Z_HPT + HOUS["fl_t"] + HOUS["h_up"] - 2, SPN["top"] + 14, "vis", "#ffffff")
    v.text(SERVO_X / 2 - 20, SPN["top"] - 10, "belt guard 305", 11)
    rv(v, GM_X - 55, GM_X + 55, Z_HPT, Z_HPT + 110, "vis", BLU); rv(v, GM_X - 52, GM_X + 52, Z_HPT + 110, Z_GM1, "vis", BLU)
    # balloons
    v.tag(400, 400, 1, (CAB["w"] / 2, 400)); v.tag(-420, 1250, 2, (-50.8, 1250) if False else (-30, Z_RIM + 60)); v.tag(-420, 1780, 3, (HPL["x0"] + 10, Z_HPT - 4))
    v.tag(380, 1400, 4, (R_O - 30, 1380)); v.tag(380, 1690, 5, (60, Z_AGTC - 4)); v.tag(-420, 880, 6, (-STAGE["w"] / 2 + 10, zst + 3))
    v.tag(-420, 1960, 7, (SERVO_X - 40, Z_SRV0 + 80)); v.tag(400, 1950, 8, (GM_X + 52, Z_GM1 - 50)); v.tag(380, 1060, 9, (TOOL["J"]["tube_od"] / 2, Z_OUT + 40))
    v.tag(420, 820, 13, (PLG["x"] + 60, Z_TOP + PLG["h"]))
    # dims
    xd = -CAB["w"] / 2
    v.dim((xd, 0), (xd, Z_TOP), 100, f"{mmi(Z_TOP)} TOP", "v")
    v.dim((xd, 0), (xd, Z_OUT), 165, f"{mmi(Z_OUT)} OUTLET", "v")
    v.dim((xd, 0), (xd, Z_RIM), 230, f"{mmi(Z_RIM)} HOPPER RIM", "v")
    v.dim((xd, 0), (xd, Z_HP), 295, f"{mmi(Z_HP)} HEAD PLATE", "v")
    v.dim((xd, 0), (xd, Z_SRV1), 360, f"{mmi(Z_SRV1)} OVERALL", "v")
    v.dim((-TOP["w"] / 2, Z_TOP), (TOP["w"] / 2, Z_TOP), 0, None, "h") if False else None
    v.dim((-TOP["w"] / 2, 0), (TOP["w"] / 2, 0), -40, f"{mmi(TOP['w'])} TOP", "h")
    v.dim((-R_RIM, Z_RIM + LID["t"]), (R_RIM, Z_RIM + LID["t"]), -0, None, "h") if False else None
    v.dim((HPL["x0"], Z_HPT), (HPL["x1"], Z_HPT), 300, None, "h")
    v.dim((SERVO_X, Z_SRV1), (0, Z_SRV1), 30, f"{mmi(BELT['C'])} BELT C", "h")
    v.dim((0, Z_GM1), (GM_X, Z_GM1), 30, f"{mmi(CHAIN['C'])} CHAIN C", "h")
    # ---------------- side elevation (y, z), section on x = 0 through the hopper
    vs = S.view(1720, 1900, s, "SIDE ELEVATION FROM THE RIGHT (1:5), HOPPER AND HEAD CUT ON X = 0", (1250, 300))
    vs.line(-660, 0, 450, 0, "thin")
    for sy in (-1, 1):
        y = FEET["yc"] + sy * FEET["y"]
        rv(vs, y - FEET["pad"] / 2, y + FEET["pad"] / 2, 0, 12, "vis", "#cfd8dc"); rv(vs, y - 6, y + 6, 12, Z_FOOT)
    rv(vs, CAB["y0"], CAB["y0"] + CAB["d"], Z_FOOT, ZC, "vis", SS)
    rv(vs, CAB["y0"] - 3.5, CAB["y0"], DOOR["z0"], DOOR["z0"] + DOOR["h"], "vis")
    rv(vs, CAB["y0"] - 20, CAB["y0"] + CAB["d"] + 20, ZC, Z_TOP, "vis", SS)
    vs.poly([(-200, Z_TOP), (-80, Z_TOP), (-80, Z_TOP + 130), (-200, Z_TOP + 60)], "vis", True, SS)
    for y in (-STAGE["rod_y"], STAGE["rod_y"]):
        rv(vs, y - 10, y + 10, Z_TOP, zst, "vis"); rv(vs, y - 10, y + 10, zst - STAGE["rod_L"], Z_TOP, "hid")
        rv(vs, y - STAGE["bush_a"] / 2, y + STAGE["bush_a"] / 2, ZC - STAGE["bush_L"], ZC, "hid")
    rv(vs, -STAGE["d"] / 2, STAGE["d"] / 2, zst, zst + STAGE["t"], "vis", SS)
    rv(vs, -25, 25, Z_TOP, Z_TOP + 40, "vis", SS); vs.circle(0, Z_TOP + PLG["h"], 14, "vis", BLU)
    rv(vs, -CAB["d"] / 2 + 220, -CAB["d"] / 2 + 230, 0, 0) if False else None
    rv(vs, X1 := 249.2, 350.8, Z_TOP + CBASE["t"], Z_HP - CAP["t"], "vis", SS)
    rv(vs, COL["y"] - CBASE["a"] / 2, COL["y"] + CBASE["a"] / 2, Z_TOP, Z_TOP + CBASE["t"], "vis", SS)
    rv(vs, COL["y"] - CAP["a"] / 2, COL["y"] + CAP["a"] / 2, Z_HP - CAP["t"], Z_HP, "vis", SS)
    vs.hatch([(HSH["ri"], Z_RIM - RIM["t"] - HSH["t"]), (COL["y"] - COL["a"] / 2, Z_RIM - RIM["t"] - HSH["t"]), (COL["y"] - COL["a"] / 2, Z_RIM - RIM["t"]), (HSH["ri"], Z_RIM - RIM["t"])], "hB")
    vs.hatch([(-HSH["ri"] - HSH["w"], Z_RIM - RIM["t"] - HSH["t"]), (-HSH["ri"], Z_RIM - RIM["t"] - HSH["t"]), (-HSH["ri"], Z_RIM - RIM["t"]), (-HSH["ri"] - HSH["w"], Z_RIM - RIM["t"])], "hB") if False else None
    revolved(vs, sec=True)
    vs.hatch([(HPL["y0"], Z_HP), (-HOUS["spig_L"] * 0 - 25, Z_HP), (-25, Z_HPT), (HPL["y0"], Z_HPT)], "hB")
    vs.hatch([(25, Z_HP), (HPL["y1"], Z_HP), (HPL["y1"], Z_HPT), (25, Z_HPT)], "hB")
    rv(vs, -55, 55, Z_HPT, Z_HPT + 110, "vis", BLU); rv(vs, -52, 52, Z_HPT + 110, Z_GM1, "vis", BLU)
    vs.text(0, Z_HPT + 230, "gearmotor P1-414 (x +184)", 11)
    rv(vs, -40, 40, Z_SRV0, Z_SRV1, "hid")
    rv(vs, -70, 70, Z_HP - 32, Z_HP, "vis")
    rv(vs, -150, -100, -620 + 0, -420 + 0, "vis") if False else None
    rv(vs, -620, -420, 0, 60, "vis", "#ffe082"); vs.text(-520, 75, "foot switch P1-417", 11)
    vs.tag(-560, 1250, 4, (-R_O + 3, 1300)); vs.tag(-560, 1450, 5, (-AGIT["r_tip"] + 20, AGIT["z_arm"] + 3)); vs.tag(-560, 1100, 9, (-TOOL["J"]["auger_od"] / 2 + 3, Z_OUT + 50))
    vs.tag(420, 1500, 2, (COL["y"] + COL["a"] / 2, 1500)); vs.tag(420, 1780, 3, (HPL["y1"] - 10, Z_HPT)); vs.tag(-560, 900, 6, (-STAGE["d"] / 2 + 5, zst + 3))
    vs.tag(-560, 1650, 12, (-HUB["fl_d"] / 2, HUB["z1"] - 4)); vs.tag(420, 860, 11, (-500, 60)) if False else None
    vs.dim((CAB["y0"] - 20, Z_TOP), (CAB["y0"] + CAB["d"] + 20, Z_TOP), -0, None, "h") if False else None
    vs.dim((CAB["y0"], 0), (CAB["y0"] + CAB["d"], 0), -40, f"{mmi(CAB['d'])} CABINET", "h")
    vs.dim((0, Z_RIM), (COL["y"], Z_RIM), 200, f"{mmi(COL['y'])} AXIS TO COLUMN", "h")
    vs.dim((-R_RIM, Z_RIM + LID["t"]), (R_RIM, Z_RIM + LID["t"]), 120, f"Ø{mmi(2 * R_RIM)} LID", "h")
    vs.dim((0, Z_OUT), (0, Z_TC), -300, None, "v") if False else None
    # ---------------- plan (x, y)
    sp = SC(5)
    vp = S.view(2650, 760, sp, "PLAN (1:5)", (2380, 300))
    vp.rect(-TOP["w"] / 2, CAB["y0"] - 20, TOP["w"], TOP["d"], "vis", SS)
    vp.rect(HPL["x0"], HPL["y0"], HPL["x1"] - HPL["x0"], HPL["y1"] - HPL["y0"], "vis", SS)
    vp.circle(0, 0, R_RIM, "vis", "#fff"); vp.circle(0, 0, HSH["ri"] + HSH["w"], "hid")
    vp.rect(LID["port_x"] - LID["port_w"] / 2 - 5, -LID["port_l"] / 2 - 5, LID["port_w"] + 10, LID["port_l"] + 10, "vis", SS)
    vp.circle(0, 0, HOUS["fl_d"] / 2, "vis", SS); vp.circle(0, 0, PD2 / 2 + 2, "vis", BLU)
    vp.rect(SERVO_X - 40, -40, 80, 80, "vis", "#37474f"); vp.rect(GM_X - 55, -55, 110, 110, "vis", BLU)
    vp.rect(-50.8, COL["y"] - 50.8, 101.6, 101.6, "hid")
    vp.poly([(200, -200), (320, -200), (320, -80), (200, -80)], "vis", True, SS); vp.circle(260, -140, 12, "vis", "#e53935")
    vp.rect(-150, -620, 300, 200, "vis", "#ffe082")
    vp.rect(-STAGE["w"] / 2, -STAGE["d"] / 2, STAGE["w"], STAGE["d"], "hid")
    vp.text(0, -470, "foot switch on the floor", 11)
    vp.text(0, CAB["y0"] - 60, "OPERATOR ↓ (front, -y)", 13)
    vp.cmark(0, 0, R_RIM + 10)
    vp.leader((LID["port_x"], -LID["port_l"] / 2), (-430, -330), ["scoop port + flap (interlocked)"], anchor="end")
    vp.leader((260, -140), (430, -330), ["HMI pod: HMI, E-stop, reset, lamps"])
    vp.dim((-TOP["w"] / 2, CAB["y0"] - 20), (-TOP["w"] / 2, CAB["y0"] + CAB["d"] + 20), 40, f"{mmi(TOP['d'])}", "v")
    vp.dim((HPL["x0"], HPL["y1"]), (HPL["x1"], HPL["y1"]), 30, f"{mmi(HPL['x1'] - HPL['x0'])} HEAD PLATE", "h")
    # tables
    S.table(2080, 1080, [("ITEM", 50), ("PART", 130), ("DESCRIPTION", 610), ("QTY", 45), ("SOURCE / DRAWING", 260)],
            [(a, b, c, d, e) for a, b, c, d, e in ITEMS], "ITEM LIST", 13, 22)
    S.table(2080, 1480, [("CONTAINER", 150), ("Ø x H", 170), ("NET g", 80), ("TOOLING", 80), ("STAGE ABOVE TOP", 170), ("PIN HOLE", 110), ("REVS / DOSE", 120), ("DOSE s", 80)],
            [(k, f"{mmi(c['d'])} x {mmi(c['h'])}", f"{c['g']:.1f}", c["tool"], mmi(STAGE_POS[k]), f"#{i + 1}", f"{C[k]['rev']:.1f}", f"{C[k]['t_dose']:.1f}")
             for i, (k, c) in enumerate(CONT.items())], "CONTAINER SET-UP (stage index, tooling, dose)", 12, 22)
    S.table(2080, 1640, [("INTERFACE", 260), ("VALUE", 530), ("SET BY", 300)], [
        ("Supply", "208 V 1-ph 20 A 2-pole circuit, cord to Q1 on the cabinet", "panel schedule ELE-P1"),
        ("Product in", "scoop from the released drum into the port at 1,632 AFF", "operator, P1-308 drum"),
        ("Container out", "to the capper bench at 905 AFF", "P1-412 / P1-409 table"),
        ("Ethernet", "Modbus TCP: counts, faults, recipe (PLC port 1)", "plant switch, MES"),
    ], "PLANT INTERFACES", 12, 22)
    S.notes(120, 1960, 2300, [
        "All dimensions mm [in]. Third-angle projection. Stage shown at the jar-12 stop; container phantom. Feet set to 60 [2.36] (±25 [1]); level the top ±0.5° before setting the tooling.",
        f"Auger drive: servo P1-413 → HTD belt 2:1 → spindle (2 x 6205) → auger on M16 LH thread. Agitator: gearmotor P1-414 → #40 chain 2:1 → hub (2 x 6009) at {AGIT['rpm']:.0f} rpm.",
        f"Hopper {C['vol_hop']:.0f} L ({C['kg_hop']:.0f} kg of blend) hangs on the horseshoe by its rim angle, 2 locating pins; it slides out forward after the auger and agitator are off (P1-401-003).",
        "Guarding: belt and chain guards fixed (tools); scoop flap interlocked (B1) with the agitator and the servo STO through the safety relay; container sensor blocks a dose with no container.",
    ], "NOTES", 13)
    S.save(DWG / "P1-401-001_general_arrangement.svg")


if __name__ == "__main__":
    ga()


def bearing(v, ri, ro, z0, z1, sg=1):
    """bearing symbol (one side): outline + X"""
    x0, x1 = sg * ri, sg * ro
    v.rect(min(x0, x1), z0, abs(x1 - x0), z1 - z0, "vis", "#fff")
    v.line(x0, z0, x1, z1, "thin"); v.line(x0, z1, x1, z0, "thin")


def mirror_hatch(v, pts, pat="hB", u=0.0):
    for sg in (-1, 1):
        v.hatch([(u + sg * x, z) for x, z in pts], pat)


def section():
    S = sheet("P1-401-002", "SECTIONS AND DETAILS: DRIVE HEAD, OUTLET, RIM, STAGE INDEX", scale="1:2 · 1:1 · 2:1", material="see item list", finish="see parts", mass="-")
    s2 = SC(2)
    # ---------------- detail H: drive head on y = 0 (1:2)
    zmid = 1750.0
    v = S.view(820, 760 + zmid * s2, s2, "DETAIL H (1:2): DRIVE HEAD, SECTION ON Y = 0", (150, 230))
    # head plate (cut)
    v.hatch([(HPL["x0"], Z_HP), (-HOUS["pilot_d"] / 2, Z_HP), (-HOUS["pilot_d"] / 2, Z_HPT), (HPL["x0"], Z_HPT)], "hA")
    v.hatch([(HOUS["pilot_d"] / 2, Z_HP), (GM_X - 25, Z_HP), (GM_X - 25, Z_HPT), (HOUS["pilot_d"] / 2, Z_HPT)], "hA")
    v.hatch([(GM_X + 25, Z_HP), (HPL["x1"], Z_HP), (HPL["x1"], Z_HPT), (GM_X + 25, Z_HPT)], "hA")
    # housing (cut)
    hz = [(14, Z_HP - (HOUS["spig_L"] - HPL["t"])), (HOUS["spig_d"] / 2, Z_HP - (HOUS["spig_L"] - HPL["t"])), (HOUS["spig_d"] / 2, Z_HP), (HOUS["pilot_d"] / 2, Z_HP),
          (HOUS["pilot_d"] / 2, Z_HPT), (HOUS["fl_d"] / 2, Z_HPT), (HOUS["fl_d"] / 2, Z_HPT + HOUS["fl_t"]), (HOUS["body_d"] / 2, Z_HPT + HOUS["fl_t"]),
          (HOUS["body_d"] / 2, HOUS["z_top"]), (26, HOUS["z_top"]),
          (26, HOUS["brg_lo"]), (19, HOUS["brg_lo"]), (19, Z_HPT), (14, Z_HPT)]
    mirror_hatch(v, hz, "hB")
    for sg in (-1, 1):
        bearing(v, 12.5, 26, HOUS["brg_lo"], HOUS["brg_lo"] + 15, sg); bearing(v, 12.5, 26, HOUS["brg_up"], HOUS["z_top"], sg)
        bearing(v, 20, 34, HUB["z_brg"], HUB["z_brg"] + 15, sg); bearing(v, 20, 34, HUB["z_brg"] + 15, HUB["z1"], sg)
    # spacers, cap + seal
    zt, ct = HOUS["z_top"], HOUS["cap_t"]
    for sg in (-1, 1):
        v.rect(min(sg * 23, sg * 26), HOUS["brg_lo"] + 15, 3, 30, "vis", "#cfd8dc"); v.rect(min(sg * 12.55, sg * 15), HOUS["brg_lo"] + 15, 2.45, 30, "vis", "#cfd8dc")
    mirror_hatch(v, [(18, zt), (36, zt), (36, zt + ct), (13, zt + ct), (13, zt + 10), (20, zt + 10), (20, zt + 3), (18, zt + 3)], "hA")
    for sg in (-1, 1):
        v.rect(min(sg * 12.5, sg * 20), zt + 3, 7.5, 7, "vis", "#263238")
        v.rect(min(sg * 12.5, sg * 20), HUB["z_seal"], 7.5, 7, "vis", "#263238")
    # spindle (not cut) and pulley
    v.rect(-SPN["d"] / 2, Z_AGTC - 60, SPN["d"], Z_PUL - Z_AGTC + 60, "vis", "#eceff1")
    v.rect(-SPN["seat"] / 2, Z_PUL, SPN["seat"], SPN["top"] - Z_PUL, "vis", "#eceff1")
    v.rect(-PD2 / 2 - 2, Z_PUL, PD2 + 4, 22, "vis", BLU); v.rect(-15, SPN["top"], 30, 3, "vis", "#cfd8dc"); v.rect(-8, SPN["top"] + 3, 16, 7, "vis", "#cfd8dc")
    v.line(-PD2 / 2 - 2, Z_PUL + 3, SERVO_X + PD1 / 2 + 2, Z_PUL + 3, "thin"); v.line(-PD2 / 2 - 2, Z_PUL + 18, SERVO_X + PD1 / 2 + 2, Z_PUL + 18, "thin")
    # hub (cut), ferrules, clamp, sleeve
    mirror_hatch(v, [(20, HUB["z_seal"]), (HUB["od"] / 2, HUB["z_seal"]), (HUB["od"] / 2, HUB["z1"] - HUB["fl_t"]), (HUB["fl_d"] / 2, HUB["z1"] - HUB["fl_t"]),
                     (HUB["fl_d"] / 2, HUB["z1"]), (34, HUB["z1"]), (34, HUB["z_brg"]), (24, HUB["z_brg"]), (24, HUB["z_seal"] + 7), (20, HUB["z_seal"] + 7)], "hB")
    mirror_hatch(v, [(30.1, Z_AGTC), (38.75, Z_AGTC), (38.75, Z_AGTC + 6), (31.75, Z_AGTC + 6), (31.75, HUB["z_seal"]), (30.1, HUB["z_seal"])], "hC")
    mirror_hatch(v, [(30.1, Z_AGTC), (38.75, Z_AGTC), (38.75, Z_AGTC - 6), (31.75, Z_AGTC - 6), (31.75, Z_AGTC - 45), (30.1, Z_AGTC - 45)], "hC")
    for sg in (-1, 1):
        v.rect(min(sg * 38.75, sg * 46), Z_AGTC - 9, 7.25, 18, "vis", "#cfd8dc")
        v.rect(min(sg * 40.5, sg * 64.3), HUB["z1"] - HUB["fl_t"] - 7.2, 23.8, 7.2, "vis", BLU)
    v.poly([(-45, Z_AGTC - 45), (-20, Z_AGTC - 40), (0, Z_AGTC - 48), (25, Z_AGTC - 42), (45, Z_AGTC - 45)], "thin", False)
    # gearmotor, sprocket, chain, guards
    v.rect(GM_X - 55, Z_HPT, 110, 110, "vis", BLU); v.rect(GM_X - 8, HUB["z1"] - HUB["fl_t"] - 7.2, 16, Z_HPT - (HUB["z1"] - HUB["fl_t"] - 7.2), "vis", "#eceff1")
    v.rect(GM_X - 30.5, HUB["z1"] - HUB["fl_t"] - 7.2, 61, 7.2, "vis", BLU)
    v.line(64.3, HUB["z1"] - HUB["fl_t"] - 1, GM_X - 30.5, HUB["z1"] - HUB["fl_t"] - 1, "thin"); v.line(64.3, HUB["z1"] - HUB["fl_t"] - 6, GM_X - 30.5, HUB["z1"] - HUB["fl_t"] - 6, "thin")
    v.poly([(-75, Z_HP), (-75, Z_HP - 32), (GM_X + 45, Z_HP - 32), (GM_X + 45, Z_HP)], "vis", False)
    v.poly([(SERVO_X - 45, Z_PUL - 5), (SERVO_X - 45, Z_HPT + BRIDGE["h"] - 1), (50, Z_HPT + BRIDGE["h"] - 1), (50, Z_PUL - 5)], "vis", False)
    # bridge + servo
    for x in (SERVO_X - 55, SERVO_X + 55):
        v.rect(x - 12.5, Z_HPT, 25, BRIDGE["h"], "vis", SS)
    v.hatch([(SERVO_X - 70, Z_HPT + BRIDGE["h"]), (SERVO_X - 35, Z_HPT + BRIDGE["h"]), (SERVO_X - 35, Z_SRV0), (SERVO_X - 70, Z_SRV0)], "hA")
    v.hatch([(SERVO_X + 35, Z_HPT + BRIDGE["h"]), (SERVO_X + 70, Z_HPT + BRIDGE["h"]), (SERVO_X + 70, Z_SRV0), (SERVO_X + 35, Z_SRV0)], "hA")
    v.rect(SERVO_X - 40, Z_SRV0, 80, 120, "vis", "#37474f"); v.text(SERVO_X, Z_SRV0 + 70, "SERVO P1-413", 12, color="#fff")
    v.rect(SERVO_X - 9.5, Z_PUL, 19, Z_SRV0 - Z_PUL, "vis", "#eceff1"); v.rect(SERVO_X - PD1 / 2 - 2, Z_PUL, PD1 + 4, 22, "vis", BLU)
    v.centre(0, Z_AGTC - 70, 0, SPN["top"] + 30); v.centre(SERVO_X, Z_PUL - 20, SERVO_X, Z_SRV0 + 130); v.centre(GM_X, HUB["z1"] - 30, GM_X, Z_HPT + 130)
    # dims and callouts
    v.dim((SERVO_X, Z_SRV0 + 120), (0, Z_SRV0 + 120), 20, f"{mmi(BELT['C'])} (slots ±8 for tension)", "h")
    v.dim((0, Z_HPT + 125), (GM_X, Z_HPT + 125), 20, f"{mmi(CHAIN['C'])} (slots ±5)", "h")
    v.dim((HOUS["fl_d"] / 2, Z_HP), (HOUS["fl_d"] / 2, Z_HPT), -110, None, "v")
    v.dim((70, HOUS["brg_lo"] + 7.5), (70, HOUS["brg_up"] + 7.5), -60, f"{mmi(45)}", "v")
    v.dim((-HPL["x0"] * 0 - 120, Z_HP), (-120, SPN["top"]), 0, None, "v") if False else None
    v.dim((HPL["x0"], Z_HP), (HPL["x0"], SPN["top"]), 110, f"{mmi(SPN['top'] - Z_HP)} TO SPINDLE TOP", "v")
    v.dim((HPL["x0"], Z_HP), (HPL["x0"], Z_AGTC), 160, f"{mmi(Z_HP - Z_AGTC)} TO AGITATOR TC", "v")
    v.leader((26, HOUS["brg_up"] + 7), (120, HOUS["z_top"] + 60), ["2 x 6205-2RS (P1-430), Ø52 H7 / Ø25 k6, spacers", "309/310 between; DIN 471 Ø25 under and over"])
    v.leader((34, HUB["z_brg"] + 15), (150, HUB["z_brg"] - 55), ["2 x 6008-2RS on spigot Ø40 k6, hub Ø68 H7", "DIN 471 Ø40 under; outers Loctite 641 in the hub"])
    v.leader((16, HUB["z_seal"] + 3), (110, Z_AGTC - 70), ["LIP SEAL 25x40x7 FDA (P1-433) in hub 304"])
    v.leader((-16, HOUS["z_top"] + 4), (-260, HOUS["z_top"] + 210), ["CAP 308 + LIP SEAL 25x40x7, 4 x M4"], anchor="end")
    v.leader((-HOUS["pilot_d"] / 2, Z_HP + 5), (-150, Z_HP - 70), ["PILOT Ø50 H8 / f7 in head plate 301", "HOUSING 302 4 x M8 x 25 on Ø90, 20 N·m"], anchor="end")
    v.leader((-42, Z_AGTC), (-150, Z_AGTC - 40), ["2.5 in TC CLAMP P1-445: agitator", "drops out with the sleeve"], anchor="end")
    v.leader((55, HUB["z1"] - 12), (120, HUB["z1"] - 90) if False else (260, Z_HP - 70), ["30T #40 SS PLATE, 4 x M6 on Ø100 (H7)", "chain #40 SS 52 links to 15T"])
    v.leader((0, SPN["top"] + 10), (60, SPN["top"] + 60), ["M10 x 25 END BOLT + Ø30 WASHER (H8) 35 N·m"])
    # ---------------- detail T: outlet (1:1)
    s1 = SC(1)
    vt = S.view(2350, 470 + 1120 * s1, s1, "DETAIL T (1:1): HOPPER OUTLET, TOOLING J, JAR", (2080, 230))
    TJ = TOOL["J"]
    mirror_hatch(vt, [(HOP["r_lo"], Z_CONE0), (HOP["r_lo"] + T14, Z_CONE0), (HOP["r_lo"] + T14 + 25 * (HOP["r"] - HOP["r_lo"]) / HOP["h_cone"], Z_CONE0 + 25),
                      (HOP["r_lo"] + 25 * (HOP["r"] - HOP["r_lo"]) / HOP["h_cone"], Z_CONE0 + 25)], "hC")
    mirror_hatch(vt, [(TC25["id"] / 2, Z_TC), (TC25["fl"] / 2, Z_TC), (TC25["fl"] / 2, Z_TC + 6), (TC25["od"] / 2, Z_TC + 6), (TC25["od"] / 2, Z_CONE0), (TC25["id"] / 2, Z_CONE0)], "hC")
    mirror_hatch(vt, [(TC25["id"] / 2, Z_TC), (TC25["fl"] / 2, Z_TC), (TC25["fl"] / 2, Z_TC - 6), (TC25["od"] / 2, Z_TC - 6), (TJ["tube_od"] / 2, Z_TC - 25),
                      (TJ["tube_od"] / 2, Z_OUT), (TJ["tube_id"] / 2, Z_OUT), (TJ["tube_id"] / 2, Z_TC - 25), (TC25["id"] / 2, Z_TC - 6)], "hC")
    for sg in (-1, 1):
        vt.rect(min(sg * TC25["fl"] / 2, sg * (TC25["fl"] / 2 + 8)), Z_TC - 10, 8, 20, "vis", "#cfd8dc")
        vt.rect(min(sg * TC25["id"] / 2, sg * TC25["fl"] / 2), Z_TC - 0.8, (TC25["fl"] - TC25["id"]) / 2, 1.6, "vis", "#263238")
    z = Z_OUT + 5; p = TJ["pitch"]
    while z + p / 2 <= Z_CONE0 + 25:
        vt.poly([(-TJ["auger_od"] / 2, z), (TJ["auger_od"] / 2, z + p / 2), (TJ["auger_od"] / 2, z + p / 2 + 2.5), (-TJ["auger_od"] / 2, z + 2.5)], "vis", True, "#cfd8dc")
        z += p
    vt.rect(-TJ["shaft"] / 2, Z_OUT + 5, TJ["shaft"], Z_CONE0 + 25 - Z_OUT - 5, "vis", "#eceff1")
    c = CONT["jar-12"]; zs = Z_OUT - GAP_FILL
    vt.poly([(-c["d"] / 2, zs - 50), (-c["d"] / 2, zs - 18), (-44.5, zs - 12), (-44.5, zs), (44.5, zs), (44.5, zs - 12), (c["d"] / 2, zs - 18), (c["d"] / 2, zs - 50)], "phan", False)
    vt.dim((-TJ["tube_id"] / 2, Z_OUT - 30), (TJ["tube_id"] / 2, Z_OUT - 30), 0, f"Ø{mmi(TJ['tube_id'])} TUBE ID", "h") if False else None
    vt.dim((-TJ["tube_od"] / 2, Z_OUT), (TJ["tube_od"] / 2, Z_OUT), -60, f"Ø{mmi(TJ['tube_od'])} x 1.65 TUBE (2 in)", "h")
    vt.dim((-TJ["auger_od"] / 2, Z_OUT + 40), (TJ["auger_od"] / 2, Z_OUT + 40), 0, f"Ø{mmi(TJ['auger_od'])} AUGER", "h") if False else None
    vt.leader((TJ["auger_od"] / 2, Z_OUT + 5 + p / 4), (75, Z_OUT + 40), [f"AUGER Ø{mmi(TJ['auger_od'])} x {mmi(p)} PITCH", f"radial clearance {C['clr_J']:.2f} [.030]"])
    vt.dim((60, zs), (60, Z_OUT), 0, f"{mmi(GAP_FILL)}", "v") if False else None
    vt.dim((-TJ["tube_od"] / 2, zs), (-TJ["tube_od"] / 2, Z_OUT), 70, f"{mmi(GAP_FILL)} GAP", "v")
    vt.dim((TC25["fl"] / 2, Z_OUT), (TC25["fl"] / 2, Z_TC), -40, f"{mmi(Z_TC - Z_OUT)}", "v")
    vt.leader((-TC25["fl"] / 2 - 4, Z_TC + 5), (-85, Z_TC + 40), ["2.5 in TC CLAMP + EPDM FDA GASKET"], anchor="end")
    vt.leader((-TC25["od"] / 2, Z_CONE0 - 5), (-85, Z_CONE0 + 30), ["FERRULE 403 BPE 2.5 in, butt to cone 402"], anchor="end")
    vt.text(70, zs - 30, "JAR-12 89 mm NECK (phantom)", 12, anchor="start", color="#607d8b")
    # ---------------- detail R: rim on horseshoe (2:1) at 150°
    s05 = SC(0.5)
    r0 = 215.0
    vr = S.view(2380 - r0 * s05, 1300 + 1600 * s05, s05, "DETAIL R (2:1): HOPPER RIM ON HORSESHOE, PIN AT 150°", (2080, 1150))
    zh0, zh1 = Z_RIM - RIM["t"] - HSH["t"], Z_RIM - RIM["t"]
    vr.hatch([(HSH["ri"], zh0), (HSH["ri"] + HSH["w"], zh0), (HSH["ri"] + HSH["w"], zh1), (HSH["ri"], zh1)], "hA")
    vr.hatch([(HOP["r"], Z_RIM - 35), (R_O, Z_RIM - 35), (R_O, Z_RIM), (HOP["r"], Z_RIM)], "hC")
    vr.hatch([(R_O, Z_RIM - RIM["w"]), (R_O + RIM["t"], Z_RIM - RIM["w"]), (R_O + RIM["t"], Z_RIM - RIM["t"]), (R_RIM, Z_RIM - RIM["t"]), (R_RIM, Z_RIM), (R_O, Z_RIM)], "hC")
    pr = HSH["ri"] + 12
    vr.rect(pr - 4, zh1, 8, 12, "vis", "#eceff1"); vr.rect(pr - 4.5, Z_RIM - RIM["t"], 9, RIM["t"], "vis", "#fff")
    vr.rect(HOP["r"] - 20, Z_RIM, R_RIM + 2 - HOP["r"] + 20, LID["t"], "vis", SS); vr.rect(R_RIM, Z_RIM - 15, LID["t"], 15 + LID["t"], "vis", SS)
    vr.dim((HSH["ri"], zh0), (R_O, zh0), -30, f"{mmi(HSH['ri'] - R_O)}", "h")
    vr.dim((HSH["ri"], zh0), (HSH["ri"] + HSH["w"], zh0), -70, None, "h")
    vr.dim((R_RIM, zh1), (R_RIM, Z_RIM), -40, None, "v")
    vr.dim((HSH["ri"] + HSH["w"], zh0), (HSH["ri"] + HSH["w"], zh1), -40, None, "v")
    vr.leader((pr, zh1 + 12), (pr + 40, Z_RIM + 25), ["PIN Ø8 x 12 proud (2, at 30° and 150°)", "rim hole Ø9: hopper lifts 13 to slide out"])
    vr.leader((R_O + 1, Z_RIM - 15), (HSH["ri"] + 5, Z_RIM - 45), ["RIM ANGLE 404 25x25x3 316L, seal weld top, fillet 2 under"], anchor="start")
    # ---------------- detail S: stage index (1:2)
    vs = S.view(640, 1780 + 800 * s2, s2, "DETAIL S (1:2): STAGE INDEX ON Y = 0 (JAR STOP)", (150, 1440))
    zst = Z_TOP + STAGE_POS["jar-12"]
    vs.hatch([(-40, ZC), (STAGE["bar_x"] - 8, ZC), (STAGE["bar_x"] - 8, Z_TOP), (-40, Z_TOP)], "hA")
    vs.hatch([(STAGE["bar_x"] + 8, ZC), (300, ZC), (300, Z_TOP), (STAGE["bar_x"] + 8, Z_TOP)], "hA")
    vs.hatch([(-40, zst), (STAGE["w"] / 2, zst), (STAGE["w"] / 2, zst + STAGE["t"]), (-40, zst + STAGE["t"])], "hA")
    vs.hatch([(STAGE["bar_x"] - 6, zst - STAGE["bar_L"]), (STAGE["bar_x"] + 6, zst - STAGE["bar_L"]), (STAGE["bar_x"] + 6, zst), (STAGE["bar_x"] - 6, zst)], "hB")
    for k, d in PINBAR_HOLES.items():
        vs.rect(STAGE["bar_x"] - 6, zst - d - PIN["hole"] / 2, 12, PIN["hole"], "vis", "#fff")
        vs.text(STAGE["bar_x"] - 20, zst - d - 3, k.split("-")[0], 10, "end")
    vs.hatch([(PLG["x"] - 20, Z_TOP), (PLG["x"] + 20, Z_TOP), (PLG["x"] + 20, Z_TOP + 40), (PLG["x"] - 20, Z_TOP + 40)], "hA")
    vs.rect(STAGE["bar_x"] - 6, Z_TOP + PLG["h"] - 5, PLG["x"] + 20 - STAGE["bar_x"] + 6, 10, "vis", "#eceff1")
    vs.rect(PLG["x"] + 20, Z_TOP + PLG["h"] - 12, 20, 24, "vis", BLU); vs.circle(PLG["x"] + 55, Z_TOP + PLG["h"], 15, "vis", BLU)
    vs.rect(-10, zst - 60, 20, 60, "hid")
    vs.dim((STAGE["bar_x"] + 6, zst), (STAGE["bar_x"] + 6, zst - PINBAR_HOLES["jar-12"]), -150, None, "v")
    vs.dim((PLG["x"] + 20, Z_TOP), (PLG["x"] + 20, Z_TOP + PLG["h"]), -100, None, "v")
    vs.dim((STAGE["w"] / 2, Z_TOP), (STAGE["w"] / 2, zst), 120, f"{mmi(STAGE_POS['jar-12'])} JAR STOP", "v")
    vs.leader((PLG["x"] + 55, Z_TOP + PLG["h"] + 15), (PLG["x"] + 90, Z_TOP + 90), ["INDEX PLUNGER GN 617-10 (P1-434)", "pull, set the stage, release"])
    vs.leader((STAGE["bar_x"], zst - STAGE["bar_L"] + 5), (STAGE["bar_x"] + 70, zst - STAGE["bar_L"] - 40), ["PIN BAR 704: 40 x 12, 4 holes Ø10.2 (table)"])
    # ---------------- fits table + notes
    S.table(1250, 1500, [("FIT", 240), ("HOLE", 140), ("SHAFT", 140), ("PARTS", 420)], [
        ("Spindle bearings", "Ø52 H7", "Ø25 k6", "housing 302 / spindle 303 / 6205"),
        ("Hub bearings", "Ø68 H7", "Ø40 k6", "hub 304 / spigot of 302 / 6008"),
        ("Housing pilot", "Ø50 H8", "Ø50 f7", "head plate 301 / housing 302"),
        ("Servo pilot", "Ø70 H8", "Ø70 j6 (servo)", "bridge 307 / P1-413"),
        ("Pulley seat", "Ø20 H7", "Ø20 h6", "40T pulley / spindle, key 6 x 6"),
        ("Lip seals", "Ø40 H8", "Ø25 h9 Ra 0.4", "cap 308, hub 304 / spindle"),
        ("Stage rods", "Ø20.05 UHMW", "Ø20 h8", "bushings 703 / rods 702"),
    ], "FITS", 12, 22)
    S.notes(1250, 1720, 1100, [
        "Bearings greased for life (H1 food grade); the product zone below the hub has no bearing: both lip seals face down.",
        "Spindle runout at the coupling face ≤ 0.05 TIR (ITP T6); auger tip in the tube within 0.3 of centre with the hopper full (T12).",
        "Agitator and auger turn independently: auger 0-1,500 rpm (servo 2:1), agitator 30 rpm (gearmotor 60 rpm, chain 2:1).",
        "Tension: belt by sliding the bridge (4 slots), chain by sliding the gearmotor (4 slots); deflection 4 mm at mid span.",
    ], "NOTES", 13)
    S.save(DWG / "P1-401-002_sections.svg")


if __name__ == "__main__":
    section()
