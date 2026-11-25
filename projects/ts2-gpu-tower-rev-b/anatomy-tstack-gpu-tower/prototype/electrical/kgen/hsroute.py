"""Deterministic coupled-pair routing for the PCIe lanes on CBP-8 (CEM x16 slot on F -> MCIO 8i on B).

Topology per slot (board-local mm, y up):
  * CEM row B (near the MCIO, host->card lanes) pads dog-bone inward to a via line; the pairs run on In2.
  * CEM row A (card->host lanes) pads dog-bone outward; the pairs run on In4.
  * Both bundles drop below the slot, run +x, turn up past the pin-82 end of the slot (a U-turn), and run back
    to the MCIO, whose pin order is mirrored because it sits on the B side - the U-turn restores the order, so
    each bundle is planar on one layer with no crossings.
  * In2 lands on the MCIO A-row vias; In4 passes between the A-row vias (at the GND pin gap) to the B-row vias.
Every pair is a coupled stripline (w / gap from the net class) between GND planes (In1/In3/In5).
A geometric check verifies spacing between all pairs on a layer, and a report lists lengths and intra-pair skew.
"""
import math

W = 0.13          # trace width (fab adjusts for 85 ohm differential on the stated stackup)
GAP = 0.18        # in-pair gap
H = (W + GAP) / 2  # centreline -> trace centreline
P = 1.0           # pair-to-pair pitch in a bundle
CH = 0.6          # 45 degree chamfer at every bend
VIA = dict(drill=0.2, dia=0.4)
HOLE_CLR = 0.55 + 0.2 + H + W / 2   # MCIO peg hole radius + hole clearance + pair half-span

NEAR = [(14, 15), (19, 20), (23, 24), (27, 28), (33, 34), (37, 38), (41, 42), (45, 46)]   # CEM row B, lanes 0-7
FAR = [(16, 17), (21, 22), (25, 26), (29, 30), (35, 36), (39, 40), (43, 44), (47, 48)]    # CEM row A, lanes 0-7
MCIO = [(2, 3), (5, 6), (14, 15), (17, 18), (20, 21), (23, 24), (32, 33), (35, 36)]       # A row (PER) and B row (PET)


def chamfer(pts, c=CH):
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, d = pts[i - 1], pts[i], pts[i + 1]
        l1 = math.hypot(b[0] - a[0], b[1] - a[1])
        l2 = math.hypot(d[0] - b[0], d[1] - b[1])
        if l1 < 1e-9 or l2 < 1e-9:
            continue
        u1 = ((b[0] - a[0]) / l1, (b[1] - a[1]) / l1)
        u2 = ((d[0] - b[0]) / l2, (d[1] - b[1]) / l2)
        if abs(u1[0] * u2[1] - u1[1] * u2[0]) < 1e-9:
            continue
        cc = min(c, l1 / 2.01, l2 / 2.01)
        out.append((b[0] - u1[0] * cc, b[1] - u1[1] * cc))
        out.append((b[0] + u2[0] * cc, b[1] + u2[1] * cc))
    out.append(pts[-1])
    return out


def offset(pts, d):
    """miter offset of a polyline to the LEFT by d"""
    segs = []
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = (-(b[1] - a[1]) / L, (b[0] - a[0]) / L)
        segs.append(n)
    out = [(pts[0][0] + segs[0][0] * d, pts[0][1] + segs[0][1] * d)]
    for i in range(1, len(pts) - 1):
        n1, n2 = segs[i - 1], segs[i]
        m = (n1[0] + n2[0], n1[1] + n2[1])
        k = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]
        out.append((pts[i][0] + m[0] * d / k, pts[i][1] + m[1] * d / k))
    out.append((pts[-1][0] + segs[-1][0] * d, pts[-1][1] + segs[-1][1] * d))
    return out


def length(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))


def seg_dist(p1, p2, q1, q2):
    def pd(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
        return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)

    def cross(a, b, c, d):
        def o(p, q, r):
            return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return (o(a, b, c) * o(a, b, d) < 0) and (o(c, d, a) * o(c, d, b) < 0)
    if cross(p1, p2, q1, q2):
        return 0.0
    return min(pd(p1, q1, q2), pd(p2, q1, q2), pd(q1, p1, p2), pd(q2, p1, p2))


