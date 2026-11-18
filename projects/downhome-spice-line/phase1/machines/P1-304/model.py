"""P1-304 rev B 3D model from design.py: STEP per made part, machine assembly STEP/GLB, masses.json."""
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


def ring(ro, ri, z0, h):
    return W().circle(ro).circle(ri).extrude(h).translate((0, 0, z0))


def polar(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


# ------------------------------------------------------------------ 100 base weldment
def p101_seat():
    s = ring(SEAT["od"] / 2, SEAT["id"] / 2, 0, SEAT["t"])
    pts = [polar(R_ISO, a) for a in A_ISO] + [polar(BOND["r"], BOND["a_seat"])]
    return s.faces(">Z").workplane(centerOption="ProjectedOrigin", origin=(0, 0, 0)).pushPoints(pts).hole(9.0)


def p102_upstand():
    return ring(R_O, R_I, UPST["z0"], UPST["h"])


def p103_skirt():
    return ring(SKIRT["od"] / 2, SKIRT["od"] / 2 - SKIRT["t"], -SKIRT["h"], SKIRT["h"])


def p104_tabs():
    out = None
    for a in (30.0, 150.0, 270.0):
        t = W().box(TAB["t"], TAB["w"], TAB["h"] + SEAT["t"]).translate((TAB["r"] + TAB["t"] / 2, 0, (SEAT["t"] - TAB["h"]) / 2))
        t = t.rotate((0, 0, 0), (0, 0, 1), a)
        out = t if out is None else out.union(t)
    return out


# ------------------------------------------------------------------ 200 body weldment
def p201_shell():
    return ring(R_O, R_I, Z_B0, Z_B1 - Z_B0)


def p202_topfl():
    return ring(TOPFL["od"] / 2, TOPFL["id"] / 2, Z_B1, TOPFL["t"])


def p207_lplates():
    out = None
    for k in range(LATCH["n"]):
        a = LATCH["a0"] + 90 * k
        pl = W().box(LPLATE["t"], LPLATE["w"], LPLATE["h"]).translate((R_O + LPLATE["t"] / 2, 0, LPLATE["z0"] + LPLATE["h"] / 2))
        pl = pl.faces(">X").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, -LPLATE["holes"][0] / 2), (0, LPLATE["holes"][0] / 2)]).hole(LPLATE["holes"][1])
        pl = pl.rotate((0, 0, 0), (0, 0, 1), a)
        out = pl if out is None else out.union(pl)
    return out


def p203_bars():
    out = None
    for y in BAR["y"]:
        L = 2 * math.sqrt(R_I ** 2 - (abs(y) + BAR["w"] / 2) ** 2) - 1
        b = W().box(L, BAR["w"], BAR["t"]).translate((0, y, BAR["z"] + BAR["t"] / 2))
        out = b if out is None else out.union(b)
    return out


def p204_ledge():
    return ring(R_I, LEDGE["id"] / 2, LEDGE["z"], LEDGE["t"])


def p205_brackets():
    out = None
    for a in A_ISO:
        h = W().box(BRK["l"] + 6, BRK["w"], BRK["t"]).translate((R_O + (BRK["l"] + 6) / 2 - 6, 0, Z_ISO_TOP + BRK["t"] / 2))
        h = h.cut(W().center(R_ISO, 0).circle(4.5).extrude(20).translate((0, 0, Z_ISO_TOP - 5)))
        if a == BOND["a_brk"]:
            h = h.cut(W().center(R_ISO + 18, 0).circle(4.5).extrude(20).translate((0, 0, Z_ISO_TOP - 5)))
        v = W().box(BRK["t"], BRK["w"], 40).translate((R_O + BRK["t"] / 2, 0, Z_ISO_TOP + 20))
        g = h.union(v).rotate((0, 0, 0), (0, 0, 1), a)
        out = g if out is None else out.union(g)
    return out


