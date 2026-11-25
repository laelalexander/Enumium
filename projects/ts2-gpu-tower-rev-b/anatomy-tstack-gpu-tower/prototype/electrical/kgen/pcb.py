"""Board build with KiCad 7 pcbnew: placement, nets, pre-routed differential pairs, pours, Freerouting, DRC.

  place(D, out, padnet)   -> <project>.kicad_pcb placed (+ pre-routed tracks, rule areas) and build/<project>.dsn
  route(D, out)           -> Freerouting (headless) -> build/<project>.ses
  finish(D, out, padnet)  -> re-place, import SES, pours, stitching vias, fill, stackup, DRC report
"""
import math
import os
import subprocess
import uuid

import pcbnew
from core import LIBNAME, LIBFP

mm = pcbnew.FromMM
tomm = pcbnew.ToMM
FPDIR = '/usr/share/kicad/footprints'
FREEROUTING = os.environ.get('FREEROUTING_JAR', '/tmp/freerouting.jar')
CU = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu, 'In3': pcbnew.In3_Cu,
      'In4': pcbnew.In4_Cu, 'In5': pcbnew.In5_Cu, 'In6': pcbnew.In6_Cu}


class Ctx:
    def __init__(self, D):
        self.D = D

    def V(self, x, y):
        return pcbnew.VECTOR2I(mm(self.D.X0 + x), mm(self.D.Y0 + self.D.H - y))

    def bd(self, v):
        return (tomm(v.x) - self.D.X0, self.D.Y0 + self.D.H - tomm(v.y))


def _sd(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def plane_checker(D, c):
    """f(net, x, y) -> True when (x, y) (page mm) lies inside a power-layer plane of that net that no higher-priority
    pour of another net covers on the same layer."""
    PL = getattr(D, 'power_layers', ())
    polys = []
    for z in D.pours:
        pts = z.get('poly') or rect_pts(*z['rect'])
        polys.append((z['net'], z['layer'], z.get('prio', 0),
                      [(pcbnew.ToMM(v.x), pcbnew.ToMM(v.y)) for v in (c.V(px, py) for px, py in pts)]))

    def inside(pt, poly):
        x, y = pt
        n, ins = len(poly), False
        for i in range(n):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                ins = not ins
        return ins

    def ok(net, x, y):
        for (n1, l1, p1, poly) in polys:
            if n1 != net or l1 not in PL:
                continue
            if not all(inside((x + dx, y + dy), poly) for dx, dy in ((0.6, 0), (-0.6, 0), (0, 0.6), (0, -0.6))):
                continue
            if any(n2 != net and l2 == l1 and p2 > p1 and inside((x, y), q) for (n2, l2, p2, q) in polys):
                continue
            return True
        return False
    ok.nets = {z['net'] for z in D.pours if z['layer'] in PL}
    return ok


def lset(*layers):
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    return ls


def add_line(board, c, a, b, layer, width=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(c.V(*a))
    s.SetEnd(c.V(*b))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)


def add_arc(board, c, start, mid, end, layer, width=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(c.V(*start), c.V(*mid), c.V(*end))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)


def add_text(board, c, txt, x, y, layer, size=1.0, angle=0, just=None):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(max(0.15, size * 0.15)))
    t.SetPosition(c.V(x, y))
    t.SetTextAngleDegrees(angle)
    if layer in (pcbnew.B_SilkS, pcbnew.B_Fab):
        t.SetMirrored(True)
    if just == 'left':
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)


def outline(board, c):
    D = c.D
    W, H, R = D.W, D.H, D.corner_r
    k = R * (1 - math.sqrt(0.5))
    E = pcbnew.Edge_Cuts
    add_line(board, c, (R, 0), (W - R, 0), E)
    add_line(board, c, (W, R), (W, H - R), E)
    add_line(board, c, (W - R, H), (R, H), E)
    add_line(board, c, (0, H - R), (0, R), E)
    add_arc(board, c, (W - R, 0), (W - k, k), (W, R), E)
    add_arc(board, c, (W, H - R), (W - k, H - k), (W - R, H), E)
    add_arc(board, c, (R, H), (k, H - k), (0, H - R), E)
    add_arc(board, c, (0, R), (k, k), (R, 0), E)


def poly_zone(board, c, pts, layers, net=None, name='', rule=False, prio=0, clearance=0.25, minw=0.25,
              thermal=True, no_tracks=True, no_vias=True, no_pour=True):
    z = pcbnew.ZONE(board)
    z.SetLayerSet(lset(*layers))
    if rule:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(no_tracks)
        z.SetDoNotAllowVias(no_vias)
        z.SetDoNotAllowCopperPour(no_pour)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
    else:
        z.SetNet(board.FindNet(net))
        z.SetLocalClearance(mm(clearance))
        z.SetMinThickness(mm(minw))
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.5))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL if thermal == 'tht' else
                        pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetAssignedPriority(prio)
    z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        p = c.V(x, y)
        o.Append(p.x, p.y)
    board.Add(z)
    return z


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circle_pts(cx, cy, r, n=32):
    rr = r / math.cos(math.pi / n)
    return [(cx + rr * math.cos(2 * math.pi * i / n), cy + rr * math.sin(2 * math.pi * i / n)) for i in range(n)]


