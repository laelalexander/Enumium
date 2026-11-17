"""P1-301 agitator: weldment 200, shaft 201, ribbon flight blanks 202/203 + arms 204/205 (+ DXF)."""
import math

from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
import design as D

s5, s4, s2, s1 = SC(5), SC(4), SC(2), SC(1)
ARMS = D.arms()
for i, a in enumerate([a for a in ARMS if a["tag"] == "A"]):
    a["id"] = f"A{i + 1}"
for i, a in enumerate([a for a in ARMS if a["tag"] == "B"]):
    a["id"] = f"B{i + 1}"


def ribbon_side(v, n, z0=0.0, step=4.0):
    """front-view projection of ribbon n (x, z): band between r_i cos θ and r_o cos θ; visible where the ribbon faces the viewer (y < 0)."""
    r = RIB[n]; ro, ri = r["od"] / 2, r["od"] / 2 - r["w"]
    xs = [r["x0"] + i * step for i in range(int((r["x1"] - r["x0"]) / step) + 1)]
    for rad in (ro, ri):
        seg, vis = [], None
        for x in xs:
            th = math.radians(D.theta(n, x)); y = -rad * math.sin(th)
            v_now = y <= 0
            if vis is None or v_now == vis:
                seg.append((x, z0 + rad * math.cos(th)))
            else:
                v.poly(seg, "vis" if vis else "hid", False); seg = [seg[-1], (x, z0 + rad * math.cos(th))]
            vis = v_now
        v.poly(seg, "vis" if vis else "hid", False)
    for x in (r["x0"], r["x1"]):
        th = math.radians(D.theta(n, x))
        v.line(x, z0 + ri * math.cos(th), x, z0 + ro * math.cos(th), "vis" if math.sin(th) >= 0 else "hid")


def arm_side(v, a, z0=0.0):
    th = math.radians(a["ang"]); c = math.cos(th)
    k = "vis" if math.sin(th) >= -0.05 else "hid"
    za, zb = z0 + a["r0"] * c, z0 + (a["r1"] + a["slot"] * 0.5) * c
    v.poly([(a["x"] - a["d"] / 2, za), (a["x"] + a["d"] / 2, za), (a["x"] + a["d"] / 2, zb), (a["x"] - a["d"] / 2, zb)], k, True, "#fff" if k == "vis" else "none")


