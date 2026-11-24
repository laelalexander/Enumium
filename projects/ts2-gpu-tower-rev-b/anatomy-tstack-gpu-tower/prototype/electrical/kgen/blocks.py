"""Reusable circuit blocks shared by the rev B boards (same parts, same pin logic, same firmware base).

Each block adds parts to a Design and returns the refs it created, so the board can place or region-pack them.
The STM32G474RET6 pin map is built by port name from the KiCad symbol, so a board only lists {port: net}.
"""
import symlib
from core import R0603

SPN = '[verify]'
_MCU_SYM = 'MCU_ST_STM32G4:STM32G474RETx'


def mcu(D, ref, ports, vdd='+3V3', vdda='+3V3A', caps=('C', 1), swd='J', fb='FB', nrst='NRST'):
    """STM32G474RET6 + 5 x 100 nF + 4.7 uF, ferrite-fed VDDA/VREF+, NRST cap, BOOT0 (PB8) pull-down, SWD 10-pin.
    ports: {'PA0': 'NET', ...}.  Unlisted ports are left unconnected.  Returns created refs."""
    pins = symlib.pins(symlib.load(_MCU_SYM))
    used = set()
    pm = {}
    for p in pins:
        n, nm = p['number'], p['name']
        if nm in ('VSS', 'VSSA'):
            pm[n] = 'GND'
        elif nm in ('VDD', 'VBAT'):
            pm[n] = vdd
        elif nm in ('VDDA', 'VREF+'):
            pm[n] = vdda
        elif nm == 'PG10':
            pm[n] = nrst
        elif nm == 'PB8':
            pm[n] = 'BOOT0'
        elif nm in ('PA13', 'PA14', 'PB3'):
            pm[n] = {'PA13': 'SWDIO', 'PA14': 'SWCLK', 'PB3': 'SWO'}[nm]
        else:
            pm[n] = ports.get(nm)
            if nm in ports:
                used.add(nm)
    missing = set(ports) - used
    assert not missing, 'unknown or reserved MCU ports: %s' % sorted(missing)
    D.P(ref, _MCU_SYM, 'STM32G474RET6', 'Package_QFP:LQFP-64_10x10mm_P0.5mm', 'STM32G474RET6', 'STMicroelectronics',
        '497-19525-ND ' + SPN, pm, 'MCU Arm Cortex-M4F 170 MHz, 512 KB flash, LQFP-64 (pin map from the KiCad STM32G4 symbol)',
        price=7.9)
    out = [ref]
    cp, cn = caps
    for j in range(5):
        r = '%s%d' % (cp, cn + j)
        D.C(r, '100n', vdd, 'GND', 'MCU VDD decoupling')
        out.append(r)
    r = '%s%d' % (cp, cn + 5)
    D.C(r, '4.7u', vdd, 'GND')
    out.append(r)
    D.P(fb, 'Device:FerriteBead_Small', '600R', 'Inductor_SMD:L_0603_1608Metric', 'BLM18KG601SN1D', 'Murata',
        '490-5258-1-ND ' + SPN, {'1': vdd, '2': vdda}, 'Ferrite 600 ohm @ 100 MHz, VDDA / VREF+ filter', price=0.1)
    out.append(fb)
    for j, (v, net) in enumerate((('1u', vdda), ('100n', vdda), ('100n', nrst))):
        r = '%s%d' % (cp, cn + 6 + j)
        D.C(r, v, net, 'GND', 'NRST filter' if net == nrst else 'VDDA decoupling')
        out.append(r)
    return out


def boot_swd(D, rboot, jswd, vdd='+3V3', nrst='NRST'):
    D.R(rboot, '10k', 'BOOT0', 'GND', 'BOOT0 pull-down (boot from flash)')
    D.P(jswd, 'Connector_Generic:Conn_02x05_Odd_Even', 'SWD', 'Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical',
        'FTSH-105-01-F-DV-K', 'Samtec', 'SAM8796-ND ' + SPN, {'1': vdd, '2': 'SWDIO', '3': 'GND', '4': 'SWCLK', '5': 'GND',
                                                            '6': 'SWO', '7': None, '8': None, '9': 'GND', '10': nrst},
        'Arm Cortex debug 10-pin 1.27 mm (SWD + SWO), keyed', price=2.1)
    return [rboot, jswd]


