"""Generates design/: CAD (STEP+STL), dimensioned 3-view part drawings (SVG, third-angle),
assembly drawing, joint section, and wiring schematics.  python -m arm.drawings"""
import json, math, shutil, sys
from html import escape
from pathlib import Path
import cadquery as cq
from cadquery.occ_impl.exporters.svg import getSVG
from . import hardware as H, build as B, design as D
from .actuators import BY_KEY
import pipeline

OUT = pipeline.HERE / "design"
SHEET_W, SHEET_H, PXMM = 1600, 1131, 1600 / 420.0     # A3 landscape, 1:1 = 3.81 px/mm
INK, DIM = "#111", "#b00020"

def load_shape(code):
    ns = {"cq": cq, "math": math}
    exec("import math\n" + code, ns)
    return ns["result"]

def view_svg(shape, direction, scale):
    shape = shape.val() if hasattr(shape, "val") else shape
    """Render a view at an exact px/mm scale; returns (inner_svg, w_px, h_px)."""
    probe = getSVG(shape, {"projectionDir": direction, "width": 1000, "height": None, "marginLeft": 0, "marginTop": 0,
                           "showAxes": False, "showHidden": False})
    import re
    us = float(re.search(r"scale\(([\d.eE+-]+),", probe).group(1))
    w_mm = float(re.search(r'width="([\d.]+)"', probe).group(1)) / us
    w_px = w_mm * scale
    svg = getSVG(shape, {"projectionDir": direction, "width": w_px, "height": None, "marginLeft": 0, "marginTop": 0,
                         "showAxes": False, "showHidden": True, "strokeWidth": 0.9 / scale * 1.0})
    h_px = float(re.search(r'height="([\d.]+)"', svg).group(1))
    svg = re.sub(r"<\?xml.*?\?>", "", svg)
    return svg, w_px, h_px

def hdim(x1, x2, y, label, off=0):
    return (f'<g stroke="{DIM}" fill="{DIM}" stroke-width="1"><line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/>'
            f'<line x1="{x1}" y1="{y-6}" x2="{x1}" y2="{y+6}"/><line x1="{x2}" y1="{y-6}" x2="{x2}" y2="{y+6}"/>'
            f'<text x="{(x1+x2)/2}" y="{y-5}" font-size="13" text-anchor="middle" stroke="none">{label}</text></g>')

def vdim(x, y1, y2, label):
    return (f'<g stroke="{DIM}" fill="{DIM}" stroke-width="1"><line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}"/>'
            f'<line x1="{x-6}" y1="{y1}" x2="{x+6}" y2="{y1}"/><line x1="{x-6}" y1="{y2}" x2="{x+6}" y2="{y2}"/>'
            f'<text x="{x-8}" y="{(y1+y2)/2}" font-size="13" text-anchor="end" stroke="none">{label}</text></g>')

def sheet(title, partno, body, notes, scale_txt, rev="A"):
    nl = "".join(f'<text x="1170" y="{935 + 15*i}" font-size="10.5">{escape(n)}</text>' for i, n in enumerate(notes))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W}" height="{SHEET_H}" viewBox="0 0 {SHEET_W} {SHEET_H}" font-family="Helvetica,Arial,sans-serif">