def load_fp(lid):
    lib, name = lid.split(':')
    path = LIBFP if lib == LIBNAME else os.path.join(FPDIR, lib + '.pretty')
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit('footprint not found: ' + lid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ---------------------------------------------------------------------------
def build(D, out, padnet, ses=None):
    c = Ctx(D)
    pcbpath = os.path.join(out, D.project + '.kicad_pcb')
    board = pcbnew.NewBoard(pcbpath)
    board.SetCopperLayerCount(D.layers)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(D.thickness))
    outline(board, c)
    nets = {}
    allnets = set()
    for ref in padnet:
        allnets |= set(padnet[ref].values())
    for p in D.prerouted:
        allnets.add(p['net'])
    for z in D.pours:
        allnets.add(z['net'])
    for name in sorted(allnets):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni
    fps = {}

    def make(part, rot, side):
        fp = load_fp(part['fp'])
        fp.SetReference(part['ref'])
        fp.SetValue(part['value'])
        board.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(0, 0))
        fp.SetOrientationDegrees(rot)
        if side == 'B':
            fp.Flip(pcbnew.VECTOR2I(0, 0), True)
        return fp

    def anchor(fp, ref):
        if ref.startswith('H') or not len(fp.Pads()):
            return fp.GetPosition()
        return fp.GetPosition()

    def crt(fp):
        try:
            lay = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
            b = fp.GetCourtyard(lay).BBox()
            if b.GetWidth() <= 0:
                raise ValueError
        except Exception:
            b = fp.GetBoundingBox(False, False)
        return b

    for ref, pl in D.place.items():
        x, y, rot = pl[:3]
        side = pl[3] if len(pl) > 3 else D.byref[ref].get('side', 'F')
        fp = make(D.byref[ref], rot, side)
        fp.SetPosition(c.V(x, y))
        fps[ref] = fp
    for reg in D.regions:
        (x0, y0, x1, y1), refs, side = reg if len(reg) == 3 else (reg[0], reg[1], 'F')
        cx, cy, row_h = x0, y1, 0.0
        made = []
        for ref in refs:
            fp = make(D.byref[ref], D.pack_rot.get(ref, 0), side)
            made.append((ref, fp, crt(fp)))
        for ref, fp, b in made:
            w, h = tomm(b.GetWidth()), tomm(b.GetHeight())
            for _ in range(20):
                if cx + w > x1 + 1e-6:
                    cx, cy, row_h = x0, cy - row_h - D.pack_gap, 0.0
                # keep clear of mounting holes (pad radius + 0.6 mm)
                hit = [hx for hx, hy in D.holes
                       if max(cx - 4.0, min(hx, cx + w + 4.0)) == hx and cy - h - 4.0 <= hy <= cy + 4.0
                       and math.hypot(max(cx - hx, 0, hx - cx - w), max(cy - h - hy, 0, hy - cy)) < 4.0]
                # other holes / spots to keep clear of (x, y, r): e.g. connector locating-peg NPTHs
                for hx, hy, hr in getattr(D, 'pack_avoid', ()):
                    if math.hypot(max(cx - hx, 0, hx - cx - w), max(cy - h - hy, 0, hy - cy)) < hr:
                        hit.append(hx + hr - 4.0)
                if not hit:
                    break
                cx = max(hit) + 4.0
            if cy - h < y0 - 1e-6:
                raise SystemExit('region %s full at %s' % ((x0, y0, x1, y1), ref))
            pos = fp.GetPosition()
            ox, oy = tomm(pos.x - b.GetX()), tomm(pos.y - b.GetY())
            fp.SetPosition(c.V(cx + ox, cy - oy))
            fps[ref] = fp
            cx += w + D.pack_gap
            row_h = max(row_h, h)
    missing = [p['ref'] for p in D.parts if p['ref'] not in fps]
    if missing:
        raise SystemExit('no placement for: ' + ' '.join(missing[:40]))
    ns_uuid = uuid.uuid5(uuid.NAMESPACE_URL, 'ts2b-kgen/' + D.project)
    root = str(uuid.uuid5(ns_uuid, 'root'))
    for part in D.parts:
        ref = part['ref']
        fp = fps[ref]
        for nm, key in (('MPN', 'mpn'), ('Manufacturer', 'mfr'), ('Supplier_PN', 'spn'), ('Description', 'desc')):
            fp.SetProperty(nm, part.get(key, '') or '')
        sheet_uuid = str(uuid.uuid5(ns_uuid, 'sheet' + part['sheet']))
        fp.SetPath(pcbnew.KIID_PATH('/%s/%s' % (sheet_uuid, str(uuid.uuid5(ns_uuid, 'sym' + ref)))))
        attrs = fp.GetAttributes()
        if not part.get('bom', True):
            attrs |= pcbnew.FP_EXCLUDE_FROM_BOM
        if not part.get('pos', True):
            attrs |= pcbnew.FP_EXCLUDE_FROM_POS_FILES
        if part.get('dnp'):
            attrs |= getattr(pcbnew, 'FP_DNP', 0)
        fp.SetAttributes(attrs)
        r = fp.Reference()
        small = ref[0] in 'RCDLQ' or ref.startswith('TP')
        r.SetTextSize(pcbnew.VECTOR2I(mm(0.6 if small else 1.0), mm(0.6 if small else 1.0)))
        r.SetTextThickness(mm(0.1 if small else 0.15))
        r.SetVisible(not small)
        fp.Value().SetVisible(False)
        pn = padnet.get(ref, {})
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num in pn:
                pad.SetNet(nets[pn[num]])
    # fan-out: every SMD pad on a plane net gets a short locked stub + via into the plane.  Freerouting treats plane
    # nets as already connected and does not always drop the via itself.  Spots are clearance-checked against
    # every other-net pad (the via is through-hole) and against the vias already placed.
    plane_nets = {z['net'] for z in D.pours if z['layer'] in getattr(D, 'power_layers', ())}
    fdia, fdrill = getattr(D, 'fanout_via', (0.6, 0.3))
    nfan, nskip = 0, 0
    skipped = []
    if plane_nets and getattr(D, 'fanout', False):
        def bxy(p):
            return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        padobs = []
        for fp in fps.values():
            for p in fp.Pads():
                bb = p.GetBoundingBox()
                (ax, ay), (bx, by) = bxy(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())), bxy(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
                padobs.append((p.GetNetname(), ax, ay, bx, by))
        placed = []
        stubsegs = []                 # (net, x0, y0, x1, y1) of fan-out stubs already placed
        for hx, hy in D.holes:
            placed.append((c.V(hx, hy), 3.5))
        edge = (D.X0 + 0.8, D.Y0 + 0.8, D.X0 + D.W - 0.8, D.Y0 + D.H - 0.8)

        plane_ok = plane_checker(D, c)

        preobs = []                    # pre-routed copper (lane pairs, via arrays): through vias must clear it on every layer
        for p_ in D.prerouted:
            if 'at' in p_:
                q = bxy(c.V(*p_['at']))
                preobs.append((p_['net'], q[0], q[1], q[0], q[1], p_.get('dia', 0.4) / 2))
            else:
                for a_, b_ in zip(p_['pts'][:-1], p_['pts'][1:]):
                    qa, qb = bxy(c.V(*a_)), bxy(c.V(*b_))
                    preobs.append((p_['net'], qa[0], qa[1], qb[0], qb[1], p_['width'] / 2))

        def spot_ok(net, x, y, sx=None, sy=None):
            if not (edge[0] < x < edge[2] and edge[1] < y < edge[3]):
                return False
            if not plane_ok(net, x, y):
                return False
            samples = [(x, y, fdia / 2 + 0.25)]
            if sx is not None:
                for k in range(1, 12):
                    samples.append((sx + (x - sx) * k / 12.0, sy + (y - sy) * k / 12.0, 0.125 + 0.2))
            for (n2, ax, ay, bx, by) in padobs:
                if n2 == net and n2:
                    continue
                for (qx, qy, r) in samples:
                    dx = max(ax - qx, 0.0, qx - bx)
                    dy = max(ay - qy, 0.0, qy - by)
                    if math.hypot(dx, dy) < r:
                        return False
            for (v, rr) in placed:
                vx, vy = bxy(v)
                for (qx, qy, r) in samples:
                    if math.hypot(vx - qx, vy - qy) < rr + r - 0.05:
                        return False
                if math.hypot(vx - x, vy - y) < rr + fdia / 2 + 0.2:
                    return False
            for (n2, a0, b0, a1, b1, rr) in preobs:
                if n2 == net or max(a0, a1) < x - 3 or min(a0, a1) > x + 3 or max(b0, b1) < y - 3 or min(b0, b1) > y + 3:
                    continue
                if _sd(x, y, a0, b0, a1, b1) < rr + fdia / 2 + 0.2:
                    return False
            for (n2, a0, b0, a1, b1) in stubsegs:
                if n2 == net:
                    continue
                for (qx, qy, r) in samples:
                    if _sd(qx, qy, a0, b0, a1, b1) < r + 0.125:
                        return False
            return True
        for ref, fp in fps.items():
            if ref in getattr(D, 'no_fanout', ()):
                continue
            cpos = fp.GetPosition()
            for pad in fp.Pads():
                if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or pad.GetNetname() not in plane_nets:
                    continue
                if '%s.%s' % (ref, pad.GetNumber()) in getattr(D, 'no_fanout_pads', ()):
                    continue              # joined through its own-layer pour instead (named in the design)
                if getattr(D, 'fanout_skip_poured', False):
                    # a pad already inside a solid pour of its own net on its own layer needs no via (frees escape room)
                    side = 'B' if fp.IsFlipped() else 'F'
                    qx, qy = bxy(pad.GetPosition())
                    if any(po['net'] == pad.GetNetname() and po['layer'] == side and not po.get('thermal', True)
                           and D.X0 + po['rect'][0] + 1 < qx < D.X0 + po['rect'][2] - 1
                           and D.Y0 + D.H - po['rect'][3] + 1 < qy < D.Y0 + D.H - po['rect'][1] - 1 for po in getattr(D, 'pours', [])):
                        continue
                pp = pad.GetPosition()
                bb = pad.GetBoundingBox()
                hw, hh = pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2
                dx, dy = pp.x - cpos.x, pp.y - cpos.y
                if math.hypot(dx, dy) < mm(0.3):
                    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                elif abs(dx) > abs(dy):
                    s0 = 1 if dx > 0 else -1
                    dirs = [(s0, 0), (0, 1), (0, -1)]
                else:
                    s0 = 1 if dy > 0 else -1
                    dirs = [(0, s0), (1, 0), (-1, 0)]
                if '%s.%s' % (ref, pad.GetNumber()) in getattr(D, 'fanout_inward', ()):
                    dirs = [(-dirs[0][0], -dirs[0][1])] + dirs      # via under the part body: leaves the outside free
                px, py = bxy(pp)
                done = False
                for ux, uy in dirs:
                    half = hw if ux else hh
                    for extra in (0.35, 0.6, 0.9, 1.3):
                        reach = half + extra + fdia / 2
                        x, y = px + ux * reach, py + uy * reach
                        if spot_ok(pad.GetNetname(), x, y, px + ux * half, py + uy * half):
                            end = pcbnew.VECTOR2I(mm(x), mm(y))
                            t = pcbnew.PCB_TRACK(board)
                            t.SetStart(pp)
                            t.SetEnd(end)
                            t.SetWidth(mm(min(0.25, 2 * min(hw, hh))))
                            t.SetLayer(pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu)
                            t.SetNet(pad.GetNet())
                            t.SetLocked(True)
                            board.Add(t)
                            v = pcbnew.PCB_VIA(board)
                            v.SetPosition(end)
                            v.SetWidth(mm(fdia))
                            v.SetDrill(mm(fdrill))
                            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                            v.SetNet(pad.GetNet())
                            v.SetLocked(True)
                            board.Add(v)
                            placed.append((end, fdia / 2))
                            stubsegs.append((pad.GetNetname(), px, py, x, y))
                            padobs.append((pad.GetNetname(), x - 0.01, y - 0.01, x + 0.01, y + 0.01))
                            nfan += 1
                            done = True
                            break
                    if done:
                        break
                if not done:
                    nskip += 1
                    skipped.append('%s.%s' % (ref, pad.GetNumber()))
    if nfan or nskip:
        print('fan-out vias: %d (no clear spot: %d %s)' % (nfan, nskip, ' '.join(skipped[:16])))
    # courtyard overlap report (same side only)
    issues = []
    items = [(r, f, crt(f), f.IsFlipped()) for r, f in fps.items() if not r.startswith('H')]
    for i in range(len(items)):
        for k in range(i + 1, len(items)):
            if items[i][3] == items[k][3] and items[i][2].Intersects(items[k][2]):
                issues.append('%s %s' % (items[i][0], items[k][0]))
    # pre-routed copper (differential pairs, power straps)
    for p in D.prerouted:
        if 'at' in p:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(c.V(*p['at']))
            v.SetWidth(mm(p.get('dia', 0.4)))
            v.SetDrill(mm(p.get('drill', 0.2)))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNet(nets[p['net']])
            v.SetLocked(True)
            board.Add(v)
            continue
        pts = p['pts']
        for a, b in zip(pts[:-1], pts[1:]):
            if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(c.V(*a))
            t.SetEnd(c.V(*b))
            t.SetWidth(mm(p['width']))
            t.SetLayer(CU[p['layer']])
            t.SetNet(nets[p['net']])
            t.SetLocked(True)
            board.Add(t)
    # rule areas
    for k in D.keepouts:
        pts = circle_pts(*k['circle']) if 'circle' in k else (k['poly'] if 'poly' in k else rect_pts(*k['rect']))
        poly_zone(board, c, pts, [CU[l] for l in k['layers']], name=k['name'], rule=True,
                  no_tracks=k.get('tracks', True), no_vias=k.get('vias', True), no_pour=k.get('pour', True))
    # plane / pour zones (exported to the DSN as planes on inner layers, so Freerouting drops vias into them)
    for z in D.pours:
        pts = z.get('poly') or rect_pts(*z['rect'])
        poly_zone(board, c, pts, [CU[z['layer']]], net=z['net'], name=z.get('name', z['net'] + '_' + z['layer']),
                  prio=z.get('prio', 0), clearance=z.get('clearance', 0.25), thermal=z.get('thermal', True))
    LAY = {'F': pcbnew.F_SilkS, 'B': pcbnew.B_SilkS, 'FF': pcbnew.F_Fab, 'BF': pcbnew.B_Fab}
    for s in D.silk:
        add_text(board, c, s['t'], s['x'], s['y'], LAY[s.get('l', 'F')], s.get('size', 1.0), s.get('angle', 0), s.get('just'))
    return board, fps, issues


def place(D, out, padnet):
    os.makedirs(os.path.join(out, 'build'), exist_ok=True)
    board, fps, issues = build(D, out, padnet)
    pcbpath = os.path.join(out, D.project + '.kicad_pcb')
    pcbnew.SaveBoard(pcbpath, board)
    set_stackup(D, pcbpath)
    board = pcbnew.LoadBoard(pcbpath)          # reload so the net classes from <project>.kicad_pro apply
    with open(os.path.join(out, 'build', 'placement-check.txt'), 'w') as f:
        f.write('courtyard overlaps (same side): %d\n' % len(issues) + '\n'.join(issues) + '\n')
    dsn = os.path.join(out, 'build', D.project + '.dsn')
    ok = pcbnew.ExportSpecctraDSN(board, dsn)
    pl = getattr(D, 'power_layers', ())
    if pl:                       # plane-only layers: Freerouting must not route traces on them
        t = open(dsn).read()
        for l in pl:
            t = t.replace('(layer %s.Cu\n      (type signal)' % l, '(layer %s.Cu\n      (type power)' % l)
        open(dsn, 'w').write(t)
    print('placed %d footprints, %d nets, overlaps %d, dsn %s' % (len(fps), board.GetNetCount(), len(issues), ok))
    if issues:
        print('  overlaps:', issues[:20])
    return dsn


def route(D, out, passes=12, timeout=1800, threads=1):
    out = os.path.abspath(out)
    dsn = os.path.join(out, 'build', D.project + '.dsn')
    ses = os.path.join(out, 'build', D.project + '.ses')
    if os.path.exists(ses):
        os.remove(ses)
    os.makedirs(os.path.join(out, 'logs'), exist_ok=True)
    cmd = ['timeout', str(timeout), 'xvfb-run', '-a', 'java', '-Xmx3g', '-jar', FREEROUTING,
           '-de', dsn, '-do', ses, '-mp', str(passes), '-mt', str(threads)]
    with open(os.path.join(out, 'logs', 'freerouting.log'), 'w') as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=os.path.join(out, 'build'))
    print('freerouting exit', r.returncode, 'ses', os.path.exists(ses))
    return os.path.exists(ses)


