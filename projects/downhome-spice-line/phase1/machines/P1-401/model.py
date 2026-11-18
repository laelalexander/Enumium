"""P1-401 rev B 3D model from design.py: STEP per made part, machine assembly STEP/GLB, masses.json."""
import json
import math
import pathlib
import sys

import cadquery as cq

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from design import *  # noqa: F401,F403

OUT = HERE / "cad"; OUT.mkdir(exist_ok=True)
RHO = 7.95e-6


def W(pl="XY"):
    return cq.Workplane(pl)


def box(x0, x1, y0, y1, z0, z1):
    return W().box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(r, z0, h, x=0.0, y=0.0):
    return W().center(x, y).circle(r).extrude(h).translate((0, 0, z0))


def ring(ro, ri, z0, h, x=0.0, y=0.0):
    return W().center(x, y).circle(ro).circle(ri).extrude(h).translate((0, 0, z0))


def holes_z(s, pts, d, z0, z1):
    for x, y in pts:
        s = s.cut(cyl(d / 2, z0 - 1, z1 - z0 + 2, x, y))
    return s


def ferrule(od, idd, fl, L, z_face, up=True, x=0.0, y=0.0):
    """BPE short weld ferrule; face at z_face, tube body going up (up=True) or down."""
    if up:
        return ring(fl / 2, idd / 2, z_face, 6, x, y).union(ring(od / 2, idd / 2, z_face, L, x, y))
    return ring(fl / 2, idd / 2, z_face - 6, 6, x, y).union(ring(od / 2, idd / 2, z_face - L, L, x, y))


X0, X1 = -CAB["w"] / 2, CAB["w"] / 2
Y0, Y1 = CAB["y0"], CAB["y0"] + CAB["d"]
TY0, TY1 = Y0 - (TOP["d"] - CAB["d"]) / 2, Y1 + (TOP["d"] - CAB["d"]) / 2
T = CAB["t"]
COL_PTS = [(sx * CBASE["pcd"] / 2, COL["y"] + sy * CBASE["pcd"] / 2) for sx in (-1, 1) for sy in (-1, 1)]
ROD_PTS = [(0.0, -STAGE["rod_y"]), (0.0, STAGE["rod_y"])]
BUSH_HOLES = [(x + dx, y + dy) for x, y in ROD_PTS for dx in (-22, 22) for dy in (-22, 22)]


# ------------------------------------------------------------------ 100 cabinet
def p101_shell():
    """wrap: 2 sides + back, 1.5 mm, front return flanges 25 for the door"""
    s = box(X0, X1, Y0, Y1, Z_FOOT, ZC).cut(box(X0 + T, X1 - T, Y0 - 1, Y1 - T, Z_FOOT - 1, ZC + 1))
    s = s.union(box(X0, X0 + 25, Y0, Y0 + T, Z_FOOT, ZC)).union(box(X1 - 25, X1, Y0, Y0 + T, Z_FOOT, ZC))
    for z in (110.0,):                                  # cable glands in the back panel: M25 supply, M20 foot switch, M20 sensor
        for x in (-200.0, -140.0, -90.0):
            s = s.cut(W("XZ").center(x, z).circle(12.75 if x == -200 else 10.25).extrude(-20).translate((0, Y1 + 5, 0)))
    return s


def p102_top():
    s = box(-TOP["w"] / 2, TOP["w"] / 2, TY0, TY1, ZC, Z_TOP)
    s = holes_z(s, ROD_PTS, STAGE["rod_d"] + 4, ZC, Z_TOP)
    s = holes_z(s, BUSH_HOLES, 6.6, ZC, Z_TOP)
    s = s.cut(box(STAGE["bar_x"] - 8, STAGE["bar_x"] + 8, -PIN["bar_w"] / 2 - 4, PIN["bar_w"] / 2 + 4, ZC - 1, Z_TOP + 1))
    s = holes_z(s, COL_PTS, 13.0, ZC, Z_TOP)
    s = holes_z(s, [(PLG["x"], -12.0), (PLG["x"], 12.0)], 6.6, ZC, Z_TOP)            # plunger block 2 x M6
    s = holes_z(s, [(260.0, -140.0)], 25.0, ZC, Z_TOP)                                  # pod cable hole (pod 106 seal-welded on)
    s = holes_z(s, [(0.0, COL["y"])], 60.0, ZC, Z_TOP)                                   # column cable pass Ø60
    return s


def p103_base():
    s = box(X0, X1, Y0, Y1, Z_FOOT, Z_FOOT + 3.0)
    return holes_z(s, [(sx * FEET["x"], (Y0 + Y1) / 2 + sy * FEET["y"]) for sx in (-1, 1) for sy in (-1, 1)], 12.0, Z_FOOT, Z_FOOT + 3)


