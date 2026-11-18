"""P1-212 rev B 3D model from design.py: STEP per made part, machine assembly STEP/GLB, masses.json."""
import json
import math
import pathlib
import sys

import cadquery as cq
from cadquery import Vector

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from design import *  # noqa: F401,F403

OUT = HERE / "cad"; OUT.mkdir(exist_ok=True)
RHO = 7.95e-6


def W(pl="XY"):
    return cq.Workplane(pl)


def cyl_x(r, x0, x1, y=0.0, z=0.0):
    return W("YZ").workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)


def tube_x(ro, ri, x0, x1):
    return cyl_x(ro, x0, x1).cut(cyl_x(ri, x0 - 1, x1 + 1))


def boxc(x0, x1, y0, y1, z0, z1):
    return W().box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def ferrule(xface, sgn):
    """2.5 in short weld ferrule, flange face at xface, tube side toward -sgn... sgn=+1: face at +x end."""
    x0, x1 = (xface - FER["L"], xface) if sgn > 0 else (xface, xface + FER["L"])
    body = tube_x(B_OD / 2, B_ID / 2, x0, x1)
    xf0, xf1 = (xface - 8, xface) if sgn > 0 else (xface, xface + 8)
    return body.union(tube_x(FER["fl_od"] / 2, B_ID / 2, xf0, xf1))


# ------------------------------------------------------------------ 100 barrel weldment
def p101_tube():
    t = tube_x(B_OD / 2, B_ID / 2, X_TUBE0, X_TUBE1)
    t = t.cut(boxc(-INLET["lx"] / 2, INLET["lx"] / 2, -INLET["wy"] / 2, INLET["wy"] / 2, 0, 40))
    t = t.cut(W().center(X_SPOUT, 0).circle(B_ID / 2).extrude(-40))
    return t


def p102_transition():
    o, i = TR_T, 0.0
    z0, z1 = 12.0, Z_FL_BOT
    outer = W().workplane(offset=z0).rect(INLET["lx"] + 2 * o, INLET["wy"] + 2 * o).workplane(offset=z1 - z0).rect(BIN_FL["open"] + 2 * o, BIN_FL["open"] + 2 * o).loft()
    inner = W().workplane(offset=z0 - 1).rect(INLET["lx"], INLET["wy"]).workplane(offset=z1 - z0 + 2).rect(BIN_FL["open"], BIN_FL["open"] + 0.6).loft()
    return outer.cut(inner).cut(cyl_x(B_OD / 2 - 0.2, -100, 100))


def p104_flange():
    f = W().rect(BIN_FL["sq"], BIN_FL["sq"]).rect(BIN_FL["open"], BIN_FL["open"]).extrude(T_FL).translate((0, 0, Z_FL_BOT))
    return f.faces(">Z").workplane().rect(BIN_FL["bolt_sq"], BIN_FL["bolt_sq"], forConstruction=True).vertices().hole(BIN_FL["hole"])


def p105_endflange():
    f = W("YZ").workplane(offset=X_FL_OUT).rect(EF["sq"], EF["sq"]).extrude(T_EF)
    f = f.cut(cyl_x(B_OD / 2 + 0.05, X_TUBE0, X_FL_IN + 1)).cut(cyl_x(EF["recess"] / 2, X_FL_OUT - 1, X_FL_OUT + EF["recess_d"]))
    f = f.cut(cyl_x(B_ID / 2, X_FL_OUT - 1, X_FL_IN + 1))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        f = f.cut(cyl_x(2.5, X_FL_OUT - 1, X_FL_OUT + 9, EF["pcd"] / 2 * math.cos(a), EF["pcd"] / 2 * math.sin(a)))
    return f


def p106_spout():
    s = W().center(X_SPOUT, 0).circle(B_OD / 2).circle(B_ID / 2).extrude(Z_SPOUT_END).translate((0, 0, 0))
    s = W().center(X_SPOUT, 0).circle(B_OD / 2).circle(B_ID / 2).extrude(-(-Z_SPOUT_END)).translate((0, 0, 0))
    return s.cut(cyl_x(B_OD / 2 - 0.3, X_SPOUT - 50, X_SPOUT + 50))


def barrel():
    return dict(tube=p101_tube(), transition=p102_transition(), flange=p104_flange(), endflange=p105_endflange(), spout=p106_spout(), ferrule=ferrule(X_TAIL, 1))


# ------------------------------------------------------------------ 200 screw
def p201_shaft():
    s = cyl_x(S_D / 2, X_S0, X_SP0).union(cyl_x(SPIGOT_D / 2, X_SP0, X_SP1))
    s = s.cut(cyl_x(SOCKET["d"] / 2, X_S0 - 1, X_S0 + SOCKET["depth"]))
    s = s.cut(boxc(X_S0 - 1, X_S0 + SOCKET["slot_d"], -SOCKET["slot_w"] / 2, SOCKET["slot_w"] / 2, -20, 20))
    return s