<rect width="100%" height="100%" fill="#fff"/><rect x="20" y="20" width="{SHEET_W-40}" height="{SHEET_H-40}" fill="none" stroke="{INK}" stroke-width="2"/>
{body}
<g stroke="{INK}" fill="none"><rect x="1160" y="900" width="420" height="211"/><line x1="1160" y1="1040" x2="1580" y2="1040"/><line x1="1460" y1="1040" x2="1460" y2="1111"/></g>
<g fill="{INK}"><text x="1172" y="1064" font-size="16" font-weight="bold">{title}</text><text x="1172" y="1090" font-size="12">PART {partno}</text>
<text x="1472" y="1064" font-size="12">SCALE {scale_txt}</text><text x="1382" y="1090" font-size="11">REV {rev} DRAFT | mm | A3</text>
<text x="1172" y="920" font-size="13" font-weight="bold">NOTES</text>{nl}</g></svg>'''

def part_drawing(name, code, qty, note):
    shape = load_shape(code)
    bb = shape.val().BoundingBox()
    X, Y, Z = bb.xlen, bb.ylen, bb.zlen
    n = next(n for n in (1, 1.5, 2, 2.5, 3, 4, 5, 8) if (X + Y) * PXMM / n <= 640 and (X + Z) * PXMM / n <= 1000)
    S = PXMM / n
    sv = shape.val()
    front, fw, fh = view_svg(sv.rotate((0, 0, 0), (1, 0, 0), -90), (0, 0, 1), S)   # x right, z up
    top, tw, th = view_svg(sv, (0, 0, 1), S)                                                                           # x right, y up
    side, sw, sh = view_svg(sv.rotate((0, 0, 0), (1, 1, 1), -120), (0, 0, 1), S)   # y right, z up
    ox, oy = 110, 90
    tx, ty = ox, oy + fh + 90
    sx = ox + max(fw, tw) + 140
    body = (f'<g transform="translate({ox},{oy})">{front}</g><g transform="translate({tx},{ty})">{top}</g>'
            f'<g transform="translate({sx},{oy})">{side}</g>')
    body += hdim(ox, ox + fw, oy - 20, f"{fw/S:.1f}") + vdim(ox - 30, oy, oy + fh, f"{fh/S:.1f}")
    body += hdim(tx, tx + tw, ty + th + 30, f"{tw/S:.1f}") + vdim(tx - 30, ty, ty + th, f"{th/S:.1f}")
    body += hdim(sx, sx + sw, oy - 20, f"{sw/S:.1f}") + vdim(sx + sw + 30, oy, oy + sh, f"{sh/S:.1f}")
    body += (f'<text x="{ox}" y="{oy-45}" font-size="12">FRONT</text><text x="{tx}" y="{ty-12}" font-size="12">TOP</text>'
             f'<text x="{sx}" y="{oy-45}" font-size="12">RIGHT</text>')
    notes = [f"Qty {qty}: {note}"[:78], f"Overall {X:.1f} x {Y:.1f} x {Z:.1f} mm, {shape.val().Volume()/1000:.1f} cm3",
             "Material: PETG/ASA/nylon-CF, 5 perimeters, 40% infill", "Holes: M5 clearance 5.5, M3 3.2-3.4; ream after print",
             "Tol +-0.2 mm. DRAFT: verify MEASURE dims vs purchased parts", "Dashed = hidden edges. Views: front/top/right."]
    return sheet(name.upper().replace("_", " "), name, body, notes, f"1:{n:g}"), shape

# ---------- assembly drawing ----------
def assembly_svg(d):
    l1, l2 = d["l1_mm"], d["l2_mm"]
    s = 0.88   # px per mm
    x0, y0 = 200, 640                       # base axis at x0, base top at y0
    sh = (x0, y0 - 150 * s)                 # shoulder axis (riser ~150 above base plate)
    el = (sh[0] + l1 * s, sh[1]); wr = (el[0] + l2 * s, el[1]); tip = (wr[0] + 200 * s, wr[1])
    def j(p, lab):
        return (f'<circle cx="{p[0]}" cy="{p[1]}" r="14" fill="#fff" stroke="{INK}" stroke-width="2"/><circle cx="{p[0]}" cy="{p[1]}" r="3" fill="{INK}"/>'
                f'<text x="{p[0]}" y="{p[1]-44}" font-size="14" text-anchor="middle" font-weight="bold">{lab}</text>')
    body = f'''<rect x="{x0-110}" y="{y0}" width="220" height="26" fill="#ddd" stroke="{INK}"/><text x="{x0}" y="{y0+44}" font-size="12" text-anchor="middle">BASE BOARD 18x18 in + TURNTABLE (yaw J1)</text>