def p104_door():
    z0 = DOOR["z0"]
    d = box(-DOOR["w"] / 2, DOOR["w"] / 2, Y0 - T - 2, Y0 - 2, z0, z0 + DOOR["h"])
    d = d.union(box(-DOOR["w"] / 2, DOOR["w"] / 2, Y0 - 2, Y0 + 13, z0, z0 + T)).union(box(-DOOR["w"] / 2, DOOR["w"] / 2, Y0 - 2, Y0 + 13, z0 + DOOR["h"] - T, z0 + DOOR["h"]))
    return d.cut(W("XZ").center(DOOR["w"] / 2 - 40, z0 + DOOR["h"] / 2).circle(11).extrude(-20).translate((0, Y0 + 5, 0)))   # quarter-turn latch Ø22


def p105_panel():
    p = box(X0 + 30, X1 - 30, Y1 - T - 25 - 2, Y1 - T - 25, Z_FOOT + 40, ZC - 40)
    return p


def p106_pod():
    """HMI pod: sloped box 1.5 mm on the top, front right; HMI cut-out, E-stop and reset holes on the 30° face."""
    x0, x1, y0, y1, h0, h1 = 200.0, 320.0, -200.0, -80.0, 60.0, 130.0
    prof = W("YZ").polyline([(y0, Z_TOP), (y1, Z_TOP), (y1, Z_TOP + h1), (y0, Z_TOP + h0)]).close().extrude(x1 - x0).translate((x0, 0, 0))
    inner = W("YZ").polyline([(y0 + T, Z_TOP), (y1 - T, Z_TOP), (y1 - T, Z_TOP + h1 - T), (y0 + T, Z_TOP + h0 - T)]).close().extrude(x1 - x0 - 2 * T).translate((x0 + T, 0, -0.01))
    return prof.cut(inner)


def p107_backing():
    s = box(-90, 90, COL["y"] - 90, COL["y"] + 90, ZC - CBASE["back_t"], ZC)   # 180 sq, clear of the back wall (y 398.5)
    s = holes_z(s, [(0.0, COL["y"])], 60.0, ZC - CBASE["back_t"], ZC)
    return holes_z(s, COL_PTS, 13.0, ZC - CBASE["back_t"], ZC)


# ------------------------------------------------------------------ 200 column
def p201_tube():
    a, t = COL["a"], COL["t"]
    z0 = Z_TOP + CBASE["t"]
    return box(-a / 2, a / 2, COL["y"] - a / 2, COL["y"] + a / 2, z0, z0 + COL["L"]).cut(box(-a / 2 + t, a / 2 - t, COL["y"] - a / 2 + t, COL["y"] + a / 2 - t, z0 - 1, z0 + COL["L"] + 1))


def p202_base():
    s = box(-CBASE["a"] / 2, CBASE["a"] / 2, COL["y"] - CBASE["a"] / 2, COL["y"] + CBASE["a"] / 2, Z_TOP, Z_TOP + CBASE["t"])
    s = holes_z(s, COL_PTS, 13.0, Z_TOP, Z_TOP + CBASE["t"])
    return s.cut(cyl(30, Z_TOP - 1, 20, 0, COL["y"]))                    # cable pass Ø60 into the cabinet


CAP_PTS = [(sx * 60, COL["y"] + sy * 60) for sx in (-1, 1) for sy in (-1, 1)]


def p203_cap():
    s = box(-CAP["a"] / 2, CAP["a"] / 2, COL["y"] - CAP["a"] / 2, COL["y"] + CAP["a"] / 2, Z_HP - CAP["t"], Z_HP)
    s = holes_z(s, CAP_PTS, 8.5, Z_HP - CAP["t"], Z_HP)                  # M10 tapped (drill 8.5)
    return s.cut(cyl(25, Z_HP - CAP["t"] - 1, 20, 0, COL["y"]))


def p204_horseshoe():
    z1 = Z_RIM - RIM["t"]; z0 = z1 - HSH["t"]
    ro = HSH["ri"] + HSH["w"]
    r = ring(ro, HSH["ri"], z0, HSH["t"]).cut(box(-HSH["open"] / 2, HSH["open"] / 2, -ro - 5, 0, z0 - 1, z1 + 1))
    arm = box(-COL["a"] / 2, COL["a"] / 2, HSH["ri"] + 5, COL["y"] - COL["a"] / 2, z0, z1)
    r = r.union(arm).cut(box(-COL["a"] / 2, COL["a"] / 2, COL["y"] - COL["a"] / 2, COL["y"] + COL["a"] / 2, z0 - 1, z1 + 1))
    r = r.cut(cyl(HSH["ri"], z0 - 1, HSH["t"] + 2))
    for a in HSH["pin_a"]:                                                # 2 locating pins Ø8 x 12 proud
        x, y = (HSH["ri"] + 12) * math.cos(math.radians(a)), (HSH["ri"] + 12) * math.sin(math.radians(a))
        r = r.union(cyl(HSH["pin_d"] / 2, z1, 12, x, y))
    return r


