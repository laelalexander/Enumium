"""P1-406 rev B 3D model from design.py: STEP per made part, machine assembly STEP/GLB, masses.json.
Modelled with guides at setting J, a jar under the head, the pusher retracted."""
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
RHO_UHMW = 0.94e-6
RHO_FRP = 1.9e-6
JAR = CONT["jar-12"]
YI, YO = SIDE["y_in"], SIDE["y_in"] + SIDE["t"]          # side plate inner / outer face (|y|)


def W(pl="XY"):
    return cq.Workplane(pl)


def box(x0, x1, y0, y1, z0, z1):
    return W().box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(r, z0, h, x=0.0, y=0.0):
    return W().circle(r).extrude(h).translate((x, y, z0))


def ycyl(r, y0, y1, x, z):                     # cylinder along y
    return W("XZ").circle(r).extrude(-(y1 - y0)).translate((x, y0, z))


def xcyl(r, x0, x1, y, z):                     # cylinder along x
    return W("YZ").circle(r).extrude(x1 - x0).translate((x0, y, z))


def tube_z(sq, t, x, y, z0, z1):               # square tube along z
    return box(x - sq / 2, x + sq / 2, y - sq / 2, y + sq / 2, z0, z1).cut(box(x - sq / 2 + t, x + sq / 2 - t, y - sq / 2 + t, y + sq / 2 - t, z0 - 1, z1 + 1))


def tube_y(a, b, t, x, z, y0, y1):             # rect tube along y, a along x, b along z
    return box(x - a / 2, x + a / 2, y0, y1, z - b / 2, z + b / 2).cut(box(x - a / 2 + t, x + a / 2 - t, y0 - 1, y1 + 1, z - b / 2 + t, z + b / 2 - t))


def tube_x(a, b, t, y, z, x0, x1):             # rect tube along x, a along y, b along z
    return box(x0, x1, y - a / 2, y + a / 2, z - b / 2, z + b / 2).cut(box(x0 - 1, x1 + 1, y - a / 2 + t, y + a / 2 - t, z - b / 2 + t, z + b / 2 - t))


def holes_y(s, pts, d, y0=-500.0, y1=500.0):
    for x, z in pts:
        s = s.cut(ycyl(d / 2, y0, y1, x, z))
    return s


# ------------------------------------------------------------------ 100 frame
SPINE_Z = SPINE["z"] - 20.0 - SPINE["h"] / 2                 # spine under the leg braces: braces z 280..320, spine z 200..280
BRG_HOLES = [(sx * PUL["brg_bolt"] / 2, sz * PUL["brg_bolt"] / 2) for sx in (-1, 1) for sz in (-1, 1)]
CLIP_X = [495.0, 510.0]                                      # FRP clip screws (|x|)
GUIDE_BKT_X = {+1: [530.0], -1: [545.0, 640.0]}              # guide brackets (|x|) per end, clear of the bearing ears
BIN_HOOKS = [BIN["x0"] + 25.0, BIN["x0"] + 95.0]
EAR = 100.0                                                  # bearing ear 100 wide, top at the pulley centre + 50
PUSH_BKT = (REJ["x"], -YO)


def side_plate(sx, sy):
    """one 4 mm side plate of an end frame: x from 475 to 760 (sign sx), y face at +-100 (sign sy), z 763..903; pulley shaft slot / hole and bearing holes."""
    x0, x1 = sorted((sx * SIDE["x0"], sx * SIDE["x1"]))
    y0, y1 = sorted((sy * YI, sy * YO))
    p = box(x0, x1, y0, y1, Z_SIDE0, Z_SIDE1)
    xp = sx * PUL["x"]
    p = p.union(box(xp - EAR / 2, xp + EAR / 2, y0, y1, Z_SIDE1 - 1, Z_PUL + EAR / 2))        # bearing ear above the plate top
    if sx < 0:                                               # tail: take-up slots
        p = p.cut(box(xp - TAKEUP / 2 - 11, xp + TAKEUP / 2 + 11, y0 - 1, y1 + 1, Z_PUL - 11, Z_PUL + 11))
        for dx, dz in BRG_HOLES:
            p = p.cut(box(xp + dx - TAKEUP / 2 - 5.5, xp + dx + TAKEUP / 2 + 5.5, y0 - 1, y1 + 1, Z_PUL + dz - 5.5, Z_PUL + dz + 5.5))
    else:
        p = holes_y(p, [(xp, Z_PUL)], 26.0)
        p = holes_y(p, [(xp + dx, Z_PUL + dz) for dx, dz in BRG_HOLES], 11.0)
    p = holes_y(p, [(sx * cx, Z_BELT - 22.0) for cx in CLIP_X], 6.6)
    return p