<rect x="{x0-50}" y="{y0-12}" width="100" height="12" fill="#bbb" stroke="{INK}"/>
<rect x="{x0-19*s}" y="{sh[1]}" width="{38*s}" height="{150*s-12}" fill="#e8e8e8" stroke="{INK}"/><text x="{x0+30}" y="{y0-60}" font-size="12">RISER TUBE ~150</text>
<rect x="{sh[0]}" y="{sh[1]-19*s}" width="{l1*s}" height="{38*s}" fill="#e8e8e8" stroke="{INK}"/>
<rect x="{el[0]}" y="{el[1]-19*s}" width="{l2*s}" height="{38*s}" fill="#e8e8e8" stroke="{INK}"/>
<rect x="{wr[0]}" y="{wr[1]-30}" width="{200*s}" height="60" fill="#cfd8dc" stroke="{INK}"/><text x="{(wr[0]+tip[0])/2}" y="{wr[1]+4}" font-size="12" text-anchor="middle">GRIPPER</text>
{j(sh,"J2 SHOULDER")}{j(el,"J3 ELBOW")}{j(wr,"J4 WRIST")}
<line x1="{tip[0]}" y1="{tip[1]-50}" x2="{tip[0]}" y2="{tip[1]+50}" stroke="{INK}" stroke-dasharray="6,4"/>'''
    body += hdim(x0, tip[0], y0 + 110, f"{(tip[0]-x0)/s:.0f} mm  ({(tip[0]-x0)/s/25.4:.1f} in)  base axis to fingertip  (max 1219 mm / 48 in)")
    body += hdim(sh[0], el[0], sh[1] - 130, f"{l1} (joint-to-joint)") + hdim(el[0], wr[0], el[1] - 130, f"{l2} (joint-to-joint)")
    body += hdim(wr[0], tip[0], wr[1] - 130, "200 tool")
    body += vdim(x0 - 80, sh[1], y0, "150 riser")
    pay = f'<line x1="{tip[0]}" y1="{tip[1]+50}" x2="{tip[0]}" y2="{tip[1]+110}" stroke="{INK}"/><rect x="{tip[0]-22}" y="{tip[1]+110}" width="44" height="30" fill="#ffd54f" stroke="{INK}"/><text x="{tip[0]}" y="{tip[1]+130}" font-size="12" text-anchor="middle">5 lb</text>'
    notes = [f"Drives: shoulder {d['joints']['shoulder']['drive']} ({d['joints']['shoulder']['required_nm']} N·m req)",
             f"elbow {d['joints']['elbow']['drive']} ({d['joints']['elbow']['required_nm']} N·m req), wrist {d['joints']['wrist']['drive']}",
             "Tube: 1.5 in OD x 0.065 in wall 6061 aluminium", f"Tube cut lengths: {l1-55} mm, {l2-55} mm", "Pose shown: fully extended horizontal (worst-case torque)"]
    return sheet("ARM ASSEMBLY - ELEVATION", "ASM-001", body + pay, notes, "NTS")

def joint_section_svg():
    """Schematic section through a pitch joint along the shaft axis (not to scale)."""
    def box(x, y, w, h, f, lab, fs=12):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{f}" stroke="{INK}"/>'
                f'<text x="{x+w/2}" y="{y+h/2+4}" font-size="{fs}" text-anchor="middle">{lab}</text>')
    b = box(60, 330, 1020, 14, "#444", "").replace("fill=\"#444\"", "fill=\"#444\"")
    body = f'<rect x="130" y="320" width="780" height="34" fill="#444" stroke="{INK}"/><text x="520" y="342" font-size="13" fill="#fff" text-anchor="middle">12 mm JOINT SHAFT</text>'
    body += box(160, 180, 40, 280, "#cfd8dc", "")
    body += f'<text x="180" y="170" font-size="12" text-anchor="middle">MOTOR CHEEK (12)</text>'
    body += box(700, 180, 40, 280, "#cfd8dc", "") + f'<text x="720" y="170" font-size="12" text-anchor="middle">PLAIN CHEEK (12)</text>'
    body += box(200, 230, 500, 180, "#f5f5f5", "") + f'<text x="545" y="262" font-size="12" text-anchor="middle">TUBE BLOCK 56 wide, M5 x4 to cheeks</text>'
    body += box(165, 300, 30, 80, "#90a4ae", "6001") + box(705, 300, 30, 80, "#90a4ae", "6001")
    body += box(300, 200, 90, 260, "#a5d6a7", "") + f'<text x="345" y="195" font-size="12" text-anchor="middle">LARGE HTD PULLEY</text>'
    body += box(395, 300, 14, 80, "#ffcc80", "") + f'<text x="402" y="478" font-size="11" text-anchor="middle">shaft collar</text>'
    body += box(740, 300, 70, 80, "#ffab91", "") + f'<text x="775" y="404" font-size="11" text-anchor="middle">CLAMP HUB</text>'
    body += box(810, 250, 40, 180, "#cfd8dc", "") + f'<text x="830" y="240" font-size="12" text-anchor="middle">TUBE SOCKET</text>'
    body += box(60, 250, 100, 180, "#b0bec5", "") + f'<text x="110" y="244" font-size="12" text-anchor="middle">GEARMOTOR</text>'
    body += f'<text x="520" y="90" font-size="16" font-weight="bold">Pitch-joint section (schematic, not to scale)</text>'
    body += f'<text x="520" y="115" font-size="12">Motor output shaft passes through the motor cheek; small HTD pulley sits in the cavity and drives the large pulley by belt.</text>'
    notes = ["Load path: link > socket > hub > shaft > 2x 6001 > cheeks > block",
             "Belt tension via slotted motor holes", "Repeats: shoulder 5:1, elbow 3:1, wrist 1:1"]
    return sheet("PITCH JOINT - SECTION", "ASM-002", body, notes, "NTS")

# ---------- wiring ----------
def wiring_svg():
    def blk(x, y, w, h, title, lines, fill="#e3f2fd"):
        t = "".join(f'<text x="{x+8}" y="{y+40+15*i}" font-size="11">{escape(l)}</text>' for i, l in enumerate(lines))
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{INK}" stroke-width="1.5"/><text x="{x+8}" y="{y+18}" font-size="14" font-weight="bold">{escape(title)}</text>{t}'
    def wire(pts, color, label=None, w=2):
        d = " ".join(("M" if i == 0 else "L") + f"{x},{y}" for i, (x, y) in enumerate(pts))
        t = f'<text x="{pts[0][0]+4}" y="{pts[0][1]-4}" font-size="10" fill="{color}">{label}</text>' if label else ""
        return f'<path d="{d}" stroke="{color}" stroke-width="{w}" fill="none"/>{t}'
    b = ""
    b += blk(40, 80, 210, 90, "24 V PSU 15 A", ["mains via IEC inlet + switch", "V+ -> fuse;  V- -> GND bus", "Earth to chassis"], "#fff3e0")
    b += blk(60, 220, 110, 60, "FUSE 20 A", ["inline, on V+"], "#ffebee")
    b += blk(60, 330, 130, 70, "E-STOP (NC)", ["in series with V+", "cuts all driver power"], "#ffcdd2")
    b += blk(380, 60, 230, 150, "ARDUINO MEGA 2560", ["STEP: D2 D3 D4 D5 D6", "DIR : D7 D8 D9 D10 D11", "ENA : D12 (all drivers)", "LIMIT: D22..D26 -> GND", "5V -> PUL+/DIR+/ENA+ (common)", "USB -> PC (115200)"], "#e8f5e9")
    names = [("J1 YAW", "NEMA23 20:1"), ("J2 SHOULDER", "NEMA23 20:1 + 5:1 belt"), ("J3 ELBOW", "NEMA23 20:1 + 3:1 belt"), ("J4 WRIST", "NEMA23 20:1 + 1:1 belt"), ("J5 GRIPPER", "NEMA17 + T8 screw")]
    drv = ["DM542", "DM542", "DM542", "DM542", "TB6600/DM542"]
    for i, ((n, m), dv) in enumerate(zip(names, drv)):
        y = 60 + i * 150
        b += blk(780, y, 150, 120, f"DRIVER {i}  {dv.split(chr(47))[0]}", ["PUL+ DIR+ ENA+ <- 5V", f"PUL- <- D{2+i}", f"DIR- <- D{7+i}", "ENA- <- D12", "VCC GND <- 24V"], "#f3e5f5")
        b += blk(1100, y, 220, 120, f"{n}", [m, "A+ A- B+ B- (twisted pair)", f"limit switch NC -> D{22+i}", "CH %d in firmware" % i], "#e0f7fa")
        b += wire([(930, y + 55), (1100, y + 55)], "#6a1b9a", "A+/A-/B+/B-")
        b += wire([(610, 100 + i * 12), (700, 100 + i * 12), (700, y + 50), (780, y + 50)], "#1565c0")
        b += wire([(780, y + 100), (740, y + 100), (740, 790)], "#d84315")
        b += wire([(780, y + 110), (760, y + 110), (760, 880)], "#212121", None, 1.5)
    b += wire([(230, 125), (290, 125), (290, 250), (170, 250)], "#d84315", "V+ 24 V", 3)
    b += wire([(115, 280), (115, 330)], "#d84315", "", 3)
    b += wire([(190, 365), (330, 365), (330, 840), (740, 840)], "#d84315", "V+ -> drivers", 3)
    b += wire([(740, 790), (740, 840)], "#d84315", "", 3)
    b += wire([(145, 170), (145, 190), (30, 190), (30, 880), (1000, 880)], "#212121", "GND bus (PSU V-, driver GND)", 3)
    leg = ["Legend: red = 24 V power (14 AWG); black = GND; blue = Mega signals (22 AWG); purple = motor phases (twisted/shielded).",
           "Common-anode: Mega 5 V to PUL+/DIR+/ENA+; Mega pins sink to PUL-/DIR-/ENA-.",
           "Driver DIP: current per motor (NEMA23 about 3.0 A peak, NEMA17 about 1.5 A), 800 pulses/rev.",
           "E-stop: cut 24 V; also wire a 2nd NC contact so D12 (ENA) goes high on E-stop.",
           "Limit switches: COM to GND, NC to D22..D26 (INPUT_PULLUP); 100 nF across each; keep away from motor leads.",
           "Tie GND once at the PSU V- bus (Mega signal GND via driver signal side only)."]
    for k, t in enumerate(leg):
        b += f'<text x="60" y="{915 + 18*k}" font-size="12">{escape(t)}</text>'
    notes = ["DRAFT schematic. Verify driver terminal names on your exact boards.", "Never connect/disconnect motors with power on", "Fuse + E-stop on the 24 V feed"]
    return sheet("WIRING SCHEMATIC", "ELE-001", b, notes, "NTS")

def main():
    d = json.loads((pipeline.HERE / "out" / "arm" / "design.json").read_text()) if (pipeline.HERE / "out/arm/design.json").exists() else B.build()
    for sub in ("cad/step", "cad/stl", "drawings", "schematics"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    ratios = {j: round(BY_KEY[v["drive"]].ratio / 20) if BY_KEY[v["drive"]].ratio >= 20 else 1 for j, v in d["joints"].items() if j != "wrist"}
    for name, (code, qty, note) in H.parts(ratios).items():
        svg, shape = part_drawing(name, code, qty, note)
        (OUT / "drawings" / f"{name}.svg").write_text(svg)
        cq.exporters.export(shape, str(OUT / "cad/step" / f"{name}.step"))
        cq.exporters.export(shape, str(OUT / "cad/stl" / f"{name}.stl"), tolerance=0.02, angularTolerance=0.1)
    (OUT / "drawings" / "ASM-001_assembly.svg").write_text(assembly_svg(d))
    (OUT / "drawings" / "ASM-002_joint_section.svg").write_text(joint_section_svg())
    (OUT / "schematics" / "ELE-001_wiring.svg").write_text(wiring_svg())
    shutil.copy(pipeline.HERE / "out/arm/BOM.md", OUT / "BOM.md")
    shutil.copy(pipeline.HERE / "out/arm/design.json", OUT / "design.json")
    print("wrote", OUT)

if __name__ == "__main__":
    main()