# ------------------------------------------------------------------ 300 drive head
BR_PTS = [(SERVO_X + sx * 55, sy * 55) for sx in (-1, 1) for sy in (-1, 1)]
HOUS_PTS = [(HOUS["pcd"] / 2 * math.cos(math.radians(45 + 90 * k)), HOUS["pcd"] / 2 * math.sin(math.radians(45 + 90 * k))) for k in range(4)]
GM_PTS = [(GM_X + sx * 45, sy * 45) for sx in (-1, 1) for sy in (-1, 1)]
GUARD_PTS = [(-60.0, -78.0), (-60.0, 78.0), (200.0, -78.0), (200.0, 78.0)]


def p301_headplate():
    s = box(HPL["x0"], HPL["x1"], HPL["y0"], HPL["y1"], Z_HP, Z_HPT)
    s = s.cut(cyl(25.0, Z_HP - 1, 20))                                   # Ø50 H8 housing pilot
    s = holes_z(s, HOUS_PTS, 6.8, Z_HP, Z_HPT)                           # M8 tapped
    for x, y in BR_PTS:                                                   # bridge posts: slots 11 x 21 (belt tension)
        s = s.cut(W().center(x, y).slot2D(21, 11).extrude(20).translate((0, 0, Z_HP - 1)))
    for x, y in GM_PTS:                                                   # gearmotor flange: slots 9 x 19 (chain tension)
        s = s.cut(W().center(x, y).slot2D(19, 9).extrude(20).translate((0, 0, Z_HP - 1)))
    s = s.cut(W().center(GM_X, 0).slot2D(50, 36).extrude(20).translate((0, 0, Z_HP - 1)))   # gearmotor shaft passage
    s = holes_z(s, [(x, y) for x, y in CAP_PTS], 11.0, Z_HP, Z_HPT)
    s = s.cut(cyl(20.0, Z_HP - 1, 20, 0, COL["y"]))                     # cable pass
    for x, y in GUARD_PTS:                                                # chain guard 306: 4 x M6 tapped from below
        s = s.cut(cyl(2.5, Z_HP - 1, 20, x, y))
    return s


def p302_housing():
    z = Z_HPT
    h = cyl(HOUS["fl_d"] / 2, z, HOUS["fl_t"]).union(cyl(HOUS["body_d"] / 2, z + HOUS["fl_t"], HOUS["h_up"]))
    h = h.union(cyl(HOUS["pilot_d"] / 2, Z_HP, HPL["t"])).union(cyl(HOUS["spig_d"] / 2, Z_HP - (HOUS["spig_L"] - HPL["t"]), HOUS["spig_L"] - HPL["t"]))
    h = h.cut(cyl(BRG_SP["D"] / 2, HOUS["brg_lo"], HOUS["z_top"] - HOUS["brg_lo"] + 1))   # Ø52 H7 straight bore: 6205 + spacer + 6205 from the top
    h = h.cut(cyl(19.0, Z_HPT - 1, HOUS["fl_t"] + 1))                                    # shoulder bore Ø38 under the lower bearing
    h = h.cut(cyl(14.0, Z_HP - HOUS["spig_L"], 200))                                    # Ø28 through the pilot and spigot
    h = h.cut(ring(HOUS["spig_d"] / 2 + 1, HOUS["spig_d"] / 2 - 1.15, HUB["z_brg"] - 1.85, 1.85))   # DIN 471 Ø40 groove right under the bearings
    for x, y in HOUS_PTS:
        h = h.cut(cyl(4.5, z - 1, HOUS["fl_t"] + 2, x, y))
    return h


def p303_spindle():
    zt = SPN["top"]
    s = cyl(SPN["seat"] / 2, Z_PUL, zt - Z_PUL).union(cyl(SPN["d"] / 2, SPN["Z_cpl"], Z_PUL - SPN["Z_cpl"]))
    s = s.cut(cyl(7.0, SPN["Z_cpl"] - 1, 31))                               # M16 x 1.5 LH, 30 deep (Ø14.5 drill)
    s = s.cut(cyl(4.25, zt - 25, 26))                                        # M10 end bolt, 22 deep
    s = s.cut(box(-3, 3, SPN["seat"] / 2 - 3.5, SPN["seat"] / 2 + 1, Z_PUL + 3, zt - 3))   # key 6 x 6
    for zr in (HOUS["brg_lo"] - 1.6, HOUS["z_top"] + 0.2):                   # DIN 471 Ø25 grooves under the lower and over the upper bearing
        s = s.cut(ring(14, 11.75, zr, 1.3))
    return s


