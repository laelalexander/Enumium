"""P1-404-000 cover + index, -003 assembly and setup, -800 bought parts and hardware, -900 ITP + calculations."""
import base64
import math
import textwrap
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

IMG = DWG / "img"
C = calcs()
M_MADE = sum(MASS.values())
M_BOUGHT = 2 * 0.9 + 1.4 + 0.1 + 0.6 + 0.5 + 2.6 + 0.1 + 0.2          # rollers, motor + controller + supply, gap sensor, kit, idler, box, start sensor, knob
M_TOT = M_MADE + M_BOUGHT
JAR, SHK = CONT["jar-12"], CONT["shaker-250"]
MM_REV = math.pi * ROL["d"] * MOT["T"] / ROLLER_T
PITCH = {k: v["lab_L"] + LAB["gap"] for k, v in CONT.items()}
F_IDL = IDL["F"]
T_HOLD = 0.6 * 9.81 * 0.05 * ROL["d"] / 2000                       # jar weight x rolling coefficient at the roller (N·m), small
SLIP_MARGIN = (F_IDL + 0.6 * 9.81) * 0.6 / (C["F_surf"])           # traction (urethane μ ≈ 0.6 on PET/glass) over the surface drag


def img(S, path, x, y, w, h):
    b = base64.b64encode(path.read_bytes()).decode()
    S.add(f'<image href="data:image/png;base64,{b}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')