def p206_vbracket():
    """vibrator plate 10 thk on 2 gussets 8 thk: gussets welded to the shell (z 40..150), flange underside, and above the flange edge."""
    z0, z1, xp = VBR["z0"], VBR["z1"], VBR["x"]
    pl = W().box(VBR["t"], VBR["w"], z1 - z0).translate((xp + VBR["t"] / 2, 0, (z0 + z1) / 2))
    pl = pl.faces(">X").workplane(centerOption="CenterOfBoundBox").center(0, Z_VIB - (z0 + z1) / 2) \
        .rect(VB_HOLES["sy"], VB_HOLES["sz"], forConstruction=True).vertices().hole(VB_HOLES["d"])
    gus = None
    for y in (-VBR["w"] / 2 + VBR["gus_t"] / 2 + 10, VBR["w"] / 2 - VBR["gus_t"] / 2 - 10):
        g = W("XZ").polyline([(R_O, z0), (xp, z0), (xp, z1), (TOPFL["od"] / 2 + 1, z1 - 60), (TOPFL["od"] / 2 + 1, Z_TOP), (R_O, Z_B1)]).close() \
            .extrude(VBR["gus_t"] / 2, both=True).translate((0, y, 0))
        gus = g if gus is None else gus.union(g)
    return pl.union(gus)


# ------------------------------------------------------------------ 300 lid weldment
def p301_lid():
    d = W().circle(LID["od"] / 2).extrude(LID["t"]).translate((0, 0, Z_LID0))
    d = d.cut(W().circle(TC4["id"] / 2).extrude(10).translate((0, 0, Z_LID0 - 2)))
    x, y = polar(TC3["r"], TC3["a"])
    d = d.cut(W().center(x, y).circle(TC3["id"] / 2).extrude(10).translate((0, 0, Z_LID0 - 2)))
    return d


def ferrule(od, idd, fl, L, x=0.0, y=0.0):
    b = W().center(x, y).circle(od / 2).circle(idd / 2).extrude(L)
    f = W().center(x, y).circle(fl / 2).circle(idd / 2).extrude(8).translate((0, 0, L - 8))
    return b.union(f).translate((0, 0, Z_FER0))


def p302_ferrules():
    x, y = polar(TC3["r"], TC3["a"])
    return ferrule(TC4["od"], TC4["id"], TC4["fl"], TC4["L"]).union(ferrule(TC3["od"], TC3["id"], TC3["fl"], TC3["L"], x, y))


def p304_ktabs():
    out = None
    for k in range(LATCH["n"]):
        a = LATCH["a0"] + 90 * k
        t = W().box(KTAB["t"], KTAB["w"], KTAB["h"]).translate((LID["od"] / 2 + KTAB["t"] / 2, 0, Z_LID0 + LID["t"] - KTAB["h"] / 2))
        t = t.faces(">X").workplane(centerOption="CenterOfBoundBox").pushPoints([(-10, -5), (10, -5)]).hole(5.5)
        t = t.rotate((0, 0, 0), (0, 0, 1), a)
        out = t if out is None else out.union(t)
    return out


def p303_pads():
    out = None
    for a in PAD["a"]:
        x, y = polar(PAD["r"], a)
        p = W().center(x, y).circle(PAD["d"] / 2).circle(PAD["d"] / 2 - 2).extrude(PAD["steel"] - 3).translate((0, 0, Z_LID0 - PAD["steel"] + 3))
        p = p.union(W().center(x, y).circle(PAD["d"] / 2).extrude(3).translate((0, 0, Z_LID0 - PAD["steel"])))
        out = p if out is None else out.union(p)
    return out


# ------------------------------------------------------------------ 400 screen deck
def p401_upper():
    return ring(DECK["od"] / 2, DECK["od"] / 2 - DECK["t"], Z_DECK0 + DECK["h_lo"], DECK["h_up"])


def p402_lower():
    return ring(DECK["od"] / 2, DECK["od"] / 2 - DECK["t"], Z_DECK0, DECK["h_lo"])


def p403_cloth():
    return W().circle(DECK["od"] / 2 - 1).extrude(0.6).translate((0, 0, Z_DECK0 + DECK["h_lo"]))


