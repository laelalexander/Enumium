"""AON-1 3D model from design/design.py.

Made parts get their own STEP (cad/step/<id>.step) and STL; the assembly goes to cad/AON-1-ASM.step and cad/AON-1-ASM.glb
(Y-up for the Anatomy viewer). Structure masses (kg) go to cad/masses.json; assembly.json drives the viewer's Assemble button.
Boards are modelled as envelopes with their mounting holes and tallest parts until the KiCad boards exist (their STEP replaces them).
"""
import json
import math
import pathlib
import sys

import cadquery as cq

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "design"))
import design as D  # noqa: E402

OUT = HERE
(OUT / "step").mkdir(exist_ok=True); (OUT / "stl").mkdir(exist_ok=True)
RHO_AL = 2.70e-6   # kg/mm3 6061-T6
E, H, RI, L = D.ENV, D.HALF, D.RI, D.ENV["L"]
FR, T = D.FR, D.FR["t"]
X0, X1 = FR["bar_x0"], FR["bar_x1"]
B0 = FR["blk0"]
HP = D.BRD["hp"]
CORNERS = [(1, 1), (-1, 1), (-1, -1), (1, -1)]


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_z(r, x, y, z0, z1):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def cyl_x(r, y, z, x0, x1):
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)


def cyl_y(r, x, z, y0, y1):
    return cq.Workplane("XZ").workplane(offset=-y0).center(x, z).circle(r).extrude(-(y1 - y0))


def csk_x(sx, y, z):
    """countersunk M2.5 through the rail along X (outer face at x = sx*50), into the Y bar end."""
    r, rh = D.RAIL_SCREW["d"] / 2 + 0.15, D.RAIL_SCREW["csk_d"] / 2
    x_out = sx * H
    hole = cyl_x(r, y, z, min(x_out, sx * RI) - 0.01, max(x_out, sx * RI) + 0.01)
    cone = cq.Solid.makeCone(rh, 0.01, rh, cq.Vector(x_out, y, z), cq.Vector(-sx, 0, 0))
    return hole.union(cq.Workplane(obj=cone))


def csk_y(sy, x, z):
    r, rh = D.RAIL_SCREW["d"] / 2 + 0.15, D.RAIL_SCREW["csk_d"] / 2
    y_out = sy * H
    hole = cyl_y(r, x, z, min(y_out, sy * RI) - 0.01, max(y_out, sy * RI) + 0.01)
    cone = cq.Solid.makeCone(rh, 0.01, rh, cq.Vector(x, y_out, z), cq.Vector(0, -sy, 0))
    return hole.union(cq.Workplane(obj=cone))


def frame_screw_z(i):
    zm = FR["z"][i] + T / 2
    return zm - FR["dz_screw"], zm + FR["dz_screw"]     # (screws along Y into X bars, screws along X into Y bars)


# ================================================================== 101 rail
def rail(sx, sy):
    x0, x1 = (RI, H) if sx > 0 else (-H, -RI)
    y0, y1 = (RI, H) if sy > 0 else (-H, -RI)
    r = box(x0, x1, y0, y1, 0, L)
    r = r.edges("|Z").fillet(E["rail_r"])
    bm = D.RAIL_SCREW["bar_mid"]
    for i in range(3):
        zy, zx = frame_screw_z(i)
        r = r.cut(csk_y(sy, sx * bm, zy))    # through the Y face into the X bar
        r = r.cut(csk_x(sx, sy * bm, zx))    # through the X face into the Y bar
    xc, yc = sx * (H - E["rail"] / 2), sy * (H - E["rail"] / 2)
    if sx * sy > 0:     # deployment switch lever notch at -Z, on the rail's inner Y face
        nx = sx * (X0 + 1.0)
        r = r.cut(box(min(nx, nx + sx * D.SWITCH["notch_w"]), max(nx, nx + sx * D.SWITCH["notch_w"]),
                      min(sy * RI, sy * (RI + D.SWITCH["notch_d"])), max(sy * RI, sy * (RI + D.SWITCH["notch_d"])), -0.01, D.SWITCH["notch_h"]))
    else:               # separation spring plunger bore at +Z
        r = r.cut(cyl_z(1.25, xc, yc, L - D.SPRING["depth"], L + 0.01))
    return r


