"""P1-212 electrical: E01 power + control schematic (typical feeder n = 1..9), E02 wire / cable list, terminals, drive settings."""
from common import *  # noqa: F401,F403
from mechsheet import Sch, BLU, GRY
from design import calcs, N_FAST, N_SLOW

INK, RED = "#111", "#b00020"
BINS = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09"]
C = calcs()

COMPONENTS = [
    ("KM-DOS", "Safety contactor 2-pole 25 A AC-3, 24 V DC coil, mirror aux (feeder drive supply)", "Siemens 3RT2016-1BB42 + 3RH2911 (or equal)", "MS-P1", 1),
    ("Q21..Q25", "MCB 2-pole C 16 A, 10 kA (1 per 2 drives; Q25 feeds drive 9 only)", "ABB S202-C16", "MS-P1", 5),
    ("U21..U29", "AC drive 0.5 HP 230 V 1-ph in / 3-ph out, RS-485 Modbus RTU (P1-226)", "AutomationDirect GS21-20P5 (confirm)", "MS-P1", 9),
    ("Q-21n", "Motor isolator 16 A lockable + early-break NO aux (P1-248)", "ABB OTP16T3M + OA1G10 (confirm)", "ring leg at bin n", 9),
    ("M-21n", "Gearmotor 0.25 kW 230/460 V Δ/Y, 1.3 A at 230 V (P1-216)", "NORD SK 072.1-71S/4", "feeder n", 9),
    ("R-485", "Termination 120 Ω 0.25 W at the last node (blender drive P1-336)", "-", "P1-336", 1),
]
WIRES = [
    ("21n.L1 / 21n.L2", "Q2x : 2 / 4", "U2n : R/L1, S/L2", "14 AWG [2.1 mm²] MTW black", "drive supply"),
    ("21n.PE", "PE bar MS-P1", "U2n : PE", "14 AWG green/yellow", ""),
    ("W-M21n 1/2/3", "U2n : U/T1, V/T2, W/T3", "Q-21n : 1 / 3 / 5", "VFD cable 4C 14 AWG shielded (cores 1,2,3)", "shield 360° at both EMC glands"),
    ("W-M21n G/Y", "U2n : PE", "Q-21n : PE", "VFD cable core G/Y", ""),
    ("W-M21n.1 1/2/3", "Q-21n : 2 / 4 / 6", "M-21n : U1 / V1 / W1 (Δ links fitted)", "VFD cable 4C 14 AWG shielded, 1.5 m", "motor 230 V Δ"),
    ("W-M21n.1 G/Y", "Q-21n : PE", "M-21n : PE", "core G/Y", ""),
    ("W-C21n 1", "U2n : +24V", "Q-21n : 13", "2C 18 AWG [0.82 mm²] TC-ER shielded", "early-break aux"),
    ("W-C21n 2", "Q-21n : 14", "U2n : DI1 (RUN ENABLE)", "same cable", "opens before the main poles"),
    ("21n.DCM", "U2n : DCM", "U2n : DI common link", "drive internal link", "SINK mode, per GS21 manual"),
    ("W-P30", "U2(n-1) : RS-485 D+/D-/SG", "U2n : RS-485 D+/D-/SG", "Belden 3105A 1 pr + drain", "daisy chain, drain to SG one end"),
]
VFD = [
    ("Motor rated voltage", "230 V", "nameplate"), ("Motor rated current", "1.30 A", "nameplate (confirm)"), ("Motor rated frequency / speed", "60 Hz / 1,690 rpm", ""),
    ("Max output frequency", "60.0 Hz", f"{C['n60']:.0f} rpm screw"), ("Min output frequency", "5.0 Hz", f"{5 / 60 * C['n60']:.0f} rpm"),
    ("Fast dosing setpoint", f"{C['f_fast']:.1f} Hz", f"{N_FAST:.0f} rpm, {C['q_fast_kgmin']:.1f} kg/min at 0.55 kg/L"),
    ("Slow (dribble) setpoint", f"{C['f_slow']:.1f} Hz", f"{N_SLOW:.0f} rpm, {C['q_slow_gs']:.1f} g/s"),
    ("Accel / decel time", "0.5 s / 0.2 s", "short decel = small in-flight error"), ("Stop method", "ramp to stop", ""),
    ("Reverse", "DISABLED", "reverse packs powder at the drive end"),
    ("Command / frequency source", "RS-485 (Modbus RTU)", "from P1-225 750-652"), ("Comm address", "n = 1..9 (bin B0n)", "blender P1-336 = 10"),
    ("Baud / format", "19,200, RTU 8-E-1", "same on every node"), ("Comm loss", "stop after 0.5 s", "fault + alarm on the MES"),
    ("DI1 function", "run enable (external permissive)", "isolator early-break aux"), ("Electronic overload", "1.30 A, standard motor", "motor protection (no thermistor)"),
    ("Carrier frequency", "8 kHz", "quiet; derate check OK at 0.25 kW"),
]


