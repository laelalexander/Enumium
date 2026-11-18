"""P1-406-001 general arrangement (front, plan, infeed end), -002 sections A-A at the head and B-B at the reject, metal-free zone, settings and fits."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
import model as M

C = calcs()
SS = "#f4f6f8"
BLU = "#dfe7f1"
UH = "#fbfbf6"
FRPC = "#f3e5ab"
HEADC = "#efefe6"
RED = "#ffcdd2"
JARC = "#e1f5fe"
JAR = CONT["jar-12"]
YI, YO = M.YI, M.YO
ZR0 = Z_BELT - BELT["t"] - UBED["t"] - FRP["h"]


def R(v, x0, x1, z0, z1, k="vis", fill="none"):
    v.rect(min(x0, x1), min(z0, z1), abs(x1 - x0), abs(z1 - z0), k, fill)


def front(v, mfz=True):
    """elevation from -y (operator side): x right, z up."""
    v.line(-900, 0, 900, 0, "phan"); v.text(-880, -18, "FLOOR", 11, "start")
    for sx in (-1, 1):
        R(v, sx * LEG["x"] - 20, sx * LEG["x"] + 20, LEG["z_foot"], Z_SIDE0 + 60, fill=SS)
        R(v, sx * LEG["x"] - 40, sx * LEG["x"] + 40, 0, 12, fill="#37474f"); v.line(sx * LEG["x"], 12, sx * LEG["x"], LEG["z_foot"] - 8, "vis")
        R(v, sx * LEG["x"] - 30, sx * LEG["x"] + 30, LEG["z_foot"] - 8, LEG["z_foot"], fill=SS)
        R(v, sx * LEG["x"] - 20, sx * LEG["x"] + 20, BRACE_Z - 20, BRACE_Z + 20, "hid")
        R(v, sx * SIDE["x0"], sx * SIDE["x1"], Z_SIDE0, Z_SIDE1, fill=SS)
        R(v, sx * PUL["x"] - M.EAR / 2, sx * PUL["x"] + M.EAR / 2, Z_SIDE1, Z_PUL + M.EAR / 2, fill=SS)
        R(v, sx * PUL["x"] - PUL["brg_sq"] / 2, sx * PUL["x"] + PUL["brg_sq"] / 2, Z_PUL - PUL["brg_sq"] / 2, Z_PUL + PUL["brg_sq"] / 2, fill="#cfd8dc")
        v.circle(sx * PUL["x"], Z_PUL, PUL["shaft"] / 2, "vis", "#fff"); v.cmark(sx * PUL["x"], Z_PUL, 50)
        for cx in (560.0, 660.0):
            R(v, sx * cx - 20, sx * cx + 20, Z_SIDE0, Z_SIDE0 + 40, "hid")
    R(v, -LEG["x"] - 20, LEG["x"] + 20, M.SPINE_Z - SPINE["h"] / 2, M.SPINE_Z + SPINE["h"] / 2, fill=SS)
    zb = M.SPINE_Z + SPINE["h"] / 2
    R(v, -40, 40, zb, zb + 40, fill=SS); R(v, -25, 25, zb + 40, HEAD["lug_z"] - 8, fill=SS); R(v, -60, 60, HEAD["lug_z"] - 8, HEAD["lug_z"], fill=SS)
    R(v, -HEAD["L"] / 2, HEAD["L"] / 2, HEAD["z0"], HEAD["z0"] + HEAD["H"], fill=HEADC)
    R(v, -HEAD["L"] / 2, HEAD["L"] / 2, HEAD["ap_z0"], HEAD["ap_z0"] + HEAD["ap_h"], "hid")
    v.text(0, HEAD["z0"] + HEAD["H"] - 60, "P1-418", 12); v.text(0, HEAD["z0"] + HEAD["H"] - 80, "HEAD", 10)
    R(v, -X_STATIC, X_STATIC, ZR0, ZR0 + FRP["h"], fill=FRPC); R(v, -UBED["x"], UBED["x"], ZR0 + FRP["h"], Z_BELT - BELT["t"], fill=UH)
    for sx in (-1, 1):
        R(v, sx * X_STATIC, sx * FRP["x"], ZR0, ZR0 + FRP["h"], "hid")
    R(v, -PUL["x"], PUL["x"], Z_BELT - BELT["t"], Z_BELT, fill="#90a4ae")
    R(v, -JAR["d"] / 2, JAR["d"] / 2, Z_BELT, Z_BELT + JAR["h"], "hid", JARC)
    for x0, x1 in ((-SIDE["x1"], -UBED["x"]), (UBED["x"], REJ["x"] - 70)):
        R(v, x0, x1, Z_BELT + 5, Z_BELT + 5 + GUIDE["h"], fill=UH)
    # reject: actuator end-on, bracket; bin behind
    R(v, BIN["x0"], BIN["x1"], BIN["z0"], BIN["z1"], "hid")
    R(v, REJ["x"] - 40, REJ["x"] + 40, Z_SIDE1 - 60, REJ["z"] + 25, fill=SS); v.circle(REJ["x"], REJ["z"], 18, "vis", "#263238")
    # gearmotor in front of the drive bearing
    R(v, PUL["x"] - 55, PUL["x"] + 55, Z_PUL - 55, Z_PUL + 55, fill="#c5cae9"); R(v, PUL["x"] - 42, PUL["x"] + 42, Z_PUL - 255, Z_PUL - 55, fill="#c5cae9")
    R(v, PUL["x"] - 15, PUL["x"] + 5, LEG["z_foot"] + 500, Z_PUL - 60, fill=SS)
    # controls box + operators
    R(v, ENC["x0"], ENC["x1"], ENC["z0"], ENC["z0"] + ENC["h"], fill="#cfd8dc")
    xm = (ENC["x0"] + ENC["x1"]) / 2
    for dz, r, col in ((200.0, 20.0, "#c62828"), (150.0, 11.0, "#43a047"), (110.0, 11.0, "#b71c1c"), (70.0, 11.0, "#263238")):
        v.circle(xm, ENC["z0"] + dz, r, "vis", col)
    # pole + beacon behind
    R(v, POLE["x"] - 12.7, POLE["x"] + 12.7, Z_SIDE1, Z_BELT + POLE["h"], fill=SS)
    for i, col in enumerate(("#a5d6a7", "#ffe082", "#ef9a9a")):
        R(v, POLE["x"] - 30, POLE["x"] + 30, Z_BELT + POLE["h"] + 20 + 60 * i, Z_BELT + POLE["h"] + 80 + 60 * i, fill=col)
    if mfz:
        for sx in (-1, 1):
            v.line(sx * X_STATIC, Z_BELT + 200, sx * X_STATIC, 1450, "phan"); v.line(sx * X_MOVING, Z_BELT + 200, sx * X_MOVING, 1400, "phan")
        v.text(0, 1470, f"STATIC METAL-FREE ZONE |x| < {X_STATIC:.0f}", 11)
        v.text(X_MOVING + 10, 1385, f"MOVING |x| < {X_MOVING:.0f}", 10, "start")


def plan(v):
    """from above: x right, y up (back)."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            R(v, sx * SIDE["x0"], sx * SIDE["x1"], sy * YI, sy * YO, fill=SS)
            R(v, sx * LEG["x"] - 20, sx * LEG["x"] + 20, sy * LEG["y"] - 20, sy * LEG["y"] + 20, fill=SS)
            R(v, sx * PUL["x"] - PUL["brg_sq"] / 2, sx * PUL["x"] + PUL["brg_sq"] / 2, sy * YO, sy * (YO + PUL["brg_t"]), fill="#cfd8dc")
        R(v, sx * SIDE["x0"], sx * (PUL["x"] - 38), -YI, YI, fill=SS)
    R(v, -PUL["x"] - 32, PUL["x"] + 32, -BELT["w"] / 2, BELT["w"] / 2, fill="#eceff1")
    for sy in (-1, 1):
        R(v, -FRP["x"], FRP["x"], sy * (FRP["y"] - FRP["w"] / 2), sy * (FRP["y"] + FRP["w"] / 2), "hid")
        g = sy * GUIDE["gap"]["J"] / 2
        for x0, x1 in ((-SIDE["x1"], -UBED["x"]), (UBED["x"], REJ["x"] - 70)):
            R(v, x0, x1, g, g + sy * GUIDE["t"], fill=UH)
    R(v, -HEAD["L"] / 2, HEAD["L"] / 2, -HEAD["W"] / 2, HEAD["W"] / 2, fill=HEADC)
    for sy in (-1, 1):
        R(v, -40, 40, sy * HEAD["lug_y"] - 30, sy * HEAD["lug_y"] + 30, fill=HEADC)
    R(v, -120, 120, -HEAD["W"] / 2 - 20, -HEAD["W"] / 2, fill="#bdbdbd"); v.text(0, -HEAD["W"] / 2 - 40, "HEAD CONTROL PANEL", 9)
    v.circle(0, 0, JAR["d"] / 2, "hid")
    # reject
    R(v, BIN["x0"], BIN["x1"], BIN["y0"], BIN["y1"], fill="#ffebee"); v.text((BIN["x0"] + BIN["x1"]) / 2, (BIN["y0"] + BIN["y1"]) / 2, "LOCKED BIN", 10)
    R(v, REJ["x"] - 18, REJ["x"] + 18, -YO - 255, -GUIDE["gap"]["J"] / 2 - 38, fill="#455a64")
    R(v, REJ["x"] - 40, REJ["x"] + 40, -YO - 266, -YO - 6, "hid")
    py0 = -GUIDE["gap"]["J"] / 2 - 18
    R(v, REJ["x"] - REJ["paddle_w"] / 2, REJ["x"] + REJ["paddle_w"] / 2, py0 - 20, py0, fill=UH)
    R(v, REJ["x"] - REJ["paddle_w"] / 2, REJ["x"] + REJ["paddle_w"] / 2, py0 - 20 + REJ["stroke"], py0 + REJ["stroke"], "phan")
    R(v, B1_X - 20, B1_X + 20, -YO - 50, -YO - 3, fill="#ffe082")
    # drive, box, pole
    yg = -(YO + PUL["brg_t"] + 8)
    R(v, PUL["x"] - 55, PUL["x"] + 55, yg - 85, yg, fill="#c5cae9"); v.circle(PUL["x"], yg - 42, 42, "hid")
    R(v, ENC["x0"], ENC["x1"], ENC["y0"], ENC["y1"], fill="#cfd8dc"); R(v, (ENC["x0"] + ENC["x1"]) / 2 - 20, (ENC["x0"] + ENC["x1"]) / 2 + 20, ENC["y0"] - 25, ENC["y0"], fill="#c62828")
    v.circle(POLE["x"], POLE["y"], 30, "vis", "#ef9a9a")
    v.centre(-PUL["x"] - 60, 0, PUL["x"] + 60, 0)
    v.line(-PUL["x"] - 40, -260, -PUL["x"] + 60, -260, "vis"); v.line(-PUL["x"] + 60, -260, -PUL["x"] + 40, -250, "vis"); v.line(-PUL["x"] + 60, -260, -PUL["x"] + 40, -270, "vis")
    v.text(-PUL["x"] + 10, -280, "FLOW", 11)


