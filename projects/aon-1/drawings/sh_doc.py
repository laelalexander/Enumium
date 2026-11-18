"""AON-1 document sheets: AON-600 bought parts + hardware, AON-E01 power/inhibit schematic + stack bus, AON-E02 harness wire list, AON-900 test plan, AON-000 cover."""
import base64
import textwrap

from common import *  # noqa: F401,F403
from mechsheet import Sch
import elec as EL

BLU, RED, GRY = "#0d47a1", "#b00020", "#607d8b"


def img(S, path, x, y, w, h):
    b = base64.b64encode(path.read_bytes()).decode()
    S.add(f'<image href="data:image/png;base64,{b}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')


def hardware():
    S = sheet("AON-600", "BOUGHT PARTS, HARDWARE AND MADE-PART LIST", scale="NTS", material="-", finish="-", mass="-")
    rows = []
    for ln, d, m, p, q, sp, u, n in BOUGHT:
        dl, pl = textwrap.wrap(d, 95), textwrap.wrap(p, 60)
        rows.append((ln, dl[0], m[:30], pl[0], q, sp, f"${u:,.2f}", f"${u * (q + sp):,.0f}"))
        for k in range(1, max(len(dl), len(pl))):
            rows.append(("", "  " + dl[k] if k < len(dl) else "", "", "  " + pl[k] if k < len(pl) else "", "", "", "", ""))
    S.table(90, 140, [("LINE", 70), ("DESCRIPTION", 900), ("MAKER", 290), ("PART NUMBER", 640), ("QTY", 50), ("SPARE", 60), ("UNIT", 100), ("TOTAL", 100)], rows,
            "BOUGHT PARTS PER SATELLITE (prices are estimates: quote before order)", 12, 22)
    tot = sum(u * (q + sp) for _, _, _, _, q, sp, u, _ in BOUGHT)
    y = 140 + 22 * (len(rows) + 1) + 30
    S.text(90, y, f"Bought parts including spares ≈ ${tot:,.0f} (solar cells dominate: confirm the Azur Space quote; the boards' own BOMs come with the KiCad packages)", 15, bold=True)
    y += 30
    S.table(90, y + 20, [("LINE", 70), ("WHERE / NOTE", 1500)], [(ln, n) for ln, _, _, _, _, _, _, n in BOUGHT], "PURCHASING NOTES", 12, 22)
    y2 = y + 20 + 22 * (len(BOUGHT) + 1) + 50
    S.table(90, y2, [("HW", 50), ("DESCRIPTION", 700), ("STANDARD", 260), ("QTY", 50), ("WHERE", 600), ("TORQUE", 330)],
            [(h, d, g, q, w, t) for h, d, g, q, w, t in HARDWARE], "HARDWARE (A4/316 stainless: non-magnetic enough for the magnetometer; verify each lot with a gaussmeter)", 12, 24)
    y3 = y2 + 24 * (len(HARDWARE) + 1) + 50
    S.table(90, y3, [("PART", 110), ("NAME", 620), ("QTY", 50), ("MATERIAL", 600), ("PROCESS", 520)], [(a, b, c, d, e) for a, b, c, d, e in MADE],
            "MADE PARTS (BUILD LINES)", 12, 24)
    S.save(DWG / "AON-600_bought_hardware.svg")