def p202_flight():
    L = X_F1 - X_F0
    turns = L / S_P
    w = (S_OD - S_D) / 2
    prof = W("XZ").center(S_D / 2 + w / 2 - 0.2, 0).rect(w + 0.4, S_T)
    hel = cq.Wire.makeHelix(S_P, L, S_D / 2 + w / 2)
    f = prof.sweep(cq.Workplane(obj=hel), isFrenet=True)
    return f.rotate((0, 0, 0), (0, 1, 0), 90).translate((X_F0, 0, 0))


# ------------------------------------------------------------------ 300 drive / tail
def p301_housing():
    h = cyl_x(HSG["spig_d"] / 2 - 0.05, X_H_FACE - HSG["spig_h"], X_H_FACE)
    h = h.union(cyl_x(HSG["collar_d"] / 2, X_FL_OUT - HSG["collar_t"], X_FL_OUT))
    h = h.union(cyl_x(HSG["body_d"] / 2, X_H_REAR0, X_FL_OUT - HSG["collar_t"]))
    h = h.union(cyl_x(HSG["rear_d"] / 2, X_H_REAR1, X_H_REAR0))
    h = h.cut(cyl_x(HSG["seal_bore"] / 2, X_H_FACE - HSG["seal_w"] - 1, X_H_FACE + 1))
    h = h.cut(cyl_x(15.0, X_BRG_A0 - 1, X_H_FACE))
    h = h.cut(cyl_x(HSG["brg_bore"] / 2, X_H_REAR1 - 1, X_BRG_A0))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        h = h.cut(cyl_x(3.3, X_FL_OUT - HSG["collar_t"] - 1, X_FL_OUT + 1, HSG["pcd_front"] / 2 * math.cos(a), HSG["pcd_front"] / 2 * math.sin(a)))
        h = h.cut(cyl_x(2.5, X_H_REAR1 - 1, X_H_REAR1 + 9, HSG["pcd_rear"] / 2 * math.cos(a), HSG["pcd_rear"] / 2 * math.sin(a)))
    return h


def p302_shaft():
    s = cyl_x(SHAFT["d"] / 2, SHAFT["x_end"], SHAFT["x_tip"])
    s = s.cut(cyl_x(3.0, -200, 200).rotate((X_PIN, 0, 0), (X_PIN, 0, 1), 0)) if False else s
    s = s.cut(W("XZ").center(X_PIN, 0).circle(3.0).extrude(15, both=True))
    s = s.union(W("XZ").center(X_PIN, 0).circle(3.0).extrude(12, both=True))       # pin fitted
    return s


def p304_spacers():
    o = tube_x(HSG["brg_bore"] / 2 - 0.05, 18.0, X_BRG_B0, X_BRG_A1)
    i = tube_x(14.0, 10.05, X_BRG_B0, X_BRG_A1)
    return o.union(i)


def p306_cap():
    c = cyl_x(FER["fl_od"] / 2, X_TAIL, X_TAIL + 10).union(cyl_x(CAP["boss_d"] / 2, X_TAIL + 10, X_TAIL + CAP["boss_l"]))
    return c.cut(cyl_x(CAP["bush_od"] / 2, X_TAIL - 1, X_TAIL + CAP["bush_l"]))


def p307_bush():
    return tube_x(CAP["bush_od"] / 2, CAP["bush_id"] / 2, X_TAIL, X_TAIL + CAP["bush_l"])


# ------------------------------------------------------------------ 400 lantern
def p400_lantern():
    t = LANT["t"]
    xf0, xf1 = X_H_REAR1 - t, X_H_REAR1
    xr0, xr1 = X_GM, X_GM + t
    f = W("YZ").workplane(offset=xf0).rect(LANT["front_sq"], LANT["front_sq"]).extrude(t).cut(cyl_x(26, xf0 - 1, xf1 + 1))
    r = W("YZ").workplane(offset=xr0).rect(LANT["rear_sq"], LANT["rear_sq"]).extrude(t).cut(cyl_x(LANT["spig"] / 2, xr0 - 1, xr1 + 1))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        f = f.cut(cyl_x(3.3, xf0 - 1, xf1 + 1, HSG["pcd_rear"] / 2 * math.cos(a), HSG["pcd_rear"] / 2 * math.sin(a)))
        r = r.cut(cyl_x(3.3, xr0 - 1, xr1 + 1, LANT["pcd_gm"] / 2 * math.cos(a), LANT["pcd_gm"] / 2 * math.sin(a)))
    bw, bt = LANT["bar"]
    bars = boxc(xr1, xf0, -bw / 2, bw / 2, 55 - bt, 55).union(boxc(xr1, xf0, -bw / 2, bw / 2, -55, -55 + bt))
    return f.union(r).union(bars)