def rail_variant(sx, sy):
    return "AON-101" if sx * sy > 0 else "AON-102"


# ================================================================== frames 103 (-Z), 104 (mid), 105 (+Z)
def frame(i):
    z0, z1 = FR["z"][i], FR["z"][i] + T
    f = None
    for s in (1, -1):
        bx = box(min(s * X0, s * X1), max(s * X0, s * X1), -RI, RI, z0, z1)       # X bars
        by = box(-RI, RI, min(s * X0, s * X1), max(s * X0, s * X1), z0, z1)       # Y bars
        f = bx.union(by) if f is None else f.union(bx).union(by)
    R = FR["relief"]
    for sx, sy in CORNERS:   # corner block joins the X and Y bars; a relief square clears the rail's inner edge
        blk = box(min(sx * B0, sx * X0), max(sx * B0, sx * X0), min(sy * B0, sy * X0), max(sy * B0, sy * X0), z0, z1)
        blk = blk.cut(box(min(sx * (X0 - R), sx * X0), max(sx * (X0 - R), sx * X0), min(sy * (X0 - R), sy * X0), max(sy * (X0 - R), sy * X0), z0 - 1, z1 + 1))
        f = f.union(blk)
    zy, zx = frame_screw_z(i)
    bm = D.RAIL_SCREW["bar_mid"]
    for s in (1, -1):    # tapped M2.5 x 8 in the bar ends (modelled as Ø2.05 tap drill)
        f = f.cut(cyl_y(1.025, s * bm, zy, RI - D.RAIL_SCREW["tap_depth"], RI + 0.01)).cut(cyl_y(1.025, s * bm, zy, -RI - 0.01, -RI + D.RAIL_SCREW["tap_depth"]))
        f = f.cut(cyl_x(1.025, s * bm, zx, RI - D.RAIL_SCREW["tap_depth"], RI + 0.01)).cut(cyl_x(1.025, s * bm, zx, -RI - 0.01, -RI + D.RAIL_SCREW["tap_depth"]))
    zc = (z0 + z1) / 2
    for sx, sy in CORNERS:   # stack rod holes
        if i == 0:
            f = f.cut(cyl_z(1.25, sx * HP, sy * HP, z0 - 0.01, z1 + 0.01))      # M3 tapped THRU (Ø2.5 tap drill)
        else:
            f = f.cut(cyl_z(1.7, sx * HP, sy * HP, z0 - 0.01, z1 + 0.01))       # Ø3.4 clearance
    if i in (0, 2):  # panel screws M2 tapped 6 deep in the bar outer faces
        for s in (1, -1):
            for yy in (-D.PANEL["hole_y"], D.PANEL["hole_y"]):
                f = f.cut(cyl_x(0.8, yy, zc, s * X1 - (6.0 if s > 0 else -6.0) * 1, s * X1) if s > 0 else cyl_x(0.8, yy, zc, -X1, -X1 + 6.0))
                f = f.cut(cyl_y(0.8, yy, zc, X1 - 6.0, X1) if s > 0 else cyl_y(0.8, yy, zc, -X1, -X1 + 6.0))
    if i == 0:       # switch bracket: 2 x M2 tapped 5 deep on the underside of the +X and -X bars
        for sx, sy in ((1, 1), (-1, -1)):
            for yy in D.SWITCH["tap_y"]:
                f = f.cut(cyl_z(0.8, sx * (X0 + X1) / 2, sy * yy, z0 - 0.01, z0 + 5.0))
    return f


# ================================================================== boards and bought parts (envelopes)
def board(z, w=D.BRD["w"], t=D.BRD["t"], ch=D.BRD["corner_ch"], holes=True):
    h = w / 2
    pts = [(-h + ch, -h), (h - ch, -h), (h, -h + ch), (h, h - ch), (h - ch, h), (-h + ch, h), (-h, h - ch), (-h, -h + ch)]
    b = cq.Workplane("XY").workplane(offset=z).polyline(pts).close().extrude(t)
    if holes:
        for sx, sy in CORNERS:
            b = b.cut(cyl_z(D.BRD["hole"] / 2, sx * HP, sy * HP, z - 0.1, z + t + 0.1))
    return b


