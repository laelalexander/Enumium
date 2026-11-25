"""TS-2 rev B mechanical drawing set: one A3 sheet per made part, generated from the parametric CAD (build123d B-rep).

For every part:
  * third-angle front / top / section A-A views (hidden-line removed) plus an isometric view;
  * overall dimensions and every hole position in mm with inches in brackets;
  * a hole table found from the B-rep itself (every full cylinder), with counterbores, depths and thread call-outs;
  * material, finish, mass, general tolerances and the design notes carried in the CAD source;
  * a 1:1 DXF cut file (mm) for every flat part, from the through-profile of the solid.

Run:  python3 drawings/gen_drawings.py           (writes drawings/pdf, drawings/dxf, drawings/TS2B-DWG_set.pdf)
"""
import math
import os
import re
import sys
import time
import traceback

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Rectangle, PathPatch  # noqa: E402
from matplotlib.path import Path as MPath             # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, '..', 'mechanical', 'cad')
sys.path.insert(0, CAD)
import parts as T                                     # noqa: E402
from build123d import (Box, Pos, Part, Plane, Compound, Keep, GeomType, ExportDXF, Unit, Vector,  # noqa: E402
                       LineType, Face)
from OCP.BRepAdaptor import BRepAdaptor_Surface        # noqa: E402

PDF = os.path.join(HERE, 'pdf')
DXF = os.path.join(HERE, 'dxf')
for d in (PDF, DXF):
    os.makedirs(d, exist_ok=True)

DATE = '2026-11-24'
REV = 'A'
IN = 25.4

# ------------------------------------------------------------------ catalogue (title, material, finish from build_all.py)
META = {}
for m in re.finditer(r'meta\("(\w+)", "([^"]+)", "([^"]+)", "(\w+)", "([^"]+)", "([^"]+)", "([^"]+)"(?:, "([^"]*)")?(?:, "([^"]*)")?\)',
                     open(os.path.join(CAD, 'build_all.py')).read()):
    key, pn, name, kind, mat, color, bom, dwg, fin = m.groups()
    META[key] = dict(pn=pn, name=name, kind=kind, material=mat, finish=fin or 'none', bom=bom)

DENS = [('C11000', 8.94), ('C12200', 8.94), ('Cu', 8.94), ('304', 8.0), ('S355', 7.85), ('6061', 2.70), ('6063', 2.70),
        ('5052', 2.68), ('1100', 2.71), ('EPDM', 1.20), ('PC', 1.20), ('PETG', 1.27), ('ASA', 1.07)]


def density(mat):
    for k, v in DENS:
        if k in mat:
            return v
    return 2.7


CR = None


def crown(k):
    global CR
    if CR is None:
        CR = T.crown_parts()
    return CR[k]


def coil():
    a, b, c, d = T.tracing_coil()
    return Compound(children=[a, b, c, d])


# (drawing no, meta key, builder, quantity per tower, part-specific hole call-outs {dia: text}, flat for DXF)
PARTS = [
    ('TS2B-201', 'base_plate', T.base_plate, 4, {}, True),
    ('TS2B-202', 'top_plate', T.top_plate, 4, {}, True),
    ('TS2B-203', 'bulkhead', T.bulkhead, 4, {4.5: 'M4 clearance, 90 deg CSK on plenum side', 6.0: 'bleed hole behind the backplane',
                                           6.6: 'M6 clearance into post slot-6 T-nut'}, True),
    ('TS2B-205', 'bracket_rail', lambda: T.bracket_rail(0), 8, {}, False),
    ('TS2B-206', 'tail_comb', lambda: T.tail_comb(1), 8, {5.0: 'M6x1.0-6H tap drill'}, False),
    ('TS2B-207', 'holddown_bar', lambda: T.holddown_bar(0), 8, {6.1: 'hinge pin 6 h8 / bore 6.1 slip'}, False),
    ('TS2B-208', 'holddown_pad', lambda: T.box(0, 16.0, 0, 3.0, 0, 28.0), 128, {}, True),
    ('TS2B-209', 'hinge_block', lambda: T.hinge_block(0), 8, {6.0: 'hinge pin 6 H7 press (pin 6 m6)'}, False),
    ('TS2B-210', 'latch', lambda: T.latch(0), 8, {4.1: 'pivot pin 4 m6 x 22 (slip in the handle)',
                                                  5.0: 'M6x1.0-6H for GN 617-6 spring plunger'}, False),
    ('TS2B-211', 'crossmember', T.crossmember, 4, {}, True),
    ('TS2B-212', 'light_bar', T.light_bar, 4, {3.4: 'M3 clearance, M3 x 35 into the crossmember'}, False),
    ('TS2B-213', 'side_skin', lambda: T.side_skin(1), 8, {5.5: 'M5 clearance (button head into post T-nut)'}, True),
    ('TS2B-214', 'bp_carrier', T.bp_carrier, 4, {3.4: 'M3 clearance, M3 x 12 hex standoff to CBP-8',
                                                  4.5: 'M4 clearance, angle clip to base / top plate'}, True),
    ('TS2B-215', 'busbar_pos', lambda: T.busbars()[0], 4, {6.6: 'M6 stud clearance (+12 V studs, 6 mm Cu bush under)',
                                                            17.0: 'clearance for the RTN 18 mm bush + PTFE sleeve',
                                                            8.5: 'M8 clearance, 2 x 4/0 lugs back to back, M8 x 40 A2-70, 12 N m'}, True),
    ('TS2B-216', 'busbar_neg', lambda: T.busbars()[1], 4, {6.6: 'M6 stud clearance (RTN studs)',
                                                            8.5: 'M8 clearance, 2 x 4/0 lugs back to back, M8 x 40 A2-70, 12 N m'}, True),
    ('TS2B-220', 'coil_sheet', coil, 4, {}, False),
    ('TS2B-221', 'drip_tray', T.drip_tray, 4, {}, False),
    ('TS2B-223', 'grille', lambda: T.grille_segment(0), 16, {}, False),
    ('TS2B-232', 'strap_p12', T.strap_p12, 4, {8.5: 'M8 clearance, lug bolt M8 x 25 A2-70 + Belleville, 12 N m',
                                               6.6: 'M6 clearance over press-fit stud, nut + Belleville 6 N m'}, True),
    ('TS2B-233', 'strap_rtn', T.strap_rtn, 4, {8.5: 'M8 clearance, lug bolt M8 x 25 A2-70 + Belleville, 12 N m',
                                               6.6: 'M6 clearance over press-fit stud, nut + Belleville 6 N m'}, True),
    ('TS2B-301', 'plenum_corner', lambda: T.plenum_corner(0), 4, {}, False),
    ('TS2B-401', 'crown_base', lambda: crown('base'), 1, {9.0: 'M8 clearance into column top plate'}, True),
    ('TS2B-402', 'crown_shell', lambda: crown('shell'), 1, {}, False),
    ('TS2B-403', 'crown_band', lambda: crown('band'), 1, {}, False),
    ('TS2B-404', 'crown_deck', lambda: crown('deck'), 1, {232.0: 'impeller inlet ring bore (ebm-papst 31050-2-4013)'}, True),
    ('TS2B-405', 'flap', lambda: T.backdraft_flap(0, 0, 0), 3, {}, True),
    ('TS2B-406', 'crown_top', lambda: crown('top'), 1, {}, False),
    ('TS2B-501', 'arm', T.plinth_arm, 4, {8.5: 'M10x1.5-6H tap drill (plinth bolt into deck)'}, False),
    ('TS2B-502', 'hub', T.plinth_hub, 1, {}, False),
    ('TS2B-601', 'tec_housing', lambda: T.tec_module()[0], 4, {5.5: 'M5 clearance to the arm deck (tapped)'}, False),
    ('TS2B-602', 'tec_cold', T.cold_block, 4, {8.0: 'coolant passage, gun drill (cross-drill plugged G1/8)',
                                               11.8: 'G1/4 BSPP port, tap drill', 8.8: 'G1/8 BSPP plug, tap drill',
                                               3.3: 'M4x0.7-6H tap drill'}, False),
    ('TS2B-701', 'console_post', lambda: T.panel_console()[0], 1, {}, False),
    ('TS2B-702', 'console_head', lambda: T.panel_console()[1], 1, {}, False),
]
META.setdefault('holddown_pad', dict(pn='TS2B-208', name='Hold-down pad, EPDM 3 mm', material='EPDM 60A sheet 3 mm (die cut)',
                                     finish='none', bom='M-208'))