def e01():
    S = sheet("AON-E01", "POWER, INHIBITS AND STACK BUS (SYSTEM SCHEMATIC)", scale="NTS", material="-", finish="-", mass="-")
    s = Sch(S)
    W = {w[3] + "@" + w[1].split(":")[0]: w[0] for w in EL.wires()}
    # solar strings
    y0 = 220
    for i, f in enumerate(EL.FACES):
        y = y0 + i * 150
        s.box(100, y, 230, 100, f"E06 {f} STRING", ["7S CIC, Vmp 16.9 V", "Isc 0.52 A, NTC"])
        w1 = [w[0] for w in EL.wires() if w[1] == f"J{101 + i}:1"][0]; w3 = [w[0] for w in EL.wires() if w[1] == f"J{101 + i}:3"][0]
        s.w(330, y + 35, 520, y + 35, no=f"{w1}/{int(w1[1:]) + 1:03d} J{101 + i}→J{1 + i}")
        s.w(330, y + 70, 470, y + 70, RED, no=f"{w3}/{int(w3[1:]) + 1:03d} (−)")
        s.t(470, y + 74, "→ GND", 12, "start", GRY)
    for k, (yy, lab) in enumerate(((y0 + 35, "A"), (y0 + 335, "B"))):
        s.box(520, yy - 20, 180, 190, f"OR {lab}", ["LM66100 ideal", "diode x 2"])
        s.w(520, yy + 150, 520, yy + 150)
        s.w(700, yy + 75, 800, yy + 75)
        s.box(800, yy, 260, 150, f"MPPT {lab} (E01)", ["TI BQ24650 sync buck", "8.40 V float, MPPT 14.9 V", "INA226 on the input"])
        s.w(1060, yy + 75, 1200, yy + 75)
    s.w(520, y0 + 185, 520, y0 + 185)
    s.w(1200, y0 + 110, 1200, y0 + 410); s.dot(1200, y0 + 110); s.dot(1200, y0 + 410)
    s.t(1210, y0 + 260, "CHARGE NODE", 13, "start", "#111", True)
    # deployment switches and battery
    s.w(1200, y0 + 260, 1320, y0 + 260)
    s.sw_v(1320, y0 + 260, "SW1 (NC, open when stowed)", nc=False)
    s.t(1340, y0 + 250, f"{W.get('VBATT_SW+@SW1', '')}/{W.get('VBATT_CELL+@SW1', '')}", 12, "start", BLU)
    s.box(1250, y0 + 330, 320, 210, "E02 BATTERY 2S2P", ["LG INR18650 MJ1 x 4, 7.0 Ah, 51 Wh", "BQ7718 OV + BQ771807 2nd level", "NTC, 2 W heater (HEATER rail)", "fuse 5 A (F1) in the + lead"])
    s.w(1320, y0 + 310, 1320, y0 + 330)
    s.sw_v(1420, y0 + 540, "SW2 (in V−)")
    s.t(1440, y0 + 600, f"{W.get('VBATT_SW-@SW2', '')}/{W.get('VBATT_CELL-@SW2', '')}", 12, "start", BLU)
    s.w(1420, y0 + 590, 1420, y0 + 640); s.t(1430, y0 + 660, "GND (single point, E01)", 12, "start", GRY)
    # RBF / inhibit FET
    s.w(1570, y0 + 400, 1760, y0 + 400)
    s.box(1760, y0 + 330, 300, 150, "INHIBIT FET Q1 (E01)", ["P-ch high side, gate held off", "while RBF1 is fitted", "(INHIBIT stack pin 35)"])
    s.box(1760, y0 + 560, 300, 110, "RBF1 / UMBILICAL (E06A J106/J105)", [f"wires {W.get('RBF_INH@J105', '')}, {W.get('CHG+@J105', '')}..", "plug fitted = inhibit"], dash=True)
    s.w(1910, y0 + 480, 1910, y0 + 560, RED)
    s.w(2060, y0 + 400, 2200, y0 + 400); s.t(2070, y0 + 390, "VBATT BUS 6.0-8.4 V (stack 1-6)", 13, "start", "#111", True)
    s.w(2200, y0 - 40, 2200, y0 + 1100); s.dot(2200, y0 + 400)
    loads = [("3V3_OBC", "TPS62130 buck, always on", "E03 OBC/ADCS, FRAM, NOR"), ("5V_SW", "TPS62130 + TPS2553 1.5 A", "ADCS drivers, payload"),
             ("VBATT_COM", "eFuse 2 A, LOAD_COM_EN", "E04 COM (PA_EN AND 45-min timer)"), ("BURN", "TPS2553 1.5 A; BURN_EN AND 30-min timer", f"E05 R1/R2 via {W.get('BURN1@J7', '')}/{W.get('BURN2@J7', '')}"),
             ("VBATT_PAY", "eFuse 1 A, LOAD_PAY_EN", "payload bay"), ("HEATER", "N-FET, thermostat in EOR-1", "E02 Kapton heater 2 W")]
    for k, (nm, how, to) in enumerate(loads):
        y = y0 - 40 + k * 190
        s.w(2200, y + 50, 2280, y + 50); s.dot(2200, y + 50)
        s.box(2280, y, 420, 110, nm, [how, "INA226 telemetry"])
        s.w(2700, y + 50, 2820, y + 50)
        s.box(2820, y + 10, 560, 80, to)
    S.table(100, 1000, [("BLOCK", 260), ("WHAT", 900), ("NEXT", 560)], EL.POWER_BLOCKS, "POWER CHAIN", 12, 24)
    S.table(1900, 1300, [("STACK PINS", 120), ("NET (ESQ-126, same position on E01-E04)", 680)], EL.STACK_BUS, "STACK BUS ALLOCATION", 11, 20)
    S.notes(100, 1300 + 24 * 2, 1700, [
        "Three independent inhibits between the battery and every load (CDS rev 14.1 + range safety): SW1 in V+, SW2 in V−, RBF/INHIBIT FET Q1. Deployables need a 4th: the 30-min hardware timer on the burn rail.",
        "RF needs: the inhibits released, LOAD_COM_EN from EOR-1 after 45 min, PA_EN from EOR-1, and the independent 45-min TPL5111 timer on E04 (two of them hardware).",
        "Charging through the umbilical bypasses SW1/SW2 only with the GSE charger connected (CHG+ on J105) and RBF fitted; the charger has its own 2S CC/CV and a 1 A limit.",
        "One-point ground at E01; chassis ground through the board mounting rings and spacers to the frames and rails (bond < 10 mΩ).",
        "Wire numbers (blue) are the AON-E02 harness numbers. Board-level schematics are the KiCad projects E01-E07 (next phase).",
    ], "NOTES", 12)
    S.save(DWG / "AON-E01_power_schematic.svg")


