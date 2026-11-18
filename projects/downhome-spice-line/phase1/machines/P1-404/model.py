"""P1-404 rev B 3D model from design.py: STEP per made part, machine assembly STEP/GLB, masses.json.
Modelled with a jar on the rollers and the idler arm down on it; peel plate at setting J."""
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
JAR = CONT["jar-12"]
XL0, XL1 = -SP["x"] - SP["t"] / 2, -SP["x"] + SP["t"] / 2       # -x plate x -165..-155
XR0, XR1 = SP["x"] - SP["t"] / 2, SP["x"] + SP["t"] / 2         # +x plate x 155..165


def W(pl="XY"):
    return cq.Workplane(pl)


def box(x0, x1, y0, y1, z0, z1):
    return W().box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(r, z0, h, x=0.0, y=0.0):
    return W().circle(r).extrude(h).translate((x, y, z0))


def xcyl(r, x0, x1, y, z):                     # cylinder along x
    return W("YZ").circle(r).extrude(x1 - x0).translate((x0, y, z))


def holes_z(s, pts, d, z0=-1.0, h=200.0):
    for x, y in pts:
        s = s.cut(cyl(d / 2, z0, h, x, y))
    return s


def holes_x(s, pts, d, x0=-400.0, x1=400.0):
    for y, z in pts:
        s = s.cut(xcyl(d / 2, x0, x1, y, z))
    return s


def yz_plate(pts, x0, x1):                     # plate in the y-z plane from an outline of (y, z)
    return W("YZ").polyline(pts).close().extrude(x1 - x0).translate((x0, 0, 0))


# ------------------------------------------------------------------ 100 frame
BASE_HOLES = [(sx * BASE["hx"], sy * BASE["hy"]) for sx in (-1, 1) for sy in (-1, 1)]
SP_SCREWS = [-80.0, 20.0, 120.0]                                    # M5 up into each side plate bottom edge (y)
FENCE_HOLES = {k: [(fence_x(k) - 20.0, sy * 0.0) for sy in (1,)] + [(fence_x(k) - 32.0, 0.0)] for k in CONT}
ENC_HOLES = [((ENC["x0"] + ENC["x1"]) / 2, -60.0), ((ENC["x0"] + ENC["x1"]) / 2, 60.0)]
TIE = dict(y=-80.0, z=30.0, d=16.0)


def p101_base():
    b = box(-BASE["w"] / 2, BASE["w"] / 2, BASE["y0"], BASE["y0"] + BASE["d"], 0, BASE["t"]).edges("|Z").fillet(10.0)
    b = holes_z(b, BASE_HOLES, BASE["hole"])
    b = holes_z(b, [(sx * SP["x"], y) for sx in (-1, 1) for y in SP_SCREWS], 5.5)
    b = holes_z(b, FENCE_HOLES["shaker-250"] + FENCE_HOLES["jar-12"], 4.2)          # M5 tapped
    b = holes_z(b, ENC_HOLES, 5.0)                                                  # M6 tapped
    return b


SPL_PTS = [(SPL["y0"], BASE["t"]), (SPL["y1"], BASE["t"]), (SPL["y1"], SPL["z1"]), (110.0, SPL["z1"]), (SPL["y0"], 200.0)]
SPR_PTS = [(SPR["y0"], BASE["t"]), (SPR["y1"], BASE["t"]), (SPR["y1"], SPR["z1"]), (60.0, SPR["z1"]), (SPR["y0"], 160.0)]
PEEL_HOLES = {k: [(40.0, z_top(CONT[c]["d"]) - 15.0), (70.0, z_top(CONT[c]["d"]) - 15.0)] for k, c in (("S", "shaker-250"), ("J", "jar-12"))}
MOT_SLOTS = [(MOT["y"] + sy * MOT["bolt_sq"] / 2, MOT["z"] + sz * MOT["bolt_sq"] / 2) for sy in (-1, 1) for sz in (-1, 1)]
LDH_PCD = 58.0
def ldh_holes(y, z):
    return [(y + LDH_PCD / 2 * math.cos(math.radians(a)), z + LDH_PCD / 2 * math.sin(math.radians(a))) for a in (90, 210, 330)]
UNW_HOLES = [(UNW["y"] + 22 * math.cos(math.radians(a)), UNW["z"] + 22 * math.sin(math.radians(a))) for a in (90, 210, 330)]


