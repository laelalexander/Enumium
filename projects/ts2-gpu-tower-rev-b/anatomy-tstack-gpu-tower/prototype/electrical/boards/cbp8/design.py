"""CBP-8: TS-2 rev B 8-slot GPU backplane (two per column, eight per tower).

Function, per slot (8 slots at the 50.8 mm card pitch):
  * PCIe CEM x16 vertical SMT slot (lanes 0-7 wired, x8 electrical) <- coupled 85 ohm stripline pairs ->
    MCIO 8i right-angle receptacle on the rear face -> cable to the host's HighPoint Rocket 1628A switch card.
  * 12 V hot-swap: MIC2587-1 controller + CSD17556Q5B (1.4 mOhm) + 2 x 3 mOhm shunt (1.5 mOhm, ~33 A breaker),
    INA181A2 current monitor (75 mV/A) to the MCU, soft-start by gate capacitor.  The switched 12 V feeds the
    12V-2x6 header (GPU auxiliary power, 600 W class sense straps) and the slot's 12 V pins.
  * Slot 3.3 V: TPS54302 3 A buck from the switched 12 V (off whenever the slot is off).
  * PERST# to the card = host PERST# AND slot power-good (74LVC1G08), so a card never sees reset released
    before its rails are up.  PRSNT2# (x16) reported to the MCU and to the host (MCIO CBL_PRES_A#).
Board level: four M6 press-fit studs to the column busbars (2 x +12 V, 2 x RTN), always-on 3.3 V buck,
STM32G474RET6 slot manager (Modbus RTU slave on the column RS-485 bus, address from the harness), SWD,
two NTC inputs, status LEDs, bus TVS.

Board: 268.0 x 434.4 mm, 8 layers, 2.0 mm (see STACKUP).  Coordinates: board-local, lower-left origin seen from
the front (F, component side facing the GPUs), x = u - 236 (column radial), y = z - (group z - 14).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kgen'))
from core import Design, R0603, R2512   # noqa: E402
import fpgen   # noqa: E402
import hsroute   # noqa: E402
from pcb import stackup_text   # noqa: E402

D = Design('cbp8', 'TS-2 rev B CBP-8 GPU backplane', 'A', w=268.0, h=434.4, layers=8, thickness=2.0, corner_r=4.0)
PITCH = 50.8
NS = 8
CEM_CX = 50.55                      # board x of the CEM pin-span centre (pin 1 at u = 244.9)


def ys(i):
    return 14.0 + PITCH * i          # slot_z(group, i) in board y


def mcio_cx(i):
    return 22.0 + 24.0 * (7 - i)    # CAD mcio_x = 258 + 24 (7 - i), minus 236


SPN = '[verify]'

# ===================================================================== per-slot circuit
CEM_SYM = 'Connector:Bus_PCI_Express_x16'
import symlib   # noqa: E402
cem_pins = {p['number']: p['name'] for p in symlib.pins(symlib.load(CEM_SYM))}
mcio_pins = {p['number']: p['name'] for p in symlib.pins(symlib.load('ts2b:MCIO_8i_74P'))}


def lane_nets(k, kind, lane):
    return ('S%d_%s%d_P' % (k, kind, lane), 'S%d_%s%d_N' % (k, kind, lane))


for i in range(NS):
    k = i + 1
    D.sheet('Slot %d' % k, notes=[
        'Slot %d: PCIe x16 CEM (x8 electrical) <-> MCIO 8i, 12 V hot-swap + current monitor, 3.3 V buck, PERST# gating.' % k,
        'Lanes: host TX (MCIO A-row PER) -> CEM side B PET; card TX (CEM side A PER) -> MCIO B-row PET.  Straight-through MCIO cable.',
        'Lane pairs are pre-routed coupled striplines (In2 / In4), 0.13 / 0.18 mm, 85 ohm differential target (see fab notes).',
        'Hot-swap: breaker 50 mV / 1.5 mOhm = 33 A; gate 22 nF -> about 0.7 V/ms ramp (18 ms to 12 V); PG at 10.3 V (100k / 13.7k).',
        '12V-2x6: SENSE0 = SENSE1 = GND -> 600 W cable class; CARD_CBL_PRES# grounded.'])
    n12, nsns, n33 = 'S%d_12V' % k, 'S%d_12V_SNS' % k, 'S%d_3V3' % k
    prs, pg, on, onm = 'S%d_PRSNT#' % k, 'S%d_PG' % k, 'S%d_ON' % k, 'S%d_ON_MCU' % k
    # --- CEM x16 slot
    pm = {}
    lanes_b = {hsroute.NEAR[l][0]: lane_nets(k, 'HTX', l)[0] for l in range(8)}
    lanes_b.update({hsroute.NEAR[l][1]: lane_nets(k, 'HTX', l)[1] for l in range(8)})
    lanes_a = {hsroute.FAR[l][0]: lane_nets(k, 'HRX', l)[0] for l in range(8)}
    lanes_a.update({hsroute.FAR[l][1]: lane_nets(k, 'HRX', l)[1] for l in range(8)})
    for num, name in cem_pins.items():
        side, n = num[0], int(num[1:])
        if name == 'GND':
            net = 'GND'
        elif name == '+12V':
            net = n12
        elif name == '+3.3V':
            net = n33
        elif side == 'B' and n in lanes_b:
            net = lanes_b[n]
        elif side == 'A' and n in lanes_a:
            net = lanes_a[n]
        else:
            net = {'A1': 'GND', 'A11': 'S%d_PERST_C#' % k, 'A13': 'S%d_REFCLK_P' % k, 'A14': 'S%d_REFCLK_N' % k,
                   'B5': 'S%d_SMBCLK' % k, 'B6': 'S%d_SMBDAT' % k, 'B10': '+3V3', 'B81': prs}.get(num)
        pm[num] = net
    D.P('J%d01' % k, CEM_SYM, 'PCIe x16 SMT', 'ts2b:TE_2364427_PCIe_x16_Vertical_SMT', '2364427-4', 'TE Connectivity', SPN,
        pm, 'PCIe CEM x16 slot, vertical SMT, 164P 1.00 mm, Gen5 32 GT/s (x8 electrical: lanes 8-15 unconnected)', price=6.5)
    # --- MCIO 8i
    pm = {}
    for num, name in mcio_pins.items():
        row, n = num[0], num[1:]
        net = None
        if name in ('GND', 'SHIELD'):
            net = 'GND'
        elif row == 'A':
            for l in range(8):
                a, b = hsroute.MCIO[l]
                if n == str(a):
                    net = lane_nets(k, 'HTX', l)[0]
                if n == str(b):
                    net = lane_nets(k, 'HTX', l)[1]
            net = net or {'SMB_SCL': 'S%d_SMBCLK' % k, 'SMB_SDA': 'S%d_SMBDAT' % k, 'PERST_A#': 'S%d_PERST_H#' % k,
                          'CBL_PRES_A#': prs}.get(name)
        elif row == 'B':
            for l in range(8):
                a, b = hsroute.MCIO[l]
                if n == str(a):
                    net = lane_nets(k, 'HRX', l)[0]
                if n == str(b):
                    net = lane_nets(k, 'HRX', l)[1]
            net = net or {'REFCLK_A+': 'S%d_REFCLK_P' % k, 'REFCLK_A-': 'S%d_REFCLK_N' % k}.get(name)
        pm[num] = net
    D.P('J%d02' % k, 'ts2b:MCIO_8i_74P', 'MCIO 8i RA', 'ts2b:Amphenol_G97R22332HR_MCIO_8i_RA_SMT', 'G97R22332HR',
        'Amphenol ICC', SPN, pm, 'MCIO 8i 74P 0.60 mm right-angle SMT receptacle (SFF-TA-1016), rear face', side='B', price=9.0)
    # --- 12V-2x6 GPU power header
    pm = {('P%d' % n): n12 for n in range(1, 7)}
    pm.update({('P%d' % n): 'GND' for n in range(7, 13)})
    pm.update({'S1': None, 'S2': 'GND', 'S3': 'GND', 'S4': 'GND', 'MP1': 'GND', 'MP2': 'GND'})
    D.P('J%d03' % k, 'ts2b:12V-2x6_Header', '12V-2x6 RA', 'ts2b:Amphenol_10160920-1240100LF_12V-2x6_RA', '10160920-1240100LF',
        'Amphenol CS', 'RS 236-8779', pm, '12V-2x6 16P RA header to the GPU power cable (600 W: SENSE0/1 = GND)', price=3.2)
    # --- hot-swap
    D.P('U%d01' % k, 'Power_Management:MIC2587-1', 'MIC2587-1', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'MIC2587-1YM',
        'Microchip', '576-1418-5-ND ' + SPN, {'1': on, '2': 'S%d_FB' % k, '3': pg, '4': 'GND', '5': 'S%d_TMR' % k,
                                              '6': 'S%d_GATE' % k, '7': nsns, '8': '+12V'},
        'Hot-swap controller 10-80 V, circuit breaker 50 mV, latched (-1)', side='B', price=2.9)
    D.P('Q%d01' % k, 'Transistor_FET:CSD17556Q5B', 'CSD17556Q5B', 'Package_TO_SOT_SMD:TDSON-8-1', 'CSD17556Q5B', 'Texas Instruments',
        '296-37919-1-ND ' + SPN, {'1': n12, '2': n12, '3': n12, '4': 'S%d_G' % k, '5': nsns},
        'N-MOSFET 30 V 1.4 mOhm SON 5x6, hot-swap pass element', side='B', price=1.4)
    for r in ('02', '03'):
        D.P('R%d%s' % (k, r), 'Device:R', '3m', R2512, 'WSL2512R0030FEA', 'Vishay Dale', 'WSL2512.003FCT-ND ' + SPN,
            {'1': '+12V', '2': nsns}, 'Current sense 3 mOhm 1 % 2512 1 W (two in parallel = 1.5 mOhm)', side='B', price=0.7)
    D.R('R%d04' % k, '10', 'S%d_GATE' % k, 'S%d_G' % k, 'Gate series 10 ohm', side='B')
    D.C('C%d01' % k, '22n', 'S%d_G' % k, 'GND', 'Gate slew capacitor 22 nF (inrush dV/dt)', side='B')
    D.C('C%d02' % k, '22n', 'S%d_TMR' % k, 'GND', 'TIMER 22 nF (overcurrent fault delay)', side='B')
    D.C('C%d03' % k, '100n', '+12V', 'GND', side='B')
    D.R('R%d05' % k, '100k', n12, 'S%d_FB' % k, 'PG divider top', side='B')
    D.R('R%d06' % k, '13.7k', 'S%d_FB' % k, 'GND', 'PG divider bottom: PG at 1.24 x 113.7/13.7 = 10.3 V', side='B')
    D.R('R%d07' % k, '10k', onm, on, 'ON series', side='B')
    D.R('R%d08' % k, '100k', on, 'GND', 'ON pull-down: slot off while the MCU is in reset', side='B')
    D.R('R%d09' % k, '10k', pg, '+3V3', 'PWRGD pull-up', side='B')
    D.C('C%d04' % k, '22u25', '+12V', 'GND', side='B')
    D.C('C%d05' % k, '22u25', '+12V', 'GND', side='B')
    D.C('C%d06' % k, '22u25', n12, 'GND', side='B')
    D.C('C%d07' % k, '22u25', n12, 'GND', side='B')
    # --- current monitor
    D.P('U%d02' % k, 'Amplifier_Current:INA181', 'INA181A2', 'Package_TO_SOT_SMD:SOT-23-6', 'INA181A2IDBVR', 'Texas Instruments',
        '296-49601-1-ND ' + SPN, {'1': 'S%d_IMON_A' % k, '2': 'GND', '3': '+12V', '4': nsns, '5': 'GND', '6': '+3V3'},
        'Current-sense amplifier gain 50: 1.5 mOhm x 50 = 75 mV/A (30 A = 2.25 V)', side='B', price=0.9)
    D.C('C%d08' % k, '100n', '+3V3', 'GND', side='B')
    D.R('R%d10' % k, '1k', 'S%d_IMON_A' % k, 'S%d_IMON' % k, 'ADC RC 1k', side='B')
    D.C('C%d09' % k, '10n', 'S%d_IMON' % k, 'GND', 'ADC RC 10 nF (16 kHz)', side='B')
    # --- slot 3.3 V buck (F side, near the slot's 3.3 V pins)
    D.P('U%d03' % k, 'Regulator_Switching:TPS54302', 'TPS54302', 'Package_TO_SOT_SMD:SOT-23-6', 'TPS54302DDCR', 'Texas Instruments',
        '296-47648-1-ND ' + SPN, {'1': 'GND', '2': 'S%d_SW' % k, '3': n12, '4': 'S%d_FB33' % k, '5': None, '6': 'S%d_BST' % k},
        'Buck 4.5-28 V 3 A 400 kHz, EN floating = on (input is the switched slot 12 V)', price=0.8)
    D.P('L%d01' % k, 'Device:L', '6.8u', 'Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm', 'SRP7028A-6R8M', 'Bourns',
        'SRP7028A-6R8MCT-ND ' + SPN, {'1': 'S%d_SW' % k, '2': n33}, 'Inductor 6.8 uH shielded 7.3 x 6.6 x 2.8 mm', price=0.6)
    D.C('C%d10' % k, '100n', 'S%d_BST' % k, 'S%d_SW' % k, 'Bootstrap 100 nF')
    D.C('C%d11' % k, '10u50', n12, 'GND')
    D.C('C%d12' % k, '22u', n33, 'GND')
    D.C('C%d13' % k, '22u', n33, 'GND')
    D.R('R%d11' % k, '100k', n33, 'S%d_FB33' % k, 'FB top')
    D.R('R%d12' % k, '22k', 'S%d_FB33' % k, 'GND', 'FB bottom: 0.596 x (1 + 100/22) = 3.31 V')
    # --- PERST# gating, sideband pull-ups
    D.P('U%d04' % k, '74xGxx:74LVC1G08', '74LVC1G08', 'Package_TO_SOT_SMD:SOT-23-5', 'SN74LVC1G08DBVR', 'Texas Instruments',
        '296-11601-1-ND ' + SPN, {'1': 'S%d_PERST_H#' % k, '2': pg, '3': 'GND', '4': 'S%d_PERST_C#' % k, '5': '+3V3'},
        'AND: card PERST# released only when host PERST# is high AND slot power is good', side='B', price=0.2)
    D.C('C%d14' % k, '100n', '+3V3', 'GND', side='B')
    D.R('R%d13' % k, '10k', 'S%d_PERST_H#' % k, '+3V3', 'host PERST# pull-up', side='B')
    D.R('R%d14' % k, '10k', prs, '+3V3', 'PRSNT2# pull-up (card shorts it to PRSNT1# = GND)', side='B')
    D.R('R%d15' % k, '4.7k', 'S%d_SMBCLK' % k, '+3V3', 'SMBus pull-up', side='B')
    D.R('R%d16' % k, '4.7k', 'S%d_SMBDAT' % k, '+3V3', 'SMBus pull-up', side='B')

# ===================================================================== board power and management
D.sheet('Power and management', notes=[
    '+12V from the column busbars through two M6 press-fit studs (T1, T3); RTN through T2, T4.',
    'Always-on +3V3 (3 A): TPS54302 from +12V; feeds the MCU, logic, sideband pull-ups and every slot 3.3Vaux pin.',
    'Modbus RTU slave on the column RS-485 bus, 115200 8E1; node address = 0x20 + 2 x ADDR1 + ADDR0, straps in the harness',
    'plug (open = 1, tied to GND = 0; TS2B-ELE-102).  Termination R904 + JP901: DNP, fitted only on CBP-8 upper (end node).',
    'MCU pins: IMON1-8 PA0-PA7 (ADC); ON1-8 PC6-PC9, PC10-PC12, PD2; PG1-8 PB0-PB2, PB10-PB14; PRSNT1-8 PC2-PC5, PB15, PA8,',
    'PA11, PA15; USART1 PA9 TX / PA10 RX / PA12 DE; NTC PC0, PC1; ADDR PB5, PB6; LEDs PB4, PB7; SWD PA13/PA14, SWO PB3; BOOT0 PB8.'])
for t, net, x, y in (('T1', '+12V', 253.5, 100.7), ('T2', 'GND', 253.5, 119.7), ('T3', '+12V', 253.5, 303.9),
                     ('T4', 'GND', 253.5, 322.9)):
    D.P(t, 'ts2b:Power_Terminal', 'M6 stud', 'ts2b:Power_Stud_M6_PressFit', 'FHS-M6-35ZI ' + SPN, 'PennEngineering', SPN,
        {'1': net}, 'M6 x 35 press-fit stud to the %s busbar TS2B-%s (%s Cu bush), 12 mm pad all layers' %
        (('+12 V', '215', '6 mm') if net == '+12V' else ('RTN', '216', '18 mm, PTFE sleeve through the +12 V bar')), side='B', price=1.2)
    D.place[t] = (x, y, 0, 'B')
for d in ('D901', 'D902'):
    D.P(d, 'Device:D_TVS', 'SMBJ15CA', 'Diode_SMD:D_SMB', 'SMBJ15CA', 'Littelfuse', 'SMBJ15CALFCT-ND ' + SPN,
        {'1': '+12V', '2': 'GND'}, 'TVS 15 V standoff 600 W bidirectional, +12V bus', price=0.3)
# always-on 3.3 V
D.P('U901', 'Regulator_Switching:TPS54302', 'TPS54302', 'Package_TO_SOT_SMD:SOT-23-6', 'TPS54302DDCR', 'Texas Instruments',
    '296-47648-1-ND ' + SPN, {'1': 'GND', '2': 'SB_SW', '3': '+12V', '4': 'SB_FB', '5': None, '6': 'SB_BST'},
    'Always-on 3.3 V 3 A buck', price=0.8)
D.P('L901', 'Device:L', '6.8u', 'Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm', 'SRP7028A-6R8M', 'Bourns',
    'SRP7028A-6R8MCT-ND ' + SPN, {'1': 'SB_SW', '2': '+3V3'}, 'Inductor 6.8 uH', price=0.6)
D.C('C901', '100n', 'SB_BST', 'SB_SW')
D.C('C902', '10u50', '+12V', 'GND')
D.C('C903', '22u', '+3V3', 'GND')
D.C('C904', '22u', '+3V3', 'GND')
D.R('R901', '100k', '+3V3', 'SB_FB')
D.R('R902', '22k', 'SB_FB', 'GND')
# MCU
MCU = {'1': '+3V3', '2': None, '3': None, '4': None, '5': None, '6': None, '7': 'NRST',
       '8': 'NTC1', '9': 'NTC2', '10': 'S1_PRSNT#', '11': 'S2_PRSNT#', '12': 'S1_IMON', '13': 'S2_IMON', '14': 'S3_IMON',
       '15': 'GND', '16': '+3V3', '17': 'S4_IMON', '18': 'S5_IMON', '19': 'S6_IMON', '20': 'S7_IMON', '21': 'S8_IMON',
       '22': 'S3_PRSNT#', '23': 'S4_PRSNT#', '24': 'S1_PG', '25': 'S2_PG', '26': 'S3_PG', '27': 'GND', '28': '+3V3A',
       '29': '+3V3A', '30': 'S4_PG', '31': 'GND', '32': '+3V3', '33': 'S5_PG', '34': 'S6_PG', '35': 'S7_PG', '36': 'S8_PG',
       '37': 'S5_PRSNT#', '38': 'S1_ON_MCU', '39': 'S2_ON_MCU', '40': 'S3_ON_MCU', '41': 'S4_ON_MCU', '42': 'S6_PRSNT#',
       '43': 'RS485_TX', '44': 'RS485_RX', '45': 'S7_PRSNT#', '46': 'RS485_DE', '47': 'GND', '48': '+3V3', '49': 'SWDIO',
       '50': 'SWCLK', '51': 'S8_PRSNT#', '52': 'S5_ON_MCU', '53': 'S6_ON_MCU', '54': 'S7_ON_MCU', '55': 'S8_ON_MCU',
       '56': 'SWO', '57': 'LED_OK', '58': 'ADDR0', '59': 'ADDR1', '60': 'LED_FLT', '61': 'BOOT0', '62': None, '63': 'GND',
       '64': '+3V3'}
D.P('U902', 'MCU_ST_STM32G4:STM32G474RETx', 'STM32G474RET6', 'Package_QFP:LQFP-64_10x10mm_P0.5mm',
    'STM32G474RET6', 'STMicroelectronics', '497-19525-ND ' + SPN, MCU,
    'MCU Arm Cortex-M4F 170 MHz, 512 KB flash, LQFP-64 (pin map from the KiCad STM32G4 library)', price=7.9)
for j, net in enumerate(['+3V3'] * 5):
    D.C('C9%02d' % (10 + j), '100n', net, 'GND', 'MCU VDD decoupling')
D.C('C915', '4.7u', '+3V3', 'GND')
D.P('FB901', 'Device:FerriteBead_Small', '600R', 'Inductor_SMD:L_0603_1608Metric', 'BLM18KG601SN1D', 'Murata',
    '490-5258-1-ND ' + SPN, {'1': '+3V3', '2': '+3V3A'}, 'Ferrite 600 ohm @ 100 MHz, VDDA / VREF+ filter', price=0.1)
D.C('C916', '1u', '+3V3A', 'GND')
D.C('C917', '100n', '+3V3A', 'GND')
D.C('C918', '100n', 'NRST', 'GND', 'NRST filter')
D.R('R903', '10k', 'BOOT0', 'GND', 'BOOT0 pull-down (boot from flash)')
# RS-485
D.P('U903', 'Interface_UART:THVD1420D', 'THVD1420', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'THVD1420DR', 'Texas Instruments',
    '296-THVD1420DRCT-ND ' + SPN, {'1': 'RS485_RX', '2': 'RS485_DE', '3': 'RS485_DE', '4': 'RS485_TX', '5': 'GND',
                                   '6': 'BUS_A', '7': 'BUS_B', '8': '+3V3'},
    'RS-485 half duplex 12 Mbps, 3.3 V, +/-12 kV ESD, fail-safe receiver', price=1.6)
D.C('C919', '100n', '+3V3', 'GND')
D.P('D903', 'Diode:SM712_SOT23', 'SM712', 'Package_TO_SOT_SMD:SOT-23', 'SM712.TCT', 'Semtech', 'SM712.TCTCT-ND ' + SPN,
    {'1': 'BUS_A', '2': 'BUS_B', '3': 'GND'}, 'RS-485 TVS -7 / +12 V asymmetric', price=0.4)
D.R('R904', '120', 'BUS_A', 'BUS_TERM', 'Bus termination 120 ohm - fit on the last node only', dnp=True)
D.P('JP901', 'Device:R', '0', R0603, '0603WAF0000T5E', 'UNI-ROYAL', '', {'1': 'BUS_TERM', '2': 'BUS_B'},
    'Termination link (fit with R904 on the last node)', dnp=True)
for jj in ('J903', 'J904'):
    D.P(jj, 'Connector_Generic:Conn_02x03_Odd_Even', 'Micro-Fit 2x3', 'Connector_Molex:Molex_Micro-Fit_3.0_43045-0612_2x03_P3.00mm_Vertical',
        '43045-0612', 'Molex', 'WM1784-ND ' + SPN, {'1': 'BUS_A', '2': 'BUS_B', '3': 'GND', '4': 'ADDR0', '5': 'ADDR1', '6': 'GND'},
        'Column RS-485 bus in/out: 1 A, 2 B, 3 GND, 4 ADDR0, 5 ADDR1, 6 GND (mating 43025-0600 + 43030 crimps)', price=1.3)
D.R('R905', '10k', 'ADDR0', '+3V3', 'ADDR0 pull-up')
D.R('R906', '10k', 'ADDR1', '+3V3', 'ADDR1 pull-up')
# SWD (Arm Cortex 10-pin 1.27 mm)
D.P('J905', 'Connector_Generic:Conn_02x05_Odd_Even', 'SWD', 'Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical',
    'FTSH-105-01-F-DV-K', 'Samtec', 'SAM8796-ND ' + SPN, {'1': '+3V3', '2': 'SWDIO', '3': 'GND', '4': 'SWCLK', '5': 'GND',
                                                        '6': 'SWO', '7': None, '8': None, '9': 'GND', '10': 'NRST'},
    'Arm Cortex debug 10-pin 1.27 mm (SWD + SWO), keyed', price=2.1)
# NTC inputs
for n, (jj, r, c) in enumerate((('J906', 'R907', 'C920'), ('J907', 'R908', 'C921'))):
    D.P(jj, 'Connector_Generic:Conn_01x02', 'NTC', 'Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical', 'B2B-PH-K-S',
        'JST', '455-1704-ND', {'1': 'NTC%d' % (n + 1), '2': 'GND'},
        'NTC 10k B3950 cable sensor %d (%s)' % (n + 1, 'busbar joint' if n == 0 else 'rear air'), price=0.2)
    D.R(r, '10k', 'NTC%d' % (n + 1), '+3V3A', 'NTC divider 10k')
    D.C(c, '100n', 'NTC%d' % (n + 1), 'GND')
# LEDs
for d, r, net, col, mpn in (('D904', 'R909', 'LED_OK', 'GREEN', '150060VS75000'), ('D905', 'R910', 'LED_FLT', 'RED', '150060RS75000')):
    D.R(r, '1k', net, net + '_A')
    D.P(d, 'Device:LED', col, 'LED_SMD:LED_0603_1608Metric', mpn, 'Wurth Elektronik', SPN, {'1': 'GND', '2': net + '_A'},
        'LED %s 0603 (%s)' % (col.lower(), 'heartbeat' if col == 'GREEN' else 'slot fault'), price=0.15)
for tp, net in (('TP901', '+12V'), ('TP902', '+3V3'), ('TP903', 'GND'), ('TP904', 'BUS_A'), ('TP905', 'BUS_B')):
    D.TP(tp, net)
# mounting: 9 x M3 plated (CAD: x 6 / 134 / 262, y 6 / 205 / H-6)
k = 1
for x in (6.0, 134.0, 262.0):
    for y in (6.0, 205.0, D.H - 6.0):          # middle row clear of slot 4's CEM (CAD: z0 + 205)
        D.HOLE('H%d' % k, x, y)
        k += 1

D.notes = [
    'TS-2 rev B CBP-8 GPU backplane.  Two per column (lower and upper 8-slot group), eight per tower; identical boards,',
    'the group and column come from the ADDR0/ADDR1 straps in the column-bus harness plug.',
    'Generated by kgen from boards/cbp8/design.py.  Parts with [verify] have supplier numbers or land patterns not yet',
    'checked against the vendor drawing; docs/part-verification.md lists each one.  Engineering review required before release.',
]

# ===================================================================== net classes
D.signal_width = 0.15
D.signal_clearance = 0.15
D.netclasses = {
    'PWR12': dict(nets=['+12V'] + ['S%d_12V' % k for k in range(1, 9)] + ['S%d_12V_SNS' % k for k in range(1, 9)],
                  width=1.0, clearance=0.25),
    'PWR3V3': dict(nets=['+3V3'] + ['S%d_3V3' % k for k in range(1, 9)] + ['S%d_SW' % k for k in range(1, 9)] + ['SB_SW'],
                   width=0.6, clearance=0.2),
    'PCIE': dict(nets=[n for k in range(1, 9) for kind in ('HTX', 'HRX') for l in range(8) for n in lane_nets(k, kind, l)]
                 + ['S%d_REFCLK_%s' % (k, s) for k in range(1, 9) for s in 'PN'],
                 width=0.13, clearance=0.15, diff=(0.13, 0.18), via=(0.4, 0.2)),
}

# ===================================================================== placement
for i in range(NS):
    k = i + 1
    y0 = ys(i)
    D.place['J%d01' % k] = (CEM_CX, y0 + 2.8, 0, 'F')
    D.place['J%d02' % k] = (mcio_cx(i), y0 + 20.0, 0, 'B')
    D.place['J%d03' % k] = (250.0, y0 + 20.0, 0, 'F')
    D.place['Q%d01' % k] = (221.0, y0 + 18.5, 180, 'B')
    D.place['R%d02' % k] = (231.5, y0 + 16.2, 0, 'B')
    D.place['R%d03' % k] = (231.5, y0 + 20.8, 0, 'B')
    D.place['U%d01' % k] = (213.0, y0 + 29.5, 0, 'B')
    D.place['U%d02' % k] = (228.0, y0 + 27.5, 0, 'B')
    D.place['U%d03' % k] = (30.0, y0 + 15.0, 0, 'F')
    D.place['L%d01' % k] = (40.0, y0 + 15.0, 0, 'F')
    # small parts: B side cluster below/above the power path, F side around the buck
    D.regions.append(((205.5, y0 + 31.5, 234.5, y0 + 37.0), ['R%d04' % k, 'C%d01' % k, 'C%d02' % k, 'C%d03' % k, 'R%d05' % k,
                                                            'R%d06' % k, 'R%d07' % k, 'R%d08' % k, 'R%d09' % k, 'C%d08' % k,
                                                            'R%d10' % k, 'C%d09' % k], 'B'))
    D.regions.append(((205.5, y0 + 6.0, 234.5, y0 + 12.5), ['C%d04' % k, 'C%d05' % k, 'C%d06' % k, 'C%d07' % k,
                                                           'U%d04' % k, 'C%d14' % k, 'R%d13' % k, 'R%d14' % k, 'R%d15' % k,
                                                           'R%d16' % k], 'B'))
    D.regions.append(((20.0, y0 + 18.8, 48.0, y0 + 23.6), ['C%d10' % k, 'C%d11' % k, 'C%d12' % k, 'C%d13' % k,
                                                          'R%d11' % k, 'R%d12' % k], 'F'))
# management cluster in the band-3 / band-4 gaps right of the card tails (F side, x 237-267)
g3 = ys(3) + 29.0
D.place['U902'] = (248.0, g3 + 14.0, 0, 'F')
D.place['J905'] = (259.5, g3 + 27.0, 90, 'F')       # pins 1..9 run +x: last pin 5.1 mm in from the edge
D.regions.append(((237.0, g3 + 0.8, 267.0, g3 + 6.6), ['C910', 'C911', 'C912', 'C913', 'C914', 'C915', 'FB901', 'C916', 'C917',
                                                       'C918'], 'F'))
D.regions.append(((237.0, g3 + 22.0, 257.0, g3 + 33.5), ['R903', 'R905', 'R906', 'R909', 'R910', 'D904', 'D905'], 'F'))
g2 = ys(2) + 29.0
D.place['U901'] = (241.0, g2 + 9.0, 0, 'F')
D.place['L901'] = (241.0, g2 + 17.0, 0, 'F')
D.regions.append(((246.0, g2 + 4.0, 267.0, g2 + 30.0), ['C901', 'C902', 'C903', 'C904', 'R901', 'R902', 'D901', 'D902',
                                                        'TP901', 'TP902', 'TP903'], 'F'))
g4 = ys(4) + 29.0
D.place['J903'] = (243.0, g4 + 26.0, 0, 'F')
D.place['J904'] = (259.5, g4 + 26.0, 0, 'F')
D.place['U903'] = (244.0, g4 + 8.0, 0, 'F')
D.regions.append(((250.0, g4 + 2.0, 267.0, g4 + 18.0), ['C919', 'D903', 'R904', 'JP901', 'TP904', 'TP905'], 'F'))
g6 = ys(6) + 29.0
D.place['J906'] = (244.0, g6 + 20.0, 0, 'F')
D.place['J907'] = (256.0, g6 + 20.0, 0, 'F')
D.regions.append(((240.0, g6 + 4.0, 264.0, g6 + 12.0), ['R907', 'C920', 'R908', 'C921'], 'F'))

# ===================================================================== pre-routed lanes + power via arrays
REPORT = []
for i in range(NS):
    k = i + 1
    y0 = ys(i)
    cx, cy = CEM_CX, y0 + 2.8
    mx, my = mcio_cx(i), y0 + 20.0
    tr, vi, rep = hsroute.route_slot(k, lambda n: cx + fpgen.cem_x(n), (cx, cy), lambda n: mx - fpgen.mcio_x(n), (mx, my),
                                     lambda kind, l, k=k: lane_nets(k, kind, l), cx + 49.2)   # U-turn columns clear the CEM key NPTH at cx + 47.4
    D.prerouted += tr + vi
    REPORT += rep
    # the slot's 25 A F-side pour (via array -> 12V-2x6 header) must stay whole: no other copper may cross it
    D.keepouts.append(dict(name='S%d_12V_F' % k, rect=(217.5, y0 + 12.5, 238.3, y0 + 28.0), layers=['F'], pour=False, vias=False))
    # same on B for the hot-swap source pour and the sense pour (tracks only: their own via arrays stay)
    D.keepouts.append(dict(name='S%d_12V_B' % k, rect=(205.5, y0 + 13.2, 217.4, y0 + 24.0), layers=['B'], pour=False, vias=False))
    D.keepouts.append(dict(name='S%d_SNS_B' % k, rect=(219.6, y0 + 13.2, 229.9, y0 + 24.0), layers=['B'], pour=False, vias=False))
    # MCIO GND pins: a B-side bridge between the A and B rows ties every GND pin of both rows together, so the GND
    # pins at the In4 pair gaps (no via possible there) still reach the GND vias of their neighbours
    D.pack_avoid = getattr(D, 'pack_avoid', []) + [(mx - 11.0, my + 1.5, 1.2), (mx + 11.0, my + 1.5, 1.2)]   # MCIO pegs
    # no routed copper inside hole clearance of the locating-peg NPTHs (CEM 2.35 mm, MCIO 1.10 mm), every layer
    ALL = ['F', 'In1', 'In2', 'In3', 'In4', 'In5', 'In6', 'B']
    for j_, (hx, hy, hr) in enumerate([(cx - 47.4, cy, 1.45), (cx + 47.4, cy, 1.45), (mx - 11.0, my + 1.5, 0.76), (mx + 11.0, my + 1.5, 0.76)]):
        D.keepouts.append(dict(name='S%d_peg%d' % (k, j_), circle=(hx, hy, hr), layers=ALL, pour=False))
    gpins = (1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37)
    xs = [mx - fpgen.mcio_x(n) for n in gpins]
    D.prerouted.append(dict(net='GND', layer='B', width=0.15, pts=[(min(xs), my + 7.0), (max(xs), my + 7.0)]))
    for x in xs:
        D.prerouted.append(dict(net='GND', layer='B', width=0.15, pts=[(x, my + 6.0), (x, my + 7.0), (x, my + 8.0)]))
    # 25 A path: hot-swap output (B pour) <-> F pour under the 12V-2x6 header: 6 x 7 via array 0.3/0.6
    for a in range(7):
        for b in range(6):
            D.prerouted.append(dict(net='S%d_12V' % k, at=(206.8 + a * 1.6, y0 + 14.2 + b * 1.6), drill=0.3, dia=0.6))
    # shunt input pads to the +12V bus layers, drain node
    for b in range(5):
        D.prerouted.append(dict(net='S%d_12V_SNS' % k, at=(226.6, y0 + 14.6 + b * 1.6), drill=0.3, dia=0.6))

# ===================================================================== pours (planes) and keep-outs
W, H = D.W, D.H
e = 0.6
D.pours = [
    dict(net='GND', layer='In1', rect=(e, e, W - e, H - e)),
    dict(net='GND', layer='In3', rect=(e, e, W - e, H - e)),
    dict(net='GND', layer='In5', rect=(e, e, W - e, H - e)),
    dict(net='GND', layer='F', rect=(e, e, W - e, H - e), prio=0, thermal='tht'),     # SMD pads solid, THT relieved
    dict(net='GND', layer='B', rect=(e, e, W - e, H - e), prio=0, thermal='tht'),
    dict(net='+12V', layer='In2', rect=(236.5, e, W - e, H - e), prio=1),
    dict(net='+12V', layer='In4', rect=(236.5, e, W - e, H - e), prio=1),
    dict(net='+12V', layer='In6', rect=(236.5, e, W - e, H - e), prio=1),
    dict(net='+12V', layer='B', rect=(233.2, e, W - e, H - e), prio=1),
]
for i in range(NS):
    k = i + 1
    y0 = ys(i)
    D.pours += [
        dict(net='S%d_12V' % k, layer='F', rect=(205.0, y0 + 12.0, 263.0, y0 + 28.5), prio=2, thermal=False),
        dict(net='S%d_12V' % k, layer='B', rect=(205.5, y0 + 13.2, 218.6, y0 + 24.0), prio=2, thermal=False),
        dict(net='S%d_12V_SNS' % k, layer='B', rect=(219.6, y0 + 13.2, 229.9, y0 + 24.0), prio=2, thermal=False),
        dict(net='S%d_12V' % k, layer='In6', rect=(4.0, y0 + 31.0, 234.0, y0 + 44.0), prio=1),
    ]
D.power_layers = ("In1", "In3", "In5", "In6")
D.fanout = True
D.stitch = dict(net='GND', pitch=6.0, layers=['F', 'In1', 'In3', 'In5', 'B'])
D.no_stitch = tuple(['J%d01' % k for k in range(1, 9)] + ['J%d02' % k for k in range(1, 9)])

D.silk = [dict(t='TS-2 rev B  CBP-8 GPU backplane  rev A', x=150.0, y=D.H - 3.0, l='F', size=2.0),
          dict(t='machine-generated - review before release', x=150.0, y=D.H - 6.5, l='F', size=1.2)]
for i in range(NS):
    D.silk.append(dict(t='SLOT %d' % (i + 1), x=150.0, y=ys(i) + 30.0, l='F', size=2.0))
    D.silk.append(dict(t='S%d 12V-2x6' % (i + 1), x=250.0, y=ys(i) + 9.5, l='F', size=1.0))
    D.silk.append(dict(t='MCIO S%d' % (i + 1), x=mcio_cx(i), y=ys(i) + 32.0, l='B', size=1.2))

# ===================================================================== stackup and fab
D.stackup = stackup_text([
    ('cu', 'F.Cu', 0.07), ('prepreg', 0.12, 'Megtron 6', 3.4, 0.004),
    ('cu', 'In1.Cu', 0.035), ('core', 0.15, 'Megtron 6', 3.4, 0.004),
    ('cu', 'In2.Cu', 0.035), ('prepreg', 0.15, 'Megtron 6', 3.4, 0.004),
    ('cu', 'In3.Cu', 0.035), ('core', 0.56, 'Megtron 6', 3.4, 0.004),
    ('cu', 'In4.Cu', 0.035), ('prepreg', 0.15, 'Megtron 6', 3.4, 0.004),
    ('cu', 'In5.Cu', 0.035), ('core', 0.15, 'Megtron 6', 3.4, 0.004),
    ('cu', 'In6.Cu', 0.07), ('prepreg', 0.17, 'Megtron 6', 3.4, 0.004),
    ('cu', 'B.Cu', 0.07)], finish='ENIG', mask='Green')
D.fab = dict(
    rules={"min_clearance": 0.1, "min_track_width": 0.1, "min_via_diameter": 0.4, "min_through_hole_diameter": 0.2,
           "min_via_annular_width": 0.1, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.2, "min_hole_to_hole": 0.25},
    layers=8, thickness='2.0 mm +/-10 %', material='Panasonic Megtron 6 (R-5775) or equivalent low-loss, Tg >= 185 C',
    copper='F/B 2 oz finished, In6 2 oz, In1-In5 1 oz', finish='ENIG', mask='green LPI both sides', silk='white both sides',
    impedance='In2/In4 edge-coupled stripline 0.13 / 0.18 mm -> 85 ohm +/-10 % differential (fab to adjust width, keep gap)',
    min_track='0.10 mm / 0.10 mm (4/4 mil)', min_drill='0.20 mm mechanical (HS vias 0.20 / 0.40 pad, tented)',
    vias='through only; HS signal vias back-drilled from F to In2 bottom / from B to In4 top is NOT required at Gen4',
    size='268.0 x 434.4 mm', panel='1 up', ipc='IPC-6012 class 2, IPC-A-600 class 2', test='100 % netlist (flying probe)')
D.test_notes = [
    'Visual + AOI both sides; X-ray the CEM (SMT, 164 pins) and MCIO solder joints on the first article.',
    'Power-up with no cards on a 12 V 10 A current-limited supply at T1/T2: +3V3 = 3.30 V +/-2 %; MCU heartbeat LED blinks.',
    'Per slot with ON driven: S#_12V ramps in 15-25 ms, PG asserts above 10.3 V, S#_3V3 = 3.30 V; IMON reads 0 A +/-0.3 A.',
    'Electronic load 25 A on each 12V-2x6 header (one at a time, 5 min): IMON within 3 %; hot-swap FET case < 85 C; 30 A trips.',
    'PERST# check: with host PERST# high, card PERST# follows slot PG; with ON low, card PERST# stays low.',
    'Modbus: read holding registers over the column bus at the strapped address; slot presence follows a test card.',
    "PCIe: link-train an RTX PRO 6000 Max-Q in every slot at Gen4 x8 through a 0.8 m MCIO cable; lspci -vv must show "
    "'LnkSta: Speed 16GT/s, Width x8'; then a 30 min nvbandwidth loop with no AER errors.",
]