META['grille']['name'] = 'Intake grille segment (printed)'

# standard hole call-outs by modelled diameter (tapped holes are modelled at the tap drill)
CALL = {2.5: 'M3x0.5-6H tap drill', 2.85: '6-32 UNC-2B tap drill (#36)', 3.3: 'M4x0.7-6H tap drill',
        3.4: 'M3 clearance', 4.2: 'M5x0.8-6H tap drill', 4.5: 'M4 clearance', 5.0: 'M6x1.0-6H tap drill',
        5.5: 'M5 clearance', 6.0: 'pin bore', 6.6: 'M6 clearance', 6.8: 'M8x1.25-6H tap drill',
        8.5: 'M10x1.5-6H tap drill', 8.6: 'M8 clearance (SHCS)', 9.0: 'M8 clearance', 11.0: 'M10 clearance',
        12.0: 'drain spud bore', 14.0: 'counterbore for M8 SHCS', 2.5: 'M3x0.5-6H tap drill', 16.5: '3/8 in tube + grommet', 20.0: 'spot face'}
THREAD_PITCH = {2.5: 0.5, 3.3: 0.7, 4.2: 0.8, 5.0: 1.0, 6.8: 1.25, 8.5: 1.5}


def tup(v):
    return (v.X, v.Y, v.Z)


def fmt(v):
    return '%.1f [%.3f]' % (v, v / IN)


# ------------------------------------------------------------------ geometry helpers
def bbox(shape):
    b = shape.bounding_box()
    return (b.min.X, b.min.Y, b.min.Z), (b.max.X, b.max.Y, b.max.Z)


def axes_for(shape):
    """Choose the drawing frame: depth (front-view line of sight) = thinnest axis, horizontal = longest remaining,
    vertical = the other.  Returns unit vectors (h, v, d) as tuples."""
    lo, hi = bbox(shape)
    ext = [hi[i] - lo[i] for i in range(3)]
    E = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    order = sorted(range(3), key=lambda i: ext[i])
    d = order[0]
    rest = [i for i in range(3) if i != d]
    # vertical: keep world Z vertical when it is not the depth axis (parts read the way they stand)
    if d != 2 and 2 in rest:
        v = 2
        h = [i for i in rest if i != 2][0]
    else:
        h, v = (rest[0], rest[1]) if ext[rest[0]] >= ext[rest[1]] else (rest[1], rest[0])
    return E[h], E[v], E[d], ext[h], ext[v], ext[d], (h, v, d)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def neg(a):
    return (-a[0], -a[1], -a[2])


def project(shape, look, up, centre, hidden=True):
    """HLR projection; returns (visible, hidden) polylines in view coordinates (right, up) relative to centre."""
    far = 20000.0
    org = (centre[0] - look[0] * far, centre[1] - look[1] * far, centre[2] - look[2] * far)
    vis, hid = shape.project_to_viewport(org, up, centre)
    # map viewport coordinates to (right, up) using the same projector on a probe
    right = cross(look, up)

    def lines(edges):
        out = []
        for e in edges:
            try:
                n = 2 if e.geom_type == GeomType.LINE else max(8, min(64, int(e.length / 1.5)))
                pts = [e.position_at(i / (n - 1)) for i in range(n)]
                out.append([(p.X, p.Y) for p in pts])
            except Exception:
                pass
        return out
    return lines(vis), (lines(hid) if hidden else []), right


_MAP = {}


