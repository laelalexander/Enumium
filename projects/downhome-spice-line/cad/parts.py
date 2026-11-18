"""Custom fabricated parts for the Down Home Creole plant: CAD (STEP, STL), drawings (SVG via partsheet.py)
and DXF cut files in mm and inch.

Every other item on the line is a bought catalog product (design/equipment.json). These parts exist because
nothing off the shelf joins the bought machines the way this plant needs:

  DH-101  Blender discharge transition chute, 250 mm square flange to 6 in Tri-Clamp (RB-303 -> SC-304)
  DH-102  Metal detector inlet spool, 6 in Tri-Clamp both ends with a sanitary magnet port (SC-304 -> MD-305)
  DH-103  Filler hopper dust pickup hood with 4 in duct collar (FL-403 and NW-501 hopper lids -> DC-310)
  DH-104  Container guide-rail bracket, adjustable, for 12.7 mm rail rod (CV-417, 36 per line)
  DH-105  Photo-eye mounting bracket, slotted (CV-417 sensors)
  DH-106  Flange gasket, FDA silicone 3 mm, for DH-101 top flange (cut file only)

Sanitary design rules applied (references/food-safety-design.md): product-contact parts 316L or 304 SS,
continuous welds ground flush, Ra <= 0.8 um, no threads in the product zone, no horizontal ledges outside,
every product-contact joint is a Tri-Clamp so it comes apart without tools for dry cleaning.
Mating dimensions marked "verify" must be checked against the maker's certified GA drawing before cutting.
Usage: python parts.py   (needs cadquery; ezdxf for DXF)
"""
import json, math, pathlib, sys

import cadquery as cq

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parent.parent / "skills" / "anatomy" / "tools" / "plant"))
import partsheet  # noqa: E402

IN = 25.4
TC6_FLANGE_OD = 6.565 * IN      # 6 in Tri-Clamp ferrule flange OD (BPE / 3-A dimension), 166.75 mm
TC6_TUBE_OD = 6.0 * IN          # 152.4 mm
TC4_FLANGE_OD = 4.684 * IN      # 4 in Tri-Clamp ferrule, 119.0 mm
TUBE_WALL = 0.083 * IN          # 14 ga sanitary tube, 2.11 mm
SHEET = 1.5                     # 16 ga sheet, 1.52 mm
PROJECT = "Down Home Creole dry plant"


def ferrule(od_flange, od_tube, h=28.6):
    """Tri-Clamp ferrule as a solid ring for drawing purposes (groove simplified)."""
    return (cq.Workplane("XY").circle(od_flange / 2).circle(od_tube / 2 - TUBE_WALL).extrude(h))


def dh101():
    """Square 250 mm flange (8 x M10 on 210 mm square) -> loft -> 6 in tube stub -> TC ferrule."""
    side, t_fl = 250.0, 6.0
    top = (cq.Workplane("XY").rect(side, side).extrude(t_fl)
           .faces(">Z").workplane().rect(210, 210, forConstruction=True).vertices().hole(11)
           .faces(">Z").workplane().pushPoints([(0, 105), (0, -105), (105, 0), (-105, 0)]).hole(11)
           .faces(">Z").workplane().rect(150, 150).cutThruAll())
    outer = (cq.Workplane("XY").rect(150 + 2 * SHEET, 150 + 2 * SHEET).workplane(offset=260).circle(TC6_TUBE_OD / 2).loft())
    inner = (cq.Workplane("XY").workplane(offset=-0.01).rect(150, 150).workplane(offset=260.02).circle(TC6_TUBE_OD / 2 - SHEET).loft())
    trans = outer.cut(inner).translate((0, 0, -260))
    fer = ferrule(TC6_FLANGE_OD, TC6_TUBE_OD).translate((0, 0, -260 - 28.6))
    part = top.union(trans).union(fer)
    return part.translate((0, 0, 260 + 28.6))


def dh102():
    """6 in spool 300 mm long, ferrules both ends, 2 in TC magnet port on the side at mid-length."""
    L = 300.0
    tube = cq.Workplane("XY").circle(TC6_TUBE_OD / 2).circle(TC6_TUBE_OD / 2 - TUBE_WALL).extrude(L)
    f1 = ferrule(TC6_FLANGE_OD, TC6_TUBE_OD)
    f2 = ferrule(TC6_FLANGE_OD, TC6_TUBE_OD).translate((0, 0, L - 28.6))
    port = (cq.Workplane("YZ").workplane(offset=0).center(0, L / 2).circle(2.0 * IN / 2).extrude(TC6_TUBE_OD / 2 + 60))
    port_flange = (cq.Workplane("YZ").workplane(offset=TC6_TUBE_OD / 2 + 60 - 21.5).center(0, L / 2).circle(2.516 * IN / 2).extrude(21.5))
    bore = cq.Workplane("YZ").center(0, L / 2).circle(2.0 * IN / 2 - TUBE_WALL).extrude(TC6_TUBE_OD / 2 + 61)
    body = tube.union(f1).union(f2).union(port).union(port_flange)
    body = body.cut(bore).cut(cq.Workplane("XY").circle(TC6_TUBE_OD / 2 - TUBE_WALL).extrude(L))
    return body