def buck(D, u, l, cb, cin, couts, rt, rb, vin, vout, sw, fbn, bst, rtop='100k', rbot='22k', note='3.3 V 3 A buck',
         lval=('6.8u', 'SRP7028A-6R8M', 'SRP7028A-6R8MCT-ND'), side='F'):
    """TPS54302 4.5-28 V 3 A buck.  Vout = 0.596 x (1 + Rtop/Rbot)."""
    D.P(u, 'Regulator_Switching:TPS54302', 'TPS54302', 'Package_TO_SOT_SMD:SOT-23-6', 'TPS54302DDCR', 'Texas Instruments',
        '296-47648-1-ND ' + SPN, {'1': 'GND', '2': sw, '3': vin, '4': fbn, '5': None, '6': bst}, note, price=0.8, side=side)
    D.P(l, 'Device:L', lval[0], 'Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm', lval[1], 'Bourns', lval[2] + ' ' + SPN,
        {'1': sw, '2': vout}, 'Inductor %sH shielded 7.3 x 6.6 x 2.8 mm' % lval[0].replace('u', ' u'), price=0.6, side=side)
    D.C(cb, '100n', bst, sw, 'Bootstrap 100 nF', side=side)
    D.C(cin, '10u50', vin, 'GND', side=side)
    for c in couts:
        D.C(c, '22u', vout, 'GND', side=side)
    D.R(rt, rtop, vout, fbn, 'FB top', side=side)
    D.R(rb, rbot, fbn, 'GND', 'FB bottom: 0.596 x (1 + %s / %s)' % (rtop, rbot), side=side)
    return [u, l, cb, cin, rt, rb] + list(couts)


def rs485(D, u, c, tvs, rterm, jp, conns, tx, rx, de, a='BUS_A', b='BUS_B', vdd='+3V3', conn_pins=None, desc=None):
    """THVD1420 half-duplex transceiver, SM712 TVS, DNP 120 ohm termination, Micro-Fit 2x3 in/out."""
    D.P(u, 'Interface_UART:THVD1420D', 'THVD1420', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'THVD1420DR', 'Texas Instruments',
        '296-THVD1420DRCT-ND ' + SPN, {'1': rx, '2': de, '3': de, '4': tx, '5': 'GND', '6': a, '7': b, '8': vdd},
        'RS-485 half duplex 12 Mbps, 3.3 V, +/-12 kV ESD, fail-safe receiver', price=1.6)
    D.C(c, '100n', vdd, 'GND')
    D.P(tvs, 'Diode:SM712_SOT23', 'SM712', 'Package_TO_SOT_SMD:SOT-23', 'SM712.TCT', 'Semtech', 'SM712.TCTCT-ND ' + SPN,
        {'1': a, '2': b, '3': 'GND'}, 'RS-485 TVS -7 / +12 V asymmetric', price=0.4)
    tn = a + '_TERM'
    D.R(rterm, '120', a, tn, 'Bus termination 120 ohm - fit on the end node only', dnp=True)
    D.P(jp, 'Device:R', '0', R0603, '0603WAF0000T5E', 'UNI-ROYAL', '', {'1': tn, '2': b},
        'Termination link (fit with %s on the end node)' % rterm, dnp=True)
    pins = conn_pins or {'1': a, '2': b, '3': 'GND', '4': None, '5': None, '6': 'GND'}
    for j in conns:
        D.P(j, 'Connector_Generic:Conn_02x03_Odd_Even', 'Micro-Fit 2x3',
            'Connector_Molex:Molex_Micro-Fit_3.0_43045-0612_2x03_P3.00mm_Vertical', '43045-0612', 'Molex', 'WM1784-ND ' + SPN,
            pins, desc or 'RS-485 bus in/out: 1 A, 2 B, 3 GND, 6 GND (mating 43025-0600 + 43030 crimps)', price=1.3)
    return [u, c, tvs, rterm, jp] + list(conns)


def led(D, d, r, net, colour):
    mpn = {'GREEN': '150060VS75000', 'RED': '150060RS75000', 'YELLOW': '150060YS75000', 'BLUE': '150060BS75000'}[colour]
    D.R(r, '1k', net, net + '_A')
    D.P(d, 'Device:LED', colour, 'LED_SMD:LED_0603_1608Metric', mpn, 'Wurth Elektronik', SPN, {'1': 'GND', '2': net + '_A'},
        'LED %s 0603' % colour.lower(), price=0.15)
    return [d, r]


def ntc(D, j, r, c, net, what, vref='+3V3A'):
    D.P(j, 'Connector_Generic:Conn_01x02', 'NTC', 'Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical', 'B2B-PH-K-S',
        'JST', '455-1704-ND', {'1': net, '2': 'GND'}, 'NTC 10k B3950 cable sensor: %s' % what, price=0.2)
    D.R(r, '10k', net, vref, 'NTC divider 10k')
    D.C(c, '100n', net, 'GND')
    return [j, r, c]


def nfet_od(D, q, rg, net_in, net_out, what):
    """2N7002 open-drain driver with 100k gate pull-down (output released while the MCU is in reset)."""
    D.P(q, 'Transistor_FET:2N7002', '2N7002', 'Package_TO_SOT_SMD:SOT-23', '2N7002,215', 'Nexperia', '1727-2N7002215CT-ND',
        {'1': net_in, '2': 'GND', '3': net_out}, 'N-MOSFET 60 V 0.3 A SOT-23, ' + what, price=0.05)
    D.R(rg, '100k', net_in, 'GND', 'gate pull-down')
    return [q, rg]