def end_frame(sx):
    f = None
    for sy in (-1, 1):
        s = side_plate(sx, sy)
        f = s if f is None else f.union(s)
        f = f.union(tube_z(LEG["sq"], LEG["t"], sx * LEG["x"], sy * LEG["y"], LEG["z_foot"], Z_SIDE0 + 60.0))       # leg welded to the plate outside
    xb0, xb1 = sorted((sx * (SIDE["x0"] + 5.0), sx * (PUL["x"] - PUL["d"] / 2 - 8.0)))
    f = f.union(box(xb0, xb1, -YI, YI, Z_SIDE1 - BED_SS["t"], Z_SIDE1))                       # SS bed
    for cx in (560.0, 660.0):
        f = f.union(tube_y(40.0, 40.0, 2.0, sx * cx, Z_SIDE0 + 20.0, -YI, YI))                 # cross tubes under the bed
    f = f.union(tube_y(40.0, 40.0, 2.0, sx * LEG["x"], BRACE_Z, -LEG["y"] + 20, LEG["y"] - 20))   # leg brace
    for sy in (-1, 1):
        f = f.union(box(sx * LEG["x"] - 30, sx * LEG["x"] + 30, sy * LEG["y"] - 30, sy * LEG["y"] + 30, LEG["z_foot"] - 8, LEG["z_foot"]))   # foot pad 60 sq x 8 (M16 nut)
    if sx < 0:                                               # take-up lugs at the tail
        for sy in (-1, 1):
            f = f.union(box(-SIDE["x1"], -SIDE["x1"] + 8.0, sy * YO, sy * (YO + 30.0), Z_PUL - 15, Z_PUL + 15) if sy > 0 else
                        box(-SIDE["x1"], -SIDE["x1"] + 8.0, -(YO + 30.0), -YO, Z_PUL - 15, Z_PUL + 15))
    return f


def p101_infeed():
    return end_frame(-1)


def p102_outfeed():
    return end_frame(+1)


def p103_spine():
    s = tube_x(SPINE["w"], SPINE["h"], SPINE["t"], 0.0, SPINE_Z, -LEG["x"] - 20, LEG["x"] + 20)
    for sx in (-1, 1):
        s = s.union(box(sx * LEG["x"] - 30, sx * LEG["x"] + 30, -40, 40, SPINE_Z + SPINE["h"] / 2, SPINE_Z + SPINE["h"] / 2 + 8))  # top plates to the braces
    return s


def p104_headstand():
    zb = SPINE_Z + SPINE["h"] / 2
    s = tube_y(80.0, 40.0, 3.0, 0.0, zb + 20.0, -STAND["beam_y"], STAND["beam_y"])
    for sy in (-1, 1):
        s = s.union(tube_z(STAND["post"], STAND["t"], 0.0, sy * HEAD["lug_y"], zb + 40.0, HEAD["lug_z"] - 8.0))
        s = s.union(box(-60, 60, sy * HEAD["lug_y"] - 35, sy * HEAD["lug_y"] + 35, HEAD["lug_z"] - 8.0, HEAD["lug_z"]))   # top plate, slots for the head lugs
    return s


