"""P1-301 rev B 3D model from design.py: one STEP per made part, the machine assembly STEP/GLB, masses (kg) to masses.json."""
import json
import math
import pathlib
import sys

import cadquery as cq
from cadquery import Vector

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from design import *  # noqa: F401,F403
import design as D

HERE = pathlib.Path(__file__).parent
OUT = HERE / "cad"
RHO = 8.0e-6                                   # kg/mm3 stainless


def W(pl="XY"):
    return cq.Workplane(pl)


def cyl_x(r, x0, x1, y=0.0, z=Z_AX):
    return W("YZ").workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)


def tube_x(ro, ri, x0, x1, y=0.0, z=Z_AX):
    return cyl_x(ro, x0, x1, y, z).cut(cyl_x(ri, x0 - 1, x1 + 1, y, z))


def rod(p1, p2, d):
    a, b = Vector(*p1), Vector(*p2)
    return cq.Workplane(obj=cq.Solid.makeCylinder(d / 2, (b - a).Length, a, (b - a).normalized()))


def ushape(r, half_w, top, x0, x1):
    """solid U section (y-z) extruded along x: semicircle radius r about the axis + rectangle up to z = Z_AX + top."""
    s = W("YZ").workplane(offset=x0).center(0, Z_AX).circle(r).extrude(x1 - x0)
    return s.union(W("YZ").workplane(offset=x0).center(0, Z_AX + top / 2).rect(2 * half_w, top).extrude(x1 - x0)).cut(
        W("YZ").workplane(offset=x0 - 1).center(0, Z_AX - r / 2 - 1).rect(2 * r + 4, r + 2).extrude(x1 - x0 + 2)) if False else \
        W("YZ").workplane(offset=x0).center(0, Z_AX).circle(r).extrude(x1 - x0).union(
            W("YZ").workplane(offset=x0).center(0, Z_AX + top / 2).rect(2 * half_w, top).extrude(x1 - x0))


# ------------------------------------------------------------------ 100 trough weldment
def p101_shell():
    s = ushape(R_IN + T_SH, R_IN + T_SH, H_SIDE, -L_IN / 2, L_IN / 2).cut(ushape(R_IN, R_IN, H_SIDE + 2, -L_IN / 2 - 1, L_IN / 2 + 1))
    s = s.cut(W().center(0, 0).circle(102.0 / 2).extrude(50).translate((0, 0, Z_TB - 20)))
    s = s.cut(W("XZ").workplane(offset=R_IN + 10).center(-300, Z_AX + 200).circle(38.6 / 2).extrude(-30))   # 1.5 in probe port (front, y-)
    return s


def p102_endplate(sx):
    r = R_IN + T_SH + EP_OFF if sx > 0 else RING["r_out"]
    x0 = L_IN / 2 if sx > 0 else -L_IN / 2 - T_EP
    p = ushape(r, r, H_SIDE, x0, x0 + T_EP)
    p = p.cut(cyl_x(BOX["spig_d"] / 2 + 0.1, x0 - 1, x0 + T_EP + 1))
    if sx < 0:
        for y, z in D.ring_bolts():
            p = p.cut(cyl_x(RING["hole"] / 2, x0 - 1, x0 + T_EP + 1, y, Z_AX + z))
    return p


def p108_ring():
    x0 = -L_IN / 2
    g = ushape(RING["r_out"], RING["r_out"], H_SIDE, x0, x0 + RING["t"]).cut(ushape(R_IN + T_SH, R_IN + T_SH, H_SIDE + 2, x0 - 1, x0 + RING["t"] + 1))
    for y, z in D.ring_bolts():
        g = g.cut(cyl_x(RING["hole"] / 2, x0 - 1, x0 + RING["t"] + 1, y, Z_AX + z))
    return g


def p103_flange():
    f = W().rect(FL_OUT_X, FL_OUT_Y).rect(L_IN, W_IN).extrude(T_FL).translate((0, 0, Z_AX + H_SIDE))
    for x in (-300.0, 300.0):                                   # hinge knuckle positions are welded; latch keepers drilled on assembly
        pass
    return f