def panel(face):
    """face: '+X','-X','+Y','-Y'. Panel PCB 82 wide on the bar faces, with 7 cells."""
    P = D.PANEL
    w, t = P["w"], P["t"]
    p = box(X1, X1 + t, -w / 2, w / 2, P["z0"], P["z1"])
    for zz in (FR["z"][0] + T / 2, FR["z"][2] + T / 2):
        for yy in (-P["hole_y"], P["hole_y"]):
            p = p.cut(cyl_x(P["hole_d"] / 2, yy, zz, X1 - 0.1, X1 + t + 0.1))
    cells = None
    C = D.CELL
    for k in range(C["n_per_face"]):
        z = D.CELL_Z0 + k * (C["w"] + D.GAP_CELL)
        c = box(X1 + t, X1 + t + C["t"], -C["l"] / 2, C["l"] / 2, z, z + C["w"])
        cells = c if cells is None else cells.union(c)
    rot = {"+X": 0, "+Y": 90, "-X": 180, "-Y": 270}[face]
    return p.rotate((0, 0, 0), (0, 0, 1), rot), cells.rotate((0, 0, 0), (0, 0, 1), rot)


def battery_pack(z):
    b = board(z)
    cells = None
    for yy in (-19.5, 19.5):
        for zz in (z + 1.6 + 9.6, z + 1.6 + 9.6 + 19.6):
            c = cq.Workplane("YZ").workplane(offset=-32.5).center(yy, zz).circle(9.2).extrude(65.0)
            cells = c if cells is None else cells.union(c)
    holder = box(-36, 36, -39.5, 39.5, z + 1.6, z + 1.6 + 2.0)
    return b, cells, holder


def pcba(z, h, parts):
    b = board(z)
    comp = None
    for (x0, x1, y0, y1, hh) in parts:
        c = box(x0, x1, y0, y1, z + 1.6, z + 1.6 + min(hh, h))
        comp = c if comp is None else comp.union(c)
    return b, comp


def rods_spacers():
    rods, sp = None, None
    for sx, sy in CORNERS:
        r = cyl_z(1.5, sx * HP, sy * HP, D.ROD["z0"], D.ROD["z1"])
        rods = r if rods is None else rods.union(r)
    # spacers fill every gap between solid layers along the rods: frames and boards
    solids = sorted([(FR["z"][i], FR["z"][i] + T) for i in range(3)] + [(z, z + D.BRD["t"]) for _, _, z, _ in D.STACK])
    seg = [(a[1], b[0]) for a, b in zip(solids, solids[1:])]
    for z0, z1 in seg:
        if z1 - z0 < 0.5:
            continue
        for sx, sy in CORNERS:
            s = cyl_z(2.75, sx * HP, sy * HP, z0, z1).cut(cyl_z(1.6, sx * HP, sy * HP, z0 - 0.1, z1 + 0.1))
            sp = s if sp is None else sp.union(s)
    return rods, sp, seg


def antenna_board():
    z = FR["z"][2] + T + 5.0
    b = board(z)
    elems = None
    for s in (1, -1):    # 2 tape-spring elements wrapped round the board edge (stowed), on standoffs above the board
        e = box(-34.0, 34.0, min(s * 39.0, s * 26.3), max(s * 39.0, s * 26.3), z + 1.6 + 0.4, z + 1.6 + 0.9)   # tape lies flat, wound, under the restraint line
        elems = e if elems is None else elems.union(e)
    so = None
    for sx, sy in CORNERS:
        c = cyl_z(2.75, sx * HP, sy * HP, FR["z"][2] + T, z).cut(cyl_z(1.5, sx * HP, sy * HP, FR["z"][2] + T - 1, z + 1))
        so = c if so is None else so.union(c)
    return b, elems, so


def end_board():
    z = FR["z"][0] - 1.6
    b = board(z)
    coil = cq.Workplane("XY").workplane(offset=z - 2.5).rect(66, 66).rect(54, 54).extrude(2.5)     # Z air coil bonded under E07
    nuts = None
    for sx, sy in CORNERS:
        n = cq.Workplane("XY").workplane(offset=z - 1.8).center(sx * HP, sy * HP).polygon(6, 5.5 / math.cos(math.pi / 6)).extrude(1.8)
        nuts = n if nuts is None else nuts.union(n)
    return b, coil, nuts


