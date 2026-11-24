"""CPD-1: TS-2 rev B column power distribution board (one per column, four per tower).

Function
  * Four CRPS 2000 W 12 V supplies (Murata D1U54T-W-2000-12-HC4TC, 3 + 1 redundant) plug straight into four vertical
    PwrBlade receptacles on the F face.  The PSUs OR their 12 V main outputs internally; this board joins them on three
    4 oz +12 V planes (F, In2, In4) and three 4 oz RTN planes (In1, In3, B).
  * Eight M6 press-fit studs per pole (two per PSU) carry the current to two copper straps on the B face
    (TS2B-232 +12 V, TS2B-233 RTN), and from the strap lugs to the column busbars through 2 x 4/0 AWG per pole (harness
    cables C01 / C02, one cable from each end of each strap).
  * One PMBus per PSU (STM32G474 I2C1..I2C4): a PSU that hangs its bus cannot block the other three, and all four use
    the default address.  PRESENT_L, AC_OK, PW_OK, SMB_ALERT per PSU to the MCU; PS_ON per PSU from the MCU through a
    2N7002 (PSU off while the MCU is in reset).  ISHARE bused, monitored.  Remote sense Kelvin-tapped at the stud row.
  * VSB (12 V standby) of each PSU OR-ed by a Schottky onto VSB_BUS: always-on 3.3 V for the MCU and a fused 12 V
    standby feed to the CCM-1 cooling controller (it must run the chiller check before the GPUs get power).
  * Modbus RTU slave on the column RS-485 bus; SYS connector: PSON_REQ# in (from CCM-1: low = cooling ready, power on)
    and COL_PWR_OK out (open drain, to the host and CCM-1).

Board: 250.0 x 95.0 mm, 6 layers 4 oz, 2.4 mm.  Coordinates: board-local, lower-left origin seen from the F face
(facing the PSUs).  x = y_world + 125, y = z - (Z_PLINTH0 + 20).  PSU k centre x = 41 + 58 k, PSU body y 21..61.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kgen'))
from core import Design   # noqa: E402
import blocks   # noqa: E402
from pcb import stackup_text   # noqa: E402

D = Design('cpd1', 'TS-2 rev B CPD-1 column power distribution', 'A', w=250.0, h=95.0, layers=6, thickness=2.4, corner_r=3.0)
SPN = '[verify]'
NP = 4


def pcx(k):
    return 41.0 + 58.0 * k          # PSU k (0..3) centre, board x


CONN_OFF = 2.25                      # footprint origin -> body centre
Y_CONN = 41.0                        # PSU card-edge centre
Y_P12 = 65.0                         # +12 V stud row (strap TS2B-232, y 59..71)
Y_RTN = 81.0                         # RTN stud row (strap TS2B-233, y 75..87)

# ===================================================================== per-PSU circuit
I2C = [('PA15', 'PB7'), ('PA9', 'PA8'), ('PC8', 'PC9'), ('PC6', 'PC7')]      # (SCL, SDA): I2C1..I2C4
PORTS = {}
for k in range(NP):
    n = k + 1
    D.sheet('PSU %d' % n, notes=[
        'PSU %d: CRPS 2000 W 12 V (166.7 A main, 12 V standby).  Main output OR-ed inside the PSU.' % n,
        'PMBus on its own MCU I2C (I2C%d), 100 kHz, 2.2k pull-ups to +3V3; PSU address strap left open (default 0x58 [verify]).' % n,
        'PS_ON low = on: 2N7002 with 100k gate pull-down, so the PSU stays off while the MCU is in reset.',
        'Remote sense: V1_SENSE+ / V1_SENSE_R joined to +12V / RTN by 0 ohm links at the stud row (Kelvin tap).',
        'VSB OR-ing: PMEG4050EP 40 V 5 A Schottky onto VSB_BUS.'])
    pre, acok, pwok, alert, pson = 'P%d_PRESENT#' % n, 'P%d_ACOK' % n, 'P%d_PWOK' % n, 'P%d_ALERT#' % n, 'P%d_PSON#' % n
    scl, sda, vsb = 'P%d_SCL' % n, 'P%d_SDA' % n, 'P%d_VSB' % n
    pm = {'A1': pre, 'B1': vsb, 'C1': acok, 'D1': 'ISHARE', 'A2': 'P%d_SNSR' % n, 'B2': 'P%d_SNSP' % n, 'C2': pwok,
          'D2': 'P%d_ADDR' % n, 'A3': sda, 'B3': scl, 'C3': pson, 'D3': alert,
          'P1': 'GND', 'P2': 'GND', 'P3': 'GND', 'P4': '+12V', 'P5': '+12V', 'P6': '+12V', 'MP1': 'GND', 'MP2': 'GND'}
    D.P('J%d' % n, 'ts2b:CRPS_Output_18P', 'CRPS PwrBlade', 'ts2b:Amphenol_CRPS_PwrBlade_Vertical_PressFit',
        '10106264-6003003LF ' + SPN, 'Amphenol (FCI)', SPN, pm,
        'CRPS PSU mating receptacle, PwrBlade 6 power + 12 signal, vertical press-fit [verify variant vs board orientation]',
        price=14.0)
    D.place['J%d' % n] = (pcx(k) - CONN_OFF, Y_CONN, 0, 'F')
    r = 100 * n
    D.R('R%d' % (r + 1), '10k', pre, '+3V3', 'PRESENT_L pull-up', side='B')
    D.R('R%d' % (r + 2), '10k', acok, '+3V3', 'AC_OK pull-up', side='B')
    D.R('R%d' % (r + 3), '10k', pwok, '+3V3', 'PW_OK pull-up', side='B')
    D.R('R%d' % (r + 4), '10k', alert, '+3V3', 'SMB_ALERT# pull-up', side='B')
    D.R('R%d' % (r + 5), '2.2k', scl, '+3V3', 'PMBus SCL pull-up', side='B')
    D.R('R%d' % (r + 6), '2.2k', sda, '+3V3', 'PMBus SDA pull-up', side='B')
    D.R('R%d' % (r + 7), '0', 'P%d_ADDR' % n, 'GND', 'PMBus address strap - DNP (open = default address)', side='B', dnp=True)
    blocks.nfet_od(D, 'Q%d' % n, 'R%d' % (r + 8), 'P%d_PSON_MCU' % n, pson, 'PS_ON# driver')
    D.byref['Q%d' % n]['side'] = 'B'
    D.byref['R%d' % (r + 8)]['side'] = 'B'
    D.R('R%d' % (r + 9), '0', 'P%d_SNSP' % n, '+12V', 'Remote sense + Kelvin link at the +12V stud', side='B')
    D.P('JP%d' % n, 'Device:R', '0', 'Resistor_SMD:R_0603_1608Metric', '0603WAF0000T5E', 'UNI-ROYAL',
        '', {'1': 'P%d_SNSR' % n, '2': 'GND'}, 'Remote sense return Kelvin link at the RTN stud', side='B', lcsc='C21189')
    D.P('D%d' % n, 'Device:D_Schottky', 'PMEG4050EP', 'Diode_SMD:D_SOD-128', 'PMEG4050EP,115', 'Nexperia',
        '1727-4993-1-ND ' + SPN, {'1': 'VSB_BUS', '2': vsb}, 'Schottky 40 V 5 A SOD-128, VSB OR-ing', side='B', price=0.35)
    D.C('C%d' % (r + 1), '1u', vsb, 'GND', 'VSB local', side='B')
    D.C('C%d' % (r + 2), '22u25', '+12V', 'GND', '+12V HF decoupling at the blades', side='B')
    D.C('C%d' % (r + 3), '22u25', '+12V', 'GND', '+12V HF decoupling at the blades', side='B')
    PORTS[I2C[k][0]] = scl
    PORTS[I2C[k][1]] = sda
    x0 = pcx(k)
    D.regions.append(((x0 - 27.0, 47.5, x0 + 27.0, 57.5), ['R%d' % (r + j) for j in (1, 2, 3, 4, 5, 6, 7, 8)] +
                      ['Q%d' % n, 'D%d' % n, 'C%d' % (r + 1), 'C%d' % (r + 2), 'C%d' % (r + 3)], 'B'))
    D.place['R%d' % (r + 9)] = (x0, (Y_P12 + Y_RTN) / 2, 0, 'B')   # in the 4 mm gap between the two straps (y 71..75)
    D.place['JP%d' % n] = (x0, Y_RTN + 9.5, 90, 'B')        # clear of the strap (y 75..87)

# per-PSU status lines -> MCU
for k, (p, a, w, al, ps) in enumerate(zip(('PB0', 'PB1', 'PB2', 'PB10'), ('PB11', 'PB12', 'PB13', 'PB14'),
                                          ('PC2', 'PC3', 'PC4', 'PC5'), ('PB15', 'PA10', 'PA11', 'PA12'),
                                          ('PC10', 'PC11', 'PC12', 'PD2'))):
    n = k + 1
    PORTS.update({p: 'P%d_PRESENT#' % n, a: 'P%d_ACOK' % n, w: 'P%d_PWOK' % n, al: 'P%d_ALERT#' % n, ps: 'P%d_PSON_MCU' % n})

# ===================================================================== bus, standby, management
D.sheet('Bus and management', notes=[
    '+12V / RTN: 3 + 3 planes of 4 oz.  Per PSU 166 A over ~25 mm of 3 x 4 oz, ~40 mm wide: ~26 uOhm, ~0.7 W per pole at full load.',
    'Studs: 8 x M6 per pole, PEM FHS-M6 class; straps TS2B-232 / TS2B-233 (C11000 12 x 6 mm, tin plated, upturned 2-hole M8 lug legs at both ends) 6 N m.',
    'VSB_BUS (12 V standby): always-on 3.3 V buck for the MCU, and a 2.5 A PTC feed to the CCM-1 (SYS connector J7 pins 1/2).',
    'MCU: I2C1-4 = PSU 1-4 PMBus; USART2 PA2 TX / PA3 RX / PA1 DE (RS-485); ADC PA0 ISHARE, PA4 +12V bus, PA5 VSB_BUS,',
    'PC0/PC1 NTC (strap + inlet air); PB5 PSON_REQ# in; PB4 COL_PWR_OK out; ADDR PB6/PB9; LEDs PC13 OK, PF1 fault.',
    'Policy (firmware): PSUs stay off until CCM-1 pulls PSON_REQ# low (cooling ready).  Then PS_ON for all present PSUs with',
    'AC_OK; COL_PWR_OK when >= 3 report PW_OK.  A PSU with an ALERT is polled (STATUS_WORD) and reported over Modbus.'])
for t, net, x, y in [('T%d' % (1 + 2 * k + j), '+12V', pcx(k) + (-13.0 if j == 0 else 13.0), Y_P12)
                     for k in range(NP) for j in range(2)] + \
                    [('T%d' % (9 + 2 * k + j), 'GND', pcx(k) + (-13.0 if j == 0 else 13.0), Y_RTN)
                     for k in range(NP) for j in range(2)]:
    D.P(t, 'ts2b:Power_Terminal', 'M6 stud', 'ts2b:Power_Stud_M6_PressFit', 'FHS-M6-20ZI ' + SPN, 'PennEngineering', SPN,
        {'1': net}, 'M6 x 20 press-fit stud to the %s strap (B face), 12 mm pad all layers' %
        ('+12 V' if net == '+12V' else 'RTN'), side='B', price=0.9)
    D.place[t] = (x, y, 0, 'B')
for d in ('D5', 'D6'):
    D.P(d, 'Device:D_TVS', 'SMBJ15CA', 'Diode_SMD:D_SMB', 'SMBJ15CA', 'Littelfuse', 'SMBJ15CALFCT-ND ' + SPN,
        {'1': '+12V', '2': 'GND'}, 'TVS 15 V standoff 600 W bidirectional, +12V bus', side='B', price=0.3)
# bus monitors
D.R('R1', '100k', 'ISHARE', 'ISH_MON', 'ISHARE divider top (8 V full scale -> 1.99 V)', side='B')
D.R('R2', '33k', 'ISH_MON', 'GND', 'ISHARE divider bottom', side='B')
D.C('C1', '100n', 'ISH_MON', 'GND', side='B')
D.R('R3', '100k', '+12V', 'V12_MON', '+12V monitor top (12 V -> 2.16 V)', side='B')
D.R('R4', '22k', 'V12_MON', 'GND', side='B')
D.C('C2', '100n', 'V12_MON', 'GND', side='B')
D.R('R5', '100k', 'VSB_BUS', 'VSB_MON', 'VSB monitor top', side='B')
D.R('R6', '22k', 'VSB_MON', 'GND', side='B')
D.C('C3', '100n', 'VSB_MON', 'GND', side='B')
D.C('C4', '10u50', 'VSB_BUS', 'GND', side='B')
PORTS.update({'PA0': 'ISH_MON', 'PA4': 'V12_MON', 'PA5': 'VSB_MON'})
# always-on 3.3 V from VSB
B33 = blocks.buck(D, 'U2', 'L1', 'C5', 'C6', ('C7', 'C8'), 'R7', 'R8', 'VSB_BUS', '+3V3', 'SB_SW', 'SB_FB', 'SB_BST',
                  note='Always-on 3.3 V buck from VSB_BUS', side='B')
# MCU
MCU = blocks.mcu(D, 'U1', dict(PORTS, PA2='RS485_TX', PA3='RS485_RX', PA1='RS485_DE', PC0='NTC1', PC1='NTC2',
                                PB5='PSON_REQ#', PB4='PWROK_MCU', PB6='ADDR0', PB9='ADDR1', PC13='LED_OK', PF1='LED_FLT'),
                 caps=('C', 61), fb='FB1')
for r in MCU:
    D.byref[r]['side'] = 'B'
SWD = blocks.boot_swd(D, 'R9', 'J5')
RS = blocks.rs485(D, 'U3', 'C50', 'D7', 'R10', 'JP5', ('J6', 'J8'), 'RS485_TX', 'RS485_RX', 'RS485_DE',
                  conn_pins={'1': 'BUS_A', '2': 'BUS_B', '3': 'GND', '4': 'ADDR0', '5': 'ADDR1', '6': 'GND'},
                  desc='Column RS-485 bus in/out: 1 A, 2 B, 3 GND, 4 ADDR0, 5 ADDR1, 6 GND (mating 43025-0600)')
D.R('R11', '10k', 'ADDR0', '+3V3', 'ADDR0 pull-up', side='B')
D.R('R12', '10k', 'ADDR1', '+3V3', 'ADDR1 pull-up', side='B')
# SYS connector: VSB feed to CCM-1, PSON_REQ# in, COL_PWR_OK out
D.P('F1', 'Device:Polyfuse', '2.5A', 'Fuse:Fuse_1812_4532Metric', 'MF-MSMF250/16X-2', 'Bourns', 'MF-MSMF250/16X-2CT-ND ' + SPN,
    {'1': 'VSB_BUS', '2': 'VSB_OUT'}, 'PTC 2.5 A hold 16 V 1812, standby feed to CCM-1', side='B', price=0.4)
D.P('J7', 'Connector_Generic:Conn_02x03_Odd_Even', 'Micro-Fit 2x3', 'Connector_Molex:Molex_Micro-Fit_3.0_43045-0612_2x03_P3.00mm_Vertical',
    '43045-0612', 'Molex', 'WM1784-ND ' + SPN, {'1': 'VSB_OUT', '2': 'VSB_OUT', '3': 'PSON_REQ#', '4': 'GND', '5': 'GND',
                                                 '6': 'COL_PWR_OK'},
    'SYS: 1/2 VSB 12 V out (2.5 A), 3 PSON_REQ# in, 4/5 GND, 6 COL_PWR_OK out (open drain)', side='B', price=1.3)
D.R('R13', '10k', 'PSON_REQ#', '+3V3', 'PSON_REQ# pull-up (open = stay off)', side='B')
blocks.nfet_od(D, 'Q5', 'R14', 'PWROK_MCU', 'COL_PWR_OK', 'COL_PWR_OK open-drain output')
D.byref['Q5']['side'] = 'B'
D.byref['R14']['side'] = 'B'
NT = blocks.ntc(D, 'J9', 'R15', 'C52', 'NTC1', 'TS2B-232 strap (stud 4)') + blocks.ntc(D, 'J10', 'R16', 'C53', 'NTC2', 'arm inlet air')
LED = blocks.led(D, 'D8', 'R17', 'LED_OK', 'GREEN') + blocks.led(D, 'D9', 'R18', 'LED_FLT', 'RED')
for r in SWD + RS + NT + LED + ['R11', 'R12', 'R13', 'F1', 'J7']:
    D.byref[r]['side'] = 'B'
for tp, net in (('TP1', '+12V'), ('TP2', '+3V3'), ('TP3', 'GND'), ('TP4', 'VSB_BUS'), ('TP5', 'ISHARE'), ('TP6', 'BUS_A'),
                ('TP7', 'BUS_B')):
    D.TP(tp, net, side='B')
k = 1
for x in (6.0, 125.0, 244.0):
    for y in (6.0, 91.0):
        D.HOLE('H%d' % k, x, y)
        k += 1

D.notes = ['TS-2 rev B CPD-1 column power distribution.  One per column; the column and node address come from the ADDR straps.',
           'Generated by kgen from boards/cpd1/design.py.  [verify] marks supplier numbers / land patterns not yet checked against',
           'the vendor drawing (docs/part-verification.md).  Engineering review required before release.']

# ===================================================================== net classes
D.signal_width = 0.2
D.signal_clearance = 0.2
D.netclasses = {
    'PWR12': dict(nets=['+12V', 'VSB_BUS', 'VSB_OUT'] + ['P%d_VSB' % n for n in range(1, 5)], width=1.0, clearance=0.3),
    'PWR3V3': dict(nets=['+3V3', 'SB_SW'], width=0.3, clearance=0.2),
}

# ===================================================================== placement (B face management strip y 2..34)
D.place['U1'] = (125.0, 18.0, 0, 'B')
D.place['U2'] = (64.0, 12.0, 0, 'B')
D.place['L1'] = (74.0, 12.0, 0, 'B')
D.place['U3'] = (168.0, 12.0, 0, 'B')
D.place['J6'] = (196.0, 10.0, 0, 'B')
D.place['J8'] = (214.0, 10.0, 0, 'B')
D.place['J7'] = (232.0, 24.0, 0, 'B')
D.place['F1'] = (232.0, 12.0, 0, 'B')
D.place['J5'] = (146.0, 28.0, 0, 'B')
D.place['J9'] = (20.0, 12.0, 0, 'B')
D.place['J10'] = (32.0, 12.0, 0, 'B')
D.regions += [
    ((106.0, 2.5, 154.0, 7.5), ['C61', 'C62', 'C63', 'C64', 'C65', 'C66', 'FB1', 'C67', 'C68', 'C69', 'R9'], 'B'),
    ((106.0, 28.0, 140.0, 34.0), ['D8', 'R17', 'D9', 'R18', 'TP2', 'TP3', 'TP1'], 'B'),
    ((54.0, 18.5, 84.0, 33.0), ['C5', 'C6', 'C7', 'C8', 'R7', 'R8', 'C4', 'TP4', 'D5', 'D6'], 'B'),
    ((158.0, 18.5, 186.0, 33.0), ['C50', 'D7', 'R10', 'JP5', 'R11', 'R12', 'TP6', 'TP7'], 'B'),
    ((88.0, 2.5, 104.0, 33.0), ['R1', 'R2', 'C1', 'R3', 'R4', 'C2', 'R5', 'R6', 'C3', 'TP5'], 'B'),
    ((200.0, 18.5, 226.0, 33.0), ['R13', 'Q5', 'R14'], 'B'),
    ((14.0, 18.5, 50.0, 33.0), ['R15', 'C52', 'R16', 'C53'], 'B'),
]

# ===================================================================== pours
W, H = D.W, D.H
e = 0.5
D.pours = [
    dict(net='GND', layer='In1', rect=(e, e, W - e, H - e), thermal=False),
    dict(net='GND', layer='In3', rect=(e, e, W - e, H - e), thermal=False),
    dict(net='GND', layer='B', rect=(e, e, W - e, H - e), prio=0, thermal=False),
    dict(net='GND', layer='F', rect=(e, e, W - e, 19.0), prio=0, thermal=False),
    dict(net='+12V', layer='F', rect=(e, 19.5, W - e, H - e), prio=1, thermal=False),
    dict(net='+12V', layer='In2', rect=(e, 36.0, W - e, H - e), prio=1, thermal=False),
    dict(net='+12V', layer='In4', rect=(e, 36.0, W - e, H - e), prio=1, thermal=False),
]
D.fanout = True
D.fanout_inward = ('U1.47',)       # MCU GND pin: via under the QFP body; an outside via would box in U1.46 (P4_ALERT#)
D.power_layers = ('In1', 'In3')
D.stitch = dict(net='GND', pitch=5.0, layers=['F', 'In1', 'In3', 'B'])
D.no_stitch = tuple('J%d' % n for n in range(1, 5))

D.silk = [dict(t='TS-2 rev B  CPD-1 column power  rev A', x=125.0, y=36.0, l='B', size=1.6),
          dict(t='machine-generated - review before release', x=125.0, y=1.6, l='B', size=1.0)]
for k in range(NP):
    D.silk.append(dict(t='PSU %d' % (k + 1), x=pcx(k), y=64.0, l='F', size=2.5))
    D.silk.append(dict(t='+12V', x=pcx(k), y=Y_P12 + 7.5, l='B', size=1.5))
    D.silk.append(dict(t='RTN', x=pcx(k), y=Y_RTN + 7.5, l='B', size=1.5))

# ===================================================================== stackup and fab
D.stackup = stackup_text([
    ('cu', 'F.Cu', 0.14), ('prepreg', 0.2, 'FR4 IT-180A', 4.3, 0.015),
    ('cu', 'In1.Cu', 0.14), ('core', 0.4, 'FR4 IT-180A', 4.3, 0.015),
    ('cu', 'In2.Cu', 0.14), ('prepreg', 0.3, 'FR4 IT-180A', 4.3, 0.015),
    ('cu', 'In3.Cu', 0.14), ('core', 0.4, 'FR4 IT-180A', 4.3, 0.015),
    ('cu', 'In4.Cu', 0.14), ('prepreg', 0.2, 'FR4 IT-180A', 4.3, 0.015),
    ('cu', 'B.Cu', 0.14)], finish='ENIG', mask='Green')
D.fab = dict(
    rules={"min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.6, "min_through_hole_diameter": 0.3,
           "min_via_annular_width": 0.15, "min_copper_edge_clearance": 0.5, "min_hole_clearance": 0.3, "min_hole_to_hole": 0.3},
    layers=6, thickness='2.4 mm +/-10 % (press-fit: confirm the PwrBlade and stud hole tolerance)',
    material='High-Tg FR-4 (ITEQ IT-180A or equal), Tg >= 170 C', copper='4 oz finished all six layers (heavy copper)',
    finish='ENIG', mask='green LPI both sides', silk='white both sides', impedance='none controlled',
    min_track='0.20 mm / 0.20 mm (8/8 mil, heavy copper)', min_drill='0.30 mm',
    vias='through only, 0.3 / 0.6 mm', size='250.0 x 95.0 mm', panel='1 up',
    press_fit='CRPS receptacles and M6 studs are press-fit: finished hole sizes per the vendor drawing, +/-0.05 mm',
    ipc='IPC-6012 class 2, IPC-A-600 class 2', test='100 % netlist (flying probe)')
D.test_notes = [
    'Visual + AOI on the B face.  Press the four PwrBlade receptacles and 16 studs with a flat-rock tool after reflow.',
    'Stud pull-out / torque check on the first article (6 N m on M6, no rotation).',
    'Apply 12 V 2 A to one VSB pin (PSU 1 slot): +3V3 = 3.30 V +/-2 %; heartbeat LED blinks; VSB_OUT live through F1.',
    'With one CRPS fitted: PRESENT, AC_OK reported over Modbus; PMBus READ_VOUT / READ_IOUT on each of the four buses.',
    'PSON_REQ# low -> PS_ON asserted for every present PSU; COL_PWR_OK goes low-impedance when >= 3 PW_OK.',
    'Load test 4 PSUs (3 + 1) into the column busbars at 450 A for 30 min: strap NTC < 70 C, stud rise < 30 K (IR camera).',
    'Pull one PSU under 450 A load: bus droop < 0.3 V, no COL_PWR_OK drop (3 remain).',
]
