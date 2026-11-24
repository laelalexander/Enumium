"""kgen core: one design table per board drives schematic, netlist check, PCB, fab package and BOM.

A board's design.py builds a Design object:

    D = Design('cbp8', 'TS-2 rev B CBP-8 GPU backplane', rev='A', w=268.0, h=434.4, layers=8)
    D.sheet('Slot 1')                       # following parts go on this schematic sheet
    D.P('U1', 'Lib:Sym', 'value', 'FpLib:Fp', mpn, mfr, supplier_pn, {'1': 'NET', ...}, desc)

Conventions
  * Board coordinates are board-local mm, origin at the lower-left corner seen from the TOP (F side),
    x right, y up.  KiCad page coordinates are (X0 + x, Y0 + H - y).
  * Every pin of every symbol must appear in the pin map ({pin: net} or {pin: None} for no-connect),
    except pins the library marks no_connect.  The schematic generator refuses to run otherwise.
  * Supplier part numbers that were not checked on a live distributor page carry '[verify]'.
"""
import os

KGEN = os.path.dirname(os.path.abspath(__file__))
LIBNAME = 'ts2b'                     # project-local symbol + footprint library shared by all rev B boards
LIBSYM = os.path.join(KGEN, 'lib', LIBNAME + '.kicad_sym')
LIBFP = os.path.join(KGEN, 'lib', LIBNAME + '.pretty')

R0402 = 'Resistor_SMD:R_0402_1005Metric'
R0603 = 'Resistor_SMD:R_0603_1608Metric'
R1206 = 'Resistor_SMD:R_1206_3216Metric'
R2512 = 'Resistor_SMD:R_2512_6332Metric'
C0402 = 'Capacitor_SMD:C_0402_1005Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C0805 = 'Capacitor_SMD:C_0805_2012Metric'
C1206 = 'Capacitor_SMD:C_1206_3216Metric'
C1210 = 'Capacitor_SMD:C_1210_3225Metric'

# value -> (MPN, Digi-Key PN).  UNI-ROYAL 0603 1 % thick film; Digi-Key numbers marked [verify].
RES = {
    '0': ('0603WAF0000T5E', 'C21189'), '10': ('0603WAF100JT5E', 'C22859'), '22': ('0603WAF220JT5E', 'C23345'),
    '33': ('0603WAF330JT5E', 'C23140'), '100': ('0603WAF1000T5E', 'C22775'), '120': ('0603WAF1200T5E', 'C22787'),
    '330': ('0603WAF3300T5E', 'C23138'), '470': ('0603WAF4700T5E', 'C23179'), '820': ('0603WAF8200T5E', 'C23253'),
    '1k': ('0603WAF1001T5E', 'C21190'), '1.5k': ('0603WAF1501T5E', 'C22843'), '2.2k': ('0603WAF2201T5E', 'C4190'),
    '3.3k': ('0603WAF3301T5E', 'C22978'), '4.7k': ('0603WAF4701T5E', 'C23162'), '5.1k': ('0603WAF5101T5E', 'C23186'),
    '6.8k': ('0603WAF6801T5E', 'C23212'), '10k': ('0603WAF1002T5E', 'C25804'), '13.7k': ('0603WAF1372T5E', 'C22959'),
    '15k': ('0603WAF1502T5E', 'C22809'), '20k': ('0603WAF2002T5E', 'C4184'), '22k': ('0603WAF2202T5E', 'C31850'),
    '27k': ('0603WAF2702T5E', 'C22967'), '33k': ('0603WAF3302T5E', 'C4216'), '45.3k': ('0603WAF4532T5E', 'C23185'),
    '47k': ('0603WAF4702T5E', 'C25819'), '51k': ('0603WAF5102T5E', 'C23196'), '68k': ('0603WAF6802T5E', 'C23231'),
    '100k': ('0603WAF1003T5E', 'C25803'), '120k': ('0603WAF1203T5E', 'C25808'), '150k': ('0603WAF1503T5E', 'C22807'),
    '180k': ('0603WAF1803T5E', 'C22827'), '200k': ('0603WAF2003T5E', 'C25811'), '1M': ('0603WAF1004T5E', 'C22935'),
}
# value -> (footprint, MPN, manufacturer, LCSC, description)
CAPS = {
    '10n': (C0603, 'CL10B103KB8NNNC', 'Samsung Electro-Mechanics', 'C57112', 'MLCC 10 nF 50 V X7R 0603'),
    '22n': (C0603, 'CL10B223KB8NNNC', 'Samsung Electro-Mechanics', 'C21122', 'MLCC 22 nF 50 V X7R 0603'),
    '100n': (C0603, 'CL10B104KB8NNNC', 'Samsung Electro-Mechanics', 'C1591', 'MLCC 100 nF 50 V X7R 0603'),
    '220n': (C0603, 'CL10B224KO8NNNC', 'Samsung Electro-Mechanics', 'C21120', 'MLCC 220 nF 16 V X7R 0603'),
    '1u': (C0603, 'CL10A105KA8NNNC', 'Samsung Electro-Mechanics', 'C15849', 'MLCC 1 uF 25 V X5R 0603'),
    '2.2u': (C0603, 'CL10A225KO8NNNC', 'Samsung Electro-Mechanics', 'C23630', 'MLCC 2.2 uF 16 V X5R 0603'),
    '4.7u': (C0603, 'CL10A475KO8NNNC', 'Samsung Electro-Mechanics', 'C19666', 'MLCC 4.7 uF 16 V X5R 0603'),
    '10u': (C0805, 'CL21A106KAYNNNE', 'Samsung Electro-Mechanics', 'C15850', 'MLCC 10 uF 25 V X5R 0805'),
    '22u': (C0805, 'CL21A226MAQNNNE', 'Samsung Electro-Mechanics', 'C45783', 'MLCC 22 uF 25 V X5R 0805'),
    '22u25': (C1206, 'CL31A226KAHNNNE', 'Samsung Electro-Mechanics', 'C12891', 'MLCC 22 uF 25 V X5R 1206'),
    '47u': (C1210, 'GRM32ER61C476KE15L', 'Murata', 'C77101', 'MLCC 47 uF 16 V X5R 1210'),
    '100u': (C1210, 'GRM32ER60J107ME20L', 'Murata', 'C88302', 'MLCC 100 uF 6.3 V X5R 1210'),
    '10u50': (C1206, 'GRM31CR61H106KA12L', 'Murata', 'C13585', 'MLCC 10 uF 50 V X5R 1206'),
}