def p104_box(sx):
    xin = L_IN / 2 if sx > 0 else -L_IN / 2
    def seg(r, a, b):
        return cyl_x(r, xin + sx * a if sx > 0 else xin + sx * b, xin + sx * b if sx > 0 else xin + sx * a)
    b = seg(BOX["spig_d"] / 2, 0, T_EP).union(seg(BOX["od"] / 2, T_EP, BOX["x_face"]))
    b = b.cut(seg(BOX["throat"] / 2, -1, BOX["x_face"] + 1)).cut(seg(BOX["bore"] / 2, 10, BOX["x_face"] + 1))
    xf = xin + sx * BOX["x_face"]
    for k in range(4):
        a = math.radians(45 + 90 * k)
        y, z = BOX["pcd"] / 2 * math.cos(a), Z_AX + BOX["pcd"] / 2 * math.sin(a)
        b = b.cut(cyl_x(4.25, xf - (BOX["stud_depth"] if sx > 0 else 0), xf + (0 if sx > 0 else BOX["stud_depth"]), y, z))
    return b


def p105_lug(x, sy):
    y0 = R_IN + T_SH
    seat = W().box(LUG["w"], 147, LUG["t"]).translate((x, sy * (y0 + 147 / 2), Z_RAIL + LUG["t"] / 2))
    seat = seat.cut(W().circle(7).extrude(20).translate((x, sy * Y_LEG, Z_RAIL - 5)))
    g = (W("YZ").workplane(offset=x - 5).polyline([(sy * y0, Z_RAIL), (sy * 355, Z_RAIL), (sy * 355, Z_RAIL - 20), (sy * y0, Z_RAIL - 100)]).close().extrude(10))
    return seat.union(g)


def ferrule(od_tube, fl_od, L, base, axis):
    """BPE short weld ferrule envelope: tube stub + clamp flange at the free end. axis: unit (dx,dy,dz) pointing out."""
    ax = Vector(*axis); b = Vector(*base)
    t = cq.Solid.makeCylinder(od_tube / 2, L, b, ax).cut(cq.Solid.makeCylinder(od_tube / 2 - 1.65, L, b, ax))
    f = cq.Solid.makeCylinder(fl_od / 2, 4.0, b + ax * (L - 4), ax).cut(cq.Solid.makeCylinder(od_tube / 2 - 1.65, 4.0, b + ax * (L - 4), ax))
    return cq.Workplane(obj=t.fuse(f))


def trough():
    parts = {"P1-301-101": p101_shell(), "P1-301-102": p102_endplate(1), "P1-301-110": p102_endplate(-1), "P1-301-103": p103_flange(),
             "P1-301-104": p104_box(1).union(p104_box(-1)), "P1-301-108": p108_ring()}
    lug = None
    for x in LUG["x"]:
        for sy in (-1, 1):
            q = p105_lug(x, sy); lug = q if lug is None else lug.union(q)
    parts["P1-301-105"] = lug
    parts["P1-301-106"] = ferrule(TC4_OD, TC4_FER_OD, TC4_FER_L, (0, 0, Z_TB + 1.5), (0, 0, -1))
    parts["P1-301-107"] = ferrule(TC15_OD, 50.5, 21.5, (-300, -(R_IN + 1.5), Z_AX + 200), (0, -1, 0))
    return parts


# ------------------------------------------------------------------ 200 agitator
def p201_shaft():
    s = cyl_x(D_SH / 2, X_FREE_END, X_SHOULDER).union(cyl_x(D_DRV / 2, X_SHOULDER, X_DRV_END))
    s = s.cut(W().box(KEY["L"], KEY["b"], 20).translate((KEY["x0"] + KEY["L"] / 2, 0, Z_AX + D_DRV / 2 - KEY["t1"] + 10)))
    return s


def ribbon(n):
    r = RIB[n]
    rm = r["od"] / 2 - r["w"] / 2
    L = r["x1"] - r["x0"]
    helix = cq.Wire.makeHelix(r["p"], L, rm, lefthand=(r["hand"] == "LH"))
    prof = cq.Workplane("XZ", origin=(rm, 0, 0)).rect(r["w"], r["t"])
    s = prof.sweep(cq.Workplane(obj=helix), isFrenet=True)
    # helix starts at angle 0 on +X of its own frame at z=0; map: helix z -> machine x, start angle -> theta(x0)
    th0 = D.theta(n, r["x0"])
    # in its own frame the start point is (rm, 0, 0); after rotate about Y by 90 the helix axis is +x and the start point is at -z.
    # angle from top dead centre CCW viewed from +x == right-hand about +x
    s = s.rotate((0, 0, 0), (0, 1, 0), 90)            # helix axis z -> x; start point (rm,0,0) -> (0,0,-rm) = bottom (180 deg)
    lh = r["hand"] == "LH"
    s = s.rotate((0, 0, 0), (1, 0, 0), th0 - 180)     # rotate so the start sits at theta(x0)
    # handedness check is done on the drawings; cadquery helix turns CCW about +z (RH) unless lefthand, consistent with design.theta
    return s.translate((r["x0"], 0, Z_AX)), lh