# ------------------------------------------------------------------ bought envelopes
def bought():
    iso = None
    for a in A_ISO:
        x, y = polar(R_ISO, a)
        c = W().center(x, y).circle(ISO["d"] / 2).extrude(ISO["h"]).translate((0, 0, SEAT["t"]))
        iso = c if iso is None else iso.union(c)
    mag = W().box(MAG["sq"], MAG["sq"], 6).translate((0, 0, BAR["z"] + BAR["t"] + 3))
    for k in range(5):
        x = -MAG["sq"] / 2 + 30 + k * 61
        mag = mag.union(W("XZ").center(x, BAR["z"] + BAR["t"] + 18).circle(12.7).extrude(MAG["sq"] / 2 - 6, both=True))
    vx = VBR["x"] + VBR["t"]
    vib = W().box(20, 120, 170).translate((vx + 10, 0, Z_VIB))
    vib = vib.union(W().center(vx + 85, 0).circle(70).extrude(260).translate((0, 0, Z_VIB - 130)))
    flex = ring(R_O + 2, R_O, Z_ISO_TOP - 26, 60)
    latches = None
    for k in range(LATCH["n"]):
        a = LATCH["a0"] + 90 * k
        l = W().box(22, 30, 75).translate((R_O + LPLATE["t"] + 11, 0, LPLATE["z0"] + 45)).rotate((0, 0, 0), (0, 0, 1), a)
        latches = l if latches is None else latches.union(l)
    x, y = polar(TC3["r"], TC3["a"])
    return {"P1-341": iso, "P1-307": mag, "P1-306": vib, "P1-344": flex, "P1-342": latches}


PARTS = {}


def build():
    PARTS.update({"P1-304-101": p101_seat(), "P1-304-102": p102_upstand(), "P1-304-103": p103_skirt(), "P1-304-104": p104_tabs(),
                  "P1-304-201": p201_shell(), "P1-304-202": p202_topfl(), "P1-304-203": p203_bars(), "P1-304-204": p204_ledge(),
                  "P1-304-205": p205_brackets(), "P1-304-206": p206_vbracket(), "P1-304-207": p207_lplates(),
                  "P1-304-301": p301_lid(), "P1-304-302": p302_ferrules(), "P1-304-303": p303_pads(), "P1-304-304": p304_ktabs(),
                  "P1-304-401": p401_upper(), "P1-304-402": p402_lower(), "P1-304-403": p403_cloth()})
    return PARTS


GROUP = {"P1-304-100": ["P1-304-101", "P1-304-102", "P1-304-103", "P1-304-104"],
         "P1-304-200": ["P1-304-201", "P1-304-202", "P1-304-203", "P1-304-204", "P1-304-205", "P1-304-206", "P1-304-207"],
         "P1-304-300": ["P1-304-301", "P1-304-302", "P1-304-303", "P1-304-304"],
         "P1-304-400": ["P1-304-401", "P1-304-402", "P1-304-403"]}

if __name__ == "__main__":
    P = build()
    masses = {}
    asm = cq.Assembly(name="P1-304")
    col_ss, col_b = cq.Color(0.78, 0.80, 0.83), cq.Color(0.20, 0.32, 0.55)
    for g, ids in GROUP.items():
        sub = cq.Assembly(name=g)
        for pid in ids:
            s = P[pid]
            masses[pid] = round(s.val().Volume() * RHO * (0.33 if pid == "P1-304-403" else 1.0), 3)   # cloth: 52 % open, round wire
            cq.exporters.export(s, str(OUT / f"{pid}.step"))
            sub.add(s, name=pid, color=col_ss)
        asm.add(sub, name=g)
    cols = {"P1-341": cq.Color(0.1, 0.1, 0.1), "P1-307": cq.Color(0.6, 0.1, 0.1), "P1-344": cq.Color(0.9, 0.9, 0.85)}
    for k, s in bought().items():
        asm.add(s, name=k, color=cols.get(k, col_b))
    asm.save(str(OUT / "P1-304-ASM.step"))
    asm.save(str(OUT / "P1-304-ASM.glb"), exportType="GLTF", tolerance=0.2, angularTolerance=0.15)
    (OUT / "masses.json").write_text(json.dumps(masses, indent=1))
    body = sum(v for k, v in masses.items() if k[:9] in ("P1-304-20",))
    print(masses, round(sum(masses.values()), 2), "kg made parts; body", round(body, 2))