# ================================================================== 200 agitator weldment
def weldment():
    S = sheet("P1-301-200", "AGITATOR WELDMENT", scale="1:4, 1:5", material=SS316L + "; shaft 316 bar A276", finish=FIN_PC,
              mass=kg("P1-301-201", "P1-301-202", "P1-301-203", "P1-301-204", "P1-301-205"))
    v = S.view(140 + 700 * s4, 620, s4, "FRONT VIEW (from the front, y-; drive end right)  1:4", (120, 120))
    v.rect(X_FREE_END, -D_SH / 2, X_SHOULDER - X_FREE_END, D_SH, "vis", "#fff"); v.rect(X_SHOULDER, -D_DRV / 2, X_DRV_END - X_SHOULDER, D_DRV, "vis", "#fff")
    v.rect(KEY["x0"], D_DRV / 2 - KEY["t1"], KEY["L"], KEY["t1"], "thin")
    for a in ARMS:
        if math.sin(math.radians(a["ang"])) < -0.05:
            arm_side(v, a)
    for n in RIB:
        ribbon_side(v, n)
    for a in ARMS:
        if math.sin(math.radians(a["ang"])) >= -0.05:
            arm_side(v, a)
    v.centre(X_FREE_END - 30, 0, X_DRV_END + 30, 0)
    v.dim((X_FREE_END, -30), (X_DRV_END, -30), -390, f"SHAFT {mmi(X_DRV_END - X_FREE_END)}", "h")
    v.dim((-435, 275), (435, 275), 40, f"RIBBONS {mmi(870)}", "h")
    v.dim((-435, -275), (0, -275), -30, f"OUTER LEFT RH  {mmi(435)}", "h"); v.dim((0, -275), (435, -275), -30, f"OUTER RIGHT LH  {mmi(435)}", "h")
    v.dim((X_FREE_END, -30), (-435, -30), -330, f"{mmi(435 + X_FREE_END * -1 - 435 * 2 + 435)}", "h") if False else None
    v.dim((X_FREE_END, 0), (-435, 0), -330 + 30 * s4, f"{mmi(-435 - X_FREE_END)}", "h")
    v.dim((435, 0), (X_SHOULDER, 0), -330 + 30 * s4, f"{mmi(X_SHOULDER - 435)}", "h")
    v.dim((-470, -275), (-470, 275), 60, "SWEPT Ø550 -1/-2  [21.654 -.04/-.08]", "v")
    v.dim((470, -160), (470, 160), -50, "Ø320 [12.598]", "v")
    v.note(-218, 300, ["outer: RH left, LH right = to the centre"], 13, "middle")
    v.note(218, 300, ["inner: LH left, RH right = to the ends"], 13, "middle")
    for a in ARMS:
        th = math.radians(a["ang"]); zt = (a["r1"] + 6) * math.cos(th)
        if a["tag"] == "A":
            v.tag(a["x"], (-330 if zt < 0 else 330) + (0 if abs(a["x"]) > 100 else (25 if a["x"] > 0 else -25)), a["id"], (a["x"], zt * 0.95))
    v.leader((X_DRV_END - 30, D_DRV / 2), (X_DRV_END + 40, 140), ["KEYWAY 14 N9 (sheet P1-301-201)"])
    v.weld((-220, -40), (-150, -150), "fillet", "6", allround=True, tail="arms to shaft (A 6, B 5)")
    v.weld((-15 - 12, 210), (-150, 190), "fillet", "5", other="fillet", tail="arm slot to ribbon")
    # ---- end view (y, z), from the drive end: screen right = +y
    e = S.view(2350, 620, s4, "END VIEW (from the drive end)  1:4  shaft turns CLOCKWISE seen from here", (1940, 120))
    e.circle(0, 0, 275, "phan"); e.circle(0, 0, 225, "phan"); e.circle(0, 0, 160, "phan"); e.circle(0, 0, 120, "phan"); e.circle(0, 0, 30, "vis", "#fff")
    for a in ARMS:
        th = math.radians(a["ang"]); dy, dz = -math.sin(th), math.cos(th)
        r_end = a["r1"] + a["slot"]
        px, pz = -dz, dy
        w = a["d"] / 2
        e.poly([(dy * a["r0"] + px * w, dz * a["r0"] + pz * w), (dy * r_end + px * w, dz * r_end + pz * w), (dy * r_end - px * w, dz * r_end - pz * w), (dy * a["r0"] - px * w, dz * a["r0"] - pz * w)], "vis", True, "#e3f2fd" if a["tag"] == "A" else "#fff3e0")
        rr = 300 if a["tag"] == "A" else 205
        e.text(dy * rr, dz * rr - 4, a["id"], 14, color="#0d47a1" if a["tag"] == "A" else "#e65100", bold=True)
    e.arc(0, 0, 330, 120, 60, "thin"); e.text(0, 342, "ROTATION (CW)", 13, color="#b00020")
    e.centre(-330, 0, 330, 0); e.centre(0, -330, 0, 330)
    e.angle((0, 0), 60, 90, 90 + 105, "A1 105°")
    e.note(0, -370, ["angles from top dead centre, counter-clockwise seen from the drive end", "blue A = outer arms Ø25, orange B = inner arms Ø20"], 13, "middle")
    rows = [(a["id"], "outer Ø25" if a["tag"] == "A" else "inner Ø20", a["ribbon"], f"{a['x']:+.0f} [{fin(a['x'])}]", f"{a['ang']:.1f}°",
             f"{a['r1'] + a['slot'] - a['r0'] + (ARM_O if a['tag'] == 'A' else ARM_I)['spig_l']:.0f}", "204" if a["tag"] == "A" else "205") for a in ARMS]
    S.table(120, 1250, [("ARM", 55), ("TYPE", 110), ("RIBBON", 75), ("x FROM CENTRE mm [in]", 200), ("ANGLE", 80), ("LENGTH", 75), ("PART", 60)], rows,
            "ARM POSITIONS (x = 0 at the trough centre, + toward the drive end)", 13, 23)
    S.table(840, 1250, [("ITEM", 50), ("PART NO.", 115), ("DESCRIPTION", 330), ("QTY", 45), ("MASS", 150)], [
        (1, "P1-301-201", "Shaft Ø60 / Ø45 (sheet 201)", 1, kg("P1-301-201")),
        (2, "P1-301-202", "Outer ribbon 50 x 8, OD 550, pitch 600", 2, kg("P1-301-202")),
        (3, "P1-301-203", "Inner ribbon 40 x 8, OD 320, pitch 450", 2, kg("P1-301-203")),
        (4, "P1-301-204", "Outer arm Ø25 (sheet 202)", 6, kg("P1-301-204")),
        (5, "P1-301-205", "Inner arm Ø20 (sheet 202)", 8, kg("P1-301-205"))], "ITEM LIST", 13, 23)
    S.notes(840, 1420, 1060, [
        "Build on the agitator fixture: shaft between centres on two V-blocks, a 360° index plate (or printed angle wheel Ø300) clamped on the Ø45 journal, a height gauge on the table. Set each arm by its x and angle from the table.",
        "Weld order: arms into the shaft sockets first (fillet all round, A 6 [.24], B 5 [.20]), alternate sides to keep the shaft straight; check runout at the journals after every 4 arms, straighten cold if > 0.5.",
        "Fit each formed ribbon into the arm slots (slot faces along the helix), clamp to the arm ends, tack, check the swept OD with a trammel from the shaft centre: 274 ±0.5 [10.79 ±.02] radius outer, 160 ±0.5 inner.",
        "Weld ribbon to arms both sides (5 [.20] fillet), ground smooth and blended. No crevices: seal-weld the slot ends.",
        "After welding: finish-turn the bearing, seal and journal diameters between centres (sheet P1-301-201 note 2); then sweep-grind the outer ribbon edge to Ø550 -1/-2 on the lathe with a tool-post grinder.",
        "Polish all welds to #4, passivate. Check: total runout of Ø60 at the boxes 0.05, at the bearings 0.05; Ø45 journal 0.03. Balance is not needed at 40 rpm.",
    ], fs=13)
    S.save(DWG / "P1-301-200_agitator.svg")