def p304_hub():
    z1 = HUB["z1"]
    hb = cyl(HUB["od"] / 2, HUB["z_seal"], z1 - HUB["fl_t"] - HUB["z_seal"]).union(cyl(HUB["fl_d"] / 2, z1 - HUB["fl_t"], HUB["fl_t"]))
    hb = hb.cut(cyl(BRG_AG["D"] / 2, HUB["z_brg"], z1 - HUB["z_brg"] + 1))
    hb = hb.cut(cyl(HUB["seal_d"] / 2, HUB["z_seal"] - 1, HUB["seal_b"] + 1))
    hb = hb.cut(cyl(24.0, HUB["z_seal"] + HUB["seal_b"], HUB["z_brg"] - HUB["z_seal"] - HUB["seal_b"]))   # Ø48 ring relief
    hb = hb.union(ferrule(63.5, 60.2, 77.5, 21.5, Z_AGTC, up=True).cut(cyl(30.1, Z_AGTC - 1, 40)))
    hb = hb.cut(cyl(13.0, Z_AGTC - 1, 200))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        hb = hb.cut(cyl(2.5, z1 - HUB["fl_t"] - 1, 20, HUB["spr_pcd"] / 2 * math.cos(a), HUB["spr_pcd"] / 2 * math.sin(a)))   # M6 tapped x 4
    return hb


def p305_beltguard():
    """1.5 mm box round both pulleys under the bridge flange, with a top hat over the spindle end"""
    x0, x1, y0, y1 = SERVO_X - 45, 50.0, -50.0, 50.0
    z0, z1 = HOUS["z_top"] + HOUS["cap_t"], Z_HPT + BRIDGE["h"] - 1
    g = box(x0, x1, y0, y1, z0, z1).cut(box(x0 + T, x1 - T, y0 + T, y1 - T, z0 - 1, z1 - T))
    g = g.cut(cyl(HOUS["body_d"] / 2 + 2, z0 - 1, 10)).cut(cyl(30, z1 - 5, 10))
    g = g.union(ring(32, 30.5, z1 - T, 20)).union(cyl(32, z1 + 20 - T, T))
    for x, y in BR_PTS:
        g = g.cut(cyl(BRIDGE["post_d"] / 2 + 1, z0 - 1, 60, x, y))
    return g


def p306_chainguard():
    x0, x1, y0, y1 = -75.0, GM_X + 45, -70.0, 70.0
    z1, z0 = Z_HP, Z_HP - 32
    g = box(x0, x1, y0, y1, z0, z1).cut(box(x0 + T, x1 - T, y0 + T, y1 - T, z0 + T, z1 + 1))
    for x, y in GUARD_PTS:                                                # 4 tabs 30 x 16 folded out at the top, Ø6.6 for M6
        sy = 1 if y > 0 else -1
        g = g.union(box(x - 15, x + 15, *sorted((sy * y1, sy * (y1 + 16))), z1 - T, z1)).cut(cyl(3.3, z1 - 5, 10, x, y))
    return g.cut(cyl(HUB["od"] / 2 + 3, z0 - 1, 10))


def p307_bridge():
    zb = Z_HPT + BRIDGE["h"]
    fl = box(SERVO_X - BRIDGE["a"] / 2, SERVO_X + BRIDGE["a"] / 2, -BRIDGE["a"] / 2, BRIDGE["a"] / 2, zb, zb + BRIDGE["t"])
    fl = fl.cut(cyl(35.0, zb - 1, 20, SERVO_X, 0))                       # Ø70 H8 servo pilot
    for k in range(4):
        a = math.radians(45 + 90 * k)
        fl = fl.cut(cyl(3.3, zb - 1, 20, SERVO_X + 45 * math.cos(a), 45 * math.sin(a)))      # 4 x Ø6.6 on Ø90 (servo M6)
    for y in (-30.0, 30.0):
        fl = fl.cut(cyl(2.5, zb - 1, 9, SERVO_X + 62, y))                 # 2 x M6 x 8 deep from below: belt guard 305
    for x, y in BR_PTS:
        fl = fl.union(cyl(BRIDGE["post_d"] / 2, Z_HPT, BRIDGE["h"], x, y))
    return fl


