"""P1-304 electrical: E01 power + control schematic, E02 wire list, cable schedule, terminals, PLC logic."""
from common import *  # noqa: F401,F403
from mechsheet import Sch, BLU, GRY
from design import calcs, N_VIB, F_MAX, AMP_TARGET

INK, RED = "#111", "#b00020"
C = calcs()

COMPONENTS = [
    ("CB-306", "Circuit breaker 1-pole 15 A, 10 kA, 120 V branch (existing schedule M-306)", "ABB S201-C15 (or panel standard)", "MS-P1", 1),
    ("F-306", "Manual motor protector 2.5-4.0 A, set to vibrator FLA; 1-ph: wire through all 3 poles in series", "ABB MS116-4.0 + HKF1-11 aux (P1-349)", "MS-P1", 1),
    ("KM-306", "Contactor 9 A 3-pole, 24 V DC coil, + 1 NO aux", "ABB AF09-30-10-13 (P1-349)", "MS-P1", 1),
    ("Q-306", "Motor isolator 2-pole 16 A, lockable OFF, early-break NO aux, IP66 (P1-348)", "ABB OTP16T2M + OA1G10", "blender frame leg", 1),
    ("M-306", "Rotary vibrator 115 V 1-ph 60 Hz 2-pole, ≈ 2.9 A FLA (P1-306)", "OLI MVE 200/36 class 1-ph (confirm)", "sifter bracket", 1),
    ("X-306", "Terminal block 4 x 4 mm² + PE in the isolator enclosure", "Phoenix UT 4 (or equal)", "Q-306", 1),
]
WIRES = [
    ("306.L1", "CB-306 : 2", "F-306 : 1", "14 AWG MTW black", ""),
    ("306.L2 / .L3", "F-306 : 2 → 3, 4 → 5", "jumpers", "14 AWG MTW black", "1-ph: all 3 poles in series (MS116 manual)"),
    ("306.L4", "F-306 : 6", "KM-306 : 1/L1", "14 AWG MTW black", ""),
    ("W-306 1", "KM-306 : 2/T1", "Q-306 : 1 (L)", "3C 14 AWG TC-ER + G/Y", "fixed cable, tray then conduit"),
    ("W-306 2", "N bar MS-P1", "Q-306 : 3 (N)", "same cable", "neutral switched at the isolator only"),
    ("W-306 G/Y", "PE bar MS-P1", "Q-306 : PE", "same cable", ""),
    ("P1-350 L / N / PE", "Q-306 : 2 / 4 / PE", "M-306 : L / N / PE (terminal box)", "SOOW 14/3 flexible, 3 m", "drip loop; cord grip H6; tied to the plate"),
    ("W-306C 1", "+24 V DO field supply (safe, SR-P1)", "PLC 750-504 ch 5 (DO_SifterVib) : 24V", "panel wiring 18 AWG", ""),
    ("306.A1", "PLC DO_SifterVib : out", "KM-306 : A1", "18 AWG MTW blue", "wire 225-03-05"),
    ("306.A2", "KM-306 : A2", "0 V", "18 AWG MTW blue/white", ""),
    ("W-306C 2/3", "Q-306 : 13 / 14", "PLC DI_SifterIso (spare DI) / +24 V", "2C 18 AWG TC-ER shielded", "isolator ON = 1"),
    ("306.TR", "F-306 HKF1 : 13 / 14", "PLC DI_SifterTrip (spare DI) / +24 V", "18 AWG panel", "protector ON = 1"),
    ("P1-347", "body bracket (H5 at 90°)", "seat ring (H5 at 60°)", "braid 16 mm², 250", "bonds the isolated body (< 1 Ω)"),
]