# ================================================================== 201 shaft
def shaft():
    S = sheet("P1-301-201", "AGITATOR SHAFT", scale="1:2.5, 1:1, 2:1", material="SS 316 bar, cold finished, ASTM A276, Ø65 [2.56]", finish="Ra 0.8 [32 µin] at bearings, seals and journal; Ra 1.6 elsewhere",
              mass=kg("P1-301-201"))
    s25 = K / 2.5
    v = S.view(170 + 690 * s25, 520, s25, "SHAFT  1:2.5  (free end left, drive end right)", (120, 120))
    v.rect(X_FREE_END, -D_SH / 2, X_SHOULDER - X_FREE_END, D_SH); v.rect(X_SHOULDER, -D_DRV / 2, X_DRV_END - X_SHOULDER, D_DRV)
    v.rect(KEY["x0"], D_DRV / 2 - KEY["t1"], KEY["L"], KEY["t1"], "thin", "#eceff1")
    v.centre(X_FREE_END - 30, 0, X_DRV_END + 30, 0)
    for a in ARMS:
        th = math.radians(a["ang"]); c = math.cos(th); dsp = (ARM_O if a["tag"] == "A" else ARM_I)["spig"]
        if abs(c) > 0.2:
            k = "vis" if math.sin(th) >= 0 else "hid"
            sgn = 1 if c > 0 else -1
            v.line(a["x"] - dsp / 2, sgn * 30, a["x"] - dsp / 2, sgn * (30 - 12 * abs(c)), k); v.line(a["x"] + dsp / 2, sgn * 30, a["x"] + dsp / 2, sgn * (30 - 12 * abs(c)), k)
        v.text(a["x"], -55 if a["tag"] == "A" else 48, a["id"], 13, color="#0d47a1" if a["tag"] == "A" else "#e65100", bold=True)
    for x0, x1 in ((-641 - 40, -641 + 40), (641 - 40, 641 + 40), (-458 - 50, -458 + 2), (458 - 2, 458 + 50)):
        v.line(x0, D_SH / 2 + 6, x1, D_SH / 2 + 6, "bend")
    v.text(-641, 50, "BEARING", 12, color="#b00020"); v.text(641, 50, "BEARING", 12, color="#b00020"); v.text(-483, 50, "PACKING", 12, color="#b00020"); v.text(483, 50, "PACKING", 12, color="#b00020")
    v.dim((X_FREE_END, -30), (X_DRV_END, -30), -110, f"{mmi(X_DRV_END - X_FREE_END)} ±0.5", "h")
    v.dim((X_FREE_END, -30), (X_SHOULDER, -30), -70, f"{mmi(X_SHOULDER - X_FREE_END)} ±0.2", "h")
    v.dim((X_SHOULDER, -22.5), (X_DRV_END, -22.5), -40, f"{mmi(X_DRV_END - X_SHOULDER)}", "h")
    v.dim((X_SHOULDER, 22.5), (KEY["x0"], 22.5), 40, f"{mmi(KEY['x0'] - X_SHOULDER)}", "h")
    v.dim((KEY["x0"], 22.5), (KEY["x0"] + KEY["L"], 22.5), 40, f"KEYWAY {KEY['L']} [{fin(KEY['L'])}]", "h")
    v.dim((X_FREE_END, 0), (0, 0), 0, None, "h") if False else None
    v.dim((X_FREE_END, 30), (-641, 30), 75, f"{mmi(641 + X_FREE_END + 2 * 0 + 49 - 49 + 49 - 49 if False else 49)}", "h")
    v.dim((-641, 30), (641, 30), 75, f"BEARING CENTRES {mmi(1282)}", "h")
    v.leader((-560, 30), (-610, 110), ["Ø60 h7 [2.3622/2.3610] (all Ø60)"])
    v.leader((X_DRV_END - 30, 22.5), (X_DRV_END + 40, 90), ["Ø45 j6 [1.7721/1.7714]"])
    v.leader((X_DRV_END, 0), (X_DRV_END + 40, -60), ["M16 x 32 [1.26] DEEP, DIN 332-D M16 centre", "(gearmotor retaining screw H6)"])
    v.leader((X_FREE_END, -5), (X_FREE_END + 120, -190), ["DIN 332-A 4 centre"])
    v.leader((X_SHOULDER, 22.5), (X_SHOULDER - 80, 120), ["R1 [.04] max fillet, C1 x 45° on both ends"])
    v.datum((X_FREE_END + 60, -30), "A", (0, -1)); v.datum((X_SHOULDER - 60, -30), "B", (0, -1))
    v.fcf(-120, -190, ["↗", "0.03", "A-B"]); v.note(-40, -195, ["Ø45 journal and Ø60 at bearings and boxes, after welding"], 13)
    # keyway section 1:1
    k = S.view(470, 1160, s1, "SECTION C-C  KEYWAY  1:1", (230, 960))
    k.circle(0, 0, D_DRV / 2, "vis", "url(#hA)"); k.rect(-KEY["b"] / 2, D_DRV / 2 - KEY["t1"], KEY["b"], KEY["t1"] + 2, "vis", "#fff")
    k.dim((-KEY["b"] / 2, D_DRV / 2), (KEY["b"] / 2, D_DRV / 2), 30, "14 N9 [.5512/.5495]", "h")
    k.dim((KEY["b"] / 2, -D_DRV / 2), (KEY["b"] / 2, D_DRV / 2 - KEY["t1"]), -60, "39.5 -0.2 [1.555 -.008]", "v")
    k.centre(-30, 0, 30, 0); k.centre(0, -30, 0, 30)
    # arm socket detail
    d = S.view(1130, 1160, SC(0.5), "DETAIL D  ARM SOCKET  2:1", (930, 960))
    d.poly([(-40, 0), (40, 0)], "vis", False)
    d.hatch([(-40, 0), (-10, 0), (-10, -12), (10, -12), (10, 0), (40, 0), (40, -25), (-40, -25)], "hA")
    d.dim((-10, 0), (10, 0), 25, "Ø20 H11 [.787/.792] A  /  Ø16 H11 B", "h")
    d.dim((10, -12), (10, 0), -30, "12 [.47] A / 10 [.39] B", "v")
    d.note(-40, -40, ["flat bottom (drill + end mill), radial to the axis ±0.5°"], 13)
    S.table(1900, 960, [("ARM", 60), ("x mm [in]", 150), ("ANGLE", 90), ("SOCKET", 200)],
            [(a["id"], f"{a['x']:+.0f} [{fin(a['x'])}]", f"{a['ang']:.1f}°", "Ø20 H11 x 12" if a["tag"] == "A" else "Ø16 H11 x 10") for a in ARMS],
            "ARM SOCKETS (x from the trough centre = 690 from the free end face)", 13, 23)
    S.notes(120, 1560, 1600, [
        "Saw Ø65 bar to 1556, face both ends to 1550, centre drill. Rough turn Ø60 to Ø61 and Ø45 to Ø46 (leave 1 [.04] on diameters for finish turning after the weldment is complete).",
        "After welding the agitator (P1-301-200), finish turn between the same centres: Ø60 h7 at both bearings and both packing zones (marked), Ø45 j6 journal, shoulder R1, chamfers. Polish packing zones to Ra 0.4.",
        "Mill the keyway 14 N9 x 140 x t1 5.5 after finish turning; deburr. Drill and tap M16 x 32 in the drive end.",
        "Mill the 14 arm sockets on the dividing head before welding, x and angle from the table (angles from top dead centre, CCW seen from the drive end, with the keyway at 0° as reference).",
        "Lathe capacity: 1,560 [61.4] between centres, Ø300 swing over the carriage for the finish turning of the agitator (ribbon OD 550 needs a gap bed or a big lathe; otherwise finish the journals in a steady rest at each end).",
    ], fs=13)
    S.save(DWG / "P1-301-201_shaft.svg")