def dh103():
    """Dust hood 400 x 250 x 120 mm open bottom, 25 mm mounting flange with 6 x 7 mm holes, 4 in TC collar on top."""
    L, W, Hh, fl = 400.0, 250.0, 120.0, 25.0
    shell = cq.Workplane("XY").rect(L, W).extrude(Hh).faces("<Z").shell(-SHEET)
    flange = (cq.Workplane("XY").rect(L + 2 * fl, W + 2 * fl).rect(L, W).extrude(SHEET)
              .faces(">Z").workplane().pushPoints([(-(L / 2 + fl / 2), 0), (L / 2 + fl / 2, 0), (-120, W / 2 + fl / 2), (120, W / 2 + fl / 2),
                                                  (-120, -(W / 2 + fl / 2)), (120, -(W / 2 + fl / 2))]).hole(7))
    collar = cq.Workplane("XY").workplane(offset=Hh).circle(4.0 * IN / 2).circle(4.0 * IN / 2 - TUBE_WALL).extrude(60)
    cf = ferrule(TC4_FLANGE_OD, 4.0 * IN, 21.5).translate((0, 0, Hh + 60))
    top_hole = cq.Workplane("XY").workplane(offset=Hh - 5).circle(4.0 * IN / 2 - TUBE_WALL).extrude(10)
    return shell.union(flange).union(collar).union(cf).cut(top_hole)


def dh104():
    """L bracket 3 mm SS304: base 60 x 50 with 2 x slot 8.5 x 30 (M8 adjust), upright 50 x 80 with 12.9 hole for 12.7 rail rod + M6 set-screw hole."""
    t = 3.0
    base = (cq.Workplane("XY").box(60, 50, t, centered=(True, True, False))
            .faces(">Z").workplane().pushPoints([(-15, 0), (15, 0)]).slot2D(30, 8.5, 90).cutThruAll())
    up = (cq.Workplane("XZ").workplane(offset=-25).center(0, 40 + t / 2).rect(60, 80).extrude(-t)
          .faces("<Y").workplane(centerOption="CenterOfBoundBox").center(0, 20).hole(12.9))
    return base.union(up)


def dh105():
    """Flat-bar photo-eye bracket 3 mm SS304, 40 x 120, 2 x slot 6.5 x 25 + 2 x M4 clearance 4.5 for the sensor."""
    t = 3.0
    b = (cq.Workplane("XY").box(120, 40, t, centered=(True, True, False))
         .faces(">Z").workplane().pushPoints([(-38, 0)]).slot2D(25, 6.5, 0).cutThruAll()
         .faces(">Z").workplane().pushPoints([(-10, 0)]).slot2D(25, 6.5, 0).cutThruAll()
         .faces(">Z").workplane().pushPoints([(35, 12.5), (35, -12.5)]).hole(4.5))
    return b