def endview(v):
    """infeed end, seen from -x: y right, z up."""
    v.line(-420, 0, 420, 0, "phan")
    zb = M.SPINE_Z + SPINE["h"] / 2
    R(v, -HEAD["W"] / 2, HEAD["W"] / 2, HEAD["z0"], HEAD["z0"] + HEAD["H"], fill=HEADC)
    R(v, -HEAD["ap_w"] / 2, HEAD["ap_w"] / 2, HEAD["ap_z0"], HEAD["ap_z0"] + HEAD["ap_h"], fill="#fff")
    for sy in (-1, 1):
        R(v, sy * HEAD["lug_y"] - 30, sy * HEAD["lug_y"] + 30, HEAD["lug_z"], HEAD["lug_z"] + 10, fill=HEADC)
        R(v, sy * HEAD["lug_y"] - 25, sy * HEAD["lug_y"] + 25, zb + 40, HEAD["lug_z"] - 8, fill=SS)
        R(v, sy * HEAD["lug_y"] - 35, sy * HEAD["lug_y"] + 35, HEAD["lug_z"] - 8, HEAD["lug_z"], fill=SS)
    R(v, -STAND["beam_y"], STAND["beam_y"], zb, zb + 40, fill=SS)
    R(v, BIN["y0"], BIN["y1"], BIN["z0"], BIN["z1"], "hid")
    for sy in (-1, 1):
        R(v, sy * LEG["y"] - 20, sy * LEG["y"] + 20, LEG["z_foot"], Z_SIDE0 + 60, fill=SS)
        R(v, sy * LEG["y"] - 40, sy * LEG["y"] + 40, 0, 12, fill="#37474f")
        R(v, sy * YI, sy * YO, Z_SIDE0, Z_SIDE1, fill=SS)
        R(v, sy * YO, sy * (YO + PUL["brg_t"]), Z_PUL - PUL["brg_sq"] / 2, Z_PUL + PUL["brg_sq"] / 2, fill="#cfd8dc")
        R(v, sy * YO, sy * (YO + 30), Z_PUL - 15, Z_PUL + 15, fill=SS)
    R(v, -LEG["y"] + 20, LEG["y"] - 20, BRACE_Z - 20, BRACE_Z + 20, fill=SS)
    R(v, -SPINE["w"] / 2, SPINE["w"] / 2, M.SPINE_Z - SPINE["h"] / 2, M.SPINE_Z + SPINE["h"] / 2, fill=SS)
    R(v, -PUL["face"] / 2, PUL["face"] / 2, Z_PUL - PUL["d"] / 2, Z_PUL + PUL["d"] / 2, fill="#cfd8dc")
    R(v, -(YO + PUL["brg_t"] + 8), YO + PUL["brg_t"] + 8, Z_PUL - PUL["shaft"] / 2, Z_PUL + PUL["shaft"] / 2, fill=SS)
    R(v, -BELT["w"] / 2, BELT["w"] / 2, Z_BELT - BELT["t"], Z_BELT, fill="#90a4ae")
    for sy in (-1, 1):
        g = sy * GUIDE["gap"]["J"] / 2
        R(v, g, g + sy * GUIDE["t"], Z_BELT + 5, Z_BELT + 5 + GUIDE["h"], fill=UH)
    R(v, -JAR["d"] / 2, JAR["d"] / 2, Z_BELT, Z_BELT + JAR["h"], "hid", JARC)
    R(v, ENC["y0"], ENC["y1"], ENC["z0"], ENC["z0"] + ENC["h"], fill="#cfd8dc")
    for dz, r in ((200.0, 20.0), (150.0, 11.0), (110.0, 11.0), (70.0, 11.0)):
        R(v, ENC["y0"] - 25, ENC["y0"], ENC["z0"] + dz - r, ENC["z0"] + dz + r, fill="#263238")
    R(v, POLE["y"] - 12.7, POLE["y"] + 12.7, Z_SIDE0 - 120, Z_BELT + POLE["h"], fill=SS)
    for i, col in enumerate(("#a5d6a7", "#ffe082", "#ef9a9a")):
        R(v, POLE["y"] - 30, POLE["y"] + 30, Z_BELT + POLE["h"] + 20 + 60 * i, Z_BELT + POLE["h"] + 80 + 60 * i, fill=col)