def e01():
    S = sheet("P1-304-E01", "ELECTRICAL: VIBRATOR POWER AND CONTROL", scale="NTS", material="see component list",
              finish="UL 508A practice, NEC 430 / 430.102 (disconnect in sight); 75 °C Cu", mass="-")
    c = Sch(S)
    c.t(120, 110, "POWER 120 V 1-ph (load M-306 on the panel schedule)", 20, bold=True)
    xL, xN = 330, 520
    c.t(xL - 10, 160, "L", 14, "end", INK, True); c.t(xN + 10, 160, "N   120 V from panel MS-P1", 14, "start", INK, True)
    c.w(xL, 165, xL, 200); c.w(xN, 165, xN, 600)
    c.box(260, 200, 140, 60, "CB-306", ["1P C15"])
    c.w(xL, 260, xL, 300, no="306.L1", side=-1)
    c.box(240, 300, 190, 90, "F-306 MS116-4.0", ["3 poles in series (1-ph)", f"set to FLA ≈ 2.9 A (confirm)", "aux HKF1-11"])
    c.w(xL, 390, xL, 430, no="306.L4", side=-1)
    c.box(260, 430, 140, 70, "KM-306", ["AF09 1/L1 → 2/T1", "coil 24 V DC"])
    c.w(xL, 500, xL, 600, no="W-306 1", side=-1); c.w(xN, 560, xN, 600)
    c.t(560, 560, "W-306  3C 14 AWG TC-ER + G/Y, ≈ 12 m", 12, "start", GRY)
    c.box(260, 600, 330, 120, "Q-306  ISOLATOR 2P 16 A (P1-348)", ["on the blender frame leg, in sight of the sifter", "lockable OFF, IP66", "1/3 → 2/4 (L, N), aux 13-14 early-break"])
    c.w(xL, 720, xL, 860, no="P1-350 L", side=-1); c.w(xN, 720, xN, 860, no="P1-350 N", side=1)
    c.t(640, 790, "P1-350 SOOW 14/3 flexible, 3 m, drip loop", 12, "start", GRY)
    c.S.add(f'<circle cx="{(xL + xN) / 2}" cy="900" r="40" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
    c.t((xL + xN) / 2, 898, "M", 20, "middle", INK, True); c.t((xL + xN) / 2, 918, "1~", 13, "middle")
    c.w(xL, 860, (xL + xN) / 2 - 30, 880); c.w(xN, 860, (xL + xN) / 2 + 30, 880)
    c.t(xN + 60, 905, "M-306 vibrator 115 V 1-ph 3,600 rpm (P1-306), capacitor in the terminal box", 13)
    c.w(200, 620, 260, 620, "#2e7d32"); c.w(200, 620, 200, 1000, "#2e7d32"); c.w(200, 1000, (xL + xN) / 2 - 10, 1000, "#2e7d32"); c.w((xL + xN) / 2 - 10, 1000, (xL + xN) / 2 - 10, 940, "#2e7d32")
    c.t(190, 800, "PE", 13, "end", "#2e7d32", True)
    c.t(120, 1060, "Body bond: braid P1-347 bridges the rubber isolators (body ↔ base); motor frame earthed by the cord PE.", 13)
    # control
    c.t(1000, 110, "CONTROL 24 V DC", 20, bold=True)
    c.w(1000, 170, 1900, 170); c.t(1000, 160, "+24 V safe (SR-P1 output, DO module field supply)", 12, "start")
    c.w(1000, 470, 1900, 470); c.t(990, 475, "0 V", 12, "end")
    c.w(1150, 170, 1150, 230); c.box(1080, 230, 140, 60, "750-504 ch 5", ["DO_SifterVib", "wire 225-03-05"])
    c.w(1150, 290, 1150, 360, no="306.A1"); c.coil_h(1150, 380, "KM-306"); c.w(1150, 391, 1150, 470, no="306.A2")
    c.w(1450, 170, 1450, 220, no="W-306C 2"); c.sw_v(1450, 220, "Q-306 13-14 early-break"); c.w(1450, 270, 1450, 330, no="W-306C 3")
    c.box(1380, 330, 140, 50, "750-430 DI", ["DI_SifterIso (spare)"])
    c.w(1750, 170, 1750, 220); c.sw_v(1750, 220, "F-306 HKF1 13-14"); c.w(1750, 270, 1750, 330)
    c.box(1680, 330, 140, 50, "750-430 DI", ["DI_SifterTrip (spare)"])
    c.t(1000, 530, "E-stop: SR-P1 removes the DO field supply → KM-306 drops → vibrator coasts down (stop cat. 0).", 13)
    c.t(1000, 550, "Isolator OFF: aux opens first → PLC drops DO_SifterVib before the poles break → no switching under load.", 13)
    c.t(1000, 570, "Assign the two spare DI channels in io_p1.json (P1-225 slot 2) when the panel is built; they only alarm, they do not interlock safety.", 13, col=RED)
    S.table(1000, 640, [("TAG", 110), ("DESCRIPTION", 700), ("PART", 330), ("WHERE", 170), ("QTY", 50)], COMPONENTS, "COMPONENTS", fs=13, rh=22)
    S.notes(1000, 840, 1360, [
        f"Load: 1 x ≈ 2.9 A at 120 V (confirm nameplate); breaker 15 A, cable 14 AWG; voltage drop on 15 m < 1 %.",
        "Disconnect in sight (NEC 430.102(B)): Q-306 on the blender frame leg; LOTO before opening the lid or adjusting the weights.",
        "Single-phase vibrators start on a run capacitor: never reverse at speed; direction does not matter for a vertical-axis gyratory drive.",
        "Flexible cord only between the isolator and the vibrator (the body moves ±0.3 mm and the drum is changed every batch).",
    ], "NOTES", fs=13)
    S.save(DWG / "P1-304-E01_power_control.svg")


def e02():
    S = sheet("P1-304-E02", "ELECTRICAL: WIRE LIST, CABLES, PLC LOGIC", scale="NTS", material="-", finish="ferrules on all fine-strand ends; labels both ends", mass="-")
    S.table(120, 140, [("WIRE / CABLE", 220), ("FROM", 360), ("TO", 420), ("TYPE", 330), ("NOTE", 450)], WIRES, "WIRE LIST", fs=13, rh=24)
    S.table(120, 540, [("CABLE", 140), ("FROM", 200), ("TO", 260), ("SPEC", 420), ("EST. LENGTH", 130)], [
        ("W-306", "MS-P1", "Q-306", "3C 14 AWG TC-ER + G/Y, 600 V", "12 m"),
        ("P1-350", "Q-306", "M-306", "SOOW 14/3 flexible, 600 V, oil/water resistant", "3 m"),
        ("W-306C", "MS-P1", "Q-306 aux", "2C 18 AWG TC-ER shielded", "12 m")], "CABLE SCHEDULE", fs=13, rh=22)
    S.table(120, 700, [("TERMINAL", 120), ("FUNCTION", 300), ("IN", 220), ("OUT", 220)], [
        ("1 / 2", "L in / L out", "W-306 1", "P1-350 L"), ("3 / 4", "N in / N out", "W-306 2", "P1-350 N"),
        ("13 / 14", "early-break NO aux", "W-306C 2", "W-306C 3"), ("PE", "earth", "W-306 G/Y", "P1-350 PE")], "ISOLATOR Q-306 TERMINALS", fs=13, rh=24)
    S.table(1400, 540, [("STEP (MES batch / PLC)", 360), ("CONDITION", 560), ("ACTION", 560)], [
        ("1 Ready", "drum on dolly under the sifter, lid latched, sock clamped (operator check on HMI)", "enable 'discharge' on the HMI"),
        ("2 Start", "DI_SifterIso = 1 and DI_SifterTrip = 1", "DO_SifterVib = 1, wait 3 s (run-up), then DO_BlValveOpen = 1"),
        ("3 Discharge", "valve open; blender agitator at discharge speed", "batch empties ≈ 19 min at 3.6 kg/min"),
        ("4 Run-on", "valve closed (MES: blender empty)", "vibrator runs 60 s more to clear the deck, then DO_SifterVib = 0"),
        ("5 Check", "operator opens the lid (LOTO not needed: vibrator stopped, latch only)", "inspect deck + magnet, log overs and catches (ITP T18/T19)"),
        ("Alarm", "DI_SifterIso = 0 or DI_SifterTrip = 0 while discharging", "close the valve at once (no unsifted product), alarm on the MES"),
    ], "PLC / MES SEQUENCE (blender discharge)", fs=13, rh=26)
    S.notes(1400, 820, 1500, [
        "The valve never opens unless the vibrator has run up: unsifted blend must not reach the drum (the screen is a quality control point, not the CCP).",
        f"Vibrator: {N_VIB:.0f} rpm, weights set to ≈ {C['setting'] * 100:.0f} % of {F_MAX / 1000:.1f} kN for ±{AMP_TARGET} mm; record the setting on the ITP and paint-mark the weights.",
        "Startup / stop pass through the isolator resonance (≈ 11 Hz) in < 1 s: a brief wobble is normal, hard knocking is not (check the band slack and isolator nuts).",
    ], "CONTROL NOTES", fs=13)
    S.save(DWG / "P1-304-E02_lists_logic.svg")
