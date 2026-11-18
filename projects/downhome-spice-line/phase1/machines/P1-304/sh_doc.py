"""P1-304-000 cover + index, -003 assembly and cleaning, -600 bought parts and hardware, -900 ITP + calculations."""
import base64
import math
import textwrap
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

IMG = DWG / "img"
C = calcs()
M_MADE = sum(MASS.values())
M_BOUGHT = sum(M_PARTS.values()) + 0.6      # + isolators, strap, cord stub
M_BODY = sum(v for k, v in MASS.items() if k[:9] == "P1-304-20")


def img(S, path, x, y, w, h):
    b = base64.b64encode(path.read_bytes()).decode()
    S.add(f'<image href="data:image/png;base64,{b}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')


def assembly():
    S = sheet("P1-304-003", "ASSEMBLY, SCREEN CHANGE, CLEANING, TORQUES", scale="NTS", material="see item list", finish="-",
              mass=f"{M_MADE:.1f} kg made + {M_BOUGHT:.1f} kg bought")
    cap = ["1  Base on the drum rim, 3 isolators", "2  Body + vibrator onto the isolators", "3  Flex band across the 4 mm gap",
           "4  Grate magnet on the bars", "5  Screen deck on the ledge", "6  Lid, 4 draw latches"]
    for i in range(6):
        x, y = 120 + (i % 3) * 560, 120 + (i // 3) * 380
        img(S, IMG / f"sf_s{i + 1}.png", x, y + 10, 540, 336)
        S.add(f'<rect x="{x}" y="{y + 10}" width="540" height="336" fill="none" stroke="#b0bec5"/>')
        S.text(x + 8, y + 32, cap[i], 17, bold=True)
    S.text(120, 900, "orange = parts added in that step; ghosted = parts still to come", 13, color="#607d8b")
    steps = [
        ("1", "Bench: screw the 3 isolators P1-341 into the seat ring P1-304-101 (lower stud through the Ø9 hole, nut H1 underneath). Base on a clean drum: tabs outside the rim, skirt inside the liner.",
         "H1 x3 M8, 12 N·m", "base sits flat on the rim, no rock; tabs clear the rim 1.5"),
        ("2", "Bench: vibrator P1-306 on bracket P1-304-206, motor axis vertical, terminal box down; set both eccentric weights to the ITP setting (start 80 %).",
         "H3 x4 M10, 45 N·m + thread lock", "weights equal top and bottom; paint-mark the setting"),
        ("3", f"Lift the body with the vibrator (≈ {M_BODY + M_PARTS['vibrator']:.0f} kg [{(M_BODY + M_PARTS['vibrator']) * 2.2046:.0f} lb], 2 people) onto the isolator studs through the bracket holes.",
         "H2 x3 M8, 12 N·m", "gap body to upstand 4 ±1 all round; body level ±1 mm"),
        ("4", "Flex band P1-344 over the upstand and the body bottom, 2 worm clamps; leave the slack loop outward.",
         "worm clamps 3 N·m", "band not tight: 10 slack, no contact with the drum"),
        ("5", "Bond strap P1-347 from the seat-ring hole (60°, R330) to the isolator bracket at 90°.", "H5 x2 M8, 12 N·m, serrated washers", "< 1 Ω base to body (T14)"),
        ("6", "Grate magnet P1-307 on the 2 bars, tubes across the flow.", "-", "magnet sits on both bars, no rock"),
        ("7", "Deck gasket P1-304-502 on the ledge, then the screen deck P1-304-400, cloth up.", "-", "deck drops in by hand, ≤ 1 radial play"),
        ("8", "Lid P1-304-300 with gasket P1-304-501; close the 4 draw latches P1-342 crosswise.", "latch adjust: firm hand close", "3 pads touch the deck (2 squeeze); lid does not rattle"),
        ("9", "Sock P1-346 from the blender valve to the 4 in inlet ferrule; dust port kit P1-345 and the collector hose on the 3 in ferrule.", "TC clamps hand-tight", "sock slack, does not pull the lid"),
        ("10", "Cord P1-350 from the isolator Q-306 to the vibrator box with a drip loop, tied to the bracket; wire per E01/E02.", "H6 cord grip", "point-to-point check vs E02"),
        ("11", "Commission per P1-304-900 (rotation not relevant, amplitude, current, interlock with the valve).", "-", "sign the ITP record"),
    ]
    S.table(1830, 120, [("STEP", 60), ("HARDWARE / TORQUE", 520), ("CHECK BEFORE THE NEXT STEP", 990)], [(a, c, d) for a, b, c, d in steps],
            "ASSEMBLY STEPS: HARDWARE AND CHECKS", 13, 24)
    S.notes(1830, 440, 1570, [b for a, b, c, d in steps], title="ASSEMBLY STEPS: OPERATIONS", fs=13)
    S.notes(120, 940, 1650, [
        "Drum change (every batch): vibrator OFF on the HMI and the valve closed. Unlatch nothing: 2 people lift the whole sifter (≈ 48 kg [106 lb]) by the seat ring, outside the isolators, and set it on the next drum; or slide the drums on the dolly if the stand allows.",
        "Before lifting: the cord P1-350 has 3 m and a drip loop; the sock and the dust hose come off at their TC clamps first.",
        "Screen change / check (every batch end, ITP T19): lock out Q-306; open the 4 latches; lift the lid; lift out the deck; inspect the cloth for tears; lift out the magnet; wipe the tubes into a bag (record the catch); refit.",
        "Allergen changeover: lock out; lid, deck, magnet, gaskets to the sink (warm detergent, rinse, sanitise, air dry). Body: vacuum then wipe inside, band off and washed. Base skirt wiped. ATP swab the deck and shell (T23).",
        "Never wash the vibrator with a jet; it is IP66 but the cord grip is the weak point. Never strike the cloth to clear it: use a soft brush from below.",
        "Spare deck P1-304-400 (make 2) is kept clean and bagged so a torn screen costs one lid opening, not a batch.",
    ], "OPERATION, SCREEN CHECK, CLEANING (about 10 min per changeover)", fs=13)
    rows = [(h, d[:58], g, q, w[:48], t[:36]) for h, d, g, q, w, t in HARDWARE]
    S.table(1830, 1180, [("ITEM", 50), ("DESCRIPTION", 470), ("STANDARD", 170), ("QTY", 40), ("WHERE", 560), ("TORQUE", 290)], rows,
            "HARDWARE AND TORQUES (all A2 stainless)", 12, 22)
    S.save(DWG / "P1-304-003_assembly.svg")


def hardware():
    S = sheet("P1-304-600", "BOUGHT PARTS AND HARDWARE", scale="NTS", material="-", finish="-", mass="-")
    rows = []
    for t, d, m, p, q, u, n in BOUGHT:
        dl, pl, ml = textwrap.wrap(d, 120), textwrap.wrap(p, 80), textwrap.wrap(m, 34)
        rows.append((t, dl[0], ml[0], pl[0], q, f"${u:,.0f}", f"${u * q:,.0f}"))
        for k in range(1, max(len(dl), len(pl), len(ml))):
            rows.append(("", "  " + dl[k] if k < len(dl) else "", ml[k] if k < len(ml) else "", "  " + pl[k] if k < len(pl) else "", "", "", ""))
    S.table(120, 140, [("TAG", 90), ("DESCRIPTION", 1060), ("MAKER", 330), ("PART NUMBER", 700), ("QTY", 50), ("UNIT", 90), ("TOTAL", 110)], rows,
            "BOUGHT PARTS (estimates unless noted; confirm before order)", 12, 22)
    tot = sum(u * q for t, d, m, p, q, u, n in BOUGHT)
    y = 140 + 22 * (len(rows) + 1) + 34
    S.text(120, y, f"Bought parts for one sifter ≈ ${tot:,.0f}", 16, bold=True)
    S.table(120, y + 40, [("TAG", 90), ("NOTE", 1500)], [(t, n) for t, d, m, p, q, u, n in BOUGHT if n], "PURCHASING NOTES", 12, 22)
    y2 = y + 40 + 22 * (len([1 for b in BOUGHT if b[6]]) + 1) + 50
    S.table(120, y2, [("ITEM", 60), ("DESCRIPTION", 620), ("STANDARD", 260), ("QTY", 50), ("WHERE", 640), ("TORQUE", 380)],
            [(h, d, g, q, w, t) for h, d, g, q, w, t in HARDWARE], "HARDWARE", 12, 24)
    circ = math.pi * (2 * R_I + T14)
    mat = [
        ("316L sheet 14 ga [1.9] 2B (shell + upstand)", f"{circ:.0f} x {Z_B1 - Z_B0:.0f} + {circ:.0f} x {UPST['h']:.0f}", "1 sheet 48 x 96 in (both strips across the width)"),
        ("316L sheet 1.5 mm 2B (skirt)", f"{math.pi * SKIRT['od']:.0f} x {SKIRT['h']:.0f}", "same order, 1 strip"),
        ("316L plate 6 mm (top flange, screen ledge)", f"Ø{TOPFL['od']:.0f} / Ø{LEDGE['id'] + 2 * LEDGE['w']:.0f} rings", "1 plate 24 x 48 in (nest the ledge inside the flange)"),
        ("304 plate 6 mm (seat ring, brackets)", f"Ø{SEAT['od']:.0f} ring + 3 angles", "1 plate 30 x 30 in, laser"),
        ("304 plate 10 + 8 mm (vibrator plate, gussets)", f"{VBR['w']:.0f} x {VBR['z1'] - VBR['z0']:.0f} + 2 gussets", "laser blanks"),
        ("316L flat bar 25 x 5 (magnet bars)", "2 x 490", "1 m"),
        ("316L sheet 2 mm (lid) + 3 mm (deck rings)", f"Ø{LID['od']:.0f} disc + 4 strips", "1 sheet 24 x 48 in each"),
        ("BPE ferrules 4 in + 3 in short weld (316L)", "1 + 1", "with the bought kit P1-345 vendor"),
        ("304 sheet 3 mm (latch plates, keeper tabs, centring tabs)", "11 small blanks", "laser, from the 6 mm order's offcut list"),
        ("FDA silicone sheet 3 mm + 2 mm (gaskets) + Ø30 cord (pad caps)", "Ø540 + Ø480 rings", "1 sheet 24 x 24 in each"),
    ]
    S.table(1900, 140 + 22 * (len(rows) + 1) + 90, [("MATERIAL", 560), ("PER SIFTER", 380), ("BUY", 460)], mat, "RAW MATERIAL (made parts)", 12, 22)
    S.save(DWG / "P1-304-600_bought_hardware.svg")


def itp():
    S = sheet("P1-304-900", "INSPECTION AND TEST PLAN, DESIGN CALCULATIONS", scale="NTS", material="-", finish="-", mass="-")
    tests = [
        ("T1", "Material certs 316L / 304 (EN 10204 3.1), mesh cert 316", "on file", "receiving", "QC"),
        ("T2", "Seat ring flatness after welding the upstand and skirt", "1.0 over Ø680", "after W1, W2", "fab"),
        ("T3", "Body: top flange flat 0.5, parallel to the ledge 0.5; shell round Ø480 ±1", "in limits", "after welding", "QC"),
        ("T4", "Product-contact welds ground flush, no crevice at the ledge and bars (W3, W4)", "pass", "before polish", "QC"),
        ("T5", "Surface Ra on shell ID, ledge, deck rings, lid underside", "≤ 0.8 µm", "after polish", "QC"),
        ("T6", "Passivation (ASTM A967), water-break free", "pass", "after passivate", "QC"),
        ("T7", "Vibrator plate flat, holes per the maker drawing (4 x Ø11 on 120 x 70)", "0.3 / ±0.2", "before welding to the shell", "QC"),
        ("T8", "Deck: cloth taut (no drum sound dull spots), no tear, rings bonded/clamped all round", "pass", "each deck", "QC"),
        ("T9", "Dry fit: base on a real drum, body on isolators, gap to the upstand", "4 ±1 all round", "assembly step 3", "assy"),
        ("T10", "Lid latched: pads squeeze the deck, lid does not move by hand", "pass", "step 8", "assy"),
        ("T11", "Inlet ferrule top to the blender valve outlet (sock length)", f"{C['gap_valve']:.0f} ±10", "installed", "assy"),
        ("T12", "Insulation resistance motor + cord at 500 V DC", "> 1 MΩ", "before power", "elec"),
        ("T13", "Isolator Q-306 OFF: aux opens first, DO_SifterVib drops (DI change on the HMI)", "pass", "commissioning", "elec"),
        ("T14", "Bond: base to body through the strap; motor frame to PE", "< 1 Ω / < 0.1 Ω", "commissioning", "elec"),
        ("T15", "E-stop: KM-306 drops, vibrator stops; valve closes", "pass", "commissioning", "elec"),
        ("T16", f"Running current at the setting (≈ {C['setting'] * 100:.0f} %)", "≤ nameplate FLA", "commissioning", "elec"),
        ("T17", f"Amplitude at the deck rim with a vibration sticker / meter", f"{2 * AMP_TARGET:.1f} ±0.15 mm p-p", "commissioning", "mech"),
        ("T18", "Startup / stop through resonance: no knocking of the body on the upstand", "pass", "10 starts", "mech"),
        ("T19", "Sieve test: 1 batch, all product through, tailings on the deck recorded", "tailings < 0.5 %", "first batch + each batch", "QA"),
        ("T20", "Throughput with the valve at the set opening", f"≥ {RATE_KGMIN:.1f} kg/min, no deck flooding", "first batch", "QA"),
        ("T21", "Dust: no visible dust at the lid and band with the collector port open", "pass", "first batch", "QA"),
        ("T22", "Magnet pull test (keeper or 1 kg test piece) and catch log", "per supplier; log", "monthly", "QA"),
        ("T23", "ATP swab on the deck and shell after allergen wash", "< 150 RLU", "each changeover", "QA"),
        ("T24", "Valve interlock: valve cannot open with the vibrator off (MES/PLC)", "pass", "commissioning", "elec"),
        ("M1", "Re-check vibrator bolts H3 after 1 h and monthly; isolators for cracks", "45 N·m", "planned", "maint"),
        ("M2", "Replace the screen cloth when torn or after 6 months", "-", "planned", "maint"),
    ]
    S.table(120, 140, [("TEST", 60), ("WHAT IS CHECKED", 820), ("LIMIT", 260), ("WHEN / PART", 230), ("BY", 70), ("RESULT / SIGN", 200)],
            [t + ("",) for t in tests], "INSPECTION AND TEST PLAN (record results here or in the MES)", fs=13, rh=24)
    w = 2 * math.pi * N_VIB / 60
    iso_dyn = ISO["k"] * AMP_TARGET
    calc = [
        ("Vibrating mass", f"{C['M']:.1f} kg", f"body + lid + deck {C['m_body']:.1f} (CAD) + magnet, vibrator, latches, band"),
        ("Drive frequency", f"{N_VIB / 60:.0f} Hz ({N_VIB:.0f} rpm)", "2-pole 60 Hz"),
        ("Static moment needed", f"{C['me'] * 1000:.1f} kg·mm", f"M x amplitude {AMP_TARGET} mm"),
        ("Centrifugal force", f"{C['F']:.0f} N = {C['setting'] * 100:.0f} % of {F_MAX:.0f} N", "set the weights to this; vibrator not over-sized"),
        ("Deck acceleration", f"{C['acc_g']:.1f} g", "3-6 g normal for gyratory sifters"),
        ("Isolators: 3 x k", f"{3 * ISO['k']:.0f} N/mm", f"{ISO['shore']} Sh Ø{ISO['d']:.0f} x {ISO['h']:.0f} (confirm curve)"),
        ("Natural frequency", f"{C['fn']:.1f} Hz", f"ratio {C['r']:.1f} (> 3 good isolation)"),
        ("Transmissibility", f"{C['T'] * 100:.1f} %", f"force to the drum ≈ {C['F_tx']:.0f} N"),
        ("Static deflection", f"{C['static']:.1f} mm", "< 4 mm gap to the upstand: OK"),
        ("Isolator load (static + dynamic)", f"{C['M'] * 9.81 / 3:.0f} + {iso_dyn:.0f} N", f"rated 400 N: SF {400 / (C['M'] * 9.81 / 3 + iso_dyn):.1f}"),
        ("Latch hold vs lift", f"{C['latch']:.0f} N vs {C['lift']:.0f} N", f"SF {C['latch'] / C['lift']:.1f} even if all force were lift"),
        ("Screen area / open area", f"{C['area_dm2']:.1f} dm² / {C['open_area'] * 100:.0f} %", f"12 mesh 0.023 wire, opening {MESH['open']:.2f} mm"),
        ("Screen capacity", f"{C['cap']:.1f} kg/min", f"at {SCREEN_LOAD} kg/(min·dm²) vs {RATE_KGMIN} kg/min: {C['cap'] / RATE_KGMIN:.1f}x"),
        ("Batch time", f"{C['t_batch']:.1f} min", f"{BATCH_KG:.1f} kg at {RATE_KGMIN} kg/min (valve throttled)"),
        ("Height stack", f"inlet top z {C['z_inlet']:.0f} = {Z_RIM_FFL + C['z_inlet']:.0f} AFF", f"{C['gap_valve']:.0f} mm under the valve for the sock"),
        ("Motor current", "≈ 2.9 A at 115 V (confirm)", "MS116-4.0 set to nameplate FLA, 14 AWG"),
    ]
    S.table(1800, 140, [("CALCULATION", 420), ("RESULT", 420), ("NOTE / LIMIT", 760)], calc, "DESIGN CALCULATIONS (design.py calcs())", fs=13, rh=24)
    S.save(DWG / "P1-304-900_itp.svg")


def cover_sheet(sheets):
    S = sheet("P1-304-000", "P1-304 DRUM-TOP VIBRATORY SIFTER: DRAWING SET", scale="NTS", material="316L product contact, 304 frame", finish=FIN_PC,
              mass=f"{M_MADE + M_BOUGHT:.0f} kg [{(M_MADE + M_BOUGHT) * 2.2046:.0f} lb]")
    S.text(120, 120, "Drum-top vibratory sifter P1-304, built in house, 1 off, rev B", 34, bold=True)
    S.text(120, 160, f"Ø480 body on 3 rubber isolators over a 55 gal drum, 12 mesh deck + grate magnet, {F_MAX / 1000:.1f} kN vibrator, "
           f"{C['cap']:.0f} kg/min capacity vs {RATE_KGMIN} kg/min duty, lid on 4 draw latches, tool-free screen change", 18)
    img(S, IMG / "sf_full.png", 120, 210, 1550, 996)
    S.table(1800, 210, [("DESIGN DATA", 330), ("", 900)], [
        ("Duty", f"check-screen the finished blend from the blender P1-301 into the 55 gal drum: {BATCH_KG:.1f} kg in ≈ {C['t_batch']:.0f} min"),
        ("Body", f"316L Ø{2 * R_I:.0f} x 14 ga shell, top flange Ø{TOPFL['od']:.0f}, screen ledge, 2 magnet bars, all on 3 isolators"),
        ("Screen", f"12 x 12 mesh 316, {MESH['open']:.2f} mm opening, {C['open_area'] * 100:.0f} % open, clamped between 2 rings; spare deck"),
        ("Magnet", "grate 12 x 12 in, rare earth, rests on the bars below the deck"),
        ("Drive", f"OLI MVE 200/36 class, 1-ph 115 V, set to {C['setting'] * 100:.0f} %, {2 * AMP_TARGET:.1f} mm p-p at {N_VIB:.0f} rpm"),
        ("Isolation", f"fn {C['fn']:.1f} Hz, {C['T'] * 100:.1f} % transmitted to the drum; flex band seals the 4 mm gap"),
        ("Plant interface", f"drum rim 1,054 AFF; inlet 4 in TC top {Z_RIM_FFL + Z_INLET_TOP:.0f} AFF under the valve at 1,261; dust 3 in TC to P1-310"),
        ("Safety", "isolator in sight (early-break aux), KM-306 on E-stop, bond strap across the isolators, valve interlocked"),
        ("Changes in rev B", "isolators on R315 outside the rim, seat Ø680, latches on the shell, vibrator axis z 150, pads gap + 2"),
    ], fs=13, rh=24)
    S.table(1800, 500, [("SHEET", 150), ("TITLE", 860), ("FILE", 220)], [(n, t, n + " svg / PDF") for n, t in sheets], "SHEET INDEX", fs=13, rh=24)
    S.notes(120, 1250, 1550, [
        "Units mm [in]. Third-angle projection. Tolerances in the title block unless noted. Weld symbols AWS A2.4; welding to AWS D18.1 / ASME BPE MJ.",
        "Product-contact parts 316L / 316, Ra ≤ 0.8 µm, welds ground flush, passivated ASTM A967. Seals FDA 21 CFR 177.2600.",
        "Cut files (DXF) in dxf/ in mm and inch; 3D: cad/ (STEP per part, P1-304-ASM.step/.glb); generator: design.py, model.py, sh_*.py.",
        "Bought parts marked 'confirm' must be checked against the supplier drawing before the matching made part is cut (vibrator feet, latch holes).",
        "Release for build: drawings checked, ITP P1-304-900 attached to the traveler, materials certified.",
    ], "GENERAL NOTES", fs=13)
    S.save(DWG / "P1-304-000_cover.svg")