def p_arm(a):
    ang = math.radians(a["ang"])
    dy, dz = -math.sin(ang), math.cos(ang)            # angle from top, positive CCW viewed from +x (right-hand about +x)
    p0 = (a["x"], dy * (a["r0"] - (ARM_O["spig_l"] if a["tag"] == "A" else ARM_I["spig_l"])), Z_AX + dz * (a["r0"] - (ARM_O["spig_l"] if a["tag"] == "A" else ARM_I["spig_l"])))
    r_end = a["r1"] + a["slot"]
    p1 = (a["x"], dy * r_end, Z_AX + dz * r_end)
    return rod(p0, p1, a["d"])


def agitator():
    parts = {"P1-301-201": p201_shaft()}
    ro = ri = None
    for n in RIB:
        s, _ = ribbon(n)
        if n[0] == "O":
            ro = s if ro is None else ro.union(s)
        else:
            ri = s if ri is None else ri.union(s)
    parts["P1-301-202"], parts["P1-301-203"] = ro, ri
    aa = ab = None
    for a in D.arms():
        s = p_arm(a)
        if a["tag"] == "A":
            aa = s if aa is None else aa.union(s)
        else:
            ab = s if ab is None else ab.union(s)
    parts["P1-301-204"], parts["P1-301-205"] = aa, ab
    return parts


# ------------------------------------------------------------------ 300 cover
Z_CV = Z_FLTOP + 3.0                       # cover underside on the compressed gasket


def cover():
    c = W().box(FL_OUT_X + 6, FL_OUT_Y + 6, 3).translate((0, 0, Z_CV + 1.5))
    c = c.cut(W().box(600, 400, 10).translate((-110, 0, Z_CV)))
    c = c.cut(W().circle(51).extrude(10).translate((330, 0, Z_CV - 2)))
    skirt = W().rect(FL_OUT_X + 6, FL_OUT_Y + 6).rect(FL_OUT_X, FL_OUT_Y).extrude(25).translate((0, 0, Z_CV + 3 - 25))
    up = W().rect(606, 406).rect(600, 400).extrude(25).translate((-110, 0, Z_CV + 3))
    fer = ferrule(TC4_OD, TC4_FER_OD, TC4_FER_L, (330, 0, Z_CV + 3), (0, 0, 1))
    hinge = None
    for x in (-300.0, 300.0):
        h = rod((x - 60, FL_OUT_Y / 2 + 14, Z_CV + 4), (x + 60, FL_OUT_Y / 2 + 14, Z_CV + 4), 20)
        hinge = h if hinge is None else hinge.union(h)
    return {"P1-301-301": c.union(skirt), "P1-301-302": up, "P1-301-303": fer, "P1-301-305": hinge}


# ------------------------------------------------------------------ 400 frame
def sqt(lx, ly, lz, t=LEG_T):
    dims = [lx, ly, lz]; k = dims.index(max(dims))
    inner = [d - 2 * t for d in dims]; inner[k] = dims[k] + 1
    return W().box(*dims).cut(W().box(*inner))


