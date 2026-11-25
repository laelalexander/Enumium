"""TS-2 rev B wiring harness: cables, numbered wire list, connector schedule, strap table, harness BOM, drawings.

Board-side pinouts are read from the board design tables (electrical/boards/*/design.py), so every wire traces to a
real board net.  Off-board devices (sensors, pump, TECs, supplies, busbars) are defined here.

Outputs (electrical/harness/out/):
  TS2B-ELE-101_harness_schematic.pdf   column wiring schematic (3 sheets) + tower bus / AC sheet
  TS2B-ELE-102_wire_list.pdf / .xlsx / .csv   every conductor numbered W001..., with from/to, gauge, colour, length mm + in
  TS2B-ELE-103_connector_schedule (sheet in the xlsx + PDF)
Per-column harness is identical; the label reads <W-number>-C<column>.  Tower-level cables use W5xx.
"""
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'kgen'))
import build   # noqa: E402

OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)
B = {b: build.load(b).D for b in ('cbp8', 'cpd1', 'ccm1', 'tcd1')}

# ------------------------------------------------------------------ unit locations (column frame, mm: u radial, v, z)
# CBP-8: board x -> u = 236 + x, board y -> z = group z - 14 + y, rear face v = -64.4.  CPD-1: plane u = 591.7,
# board x -> v = x - 125, board y -> z = 115 + y.  Base thermal module TS2B-601: u 660-900, z 400-570.
LOC = {
    'CBP-L': lambda x, y: (236.0 + x, -66.0, 438.0 + y),
    'CBP-U': lambda x, y: (236.0 + x, -66.0, 904.4 + y),
    'CPD-1': lambda x, y: (589.0, x - 125.0, 115.0 + y),
    'CCM-1': lambda x, y: (690.0 + x, 108.0, 410.0 + y),
    'TCD-1': lambda x, y: (690.0 + x, -108.0, 410.0 + y),
}
BOARD_OF = {'CBP-L': 'cbp8', 'CBP-U': 'cbp8', 'CPD-1': 'cpd1', 'CCM-1': 'ccm1', 'TCD-1': 'tcd1'}
DEV = {   # off-board end points
    'BUSBAR+': (489.5, -80.0, 120.0), 'BUSBAR-': (489.5, -92.0, 120.0),
    'CPD STRAP+': (591.0, 0.0, 180.0), 'CPD STRAP-': (591.0, 0.0, 196.0),
    'RSP-750-12': (740.0, 90.0, 230.0), 'ARM AC TB': (880.0, 140.0, 200.0),
    'SHT45': (625.0, 0.0, 520.0), 'SDP810': (600.0, 40.0, 450.0),
    'NTC coolant supply': (573.0, 90.0, 430.0), 'NTC coolant return': (573.0, 90.0, 1350.0),
    'NTC room air': (622.0, 0.0, 900.0), 'NTC GPU inlet L': (528.0, 0.0, 650.0), 'NTC GPU inlet U': (528.0, 0.0, 1130.0),
    'NTC cold block': (780.0, 0.0, 450.0), 'Leak drip tray': (573.0, 0.0, 405.0), 'Leak module floor': (780.0, 60.0, 402.0),
    'Flow column supply': (560.0, 95.0, 420.0), 'Flow pump loop': (800.0, 40.0, 430.0), 'D5 pump': (800.0, 0.0, 430.0),
    'Impeller 3': (205.0, 0.0, 1485.0), 'Light bar': (630.0, 0.0, 420.0), 'Chiller bulkhead': (905.0, 150.0, 300.0),
    'Door switches': (700.0, 160.0, 250.0), 'NTC strap': (591.0, 40.0, 190.0), 'NTC arm inlet': (915.0, 0.0, 120.0),
    'TEC 1': (720.0, 0.0, 452.0), 'TEC 2': (758.0, 0.0, 452.0), 'TEC 3': (796.0, 0.0, 452.0), 'TEC 4': (834.0, 0.0, 452.0),
    'NTC hot side 1': (780.0, -76.0, 520.0), 'NTC hot side 2': (780.0, 76.0, 520.0),
}


def conn_pos(unit, ref):
    D = B[BOARD_OF[unit]]
    pl = D.place.get(ref)
    if pl is None:            # region-packed parts: use the footprint position from the routed board if available
        return LOC[unit](D.W / 2, D.H / 2)
    return LOC[unit](pl[0], pl[1])


def pins(unit, ref):
    return B[BOARD_OF[unit]].byref[ref]['pins']


def route_len(a, b, via=()):
    pts = [a] + list(via) + [b]
    L = sum(abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) for p, q in zip(pts[:-1], pts[1:]))
    L = L * 1.15 + 100.0                       # 15 % routing allowance + 2 x 50 mm service loops
    return int(math.ceil(L / 25.0) * 25)


# ------------------------------------------------------------------ mating parts
MF_HOUS = {4: '43025-0400', 6: '43025-0600', 8: '43025-0800'}
MF_CRIMP = {18: '43030-0038 [verify] (18 AWG)', 20: '43030-0007 (20-24 AWG)', 22: '43030-0007 (20-24 AWG)',
            24: '43030-0007 (20-24 AWG)'}
PH_CRIMP = 'SPH-002T-P0.5S (24-30 AWG)'


def mating(unit, ref):
    p = B[BOARD_OF[unit]].byref[ref]
    v, fp = p['value'], p['fp']
    if 'Micro-Fit' in v:
        n = len([k for k in p['pins'] if k.isdigit()])
        return 'Molex Micro-Fit 3.0 receptacle %s' % MF_HOUS[n], 'MF'
    if v.startswith('PH') or v == 'NTC':
        n = len(p['pins'])
        return 'JST PHR-%d' % n, 'PH'
    if 'Fan' in v:
        return 'fan cable plug (Molex 47054-1000 class, supplied on the fan)', 'FAN'
    return v, ''