# ------------------------------------------------------------------ 200 belt run
def pulley(drive):
    yl0 = -(YO + PUL["brg_t"] + (95.0 if drive else 8.0)); yl1 = YO + PUL["brg_t"] + 8.0
    drum = ycyl(PUL["d"] / 2, -PUL["face"] / 2, PUL["face"] / 2, 0, 0).cut(ycyl(PUL["d"] / 2 - 4.0, -PUL["face"] / 2 + 8.0, PUL["face"] / 2 - 8.0, 0, 0))   # pipe drum + 2 end discs 8
    sh = ycyl(PUL["shaft"] / 2, yl0, yl1, 0, 0)
    return drum.union(sh)


def p201_drive():
    return pulley(True).translate((PUL["x"], 0, Z_PUL))


def p202_tail():
    return pulley(False).translate((-PUL["x"], 0, Z_PUL))


def p203_takeup():
    out = None
    for sy in (-1, 1):
        y = sy * (YO + 15.0)
        s = xcyl(5.0, -SIDE["x1"] - 25.0, -PUL["x"] - PUL["brg_sq"] / 2, y, Z_PUL)   # M10 push screw against the bearing flange
        out = s if out is None else out.union(s)
    return out


def p204_frp():
    out = None
    for sy in (-1, 1):
        r = box(-FRP["x"], FRP["x"], sy * FRP["y"] - FRP["w"] / 2, sy * FRP["y"] + FRP["w"] / 2, Z_BELT - BELT["t"] - UBED["t"] - FRP["h"], Z_BELT - BELT["t"] - UBED["t"])
        r = r.cut(box(-FRP["x"] + FRP["t"], FRP["x"] - FRP["t"], sy * FRP["y"] - FRP["w"] / 2 + FRP["t"], sy * FRP["y"] + FRP["w"] / 2 - FRP["t"],
                      Z_BELT - BELT["t"] - UBED["t"] - FRP["h"] + FRP["t"], Z_BELT - BELT["t"] - UBED["t"] - FRP["t"]))
        out = r if out is None else out.union(r)
    return out