def p308_cap():
    z = HOUS["z_top"]
    c = cyl(HOUS["body_d"] / 2, z, HOUS["cap_t"]).cut(cyl(13.0, z - 1, 20)).cut(cyl(18.0, z - 1, 4)).cut(cyl(20.0, z + 3, 7))   # ring recess Ø36 x 3, seal pocket Ø40 x 7
    for k in range(4):
        a = math.radians(45 + 90 * k)
        c = c.cut(cyl(2.25, z - 1, 20, 31 * math.cos(a), 31 * math.sin(a)))       # 4 x Ø4.5 on Ø62 (M4)
    return c


def p309_spacer_out():
    return ring(SPACER["od"] / 2 - 0.02, SPACER["id_o"] / 2, HOUS["brg_lo"] + BRG_SP["B"], SPACER["L"])


def p310_spacer_in():
    return ring(SPACER["od_i"] / 2, SPACER["d_i"] / 2, HOUS["brg_lo"] + BRG_SP["B"], SPACER["L"])


# ------------------------------------------------------------------ 400 hopper (316L)
def p401_cyl():
    return ring(HOP["r"] + T14, HOP["r"], Z_CYL0, HOP["h_cyl"])


def p402_cone():
    o = W().circle(HOP["r"] + T14).workplane(offset=-HOP["h_cone"]).circle(HOP["r_lo"] + T14).loft()
    i = W().workplane(offset=0.01).circle(HOP["r"]).workplane(offset=-HOP["h_cone"] - 0.02).circle(HOP["r_lo"]).loft()
    return o.cut(i).translate((0, 0, Z_CYL0))


def p403_ferrule():
    return ferrule(TC25["od"], TC25["id"], TC25["fl"], TC25["L"], Z_TC, up=True)


def p404_rim():
    r0 = HOP["r"] + T14
    a = ring(r0 + RIM["w"], r0, Z_RIM - RIM["t"], RIM["t"]).union(ring(r0 + RIM["t"], r0, Z_RIM - RIM["w"], RIM["w"]))
    for ang in HSH["pin_a"]:
        x, y = (HSH["ri"] + 12) * math.cos(math.radians(ang)), (HSH["ri"] + 12) * math.sin(math.radians(ang))
        a = a.cut(cyl(4.5, Z_RIM - 10, 20, x, y))
    return a


def p405_lid():
    r = HOP["r"] + T14 + RIM["w"]
    l = cyl(r, Z_RIM, LID["t"]).union(ring(r, r - LID["t"], Z_RIM - 15, 15))
    l = l.cut(cyl(LID["bore"] / 2, Z_RIM - 1, 10))
    l = l.cut(box(LID["port_x"] - LID["port_w"] / 2, LID["port_x"] + LID["port_w"] / 2, -LID["port_l"] / 2, LID["port_l"] / 2, Z_RIM - 1, Z_RIM + 5))
    l = l.union(box(LID["port_x"] - LID["port_w"] / 2 - LID["t"], LID["port_x"] + LID["port_w"] / 2 + LID["t"], -LID["port_l"] / 2 - LID["t"], LID["port_l"] / 2 + LID["t"],
                    Z_RIM, Z_RIM + LID["up"]).cut(box(LID["port_x"] - LID["port_w"] / 2, LID["port_x"] + LID["port_w"] / 2, -LID["port_l"] / 2, LID["port_l"] / 2, Z_RIM - 1, Z_RIM + LID["up"] + 1)))
    l = l.union(ring(LID["bore"] / 2 + LID["t"], LID["bore"] / 2, Z_RIM, 25))                    # dust collar round the sleeve
    return l


def p406_flap():
    x0, x1 = LID["port_x"] - LID["port_w"] / 2 - 5, LID["port_x"] + LID["port_w"] / 2 + 5
    return box(x0, x1, -LID["port_l"] / 2 - 5, LID["port_l"] / 2 + 5, Z_RIM + LID["up"], Z_RIM + LID["up"] + LID["t"]).union(
        box(x0, x0 + 12, -LID["port_l"] / 2 - 5, LID["port_l"] / 2 + 5, Z_RIM + LID["up"] - 10, Z_RIM + LID["up"]))


def p407_handles():
    """2 U handles 10 x 10 bar on the cylinder, left and right"""
    out = None
    for sx in (-1, 1):
        x = sx * (HOP["r"] + T14)
        xs = sorted((x, x + sx * 40)); xe = sorted((x + sx * 30, x + sx * 40))
        z0, z1 = Z_CYL0 + 70, Z_CYL0 + 80
        hd = box(*xs, -45, -35, z0, z1).union(box(*xs, 35, 45, z0, z1)).union(box(*xe, -45, 45, z0, z1))
        out = hd if out is None else out.union(hd)
    return out


