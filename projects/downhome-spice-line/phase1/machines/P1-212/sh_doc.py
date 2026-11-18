"""P1-212-000 cover + index, -003 assembly and cleaning, -600 hardware and bought parts, -900 ITP + calculations."""
import base64
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

IMG = DWG / "img"
C = calcs()


def img(S, path, x, y, w, h):
    b = base64.b64encode(path.read_bytes()).decode()
    S.add(f'<image href="data:image/png;base64,{b}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')


def assembly():
    S = sheet("P1-212-003", "ASSEMBLY, CLEANING PULL-OUT, TORQUES", scale="NTS", material="see item list", finish="-", mass=f"{sum(MASS.values()):.1f} kg made parts + bought ≈ 9.5 kg")
    cap = ["1  Barrel weldment hung on the bin flange", "2  Screw slid in from the tail end", "3  Drive housing + shaft into the end flange",
           "4  Lantern, coupling, gearmotor", "5  Tail cap + bush, hex-nut clamp", "6  Sleeve to the hopper lid stub"]
    for i in range(6):
        x, y = 120 + (i % 3) * 560, 120 + (i // 3) * 380
        img(S, IMG / f"fd_s{i + 1}.png", x, y + 10, 540, 336)
        S.add(f'<rect x="{x}" y="{y + 10}" width="540" height="336" fill="none" stroke="#b0bec5"/>')
        S.text(x + 8, y + 32, cap[i], 17, bold=True)
    S.text(120, 900, "orange = parts added in that step; ghosted = parts still to come", 13, color="#607d8b")
    steps = [
        ("1", "Bench: assemble the drive cartridge: bearings + spacers on the shaft (DIN 471 both), into housing from the rear, DIN 472, pin H5 pressed, lip seal from the front (grease H1).", "H5, H6, H7", "shaft turns freely; end play < 0.1"),
        ("2", "Bench: O-ring P1-243 in the housing face; housing onto the barrel end flange recess.", "H2 x4 M6, 8 N·m", "spigot fully seated, no gap at the collar"),
        ("3", "Bench: lantern onto the housing rear flange; coupling hubs on both shafts (keys H8, set screws H10); gearmotor into the lantern spigot.", "H3 x4 + H4 x4 M6, 8 N·m; H10 5 N·m", "coupling gap 1.6 [1/16 in]; turn by hand"),
        ("4", "Plant: gasket P1-212-501 on the bin flange, lift the feeder (≈ 25 kg [55 lb], 2 people), spout over the lid port, bolt up.", "H1 x4 M10, 25 N·m cross", "spout centred on the lid stub ±3; barrel level ±1°"),
        ("5", "Slide the screw in from the tail end, slot over the drive pin (turn the screw until it drops on).", "-", "screw turns by hand with the motor fan; no rub"),
        ("6", "Tail bush + cap P1-212-306 with gasket P1-246, hex-nut clamp P1-247.", "clamp nut hand-tight + 1/4 turn with a wrench", "cap seated; tool needed to open"),
        ("7", "Sleeve P1-214 over the spout and the lid stub, 2 band clamps.", "band clamps 3 N·m", "sleeve slack 10 [.4]: hopper weight not carried"),
        ("8", "Guards P1-212-404 on the lantern; isolator P1-248 on the ring leg; wire per E01/E02.", "H9 x4 M5, 3 N·m", "point-to-point check vs E02"),
        ("9", "Commission per P1-212-900 (rotation, enable, Modbus, calibration).", "-", "sign the ITP record"),
    ]
    S.table(1830, 120, [("STEP", 60), ("HARDWARE / TORQUE", 520), ("CHECK BEFORE THE NEXT STEP", 990)], [(a, c, d) for a, b, c, d in steps],
            "ASSEMBLY STEPS: HARDWARE AND CHECKS", 13, 24)
    S.notes(1830, 380, 1570, [f"Step {a}: {b}" for a, b, c, d in steps], title="ASSEMBLY STEPS: OPERATIONS", fs=13)
    S.notes(120, 940, 1650, [
        "Lock out isolator Q-21n (P1-248) and try the HMI start: the feeder must not run.",
        "Open the tail clamp with a wrench; remove the cap with the bush (catch the powder in a scoop; vacuum, never blow).",
        "Pull the screw straight out of the tail end (5.8 kg, 1.2 m long); lay it on the cleaning rack, not the floor.",
        "Barrel: brush from the tail end with the 2.5 in brush on a rod; wipe; the inlet is reached from the bin side when the bin is empty.",
        "Allergen changeover: wash screw, cap, bush in the sink (warm detergent, rinse, sanitise, air dry); dry barrel with the swab; ATP swab the screw (ITP T25).",
        "Refit in reverse (steps 5, 6). The drive end is never opened for cleaning: the lip seal keeps product out of the bearings.",
    ], "CLEANING / ALLERGEN CHANGEOVER (about 15 min per feeder)", fs=13)
    rows = [(h, d[:58], g, q, w[:48], t[:36]) for h, d, g, q, w, t in HARDWARE]
    S.table(1830, 1180, [("ITEM", 50), ("DESCRIPTION", 470), ("STANDARD", 170), ("QTY", 40), ("WHERE", 560), ("TORQUE", 290)], rows, "HARDWARE AND TORQUES (per feeder, all A2/A4 stainless)", 12, 22)
    S.save(DWG / "P1-212-003_assembly.svg")


def hardware():
    S = sheet("P1-212-600", "BOUGHT PARTS AND HARDWARE (PER FEEDER, 9 FEEDERS)", scale="NTS", material="-", finish="-", mass="-")
    import textwrap
    rows = []
    for t, d, m, p, q, u, n in BOUGHT:
        dl, pl = textwrap.wrap(d, 150), textwrap.wrap(p, 95)
        rows.append((t, dl[0], m, pl[0], q, q * 9, f"${u:,.0f}", f"${u * q * 9:,.0f}"))
        for k in range(1, max(len(dl), len(pl))):
            rows.append(("", "  " + dl[k] if k < len(dl) else "", "", "  " + pl[k] if k < len(pl) else "", "", "", "", ""))
    S.table(120, 140, [("TAG", 90), ("DESCRIPTION", 1000), ("MAKER", 260), ("PART NUMBER", 640), ("QTY", 50), ("x9", 50), ("UNIT", 90), ("TOTAL x9", 110)], rows,
            "BOUGHT PARTS (estimates unless noted; confirm before order)", 12, 24)
    tot = sum(u * q * 9 for t, d, m, p, q, u, n in BOUGHT)
    S.text(120, 140 + 24 * (len(rows) + 1) + 30, f"Bought parts for 9 feeders ≈ ${tot:,.0f}  (drives P1-226 and panel parts are priced in the plant BOM)", 16, bold=True)
    S.table(120, 760, [("TAG", 90), ("NOTE", 1500)], [(t, n) for t, d, m, p, q, u, n in BOUGHT if n], "PURCHASING NOTES", 12, 22)
    S.table(120, 1100, [("ITEM", 60), ("DESCRIPTION", 620), ("STANDARD", 300), ("QTY", 50), ("x9", 50), ("WHERE", 600), ("TORQUE", 380)],
            [(h, d, g, q, q * 9, w, t) for h, d, g, q, w, t in HARDWARE], "HARDWARE", 12, 24)
    mat = [("316L tube A270 2.5 in x 16 ga, S2 polished ID", f"{(X_TUBE1 - X_TUBE0 + 140) / 1000:.2f} m", f"{9 * (X_TUBE1 - X_TUBE0 + 140) / 1000:.1f} m (2 x 20 ft sticks)"),
           ("316L sheet 14 ga (transition walls)", "0.10 m²", "1 sheet 48 x 48 in"), ("316L plate 6 mm (inlet flange)", "200 x 200", "1 plate 24 x 24 in nest"),
           ("316L plate 12 mm (end flange)", "112 x 112", "9 blanks"), ("316 bar Ø25 (screw shaft)", "1.22 m", "11 m (3 x 12 ft)"),
           ("316 bar Ø25 (drive shaft)", "0.22 m", "2.0 m"), ("316 bar Ø115 (drive housing)", "0.12 m", "1.1 m"), ("316 bar Ø85 (tail cap)", "0.05 m", "0.5 m"),
           ("304 plate 8 mm (lantern)", "plates + bars", "1 plate 24 x 24 in"), ("304 perforated 1.5 mm Ø5 (guards)", "2 x 74 x 118", "1 sheet 24 x 24 in"),
           ("UHMW-PE FDA rod Ø35", "0.03 m", "0.3 m"), ("FDA silicone sheet 3 mm", "200 x 200", "1 sheet 24 x 24 in")]
    S.table(120, 1450, [("MATERIAL", 560), ("PER FEEDER", 200), ("FOR 9 (+ cut allowance)", 330)], mat, "RAW MATERIAL (made parts)", 12, 22)
    S.save(DWG / "P1-212-600_bought_hardware.svg")


def itp():
    S = sheet("P1-212-900", "INSPECTION AND TEST PLAN, DESIGN CALCULATIONS", scale="NTS", material="-", finish="-", mass="-")
    tests = [
        ("T1", "Material certs 316L / 316 (EN 10204 3.1), tube A270 S2", "on file", "receiving", "QC"),
        ("T2", "Barrel straightness and inlet flange squareness", "0.5 / 0.5 over 200", "after W1-W6", "fab"),
        ("T3", "Barrel ID and welds: borescope, no crevice, no concavity > 0.1", "pass", "after W3, W5, W6", "QC"),
        ("T4", "End flange recess Ø70 H8 coaxial to A, face ⟂ A", "Ø0.1 / 0.1", "after machining", "QC"),
        ("T5", "Housing: seal bore, bearing bore, spigot (limits on -300)", "in limits", "100 %", "QC"),
        ("T6", "Drive shaft: k6 seats, h9 lip journal Ra 0.4, pin proud 2 ±0.3", "in limits", "100 %", "QC"),
        ("T7", "Screw: flight OD 56 +0/-0.3, shaft TIR 0.3, flight TIR 0.5, pitch 56 ±1", "in limits", "after straightening", "QC"),
        ("T8", "Screw slides through the barrel by hand (dry fit)", "no rub", "before polish", "fab"),
        ("T9", "Passivation (ASTM A967), water-break free, ferroxyl test on one barrel", "pass", "after passivate", "QC"),
        ("T10", "Drive cartridge turns freely, end play < 0.1, lip seal seated", "pass", "assembly step 1", "assy"),
        ("T11", "Coupling gap 1.6 and alignment by spigots (no shims)", "pass", "step 3", "assy"),
        ("T12", "Feeder hung: spout centred on the lid stub ±3, sleeve slack", "pass", "step 7", "assy"),
        ("T13", "Insulation resistance motor + cable at 500 V DC (drive disconnected)", "> 1 MΩ", "before power", "elec"),
        ("T14", "Rotation: screw carries product toward the spout (+x)", "correct", "first run, empty", "elec"),
        ("T15", "Isolator OFF stops the drive (DI1) before the main poles open", "pass", "commissioning", "elec"),
        ("T16", "E-stop drops KM-DOS, all 9 drives stop; restart needs reset", "pass", "commissioning", "elec"),
        ("T17", "Modbus: address n answers, run/stop/frequency/status from the PLC", "pass", "commissioning", "elec"),
        ("T18", "Comm loss: unplug W-P30, drive stops ≤ 0.5 s, alarm", "pass", "commissioning", "elec"),
        ("T19", "Empty run 30 min at fast speed: no noise, current < 1.0 A, housing < 50 °C", "pass", "commissioning", "mech"),
        ("T20", "Calibration: fast and slow rate per bin with the real ingredient (g/s)", "record", "per bin", "QA"),
        ("T21", "Dosing accuracy over 10 doses at the recipe target", "±0.5 % or ±20 g", "per bin", "QA"),
        ("T22", "Product flow from a full bin, no bridging at the inlet (herbs with agitator)", "pass", "per bin", "QA"),
        ("T23", "Cleaning: pull-out and refit in ≤ 15 min by one person", "pass", "training", "ops"),
        ("T24", "Tail cap needs a tool; cap off with isolator ON is not done (LOTO training)", "pass", "training", "ops"),
        ("T25", "ATP swab on screw and barrel after allergen wash", "< 150 RLU", "each changeover", "QA"),
        ("M1", "Maintenance: lip seal and O-ring replace", "12 months", "planned", "maint"),
        ("M2", "Maintenance: tail bush replace when the screw drops > 1 mm", "check monthly", "planned", "maint"),
    ]
    S.table(120, 140, [("TEST", 60), ("WHAT IS CHECKED", 820), ("LIMIT", 220), ("WHEN / PART", 230), ("BY", 70), ("RESULT / SIGN", 220)],
            [t + ("",) for t in tests], "INSPECTION AND TEST PLAN (record results here or in the MES)", fs=13, rh=24)
    m_in = MASS.get("P1-212-101", 0) + MASS.get("P1-212-106", 0) + MASS.get("P1-212-107", 0) + MASS.get("P1-212-306", 0) + C["mass_screw"]
    m_out = MASS.get("P1-212-301", 0) + MASS.get("P1-212-302", 0) + MASS.get("P1-212-400", 0) + 8.0
    mom = (m_in * 9.81 * 0.50) - (m_out * 9.81 * 0.37)
    calc = [
        ("Volume per turn (full)", f"{C['vol_rev']:.4f} L", "π/4 (56² - 25²) x 56"), ("Fill / volume per turn", f"40 % / {C['q_rev']:.4f} L", "free-flowing seasonings 30-45 %"),
        ("Screw speed at 60 Hz", f"{C['n60']:.0f} rpm", "1,690 / 10.25"),
        ("Fast rate (150 rpm)", f"{C['q_fast_lh']:.0f} L/h = {C['q_fast_kgmin']:.2f} kg/min", "at 0.55 kg/L"),
        ("Slow rate (15 rpm)", f"{C['q_slow_lh']:.0f} L/h = {C['q_slow_gs']:.1f} g/s", "dribble: in-flight ≈ 0.3 s x 6 g/s = 2 g"),
        ("Output torque (rated)", f"{C['T_out']:.1f} N·m", "0.25 kW, η 0.9, 165 rpm"),
        ("Drive pin shear", f"{C['tau_pin']:.1f} MPa (2 planes)", "A1-70 pin τ allow ≈ 200 MPa: SF > 8"),
        ("Screw deflection (simply supported)", f"{C['defl']:.2f} mm over {C['span']:.0f}", f"clearance {C['clear']:.1f} radial: OK"),
        ("Bearing load (radial, each)", "≈ 30 N", "W 6004 C = 9.4 kN: life unlimited"),
        ("Moment at the bin flange", f"{mom:.0f} N·m net", f"barrel side {m_in:.1f} kg at 0.50 m vs drive {m_out:.1f} kg at 0.37 m"),
        ("Bolt load at bin flange (4 x M10)", f"{abs(mom) / 0.16 + 9.81 * (m_in + m_out) / 4:.0f} N per bolt pair", "preload at 25 N·m ≈ 12 kN each"),
        ("Motor current / drive", "1.3 A / GS21 0.5 HP 2.5 A", "drive sized 1 frame up for low-speed torque"),
    ]
    S.table(1800, 140, [("CALCULATION", 420), ("RESULT", 420), ("NOTE / LIMIT", 600)], calc, "DESIGN CALCULATIONS (design.py calcs())", fs=13, rh=24)
    S.save(DWG / "P1-212-900_itp.svg")


def cover_sheet(sheets):
    S = sheet("P1-212-000", "P1-212 BIN SCREW FEEDER: DRAWING SET", scale="NTS", material="316L product contact, 304 drive frame", finish=FIN_PC,
              mass=f"{sum(MASS.values()) + 9.5:.0f} kg [{(sum(MASS.values()) + 9.5) * 2.2046:.0f} lb] each")
    S.text(120, 120, "Bin screw feeder P1-212, built in house, 9 off, rev B", 34, bold=True)
    S.text(120, 160, f"2.5 in sanitary barrel, Ø56 screw supported both ends, {C['q_fast_lh']:.0f} L/h fast / {C['q_slow_gs']:.0f} g/s dribble, 0.25 kW gearmotor on Modbus drive, tool-free inside, screw pulls out the tail end", 18)
    img(S, IMG / "fd_full.png", 120, 210, 1550, 886)
    S.table(1800, 210, [("DESIGN DATA", 330), ("", 900)], [
        ("Duty", "dose one ingredient at a time from bin B0n into the weigh hopper P1-220 (DosingStation.st)"),
        ("Barrel", "ASTM A270 316L 2.5 in x 16 ga, ID Ra ≤ 0.8 µm, 1,195 flange to tail"),
        ("Screw", f"Ø{S_OD:.0f} x pitch {S_P:.0f} x {S_T:.0f} formed flight on Ø{S_D:.0f} shaft, RH, clearance {C['clear']:.1f}"),
        ("Support", "drive pin in socket at the drive end, UHMW bush at the tail; no bearing in the product"),
        ("Drive", "NORD SK 072.1 0.25 kW i 10.25, B14 lantern, L-075 jaw coupling; GS21 drive, Modbus RTU"),
        ("Seals", "PTFE lip seal 20x35x7 + EPDM O-ring at the drive end; TC 2.5 in at the tail"),
        ("Plant interface", "bin flange 200 sq 4 x Ø11 on 160 sq; spout on R280 over the hopper lid; axis 1,526 AFF"),
        ("Safety", "isolator in sight with early-break aux; KM-DOS on E-stop; tail cap = tool-fixed guard"),
        ("Changes in rev B", "longer barrel (spout vertical over the lid), tail bush, drive cartridge, ring legs moved 15°"),
    ], fs=13, rh=24)
    S.table(1800, 500, [("SHEET", 150), ("TITLE", 860), ("FILE", 220)], [(n, t, n + " svg / PDF") for n, t in sheets], "SHEET INDEX", fs=13, rh=24)
    S.notes(120, 1130, 1550, [
        "Units mm [in]. Third-angle projection. Tolerances in the title block unless noted. Weld symbols AWS A2.4; welding to AWS D18.1 / ASME BPE MJ.",
        "Product-contact parts 316L / 316, Ra ≤ 0.8 µm, welds ground flush, passivated ASTM A967. Seals and plastics FDA 21 CFR 177.",
        "Cut files (DXF) in dxf/ in mm and inch; 3D: cad/ (STEP per part, P1-212-ASM.step/.glb); generator: design.py, model.py, sh_*.py.",
        "Bought parts marked 'confirm' must be checked against the supplier drawing before the matching made part is cut (gearmotor flange, drive model).",
        "Release for build: drawings checked, ITP P1-212-900 attached to the traveler, materials certified.",
    ], "GENERAL NOTES", fs=13)
    S.save(DWG / "P1-212-000_cover.svg")


if __name__ == "__main__":
    assembly(); hardware(); itp()