def import_ses(board, path):
    """Read Freerouting's SES (wires + vias) into the board (pcbnew 7's ImportSpecctraSES needs the GUI board)."""
    import re
    from sexpr import parse, find, findall
    t = parse(open(path, encoding='utf-8').read())
    routes = find(t, 'routes')
    res = find(routes, 'resolution')
    k = 1000.0 / float(res[2])            # nm per unit ('um 10' -> 100 nm)
    lnames = {board.GetLayerName(l): l for l in range(pcbnew.PCB_LAYER_ID_COUNT) if pcbnew.IsCopperLayer(l)}
    nets = board.GetNetsByName()
    nw = nv = 0
    for n in findall(find(routes, 'network_out'), 'net'):
        name = str(n[1])
        net = nets[name] if nets.has_key(name) else None
        for w in findall(n, 'wire'):
            p = find(w, 'path')
            if p is None:
                continue
            lay = lnames[str(p[1])]
            width = int(float(p[2]) * k)
            xy = [float(v) for v in p[3:] if not isinstance(v, list)]
            pts = [(int(xy[i] * k), int(-xy[i + 1] * k)) for i in range(0, len(xy) - 1, 2)]
            for a, b in zip(pts[:-1], pts[1:]):
                if a == b:
                    continue
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(*a))
                tr.SetEnd(pcbnew.VECTOR2I(*b))
                tr.SetWidth(width)
                tr.SetLayer(lay)
                if net:
                    tr.SetNet(net)
                board.Add(tr)
                nw += 1
        for v in findall(n, 'via'):
            m = re.search(r'\[(\d+)-(\d+)\]_(\d+):(\d+)_um', str(v[1]))
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(int(float(v[2]) * k), int(-float(v[3]) * k)))
            dia, drill = (int(m.group(3)), int(m.group(4))) if m else (600, 300)
            via.SetWidth(dia * 1000)
            via.SetDrill(drill * 1000)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            if net:
                via.SetNet(net)
            board.Add(via)
            nv += 1
    print('SES: %d track segments, %d vias' % (nw, nv))
    return True


def fill(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def keepout_test(board):
    """f(x_mm, y_mm, layer or None, r_mm, via) -> True when copper of radius r at page point (x, y) would sit in a
    rule-area keep-out (layer None = a through via, every layer)."""
    kos = []
    for z in board.Zones():
        if not z.GetIsRuleArea():
            continue
        ol = z.Outline()
        bb = ol.BBox()
        kos.append((z.GetLayerSet(), ol, z.GetDoNotAllowTracks(), z.GetDoNotAllowVias(),
                    (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))))

    def hit(x, y, layer, r, via):
        for (ls, ol, nt, nv, (bx0, by0, bx1, by1)) in kos:
            if x < bx0 - r - 0.05 or x > bx1 + r + 0.05 or y < by0 - r - 0.05 or y > by1 + r + 0.05:
                continue
            if via and not nv:
                continue
            if not via and not nt:
                continue
            if layer is not None and not ls.Contains(layer):
                continue
            v = pcbnew.VECTOR2I(mm(x), mm(y))
            if ol.Contains(v) or math.sqrt(ol.SquaredDistance(v)) / 1e6 < r:
                return True
        return False
    return hit


def stitch_islands(board, c, netname, outer=('F', 'B'), drill=0.3, dia=0.6, gap=0.3):
    """Tie every outer-layer fill island of a plane net that holds no through via / THT pad of that net to the inner
    planes with one via inside it (an island fenced in by fan-out and pairs is otherwise left floating)."""
    D = c.D
    lid = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
    net = board.FindNet(netname)
    obst = []
    for t in board.GetTracks():
        if t.GetNetname() == netname:
            continue
        if t.GetClass() == 'PCB_VIA':
            q = t.GetPosition()
            obst.append((pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), pcbnew.ToMM(t.GetWidth()) / 2))
        else:
            a, b = t.GetStart(), t.GetEnd()
            obst.append((pcbnew.ToMM(a.x), pcbnew.ToMM(a.y), pcbnew.ToMM(b.x), pcbnew.ToMM(b.y), pcbnew.ToMM(t.GetWidth()) / 2))
    rects = []
    anchors = []
    holes = []                                  # every drilled hole, any net: hole-to-hole spacing
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            holes.append((pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y), pcbnew.ToMM(t.GetDrillValue()) / 2))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            q = p.GetPosition()
            if p.GetDrillSize().x > 0:
                holes.append((pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), pcbnew.ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2))
            if p.GetNetname() == netname and p.GetDrillSize().x > 0:
                anchors.append(q)
            if p.GetNetname() == netname and p.GetNetname():
                continue
            bb = p.GetBoundingBox()
            rects.append((pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())))
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() == netname:
            anchors.append(t.GetPosition())
    lim = dia / 2 + gap
    ko = keepout_test(board)

    def clear(x, y):
        for (x0, y0, x1, y1, r) in obst:
            if abs(x - x0) > 6 and abs(x - x1) > 6:
                continue
            if _sd(x, y, x0, y0, x1, y1) < r + lim:
                return False
        for (ax, ay, bx, by) in rects:
            if math.hypot(max(ax - x, 0, x - bx), max(ay - y, 0, y - by)) < lim:
                return False
        for (hx, hy, hr) in holes:
            if abs(hx - x) < 3 and math.hypot(hx - x, hy - y) < hr + drill / 2 + 0.35:
                return False
        return True
    def others(layer):
        return [z.GetFilledPolysList(l) for z in board.Zones() if z.GetNetname() == netname and not z.GetIsRuleArea()
                for l in z.GetLayerSet().Seq() if l != layer]
    n = 0
    for z in list(board.Zones()):
        if z.GetIsRuleArea() or z.GetNetname() != netname:
            continue
        for side in outer:
            l = lid[side]
            if not z.GetLayerSet().Contains(l):
                continue
            fpoly = z.GetFilledPolysList(l)
            inner = others(l)
            for i in range(fpoly.OutlineCount()):
                isl = pcbnew.SHAPE_POLY_SET()
                isl.AddOutline(fpoly.Outline(i))
                for h in range(fpoly.HoleCount(i)):
                    isl.AddHole(fpoly.Hole(i, h))
                if any(isl.Contains(a) for a in anchors):
                    continue
                bb = fpoly.Outline(i).BBox()
                x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
                x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
                if (x1 - x0) < dia or (y1 - y0) < dia:
                    continue
                done = False
                step = 0.2
                yy = y0 + dia / 2
                while yy <= y1 - dia / 2 and not done:
                    xx = x0 + dia / 2
                    while xx <= x1 - dia / 2:
                        v = pcbnew.VECTOR2I(mm(xx), mm(yy))
                        ring = [pcbnew.VECTOR2I(mm(xx + dx), mm(yy + dy)) for dx, dy in
                                ((dia / 2 + 0.05, 0), (-dia / 2 - 0.05, 0), (0, dia / 2 + 0.05), (0, -dia / 2 - 0.05))]
                        if all(isl.Contains(r) for r in [v] + ring) and clear(xx, yy) and not ko(xx, yy, None, dia / 2, True) and \
                                all(any(f.Contains(v) for f in inner_l) for inner_l in [inner] if inner_l):
                            via = pcbnew.PCB_VIA(board)
                            via.SetPosition(v)
                            via.SetWidth(mm(dia))
                            via.SetDrill(mm(drill))
                            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                            via.SetNet(net)
                            board.Add(via)
                            anchors.append(v)
                            holes.append((xx, yy, drill / 2))
                            n += 1
                            done = True
                            break
                        xx += step
                    yy += step
    return n