def p102_sidel():
    s = yz_plate(SPL_PTS, XL0, XL1)
    s = holes_x(s, [(-ROL["y"], ROL["z"]), (ROL["y"], ROL["z"])], 28.0)           # 6001 bores H7
    s = holes_x(s, [(MOT["y"], MOT["z"])], 38.5)                                   # motor pilot, clearance for the belt tension slide
    s = holes_x(s, MOT_SLOTS, 5.5)
    s = holes_x(s, [(LD["y"], LD["z"]), (REW["y"], REW["z"])], 40.0)               # bearing housing spigots H8
    s = holes_x(s, ldh_holes(LD["y"], LD["z"]) + ldh_holes(REW["y"], REW["z"]), 5.5)
    s = holes_x(s, [(UNW["y"], UNW["z"])], 25.0)
    s = holes_x(s, UNW_HOLES, 4.2)
    s = holes_x(s, [(IDL["piv_y"], IDL["piv_z"])], 16.0)
    s = holes_x(s, [(G1["y"], G1["z"])], 8.5)
    s = holes_x(s, [(PINCH["piv_y"], PINCH["piv_z"])], 8.0)
    s = holes_x(s, [(TIE["y"], TIE["z"])], 8.5)
    s = holes_x(s, PEEL_HOLES["S"] + PEEL_HOLES["J"], 4.2)
    return s


def p103_sider():
    s = yz_plate(SPR_PTS, XR0, XR1)
    s = holes_x(s, [(-ROL["y"], ROL["z"]), (ROL["y"], ROL["z"])], 28.0)
    s = holes_x(s, [(IDL["piv_y"], IDL["piv_z"])], 16.0)
    s = holes_x(s, [(TIE["y"], TIE["z"])], 8.5)
    s = holes_x(s, [(IDL["piv_y"] - 50.0, IDL["piv_z"] - 12.0)], 12.2)            # M12 start sensor B1
    return s


def p104_tie():
    return xcyl(TIE["d"] / 2, XL1, XR0, TIE["y"], TIE["z"])


def p105_fence():
    x = fence_x("jar-12")
    f = box(x - FENCE["t"], x, -FENCE["w"] / 2, FENCE["w"] / 2, BASE["t"], BASE["t"] + FENCE["h"])
    return f.union(box(x - 40.0, x, -FENCE["w"] / 2, FENCE["w"] / 2, BASE["t"], BASE["t"] + 8.0))


# ------------------------------------------------------------------ 200 drive
def p201_housing(y, z):
    h = xcyl(20.0, XL1, XL1 + 40.0, y, z).union(xcyl(35.0, XL1, XL1 + 6.0, y, z)).union(xcyl(20.0, XL0, XL1, y, z))
    h = h.cut(xcyl(14.0, XL0 - 1, XL1 + 41, y, z))
    for yy, zz in ldh_holes(y, z):
        h = h.cut(xcyl(2.75, XL1 - 1, XL1 + 7, yy, zz))
    return h


def p202_linerroller():
    r = xcyl(LD["d"] / 2, LD["x0"], LD["x1"], LD["y"], LD["z"])
    return r.union(xcyl(6.0, X_ORING - 8.0, LD["x0"], LD["y"], LD["z"]))


def p203_pinchlever():
    py, pz = PINCH["piv_y"], PINCH["piv_z"]
    ry, rz = LD["y"], LD["z"] + LD["d"] / 2 + PINCH["d"] / 2 + 0.2
    lev = W("YZ").polyline([(py + 8, pz + 8), (ry - 8, rz + 8), (ry - 8, rz - 8), (py + 8, pz - 8)]).close().extrude(6.0).translate((XL1 + 2, 0, 0))
    lev = lev.union(xcyl(4.0, XL1 + 2, LD["x1"], ry, rz))                    # pinch shaft Ø8 cantilever
    lev = lev.union(xcyl(PINCH["d"] / 2, LD["x0"] + 20, LD["x1"] - 10, ry, rz))  # UHMW pinch roller (same part number group)
    return lev


def p204_guard():
    y0, y1, z0, z1 = -90.0, 165.0, 15.0, 165.0
    g = box(XL0 - 55.0, XL0, y0, y1, z0, z1).cut(box(XL0 - 53.5, XL0 + 1, y0 + 1.5, y1 - 1.5, z0 + 1.5, z1 - 1.5))
    return g