def p205_clips():
    out = None
    zr0 = Z_BELT - BELT["t"] - UBED["t"] - FRP["h"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((sx * 490.0, sx * 540.0))
            ya, yb = sorted((sy * (FRP["y"] + FRP["w"] / 2), sy * YI))
            c = box(xa, xb, ya, yb, zr0 - 4.0, zr0)                                  # shelf under the rail
            ya2, yb2 = sorted((sy * (YI - 4.0), sy * YI))
            c = c.union(box(xa, xb, ya2, yb2, zr0 - 4.0, Z_BELT - 12.0))                  # upright on the plate inner face
            out = c if out is None else out.union(c)
    return out


def p206_bed():
    return box(-UBED["x"], UBED["x"], -UBED["w"] / 2, UBED["w"] / 2, Z_BELT - BELT["t"] - UBED["t"], Z_BELT - BELT["t"])


def guide_strip(x0, x1, sy, k="J"):
    y = sy * (GUIDE["gap"][k] / 2)
    ya, yb = sorted((y, y + sy * GUIDE["t"]))
    return box(x0, x1, ya, yb, Z_BELT + 5.0, Z_BELT + 5.0 + GUIDE["h"])


def p207_guides(k="J"):
    g = guide_strip(-SIDE["x1"], -UBED["x"], -1, k).union(guide_strip(-SIDE["x1"], -UBED["x"], 1, k))
    for sy in (-1, 1):
        g = g.union(guide_strip(UBED["x"], REJ["x"] - 70.0, sy, k))
    return g


def p208_guidebkts(k="J"):
    out = None
    for sx in (-1, 1):
        for cx in GUIDE_BKT_X[sx]:
            for sy in (-1, 1):
                y_in = sy * (GUIDE["gap"][k] / 2 + GUIDE["t"])
                ya, yb = sorted((y_in, sy * YO))
                b = box(sx * cx - 15, sx * cx + 15, ya, yb, Z_BELT + 15, Z_BELT + 20)                 # arm over the plate top, slotted
                yc0, yc1 = sorted((sy * YO, sy * (YO + 3)))
                b = b.union(box(sx * cx - 15, sx * cx + 15, yc0, yc1, Z_SIDE1 - 30, Z_BELT + 20))   # down the plate outer face
                out = b if out is None else out.union(b)
    return out


# ------------------------------------------------------------------ 300 reject
def p301_pushbkt():
    x = REJ["x"]
    b = box(x - 40, x + 40, -YO - 6.0, -YO, Z_SIDE1 - 60, REJ["z"] + 25)                     # plate on the -y side plate outer face
    b = b.union(box(x - 40, x + 40, -YO - 260.0, -YO - 6.0, REJ["z"] - 35, REJ["z"] - 29))     # shelf under the actuator body
    b = b.union(box(x - 40, x + 40, -YO - 266.0, -YO - 260.0, REJ["z"] - 35, REJ["z"] + 15))   # rear clevis plate
    return b


def p302_paddle():
    y0 = -GUIDE["gap"]["J"] / 2 - 18.0
    return box(REJ["x"] - REJ["paddle_w"] / 2, REJ["x"] + REJ["paddle_w"] / 2, y0 - 20.0, y0, Z_BELT + 6.0, Z_BELT + 6.0 + REJ["paddle_h"])


def p303_bin():
    b = box(BIN["x0"], BIN["x1"], BIN["y0"], BIN["y1"], BIN["z0"], BIN["z1"])
    t = BIN["t"]
    b = b.cut(box(BIN["x0"] + t, BIN["x1"] - t, BIN["y0"] + t, BIN["y1"] - t, BIN["z0"] + t, BIN["z1"] - t))
    b = b.cut(box(REJ["x"] - BIN["slot_w"] / 2, REJ["x"] + BIN["slot_w"] / 2, BIN["y0"] - 1, BIN["y0"] + t + 1, Z_BELT - 5, Z_BELT - 5 + BIN["slot_h"]))
    b = b.union(box(BIN["x0"] - 20, BIN["x1"] + 20, BIN["y0"] - 2, BIN["y1"] + 20, BIN["z1"], BIN["z1"] + 2))     # lid
    for x in BIN_HOOKS:
        b = b.union(box(x - 15, x + 15, YO, BIN["y0"], Z_SIDE1 - 40, Z_SIDE1 - 36))                         # hooks onto the plate top edge
    return b


def p304_sensorbkts():
    b = box(B1_X - 15, B1_X + 15, -YO - 3, -YO, Z_SIDE1 - 30, Z_BELT + 60)                    # B1 eye on the -y plate
    b = b.union(box(B1_X - 15, B1_X + 15, YO, YO + 3, Z_SIDE1 - 30, Z_BELT + 60))             # its reflector on the +y plate
    return b


# ------------------------------------------------------------------ 400 drive + controls
def p401_torquearm():
    y = -(YO + PUL["brg_t"] + 60.0)
    return box(PUL["x"] - 15, PUL["x"] + 5, y - 3, y + 3, LEG["z_foot"] + 500, Z_PUL - 60).union(
        box(LEG["x"] - 20, PUL["x"] + 5, y - 3, y + 3, LEG["z_foot"] + 500, LEG["z_foot"] + 530))


def p402_boxbkt():
    x = -LEG["x"]
    return box(ENC["x0"] + 20, ENC["x1"] - 20, -LEG["y"] - 20 - 3, -LEG["y"] - 20, ENC["z0"] + 20, ENC["z0"] + ENC["h"] - 20).union(
        box(x - 20, x + 20, ENC["y1"], -LEG["y"] - 20, ENC["z0"] + 40, ENC["z0"] + 60))


def p403_pole():
    L = POLE["h"] + (Z_BELT - Z_SIDE0) + 120
    p = cyl(12.7, Z_SIDE0 - 120, L, POLE["x"], POLE["y"]).cut(cyl(11.0, Z_SIDE0 - 121, L + 2, POLE["x"], POLE["y"]))
    return p.union(box(POLE["x"] - 20, POLE["x"] + 20, LEG["y"] + LEG["sq"] / 2, POLE["y"] - 12.7, Z_SIDE0 - 120, Z_SIDE0 - 100)).union(
        box(POLE["x"] - 20, POLE["x"] + 20, LEG["y"] + LEG["sq"] / 2, POLE["y"] - 12.7, Z_SIDE0 + 100, Z_SIDE0 + 120))


def bought():
    h = HEAD
    head = box(-h["L"] / 2, h["L"] / 2, -h["W"] / 2, h["W"] / 2, h["z0"], h["z0"] + h["H"]).cut(
        box(-h["L"] / 2 - 1, h["L"] / 2 + 1, -h["ap_w"] / 2, h["ap_w"] / 2, h["ap_z0"], h["ap_z0"] + h["ap_h"]))
    for sy in (-1, 1):
        head = head.union(box(-40, 40, sy * h["lug_y"] - 30, sy * h["lug_y"] + 30, h["lug_z"], h["lug_z"] + 10))
    ctrl = box(-120, 120, -h["W"] / 2 - 20, -h["W"] / 2, h["z0"] + 240, h["z0"] + 420)                # control panel on the -y face
    belt = box(-PUL["x"], PUL["x"], -BELT["w"] / 2, BELT["w"] / 2, Z_BELT - BELT["t"], Z_BELT)
    for sx in (-1, 1):
        belt = belt.union(ycyl(PUL["d"] / 2 + BELT["t"], -BELT["w"] / 2, BELT["w"] / 2, sx * PUL["x"], Z_PUL).cut(ycyl(PUL["d"] / 2, -BELT["w"] / 2 - 1, BELT["w"] / 2 + 1, sx * PUL["x"], Z_PUL)))
    belt = belt.union(box(-PUL["x"], PUL["x"], -BELT["w"] / 2, BELT["w"] / 2, Z_PUL - PUL["d"] / 2 - BELT["t"], Z_PUL - PUL["d"] / 2))
    brg = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            yb0, yb1 = sorted((sy * YO, sy * (YO + PUL["brg_t"])))
            b = box(sx * PUL["x"] - PUL["brg_sq"] / 2, sx * PUL["x"] + PUL["brg_sq"] / 2, yb0, yb1, Z_PUL - PUL["brg_sq"] / 2, Z_PUL + PUL["brg_sq"] / 2)
            brg = b if brg is None else brg.union(b)
    yg = -(YO + PUL["brg_t"] + 8.0)
    gm = box(PUL["x"] - 55, PUL["x"] + 55, yg - 85, yg, Z_PUL - 55, Z_PUL + 55)                       # right-angle gearbox, hollow bore on the shaft
    gm = gm.union(cyl(42.0, Z_PUL - 55 - 200, 200, PUL["x"], yg - 42))                                 # motor hanging down
    push = ycyl(18.0, -YO - 255.0, -GUIDE["gap"]["J"] / 2 - 38.0, REJ["x"], REJ["z"])                 # actuator body + rod, retracted
    ctl = box(ENC["x0"], ENC["x1"], ENC["y0"], ENC["y1"], ENC["z0"], ENC["z0"] + ENC["h"])
    for dz, r in ((200.0, 20.0), (150.0, 11.0), (110.0, 11.0), (70.0, 11.0)):
        ctl = ctl.union(ycyl(r, ENC["y0"] - 25, ENC["y0"], (ENC["x0"] + ENC["x1"]) / 2, ENC["z0"] + dz))
    eyes = box(B1_X - 20, B1_X + 20, -YO - 50, -YO - 3, Z_BELT + 25, Z_BELT + 60)
    beacon = cyl(30.0, Z_BELT + POLE["h"], 220.0, POLE["x"], POLE["y"])
    feet = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            f = cyl(40.0, 0, 12, sx * LEG["x"], sy * LEG["y"]).union(cyl(8.0, 12, LEG["z_foot"] - 20, sx * LEG["x"], sy * LEG["y"]))
            feet = f if feet is None else feet.union(f)
    jar = cyl(JAR["d"] / 2, Z_BELT, JAR["h"], 0, 0)
    return {"P1-418": head.union(ctrl), "P1-419": belt.union(brg), "P1-420": gm, "P1-421": push, "P1-459": ctl, "P1-460": eyes, "P1-461": beacon, "P1-462": feet, "JAR": jar}


PARTS = {}


def build():
    PARTS.update({"P1-406-101": p101_infeed(), "P1-406-102": p102_outfeed(), "P1-406-103": p103_spine(), "P1-406-104": p104_headstand(),
                  "P1-406-201": p201_drive(), "P1-406-202": p202_tail(), "P1-406-203": p203_takeup(), "P1-406-204": p204_frp(), "P1-406-205": p205_clips(),
                  "P1-406-206": p206_bed(), "P1-406-207": p207_guides(), "P1-406-208": p208_guidebkts(),
                  "P1-406-301": p301_pushbkt(), "P1-406-302": p302_paddle(), "P1-406-303": p303_bin(), "P1-406-304": p304_sensorbkts(),
                  "P1-406-401": p401_torquearm(), "P1-406-402": p402_boxbkt(), "P1-406-403": p403_pole()})
    return PARTS


GROUP = {"P1-406-100": ["P1-406-101", "P1-406-102", "P1-406-103", "P1-406-104"],
         "P1-406-200": ["P1-406-201", "P1-406-202", "P1-406-203", "P1-406-204", "P1-406-205", "P1-406-206", "P1-406-207", "P1-406-208"],
         "P1-406-300": ["P1-406-301", "P1-406-302", "P1-406-303", "P1-406-304"],
         "P1-406-400": ["P1-406-401", "P1-406-402", "P1-406-403"]}
UHMW_PARTS = ("P1-406-206", "P1-406-207", "P1-406-302")
DENS = {p: RHO_UHMW for p in UHMW_PARTS}
DENS["P1-406-204"] = RHO_FRP

if __name__ == "__main__":
    P = build()
    masses = {}
    asm = cq.Assembly(name="P1-406")
    col_ss, col_b, col_u, col_f = cq.Color(0.78, 0.80, 0.83), cq.Color(0.20, 0.32, 0.55), cq.Color(0.96, 0.96, 0.94), cq.Color(0.85, 0.75, 0.35)
    for g, ids in GROUP.items():
        sub = cq.Assembly(name=g)
        for pid in ids:
            s = P[pid]
            masses[pid] = round(s.val().Volume() * DENS.get(pid, RHO), 3)
            cq.exporters.export(s, str(OUT / f"{pid}.step"))
            sub.add(s, name=pid, color=col_u if pid in UHMW_PARTS else (col_f if pid == "P1-406-204" else col_ss))
        asm.add(sub, name=g)
    cols = {"P1-418": cq.Color(0.85, 0.85, 0.80), "P1-419": cq.Color(0.95, 0.95, 0.95), "P1-420": cq.Color(0.25, 0.35, 0.55), "P1-421": cq.Color(0.15, 0.15, 0.15),
            "P1-459": cq.Color(0.55, 0.57, 0.6), "P1-460": cq.Color(0.9, 0.75, 0.1), "P1-461": cq.Color(0.9, 0.2, 0.2), "P1-462": cq.Color(0.1, 0.1, 0.1),
            "JAR": cq.Color(0.75, 0.88, 0.95)}
    for k, s in bought().items():
        asm.add(s, name=k, color=cols.get(k, col_b))
    asm.save(str(OUT / "P1-406-ASM.step"))
    asm.save(str(OUT / "P1-406-ASM.glb"), exportType="GLTF", tolerance=0.2, angularTolerance=0.15)
    (OUT / "masses.json").write_text(json.dumps(masses, indent=1))
    print(masses, round(sum(masses.values()), 2), "kg made parts")