def stitch(board, c, netname, pitch, layers_need, exclude, drill=0.3, dia=0.6):
    """GND stitching vias on a grid where every listed layer's fill contains a ring around the point."""
    net = board.FindNet(netname)
    zs = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == netname]
    fills = []
    for z in zs:
        for l in z.GetLayerSet().Seq():
            if l in layers_need:
                fills.append(z.GetFilledPolysList(l))
    n = 0
    D = c.D
    # through vias: keep clear of every other-net track, via and pad on ALL copper layers (not only the stitch layers)
    gap = 0.35
    obst = {}

    def _add(x0, y0, x1, y1, r):
        for gx in range(int((min(x0, x1) - r - 2) // 4), int((max(x0, x1) + r + 2) // 4) + 1):
            for gy in range(int((min(y0, y1) - r - 2) // 4), int((max(y0, y1) + r + 2) // 4) + 1):
                obst.setdefault((gx, gy), []).append((x0, y0, x1, y1, r))

    def _bxy(p):
        return pcbnew.ToMM(p.x) - D.X0, D.Y0 + D.H - pcbnew.ToMM(p.y)
    for t in board.GetTracks():
        if t.GetNetname() == netname:
            continue
        if t.GetClass() == 'PCB_VIA':
            px, py = _bxy(t.GetPosition())
            _add(px, py, px, py, pcbnew.ToMM(t.GetWidth()) / 2)
        else:
            ax, ay = _bxy(t.GetStart())
            bx, by = _bxy(t.GetEnd())
            _add(ax, ay, bx, by, pcbnew.ToMM(t.GetWidth()) / 2)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == netname and p.GetNetname():
                continue
            bb = p.GetBoundingBox()
            ax, ay = _bxy(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
            bx, by = _bxy(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
            cxp, cyp = (ax + bx) / 2, (ay + by) / 2
            _add(cxp, cyp, cxp, cyp, math.hypot(bx - ax, by - ay) / 2)

    def _clear(x, y):
        for (x0, y0, x1, y1, r) in obst.get((int(x // 4), int(y // 4)), ()):
            dx, dy = x1 - x0, y1 - y0
            L = dx * dx + dy * dy
            t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / L))
            if math.hypot(x - (x0 + t * dx), y - (y0 + t * dy)) < r + dia / 2 + gap:
                return False
        return True
    ko = keepout_test(board)
    x = 2.0
    while x < D.W - 2.0:
        y = 2.0
        while y < D.H - 2.0:
            if not exclude(x, y) and _clear(x, y) and not ko(D.X0 + x, D.Y0 + D.H - y, None, dia / 2, True):
                ok = True
                for need in layers_need:
                    lf = [z.GetFilledPolysList(need) for z in zs if z.GetLayerSet().Contains(need)]
                    hit = False
                    for f in lf:
                        if all(f.Contains(c.V(x + r * math.cos(k * math.pi / 4), y + r * math.sin(k * math.pi / 4)))
                               for r in (0.0, dia / 2 + 0.25) for k in range(8)):
                            hit = True
                            break
                    if not hit:
                        ok = False
                        break
                if ok:
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(c.V(x, y))
                    v.SetWidth(mm(dia))
                    v.SetDrill(mm(drill))
                    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    v.SetNet(net)
                    board.Add(v)
                    n += 1
            y += pitch
        x += pitch
    return n


def finish(D, out, padnet):
    c = Ctx(D)
    board, fps, issues = build(D, out, padnet)
    ses = os.path.join(out, 'build', D.project + '.ses')
    ok = import_ses(board, ses) if os.path.exists(ses) else False
    # Freerouting returns the locked pre-routed copper too; drop exact duplicates
    seen = set()
    dup = []
    vias = {}
    for t in sorted(board.GetTracks(), key=lambda t: not t.IsLocked()):      # locked (pre-routed) copper wins
        if t.GetClass() == 'PCB_VIA':
            k = (round(t.GetPosition().x / 20000), round(t.GetPosition().y / 20000), t.GetNetCode())   # 20 um grid, per net
            if any((k[0] + a, k[1] + b, k[2]) in vias for a in (-1, 0, 1) for b in (-1, 0, 1)):
                dup.append(t)
                continue
            vias[k] = t
            continue
        key = (t.GetClass(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetLayer(), t.GetNetCode())
        if key in seen:
            dup.append(t)
        seen.add(key)
    for t in dup:
        board.Remove(t)
    stubs = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetLength() < mm(0.01)]
    for t in stubs:
        board.Remove(t)
    print('SES import', ok, 'tracks+vias', len(board.GetTracks()), 'duplicates removed', len(dup))
    pcbpath = os.path.join(out, D.project + '.kicad_pcb')
    pcbnew.SaveBoard(pcbpath, board)
    board = pcbnew.LoadBoard(pcbpath)
    fill(board)
    if D.stitch:
        holes = [(x, y) for x, y in D.holes]

        def excl(x, y):
            if any(math.hypot(x - hx, y - hy) < 5.0 for hx, hy in holes):
                return True
            for fp in board.GetFootprints():
                if fp.GetReference() in D.no_stitch:
                    bb = fp.GetBoundingBox(False, False)
                    (x0, y1), (x1, y0) = c.bd(bb.GetOrigin()), c.bd(bb.GetEnd())
                    if x0 - 0.5 <= x <= x1 + 0.5 and y0 - 0.5 <= y <= y1 + 0.5:
                        return True
            return False
        need = [CU[l] for l in D.stitch['layers']]
        n = stitch(board, c, D.stitch['net'], D.stitch['pitch'], need, excl)
        print('stitching vias:', n)
        fill(board)
        ni = sum(stitch_islands(board, c, n_) for n_ in sorted({z['net'] for z in D.pours if z['layer'] in ('F', 'B')}))
        if ni:
            print('island stitch vias:', ni)
            fill(board)
    # repair: read KiCad's own unconnected list and close what a straight / L track or a via can close cleanly
    tmp = os.path.join(out, 'build', 'repair-drc.rpt')
    pcbnew.WriteDRCReport(board, tmp, pcbnew.EDA_UNITS_MILLIMETRES, True)
    nrm = drop_clashes(board, tmp)
    if nrm:
        print('clearance clashes: removed %d unlocked track/via items (re-joined by the repair pass)' % nrm)
        fill(board)
    last_n = 10 ** 9
    for it in range(8):
        pcbnew.WriteDRCReport(board, tmp, pcbnew.EDA_UNITS_MILLIMETRES, True)
        if it:                    # copper a repair pass added can itself clash: drop it and let the next pass retry
            nrm2 = drop_clashes(board, tmp)
            if nrm2:
                print('  pass %d: removed %d clashing items' % (it + 1, nrm2))
                fill(board)
                pcbnew.WriteDRCReport(board, tmp, pcbnew.EDA_UNITS_MILLIMETRES, True)
        pairs = drc_pairs(tmp, board)
        if not pairs:
            break
        if it >= 2 and len(pairs) >= last_n:
            break                 # no progress over the last pass: stop instead of cycling the same items
        last_n = len(pairs)
        clr = max([0.25, getattr(D, 'signal_clearance', 0.2)] + [nc.get('clearance', 0.2) for nc in getattr(D, 'netclasses', {}).values()])
        fixed, failed = repair(board, c, pairs, clearance=clr)
        print('repair pass %d: %d unconnected, fixed %d, left %s' % (it + 1, len(pairs), fixed, sorted(set(failed))[:12]))
        if not fixed:
            break
        fill(board)
    # same-net vias closer than the hole-to-hole rule: the later one goes (its tracks still end on the kept via's pad)
    # (hole-to-hole needs drill + 0.3 mm between centres); tracks that ended on the removed via are moved onto the kept one
    keptv = []
    for t in list(board.GetTracks()):
        if t.GetClass() == 'PCB_VIA':
            x, y, nc = pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y), t.GetNetCode()
            lim = pcbnew.ToMM(t.GetDrillValue()) + 0.32
            hit = [k for k in keptv if k[2] == nc and math.hypot(x - k[0], y - k[1]) < lim]
            if hit:
                old_p, new_p = t.GetPosition(), hit[0][3].GetPosition()
                for st in board.GetTracks():
                    if st.GetClass() == 'PCB_TRACK' and st.GetNetCode() == nc:
                        if st.GetStart() == old_p:
                            st.SetStart(new_p)
                        if st.GetEnd() == old_p:
                            st.SetEnd(new_p)
                board.Remove(t)
            else:
                keptv.append((x, y, nc, t))
    # dangling vias (a via that reaches copper on one layer only) are removed with the stub that feeds them
    import re as _re
    pcbnew.WriteDRCReport(board, tmp, pcbnew.EDA_UNITS_MILLIMETRES, True)
    dang = [(float(a), float(b)) for a, b in _re.findall(r'\[via_dangling\][^\n]*\n[^\n]*\n\s*@\(([-\d.]+) mm, ([-\d.]+) mm\)', open(tmp).read())]
    nd = 0
    for (x, y) in dang:
        for t in list(board.GetTracks()):
            if t.GetClass() == 'PCB_VIA' and math.hypot(pcbnew.ToMM(t.GetPosition().x) - x, pcbnew.ToMM(t.GetPosition().y) - y) < 0.01:
                p = t.GetPosition()
                for st in list(board.GetTracks()):
                    if st.GetClass() == 'PCB_TRACK' and st.GetNetCode() == t.GetNetCode() and (st.GetEnd() == p or st.GetStart() == p) \
                            and st.GetLength() < mm(3.0):
                        board.Remove(st)
                board.Remove(t)
                nd += 1
                break
    if nd:
        print('dangling vias removed:', nd)
    fill(board)                       # always refill last: the via clean-up above can move track ends
    pcbnew.SaveBoard(pcbpath, board)
    set_stackup(D, pcbpath)
    board = pcbnew.LoadBoard(pcbpath)
    rpt = os.path.join(out, 'fab', D.project + '-drc.rpt')
    os.makedirs(os.path.dirname(rpt), exist_ok=True)
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(rpt).read()
    import re
    summ = re.findall(r'\*\* Found (\d+) (DRC violations|unconnected pads|Footprint errors)', txt)
    print('DRC:', summ)
    unrouted = board.GetConnectivity().GetUnconnectedCount(True) if hasattr(board.GetConnectivity(), 'GetUnconnectedCount') else -1
    print('unrouted connections:', unrouted)
    return summ


def set_paper(D, pcbpath):
    t = open(pcbpath, encoding='utf-8').read()
    paper = '(paper "%s"%s)' % ('A1' if max(D.W, D.H) > 250 else ('A2' if max(D.W, D.H) > 150 else 'A3'),
                                ' portrait' if D.H > D.W else '')
    import re
    t = re.sub(r'\(paper "[^"]*"( portrait)?\)', paper, t, count=1)
    open(pcbpath, 'w', encoding='utf-8', newline='\n').write(t)


def set_stackup(D, pcbpath):
    set_paper(D, pcbpath)
    if not D.stackup:
        return
    t = open(pcbpath, encoding='utf-8').read()
    if '(stackup' in t:
        a = t.index('(stackup')
        depth = 0
        for i in range(a, len(t)):
            if t[i] == '(':
                depth += 1
            elif t[i] == ')':
                depth -= 1
                if depth == 0:
                    t = t[:a] + t[i + 1:]
                    break
    i = t.index('(setup')
    j = t.index('\n', i) + 1
    t = t[:j] + D.stackup + t[j:]
    with open(pcbpath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)


def stackup_text(layers, finish='ENIG', mask='Green'):
    """layers: list of ('cu', name, thickness_mm) / ('core'|'prepreg', thickness_mm, material, er, tand)"""
    out = ['    (stackup', '      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))',
           '      (layer "F.Paste" (type "Top Solder Paste"))',
           '      (layer "F.Mask" (type "Top Solder Mask") (color "%s") (thickness 0.01))' % mask]
    k = 1
    for L in layers:
        if L[0] == 'cu':
            out.append('      (layer "%s" (type "copper") (thickness %s))' % (L[1], L[2]))
        else:
            out.append('      (layer "dielectric %d" (type "%s") (thickness %s) (material "%s") (epsilon_r %s) (loss_tangent %s))'
                       % (k, L[0], L[1], L[2], L[3], L[4]))
            k += 1
    out += ['      (layer "B.Mask" (type "Bottom Solder Mask") (color "%s") (thickness 0.01))' % mask,
            '      (layer "B.Paste" (type "Bottom Solder Paste"))',
            '      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))',
            '      (copper_finish "%s")' % finish, '      (dielectric_constraints yes)', '    )']
    return '\n'.join(out) + '\n'


# ---------------------------------------------------------------------------------------------- post-route repair
def _copper_layers(item):
    return [l for l in item.GetLayerSet().Seq() if pcbnew.IsCopperLayer(l)]


def clusters(board):
    """Per-net groups of copper items that touch (pads, tracks, vias, zone-fill islands).  Pure geometry."""
    out = {}
    tracks = list(board.GetTracks())
    pads = [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetCode() > 0]
    zones = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetCode() > 0]
    bynet = {}
    for p in pads:
        bynet.setdefault(p.GetNetname(), {'pads': [], 'tr': [], 'vi': [], 'zi': []})['pads'].append(p)
    for t in tracks:
        if t.GetNetCode() <= 0:
            continue
        d = bynet.setdefault(t.GetNetname(), {'pads': [], 'tr': [], 'vi': [], 'zi': []})
        (d['vi'] if t.GetClass() == 'PCB_VIA' else d['tr']).append(t)
    for z in zones:
        d = bynet.setdefault(z.GetNetname(), {'pads': [], 'tr': [], 'vi': [], 'zi': []})
        for l in _copper_layers(z):
            f = z.GetFilledPolysList(l)
            for i in range(f.OutlineCount()):
                d['zi'].append((l, f, i))
    for net, d in bynet.items():
        items = [('p', p) for p in d['pads']] + [('t', t) for t in d['tr']] + [('v', v) for v in d['vi']] + \
                [('z', z) for z in d['zi']]
        if len(d['pads']) < 2:
            continue
        par = list(range(len(items)))

        def find(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                par[ra] = rb

        def pts(kind, it):
            if kind == 't':
                return [it.GetStart(), it.GetEnd()]
            return [it.GetPosition()]

        def layers(kind, it):
            if kind == 'z':
                return [it[0]]
            if kind == 'v':
                return list(range(pcbnew.F_Cu, pcbnew.B_Cu + 1)) if True else []
            return _copper_layers(it)

        def hit(kind, it, p, lay):
            if kind == 'z':
                l, f, i = it
                return l == lay and f.Outline(i).PointInside(p) or (l == lay and f.Outline(i).PointOnEdge(p))
            if lay not in layers(kind, it):
                return False
            if kind == 'p':
                return it.HitTest(p, 0) if hasattr(it, 'HitTest') else False
            if kind == 'v':
                return (p - it.GetPosition()).EuclideanNorm() <= it.GetWidth() / 2
            return it.HitTest(p, 1)

        n = len(items)
        lay_cache = [layers(k, it) for k, it in items]
        for a in range(n):
            ka, ia = items[a]
            if ka == 'z':
                continue
            for pa in pts(ka, ia):
                for b in range(n):
                    if a == b:
                        continue
                    kb, ib = items[b]
                    for lay in lay_cache[a]:
                        if lay in lay_cache[b] and hit(kb, ib, pa, lay):
                            union(a, b)
                            break
        groups = {}
        for i in range(n):
            groups.setdefault(find(i), []).append(items[i])
        gs = [g for g in groups.values() if any(k == 'p' for k, _ in g)]
        if len(gs) > 1:
            out[net] = gs
    return out


def repair(board, c, pairs=None, clearance=0.25, width=0.25):
    """Join split clusters of a net with a straight or L-shaped track on a layer both ends reach, if it is clear."""
    D = c.D
    allc = list(range(pcbnew.F_Cu, pcbnew.B_Cu + 1))
    cu = [l for l in allc if board.IsLayerEnabled(l)]
    obst = {l: [] for l in cu}
    rects = {l: [] for l in cu}             # pads as their exact (bounding) rectangles: a capsule misses the corners

    def bxy(p):
        return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            x, y = bxy(t.GetPosition())
            for l in cu:
                obst[l].append((t.GetNetname(), x, y, x, y, pcbnew.ToMM(t.GetWidth()) / 2))
        else:
            (ax, ay), (bx, by) = bxy(t.GetStart()), bxy(t.GetEnd())
            obst[t.GetLayer()].append((t.GetNetname(), ax, ay, bx, by, pcbnew.ToMM(t.GetWidth()) / 2))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            (ax, ay), (bx, by) = bxy(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())), bxy(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
            for l in _copper_layers(p):
                if l in obst:
                    rects[l].append((p.GetNetname(), ax, ay, bx, by))

    ko = keepout_test(board)

    def sd(px, py, x0, y0, x1, y1):
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L))
        return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))

    def segdist(a, b):
        (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = a, b
        # sampled is enough at this scale (0.05 mm steps)
        n = max(2, int(math.hypot(ax1 - ax0, ay1 - ay0) / 0.05))
        return min(sd(ax0 + (ax1 - ax0) * i / n, ay0 + (ay1 - ay0) * i / n, bx0, by0, bx1, by1) for i in range(n + 1))

    def clear(net, lay, seg, w=None):
        w = width if w is None else w
        x0, y0, x1, y1 = seg
        lo_x, hi_x, lo_y, hi_y = min(x0, x1) - 3, max(x0, x1) + 3, min(y0, y1) - 3, max(y0, y1) + 3
        for (n2, a, b, cc, d, r) in obst[lay]:
            if n2 == net:
                continue
            if max(a, cc) < lo_x or min(a, cc) > hi_x or max(b, d) < lo_y or min(b, d) > hi_y:
                continue
            if segdist(seg, (a, b, cc, d)) < r + w / 2 + clearance:
                return False
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.05))
        for (n2, a, b, cc, d) in rects[lay]:
            if n2 == net or cc < lo_x or a > hi_x or d < lo_y or b > hi_y:
                continue
            lim = w / 2 + clearance
            for i in range(n + 1):
                px, py = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
                if math.hypot(max(a - px, 0, px - cc), max(b - py, 0, py - d)) < lim:
                    return False
        nko = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.1))
        for i_ in range(nko + 1):
            px_, py_ = x0 + (x1 - x0) * i_ / nko, y0 + (y1 - y0) * i_ / nko
            if (x0, y0) == (x1, y1):
                if ko(px_, py_, None, w / 2, True):
                    return False
            elif ko(px_, py_, lay, w / 2, False):
                return False
        ex0, ey0 = D.X0, D.Y0
        for x, y in ((x0, y0), (x1, y1)):
            if x < ex0 + 0.6 or x > ex0 + D.W - 0.6 or y < ey0 + 0.6 or y > ey0 + D.H - 0.6:
                return False
        return True

    def anchors(group):
        out = []
        for k, it in group:
            if k == 'p':
                out.append((bxy(it.GetPosition()), [l for l in _copper_layers(it) if l in obst]))
            elif k == 'v':
                out.append((bxy(it.GetPosition()), list(cu)))
            elif k == 't':
                for p in (it.GetStart(), it.GetEnd()):
                    out.append((bxy(p), [it.GetLayer()]))
        return out

    fixed, failed = 0, []
    allpairs = pairs if pairs is not None else []
    vd = c.D.fanout_via if hasattr(c.D, 'fanout_via') else (0.6, 0.3)
    for net, A, B in allpairs:
        netinfo = board.FindNet(net)
        if netinfo is None:
            continue
        if A == 'zones':
            # an isolated fill island: tie it to the other layers of the same net with a through via, if clear
            ok = False
            for (pt, lays, d) in B:
                for dx, dy in ((0, 0), (0.6, 0), (-0.6, 0), (0, 0.6), (0, -0.6), (1.2, 0), (-1.2, 0), (0, 1.2), (0, -1.2)):
                    p = (pt[0] + dx, pt[1] + dy)
                    if all(clear(net, l, (p[0], p[1], p[0], p[1]), w=vd[0]) for l in cu):
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pcbnew.VECTOR2I(mm(p[0]), mm(p[1])))
                        v.SetWidth(mm(vd[0]))
                        v.SetDrill(mm(vd[1]))
                        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                        v.SetNet(netinfo)
                        board.Add(v)
                        for l in cu:
                            obst[l].append((net, p[0], p[1], p[0], p[1], vd[0] / 2))
                        ok = True
                        break
            if ok:
                fixed += 1
            else:
                failed.append(net)
            continue
        (pa, la), (pb, lb) = A, B
        common = [l for l in la if l in lb]
        plans = []
        for lay in sorted(common, key=lambda l: (l not in (pcbnew.F_Cu, pcbnew.B_Cu), l)):
            for path in ([pa, pb], [pa, (pb[0], pa[1]), pb], [pa, (pa[0], pb[1]), pb]):
                plans.append((lay, path, None))
        if not common:
            # drop a through via at one end and route on the other end's layer
            for (pv, lay_list) in ((pb, la), (pa, lb)):
                for lay in lay_list:
                    other = pa if pv is pb else pb
                    for path in ([other, pv], [other, (pv[0], other[1]), pv], [other, (other[0], pv[1]), pv]):
                        plans.append((lay, path, pv))
        drilled = [bxy(pd.GetPosition()) for fp in board.GetFootprints() for pd in fp.Pads()
                   if pd.GetNetname() == net and pd.GetDrillSize().x > 0]
        plans = [(lay, path, None if via is not None and any(math.hypot(via[0] - q[0], via[1] - q[1]) < 0.3 for q in drilled) else via)
                 for lay, path, via in plans]
        done = False
        for lay, path, via in plans:
            segs = [(a[0], a[1], b[0], b[1]) for a, b in zip(path[:-1], path[1:]) if a != b]
            if not segs or not all(clear(net, lay, s) for s in segs):
                continue
            if via is not None and not all(clear(net, l, (via[0], via[1], via[0], via[1]), w=vd[0]) for l in cu):
                continue
            for s in segs:
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(mm(s[0]), mm(s[1])))
                t.SetEnd(pcbnew.VECTOR2I(mm(s[2]), mm(s[3])))
                t.SetWidth(mm(width))
                t.SetLayer(lay)
                t.SetNet(netinfo)
                board.Add(t)
                obst[lay].append((net,) + s + (width / 2,))
            if via is not None:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(via[0]), mm(via[1])))
                v.SetWidth(mm(c.D.fanout_via[0] if hasattr(c.D, 'fanout_via') else 0.6))
                v.SetDrill(mm(c.D.fanout_via[1] if hasattr(c.D, 'fanout_via') else 0.3))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNet(netinfo)
                board.Add(v)
                for l in cu:
                    obst[l].append((net, via[0], via[1], via[0], via[1], 0.3))
            done = True
            break
        if not done:
            done = maze(board, c, net, netinfo, pa, la, pb, lb, obst, cu, vd, clearance=clearance, width=0.2)
        if not done:
            # the far end may be boxed in: aim at the other pads of the far cluster (nearer pb than pa), both directions
            alt = []
            for fp in board.GetFootprints():
                for pd in fp.Pads():
                    if pd.GetNetname() != net:
                        continue
                    q = bxy(pd.GetPosition())
                    if math.hypot(q[0] - pb[0], q[1] - pb[1]) < math.hypot(q[0] - pa[0], q[1] - pa[1]) - 1.0:
                        alt.append((math.hypot(q[0] - pb[0], q[1] - pb[1]), q, [l for l in _copper_layers(pd) if l in obst]))
            for _, q, lq in sorted(alt)[:3]:
                if maze(board, c, net, netinfo, q, lq, pa, la, obst, cu, vd, clearance=clearance, width=0.2):
                    done = True
                    break
        if done:
            fixed += 1
        else:
            failed.append(net)
    return fixed, failed