# ------------------------------------------------------------------ 500 agitator (316L)
def r_cone(z):
    return HOP["r_lo"] + (HOP["r"] - HOP["r_lo"]) * (z - Z_CONE0) / HOP["h_cone"]


def p501_sleeve():
    s = ring(AGIT["sleeve_od"] / 2, AGIT["sleeve_od"] / 2 - AGIT["sleeve_t"], AGIT["z_arm"], Z_AGTC - 21.5 - AGIT["z_arm"] + 21.5 - 21.5)
    return s.union(ferrule(63.5, 60.2, 77.5, 21.5, Z_AGTC, up=False))


def p502_arms():
    out = None
    for a in (0.0, 180.0):
        b = box(AGIT["sleeve_od"] / 2 - 1, AGIT["r_tip"], -AGIT["arm_w"] / 2, AGIT["arm_w"] / 2, AGIT["z_arm"], AGIT["z_arm"] + AGIT["arm_t"]).rotate((0, 0, 0), (0, 0, 1), a)
        out = b if out is None else out.union(b)
    return out


def p503_blades():
    out = None
    rw = HOP["r"] - AGIT["clear"]
    for a in (0.0, 180.0):
        v = box(rw - AGIT["blade_t"], rw, -AGIT["blade_w"] / 2, AGIT["blade_w"] / 2, Z_CYL0, AGIT["z_arm"] + AGIT["arm_t"])
        # cone scraper: inclined bar along the cone wall, 10 off, from Z_CYL0 down to z_cone_end
        z0, z1 = AGIT["z_cone_end"], Z_CYL0
        r0, r1 = r_cone(z0) - AGIT["clear"] / math.cos(math.atan((HOP["r"] - HOP["r_lo"]) / HOP["h_cone"])), rw
        L = math.hypot(r1 - r0, z1 - z0)
        ang = math.degrees(math.atan2(z1 - z0, r1 - r0))
        c = W().box(L, AGIT["blade_w"], AGIT["blade_t"]).rotate((0, 0, 0), (0, 1, 0), -ang).translate(((r0 + r1) / 2 - AGIT["blade_t"] / 2, 0, (z0 + z1) / 2))
        g = v.union(c).rotate((0, 0, 0), (0, 0, 1), a)
        out = g if out is None else out.union(g)
    return out


# ------------------------------------------------------------------ 700 container stage
SB_PTS = [(-85.0, STAGE["d"] / 2 - 15), (-70.0, STAGE["d"] / 2 - 15)]   # sensor bracket M5 x 2


def stage_z(k="jar-12"):
    return Z_TOP + STAGE_POS[k]


def p701_plate(k="jar-12"):
    z = stage_z(k)
    s = box(-STAGE["w"] / 2, STAGE["w"] / 2, -STAGE["d"] / 2, STAGE["d"] / 2, z, z + STAGE["t"])
    s = holes_z(s, ROD_PTS, 10.5, z, z + STAGE["t"])                      # Ø10.5 csk for M10 x 20 into the rod ends
    s = holes_z(s, SB_PTS, 4.2, z, z + STAGE["t"])                        # M5 sensor bracket
    return holes_z(s, [(sx * 70, sy * 70) for sx in (-1, 1) for sy in (-1, 1)], 4.2, z, z + STAGE["t"])   # M5 nest screws


def p702_rods(k="jar-12"):
    z = stage_z(k)
    out = None
    for x, y in ROD_PTS:
        r = cyl(STAGE["rod_d"] / 2, z - STAGE["rod_L"], STAGE["rod_L"], x, y)
        out = r if out is None else out.union(r)
    return out


def p703_bushings():
    out = None
    for x, y in ROD_PTS:
        b = box(x - STAGE["bush_a"] / 2, x + STAGE["bush_a"] / 2, y - STAGE["bush_a"] / 2, y + STAGE["bush_a"] / 2, ZC - STAGE["bush_L"], ZC)
        b = b.cut(cyl(STAGE["rod_d"] / 2 + 0.05, ZC - STAGE["bush_L"] - 1, STAGE["bush_L"] + 2, x, y))
        out = b if out is None else out.union(b)
    return out


def p704_pinbar(k="jar-12"):
    z = stage_z(k)
    x = STAGE["bar_x"]
    b = box(x - PIN["bar_t"] / 2, x + PIN["bar_t"] / 2, -PIN["bar_w"] / 2, PIN["bar_w"] / 2, z - STAGE["bar_L"], z)
    for d in PINBAR_HOLES.values():
        b = b.cut(W("YZ").center(0, z - d).circle(PIN["hole"] / 2).extrude(30).translate((x - 15, 0, 0)))
    return b