def ga():
    MB = 8.5 * 0 + 30.0 + 7.0 + 6.5 + 1.5 + 4.0 + 0.6 + 1.5 + 1.0     # head (used, ≈ 30), belt+bearings, gearmotor, pusher, box, sensors, beacon, feet
    S = sheet("P1-406-001", "DETECTOR CONVEYOR: GENERAL ARRANGEMENT", scale="1:5 · 1:8", material="SS 304 frame; FRP rails + UHMW bed in the head zone; PU belt", finish=FIN_NPC,
              mass=f"{sum(MASS.values()) + MB:.0f} kg [{(sum(MASS.values()) + MB) * 2.2046:.0f} lb] with bought parts")
    s = SC(5)
    v = S.view(820, 1560, s, "FRONT VIEW (1:5), FROM THE OPERATOR SIDE", (820, 130))
    front(v)
    v.dim((-SIDE["x1"], 0), (SIDE["x1"], 0), -60, None, "h")
    v.dim((-PUL["x"], Z_PUL), (PUL["x"], Z_PUL), -150, f"PULLEYS {PUL['x'] * 2:.0f} [{fin(PUL['x'] * 2)}] CTRS", "h")
    v.dim((SIDE["x1"], 0), (SIDE["x1"], Z_BELT), -140, f"BELT TOP {mmi(Z_BELT)} ±25 (FEET)", "v")
    v.dim((-HEAD["L"] / 2, HEAD["ap_z0"]), (-HEAD["L"] / 2, HEAD["ap_z0"] + HEAD["ap_h"]), 120, "APERTURE H", "v")
    for n, at, to in ((1, (-600, Z_SIDE1 - 30), (-860, 1000)), (2, (520, Z_SIDE1 - 30), (860, 1040)), (3, (-300, M.SPINE_Z), (-300, 120)), (4, (0, 500), (180, 380)),
                      (5, (PUL["x"], Z_PUL + 20), (860, 900)), (6, (-PUL["x"], Z_PUL + 20), (-860, 900)), (8, (-300, ZR0 + 20), (-300, 760)),
                      (10, (300, ZR0 + FRP["h"] + 5), (300, 780)), (11, (-560, Z_BELT + 25), (-560, 1110)), (20, (0, 1150), (300, 1300)),
                      (22, (PUL["x"], Z_PUL - 150), (860, 640)), (23, (REJ["x"], REJ["z"]), (560, 1220)), (15, (BIN["x1"] - 10, 600), (860, 520)),
                      (24, (ENC["x0"] + 20, 640), (-860, 640)), (26, (POLE["x"], Z_BELT + POLE["h"] + 100), (-860, 1500)), (27, (LEG["x"], 6), (860, 80))):
        v.tag(*to, n, at)
    vp = S.view(2350, 470, SC(8), "PLAN (1:8)", (2350, 130))
    plan(vp)
    vp.dim((-SIDE["x1"], -YO), (SIDE["x1"], -YO), -120, None, "h")
    vp.dim((SIDE["x1"], -YO), (SIDE["x1"], YO), -60, f"{YO * 2:.0f} FRAME", "v")
    vp.dim((BIN["x1"], BIN["y0"]), (BIN["x1"], BIN["y1"]), -40, None, "v")
    for n, at, to in ((13, (REJ["x"], -YO - 30), (500, -400)), (14, (REJ["x"], -GUIDE["gap"]["J"] / 2 - 25), (300, -400)), (25, (B1_X, -YO - 30), (700, -400)),
                      (12, (-520, -YO), (-700, -400)), (21, (-PUL["x"], YO + 10), (-860, 300))):
        vp.tag(*to, n, at)
    ve = S.view(3050, 1560, SC(8), "INFEED END VIEW (1:8), FROM -X", (3050, 700))
    endview(ve)
    ve.dim((-LEG["y"], 0), (LEG["y"], 0), -40, None, "h"); ve.dim((-HEAD["ap_w"] / 2, HEAD["ap_z0"] + HEAD["ap_h"]), (HEAD["ap_w"] / 2, HEAD["ap_z0"] + HEAD["ap_h"]), 30, "APERTURE W", "h")
    ve.dim((-HEAD["W"] / 2, HEAD["z0"]), (-HEAD["W"] / 2, HEAD["z0"] + HEAD["H"]), 40, None, "v")
    S.table(1300, 1660, [("ITEM", 50), ("PART", 120), ("DESCRIPTION", 300), ("QTY", 40), ("SEE", 180)], ITEMS[:14], "ITEM LIST (1)", 11, 19)
    S.table(1900, 1660, [("ITEM", 50), ("PART", 120), ("DESCRIPTION", 300), ("QTY", 40), ("SEE", 180)], ITEMS[14:], "ITEM LIST (2)", 11, 19)
    S.table(120, 1840, [("INTERFACE", 220), ("VALUE", 560), ("SET BY", 320)], [
        ("Floor", f"belt top {Z_BELT:.0f} [{fin(Z_BELT)}] AFF on 4 levelling feet ±25", "level to the labeler table"),
        ("Packs", f"shaker Ø{CONT['shaker-250']['d']:.0f} x {CONT['shaker-250']['h']:.1f}; jar Ø{JAR['d']:.1f} x {JAR['h']:.1f}, upright, closed", "guides at S or J"),
        ("Rate", f"{RATE:.0f} packs / min, belt {C['v']:.0f} mm/s ({C['v_mpm']:.1f} m/min)", "fixed-speed gearmotor"),
        ("Power", f"120 V 1-ph: controls cord {ELE['A']:.1f} A; head on its own dedicated receptacle (clean power)", "plant circuits"),
    ], "INTERFACES", 12, 22)
    S.save(DWG / "P1-406-001_general_arrangement.svg")