def view_map(look, up):
    """2D mapping of the projector: returns a function world -> (x2, y2) consistent with project()."""
    key = (look, up)
    if key in _MAP:
        return _MAP[key]
    pts = [(0.0, 0.0, 0.0), (100.0, 0.0, 0.0), (0.0, 100.0, 0.0), (0.0, 0.0, 100.0)]
    res = []
    for p in pts:
        b = Pos(*p) * Box(2, 2, 2)
        vis, hid, _ = project(b, look, up, (0, 0, 0), hidden=False)
        xs = [q[0] for l in vis for q in l]
        ys = [q[1] for l in vis for q in l]
        res.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
    o = res[0]
    cols = [((res[i][0] - o[0]) / 100.0, (res[i][1] - o[1]) / 100.0) for i in (1, 2, 3)]

    def f(w, c=(0, 0, 0)):
        w = sub(w, c)
        return (o[0] + cols[0][0] * w[0] + cols[1][0] * w[1] + cols[2][0] * w[2],
                o[1] + cols[0][1] * w[0] + cols[1][1] * w[1] + cols[2][1] * w[2])
    _MAP[key] = f
    return f


def holes(shape):
    """Every full internal cylinder, grouped by axis line: [dict(axis, dir, pt, steps=[(dia, t0, t1)])]."""
    groups = {}
    for fc in shape.faces():
        if fc.geom_type != GeomType.CYLINDER:
            continue
        try:
            s = BRepAdaptor_Surface(fc.wrapped)
            cy = s.Cylinder()
        except Exception:
            continue
        r = cy.Radius()
        ax = cy.Axis()
        dvec = (ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z())
        if max(abs(c) for c in dvec) < 0.999:
            continue                                   # oblique cylinders (blades, bends): not a drilled hole
        k = max(range(3), key=lambda i: abs(dvec[i]))
        dvec = tuple(1.0 if i == k else 0.0 for i in range(3))
        loc = (ax.Location().X(), ax.Location().Y(), ax.Location().Z())
        # internal?  the face normal points toward the axis
        try:
            p = fc.position_at(0.5, 0.5)
            nrm = fc.normal_at(0.5, 0.5)
        except Exception:
            continue
        rad = sub((p.X, p.Y, p.Z), loc)
        rad = tuple(rad[i] if i != k else 0.0 for i in range(3))
        if dot(rad, (nrm.X, nrm.Y, nrm.Z)) > 0:
            continue
        span = abs(s.LastUParameter() - s.FirstUParameter())
        bb = fc.bounding_box()
        t0, t1 = (bb.min.X, bb.min.Y, bb.min.Z)[k], (bb.max.X, bb.max.Y, bb.max.Z)[k]
        line = tuple(round(loc[i], 1) if i != k else 0.0 for i in range(3)) + (k,)
        g = groups.setdefault(line, dict(k=k, pt=tuple(loc[i] if i != k else 0.0 for i in range(3)), faces=[]))
        g['faces'].append((round(2 * r, 2), span, t0, t1))
    out = []
    for line, g in groups.items():
        # merge faces of one cylinder (same dia, overlapping interval: OCC splits a full cylinder into halves)
        cyls = []
        for dia, span, t0, t1 in sorted(g['faces'], key=lambda f: (f[0], f[2])):
            for c in cyls:
                if c[0] == dia and t0 < c[3] - 0.01 and t1 > c[2] + 0.01:
                    c[1] += span
                    c[2], c[3] = min(c[2], t0), max(c[3], t1)
                    break
            else:
                cyls.append([dia, span, t0, t1])
        cyls = [c for c in cyls if c[1] > 2 * math.pi - 0.2]
        # cluster contiguous intervals along the axis into one hole (drill + counterbore / spot face)
        cyls.sort(key=lambda c: c[2])
        clusters = []
        for c in cyls:
            if clusters and c[2] <= max(x[3] for x in clusters[-1]) + 0.05:
                clusters[-1].append(c)
            else:
                clusters.append([c])
        for cl in clusters:
            steps = sorted((dia, t0, t1) for dia, _, t0, t1 in cl)
            out.append(dict(k=g['k'], pt=g['pt'], steps=steps))
    return out


def describe(h, lo, hi, call):
    """Call-out text for one hole: main diameter, THRU or depth, counterbore / spot face, thread."""
    k = h['k']
    ext0, ext1 = lo[k], hi[k]
    steps = h['steps']
    d0, a0, a1 = steps[0]
    u0, u1 = min(st[1] for st in steps), max(st[2] for st in steps)
    thru = (u0 <= ext0 + 0.3 and u1 >= ext1 - 0.3)
    txt = []
    nm = call.get(d0) or CALL.get(d0, '')
    if d0 in THREAD_PITCH and not thru and 'clear' not in nm:
        m = re.match(r'(M\d+x[\d.]+-6H|[\d-]+ UNC-2B)', nm)
        thread = (m.group(1) if m else nm)
        depth = (a1 - a0)
        txt.append('%s, drill ⌀%.2f DP %.1f [%.3f], thread DP %.1f' % (thread, d0, depth, depth / IN, depth - 2 * THREAD_PITCH[d0]))
    else:
        txt.append('⌀%.2f [%.3f] %s' % (d0, d0 / IN, 'THRU' if thru else 'DP %.1f [%.3f]' % (a1 - a0, (a1 - a0) / IN)))
        if nm:
            txt.append(nm)
    for d, b0, b1 in steps[1:]:
        dep = b1 - b0
        kind = 'SPOT FACE' if dep <= 1.5 else 'CBORE'
        nm2 = call.get(d) or ''
        txt.append('%s ⌀%.1f [%.3f] DP %.1f [%.3f]%s' % (kind, d, d / IN, dep, dep / IN, (' (%s)' % nm2) if nm2 else ''))
    return '; '.join(txt)


# ------------------------------------------------------------------ sheet
A3 = (420.0, 297.0)
LEFT_W = 262.0          # view area width (mm on paper)
RX = 10.0 + LEFT_W + 4  # right column x