def p705_plgblock():
    b = box(PLG["x"] - 20, PLG["x"] + 20, -25, 25, Z_TOP, Z_TOP + 40)
    b = b.cut(W("YZ").center(0, Z_TOP + PLG["h"]).circle(7.25).extrude(50).translate((PLG["x"] - 25, 0, 0)))     # M16 x 1.5 tapped (Ø14.5)
    return b.cut(cyl(3.3, Z_TOP - 1, 15, PLG["x"], -12)).cut(cyl(3.3, Z_TOP - 1, 15, PLG["x"], 12))


def p706_sensorbkt(k="jar-12"):
    """3 mm angle 40 x 30 x 45 high; Ø18.5 for the QS18 at 25 above the stage, looking +x across it"""
    z = stage_z(k) + STAGE["t"]
    yc = STAGE["d"] / 2 - 15
    b = box(-100, -60, yc - 15, yc + 15, z, z + 3).union(box(-100, -97, yc - 15, yc + 15, z, z + 45))
    b = b.cut(W("YZ").center(yc, z + 25).circle(9.25).extrude(10).translate((-105, 0, 0)))
    for x, y in SB_PTS:
        b = b.cut(cyl(2.75, z - 1, 5, x, y))
    return b


# ------------------------------------------------------------------ 600 tooling (bought to our spec): jar tooling installed
def tool_tube(t="J"):
    T_ = TOOL[t]
    tube = ring(T_["tube_od"] / 2, T_["tube_id"] / 2, Z_OUT, Z_TC - 25 - Z_OUT)
    red = (W().circle(TC25["od"] / 2).workplane(offset=25 - 10).circle(T_["tube_od"] / 2).loft()
           .cut(W().workplane(offset=-0.01).circle(TC25["id"] / 2).workplane(offset=25 - 10 + 0.02).circle(T_["tube_id"] / 2).loft()))
    red = red.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, Z_TC - 6 - 0.0))
    fer = ring(TC25["fl"] / 2, TC25["id"] / 2, Z_TC - 6, 6)
    return tube.union(red).union(fer)


def tool_auger(t="J"):
    T_ = TOOL[t]
    sh = cyl(8.0, Z_OUT + 5, SPN["Z_cpl"] - Z_OUT - 5)
    z0, z1 = Z_OUT + 5, Z_TC + 30
    n = (z1 - z0) / T_["pitch"]
    sp = cq.Wire.makeHelix(T_["pitch"], z1 - z0, T_["auger_od"] / 2 - 4)
    flight = (W("XZ").center(T_["auger_od"] / 2 - 4, 0).rect(8, 2.5).sweep(cq.Workplane().add(sp), isFrenet=True)).translate((0, 0, z0))
    return sh.union(flight)


def bought():
    servo = cyl(40, Z_HPT + BRIDGE["h"] + BRIDGE["t"], 150, SERVO_X, 0).union(box(SERVO_X - 40, SERVO_X + 40, -40, 40, Z_HPT + BRIDGE["h"] + BRIDGE["t"], Z_HPT + BRIDGE["h"] + BRIDGE["t"] + 12))
    pulleys = cyl(PD2 / 2 + 2, Z_PUL, 22).union(cyl(PD1 / 2 + 2, Z_PUL, 22, SERVO_X, 0))
    belt = (W().center(SERVO_X / 2, 0).rect(BELT["C"], PD1 + 6).extrude(15).translate((0, 0, Z_PUL + 3))).union(cyl(PD2 / 2 + 3, Z_PUL + 3, 15)).union(cyl(PD1 / 2 + 3, Z_PUL + 3, 15, SERVO_X, 0))
    gm = box(GM_X - 55, GM_X + 55, -55, 55, Z_HPT, Z_HPT + 110).union(cyl(52, Z_HPT + 110, 150, GM_X, 0).rotate((GM_X, 0, Z_HPT + 160), (GM_X + 1, 0, Z_HPT + 160), 0))
    spro = cyl(61.1, HUB["z1"] - HUB["fl_t"] - 8, 8).union(cyl(30.5, HUB["z1"] - HUB["fl_t"] - 8, 8, GM_X, 0))
    plg = W("YZ").center(0, Z_TOP + PLG["h"]).circle(14).extrude(60).translate((PLG["x"] + 20, 0, 0))
    pod_hmi = box(225.0, 295.0, -180.0, -110.0, Z_TOP + 80, Z_TOP + 110)
    sensor = W("YZ").center(STAGE["d"] / 2 - 15, stage_z() + STAGE["t"] + 25).circle(9).extrude(70).translate((-140, 0, 0))
    foot = box(-150, 150, -620, -420, 0, 60)
    feet = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            f = cyl(FEET["pad"] / 2, 0, 12, sx * FEET["x"], FEET["yc"] + sy * FEET["y"]).union(cyl(6, 12, Z_FOOT - 12, sx * FEET["x"], FEET["yc"] + sy * FEET["y"]))
            feet = f if feet is None else feet.union(f)
    return {"P1-413": servo, "P1-431": pulleys.union(belt), "P1-414": gm, "P1-432": spro, "P1-434": plg, "P1-416": pod_hmi, "P1-435": sensor, "P1-417": foot, "P1-443": feet,
            "P1-415J": tool_tube("J"), "P1-415A": tool_auger("J")}


