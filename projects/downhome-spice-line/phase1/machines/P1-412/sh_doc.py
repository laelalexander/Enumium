"""P1-412-000 cover + index, -003 assembly and setup, -800 bought parts and hardware, -900 ITP + calculations."""
import base64
import math
import textwrap
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

IMG = DWG / "img"
C = calcs()
M_MADE = sum(MASS.values())
M_BOUGHT = 3.6 + 0.8 + 0.6 + 0.4 + 1.2 + 0.6 + 0.3 + 0.2      # gearmotor, clutch + inserts, rail + spring, toggle, controls, drive, switch, knob
M_TOT = M_MADE + M_BOUGHT
M_CARR = sum(MASS.get(p, 0) for p in ("P1-412-201", "P1-412-202", "P1-412-203", "P1-412-204", "P1-412-301", "P1-412-302", "P1-412-303", "P1-412-304")) + 3.6 + 0.8 + 0.15
W_CARR = M_CARR * 9.81
F_NET = GAS["F"] - W_CARR
F_LINK = F_NET + 40.0                                  # pulling down against the spring + 40 N chuck float spring
F_KNOB = F_LINK * LEV["a"] / LEV["L"]
T_CYCLE = 1.0 + 0.7 + 1.2 + 0.5 + 1.0                  # place, clamp, lower + cap, release, unclamp + remove (s)
MP_RAIL = (F_LINK * CAR["lug_x"] + 2.5 * 1000) / 1000  # roll moment from the link offset + cap reaction (N·m)
MGN = dict(C=6.37, C0=9.22, MR=61.0, MP=38.0, MY=38.0)  # MGN15H (HIWIN catalogue, confirm)


def img(S, path, x, y, w, h):
    b = base64.b64encode(path.read_bytes()).decode()
    S.add(f'<image href="data:image/png;base64,{b}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')