def frame(fig, ax, pn, title, mat, fin, scale, mass, qty, sheet, nsheets):
    ax.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=0.8))
    # zone ticks
    for i in range(1, 8):
        x = 10 + i * 400 / 8
        ax.plot([x, x], [10, 13], 'k-', lw=0.4)
        ax.plot([x, x], [284, 287], 'k-', lw=0.4)
    for i in range(1, 6):
        y = 10 + i * 277 / 6
        ax.plot([10, 13], [y, y], 'k-', lw=0.4)
        ax.plot([407, 410], [y, y], 'k-', lw=0.4)
    for i in range(8):
        ax.text(10 + (i + 0.5) * 400 / 8, 7.0, str(8 - i), ha='center', va='center', fontsize=5)
    for i, L in enumerate('FEDCBA'):
        ax.text(6.5, 10 + (i + 0.5) * 277 / 6, L, ha='center', va='center', fontsize=5)
    # title block 134 x 46 at the lower right
    x0, y0, w = RX, 10.0, 410.0 - RX
    rows = [
        ('TS-2 rev B  64-GPU tower', 'Anatomy', 7.0),
        (title, '', 6.0),
        ('DRAWING NO.  %s' % pn, 'REV %s' % REV, 6.0),
        ('MATERIAL  %s' % mat, '', 4.6),
        ('FINISH  %s' % fin, '', 4.6),
        ('SCALE %s   SHEET A3   %d of %d' % (scale, sheet, nsheets), 'QTY / TOWER %d' % qty, 4.6),
        ('MASS %.3f kg [%.2f lb] (CAD)' % (mass, mass * 2.20462), 'UNITS mm [in]', 4.6),
        ('DRAWN Anatomy generator  %s' % DATE, 'CHECKED ______', 4.4),
    ]
    h = 5.8
    ax.add_patch(Rectangle((x0, y0), w, h * len(rows), fill=False, lw=0.8))
    for i, (a, b, fs) in enumerate(rows):
        y = y0 + h * (len(rows) - i - 1)
        ax.plot([x0, x0 + w], [y, y], 'k-', lw=0.3)
        ax.text(x0 + 1.5, y + h / 2, a, fontsize=fs, va='center', ha='left', fontweight='bold' if i in (1, 2) else 'normal')
        if b:
            ax.text(x0 + w - 1.5, y + h / 2, b, fontsize=4.4, va='center', ha='right')
    # third-angle symbol
    sx, sy = x0 + w - 18, y0 + h * len(rows) + 4
    ax.add_patch(plt.Polygon([(sx, sy), (sx, sy + 6), (sx + 8, sy + 4.5), (sx + 8, sy + 1.5)], fill=False, lw=0.5))
    for r in (3.0, 1.6):
        ax.add_patch(plt.Circle((sx + 13, sy + 3), r, fill=False, lw=0.5))
    ax.text(sx - 1, sy + 3, 'THIRD ANGLE', fontsize=3.8, ha='right', va='center')
    return y0 + h * len(rows) + 12


def draw_lines(ax, lines, ox, oy, s, style='-', lw=0.45, color='k'):
    for l in lines:
        ax.plot([ox + p[0] * s for p in l], [oy + p[1] * s for p in l], style, lw=lw, color=color,
                dashes=(2.0, 1.2) if style == '--' else (None, None))


def ext2d(lines):
    xs = [p[0] for l in lines for p in l]
    ys = [p[1] for l in lines for p in l]
    return min(xs), min(ys), max(xs), max(ys)


def dim_h(ax, x0, x1, y, yref, txt, below=True):
    """horizontal dimension between x0..x1 drawn at y, extension lines from yref"""
    for x in (x0, x1):
        ax.plot([x, x], [yref, y + (-1.2 if below else 1.2)], 'k-', lw=0.25)
    ax.annotate('', xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle='<|-|>', lw=0.3, mutation_scale=4, shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + (-1.0 if below else 1.0), txt, fontsize=4.2, ha='center', va='top' if below else 'bottom')


def dim_v(ax, y0, y1, x, xref, txt, left=True):
    for y in (y0, y1):
        ax.plot([xref, x + (-1.2 if left else 1.2)], [y, y], 'k-', lw=0.25)
    ax.annotate('', xy=(x, y0), xytext=(x, y1), arrowprops=dict(arrowstyle='<|-|>', lw=0.3, mutation_scale=4, shrinkA=0, shrinkB=0))
    ax.text(x + (-1.0 if left else 1.0), (y0 + y1) / 2, txt, fontsize=4.2, ha='right' if left else 'left', va='center', rotation=90)


SCALES = [(2, 1), (1, 1), (1, 2), (1, 2.5), (1, 5), (1, 10), (1, 20)]


def section_faces(shape, axis_i, pos):
    """faces of the solid cut by the plane x_axis_i = pos"""
    n = [0.0, 0.0, 0.0]
    n[axis_i] = 1.0
    o = [0.0, 0.0, 0.0]
    o[axis_i] = pos
    pl = Plane(origin=tuple(o), z_dir=tuple(n))
    try:
        sec = shape.intersect(pl.to_location() * Box(1e5, 1e5, 0.001)) if False else None
    except Exception:
        sec = None
    try:
        from build123d import section as b3d_section  # noqa: F401
    except Exception:
        pass
    try:
        cut = shape & (Pos(*[pos - 0.005 if i == axis_i else 0 for i in range(3)]) *
                       Box(*[0.01 if i == axis_i else 1e5 for i in range(3)]))
        faces = [f for f in cut.faces() if abs(tup(f.normal_at())[axis_i]) > 0.99 and
                 abs(tup(f.center())[axis_i] - pos) < 0.002]
        return faces
    except Exception:
        return []


def face_path(face, f2, c):
    verts, codes = [], []
    for w in [face.outer_wire()] + list(face.inner_wires()):
        pts = []
        for e in w.edges():
            n = 2 if e.geom_type == GeomType.LINE else 24
            pts += [f2(tup(e.position_at(i / (n - 1))), c) for i in range(n)]
        if len(pts) < 3:
            continue
        verts += pts + [pts[0]]
        codes += [MPath.MOVETO] + [MPath.LINETO] * (len(pts) - 1) + [MPath.CLOSEPOLY]
    return MPath(verts, codes) if verts else None