PARTS = {}


def build():
    PARTS.update({
        "P1-401-101": p101_shell(), "P1-401-102": p102_top(), "P1-401-103": p103_base(), "P1-401-104": p104_door(), "P1-401-105": p105_panel(),
        "P1-401-106": p106_pod(), "P1-401-107": p107_backing(),
        "P1-401-201": p201_tube(), "P1-401-202": p202_base(), "P1-401-203": p203_cap(), "P1-401-204": p204_horseshoe(),
        "P1-401-301": p301_headplate(), "P1-401-302": p302_housing(), "P1-401-303": p303_spindle(), "P1-401-304": p304_hub(), "P1-401-305": p305_beltguard(),
        "P1-401-306": p306_chainguard(), "P1-401-307": p307_bridge(), "P1-401-308": p308_cap(),
        "P1-401-309": p309_spacer_out(), "P1-401-310": p310_spacer_in(),
        "P1-401-401": p401_cyl(), "P1-401-402": p402_cone(), "P1-401-403": p403_ferrule(), "P1-401-404": p404_rim(), "P1-401-405": p405_lid(),
        "P1-401-406": p406_flap(), "P1-401-407": p407_handles(),
        "P1-401-501": p501_sleeve(), "P1-401-502": p502_arms(), "P1-401-503": p503_blades(),
        "P1-401-701": p701_plate(), "P1-401-702": p702_rods(), "P1-401-703": p703_bushings(), "P1-401-704": p704_pinbar(), "P1-401-705": p705_plgblock(),
        "P1-401-706": p706_sensorbkt()})
    return PARTS


GROUP = {"P1-401-100": ["P1-401-10%d" % i for i in range(1, 8)],
         "P1-401-200": ["P1-401-20%d" % i for i in range(1, 5)],
         "P1-401-300": ["P1-401-30%d" % i for i in range(1, 10)] + ["P1-401-310"],
         "P1-401-400": ["P1-401-40%d" % i for i in range(1, 8)],
         "P1-401-500": ["P1-401-50%d" % i for i in range(1, 4)],
         "P1-401-700": ["P1-401-70%d" % i for i in range(1, 7)]}
DENS = {"P1-401-703": 0.94e-6}       # UHMW-PE

if __name__ == "__main__":
    P = build()
    masses = {}
    asm = cq.Assembly(name="P1-401")
    col_ss, col_b = cq.Color(0.78, 0.80, 0.83), cq.Color(0.20, 0.32, 0.55)
    for g, ids in GROUP.items():
        sub = cq.Assembly(name=g)
        for pid in ids:
            s = P[pid]
            masses[pid] = round(s.val().Volume() * DENS.get(pid, RHO), 3)
            cq.exporters.export(s, str(OUT / f"{pid}.step"))
            sub.add(s, name=pid, color=cq.Color(0.95, 0.95, 0.92) if pid == "P1-401-703" else col_ss)
        asm.add(sub, name=g)
    cols = {"P1-414": cq.Color(0.2, 0.32, 0.55), "P1-413": cq.Color(0.15, 0.15, 0.17), "P1-417": cq.Color(0.9, 0.75, 0.1), "P1-415J": cq.Color(0.85, 0.86, 0.88),
            "P1-415A": cq.Color(0.70, 0.72, 0.75), "P1-416": cq.Color(0.1, 0.1, 0.1)}
    for k, s in bought().items():
        asm.add(s, name=k, color=cols.get(k, col_b))
    asm.save(str(OUT / "P1-401-ASM.step"))
    asm.save(str(OUT / "P1-401-ASM.glb"), exportType="GLTF", tolerance=0.3, angularTolerance=0.2)
    (OUT / "masses.json").write_text(json.dumps(masses, indent=1))
    print(json.dumps(masses), round(sum(masses.values()), 2), "kg made parts")