def assembly():
    S = sheet("P1-412-003", "ASSEMBLY, SETUP AND CHANGEOVER", scale="NTS", material="see item list", finish="-",
              mass=f"{M_TOT:.0f} kg [{M_TOT * 2.2046:.0f} lb]")
    cap = ["1  Base weldment", "2  Rail, spring, stop", "3  Carriage", "4  Drive line", "5  Chuck guard", "6  Lever + link", "7  Nest + clamp", "8  Controls + switch"]
    for i in range(8):
        x, y = 110 + (i % 4) * 420, 110 + (i // 4) * 560
        img(S, IMG / f"cp_s{i + 1}.png", x, y + 10, 400, 520)
        S.add(f'<rect x="{x}" y="{y + 10}" width="400" height="520" fill="none" stroke="#b0bec5"/>')
        S.add(f'<rect x="{x + 2}" y="{y + 12}" width="{len(cap[i]) * 10 + 10}" height="30" fill="#fff" fill-opacity="0.85"/>')
        S.text(x + 8, y + 34, cap[i], 17, bold=True)
    S.text(110, 1250, "orange = parts added in that step; ghosted = parts still to come", 13, color="#607d8b")
    steps = [
        ("1", "Base weldment 100 on the bench TBL-1 at the marked position, column at the back; 4 bolts through the bench top.",
         "H1 x4 M8 18 N·m", "base flat on the bench (no rock); column plumb 0.5 / 600 both ways"),
        ("2", "Rail MGN15 on the seat bar 106, pushed against the reference edge, bolts from the middle out. Block on the rail (keep the retainer until the rail is in). "
              "Gas spring base bracket 505 on the base; stop rod 503 screwed into hole D with jam nuts under and over; flip stop 504 on its pin.",
         "H2 x12 M3 1.2 N·m; H8 x2 M8 18 N·m; H11 M16 40 N·m", "block runs the full rail with no tight spot; rail straight 0.05 / 500 (dial on the block)"),
        ("3", "Carriage weldment 200 on the block (face B to the block); gas spring between bracket 505 and the shelf ball stud (rod end up).",
         "H3 x4 M3 + Loctite 243 1.2 N·m", "carriage rises to the top by itself and stops on the spring end of stroke"),
        ("4", "Gearmotor P1-422 on the shelf, shaft down through Ø30 H8; clutch on the motor shaft; stub shaft 301 in the clutch; chuck adapter 302 + float spring on the spigot; urethane insert J or S.",
         "H4 x4 10-32 3 N·m; H12 x5 M6 4 N·m (adapter screw no Loctite)", "chuck face run-out ≤ 0.1 TIR; adapter slides 12 on the spigot and springs back"),
        ("5", "Guard 303 on 3 standoffs 304 under the shelf.", "H5 x3 M5 3 N·m (PC: no more)", "guard clears the chuck 19 all round; no gap > 6 at the bottom edge with a jar in place"),
        ("6", "Lever 501 in the clevis with the shoulder bolt and 2 nylon washers; link 502 with rod ends between the lever pin and the carriage lug 204; knob on the lever.",
         "H9 8 N·m (thread only); H10 x2 M8 12 N·m", "lever swings free; carriage reaches the stop rod with the lever 1-2° above its lowest"),
        ("7", "Nest plate 401 and V-block 402 at setting J (or S) with 2 countersunk screws; toggle bracket 404 and toggle clamp P1-450; pad 403 on the spindle thread.",
         "H6 x2 M8 10 N·m; H7 x8 M6 8 N·m", "pad centres the jar in the V within 0.5; container upright"),
        ("8", "Controls P1-451 at the front-left (2 screws through the box floor), drive A1 inside; limit switch P1-452 on the column (rivnuts); cables W0-W2 per E01.",
         "H13 x2 M6 3 N·m; H14 x2 M4 2 N·m", "B1 operates with the carriage within 5 of the top; < 0.1 Ω PE; ITP T12-T16"),
    ]
    S.table(1830, 110, [("STEP", 60), ("HARDWARE / TORQUE", 560), ("CHECK BEFORE THE NEXT STEP", 950)], [(a, c, d) for a, b, c, d in steps],
            "ASSEMBLY STEPS: HARDWARE AND CHECKS", 12, 24)
    S.notes(1830, 360, 1570, [b for a, b, c, d in steps], title="ASSEMBLY STEPS: OPERATIONS", fs=12)
    S.notes(110, 1290, 1640, [
        "Changeover shaker ↔ jar (about 5 min, plug pulled): move the V-block to its S or J holes (2 screws); swap the urethane insert (3 set screws); flip the stop block 504 up (shaker) or down (jar); set the clutch torque.",
        f"Clutch torque: shaker {CONT['shaker-250']['T']:.1f} N·m [{CONT['shaker-250']['T_lbin']:.0f} lbf·in], jar {CONT['jar-12']['T']:.1f} N·m [{CONT['jar-12']['T_lbin']:.0f} lbf·in]. Set on the clutch scale, cap 10 containers, check each with the torque tester P1-402 (ITP T19), adjust.",
        "Each cycle: stand the container in the V, push the toggle clamp (left hand), pull the lever (right hand) until the stop, hold about 1 s after the clutch slips, release, pull the clamp back, remove.",
        "Cleaning: wipe down only (no product contact with caps on). Remove the insert weekly and wash it. Do not hose the controls box.",
        "Lubrication: MGN block has a seal and a reservoir: grease every 6 months through the nipple (NSF H1). Check the gas spring force yearly (carriage must rise on its own).",
    ], "OPERATION, CHANGEOVER, CARE", fs=12)
    S.table(1830, 960, [("ITEM", 50), ("DESCRIPTION", 560), ("QTY", 40), ("WHERE", 600), ("TORQUE", 320)],
            [(h, d[:84], q, w[:70], t) for h, d, g, q, w, t in HARDWARE], "HARDWARE AND TORQUES (all A2 stainless; full spec on 800)", 12, 22)
    S.save(DWG / "P1-412-003_assembly.svg")


def hardware():
    S = sheet("P1-412-800", "BOUGHT PARTS AND HARDWARE", scale="NTS", material="-", finish="-", mass="-")
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
    S.text(110, y, f"Bought parts for one capper ≈ ${tot:,.0f}", 16, bold=True)
    y2 = y + 60
    S.table(110, y2, [("ITEM", 50), ("DESCRIPTION", 560), ("STANDARD", 210), ("QTY", 40), ("WHERE", 640), ("TORQUE", 160)],
            [(h, d, g, q, w, t) for h, d, g, q, w, t in HARDWARE], "HARDWARE (all A2 / 18-8 stainless)", 12, 22)
    mat = [
        ("304 plate 12 mm (base 101)", "400 x 350", "laser blank"),
        ("304 plate 10 mm (carriage plate 201, shelf 202, lug 204)", "120 x 170 + 200 x 174 + 30 x 35", "laser blanks"),
        ("304 plate 6 / 8 mm (gussets, cap, clevis, toggle bracket)", "per cut lists 100, 200, 400", "laser blanks"),
        ("304 sq tube 2 in x 11 ga (column 102)", "650", "1 length 1 m"),
        ("304 flat 30 x 12 (seat bar 106), 25 x 10 (lever 501)", "520 + 445", "1 length each"),
        ("304 round Ø115 (chuck adapter), Ø25 (stub), Ø16 (stop rod), Ø10 (link, standoffs)", "50 / 75 / 280 / 340 + 36", "machine shop stock"),
        ("UHMW-PE natural FDA 8 / 20 / 60 mm", "205 x 140; 60 x 40; 60 x 100", "offcuts"),
        ("Polycarbonate tube Ø150 x 3 + sheet 6 mm (guard)", "84 long + Ø190 ring", "with the guard order"),
    ]
    S.table(1900, y2, [("MATERIAL", 640), ("PER CAPPER", 440), ("BUY", 340)], mat, "RAW MATERIAL (made parts)", 12, 22)
    S.table(1900, y2 + 22 * (len(mat) + 1) + 60, [("TAG", 90), ("WHERE / NOTE", 1330)], [(t, n) for t, d, m, p, q, u, n in BOUGHT if n],
            "PURCHASING AND MOUNTING NOTES", 12, 22)
    S.save(DWG / "P1-412-800_bought_hardware.svg")


def itp():
    S = sheet("P1-412-900", "INSPECTION AND TEST PLAN, CALCULATIONS", scale="NTS", material="-", finish="-", mass="-")
    tests = [
        ("T1", "Material certs 304 (EN 10204 3.1); UHMW and PC FDA letters", "on file", "receiving", "QC"),
        ("T2", "Column square to the base, top cap parallel", "0.5 / 600", "after welding", "QC"),
        ("T3", "Seat bar face A flat and parallel to the column side", "0.05 / 0.1", "after machining", "QC"),
        ("T4", "Carriage face B flat; motor bore Ø30 H8 square to B and at 73.6 ±0.05", "0.02 / 0.05", "after machining", "QC"),
        ("T5", "Stub Ø12.70 h6, spigot Ø16 g6; adapter bore Ø16 H8, pocket Ø100 H9", "per 300", "after machining", "QC"),
        ("T6", "Rail straightness along the stroke (dial on the block)", "0.05 / 500", "step 2", "assy"),
        ("T7", "Chuck face run-out to the stub, on the clutch", "≤ 0.1 TIR", "step 4", "assy"),
        ("T8", "Chuck float: 12 mm travel, returns fully", "pass", "step 4", "assy"),
        ("T9", "Carriage rises by itself from the bottom of the stroke (gas spring)", "pass", "step 3", "assy"),
        ("T10", "Lowest carriage on the stop: chuck face 6 below the cap top (shaker and jar)", "±1", "step 6", "assy"),
        ("T11", "Container centred under the chuck (V-block S and J)", "≤ 0.5", "step 7", "assy"),
        ("T12", "Wiring vs E01; PE continuity to the column and the motor frame", "< 0.1 Ω", "before power", "elec"),
        ("T13", "Hi-pot / insulation, cord to PE (drive disconnected)", "> 1 MΩ at 500 V", "before power", "elec"),
        ("T14", "E-stop stops the chuck; motor does not restart on release until S1 cycled", "pass", "commissioning", "elec"),
        ("T15", "Limit switch: chuck stationary with the carriage up; runs within 5 mm of travel", "pass", "commissioning", "elec"),
        ("T16", f"Chuck speed at MAX ({GM['rpm']:.0f} rpm, tach)", "±10 rpm", "commissioning", "elec"),
        ("T17", "Guard: no finger access to the chuck (ISO 13857) with and without a container", "pass", "commissioning", "QC"),
        ("T18", "Hand force at the knob through the stroke", f"≤ {F_KNOB * 1.3:.0f} N", "commissioning", "QA"),
        ("T19", f"Removal torque on 10 caps per size: shaker {CONT['shaker-250']['T']:.1f}, jar {CONT['jar-12']['T']:.1f} N·m (tester P1-402)", "±15 %", "per changeover", "QA"),
        ("T20", "Cap straight, no cross-thread, liner seal: 30 containers, inverted 5 min", "no leak", "first run", "QA"),
        ("T21", f"Rate: {T_CYCLE:.1f} s cycle, ≥ {60 / T_CYCLE:.0f} /min for 10 min (filler rated 12 shakers, 8 jars /min)", "pass", "first run", "QA"),
        ("M1", "Clutch setting with the torque tester", "per T19", "hourly", "QA"),
        ("M2", "Grease the MGN block; gas spring force check; insert wear", "-", "6 months", "maint"),
    ]
    S.table(110, 110, [("TEST", 60), ("WHAT IS CHECKED", 860), ("LIMIT", 270), ("WHEN / PART", 230), ("BY", 70), ("RESULT / SIGN", 200)],
            [t + ("",) for t in tests], "INSPECTION AND TEST PLAN (record results here or in the MES)", fs=14, rh=30)
    setup = [(k, f"Ø{v['d']:.1f} x {v['h']:.1f}", f"{v['cap_d']:.0f} / {v['cap_h']:.0f}", v["nest"], f"{v['T']:.1f} [{v['T_lbin']:.0f}]",
              f"{C[k]['z_down']:.1f}", f"{C[k]['stroke']:.1f}", f"{vb_face(v['d']):.1f}", f"{C[k]['F_clamp']:.0f}")
             for k, v in CONT.items()]
    S.table(110, 110 + 30 * (len(tests) + 1) + 70, [("CONTAINER", 180), ("SIZE", 160), ("CAP Ø / H", 120), ("NEST", 70), ("TORQUE N·m [lbf·in]", 200),
                                                    ("SHELF DOWN z", 150), ("STROKE", 110), ("V FACE x", 120), ("CLAMP N", 110)],
            setup, "SETUP TABLE (z above the bench top; V face from the spindle axis)", fs=14, rh=30)
    calc = [
        ("Carriage mass / weight", f"{M_CARR:.2f} kg / {W_CARR:.0f} N", "plate, shelf, motor, clutch, chuck, guard (masses.json + bought)"),
        ("Gas spring net lift", f"{F_NET:.0f} N", f"{GAS['F']:.0f} N spring: carriage returns to the top unaided (needs > 0)"),
        ("Hand force at the knob", f"{F_KNOB:.0f} N", f"link {F_LINK:.0f} N x {LEV['a']:.0f} / {LEV['L']:.0f}; limit 50 N for repetitive pulls"),
        ("Lever swing / stroke", f"±{TH0:.1f}° / {STROKE_MAX:.1f} mm", f"shaker stroke {C['shaker-250']['stroke']:.1f}, jar {C['jar-12']['stroke']:.1f} (flip block)"),
        ("Motor torque vs clutch", f"{GM['T']:.1f} N·m vs set {CONT['jar-12']['T']:.1f} max", f"motor stalls only above the clutch slip; ratio {C['T_ratio']:.2f} of the clutch max"),
        ("Motor power", f"{C['P_motor']:.0f} W", f"1/8 HP = 93 W at {GM['rpm']:.0f} rpm"),
        ("Cap run-down time", f"{C['jar-12']['t_cap']:.2f} s", "≈ 1.5 turns of the cap thread at 190 rpm"),
        ("Clamp force needed", f"{C['jar-12']['F_clamp']:.0f} N (jar)", f"toggle holds {TGL['F_hold']:.0f} N: SF {TGL['F_hold'] / C['jar-12']['F_clamp']:.0f}"),
        ("Rail roll moment", f"{MP_RAIL:.1f} N·m", f"MGN15H MR {MGN['MR']:.0f} N·m (confirm): SF {MGN['MR'] / MP_RAIL:.0f}"),
        ("Rail pitch moment", f"{W_CARR * 0.0736 + 40 * 0.0736:.1f} N·m", f"weight + float spring at {abs(Y_BLK):.1f} from the rail; MP {MGN['MP']:.0f} N·m"),
        ("Cycle / rate", f"{T_CYCLE:.1f} s / {60 / T_CYCLE:.0f} per min", "place 1.0, clamp 0.7, cap 1.2, release 0.5, remove 1.0 s"),
        ("Electrical load", f"{ELE['A']:.1f} A at 120 V", "fuse 3 A T; cord 14 AWG"),
        ("Mass", f"{M_TOT:.0f} kg [{M_TOT * 2.2046:.0f} lb]", "bolted to the bench with 4 x M8"),
    ]
    S.table(1840, 110, [("CALCULATION", 360), ("RESULT", 400), ("NOTE / LIMIT", 820)], calc, "DESIGN CALCULATIONS (design.py, sh_doc.py)", fs=13, rh=30)
    S.save(DWG / "P1-412-900_itp.svg")


def cover_sheet(sheets):
    S = sheet("P1-412-000", "P1-412 SPINDLE CAPPER: DRAWING SET", scale="NTS", material="304 frame, UHMW nest, PC guard", finish=FIN_NPC,
              mass=f"{M_TOT:.0f} kg [{M_TOT * 2.2046:.0f} lb]")
    S.text(110, 110, "Bench spindle capper P1-412, built in house, 1 off, rev B", 34, bold=True)
    S.text(110, 150, "Lever-fed spinning chuck on a linear rail; slip clutch sets the cap torque; V-nest with a toggle clamp; 120 V cord and plug", 18)
    img(S, IMG / "cp_full.png", 110, 190, 780, 1014)
    img(S, IMG / "cp_back.png", 900, 190, 780, 1014)
    S.table(1800, 190, [("DESIGN DATA", 330), ("", 900)], [
        ("Duty", f"screw caps on shakers (53 mm cap, {CONT['shaker-250']['T']:.1f} N·m) and jars (89 mm cap, {CONT['jar-12']['T']:.1f} N·m) after the filler P1-401"),
        ("Drive", f"1/8 HP PMDC gearmotor {GM['rpm']:.0f} rpm, KB SCR drive, slip clutch 0.5-5 N·m, floating chuck 12 mm"),
        ("Motion", f"carriage on MGN15 rail, gas spring return, lever {LEV['L']:.0f} long ({F_KNOB:.0f} N at the knob), stop rod + flip block"),
        ("Nest", "UHMW V-block in 2 positions (S / J), push-pull toggle clamp with a V pad"),
        ("Controls", "E-stop, ON/OFF, pilot, speed pot; limit switch inhibits the chuck with the carriage up"),
        ("Supply", f"120 V 1-ph cord and plug, {ELE['A']:.1f} A"),
        ("Plant interface", f"on the bench TBL-1 (top {Z_BENCH:.0f} AFF), 4 x M8; footprint {BASE['w']:.0f} x {BASE['d']:.0f}; height {Z_CAP + 50:.0f} + lever"),
        ("Rate", f"{60 / T_CYCLE:.0f} per min one operator (filler 12 shakers / 8 jars per min)"),
        ("Rev B", "full shop set: rail carriage, slip clutch torque, floating chuck, V-nest clamp, standing controls box at the front-left"),
    ], fs=13, rh=24)
    S.table(1800, 500, [("SHEET", 150), ("TITLE", 860), ("FILE", 220)], [(n, t, n + " svg / PDF") for n, t in sheets], "SHEET INDEX", fs=13, rh=24)
    S.notes(110, 1250, 1570, [
        "Units mm [in]. Third-angle projection. Tolerances in the title block unless noted. Weld symbols AWS A2.4; welding to AWS D1.6.",
        "No product contact with the cap on; containers touch only UHMW (FDA). Finish #4 or bead blast, passivated ASTM A967.",
        "Cut files (DXF) in dxf/ in mm and inch; 3D: cad/ (STEP per part, P1-412-ASM.step/.glb); generator: design.py, model.py, sh_*.py.",
        "Bought parts marked 'confirm' must be checked against the supplier drawing before the matching made part is cut (motor face, clutch bores, rail holes).",
        "Release for build: drawings checked, ITP P1-412-900 attached to the traveler, materials certified.",
    ], "GENERAL NOTES", fs=13)
    S.save(DWG / "P1-412-000_cover.svg")