def maze(board, c, net, netinfo, pa, la, pb, lb, obst, cu, vd, clearance=0.2, width=0.2, grid=0.1, margin=12.0, _stage=0):
    """Grid router for what the straight / L repair cannot close: F.Cu and B.Cu, through vias between them,
    obstacles = every other-net track, via and pad (all layers for the via test).  Dijkstra with a via cost."""
    import heapq
    import numpy as np
    outer = [l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if l in obst]
    x0 = max(min(pa[0], pb[0]) - margin, c.D.X0 + 0.7)
    y0 = max(min(pa[1], pb[1]) - margin, c.D.Y0 + 0.7)
    x1 = min(max(pa[0], pb[0]) + margin, c.D.X0 + c.D.W - 0.7)
    y1 = min(max(pa[1], pb[1]) + margin, c.D.Y0 + c.D.H - 0.7)
    x0 = pa[0] - math.floor((pa[0] - x0) / grid) * grid          # grid node exactly on the start pad centre
    y0 = pa[1] - math.floor((pa[1] - y0) / grid) * grid
    nx, ny = int((x1 - x0) / grid) + 1, int((y1 - y0) / grid) + 1
    if nx * ny > 9000000:
        return False
    gx = x0 + np.arange(nx) * grid
    gy = y0 + np.arange(ny) * grid

    def bxy(p):
        return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
    D_ = c.D
    base_cl = getattr(D_, 'signal_clearance', 0.2)
    clmap = {}
    for nc in getattr(D_, 'netclasses', {}).values():
        for n_ in nc.get('nets', []):
            clmap[n_] = max(clmap.get(n_, 0.0), nc.get('clearance', base_cl))
    own_cl = clmap.get(net, base_cl)
    clearance = max(base_cl, 0.2)              # the raster inflation below adds the per-pair excess

    def extra(other):
        return max(own_cl, clmap.get(other, base_cl)) - clearance
    wx0, wy0, wx1, wy1 = x0 - 3, y0 - 3, x1 + 3, y1 + 3
    segs_l = {l: [] for l in cu}           # other-net tracks / vias: (a, b, cc, d, r)
    rects_l = {l: [] for l in cu}          # other-net pads: (ax, ay, bx, by)
    own = []                               # own-pad rectangles at the two ends
    for t in board.GetTracks():
        if t.GetNetname() == net:
            continue
        if t.GetClass() == 'PCB_VIA':
            x, y = bxy(t.GetPosition())
            if wx0 < x < wx1 and wy0 < y < wy1:
                for l in cu:
                    segs_l[l].append((x, y, x, y, pcbnew.ToMM(t.GetWidth()) / 2 + extra(t.GetNetname())))
        else:
            (ax_, ay_), (bx_, by_) = bxy(t.GetStart()), bxy(t.GetEnd())
            if max(ax_, bx_) < wx0 or min(ax_, bx_) > wx1 or max(ay_, by_) < wy0 or min(ay_, by_) > wy1:
                continue
            if t.GetLayer() in segs_l:
                segs_l[t.GetLayer()].append((ax_, ay_, bx_, by_, pcbnew.ToMM(t.GetWidth()) / 2 + extra(t.GetNetname())))
    for fp in board.GetFootprints():
        for pd in fp.Pads():
            bb = pd.GetBoundingBox()
            (ax_, ay_), (bx_, by_) = bxy(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())), bxy(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
            if bx_ < wx0 or ax_ > wx1 or by_ < wy0 or ay_ > wy1:
                continue
            lays = [l for l in _copper_layers(pd) if l in rects_l]
            if pd.GetDrillSize().x > 0:
                lays = list(cu)
            if pd.GetNetname() == net and pd.GetNetname():
                if (ax_ - 0.01 <= pa[0] <= bx_ + 0.01 and ay_ - 0.01 <= pa[1] <= by_ + 0.01) or \
                        (ax_ - 0.01 <= pb[0] <= bx_ + 0.01 and ay_ - 0.01 <= pb[1] <= by_ + 0.01):
                    own.append((ax_, ay_, bx_, by_, lays))
                continue
            e_ = extra(pd.GetNetname())
            for l in lays:
                rects_l[l].append((ax_ - e_, ay_ - e_, bx_ + e_, by_ + e_))

    def raster(segs, rects, inflate):
        m = np.zeros((ny, nx), dtype=bool)
        for (a, b, cc, d, r) in segs:
            R = r + inflate
            i0, i1 = max(0, int((min(a, cc) - R - x0) / grid)), min(nx - 1, int((max(a, cc) + R - x0) / grid) + 1)
            j0, j1 = max(0, int((min(b, d) - R - y0) / grid)), min(ny - 1, int((max(b, d) + R - y0) / grid) + 1)
            if i0 > i1 or j0 > j1:
                continue
            X, Y = np.meshgrid(gx[i0:i1 + 1], gy[j0:j1 + 1])
            dx, dy = cc - a, d - b
            L = dx * dx + dy * dy
            if L == 0:
                D = np.hypot(X - a, Y - b)
            else:
                t = np.clip(((X - a) * dx + (Y - b) * dy) / L, 0, 1)
                D = np.hypot(X - (a + t * dx), Y - (b + t * dy))
            m[j0:j1 + 1, i0:i1 + 1] |= D < R
        for (ax_, ay_, bx_, by_) in rects:
            R = inflate
            i0, i1 = max(0, int((ax_ - R - x0) / grid)), min(nx - 1, int((bx_ + R - x0) / grid) + 1)
            j0, j1 = max(0, int((ay_ - R - y0) / grid)), min(ny - 1, int((by_ + R - y0) / grid) + 1)
            if i0 > i1 or j0 > j1:
                continue
            X, Y = np.meshgrid(gx[i0:i1 + 1], gy[j0:j1 + 1])
            ddx = np.maximum(np.maximum(ax_ - X, 0), X - bx_)
            ddy = np.maximum(np.maximum(ay_ - Y, 0), Y - by_)
            m[j0:j1 + 1, i0:i1 + 1] |= np.hypot(ddx, ddy) < R
        return m
    blk = {l: raster(segs_l[l], rects_l[l], clearance + width / 2 + 0.005) for l in outer}
    vblk = np.zeros((ny, nx), dtype=bool)
    for l in cu:
        vblk |= raster(segs_l[l], rects_l[l], clearance + vd[0] / 2 + 0.005)
    # rule-area keep-outs
    for z in board.Zones():
        if not z.GetIsRuleArea():
            continue
        bb = z.Outline().BBox()
        zx0, zy0, zx1, zy1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
        i0, i1 = max(0, int((zx0 - 0.5 - x0) / grid)), min(nx - 1, int((zx1 + 0.5 - x0) / grid) + 1)
        j0, j1 = max(0, int((zy0 - 0.5 - y0) / grid)), min(ny - 1, int((zy1 + 0.5 - y0) / grid) + 1)
        if i0 > i1 or j0 > j1:
            continue
        ol = z.Outline()
        for jj in range(j0, j1 + 1):
            for ii in range(i0, i1 + 1):
                v = pcbnew.VECTOR2I(mm(x0 + ii * grid), mm(y0 + jj * grid))
                dd = 0.0 if ol.Contains(v) else math.sqrt(ol.SquaredDistance(v)) / 1e6
                if z.GetDoNotAllowTracks() and dd < width / 2 + 0.01:
                    for l in outer:
                        if z.GetLayerSet().Contains(l):
                            blk[l][jj, ii] = True
                if z.GetDoNotAllowVias() and dd < vd[0] / 2 + 0.01:
                    vblk[jj, ii] = True

    def cell(p):
        return (int(round((p[1] - y0) / grid)), int(round((p[0] - x0) / grid)))
    sa, sb = cell(pa), cell(pb)
    starts = [(li, sa) for li, l in enumerate(outer) if l in la]
    goals = {(li, sb) for li, l in enumerate(outer) if l in lb}
    if not starts or not goals:
        # an end on an inner layer only (via / plane): allow both outer layers there
        starts = starts or [(li, sa) for li in range(len(outer))]
        goals = goals or {(li, sb) for li in range(len(outer))}
    # inside the own end pads (shrunk by half the track width) the track is covered by pad copper: free
    for (ax_, ay_, bx_, by_, lays) in own:
        i0, i1 = int(math.ceil((ax_ + width / 2 - x0) / grid)), int((bx_ - width / 2 - x0) / grid)
        j0, j1 = int(math.ceil((ay_ + width / 2 - y0) / grid)), int((by_ - width / 2 - y0) / grid)
        for l in lays:
            if l in blk and i0 <= i1 and j0 <= j1:
                blk[l][max(0, j0):max(0, j1 + 1), max(0, i0):max(0, i1 + 1)] = False
    starts = [(li, (j, i)) for li, (j, i) in starts if 0 <= j < ny and 0 <= i < nx]
    goals = {(li, (j, i)) for li, (j, i) in goals if 0 <= j < ny and 0 <= i < nx}
    if not starts or not goals:
        return False
    for li, (j, i) in list(starts) + list(goals):
        if 0 <= j < ny and 0 <= i < nx:
            blk[outer[li]][j, i] = False
    pchk = plane_checker(c.D, c)
    plane_net = net in pchk.nets
    VIA_COST = 40.0
    plane_via = False
    dist = {}
    prev = {}
    pq = []
    for st in starts:
        dist[st] = 0.0
        heapq.heappush(pq, (0.0, st))
    nbr = [(0, 1, 1.0), (0, -1, 1.0), (1, 0, 1.0), (-1, 0, 1.0), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    found = None
    gj, gi = sb
    while pq:
        dcur, (li, (j, i)) = heapq.heappop(pq)
        if dcur > dist.get((li, (j, i)), 1e18):
            continue
        if (li, (j, i)) in goals:
            found = (li, (j, i))
            break
        if plane_net and dcur > 8 and not vblk[j, i] and pchk(net, x0 + i * grid, y0 + j * grid):
            found = (li, (j, i))
            plane_via = True
            break
        if dcur > 20000:
            break
        h = blk[outer[li]]
        for dj, di, w in nbr:
            jj, ii = j + dj, i + di
            if not (0 <= jj < ny and 0 <= ii < nx) or h[jj, ii]:
                continue
            nd = dcur + w
            key = (li, (jj, ii))
            if nd < dist.get(key, 1e18):
                dist[key] = nd
                prev[key] = (li, (j, i))
                heapq.heappush(pq, (nd + 0.0, key))
        if len(outer) == 2 and not vblk[j, i]:
            key = (1 - li, (j, i))
            nd = dcur + VIA_COST
            if not blk[outer[1 - li]][j, i] and nd < dist.get(key, 1e18):
                dist[key] = nd
                prev[key] = (li, (j, i))
                heapq.heappush(pq, (nd, key))
    if not found and os.environ.get('MAZE_DEBUG'):
        print('  maze debug %s stage %d: explored %d, start blocked %s, goal blocked %s' % (net, _stage, len(dist),
              [bool(blk[outer[li]][j, i]) for li, (j, i) in starts], [bool(blk[outer[li]][j, i]) for li, (j, i) in goals]))
    if not found:
        if _stage == 0:       # finer grid
            return maze(board, c, net, netinfo, pa, la, pb, lb, obst, cu, vd, clearance, width, grid=0.05, margin=12.0, _stage=1)
        if _stage == 1:       # wider window
            return maze(board, c, net, netinfo, pa, la, pb, lb, obst, cu, vd, clearance, width, grid=0.1, margin=30.0, _stage=2)
        if _stage == 2:       # widest window, fine grid
            return maze(board, c, net, netinfo, pa, la, pb, lb, obst, cu, vd, clearance, width, grid=0.05, margin=45.0, _stage=3)
        if _stage == 3:       # whole board (long detours around a dense area)
            return maze(board, c, net, netinfo, pa, la, pb, lb, obst, cu, vd, clearance, width, grid=0.1, margin=400.0, _stage=4)
        return False
    path = [found]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    if len(path) == 1:
        path = path * 1

    def xy(n):
        return (x0 + n[1][1] * grid, y0 + n[1][0] * grid)
    # emit: collapse straight runs, vias on layer changes
    pts = [path[0]]
    if len(path) == 1:
        pts = [path[0]]
    for k in range(1, len(path) - 1):
        a, b, cc = path[k - 1], path[k], path[k + 1]
        if a[0] != b[0] or b[0] != cc[0]:
            pts.append(b)
            continue
        d1 = (b[1][0] - a[1][0], b[1][1] - a[1][1])
        d2 = (cc[1][0] - b[1][0], cc[1][1] - b[1][1])
        if d1 != d2:
            pts.append(b)
    if len(path) > 1:
        pts.append(path[-1])
    segs = [(xy(pa_[0:2] if False else a), xy(b), outer[a[0]]) for a, b in zip(pts[:-1], pts[1:]) if a[0] == b[0] and a[1] != b[1]]
    vias = [xy(b) for a, b in zip(pts[:-1], pts[1:]) if a[0] != b[0]]
    if plane_via:
        vias.append(xy(pts[-1]))
    # an end that sits on an inner layer only (inner track end, plane) needs a via where the path meets it
    if len(pts) > 1 or plane_via:
        if outer[path[0][0]] not in la:
            vias.append(pa)
        if not plane_via and outer[path[-1][0]] not in lb:
            vias.append(pb)
    if len(pts) == 1 and not plane_via:
        # both ends on the same spot, on layers that do not meet: a via joins them
        if not set(la) & set(lb) and not vblk[pts[0][1][0], pts[0][1][1]]:
            vias.append(pb)
        else:
            return False
    # an end on a plated through pad needs no via (the barrel already joins every layer)
    drilled = [bxy(pd.GetPosition()) for fp in board.GetFootprints() for pd in fp.Pads()
               if pd.GetNetname() == net and pd.GetDrillSize().x > 0]
    vias = [v_ for v_ in vias if not any(math.hypot(v_[0] - q[0], v_[1] - q[1]) < 0.3 for q in drilled)]
    # every via must clear other-net copper on all layers (end vias sit on inner track ends, not on grid cells)
    for v_ in vias:
        j_, i_ = cell(v_)
        if 0 <= j_ < ny and 0 <= i_ < nx and vblk[j_, i_]:
            return False
    # tie the grid ends to the true pad centres
    segs = [((pa if k == 0 else s0), s1, l) for k, (s0, s1, l) in enumerate(segs)]
    if segs:
        s0, s1, l = segs[-1]
        segs[-1] = (s0, pb, l) if (pts[-1][0] == pts[-2][0] and not plane_via) else segs[-1]
    for (s0, s1, l) in segs:
        if math.hypot(s1[0] - s0[0], s1[1] - s0[1]) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(s0[0]), mm(s0[1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(s1[0]), mm(s1[1])))
        t.SetWidth(mm(width))
        t.SetLayer(l)
        t.SetNet(netinfo)
        board.Add(t)
        obst[l].append((net, s0[0], s0[1], s1[0], s1[1], width / 2))
    for v_ in vias:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(v_[0]), mm(v_[1])))
        v.SetWidth(mm(vd[0]))
        v.SetDrill(mm(vd[1]))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(netinfo)
        board.Add(v)
        for l in cu:
            obst[l].append((net, v_[0], v_[1], v_[0], v_[1], vd[0] / 2))
    print('  maze: %s %d segments %d vias' % (net, len(segs), len(vias)))
    return True