# ------------------------------------------------------------------ cable table
CABLES = []     # dict(id, name, a, b, kind, wires=[dict(fp, tp, sig, awg, col)], len, notes, cols)
W = {'n': 0}


def wire_no():
    W['n'] += 1
    return 'W%03d' % W['n']


def cable(cid, name, a, b, wires, length, notes='', kind='discrete', columns='all', twisted=()):
    ws = []
    for w in wires:
        fp, tp, sig, awg, col = w
        ws.append(dict(no=wire_no() if kind != 'assembly' else '', fp=fp, tp=tp, sig=sig, awg=awg, col=col))
    CABLES.append(dict(id=cid, name=name, a=a, b=b, wires=ws, len=length, notes=notes, kind=kind, cols=columns,
                       twisted=twisted))


def board_cable(cid, name, ua, ra, ub, rb, pinmap, awg, colours, notes='', via=(), columns='all', twisted=()):
    """pinmap: [(pin_a, pin_b)]; signal name from board A's net (checked against board B's net)."""
    pa, pb = pins(ua, ra), pins(ub, rb)
    ws = []
    for (x, y), a, c in zip(pinmap, awg, colours):
        na, nb = pa.get(x), pb.get(y)
        sig = na if na == nb or nb is None else '%s / %s' % (na, nb)
        ws.append((x, y, sig, a, c))
    L = route_len(conn_pos(ua, ra), conn_pos(ub, rb), via)
    cable(cid, name, (ua, ra), (ub, rb), ws, L, notes, columns=columns, twisted=twisted)


def dev_cable(cid, name, unit, ref, dev, pinmap, awg, colours, notes='', via=(), columns='all', dev_conn='', twisted=()):
    p = pins(unit, ref)
    ws = [(x, y, p.get(x), a, c) for (x, y), a, c in zip(pinmap, awg, colours)]
    L = route_len(conn_pos(unit, ref), DEV[dev], via)
    cable(cid, name, (unit, ref), (dev, dev_conn), ws, L, notes, columns=columns, twisted=twisted)


REAR = (489.5, -100.0, 420.0)      # rear cable channel at the column base
DECK = (500.0, -90.0, 392.0)       # deck pass-through TS2B-501 (470-512, -96..-68)

# --- power ---------------------------------------------------------------------------------------
cable('C01', '+12 V straps to column busbar (CPD-1 TS2B-232 -> TS2B-215)', ('CPD STRAP+', 'lug M8'), ('BUSBAR+', 'lug M8'),
      [('L1', 'L1', '+12V', '4/0', 'RED'), ('L2', 'L2', '+12V', '4/0', 'RED')],
      route_len(DEV['CPD STRAP+'], DEV['BUSBAR+']),
      '4/0 AWG fine-strand welding cable (Class K), 105 C; 2-hole compression lugs M8 both ends, 12 N m; heat shrink red',
      kind='power')
cable('C02', 'RTN straps to column busbar (CPD-1 TS2B-233 -> TS2B-216)', ('CPD STRAP-', 'lug M8'), ('BUSBAR-', 'lug M8'),
      [('L1', 'L1', 'RTN', '4/0', 'BLK'), ('L2', 'L2', 'RTN', '4/0', 'BLK')],
      route_len(DEV['CPD STRAP-'], DEV['BUSBAR-']), 'as C01, black heat shrink', kind='power')
cable('C03', 'RSP-750-12 output to TCD-1 studs', ('RSP-750-12', '+V/-V M4 TB'), ('TCD-1', 'T1-T4 M5'),
      [('+V', 'T1', '12V_IN', '10', 'RED'), ('+V', 'T2', '12V_IN', '10', 'RED'), ('-V', 'T3', 'GND', '10', 'BLK'),
       ('-V', 'T4', 'GND', '10', 'BLK')], route_len(DEV['RSP-750-12'], LOC['TCD-1'](12.5, 90.0)),
      '10 AWG UL1015 105 C; fork M4 at the supply, ring M5 at the studs (3 N m)', kind='power')
dev_cable('C04', 'RSP-750-12 output to CCM-1 J1 (12V_AUX)', 'CCM-1', 'J1', 'RSP-750-12',
          [('1', '+V'), ('2', '+V'), ('3', '-V'), ('4', '-V')], [18] * 4, ['RED', 'RED', 'BLK', 'BLK'],
          '18 AWG UL1007; fork M4 at the supply (shares the terminal with C03)', dev_conn='+V/-V M4 TB')
cable('C05', 'AC feed to RSP-750-12', ('ARM AC TB', 'TB1'), ('RSP-750-12', 'L/N/PE'),
      [('L', 'L', 'AC L', '14', 'BRN'), ('N', 'N', 'AC N', '14', 'BLU'), ('PE', 'PE', 'PE', '14', 'GRN/YEL')],
      route_len(DEV['ARM AC TB'], DEV['RSP-750-12']), '14 AWG UL1015 600 V; ferrules at the TB, fork at the supply',
      kind='power')
# --- column RS-485 chain: CCM-1 (master, terminated) -> TCD-1 -> CPD-1 -> CBP-L -> CBP-U (terminated) -----------
BUS = [('1', '1'), ('2', '2'), ('3', '3'), ('6', '6')]
BUSAWG = [24, 24, 22, 22]
BUSCOL = ['WHT/BLU', 'BLU', 'BLK', 'BLK']
board_cable('C10', 'Column bus: CCM-1 J4 -> TCD-1 J5', 'CCM-1', 'J4', 'TCD-1', 'J5', BUS, BUSAWG, BUSCOL,
            'A/B twisted pair (Belden 9841 class 120 ohm); pins 4/5 not carried', twisted=('1', '2'))
board_cable('C11', 'Column bus: TCD-1 J6 -> CPD-1 J6', 'TCD-1', 'J6', 'CPD-1', 'J6', BUS, BUSAWG, BUSCOL,
            'as C10', via=[(700.0, 0.0, 395.0)], twisted=('1', '2'))