def e02():
    S = sheet("AON-E02", "HARNESS WIRE LIST (EVERY WIRE NUMBERED) AND CONNECTORS", scale="NTS", material="M22759/32 ETFE wire, Gecko-SL crimp", finish="-", mass="≈ 55 g")
    W = EL.wires()
    half = (len(W) + 1) // 2
    cols = [("WIRE", 70), ("FROM", 120), ("TO", 120), ("SIGNAL", 190), ("SPEC", 260), ("GAUGE", 110), ("COLOUR", 110), ("CUT L", 80)]
    S.table(70, 120, cols, [(a, b, c, d, e, f, g, f"{h:.0f}") for a, b, c, d, e, f, g, h in W[:half]], f"WIRES W001-{W[half - 1][0]}", 11, 21)
    S.table(1160, 120, cols, [(a, b, c, d, e, f, g, f"{h:.0f}") for a, b, c, d, e, f, g, h in W[half:]], f"WIRES {W[half][0]}-{W[-1][0]}", 11, 21)
    S.table(2260, 120, [("REF", 70), ("BOARD", 110), ("CONNECTOR", 380), ("PINS", 50), ("MATES", 70), ("USE", 420)],
            [(a, b, c, d, e, f[:60]) for a, b, c, d, e, f in EL.CONNECTORS], "CONNECTORS", 10, 20)
    tot = sum(w[7] for w in W if "coax" not in w[5]) / 1000
    S.notes(2260, 120 + 20 * (len(EL.CONNECTORS) + 1) + 40, 1150, [
        f"{len(W)} wires; {tot:.1f} m of ETFE wire plus 0.15 m coax. Cut lengths include 60-110 mm service loop and routing; trim at the harness board.",
        "Crimp Gecko-SL contacts with the Harwin hand tool listed for G125 contacts on the Harwin datasheet, pull-test 1 per 10 crimps (IPC/WHMA-A-620 Class 3 space addendum).",
        "Twist the pairs: SA± (2 + 2), MTQ±, SUN/SUN_RTN, NTC/NTC_RTN, UART TX/RX with GND. Lace with waxed polyester cord, tie-down every 50 mm to the frame lacing points with 2216 dots.",
        "Mark each wire end with its W-number on a heat-shrink label (Raychem TMS-SCE, low outgassing).",
        "Route panel harnesses along the frame corner blocks clear of the rods; keep MTQ wires ≥ 20 mm from the magnetometer on E03 (the RM3100 sits at the E03 centre).",
        "Continuity + 500 V DC insulation (> 100 MΩ) of each harness before installation (AON-900 T9).",
    ], "NOTES", 12)
    S.save(DWG / "AON-E02_wire_list.svg")


