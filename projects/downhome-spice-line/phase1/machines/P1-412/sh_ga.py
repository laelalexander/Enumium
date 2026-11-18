"""P1-412-001 general arrangement (front, side, plan), -002 section A-A on the spindle and details."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
import model as M

C = calcs()
SS = "#f4f6f8"
BLU = "#dfe7f1"
UH = "#fbfbf6"
PC = "#e3f2fd"
ZS = Z_SHELF_UP
ZD = z_shelf_down("shaker-250")
PIN_UP, END_UP = M.lever_pts(True)
PIN_DN, END_DN = M.lever_pts(False)
JAR = CONT["jar-12"]
SHK = CONT["shaker-250"]
XF_J = vb_face(JAR["d"])
XF_S = vb_face(SHK["d"])


def R(v, x0, x1, z0, z1, k="vis", fill="none"):
    v.rect(min(x0, x1), min(z0, z1), abs(x1 - x0), abs(z1 - z0), k, fill)


def jar_ph(v, xc=0.0, c=JAR):
    R(v, xc - c["d"] / 2, xc + c["d"] / 2, Z_STAND, Z_STAND + c["h"], "phan")
    R(v, xc - c["cap_d"] / 2 - 1, xc + c["cap_d"] / 2 + 1, Z_STAND + c["h"], Z_STAND + c["h"] + c["cap_h"], "phan")


def front(v, zs=ZS, section=False):
    """front elevation, looking +y (x right, z up)."""
    v.line(-260, 0, 260, 0, "phan"); v.text(-235, -18, "BENCH TBL-1 (914 [35.98] AFF)", 11, "start")
    R(v, -BASE["w"] / 2, BASE["w"] / 2, 0, BASE["t"], fill=SS)
    for sx in (-1, 1):                                                       # gussets (plane y 125, seen flat)
        v.poly([(sx * COL["a"] / 2, Z_COL0), (sx * (COL["a"] / 2 + GUS["a"]), Z_COL0), (sx * COL["a"] / 2, Z_COL0 + GUS["a"])], fill=SS)
    R(v, -COL["a"] / 2, COL["a"] / 2, Z_COL0, Z_COL1, fill=SS)
    R(v, CAPPL["x0"], CAPPL["x1"], Z_COL1, Z_CAP, fill=SS)
    R(v, CLEV["x"], CLEV["x"] + CLEV["t"], Z_CAP, Z_CAP + CLEV["h"], fill=SS)
    R(v, -RSB["w"] / 2, RSB["w"] / 2, RSB["z0"], RSB["z0"] + RSB["L"], "hid")
    # carriage
    R(v, -CAR["w"] / 2, CAR["w"] / 2, zs + CAR["sh_t"], zs + CAR["sh_t"] + CAR["h"], fill=SS)
    R(v, CAR["sh_x0"], CAR["sh_x1"], zs, zs + CAR["sh_t"], fill=SS)
    R(v, CAR["lug_x"] - 5, CAR["lug_x"] + 5, zs + CAR["sh_t"], zs + Z_LUGPIN + 15, fill=SS)
    # gearmotor
    R(v, -GM["body_d"] / 2, GM["body_d"] / 2, zs + CAR["sh_t"], zs + CAR["sh_t"] + 40, fill=BLU)
    R(v, -36, 36, zs + CAR["sh_t"] + 40, zs + CAR["sh_t"] + GM["body_h"], fill=BLU)
    R(v, -25, 25, zs + CAR["sh_t"] + 120, zs + CAR["sh_t"] + 180, fill=BLU)
    # guard, chuck, clutch (behind the clear guard)
    R(v, -GUARD["r_bolt"] - 10, GUARD["r_bolt"] + 10, zs - 16, zs - 10, fill=PC)
    R(v, -GUARD["d"] / 2, GUARD["d"] / 2, zs - GUARD["h"], zs - 16, fill=PC)
    R(v, -CLU["d"] / 2, CLU["d"] / 2, zs - CLU["L"], zs, "thin", BLU)
    R(v, -CHK["d"] / 2, CHK["d"] / 2, zs - STACK, zs - STACK + CHK["h"], "thin", SS)
    # link + lever (lever along y: seen end-on at x 82)
    R(v, PIV["x"] - 5, PIV["x"] + 5, zs + Z_LUGPIN, PIN_UP[2] if zs == ZS else PIN_DN[2], fill=SS)
    zl0, zl1 = PIV["z"] - 15, (END_UP[2] if zs == ZS else END_DN[2]) + 12
    R(v, LEV["x"] - LEV["t"] / 2, LEV["x"] + LEV["t"] / 2, min(zl0, zl1), max(zl0, zl1), fill=SS)
    e = END_UP if zs == ZS else END_DN
    R(v, e[0] + 5, e[0] + 45, e[2] - 16, e[2] + 16, fill="#263238")
    v.circle(PIV["x"] + CLEV["t"] + 6, PIV["z"], 6, "thin")
    # gas spring, stop rod + flip block
    R(v, GAS["x"] - 11, GAS["x"] + 11, GAS["z_lo"], GAS["z_lo"] + 190, fill=BLU)
    R(v, GAS["x"] - 5, GAS["x"] + 5, GAS["z_lo"] + 190, zs, fill=SS)
    R(v, GAS["x"] - 30, GAS["x"] + 30, BASE["t"], BASE["t"] + 4, fill=SS)
    R(v, STOP["x"] - 8, STOP["x"] + 8, BASE["t"], ZD, fill=SS)
    R(v, STOP["x"] + 10, STOP["x"] + 40, ZD - STOP["flip_t"] + 10, ZD + 10, fill=SS)
    # nest, V-block (J), pad, clamp, bracket
    R(v, -95, 110, BASE["t"], Z_STAND, fill=UH)
    R(v, XF_J, XF_J + VB["t"], Z_STAND, Z_STAND + VB["h"], fill=UH)
    v.line(XF_J + VB["depth"], Z_STAND, XF_J + VB["depth"], Z_STAND + VB["h"], "hid")
    xp = -JAR["d"] / 2
    R(v, xp - PAD["t"], xp, Z_STAND + 20, Z_STAND + 20 + PAD["h"], fill=UH)
    R(v, -195, -125, BASE["t"], BASE["t"] + 6, fill=SS); R(v, -131, -125, BASE["t"], BASE["t"] + 70, fill=SS)
    R(v, -195, -137, BASE["t"] + 30, BASE["t"] + 66, fill="#263238")
    R(v, -137, xp - PAD["t"], BASE["t"] + 43, BASE["t"] + 53, fill=SS)
    v.poly([(-172, BASE["t"] + 66), (-218, BASE["t"] + 140), (-206, BASE["t"] + 146), (-162, BASE["t"] + 70)], fill="#263238")
    # enclosure + E-stop + selector (front-left)
    R(v, M.ENC["x0"], M.ENC["x1"], BASE["t"], BASE["t"] + M.ENC["h"], fill="#cfd8dc")
    for k, (x, z) in M.ENC_OPS.items():
        v.circle(x, BASE["t"] + z, {"estop": 20, "pot": 8}.get(k, 11), "vis", {"estop": "#c62828", "lamp": "#43a047"}.get(k, "#263238"))
    # limit switch on the column (left face), struck by the carriage plate top
    R(v, -40, -26, ZS + CAR["sh_t"] + CAR["h"] + 6, ZS + CAR["sh_t"] + CAR["h"] + 46, fill="#ffca28")
    jar_ph(v)
    v.centre(0, -20, 0, 640)


def side(v, zs=ZS):
    """right side view, looking -x (y right = toward the column, z up)."""
    v.line(-300, 0, 200, 0, "phan")
    R(v, BASE["y0"], BASE["y0"] + BASE["d"], 0, BASE["t"], fill=SS)
    R(v, COL["y"] - COL["a"] / 2, COL["y"] + COL["a"] / 2, Z_COL0, Z_COL1, fill=SS)
    R(v, COL["y"] - 3, COL["y"] + 3, Z_COL0, Z_COL0 + GUS["a"], fill=SS)
    R(v, CAPPL["y0"], CAPPL["y1"], Z_COL1, Z_CAP, fill=SS)
    v.poly([(CLEV["y0"], Z_CAP), (CLEV["y1"], Z_CAP), (CLEV["y1"], Z_CAP + CLEV["h"] - 20), (CLEV["y1"] - 20, Z_CAP + CLEV["h"]), (CLEV["y0"] + 20, Z_CAP + CLEV["h"]),
            (CLEV["y0"], Z_CAP + CLEV["h"] - 20)], fill=SS)
    v.circle(PIV["y"], PIV["z"], 5, "vis", "#fff")
    R(v, Y_RSB, Y_COLF, RSB["z0"], RSB["z0"] + RSB["L"], fill=SS)
    R(v, Y_RSB - RAIL["h"], Y_RSB, RAIL["z0"], RAIL["z0"] + RAIL["L"], fill=BLU)
    zb = zs + CAR["sh_t"] + CAR["h"] / 2
    R(v, Y_BLK, Y_RSB - 4, zb - BLK["L"] / 2, zb + BLK["L"] / 2, fill=BLU)
    R(v, Y_BLK - CAR["t"], Y_BLK, zs + CAR["sh_t"], zs + CAR["sh_t"] + CAR["h"], fill=SS)
    R(v, SHELF_Y0, Y_BLK, zs, zs + CAR["sh_t"], fill=SS)
    v.poly([(Y_BLK - CAR["t"], zs + CAR["sh_t"]), (Y_BLK - CAR["t"] - CAR["gus"], zs + CAR["sh_t"]), (Y_BLK - CAR["t"], zs + CAR["sh_t"] + CAR["gus"])], fill=SS)
    R(v, -GM["body_d"] / 2, GM["body_d"] / 2, zs + CAR["sh_t"], zs + CAR["sh_t"] + 40, fill=BLU)
    R(v, -36, 36, zs + CAR["sh_t"] + 40, zs + CAR["sh_t"] + GM["body_h"], fill=BLU)
    R(v, -60, -36, zs + CAR["sh_t"] + 120, zs + CAR["sh_t"] + 180, fill=BLU)
    R(v, -GUARD["r_bolt"] - 10, GUARD["r_bolt"] + 10, zs - 16, zs - 10, fill=PC)
    R(v, -GUARD["d"] / 2, GUARD["d"] / 2, zs - GUARD["h"], zs - 16, fill=PC)
    R(v, -CLU["d"] / 2, CLU["d"] / 2, zs - CLU["L"], zs, "thin", BLU)
    R(v, -CHK["d"] / 2, CHK["d"] / 2, zs - STACK, zs - STACK + CHK["h"], "thin", SS)
    # link and lever
    pin, end = (PIN_UP, END_UP) if zs == ZS else (PIN_DN, END_DN)
    v.poly([(CAR["lug_y"] - 15, zs + CAR["sh_t"]), (CAR["lug_y"] + 15, zs + CAR["sh_t"]), (CAR["lug_y"] + 15, zs + Z_LUGPIN + 15), (CAR["lug_y"] - 15, zs + Z_LUGPIN + 15)], fill=SS)
    v.poly([(CAR["lug_y"] - 5, zs + Z_LUGPIN), (CAR["lug_y"] + 5, zs + Z_LUGPIN), (pin[1] + 5, pin[2]), (pin[1] - 5, pin[2])], fill=SS)
    th = math.atan2(end[2] - PIV["z"], end[1] - PIV["y"])
    n = (-math.sin(th) * LEV["w"] / 2, math.cos(th) * LEV["w"] / 2)
    a = (PIV["y"] - 25 * math.cos(th), PIV["z"] - 25 * math.sin(th))
    v.poly([(a[0] + n[0], a[1] + n[1]), (end[1] + n[0], end[2] + n[1]), (end[1] - n[0], end[2] - n[1]), (a[0] - n[0], a[1] - n[1])], fill=SS)
    v.circle(end[1], end[2], 16, "vis", "#263238")
    for p in (pin, (0, PIV["y"], PIV["z"])):
        v.circle(p[1], p[2], 4, "thin", "#fff")
    # gas spring (y 50), stop rod (y 62)
    R(v, GAS["y"] - 11, GAS["y"] + 11, GAS["z_lo"], GAS["z_lo"] + 190, "hid")
    R(v, STOP["y"] - 8, STOP["y"] + 8, BASE["t"], ZD, fill=SS)
    R(v, STOP["y"] - 12, STOP["y"] + 12, ZD - STOP["flip_t"] + 10, ZD + 10, fill=SS)
    # nest, V-block, enclosure (front), pad/clamp hidden behind the V-block
    R(v, -70, 70, BASE["t"], Z_STAND, fill=UH)
    R(v, -VB["L"] / 2, VB["L"] / 2, Z_STAND, Z_STAND + VB["h"], fill=UH)
    R(v, M.ENC["y0"], M.ENC["y1"], BASE["t"], BASE["t"] + M.ENC["h"], fill="#cfd8dc")
    R(v, M.ENC["y0"] - 32, M.ENC["y0"], BASE["t"] + M.ENC_OPS["estop"][1] - 20, BASE["t"] + M.ENC_OPS["estop"][1] + 20, fill="#c62828")
    jar_ph(v)
    v.centre(0, -20, 0, 640)


def plan(v):
    """plan, looking down (x right, y up)."""
    rr = lambda x0, x1, y0, y1, k="vis", fill="none": R(v, x0, x1, y0, y1, k, fill)
    rr(-BASE["w"] / 2, BASE["w"] / 2, BASE["y0"], BASE["y0"] + BASE["d"], fill=SS)
    for x, y in M.BASE_HOLES:
        v.circle(x, y, BASE["hole"] / 2, "thin", "#fff")
    rr(-95, 110, -70, 70, fill=UH)
    v.poly([(XF_J, -VB["L"] / 2), (XF_J + VB["t"], -VB["L"] / 2), (XF_J + VB["t"], VB["L"] / 2), (XF_J, VB["L"] / 2), (XF_J, VB["depth"]), (XF_J + VB["depth"], 0),
            (XF_J, -VB["depth"])], fill=UH)
    for x, y in M.VB_HOLES["J"]:
        v.circle(x, y, 7.5, "thin")
    for x, y in M.VB_HOLES["S"]:
        v.circle(x, y, 3.4, "hid")
    xp = -JAR["d"] / 2
    v.poly([(xp - PAD["t"], -PAD["w"] / 2), (xp, -PAD["w"] / 2), (xp, -16), (xp - 8, 0), (xp, 16), (xp, PAD["w"] / 2), (xp - PAD["t"], PAD["w"] / 2)], fill=UH)
    rr(-195, -125, -30, 30, fill=SS)
    rr(-195, -137, -12, 12, fill="#263238")
    rr(-137, xp - PAD["t"], -5, 5, fill=SS)
    rr(M.ENC["x0"], M.ENC["x1"], M.ENC["y0"], M.ENC["y1"], fill="#cfd8dc")
    rr(M.ENC_OPS["estop"][0] - 20, M.ENC_OPS["estop"][0] + 20, M.ENC["y0"] - 32, M.ENC["y0"], fill="#c62828")
    v.circle(STOP["x"], STOP["y"], 8, "hid"); v.circle(GAS["x"], GAS["y"], 11, "hid")
    v.circle(0, 0, GUARD["r_bolt"] + 10, "hid")
    # shelf, carriage plate, motor
    v.poly([(CAR["sh_x0"], SHELF_Y0), (CAR["sh_x1"], SHELF_Y0), (CAR["sh_x1"], Y_BLK), (CAR["sh_x0"], Y_BLK)], fill=SS)
    rr(-CAR["w"] / 2, CAR["w"] / 2, Y_BLK - CAR["t"], Y_BLK, fill=SS)
    rr(-BLK["W"] / 2, BLK["W"] / 2, Y_BLK, Y_RSB - 4, fill=BLU)
    rr(-RSB["w"] / 2, RSB["w"] / 2, Y_RSB, Y_COLF, fill=SS)
    rr(-COL["a"] / 2, COL["a"] / 2, COL["y"] - COL["a"] / 2, COL["y"] + COL["a"] / 2, fill="#cfd8dc")
    rr(CAPPL["x0"], CAPPL["x1"], CAPPL["y0"], CAPPL["y1"], fill=SS)
    rr(CLEV["x"], CLEV["x"] + CLEV["t"], CLEV["y0"], CLEV["y1"], fill=SS)
    v.circle(0, 0, GM["body_d"] / 2, "vis", BLU)
    rr(-25, 25, -60, -36, fill=BLU)
    rr(CAR["lug_x"] - 5, CAR["lug_x"] + 5, CAR["lug_y"] - 15, CAR["lug_y"] + 15, fill=SS)
    rr(LEV["x"] - LEV["t"] / 2, LEV["x"] + LEV["t"] / 2, END_UP[1], PIV["y"] + 25, fill=SS)
    rr(END_UP[0] + 5, END_UP[0] + 45, END_UP[1] - 16, END_UP[1] + 16, fill="#263238")
    v.circle(0, 0, JAR["d"] / 2, "phan")
    v.centre(-120, 0, 120, 0); v.centre(0, -120, 0, 160)


def ga():
    S = sheet("P1-412-001", "BENCH SPINDLE CAPPER: GENERAL ARRANGEMENT", scale="1:3", material="SS 304 frame; UHMW nest; PC guard", finish=FIN_NPC,
              mass=f"{sum(MASS.values()) + 7.5:.0f} kg [{(sum(MASS.values()) + 7.5) * 2.2046:.0f} lb] with bought parts")
    s = SC(3)
    v = S.view(600, 1320, s, "FRONT VIEW (1:3), CARRIAGE UP, JAR PHANTOM", (380, 150))
    front(v)
    # carriage down (shaker) phantom
    R(v, CAR["sh_x0"], CAR["sh_x1"], ZD, ZD + CAR["sh_t"], "phan"); R(v, -GUARD["d"] / 2, GUARD["d"] / 2, ZD - GUARD["h"], ZD - 16, "phan")
    v.dim((-BASE["w"] / 2, 0), (BASE["w"] / 2, 0), -40, None, "h")
    v.dim((-BASE["w"] / 2, 0), (-BASE["w"] / 2, Z_CAP), 70, f"{mmi(Z_CAP)} TOP OF COLUMN", "v")
    v.dim((-BASE["w"] / 2, 0), (-BASE["w"] / 2, END_UP[2] + 16), 120, f"{mmi(END_UP[2] + 16)} LEVER UP", "v")
    v.dim((GUARD["d"] / 2, 0), (GUARD["d"] / 2, Z_CHK_UP), -150, f"CHUCK FACE {mmi(Z_CHK_UP)} (UP)", "v")
    v.dim((CAR["sh_x1"], ZD), (CAR["sh_x1"], ZS), -80, f"STROKE {mmi(STROKE_MAX, 1)}", "v")
    for n, at, to in ((1, (-150, 6), (-330, 140)), (2, (-80, ZS + 5), (-330, 440)), (16, (-30, ZS + 150), (-330, 620)), (5, (-60, ZS - 60), (-330, 300)),
                      (19, (-180, 60), (-330, 220)), (20, (-110, 50), (-330, 30)), (8, (60, 60), (330, 120)), (13, (STOP["x"], 120), (330, 200)),
                      (14, (STOP["x"] + 25, ZD - 10), (330, 270)), (11, (LEV["x"], 800), (330, 820)), (12, (PIV["x"], 560), (330, 560)),
                      (18, (GAS["x"], 100), (-330, 80)), (21, (-33, 560), (-330, 700)), (22, (END_UP[0] + 25, END_UP[2]), (330, 900)), (7, (100, 16), (330, 40))):
        v.tag(*to, n, at)
    # side view
    vs = S.view(1480, 1320, s, "RIGHT SIDE VIEW (1:3)", (1300, 150))
    side(vs)
    vs.dim((BASE["y0"], 0), (BASE["y0"] + BASE["d"], 0), -40, None, "h")
    vs.dim((BASE["y0"], 0), (COL["y"], 0), -80, f"{mmi(COL['y'] - BASE['y0'])} TO COLUMN AXIS", "h")
    vs.dim((0, Z_STAND), (0, Z_STAND + JAR["h"] + JAR["cap_h"]), 130, f"JAR + CAP {mmi(JAR['h'] + JAR['cap_h'], 1)}", "v")
    vs.dim((END_UP[1], END_UP[2]), (PIV["y"], END_UP[2]), 30, f"{mmi(PIV['y'] - END_UP[1], 0)}", "h")
    vs.dim((COL["y"] + COL["a"] / 2, 0), (COL["y"] + COL["a"] / 2, PIV["z"]), -60, f"PIVOT {mmi(PIV['z'])}", "v")
    vs.tag(-330, 760, 11, ((END_UP[1] + PIV["y"]) / 2, (END_UP[2] + PIV["z"]) / 2 + 5))
    vs.tag(150, 480, 18, (Y_RSB - 5, 400)); vs.tag(150, 300, 1, (COL["y"] + 25, 250))
    vs.tag(-330, 300, 20, (-140, 60)); vs.tag(-330, 420, 5, (-GUARD["d"] / 2, ZS - 50))
    vs.angle((PIV["y"], PIV["z"]), 70, 180 - TH0, 180 + TH0, f"±{TH0:.1f}°")
    # plan
    vp = S.view(2170, 1180, s, "PLAN (1:3)", (2080, 780))
    plan(vp)
    vp.dim((-BASE["w"] / 2, BASE["y0"]), (BASE["w"] / 2, BASE["y0"]), -40, None, "h")
    vp.dim((BASE["w"] / 2, BASE["y0"]), (BASE["w"] / 2, BASE["y0"] + BASE["d"]), -40, None, "v")
    vp.dim((-BASE["hx"], -BASE["hy"]), (BASE["hx"], -BASE["hy"]), 330, f"4 x Ø9 ON {mmi(2 * BASE['hx'])} x {mmi(2 * BASE['hy'])}", "h")
    vp.tag(300, 120, 2, (60, -80)); vp.tag(300, 0, 8, (XF_J + 50, 30)); vp.tag(-300, 0, 9, (-60, 25)); vp.tag(-300, -170, 20, (-150, -150))
    vp.tag(300, -150, 11, (LEV["x"], -150)); vp.tag(300, 220, 1, (20, 160))
    S.table(2620, 210, [("ITEM", 50), ("PART", 120), ("DESCRIPTION", 480), ("QTY", 40)], [(a, b, c, d) for a, b, c, d, e in ITEMS], "ITEM LIST", 12, 22)
    S.table(120, 1500, [("INTERFACE", 300), ("VALUE", 520), ("SET BY", 380)], [
        ("Bench", f"TBL-1 top 914 [35.98] AFF; 4 x M8 through the bench top", "P1-409 table, drill on site"),
        ("Containers", f"shaker Ø{mmi(SHK['d'])} 53 mm cap; jar Ø{mmi(JAR['d'])} 89 mm cap", "P1-401 fills; V-block S or J holes"),
        ("Cap torque", f"53 mm: {SHK['T']} N·m [{SHK['T_lbin']:.0f} lbf·in]; 89 mm: {JAR['T']} N·m [{JAR['T_lbin']:.0f} lbf·in]", "clutch setting, check on P1-402 hourly"),
        ("Stop", f"shaker: rod top {mmi(ZD, 1)}; jar: flip block in ({mmi(z_shelf_down('jar-12'), 1)})", "stop rod 503 + flip 504"),
        ("Power", "120 V 1-ph 15 A receptacle, cord 3 m", "plant panel bench circuit"),
    ], "INTERFACES", fs=13, rh=24)
    S.notes(1300, 1500, 1200, [
        "Operator: container in the V-nest, close the toggle clamp (left hand), pull the lever (right hand). Release when the clutch slips (≈ 1/2 s); open the clamp.",
        "Motor runs only when the carriage is below the top limit switch (21) and the E-stop is out; carriage rises by the gas spring when the lever is released.",
        "Change S ↔ J: swap the chuck insert (3 set screws), move the V-block to the S or J holes (2 x M8), flip block in (jar) or out (shaker), set the clutch, test on P1-402.",
        "No product contact: caps are on before the chuck touches them. Nest, V-block and pad are UHMW so they do not mark the containers.",
        "All steel parts 304, #4 brushed; welds per P1-412-100 / 200. Hardware A2-70 unless noted (P1-412-800).",
    ], "OPERATION AND GENERAL NOTES", fs=13)
    S.save(DWG / "P1-412-001_general_arrangement.svg")


def section():
    S = sheet("P1-412-002", "SECTION A-A ON THE SPINDLE, DETAILS: NEST, STOP, PIVOT", scale="1:2 · 1:1", material="see item list", finish="see parts", mass="-")
    s = SC(2)
    zc = ZS - 120
    v = S.view(900, 300 + (ZS + 300) * s, s, "SECTION A-A (1:2): SPINDLE LINE, CARRIAGE, RAIL (CUT ON X = 0, LOOKING -X)", (520, 230))
    zs = ZS
    # column, rail bar, rail, block (cut)
    R(v, COL["y"] - COL["a"] / 2, COL["y"] - COL["a"] / 2 + COL["t"], zs - 120, zs + 260, fill="url(#hA)")
    R(v, COL["y"] + COL["a"] / 2 - COL["t"], COL["y"] + COL["a"] / 2, zs - 120, zs + 260, fill="url(#hA)")
    R(v, Y_RSB, Y_COLF, zs - 120, zs + 260, fill="url(#hB)")
    R(v, Y_RSB - RAIL["h"], Y_RSB, zs - 120, zs + 260, fill="url(#hC)")
    zb = zs + CAR["sh_t"] + CAR["h"] / 2
    R(v, Y_BLK, Y_RSB - 4, zb - BLK["L"] / 2, zb + BLK["L"] / 2, fill=BLU)
    for z in (zb - BLK["C"] / 2, zb + BLK["C"] / 2):
        R(v, Y_BLK - CAR["t"] - 2, Y_BLK + 6, z - 1.5, z + 1.5, "thin", "#90a4ae")
    # carriage plate, shelf, gusset (cut at x = 0: plate and shelf cut; gusset beyond)
    R(v, Y_BLK - CAR["t"], Y_BLK, zs + CAR["sh_t"], zs + CAR["sh_t"] + CAR["h"], fill="url(#hA)")
    R(v, SHELF_Y0, -MOTOR_BORE / 2, zs, zs + CAR["sh_t"], fill="url(#hA)"); R(v, MOTOR_BORE / 2, Y_BLK, zs, zs + CAR["sh_t"], fill="url(#hA)")
    v.poly([(Y_BLK - CAR["t"], zs + CAR["sh_t"]), (Y_BLK - CAR["t"] - CAR["gus"], zs + CAR["sh_t"]), (Y_BLK - CAR["t"], zs + CAR["sh_t"] + CAR["gus"])], "hid")
    # gearmotor (outline), shaft
    R(v, -GM["body_d"] / 2, GM["body_d"] / 2, zs + CAR["sh_t"], zs + CAR["sh_t"] + 40, fill=BLU)
    R(v, -36, 36, zs + CAR["sh_t"] + 40, zs + CAR["sh_t"] + 160, fill=BLU)
    v.line(-36, zs + CAR["sh_t"] + 160, 36, zs + CAR["sh_t"] + 160, "phan"); v.text(0, zs + CAR["sh_t"] + 175, "gearmotor P1-422 (continues)", 11)
    R(v, -MOTOR_BORE / 2, MOTOR_BORE / 2, zs, zs + CAR["sh_t"] + 2, fill=BLU)
    R(v, -GM["shaft"] / 2, GM["shaft"] / 2, zs - 30, zs, fill=SS)
    # clutch (bought, in section outline), stub shaft 301, chuck 302, insert, float spring
    R(v, -CLU["d"] / 2, CLU["d"] / 2, zs - CLU["L"], zs - 2, fill=BLU)
    v.line(-CLU["d"] / 2, zs - CLU["L"] / 2, CLU["d"] / 2, zs - CLU["L"] / 2, "thin")
    zc0 = zs - CLU["L"] - STUB["collar_t"]
    R(v, -STUB["d"] / 2, STUB["d"] / 2, zc0 + STUB["collar_t"], zc0 + STUB["collar_t"] + 30, fill="url(#hC)")
    R(v, -STUB["collar_d"] / 2, STUB["collar_d"] / 2, zc0, zc0 + STUB["collar_t"], fill="url(#hC)")
    R(v, -STUB["spig_d"] / 2, STUB["spig_d"] / 2, zc0 - STUB["spig_L"], zc0, fill="url(#hC)")
    zf = zs - STACK
    for sg in (-1, 1):
        x0, x1 = sg * STUB["spig_d"] / 2 + sg * 0.1, sg * CHK["d"] / 2
        R(v, x0, x1, zf + 20, zf + CHK["h"], fill="url(#hA)")
        R(v, sg * (INSERT["J"]["id_bot"] / 2 + 4), x1, zf, zf + 20, fill="url(#hA)")
        R(v, sg * INSERT["J"]["id_bot"] / 2, sg * (INSERT["J"]["id_bot"] / 2 + 4), zf, zf + 19, fill="#ffcc80")
    v.line(-STUB["spig_d"] / 2 - 2, zf + CHK["h"] - STUB["spig_L"] + CHK["float_"], STUB["spig_d"] / 2 + 2, zf + CHK["h"] - STUB["spig_L"] + CHK["float_"], "thin")
    for k in range(5):                                                               # float spring (zig-zag)
        z = zf + 20 + k * 2.4
        v.line(-12, z, 12, z + 1.2, "thin")
    R(v, 7.0, 10.0, zf + CHK["h"] - 14, zf + CHK["h"] - 2, fill="#90a4ae")             # set screw in the float slot
    # guard + standoff
    for sg in (-1, 1):
        R(v, sg * (GUARD["d"] / 2 - GUARD["t"]), sg * GUARD["d"] / 2, zs - GUARD["h"], zs - 16, fill=PC)
        R(v, sg * (GUARD["d"] / 2 - GUARD["t"]), sg * (GUARD["r_bolt"] + 10), zs - 16, zs - 10, fill=PC)
    R(v, -GUARD["r_bolt"] - 5, -GUARD["r_bolt"] + 5, zs - 10, zs, fill="url(#hC)")
    # jar + cap phantom with the carriage down on the jar stop
    v.rect(-JAR["cap_d"] / 2 - 1, zf - JAR["cap_h"] + 6, JAR["cap_d"] + 2, JAR["cap_h"], "phan")
    v.centre(0, zf - 40, 0, zs + 200)
    # dims
    v.dim((0, zf), (0, zs), -230, f"STACK {mmi(STACK)}", "v")
    v.dim((-CHK["d"] / 2, zf), (CHK["d"] / 2, zf), -60, f"Ø{mmi(CHK['d'])}", "h")
    v.dim((-INSERT["J"]["id_bot"] / 2, zf + 20), (INSERT["J"]["id_bot"] / 2, zf + 20), 30, f"INSERT Ø{mmi(INSERT['J']['id_bot'] + 8)} OD x 20 (S: {INSERT['S']['id_top']:.0f}/{INSERT['S']['id_bot']:.0f}, J: {INSERT['J']['id_top']:.0f}/{INSERT['J']['id_bot']:.0f} ID)", "h") if False else None
    v.dim((0, Y_BLK), (0, Y_BLK), 0) if False else None
    v.dim((0, zs + CAR["sh_t"] + CAR["h"]), (Y_BLK, zs + CAR["sh_t"] + CAR["h"]), 30, f"{mmi(Y_BLK)} AXIS TO BLOCK FACE", "h")
    v.dim((Y_RSB, zs - 120), (Y_COLF, zs - 120), -30, None, "h")
    v.leader((CLU["d"] / 2, zs - 30), (150, zs - 40), ["SLIP CLUTCH P1-423, Ø1/2 BORES, SET 1.6 / 2.5 N·m", "2 SET SCREWS EACH HUB (H12) ON FLATS"], 13)
    v.leader((STUB["collar_d"] / 2, zc0 + 3), (150, zc0 - 10), ["STUB SHAFT 301: Ø12.70 h6 INTO THE CLUTCH,", "COLLAR Ø22, SPIGOT Ø16 g6 x 30"], 13)
    v.leader((CHK["d"] / 2, zf + 30), (150, zf + 10), ["CHUCK ADAPTER 302 Ø112, FLOATS 12 ON THE SPIGOT;", "SET SCREW RIDES IN A 12 SLOT (NO SPIN, FLOAT ONLY)"], 13)
    v.leader((INSERT["J"]["id_bot"] / 2 + 2, zf + 5), (150, zf - 40), ["URETHANE CONE INSERT P1-423 (J SHOWN), 3 SET SCREWS", f"S: ID {INSERT['S']['id_top']:.0f}/{INSERT['S']['id_bot']:.0f}, J: ID {INSERT['J']['id_top']:.0f}/{INSERT['J']['id_bot']:.0f} x {INSERT['J']['depth']:.0f} DEEP"], 13)
    v.leader((-GUARD["d"] / 2, zs - 60), (-230, zs - 80), ["GUARD 303: PC TUBE Ø150 x 3 ON 3 STANDOFFS 304", "BOTTOM 12 ABOVE THE CHUCK FACE"], 13)
    v.leader((-MOTOR_BORE / 2, zs + 5), (-230, zs + 40), ["MOTOR PILOT IN Ø30.00 H8 BORE, ⊥ 0.05 TO BLOCK FACE B"], 13)
    v.leader((Y_BLK + 3, zb), (150, zb + 120), ["MGN15H BLOCK, 4 x M3 x 12 + LOCTITE 243 (H3)", "RAIL ON THE MACHINED SEAT BAR 106, M3 AT 40 PITCH"], 13)
    v.datum((Y_BLK, zs + CAR["sh_t"] + CAR["h"] - 10), "B", (1, 0))
    v.fcf(-230, zs - 150, ["⊥", "0.05", "B"])
    v.text(-230 + 40, zs - 175, "spindle axis to block face B", 11, "start")
    # ---- detail C: nest plan (1:2), both containers
    vc = S.view(2120, 760, s, "DETAIL C (1:2): NEST, V-BLOCK S / J, CLAMP PAD", (1840, 230))
    vc.rect(-95, -70, 205, 140, "vis", UH)
    for k, c, xf, kk in (("J", JAR, XF_J, "vis"), ("S", SHK, XF_S, "phan")):
        vc.poly([(xf, -VB["L"] / 2), (xf + VB["t"], -VB["L"] / 2), (xf + VB["t"], VB["L"] / 2), (xf, VB["L"] / 2), (xf, VB["depth"]), (xf + VB["depth"], 0), (xf, -VB["depth"])], kk, fill=UH if k == "J" else "none")
        vc.circle(0, 0, c["d"] / 2, "phan")
        for x, y in M.VB_HOLES[k]:
            vc.circle(x, y, 4.5 if k == "J" else 3.4, "vis" if k == "J" else "hid")
    vc.text(0, 4, "AXIS", 12, color=ms.CEN)
    vc.centre(-110, 0, 140, 0); vc.centre(0, -90, 0, 90)
    xp = -JAR["d"] / 2
    vc.poly([(xp - PAD["t"], -PAD["w"] / 2), (xp, -PAD["w"] / 2), (xp, -16), (xp - 8, 0), (xp, 16), (xp, PAD["w"] / 2), (xp - PAD["t"], PAD["w"] / 2)], fill=UH)
    vc.dim((0, 60), (XF_J + VB["depth"], 60), 40, f"J {mmi(v_offset(JAR['d']), 1)}", "h")
    vc.dim((0, -60), (XF_S + VB["depth"], -60), -40, f"S {mmi(v_offset(SHK['d']), 1)}", "h")
    vc.dim((M.VB_HOLES["J"][0][0], -35), (M.VB_HOLES["J"][0][0], 35), -60, None, "v")
    vc.leader(M.VB_HOLES["J"][1], (170, 95), [f"J HOLES 2 x M8 AT X {mmi(M.VB_HOLES['J'][0][0], 1)}", f"S HOLES AT X {mmi(M.VB_HOLES['S'][0][0], 1)} (HIDDEN)"], 13)
    vc.leader((xp - 4, 0), (-200, 95), ["PAD 403 ON THE TOGGLE SPINDLE (M10),", "SET TO TOUCH THE JAR WITH THE CLAMP OVER-CENTRE"], 13)
    vc.angle((XF_J + VB["depth"], 0), 25, 135, 225, "90°")
    # ---- detail D: stop rod + flip block (1:2)
    vd = S.view(1700, 1700, s, "DETAIL D (1:2): STOP ROD 503 AND FLIP STOP 504", (1560, 1180))
    vd.rect(-40, -BASE["t"], 120, BASE["t"], fill="url(#hA)")
    vd.rect(-8, -BASE["t"] - 6, 16, ZD - BASE["t"] + 6 - 140, fill=SS)
    vd.line(-8, ZD - 150, 8, ZD - 150, "phan")
    vd.rect(-12, 0, 24, 8, fill="#cfd8dc"); vd.rect(-12, -BASE["t"] - 14, 24, 8, fill="#cfd8dc")
    yz = ZD - 140                                                    # broken view: top shown 140 lower
    vd.rect(-8, yz - 40, 16, 40, fill=SS)
    vd.rect(10, yz - STOP["flip_t"] + 10, 30, STOP["flip_t"], fill=SS); vd.circle(25, yz - 5, 3, "thin")
    vd.rect(-30, yz, 70, 10, "phan"); vd.text(70, yz + 5, "shelf (shaker)", 11, "start")
    vd.rect(-30, yz + STOP["flip_t"], 70, 10, "phan"); vd.text(70, yz + STOP["flip_t"] + 5, "shelf (jar, flip in)", 11, "start")
    vd.dim((40, yz - STOP["flip_t"] + 10), (40, yz + 10), -40, f"FLIP {mmi(STOP['flip_t'], 1)}", "v")
    vd.leader((-8, 20), (-110, 40), ["STOP ROD Ø16, M16 x 1.5 x 25 INTO THE BASE,", f"TOP AT {mmi(ZD, 1)} (SHAKER); JAM NUT 40 N·m"], 13)
    vd.leader((25, yz - 5), (-110, yz + 70), ["FLIP BLOCK ON Ø6 PIN, SWINGS OVER THE ROD FOR JARS"], 13)
    # ---- detail E: lever pivot (1:1)
    s1 = SC(1)
    ve = S.view(2700, 1650, s1, "DETAIL E (1:1): LEVER PIVOT ON CLEVIS 105 (SEEN FROM BELOW... PLAN)", (2560, 1180)) if False else S.view(2700, 1650, s1, "DETAIL E (1:1): LEVER PIVOT, PLAN SECTION", (2560, 1180))
    ve.rect(CLEV["x"] - PIV["x"], -30, CLEV["t"], 60, fill="url(#hA)")
    ve.rect(-LEV["t"] / 2, -12.5, LEV["t"], 25, fill="url(#hB)")
    ve.rect(LEV["t"] / 2, -10, 5, 20, fill="#fff9c4"); ve.rect(-LEV["t"] / 2 - 2, -10, 2, 20, fill="#fff9c4")
    ve.rect(-LEV["t"] / 2 - 10, -8, 10 + LEV["t"] + 5 + CLEV["t"] + 8, 16, "thin")
    ve.rect(-LEV["t"] / 2 - 18, -9, 8, 18, fill="#cfd8dc")
    ve.centre(-40, 0, 40, 0)
    ve.leader((-LEV["t"] / 2 - 14, 9), (-60, 40), ["SHOULDER BOLT Ø10 x 20 (H9), NYLOC ON THE M8 END,", "NYLON WASHERS BOTH SIDES OF THE LEVER (5 GAP)"], 13)
    ve.dim((CLEV["x"] - PIV["x"], -30), (CLEV["x"] - PIV["x"] + CLEV["t"], -30), -30, None, "h")
    S.table(120, 1530, [("FIT", 200), ("HOLE", 160), ("SHAFT", 160), ("PARTS", 520)], [
        ("Motor pilot", "Ø30.00 H8", "Ø29.97 (motor)", "shelf 202 / gearmotor P1-422 (confirm pilot)"),
        ("Clutch on motor", "Ø12.70 (clutch)", "Ø12.70 (motor)", "set screws on the flat + key"),
        ("Stub in clutch", "Ø12.70 (clutch)", "Ø12.70 h6", "stub 301"),
        ("Chuck float", "Ø16 H8", "Ø16 g6", "chuck adapter 302 on stub spigot: slides 12"),
        ("Lever pivot", "Ø10.2", "Ø10 shoulder bolt", "lever 501 in clevis 105"),
        ("Rod end pins", "Ø8.2", "M8 bolt", "lug 204, lever 501"),
    ], "FITS", 12, 22)
    S.notes(120, 1720, 1300, [
        "Rail seat bar 106 is faced after welding: flat 0.05 over 500, parallel to the column 0.1. Block face B is machined after the carriage is welded.",
        "The chuck floats 12 [.47] against a light spring so it lands softly on the loose cap; torque passes through the set screw in the slot, not the spring.",
        "Clutch set per cap (S 1.6, J 2.5 N·m) with the torque tester P1-402; motor stall torque 4.4 N·m is above the highest setting.",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-412-002_sections.svg")


if __name__ == "__main__":
    ga(); section()