def deskew(a, b, hb=0.25, run=0.5):
    """Equalise in-pair length: add 45-degree bumps (height hb, away from the partner) on the shorter trace's
    longest segment.  Each bump adds 2*hb*(sqrt(2)-1) mm."""
    La, Lb = length(a), length(b)
    if abs(La - Lb) < 0.02:
        return a, b
    short, long_ = (a, b) if La < Lb else (b, a)
    need = abs(La - Lb)
    per = 2 * hb * (math.sqrt(2) - 1)
    nb = int(math.ceil(need / per - 1e-9))
    hb2 = need / (nb * 2 * (math.sqrt(2) - 1)) if nb else 0
    if nb == 0:
        return a, b
    i = max(range(len(short) - 1), key=lambda k: math.hypot(short[k + 1][0] - short[k][0], short[k + 1][1] - short[k][1]))
    p0, p1 = short[i], short[i + 1]
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    u = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    n = (-u[1], u[0])
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    # bumps go away from the partner: test a point one bump-height off the segment midpoint on each side and keep
    # the side farther from the partner polyline (a nearest-vertex test picks the wrong side on long segments)
    def dpoly(pt):
        return min(seg_dist(pt, pt, q1, q2) for q1, q2 in zip(long_[:-1], long_[1:]))
    if dpoly((mid[0] + n[0] * hb, mid[1] + n[1] * hb)) < dpoly((mid[0] - n[0] * hb, mid[1] - n[1] * hb)):
        n = (-n[0], -n[1])
    pitch = 2 * hb2 + run + 0.6
    if nb * pitch > L - 4.0:
        nb = max(1, int((L - 4.0) / pitch))
        hb2 = need / (nb * 2 * (math.sqrt(2) - 1))
        pitch = 2 * hb2 + run + 0.6
    s0 = (L - nb * pitch) / 2
    pts = [p0]
    for k in range(nb):
        t = s0 + k * pitch
        for dt, dh in ((0, 0), (hb2, hb2), (hb2 + run, hb2), (2 * hb2 + run, 0)):
            pts.append((p0[0] + u[0] * (t + dt) + n[0] * dh, p0[1] + u[1] * (t + dt) + n[1] * dh))
    pts.append(p1)
    short = short[:i] + pts + short[i + 2:]
    return (short, long_) if La < Lb else (long_, short)