def frame():
    p = {}
    legs = rails = low = bp = feet = None
    hz = Z_RAIL - 12 - 3
    for sx in (-1, 1):
        for sy in (-1, 1):
            l = sqt(LEG, LEG, hz).translate((sx * X_LEG, sy * Y_LEG, 12 + hz / 2))
            legs = l if legs is None else legs.union(l)
            f = W().box(FOOT, FOOT, 12).translate((sx * X_LEG, sy * Y_LEG, 6)).faces(">Z").workplane(centerOption="CenterOfBoundBox").rect(110, 110, forConstruction=True).vertices().hole(14)
            f = f.union(W().box(LEG, LEG, 3).translate((sx * X_LEG, sy * Y_LEG, Z_RAIL - 1.5)))
            feet = f if feet is None else feet.union(f)
    Lr = 2 * (X_LEG - LEG / 2)
    for sy in (-1, 1):
        r = sqt(Lr, LEG, LEG).translate((0, sy * Y_LEG, Z_RAIL - LEG / 2))
        rails = r if rails is None else rails.union(r)
        q = sqt(Lr, LEG, LEG).translate((0, sy * Y_LEG, Z_LOW - LEG / 2))
        low = q if low is None else low.union(q)
    low = low.union(sqt(LEG, 2 * (Y_LEG - LEG / 2), LEG).translate((X_LEG, 0, Z_LOW - LEG / 2)))
    for sx in (-1, 1):
        x0 = BP["x_in"] if sx > 0 else -BP["x_in"] - BP["t"]
        b = W().box(BP["t"], 2 * (Y_LEG - LEG / 2), BP["z1"] - BP["z0"]).translate((x0 + BP["t"] / 2, 0, (BP["z0"] + BP["z1"]) / 2))
        b = b.cut(cyl_x(BP["hole"] / 2, x0 - 1, x0 + BP["t"] + 1))
        for dy in (-1, 1):
            for dz in (-1, 1):
                b = b.cut(cyl_x(BP["bolt_d"] / 2, x0 - 1, x0 + BP["t"] + 1, dy * BP["bolt_sq"] / 2, Z_AX + dz * BP["bolt_sq"] / 2))
        bp = b if bp is None else bp.union(b)
    ta = W().box(10, 80, 100).translate((X_LEG + LEG / 2 + 5, -Y_LEG, 1500)).cut(cyl_x(8.5, X_LEG + LEG / 2 - 1, X_LEG + LEG / 2 + 12, -Y_LEG, 1500))
    p.update({"P1-301-401": legs, "P1-301-402": rails, "P1-301-403": low, "P1-301-405": bp, "P1-301-406": feet, "P1-301-408": ta})
    return p


def gland():
    g = None
    for sx in (-1, 1):
        xin = L_IN / 2 + BOX["x_face"] - 8          # spigot 8 inside the box bore at first fit
        a, b = (xin, xin + FOLLOW["spig_l"]) if sx > 0 else (-xin - FOLLOW["spig_l"], -xin)
        s = cyl_x(FOLLOW["spig_d"] / 2, a, b)
        fa, fb = (b, b + FOLLOW["t"]) if sx > 0 else (a - FOLLOW["t"], a)
        s = s.union(cyl_x(FOLLOW["od"] / 2, fa, fb)).cut(cyl_x(FOLLOW["bore"] / 2, min(a, fa) - 1, max(b, fb) + 1))
        g = s if g is None else g.union(s)
    return {"P1-301-501": g}


def bought():
    b = {}
    brg = None
    for sx in (-1, 1):
        x = sx * X_BRG
        h = W().box(48, 175, 175).translate((x, 0, Z_AX)).cut(cyl_x(31, x - 40, x + 40))
        brg = h if brg is None else brg.union(h)
    b["P1-334 bearings UCF212"] = brg
    gm = W().box(170, 230, 260).translate((780, 0, Z_AX - 20)).cut(cyl_x(23, 690, 870))
    gm = gm.union(W("XZ").workplane(offset=115).center(780, Z_AX - 60).circle(95).extrude(330))   # motor along -y
    b["P1-333 gearmotor"] = gm
    b["P1-331 valve"] = W().circle(70).extrude(110).translate((0, 0, Z_TB - TC4_FER_L - 110)).union(W().box(160, 110, 110).translate((150, 0, Z_TB - 90)))
    b["CP-301 control panel"] = W().box(203, 508, 610).translate((X_LEG + LEG / 2 + 16 + 101.5, 0, 1200))
    return b


COL = {"1": (0.80, 0.82, 0.84), "2": (0.70, 0.74, 0.78), "3": (0.86, 0.87, 0.88), "4": (0.62, 0.66, 0.70), "5": (0.75, 0.75, 0.70)}


def build():
    OUT.mkdir(exist_ok=True)
    made = {}
    for fn in (trough, agitator, cover, frame, gland):
        made.update(fn())
    masses = {}
    asm = cq.Assembly(name="P1-301")
    for pid, s in made.items():
        cq.exporters.export(s, str(OUT / f"{pid}.step"))
        masses[pid] = round(s.val().Volume() * RHO, 2)
        asm.add(s, name=pid, color=cq.Color(*COL[pid.split("-")[-1][0]]))
    for k, s in bought().items():
        asm.add(s, name=k, color=cq.Color(0.20, 0.33, 0.50))
    asm.save(str(OUT / "P1-301-ASM.step"))
    asm.save(str(OUT / "P1-301-ASM.glb"), exportType="GLTF", tolerance=0.5, angularTolerance=0.2)
    (OUT / "masses.json").write_text(json.dumps(masses, indent=1))
    print(masses, round(sum(masses.values()), 1), "kg made parts")


if __name__ == "__main__":
    build()
