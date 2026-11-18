"""P1-404-001 general arrangement (front, side, plan), -002 section A-A on the web path, belt drive view, S / J settings."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
import model as M

C = calcs()
SS = "#f4f6f8"
BLU = "#dfe7f1"
UH = "#fbfbf6"
ORG = "#ffe0b2"
RED = "#ffcdd2"
LABC = "#fff8e1"
JAR = CONT["jar-12"]
SHK = CONT["shaker-250"]
XL0, XL1, XR0, XR1 = M.XL0, M.XL1, M.XR0, M.XR1


def R(v, x0, x1, z0, z1, k="vis", fill="none"):
    v.rect(min(x0, x1), min(z0, z1), abs(x1 - x0), abs(z1 - z0), k, fill)


def arm_poly(v, k="jar-12", fill=SS, ext=0.0):
    (py, pz), (yc, zc) = M.arm_pts(k)
    L = math.hypot(yc - py, zc - pz); ux, uz = (yc - py) / L, (zc - pz) / L
    ey, ez = py + ux * (L + ext), pz + uz * (L + ext); ny, nz = -uz * IDL["arm_w"] / 2, ux * IDL["arm_w"] / 2
    v.poly([(py + ny, pz + nz), (ey + ny, ez + nz), (ey - ny, ez - nz), (py - ny, pz - nz)], fill=fill)


def side(v, k="jar-12", web=True, labels=True):
    """side elevation seen from +x (y right = back, z up): the web path in the plane of the drawing."""
    c = CONT[k]; st = c["setting"]
    v.line(-200, 0, 320, 0, "phan")
    R(v, BASE["y0"], BASE["y0"] + BASE["d"], 0, BASE["t"], fill=SS)
    v.poly(M.SPL_PTS, "hid")                                                     # -x plate behind
    R(v, ENC["y0"], ENC["y1"], BASE["t"], BASE["t"] + ENC["h"], "hid")
    # rollers + container
    for y in (-ROL["y"], ROL["y"]):
        v.circle(y, ROL["z"], ROL["d"] / 2, "vis", ORG); v.circle(y, ROL["z"], ROL["shaft"] / 2, "thin"); v.cmark(y, ROL["z"], 32)
    zc = z_cent(c["d"])
    v.circle(0, zc, c["d"] / 2, "phan", "#e1f5fe"); v.cmark(0, zc, c["d"] / 2 + 8)
    # tie, pivot, fence (fence seen end-on between the rollers)
    v.circle(M.TIE["y"], M.TIE["z"], M.TIE["d"] / 2, "vis", SS)
    R(v, -FENCE["w"] / 2, FENCE["w"] / 2, BASE["t"], BASE["t"] + FENCE["h"], "hid")
    # liner drive, pinch, rewind, unwind, guide
    v.circle(LD["y"], LD["z"], LD["d"] / 2, "vis", SS); v.cmark(LD["y"], LD["z"], 22)
    v.circle(LD["y"], LD["z"], 35.0, "hid")
    pr = (LD["y"], LD["z"] + LD["d"] / 2 + PINCH["d"] / 2 + 0.2)
    v.poly([(PINCH["piv_y"] + 6, PINCH["piv_z"] + 8), (pr[0] - 6, pr[1] + 8), (pr[0] - 6, pr[1] - 8), (PINCH["piv_y"] + 6, PINCH["piv_z"] - 8)], fill=SS)
    v.circle(pr[0], pr[1], PINCH["d"] / 2, "vis", UH); v.circle(PINCH["piv_y"], PINCH["piv_z"], 4, "vis", "#fff")
    v.circle(REW["y"], REW["z"], REW["hub_d"] / 2, "vis", UH); v.circle(REW["y"], REW["z"], 55.0, "phan"); v.cmark(REW["y"], REW["z"], 50)
    v.circle(UNW["y"], UNW["z"], UNW["flange_d"] / 2, "hid"); v.circle(UNW["y"], UNW["z"], LAB["od_max"] / 2, "phan", LABC if labels else "none")
    v.circle(UNW["y"], UNW["z"], UNW["hub_d"] / 2, "vis", UH); v.circle(UNW["y"], UNW["z"], 12.5, "vis", SS); v.cmark(UNW["y"], UNW["z"], 120)
    v.circle(G1["y"], G1["z"], G1["d"] / 2, "vis", UH)
    # peel plate + bracket
    (y0, z0), (y1, z1) = M.peel_pts(st)
    v.poly([(y0, z0), (y1, z1), (y1, z1 - 30), (y1 - PEEL["t"], z1 - 30), (y1 - PEEL["t"], z1 - PEEL["t"]), (y0, z0 - PEEL["t"])], fill=SS)
    zf = z_top(c["d"]) - 15.0
    R(v, 25.0, y1 + 6, zf - 12, zf + 12, "hid")
    R(v, 45, 70, z0 - 25, z0 + 30, "vis", "#bbdefb")                              # gap sensor fork
    # idler arm + idler
    arm_poly(v, k, SS, 55.0 if True else 0.0)
    yc, zcI, _ = idler_at(k)
    v.circle(yc, zcI, IDL["d"] / 2, "vis", RED); v.circle(yc, zcI, IDL["shaft"] / 2, "thin")
    v.circle(IDL["piv_y"], IDL["piv_z"], 8, "vis", SS)
    e = M._arm_end() if k == "jar-12" else None
    if e:
        v.circle(e[0], e[1], 14, "vis", "#263238")
    # web path
    if web:
        rr = LAB["od_max"] / 2
        a = math.atan2(G1["z"] - UNW["z"], G1["y"] - UNW["y"])
        p_off = (UNW["y"] - rr * 0.98, UNW["z"] - rr * 0.2)
        wl = [(p_off[0], p_off[1]), (G1["y"] - G1["d"] / 2, G1["z"]), (y1 - 2, z1 + 1.2), (y0, z0 + 0.3)]
        for i in range(len(wl) - 1):
            v.line(*wl[i], *wl[i + 1], "cut")
        lw = [(y0, z0 - PEEL["t"] - 0.6), (y1 - 4, z1 - PEEL["t"] - 0.6), (LD["y"] - 10, LD["z"] + LD["d"] / 2 + 0.6), (LD["y"] + 12, LD["z"] + LD["d"] / 2 + 0.3),
              (REW["y"] - 10, REW["z"] + REW["hub_d"] / 2 + 6)]
        for i in range(len(lw) - 1):
            v.line(*lw[i], *lw[i + 1], "bend")


def front(v):
    """front elevation looking +y (x right, z up)."""
    v.line(-340, 0, 340, 0, "phan"); v.text(-320, -18, "BENCH TBL-2 (914 [35.98] AFF)", 11, "start")
    R(v, -BASE["w"] / 2, BASE["w"] / 2, 0, BASE["t"], fill=SS)
    R(v, XL0, XL1, BASE["t"], SPL["z1"], fill=SS); R(v, XR0, XR1, BASE["t"], SPR["z1"], fill=SS)
    R(v, XL0 - 55, XL0, 15, 165, fill=SS)                                         # belt guard
    R(v, ENC["x0"], ENC["x1"], BASE["t"], BASE["t"] + ENC["h"], fill="#cfd8dc")
    for k, (x, z) in ENC_OPS.items():
        v.circle(x, BASE["t"] + z, 20 if k == "estop" else 14, "vis", {"estop": "#c62828", "feed": "#43a047"}.get(k, "#263238"))
    R(v, -ROL["face"] / 2, ROL["face"] / 2, ROL["z"] - ROL["d"] / 2, ROL["z"] + ROL["d"] / 2, fill=ORG)
    v.line(XL1, ROL["z"], XR0, ROL["z"], "cen")
    R(v, XL1, XL1 + 100, MOT["z"] - 28.6, MOT["z"] + 28.6, "hid")
    xf = fence_x("jar-12")
    R(v, xf - FENCE["t"], xf, BASE["t"], BASE["t"] + FENCE["h"], fill=UH)
    zc = z_cent(JAR["d"])
    R(v, xf, xf + JAR["h"], zc - JAR["d"] / 2, zc + JAR["d"] / 2, "phan", "#e1f5fe")
    R(v, xf + JAR["h"], xf + JAR["h"] + JAR["cap_h"], zc - 44.5, zc + 44.5, "phan")
    R(v, -JAR["lab_H"] / 2, JAR["lab_H"] / 2, zc - JAR["d"] / 2, zc + JAR["d"] / 2, "thin", LABC)
    yc, zcI, _ = idler_at("jar-12")
    R(v, -IDL["face"] / 2, IDL["face"] / 2, zcI - IDL["d"] / 2, zcI + IDL["d"] / 2, fill=RED)
    for x0 in (XL1 + 4, XR0 - 4 - IDL["arm_t"]):
        R(v, x0, x0 + IDL["arm_t"], zcI - 12, IDL["piv_z"] + 12, fill=SS)
    R(v, XL1, XR0, IDL["piv_z"] - 8, IDL["piv_z"] + 8, "thin", SS)
    e = M._arm_end(); R(v, XR0 - 4, XR0 + 30, e[1] - 14, e[1] + 14, fill="#263238")
    (y0, z0), (y1, z1) = M.peel_pts("J")
    R(v, -PEEL["w"] / 2, PEEL["w"] / 2, z1 - 30, z1, "hid")
    R(v, -LAB["od_max"] / 2 * 0 - JAR["web"] / 2 if False else -(JAR["lab_H"] + LAB["liner"]) / 2, (JAR["lab_H"] + LAB["liner"]) / 2, UNW["z"] - LAB["od_max"] / 2, UNW["z"] + LAB["od_max"] / 2, "vis", LABC)
    R(v, -76, -70, UNW["z"] - UNW["flange_d"] / 2, UNW["z"] + UNW["flange_d"] / 2, fill=UH)
    R(v, XL1, 85, UNW["z"] - 12.5, UNW["z"] + 12.5, "thin")
    R(v, -(JAR["lab_H"] + LAB["liner"]) / 2, (JAR["lab_H"] + LAB["liner"]) / 2, REW["z"] - 55, REW["z"] + 55, "hid")
    v.centre(0, -15, 0, SPL["z1"] + 10)


def plan(v):
    rr = lambda x0, x1, y0, y1, k="vis", fill="none": v.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0), k, fill)
    rr(-BASE["w"] / 2, BASE["w"] / 2, BASE["y0"], BASE["y0"] + BASE["d"], fill=SS)
    for x, y in M.BASE_HOLES:
        v.circle(x, y, BASE["hole"] / 2, "vis", "#fff")
    rr(XL0, XL1, SPL["y0"], SPL["y1"], fill=SS); rr(XR0, XR1, SPR["y0"], SPR["y1"], fill=SS)
    rr(XL0 - 55, XL0, -90, 165, fill=SS)
    rr(ENC["x0"], ENC["x1"], ENC["y0"], ENC["y1"], fill="#cfd8dc"); rr(ENC_OPS["estop"][0] - 20, ENC_OPS["estop"][0] + 20, ENC["y0"] - 32, ENC["y0"], fill="#c62828")
    for y in (-ROL["y"], ROL["y"]):
        rr(-ROL["face"] / 2, ROL["face"] / 2, y - ROL["d"] / 2, y + ROL["d"] / 2, fill=ORG)
    xf = fence_x("jar-12")
    rr(xf, xf + JAR["h"], -JAR["d"] / 2, JAR["d"] / 2, "phan")
    rr(xf - FENCE["t"], xf, -FENCE["w"] / 2, FENCE["w"] / 2, fill=UH)
    yc, zcI, _ = idler_at("jar-12")
    rr(-IDL["face"] / 2, IDL["face"] / 2, yc - IDL["d"] / 2, yc + IDL["d"] / 2, fill=RED)
    (y0, z0), (y1, z1) = M.peel_pts("J")
    rr(-PEEL["w"] / 2, PEEL["w"] / 2, y0, y1, fill=SS)
    rr(XL1, -PEEL["w"] / 2, y1, y1 + 6, fill=SS)
    rr(40, 70, 45, 70, fill="#bbdefb")
    for x0 in (XL1 + 4, XR0 - 4 - IDL["arm_t"]):
        rr(x0, x0 + IDL["arm_t"], yc, IDL["piv_y"], fill=SS)
    rr(XL1, XR0, IDL["piv_y"] - 8, IDL["piv_y"] + 8, fill=SS)
    rr(-(JAR["lab_H"] + LAB["liner"]) / 2, (JAR["lab_H"] + LAB["liner"]) / 2, UNW["y"] - LAB["od_max"] / 2, UNW["y"] + LAB["od_max"] / 2, "phan", LABC)
    rr(XL1, XL1 + 100, MOT["y"] - 28.6, MOT["y"] + 28.6, "hid")
    v.centre(-ROL["face"] / 2 - 20, 0, ROL["face"] / 2 + 20, 0); v.centre(0, BASE["y0"] - 15, 0, SPL["y1"] + 15)


def ga():
    S = sheet("P1-404-001", "WRAP LABELER: GENERAL ARRANGEMENT", scale="1:3", material="SS 304 frame; UHMW hubs; urethane + silicone rollers", finish=FIN_NPC,
              mass=f"{sum(MASS.values()) + 6.5:.0f} kg [{(sum(MASS.values()) + 6.5) * 2.2046:.0f} lb] with bought parts")
    s = SC(3)
    v = S.view(620, 1300, s, "FRONT VIEW (1:3), JAR ON THE ROLLERS, ARM DOWN", (560, 150))
    front(v)
    v.dim((-BASE["w"] / 2, 0), (BASE["w"] / 2, 0), -50, None, "h")
    v.dim((XR1, 0), (XR1, SPR["z1"]), -330, None, "v"); v.dim((XL0 - 55, 0), (XL0 - 55, SPL["z1"]), 200, f"{mmi(SPL['z1'])} OVERALL", "v")
    v.dim((-ROL["face"] / 2, ROL["z"] - 25), (ROL["face"] / 2, ROL["z"] - 25), -95, f"ROLLER FACE {mmi(ROL['face'])}", "h")
    for n, at, to in ((1, (250, 4), (250, -60)), (2, (XL0 + 3, 380), (-380, 420)), (3, (XR1 - 3, 200), (300, 300)), (23, (60, ROL["z"]), (300, 60)),
                      (27, (60, idler_at("jar-12")[1]), (300, 220)), (28, (ENC["x1"] - 10, 100), (400, 110)), (5, (fence_x("jar-12") - 4, 40), (-200, -60)),
                      (9, (XL0 - 30, 100), (-380, 120)), (30, (XR0 + 20, M._arm_end()[1]), (260, 370))):
        v.tag(*to, n, at)
    vs = S.view(1520, 1300, s, "RIGHT SIDE VIEW (1:3), FROM +X, WEB PATH", (1460, 150))
    side(vs)
    vs.dim((BASE["y0"], 0), (BASE["y0"] + BASE["d"], 0), -50, None, "h")
    vs.dim((SPL["y0"], 0), (SPL["y1"], 0), -90, f"{mmi(SPL['y1'] - SPL['y0'])} SIDE PLATE", "h")
    vs.dim((BASE["y0"], 0), (BASE["y0"], z_top(JAR["d"])), 40, f"JAR TOP {mmi(z_top(JAR['d']), 1)}", "v")
    for n, at, to in ((10, (UNW["y"], UNW["z"] + 30), (320, 470)), (16, (G1["y"], G1["z"]), (320, 260)), (17, (40, z_top(JAR["d"]) + 4), (-220, 300)),
                      (25, (57, z_top(JAR["d"]) + 30), (-220, 380)), (20, (60, 222), (-220, 440)), (19, (IDL["piv_y"], IDL["piv_z"]), (320, 330)),
                      (7, (LD["y"], LD["z"]), (320, 180)), (8, (PINCH["piv_y"], PINCH["piv_z"]), (320, 220)), (14, (REW["y"], REW["z"] + 38), (320, 120)),
                      (4, (M.TIE["y"], M.TIE["z"]), (-220, 60)), (11, (UNW["y"] - 38, UNW["z"]), (320, 420))):
        vs.tag(*to, n, at)
    vs.note(-200, -110, ["Label web (dashed red) from the unwind roll over the guide and the peel plate to the tip; liner (dash-dot)",
                         "returns under the plate to the liner drive nip and the rewind. Container turns: label goes on at the top."], 11)
    vp = S.view(2530, 640, s, "PLAN (1:3)", (2530, 150))
    plan(vp)
    vp.dim((-BASE["w"] / 2, BASE["y0"]), (BASE["w"] / 2, BASE["y0"]), -40, None, "h")
    vp.dim((BASE["w"] / 2, BASE["y0"]), (BASE["w"] / 2, BASE["y0"] + BASE["d"]), -40, None, "v")
    vp.dim((-BASE["hx"], BASE["hy"]), (BASE["hx"], BASE["hy"]), 120, f"4 x Ø7 ON {BASE['hx'] * 2:.0f} x {BASE['hy'] * 2:.0f}", "h")
    for n, at, to in ((24, (XL1 + 50, MOT["y"]), (380, 330)), (21, (0, idler_at("jar-12")[0]), (380, -60)), (6, (XL1 + 20, LD["y"]), (-380, 230))):
        vp.tag(*to, n, at)
    S.table(2200, 1180, [("ITEM", 50), ("PART", 120), ("DESCRIPTION", 430), ("QTY", 40), ("SEE", 160)], ITEMS, "ITEM LIST", 11, 19)
    S.table(120, 1560, [("INTERFACE", 300), ("VALUE", 560), ("SET BY", 340)], [
        ("Bench", f"TBL-2 top {Z_BENCH:.0f} [{fin(Z_BENCH)}] AFF; 4 x M6 through the bench top", "P1-409 table, drill on site"),
        ("Containers", f"shaker Ø{SHK['d']:.0f} x {SHK['h']:.1f}; jar Ø{JAR['d']:.1f} x {JAR['h']:.1f}, lying cap toward +x", "fence 105 at S or J holes"),
        ("Labels", f"shaker {SHK['lab_H']:.0f} x {SHK['lab_L']:.0f}, jar {JAR['lab_H']:.0f} x {JAR['lab_L']:.0f}; 3 in core, 200 OD", "printed on P1-405"),
        ("Label speed", f"{LAB['speed']:.0f} mm/s = container surface speed (both belts)", "ClearCore program"),
        ("Power", f"120 V 1-ph 15 A receptacle, cord 3 m, {ELE['A']:.1f} A", "plant bench circuit"),
    ], "INTERFACES", 12, 22)
    S.notes(1440, 1560, 700, [
        "Operator: lay the container on the rollers against the fence, lower the arm (right hand): the label runs and stops at the next gap; lift the arm, take the container.",
        "Change S ↔ J: fence to the S or J holes (2 screws), peel bracket to the S or J holes (2 screws), select S / J on the box, load the label roll, teach the gap sensor.",
        "Rollers, liner drive and container surface all run at the same speed through the two timing belts: no adjustment for the container size.",
        "No product contact: the container is closed and capped; all steel 304, #4 brushed. Hardware A2-70 unless noted (P1-404-800).",
    ], "OPERATION AND GENERAL NOTES", fs=12)
    S.save(DWG / "P1-404-001_general_arrangement.svg")


def section():
    S = sheet("P1-404-002", "SECTION A-A ON THE WEB PATH, BELT DRIVE, S / J SETTINGS", scale="1:2", material="see 001", finish=FIN_NPC, mass="-")
    s = SC(2)
    v = S.view(800, 1250, s, "SECTION A-A (1:2) AT X 0: JAR, ARM DOWN", (880, 150))
    side(v)
    zt = z_top(JAR["d"]); zc = z_cent(JAR["d"])
    v.dim((-ROL["y"], ROL["z"]), (ROL["y"], ROL["z"]), -80, f"ROLLERS {ROL['y'] * 2:.0f} [{fin(ROL['y'] * 2)}] CTRS", "h")
    v.dim((ROL["y"] + 25, 0), (ROL["y"] + 25, ROL["z"]), -50, None, "v")
    v.dim((-JAR["d"] / 2, 0), (-JAR["d"] / 2, zc), 120, f"JAR AXIS {mmi(zc, 1)}", "v")
    v.dim((0, zt), (PEEL["tip_y"], zt), 150, f"TIP {PEEL['tip_y']:.0f} BEHIND TDC", "h")
    v.leader((PEEL["tip_y"], zt + 1), (-120, 290), ["PEEL TIP R1, 1 [.04] ABOVE THE JAR TOP", f"(SHAKER {mmi(z_top(SHK['d']) + 1, 1)}, JAR {mmi(zt + 1, 1)})"], 12)
    v.leader((LD["y"], LD["z"] + LD["d"] / 2), (250, 60), [f"LINER DRIVE Ø{LD['d']:.0f} KNURLED, {LD['T']}T: SAME SURFACE", "SPEED AS THE ROLLERS (30T, Ø50)"], 12)
    v.leader((PINCH["piv_y"], PINCH["piv_z"]), (250, 190), [f"PINCH LEVER, SPRING {PINCH['F']:.0f} N"], 12)
    v.leader((REW["y"] + 30, REW["z"] - 30), (250, -40), ["REWIND: O-RING SLIP DRIVE 1:1 FROM THE LINER", "DRIVE (OVERSPEED 2.5 x AT THE CORE)"], 12)
    v.leader((G1["y"], G1["z"] + 10), (250, 290), ["GUIDE Ø20 UHMW"], 12)
    v.leader((UNW["y"] - 50, UNW["z"] + 80), (-60, 520), ["UNWIND: ROLL ON Ø76 HUB, FELT DRAG BRAKE ON THE FLANGE"], 12)
    v.leader((IDL["piv_y"], IDL["piv_z"] + 8), (60, 360), [f"ARM PIVOT Ø16 (TIE BETWEEN THE PLATES), ARM R{idler_at('jar-12')[2]:.1f}"], 12)
    yc, zcI, _ = idler_at("jar-12")
    v.leader((yc - 10, zcI + 10), (-190, 240), [f"IDLER Ø{IDL['d']:.0f} SILICONE, {IDL['F']:.0f} N (ARM WEIGHT)"], 12)
    # belt drive seen from -x (outside the guard): mirror y so the view reads from the drive side
    vb = S.view(2050, 820, s, "BELT DRIVE (1:2), SEEN FROM -X, GUARD OFF", (1950, 300))
    m = lambda y: -y
    vb.poly([(m(SPL["y0"]), BASE["t"]), (m(SPL["y1"]), BASE["t"]), (m(SPL["y1"]), 200.0), (m(SPL["y0"]), 200.0)], "thin")
    vb.text(m(80), 206, "-X SIDE PLATE (BROKEN AT Z 200)", 10)
    for (y, z, d), lab in zip(B1_PTS, (f"ROLLER A {ROLLER_T}T", f"MOTOR {MOT['T']}T", f"ROLLER B {ROLLER_T}T")):
        vb.circle(m(y), z, d / 2, "vis", ORG); vb.cmark(m(y), z, d / 2 + 6)
    vb.circle(m(LD["y"]), LD["z"], pd(LD["T"]) / 2, "vis", BLU); vb.cmark(m(LD["y"]), LD["z"], 16)
    vb.circle(m(ROL["y"]), ROL["z"], pd(ROLLER_T) / 2 + 3, "hid")
    def ext_tangents(c1, c2):
        (y1, z1, d1), (y2, z2, d2) = c1, c2
        th = math.atan2(z2 - z1, y2 - y1); dd = math.hypot(y2 - y1, z2 - z1); out = []
        for sg in (1, -1):
            ph = th + sg * math.acos((d1 / 2 - d2 / 2) / dd)
            out.append(((y1 + d1 / 2 * math.cos(ph), z1 + d1 / 2 * math.sin(ph)), (y2 + d2 / 2 * math.cos(ph), z2 + d2 / 2 * math.sin(ph))))
        return out
    def belt(pts, k):
        cy = sum(p[0] for p in pts) / len(pts); cz = sum(p[1] for p in pts) / len(pts)
        for i in range(len(pts)):
            ts = ext_tangents(pts[i], pts[(i + 1) % len(pts)])
            if len(pts) > 2:
                ts = [max(ts, key=lambda t: math.hypot((t[0][0] + t[1][0]) / 2 - cy, (t[0][1] + t[1][1]) / 2 - cz))]
            for p1, p2 in ts:
                vb.line(m(p1[0]), p1[1], m(p2[0]), p2[1], k)
            if len(pts) == 2:
                break
    belt(B1_PTS, "vis"); belt(B2_PTS, "cut")
    vb.dim((m(-ROL["y"]), ROL["z"]), (m(ROL["y"]), ROL["z"]), -80, None, "h")
    vb.dim((m(ROL["y"]), MOT["z"]), (m(MOT["y"]), MOT["z"]), -100, None, "h")
    vb.dim((m(MOT["y"]), 0), (m(MOT["y"]), MOT["z"]), -40, None, "v")
    vb.dim((m(LD["y"]), ROL["z"]), (m(LD["y"]), LD["z"]), 50, None, "v")
    vb.note(m(250), -40, [f"Belt 1 (plane x {X_BELT1:.0f}): {BELT1}, calc {C['L_b1']:.1f}; tension by the motor slots (±3).",
                          f"Belt 2 (plane x {X_BELT2:.0f}): {BELT2}, calc {C['L_b2']:.1f}; tension by the housing slots.",
                          f"Rollers {C['n_roll']:.1f} rpm, motor {C['n_mot']:.1f} rpm at {LAB['speed']:.0f} mm/s label speed.",
                          "Both rollers and the liner drive turn the same way: CCW in this view."], 12)
    # S / J settings table and detail
    rows = []
    for k, c in CONT.items():
        ck = C[k]; yc, zcI, _ = ck["idler"]
        rows.append((k, c["setting"], f"{mmi(ck['z_c'], 1)}", f"{mmi(ck['z_top'], 1)}", f"{ck['contact']:.1f}°", f"{mmi(ck['fence'], 1)}",
                     f"y {yc:.1f} z {zcI:.1f}", f"{ck['web']:.0f}", f"{ck['wrap'] * 100:.0f} %"))
    S.table(1560, 1350, [("CONTAINER", 150), ("SET", 50), ("AXIS z", 170), ("TOP z", 170), ("CONTACT", 90), ("FENCE x", 160), ("IDLER", 160), ("WEB", 60), ("WRAP", 70)],
            rows, "S / J SETTINGS (z above the bench top; x from the label centre)", 12, 24)
    S.table(1560, 1500, [("FIT", 300), ("WHERE", 600), ("LIMITS", 340)], [
        ("Ø28 H7 / 6001 OD", "roller and housing bearing bores", "28.000 / 28.021"),
        ("Ø12 h6 / 6001 bore k6 class", "roller shafts, liner drive, rewind, idler", "11.989 / 12.000"),
        ("Ø40 H8 / g6", "housing spigots in the -x plate", "40.000 / 40.039 ; 39.975 / 39.991"),
        ("Ø16 H9 / f8", "arm pivot holes on the shaft 403", "16.000 / 16.043 ; 15.957 / 15.984"),
        ("Ø25 H8 / g6", "unwind spindle in the plate", "25.000 / 25.033"),
    ], "FITS", 12, 22)
    S.save(DWG / "P1-404-002_sections.svg")
