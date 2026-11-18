"""P1-412 rev B 3D model from design.py: STEP per made part, machine assembly STEP/GLB, masses.json.
Modelled with the carriage up (shelf underside z 350) and the lever raised."""
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
RHO_PC = 1.2e-6
ZS = Z_SHELF_UP                       # shelf underside as modelled


def W(pl="XY"):
    return cq.Workplane(pl)


def box(x0, x1, y0, y1, z0, z1):
    return W().box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(r, z0, h, x=0.0, y=0.0):
    return W().circle(r).extrude(h).translate((x, y, z0))


def rod(p1, p2, d):
    v = cq.Vector(*p2) - cq.Vector(*p1)
    return cq.Workplane(cq.Plane(origin=p1, xDir=v.cross(cq.Vector(0, 0, 1)) if abs(v.normalized().z) < 0.99 else (1, 0, 0), normal=v)).circle(d / 2).extrude(v.Length)


def holes_z(s, pts, d, z0=-1.0, h=200.0):
    for x, y in pts:
        s = s.cut(cyl(d / 2, z0, h, x, y))
    return s


# ------------------------------------------------------------------ 100 base weldment
BASE_HOLES = [(sx * BASE["hx"], sy * BASE["hy"]) for sx in (-1, 1) for sy in (-1, 1)]
VB_HOLES = {k: [(vb_face(CONT[c]["d"]) + VB_BOLT_DX, sy * 35.0) for sy in (-1, 1)] for k, c in (("S", "shaker-250"), ("J", "jar-12"))}
TGL_HOLES = [(-180.0, -15.0), (-180.0, 15.0), (-140.0, -15.0), (-140.0, 15.0)]     # clamp bracket 404, 4 x M6 tapped
ENC = dict(x0=-198.0, x1=-78.0, y0=-172.0, y1=-82.0, h=200.0)                   # PC box 200 x 120 x 90 standing on its end, lid (operators) facing the operator (-y)
ENC_OPS = dict(estop=(-138.0, 170.0), sel=(-163.0, 110.0), lamp=(-113.0, 110.0), pot=(-138.0, 55.0))   # (x, z above the base top) on the lid
ENC_HOLES = [(-163.0, -127.0), (-113.0, -127.0)]                                  # 2 x M6 up through the bottom end wall (bonded sealing washers)
GAS_BKT = dict(x=GAS["x"], y=GAS["y"])
GAS_HOLES = [(GAS["x"] - 20.0, GAS["y"]), (GAS["x"] + 20.0, GAS["y"])]


def p101_base():
    b = box(-BASE["w"] / 2, BASE["w"] / 2, BASE["y0"], BASE["y0"] + BASE["d"], 0, BASE["t"])
    b = b.edges("|Z").fillet(10.0)
    b = holes_z(b, BASE_HOLES, BASE["hole"])
    b = holes_z(b, VB_HOLES["S"] + VB_HOLES["J"] + GAS_HOLES, 6.8)        # M8 tapped
    b = holes_z(b, TGL_HOLES + ENC_HOLES, 5.0)                              # M6 tapped
    b = holes_z(b, [(STOP["x"], STOP["y"])], 14.5)                          # M16 x 1.5 tapped
    return b


def p102_column():
    a, t = COL["a"], COL["t"]
    o = box(-a / 2, a / 2, COL["y"] - a / 2, COL["y"] + a / 2, Z_COL0, Z_COL1)
    i = box(-a / 2 + t, a / 2 - t, COL["y"] - a / 2 + t, COL["y"] + a / 2 - t, Z_COL0 - 1, Z_COL1 + 1)
    return o.cut(i)


def p103_gussets():
    out = None
    for sx in (-1, 1):
        x0 = sx * COL["a"] / 2
        pts = [(x0, Z_COL0), (x0 + sx * GUS["a"], Z_COL0), (x0, Z_COL0 + GUS["a"])]
        g = W("XZ").polyline(pts).close().extrude(GUS["t"] / 2, both=True).translate((0, COL["y"], 0))
        out = g if out is None else out.union(g)
    return out


def p104_cap():
    c = box(CAPPL["x0"], CAPPL["x1"], CAPPL["y0"], CAPPL["y1"], Z_COL1, Z_CAP)
    return c