def drop_clashes(board, rpt):
    """Remove unlocked routed copper that breaks track/via clearance to another net (from a DRC report).  The repair
    pass then re-joins the net with a clean straight / L track."""
    import re
    txt = open(rpt).read()
    item = re.compile(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (Track|Via) \[([^\]]*)\] on ([\w.]+)(?: - [\w.]+)?(?:, length ([\d.]+) mm)?')
    lid = {board.GetLayerName(l): l for l in range(pcbnew.PCB_LAYER_ID_COUNT) if pcbnew.IsCopperLayer(l)}
    tracks = list(board.GetTracks())
    kill = set()
    for blk in re.split(r'\n(?=\[)', txt):
        if blk.startswith('[items_not_allowed]'):          # routed copper inside a keep-out: it goes
            for (x, y, kind, net, lay, ln) in item.findall(blk):
                for t in tracks:
                    if t.GetNetname() == net and not t.IsLocked() and t.GetClass() == ('PCB_VIA' if kind == 'Via' else 'PCB_TRACK'):
                        q = t.GetPosition() if kind == 'Via' else t.GetStart()
                        e = q if kind == 'Via' else t.GetEnd()
                        if _sd(float(x), float(y), pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)) < 0.05:
                            kill.add(t.m_Uuid.AsString())
            continue
        if not blk.startswith('[clearance]') and not blk.startswith('[hole_clearance]'):
            continue
        its = item.findall(blk)
        if len(its) == 1 and re.search(r'\]: Pad |\): (N?PTH )?[Pp]ad ', blk):
            pass                                     # track / via against a pad: the routed item goes
        elif len(its) != 2 or its[0][3] == its[1][3]:
            continue
        cand = []
        for (x, y, kind, net, lay, ln) in its:
            x, y = float(x), float(y)
            best = None
            for t in tracks:
                if t.GetNetname() != net or t.IsLocked():
                    continue
                if kind == 'Via':
                    if t.GetClass() != 'PCB_VIA':
                        continue
                    d = math.hypot(pcbnew.ToMM(t.GetPosition().x) - x, pcbnew.ToMM(t.GetPosition().y) - y)
                else:
                    if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != lid.get(lay, -1):
                        continue
                    if ln and abs(pcbnew.ToMM(t.GetLength()) - float(ln)) > 0.002:
                        continue
                    a, b = t.GetStart(), t.GetEnd()
                    d = _sd(x, y, pcbnew.ToMM(a.x), pcbnew.ToMM(a.y), pcbnew.ToMM(b.x), pcbnew.ToMM(b.y))
                if d < 0.05 and (best is None or d < best[0]):
                    best = (d, t)
            if best:
                cand.append(best[1])
        if not cand:
            continue
        # the shorter unlocked item goes (a via counts as length 0, so a track is preferred over a via)
        cand.sort(key=lambda t: -1 if t.GetClass() == 'PCB_VIA' else pcbnew.ToMM(t.GetLength()))
        victim = [t for t in cand if t.GetClass() == 'PCB_TRACK'][:1] or cand[:1]
        for t in victim:
            kill.add(t.m_Uuid.AsString())
    n = 0
    for t in tracks:
        if t.m_Uuid.AsString() in kill:
            board.Remove(t)
            n += 1
    return n


