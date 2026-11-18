"""P1-406-000 cover + index, -003 assembly and setup, -800 bought parts and hardware, -900 ITP + calculations."""
import base64
import textwrap
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

IMG = DWG / "img"
C = calcs()
M_MADE = sum(MASS.values())
M_BOUGHT = 45.0 + 4.0 + 6.0 + 1.5 + 5.0 + 0.5 + 1.0 + 2.0       # head (used, estimate), belt + bearings, gearmotor, pusher, controls, sensors, light, feet + locks
M_TOT = M_MADE + M_BOUGHT
JAR, SHK = CONT["jar-12"], CONT["shaker-250"]


def img(S, path, x, y, w, h):
    b = base64.b64encode(path.read_bytes()).decode()
    S.add(f'<image href="data:image/png;base64,{b}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')


def assembly():
    S = sheet("P1-406-003", "ASSEMBLY, BELT SPLICE AND SETUP", scale="NTS · 1:8", material="see item list", finish="-",
              mass=f"{M_TOT:.0f} kg [{M_TOT * 2.2046:.0f} lb]")
    cap = ["1  Frame + spine + stand", "2  Head on the stand", "3  Pulleys + take-up", "4  FRP rails + bed (through)", "5  Belt, bearings, drive",
           "6  Guides", "7  Reject + sensors", "8  Controls, light, feet"]
    for i in range(8):
        x, y = 110 + (i % 4) * 420, 110 + (i // 4) * 400
        img(S, IMG / f"cv_s{i + 1}.png", x, y + 10, 400, 373)
        S.add(f'<rect x="{x}" y="{y + 10}" width="400" height="373" fill="none" stroke="#b0bec5"/>')
        S.add(f'<rect x="{x + 2}" y="{y + 12}" width="{len(cap[i]) * 10 + 10}" height="30" fill="#fff" fill-opacity="0.85"/>')
        S.text(x + 8, y + 34, cap[i], 17, bold=True)
    S.text(110, 925, "orange = parts added in that step; ghosted = parts still to come", 13, color="#607d8b")
    steps = [
        ("1", "Set the end frames 101 (infeed) and 102 (outfeed) on their feet, 1,420 between the pulley centres; bolt the spine 103 to the leg braces; bolt the head stand 104 to the spine at x 0.",
         "H1 x8 M8 15 N·m; feet P1-462 M16", "belt top z 905 ±2 both ends, level 1 / 1000 along and across; frames square to the spine (diagonals ±2)"),
        ("2", "Lift the head P1-418 onto the stand: G10 pad and nylon shoulder bushes under the +y lug, plain on the -y lug. Centre the aperture on the belt line (y 0) and on the bed height.",
         "H7 x4 M8 10 N·m (bushes: hand + 1/4 turn)", f"aperture bottom z {HEAD['ap_z0']:.0f} ±2; head-to-frame resistance on the +y lug > 1 MΩ (loop broken, T8)"),
        ("3", "Bolt the 4 UCFL204 flanges loose on the side-plate ears; slide the drive pulley 201 (keyed shaft to -y) into the outfeed pair and the tail pulley 202 into the infeed slots; fit the take-up screws 203.",
         "H2 x16 M10 25 N·m (tail: snug only); H3 x2", "pulley axes parallel 0.5 over 1,420 (T3); set screws in the bearings tight after alignment"),
        ("4", "Thread the two FRP rails 204 through the head aperture; clip them to the side plates with 205; lay the UHMW bed 206 on the rails and screw down with nylon screws (no metal in the MFZ).",
         "H4 x8 M6 6 N·m (clips, outside the MFZ); H5 x20 nylon hand tight", f"bed top z {Z_BELT - BELT['t']:.0f} = pulley tops ±0.5 (straight edge); clearance to the aperture ≥ 10 all round"),
        ("5", "Thread the open belt P1-419 through the aperture over the bed, round both pulleys and back under through the aperture; splice in place (finger splice, supplier or hot press). Fit the gearmotor P1-420 + torque arm 401.",
         "H12 x2 4 N·m + Loctite 243; H13 8 N·m (bush not crushed)", "splice flat, no step > 0.2; belt tracks centred ±3 over 10 min at speed (take-up screws, T5)"),
        ("6", "Guide brackets 208 to the side plates in the S or J slot position; guide strips 207 on the brackets (infeed 280 pair, outfeed 70 pair). No guide inside the MFZ.",
         "H6 x12 M5 4 N·m", f"gap S {GUIDE['gap']['S']:.0f} / J {GUIDE['gap']['J']:.1f} ±1, centred on y 0"),
        ("7", "Pusher bracket 301 to the -y outfeed plate, actuator P1-421 + paddle 302; locked bin 303 hooked on the +y plate, lid and hasp; eye brackets 304 + B1 eye and reflector, B2 in the bin slot, B3 on the lid.",
         "H8 x6 M6 8 N·m; H9 clevis pins", "retracted paddle face 8 outside the J guide line; extended: paddle passes the belt centre +40 (T10)"),
        ("8", "Controls box P1-459 on bracket 402 on the -y infeed leg; beacon pole 403 + stack light P1-461 on the +y infeed leg; cables W1, W5-W10 per E01, P-clipped on the legs, away from the head.",
         "H10 x4 M6 4 N·m (PC box); H11 U-bolts 6 N·m", "wiring per E01, < 0.1 Ω PE (T13); program P1-406-FW-01 loaded; head validated with the test pieces (T15-T18)"),
    ]
    S.table(1830, 110, [("STEP", 60), ("HARDWARE / TORQUE", 640), ("CHECK BEFORE THE NEXT STEP", 870)], [(a, c, d) for a, b, c, d in steps],
            "ASSEMBLY STEPS: HARDWARE AND CHECKS", 12, 24)
    S.notes(1830, 360, 1570, [b for a, b, c, d in steps], title="ASSEMBLY STEPS: OPERATIONS", fs=12)
    import sh_ga
    s8 = SC(8)
    vt = S.view(900, 1880, s8, "SETUP (1:8), FROM -Y: METAL-FREE ZONE, RAILS, REJECT", (110, 1010))
    sh_ga.front(vt)
    for txt, at, to in (("FRP RAILS + UHMW BED, NYLON SCREWS ONLY", (300.0, Z_BELT - 20), (250, 1600)),
                        ("TAIL TAKE-UP ±15 (SPLICE AT MID TRAVEL)", (-PUL["x"], Z_PUL), (-750, 1500)),
                        ("DRIVE, PUSHER + LOCKED BIN", (REJ["x"], Z_BELT + 40), (750, 1500))):
        vt.leader(at, to, [txt], 12)
    S.notes(1830, 1380, 1570, [
        f"Belt splice: cut square to length (3,035 + the maker's finger allowance) with the tail at mid take-up; finger-cut both ends, press at the maker's temperature, trim. No metal lacing or clips ever: they would trip the head.",
        f"Changeover shaker ↔ jar (about 2 min, belt stopped): move the 6 guide brackets 208 to the S or J slot ends (2 screws each). Nothing else changes; the head sees both ({SHK['d']:.0f} / {JAR['d']:.1f} Ø).",
        f"Each pack: the operator sets it on the belt between the infeed guides, one at a time, ≥ {C['pitch_min'] / 4:.0f} apart; the belt runs {C['v_mpm']:.0f} m/min. Rejects stop the belt for ≈ {C['t_reject']:.0f} s; hold packs while amber/red.",
        "Every 4 h, at start and after any stop > 30 min: pass the Fe, NFe and SS test pieces through the aperture centre on a pack, each must be rejected into the bin and confirmed by B2 (record in the CCP-1 log).",
        "Cleaning: dry wipe; belt with food-safe detergent, no water jet on the head control or the box. Care: belt tracking weekly; bearings grease monthly (food grade H1); belt replace when cut or frayed.",
    ], "SPLICE, CHANGEOVER, OPERATION, VALIDATION, CARE", fs=12)
    S.table(1830, 1000, [("ITEM", 50), ("DESCRIPTION", 560), ("QTY", 40), ("WHERE", 600), ("TORQUE", 320)],
            [(h, d[:84], q, w[:70], t) for h, d, g, q, w, t in HARDWARE], "HARDWARE AND TORQUES (all A2 stainless; full spec on 800)", 11, 20)
    S.save(DWG / "P1-406-003_assembly.svg")


def hardware():
    S = sheet("P1-406-800", "BOUGHT PARTS AND HARDWARE", scale="NTS", material="-", finish="-", mass="-")
    rows = []
    for t, d, m, p, q, u, n in BOUGHT:
        dl, pl, ml = textwrap.wrap(d, 120), textwrap.wrap(p, 80), textwrap.wrap(m, 34)
        rows.append((t, dl[0], ml[0], pl[0], q, f"${u:,.0f}", f"${u * q:,.0f}"))
        for k in range(1, max(len(dl), len(pl), len(ml))):
            rows.append(("", "  " + dl[k] if k < len(dl) else "", ml[k] if k < len(ml) else "", "  " + pl[k] if k < len(pl) else "", "", "", ""))
    S.table(110, 110, [("TAG", 90), ("DESCRIPTION", 1080), ("MAKER", 330), ("PART NUMBER", 720), ("QTY", 50), ("UNIT", 90), ("TOTAL", 110)], rows,
            "BOUGHT PARTS (estimates unless noted; confirm before order)", 13, 23)
    tot = sum(u * q for t, d, m, p, q, u, n in BOUGHT)
    y = 110 + 23 * (len(rows) + 1) + 36
    S.text(110, y, f"Bought parts for one conveyor ≈ ${tot:,.0f} (used head ${BOUGHT[0][5]:,.0f} of it)", 16, bold=True)
    y2 = y + 60
    S.table(110, y2, [("ITEM", 50), ("DESCRIPTION", 560), ("STANDARD", 210), ("QTY", 40), ("WHERE", 640), ("TORQUE", 160)],
            [(h, d, g, q, w, t) for h, d, g, q, w, t in HARDWARE], "HARDWARE (all A2 / 18-8 stainless unless nylon)", 12, 22)
    mat = [
        ("304 sheet 4 mm (side plates x 4, clips 205)", "4 x 285 x 190 + 4 x 50 x 150", "laser, set of 4 plates"),
        ("304 sheet 3 / 1.5 mm (beds, brackets; bin 303 + lid)", "2 x 290 x 200 + small; 1,200 x 1,280 + 220 x 280", "laser + brake"),
        ("304 plate 6 / 8 mm (pusher bracket, torque arm; pads, top plates)", "80 x 400 + 45 x 260; 8 x 60 x 60, 4 x 70 x 120", "laser"),
        ("304 tube 40 x 40 x 2 (legs, cross tubes, braces)", "≈ 7.5 m", "2 x 6 m lengths"),
        ("304 tube 80 x 40 x 3 (spine, stand beam) + 50 x 50 x 3 (posts)", "1,420 + 640; 2 x 430", "cut to length"),
        ("304 tube Ø25.4 x 1.65 (pole 403)", "762", "1 length"),
        ("2 in SCH 40 304 pipe + Ø80 x 8 discs + Ø25 bar (pulleys)", "2 x 175; 4 discs; 362 + 200", "machine shop stock"),
        ("FRP rect tube 38.1 x 19.05 x 3.2 (rails 204)", "2 x 1,070", "Strongwell / Bedford, 1 x 8 ft"),
        ("UHMW-PE FDA: 10 sheet (bed), 10 x 40 bar (guides), 20 plate (paddle)", "960 x 196; 2 x 280 + 2 x 70; 120 x 80", "offcuts"),
        ("G10 sheet 6 (head insulator) + nylon shoulder bushes", "80 x 70", "with P1-462"),
    ]
    S.table(1900, y2, [("MATERIAL", 640), ("PER CONVEYOR", 440), ("BUY", 340)], mat, "RAW MATERIAL (made parts)", 12, 22)
    S.table(1900, y2 + 22 * (len(mat) + 1) + 60, [("TAG", 90), ("WHERE / NOTE", 1330)], [(t, n) for t, d, m, p, q, u, n in BOUGHT if n],
            "PURCHASING AND MOUNTING NOTES", 12, 22)
    S.save(DWG / "P1-406-800_bought_hardware.svg")


def itp():
    S = sheet("P1-406-900", "INSPECTION AND TEST PLAN, CALCULATIONS", scale="NTS", material="-", finish="-", mass="-")
    tests = [
        ("T1", "Material certs 304 (EN 10204 3.1); UHMW and belt FDA letters; FRP datasheet (non-conductive)", "on file", "receiving", "QC"),
        ("T2", "Used head: maker's service report, serial, aperture and lug drawing; head stand re-dimensioned if needed", "matches 104", "before cutting 104", "QC"),
        ("T3", "Pulley axes parallel and square to the flow; belt top level both ends", "0.5 / 1,420; ±2", "step 3", "assy"),
        ("T4", f"No metal inside |x| < {X_STATIC:.0f} (static) and < {X_MOVING:.0f} (moving): screws nylon, rails FRP, no guides", "visual + magnet", "step 4", "QC"),
        ("T5", "Belt tracking at speed for 10 min, splice flat", "±3; step ≤ 0.2", "step 5", "assy"),
        ("T6", f"Belt speed (mark + stopwatch over 5 m)", f"{C['v_mpm']:.1f} m/min ±5 %", "commissioning", "assy"),
        ("T7", "Pack clearance in the aperture, S and J (gauge pack of each)", f"jar ≥ {C['jar-12']['clear']:.0f}, shaker ≥ {C['shaker-250']['clear']:.0f}", "step 4", "assy"),
        ("T8", "Head isolated from the frame on the +y lug (G10 + bushes): no conductive loop through the stand", "> 1 MΩ", "step 2", "elec"),
        ("T9", "Head sensitivity set up by the service engineer with the product (packs of each spice), phase / gain locked", "report", "commissioning", "QA"),
        ("T10", "Pusher: retracted clear of the J guide line; extended pack lands in the bin, both packs, 20 cycles", "20 / 20", "step 7", "assy"),
        ("T11", "Bin locked: lid open (B3) stops the line; key held by QA only", "pass", "commissioning", "QA"),
        ("T12", "Run-time check reminder (amber every 4 h) and START acknowledge", "pass", "commissioning", "elec"),
        ("T13", "Wiring vs E01; PE continuity stud → frame, motor, head stand side", "< 0.1 Ω", "before power", "elec"),
        ("T14", "Hi-pot / insulation, cord to PE (G1 disconnected)", "> 1 MΩ at 500 V", "before power", "elec"),
        ("T15", "Test piece Fe 1.5 on the leading, middle and trailing edge of a jar, aperture centre: rejected + B2 confirm", "3 / 3", "commissioning + every 4 h", "QA"),
        ("T16", "Test piece NFe 2.0, same", "3 / 3", "commissioning + every 4 h", "QA"),
        ("T17", "Test piece SS 2.5, same", "3 / 3", "commissioning + every 4 h", "QA"),
        ("T18", "Fail-safe: head unplugged, W5 cut, bin full (B2 blocked), lid open, E-stop: each stops the belt, red / amber", "5 / 5", "commissioning", "QA"),
        ("T19", "False rejects: 200 clean packs of each product", "≤ 1", "first run", "QA"),
        ("T20", f"Rate {RATE:.0f} packs / min for 10 min without a stop", "pass", "first run", "QA"),
        ("M1", "Belt tracking, splice, bed wear; bearings grease H1", "-", "weekly / monthly", "maint"),
        ("M2", "Head validation by the service engineer", "report", "yearly", "QA"),
    ]
    S.table(110, 110, [("TEST", 60), ("WHAT IS CHECKED", 900), ("LIMIT", 250), ("WHEN / PART", 230), ("BY", 70), ("RESULT / SIGN", 200)],
            [t + ("",) for t in tests], "INSPECTION AND TEST PLAN (CCP-1: record results in the CCP log)", fs=13, rh=28)
    setup = [(k, v["setting"], f"Ø{v['d']:.1f} x {v['h']:.1f}", f"{GUIDE['gap'][v['setting']]:.1f}", f"{C[k]['top']:.0f}", f"{C[k]['clear']:.0f}", f"{C[k]['centre_off']:+.0f}")
             for k, v in CONT.items()]
    S.table(110, 110 + 28 * (len(tests) + 1) + 70, [("PACK", 160), ("SET", 50), ("SIZE", 160), ("GUIDE GAP", 120), ("TOP z", 100), ("CLEAR TO APERTURE", 200), ("CENTRE vs APERTURE", 200)],
            setup, "SETUP TABLE (z above the floor)", fs=13, rh=28)
    calc = [
        ("Belt speed", f"{C['v']:.0f} mm/s = {C['v_mpm']:.1f} m/min", f"Ø{PUL['d']:.0f} drive pulley at {MOTOR['rpm']:.0f} rpm"),
        ("Pack pitch at the line rate", f"{C['pitch_min']:.0f} mm", f"{RATE:.0f} packs / min; packs are well spaced for one-at-a-time reject"),
        ("Time in the aperture", f"{C['t_head']:.2f} s", "head length + jar Ø, well above the head's minimum (≈ 0.1 s)"),
        ("Head to reject", f"{C['t_track']:.2f} s", f"{REJ['x']:.0f} mm at {C['v']:.0f} mm/s; B1 window ±0.5 s"),
        ("Reject cycle", f"{C['t_reject']:.1f} s", f"stop 0.3 + out / in {REJ['stroke']:.0f} at {REJ['speed']:.0f} mm/s + 0.5"),
        ("Belt length", f"{C['L_belt']:.0f} mm", f"2 x {2 * PUL['x']:.0f} + π (Ø{PUL['d']:.0f} + t); take-up ±{TAKEUP / 2:.0f}"),
        ("Belt pull", f"{C['F_belt']:.1f} N", "packs + belt on UHMW (μ 0.3) + pulley drag"),
        ("Pulley torque / power", f"{C['T_pul']:.2f} N·m / {C['P']:.1f} W", f"with start factor 1.5; gearmotor {MOTOR['T']:.1f} N·m: SF {C['T_motor_ratio']:.0f}"),
        ("FRP rail deflection", f"{C['FRP_defl']:.2f} mm", "3 packs + bed + belt on a 970 span, E 17 GPa"),
        ("Metal-free zone", f"{MFZ['static']:.0f} / {MFZ['moving']:.0f} mm", f"1.5 / 2.0 x aperture height {HEAD['ap_h']:.0f} each side of the head faces"),
        ("Electrical load", f"{ELE['A']:.1f} A at 120 V", f"fuse {ELE['fuse']:.0f} A T; 24 V {ELE['I_dc']:.1f} A supply"),
        ("Mass", f"{M_TOT:.0f} kg [{M_TOT * 2.2046:.0f} lb]", f"made {M_MADE:.0f} kg + bought ≈ {M_BOUGHT:.0f} kg (head estimate)"),
    ]
    S.table(1840, 110, [("CALCULATION", 320), ("RESULT", 340), ("NOTE / LIMIT", 900)], calc, "DESIGN CALCULATIONS (design.py, sh_doc.py)", fs=13, rh=28)
    S.notes(1840, 520, 1560, [
        "This conveyor carries CCP-1 (metal) in the HACCP plan. A pack may only leave the conveyor at the outfeed end after passing a healthy head, or into the locked bin.",
        "Before production each day and every 4 h: T15-T17 with the certified test pieces (kept by QA). A failed test: hold all packs since the last good test and re-run them.",
        "Rejects: QA opens the bin, logs each pack, re-runs it once; a second reject is investigated (the source of the metal is found before the line restarts).",
        "Any change to the head settings, the belt speed or the reject timing needs T9 and T15-T18 again.",
    ], "CCP-1 RULES", fs=13)
    S.save(DWG / "P1-406-900_itp.svg")


def cover_sheet(sheets):
    S = sheet("P1-406-000", "P1-406 METAL DETECTOR CONVEYOR: DRAWING SET", scale="NTS", material="304 frame, FRP + UHMW through the head", finish=FIN_NPC,
              mass=f"{M_TOT:.0f} kg [{M_TOT * 2.2046:.0f} lb]")
    S.text(110, 110, "Metal detector conveyor P1-406 (CCP-1), built in house around a used search head, 1 off, rev B", 34, bold=True)
    S.text(110, 150, "Closed, labelled packs pass a refurbished head on a 6 in belt; the frame keeps all metal out of the metal-free zone; detects go into a locked bin", 18)
    img(S, IMG / "cv_full.png", 110, 190, 820, 736)
    img(S, IMG / "cv_back.png", 940, 190, 820, 736)
    S.table(1800, 190, [("DESIGN DATA", 330), ("", 900)], [
        ("Duty", f"check every pack ({SHK['d']:.0f} Ø shakers, {JAR['d']:.1f} Ø jars) after the labeler P1-404, {RATE:.0f} packs / min"),
        ("Head", f"P1-418 used, aperture {HEAD['ap_w']:.0f} x {HEAD['ap_h']:.0f}, test pieces Fe 1.5 / NFe 2.0 / SS 2.5; own supply"),
        ("Belt", f"PU 2 mm FDA 6 in, {C['v_mpm']:.0f} m/min, Ø{PUL['d']:.0f} pulleys, UHMW bed on FRP rails through the head; spliced in place"),
        ("Frame", f"2 bolted 304 end frames outside |x| {X_STATIC:.0f}, low spine and head stand with G10 insulator; belt top z {Z_BELT:.0f}"),
        ("Reject", f"stop and push: 24 V actuator {REJ['stroke']:.0f} stroke into a locked bin, bin-entry eye confirms"),
        ("Controls", "CLICK PLC, START / STOP / E-stop / QA reset key, 3-colour stack light + buzzer, fail-safe head relays"),
        ("Supply", f"120 V 1-ph cord and plug, {ELE['A']:.1f} A; head on its own receptacle"),
        ("Footprint", f"{2 * SIDE['x1']:.0f} x {2 * BIN['y1'] + 40:.0f}; height {POLE['h'] + Z_BELT + 40:.0f} (stack light)"),
        ("Rev B", "full shop set: bolted end frames, FRP / UHMW metal-free zone, splice-in-place belt, electric reject with bin-entry confirm"),
    ], fs=13, rh=24)
    S.table(1800, 500, [("SHEET", 150), ("TITLE", 860), ("FILE", 220)], [(n, t, n + " svg / PDF") for n, t in sheets], "SHEET INDEX", fs=13, rh=24)
    S.notes(110, 1000, 1570, [
        "Units mm [in]. Third-angle projection. Tolerances in the title block unless noted. Welding to AWS D1.6.",
        "No product contact: packs are closed and labelled. Finish #4 or bead blast, passivated ASTM A967.",
        "Cut files (DXF) in dxf/ in mm and inch; 3D: cad/ (STEP per part, P1-406-ASM.step/.glb); generator: design.py, model.py, sh_*.py.",
        "The used head must be in hand (or its drawing confirmed) before the head stand 104 and the side-plate MFZ ends are cut: aperture, housing length, lug positions.",
        "Release for build: drawings checked, ITP P1-406-900 attached to the traveler, materials certified, program P1-406-FW-01 loaded, head validated (T9, T15-T18).",
    ], "GENERAL NOTES", fs=13)
    S.save(DWG / "P1-406-000_cover.svg")