# ------------------------------------------------------------------ 300 web path
def p301_unwspindle():
    s = xcyl(12.5, XL1, 85.0, UNW["y"], UNW["z"]).union(xcyl(30.0, XL1, XL1 + 8.0, UNW["y"], UNW["z"]))
    return s


def p302_hub(y, z, flange=True):
    h = xcyl(UNW["hub_d"] / 2 - 0.4, -70.0, 70.0, y, z)
    if flange:
        h = h.union(xcyl(UNW["flange_d"] / 2, -76.0, -70.0, y, z))
    return h.cut(xcyl(12.6 if flange else 6.1, -80.0, 80.0, y, z))


def p303_collar(y, z):
    return xcyl(25.0, 70.0, 90.0, y, z).cut(xcyl(12.6, 69.0, 91.0, y, z))


def p304_brake():
    y, z = UNW["y"], UNW["z"] - UNW["flange_d"] / 2 + 15.0
    return box(-82.0, -77.0, y - 15.0, y + 15.0, z - 5.0, z + 60.0).union(box(XL1, -77.0, y - 15.0, y + 15.0, z + 50.0, z + 60.0))


def p305_rewshaft():
    return xcyl(6.0, X_ORING - 8.0, 75.0, REW["y"], REW["z"])


def p306_orpulleys():
    return xcyl(20.0, X_ORING - 5.0, X_ORING + 5.0, LD["y"], LD["z"]).union(xcyl(20.0, X_ORING - 5.0, X_ORING + 5.0, REW["y"], REW["z"]))


def p307_guide():
    return xcyl(G1["d"] / 2, -65.0, 65.0, G1["y"], G1["z"]).union(xcyl(5.0, XL1, 70.0, G1["y"], G1["z"]))


# ------------------------------------------------------------------ 400 peel + idler
def peel_pts(k="J"):
    c = "jar-12" if k == "J" else "shaker-250"
    zt = z_top(CONT[c]["d"]) + 1.0
    a = math.radians(PEEL["slope"])
    return (PEEL["tip_y"], zt), (PEEL["tip_y"] + PEEL["L"] * math.cos(a), zt + PEEL["L"] * math.sin(a))


def p401_peel(k="J"):
    (y0, z0), (y1, z1) = peel_pts(k)
    pl = W("YZ").polyline([(y0, z0), (y1, z1), (y1, z1 - PEEL["t"]), (y0, z0 - PEEL["t"])]).close().extrude(PEEL["w"]).translate((-PEEL["w"] / 2, 0, 0))
    fl = box(-PEEL["w"] / 2, PEEL["w"] / 2, y1 - PEEL["t"], y1, z1 - 30.0, z1)
    return pl.union(fl)


def p402_peelbkt(k="J"):
    (y0, z0), (y1, z1) = peel_pts(k)
    zc = z_top(CONT["jar-12" if k == "J" else "shaker-250"]["d"]) - 15.0
    arm = box(XL1, PEEL["w"] / 2 - 5.0, y1, y1 + 6.0, z1 - 30.0, z1)              # along x behind the peel flange, 2 x M5 at x ±40
    foot = box(XL1, XL1 + 6.0, 25.0, y1 + 6.0, zc - 12.0, zc + 12.0)               # on the side plate, 2 x M5 at S or J
    riser = box(XL1, XL1 + 6.0, y1, y1 + 6.0, zc - 12.0, z1)
    return arm.union(foot).union(riser)


def p403_pivot():
    return xcyl(8.0, XL1, XR0, IDL["piv_y"], IDL["piv_z"])


def arm_pts(k="jar-12"):
    yc, zc, R = idler_at(k)
    return (IDL["piv_y"], IDL["piv_z"]), (yc, zc)


def p404_arms(k="jar-12"):
    (py, pz), (yc, zc) = arm_pts(k)
    out = None
    for x0 in (XL1 + 4.0, XR0 - 4.0 - IDL["arm_t"]):
        L = math.hypot(yc - py, zc - pz) + (60.0 if x0 > 0 else 0.0)
        ux, uz = (yc - py) / math.hypot(yc - py, zc - pz), (zc - pz) / math.hypot(yc - py, zc - pz)
        ey, ez = py + ux * L, pz + uz * L
        nx, nz = -uz * IDL["arm_w"] / 2, ux * IDL["arm_w"] / 2
        a = W("YZ").polyline([(py + nx, pz + nz), (ey + nx, ez + nz), (ey - nx, ez - nz), (py - nx, pz - nz)]).close().extrude(IDL["arm_t"]).translate((x0, 0, 0))
        out = a if out is None else out.union(a)
    return out