def p404_guard():
    g = boxc(X_GM + 8, X_H_REAR1 - 8, -51.5, 51.5, -47, 47).cut(boxc(X_GM, X_H_REAR1, -50, 50, -46.9, 46.9))
    return g.cut(boxc(X_GM, X_H_REAR1, -60, 60, -46, 46).translate((0, 0, 0)).cut(boxc(X_GM, X_H_REAR1, -60, 60, -100, -46)).cut(boxc(X_GM, X_H_REAR1, -60, 60, 46, 100))) if False else \
        boxc(X_GM + 8, X_H_REAR1 - 8, 51.5 - 1.5, 51.5, -47, 47).union(boxc(X_GM + 8, X_H_REAR1 - 8, -51.5, -50, -47, 47))


# ------------------------------------------------------------------ bought (envelopes)
def bought():
    gm = cyl_x(60, X_GM - GM_LEN, X_GM - 40).union(boxc(X_GM - 110, X_GM - 10, -62, 62, -62, 70)).union(cyl_x(LANT["spig"] / 2 - 0.1, X_GM - 10, X_GM))
    gm = gm.union(cyl_x(SHAFT["d"] / 2, X_GM, X_GM + 40))
    cpl = cyl_x(17.0, -305, -250)
    brg = tube_x(21, 10, X_BRG_A1, X_BRG_A0).union(tube_x(21, 10, X_BRG_B1, X_BRG_B0))
    clamp = tube_x(FER["fl_od"] / 2 + 12, FER["fl_od"] / 2 - 4, X_TAIL - 8, X_TAIL + 10)
    sleeve = W().center(X_SPOUT, 0).circle(B_OD / 2 + 3).circle(B_OD / 2).extrude(Z_LID + 25 - Z_SPOUT_END + 30).translate((0, 0, Z_LID + 25 - 30 + 0)).translate((0, 0, 0))
    sleeve = W().center(X_SPOUT, 0).circle(B_OD / 2 + 3).circle(B_OD / 2).extrude((Z_SPOUT_END + 30) - (Z_LID + 25 - 30)).translate((0, 0, Z_LID - 5))
    return {"P1-216": gm, "P1-244": cpl, "P1-241": brg, "P1-247": clamp, "P1-214": sleeve}


PARTS = {}


def build():
    b = barrel()
    PARTS.update({"P1-212-101": b["tube"], "P1-212-102": b["transition"], "P1-212-104": b["flange"], "P1-212-105": b["endflange"],
                  "P1-212-106": b["spout"], "P1-212-107": b["ferrule"], "P1-212-201": p201_shaft(), "P1-212-202": p202_flight(),
                  "P1-212-301": p301_housing(), "P1-212-302": p302_shaft(), "P1-212-304": p304_spacers(), "P1-212-306": p306_cap(),
                  "P1-212-307": p307_bush(), "P1-212-400": p400_lantern(), "P1-212-404": p404_guard()})
    return PARTS


GROUP = {"P1-212-10": ["P1-212-101", "P1-212-102", "P1-212-104", "P1-212-105", "P1-212-106", "P1-212-107"],
         "P1-212-20": ["P1-212-201", "P1-212-202"], "P1-212-30": ["P1-212-301", "P1-212-302", "P1-212-304"],
         "P1-212-31": ["P1-212-306", "P1-212-307"], "P1-212-40": ["P1-212-400", "P1-212-404"]}

if __name__ == "__main__":
    P = build()
    masses = {}
    asm = cq.Assembly(name="P1-212")
    col_ss, col_b = cq.Color(0.78, 0.80, 0.83), cq.Color(0.20, 0.32, 0.55)
    for g, ids in GROUP.items():
        sub = cq.Assembly(name=g)
        for pid in ids:
            s = P[pid]
            rho = 0.94e-6 if pid == "P1-212-307" else RHO
            masses[pid] = round(s.val().Volume() * rho, 3)
            cq.exporters.export(s, str(OUT / f"{pid}.step"))
            sub.add(s, name=pid, color=cq.Color(0.95, 0.95, 0.92) if pid == "P1-212-307" else col_ss)
        asm.add(sub, name=g)
    for k, s in bought().items():
        asm.add(s, name=k, color=col_b if k != "P1-214" else cq.Color(0.9, 0.9, 0.85))
    asm.save(str(OUT / "P1-212-ASM.step"))
    asm.save(str(OUT / "P1-212-ASM.glb"), exportType="GLTF", tolerance=0.2, angularTolerance=0.15)
    (OUT / "masses.json").write_text(json.dumps(masses, indent=1))
    print(masses, round(sum(masses.values()), 2), "kg made parts")
