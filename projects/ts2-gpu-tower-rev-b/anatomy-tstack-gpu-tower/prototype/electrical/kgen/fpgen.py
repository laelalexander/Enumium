"""Project-local footprints (KiCad 7 .kicad_mod) for the TS-2 rev B boards.

Every footprint here states its source.  Where the vendor drawing was not read in this pass, the footprint is
flagged VERIFY in its description and in docs/part-verification.md, and the fab notes require a check of the
land pattern against the vendor PCB layout before release.  Geometry is parametric so a correction is one number.
"""
import os
from core import LIBFP

FPS = {}


def _f(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


class FP:
    def __init__(self, name, desc, tags='', smd=True):
        self.name = name
        self.desc = desc
        self.tags = tags
        self.smd = smd
        self.items = []

    def pad(self, num, kind, shape, x, y, w, h, drill=None, layers=None, rr=0.25, rot=0):
        if kind == 'smd':
            layers = layers or '"F.Cu" "F.Paste" "F.Mask"'
            extra = ''
        elif kind == 'thru_hole':
            layers = layers or '"*.Cu" "*.Mask"'
            extra = ' (drill %s)' % _f(drill)
        else:   # np_thru_hole
            layers = layers or '"*.Cu" "*.Mask"'
            extra = ' (drill %s)' % _f(drill)
        rrs = ' (roundrect_rratio %s)' % _f(rr) if shape == 'roundrect' else ''
        self.items.append('  (pad "%s" %s %s (at %s %s%s) (size %s %s)%s (layers %s)%s)' % (
            num, kind, shape, _f(x), _f(y), (' %s' % _f(rot)) if rot else '', _f(w), _f(h), extra, layers, rrs))

    def line(self, x1, y1, x2, y2, layer, w=0.12):
        self.items.append('  (fp_line (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "%s"))' % (
            _f(x1), _f(y1), _f(x2), _f(y2), _f(w), layer))

    def rect(self, x1, y1, x2, y2, layer, w=0.12):
        for a, b in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
            self.line(a[0], a[1], b[0], b[1], layer, w)

    def circle(self, x, y, r, layer, w=0.12):
        self.items.append('  (fp_circle (center %s %s) (end %s %s) (stroke (width %s) (type solid)) (fill none) (layer "%s"))'
                          % (_f(x), _f(y), _f(x + r), _f(y), _f(w), layer))

    def text(self, kind, txt, x, y, layer, size=1.0, hide=False):
        self.items.append('  (fp_text %s "%s" (at %s %s) (layer "%s")%s (effects (font (size %s %s) (thickness %s))))' % (
            kind, txt, _f(x), _f(y), layer, ' hide' if hide else '', _f(size), _f(size), _f(size * 0.15)))

    def body(self, x1, y1, x2, y2, pin1=None, crt=0.25, silk=True, courtyard=True):
        """fab outline, courtyard (+crt), silk outline (+0.11) and a pin-1 marker"""
        self.rect(x1, y1, x2, y2, 'F.Fab', 0.1)
        if courtyard:
            self.rect(x1 - crt, y1 - crt, x2 + crt, y2 + crt, 'F.CrtYd', 0.05)
        if silk:
            self.rect(x1 - 0.11, y1 - 0.11, x2 + 0.11, y2 + 0.11, 'F.SilkS', 0.12)
        if pin1:
            self.circle(pin1[0], pin1[1], 0.3, 'F.SilkS', 0.25)
        self.text('reference', 'REF**', (x1 + x2) / 2, y1 - 1.2, 'F.SilkS', 1.0)
        self.text('value', self.name, (x1 + x2) / 2, y2 + 1.2, 'F.Fab', 1.0)
        self.text('user', '${REFERENCE}', (x1 + x2) / 2, (y1 + y2) / 2, 'F.Fab', 0.8)

    def dump(self):
        attr = '(attr smd)' if self.smd else '(attr through_hole)'
        out = ['(footprint "%s" (version 20221018) (generator kgen)' % self.name,
               '  (layer "F.Cu")', '  (descr "%s")' % self.desc.replace('"', "'"), '  (tags "%s")' % self.tags,
               '  ' + attr]
        out += self.items
        out.append(')')
        return '\n'.join(out) + '\n'


# ------------------------------------------------------------------ PCIe x16 CEM slot, vertical SMT
# TE Connectivity PCIe Gen5 CEM, vertical SMT, 164P, 1.00 mm pitch (TE PCIe Gen5 flyer 09/22: 2364427-4 family).
# Pin 1 to 11, key, pin 12 to 82 (PCI-SIG CEM).  Key: pin 11 to pin 12 = 3.30 mm (card edge drawing, 11.65 key centre).
# Row B (component side of the card) at -y (toward the MCIO, i.e. board +z), row A at +y.  VERIFY: row spacing
# 7.70 mm, pad 0.60 x 2.00, peg holes, hold-down tabs - against TE customer drawing 2364427 before release.
CEM_ROW = 3.85
CEM_PAD = (0.60, 2.00)


def cem_x(n):
    """x of pin n (A or B) relative to footprint origin (centre of the 1..82 span)"""
    x = (n - 1) * 1.0 if n <= 11 else 13.30 + (n - 12) * 1.0
    return x - 41.65


def cem_x16():
    f = FP('TE_2364427_PCIe_x16_Vertical_SMT', 'PCIe CEM x16 (164P 1.00 mm) vertical SMT slot, TE 2364427-4 family '
           '(PCIe Gen5 32 GT/s, 85 ohm). VERIFY land pattern vs TE drawing.', 'pcie cem x16 smt gen5')
    for n in range(1, 83):
        f.pad('A%d' % n, 'smd', 'roundrect', cem_x(n), CEM_ROW, *CEM_PAD)
        f.pad('B%d' % n, 'smd', 'roundrect', cem_x(n), -CEM_ROW, *CEM_PAD)
    for x in (-47.4, 47.4):
        f.pad('', 'np_thru_hole', 'circle', x, 0.0, 2.35, 2.35, drill=2.35)
    x0, x1 = -46.25, 51.75          # body 98.0 long incl. the retention latch end
    f.body(x0, -3.8, x1, 3.8, pin1=(cem_x(1) - 1.2, CEM_ROW + 1.6), crt=1.4, silk=False)
    f.line(x0, -3.91, x0, 3.91, 'F.SilkS')
    f.line(x1, -3.91, x1, 3.91, 'F.SilkS')
    f.text('user', 'B1', cem_x(1), -CEM_ROW - 1.9, 'F.Fab', 0.6)
    f.text('user', 'A1', cem_x(1), CEM_ROW + 1.9, 'F.Fab', 0.6)
    f.text('user', 'KEY', (cem_x(11) + cem_x(12)) / 2, 0, 'F.Fab', 0.6)
    return f


# ------------------------------------------------------------------ MCIO 8i right angle SMT
# Amphenol G97R22332HR, 74 positions, 0.60 mm pitch (Digi-Key listing).  Rows A (nearer the body) and B, numbered
# 1..37 along +x.  Mating face toward +y (cable exits +y).  VERIFY pad rows, tabs and pegs vs Amphenol drawing.
MCIO_ROW_A = -6.0
MCIO_ROW_B = -8.0
MCIO_PAD = (0.35, 1.30)


def mcio_x(n):
    return (n - 19) * 0.60


def mcio():
    f = FP('Amphenol_G97R22332HR_MCIO_8i_RA_SMT', 'MCIO 8i 74P 0.60 mm right-angle SMT receptacle, Amphenol G97R22332HR '
           '(SFF-TA-1016). VERIFY land pattern vs Amphenol drawing.', 'mcio sff-ta-1016 pcie smt')
    for n in range(1, 38):
        f.pad('A%d' % n, 'smd', 'roundrect', mcio_x(n), MCIO_ROW_A, *MCIO_PAD)
        f.pad('B%d' % n, 'smd', 'roundrect', mcio_x(n), MCIO_ROW_B, *MCIO_PAD)
    for x in (-13.0, 13.0):
        f.pad('MP', 'smd', 'roundrect', x, -3.5, 2.0, 3.2)
    for x in (-11.0, 11.0):
        f.pad('', 'np_thru_hole', 'circle', x, -1.5, 1.10, 1.10, drill=1.10)
    f.body(-12.0, -5.0, 12.0, 4.6, pin1=(mcio_x(1) - 0.5, MCIO_ROW_B - 1.3), crt=0.5, silk=False, courtyard=False)
    f.rect(-14.25, -9.15, 14.25, 5.1, 'F.CrtYd', 0.05)
    f.line(-12.11, 4.71, 12.11, 4.71, 'F.SilkS')
    f.text('user', 'CABLE', 0, 3.5, 'F.Fab', 0.8)
    return f


# ------------------------------------------------------------------ 12V-2x6 right-angle header
# Amphenol Minitek Pwr 10160920-1240100LF (RS 236-8779): 2 x 6 power at 3.00 mm, 4 sideband, RA THT.
# VERIFY: sideband row position/pitch and peg holes vs Amphenol drawing 10160920.
def h12v2x6():
    f = FP('Amphenol_10160920-1240100LF_12V-2x6_RA', '12V-2x6 16P right-angle THT header 3.0 mm, Amphenol Minitek Pwr '
           '10160920-1240100LF (PCIe CEM 5.1). P1-P6 +12V, P7-P12 GND, S1-S4 sideband. VERIFY vs drawing.',
           '12v-2x6 12vhpwr cem5', smd=False)
    for k in range(6):
        x = (k - 2.5) * 3.0
        f.pad('P%d' % (k + 1), 'thru_hole', 'rect' if k == 0 else 'circle', x, -1.5, 1.7, 1.7, drill=1.02)
        f.pad('P%d' % (k + 7), 'thru_hole', 'circle', x, 1.5, 1.7, 1.7, drill=1.02)
    for k in range(4):
        f.pad('S%d' % (k + 1), 'thru_hole', 'circle', (k - 1.5) * 3.0, -5.0, 1.3, 1.3, drill=0.80)
    for x in (-10.4, 10.4):
        f.pad('MP%d' % (1 if x < 0 else 2), 'thru_hole', 'circle', x, 0.0, 3.0, 3.0, drill=2.30)
    f.body(-11.6, -6.6, 11.6, 3.4, pin1=(-7.5 - 1.4, -3.0), crt=0.5)
    f.text('user', 'MATING FACE ->', 0, 4.4, 'F.Fab', 0.6)
    return f


# ------------------------------------------------------------------ CRPS output mating connector
# FCI/Amphenol PwrBlade 10106264-6003003LF class (Murata D1U54T datasheet: mating connector).  6 power blades
# P1..P6, 12 signal pins A1..D3.  Press-fit/solder tails modelled as plated holes.  VERIFY vs Amphenol drawing.
def crps():
    f = FP('Amphenol_CRPS_PwrBlade_Vertical_PressFit', 'CRPS PSU output mating connector, PwrBlade class, 6 power + 12 signal, vertical press-fit (board perpendicular to the PSU). '
           'Pin pattern modelled on FCI/Amphenol 10106264 per Murata D1U54T. VERIFY variant + land pattern vs Amphenol drawing.', 'crps pwrblade', smd=False)
    rows = 'ABCD'
    for c in range(3):
        for r in range(4):
            f.pad('%s%d' % (rows[r], c + 1), 'thru_hole', 'rect' if (r, c) == (0, 0) else 'circle',
                  -18.0 + c * 2.0, -3.0 + r * 2.0, 1.2, 1.2, drill=0.70)
    for b in range(6):
        xb = -10.0 + b * 6.35
        for i in range(2):
            for j in range(3):
                f.pad('P%d' % (b + 1), 'thru_hole', 'circle', xb + (i - 0.5) * 2.5, -2.5 + j * 2.5, 1.9, 1.9, drill=1.15)
    for k, x in enumerate((-22.0, 26.5)):
        f.pad('MP%d' % (k + 1), 'thru_hole', 'circle', x, 0.0, 3.4, 3.4, drill=2.60)
    f.body(-23.8, -5.0, 28.3, 5.5, pin1=(-19.6, -4.4), crt=0.5)
    return f


# ------------------------------------------------------------------ M6 press-fit power stud (busbar connection)
def stud(drill=6.4, pad=12.0, name='Power_Stud_M6_PressFit'):
    f = FP(name, 'M6 press-fit / broaching power stud (PEM FHS-M6 class) to the column busbar or CPD strap, %.1f mm plated hole, '
           '%.0f mm pad on all layers, 8 stitching vias' % (drill, pad), 'stud busbar power', smd=False)
    f.pad('1', 'thru_hole', 'circle', 0, 0, pad, pad, drill=drill)
    import math
    for k in range(8):
        a = k * math.pi / 4
        f.pad('1', 'thru_hole', 'circle', (pad / 2 - 1.3) * math.cos(a), (pad / 2 - 1.3) * math.sin(a), 0.9, 0.9, drill=0.5)
    f.circle(0, 0, pad / 2 + 0.3, 'F.CrtYd', 0.05)
    f.circle(0, 0, pad / 2 + 0.2, 'F.SilkS', 0.15)
    f.circle(0, 0, pad / 2, 'F.Fab', 0.1)
    f.text('reference', 'REF**', 0, -pad / 2 - 1.2, 'F.SilkS', 1.0)
    f.text('value', name, 0, pad / 2 + 1.2, 'F.Fab', 1.0)
    return f


# ------------------------------------------------------------------ TI QFN land patterns (filled from the TI package pages)
QFN = {}


def qfn_from_table(name, desc, pads, body, ep=()):
    """pads: [(num, x, y, w, h)], ep: [(num, x, y, w, h)] - from TI 'EXAMPLE BOARD LAYOUT'."""
    f = FP(name, desc, 'qfn ti')
    for num, x, y, w, h in pads:
        f.pad(num, 'smd', 'roundrect', x, y, w, h, rr=0.1)
    for num, x, y, w, h in ep:
        f.pad(num, 'smd', 'rect', x, y, w, h)
    bw, bh = body
    f.body(-bw / 2, -bh / 2, bw / 2, bh / 2, crt=0.4, silk=False)
    xs = [p[1] - p[3] / 2 for p in pads]
    ys = [p[2] - p[4] / 2 for p in pads]
    f.circle(min(xs) - 0.4, min(ys) - 0.4, 0.15, 'F.SilkS', 0.2)
    QFN[name] = f
    return f


def kicad_copy(lib, name, newname, desc_add, rename_unnumbered=None):
    """copy a stock KiCad footprint, renaming unnumbered copper pads (e.g. the TDSON-8 drain tabs) to a pin"""
    txt = open(os.path.join('/usr/share/kicad/footprints', lib + '.pretty', name + '.kicad_mod')).read()
    txt = txt.replace('(footprint "%s"' % name, '(footprint "%s"' % newname, 1)
    if rename_unnumbered:
        txt = txt.replace('(pad "" smd', '(pad "%s" smd' % rename_unnumbered)
    i = txt.index('(descr "') + 8
    txt = txt[:i] + desc_add + ' ' + txt[i:]
    return newname, txt


EXTRA_COPIES = [('Package_TO_SOT_SMD', 'TDSON-8-1', 'TDSON-8-1_DrainTabsNumbered',
                 '[ts2b: drain tabs numbered 5 so pours connect]', '5')]


def write(extra=()):
    os.makedirs(LIBFP, exist_ok=True)
    fps = [cem_x16(), mcio(), h12v2x6(), crps(), stud(), stud(5.4, 10.0, 'Power_Stud_M5_PressFit')] + list(QFN.values()) + list(extra)
    for f in fps:
        with open(os.path.join(LIBFP, f.name + '.kicad_mod'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(f.dump())
    for lib, name, new, d, ren in EXTRA_COPIES:
        n, txt = kicad_copy(lib, name, new, d, ren)
        with open(os.path.join(LIBFP, n + '.kicad_mod'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(txt)
    print('wrote', len(fps), 'footprints to', LIBFP)


if __name__ == '__main__':

    write()