def e01():
    S = sheet("P1-212-E01", "ELECTRICAL: FEEDER POWER AND CONTROL (TYPICAL n = 1..9)", scale="NTS", material="see component list",
              finish="UL 508A practice, NEC 430 / 430.102 (disconnect in sight); 75 °C Cu", mass="-", qty="9 circuits")
    c = Sch(S)
    c.t(120, 110, "POWER (one feeder shown; repeat for n = 1..9)", 20, bold=True)
    # supply bus
    xL1, xL2 = 300, 360
    c.t(xL1 - 10, 160, "L1", 14, "end", INK, True); c.t(xL2 + 10, 160, "L2  230 V 1-ph from MS-P1 dosing bus", 14, "start", INK, True)
    c.w(xL1, 165, xL1, 200); c.w(xL2, 165, xL2, 200)
    c.box(250, 200, 170, 70, "KM-DOS", ["safety contactor (E-stop)", "1-2 / 3-4"])
    c.w(xL1, 270, xL1, 320); c.w(xL2, 270, xL2, 320)
    c.box(250, 320, 170, 70, "Q2x", ["MCB 2P C16 (2 drives)", "1-2 / 3-4"])
    c.w(xL1, 390, xL1, 450, no="21n.L1", side=-1); c.w(xL2, 390, xL2, 450, no="21n.L2")
    c.box(230, 450, 230, 170, "U2n  GS21-20P5", ["AC drive 0.5 HP (P1-226)", "R/L1  S/L2   in", "U/T1 V/T2 W/T3 out", "RS-485, DI1 enable"])
    for i, x in enumerate((280, 340, 400)):
        c.w(x, 620, x, 760, no=f"W-M21n {i + 1}", side=1 if i == 2 else -1 if i == 0 else 1)
    c.t(470, 700, "VFD cable 4C 14 AWG shielded", 12, "start", GRY); c.t(470, 716, "shield 360° both ends", 12, "start", GRY)
    c.box(230, 760, 230, 110, "Q-21n  ISOLATOR 16 A", ["on the ring leg beside bin n", "lockable OFF, IP66 (P1-248)", "1/3/5 → 2/4/6, aux 13-14"], dash=False)
    for x in (280, 340, 400):
        c.w(x, 870, x, 960)
    c.t(470, 920, "W-M21n.1, 1.5 m", 12, "start", GRY)
    c.motor(340, 1000, "M-21n  0.25 kW 230 V Δ  (P1-216)")
    c.w(280, 960, 315, 975); c.w(400, 960, 365, 975)
    # PE
    c.w(200, 480, 230, 480, "#2e7d32"); c.w(200, 480, 200, 1040, "#2e7d32"); c.w(200, 1040, 310, 1040, "#2e7d32"); c.t(190, 760, "PE", 13, "end", "#2e7d32", True)
    # control: enable loop
    c.t(1000, 110, "CONTROL", 20, bold=True)
    c.box(1000, 160, 320, 230, "U2n (drive control terminals)", ["+24V  (internal supply)", "DI1   RUN ENABLE", "DCM   common (SINK)", "RS-485  D+  D-  SG", "RA/RC  fault relay (spare)"])
    c.term(1330, 210, "+24V"); c.term(1330, 240, "DI1")
    c.w(1330, 210, 1500, 210, no="W-C21n 1"); c.w(1330, 240, 1450, 240, no="W-C21n 2")
    c.w(1500, 210, 1500, 260); c.sw_v(1500, 260, "Q-21n 13-14 early-break NO")
    c.w(1500, 310, 1500, 330); c.w(1450, 330, 1500, 330); c.w(1450, 240, 1450, 330)
    c.t(1000, 430, "Isolator OFF → aux opens first → DI1 drops → drive stops on the ramp before the main poles break (no switching under load).", 13)
    c.t(1000, 450, "PLC sees 'not enabled' over Modbus status and skips the bin; MES shows 'feeder n isolated'.", 13)
    # E-stop / safety contactor
    c.t(1000, 520, "SAFETY (from plant safety relay SR-P1, DH-ELE-P1-003)", 16, bold=True)
    c.w(1000, 560, 1600, 560); c.t(990, 565, "+24 V safe out (SR-P1 S34 / 14)", 12, "end")
    c.w(1100, 560, 1100, 590); c.coil_h(1100, 612, "KM-DOS"); c.w(1100, 623, 1100, 660); c.w(1000, 660, 1600, 660); c.t(990, 665, "0 V", 12, "end")
    c.t(1140, 610, "E-stop or dosing-room guard → SR-P1 drops KM-DOS → all 9 drives lose supply (stop cat. 0).", 13)
    c.t(1140, 628, "KM-DOS mirror contact 21-22 to SR-P1 feedback loop (EDM).", 13)
    c.t(1140, 646, "If the drives bought have STO, wire STO1/STO2 from SR-P1 instead and keep KM-DOS as the supply switch.", 13, col=RED)
    # Modbus chain
    c.t(1000, 740, "RS-485 MODBUS RTU (W-P30, Belden 3105A, daisy chain)", 16, bold=True)
    xs = [1000 + 120 * i for i in range(11)]
    c.box(1000, 770, 100, 60, "750-652", ["P1-225"])
    for i in range(1, 11):
        c.box(xs[i] - 10, 770, 100, 60, f"U2{i}" if i < 10 else "P1-336", [f"addr {i}" if i < 10 else "addr 10, 120 Ω"])
        c.w(xs[i - 1] + 90, 800, xs[i] - 10, 800)
    c.t(1000, 860, "D+ / D- twisted pair, SG to drain; drain bonded at the PLC end only; no stubs > 0.3 m; 120 Ω at the far end only.", 13)
    S.table(1000, 920, [("TAG", 120), ("DESCRIPTION", 620), ("PART", 330), ("WHERE", 160), ("QTY", 50)], COMPONENTS, "COMPONENTS (feeder circuits)", fs=13, rh=22)
    rows = []
    for n, b in enumerate(BINS, 1):
        q = 21 + (n - 1) // 2
        rows.append((n, b, f"U2{n}", f"Q{q}", f"Q-21{n}", f"M-21{n}", f"W-M21{n} / W-M21{n}.1", f"W-C21{n}", n))
    S.table(1000, 1140, [("n", 40), ("BIN", 60), ("DRIVE", 80), ("MCB", 70), ("ISOLATOR", 100), ("MOTOR", 90), ("POWER CABLES", 240), ("ENABLE", 100), ("MODBUS", 80)],
            rows, "TAG TABLE (n = feeder = bin number)", fs=13, rh=22)
    S.notes(120, 1150, 800, [
        "Load: 9 x 1.3 A motors, drives 1-ph input ≈ 4.4 A each at full load; one feeder runs at a time (DosingStation.st), so the dosing bus carries < 10 A.",
        "Disconnect in sight (NEC 430.102(B)): isolator Q-21n at each bin; lockable OFF, used for LOTO before opening the tail cap.",
        "Cable lengths ~15 m [50 ft] from MS-P1 (confirm on site); VFD cable max 50 m without output reactor (GS21 manual).",
        "Bond the barrel and gearmotor to PE (< 10 Ω) through the motor cable G/Y and the bin ring.",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-212-E01_power_control.svg")


def e02():
    S = sheet("P1-212-E02", "ELECTRICAL: WIRE LIST, ISOLATOR TERMINALS, DRIVE SETTINGS", scale="NTS", material="-", finish="ferrules on all fine-strand ends; labels both ends", mass="-", qty="9 circuits")
    S.table(120, 140, [("WIRE / CABLE (n = 1..9)", 260), ("FROM", 270), ("TO", 330), ("TYPE", 380), ("NOTE", 330)], WIRES, "WIRE LIST (typical feeder n)", fs=13, rh=24)
    S.table(120, 520, [("TERMINAL", 120), ("FUNCTION", 300), ("WIRE IN", 220), ("WIRE OUT", 220)], [
        ("1 / 3 / 5", "line in (from drive U/V/W)", "W-M21n 1/2/3", "-"), ("2 / 4 / 6", "load out (to motor)", "-", "W-M21n.1 1/2/3"),
        ("13 / 14", "early-break NO aux", "W-C21n 1", "W-C21n 2"), ("PE", "earth", "W-M21n G/Y", "W-M21n.1 G/Y")],
        "ISOLATOR Q-21n TERMINALS", fs=13, rh=24)
    S.table(120, 700, [("CABLE", 140), ("FROM", 160), ("TO", 200), ("SPEC", 420), ("EST. LENGTH", 130)],
            [(f"W-M21{n}", f"U2{n} MS-P1", f"Q-21{n} ring leg B0{n}", "4C 14 AWG VFD, shielded, 600 V, TC-ER", "15 m") for n in range(1, 10)] +
            [(f"W-M21{n}.1", f"Q-21{n}", f"M-21{n}", "4C 14 AWG VFD, shielded", "1.5 m") for n in (1,)] +
            [(f"W-C21{n}", f"U2{n} MS-P1", f"Q-21{n}", "2C 18 AWG shielded TC-ER", "15 m") for n in (1,)],
            "CABLE SCHEDULE (W-M21n.1 and W-C21n: same for n = 2..9)", fs=13, rh=22)
    S.table(1500, 140, [("SETTING (GS21 parameter names; confirm numbers in the GS21 manual)", 520), ("VALUE", 260), ("NOTE", 500)], VFD,
            "DRIVE SETTINGS U21..U29", fs=13, rh=24)
    S.table(1500, 640 + 40, [("MODBUS REGISTER (confirm in GS21 manual)", 500), ("USE", 420), ("SCALE", 200)], [
        ("command word (run / stop)", "write 1 = run fwd, 0 = stop (decel ramp)", "-"), ("frequency command", "write fast / slow setpoint", "0.01 Hz"),
        ("status word", "read: running, enabled (DI1), fault", "bits"), ("output current", "read: torque trend / bridging alarm", "0.01 A"),
        ("fault code", "read on fault; reset after the cause is cleared", "-")], "MODBUS MAP (P1-225 DosingStation.st)", fs=13, rh=24)
    S.notes(1500, 900, 1280, [
        "Bridging / empty bin: the MES compares the weight gain per second with the setpoint; if < 30 % for 5 s at fast speed the feeder stops and alarms 'no flow B0n'.",
        "Over-torque: output current > 1.2 A for 2 s = plug at the discharge or a foreign object; stop, alarm, no auto-restart.",
        "After any fault the operator must confirm on the HMI; the screw is enclosed so no guard interlock is needed (tail cap = fixed guard, tool required).",
    ], "CONTROL NOTES", fs=13)
    S.save(DWG / "P1-212-E02_lists_settings.svg")


if __name__ == "__main__":
    e01(); e02()