def route_slot(slot, cem_x, cem_c, mcio_x, mcio_c, nets, x_end):
    """cem_x(n)/mcio_x(n): board x of pin n; cem_c=(cx, cy); mcio_c=(mx, my) (MCIO on B, rows at my+6 / my+8).
    nets(kind, lane) -> (p_net, n_net).  Returns (tracks, vias, report rows)."""
    cx, cy = cem_c
    mx, my = mcio_c
    yB, yA = cy + 3.85, cy - 3.85
    vB, vA = yB - 1.75, yA - 1.75                # CEM via lines (near: inward, far: outward)
    mA, mB = my + 6.0, my + 8.0
    mvA, mvB = mA - 1.4, mB + 1.4                # MCIO via lines (A: toward the body, B: outward)
    tracks, vias, rep = [], [], []
    for kind, layer, cem_pairs, crow, cvia, mrow, mvia in (
            ('HTX', 'In2', NEAR, yB, vB, mA, mvA), ('HRX', 'In4', FAR, yA, vA, mB, mvB)):
        starts, ends, info = [], [], []
        for lane in range(8):
            a, b = cem_pairs[lane]
            xa, xb = cem_x(a), cem_x(b)
            ma, mb = MCIO[lane]
            ya, yb = mcio_x(ma), mcio_x(mb)
            pn = nets(kind, lane)
            # dog-bones on the pad layer (F for the CEM, B for the MCIO)
            for net, x in ((pn[0], xa), (pn[1], xb)):
                tracks.append(dict(net=net, layer='F', width=0.15, pts=[(x, crow), (x, cvia)]))
                vias.append(dict(net=net, at=(x, cvia), **VIA))
            for net, x in ((pn[0], ya), (pn[1], yb)):
                tracks.append(dict(net=net, layer='B', width=0.15, pts=[(x, mrow), (x, mvia)]))
                vias.append(dict(net=net, at=(x, mvia), **VIA))
            starts.append(((xa + xb) / 2, cvia))
            gap_x = mcio_x(mb + 1) if kind == 'HRX' else None     # A-row GND pin beside the pair (no via there)
            ends.append(((ya + yb) / 2, mvia, gap_x))
            info.append((lane, pn, (xa, xb), (ya, yb)))
        # level assignment
        order = sorted(range(8), key=lambda k: -starts[k][0])            # j = 0 nearest the U-turn end
        j_of = {k: j for j, k in enumerate(order)}
        ybot0 = cy - 7.2
        xup0 = x_end
        ytop0 = cy + 9.0
        right = [k for k in range(8) if (ends[k][2] or ends[k][0]) > xup0 + j_of[k] * P]
        left = [k for k in range(8) if k not in right]
        top = {}
        for grp, rev in ((right, False), (left, True)):
            g = sorted(grp, key=lambda k: j_of[k], reverse=rev)          # first = highest
            for r, k in enumerate(g):
                top[k] = ytop0 + (len(g) - 1 - r) * P
        centre = {}
        for k in range(8):
            j = j_of[k]
            sx, sy = starts[k]
            ex, ey, gx = ends[k]
            yb_ = ybot0 - j * P
            xu = xup0 + j * P
            yt = top[k]
            pts = [(sx, sy), (sx, yb_), (xu, yb_), (xu, yt)]
            if gx is None:
                pts += [(ex, yt), (ex, ey)]
            else:
                ylim = mvA + 1.0                                       # just past the A-row via line
                jog = []
                for hx, hy in ((mx - 11.0, my + 1.5), (mx + 11.0, my + 1.5)):     # MCIO locating-peg NPTHs
                    if abs(gx - hx) < HOLE_CLR and yt < hy < ylim:
                        gx2 = hx + math.copysign(HOLE_CLR + 0.05, mx - hx)       # pass the peg on the body side
                        jog = [(gx2, yt), (gx2, hy + 1.0), (gx, hy + 1.0 + abs(gx - gx2))]
                pts += (jog or [(gx, yt)]) + [(gx, ylim), (ex, ylim + abs(gx - ex)), (ex, ey)]
            centre[k] = chamfer(pts)
        # spacing check on this layer
        worst = 99.0
        for k in range(8):
            for m in range(k + 1, 8):
                for a1, a2 in zip(centre[k][1:-2], centre[k][2:-1]):
                    for b1, b2 in zip(centre[m][1:-2], centre[m][2:-1]):
                        worst = min(worst, seg_dist(a1, a2, b1, b2))
        for k in range(8):
            lane, pn, (xa, xb), (ya, yb) = info[k]
            c = centre[k]
            # left/right of travel: travel starts downward (-y); left of 'down' is +x
            lp = offset(c, H)
            rp = offset(c, -H)
            # assign: the trace starting nearer xa gets net p
            if abs(lp[0][0] - xa) < abs(rp[0][0] - xa):
                pp, nn = lp, rp
            else:
                pp, nn = rp, lp
            # necks: from the via centres to the coupled ends
            p_pts = [(xa, cvia)] + pp[1:-1] + [(ya if abs(pp[-2][0] - ya) <= abs(pp[-2][0] - yb) else yb, ends[k][1])]
            n_pts = [(xb, cvia)] + nn[1:-1] + [(yb if p_pts[-1][0] == ya else ya, ends[k][1])]
            p_pts, n_pts = deskew(p_pts, n_pts)
            tracks.append(dict(net=pn[0], layer=layer, width=W, pts=p_pts))
            tracks.append(dict(net=pn[1], layer=layer, width=W, pts=n_pts))
            Lp, Ln = length(p_pts), length(n_pts)
            rep.append(dict(slot=slot, dir=kind, lane=lane, layer=layer, p=pn[0], len_p=round(Lp, 2), len_n=round(Ln, 2),
                            skew=round(Lp - Ln, 3), min_pair_spacing=round(worst, 3),
                            mcio_swap=(p_pts[-1][0] != ya)))
    return tracks, vias, rep