def bracket(sx, sy):
    """AON-106: 1.0 mm L bracket. Flange under the X bar (y 14-26), leg in the plane x = 41.1-42.1 (y 14-40) carrying the switch."""
    S = D.SWITCH
    z0 = FR["z"][0]
    lx0, lx1 = S["leg_x"], S["leg_x"] + S["t"]
    leg = box(lx0, lx1, 14.0, 40.0, 0.3, z0)
    fl = box(lx1, X1, 14.0, 26.0, z0 - S["t"], z0)
    b = leg.union(fl)
    for yy in S["tap_y"]:
        b = b.cut(cyl_z(1.1, (X0 + X1) / 2, yy, z0 - 2, z0 + 1))
    for yy in (30.0, 36.5):
        b = b.cut(cyl_x(1.1, yy, 3.0, lx0 - 1, lx1 + 1))
    b = b.rotate((0, 0, 0), (0, 0, 1), 0 if sx > 0 else 180)
    return b


def switches():
    sw = None
    S = D.SWITCH
    for sx, sy in ((1, 1), (-1, -1)):
        lx1 = S["leg_x"] + S["t"]
        body = box(lx1, lx1 + S["body"][2], 27.2, 40.0, 0.3, 0.3 + S["body"][0])
        lev = box(X0 + 1.0, X0 + 3.0, 39.0, RI + 4.0, -S["protrude"], 1.0)
        u = body.union(lev).rotate((0, 0, 0), (0, 0, 1), 0 if sx > 0 else 180)
        sw = u if sw is None else sw.union(u)
    return sw


def plungers():
    p = None
    for sx, sy in ((1, -1), (-1, 1)):
        xc, yc = sx * (H - E["rail"] / 2), sy * (H - E["rail"] / 2)
        c = cyl_z(1.5, xc, yc, L - D.SPRING["depth"], L).union(cyl_z(1.2, xc, yc, L, L + D.SPRING["protrude"]))
        p = c if p is None else p.union(c)
    return p


