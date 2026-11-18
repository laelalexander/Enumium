"""P1-401-000 cover + index, -003 assembly and changeover, -800 bought parts and hardware, -900 ITP + calculations."""
import base64
import math
import textwrap
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

IMG = DWG / "img"
C = calcs()
M_MADE = sum(MASS.values())
M_BOUGHT = sum(M_HEAD_BOUGHT.values()) + 12.0      # head drives + controls in the cabinet


def img(S, path, x, y, w, h):
    b = base64.b64encode(path.read_bytes()).decode()
    S.add(f'<image href="data:image/png;base64,{b}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')


def assembly():
    S = sheet("P1-401-003", "ASSEMBLY SEQUENCE, TOOLING CHANGE, CLEANING", scale="NTS", material="see item list", finish="-",
              mass=f"{C['m_tot']:.0f} kg [{C['m_tot'] * 2.2046:.0f} lb] empty")
    cap = ["1  Cabinet + feet", "2  Column + horseshoe", "3  Container stage", "4  Head plate + bearings",
           "5  Drives, bridge, guards", "6  Hopper", "7  Agitator", "8  Tooling, HMI, foot switch"]
    for i in range(8):
        x, y = 110 + (i % 4) * 420, 110 + (i // 4) * 560
        img(S, IMG / f"fl_s{i + 1}.png", x, y + 10, 400, 520)
        S.add(f'<rect x="{x}" y="{y + 10}" width="400" height="520" fill="none" stroke="#b0bec5"/>')
        S.add(f'<rect x="{x + 2}" y="{y + 12}" width="{len(cap[i]) * 10 + 10}" height="30" fill="#fff" fill-opacity="0.85"/>')
        S.text(x + 8, y + 34, cap[i], 17, bold=True)
    S.text(110, 1250, "orange = parts added in that step; ghosted = parts still to come", 13, color="#607d8b")
    steps = [
        ("1", "Cabinet 100 on its back on a pallet: screw the 4 feet P1-443 into the weld nuts, set to 60 [2.36] underside to floor. Stand it up, level the top ±0.5 mm/m with the feet.",
         "feet lock nuts hand-tight + 1/4 turn", "top level; door closes with 3 gap all round"),
        ("2", "Back panel 105 on the 4 weld studs (spacers + nylocs); mount the DIN parts per E03 and wire per E01/E02 on the bench before fitting if easier.",
         "H14 studs 6 N·m", "point-to-point check against the wire list (T13)"),
        ("3", "Column 200 on the top: backing plate 107 inside, 4 bolts through top and backing; horseshoe opening to the front (-y).",
         "H1 x4 M12, 70 N·m", "column plumb 0.5 / 1,000 both ways; shim under the base plate if needed"),
        ("4", "Stage: bushing blocks 703 under the top, rods 702 through, plate 701 on the rods; pin bar 704 on the rod clamp; plunger block 705 and plunger P1-434; sensor bracket 706 + P1-435.",
         "H10 x8 M6 6 N·m; H15 x2 M10 25 N·m; H13 x2; H11 M5 4 N·m", "stage slides free full stroke; plunger drops in each of the 4 holes"),
        ("5", "Spindle cartridge on the bench: press 6205 #1 on the spindle to the shoulder, inner spacer 310, 6205 #2, DIN 471 Ø25; slide into housing 302 from the top with outer spacer 309 between the bearings, DIN 472 Ø52, cap 308 with the seal.",
         "H11 M4 x4 3 N·m; press on the inner ring only", "spindle turns by hand, no end play felt"),
        ("6", "Hub 304: 2 x 6008 on the housing spigot (Loctite 641 in the hub), DIN 471 Ø40 under; bottom seal 25 x 40 x 7 lip down; 30T sprocket plate on the hub.",
         "H7 x4 M6 8 N·m + thread lock", "hub turns free; seal lip oiled with H1 grease"),
        ("7", "Housing + hub to head plate 301 from below; head plate onto the column cap 203.",
         "H3 x4 M8 20 N·m; H2 x4 M10 45 N·m", "spindle axis to the horseshoe centre ≤ 0.5 (check with a plumb or the tooling tube)"),
        ("8", "Gearmotor P1-414 with 15T sprocket under the plate; chain 52 L; tension by the slots. Bridge 307 on its 4 posts; servo P1-413 on the bridge; pulleys 20T / 40T; belt 450-5M-15; tension by the bridge slots.",
         "H6 x4 8 N·m; H5 x4 M10 45 N·m; H4 x4 M6 8 N·m; H8 M10 35 N·m", "chain sag 4-6 mm; belt 10 mm deflection at 15 N mid-span"),
        ("9", "Guards 305 (belt) and 306 (chain).", "H12 x6 M6 5 N·m", "no pinch point reachable (ISO 13857); guards need a tool to remove"),
        ("10", "Hopper 400 into the horseshoe from the front, rim on the arm, locate on the 2 pins; lid halves 403/404 and flap 405 with B1 actuator.",
         "-", "hopper outlet ferrule on the spindle axis ≤ 1; flap opens the interlock"),
        ("11", "Agitator 500 up through the hopper onto the hub ferrule, TC clamp P1-445.", "TC clamp hand-tight", "scraper clears the cone 3 ±1 all round by hand turn"),
        ("12", "Tooling J (or S): auger up through the outlet, screw onto the spindle LH M16 x 1.5: turn it clockwise seen from above (against the dosing rotation) to tighten; tube on the outlet TC clamp.",
         "auger hand-tight, it self-tightens in dosing rotation", "auger runs true in the tube: 0.75 radial clearance all round (T9)"),
        ("13", "HMI A3 and pod operators; foot switch S2 on its cord; cables per the cable schedule; earth bonding.", "glands hand + 1/2 turn", "< 0.1 Ω PE to every metal part (T14)"),
        ("14", "Commission per P1-401-900: rotation, safety function, calibration doses for each container.", "-", "sign the ITP record"),
    ]
    S.table(1830, 110, [("STEP", 60), ("HARDWARE / TORQUE", 640), ("CHECK BEFORE THE NEXT STEP", 870)], [(a, c, d) for a, b, c, d in steps],
            "ASSEMBLY STEPS: HARDWARE AND CHECKS", 12, 24)
    S.notes(1830, 500, 1570, [b for a, b, c, d in steps], title="ASSEMBLY STEPS: OPERATIONS", fs=12)
    S.notes(110, 1290, 1640, [
        "Tooling change S ↔ J (about 10 min): lock out Q1; hopper empty or scoop the product out; TC clamp off, drop the tube; unscrew the auger (LH thread: turn it the dosing way, counter-clockwise seen from above, to loosen); fit the other set; select the product on the HMI.",
        "Stage change: pull the plunger knob, slide the stage to the hole marked for the container (shaker / jar / tub / pouch), release; the HMI asks to confirm the container.",
        "Allergen changeover: lock out Q1; hopper off the horseshoe (2 people, about 9 kg empty), agitator off its clamp, tooling off; all product-contact parts to the sink (warm detergent, rinse, sanitise, air dry). Wipe the stage and the cabinet top. ATP swab hopper cone, auger, tube (T22).",
        "Do not jet-wash the head or cabinet; the head is IP54 only. Never run the auger dry for more than 5 s (galling in the tube).",
        "Re-grease nothing: bearings are sealed for life. Check belt and chain tension monthly (M1).",
    ], "OPERATION, TOOLING CHANGE, CLEANING", fs=12)
    S.table(1830, 840, [("ITEM", 50), ("DESCRIPTION", 560), ("QTY", 40), ("WHERE", 600), ("TORQUE", 320)],
            [(h, d[:84], q, w[:66], t) for h, d, g, q, w, t in HARDWARE], "HARDWARE AND TORQUES (all A2 stainless; full spec on 800)", 12, 22)
    S.save(DWG / "P1-401-003_assembly.svg")


def hardware():
    S = sheet("P1-401-800", "BOUGHT PARTS, HARDWARE AND RAW MATERIAL", scale="NTS", material="-", finish="-", mass="-")
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
    S.text(110, y, f"Bought parts for one filler ≈ ${tot:,.0f}", 16, bold=True)
    y2 = y + 60
    S.table(110, y2, [("ITEM", 50), ("DESCRIPTION", 640), ("STANDARD", 210), ("QTY", 40), ("WHERE", 560), ("TORQUE", 160)],
            [(h, d, g, q, w, t) for h, d, g, q, w, t in HARDWARE], "HARDWARE (all A2 / 18-8 stainless)", 12, 22)
    mat = [
        ("304 sheet 1.5 mm 2B (cabinet shell, back, door, base, pod)", "shell wrap 1,840 x 697 + 4 blanks", "2 sheets 48 x 96 in"),
        ("304 sheet 3 mm (top plate 102, backing 107)", "640 x 640 + 180 x 180", "1 sheet 36 x 48 in"),
        ("304 sq tube 4 in x 11 ga (column)", f"1 x {COL['L']:.0f}", "1 length 6 ft"),
        ("304 plate 12 mm (column base, cap) + 20 mm (horseshoe)", "180 sq + 160 sq; horseshoe R272 blank", "laser blanks"),
        ("304 plate 10 mm (head plate, bridge flange) + Ø25 bar (posts)", "485 x 500 + 140 sq; 4 x 110", "laser + saw"),
        ("304 round bar Ø120 (housing), Ø90 (hub), 17-4PH Ø30 (spindle)", "80 / 70 / 380 long", "machine shop stock"),
        ("316L sheet 1.5 mm 2B (hopper cone + cylinder, lid)", "cone + cylinder blanks per 400", "1 sheet 48 x 120 in"),
        ("316L angle 25 x 25 x 3 (hopper rim, rolled)", "Ø456 ring", "1 length 2 m"),
        ("316L tube 2.5 in OD x 16 ga (agitator sleeve) + 25 x 6 flat (arms, blades)", "per 500 cut list", "1 m + 2 m"),
        ("304 plate 6 mm (stage plate), Ø20 ground rod, UHMW blocks", "240 sq; 2 x 290; 4 blocks", "laser + saw"),
        ("BPE ferrules 2.5 in (hopper outlet, hub)", "2", "with P1-445"),
    ]
    S.table(1900, y2, [("MATERIAL", 620), ("PER FILLER", 460), ("BUY", 340)],
            mat, "RAW MATERIAL (made parts)", 12, 22)
    S.table(1900, y2 + 22 * (len(mat) + 1) + 60, [("TAG", 90), ("WHERE / NOTE", 1330)], [(t, n) for t, d, m, p, q, u, n in BOUGHT if n],
            "PURCHASING AND MOUNTING NOTES", 12, 22)
    S.save(DWG / "P1-401-800_bought_hardware.svg")


def itp():
    S = sheet("P1-401-900", "INSPECTION AND TEST PLAN, DESIGN CALCULATIONS", scale="NTS", material="-", finish="-", mass="-")
    tests = [
        ("T1", "Material certs 316L / 304 / 17-4PH (EN 10204 3.1)", "on file", "receiving", "QC"),
        ("T2", "Cabinet top flat, level; column bolt holes to the backing plate", "1.0 over 640", "after welding", "fab"),
        ("T3", "Column square to the base plate, cap parallel to the base", "0.5 / 1,000", "after welding", "QC"),
        ("T4", "Head plate: housing bore and column-cap holes true position", "Ø0.2", "after machining", "QC"),
        ("T5", "Housing bores Ø52 H7 coaxial; spigot Ø40 k6; spindle seats Ø25 k5; hub Ø68 H7", "per 301", "after machining", "QC"),
        ("T6", "Hopper: cone round, ferrule square to the axis, product-contact welds ground flush", "Ø ±1 / 0.3", "after welding", "QC"),
        ("T7", "Surface Ra on hopper, agitator, lid underside, tooling", "≤ 0.8 µm", "after polish", "QC"),
        ("T8", "Passivation (ASTM A967), water-break free", "pass", "after passivate", "QC"),
        ("T9", f"Auger in tube: radial clearance J {C['clr_J']:.2f}, S {C['clr_S']:.2f} all round, run-out at the tip", "≤ 0.25 TIR", "step 12", "assy"),
        ("T10", "Spindle axis to hopper outlet and stage centre", "≤ 0.5 / ≤ 1", "steps 7, 10", "assy"),
        ("T11", "Belt tension and chain sag", "15 N / 10 mm; 4-6 mm", "step 8", "assy"),
        ("T12", "Agitator scraper clearance to the cone", "3 ±1", "step 11", "assy"),
        ("T13", "Point-to-point wiring vs E01-E03; insulation 500 V DC power circuits (drive, PLC off)", "> 1 MΩ", "before power", "elec"),
        ("T14", "PE continuity: cabinet, door, column, head, motor frames to the PE bar", "< 0.1 Ω", "before power", "elec"),
        ("T15", "Rotation: auger CCW seen from above (dosing), agitator direction per 500", "pass", "jog from the HMI", "elec"),
        ("T16", "Safety function: E-stop and flap each stop the auger (STO) and agitator; reset needed; single fault test", "pass", "commissioning", "elec"),
        ("T17", "Servo tuning: no overshoot at the dose end; following error", "< 1 % of a rev", "commissioning", "elec"),
        ("T18", "Container sensor: dose blocked with no container on the stage", "pass", "commissioning", "elec"),
        ("T19", "Calibration: 20 doses per container at rated speed, mean on target", "±0.5 %", "per product", "QA"),
        ("T20", "Dose accuracy: 50 doses, standard deviation (shaker / jar / tub)", "≤ 1 % / 0.7 % / 0.5 %", "per product", "QA"),
        ("T21", f"Rate: {UPM['shaker']:.0f} shakers/min and {UPM['jar']:.0f} jars/min for 10 min, no bridging in the hopper", "pass", "first run", "QA"),
        ("T22", "ATP swab after allergen wash (hopper cone, auger, tube)", "< 150 RLU", "each changeover", "QA"),
        ("T23", "Noise at the operator position", "< 75 dB(A)", "first run", "QA"),
        ("M1", "Belt and chain tension, guard fixings, seal lips", "per T11", "monthly", "maint"),
        ("M2", "Replace lip seals P1-433; check bearing noise", "-", "12 months", "maint"),
    ]
    S.table(110, 110, [("TEST", 60), ("WHAT IS CHECKED", 860), ("LIMIT", 270), ("WHEN / PART", 230), ("BY", 70), ("RESULT / SIGN", 200)],
            [t + ("",) for t in tests], "INSPECTION AND TEST PLAN (record results here or in the MES)", fs=14, rh=30)
    k = C
    dose = [(n, f"{v['g']:.0f} g", f"{k[n]['mL']:.0f} mL", CONT[n]["tool"], f"{k[n]['g_rev']:.1f} g", f"{k[n]['rev']:.1f}", f"{k[n]['t_dose']:.2f} s", f"{k[n]['stage']:.0f}")
            for n, v in CONT.items()]
    S.table(110, 110 + 30 * (len(tests) + 1) + 70, [("CONTAINER", 200), ("NET", 110), ("VOLUME", 120), ("TOOL", 70), ("PER REV", 120), ("REVS", 90), ("DOSE TIME", 130), ("STAGE (above top)", 220)],
            dose, f"DOSE TABLE (bulk density {RHO} g/mL, fill efficiency {FILL_EFF:.2f}; calibrate per T19)", fs=14, rh=30)
    calc = [
        ("Hopper volume / product", f"{k['vol_hop']:.1f} L / {k['kg_hop']:.1f} kg", f"cone {k['cone_ang']:.0f}° to the horizontal (≥ 55° for this blend)"),
        ("Units per hopper fill", f"{k['units_per_hopper']:.0f} shakers", "refill by scoop through the flap"),
        ("Drive ratio / auger speed", f"{k['ratio']:.0f}:1 belt; J {RPM['J']:.0f} rpm, S {RPM['S']:.0f} rpm", f"servo {k['n_servo_J']:.0f} / {k['n_servo_S']:.0f} rpm (max {SERVO['n_max']:.0f})"),
        ("Torque at the auger", f"{k['T_out']:.2f} N·m continuous", f"vs {T_AUGER['J']:.1f} N·m (J, full hopper): SF {k['SF_T']:.2f}; peak {SERVO['T_peak'] * k['ratio'] * 0.95:.1f}"),
        ("Belt length / pull", f"{k['belt_L']:.1f} mm (450 std) / {k['F_belt']:.0f} N", f"HTD 5M 15 wide, centre {BELT['C']:.0f}"),
        ("Upper 6205 load / life", f"{k['R_up']:.0f} N / L10 {k['L10h'] / 1000:.0f} kh", "C = 14.8 kN; far beyond 40 kh target"),
        ("Chain links", f"{k['chain_links']:.1f} → {CHAIN['links']}", f"#40 SS 15T / 30T, C {CHAIN['C']:.0f}; agitator {AGIT['rpm']:.0f} rpm, tip {k['agit_tip']:.2f} m/s"),
        ("Column moment / stress", f"{k['M_col']:.0f} N·m / {k['sig']:.1f} MPa", f"head {k['m_head']:.0f} kg + full hopper {k['m_hop_full']:.0f} kg at {COL['y']:.0f}; 304 yield 205 MPa"),
        ("Column tip deflection", f"{k['defl']:.2f} mm", "< 0.5 keeps the auger centred in the tube"),
        ("Base bolt tension (2 back)", f"{k['bolt_T']:.0f} N each", "M12 A2-70 proof ≈ 38 kN: SF > 40"),
        ("Horseshoe arm", f"{k['d_hsh']:.2f} mm / {k['s_hsh']:.0f} MPa", "20 x 40 304 plate, hopper full"),
        ("Mass / CG", f"{k['m_tot']:.0f} kg, CG y {k['y_cg']:.0f}", f"feet at y {FEET['yc'] - FEET['y']:.0f} / {FEET['yc'] + FEET['y']:.0f}: stable, no anchor needed"),
        ("Cycle", f"{k['t_cycle']:.1f} s at {UPM['rated']:.0f} /min rated", f"jar dose {k['jar-12']['t_dose']:.2f} s + place/remove"),
    ]
    S.table(1840, 110, [("CALCULATION", 360), ("RESULT", 400), ("NOTE / LIMIT", 820)], calc, "DESIGN CALCULATIONS (design.py calcs())", fs=13, rh=30)
    S.save(DWG / "P1-401-900_itp.svg")


def cover_sheet(sheets):
    S = sheet("P1-401-000", "P1-401 SERVO AUGER FILLER: DRAWING SET", scale="NTS", material="316L product contact, 304 frame", finish=FIN_PC,
              mass=f"{C['m_tot']:.0f} kg [{C['m_tot'] * 2.2046:.0f} lb]")
    S.text(110, 110, "Servo auger filler P1-401, built in house, 1 off, rev B", 34, bold=True)
    S.text(110, 150, f"{C['vol_hop']:.0f} L hopper on a 4 in column over a controls cabinet; 750 W servo auger, 2 tooling sets, 4-position container stage, "
           f"{UPM['rated']:.0f} doses/min rated", 18)
    img(S, IMG / "fl_full.png", 110, 190, 780, 1014)
    img(S, IMG / "fl_back.png", 900, 190, 780, 1014)
    S.table(1800, 190, [("DESIGN DATA", 330), ("", 900)], [
        ("Duty", f"dose the finished blend into shakers {CONT['shaker-250']['g']:.0f} g, jars and pouches {CONT['jar-12']['g']:.0f} g, tubs {CONT['tub-5lb']['g']:.0f} g"),
        ("Hopper", f"316L Ø450, {C['vol_hop']:.1f} L, cone {C['cone_ang']:.0f}°, 2.5 in TC outlet, split lid with interlocked scoop flap"),
        ("Auger drive", f"SureServo2 750 W, HTD belt 2:1, spindle on 2 x 6205 in a cartridge; J {RPM['J']:.0f} rpm, S {RPM['S']:.0f} rpm"),
        ("Agitator", f"1/4 HP gearmotor, #40 SS chain 2:1, {AGIT['rpm']:.0f} rpm, hub on 2 x 6008 around the spindle"),
        ("Tooling", f"S {TOOL['S']['auger_od']:.0f} OD (shakers), J {TOOL['J']['auger_od']:.0f} OD (jars, pouches, tubs), LH M16 x 1.5 top thread"),
        ("Stage", "4 heights on 2 Ø20 rods, index plunger, container sensor (no container, no dose)"),
        ("Controls", "CLICK PLUS PLC, 3 in HMI, PNOZ s4 safety relay (E-stop + flap → STO), foot switch start"),
        ("Supply", "208 V 1-ph 20 A + PE; Ethernet to the MES"),
        ("Plant interface", f"top {Z_TOP:.0f}, outlet {Z_OUT:.0f} AFF; footprint 640 x 640 + column; hopper rim {Z_RIM:.0f}"),
        ("Rev B changes", "cartridge loads from the top with spacers; 12 mm cap; 750 VA control transformer; cabinet moved 200 back"),
    ], fs=13, rh=24)
    S.table(1800, 530, [("SHEET", 150), ("TITLE", 860), ("FILE", 220)], [(n, t, n + " svg / PDF") for n, t in sheets], "SHEET INDEX", fs=13, rh=24)
    S.notes(110, 1250, 1570, [
        "Units mm [in]. Third-angle projection. Tolerances in the title block unless noted. Weld symbols AWS A2.4; welding to AWS D18.1 / ASME BPE MJ.",
        "Product-contact parts 316L, Ra ≤ 0.8 µm, welds ground flush, passivated ASTM A967. Seals FDA 21 CFR 177.2600; bearing grease NSF H1.",
        "Cut files (DXF) in dxf/ in mm and inch; 3D: cad/ (STEP per part, P1-401-ASM.step/.glb); generator: design.py, model.py, sh_*.py.",
        "Bought parts marked 'confirm' must be checked against the supplier drawing before the matching made part is cut (servo flange, gearmotor face, auger thread).",
        "Release for build: drawings checked, ITP P1-401-900 attached to the traveler, materials certified.",
    ], "GENERAL NOTES", fs=13)
    S.save(DWG / "P1-401-000_cover.svg")