def assembly():
    S = sheet("P1-404-003", "ASSEMBLY, THREAD-UP AND CHANGEOVER", scale="NTS", material="see item list", finish="-",
              mass=f"{M_TOT:.0f} kg [{M_TOT * 2.2046:.0f} lb]")
    cap = ["1  Frame", "2  Rollers + motor", "3  Liner drive + guard", "4  Web path", "5  Peel plate + sensor", "6  Idler arm", "7  Controls box", "8  Label roll + jar"]
    for i in range(8):
        x, y = 110 + (i % 4) * 420, 110 + (i // 4) * 400
        img(S, IMG / f"lb_s{i + 1}.png", x, y + 10, 400, 373)
        S.add(f'<rect x="{x}" y="{y + 10}" width="400" height="373" fill="none" stroke="#b0bec5"/>')
        S.add(f'<rect x="{x + 2}" y="{y + 12}" width="{len(cap[i]) * 10 + 10}" height="30" fill="#fff" fill-opacity="0.85"/>')
        S.text(x + 8, y + 34, cap[i], 17, bold=True)
    S.text(110, 925, "orange = parts added in that step; ghosted = parts still to come", 13, color="#607d8b")
    steps = [
        ("1", "Base 101 on the bench TBL-2; side plates 102 (-x) and 103 (+x) on the base with 3 screws each from below; tie rod 104 between them; end fence 105 at S or J.",
         "H1 x4 M6 8 N·m; H2 x6 M5 5 N·m; H3 x2 M8 15 N·m; H10 x2 M5 3 N·m", "plates parallel 0.05 over 320 (bore R holes in line, ITP T3); base flat on the bench"),
        ("2", "Bearings 6001-2RS in the R holes of both plates; drive rollers P1-425 (key flat at -x) with 30T pulleys and rings; motor P1-426 on the -x inner face, 15T pulley; belt 1 375-3M round A, motor, B.",
         "H4 x4 M5 4 N·m (slots: tension); H6 x2 per pulley 1.5 N·m + Loctite 243; H7 rings", "belt 1 deflects 3 at 10 N mid-span; rollers turn together, run-out ≤ 0.05 (T6)"),
        ("3", "Housings 201 into H1 (liner drive) and H2 (rewind) with bearings; liner drive 202 with the 18T pulley; belt 2 261-3M from the second 30T on roller B; pinch lever 203 with its spring; guard 204 on standoffs.",
         "H5 x6 M5 4 N·m (slots: belt 2); H6; H12 x6 M4 1.5 N·m", "liner surface speed = roller surface speed (mark test, T9); pinch closes on the knurl"),
        ("4", "Unwind spindle 301 (3 screws), hub 302 with flange, collar 303; brake leaf 304 with felt; rewind shaft 305 in housing H2 with hub 302 and O-ring pulleys 306 + PU belt; guide roller 307.",
         "H8 x3 M4 2.5 N·m; H11 M8 10 N·m; H14 2 N·m", "unwind turns with a light even drag (felt); rewind slips on the O-ring belt when held"),
        ("5", "Peel bracket 402 at PS (shaker) or PJ (jar) holes; peel plate 401 on the bracket arm; gap sensor P1-427 on the plate edge over the window.",
         "H9 x4 M5 4 N·m", "tip 15 behind the container top, 1 above (T7); fork straddles the web edge, teach on liner"),
        ("6", "Pivot shaft 403 between the plates; idler arms 404 on it with nylon washers; idler shaft 405 with the idler roller P1-455; knob on the +x arm; sensor bracket 406 and start sensor P1-457 in the 103 plate.",
         "H3 x2 M8 15 N·m; H14 x2 M5 2 N·m", "arm drops onto the container under its own weight; B2 switches with the arm down on both containers (T12)"),
        ("7", "Controls box P1-456 on the +x end of the base (2 screws inside the floor); G1 and terminals on the back wall, A1 on the floor; cables W0-W4 per E01.",
         "H13 x2 M6 3 N·m", "wiring per E01, < 0.1 Ω PE (T13); program P1-404-FW-01 loaded"),
        ("8", "Label roll on the unwind hub (labels out, wound out); thread up per the card; liner end into the rewind hub slot, 2 turns; FEED to the first gap. Lay the first container on the rollers.",
         "-", "label lands square on the container with ≤ 1 overlap error (T15-T17)"),
    ]
    S.table(1830, 110, [("STEP", 60), ("HARDWARE / TORQUE", 640), ("CHECK BEFORE THE NEXT STEP", 870)], [(a, c, d) for a, b, c, d in steps],
            "ASSEMBLY STEPS: HARDWARE AND CHECKS", 12, 24)
    S.notes(1830, 360, 1570, [b for a, b, c, d in steps], title="ASSEMBLY STEPS: OPERATIONS", fs=12)
    import sh_ga
    vt = S.view(452, 1880, SC(2.5), "THREAD-UP (2:5), SEEN FROM +X: LABEL WEB DASHED RED, LINER DASH-DOT", (520, 1000))
    sh_ga.side(vt)
    zt = z_top(JAR["d"]) + 1.0
    for txt, at, to in (("1 UNWIND (labels out, off the top)", (UNW["y"] + 60, UNW["z"] + 60), (350, 470)),
                        ("2 OVER GUIDE ROLLER 307", (G1["y"] + 10, G1["z"]), (350, 300)),
                        ("3 UNDER THE GAP FORK B1", (57.0, zt + 8), (350, 255)),
                        ("4 ROUND THE PEEL TIP, LINER BACK UNDER", (PEEL["tip_y"], zt), (350, 210)),
                        ("5 NIP: LINER DRIVE 202 + PINCH 203", (LD["y"], LD["z"] + LD["d"] / 2), (350, 160)),
                        ("6 REWIND HUB 302 (slot, 2 turns)", (REW["y"] + 40, REW["z"]), (350, 80))):
        vt.leader(at, to, [txt], 12)
    S.notes(1830, 1380, 1570, [
        "Thread-up: unwind (labels outward, coming off the top) → over the guide roller 307 → under the gap fork → over the peel plate to the tip → round the tip, liner back under the plate → "
        "between the liner drive 202 and the pinch 203 (lift the lever) → rewind hub 302. Cut the first labels off the liner for 300 mm.",
        f"Changeover shaker ↔ jar (about 3 min, power off): fence 105 to its S or J holes (2 screws); peel bracket 402 to PS or PJ (2 screws); S2 to S or J; change the label roll; "
        f"FEED to the first gap. Nothing else changes: the rollers and the idler arm suit both diameters ({SHK['d']:.0f} and {JAR['d']:.1f}).",
        f"Each cycle: lay the container on the rollers against the fence, lower the arm with the knob; the label runs ({C['jar-12']['t_lab']:.1f} s jar) and stops at the next gap; lift the arm, take the container. "
        f"About {60 / C['t_cycle']:.0f} per minute.",
        "Cleaning: wipe down only; no product contact (the container is closed and capped). Keep adhesive off the rollers: clean with IPA on a cloth, never solvent on the urethane.",
        "Care: belts every 6 months (tension, wear); felt pad yearly; replace the urethane roller covers when the Ø is down 0.3 (labels start to skew).",
    ], "THREAD-UP, CHANGEOVER, OPERATION, CARE", fs=12)
    S.table(1830, 1000, [("ITEM", 50), ("DESCRIPTION", 560), ("QTY", 40), ("WHERE", 600), ("TORQUE", 320)],
            [(h, d[:84], q, w[:70], t) for h, d, g, q, w, t in HARDWARE], "HARDWARE AND TORQUES (all A2 stainless; full spec on 800)", 12, 22)
    S.save(DWG / "P1-404-003_assembly.svg")


def hardware():
    S = sheet("P1-404-800", "BOUGHT PARTS AND HARDWARE", scale="NTS", material="-", finish="-", mass="-")
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
    S.text(110, y, f"Bought parts for one labeler ≈ ${tot:,.0f}", 16, bold=True)
    y2 = y + 60
    S.table(110, y2, [("ITEM", 50), ("DESCRIPTION", 560), ("STANDARD", 210), ("QTY", 40), ("WHERE", 640), ("TORQUE", 160)],
            [(h, d, g, q, w, t) for h, d, g, q, w, t in HARDWARE], "HARDWARE (all A2 / 18-8 stainless)", 12, 22)
    mat = [
        ("304 plate 8 mm (base 101)", "640 x 360", "laser blank"),
        ("304 plate 10 mm (side plates 102, 103)", "365 x 442 + 240 x 257", "laser blanks, bore R/H/U on a mill"),
        ("304 plate 6 mm (pinch lever 203, peel bracket 402)", "60 x 20 + 66 x 38 + 210 x 30", "laser blanks"),
        ("304 sheet 1.5 / 2 / 3 (guard 204, peel 401, bracket 406)", "365 x 260; 120 x 100; 60 x 30", "laser + brake"),
        ("304 round Ø75, Ø65, Ø35, Ø16, Ø12 (housings, spindle, liner drive, shafts)", "2 x 52; 250; 260; 310 + 300 + 160; 302", "machine shop stock"),
        ("304 flat 25 x 8 (idler arms 404)", "2 x 231", "1 length 0.5 m"),
        ("UHMW-PE natural FDA Ø80 / Ø55 / Ø45 / Ø25 rod, 8 plate", "2 x 150; 2 x 25; 2 x 12; 130; 160 x 40", "offcuts"),
        ("Spring strip 304 0.8 1/2 hard + felt 5", "30 x 70 + 30 x 30", "with the brake"),
    ]
    S.table(1900, y2, [("MATERIAL", 640), ("PER LABELER", 440), ("BUY", 340)], mat, "RAW MATERIAL (made parts)", 12, 22)
    S.table(1900, y2 + 22 * (len(mat) + 1) + 60, [("TAG", 90), ("WHERE / NOTE", 1330)], [(t, n) for t, d, m, p, q, u, n in BOUGHT if n],
            "PURCHASING AND MOUNTING NOTES", 12, 22)
    S.save(DWG / "P1-404-800_bought_hardware.svg")


def itp():
    S = sheet("P1-404-900", "INSPECTION AND TEST PLAN, CALCULATIONS", scale="NTS", material="-", finish="-", mass="-")
    tests = [
        ("T1", "Material certs 304 (EN 10204 3.1); UHMW FDA letter; roller cover hardness 70A", "on file", "receiving", "QC"),
        ("T2", "Side plates: R, H, U holes bored together (stacked) to the drawing", "±0.02 position", "after machining", "QC"),
        ("T3", "Roller axes parallel (both plates on the base, tie rod in)", "0.05 / 320", "step 1", "assy"),
        ("T4", "Housing 201 bore Ø28 H7, spigot Ø40 g6; liner drive Ø30 h8, journals Ø12 h6", "per 200", "after machining", "QC"),
        ("T5", "Drive roller Ø50 matched pair (P1-425 view R)", "±0.05, 0.05 TIR", "receiving", "QC"),
        ("T6", "Rollers turn together, smooth, no tight spot; belt 1 and 2 deflection 3 mm at 10 N", "pass", "steps 2-3", "assy"),
        ("T7", "Peel tip: 15 behind container top centre, 1 above, square to the roller axes (S and J)", "±0.5", "step 5", "assy"),
        ("T8", "Unwind drag: roll does not overrun when M1 stops at speed", "pass", "step 4", "assy"),
        ("T9", "Liner speed = container surface speed: mark web and container, run 10 labels", "≤ 1 % drift", "commissioning", "assy"),
        ("T10", "Rewind takes up the liner at full roll and empty roll (O-ring slip)", "no slack", "commissioning", "assy"),
        ("T11", "Gap sensor taught on the liner; detects every gap at 150 mm/s, both rolls", "100 / 100", "commissioning", "elec"),
        ("T12", "Start sensor B2: switches with the arm down on shaker and jar, off with the arm up 10°", "pass", "commissioning", "elec"),
        ("T13", "Wiring vs E01; PE continuity: stud to -x plate, base, M1 body", "< 0.1 Ω", "before power", "elec"),
        ("T14", "Hi-pot / insulation, cord to PE (G1 disconnected)", "> 1 MΩ at 500 V", "before power", "elec"),
        ("T15", "E-stop stops M1; no restart on release until FEED", "pass", "commissioning", "elec"),
        ("T16", "Arm lifted mid-label: M1 stops at once", "< 50 ms", "commissioning", "elec"),
        ("T17", f"Label placement on 20 shakers and 20 jars: skew, start position, overlap ({SHK['lab_L']:.0f} / {JAR['lab_L']:.0f} long)", "≤ 1 mm skew, ±2 start", "first run", "QA"),
        ("T18", "Label bubbles / flags after 24 h", "none > 2 mm", "first run + 24 h", "QA"),
        ("T19", f"Rate: {C['t_cycle']:.1f} s cycle, ≥ {60 / C['t_cycle']:.0f} /min for 10 min (capper rate {60 / 4.4:.0f} /min)", "pass", "first run", "QA"),
        ("M1", "Roller covers: Ø check, IPA clean", "Ø ≥ 49.7", "weekly", "maint"),
        ("M2", "Belts, felt, O-ring belt wear", "-", "6 months", "maint"),
    ]
    S.table(110, 110, [("TEST", 60), ("WHAT IS CHECKED", 860), ("LIMIT", 270), ("WHEN / PART", 230), ("BY", 70), ("RESULT / SIGN", 200)],
            [t + ("",) for t in tests], "INSPECTION AND TEST PLAN (record results here or in the MES)", fs=14, rh=30)
    setup = [(k, v["setting"], f"Ø{v['d']:.1f} x {v['h']:.1f}", f"{v['lab_H']:.0f} x {v['lab_L']:.0f}", f"{PITCH[k]:.0f}", f"{C[k]['z_c']:.1f}", f"{C[k]['z_top']:.1f}",
              f"{C[k]['contact']:.1f}°", f"{C[k]['fence']:.1f}", f"{C[k]['wrap']:.2f}", f"{C[k]['labels_roll']:.0f}")
             for k, v in CONT.items()]
    S.table(110, 110 + 30 * (len(tests) + 1) + 70, [("CONTAINER", 160), ("SET", 50), ("SIZE", 150), ("LABEL H x L", 140), ("PITCH", 80), ("AXIS z", 100), ("TOP z", 100),
                                                    ("CONTACT", 100), ("FENCE x", 100), ("WRAP", 80), ("LABELS / ROLL", 140)],
            setup, "SETUP TABLE (z above the bench top; fence x from the label centre)", fs=14, rh=30)
    calc = [
        ("Roller / motor speed", f"{C['n_roll']:.1f} / {C['n_mot']:.1f} rpm", f"{LAB['speed']:.0f} mm/s surface; 30T / 15T belt 1"),
        ("Liner drive speed", f"{C['v_liner']:.1f} mm/s", f"30T → 18T on Ø{LD['d']:.0f}: ratio error {C['ratio_err'] * 100:.2f} % (any container Ø)"),
        ("Belt lengths", f"{C['L_b1']:.1f} / {C['L_b2']:.1f} mm", f"chosen {BELT1} / {BELT2}; slots take up ± 3"),
        ("Surface drag", f"{C['F_surf']:.1f} N", "peel 2, idler + rolling 1.0, rewind slip 2 N"),
        ("Motor torque needed", f"{C['T_mot']:.3f} N·m", "ClearPath SDSK 2311: ≈ 0.8 N·m continuous at 115 rpm, 24 V: SF > 10"),
        ("Container traction", f"SF {SLIP_MARGIN:.1f}", f"(idler {F_IDL:.0f} N + jar weight) x μ 0.6 over the drag: container turns without slip"),
        ("Step size", f"{MM_REV / 800:.3f} mm", f"{MM_REV:.1f} mm per motor rev, 800 steps: gap 3 mm = {3 / (MM_REV / 800):.0f} steps"),
        ("Label time", f"{C['shaker-250']['t_lab']:.2f} / {C['jar-12']['t_lab']:.2f} s", "shaker / jar, at 150 mm/s incl. 20 mm run-in"),
        ("Wrap", f"{C['shaker-250']['wrap']:.2f} / {C['jar-12']['wrap']:.2f} turns", "labels do not overlap (wrap < 1)"),
        ("Cycle / rate", f"{C['t_cycle']:.1f} s / {60 / C['t_cycle']:.0f} per min", "load 1.0, arm 0.5, label 1.8, unload 1.0 s"),
        ("Labels per roll", f"{C['shaker-250']['labels_roll']:.0f} / {C['jar-12']['labels_roll']:.0f}", f"200 OD on a 3 in core, {LAB['t']:.2f} web"),
        ("Electrical load", f"{ELE['A']:.1f} A at 120 V", "fuse 3 A T; cord 14 AWG; 24 V 6.5 A supply"),
        ("Mass", f"{M_TOT:.0f} kg [{M_TOT * 2.2046:.0f} lb]", "bolted to the bench with 4 x M6"),
    ]
    S.table(1840, 110, [("CALCULATION", 320), ("RESULT", 360), ("NOTE / LIMIT", 900)], calc, "DESIGN CALCULATIONS (design.py, sh_doc.py)", fs=13, rh=30)
    S.save(DWG / "P1-404-900_itp.svg")


def cover_sheet(sheets):
    S = sheet("P1-404-000", "P1-404 WRAP LABELER: DRAWING SET", scale="NTS", material="304 frame, UHMW hubs, urethane rollers", finish=FIN_NPC,
              mass=f"{M_TOT:.0f} kg [{M_TOT * 2.2046:.0f} lb]")
    S.text(110, 110, "Wrap labeler for round containers P1-404, built in house, 1 off, rev B", 34, bold=True)
    S.text(110, 150, "Container turns on two driven rollers; one servo-stepper drives the rollers and the liner so the label speed always equals the surface speed", 18)
    img(S, IMG / "lb_full.png", 110, 190, 820, 736)
    img(S, IMG / "lb_back.png", 940, 190, 820, 736)
    S.table(1800, 190, [("DESIGN DATA", 330), ("", 900)], [
        ("Duty", f"wrap labels on shakers ({SHK['lab_H']:.0f} x {SHK['lab_L']:.0f}) and jars ({JAR['lab_H']:.0f} x {JAR['lab_L']:.0f}) after the capper P1-412"),
        ("Drive", f"ClearPath SDSK NEMA 23 at 24 V, belt 1 to both Ø{ROL['d']:.0f} urethane rollers, belt 2 to the Ø{LD['d']:.0f} liner drive; {LAB['speed']:.0f} mm/s"),
        ("Web", f"3 in core roll ≤ {LAB['od_max']:.0f} OD, felt brake; peel plate 2 mm, tip R1; O-ring slip rewind; gap fork sensor"),
        ("Container", f"lies on the rollers against the UHMW fence (S / J), silicone idler Ø{IDL['d']:.0f} on a weighted arm ({F_IDL:.0f} N)"),
        ("Controls", "ClearCore: start on arm down, stop at the next gap; FEED, S/J, E-stop, ON/OFF; one 24 V supply"),
        ("Supply", f"120 V 1-ph cord and plug, {ELE['A']:.1f} A"),
        ("Plant interface", f"on the bench TBL-2 (top {Z_BENCH:.0f} AFF), 4 x M6; footprint {BASE['w']:.0f} x {BASE['d'] + SPL['y1'] - 180:.0f}; height {SPL['z1']:.0f}"),
        ("Rate", f"{60 / C['t_cycle']:.0f} per min one operator (capper {60 / 4.4:.0f} per min)"),
        ("Rev B", "full shop set: matched drive rollers, liner speed locked to the rollers, S/J changeover by 2 screw pairs, controls box on the +x end"),
    ], fs=13, rh=24)
    S.table(1800, 500, [("SHEET", 150), ("TITLE", 860), ("FILE", 220)], [(n, t, n + " svg / PDF") for n, t in sheets], "SHEET INDEX", fs=13, rh=24)
    S.notes(110, 1000, 1570, [
        "Units mm [in]. Third-angle projection. Tolerances in the title block unless noted. Welding (peel bracket only) to AWS D1.6.",
        "No product contact: the container is closed and capped. Finish #4 or bead blast, passivated ASTM A967.",
        "Cut files (DXF) in dxf/ in mm and inch; 3D: cad/ (STEP per part, P1-404-ASM.step/.glb); generator: design.py, model.py, sh_*.py.",
        "Bought parts marked 'confirm' must be checked against the supplier drawing before the matching made part is cut (motor flange, roller shaft ends, box size).",
        "Release for build: drawings checked, ITP P1-404-900 attached to the traveler, materials certified, program P1-404-FW-01 loaded.",
    ], "GENERAL NOTES", fs=13)
    S.save(DWG / "P1-404-000_cover.svg")