def make_sheet(entry, pdf_all, sheet_no, nsheets):
    pn, key, builder, qty, call, flat = entry
    meta = META[key]
    title = meta['name'] if pn != 'TS2B-220' else 'Tracing coil assembly (3 row x 32 pass, 12 FPI)'
    t0 = time.time()
    shape = builder()
    lo, hi = bbox(shape)
    c = tuple((lo[i] + hi[i]) / 2 for i in range(3))
    H, V, Dp, eh, ev, ed, (ih, iv, idp) = axes_for(shape)
    look_front = neg(Dp)            # viewer on the +depth side (plates: seen from the top face)
    up_front = V
    look_top = neg(V)               # from above, looking down -V
    up_top = neg(Dp)                # third angle: top view above the front; the near (+depth) face is at its bottom
    look_side = neg(H)              # right-side view: viewer on +H looking toward -H
    up_side = V
    vol = shape.volume
    mass = vol * density(meta['material']) * 1e-6
    # scale
    avail_w, avail_h = LEFT_W - 30.0, 277.0 - 40.0
    sc = None
    for a, b in SCALES:
        s = a / b
        if (eh + ed) * s + 100 <= LEFT_W + 4 and (ev + ed) * s + 80 <= 272:
            sc = (a, b)
            break
    if sc is None:
        sc = (1, 50)
    s = sc[0] / sc[1]
    scale_txt = '%g:%g' % sc
    # projections
    fv, fh, _ = project(shape, look_front, up_front, c)
    tv, th, _ = project(shape, look_top, up_top, c)
    # section A-A on the right view: cut through the hole column nearest the middle (or the middle)
    hl = holes(shape)
    cut_at = c[ih]
    cand = [h['pt'][ih] for h in hl if h['k'] != ih]
    if cand:
        cut_at = min(cand, key=lambda x: abs(x - c[ih]))
    try:
        keep_half = shape.split(Plane(origin=tuple(cut_at if i == ih else 0.0 for i in range(3)),
                                      z_dir=tuple(-1.0 if i == ih else 0.0 for i in range(3))), keep=Keep.TOP)
        sv, sh, _ = project(keep_half, look_side, up_side, c)
        secfaces = section_faces(shape, ih, cut_at)
        sect = True
    except Exception:
        sv, sh, _ = project(shape, look_side, up_side, c)
        secfaces, sect = [], False
    iso_dir = tuple(-(H[i] * 0.55) + Dp[i] * 0.6 - V[i] * 0.55 for i in range(3))
    L = math.sqrt(dot(iso_dir, iso_dir))
    iso_dir = tuple(x / L for x in iso_dir)
    iv_, _, _ = project(shape, iso_dir, V, c, hidden=False)

    fig = plt.figure(figsize=(A3[0] / IN, A3[1] / IN))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, A3[0])
    ax.set_ylim(0, A3[1])
    ax.set_aspect('equal')
    ax.axis('off')
    top_of_tb = frame(fig, ax, pn, title, meta['material'], meta['finish'], scale_txt, mass, qty, sheet_no, nsheets)

    # placement: front lower-left, top above it, section right of it
    fx0, fy0, fx1, fy1 = ext2d(fv + fh)
    ox = 10 + 34 - fx0 * s
    tx0_, ty0_, tx1_, ty1_ = ext2d(tv + th) if (tv or th) else (0, 0, 0, 0)
    group_h = (fy1 - fy0) * s + 30 + (ty1_ - ty0_) * s + 12
    oy = 10 + 38 + max(0.0, (277 - 50 - 100 - group_h) / 2) - fy0 * s
    draw_lines(ax, fh, ox, oy, s, '--', 0.25, '0.35')
    draw_lines(ax, fv, ox, oy, s)
    ax.text(ox + (fx0 + fx1) / 2 * s, oy + fy0 * s - 35, 'FRONT VIEW', fontsize=5, ha='center', fontweight='bold')
    # overall dims
    dim_h(ax, ox + fx0 * s, ox + fx1 * s, oy + fy0 * s - 28, oy + fy0 * s, fmt(fx1 - fx0))
    dim_v(ax, oy + fy0 * s, oy + fy1 * s, ox + fx0 * s - 29, ox + fx0 * s, fmt(fy1 - fy0))
    # top view
    tx0, ty0, tx1, ty1 = ext2d(tv + th)
    tox = ox + (fx0 - tx0) * s + ((fx1 - fx0) - (tx1 - tx0)) * s / 2
    toy = oy + fy1 * s + 28 - ty0 * s
    draw_lines(ax, th, tox, toy, s, '--', 0.25, '0.35')
    draw_lines(ax, tv, tox, toy, s)
    ax.text(tox + (tx0 + tx1) / 2 * s, toy + ty1 * s + 2.5, 'TOP VIEW', fontsize=5, ha='center', fontweight='bold')
    dim_v(ax, toy + ty0 * s, toy + ty1 * s, tox + tx1 * s + 5, tox + tx1 * s, fmt(ty1 - ty0), left=False)
    # section / side view
    sx0, sy0, sx1, sy1 = ext2d(sv + sh) if (sv or sh) else (0, 0, 1, 1)
    sox = ox + fx1 * s + 30 - sx0 * s
    soy = oy + (fy0 - sy0) * s
    f_side = view_map(look_side, up_side)
    if secfaces:
        for fc in secfaces:
            pth = face_path(fc, f_side, c)
            if pth is None:
                continue
            pth = MPath([(sox + x * s, soy + y * s) for x, y in pth.vertices], pth.codes)
            ax.add_patch(PathPatch(pth, facecolor='none', edgecolor='k', hatch='//////', lw=0.5))
    draw_lines(ax, sh, sox, soy, s, '--', 0.25, '0.35')
    draw_lines(ax, sv, sox, soy, s)
    ax.text(sox + (sx0 + sx1) / 2 * s, soy + sy0 * s - 9, 'SECTION A-A' if sect else 'RIGHT VIEW', fontsize=5, ha='center',
            fontweight='bold')
    dim_h(ax, sox + sx0 * s, sox + sx1 * s, soy + sy0 * s - 4.5, soy + sy0 * s, fmt(sx1 - sx0))
    if sect:
        # cutting-plane line on the front view
        f_front = view_map(look_front, up_front)
        px = f_front(tuple(cut_at if i == ih else c[i] for i in range(3)), c)[0]
        X = ox + px * s
        ax.plot([X, X], [oy + fy0 * s - 2, oy + fy1 * s + 2], '-.', lw=0.5, color='k')
        for yy in (oy + fy0 * s - 2, oy + fy1 * s + 2):
            ax.annotate('', xy=(X + 4, yy), xytext=(X, yy), arrowprops=dict(arrowstyle='-|>', lw=0.4, mutation_scale=5))
            ax.text(X + 5, yy, 'A', fontsize=6, va='center', fontweight='bold')
    # iso (top right of the view field)
    if iv_:
        ix0, iy0, ix1, iy1 = ext2d(iv_)
        right_edge = max(tox + tx1 * s + 14, sox + sx1 * s + 26)
        # candidate boxes: right of the views (full height) or above the top view (full width)
        boxes = [(right_edge, 20.0, RX - 4, 283.0), (14.0, toy + ty1 * s + 8, RX - 4, 283.0)]
        best = None
        for (bx0, by0, bx1, by1) in boxes:
            if bx1 - bx0 < 30 or by1 - by0 < 30:
                continue
            si_ = min(1.6 * s, (bx1 - bx0) / max(ix1 - ix0, 1), (by1 - by0 - 6) / max(iy1 - iy0, 1))
            if best is None or si_ > best[0]:
                best = (si_, bx0, by0, bx1, by1)
        if best is None:
            best = (0.0, 0, 0, 0, 0)
        si, bx0, by0, bx1, by1 = best
        iox = (bx0 + bx1) / 2 - (ix0 + ix1) / 2 * si
        ioy = by1 - 2 - iy1 * si
        draw_lines(ax, iv_, iox, ioy, si, '-', 0.35)
        ax.text(iox + (ix0 + ix1) / 2 * si, ioy + iy0 * si - 4, 'ISOMETRIC (not to scale)', fontsize=4.5, ha='center')

    # hole tags and table
    rows = []
    groups = {}
    f_front = view_map(look_front, up_front)
    f_top = view_map(look_top, up_top)
    for h in hl:
        dsc = describe(h, lo, hi, call)
        groups.setdefault(dsc, []).append(h)
    letters = 'ABCDEFGHJKLMNPRSTUVWXYZ'
    front_pts = []
    for gi, (dsc, hs) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1]))):
        tag = letters[gi % len(letters)] + ('' if gi < len(letters) else str(gi // len(letters)))
        rows.append((tag, len(hs), dsc, hs))
        for h in hs:
            p = list(h['pt'])
            p[h['k']] = (lo[h['k']] + hi[h['k']]) / 2
            if h['k'] == idp:
                q = f_front(tuple(p), c)
                X, Y = ox + q[0] * s, oy + q[1] * s
            elif h['k'] == iv:
                q = f_top(tuple(p), c)
                X, Y = tox + q[0] * s, toy + q[1] * s
            else:
                q = f_side(tuple(p), c)
                X, Y = sox + q[0] * s, soy + q[1] * s
            ax.text(X + 1.2, Y + 1.2, tag, fontsize=3.4, color='#b00020', fontweight='bold')
            if h['k'] == idp:
                front_pts.append((X, Y))
    # ordinate dimensions on the front view: hole centres (below / left) and profile corners (above / right)
    X0, Y0, X1, Y1 = ox + fx0 * s, oy + fy0 * s, ox + fx1 * s, oy + fy1 * s
    ordinates(ax, sorted({round(p[0], 2) for p in front_pts}), X0, s, Y0, 'below')
    ordinates(ax, sorted({round(p[1], 2) for p in front_pts}), Y0, s, X0, 'left')
    corners_x, corners_y = set(), set()
    for l in fv:
        if len(l) == 2:
            (u0, w0), (u1, w1) = l
            if abs(u0 - u1) < 1e-3 and abs(w1 - w0) * s > 3.0:          # vertical edge: its x is a profile size
                corners_x.add(round(ox + u0 * s, 2))
            if abs(w0 - w1) < 1e-3 and abs(u1 - u0) * s > 3.0:          # horizontal edge
                corners_y.add(round(oy + w0 * s, 2))
    ordinates(ax, merge(sorted(corners_x), 0.25), X0, s, Y1, 'above', skip=(X0, X1))
    ordinates(ax, merge(sorted(corners_y), 0.25), Y0, s, X1, 'right', skip=(Y0, Y1))
    # right column: hole table (summary) then coordinate table
    y = 287.0 - 4.0
    ax.text(RX, y, 'HOLE TABLE  (positions from datum A = front-view lower-left corner; mm [in])', fontsize=4.6,
            fontweight='bold', va='top')
    y -= 4.5
    for tag, n, dsc, hs in rows:
        txt = '%s  %dx  %s' % (tag, n, dsc)
        for line in wrap(txt, 84):
            ax.text(RX, y, line, fontsize=4.4, va='top', family='DejaVu Sans')
            y -= 3.3
    if not rows:
        ax.text(RX, y, '(no drilled holes)', fontsize=3.8, va='top')
        y -= 3.4
    y -= 1.5
    # coordinates
    coords = []
    for tag, n, dsc, hs in rows:
        for j, h in enumerate(sorted(hs, key=lambda h: tuple(round(v, 1) for v in h['pt']))):
            p = list(h['pt'])
            p[h['k']] = (lo[h['k']] + hi[h['k']]) / 2
            hv = p[ih] - lo[ih]
            vv = p[iv] - lo[iv]
            dv = p[idp] - lo[idp]
            view = {idp: 'FRONT', iv: 'TOP', ih: 'SECT'}[h['k']]
            a1, a2 = {idp: (hv, vv), iv: (hv, dv), ih: (dv, vv)}[h['k']]
            coords.append('%s%-2d %-5s X %7.2f [%6.3f]  Y %7.2f [%6.3f]' % (tag, j + 1, view, a1, a1 / IN, a2, a2 / IN))
    max_lines = int((y - top_of_tb - 70) / 3.0)
    ax.text(RX, y, 'HOLE POSITIONS', fontsize=4.6, fontweight='bold', va='top')
    y -= 4.0
    ncol = 2 if len(coords) > max_lines else 1
    per = max(1, max_lines)
    shown = coords[:per * ncol]
    for i, ln in enumerate(shown):
        col, row = divmod(i, per)
        ax.text(RX + col * 67.5, y - row * 3.0, ln if ncol == 1 else ln.replace('  ', ' '), fontsize=3.1 if ncol == 2 else 4.0,
                va='top', family='DejaVu Sans Mono')
    nrows = min(len(shown), per)
    y -= nrows * 3.0 + 2
    if len(coords) > len(shown):
        ax.text(RX, y, '+ %d more: see %s.dxf / STEP for every position' % (len(coords) - len(shown), pn), fontsize=3.6, va='top')
        y -= 3.5
    # notes
    doc = (builder.__doc__ if builder.__doc__ and not builder.__name__ == '<lambda>' else '') or ''
    if not doc:
        fn = {'bracket_rail': T.bracket_rail, 'tail_comb': T.tail_comb, 'holddown_bar': T.holddown_bar, 'hinge_block': T.hinge_block,
              'latch': T.latch, 'side_skin': T.side_skin, 'busbar_pos': T.busbars, 'busbar_neg': T.busbars,
              'grille': T.grille_segment, 'plenum_corner': T.plenum_corner, 'crown_base': T.crown_parts,
              'crown_shell': T.crown_parts, 'crown_band': T.crown_parts, 'crown_deck': T.crown_parts, 'crown_top': T.crown_parts,
              'flap': T.backdraft_flap, 'tec_housing': T.tec_module, 'tec_cold': T.tec_module, 'console_post': T.panel_console,
              'console_head': T.panel_console, 'coil_sheet': T.tracing_coil, 'holddown_pad': T.holddown_pads}.get(key)
        doc = (fn.__doc__ if fn else '') or ''
    doc = ' '.join(doc.split())
    notes = ['DESIGN: ' + doc] if doc else []
    notes += general_notes(meta, flat, pn)
    ny = top_of_tb + 66
    ax.text(RX, ny, 'NOTES', fontsize=4.8, fontweight='bold', va='top')
    ny -= 4.0
    for i, n in enumerate(notes):
        for j, line in enumerate(wrap('%d. %s' % (i + 1, n), 90)):
            if ny < top_of_tb + 2:
                break
            ax.text(RX, ny, line, fontsize=4.0, va='top')
            ny -= 2.9
    fig.savefig(os.path.join(PDF, '%s.pdf' % pn))
    pdf_all.savefig(fig)
    plt.close(fig)
    dxf = write_dxf(shape, pn, H, V, Dp, idp, lo, hi) if flat else None
    print('%s %-38s scale %-6s holes %3d  dxf %s  %.1f s' % (pn, title[:38], scale_txt, sum(r[1] for r in rows),
                                                             'yes' if dxf else '-', time.time() - t0))
    return dict(pn=pn, title=title, material=meta['material'], finish=meta['finish'], qty=qty, mass=mass,
                holes=sum(r[1] for r in rows), dxf=bool(dxf), scale=scale_txt)


def merge(vals, tol):
    out = []
    for v in vals:
        if not out or v - out[-1] > tol:
            out.append(v)
    return out


def ordinates(ax, vals, datum, s, edge, side, skip=(), limit=16):
    """ordinate dimensions from the datum edge (paper coords); side: below/above (x values) or left/right (y values)"""
    vals = [v for v in vals if all(abs(v - k) > 0.3 for k in skip)]
    if not vals or len(vals) > limit:
        return
    horiz = side in ('below', 'above')
    sg = -1 if side in ('below', 'left') else 1
    base = edge + sg * (14.0 if side in ('below', 'left') else 5.0)
    last = -1e9
    for v in vals:
        mmv = (v - datum) / s
        t = '%.1f [%.3f]' % (mmv, mmv / IN)
        if horiz:
            lx = max(v, last + 3.2)
            ax.plot([v, v, lx], [edge + sg * 1.0, base - sg * 2.0, base], 'k-', lw=0.2)
            ax.text(lx, base + sg * 0.6, t, fontsize=3.4, rotation=90, ha='center', va='top' if sg < 0 else 'bottom')
        else:
            lx = max(v, last + 3.2)
            ax.plot([edge + sg * 1.0, base - sg * 2.0, base], [v, v, lx], 'k-', lw=0.2)
            ax.text(base + sg * 0.6, lx, t, fontsize=3.4, ha='right' if sg < 0 else 'left', va='center')
        last = lx
    # datum zero
    if horiz:
        ax.plot([datum, datum], [edge + sg * 1.0, base], 'k-', lw=0.2)
        ax.text(datum, base + sg * 0.6, '0', fontsize=3.4, rotation=90, ha='center', va='top' if sg < 0 else 'bottom')
    else:
        ax.plot([edge + sg * 1.0, base], [datum, datum], 'k-', lw=0.2)
        ax.text(base + sg * 0.6, datum, '0', fontsize=3.4, ha='right' if sg < 0 else 'left', va='center')


def wrap(t, n):
    words, out, cur = t.split(' '), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = '   ' + w
        else:
            cur = (cur + ' ' + w).strip(' ') if cur else w
    if cur:
        out.append(cur)
    return out


def general_notes(meta, flat, pn):
    m = meta['material']
    n = ['Dimensions in mm, inches in brackets.  Model: mechanical/step/%s_*.step is the master geometry; this sheet '
         'governs tolerances.' % pn,
         'General tolerances ISO 2768-mK unless stated: linear +/-0.2 (to 120), +/-0.3 (to 400), +/-0.5 (to 1000); '
         'hole positions +/-0.1; tapped and fitted holes per call-out.',
         'Break all sharp edges 0.3-0.5 x 45 deg.  Deburr every hole both sides.  Surface Ra 3.2 unless stated.']
    if 'Cu' in m or 'C11000' in m:
        n.append('Copper: C11000 ETP, half hard.  Contact faces flat within 0.1 over the lug / stud areas, no plating '
                 'build-up in holes; bright tin 5-8 um after machining.  Contact faces with joint compound at assembly.')
    if '6061' in m or '6063' in m or '5052' in m:
        n.append('Aluminium: anodise after all machining.  Mask tapped holes and electrical bond points (mark "BOND").')
    if 'S355' in m:
        n.append('Weldment: MIG, continuous fillet a3 on outside seams, stitch 30/100 inside.  Stress-relieve not required.'
                 '  Powder coat after machining of the deck holes.')
    if 'EPDM' in m:
        n.append('Die cut from 60 Shore A EPDM sheet, tolerance +/-0.3, peel-and-stick acrylic adhesive on one face.')
    if 'PETG' in m or 'ASA' in m:
        n.append('3D printed: 0.2 mm layers, 4 walls, 25 % gyroid; print file in prototype/print (Bambu Studio).')
    if flat:
        n.append('Flat profile: cut from the DXF %s.dxf (1:1, mm; layer CUT = through profile).  Counterbores, spot '
                 'faces and tapped holes are machined after cutting.' % pn)
    n.append('Mark part number %s rev %s with a vibro-etch or label on a non-functional face.' % (pn, REV))
    return n


def write_dxf(shape, pn, H, V, Dp, idp, lo, hi):
    """through profile = section near one face intersected with the section near the other face"""
    try:
        t0, t1 = lo[idp], hi[idp]
        def sec(at):
            return section_faces(shape, idp, at)
        fa, fb = sec(t0 + 0.05), sec(t1 - 0.05)
        if not fa or not fb:
            return None
        pl = Plane(origin=lo, x_dir=H, z_dir=Dp)
        A = Compound(children=[pl.to_local_coords(f) for f in fa])
        B = Compound(children=[pl.to_local_coords(f) for f in fb])
        # flatten both to z = 0 then intersect
        A = Pos(0, 0, -A.bounding_box().min.Z) * A
        B = Pos(0, 0, -B.bounding_box().min.Z) * B
        prof = A.intersect(B) if hasattr(A, 'intersect') else A
        faces = [f for f in (prof.faces() if prof else [])] or list(A.faces())
        exp = ExportDXF(unit=Unit.MM, line_weight=0.35)
        exp.add_layer('CUT', color=None, line_type=LineType.CONTINUOUS)
        for f in faces:
            exp.add_shape(f.edges(), layer='CUT')
        path = os.path.join(DXF, pn + '.dxf')
        exp.write(path)
        return path
    except Exception:
        traceback.print_exc()
        return None


def index_sheet(pdf_all, rows):
    fig = plt.figure(figsize=(A3[0] / IN, A3[1] / IN))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, A3[0])
    ax.set_ylim(0, A3[1])
    ax.axis('off')
    ax.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=0.8))
    ax.text(20, 275, 'TS-2 rev B  -  mechanical drawing set (made parts)', fontsize=12, fontweight='bold')
    ax.text(20, 268, 'Generated %s from the parametric CAD (mechanical/cad/parts.py).  Dual units: mm [in].  Third angle.  '
                     'DXF cut files in drawings/dxf.  Assembly: TS2B-ASM-100 (illustrated GPU column build).' % DATE, fontsize=6)
    hdr = ['Drawing', 'Title', 'Material', 'Finish', 'Qty/tower', 'Mass kg', 'Holes', 'DXF', 'Scale']
    xs = [20, 48, 150, 232, 300, 320, 340, 356, 368]
    y = 258
    for x, hname in zip(xs, hdr):
        ax.text(x, y, hname, fontsize=5.4, fontweight='bold')
    ax.plot([20, 400], [y - 1.5, y - 1.5], 'k-', lw=0.4)
    for r in rows:
        y -= 6.2
        vals = [r['pn'], r['title'][:52], r['material'][:42], (r['finish'] or '')[:34], str(r['qty']), '%.3f' % r['mass'],
                str(r['holes']), 'yes' if r['dxf'] else '-', r['scale']]
        for x, v in zip(xs, vals):
            ax.text(x, y, v, fontsize=5.0)
    pdf_all.savefig(fig)
    fig.savefig(os.path.join(PDF, 'TS2B-DWG-000_index.pdf'))
    plt.close(fig)


