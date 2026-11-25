"""CBP-8 targeted touch-up after finish (board coords, mm).  Fixes the last items the generic passes leave:
  * RS485_DE ran down through the slot-5 S5_12V F pour and split it: re-routed with that pour fenced off on F.
  * Kelvin IN+ of U502 and the slot-5/8 shunt +12V pads sat in fill islands cut off by +3V3 / sense routing:
    joined to the +12V planes (through via or a short track to the nearest +12V via).
  * U803 GND pad island: joined to the nearest GND via.
  * J905 pin 9 (GND, PTH): starved thermal -> solid zone connection on that pad.
  * over-wide 12 V tracks that break clearance are narrowed; dangling stubs removed.
python3 fix_cbp8.py [in.kicad_pcb] [out.kicad_pcb]"""
import math
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew   # noqa: E402
import build    # noqa: E402
import pcb      # noqa: E402

m = build.load('cbp8')
D = m.D
c = pcb.Ctx(D)
here = os.path.dirname(os.path.abspath(__file__))
bdir = os.path.normpath(os.path.join(here, '..', 'boards', 'cbp8'))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(bdir, 'cbp8.kicad_pcb')
dst = sys.argv[2] if len(sys.argv) > 2 else src
board = pcbnew.LoadBoard(src)
rpt = os.path.join(bdir, 'build', 'fix-drc.rpt')
MM = pcbnew.FromMM
W = pcbnew.ToMM
GRAVE = []          # removed items stay referenced: no wrapper-side delete while the board is live
item = re.compile(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (Track|Via) \[([^\]]*)\] on ([\w.]+)(?: - [\w.]+)?(?:, length ([\d.]+) mm)?')


def drc():
    pcb.fill(board)
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    t = open(rpt).read()
    nv = int(re.search(r'Found (\d+) DRC violations', t).group(1))
    nu = int(re.search(r'Found (\d+) unconnected', t).group(1))
    return t, nv, nu


def seg_near(t, x, y, tol=0.02):
    a, e = t.GetStart(), t.GetEnd()
    return pcb._sd(x, y, W(a.x), W(a.y), W(e.x), W(e.y)) < tol


def nearest_via(net, x, y, xmin=None):
    best = None
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net:
            q = t.GetPosition()
            if xmin is not None and W(q.x) < xmin:
                continue
            d = math.hypot(W(q.x) - x, W(q.y) - y)
            if best is None or d < best[0]:
                best = (d, (W(q.x), W(q.y)))
    return best[1]