# ================================================================== 202 ribbon blanks + arms
def sector(Ri, Ro, deg, n=90):
    a0 = -deg / 2
    out = [(Ro * math.cos(math.radians(a0 + deg * i / n)), Ro * math.sin(math.radians(a0 + deg * i / n))) for i in range(n + 1)]
    inn = [(Ri * math.cos(math.radians(a0 + deg * (n - i) / n)), Ri * math.sin(math.radians(a0 + deg * (n - i) / n))) for i in range(n + 1)]
    return out + inn


def ribbons():
    S = sheet("P1-301-202", "RIBBON FLIGHT BLANKS AND ARMS", scale="1:5, 1:2", material="SS 316L plate 8 [.315] (ribbons), 316 bar Ø25 / Ø20 (arms)",
              finish=FIN_PC, mass=kg("P1-301-202", "P1-301-203", "P1-301-204", "P1-301-205"), qty="2 + 2 + 6 + 8")
    for i, (n, part, ox) in enumerate((("OL", "P1-301-202", 520), ("IL", "P1-301-203", 1650))):
        b = D.blank(n); r = RIB[n]
        v = S.view(ox, 600, s5, f"{part}  {'OUTER' if n == 'OL' else 'INNER'} RIBBON BLANK  8 [.315] 316L  QTY 2  1:5", (120 + 1150 * i, 120))
        S.text(120 + 1150 * i, 150, "one blank per ribbon: form one RH and one LH from the same blank", 14)
        pts = sector(b["Ri"], b["Ro"], b["sector_cut"])
        v.poly(pts)
        v.arc(0, 0, b["Ri"], -b["sector_deg"] / 2, b["sector_deg"] / 2, "phan") if False else None
        for sg in (1, -1):
            a = math.radians(sg * b["sector_deg"] / 2)
            v.line(b["Ri"] * math.cos(a), b["Ri"] * math.sin(a), b["Ro"] * math.cos(a), b["Ro"] * math.sin(a), "bend")
        v.cmark(0, 0, 20)
        v.rad(0, 0, b["Ro"], 20, (b["Ro"] + 40, 200), f"R{b['Ro']:.1f} [{fin(b['Ro'])}]")
        v.rad(0, 0, b["Ri"], -20, (b["Ro"] + 40, -200), f"R{b['Ri']:.1f} [{fin(b['Ri'])}]")
        v.angle((0, 0), b["Ri"] * 0.5, b["sector_cut"] / 2, 360 - b["sector_cut"] / 2, f"GAP {360 - b['sector_cut']:.1f}°")
        v.note(0, -b["Ro"] - 60, [f"sector {b['sector_cut']:.1f}° incl. 15 [.59] trim each end (dashed = net {b['sector_deg']:.1f}°)",
                                 f"helix: OD {r['od']:.0f}, ID {r['od'] - 2 * r['w']:.0f}, pitch {r['p']:.0f}, {b['turns']:.3f} turn, lead {b['helix_deg_out']:.1f}° at OD"], 13, "middle")
        ms.dxf_profile(str(DXF / f"{part}_ribbon_blank"), pts, holes=[], text=f"{part} blank 8mm 316L x2 - Ri {b['Ri']:.2f} Ro {b['Ro']:.2f} {b['sector_cut']:.2f} deg")
    # arms 1:2
    for j, (part, A, r1, n, tag) in enumerate((("P1-301-204", ARM_O, RIB["OL"]["od"] / 2 - RIB["OL"]["w"], "OL", "A"), ("P1-301-205", ARM_I, RIB["IL"]["od"] / 2 - RIB["IL"]["w"], "IL", "B"))):
        L = r1 + A["slot"] - (D_SH / 2 - A["spig_l"])
        oy = 1290 + 270 * j
        a = S.view(250, oy, s2, f"{part}  {'OUTER' if tag == 'A' else 'INNER'} ARM  Ø{A['d']:.0f} 316 BAR  QTY {6 if tag == 'A' else 8}  1:2", (120, oy - 80))
        a.rect(0, -A["spig"] / 2, A["spig_l"], A["spig"]); a.rect(A["spig_l"], -A["d"] / 2, L - A["spig_l"], A["d"])
        a.rect(L - A["slot"], -4.25, A["slot"], 8.5, "thin", "#eceff1")
        a.centre(-10, 0, L + 10, 0)
        a.dim((0, A["d"] / 2), (L, A["d"] / 2), 30, f"{mmi(L)} ±0.3", "h")
        a.dim((0, -A["spig"] / 2), (A["spig_l"], -A["spig"] / 2), -25, f"{mmi(A['spig_l'])}", "h")
        a.dim((L - A["slot"], -A["d"] / 2), (L, -A["d"] / 2), -25, f"SLOT {mmi(A['slot'])} DEEP", "h")
        a.dim((-3, -A["spig"] / 2), (-3, A["spig"] / 2), 25, f"Ø{A['spig']:.0f} e9", "v")
        a.dim((L + 3, -A["d"] / 2), (L + 3, A["d"] / 2), -25, f"Ø{A['d']:.0f} [{fin(A['d'])}]", "v")
        lead = D.lead_deg(n, r1)
        a.leader((L - A["slot"] / 2, 4.25), (L + 40, 40), [f"SLOT 8.5 [.335] wide, plane at {90 - lead:.1f}° to the shaft axis", "(along the ribbon at its inner edge); cut on assembly to suit"])
    S.notes(1900, 1120, 1300, [
        "Cut blanks by laser or waterjet from the DXF (one blank makes one ribbon; RH and LH come from the same blank formed in opposite directions). Weld a 50 x 10 pull tab on each end inside the trim zone.",
        "Forming (sectional flight method): clamp one end to the forming jig (a Ø450 / Ø240 pipe mandrel with a pitch bar), pull the other end with a 5 t chain hoist or porta-power along the axis until the ribbon reaches the pitch; work along with a mallet so the inner edge does not buckle. 316L forms cold; re-pull to correct spring back.",
        "Checks after forming: OD 550 ±3 before grinding (outer) / 320 ±2 (inner); pitch 600 ±5 / 450 ±5 measured over the length; ribbon face square to the axis within 3°.",
        "Trim 15 at each end to the net angle after fitting; radius the ends R20 and grind smooth (product contact).",
        "Option if the forming jig is not worth building: order the four flights formed from a screw-conveyor flight maker (8 mm 316L sectional flights to these OD / ID / pitch / hand). Same drawings apply.",
        "Arms: saw, turn the spigot e9 for a push fit in the H11 socket, cut the slot on the bandsaw after a trial fit on the ribbon so the slot follows the helix. Break edges, all welds ground smooth.",
    ], fs=13)
    S.table(1900, 1830, [("FILE", 400), ("PART", 280), ("QTY", 60)],
            [("P1-301-202_ribbon_blank_mm/_in.dxf", "outer blank 8 mm", 2), ("P1-301-203_ribbon_blank_mm/_in.dxf", "inner blank 8 mm", 2)], "CUT FILES", 13, 23)
    S.save(DWG / "P1-301-202_ribbons_arms.svg")


if __name__ == "__main__":
    weldment(); shaft(); ribbons()