def main(only=None):
    todo = [p for p in PARTS if not only or p[0] in only]
    rows = []
    tmp = os.path.join(HERE, '_parts.pdf')
    with PdfPages(tmp) as pdf_all:
        for i, e in enumerate(todo):
            try:
                rows.append(make_sheet(e, pdf_all, i + 2, len(todo) + 1))
            except Exception:
                print('FAILED', e[0])
                traceback.print_exc()
    with PdfPages(os.path.join(HERE, 'TS2B-DWG_set.pdf')) as pdf_all:
        index_sheet(pdf_all, rows)
    # merge: index first, then the part sheets
    from pypdf import PdfWriter, PdfReader
    w = PdfWriter()
    for f in [x for x in (os.path.join(HERE, "TS2B-DWG_set.pdf"), tmp) if os.path.exists(x)]:
        for pg in PdfReader(f).pages:
            w.add_page(pg)
    with open(os.path.join(HERE, 'TS2B-DWG_set_full.pdf'), 'wb') as fh:
        w.write(fh)
    os.replace(os.path.join(HERE, 'TS2B-DWG_set_full.pdf'), os.path.join(HERE, 'TS2B-DWG_set.pdf'))
    if os.path.exists(tmp):
        os.remove(tmp)
    print('sheets', len(rows), 'of', len(todo))


if __name__ == '__main__':
    main(sys.argv[1:] or None)