PARTS = [
    dict(id="DH-101", fn=dh101, title="Blender discharge transition chute", material="SS 316L (contact), 304 flange", tol="sheet", density=8.0, qty="1",
         process="Laser cut, formed, TIG, ground, polished, passivated",
         assy="ASM-001 blending discharge", notes=["Inside welds ground flush, #4 polish Ra <= 0.8 um [32 uin], passivate per ASTM A967",
                                                   "Top flange bolt pattern 210 mm square: VERIFY against Ross 42N-36 discharge valve GA before cutting",
                                                   "Bottom: 6 in Tri-Clamp ferrule (BPE), clamps to SC-304 inlet with EPDM/FKM FDA gasket"],
         fasteners=lambda f: "M10 x 30 A2-70, torque 25 N·m [18 lbf·ft]" if abs(f["dia"] - 11) < 0.5 else "6 in Tri-Clamp to SC-304, FDA gasket"),
    dict(id="DH-102", fn=dh102, title="Metal detector inlet spool with magnet port", material="SS 316L tube 6 in x 14 ga", tol="metal", density=8.0, qty="1",
         process="Orbital welded, ground, Ra<=0.8 um, passivated", assy="ASM-001 blending discharge",
         notes=["Length 300 mm keeps the metal-free zone of MD-305 (1.5 x aperture): VERIFY with Safeline GA",
                "2 in Tri-Clamp side port takes a sanitary bullet magnet; clamp torque by hand, 2 in clamp"],
         fasteners=lambda f: "6 in / 2 in Tri-Clamp, FDA gasket"),
    dict(id="DH-103", fn=dh103, title="Filler hopper dust pickup hood", material="SS 304, 16 ga", tol="sheet", density=8.0, qty="2",
         process="Laser cut, brake formed, TIG welded, ground", assy="ASM-002 pack line (FL-403, NW-501)",
         notes=["Capture velocity 1.0 m/s [200 fpm] at the hopper lid opening: 250 cfm per hood (DC-310 sizing)",
                "Flange holes clear #10 / M6 self-sealing screws into the hopper lid"],
         fasteners=lambda f: "M6 x 16 A2-70 + bonded washer, 6 N·m [4.4 lbf·ft]" if abs(f["dia"] - 7) < 0.5 else ""),
    dict(id="DH-104", fn=dh104, title="Container guide-rail bracket", material="SS 304, 3 mm [11 ga]", tol="sheet", density=8.0, qty="36",
         process="Laser cut, one 90° bend, deburr, electropolish", assy="CV-417 conveyor, 36 per line A",
         notes=["Slots give ±15 mm [±.59 in] rail adjustment per container size", "Rail rod 12.7 mm [1/2 in] SS, UHMW wear strip clipped on"],
         fasteners=lambda f: ("M8 x 20 A2-70 + washer, 18 N·m [13 lbf·ft]" if f["kind"] == "slot" else "1/2 in rail rod, slip fit; M6 set screw")),
    dict(id="DH-105", fn=dh105, title="Photo-eye mounting bracket", material="SS 304, 3 mm [11 ga]", tol="sheet", density=8.0, qty="14",
         process="Laser cut, deburr, electropolish", assy="CV-417 sensors (ELE-002 list)",
         notes=["Slots let the sensor slide 25 mm [1 in] along the conveyor"],
         fasteners=lambda f: ("M6 x 16 A2-70, 8 N·m [6 lbf·ft]" if f["kind"] == "slot" else "M4 x 25 sensor screws, 1.2 N·m")),
]