def itp():
    S = sheet("AON-900", "INSPECTION, INTEGRATION AND TEST PLAN", scale="NTS", material="-", finish="-", mass="-")
    tests = [
        ("T1", "Material certs (6061-T6, 5052, Ti-6Al-4V, A4 fasteners), outgassing data for every non-metal", "on file", "receiving", "QA"),
        ("T2", "Frames AON-103/4/5: bar span 83.00 +0/-0.05, thickness 10.00 ±0.05, flatness 0.05, hole table", "per drawing", "after machining", "QC"),
        ("T3", "Rails: 8.50 ±0.02 after anodise all faces, length 340.50 ±0.10, straightness 0.05, R1 edges, csk flush", "per drawing", "after anodise", "QC"),
        ("T4", "Squareness of the assembled structure: envelope 100.0 ±0.1 at 3 heights, diagonals equal 0.1, rail ends coplanar 0.1", "pass", "after step 6", "QC"),
        ("T5", "Fit check in the AODV-1 dispenser / a 3U test pod: slides under its own weight, no binding", "pass", "after step 7", "I&T"),
        ("T6", "Deployment switches: open when the lever is flush with the rail end, closed at ≥ 1.0 proud; spring plungers 3-7 N", "pass", "after step 6", "I&T"),
        ("T7", "Board bring-up E01-E07 (each board's own bring-up list, KiCad packages)", "pass", "before stack", "EE"),
        ("T8", "Battery cell screening per NASA JSC-20793: capacity, DCIR, OCV match ±10 mV, vacuum leak (mass loss)", "pass", "before E02", "EE"),
        ("T9", "Harness continuity, 500 V DC insulation > 100 MΩ, pull test", "pass", "before install", "EE"),
        ("T10", "Inhibit test: with SW1, SW2 pressed and RBF fitted, no voltage on VBATT bus, COM or BURN; each inhibit alone also blocks", "0 V", "flight config", "I&T"),
        ("T11", "Bonding: any panel / board ground ring to the rails", "< 10 mΩ", "after step 7", "I&T"),
        ("T12", "Deployment timeline: release the switches, verify burn at ≥ 30:00 and first RF at ≥ 45:00 (stopwatch + SDR)", "pass", "functional", "I&T"),
        ("T13", "Mass and CG (3 load cells)", f"≤ {D.ENV['m_max'] * 1000:.0f} g; CG per AON-001", "flight config", "I&T"),
        ("T14", "Antenna deployment (ambient, then cold -20 °C): both elements release within 1 burn; VSWR < 1.5 at 401.5 MHz deployed", "pass", "functional", "RF"),
        ("T15", "Sine survey 0.25 g 5-2000 Hz each axis before and after random: first mode > 100 Hz, shift < 5 %", "pass", "environmental", "ENV"),
        ("T16", "Random vibration, GSFC-STD-7000B: qualification 14.1 grms 2 min/axis (EM), acceptance 6.8 grms 1 min/axis (FM); replace with the launcher's levels", "no damage, functional", "environmental", "ENV"),
        ("T17", "Thermal vacuum < 1e-5 torr, -20 °C to +50 °C operating, 4 cycles (acceptance) / 8 cycles (qual); hot and cold starts", "functional each plateau", "environmental", "ENV"),
        ("T18", "Bake-out 70 °C 24 h in vacuum with TQCM; end when the TQCM rate is below the launcher's limit", "pass", "before delivery", "ENV"),
        ("T19", "RF: TX power 33 dBm ±1, frequency ±1 kHz, spurious per the FCC licence mask; RX sensitivity -117 dBm at 1e-5 BER", "pass", "functional", "RF"),
        ("T20", "End-to-end: ground station + AOMC → authenticated command, HK beacon decode, store-and-forward round trip", "pass", "functional", "SW"),
        ("T21", "Security: replayed, forged and bit-flipped commands rejected (EOR-1 tests + on hardware)", "pass", "functional", "SW"),
        ("T22", "Day-in-the-life: 72 h on the sun simulator / lab supply profile, all modes, safe-mode entry and exit", "no resets", "system", "I&T"),
        ("T23", "Final RBF-out check, battery at 40-60 % SOC for storage/launch, photos of every face, sign-off", "pass", "delivery", "QA"),
    ]
    S.table(90, 140, [("TEST", 60), ("WHAT IS CHECKED", 1500), ("LIMIT", 330), ("WHEN", 220), ("BY", 70), ("RESULT / SIGN", 280)], tests, "TESTS", 12, 26)
    y = 140 + 26 * (len(tests) + 1) + 60
    S.notes(90, y, 2400, [
        "Models: build one engineering model (EM) for qualification (T15-T17 at qual levels) and the flight model (FM) for acceptance. The EM can use commercial cells instead of CIC.",
        "Vibration levels: GSFC-STD-7000B generalised random (workmanship 6.8 grms) is a placeholder; AODV-1's own environment comes from the vehicle program (30-launch-vehicle-concept.md) and any rideshare ICD.",
        "Battery safety: JSC-20793 screening and the 2-fault-tolerant protection on E02 are needed for any launch provider's safety review.",
        "Every test result goes in the traveller; nonconformances are raised as ECOs (supply-and-change process).",
    ], "NOTES", 13)
    S.save(DWG / "AON-900_test_plan.svg")