class Design:
    def __init__(self, project, title, rev, w, h, layers=2, thickness=1.6, corner_r=3.0):
        self.project = project
        self.title = title
        self.rev = rev
        self.W, self.H = w, h
        self.layers = layers
        self.thickness = thickness
        self.corner_r = corner_r
        self.X0, self.Y0 = 50.0, 50.0
        self.parts = []
        self.byref = {}
        self.sheets = []           # [(name, [refs])]
        self._sheet = None
        self.notes = []            # schematic notes per sheet {sheet: [text]}
        self.sheet_notes = {}
        self.pwr_flags = []
        self.netclasses = {}       # name -> dict(nets=[...], width, clearance, [diff=(w, gap)])
        self.signal_width = 0.2
        self.signal_clearance = 0.2
        self.place = {}            # ref -> (x, y, rot[, side])
        self.regions = []          # [((x0, y0, x1, y1), [refs], side)]
        self.pack_gap = 1.0
        self.pack_rot = {}
        self.keepouts = []         # dict(name, rect|circle, layers)
        self.pours = []            # dict(net, layer, rect=(x0,y0,x1,y1) or poly=[...], prio)
        self.prerouted = []        # dict(net, layer, pts=[(x,y)...], width)  or via dict(net, at, drill, dia)
        self.silk = []
        self.holes = []
        self.stackup = None
        self.fab = {}              # fab notes key -> value
        self.test_notes = []
        self.route_layers = None   # copper layers freerouting may use (None = all signal layers)
        self.no_stitch = ()
        self.stitch = None         # dict(net='GND', pitch=5.0)

    # ------------------------------------------------------------------ table
    def sheet(self, name, notes=None):
        self._sheet = name
        if name not in [s[0] for s in self.sheets]:
            self.sheets.append((name, []))
        if notes:
            self.sheet_notes.setdefault(name, []).extend(notes)

    def P(self, ref, sym, value, fp, mpn, mfr, spn, pins, desc='', bom=True, pos=True, side='F', price=0.0, dnp=False,
          lcsc=''):
        assert ref not in self.byref, 'duplicate ref ' + ref
        assert self._sheet, 'call sheet() first'
        p = dict(ref=ref, sym=sym, value=value, fp=fp, mpn=mpn, mfr=mfr, spn=spn, lcsc=lcsc, pins=pins, desc=desc,
                 bom=bom, pos=pos, side=side, price=price, dnp=dnp, sheet=self._sheet)
        self.parts.append(p)
        self.byref[ref] = p
        [s for s in self.sheets if s[0] == self._sheet][0][1].append(ref)
        return p

    def R(self, ref, val, a, b, desc='', fp=R0603, side='F', dnp=False):
        mpn, lcsc = RES[val]
        if fp != R0603:
            mpn = mpn + ' [size: %s]' % fp.split(':')[1].split('_')[1]
        return self.P(ref, 'Device:R', val, fp, mpn, 'UNI-ROYAL', '', {'1': a, '2': b},
                      desc or 'Resistor %s 1%% 0603' % val, side=side, price=0.002, dnp=dnp, lcsc=lcsc)

    def C(self, ref, val, a, b, desc='', side='F', dnp=False):
        fp, mpn, mfr, lcsc, d = CAPS[val]
        return self.P(ref, 'Device:C', val.replace('u50', 'u/50V').replace('u25', 'u/25V'), fp, mpn, mfr, '',
                      {'1': a, '2': b}, desc or d, side=side, price=0.01 if fp == C0603 else 0.06, dnp=dnp, lcsc=lcsc)

    def TP(self, ref, net, side='F'):
        return self.P(ref, 'Connector:TestPoint', net, 'TestPoint:TestPoint_Pad_D1.5mm', '', '', '', {'1': net},
                      'Test point, bare pad d1.5 (no part)', bom=False, pos=False, side=side)

    def HOLE(self, ref, x, y, net='GND', fp='MountingHole:MountingHole_3.2mm_M3_Pad_Via', desc='M3 plated, bonded to GND'):
        self.P(ref, 'Mechanical:MountingHole_Pad', 'M3', fp, '', '', '', {'1': net},
               'Mounting hole ' + desc, bom=False, pos=False)
        self.place[ref] = (x, y, 0)
        self.holes.append((x, y))

    # ------------------------------------------------------------------ queries
    def expected_nets(self):
        nets = {}
        for p in self.parts:
            for pin, net in p['pins'].items():
                if net is not None:
                    nets.setdefault(net, set()).add((p['ref'], pin))
        return nets

    def single_pin_nets(self):
        return sorted(n for n, s in self.expected_nets().items() if len(s) == 1)


def board_dir(project):
    return os.path.join(os.path.dirname(KGEN), 'boards', project)
