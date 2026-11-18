"""AON-1 electrical interface definition: harness connectors, every numbered wire, and the stack-bus pin allocation.

Used by drawings/sh_doc.py (AON-E01 schematic, AON-E02 wire list) and bom/make_bom.py. Boards E01-E07 are designed in KiCad from this.
"""
import math

# wire classes: (spec, gauge) M22759/32 ETFE, silver-plated copper
PWR, SIG = ("M22759/32-24", "24 AWG"), ("M22759/32-26", "26 AWG")

FACES = ["+X", "-X", "+Y", "-Y"]
# panel harness exit: panel connectors sit on the panel back at Z = 60 (lower bay); E01 connectors at Z 82, E03 at Z 110
PANEL_Z = 60.0

CONNECTORS = [  # ref, board, part, pins, mates, note
    *[(f"J{101 + i}", f"E06 {f}", "Gecko-SL 2x3 vertical header", 6, f"P{101 + i}", "solar string + panel NTC") for i, f in enumerate(FACES)],
    *[(f"J{111 + i}", f"E06 {f}", "Gecko-SL 2x2 vertical header", 4, f"P{111 + i}", "torquer coil + sun sensor") for i, f in enumerate(FACES)],
    ("J105", "E06A +X", "Gecko-SL 2x5 vertical header (panel back)", 10, "P105", "RBF + umbilical port (front-face Gecko 4-way RBF socket J106 on the same board)"),
    ("J1", "E01", "Gecko-SL 2x3 right-angle", 6, "P1", "+X string"), ("J2", "E01", "Gecko-SL 2x3 right-angle", 6, "P2", "-X string"),
    ("J3", "E01", "Gecko-SL 2x3 right-angle", 6, "P3", "+Y string"), ("J4", "E01", "Gecko-SL 2x3 right-angle", 6, "P4", "-Y string"),
    ("J5", "E01", "Gecko-SL 2x2 right-angle", 4, "P5", "deployment switches SW1, SW2"),
    ("J6", "E01", "Gecko-SL 2x5 right-angle", 10, "P6", "umbilical + RBF from E06A"),
    ("J7", "E01", "Gecko-SL 2x3 right-angle", 6, "P7", "burn rail + element switches to E05"),
    ("J21", "E03", "Gecko-SL 2x2 right-angle", 4, "P21", "+X coil/sun"), ("J22", "E03", "Gecko-SL 2x2 right-angle", 4, "P22", "-X coil/sun"),
    ("J23", "E03", "Gecko-SL 2x2 right-angle", 4, "P23", "+Y coil/sun"), ("J24", "E03", "Gecko-SL 2x2 right-angle", 4, "P24", "-Y coil/sun"),
    ("J25", "E03", "Gecko-SL 2x3 right-angle", 6, "P25", "E07: Z coil, -Z sun, NTC"), ("J71", "E07", "Gecko-SL 2x3 vertical", 6, "P71", "to E03 J25"),
    ("J51", "E05", "Gecko-SL 2x3 vertical", 6, "P51", "burn + element switches from E01 J7"),
    ("J41", "E04", "U.FL (Hirose U.FL-R-SMT-1)", 1, "BP-08", "RF out"), ("J52", "E05", "U.FL", 1, "BP-08", "RF in to the phasing network"),
    ("SW1", "-Z frame", "Omron D2F-01L (BP-03), solder lugs", 2, "P5", "deployment switch in battery +"),
    ("SW2", "-Z frame", "Omron D2F-01L (BP-03), solder lugs", 2, "P5", "deployment switch in battery -"),
]


def _route_len(z_from, z_to, extra=60.0):
    return round(abs(z_to - z_from) + extra, -1)