def cover(sheets):
    S = sheet("AON-000", "AON-1 3U CUBESAT: DRAWING SET", scale="NTS", material="see AON-002", finish="-", mass=f"{BASIS['mass']['cbe_g']:.0f} g CBE")
    S.text(100, 110, "AON-1 Ambient Orbital Node 1: 3U CubeSat, rev A (structure, integration, harness, test)", 34, bold=True)
    p, lk = BASIS["power"], BASIS["link"]
    S.text(100, 152, f"100 x 100 x 340.5 mm on hard-anodised rails · {BASIS['mass']['cbe_g']:.0f} g CBE · 28 CIC cells · {p['batt_Wh']:.0f} Wh · UHF 2 W, "
           f"{lk['dl_margin_dB']:.1f} dB downlink margin at 10° · EOR-1 flight runtime", 18)
    from sh_asm import img as im
    im(S, IMG / "iso.png", 100, 190, 1100, 960)
    im(S, IMG / "cutaway.png", 1150, 190, 1100, 960)
    S.table(100, 1200, [("SHEET", 130), ("TITLE", 900)], sheets, "SHEETS", 14, 28)
    S.table(1300, 1200, [("DESIGN DATA", 330), ("", 1100)], [
        ("Mission", "authenticated telemetry, command and store-and-forward messaging for the Ambient/Enumium network, 500 km"),
        ("Structure", "4 rails (2 variants) + 3 machined frames, 6061-T6; 24 M2.5 countersunk screws; boards on 4 Ti rods"),
        ("Power", f"7 cells per long face, 2 MPPT channels, 2S2P 18650; orbit-average {p['orbit_avg_gen_tumble_W']:.1f} W tumbling vs {p['orbit_avg_load_W']:.1f} W load"),
        ("Avionics", "E01 EPS, E02 battery, E03 OBC/ADCS (STM32H743), E04 UHF COM, E05 antenna, E06 panels with coils, E07 end board"),
        ("Safety", "3 inhibits (2 deployment switches + RBF), 30-min deploy and 45-min RF timers in firmware and hardware"),
        ("Files", "cad/ STEP + GLB · dxf/ cut files mm + inch · firmware/eor1 (146 host checks) · design/design-basis.md"),
        ("Status", "FOR REVIEW. Boards E01-E07 are envelopes until the KiCad layouts are done (next phase)."),
    ], None, 14, 30)
    S.save(DWG / "AON-000_cover.svg")


def all_doc():
    hardware(); e01(); e02(); itp()