# ================================================================== build
def main():
    made, parts, masses = {}, [], {}
    rails = {}
    for sx, sy in CORNERS:
        rails[(sx, sy)] = rail(sx, sy)
    made["AON-101"] = rails[(1, 1)]; made["AON-102"] = rails[(1, -1)]
    frames = [frame(i) for i in range(3)]
    made["AON-103"], made["AON-104"], made["AON-105"] = frames
    made["AON-106"] = bracket(1, 1)
    for pid, s in made.items():
        cq.exporters.export(s, str(OUT / "step" / f"{pid}.step"))
        cq.exporters.export(s, str(OUT / "stl" / f"{pid}.stl"), tolerance=0.02, angularTolerance=0.1)
        masses[pid] = s.val().Volume() * RHO_AL
    qty = {"AON-101": 2, "AON-102": 2, "AON-103": 1, "AON-104": 1, "AON-105": 1, "AON-106": 2}
    struct_kg = sum(masses[p] * q for p, q in qty.items())

    A = cq.Assembly(name="AON-1")
    AL, ANOD, FR4, CELLC, GOLD, BAT, TI, BLK = (cq.Color(0.80, 0.81, 0.83), cq.Color(0.55, 0.56, 0.60), cq.Color(0.10, 0.38, 0.20), cq.Color(0.10, 0.14, 0.42),
                                                 cq.Color(0.85, 0.65, 0.20), cq.Color(0.20, 0.45, 0.75), cq.Color(0.6, 0.6, 0.65), cq.Color(0.12, 0.12, 0.12))
    steps = []

    def add(obj, name, color, step, pid=None):
        if obj is None:
            return
        A.add(obj, name=name, color=color)
        parts.append(dict(name=name, pid=pid or name, step=step))

    # step 1: -Z frame + E07 + switches, 2: rails, 3: lower stack, 4: mid frame, 5: upper stack, 6: +Z frame + antenna, 7: panels
    add(frames[0], "AON-103 -Z frame", AL, 1, "AON-103")
    add(switches(), "SW1-SW2 deployment switches", BLK, 1, "SW1")
    eb, coil, nuts = end_board()
    add(eb, "E07 -Z end board", FR4, 3, "E07"); add(coil, "E07 Z torquer coil", GOLD, 3, "E07"); add(nuts, "E07 nuts M3 thin (4)", TI, 3, "H3")
    add(bracket(1, 1).union(bracket(-1, -1)), "AON-106 switch brackets (2)", AL, 1, "AON-106")
    for (sx, sy), r in rails.items():
        add(r, f"{rail_variant(sx, sy)} rail {'+' if sx > 0 else '-'}X{'+' if sy > 0 else '-'}Y", ANOD, 2, rail_variant(sx, sy))
    rods, sp, seg = rods_spacers()
    b, cells, holder = battery_pack(D.STACK[0][2])
    add(b, "E02 battery board", FR4, 3, "E02"); add(cells, "E02 18650 cells (4)", BAT, 3, "BAT"); add(holder, "E02 cell holder", BLK, 3, "E02")
    b, c = pcba(D.STACK[1][2], 12, [(-30, 30, -30, 0, 8), (-35, -15, 10, 35, 12), (10, 35, 10, 35, 6)])
    add(b, "E01 EPS board", FR4, 3, "E01"); add(c, "E01 EPS parts", BLK, 3, "E01")
    b, c = pcba(D.STACK[2][2], 12, [(-12, 12, -12, 12, 2), (-35, -15, -35, -15, 6), (15, 35, -35, -10, 5), (-30, 30, 25, 35, 8)])
    add(b, "E03 OBC board", FR4, 3, "E03"); add(c, "E03 OBC parts", BLK, 3, "E03")
    add(frames[1], "AON-104 mid frame", AL, 4, "AON-104")
    b, c = pcba(D.STACK[3][2], 14, [(-32, 32, -32, 20, 9), (20, 34, 24, 34, 12)])
    add(b, "E04 COM board", FR4, 5, "E04"); add(c, "E04 COM shield can", AL, 5, "E04")
    add(rods, "Stack rods M3 Ti (4)", TI, 3, "HW-ROD"); add(sp, "Stack spacers", AL, 3, "HW-SP")
    add(frames[2], "AON-105 +Z frame", AL, 6, "AON-105")
    ab, el, so = antenna_board()
    add(ab, "E05 antenna board", FR4, 6, "E05"); add(el, "E05 UHF tape elements (stowed)", GOLD, 6, "E05"); add(so, "E05 standoffs", AL, 6, "HW-SO")
    add(plungers(), "Separation spring plungers (2)", TI, 6, "SPR")
    for f in ("+X", "-Y", "-X", "+Y"):
        p, c = panel(f)
        add(p, f"E06 solar panel {f}", FR4, 7, "E06"); add(c, f"E06 cells {f}", CELLC, 7, "E06")
    A.save(str(OUT / "AON-1-ASM.step"))
    # GLB: rotate so +Z (satellite long axis) is up in a Y-up viewer
    A.save(str(OUT / "AON-1-ASM.glb"))      # the glTF writer converts Z-up to Y-up
    for ch in A.children:
        cq.exporters.export(ch.obj, str(OUT / "stl" / f"asm_{ch.name.replace(' ', '_').replace('/', '-')}.stl"), tolerance=0.05, angularTolerance=0.2)
    titles = {1: "-Z frame, switch brackets and deployment switches", 2: "Four rails screwed to the -Z frame", 3: "Stack rods, -Z end board, spacers and the lower stack: battery, EPS, OBC",
              4: "Mid frame onto the rails", 5: "Upper stack: COM board", 6: "+Z frame, antenna board, spring plungers", 7: "Four solar panels"}
    asm = dict(units="mm", in_place=True,
               parts=[dict(file=f"cad/stl/asm_{p['name'].replace(' ', '_').replace('/', '-')}.stl", name=p["name"]) for p in parts],
               steps=[dict(n=n, title=t, add=[p["name"] for p in parts if p["step"] == n]) for n, t in titles.items()])
    (HERE.parent / "assembly.json").write_text(json.dumps(asm, indent=1))
    (OUT / "masses.json").write_text(json.dumps({k: round(v, 5) for k, v in masses.items()}, indent=1))
    (OUT / "structure_kg.json").write_text(json.dumps(dict(qty=qty, total_kg=struct_kg), indent=1))
    print("made", {k: f"{v * 1000:.1f} g" for k, v in masses.items()}, "structure", f"{struct_kg * 1000:.0f} g", "parts", len(parts), "stack gaps", [(round(a, 2), round(b, 2)) for a, b in seg])


if __name__ == "__main__":
    main()
