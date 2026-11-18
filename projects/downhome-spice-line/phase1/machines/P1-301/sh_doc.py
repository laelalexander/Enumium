"""P1-301 cover sheet 000, assembly sequence 003, hardware and bought parts 600, inspection and test plan 900."""
import base64

from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
import design as D

IMG = DWG / "img"


def img(S, path, x, y, w, h):
    b = base64.b64encode(path.read_bytes()).decode()
    S.add(f'<image href="data:image/png;base64,{b}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')


def assembly():
    S = sheet("P1-301-003", "ASSEMBLY SEQUENCE, TORQUES AND CHECKS", scale="NTS", material="see item lists", finish="-", mass=f"{sum(MASS.values()):.0f} kg made parts + bought ≈ 390 kg [860 lb]")
    cap = ["1  Frame set, levelled, anchored", "2  Trough on the frame (free end open)", "3  Agitator slid in, bearings on",
           "4  Free-end plate, packing, followers", "5  Gearmotor and torque arm", "6  Cover, valve, panel, sensors"]
    for i in range(6):
        x, y = 120 + (i % 3) * 560, 120 + (i // 3) * 470
        img(S, IMG / f"asm_s{i + 1}.png", x, y + 10, 540, 432)
        S.add(f'<rect x="{x}" y="{y + 10}" width="540" height="432" fill="none" stroke="#b0bec5"/>')
        S.text(x + 8, y + 32, cap[i], 17, bold=True)
    S.text(120, 1075, "orange = parts added in that step; ghosted = parts still to come", 13, color="#607d8b")
    steps = [
        ("1", "Set frame 400 on the marked location; shim feet level within 1 [.04]; drill and set anchors.", "H4 x16, 60 N·m", "rails + bearing plates coplanar 1; diagonals 2"),
        ("2", "Lift trough 100 (≈ 100 kg) with a spreader; lugs on the rails over the sleeves. Free-end plate 110 OFF.", "H3 x4 M12, 70 N·m", "bar Ø63.8 through drive throat and both Ø80 plate holes: free"),
        ("3", "Sling the agitator 200 (≈ 53 kg) at the shaft between arms, slide it in from the free end, drive journal through the drive throat and plate.", "-", "ribbons do not touch the shell while sliding: guide by hand"),
        ("4", "Gasket 111 and free-end plate 110 over the free shaft end, onto the ring 108.", "H13 x15 M10, 25 N·m cross", "gasket edge flush with the inside, no step"),
        ("5", "Slide SUCF212 bearings on both ends; centre the shaft in both throats (2 [.08] radial gap all round), then torque; set axial position.", "H1 x8 M16, 120 N·m; H5 set screws", "15 ±3 ribbon to plate both ends; turn by hand: 4..6 ribbon gap"),
        ("6", "Packing: 4 rings 10 sq per box, joints 90° apart; follower; studs.", "H2 x8 M10, hand + 1/4 turn", "follower square, 10 [.39] gap left for adjustment"),
        ("7", "Gearmotor: key H12, food-grade anti-seize, slide onto the Ø45 journal, retaining screw; torque arm to bracket 408 (drill bracket now).", "H6 per NORD; H7 bushes just compress", "no side load: motor hangs free on the arm"),
        ("8", "Valve P1-331 + clamp; level switch P1-337; panel CP-301 on rails 410; wire per E01..E04.", "H11 x4 M10, 40 N·m", "point-to-point check against E04"),
        ("9", "Cover 300: hinge pins H10; gasket P1-339 on the flange land; latches + keepers and interlock (drill on assembly).", "H8 4 N·m; H9 1.5 N·m", "cover lands evenly, gasket 3 ±0.5; sensor gap 5"),
        ("10", "Commission per P1-301-900: rotation, interlock, STO, run-in, product trial.", "-", "sign the ITP record"),
    ]
    S.table(1830, 120, [("STEP", 60), ("HARDWARE / TORQUE", 520), ("CHECK BEFORE THE NEXT STEP", 990)],
            [(a, c, d) for a, b, c, d in steps], "ASSEMBLY STEPS: HARDWARE AND CHECKS", 13, 24)
    S.notes(1830, 420, 1570, [f"Step {a}: {b}" for a, b, c, d in steps] + [
        "Lifting: trough + agitator ≈ 155 kg [340 lb]: use the shop hoist or a gantry, never lift by the shaft ends or the stuffing boxes.",
        "Agitator removal for maintenance is the reverse of steps 7, 6, 5, 4, 3 (cover open, valve off).",
    ], title="ASSEMBLY STEPS: OPERATIONS", fs=13)
    rows = [(h, d[:60], g, q, w[:46], t[:40]) for h, d, g, q, w, t in HARDWARE]
    S.table(1830, 1160, [("ITEM", 50), ("DESCRIPTION", 520), ("STANDARD", 230), ("QTY", 40), ("WHERE", 360), ("TORQUE", 340)], rows, "HARDWARE AND TORQUES (all A4 / 316 stainless)", 12, 22)
    S.save(DWG / "P1-301-003_assembly.svg")


def hardware():
    S = sheet("P1-301-600", "BOUGHT PARTS AND HARDWARE SCHEDULE", scale="NTS", material="-", finish="-", mass="-")
    rows = [(t, d[:92], m, pn[:62], q, f"${u:,.0f}", f"${u * q:,.0f}", n[:40]) for t, d, m, pn, q, u, n in BOUGHT]
    tot = sum(u * q for *_, q, u, n in BOUGHT)
    rows.append(("", "TOTAL BOUGHT (estimates; panel components itemised on E03)", "", "", "", "", f"${tot:,.0f}", ""))
    S.table(120, 140, [("TAG", 80), ("DESCRIPTION", 700), ("MAKER", 180), ("PART NUMBER", 520), ("QTY", 40), ("EACH", 70), ("EXT", 80), ("NOTE", 360)], rows,
            "BOUGHT PARTS (P1-301 BOM lines)", 12, 24)
    rows = [(h, d, g, q, w, t) for h, d, g, q, w, t in HARDWARE]
    S.table(120, 560, [("ITEM", 50), ("DESCRIPTION", 560), ("STANDARD / GRADE", 300), ("QTY", 40), ("WHERE", 480), ("TORQUE", 420)], rows,
            "HARDWARE (A4-70 / 316 stainless; dry torques, food-grade anti-seize only where noted)", 12, 24)
    made = [(k, v) for k, v in sorted(MASS.items())]
    S.table(120, 1000, [("PART", 140), ("MASS kg", 100)], [(k, f"{v:.2f}") for k, v in made[:12]], "MADE-PART MASSES (from the 3D model)", 12, 22)
    S.table(420, 1000, [("PART", 140), ("MASS kg", 100)], [(k, f"{v:.2f}") for k, v in made[12:]], None, 12, 22)
    S.notes(800, 1000, 1500, [
        "Prices are estimates for budgeting (2026-11). Every 'confirm' part number is checked against a quote before ordering; NORD frame and hollow bore set the shaft journal and the torque bracket.",
        "Materials: product contact 316L (trough, cover, agitator; shaft 316); frame 304. Certs (EN 10204 3.1) required for all 316L plate and bar.",
        "Weld consumables: ER316L Ø1.6 and Ø2.4 TIG rod, argon 99.996 %, back-purge for full-penetration joints; passivation gel or citric bath (ASTM A967).",
    ], fs=13)
    S.save(DWG / "P1-301-600_hardware.svg")


def itp():
    S = sheet("P1-301-900", "INSPECTION AND TEST PLAN, DESIGN CALCULATIONS", scale="NTS", material="-", finish="-", mass="-")
    c = D.calcs()
    tests = [
        ("T1", "Material certs 316L / 316 / 304 against heat numbers", "EN 10204 3.1", "before cutting", "QC"),
        ("T2", "Shell formed radius with template, every 150", "gap ≤ 1", "101 after forming", "fab"),
        ("T3", "Trough: bar Ø63.8 through both throats turns free after welding", "free by hand", "100 after W3", "fab"),
        ("T4", "Box face square to the bar / concentric", "0.2 / 0.25", "100", "QC"),
        ("T5", "Inside welds: visual, ground flush, no pits or crevices; surface Ra", "Ra ≤ 0.8 µm", "100, 300", "QC"),
        ("T6", "Flange flat; lug seats coplanar", "1.5 / 1.0", "100", "QC"),
        ("T7", "Shaft: Ø60 h7, Ø45 j6, keyway 14 N9, runout after welding", "per 201; 0.03 A-B", "201 / 200", "QC"),
        ("T8", "Agitator swept OD (trammel from centres)", "Ø550 -1/-2; Ø320 ±1", "200", "QC"),
        ("T9", "Stuffing box Ø80 H8 bore, Ø100 f8 spigot (gauges)", "per 104", "104", "QC"),
        ("T10", "Frame: rails coplanar, bearing holes on one axis", "1 / 0.5", "400", "fab"),
        ("T11", "Ribbon-to-trough gap turning by hand, full length", "4..6 [.16..24]", "assembly step 5", "QC"),
        ("T12", "Passivation (ASTM A967): water break / ferroxyl test on coupons", "pass", "before assembly", "QC"),
        ("T20", "Point-to-point wiring against E04; insulation resistance 500 V (power only)", "> 1 MΩ", "CP-301", "elec"),
        ("T21", "Rotation: clockwise seen from the drive end (outer ribbons carry to the centre)", "correct", "first run", "elec"),
        ("T22", "E-stop stops the agitator via STO; restart needs RESET + START", "pass", "commissioning", "elec + QC"),
        ("T23", "Cover open stops the agitator; closing does not restart it", "pass", "commissioning", "elec + QC"),
        ("T24", "Single fault on each safety channel detected (open one wire)", "no reset possible", "commissioning", "elec"),
        ("T25", "Run-down time after E-stop", "< 2 s", "commissioning", "elec"),
        ("T26", "No-load current; full-batch current (67 kg) after 15 min", "< 70 % FLA / < FLA", "commissioning", "elec"),
        ("T27", "Packing run-in: weep allowed 1st hour, then re-tighten; box temp", "< 60 °C", "run-in 4 h", "mech"),
        ("T28", "Mixing test: 67 kg batch with 0.5 % salt tracer, 10 samples at 10 min", "CV ≤ 5 %", "product trial", "QA"),
        ("T29", "Discharge: residue after valve open and 60 s run", "< 0.5 kg", "product trial", "QA"),
        ("T30", "Clean-out: dry clean, allergen swab (ATP) on ribbons, boxes, valve", "pass", "before release", "QA"),
    ]
    S.table(120, 140, [("TEST", 55), ("WHAT IS CHECKED", 760), ("LIMIT", 210), ("WHEN / PART", 200), ("BY", 90), ("RESULT / SIGN", 220)],
            [(a, b, l, w, by, "") for a, b, l, w, by in tests], "INSPECTION AND TEST PLAN (record results here or in the MES)", 12, 26)
    calc = [
        ("Total trough volume", f"{c['vol_total_l']:.0f} L [{c['vol_total_l'] / 28.317:.1f} cu ft]", "semi-circle R280 + 294 straight sides x 900 long"),
        ("Working batch", f"{c['batch_l']:.0f} L = {c['batch_kg']:.0f} kg at 0.51 kg/L ({c['fill'] * 100:.0f} % of total)", "ribbon blenders mix well at 40-70 % fill"),
        ("Agitator speed / tip speed", f"40 rpm / {c['tip']:.2f} m/s", "typical ribbon tip 1.0-1.5 m/s for spice"),
        ("Motor / output torque", f"1.5 kW / {c['torque_nm']:.0f} N·m at 40 rpm", "gearmotor i ≈ 43.7"),
        ("Shaft shear stress Ø60 at 2 x torque", f"{c['tau_60']:.1f} MPa", "316 yield 205 MPa: SF > 6 in shear"),
        ("Journal shear stress Ø45 at 2 x torque", f"{c['tau_45']:.1f} MPa", "SF ≈ 3 in shear on 0.58 x yield"),
        ("Key 14 x 9 x 125: shear / bearing at 2 x torque", f"{c['key_shear']:.0f} / {c['key_bear']:.0f} MPa", "316 key: OK; hub is the gearbox steel"),
        ("Bearing load (agitator 53 kg + product reaction)", "≈ 0.6 kN radial each", "SUCF212 C = 52 kN: life >> 100,000 h"),
        ("Inner/outer ribbon clearance at the arms", f"{D.CLEAR_DEG:.0f}° minimum phase", "arm of one ribbon never crosses the other ribbon"),
        ("Frame: 4 legs 76.2 x 3.05, 1.78 m", "≈ 1.0 kN per leg", "Euler buckling > 100 kN: no issue; anchors for vibration"),
    ]
    S.table(1800, 140, [("CALCULATION", 420), ("RESULT", 520), ("NOTE / LIMIT", 600)], calc, "DESIGN CALCULATIONS (design.py calcs())", 12, 25)
    S.save(DWG / "P1-301-900_itp.svg")


def cover_sheet(sheets):
    S = sheet("P1-301-000", "P1-301 RIBBON BLENDER 6 CU FT: DRAWING SET", scale="NTS", material="316L product contact, 304 frame", finish=FIN_PC,
              mass=f"≈ 390 kg [860 lb] complete, 67 kg batch")
    img(S, IMG / "asm_full.png", 120, 210, 1500, 980)
    S.text(130, 150, "Ribbon blender P1-301, built in house, rev B", 30, bold=True)
    S.text(130, 185, "6 cu ft working, 131 L / 67 kg batch, 40 rpm, 1.5 kW, 230 V 1-ph, 316L product contact, bolted free end for agitator removal", 16)
    data = [("Duty", "dry seasoning blends, Phase 1 line (1,000 lb/week), 1 batch per 20-30 min"), ("Trough", "R280 inside x 900 long, 3 mm 316L, #4 inside"),
            ("Agitator", "double ribbon: outer Ø550 / inner Ø320, pitches 600 / 450; 14 arms"), ("Seals", "PTFE packing 4 x 10 sq in stuffing boxes; bearings outboard"),
            ("Drive", "NORD helical-bevel hollow-shaft gearmotor 1.5 kW on a torque arm; VFD GS21 with STO"),
            ("Discharge", "4 in sanitary butterfly valve, 24 V actuator, bottom centre"), ("Safety", "cover interlock + E-stop, PNOZ s4, PL d target"),
            ("Heights", "axis 1,683; flange top 1,983; valve outlet 1,261; upstand top 2,014 [79.3 in]")]
    S.table(1700, 140, [("DESIGN DATA", 240), ("", 1220)], data, None, 13, 26)
    S.table(1700, 400, [("SHEET", 130), ("TITLE", 900), ("FILE", 430)],
            [(n, t, f"P1-301-{n.split('-')[-1]}*.svg / PDF") for n, t in sheets], "SHEET INDEX", 13, 25)
    S.notes(120, 1220, 1500, [
        "Units mm [in]. Third-angle projection. Tolerances in the title block unless noted. Weld symbols AWS A2.4; welding GTAW ER316L per AWS D1.6.",
        "Product-contact surfaces #4, Ra ≤ 0.8 µm [32 µin], welds ground flush and blended, no crevices; passivate ASTM A967 after all welding.",
        "Cut files (DXF, mm and inch) are in dxf/; 3D models (STEP per part, assembly STEP/GLB) in cad/; generators: design.py, model.py, sh_*.py.",
        "Bought parts marked 'confirm' must be checked against the supplier drawing before the related made part is cut (NORD bore and torque arm, latch, enclosure foot kit).",
        "Release for build: drawings checked, ITP P1-301-900 attached to the traveler, materials certified.",
    ], title="GENERAL NOTES", fs=14)
    S.save(DWG / "P1-301-000_cover.svg")