board_cable('C12', 'Column bus: CPD-1 J8 -> CBP-8 lower J903', 'CPD-1', 'J8', 'CBP-L', 'J903', BUS, BUSAWG, BUSCOL,
            'as C10; ADDR strap S1 in the J903 plug', via=[DECK, REAR], twisted=('1', '2'))
board_cable('C13', 'Column bus: CBP-8 lower J904 -> CBP-8 upper J903', 'CBP-L', 'J904', 'CBP-U', 'J903', BUS, BUSAWG,
            BUSCOL, 'as C10; CBP-8 upper is the end node: fit R904 + JP901 on it', via=[REAR], twisted=('1', '2'))
board_cable('C14', 'SYS: CPD-1 J7 <-> CCM-1 J2 (standby power, PSON_REQ#, COL_PWR_OK)', 'CPD-1', 'J7', 'CCM-1', 'J2',
            [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')], [18, 18, 22, 18, 18, 22],
            ['RED', 'RED', 'ORN', 'BLK', 'BLK', 'GRN'], 'straight 1:1', via=[(700.0, 0.0, 395.0)])
# --- CCM-1 sensors and actuators -----------------------------------------------------------------
dev_cable('C20', 'SHT45 room T/RH sensor', 'CCM-1', 'J7', 'SHT45', [('1', 'VDD'), ('2', 'SDA'), ('3', 'SCL'), ('4', 'GND')],
          [24] * 4, ['RED', 'BLU', 'YEL', 'BLK'], 'shielded 4-core 24 AWG, shield to GND at CCM end only; max 1 m',
          via=[(640.0, 100.0, 420.0)], dev_conn='sensor pigtail')
dev_cable('C21', 'SDP810-500Pa coil differential pressure', 'CCM-1', 'J8', 'SDP810',
          [('1', 'VDD'), ('2', 'SDA'), ('3', 'SCL'), ('4', 'GND')], [24] * 4, ['RED', 'BLU', 'YEL', 'BLK'],
          'shielded 4-core; sensor end JST GH 4P (SDP8xx connector) [verify]; tubes 3/16 in ID to the coil taps',
          via=[(640.0, 100.0, 420.0)], dev_conn='JST GHR-04V-S [verify]')
for k, (ref, dev) in enumerate([('J9', 'NTC coolant supply'), ('J10', 'NTC coolant return'), ('J11', 'NTC room air'),
                                ('J12', 'NTC GPU inlet L'), ('J13', 'NTC GPU inlet U'), ('J14', 'NTC cold block')]):
    dev_cable('C%d' % (22 + k), dev + ' (CCM-1 %s)' % ref, 'CCM-1', ref, dev, [('1', 'A'), ('2', 'B')], [26, 26],
              ['WHT', 'WHT'], '10k B3950 probe, 2-core 26 AWG PTFE; butt-splice + heat shrink to the probe leads',
              via=[(640.0, 100.0, 420.0)] if 'cold' not in dev else (), dev_conn='probe leads')
for k, (ref, dev) in enumerate([('J15', 'Leak drip tray'), ('J16', 'Leak module floor')]):
    dev_cable('C%d' % (28 + k), dev + ' rope sensor leader', 'CCM-1', ref, dev, [('1', 'SENSE'), ('2', 'GND')],
              [24, 24], ['YEL', 'BLK'], 'leader to the rope sensor end connector (TraceTek TT1000 class) [verify]',
              dev_conn='rope leader')
for k, (ref, dev) in enumerate([('J17', 'Flow column supply'), ('J18', 'Flow pump loop')]):
    dev_cable('C%d' % (30 + k), dev + ' meter', 'CCM-1', ref, dev, [('1', '+V'), ('2', 'GND'), ('3', 'PULSE')],
              [24] * 3, ['RED', 'BLK', 'WHT'], 'Hall pulse meter, open collector (Gems FT-110 class) [verify]',
              dev_conn='meter pigtail')
dev_cable('C32', 'D5 pump (CCM-1 J19)', 'CCM-1', 'J19', 'D5 pump', [('1', '2'), ('2', '1'), ('3', '4'), ('4', '3')],
          [18, 18, 24, 24], ['YEL', 'BLK', 'BLU', 'GRN'],
          'adapter: Micro-Fit 2x2 -> 4-pin fan plug on the pump lead (1 GND, 2 +12 V, 3 tach, 4 PWM)',
          dev_conn='4-pin fan socket 47054-1000')
dev_cable('C33', 'Impeller 3 tach (column 3 only)', 'CCM-1', 'J20', 'Impeller 3', [('1', 'TACH'), ('2', 'GND')],
          [24, 24], ['WHT', 'BLK'], 'runs up the rear channel to the crown, P-clipped every 200 mm', via=[DECK, REAR,
                                                                                                         (489.5, -100.0, 1380.0)],
          columns='3', dev_conn='motor control lead (TMC-1 harness)')
dev_cable('C34', 'Light bar SK6812 (TS2B-212)', 'CCM-1', 'J21', 'Light bar', [('1', '+5V'), ('2', 'DIN'), ('3', 'GND')],
          [22, 24, 22], ['RED', 'GRN', 'BLK'], 'strip input pads soldered, strain relief at the TS2B-212 end cap',
          dev_conn='strip pads')
dev_cable('C35', 'Chiller interface (column 1 only) to the rear bulkhead', 'CCM-1', 'J22', 'Chiller bulkhead',
          [(str(i), str(i)) for i in range(1, 9)], [22] * 8,
          ['VIO', 'GRY', 'WHT', 'ORN', 'BLK', 'YEL', 'BLK', 'BLK'],
          'bulkhead M12 8-pin A-coded panel receptacle (1:1); chiller cable by site', columns='1',
          dev_conn='M12 8P A-coded panel [verify]')
dev_cable('C36', 'Door / latch switches (3 branches)', 'CCM-1', 'J23', 'Door switches',
          [('1', 'SW1'), ('2', 'SW2'), ('3', 'SW3'), ('4', 'COM')], [24] * 4, ['WHT', 'GRY', 'VIO', 'BLK'],
          'sealed micro-switches NO: SW1 arm service door, SW2 crown access (+1300 mm branch), SW3 coil latch; COM daisy',
          dev_conn='switch tabs 2.8 mm')
# --- CPD-1 sensors -------------------------------------------------------------------------------
dev_cable('C40', 'CPD-1 strap NTC', 'CPD-1', 'J9', 'NTC strap', [('1', 'A'), ('2', 'B')], [26, 26], ['WHT', 'WHT'],
          'ring-lug NTC (M6) under the stud 4 nut [verify part]', dev_conn='ring-lug NTC')
dev_cable('C41', 'CPD-1 arm inlet air NTC', 'CPD-1', 'J10', 'NTC arm inlet', [('1', 'A'), ('2', 'B')], [26, 26],
          ['WHT', 'WHT'], '10k B3950 probe', dev_conn='probe leads')
# --- TCD-1 ---------------------------------------------------------------------------------------
for k in range(4):
    dev_cable('C%d' % (50 + k), 'TEC %d (TCD-1 J%d)' % (k + 1, k + 1), 'TCD-1', 'J%d' % (k + 1), 'TEC %d' % (k + 1),
              [('1', '+'), ('2', '+'), ('3', '-'), ('4', '-')], [18] * 4, ['RED', 'RED', 'BLK', 'BLK'],
              '18 AWG, two conductors per pole (14 A); TEC leads butt-spliced (Molex 19164-0024 class) to the extension',
              dev_conn='TEC leads')
for k in range(2):
    dev_cable('C%d' % (54 + k), 'TEC hot-side NTC %d (TCD-1 J%d)' % (k + 1, 8 + k), 'TCD-1', 'J%d' % (8 + k),
              'NTC hot side %d' % (k + 1), [('1', 'A'), ('2', 'B')], [26, 26], ['WHT', 'WHT'],
              'NTC epoxied in the tower base plate, Arctic Silver class adhesive', dev_conn='probe leads')

# --- assemblies: GPU 12V-2x6 and MCIO (16 each per column) ---------------------------------------
GPU_PWR = []
for g, unit in enumerate(('CBP-L', 'CBP-U')):
    for i in range(8):
        k = i + 1
        a = conn_pos(unit, 'J%d03' % k)
        z = a[2]
        L = 150
        CABLES.append(dict(id='C%d' % (61 + 8 * g + i), name='GPU %s slot %d 12V-2x6 power' % (unit[-1], k),
                           a=(unit, 'J%d03' % k), b=('GPU %s%d' % (unit[-1], k), '12V-2x6'), wires=[], len=L,
                           notes='12V-2x6 to 12V-2x6, 12 x 16 AWG + 4 sense (SENSE0/1 to GND per CBP), 600 W class, '
                                 'PCI-SIG CEM 5.1 compliant cable assembly [verify MPN]', kind='assembly', cols='all',
                           twisted=()))
MCIO_STD = (500, 750, 1000, 1250, 1500, 1750, 2000, 2250)
# PCIe Gen4 loss budget at 8 GHz (Nyquist of 16 GT/s), bump to bump 28 dB.  Allocations are ESTIMATES (typical datasheet
# values) to be replaced by measured S-parameters on the first article.
LB = dict(host=3.5, mcio_conn=0.5, cem_conn=0.5, aic=8.0, bp_db_per_mm=0.024, budget=28.0)
CABLE_DB_PER_M = {30: 3.3, 28: 2.7, 26: 2.2}
import json   # noqa: E402
_hs = json.load(open(os.path.join(HERE, '..', 'boards', 'cbp8', 'build', 'hs-pairs.json')))
BP_LEN = {}
for r in _hs:
    BP_LEN[r['slot']] = max(BP_LEN.get(r['slot'], 0.0), r['len_p'])
LOSS = []
for g, unit in enumerate(('CBP-L', 'CBP-U')):
    for i in range(8):
        k = i + 1
        a = conn_pos(unit, 'J%d02' % k)
        card = 2 * g + i // 4
        port = i % 4
        host = (245.0 + 40.64 * card + 7.0, 20.0 + 20.0 * port, 190.0)
        need = route_len(a, host, via=[(a[0], -100.0, a[2]), (a[0], -100.0, 420.0), DECK])
        std = next((s for s in MCIO_STD if s >= need), MCIO_STD[-1])
        awg = 30 if std <= 1000 else (28 if std <= 1750 else 26)
        bp = BP_LEN.get(k, 230.0)
        loss = LB['host'] + 2 * LB['mcio_conn'] + CABLE_DB_PER_M[awg] * std / 1000.0 + LB['bp_db_per_mm'] * bp + \
            LB['cem_conn'] + LB['aic']
        LOSS.append((unit, k, std, awg, round(bp, 1), round(loss, 1), round(LB['budget'] - loss, 1)))
        CABLES.append(dict(id='C%d' % (81 + 8 * g + i), name='PCIe Gen4 x8 link: %s slot %d -> host switch card %d port %d'
                           % (unit, k, card + 1, port + 1), a=(unit, 'J%d02' % k),
                           b=('HOST', 'Rocket 1628A #%d MCIO %d' % (card + 1, port + 1)), wires=[], len=std,
                           notes='MCIO 8i (SFF-TA-1016) 74P straight-through, 85 ohm twinax %d AWG, %d mm (route needs %d mm); '
                                 'est. channel loss %.1f dB of 28 dB at 8 GHz; catalogue or build-to-length [verify MPN]'
                                 % (awg, std, need, loss), kind='assembly', cols='all', twisted=()))

# --- tower bus (per tower, W5xx) ------------------------------------------------------------------
W['n'] = 500
for k in range(4):
    a = 'HOST USB-RS485 (FTDI USB-RS485-WE class)' if k == 0 else 'CCM-1 column %d J6' % k
    CABLES.append(dict(id='T%02d' % (k + 1), name='Tower bus: %s -> CCM-1 column %d J5' % (a, k + 1), a=(a, ''),
                       b=('CCM-1 col %d' % (k + 1), 'J5'),
                       wires=[dict(no=wire_no(), fp=p, tp=p, sig=s, awg=w, col=c) for p, s, w, c in
                              (('1', 'TWR_A', 24, 'WHT/BLU'), ('2', 'TWR_B', 24, 'BLU'), ('3', 'GND', 22, 'BLK'))],
                       len=1600 if k else 900, notes='120 ohm twisted pair, through the hub; CCM-1 column 1 is not '
                                                     'terminated (host adapter end is)', kind='discrete', cols='tower',
                       twisted=('1', '2')))
CABLES.append(dict(id='T05', name='Tower bus: CCM-1 column 4 J6 -> TMC-1 RS-485 (end node, terminated)',
                   a=('CCM-1 col 4', 'J6'), b=('TMC-1', 'RS-485 port [per TMC-1 drawing]'),
                   wires=[dict(no=wire_no(), fp=p, tp=q, sig=s, awg=w, col=c) for p, q, s, w, c in
                          (('1', 'A', 'TWR_A', 24, 'WHT/BLU'), ('2', 'B', 'TWR_B', 24, 'BLU'), ('3', 'GND', 'GND', 22, 'BLK'))],
                   len=1500, notes='up the column 4 rear channel to the crown', kind='discrete', cols='tower', twisted=('1', '2')))
for k in range(4):
    CABLES.append(dict(id='A%02d' % (k + 1), name='AC cord CRPS %d' % (k + 1), a=('Column PDU', 'C19 outlet [verify]'),
                       b=('CRPS %d' % (k + 1), 'AC inlet'), wires=[], len=1000,
                       notes='IEC 60320 cord, 14 AWG, 15 A 250 V; inlet type per Murata D1U54T-W-2000 variant [verify]',
                       kind='assembly', cols='all', twisted=()))

# ------------------------------------------------------------------ strap table (address plugs)
STRAPS = [
    ('S1', 'CBP-8 lower J903 plug', 'ADDR0 (4) + ADDR1 (5) to GND (3)', 'group 0 -> Modbus 0x20 (0x20 + 2 ADDR1 + ADDR0)', 'all'),
    ('-', 'CBP-8 upper J903 plug', 'none (ADDR0 = ADDR1 = 1)', 'group 1 -> Modbus 0x23', 'all'),
    ('S2', 'CCM-1 J3 address plug', 'col 1: ADDR0 + ADDR1 to GND', 'tower address 0x40', '1'),
    ('S3', 'CCM-1 J3 address plug', 'col 2: ADDR1 to GND', 'tower address 0x41', '2'),
    ('S4', 'CCM-1 J3 address plug', 'col 3: ADDR0 to GND', 'tower address 0x42', '3'),
    ('-', 'CCM-1 J3 address plug', 'col 4: none', 'tower address 0x43', '4'),
    ('-', 'CPD-1 J6 / TCD-1 J5', 'none (fixed node types)', 'CPD-1 0x10, TCD-1 0x30', 'all'),
]
SITES = {'CBP-L': 'CBP-8 lower', 'CBP-U': 'CBP-8 upper'}


def ends(c):
    return '%s %s' % (SITES.get(c['a'][0], c['a'][0]), c['a'][1]), '%s %s' % (SITES.get(c['b'][0], c['b'][0]), c['b'][1])


# ------------------------------------------------------------------ outputs: CSV + XLSX
ROWS = []
for c in CABLES:
    fa, fb = ends(c)
    for w in c['wires']:
        ROWS.append([w['no'], c['id'], c['name'], fa, w['fp'], fb, w['tp'], w['sig'], w['awg'], w['col'], c['len'],
                     round(c['len'] / 25.4, 1), 'TP' if w['fp'] in c['twisted'] else '', c['cols']])
HDR = ['Wire', 'Cable', 'Cable name', 'From', 'From pin', 'To', 'To pin', 'Signal (board net)', 'AWG', 'Colour',
       'Length mm', 'Length in', 'Twist', 'Columns']
with open(os.path.join(OUT, 'TS2B-ELE-102_wire_list.csv'), 'w', newline='') as f:
    wr = csv.writer(f)
    wr.writerow(HDR)
    wr.writerows(ROWS)

CONNS = []
seen = set()
for c in CABLES:
    for unit, ref in (c['a'], c['b']):
        if unit in BOARD_OF and ref in B[BOARD_OF[unit]].byref and (unit, ref) not in seen:
            seen.add((unit, ref))
            p = B[BOARD_OF[unit]].byref[ref]
            hous, fam = mating(unit, ref)
            awgs = sorted({w['awg'] for w in c['wires']}, key=str)
            crimp = PH_CRIMP if fam == 'PH' else (', '.join(sorted({MF_CRIMP.get(a, '') for a in awgs if a in MF_CRIMP}))
                                                  if fam == 'MF' else '')
            CONNS.append([SITES.get(unit, unit), ref, p['value'], p['mpn'], hous, crimp, c['id'], p['desc']])

from openpyxl import Workbook   # noqa: E402
from openpyxl.styles import Font, PatternFill, Alignment   # noqa: E402
wb = Workbook()
ws = wb.active
ws.title = 'Cables'
ch = ['Cable', 'Name', 'From', 'To', 'Kind', 'Conductors', 'Length mm', 'Length in', 'Columns', 'Notes']
ws.append(ch)
for c in CABLES:
    fa, fb = ends(c)
    ws.append([c['id'], c['name'], fa, fb, c['kind'], len(c['wires']), c['len'], round(c['len'] / 25.4, 1), c['cols'],
               c['notes']])
ws2 = wb.create_sheet('Wire list')
ws2.append(HDR)
for r in ROWS:
    ws2.append(r)
ws3 = wb.create_sheet('Connector schedule')
ws3.append(['Unit', 'Board ref', 'Board part', 'Board MPN', 'Mating housing', 'Crimp', 'Cable', 'Function'])
for r in CONNS:
    ws3.append(r)
ws4 = wb.create_sheet('Address straps')
ws4.append(['Strap', 'Where', 'Wiring', 'Result', 'Columns'])
for r in STRAPS:
    ws4.append(list(r))
# harness materials
mat = {}
for c in CABLES:
    n = 1 if c['cols'] in ('tower',) or c['cols'] in ('1', '3') else 4
    if c['kind'] == 'assembly':
        key = ('assembly', c['notes'].split(',')[0][:80], c['len'])
        mat[key] = mat.get(key, 0) + n
        continue
    for w in c['wires']:
        key = ('wire', '%s AWG %s' % (w['awg'], w['col']), '')
        mat[key] = mat.get(key, 0) + n * c['len'] / 1000.0
ws6 = wb.create_sheet('Gen4 loss budget')
ws6.append(['Board', 'Slot', 'Cable mm', 'Cable AWG', 'Backplane lane max mm', 'Est. loss dB @ 8 GHz', 'Margin to 28 dB'])
for r in LOSS:
    ws6.append(list(r))
ws5 = wb.create_sheet('Harness BOM (tower)')
ws5.append(['Type', 'Item', 'Length mm (assemblies)', 'Qty / metres per tower (+10 % spare on wire)'])
for (t, item, L), q in sorted(mat.items(), key=lambda kv: (kv[0][0], str(kv[0][1]), str(kv[0][2]))):
    ws5.append([t, item, L, round(q * 1.1, 2) if t == 'wire' else q])
for sh in wb.worksheets:
    for cell in sh[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='1F3B57')
        cell.alignment = Alignment(wrap_text=True, vertical='top')
    for col in sh.columns:
        w = max(len(str(c.value or '')) for c in col)
        sh.column_dimensions[col[0].column_letter].width = min(60, max(8, w + 2))
    sh.freeze_panes = 'A2'
wb.save(os.path.join(OUT, 'TS2B-ELE-102_wire_list.xlsx'))
print('cables', len(CABLES), 'numbered wires', len([r for r in ROWS if r[0]]), 'connectors', len(CONNS))


# ------------------------------------------------------------------ drawings (matplotlib, A3 landscape, dual units)
import matplotlib   # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages   # noqa: E402
from matplotlib.patches import Rectangle, FancyBboxPatch   # noqa: E402

A3 = (420 / 25.4, 297 / 25.4)
COLMAP = {'RED': '#d62728', 'BLK': '#222222', 'BLU': '#1f5fbf', 'WHT/BLU': '#7fa7e0', 'WHT': '#9a9a9a', 'YEL': '#d4b000',
          'GRN': '#2ca02c', 'ORN': '#ff7f0e', 'BRN': '#8c564b', 'GRN/YEL': '#7a9a00', 'GRY': '#7f7f7f', 'VIO': '#9467bd'}


def frame(fig, dwg, title, sheet, nsheets):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 420)
    ax.set_ylim(0, 297)
    ax.axis('off')
    ax.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=1.0))
    # title block 180 x 32 lower right
    x0, y0 = 230, 10
    ax.add_patch(Rectangle((x0, y0), 180, 32, fill=False, lw=0.8))
    for yy in (18, 26):
        ax.plot([x0, x0 + 180], [y0 + yy - 10 + 2, y0 + yy - 10 + 2], lw=0.4, color='k') if False else None
    ax.plot([x0, x0 + 180], [y0 + 12, y0 + 12], lw=0.5, color='k')
    ax.plot([x0, x0 + 180], [y0 + 22, y0 + 22], lw=0.5, color='k')
    ax.plot([x0 + 120, x0 + 120], [y0, y0 + 22], lw=0.5, color='k')
    ax.text(x0 + 3, y0 + 26, 'TS-2 rev B  GPU tower', fontsize=9, weight='bold', va='center')
    ax.text(x0 + 3, y0 + 17, title, fontsize=7.5, va='center')
    ax.text(x0 + 3, y0 + 6, 'Lengths mm [in].  AWG per UL 1007/1015 unless noted.  Generated by harness/gen_harness.py',
            fontsize=5, va='center')
    ax.text(x0 + 123, y0 + 17, dwg, fontsize=8, weight='bold', va='center')
    ax.text(x0 + 123, y0 + 6, 'rev A   sheet %d / %d   2026-11-24' % (sheet, nsheets), fontsize=6, va='center')
    ax.text(15, 280, 'MACHINE-GENERATED  -  REVIEW BEFORE RELEASE', fontsize=6, color='#b00')
    return ax