def section():
    S = sheet("P1-406-002", "SECTIONS, METAL-FREE ZONE, SETTINGS", scale="1:2 · 1:10", material="see 001", finish=FIN_NPC, mass="-")
    s = SC(2)
    # section A-A at x 0, seen from +x (y left = +y?) -> draw y right as seen from -x
    v = S.view(900, 1350 + 720 * s, s, "SECTION A-A (1:2) AT X 0, SEEN FROM THE INFEED", (900, 130))
    zb = M.SPINE_Z + SPINE["h"] / 2
    v.rect(-HEAD["W"] / 2, HEAD["z0"], HEAD["W"], HEAD["H"], "vis", "url(#hA)")
    R(v, -HEAD["ap_w"] / 2, HEAD["ap_w"] / 2, HEAD["ap_z0"], HEAD["ap_z0"] + HEAD["ap_h"], fill="#fff")
    v.text(0, HEAD["z0"] + HEAD["H"] - 40, "HEAD P1-418 (SECTIONED, SCHEMATIC: COIL HOUSING)", 11)
    for sy in (-1, 1):
        R(v, sy * HEAD["lug_y"] - 30, sy * HEAD["lug_y"] + 30, HEAD["lug_z"], HEAD["lug_z"] + 10, fill=HEADC)
        R(v, sy * HEAD["lug_y"] - 35, sy * HEAD["lug_y"] + 35, HEAD["lug_z"] - 8, HEAD["lug_z"], fill=SS)
        R(v, sy * HEAD["lug_y"] - 25, sy * HEAD["lug_y"] + 25, 725, HEAD["lug_z"] - 8, fill=SS)
        v.line(sy * HEAD["lug_y"] - 35, 725, sy * HEAD["lug_y"] + 35, 725, "thin")
    v.text(0, 735, "POSTS CONTINUE DOWN TO THE STAND BEAM AND SPINE (SHEET 100)", 10)
    R(v, HEAD["lug_y"] - 35, HEAD["lug_y"] + 35, HEAD["lug_z"] - 14, HEAD["lug_z"] - 8, fill="#a1887f")
    v.leader((HEAD["lug_y"] + 35, HEAD["lug_z"] - 11), (HEAD["lug_y"] + 110, HEAD["lug_z"] - 80), ["G10 PAD 6 + NYLON BUSHES: BREAKS THE LOOP", "HEAD - STAND - SPINE (+y SIDE ONLY)"], 11)
    for sy in (-1, 1):
        R(v, sy * (FRP["y"] - FRP["w"] / 2), sy * (FRP["y"] + FRP["w"] / 2), ZR0, ZR0 + FRP["h"], fill="url(#hA)")
    R(v, -UBED["w"] / 2, UBED["w"] / 2, ZR0 + FRP["h"], Z_BELT - BELT["t"], fill=UH)
    R(v, -BELT["w"] / 2, BELT["w"] / 2, Z_BELT - BELT["t"], Z_BELT, fill="#607d8b")
    R(v, -JAR["d"] / 2, JAR["d"] / 2, Z_BELT, Z_BELT + JAR["h"], "vis", JARC)
    sh = CONT["shaker-250"]; R(v, -sh["d"] / 2, sh["d"] / 2, Z_BELT, Z_BELT + sh["h"], "phan")
    v.dim((-HEAD["ap_w"] / 2, HEAD["ap_z0"]), (HEAD["ap_w"] / 2, HEAD["ap_z0"]), -40, f"APERTURE {HEAD['ap_w']:.0f} [{fin(HEAD['ap_w'])}] (CONFIRM)", "h")
    v.dim((HEAD["ap_w"] / 2, HEAD["ap_z0"]), (HEAD["ap_w"] / 2, HEAD["ap_z0"] + HEAD["ap_h"]), -60, None, "v")
    v.dim((-HEAD["ap_w"] / 2, Z_BELT + JAR["h"]), (-HEAD["ap_w"] / 2, HEAD["ap_z0"] + HEAD["ap_h"]), 40, f"{C['jar-12']['clear']:.0f} CLEAR (JAR)", "v")
    v.dim((-FRP["y"] - FRP["w"] / 2, ZR0), (FRP["y"] + FRP["w"] / 2, ZR0), -100, None, "h")
    v.dim((-UBED["w"] / 2, Z_BELT), (-UBED["w"] / 2, ZR0), 120, None, "v")
    v.dim((-HEAD["W"] / 2, HEAD["lug_z"]), (-HEAD["W"] / 2, HEAD["ap_z0"]), 60, f"AP. BOTTOM {mmi(HEAD['ap_z0'])} AFF", "v")
    v.dim((-HEAD["lug_y"], HEAD["lug_z"] - 8), (HEAD["lug_y"], HEAD["lug_z"] - 8), -80, "LUGS (CONFIRM)", "h")
    v.leader((FRP["y"], ZR0 + 15), (220, 820), [f"FRP RAIL {FRP['h']:.1f} x {FRP['w']:.2f} x {FRP['t']:.1f} [1-1/2 x 3/4 x 1/8 in] ON EDGE", "NYLON SCREWS M5 TO THE BED (H5)"], 11)
    v.leader((40, Z_BELT - 6), (220, 870), [f"UHMW BED {UBED['t']:.0f} x {UBED['w']:.0f} ; BELT PU {BELT['t']:.0f}"], 11)
    v.note(-HEAD["W"] / 2, 700, ["Nothing metal inside the aperture or within the metal-free zone: belt, bed, rails and screws are all non-metal.",
                                  "Jar shown (solid) and shaker (phantom): both centred in the aperture height within 16 mm."], 11)
    # section B-B at the reject, x 640
    v2 = S.view(2350, 1450 + 500 * s, s, f"SECTION B-B (1:2) AT X {REJ['x']:.0f}: REJECT STATION", (2350, 130))
    for sy in (-1, 1):
        R(v2, sy * YI, sy * YO, Z_SIDE0, Z_SIDE1, fill="url(#hA)")
    R(v2, -YI, YI, Z_SIDE1 - BED_SS["t"], Z_SIDE1, fill="url(#hA)")
    R(v2, -BELT["w"] / 2, BELT["w"] / 2, Z_BELT - BELT["t"], Z_BELT, fill="#607d8b")
    R(v2, -YI, YI, Z_SIDE0, Z_SIDE0 + 40, "hid")
    py0 = -GUIDE["gap"]["J"] / 2 - 18
    R(v2, py0 - 20, py0, Z_BELT + 6, Z_BELT + 6 + REJ["paddle_h"], fill=UH)
    R(v2, py0 - 20 + REJ["stroke"], py0 + REJ["stroke"], Z_BELT + 6, Z_BELT + 6 + REJ["paddle_h"], "phan")
    R(v2, -YO - 255, py0 - 20, REJ["z"] - 18, REJ["z"] + 18, fill="#455a64")
    R(v2, -YO - 266, -YO - 6, REJ["z"] - 35, REJ["z"] - 29, fill=SS); R(v2, -YO - 266, -YO - 260, REJ["z"] - 35, REJ["z"] + 15, fill=SS)
    R(v2, -YO - 6, -YO, Z_SIDE1 - 60, REJ["z"] + 25, fill=SS)
    R(v2, -JAR["d"] / 2, JAR["d"] / 2, Z_BELT, Z_BELT + JAR["h"], "vis", JARC)
    R(v2, -JAR["d"] / 2 + REJ["stroke"] + 40, JAR["d"] / 2 + REJ["stroke"] + 40, Z_BELT - 160, Z_BELT - 160 + JAR["h"], "phan")
    R(v2, BIN["y0"], BIN["y1"], BIN["z0"], BIN["z1"], "vis")
    R(v2, BIN["y0"] - 1, BIN["y0"] + BIN["t"] + 1, Z_BELT - 5, Z_BELT - 5 + BIN["slot_h"], fill="#fff")
    R(v2, BIN["y0"] - 2, BIN["y1"] + 20, BIN["z1"], BIN["z1"] + 2, fill=SS)
    v2.leader((BIN["y1"] - 40, BIN["z1"] + 2), (180, BIN["z1"] + 160), ["LID, HINGED AT +y, PADLOCK HASP (QA KEY); REED SWITCH B3 = LID SHUT"], 11)
    v2.leader((BIN["y0"], Z_BELT + 50), (180, BIN["z1"] + 110), [f"SLOT {BIN['slot_w']:.0f} x {BIN['slot_h']:.0f}; B2 EYE ACROSS THE SLOT (ENTRY CONFIRM)"], 11)
    v2.leader((-YO - 100, REJ["z"]), (-YO - 200, REJ["z"] + 150), [f"PUSHER P1-421: {REJ['stroke']:.0f} STROKE, ≈ {REJ['speed']:.0f} mm/s"], 11)
    v2.leader((-YO - 3, Z_BELT + 40), (-YO - 200, Z_BELT + 250), ["B1 EYE (PACK AT REJECT), REFLECTOR ON THE +y PLATE"], 11)
    v2.dim((py0, Z_BELT + 90), (py0 + REJ["stroke"], Z_BELT + 90), 40, None, "h")
    v2.dim((-YO, Z_SIDE0 - 10), (YO, Z_SIDE0 - 10), -40, None, "h")
    v2.dim((BIN["y1"], BIN["z0"]), (BIN["y1"], BIN["z1"]), -40, None, "v")
    v2.dim((BIN["y0"], BIN["z0"]), (BIN["y1"], BIN["z0"]), -40, None, "h")
    v2.note(-YO - 270, BIN["z0"] - 80, ["Hooks on the bin hang it on the +y side plate top edge; 2 screws (H8) stop it lifting.",
                                         "Bin 1.5 304, all seams welded; holds ≈ 20 jars; empty only under QA (CCP-1 record)."], 11)
    # MFZ diagram 1:10
    s10 = SC(10)
    v3 = S.view(1250, 2150, s10, "METAL-FREE ZONE (1:10), ELEVATION", (1250, 1600))
    for sx in (-1, 1):
        v3.rect(min(sx * X_STATIC, sx * X_MOVING), Z_BELT - 200, abs(X_MOVING - X_STATIC), 500, "thin", "#fff3e0")
    v3.rect(-X_STATIC, Z_BELT - 200, 2 * X_STATIC, 500, "thin", "#ffebee")
    R(v3, -HEAD["L"] / 2, HEAD["L"] / 2, HEAD["z0"], HEAD["z0"] + HEAD["H"], fill=HEADC)
    R(v3, -PUL["x"], PUL["x"], Z_BELT - BELT["t"], Z_BELT, fill="#607d8b")
    for sx in (-1, 1):
        v3.circle(sx * PUL["x"], Z_PUL, PUL["d"] / 2, "vis", "#cfd8dc"); R(v3, sx * SIDE["x0"], sx * SIDE["x1"], Z_SIDE0, Z_SIDE1, fill=SS)
    v3.dim((-HEAD["L"] / 2, Z_BELT + 300), (-X_STATIC, Z_BELT + 300), 20, f"1.5 x {HEAD['ap_h']:.0f} = {MFZ['static']:.0f}", "h")
    v3.dim((HEAD["L"] / 2, Z_BELT + 300), (X_MOVING, Z_BELT + 300), 20, f"2 x {HEAD['ap_h']:.0f} = {MFZ['moving']:.0f}", "h")
    v3.note(-PUL["x"] - 40, Z_BELT - 260, ["red: no metal at all (static or moving); orange: static metal only (frame, guides, bin); pulleys, motor and pusher outside.",
                                           "Rule from the head maker (confirm for the actual head): static 1.5 x aperture height, moving 2 x, from each face."], 11)
    rows = [(k, c["setting"], f"{c['d']:.1f} x {c['h']:.1f}", f"{C[k]['guide']:.1f}", f"{mmi(C[k]['top'], 1)}", f"{C[k]['clear']:.0f}", f"{C[k]['centre_off']:+.0f}")
            for k, c in CONT.items()]
    S.table(2200, 1560, [("PACK", 150), ("SET", 50), ("Ø x H", 130), ("GUIDE GAP", 110), ("TOP z", 170), ("TOP CLEAR", 100), ("CENTRE vs AP.", 120)],
            rows, "S / J SETTINGS (guides on the end frames only)", 12, 22)
    S.table(2200, 1680, [("FIT", 240), ("WHERE", 420), ("LIMITS", 300)], [
        ("Ø20 k6 / UC204 bore", "pulley shaft journals (set screw insert)", "20.002 / 20.015"),
        ("Ø20 h7 + key 6 / gearmotor bore", "drive shaft end, -y", "19.979 / 20.000"),
        ("Ø56 H7 / Ø20 shaft", "pulley end discs on the shaft, welded", "56 drum disc bore on Ø20: 20 H7 20.000 / 20.021"),
        ("Crown 0.5 on Ø", "both pulleys, tracks the belt", "Ø60.0 centre, Ø59.0 at the edges"),
    ], "FITS", 12, 22)
    S.save(DWG / "P1-406-002_sections.svg")


if __name__ == "__main__":
    ga(); section()