def temp_keepout(x0, y0, x1, y1, layer):
    z = pcbnew.ZONE(board)
    z.SetLayerSet(pcb.lset(layer) if isinstance(layer, str) else layer)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowCopperPour(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(MM(px), MM(py))
    board.Add(z)
    return z


txt, nv, nu = drc()
print('start: %d violations, %d unconnected' % (nv, nu), flush=True)

# 1. narrow over-wide routed tracks in clearance violations; drop dangling stubs
for blk in re.split(r'\n(?=\[)', txt):
    if blk.startswith('[clearance]'):
        need = re.search(r'clearance ([\d.]+) mm; actual ([\d.]+) mm', blk)
        short = float(need.group(1)) - float(need.group(2)) if need else 0.1
        for (x, y, kind, net, lay, ln) in item.findall(blk):
            if kind != 'Track':
                continue
            for t in board.GetTracks():
                if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net and board.GetLayerName(t.GetLayer()) == lay \
                        and not t.IsLocked() and abs(W(t.GetLength()) - float(ln)) < 0.002 and seg_near(t, float(x), float(y), 0.05):
                    if W(t.GetWidth()) > 0.3 + 1e-6:
                        t.SetWidth(MM(max(0.3, W(t.GetWidth()) - 2 * short - 0.04)))
                        print('  narrowed', net, lay, '%.2f' % W(t.GetWidth()))
                    break
            else:
                continue
            break
    elif blk.startswith('[track_dangling]'):
        for (x, y, kind, net, lay, ln) in item.findall(blk):
            for t in list(board.GetTracks()):
                if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net and not t.IsLocked() and \
                        abs(W(t.GetLength()) - float(ln)) < 0.002 and seg_near(t, float(x), float(y), 0.05):
                    board.Remove(t)
                    GRAVE.append(t)
                    print('  removed dangling', net, ln)

tmp_pcb = os.path.join(bdir, 'build', 'fix-tmp.kicad_pcb')
pcbnew.SaveBoard(tmp_pcb, board)
board = pcbnew.LoadBoard(tmp_pcb)

# 2. RS485_DE out of the slot-5 S5_12V F pour
de = [(297.37, 236.43, 297.37, 243.10), (297.37, 243.10, 297.29, 243.17), (297.29, 243.17, 297.29, 249.04),
      (297.29, 249.04, 302.52, 254.27)]
for t in list(board.GetTracks()):
    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'RS485_DE' and t.GetLayer() == pcbnew.F_Cu:
        a, e = t.GetStart(), t.GetEnd()
        for s in de:
            if (abs(W(a.x) - s[0]) < .02 and abs(W(a.y) - s[1]) < .02 and abs(W(e.x) - s[2]) < .02 and abs(W(e.y) - s[3]) < .02):
                board.Remove(t); GRAVE.append(t)
ko = temp_keepout(255.0, 238.0, 313.5, 255.0, pcb.lset(pcbnew.F_Cu))
pcb.fill(board)
allc = [l for l in range(pcbnew.F_Cu, pcbnew.B_Cu + 1) if board.IsLayerEnabled(l)]
F, B = pcbnew.F_Cu, pcbnew.B_Cu
pairs = [('RS485_DE', ((297.37, 236.43), [F]), ((302.52, 254.27), [F]))]
clr = max([0.25, getattr(D, 'signal_clearance', 0.2)] + [nc.get('clearance', 0.2) for nc in getattr(D, 'netclasses', {}).values()])
fx, fl = pcb.repair(board, c, pairs, clearance=clr)
print('RS485_DE reroute: fixed %d failed %s' % (fx, fl), flush=True)
board.Remove(ko); GRAVE.append(ko)
pcbnew.SaveBoard(tmp_pcb, board)
board = pcbnew.LoadBoard(tmp_pcb)

# 3. +12V Kelvin / shunt islands and the GND island
def pad_xy(ref, num):
    p = [q for q in board.FindFootprintByReference(ref).Pads() if q.GetNumber() == num][0]
    return W(p.GetPosition().x), W(p.GetPosition().y), [l for l in pcb._copper_layers(p)]


def pad_bb(ref, num):
    p = [q for q in board.FindFootprintByReference(ref).Pads() if q.GetNumber() == num][0]
    bb = p.GetBoundingBox()
    return W(bb.GetLeft()), W(bb.GetTop()), W(bb.GetRight()), W(bb.GetBottom())


def seg_hits_rect(x0, y0, x1, y1, r, rect):
    rx0, ry0, rx1, ry1 = rect
    for i in range(41):
        px, py = x0 + (x1 - x0) * i / 40.0, y0 + (y1 - y0) * i / 40.0
        if rx0 - r <= px <= rx1 + r and ry0 - r <= py <= ry1 + r:
            return True
    return False


# the shunt's +12V pads (Rk02.1 / Rk03.1) and the Kelvin IN+ (Uk02.3) must sit in the +12V B pour: clear every
# other-net B track out of that strip, fence it, and re-route what was cut
kos = []
for k in (5, 8):
    ux0, uy0, ux1, uy1 = pad_bb('U%d02' % k, '3')
    rb = max(pad_bb('R%d02' % k, '1')[3], pad_bb('R%d03' % k, '1')[3])
    rect = (283.3, uy0 - 0.15, 287.8, rb + 0.6)
    gone = 0
    for t in list(board.GetTracks()):
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != B or t.IsLocked() or t.GetNetname() == '+12V':
            continue
        a_, e_ = t.GetStart(), t.GetEnd()
        if seg_hits_rect(W(a_.x), W(a_.y), W(e_.x), W(e_.y), W(t.GetWidth()) / 2 + 0.25, rect):
            board.Remove(t); GRAVE.append(t)
            gone += 1
    print('  slot %d: strip %s cleared of %d tracks' % (k, tuple(round(v, 2) for v in rect), gone))
    kos.append(temp_keepout(rect[0], rect[1], rect[2], rect[3], pcb.lset(B)))
pcb.fill(board)
for k in (5, 8):
    # IN- (Uk02.4) to the Sk_12V_SNS pour that holds the shunt's load-side pads, entering at its corner nearest U
    zs = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'S%d_12V_SNS' % k and z.GetLayer() == B]
    bb = zs[0].Outline().BBox()
    x, y, ls = pad_xy('U%d02' % k, '4')
    tgt = (W(bb.GetRight()) - 0.3, W(bb.GetTop()) + 0.3)
    fx, fl = pcb.repair(board, c, [('S%d_12V_SNS' % k, ((x, y), [B]), (tgt, [B]))], clearance=clr)
    print('  slot %d IN- to SNS pour: fixed %d %s' % (k, fx, fl), flush=True)