def p105_clevis():
    c = box(CLEV["x"], CLEV["x"] + CLEV["t"], CLEV["y0"], CLEV["y1"], Z_CAP, Z_CAP + CLEV["h"])
    c = c.edges("|X and >Z").fillet(20.0)
    return c.cut(rod((CLEV["x"] - 1, PIV["y"], PIV["z"]), (CLEV["x"] + CLEV["t"] + 1, PIV["y"], PIV["z"]), 10.2))


def p106_railbar():
    b = box(-RSB["w"] / 2, RSB["w"] / 2, Y_RSB, Y_COLF, RSB["z0"], RSB["z0"] + RSB["L"])
    for k in range(int(RAIL["L"] // RAIL["pitch"])):
        z = RAIL["z0"] + RAIL["e"] + k * RAIL["pitch"]
        b = b.cut(rod((0, Y_RSB - 1, z), (0, Y_RSB + 8, z), 2.5))           # M3 x 8 deep tapped
    return b


# ------------------------------------------------------------------ 200 carriage weldment
Z_BLK = ZS + CAR["sh_t"] + CAR["h"] / 2          # block centre with the carriage up
MOT_HOLES = [(GM["pcd"] / 2 * math.cos(math.radians(45 + 90 * k)), GM["pcd"] / 2 * math.sin(math.radians(45 + 90 * k))) for k in range(4)]
GRD_HOLES = [(GUARD["r_bolt"] * math.cos(math.radians(a)), GUARD["r_bolt"] * math.sin(math.radians(a))) for a in (-90.0, 30.0, 150.0)]


def p201_vplate():
    p = box(-CAR["w"] / 2, CAR["w"] / 2, Y_BLK - CAR["t"], Y_BLK, ZS + CAR["sh_t"], ZS + CAR["sh_t"] + CAR["h"])
    for dx in (-BLK["B"] / 2, BLK["B"] / 2):
        for dz in (-BLK["C"] / 2, BLK["C"] / 2):
            p = p.cut(rod((dx, Y_BLK - CAR["t"] - 1, Z_BLK + dz), (dx, Y_BLK + 1, Z_BLK + dz), 3.4))
    return p


def p202_shelf():
    s = box(CAR["sh_x0"], CAR["sh_x1"], SHELF_Y0, Y_BLK, ZS, ZS + CAR["sh_t"])
    s = s.edges("|Z and <Y").fillet(15.0)
    s = holes_z(s, [(0.0, 0.0)], MOTOR_BORE + 0.1, ZS - 1, 20)
    s = holes_z(s, MOT_HOLES, 5.0, ZS - 1, 20)
    s = holes_z(s, GRD_HOLES, 4.2, ZS - 1, 20)                                  # M5 tapped
    s = holes_z(s, [(GAS["x"], GAS["y"])], 6.8, ZS - 1, 20)                     # M8 tapped (gas spring ball stud)
    return s


def p203_gussets():
    out = None
    for x in (-50.0, 50.0):
        pts = [(Y_BLK - CAR["t"], ZS + CAR["sh_t"]), (Y_BLK - CAR["t"] - CAR["gus"], ZS + CAR["sh_t"]), (Y_BLK - CAR["t"], ZS + CAR["sh_t"] + CAR["gus"])]
        g = W("YZ").polyline(pts).close().extrude(3.0, both=True).translate((x, 0, 0))
        out = g if out is None else out.union(g)
    return out


def p204_lug():
    lx = CAR["lug_x"]
    l = box(lx - 5, lx + 5, CAR["lug_y"] - 15, CAR["lug_y"] + 15, ZS + CAR["sh_t"], ZS + Z_LUGPIN + 15)
    return l.cut(rod((lx - 6, CAR["lug_y"], ZS + Z_LUGPIN), (lx + 6, CAR["lug_y"], ZS + Z_LUGPIN), 8.2))


# ------------------------------------------------------------------ 300 spindle parts
Z_CLU0 = ZS - CLU["L"]
Z_STUB_C = Z_CLU0 - STUB["collar_t"]
Z_CHK_F = ZS - STACK                              # chuck face


def p301_stub():
    s = cyl(STUB["d"] / 2, Z_STUB_C + STUB["collar_t"], 30.0)                      # into the clutch output hub
    s = s.union(cyl(STUB["collar_d"] / 2, Z_STUB_C, STUB["collar_t"]))
    s = s.union(cyl(STUB["spig_d"] / 2, Z_STUB_C - STUB["spig_L"], STUB["spig_L"]))
    return s


def p302_chuck():
    c = cyl(CHK["d"] / 2, Z_CHK_F, CHK["h"])
    c = c.cut(cyl(INSERT["J"]["id_bot"] / 2 + 4, Z_CHK_F - 1, INSERT["J"]["depth"] + 5))   # insert pocket Ø100 x 20
    return c.cut(cyl(STUB["spig_d"] / 2 + 0.1, Z_CHK_F + CHK["h"] - STUB["spig_L"] + CHK["float_"], 60))


def p303_guard():
    g = cyl(GUARD["d"] / 2, ZS - GUARD["h"], GUARD["h"] - 10).cut(cyl(GUARD["d"] / 2 - GUARD["t"], ZS - GUARD["h"] - 1, GUARD["h"]))
    ring = cyl(GUARD["r_bolt"] + 10, ZS - 16, 6).cut(cyl(GUARD["d"] / 2 - GUARD["t"], ZS - 17, 8))
    return holes_z(g.union(ring), GRD_HOLES, 5.5, ZS - 20, 10)


def p304_standoffs():
    out = None
    for x, y in GRD_HOLES:
        s = cyl(5.0, ZS - 10, 10, x, y).cut(cyl(2.75, ZS - 11, 12, x, y))
        out = s if out is None else out.union(s)
    return out


# ------------------------------------------------------------------ 400 nest and clamp
def p401_nest():
    n = box(-95.0, 110.0, -70.0, 70.0, BASE["t"], Z_STAND)
    n = n.edges("|Z").fillet(8.0)
    for k in ("S", "J"):
        for x, y in VB_HOLES[k]:
            n = n.cut(cyl(5.0, BASE["t"] - 1, 20, x, y))
    return n


def vblock(k):
    xf = vb_face(CONT["shaker-250" if k == "S" else "jar-12"]["d"])
    b = box(xf, xf + VB["t"], -VB["L"] / 2, VB["L"] / 2, Z_STAND, Z_STAND + VB["h"])
    v = W().polyline([(xf - 1, -VB["depth"] - 1), (xf + VB["depth"], 0), (xf - 1, VB["depth"] + 1)]).close().extrude(VB["h"] + 2).translate((0, 0, Z_STAND - 1))
    b = b.cut(v)
    for x, y in VB_HOLES[k]:
        b = b.cut(cyl(4.5, Z_STAND - 1, VB["h"] + 2, x, y)).cut(cyl(7.5, Z_STAND + VB["h"] - 9, 10, x, y))
    return b


def p402_vblock():
    return vblock("J")


def p403_pad():
    xp = -CONT["jar-12"]["d"] / 2                 # pad face touching the jar
    p = box(xp - PAD["t"], xp, -PAD["w"] / 2, PAD["w"] / 2, Z_STAND + 20, Z_STAND + 20 + PAD["h"])
    return p.cut(W().polyline([(xp + 1, -16.0), (xp - 8, 0.0), (xp + 1, 16.0)]).close().extrude(PAD["h"] + 2).translate((0, 0, Z_STAND + 19)))


def p404_bracket():
    b = box(-195.0, -125.0, -30.0, 30.0, BASE["t"], BASE["t"] + 6)
    b = b.union(box(-131.0, -125.0, -30.0, 30.0, BASE["t"], BASE["t"] + 70))
    return holes_z(b, TGL_HOLES, 6.6, BASE["t"] - 1, 10)


# ------------------------------------------------------------------ 500 lever, link, stop, gas spring bracket
def lever_pts(up=True):
    th = math.radians(TH0 if up else -TH0)
    pin = (PIV["x"], PIV["y"] - LEV["a"] * math.cos(th), PIV["z"] + LEV["a"] * math.sin(th))
    end = (PIV["x"], PIV["y"] - LEV["L"] * math.cos(th), PIV["z"] + LEV["L"] * math.sin(th))
    return pin, end


def p501_lever():
    pin, end = lever_pts()
    th = math.radians(TH0)
    L = LEV["L"] + 25.0
    bar = box(-LEV["t"] / 2, LEV["t"] / 2, -L + 25.0, 25.0, -LEV["w"] / 2, LEV["w"] / 2)
    bar = bar.cut(rod((-6, 0, 0), (6, 0, 0), 10.2)).cut(rod((-6, -LEV["a"], 0), (-6 + 12, -LEV["a"], 0), 8.2))
    bar = bar.cut(rod((-6, -LEV["L"], 0), (6, -LEV["L"], 0), 8.5))              # M10 knob tapped Ø8.5
    bar = bar.rotate((0, 0, 0), (1, 0, 0), -math.degrees(th))
    return bar.translate((PIV["x"], PIV["y"], PIV["z"]))


def p502_link():
    pin, _ = lever_pts()
    lug = (CAR["lug_x"], CAR["lug_y"], ZS + Z_LUGPIN)
    return rod(lug, pin, LINK["d"])


def p503_stoprod():
    return cyl(STOP["d"] / 2, 0.0, z_shelf_down("shaker-250"), STOP["x"], STOP["y"])


def p504_flip():
    z = z_shelf_down("shaker-250")
    b = box(STOP["x"] + 10, STOP["x"] + 40, STOP["y"] - 12, STOP["y"] + 12, z - STOP["flip_t"] + 10, z + 10)
    return b


def p505_gasbkt():
    b = box(GAS["x"] - 30, GAS["x"] + 30, GAS["y"] - 12, GAS["y"] + 12, BASE["t"], BASE["t"] + 4)
    b = b.union(cyl(8.0, BASE["t"] + 4, GAS["z_lo"] - BASE["t"] - 4, GAS["x"], GAS["y"]))
    return holes_z(b, GAS_HOLES, 9.0, BASE["t"] - 1, 10)


# ------------------------------------------------------------------ bought (simplified envelopes)
def bought():
    gm = cyl(GM["body_d"] / 2, ZS + CAR["sh_t"], 40).union(cyl(36.0, ZS + CAR["sh_t"] + 40, GM["body_h"] - 40)).union(
        box(-25, 25, -60, -36, ZS + CAR["sh_t"] + 120, ZS + CAR["sh_t"] + 180))                             # terminal box at the front
    clu = cyl(CLU["d"] / 2, Z_CLU0, CLU["L"])
    ins = cyl(INSERT["J"]["id_bot"] / 2 + 4, Z_CHK_F, INSERT["J"]["depth"] + 4).cut(cyl(INSERT["J"]["id_bot"] / 2, Z_CHK_F - 1, INSERT["J"]["depth"] + 1))
    rail = box(-RAIL["w"] / 2, RAIL["w"] / 2, Y_RSB - RAIL["h"], Y_RSB, RAIL["z0"], RAIL["z0"] + RAIL["L"])
    blk = box(-BLK["W"] / 2, BLK["W"] / 2, Y_BLK, Y_RSB - 4, Z_BLK - BLK["L"] / 2, Z_BLK + BLK["L"] / 2)
    gas = rod((GAS["x"], GAS["y"], GAS["z_lo"]), (GAS["x"], GAS["y"], GAS["z_lo"] + 190), 22).union(
        rod((GAS["x"], GAS["y"], GAS["z_lo"] + 190), (GAS["x"], GAS["y"], ZS), 10))
    xp = -CONT["jar-12"]["d"] / 2 - PAD["t"]
    tgl = box(-195.0, -137.0, -12.0, 12.0, BASE["t"] + 30, BASE["t"] + 66).union(rod((-137.0, 0, BASE["t"] + 48), (xp, 0, BASE["t"] + 48), 10)).union(
        rod((-170.0, 0, BASE["t"] + 66), (-215.0, 0, BASE["t"] + 140), 14))
    enc = box(ENC["x0"], ENC["x1"], ENC["y0"], ENC["y1"], BASE["t"], BASE["t"] + ENC["h"])
    yl = ENC["y0"]
    ex, ez = ENC_OPS["estop"]; estop = rod((ex, yl, BASE["t"] + ez), (ex, yl - 32, BASE["t"] + ez), 40)
    sw = None
    for k in ("sel", "lamp", "pot"):
        x, z = ENC_OPS[k]; c = rod((x, yl, BASE["t"] + z), (x, yl - 20, BASE["t"] + z), 22 if k != "pot" else 16)
        sw = c if sw is None else sw.union(c)
    _, end = lever_pts()
    knob = rod(end, (end[0] + 45, end[1], end[2]), 32)
    lim = box(-20.0, -6.0, Y_BLK - 40, Y_BLK - 10, ZS + CAR["sh_t"] + CAR["h"] + 6, ZS + CAR["sh_t"] + CAR["h"] + 46)
    return {"P1-422": gm, "P1-423": clu.union(ins), "P1-424": rail.union(blk).union(gas), "P1-450": tgl, "P1-451": enc.union(estop).union(sw),
            "P1-452": lim, "P1-453": knob}


PARTS = {}


def build():
    PARTS.update({"P1-412-101": p101_base(), "P1-412-102": p102_column(), "P1-412-103": p103_gussets(), "P1-412-104": p104_cap(),
                  "P1-412-105": p105_clevis(), "P1-412-106": p106_railbar(),
                  "P1-412-201": p201_vplate(), "P1-412-202": p202_shelf(), "P1-412-203": p203_gussets(), "P1-412-204": p204_lug(),
                  "P1-412-301": p301_stub(), "P1-412-302": p302_chuck(), "P1-412-303": p303_guard(), "P1-412-304": p304_standoffs(),
                  "P1-412-401": p401_nest(), "P1-412-402": p402_vblock(), "P1-412-403": p403_pad(), "P1-412-404": p404_bracket(),
                  "P1-412-501": p501_lever(), "P1-412-502": p502_link(), "P1-412-503": p503_stoprod(), "P1-412-504": p504_flip(),
                  "P1-412-505": p505_gasbkt()})
    return PARTS


GROUP = {"P1-412-100": ["P1-412-101", "P1-412-102", "P1-412-103", "P1-412-104", "P1-412-105", "P1-412-106"],
         "P1-412-200": ["P1-412-201", "P1-412-202", "P1-412-203", "P1-412-204"],
         "P1-412-300": ["P1-412-301", "P1-412-302", "P1-412-303", "P1-412-304"],
         "P1-412-400": ["P1-412-401", "P1-412-402", "P1-412-403", "P1-412-404"],
         "P1-412-500": ["P1-412-501", "P1-412-502", "P1-412-503", "P1-412-504", "P1-412-505"]}
DENS = {"P1-412-303": RHO_PC, "P1-412-401": RHO_UHMW, "P1-412-402": RHO_UHMW, "P1-412-403": RHO_UHMW}
NONMET = {"P1-412-303": cq.Color(0.85, 0.92, 0.97), "P1-412-401": cq.Color(0.96, 0.96, 0.94), "P1-412-402": cq.Color(0.96, 0.96, 0.94),
          "P1-412-403": cq.Color(0.96, 0.96, 0.94)}

if __name__ == "__main__":
    P = build()
    masses = {}
    asm = cq.Assembly(name="P1-412")
    col_ss, col_b = cq.Color(0.78, 0.80, 0.83), cq.Color(0.20, 0.32, 0.55)
    for g, ids in GROUP.items():
        sub = cq.Assembly(name=g)
        for pid in ids:
            s = P[pid]
            masses[pid] = round(s.val().Volume() * DENS.get(pid, RHO), 3)
            cq.exporters.export(s, str(OUT / f"{pid}.step"))
            sub.add(s, name=pid, color=NONMET.get(pid, col_ss))
        asm.add(sub, name=g)
    cols = {"P1-450": cq.Color(0.1, 0.1, 0.1), "P1-451": cq.Color(0.55, 0.57, 0.6), "P1-452": cq.Color(0.9, 0.75, 0.1), "P1-453": cq.Color(0.1, 0.1, 0.1)}
    for k, s in bought().items():
        asm.add(s, name=k, color=cols.get(k, col_b))
    asm.save(str(OUT / "P1-412-ASM.step"))
    asm.save(str(OUT / "P1-412-ASM.glb"), exportType="GLTF", tolerance=0.2, angularTolerance=0.15)
    (OUT / "masses.json").write_text(json.dumps(masses, indent=1))
    car = sum(v for k, v in masses.items() if k[:9] in ("P1-412-20", "P1-412-30"))
    print(masses, round(sum(masses.values()), 2), "kg made parts; carriage + spindle", round(car, 2))