def flat_dxf(pid, path_mm, path_in):
    """2D cut files. Flat parts are the true outline; formed parts carry bend lines (layer BEND)."""
    import ezdxf
    for path, f in ((path_mm, 1.0), (path_in, 1 / IN)):
        doc = ezdxf.new("R2010"); doc.units = 4 if f == 1.0 else 1
        m = doc.modelspace()
        for name, col in (("CUT", 1), ("BEND", 3), ("TEXT", 7)):
            doc.layers.add(name, color=col)
        P = lambda pts: m.add_lwpolyline([(x * f, y * f) for x, y in pts], close=True, dxfattribs={"layer": "CUT"})
        C = lambda x, y, d: m.add_circle((x * f, y * f), d / 2 * f, dxfattribs={"layer": "CUT"})
        def S(x, y, L, w, ang):                         # obround slot centred at x, y
            r = w / 2; dx, dy = math.cos(math.radians(ang)) * (L - w) / 2, math.sin(math.radians(ang)) * (L - w) / 2
            nx, ny = -math.sin(math.radians(ang)) * r, math.cos(math.radians(ang)) * r
            m.add_line(((x - dx + nx) * f, (y - dy + ny) * f), ((x + dx + nx) * f, (y + dy + ny) * f), dxfattribs={"layer": "CUT"})
            m.add_line(((x - dx - nx) * f, (y - dy - ny) * f), ((x + dx - nx) * f, (y + dy - ny) * f), dxfattribs={"layer": "CUT"})
            a0 = ang + 90
            m.add_arc(((x + dx) * f, (y + dy) * f), r * f, a0 - 180, a0, dxfattribs={"layer": "CUT"})
            m.add_arc(((x - dx) * f, (y - dy) * f), r * f, a0, a0 + 180, dxfattribs={"layer": "CUT"})
        B = lambda a, b: m.add_line((a[0] * f, a[1] * f), (b[0] * f, b[1] * f), dxfattribs={"layer": "BEND", "linetype": "DASHED"})
        T = lambda s, x, y: m.add_text(s, dxfattribs={"layer": "TEXT", "height": 4 * f}).set_placement((x * f, y * f))
        if pid == "DH-101":            # top flange plate 250 sq, 150 sq opening, 12 holes
            P([(0, 0), (250, 0), (250, 250), (0, 250)]); P([(50, 50), (200, 50), (200, 200), (50, 200)])
            for x, y in [(20, 20), (230, 20), (20, 230), (230, 230), (125, 20), (125, 230), (20, 125), (230, 125)]:
                C(x, y, 11)
            T("DH-101-1 top flange, 6 mm SS304, qty 1. Transition cone: form from STEP (fabricator unfolds).", 0, -12)
        elif pid == "DH-103":          # hood unfolded: top 400x250 + four sides 120, flange 25 shown as separate plate
            P([(0, 120), (120 + 0, 120)] and [(0, 120), (120, 120), (120, 0), (520, 0), (520, 120), (640, 120), (640, 370), (520, 370), (520, 490), (120, 490), (120, 370), (0, 370)])
            C(320, 245, 4.0 * IN - 2 * 2.11)
            for a, b in (((120, 120), (520, 120)), ((120, 370), (520, 370)), ((120, 120), (120, 370)), ((520, 120), (520, 370))):
                B(a, b)
            T("DH-103-1 hood blank, 16 ga SS304, 4 bends 90 deg up, corners welded. Bend allowance not included: K=0.33 per shop.", 0, -12)
            P([(700, 0), (1150, 0), (1150, 300), (700, 300)]); P([(725, 25), (1125, 25), (1125, 275), (725, 275)])
            for x, y in [(712.5, 150), (1137.5, 150), (805, 12.5), (1045, 12.5), (805, 287.5), (1045, 287.5)]:
                C(x, y, 7)
            T("DH-103-2 mounting flange, 16 ga SS304", 700, -12)
        elif pid == "DH-104":          # flat blank 60 x (50 + 80 - bend), bend line at 50
            P([(0, 0), (60, 0), (60, 130), (0, 130)]); B((0, 50), (60, 50))
            S(15, 25, 30, 8.5, 90); S(45, 25, 30, 8.5, 90); C(30, 108.5, 12.9)
            T("DH-104 blank 3 mm SS304, bend 90 deg on BEND line, qty 36", 0, -10)
        elif pid == "DH-105":
            P([(0, 0), (120, 0), (120, 40), (0, 40)]); S(22, 20, 25, 6.5, 0); S(50, 20, 25, 6.5, 0); C(95, 32.5, 4.5); C(95, 7.5, 4.5)
            T("DH-105 3 mm SS304 flat, qty 14", 0, -10)
        elif pid == "DH-106":          # gasket for DH-101 top flange
            P([(0, 0), (250, 0), (250, 250), (0, 250)]); P([(50, 50), (200, 50), (200, 200), (50, 200)])
            for x, y in [(20, 20), (230, 20), (20, 230), (230, 230), (125, 20), (125, 230), (20, 125), (230, 125)]:
                C(x, y, 11)
            T("DH-106 gasket 3 mm FDA silicone (21 CFR 177.2600), white, qty 2 (1 + spare)", 0, -12)
        doc.saveas(path)


def main():
    out_cad, out_dwg, out_dxf = ROOT / "cad", ROOT / "drawings" / "parts", ROOT / "dxf"
    for d in (out_cad / "step", out_cad / "stl", out_dwg, out_dxf):
        d.mkdir(parents=True, exist_ok=True)
    summary = []
    for p in PARTS:
        shape = p["fn"]()
        cq.exporters.export(shape, str(out_cad / "step" / f"{p['id']}.step"))
        cq.exporters.export(shape, str(out_cad / "stl" / f"{p['id']}.stl"), tolerance=0.05, angularTolerance=0.1)
        info = dict(title=p["title"], partno=p["id"], material=p["material"], process=p["process"], qty=p["qty"], density=p["density"],
                    tol=p["tol"], notes=p["notes"], project=PROJECT, assy=p["assy"], qty_label="QTY PER PLANT")
        svg, feats = partsheet.sheet(shape, info, fasteners=p["fasteners"])
        (out_dwg / f"{p['id']}.svg").write_text(svg)
        bb = shape.val().BoundingBox()
        summary.append(dict(id=p["id"], title=p["title"], qty=p["qty"], material=p["material"], features=len(feats),
                            size_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)], volume_cm3=round(shape.val().Volume() / 1000, 1)))
        print(p["id"], len(feats), "features", summary[-1]["size_mm"])
    try:
        for pid in ("DH-101", "DH-103", "DH-104", "DH-105", "DH-106"):
            flat_dxf(pid, out_dxf / f"{pid}_mm.dxf", out_dxf / f"{pid}_in.dxf")
    except ImportError:
        print("ezdxf missing: DXF skipped")
    (out_cad / "parts.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