def p405_idlershaft(k="jar-12"):
    yc, zc, _ = idler_at(k)
    return xcyl(IDL["shaft"] / 2, XL1 + 4.0, XR0 - 4.0, yc, zc)


def p406_sensorbkt():
    return box(XR0 - 30.0, XR0, IDL["piv_y"] - 62.0, IDL["piv_y"] - 38.0, IDL["piv_z"] - 30.0, IDL["piv_z"] - 27.0).union(
        box(XR0 - 3.0, XR0, IDL["piv_y"] - 62.0, IDL["piv_y"] - 38.0, IDL["piv_z"] - 30.0, IDL["piv_z"] - 5.0))


# ------------------------------------------------------------------ bought (envelopes)
def bought():
    rol = xcyl(ROL["d"] / 2, -ROL["face"] / 2, ROL["face"] / 2, -ROL["y"], ROL["z"]).union(xcyl(ROL["d"] / 2, -ROL["face"] / 2, ROL["face"] / 2, ROL["y"], ROL["z"]))
    for y in (-ROL["y"], ROL["y"]):
        rol = rol.union(xcyl(ROL["shaft"] / 2, X_BELT2 - 6.0, XR1, y, ROL["z"]))
    mot = box(XL1, XL1 + MOT["body_L"], MOT["y"] - MOT["flange"] / 2, MOT["y"] + MOT["flange"] / 2, MOT["z"] - MOT["flange"] / 2, MOT["z"] + MOT["flange"] / 2)
    belts = xcyl(pd(ROLLER_T) / 2 + 1, X_BELT1 - 5, X_BELT1 + 5, -ROL["y"], ROL["z"]).union(xcyl(pd(ROLLER_T) / 2 + 1, X_BELT1 - 5, X_BELT1 + 5, ROL["y"], ROL["z"]))
    belts = belts.union(xcyl(pd(MOT["T"]) / 2 + 1, X_BELT1 - 5, X_BELT1 + 5, MOT["y"], MOT["z"])).union(xcyl(pd(ROLLER_T) / 2 + 1, X_BELT2 - 5, X_BELT2 + 5, ROL["y"], ROL["z"]))
    belts = belts.union(xcyl(pd(LD["T"]) / 2 + 1, X_BELT2 - 5, X_BELT2 + 5, LD["y"], LD["z"]))
    yc, zc, _ = idler_at("jar-12")
    idl = xcyl(IDL["d"] / 2, -IDL["face"] / 2, IDL["face"] / 2, yc, zc)
    (y0, z0), (y1, z1) = peel_pts("J")
    gap = box(40.0, 70.0, 45.0, 70.0, z0 - 25.0, z0 + 30.0).cut(box(39.0, 71.0, 44.0, 71.0, z0 - 5.0, z0 + 12.0))   # fork over the web edge at +x
    roll = xcyl(LAB["od_max"] / 2 - 10, -JAR["lab_H"] / 2 - 3, JAR["lab_H"] / 2 + 3, UNW["y"], UNW["z"]).cut(xcyl(UNW["hub_d"] / 2, -60, 60, UNW["y"], UNW["z"]))
    rew = xcyl(55.0, -JAR["lab_H"] / 2 - 3, JAR["lab_H"] / 2 + 3, REW["y"], REW["z"]).cut(xcyl(UNW["hub_d"] / 2, -60, 60, REW["y"], REW["z"]))
    enc = box(ENC["x0"], ENC["x1"], ENC["y0"], ENC["y1"], BASE["t"], BASE["t"] + ENC["h"])
    ops = None
    for k, (x, z) in ENC_OPS.items():
        r, L = (20.0, 32.0) if k == "estop" else (14.0, 20.0)
        o = W("XZ").circle(r).extrude(L).translate((x, ENC["y0"], BASE["t"] + z))
        ops = o if ops is None else ops.union(o)
    sens = xcyl(6.0, XR0 - 40.0, XR0 - 3.0, IDL["piv_y"] - 50.0, IDL["piv_z"] - 12.0)
    knob = xcyl(14.0, XR0 - 4.0, XR0 + 30.0, *_arm_end())
    jar = xcyl(JAR["d"] / 2, fence_x("jar-12"), fence_x("jar-12") + JAR["h"], 0.0, z_cent(JAR["d"]))
    return {"P1-425": rol, "P1-426": mot, "P1-427": gap, "P1-454": belts, "P1-455": idl, "P1-456": enc.union(ops), "P1-457": sens, "P1-458": knob,
            "LABELS": roll.union(rew), "JAR": jar}


