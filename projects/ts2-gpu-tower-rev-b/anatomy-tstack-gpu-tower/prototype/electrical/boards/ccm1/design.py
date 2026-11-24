"""CCM-1: TS-2 rev B column cooling controller (one per column, in the base thermal module TS2B-601).

Job: keep the tracing-coil coolant at dew point + 2 K or above, prove cooling before any GPU gets power, and alarm.
  * Room dew point from an SHT45 (T / RH) on the arm inlet; coil air-side pressure drop from an SDP810-500Pa.
  * Six NTC channels: coolant supply, coolant return, room air at the coil inlet, GPU inlet air (lower and upper group),
    TEC cold block.  Two rope leak sensors (coil drip tray, base module floor).  Two pulse flow meters
    (column supply, pump loop).  Impeller 3 tachometer (impellers 1-2 are read by TMC-1).
  * D5 pump: 12 V, PWM speed (open-drain, inverted) and tach.  Chiller interface: run relay (dry contact), alarm input
    (opto), remote set point 0-9.9 V (DAC -> LM321 x 3).
  * Power interlock: drives PSON_REQ# to the CPD-1 only when flow, coolant temperature and leak checks pass; reads
    COL_PWR_OK.  Master on the column RS-485 bus (CPD-1, two CBP-8, TCD-1); slave on the tower bus (host, TMC-1).
  * Light bar: SK6812 strip, 5 V 2 A buck, data through a 74AHCT1G125 level shifter.
  * Power: 12V_AUX from the module's RSP-750-12 (always on with AC) and VSB from CPD-1, OR-ed by two Schottkys.

Board: 160.0 x 100.0 mm, 4 layers, 1.6 mm, all parts on F.  Connectors on the two long edges.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kgen'))
from core import Design   # noqa: E402
import blocks   # noqa: E402
from pcb import stackup_text   # noqa: E402

D = Design('ccm1', 'TS-2 rev B CCM-1 column cooling controller', 'A', w=160.0, h=100.0, layers=4, thickness=1.6, corner_r=3.0)
SPN = '[verify]'
MF = 'Connector_Molex:Molex_Micro-Fit_3.0_43045-0%d12_2x0%d_P3.00mm_Vertical'
PH = 'Connector_JST:JST_PH_B%dB-PH-K_1x0%d_P2.00mm_Vertical'


def microfit(ref, n2, pins, desc):
    """Micro-Fit 3.0 2 x n2 vertical"""
    D.P(ref, 'Connector_Generic:Conn_02x0%d_Odd_Even' % n2, 'Micro-Fit 2x%d' % n2, MF % (2 * n2, n2), '43045-0%d12' % (2 * n2),
        'Molex', SPN, pins, desc + ' (mating 43025-0%d00 + 43030 crimps)' % (2 * n2), price=1.2)


def jph(ref, n, pins, desc):
    D.P(ref, 'Connector_Generic:Conn_01x0%d' % n, 'PH %dP' % n, PH % (n, n), 'B%dB-PH-K-S' % n, 'JST', SPN, pins,
        desc + ' (mating PHR-%d + SPH-002T-P0.5S)' % n, price=0.2)


# ===================================================================== power
D.sheet('Power', notes=[
    '12V_AUX (RSP-750-12 in the base module, live with AC) and VSB (CPD-1 SYS) OR-ed by PMEG4050EP onto 12V_IN.',
    '+3V3: TPS54302 3 A.  +5V_LED: TPS54302 3 A, 10 uH, 4.95 V, light bar only.  Pump 12 V through a 2.5 A PTC.'])
microfit('J1', 2, {'1': '12V_AUX', '2': '12V_AUX', '3': 'GND', '4': 'GND'}, '12V_AUX in from RSP-750-12: 1/2 +12 V, 3/4 GND')
microfit('J2', 3, {'1': 'VSB', '2': 'VSB', '3': 'PSON_REQ#', '4': 'GND', '5': 'GND', '6': 'COL_PWR_OK'},
         'CPD-1 SYS: 1/2 VSB in, 3 PSON_REQ# out (open drain), 4/5 GND, 6 COL_PWR_OK in')
for d, a in (('D1', '12V_AUX'), ('D2', 'VSB')):
    D.P(d, 'Device:D_Schottky', 'PMEG4050EP', 'Diode_SMD:D_SOD-128', 'PMEG4050EP,115', 'Nexperia', '1727-4993-1-ND ' + SPN,
        {'1': '12V_IN', '2': a}, 'Schottky 40 V 5 A SOD-128, supply OR-ing', price=0.35)
D.P('D3', 'Device:D_TVS', 'SMBJ15CA', 'Diode_SMD:D_SMB', 'SMBJ15CA', 'Littelfuse', 'SMBJ15CALFCT-ND ' + SPN,
    {'1': '12V_IN', '2': 'GND'}, 'TVS 15 V 600 W, 12V_IN', price=0.3)
D.C('C1', '10u50', '12V_IN', 'GND')
D.C('C2', '10u50', '12V_IN', 'GND')
PWR = ['D1', 'D2', 'D3', 'C1', 'C2']
PWR += blocks.buck(D, 'U2', 'L1', 'C3', 'C4', ('C5', 'C6'), 'R1', 'R2', '12V_IN', '+3V3', 'B3_SW', 'B3_FB', 'B3_BST',
                   note='3.3 V 3 A buck (logic, sensors)')
PWR += blocks.buck(D, 'U3', 'L2', 'C7', 'C8', ('C9', 'C10'), 'R3', 'R4', '12V_IN', '+5V_LED', 'B5_SW', 'B5_FB', 'B5_BST',
                   rtop='100k', rbot='13.7k', note='5 V 3 A buck for the SK6812 light bar',
                   lval=('10u', 'SRP7028A-100M', 'SRP7028A-100MCT-ND'))
D.R('R5', '100k', '12V_IN', 'V12_MON', '12V_IN monitor top')
D.R('R6', '22k', 'V12_MON', 'GND')
D.C('C11', '100n', 'V12_MON', 'GND')
PWR += ['R5', 'R6', 'C11']

# ===================================================================== MCU + comms
D.sheet('MCU and buses', notes=[
    'USART2 (PA2/PA3, DE PA1): column bus master -> CPD-1, CBP-8 x 2, TCD-1.  USART1 (PA9/PA10, DE PA12): tower bus slave.',
    'I2C1 PA15/PB7: SHT45 (0x44).  I2C3 PC8/PC9: SDP810-500Pa (0x25).  Both 100 kHz, 2.2k pull-ups, TPD4E05 ESD.',
    'Timers: flow 1 PA5 (TIM2_CH1), flow 2 PB6 (TIM4_CH1), pump tach PC6 (TIM3_CH1), impeller 3 tach PC7 (TIM3_CH2);',
    'pump PWM PA8 (TIM1_CH1, 25 kHz, open drain inverted); light bar PB4 (TIM3_CH1 alt / DMA bit-bang).',
    'DAC1_OUT1 PA4 -> LM321 x 3 -> chiller set point 0-9.9 V.  ADC: NTC1-6 PC0 PC1 PC2 PC3 PA6 PA7, leak PB0 PB1, 12V_IN PB2.'])
PORTS = {'PA2': 'COL_TX', 'PA3': 'COL_RX', 'PA1': 'COL_DE', 'PA9': 'TWR_TX', 'PA10': 'TWR_RX', 'PA12': 'TWR_DE',
         'PA15': 'SCL1', 'PB7': 'SDA1', 'PC8': 'SCL3', 'PC9': 'SDA3',
         'PA5': 'FLOW1', 'PB6': 'FLOW2', 'PC6': 'PUMP_TACH', 'PC7': 'IMP3_TACH', 'PA8': 'PUMP_PWM_MCU', 'PB4': 'LED_DATA_3V',
         'PA4': 'SP_DAC', 'PC0': 'NTC1', 'PC1': 'NTC2', 'PC2': 'NTC3', 'PC3': 'NTC4', 'PA6': 'NTC5', 'PA7': 'NTC6',
         'PB0': 'LEAK1', 'PB1': 'LEAK2', 'PB2': 'V12_MON', 'PC10': 'CHILLER_RUN_MCU', 'PC11': 'CHILLER_ALM#',
         'PC12': 'DOOR1', 'PD2': 'DOOR2', 'PB12': 'LATCH', 'PB13': 'PSON_REQ_MCU', 'PB14': 'COL_PWR_OK',
         'PB10': 'ADDR0', 'PB11': 'ADDR1', 'PC13': 'LED_OK', 'PF1': 'LED_FLT'}
MCU = blocks.mcu(D, 'U1', PORTS, caps=('C', 20), fb='FB1')
MCU += blocks.boot_swd(D, 'R7', 'J24')
COLBUS = blocks.rs485(D, 'U4', 'C30', 'D4', 'R8', 'JP1', ('J3', 'J4'), 'COL_TX', 'COL_RX', 'COL_DE', a='COL_A', b='COL_B',
                      conn_pins={'1': 'COL_A', '2': 'COL_B', '3': 'GND', '4': 'ADDR0', '5': 'ADDR1', '6': 'GND'},
                      desc='Column RS-485 bus: 1 A, 2 B, 3 GND, 4 ADDR0, 5 ADDR1, 6 GND (mating 43025-0600)')
D.byref['R8']['dnp'] = False
D.byref['JP1']['dnp'] = False
D.byref['R8']['desc'] = 'Column bus termination 120 ohm - fitted: CCM-1 is the master at one end of the column bus'
TWRBUS = blocks.rs485(D, 'U5', 'C31', 'D5', 'R9', 'JP2', ('J5', 'J6'), 'TWR_TX', 'TWR_RX', 'TWR_DE', a='TWR_A', b='TWR_B',
                      desc='Tower RS-485 bus: 1 A, 2 B, 3 GND, 6 GND (mating 43025-0600)')
D.R('R10', '10k', 'ADDR0', '+3V3', 'ADDR0 pull-up (column number from the harness plug)')
D.R('R11', '10k', 'ADDR1', '+3V3', 'ADDR1 pull-up')
LEDS = blocks.led(D, 'D6', 'R12', 'LED_OK', 'GREEN') + blocks.led(D, 'D7', 'R13', 'LED_FLT', 'RED')
COMMS = COLBUS + TWRBUS + ['R10', 'R11']

# ===================================================================== sensors
D.sheet('Sensors', notes=[
    'NTC: 10k B3950 to GND, 10k pull-up to +3V3A, 100 nF.  1: coolant supply, 2: coolant return, 3: room air at coil inlet,',
    '4: GPU inlet lower group, 5: GPU inlet upper group, 6: TEC cold block.',
    'Leak: rope sensor (TraceTek TT1000 class) between LEAKx and GND; 100k pull-up; dry > 1 Mohm, wet < 50 kohm.',
    'Flow: Hall pulse meters (Gems FT-110 class, open collector), 12 V supply, 10k pull-up to +3V3, 1k + 1 nF input RC.',
    'SHT45 and SDP810 on 4-wire PH cables (3V3, SDA, SCL, GND), max 1 m.'])
SEN = []
for n, what in enumerate(('coolant supply', 'coolant return', 'room air at coil inlet', 'GPU inlet, lower group',
                          'GPU inlet, upper group', 'TEC cold block')):
    SEN += blocks.ntc(D, 'J%d' % (9 + n), 'R%d' % (20 + n), 'C%d' % (40 + n), 'NTC%d' % (n + 1), what)
for n in range(2):
    jph('J%d' % (15 + n), 2, {'1': 'LEAK%d' % (n + 1), '2': 'GND'},
        'Leak rope sensor %d (%s)' % (n + 1, 'coil drip tray' if n == 0 else 'base module floor'))
    D.R('R%d' % (26 + n), '100k', 'LEAK%d' % (n + 1), '+3V3A', 'leak pull-up')
    D.C('C%d' % (46 + n), '100n', 'LEAK%d' % (n + 1), 'GND')
    SEN += ['R%d' % (26 + n), 'C%d' % (46 + n)]
for n in range(2):
    jph('J%d' % (17 + n), 3, {'1': '12V_IN', '2': 'GND', '3': 'FLOW%d_IN' % (n + 1)},
        'Flow meter %d (%s): 1 +12 V, 2 GND, 3 pulse' % (n + 1, 'column supply' if n == 0 else 'pump loop'))
    D.R('R%d' % (28 + 2 * n), '10k', 'FLOW%d_IN' % (n + 1), '+3V3', 'open-collector pull-up')
    D.R('R%d' % (29 + 2 * n), '1k', 'FLOW%d_IN' % (n + 1), 'FLOW%d' % (n + 1), 'input series')
    D.C('C%d' % (48 + n), '10n', 'FLOW%d' % (n + 1), 'GND', 'input filter (pulses < 2 kHz)')
    SEN += ['R%d' % (28 + 2 * n), 'R%d' % (29 + 2 * n), 'C%d' % (48 + n)]
jph('J20', 2, {'1': 'IMP3_TACH_IN', '2': 'GND'}, 'Impeller 3 tach (open collector from the EC motor)')
D.R('R32', '10k', 'IMP3_TACH_IN', '+3V3', 'tach pull-up')
D.R('R33', '1k', 'IMP3_TACH_IN', 'IMP3_TACH', 'input series')
D.C('C50', '10n', 'IMP3_TACH', 'GND')
jph('J23', 4, {'1': 'DOOR1', '2': 'DOOR2', '3': 'LATCH', '4': 'GND'},
    'Switches to GND: 1 service door, 2 crown access, 3 coil latch')
for n, s in enumerate(('DOOR1', 'DOOR2', 'LATCH')):
    D.R('R%d' % (34 + n), '10k', s, '+3V3', '%s pull-up' % s)
    D.C('C%d' % (51 + n), '100n', s, 'GND', 'debounce')
SEN += ['R32', 'R33', 'C50', 'R34', 'R35', 'R36', 'C51', 'C52', 'C53']
for j, which, scl, sda in (('J7', 'SHT45 (room T/RH -> dew point)', 'SCL1', 'SDA1'), ('J8', 'SDP810-500Pa (coil dP)', 'SCL3', 'SDA3')):
    jph(j, 4, {'1': '+3V3', '2': sda, '3': scl, '4': 'GND'}, which + ': 1 3V3, 2 SDA, 3 SCL, 4 GND')
D.R('R37', '2.2k', 'SCL1', '+3V3', 'I2C pull-up')
D.R('R38', '2.2k', 'SDA1', '+3V3', 'I2C pull-up')
D.R('R39', '2.2k', 'SCL3', '+3V3', 'I2C pull-up')
D.R('R40', '2.2k', 'SDA3', '+3V3', 'I2C pull-up')
D.P('U6', 'Power_Protection:TPD4E05U06DQA', 'TPD4E05U06', 'Package_SON:USON-10_2.5x1.0mm_P0.5mm', 'TPD4E05U06DQAR',
    'Texas Instruments', '296-30407-1-ND ' + SPN, {'1': 'SDA1', '2': 'SCL1', '3': 'GND', '4': 'SDA3', '5': 'SCL3', '6': None,
                                                   '7': None, '8': 'GND', '9': None, '10': None},
    'ESD 4-channel 0.5 pF, sensor I2C lines', price=0.5)
D.C('C54', '100n', '+3V3', 'GND', 'sensor supply')
SEN += ['R37', 'R38', 'R39', 'R40', 'U6', 'C54']

# ===================================================================== actuators
D.sheet('Pump, chiller, light bar, interlock', notes=[
    'Pump: D5 PWM (Laing / Xylem D5 Vario-PWM class) 12 V 1.9 A: J19 1 +12 V (PTC F1), 2 GND, 3 PWM (open drain), 4 tach.',
    'Chiller J22: 1 COM, 2 NO, 3 NC (run relay, dry contact 1 A 24 V) [verify NO/NC pins vs Omron G5V-1 drawing];',
    '4 ALM (contact to GND, opto input), 5 GND, 6 SP out 0-9.9 V (10 mA), 7 AGND, 8 GND.',
    'PSON_REQ#: low only when firmware has flow > 4 L/min, supply > dew + 2 K, no leak, doors closed (see firmware spec).',
    'Light bar J21: 1 +5 V 2 A, 2 DIN (5 V CMOS via 74AHCT1G125 + 33 ohm), 3 GND.'])
D.P('F1', 'Device:Polyfuse', '2.5A', 'Fuse:Fuse_1812_4532Metric', 'MF-MSMF250/16X-2', 'Bourns', 'MF-MSMF250/16X-2CT-ND ' + SPN,
    {'1': '12V_IN', '2': 'PUMP_12V'}, 'PTC 2.5 A hold 16 V 1812, pump supply', price=0.4)
microfit('J19', 2, {'1': 'PUMP_12V', '2': 'GND', '3': 'PUMP_PWM', '4': 'PUMP_TACH_IN'},
         'D5 pump: 1 +12 V, 2 GND, 3 PWM, 4 tach')
ACT = ['F1']
ACT += blocks.nfet_od(D, 'Q1', 'R41', 'PUMP_PWM_MCU', 'PUMP_PWM', 'pump PWM open drain (inverted in firmware)')
D.R('R42', '10k', 'PUMP_TACH_IN', '+3V3', 'tach pull-up')
D.R('R43', '1k', 'PUMP_TACH_IN', 'PUMP_TACH', 'input series')
D.C('C55', '10n', 'PUMP_TACH', 'GND')
D.C('C56', '10u50', 'PUMP_12V', 'GND')
ACT += ['R42', 'R43', 'C55', 'C56']
# chiller
D.P('K1', 'Relay:G5V-1', 'G5V-1 12VDC', 'Relay_THT:Relay_SPDT_Omron_G5V-1', 'G5V-1-DC12', 'Omron', 'Z2296-ND ' + SPN,
    {'2': '12V_IN', '9': 'K1_COIL', '5': 'CHL_COM', '6': 'CHL_COM', '1': 'CHL_NC', '10': 'CHL_NO'},
    'Relay SPDT 12 V coil 30 mA, 1 A 24 VDC contact, chiller remote run', price=1.9)
D.P('D8', 'Diode:1N4148W', '1N4148W', 'Diode_SMD:D_SOD-123', '1N4148W-7-F', 'Diodes Inc', '1N4148W-FDICT-ND',
    {'1': '12V_IN', '2': 'K1_COIL'}, 'Relay coil flyback', price=0.05)
ACT += ['K1', 'D8'] + blocks.nfet_od(D, 'Q2', 'R44', 'CHILLER_RUN_MCU', 'K1_COIL', 'relay coil driver')
D.P('U7', 'Isolator:PC817', 'PC817', 'Package_DIP:SMDIP-4_W9.53mm', 'PC817X2NSZ9F', 'Sharp', 'PC817X2NSZ9F-ND ' + SPN,
    {'1': 'ALM_LED', '2': 'CHL_ALM', '3': 'GND', '4': 'CHILLER_ALM#'},
    'Optocoupler: chiller alarm contact input (contact closes CHL_ALM to GND)', price=0.3)
D.R('R45', '4.7k', '12V_IN', 'ALM_LED', 'opto LED 2.4 mA')
D.R('R46', '10k', 'CHILLER_ALM#', '+3V3', 'opto output pull-up')
ACT += ['U7', 'R45', 'R46']
D.P('U8', 'Amplifier_Operational:LM321', 'LM321', 'Package_TO_SOT_SMD:SOT-23-5', 'LM321MF/NOPB', 'Texas Instruments',
    'LM321MFNOPBCT-ND ' + SPN, {'1': 'SP_DAC', '2': 'GND', '3': 'SP_FB', '4': 'SP_AMP', '5': '12V_IN'},
    'Op-amp, set point amplifier x 3 (DAC 0-3.3 V -> 0-9.9 V)', price=0.3)
D.R('R47', '20k', 'SP_AMP', 'SP_FB', 'gain 1 + 20k / 10k = 3')
D.R('R48', '10k', 'SP_FB', 'GND')
D.R('R49', '100', 'SP_AMP', 'CHL_SP', 'output isolation')
D.C('C57', '100n', '12V_IN', 'GND')
D.C('C58', '10n', 'CHL_SP', 'GND')
ACT += ['U8', 'R47', 'R48', 'R49', 'C57', 'C58']
microfit('J22', 4, {'1': 'CHL_COM', '2': 'CHL_NO', '3': 'CHL_NC', '4': 'CHL_ALM', '5': 'GND', '6': 'CHL_SP', '7': 'GND',
                    '8': 'GND'}, 'Chiller: 1 COM, 2 NO, 3 NC, 4 ALM, 5 GND, 6 SP 0-9.9 V, 7 AGND, 8 GND')
# light bar
D.P('U9', '74xGxx:74AHCT1G125', '74AHCT1G125', 'Package_TO_SOT_SMD:SOT-23-5', 'SN74AHCT1G125DBVR', 'Texas Instruments',
    '296-4596-1-ND ' + SPN, {'1': 'GND', '2': 'LED_DATA_3V', '3': 'GND', '4': 'LED_DATA_5V', '5': '+5V_LED'},
    'Buffer 3.3 V -> 5 V (TTL input), SK6812 data', price=0.2)
D.C('C59', '100n', '+5V_LED', 'GND')
D.R('R50', '33', 'LED_DATA_5V', 'LED_DIN', 'data series')
jph('J21', 3, {'1': '+5V_LED', '2': 'LED_DIN', '3': 'GND'}, 'Light bar SK6812: 1 +5 V, 2 DIN, 3 GND')
ACT += ['U9', 'C59', 'R50']
# interlock
ACT += blocks.nfet_od(D, 'Q3', 'R51', 'PSON_REQ_MCU', 'PSON_REQ#', 'PSON_REQ# to CPD-1 (low = power on allowed)')
D.R('R52', '10k', 'COL_PWR_OK', '+3V3', 'COL_PWR_OK pull-up (CPD-1 output is open drain)')
ACT += ['R52']
for tp, net in (('TP1', '12V_IN'), ('TP2', '+3V3'), ('TP3', '+5V_LED'), ('TP4', 'GND'), ('TP5', 'CHL_SP'), ('TP6', 'GND')):
    D.TP(tp, net)
k = 1
for x in (4.0, 156.0):
    for y in (4.0, 96.0):
        D.HOLE('H%d' % k, x, y)
        k += 1

D.notes = ['TS-2 rev B CCM-1 column cooling controller.  Generated by kgen from boards/ccm1/design.py.',
           '[verify] marks supplier numbers / land patterns not yet checked against the vendor drawing.']
D.signal_width = 0.2
D.signal_clearance = 0.2
D.netclasses = {
    'PWR': dict(nets=['12V_IN', '12V_AUX', 'VSB', 'PUMP_12V', '+5V_LED', 'B3_SW', 'B5_SW'], width=0.8, clearance=0.25),
    'P3V3': dict(nets=['+3V3'], width=0.3, clearance=0.2),
}

# ===================================================================== placement
TOP, BOT = 93.0, 7.0
for ref, x in (('J1', 13.0), ('J2', 28.0), ('J3', 46.0), ('J4', 62.0), ('J5', 78.0), ('J6', 94.0), ('J22', 112.0),
               ('J19', 131.0)):
    D.place[ref] = (x, TOP, 0, 'F')
D.place['J21'] = (144.0, TOP - 1.0, 0, 'F')
for n in range(6):
    D.place['J%d' % (9 + n)] = (13.0 + 9.0 * n, BOT, 0, 'F')
for ref, x in (('J15', 67.0), ('J16', 76.0), ('J17', 85.0), ('J18', 96.0), ('J20', 106.0), ('J23', 115.0), ('J7', 127.0),
               ('J8', 139.0)):
    D.place[ref] = (x, BOT, 0, 'F')
D.place['U1'] = (80.0, 50.0, 0, 'F')
D.place['J24'] = (150.0, 50.0, 90, 'F')
D.place['U2'] = (12.0, 70.0, 0, 'F')
D.place['L1'] = (22.0, 70.0, 0, 'F')
D.place['U3'] = (12.0, 52.0, 0, 'F')
D.place['L2'] = (22.0, 52.0, 0, 'F')
D.place['K1'] = (124.0, 82.0, 0, 'F')
D.place['U4'] = (55.0, 76.0, 0, 'F')
D.place['U5'] = (85.0, 76.0, 0, 'F')
D.regions += [
    ((30.0, 60.0, 46.0, 84.0), ['D1', 'D2', 'D3', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'R1', 'R2', 'R5', 'R6', 'C11', 'TP1', 'TP4']),
    ((4.0, 38.0, 46.0, 46.0), ['C7', 'C8', 'C9', 'C10', 'R3', 'R4', 'TP3', 'TP2']),
    ((64.0, 59.0, 100.0, 66.0), ['C20', 'C21', 'C22', 'C23', 'C24', 'C25', 'FB1', 'C26', 'C27', 'C28', 'R7', 'D6', 'R12', 'D7', 'R13']),
    ((48.0, 68.0, 70.0, 84.0), ['C30', 'D4', 'R8', 'JP1', 'R10', 'R11']),
    ((76.0, 68.0, 100.0, 84.0), ['C31', 'D5', 'R9', 'JP2']),
    ((4.0, 14.0, 62.0, 32.0), ['R20', 'C40', 'R21', 'C41', 'R22', 'C42', 'R23', 'C43', 'R24', 'C44', 'R25', 'C45']),
    ((62.0, 14.0, 128.0, 32.0), ['R26', 'C46', 'R27', 'C47', 'R28', 'R29', 'C48', 'R30', 'R31', 'C49', 'R32', 'R33', 'C50',
                                 'R34', 'R35', 'R36', 'C51', 'C52', 'C53']),
    ((128.0, 14.0, 156.0, 32.0), ['R37', 'R38', 'R39', 'R40', 'U6', 'C54']),
    ((104.0, 36.0, 142.0, 64.0), ['U8', 'R47', 'R48', 'R49', 'C57', 'C58', 'U7', 'R45', 'R46', 'Q2', 'R44', 'D8', 'TP5', 'TP6',
                                  'Q3', 'R51', 'R52']),
    ((140.0, 62.0, 157.0, 86.0), ['F1', 'Q1', 'R41', 'R42', 'R43', 'C55', 'C56', 'U9', 'C59', 'R50']),
]

W, H = D.W, D.H
e = 0.5
D.pours = [dict(net='GND', layer='In1', rect=(e, e, W - e, H - e)),
           dict(net='GND', layer='F', rect=(e, e, W - e, H - e), prio=0),
           dict(net='GND', layer='B', rect=(e, e, W - e, H - e), prio=0),
           dict(net='+3V3', layer='In2', rect=(e, e, W - e, H - e), prio=0),
           dict(net='12V_IN', layer='In2', rect=(2.0, 56.0, 48.0, 86.0), prio=1)]
D.fanout = True
D.power_layers = ('In1', 'In2')
D.stitch = dict(net='GND', pitch=6.0, layers=['F', 'In1', 'B'])
D.silk = [dict(t='TS-2 rev B  CCM-1 cooling controller  rev A', x=80.0, y=35.0, l='F', size=1.6),
          dict(t='machine-generated - review before release', x=80.0, y=33.0, l='F', size=0.9)]
D.stackup = stackup_text([
    ('cu', 'F.Cu', 0.035), ('prepreg', 0.2, 'FR4', 4.3, 0.02), ('cu', 'In1.Cu', 0.035), ('core', 1.065, 'FR4', 4.3, 0.02),
    ('cu', 'In2.Cu', 0.035), ('prepreg', 0.2, 'FR4', 4.3, 0.02), ('cu', 'B.Cu', 0.035)], finish='ENIG', mask='Green')
D.fab = dict(
    rules={"min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.25,
           "min_via_annular_width": 0.1, "min_copper_edge_clearance": 0.4, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25},
    layers=4, thickness='1.6 mm +/-10 %', material='FR-4 Tg 150', copper='1 oz all layers', finish='ENIG',
    mask='green LPI both sides', silk='white top', impedance='none controlled', min_track='0.15 / 0.15 mm (6/6 mil)',
    min_drill='0.25 mm', vias='through only', size='160.0 x 100.0 mm', panel='1 up', ipc='IPC-6012 class 2',
    test='100 % netlist (flying probe)')
D.test_notes = [
    'AOI top.  Power from J1 at 12 V 1 A limit: +3V3 3.30 V, +5V_LED 4.95 V +/-3 %, idle < 60 mA; repeat from J2 (VSB) with J1 open.',
    'Six 10k resistors on the NTC inputs read 25.0 C +/-0.5 C; leak inputs read dry open / wet with 22k to GND.',
    'Flow and tach inputs: 100 Hz square from a function generator (open collector) counted +/-1 Hz.',
    'SHT45 and SDP810 on 300 mm cables answer at 0x44 / 0x25.',
    'Pump PWM 25 kHz on J19-3 (open drain); relay clicks, J22 1-2 closes; alarm short J22-4 to GND reads active;',
    'set point DAC 1.65 V -> J22-6 4.95 V +/-1 %.  Light bar: 60 SK6812 on J21 run the test pattern.',
    'Interlock: PSON_REQ# (J2-3) stays high-Z until the simulated flow, temperature and leak checks pass.',
    'Modbus on both buses: column master polls a CPD-1; tower slave answers the host at the strapped address.',
]