def drc_pairs(rpt, board):
    """Unconnected pairs from a KiCad DRC report: [(net, ((x, y), layers), ((x, y), layers))] in page mm."""
    import re
    txt = open(rpt).read()
    if '** Found' not in txt or 'unconnected pads' not in txt:
        return []
    sec = txt[txt.index('unconnected pads'):]
    allc = [l for l in range(pcbnew.F_Cu, pcbnew.B_Cu + 1) if board.IsLayerEnabled(l)]
    names = {board.GetLayerName(l): l for l in allc}
    out = []
    for m in re.finditer(r'\[unconnected_items\][^\n]*\n[^\n]*\n\s*@\(([-\d.]+) mm, ([-\d.]+) mm\): ([^\n]*)\n'
                         r'\s*@\(([-\d.]+) mm, ([-\d.]+) mm\): ([^\n]*)', sec):
        ends = []
        net = None
        for x, y, d in ((m.group(1), m.group(2), m.group(3)), (m.group(4), m.group(5), m.group(6))):
            nm = re.search(r'\[([^\]]*)\]', d)
            net = nm.group(1) if nm else net
            if d.startswith('PTH') or d.startswith('Via'):
                lays = list(allc)
            else:
                lm = re.search(r' on ([A-Za-z0-9.]+)', d)
                lays = [names[lm.group(1)]] if lm and lm.group(1) in names else list(allc)
            ends.append(((float(x), float(y)), lays, d))
        if ends[0][2].startswith('Zone') and ends[1][2].startswith('Zone'):
            out.append((net, 'zones', ends))
            continue
        out.append((net, (ends[0][0], ends[0][1]), (ends[1][0], ends[1][1])))
    return out