def _arm_end():
    (py, pz), (yc, zc) = arm_pts()
    L = math.hypot(yc - py, zc - pz); u = ((yc - py) / L, (zc - pz) / L)
    return py + u[0] * (L + 55.0), pz + u[1] * (L + 55.0)


PARTS = {}


def build():
    PARTS.update({"P1-404-101": p101_base(), "P1-404-102": p102_sidel(), "P1-404-103": p103_sider(), "P1-404-104": p104_tie(), "P1-404-105": p105_fence(),
                  "P1-404-201": p201_housing(LD["y"], LD["z"]).union(p201_housing(REW["y"], REW["z"])), "P1-404-202": p202_linerroller(),
                  "P1-404-203": p203_pinchlever(), "P1-404-204": p204_guard(),
                  "P1-404-301": p301_unwspindle(), "P1-404-302": p302_hub(UNW["y"], UNW["z"]).union(p302_hub(REW["y"], REW["z"], False)),
                  "P1-404-303": p303_collar(UNW["y"], UNW["z"]).union(p303_collar(REW["y"], REW["z"])), "P1-404-304": p304_brake(),
                  "P1-404-305": p305_rewshaft(), "P1-404-306": p306_orpulleys(), "P1-404-307": p307_guide(),
                  "P1-404-401": p401_peel(), "P1-404-402": p402_peelbkt(), "P1-404-403": p403_pivot(), "P1-404-404": p404_arms(),
                  "P1-404-405": p405_idlershaft(), "P1-404-406": p406_sensorbkt()})
    return PARTS


GROUP = {"P1-404-100": ["P1-404-101", "P1-404-102", "P1-404-103", "P1-404-104", "P1-404-105"],
         "P1-404-200": ["P1-404-201", "P1-404-202", "P1-404-203", "P1-404-204"],
         "P1-404-300": ["P1-404-301", "P1-404-302", "P1-404-303", "P1-404-304", "P1-404-305", "P1-404-306", "P1-404-307"],
         "P1-404-400": ["P1-404-401", "P1-404-402", "P1-404-403", "P1-404-404", "P1-404-405", "P1-404-406"]}
UHMW_PARTS = ("P1-404-105", "P1-404-302", "P1-404-303", "P1-404-306", "P1-404-307")
DENS = {p: RHO_UHMW for p in UHMW_PARTS}

if __name__ == "__main__":
    P = build()
    masses = {}
    asm = cq.Assembly(name="P1-404")
    col_ss, col_b, col_u = cq.Color(0.78, 0.80, 0.83), cq.Color(0.20, 0.32, 0.55), cq.Color(0.96, 0.96, 0.94)
    for g, ids in GROUP.items():
        sub = cq.Assembly(name=g)
        for pid in ids:
            s = P[pid]
            masses[pid] = round(s.val().Volume() * DENS.get(pid, RHO), 3)
            cq.exporters.export(s, str(OUT / f"{pid}.step"))
            sub.add(s, name=pid, color=col_u if pid in UHMW_PARTS else col_ss)
        asm.add(sub, name=g)
    cols = {"P1-425": cq.Color(0.85, 0.55, 0.15), "P1-426": cq.Color(0.15, 0.15, 0.15), "P1-427": cq.Color(0.2, 0.4, 0.8), "P1-455": cq.Color(0.9, 0.3, 0.25),
            "P1-456": cq.Color(0.55, 0.57, 0.6), "P1-457": cq.Color(0.9, 0.75, 0.1), "P1-458": cq.Color(0.1, 0.1, 0.1),
            "LABELS": cq.Color(0.95, 0.92, 0.80), "JAR": cq.Color(0.75, 0.88, 0.95)}
    for k, s in bought().items():
        asm.add(s, name=k, color=cols.get(k, col_b))
    asm.save(str(OUT / "P1-404-ASM.step"))
    asm.save(str(OUT / "P1-404-ASM.glb"), exportType="GLTF", tolerance=0.2, angularTolerance=0.15)
    (OUT / "masses.json").write_text(json.dumps(masses, indent=1))
    print(masses, round(sum(masses.values()), 2), "kg made parts")