for it in range(4):
    txt, nv, nu = drc()
    pairs = [p for p in pcb.drc_pairs(rpt, board) if p[1] != 'zones' and not p[0].endswith('_12V_SNS')]
    print('  re-route pass %d: %d violations, %d unconnected, %d track pairs' % (it, nv, nu, len(pairs)), flush=True)
    if not pairs:
        break
    fx, fl = pcb.repair(board, c, pairs, clearance=clr)
    print('  re-routed %d, left %s' % (fx, fl), flush=True)
    if not fx:
        break
for z in kos:
    board.Remove(z); GRAVE.append(z)
pcbnew.SaveBoard(tmp_pcb, board)
board = pcbnew.LoadBoard(tmp_pcb)

# U803.1 (GND) is boxed in on F by the slot-8 buck switch-node trace (it wraps pin 1 to reach pin 2), and the
# slot-8 PCIe lanes 1-7 run under the buck on In2/In4, so no via fits there.  The SW leg to L801 is lifted 0.71 mm
# (y 98.01 -> 97.30): the F GND fill then runs from pin 1 over the pin row and out past pin 6 to the main F plane.
x, y, ls = pad_xy('U803', '1')
SW = board.FindNet('S8_SW')
for t in list(board.GetTracks()):
    if t.GetClass() != 'PCB_TRACK' or t.GetNetname() != 'S8_SW':
        continue
    a_, e_ = t.GetStart(), t.GetEnd()
    if abs(W(a_.y) - 98.01) < 0.02 and abs(W(e_.y) - 98.01) < 0.02 and {round(W(a_.x), 2), round(W(e_.x), 2)} == {83.51, 78.09}:
        w = t.GetWidth()
        board.Remove(t); GRAVE.append(t)
        for (sx, sy, ex, ey) in ((78.09, 97.30, 83.51, 97.30), (83.51, 97.30, 83.51, 98.01)):
            n_ = pcbnew.PCB_TRACK(board)
            n_.SetStart(pcbnew.VECTOR2I(MM(sx), MM(sy)))
            n_.SetEnd(pcbnew.VECTOR2I(MM(ex), MM(ey)))
            n_.SetWidth(w)
            n_.SetLayer(F)
            n_.SetNet(SW)
            board.Add(n_)
        print('  S8_SW leg lifted to y 97.30')
        break
# the IN- sense now enters the Sk_12V_SNS B pour directly; the pour's preroute via that used to carry it is left
# floating on one layer: removed
for k, yy in ((5, 246.2), (8, 93.8)):
    for t in list(board.GetTracks()):
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'S%d_12V_SNS' % k and \
                math.hypot(W(t.GetPosition().x) - 276.6, W(t.GetPosition().y) - yy) < 0.02:
            board.Remove(t); GRAVE.append(t)

# dangling stubs and vias left by the re-routes: remove (unlocked only), repeat until none
for it in range(6):
    txt, nv, nu = drc()
    n = 0
    for blk in re.split(r'\n(?=\[)', txt):
        if blk.startswith('[track_dangling]') or blk.startswith('[via_dangling]'):
            for (x, y, kind, net, lay, ln) in item.findall(blk):
                for t in list(board.GetTracks()):
                    if t.IsLocked() or t.GetNetname() != net:
                        continue
                    if kind == 'Via' and t.GetClass() == 'PCB_VIA' and \
                            math.hypot(W(t.GetPosition().x) - float(x), W(t.GetPosition().y) - float(y)) < 0.01:
                        board.Remove(t); GRAVE.append(t); n += 1
                        break
                    if kind == 'Track' and t.GetClass() == 'PCB_TRACK' and abs(W(t.GetLength()) - float(ln)) < 0.002 \
                            and seg_near(t, float(x), float(y), 0.05):
                        board.Remove(t); GRAVE.append(t); n += 1
                        break
    print('  dangling pass %d: removed %d' % (it, n), flush=True)
    if not n:
        break

# 4. J905 pin 9: solid connection (one spoke only fits)
for p in board.FindFootprintByReference('J905').Pads():
    if p.GetNumber() == '9':
        p.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

txt, nv, nu = drc()
print('end: %d violations, %d unconnected' % (nv, nu), flush=True)
for blk in re.split(r'\n(?=\[)', txt):
    if blk.startswith('['):
        print(' ', '\n  '.join(blk.splitlines()[:3]))
pcbnew.SaveBoard(dst, board)
print('saved', dst)