def unit_box(ax, x, y, w, h, title, sub='', fc='#eef3f8'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.4,rounding_size=1.5', fc=fc, ec='#1F3B57', lw=0.9))
    ax.text(x + 2, y + h - 3.5, title, fontsize=7, weight='bold', va='center')
    if sub:
        ax.text(x + 2, y + h - 7.5, sub, fontsize=4.6, va='center', color='#333')


def overview(pdf, nsheets):
    fig = plt.figure(figsize=A3)
    ax = frame(fig, 'TS2B-ELE-101', 'Column wiring schematic - overview (one column; four per tower)', 1, nsheets)
    U = {
        'CBP-U': (40, 205, 80, 50, 'CBP-8 upper (slots 9-16)', 'J903/J904 bus, J*02 MCIO x8, J*03 12V-2x6 x8, T1-T4 studs'),
        'CBP-L': (40, 135, 80, 50, 'CBP-8 lower (slots 1-8)', 'J903/J904 bus, J*02 MCIO x8, J*03 12V-2x6 x8, T1-T4 studs'),
        'BUS': (140, 135, 36, 120, 'Busbars TS2B-215/216', '+12 V / RTN 14 x 10 C11000'),
        'HOST': (40, 60, 80, 50, 'Host node (arm)', 'ROMED8-2T, 4 x Rocket 1628A (16 MCIO)'),
        'CPD-1': (200, 135, 60, 50, 'CPD-1 column power', '4 x CRPS 2000 W, J6/J8 bus, J7 SYS, J9/J10 NTC'),
        'CCM-1': (300, 185, 70, 70, 'CCM-1 cooling controller', 'J1 12V_AUX, J2 SYS, J3 addr, J4 col bus, J5/J6 tower bus,\n'
                  'J7-J23 sensors, pump, chiller, light bar, switches'),
        'TCD-1': (300, 100, 70, 60, 'TCD-1 Peltier driver', 'T1-T4 12 V studs, J1-J4 TEC, J5/J6 bus, J8/J9 NTC, J11/J12 fans'),
        'RSP': (200, 60, 60, 40, 'RSP-750-12 (arm)', '12 V 62.5 A AC-DC, live with AC'),
        'GPU': (40, 262, 80, 16, 'GPUs x16 (RTX PRO 6000 Max-Q)', ''),
        'DEV': (383, 100, 24, 155, 'Field', 'sensors\npump\nTECs\nfans\nswitches\nlight bar\nchiller'),
    }
    for k, (x, y, w, h, t, s) in U.items():
        unit_box(ax, x, y, w, h, t, s)
    def link(p, q, lab, col='#1F3B57', lw=1.0, ls='-'):
        (x1, y1), (x2, y2) = p, q
        xm = (x1 + x2) / 2
        ax.plot([x1, xm, xm, x2], [y1, y1, y2, y2], color=col, lw=lw, ls=ls)
        ax.text(xm + 1, (y1 + y2) / 2, lab, fontsize=4.8, color=col, va='center',
                bbox=dict(fc='white', ec='none', pad=0.3))
    byid = {c['id']: c for c in CABLES}

    def L(cid):
        c = byid[cid]
        return '%s %s  %d mm [%.1f in]' % (cid, ('%s-%s' % (c['wires'][0]['no'], c['wires'][-1]['no'])) if c['wires'] and c['wires'][0]['no'] else '', c['len'], c['len'] / 25.4)
    link((176, 200), (200, 170), 'C01/C02  2 x 4/0 AWG per pole', COLMAP['RED'], 2.0)
    link((120, 230), (140, 230), 'CBP-U T1-T4 bolted', COLMAP['RED'], 2.0)
    link((120, 160), (140, 160), 'CBP-L T1-T4 bolted', COLMAP['RED'], 2.0)
    link((80, 255), (80, 262), '', COLMAP['RED'], 1.5)
    ax.text(82, 258.5, 'C61-C76  12V-2x6 x16, 600 W', fontsize=4.8, color=COLMAP['RED'])
    link((60, 135), (60, 110), '', '#555', 1.5)
    ax.text(62, 122, 'C81-C96  MCIO 8i x16\nPCIe Gen4 x8 (0.5-1.5 m)', fontsize=4.8, color='#555')
    link((60, 205), (60, 185), '', '#1f5fbf', 1.0, '--')
    ax.text(62, 195, L('C13'), fontsize=4.6, color='#1f5fbf')
    link((200, 150), (120, 145), L('C12'), '#1f5fbf', 1.0, '--')
    link((300, 120), (260, 145), L('C11'), '#1f5fbf', 1.0, '--')
    link((300, 195), (335, 160), L('C10'), '#1f5fbf', 1.0, '--')
    link((260, 175), (300, 225), L('C14') + '  SYS: VSB, PSON_REQ#, PWR_OK', COLMAP['ORN'], 1.2)
    link((260, 80), (300, 110), L('C03') + '  10 AWG x4', COLMAP['RED'], 2.0)
    link((260, 90), (300, 245), L('C04') + '  12V_AUX', COLMAP['RED'], 1.0)
    link((230, 60), (230, 40), 'C05  AC L/N/PE 14 AWG', COLMAP['BRN'], 1.0)
    link((370, 220), (385, 220), 'C20-C36', '#2ca02c', 1.0)
    link((370, 130), (385, 130), 'C50-C55, fans', '#2ca02c', 1.0)
    link((370, 250), (395, 270), 'T01-T05 tower bus (sheet %d)' % nsheets, '#9467bd', 1.0, ':')
    ax.text(15, 40, 'Notes\n1  Column RS-485 chain: CCM-1 (master, terminated) - TCD-1 - CPD-1 - CBP-8 lower - CBP-8 upper (terminated: fit R904 + JP901).\n'
            '2  Address straps live in the plugs (TS2B-ELE-102, sheet "Address straps").  Pins 4/5 are never carried between nodes.\n'
            '3  Power-on interlock: CCM-1 pulls PSON_REQ# (C14) low only after flow, coolant temperature, leak and door checks pass.\n'
            '4  Every conductor carries a heat-shrink label "<W-no>-C<column>" at both ends, 20 mm from the contact.\n'
            '5  Pin-to-pin wiring of every discrete cable: sheets 2-%d.  Full wire list with lengths: TS2B-ELE-102.' % (nsheets - 1),
            fontsize=5.5, va='bottom')
    pdf.savefig(fig)
    plt.close(fig)


def cable_block(ax, x, y, c):
    """pin table left, wires, pin table right; returns height used"""
    n = len(c['wires'])
    rh = 4.2
    h = 15 + n * rh
    fa, fb = ends(c)
    ax.add_patch(Rectangle((x, y - h), 190, h, fill=False, lw=0.4, ec='#999'))
    ax.text(x + 2, y - 4, '%s  %s' % (c['id'], c['name']), fontsize=5.8, weight='bold', va='center')
    ax.text(x + 2, y - 8.5, '%d mm [%.1f in]   columns: %s   %s' % (c['len'], c['len'] / 25.4, c['cols'], c['notes'][:120]),
            fontsize=3.8, va='center', color='#333')
    tx0, tx1 = x + 4, x + 142
    ax.text(tx0, y - 12.5, fa, fontsize=4.2, weight='bold', va='center')
    ax.text(tx1, y - 12.5, fb, fontsize=4.2, weight='bold', va='center')
    for k, w in enumerate(c['wires']):
        yy = y - 16 - k * rh
        ax.add_patch(Rectangle((tx0, yy - 1.8), 8, 3.6, fill=False, lw=0.4))
        ax.text(tx0 + 4, yy, w['fp'], fontsize=4.2, ha='center', va='center')
        ax.text(tx0 + 10, yy, str(w['sig'])[:22], fontsize=4.0, va='center')
        ax.add_patch(Rectangle((tx1 + 28, yy - 1.8), 8, 3.6, fill=False, lw=0.4))
        ax.text(tx1 + 32, yy, w['tp'], fontsize=4.2, ha='center', va='center')
        col = COLMAP.get(w['col'], '#444')
        ax.plot([tx0 + 46, tx1 + 26], [yy, yy], color=col, lw=1.1 if str(w['awg']) not in ('4/0', '10') else 2.4)
        ax.text((tx0 + tx1) / 2 + 8, yy + 1.1, '%s  %s AWG  %s' % (w['no'], w['awg'], w['col']), fontsize=4.0,
                ha='center', va='bottom', bbox=dict(fc='white', ec='none', pad=0.2))
        if w['fp'] in c['twisted']:
            ax.text(tx1 + 2, yy - 2.1, 'twisted pair', fontsize=3.4, color='#1f5fbf')
    return h + 3


def wiring_sheets(pdf, sheet0, nsheets):
    disc = [c for c in CABLES if c['wires'] and not c['id'].startswith('T')]
    sheet = sheet0
    i = 0
    while i < len(disc):
        fig = plt.figure(figsize=A3)
        ax = frame(fig, 'TS2B-ELE-101', 'Column wiring - pin-to-pin, cables %s onward' % disc[i]['id'], sheet, nsheets)
        for colx in (14, 214):
            y = 276
            while i < len(disc):
                need = 15 + len(disc[i]['wires']) * 4.2
                ylim = 46 if colx > 200 else 14
                if y - need < ylim:
                    break
                y -= cable_block(ax, colx, y, disc[i])
                i += 1
        pdf.savefig(fig)
        plt.close(fig)
        sheet += 1
    return sheet


def tower_sheet(pdf, sheet, nsheets):
    fig = plt.figure(figsize=A3)
    ax = frame(fig, 'TS2B-ELE-101', 'Tower RS-485 bus and AC cords', sheet, nsheets)
    y = 276
    for c in CABLES:
        if c['id'].startswith('T'):
            y -= cable_block(ax, 14, y, c)
    ac = [c for c in CABLES if c['id'].startswith('A')]
    ax.text(214, 270, 'AC cords per column (assemblies)', fontsize=7, weight='bold')
    for k, c in enumerate(ac):
        ax.text(214, 262 - 6 * k, '%s  %s: %s -> %s, %d mm [%.1f in]' % (c['id'], c['name'], c['a'][1], c['b'][1], c['len'],
                                                                       c['len'] / 25.4), fontsize=5)
    ax.text(214, 225, 'Assemblies per column (no individual wire numbers)', fontsize=7, weight='bold')
    rows = [c for c in CABLES if c['kind'] == 'assembly' and c['id'][0] == 'C']
    for k, c in enumerate(rows):
        ax.text(214, 218 - 4.1 * k, '%s  %s  %d mm [%.1f in]' % (c['id'], c['name'][:70], c['len'], c['len'] / 25.4),
                fontsize=4.2)
    pdf.savefig(fig)
    plt.close(fig)


def wirelist_pdf():
    path = os.path.join(OUT, 'TS2B-ELE-102_wire_list.pdf')
    per = 52
    pages = (len(ROWS) + per - 1) // per
    with PdfPages(path) as pdf:
        for p in range(pages):
            fig = plt.figure(figsize=A3)
            ax = frame(fig, 'TS2B-ELE-102', 'Wire list (every conductor numbered)', p + 1, pages)
            cols = [('Wire', 14), ('Cable', 12), ('From', 52), ('Pin', 10), ('To', 62), ('Pin', 12), ('Signal', 44),
                    ('AWG', 10), ('Colour', 16), ('mm', 12), ('in', 12), ('TP', 8), ('Col', 10)]
            idx = [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
            x = 14
            y = 270
            for (hname, w) in cols:
                ax.text(x, y, hname, fontsize=5.5, weight='bold')
                x += w * 1.33
            ax.plot([14, 406], [y - 2, y - 2], lw=0.5, color='k')
            for r in ROWS[p * per:(p + 1) * per]:
                y -= 4.3
                x = 14
                for (hname, w), j in zip(cols, idx):
                    ax.text(x, y, str(r[j])[:int(w * 0.9)], fontsize=4.6)
                    x += w * 1.33
            pdf.savefig(fig)
            plt.close(fig)
    return path


disc_n = len([c for c in CABLES if c['wires'] and not c['id'].startswith('T')])
# dry run to count sheets
_tmp = os.path.join(OUT, '_count.pdf')
with PdfPages(_tmp) as pdf:
    end = wiring_sheets(pdf, 2, 0)
os.remove(_tmp)
NS = end   # overview + wiring sheets (2..end-1) + tower sheet
with PdfPages(os.path.join(OUT, 'TS2B-ELE-101_harness_schematic.pdf')) as pdf:
    overview(pdf, NS)
    s = wiring_sheets(pdf, 2, NS)
    tower_sheet(pdf, s, NS)
print('ELE-101 sheets', NS, '->', wirelist_pdf())