def wires():
    """every harness wire: (W-no, from ref:pin, to ref:pin, signal, spec, gauge, colour, length mm)."""
    W = []
    n = 1

    def add(a, b, sig, cls, col, L):
        nonlocal n
        W.append((f"W{n:03d}", a, b, sig, cls[0], cls[1], col, L)); n += 1

    for i, f in enumerate(FACES):
        Lp = _route_len(PANEL_Z, 82.0, 90.0 if f in ("+X", "-X") else 110.0)
        for pin, sig, cls, col in ((1, f"SA{f}+", PWR, "red"), (2, f"SA{f}+", PWR, "red"), (3, f"SA{f}-", PWR, "black"), (4, f"SA{f}-", PWR, "black"),
                                   (5, f"NTC{f}", SIG, "white"), (6, f"NTC{f}_RTN", SIG, "white/black")):
            add(f"J{101 + i}:{pin}", f"J{1 + i}:{pin}", sig, cls, col, Lp)
        Ls = _route_len(PANEL_Z, 110.0, 90.0 if f in ("+X", "-X") else 110.0)
        for pin, sig, col in ((1, f"MTQ{f}+", "blue"), (2, f"MTQ{f}-", "blue/white"), (3, f"SUN{f}", "white"), (4, f"SUN{f}_RTN", "white/black")):
            add(f"J{111 + i}:{pin}", f"J{21 + i}:{pin}", sig, SIG, col, Ls)
    for pin, sig, cls, col in ((1, "MTQZ+", SIG, "blue"), (2, "MTQZ-", SIG, "blue/white"), (3, "SUN-Z", SIG, "white"), (4, "SUN-Z_RTN", SIG, "white/black"),
                               (5, "NTC-Z", SIG, "white"), (6, "NTC-Z_RTN", SIG, "white/black")):
        add(f"J71:{pin}", f"J25:{pin}", sig, cls, col, _route_len(5.0, 110.0, 80.0))
    for a, b, sig, col in (("SW1:C", "J5:1", "VBATT_CELL+", "red"), ("SW1:NC", "J5:2", "VBATT_SW+", "red"),
                           ("SW2:C", "J5:3", "VBATT_CELL-", "black"), ("SW2:NC", "J5:4", "VBATT_SW-", "black")):
        add(a, b, sig, PWR, col, _route_len(3.0, 82.0, 70.0))
    for pin, sig, cls, col in ((1, "CHG+", PWR, "red"), (2, "CHG+", PWR, "red"), (3, "CHG-", PWR, "black"), (4, "CHG-", PWR, "black"),
                               (5, "RBF_INH", SIG, "yellow"), (6, "RBF_RTN", SIG, "yellow/black"), (7, "GSE_UART_TX", SIG, "green"),
                               (8, "GSE_UART_RX", SIG, "green/white"), (9, "GND", SIG, "black"), (10, "OBC_NRST", SIG, "violet")):
        add(f"J105:{pin}", f"J6:{pin}", sig, cls, col, _route_len(312.0, 82.0, 60.0))
    for pin, sig, cls, col in ((1, "BURN1", PWR, "orange"), (2, "BURN2", PWR, "orange/white"), (3, "BURN_RTN", PWR, "black"), (4, "BURN_RTN", PWR, "black"),
                               (5, "DEP1_SW", SIG, "white"), (6, "DEP2_SW", SIG, "white/black")):
        add(f"J7:{pin}", f"J51:{pin}", sig, cls, col, _route_len(82.0, 336.0, 70.0))
    W.append((f"W{n:03d}", "J41", "J52", "RF 401.5 MHz", "BP-08 U.FL-2LP-04N1T-A-(150)", "1.13 mm coax", "-", 150.0))
    return W


# stack bus ESQ-126 (2 x 26): pin -> net. Power pins are paralleled (each pin 3 A max; budget ≤ 1 A per pin).
STACK_BUS = [
    ("1-6", "VBATT (protected battery bus, 6.0-8.4 V)"), ("7-12", "GND (power return)"),
    ("13-14", "3V3_OBC (always-on, from E01 buck, 1 A)"), ("15-16", "5V_SW (switched, ADCS + payload, 1.5 A)"),
    ("17-18", "VBATT_COM (switched + current-limited 2 A, to E04)"), ("19", "VBATT_PAY (switched, payload bay)"),
    ("20", "HEATER (E01 switch to the E02 heater)"), ("21", "BURN_EN (OBC → E01 burn-rail enable)"),
    ("22-23", "I2C1 SCL/SDA (EPS + battery telemetry: INA226 x 6, BQ gauge, TMP)"), ("24-25", "I2C2 SCL/SDA (COM housekeeping)"),
    ("26-29", "SPI2 SCK/MISO/MOSI/CS (OBC ↔ COM AX5043)"), ("30", "COM_IRQ"), ("31", "PA_EN (OBC → E04, AND-ed with the E04 45-min timer)"),
    ("32-33", "UART1 TX/RX (GSE umbilical → OBC)"), ("34", "OBC_NRST (GSE / watchdog)"), ("35", "INHIBIT (RBF fitted = low: EPS output off)"),
    ("36", "LOAD_COM_EN"), ("37", "LOAD_ADCS_EN"), ("38", "LOAD_PAY_EN"), ("39", "WDT_KICK"), ("40", "SEP_TIMER_DONE (E01 hardware 30-min timer)"),
    ("41-44", "spare (payload SPI)"), ("45-48", "GND (signal)"), ("49-52", "chassis bond (through the spacer rings, not power GND)"),
]

POWER_BLOCKS = [
    ("String +X / -X", "7S CIC, Vmp 16.9 V, Isc 0.52 A", "ideal-diode OR (LM66100 x 2) → MPPT A"),
    ("String +Y / -Y", "same", "ideal-diode OR → MPPT B"),
    ("MPPT A, B", "TI BQ24650 synchronous buck, 8.4 V charge, MPPT set 80 % Voc (14.9 V)", "→ battery node through SW1 (+) and SW2 (−)"),
    ("Battery E02", "2S2P LG MJ1, 7.0 Ah, 51 Wh; TI BQ7718 2S over-voltage + BQ771807 secondary; NTC, 2 W Kapton heater", "→ VBATT bus"),
    ("Inhibits", "SW1 (V+), SW2 (V−) open while stowed; RBF1 holds the E01 output FET gate low; 30-min hardware timer gates the burn rail", "3 independent inhibits"),
    ("3V3_OBC", "TI TPS62130 buck, always on after the inhibits release", "OBC, FRAM, sensors"),
    ("5V_SW", "TPS62130 buck + TPS2553 limit 1.5 A", "ADCS drivers, payload"),
    ("VBATT_COM", "TPS2553-style eFuse 2 A, OBC enable", "E04 PA + radio"),
    ("BURN", "TPS2553 limit 1.5 A, enabled only by OBC BURN_EN AND the 30-min timer", "E05 R1/R2 via MOSFETs"),
    ("Telemetry", "INA226 on each string, battery and every switched rail; I2C1", "EOR-1 hk"),
]
