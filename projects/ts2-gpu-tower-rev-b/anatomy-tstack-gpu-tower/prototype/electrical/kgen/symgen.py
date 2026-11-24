"""Project-local symbols (KiCad 7 library format) for parts the stock KiCad 7 libraries do not carry.

Each symbol is a plain box: left pins, right pins, optional top/bottom power pins.  Pin numbers and names come
from the vendor pin tables quoted in ../../docs/part-verification.md; the box drawing itself is generic.
"""
import os
from core import LIBSYM

PITCH = 2.54
PLEN = 2.54


def _q(s):
    return '"' + s.replace('"', '\\"') + '"'


def box(name, left, right, ref='U', fp='', desc='', keywords='', width=None, top=(), bottom=()):
    """left/right: list of (number, name, etype) or None for a gap; etype = KiCad pin electrical type."""
    rows = max(len(left), len(right))
    lw = max([len(p[1]) for p in left if p] + [1])
    rw = max([len(p[1]) for p in right if p] + [1])
    w = width or max(10.16, round(((lw + rw) * 1.0 + 6) / PITCH) * PITCH)
    w = round(w / PITCH) * PITCH
    h = (rows + 1) * PITCH
    y0 = (rows - 1) / 2.0 * PITCH
    y0 = round(y0 / PITCH * 2) / 2 * PITCH
    top_y = y0 + PITCH
    bot_y = y0 - rows * PITCH
    xl, xr = -w / 2, w / 2
    out = []
    out.append('  (symbol %s (in_bom yes) (on_board yes)' % _q(name))
    out.append('    (property "Reference" %s (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) (justify left)))'
               % (_q(ref), xl, top_y + 1.27 + (PLEN if top else 0)))
    out.append('    (property "Value" %s (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) (justify left)))'
               % (_q(name), xl, bot_y - 1.27 - (PLEN if bottom else 0)))
    out.append('    (property "Footprint" %s (at 0 0 0) (effects (font (size 1.27 1.27)) hide))' % _q(fp))
    out.append('    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    out.append('    (property "ki_keywords" %s (at 0 0 0) (effects (font (size 1.27 1.27)) hide))' % _q(keywords))
    out.append('    (property "ki_description" %s (at 0 0 0) (effects (font (size 1.27 1.27)) hide))' % _q(desc))
    out.append('    (symbol %s' % _q(name + '_0_1'))
    out.append('      (rectangle (start %.2f %.2f) (end %.2f %.2f) (stroke (width 0.254) (type default)) (fill (type background)))'
               % (xl, top_y, xr, bot_y))
    out.append('    )')
    out.append('    (symbol %s' % _q(name + '_1_1'))
    for i, p in enumerate(left):
        if p:
            y = y0 - i * PITCH
            out.append('      (pin %s line (at %.2f %.2f 0) (length %.2f) (name %s (effects (font (size 1.27 1.27)))) '
                       '(number %s (effects (font (size 1.27 1.27)))))' % (p[2], xl - PLEN, y, PLEN, _q(p[1]), _q(p[0])))
    for i, p in enumerate(right):
        if p:
            y = y0 - i * PITCH
            out.append('      (pin %s line (at %.2f %.2f 180) (length %.2f) (name %s (effects (font (size 1.27 1.27)))) '
                       '(number %s (effects (font (size 1.27 1.27)))))' % (p[2], xr + PLEN, y, PLEN, _q(p[1]), _q(p[0])))
    for k, p in enumerate(top):
        x = round((-(len(top) - 1) / 2 + k) * PITCH * 2 / PITCH) * PITCH
        out.append('      (pin %s line (at %.2f %.2f 270) (length %.2f) (name %s (effects (font (size 1.27 1.27)))) '
                   '(number %s (effects (font (size 1.27 1.27)))))' % (p[2], x, top_y + PLEN, PLEN, _q(p[1]), _q(p[0])))
    for k, p in enumerate(bottom):
        x = round((-(len(bottom) - 1) / 2 + k) * PITCH * 2 / PITCH) * PITCH
        out.append('      (pin %s line (at %.2f %.2f 90) (length %.2f) (name %s (effects (font (size 1.27 1.27)))) '
                   '(number %s (effects (font (size 1.27 1.27)))))' % (p[2], x, bot_y - PLEN, PLEN, _q(p[1]), _q(p[0])))
    out.append('    )')
    out.append('  )')
    return '\n'.join(out)


S = []
P_, I_, O_, B_, W_, PS = 'passive', 'input', 'output', 'bidirectional', 'power_in', 'power_out'

# MCIO 8i (SFF-TA-1016) 74-position receptacle, lanes 0-7.  Pin map: NVIDIA ConnectX MCIO tables (A1-A37, B1-B37).
# Signal names here are *device side* (the backplane is the device end of the cable): PER = from host, PET = to host.
mcio_a = ['GND', 'PERp0', 'PERn0', 'GND', 'PERp1', 'PERn1', 'GND', 'SMB_SCL', 'SMB_SDA', 'GND', 'PERST_A#', 'CBL_PRES_A#', 'GND',
          'PERp2', 'PERn2', 'GND', 'PERp3', 'PERn3', 'GND', 'PERp4', 'PERn4', 'GND', 'PERp5', 'PERn5', 'GND',
          'SB_A26', 'SB_A27', 'GND', 'PERST_B#', 'CBL_PRES_B#', 'GND', 'PERp6', 'PERn6', 'GND', 'PERp7', 'PERn7', 'GND']
mcio_b = ['GND', 'PETp0', 'PETn0', 'GND', 'PETp1', 'PETn1', 'GND', '3V3_AUX', 'FLEXIO0', 'GND', 'REFCLK_A+', 'REFCLK_A-', 'GND',
          'PETp2', 'PETn2', 'GND', 'PETp3', 'PETn3', 'GND', 'PETp4', 'PETn4', 'GND', 'PETp5', 'PETn5', 'GND',
          'REFCLK_B+', 'REFCLK_B-', 'GND', 'FLEXIO7', 'FLEXIO8', 'GND', 'PETp6', 'PETn6', 'GND', 'PETp7', 'PETn7', 'GND']
S.append(box('MCIO_8i_74P', [('A%d' % (i + 1), n, P_) for i, n in enumerate(mcio_a)] + [None, ('MP', 'SHIELD', P_)],
             [('B%d' % (i + 1), n, P_) for i, n in enumerate(mcio_b)],
             ref='J', fp='ts2b:Amphenol_G97R22332HR_MCIO_8i_RA_SMT', desc='MCIO 8i 74-position 0.60 mm right-angle receptacle',
             keywords='mcio sff-ta-1016 pcie', width=27.94))

# 12V-2x6 (PCIe CEM 5.1) 16-position right-angle header: P1-P6 +12V, P7-P12 GND, S1-S4 sideband
S.append(box('12V-2x6_Header', [('P%d' % i, '+12V', P_) for i in range(1, 7)] + [None] +
             [('S1', 'CARD_PWR_STABLE', P_), ('S2', 'CARD_CBL_PRES#', P_), ('S3', 'SENSE0', P_), ('S4', 'SENSE1', P_)],
             [('P%d' % i, 'GND', P_) for i in range(7, 13)] + [None, ('MP1', 'PEG', P_), ('MP2', 'PEG', P_)],
             ref='J', fp='ts2b:Amphenol_10160920-1240100LF_12V-2x6_RA', desc='12V-2x6 16-position 3.0 mm right-angle header',
             keywords='12vhpwr 12v-2x6 gpu power', width=22.86))

# CRPS output mating connector (FCI 10106264-6003003LF class): 6 power blades + 12 signal pins (Murata D1U54T pin table)
crps_sig = [('A1', 'PRESENT_L'), ('B1', 'VSB'), ('C1', 'AC_OK'), ('D1', 'ISHARE'), ('A2', 'V1_SENSE_R'), ('B2', 'V1_SENSE+'),
            ('C2', 'PW_OK'), ('D2', 'ADDR'), ('A3', 'SDA'), ('B3', 'SCL'), ('C3', 'PS_ON'), ('D3', 'SMB_ALERT')]
S.append(box('CRPS_Output_18P', [(n, nm, P_) for n, nm in crps_sig],
             [('P4', 'V1_+12V', P_), ('P5', 'V1_+12V', P_), ('P6', 'V1_+12V', P_), None,
              ('P1', 'RTN', P_), ('P2', 'RTN', P_), ('P3', 'RTN', P_), None, ('MP1', 'PEG', P_), ('MP2', 'PEG', P_)],
             ref='J', fp='ts2b:Amphenol_CRPS_PwrBlade_Vertical_PressFit', desc='CRPS PSU output mating connector, 6 power + 12 signal, vertical',
             keywords='crps pwrblade psu', width=22.86))

# Wurth REDCUBE / PEM class press-fit power terminal, one pin
S.append(box('Power_Terminal', [('1', 'T', P_)], [], ref='T', fp='', desc='Press-fit power terminal (busbar / ring lug)',
             keywords='power terminal stud', width=7.62))


def write():
    os.makedirs(os.path.dirname(LIBSYM), exist_ok=True)
    with open(LIBSYM, 'w', encoding='utf-8', newline='\n') as f:
        f.write('(kicad_symbol_lib (version 20220914) (generator kgen)\n')
        f.write('\n'.join(S))
        f.write('\n)\n')
    print('wrote', LIBSYM, len(S), 'symbols')


if __name__ == '__main__':
    write()
