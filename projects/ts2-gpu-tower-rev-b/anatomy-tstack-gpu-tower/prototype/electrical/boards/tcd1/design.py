"""TCD-1: TS-2 rev B Peltier (TEC) driver, one per column, inside the base thermal module TS2B-601.

  * Four independent synchronous buck channels, 12 V in, 0-11.5 V / 0-14 A out, one per TEC (TE Technology class
    62 x 62 mm, Imax 21 A, run at ~ 55 % Imax).  DC drive, no PWM into the TEC (ripple costs TEC COP): LC output,
    ~ 2 A p-p inductor ripple at 200 kHz, < 1 % voltage ripple on the module.
  * Per channel: LM5109B half-bridge driver, CSD17578Q5A high side + CSD17556Q5B low side, IHLP-5050 6.8 uH,
    2 mOhm low-side shunt in the TEC return + INA181A2 (0.1 V/A), output voltage divider, 100k pull-downs on HI / LI.
  * STM32G474 HRTIM timers A-D (PA8/PA9, PA10/PA11, PB12/PB13, PB14/PB15) generate the complementary drive with
    dead time; current loop in firmware, set point (W or A) from CCM-1 over the column RS-485 bus.
  * Two hot-side heat-pipe tower fans (4-pin PWM 120 mm), two hot-side NTCs.  Thermal cut-out: firmware at 70 C,
    and the HRTIM is held off whenever the MCU is in reset (gate pull-downs).
  * Power: 12 V ~ 50 A from the module's RSP-750-12 on two M5 stud pairs.

Board: 150.0 x 110.0 mm, 4 layers 2 oz, 1.6 mm.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kgen'))
from core import Design, R2512   # noqa: E402
import blocks   # noqa: E402
from pcb import stackup_text   # noqa: E402

D = Design('tcd1', 'TS-2 rev B TCD-1 Peltier driver', 'A', w=150.0, h=110.0, layers=4, thickness=1.6, corner_r=3.0)
SPN = '[verify]'
NCH = 4
HR = [('PA8', 'PA9'), ('PA10', 'PA11'), ('PB12', 'PB13'), ('PB14', 'PB15')]   # HRTIM TA1/TA2 .. TD1/TD2 (HI, LI)
IMON = ['PA0', 'PA1', 'PA6', 'PA7']
VMON = ['PC0', 'PC1', 'PC2', 'PC3']
PORTS = {}


def chx(k):
    return 22.0 + 35.0 * k       # channel column centre, board x


for k in range(NCH):
    n = k + 1
    c = 'T%d_' % n
    D.sheet('TEC channel %d' % n, notes=[
        'Channel %d: synchronous buck 12 V -> 0-11.5 V, 14 A continuous into TEC %d.  HRTIM timer %s, 200 kHz, dead time 50 ns.'
        % (n, n, 'ABCD'[k]),
        'Shunt 2 mOhm in the TEC return; INA181A2 gain 50 -> 0.1 V/A (14 A = 1.4 V).  VOUT divider 100k / 22k -> 0.18 V/V.',
        'LM5109B VDD from 12V_IN (8-14 V); bootstrap MBR0540 + 220 nF.'])
    D.P('U%d1' % (10 * n), 'Driver_FET:LM5109BMA', 'LM5109B', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'LM5109BMAX/NOPB',
        'Texas Instruments', 'LM5109BMAX/NOPBCT-ND ' + SPN,
        {'1': '12V_IN', '2': c + 'HI', '3': c + 'LI', '4': 'GND', '5': c + 'LO', '6': c + 'SW', '7': c + 'HO', '8': c + 'HB'},
        'Half-bridge gate driver 100 V 1 A, independent HI / LI inputs', price=1.3)
    D.P('Q%d1' % (10 * n), 'Transistor_FET:CSD17578Q5A', 'CSD17578Q5A', 'Package_TO_SOT_SMD:TDSON-8-1', 'CSD17578Q5A',
        'Texas Instruments', '296-37934-1-ND ' + SPN, {'1': c + 'SW', '2': c + 'SW', '3': c + 'SW', '4': c + 'GH', '5': '12V_IN'},
        'N-MOSFET 30 V SON 5x6, high side (low Qg)', price=0.6)
    D.P('Q%d2' % (10 * n), 'Transistor_FET:CSD17556Q5B', 'CSD17556Q5B', 'Package_TO_SOT_SMD:TDSON-8-1', 'CSD17556Q5B',
        'Texas Instruments', '296-37919-1-ND ' + SPN, {'1': 'GND', '2': 'GND', '3': 'GND', '4': c + 'GL', '5': c + 'SW'},
        'N-MOSFET 30 V 1.4 mOhm SON 5x6, low side (synchronous rectifier)', price=1.4)
    D.R('R%d1' % (10 * n), '10', c + 'HO', c + 'GH', 'high-side gate 10 ohm')
    D.R('R%d2' % (10 * n), '10', c + 'LO', c + 'GL', 'low-side gate 10 ohm')
    D.R('R%d3' % (10 * n), '100k', c + 'HI', 'GND', 'HI pull-down (off in reset)')
    D.R('R%d4' % (10 * n), '100k', c + 'LI', 'GND', 'LI pull-down (off in reset)')
    D.P('D%d1' % (10 * n), 'Device:D_Schottky', 'MBR0540', 'Diode_SMD:D_SOD-123', 'MBR0540T1G', 'onsemi', 'MBR0540T1GOSCT-ND',
        {'1': c + 'HB', '2': '12V_IN'}, 'Bootstrap Schottky 40 V 0.5 A', price=0.1)
    D.C('C%d1' % (10 * n), '220n', c + 'HB', c + 'SW', 'bootstrap 220 nF')
    D.C('C%d2' % (10 * n), '1u', '12V_IN', 'GND', 'driver VDD')
    D.C('C%d3' % (10 * n), '22u25', '12V_IN', 'GND', 'half-bridge input')
    D.C('C%d4' % (10 * n), '22u25', '12V_IN', 'GND', 'half-bridge input')
    D.C('C%d5' % (10 * n), '100n', '12V_IN', 'GND', 'half-bridge HF loop')
    D.P('L%d1' % (10 * n), 'Device:L', '6.8u', 'Inductor_SMD:L_Vishay_IHLP-5050', 'IHLP5050FDER6R8M01', 'Vishay Dale',
        '541-1242-1-ND ' + SPN, {'1': c + 'SW', '2': c + 'OUT'}, 'Power inductor 6.8 uH ~ 20 A sat, 12.9 x 12.9 mm', price=2.2)
    for j in (6, 7, 8, 9):
        D.C('C%d%d' % (10 * n, j), '22u25', c + 'OUT', 'GND', 'output filter')
    D.P('R%d5' % (10 * n), 'Device:R', '2m', R2512, 'WSL2512R0020FEA', 'Vishay Dale', 'WSL2512.002FCT-ND ' + SPN,
        {'1': c + 'RET', '2': 'GND'}, 'Shunt 2 mOhm 1 % 2512 1 W (TEC return)', price=0.7)
    D.P('U%d2' % (10 * n), 'Amplifier_Current:INA181', 'INA181A2', 'Package_TO_SOT_SMD:SOT-23-6', 'INA181A2IDBVR', 'Texas Instruments',
        '296-49601-1-ND ' + SPN, {'1': c + 'IA', '2': 'GND', '3': c + 'RET', '4': 'GND', '5': 'GND', '6': '+3V3'},
        'Current-sense amplifier gain 50 (0.1 V/A)', price=0.9)
    D.C('C%d10' % (10 * n), '100n', '+3V3', 'GND')
    D.R('R%d6' % (10 * n), '1k', c + 'IA', c + 'IMON', 'ADC RC')
    D.C('C%d11' % (10 * n), '10n', c + 'IMON', 'GND')
    D.R('R%d7' % (10 * n), '100k', c + 'OUT', c + 'VMON', 'VOUT divider top')
    D.R('R%d8' % (10 * n), '22k', c + 'VMON', 'GND', 'VOUT divider bottom')
    D.C('C%d12' % (10 * n), '10n', c + 'VMON', 'GND')
    D.P('J%d' % n, 'Connector_Generic:Conn_02x02_Odd_Even', 'Micro-Fit 2x2',
        'Connector_Molex:Molex_Micro-Fit_3.0_43045-0412_2x02_P3.00mm_Vertical', '43045-0412', 'Molex', SPN,
        {'1': c + 'OUT', '2': c + 'OUT', '3': c + 'RET', '4': c + 'RET'},
        'TEC %d: 1/2 TEC+ (red), 3/4 TEC- (black), 18 AWG, 2 pins per pole (14 A) (mating 43025-0400)' % n, price=1.0)
    PORTS.update({HR[k][0]: c + 'HI', HR[k][1]: c + 'LI', IMON[k]: c + 'IMON', VMON[k]: c + 'VMON'})
    x = chx(k)
    D.place['J%d' % n] = (x, 7.5, 0, 'F')
    D.place['L%d1' % (10 * n)] = (x + 1.5, 26.0, 270, 'F')   # pad 1 (SW) up
    D.place['Q%d1' % (10 * n)] = (x - 7.0, 44.0, 90, 'F')       # high side: drain tab up to the 12V strip
    D.place['Q%d2' % (10 * n)] = (x + 7.0, 44.0, 270, 'F')      # low side: drain tab down to the switch node
    D.place['U%d1' % (10 * n)] = (x, 58.0, 0, 'F')
    D.place['R%d5' % (10 * n)] = (x + 10.0, 14.0, 90, 'F')
    D.regions.append(((x - 16.5, 9.0, x - 6.0, 23.5), ['C%d6' % (10 * n), 'C%d7' % (10 * n), 'C%d8' % (10 * n),
                                                        'C%d9' % (10 * n)], 'F'))
    D.regions.append(((x - 16.5, 48.0, x + 16.5, 52.0), ['C%d3' % (10 * n), 'C%d5' % (10 * n), 'C%d4' % (10 * n)], 'F'))
    D.regions.append(((x + 5.0, 53.0, x + 16.5, 64.0), ['D%d1' % (10 * n), 'C%d1' % (10 * n), 'C%d2' % (10 * n),
                                                        'R%d1' % (10 * n), 'R%d2' % (10 * n)], 'F'))
    D.regions.append(((x - 16.5, 53.0, x - 5.0, 64.0), ['R%d3' % (10 * n), 'R%d4' % (10 * n)], 'F'))
    D.regions.append(((x - 16.5, 64.5, x + 16.5, 70.5), ['U%d2' % (10 * n), 'C%d10' % (10 * n), 'R%d6' % (10 * n),
                                                         'C%d11' % (10 * n), 'R%d7' % (10 * n), 'R%d8' % (10 * n),
                                                         'C%d12' % (10 * n)], 'F'))

# ===================================================================== power, MCU, fans, bus
D.sheet('Power, MCU, fans, bus', notes=[
    '12V_IN: two M5 studs per pole from the RSP-750-12 (8 AWG pair).  Bulk 2 x 470 uF hybrid + per-channel MLCC.',
    'MCU: HRTIM TA-TD -> channels 1-4; ADC IMON PA0 PA1 PA6 PA7, VMON PC0-PC3, NTC PB0 PB1, 12V_IN PB2.',
    'Fans: PWM PB6 / PB7 (TIM4, 25 kHz, open drain), tach PB4 / PB5 (TIM3).  RS-485 USART2 PA2 / PA3, DE PD2 (GPIO).',
    'ADDR PC4 / PC5 from the column bus plug.  LEDs PC13 OK, PF1 fault.'])
for t, net, x, y in (('T1', '12V_IN', 6.5, 96.0), ('T2', '12V_IN', 6.5, 84.0), ('T3', 'GND', 18.5, 96.0), ('T4', 'GND', 18.5, 84.0)):
    D.P(t, 'ts2b:Power_Terminal', 'M5 stud', 'ts2b:Power_Stud_M5_PressFit', 'FHS-M5-15ZI ' + SPN, 'PennEngineering', SPN,
        {'1': net}, 'M5 press-fit stud, %s from the RSP-750-12 (ring lug, 3 N m)' % ('+12 V' if net != 'GND' else 'return'),
        price=0.7)
    D.place[t] = (x, y, 0, 'F')
for c in ('C1', 'C2'):
    D.P(c, 'Device:C_Polarized', '470u', 'Capacitor_SMD:CP_Elec_10x10', 'EEH-ZA1E471P', 'Panasonic', 'PCE5003CT-ND ' + SPN,
        {'1': '12V_IN', '2': 'GND'}, 'Hybrid polymer 470 uF 25 V 10 x 10.2 mm, 2.8 A ripple', price=1.6)
D.P('D1', 'Device:D_TVS', 'SMBJ15CA', 'Diode_SMD:D_SMB', 'SMBJ15CA', 'Littelfuse', 'SMBJ15CALFCT-ND ' + SPN,
    {'1': '12V_IN', '2': 'GND'}, 'TVS 15 V 600 W', price=0.3)
D.place['C1'] = (32.0, 96.0, 0, 'F')
D.place['C2'] = (32.0, 84.0, 0, 'F')
PWR = blocks.buck(D, 'U1', 'L1', 'C3', 'C4', ('C5', 'C6'), 'R1', 'R2', '12V_IN', '+3V3', 'B3_SW', 'B3_FB', 'B3_BST')
D.R('R3', '100k', '12V_IN', 'V12_MON')
D.R('R4', '22k', 'V12_MON', 'GND')
D.C('C7', '100n', 'V12_MON', 'GND')
PORTS.update({'PB2': 'V12_MON', 'PB0': 'NTC1', 'PB1': 'NTC2', 'PB6': 'FAN1_PWM_MCU', 'PB7': 'FAN2_PWM_MCU',
              'PB4': 'FAN1_TACH', 'PB5': 'FAN2_TACH', 'PA2': 'RS485_TX', 'PA3': 'RS485_RX', 'PD2': 'RS485_DE',
              'PC4': 'ADDR0', 'PC5': 'ADDR1', 'PC13': 'LED_OK', 'PF1': 'LED_FLT'})
MCU = blocks.mcu(D, 'U5', PORTS, caps=('C', 50), fb='FB1') + blocks.boot_swd(D, 'R5', 'J10')
RS = blocks.rs485(D, 'U6', 'C60', 'D2', 'R6', 'JP1', ('J5', 'J6'), 'RS485_TX', 'RS485_RX', 'RS485_DE',
                  conn_pins={'1': 'BUS_A', '2': 'BUS_B', '3': 'GND', '4': 'ADDR0', '5': 'ADDR1', '6': 'GND'},
                  desc='Column RS-485 bus: 1 A, 2 B, 3 GND, 4 ADDR0, 5 ADDR1, 6 GND (mating 43025-0600)')
D.R('R7', '10k', 'ADDR0', '+3V3', 'ADDR0 pull-up')
D.R('R8', '10k', 'ADDR1', '+3V3', 'ADDR1 pull-up')
FAN = []
for n in (1, 2):
    D.P('J%d' % (10 + n), 'Connector_Generic:Conn_01x04', 'Fan 4P', 'Connector:FanPinHeader_1x04_P2.54mm_Vertical',
        '47053-1000', 'Molex', 'WM4330-ND ' + SPN, {'1': 'GND', '2': '12V_IN', '3': 'FAN%d_TACH_IN' % n, '4': 'FAN%d_PWM' % n},
        'Heat-pipe tower fan %d, 4-pin PWM (Intel fan spec): 1 GND, 2 +12 V, 3 tach, 4 PWM' % n, price=0.4)
    FAN += blocks.nfet_od(D, 'Q%d' % n, 'R%d' % (9 + n), 'FAN%d_PWM_MCU' % n, 'FAN%d_PWM' % n, 'fan PWM open drain')
    D.R('R%d' % (11 + 2 * n), '10k', 'FAN%d_TACH_IN' % n, '+3V3', 'tach pull-up')
    D.R('R%d' % (12 + 2 * n), '1k', 'FAN%d_TACH_IN' % n, 'FAN%d_TACH' % n, 'tach series')
    D.C('C%d' % (7 + n), '10n', 'FAN%d_TACH' % n, 'GND')
    FAN += ['R%d' % (11 + 2 * n), 'R%d' % (12 + 2 * n), 'C%d' % (7 + n)]
NT = blocks.ntc(D, 'J8', 'R17', 'C10', 'NTC1', 'TEC hot side, tower 1') + blocks.ntc(D, 'J9', 'R18', 'C11', 'NTC2', 'TEC hot side, tower 2')
LED = blocks.led(D, 'D3', 'R19', 'LED_OK', 'GREEN') + blocks.led(D, 'D4', 'R20', 'LED_FLT', 'RED')
for tp, net in (('TP1', '12V_IN'), ('TP2', '+3V3'), ('TP3', 'GND'), ('TP4', 'GND')):
    D.TP(tp, net)
k = 1
for x, y in ((4.0, 4.0), (146.0, 4.0), (146.0, 106.0), (4.0, 106.0)):
    D.HOLE('H%d' % k, x, y)
    k += 1

D.notes = ['TS-2 rev B TCD-1 Peltier driver.  Generated by kgen from boards/tcd1/design.py.',
           '[verify] marks supplier numbers / land patterns not yet checked against the vendor drawing.']
D.signal_width = 0.2
D.signal_clearance = 0.2
D.netclasses = {
    'PWR': dict(nets=['12V_IN'] + ['T%d_%s' % (n, s) for n in range(1, 5) for s in ('SW', 'OUT', 'RET')],
                width=0.8, clearance=0.3),     # current is carried by the F pours; tracks only reach small pads
    'GATE': dict(nets=['T%d_%s' % (n, s) for n in range(1, 5) for s in ('GH', 'GL', 'HO', 'LO', 'HB')], width=0.4, clearance=0.2),
    'P3V3': dict(nets=['+3V3', 'B3_SW'], width=0.3, clearance=0.2),
}

# ===================================================================== placement (management band y 74..108)
D.place['U5'] = (78.0, 88.0, 0, 'F')
D.place['U1'] = (46.0, 98.0, 0, 'F')
D.place['L1'] = (56.0, 98.0, 0, 'F')
D.place['U6'] = (110.0, 98.0, 0, 'F')
D.place['J5'] = (124.0, 99.0, 0, 'F')
D.place['J6'] = (140.0, 99.0, 0, 'F')
D.place['J11'] = (126.0, 79.0, 0, 'F')
D.place['J12'] = (139.0, 79.0, 0, 'F')
D.place['J8'] = (101.0, 80.0, 0, 'F')
D.place['J9'] = (112.0, 80.0, 0, 'F')
D.place['J10'] = (95.0, 104.0, 0, 'F')
D.regions += [
    ((40.0, 74.0, 62.0, 92.0), ['C3', 'C4', 'C5', 'C6', 'R1', 'R2', 'R3', 'R4', 'C7', 'D1', 'TP1', 'TP2']),
    ((64.0, 74.0, 94.0, 79.5), ['C50', 'C51', 'C52', 'C53', 'C54', 'C55', 'FB1', 'C56', 'C57', 'C58', 'R5']),
    ((64.0, 98.0, 90.0, 108.0), ['D3', 'R19', 'D4', 'R20', 'TP3', 'TP4']),
    ((96.0, 86.0, 120.0, 94.0), ['C60', 'D2', 'R6', 'JP1', 'R7', 'R8', 'R17', 'C10', 'R18', 'C11']),
    ((120.0, 84.0, 148.0, 92.0), FAN),
]
W, H = D.W, D.H
e = 0.5
D.pours = [dict(net='GND', layer='In1', rect=(e, e, W - e, H - e), thermal=False),
           dict(net='GND', layer='B', rect=(e, e, W - e, H - e), prio=0, thermal=False),
           dict(net='GND', layer='F', rect=(e, e, W - e, H - e), prio=0),
           dict(net='12V_IN', layer='In2', rect=(e, e, W - e, 76.0), prio=1, thermal=False),
           dict(net='12V_IN', layer='In2', rect=(e, 76.0, 38.0, H - e), prio=1, thermal=False),
           dict(net='+3V3', layer='In2', rect=(38.5, 76.5, W - e, H - e), prio=1),
           dict(net='12V_IN', layer='In2', rect=(118.0, 72.0, W - e, 86.0), prio=2, thermal=False),   # fan headers
           dict(net='12V_IN', layer='F', rect=(1.0, 78.0, 38.0, H - 1.0), prio=1, thermal=False)]
for k in range(NCH):
    x, n = chx(k), k + 1
    D.pours += [dict(net='T%d_SW' % n, layer='F', rect=(x - 11.0, 29.5, x + 11.0, 42.3), prio=2, thermal=False),
                dict(net='T%d_OUT' % n, layer='F', rect=(x - 16.5, 9.5, x + 4.5, 22.5), prio=2, thermal=False),
                dict(net='12V_IN', layer='F', rect=(x - 16.5, 46.0, x + 16.5, 52.5), prio=2, thermal=False)]
D.fanout = True
D.power_layers = ('In1', 'In2')
D.stitch = dict(net='GND', pitch=5.0, layers=['F', 'In1', 'B'])
D.silk = [dict(t='TS-2 rev B  TCD-1 Peltier driver  rev A', x=80.0, y=72.5, l='F', size=1.5)]
for k in range(NCH):
    D.silk.append(dict(t='TEC %d' % (k + 1), x=chx(k), y=1.6, l='F', size=1.2))
D.stackup = stackup_text([
    ('cu', 'F.Cu', 0.07), ('prepreg', 0.2, 'FR4', 4.3, 0.02), ('cu', 'In1.Cu', 0.07), ('core', 0.92, 'FR4', 4.3, 0.02),
    ('cu', 'In2.Cu', 0.07), ('prepreg', 0.2, 'FR4', 4.3, 0.02), ('cu', 'B.Cu', 0.07)], finish='ENIG', mask='Green')
D.fab = dict(
    rules={"min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.6, "min_through_hole_diameter": 0.3,
           "min_via_annular_width": 0.15, "min_copper_edge_clearance": 0.5, "min_hole_clearance": 0.3, "min_hole_to_hole": 0.3},
    layers=4, thickness='1.6 mm +/-10 %', material='High-Tg FR-4 Tg >= 170 C', copper='2 oz finished all layers',
    finish='ENIG', mask='green LPI both sides', silk='white top', impedance='none controlled',
    min_track='0.20 / 0.20 mm (8/8 mil)', min_drill='0.30 mm', vias='through only', size='150.0 x 110.0 mm', panel='1 up',
    press_fit='M5 studs press-fit: finished hole per PEM drawing', ipc='IPC-6012 class 2', test='100 % netlist (flying probe)')
D.test_notes = [
    'AOI top.  12 V 2 A limit on the studs: +3V3 3.30 V; idle < 80 mA with all channels off; no gate activity in reset.',
    'Each channel into a 0.6 ohm 300 W load: duty sweep 0-95 %; VOUT within 2 % of set point, IMON within 3 % of a reference shunt.',
    'Full load: four channels at 12 A for 30 min at 40 C ambient, FET case < 95 C, inductor < 100 C (thermocouples).',
    'Shoot-through check: low-side gate never overlaps high-side (scope, 50 ns dead time).',
    'Fans: 25 kHz PWM sweep, tach counted; NTC inputs with 10k read 25.0 C +/-0.5.  Modbus answers on the column bus.',
]
