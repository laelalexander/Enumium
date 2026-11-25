"""Write a hierarchical KiCad 7 schematic from a Design: a root sheet with one sub-sheet per design sheet.

Every connected pin gets a short wire stub and a global label with its net name (global labels connect across
sheets); no-connect pins get a no-connect flag.  Parts are packed in rows from the symbol pin geometry so labels
do not overlap.  Sheet notes are printed under the parts.
"""
import math
import os
import uuid

import symlib
from core import LIBNAME, LIBSYM
from sexpr import Sym, dump, find, findall

symlib.EXTRA[LIBNAME] = LIBSYM
S = Sym
STUB = 2.54
GRID = 1.27
CHARW = 1.05
DIRS = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}


def g(v):
    return round(round(v / GRID) * GRID, 4)


def font(size=1.27, bold=False):
    f = [S('font'), [S('size'), size, size]]
    if bold:
        f.append(S('bold'))
    return f


def xform(px, py, rot):
    r = math.radians(rot)
    return px * math.cos(r) - py * math.sin(r), px * math.sin(r) + py * math.cos(r)


class Writer:
    def __init__(self, D, outdir):
        self.D = D
        self.out = outdir
        self.ns = uuid.uuid5(uuid.NAMESPACE_URL, 'ts2b-kgen/' + D.project)
        self.root = self.U('root')
        self.libsyms = {}

    def U(self, key):
        return str(uuid.uuid5(self.ns, key))

    def lib(self, lid):
        if lid not in self.libsyms:
            self.libsyms[lid] = symlib.load(lid)
        return self.libsyms[lid]

    # ------------------------------------------------------------------ primitives
    def prop(self, name, value, x, y, ang=0, hide=False, justify=None, size=1.27):
        eff = [S('effects'), font(size)]
        if justify:
            eff.append([S('justify')] + [S(j) for j in justify])
        if hide:
            eff.append(S('hide'))
        return [S('property'), name, value, [S('at'), x, y, ang], eff]

    def wire(self, items, x1, y1, x2, y2):
        items.append([S('wire'), [S('pts'), [S('xy'), x1, y1], [S('xy'), x2, y2]],
                      [S('stroke'), [S('width'), 0], [S('type'), S('default')]], [S('uuid'), self.U('w%s%s%s%s%s' % (id(items), x1, y1, x2, y2))]])

    def label(self, items, net, x, y, ang, key):
        just = 'left' if ang in (0, 90) else 'right'
        items.append([S('global_label'), net, [S('shape'), S('passive')], [S('at'), x, y, ang], [S('fields_autoplaced')],
                      [S('effects'), font(), [S('justify'), S(just)]], [S('uuid'), self.U('lbl' + key)],
                      [S('property'), 'Intersheetrefs', '${INTERSHEET_REFS}', [S('at'), x, y, 0],
                       [S('effects'), font(), S('hide')]]])

    def noconn(self, items, x, y, key):
        items.append([S('no_connect'), [S('at'), x, y], [S('uuid'), self.U('nc' + key)]])

    def text(self, items, s, x, y, size=1.27, bold=False):
        items.append([S('text'), s, [S('at'), x, y, 0], [S('effects'), font(size, bold), [S('justify'), S('left'), S('bottom')]],
                      [S('uuid'), self.U('txt' + s + str(x) + str(y))]])

    def frame(self, items, x1, y1, x2, y2, title):
        items.append([S('rectangle'), [S('start'), x1, y1], [S('end'), x2, y2],
                      [S('stroke'), [S('width'), 0.15], [S('type'), S('dash')]], [S('fill'), [S('type'), S('none')]],
                      [S('uuid'), self.U('fr' + title + str(y1))]])
        self.text(items, title, x1 + 1.5, y1 + 4.5, 2.0, True)

    # ------------------------------------------------------------------ symbols
    def style_of(self, part):
        s = part['sym']
        if s in ('Device:R', 'Device:C', 'Device:Thermistor_NTC', 'Device:C_Polarized', 'Device:L', 'Device:Polyfuse',
                 'Device:Fuse', 'Device:FerriteBead_Small'):
            return 90, 'h2'
        if s in ('Device:LED', 'Switch:SW_Push', 'Device:D_TVS') or s.startswith('Diode:PMEG'):
            return 0, 'h2'
        return 0, 'lib'

    def outward(self, p, rot):
        return (p['angle'] + 180 + rot) % 360

    def extent(self, part):
        rot, style = self.style_of(part)
        node = self.lib(part['sym'])
        xs, ys = [], []
        pmap = part['pins']
        for p in symlib.pins(node):
            dx, dy = xform(p['x'], p['y'], rot)
            px, py = dx, -dy
            xs.append(px)
            ys.append(py)
            net = pmap.get(p['number'])
            if net is None:
                continue
            ox, oy = DIRS[self.outward(p, rot)]
            L = STUB + len(net) * CHARW + 2.5
            xs.append(px + ox * L)
            ys.append(py + oy * L if oy else py)
        for sub in findall(node, 'symbol'):
            for r in findall(sub, 'rectangle'):
                for k in ('start', 'end'):
                    a = find(r, k)
                    dx, dy = xform(float(a[1]), float(a[2]), rot)
                    xs.append(dx)
                    ys.append(-dy)
        if not xs:
            xs, ys = [-3, 3], [-3, 3]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if style == 'lib':
            y0 -= 3.5
            y1 += 3.5
        else:
            y0 -= 3.0
            y1 += 3.5
            w = max(len(part['ref']), len(part['value'])) * CHARW
            x0, x1 = min(x0, -w / 2), max(x1, w / 2)
        return x0 - 1.0, y0, x1 + 1.0, y1

    def place(self, items, part, x, y, path):
        ref = part['ref']
        rot, style = self.style_of(part)
        x, y = g(x), g(y)
        lid = part['sym']
        node = self.lib(lid)
        pinlist = symlib.pins(node)
        libprops = {p[1]: p for p in findall(node, 'property')}
        sym = [S('symbol'), [S('lib_id'), lid], [S('at'), x, y, rot], [S('unit'), 1],
               [S('in_bom'), S('yes' if part.get('bom', True) else 'no')], [S('on_board'), S('yes')],
               [S('dnp'), S('yes' if part.get('dnp') else 'no')], [S('uuid'), self.U('sym' + ref)]]
        fang = 90 if rot in (90, 270) else 0

        def libpos(name):
            at = find(libprops[name], 'at')
            dx, dy = xform(float(at[1]), float(at[2]), rot)
            eff = find(libprops[name], 'effects')
            j = find(eff, 'justify')
            return round(x + dx, 3), round(y - dy, 3), ([str(v) for v in j[1:]] if j else None)

        if style == 'lib':
            rx, ry, rj = libpos('Reference')
            vx, vy, vj = libpos('Value')
        else:
            rx, ry, rj = x, y - 2.6, None
            vx, vy, vj = x, y + 3.2, None
        sym.append(self.prop('Reference', ref, rx, ry, fang, justify=rj))
        sym.append(self.prop('Value', part['value'], vx, vy, fang, justify=vj))
        sym.append(self.prop('Footprint', part.get('fp', ''), x, y, 0, hide=True))
        ds = libprops.get('Datasheet')
        sym.append(self.prop('Datasheet', ds[2] if ds else '', x, y, 0, hide=True))
        sym.append(self.prop('Description', part.get('desc', ''), x, y, 0, hide=True))
        for nm, key in (('MPN', 'mpn'), ('Manufacturer', 'mfr'), ('Supplier_PN', 'spn'), ('LCSC', 'lcsc')):
            sym.append(self.prop(nm, part.get(key, ''), x, y, 0, hide=True))
        for p in pinlist:
            sym.append([S('pin'), p['number'], [S('uuid'), self.U('pin' + ref + p['number'])]])
        sym.append([S('instances'), [S('project'), self.D.project,
                                     [S('path'), path, [S('reference'), ref], [S('unit'), 1]]]])
        items.append(sym)
        pmap = part['pins']
        nums = [p['number'] for p in pinlist]
        for p in pinlist:
            if p['number'] not in pmap and p['type'] != 'no_connect':
                raise KeyError('%s pin %s (%s) missing in design table' % (ref, p['number'], p['name']))
        for num in pmap:
            if num not in nums:
                raise KeyError('%s: design pin %s not in symbol %s' % (ref, num, lid))
        done = {}
        for p in pinlist:
            if p['number'] not in pmap:
                continue
            net = pmap[p['number']]
            dx, dy = xform(p['x'], p['y'], rot)
            px, py = round(x + dx, 3), round(y - dy, 3)
            key = (px, py)
            if key in done:
                assert done[key] == net, '%s stacked pins %s on different nets' % (ref, p['number'])
                continue
            done[key] = net
            if net is None:
                if p['type'] != 'no_connect':
                    self.noconn(items, px, py, ref + p['number'])
                continue
            ox, oy = DIRS[self.outward(p, rot)]
            ex, ey = round(px + ox * STUB, 3), round(py + oy * STUB, 3)
            self.wire(items, px, py, ex, ey)
            self.label(items, net, ex, ey, self.outward(p, rot), ref + p['number'])

    # ------------------------------------------------------------------ sheets
    def layout(self, refs, path, title, notes):
        items = []
        W = 420.0
        M = 12.0
        FW = W - 2 * M
        fx0, fy0 = M, 18.0
        cx, cy = fx0 + 4.0, fy0 + 8.0
        row_h = 0.0
        for ref in refs:
            part = self.D.byref[ref]
            x0, y0, x1, y1 = self.extent(part)
            w, h = x1 - x0, y1 - y0
            if cx + w > fx0 + FW - 2 and cx > fx0 + 4.0:
                cx = fx0 + 4.0
                cy += row_h + 4.0
                row_h = 0.0
            self.place(items, part, cx - x0 + 0.6, cy - y0 + 0.6, path)
            cx += w + 4.0
            row_h = max(row_h, h)
        fy1 = cy + row_h + 3.0
        self.frame(items, fx0, fy0, fx0 + FW, fy1, title)
        y = fy1 + 8.0
        for s in notes:
            self.text(items, s, M + 2, y, 1.6)
            y += 5.0
        H = max(297.0, math.ceil((y + 20) / 10) * 10)
        return items, W, H

    def header(self, uid, W, H, title, sheet_no):
        D = self.D
        return [S('kicad_sch'), [S('version'), 20230121], [S('generator'), S('eeschema')], [S('uuid'), uid],
                [S('paper'), 'User', W, H],
                [S('title_block'), [S('title'), D.title + (' - ' + title if title else '')], [S('date'), '2026-11-24'],
                 [S('rev'), D.rev], [S('company'), 'TS-2 rev B 64-GPU tower'],
                 [S('comment'), 1, 'Generated by kgen from boards/%s/design.py - do not hand-edit' % D.project],
                 [S('comment'), 2, 'Machine-generated; engineering review required before release'],
                 [S('comment'), 3, 'Sheet %d' % sheet_no]]]

    def write(self):
        D = self.D
        os.makedirs(self.out, exist_ok=True)
        # sub-sheets
        sheet_syms = []
        files = []
        for k, (name, refs) in enumerate(D.sheets):
            suid = self.U('sheet' + name)
            fname = '%s_%02d_%s.kicad_sch' % (D.project, k + 1, ''.join(c if c.isalnum() else '_' for c in name.lower()).strip('_'))
            path = '/%s/%s' % (self.root, suid)
            items, W, H = self.layout(refs, path, name, D.sheet_notes.get(name, []))
            libs = sorted({self.D.byref[r]['sym'] for r in refs})
            root = self.header(self.U('file' + name), W, H, name, k + 2)
            root.append([S('lib_symbols')] + [self.lib(l) for l in libs])
            root += items
            with open(os.path.join(self.out, fname), 'w', encoding='utf-8', newline='\n') as f:
                f.write(dump(root))
            files.append(fname)
            sheet_syms.append((suid, name, fname, k + 2))
        # root sheet: one sheet symbol per sub-sheet + notes
        items = []
        cols = 4
        for j, (suid, name, fname, page) in enumerate(sheet_syms):
            x = 20 + (j % cols) * 95
            y = 30 + (j // cols) * 40
            items.append([S('sheet'), [S('at'), x, y], [S('size'), 80, 25], [S('fields_autoplaced')],
                          [S('stroke'), [S('width'), 0.1524], [S('type'), S('solid')]],
                          [S('fill'), [S('color'), 0, 0, 0, 0.0]], [S('uuid'), suid],
                          [S('property'), 'Sheetname', name, [S('at'), x, y - 0.7, 0],
                           [S('effects'), font(), [S('justify'), S('left'), S('bottom')]]],
                          [S('property'), 'Sheetfile', fname, [S('at'), x, y + 25.6, 0],
                           [S('effects'), font(), [S('justify'), S('left'), S('top')]]],
                          [S('instances'), [S('project'), D.project, [S('path'), '/' + self.root, [S('page'), str(page)]]]]])
        y = 30 + ((len(sheet_syms) + cols - 1) // cols) * 40 + 10
        for s in D.notes:
            self.text(items, s, 20, y, 1.8)
            y += 6.0
        H = max(297.0, math.ceil((y + 20) / 10) * 10)
        root = self.header(self.root, 420.0, H, '', 1)
        root.append([S('lib_symbols')])
        root += items
        root.append([S('sheet_instances'), [S('path'), '/', [S('page'), '1']]])
        with open(os.path.join(self.out, D.project + '.kicad_sch'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(dump(root))
        print('schematic: root + %d sheets, %d symbols' % (len(files), len(D.parts)))
        return files


def write(D, outdir):
    return Writer(D, outdir).write()
