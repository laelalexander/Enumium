"""Machine shop-drawing kit (Anatomy plant tools): build-ready detail and assembly sheets drawn from engineered numbers.

Unlike partsheet.py (automatic views of a CAD solid), every line and dimension here is placed on purpose, the way a
designer details a part for the shop:

  Sheet(...)            ARCH D sheet, title block with material / finish / mass / tolerance block / revision row
  sheet.view(ox, oy, s) a 2D view: model mm (x right, y up) -> sheet px at scale s px/mm
  V.line / poly / rect / circle / arc / hatch / centre / hidden / phantom
  V.dim(p1, p2, off)    linear dimension (h, v or aligned), dual units by default, optional tolerance text
  V.dia / V.rad / V.angle / V.leader / V.note / V.hole
  V.weld(...)           AWS A2.4 weld symbol: fillet, square/V/bevel groove, plug, both sides, all around, field, tail
  V.finish(...)         surface finish symbol with Ra
  V.fcf(...)            GD&T feature control frame;  V.datum(...) datum feature symbol
  V.cut(...)            section cutting plane with arrows;  V.detail(...) detail circle
  dxf_profile(...)      write a flat pattern / cut file in mm and inch (ezdxf)

Dual units: mm [in]. Third-angle projection. Pure Python + ezdxf; SVG out.
"""
import math
from html import escape

SW, SH = 3456, 2304
IN = 25.4
INK, DIM, HID, CEN, BAL, WELD, HAT = "#111", "#b00020", "#7b8288", "#2e7d32", "#0d47a1", "#4a148c", "#546e7a"


def fin(v, d=3):
    s = f"{v / IN:.{d}f}"
    return s[1:] if s.startswith("0.") else s.replace("-0.", "-.")


def mmi(v, d=None, tol=None):
    """'120 [4.724]' ; d = mm decimals (auto: 0 if whole, else 1 or 2)."""
    if d is None:
        d = 0 if abs(v - round(v)) < 1e-6 else (1 if abs(v * 10 - round(v * 10)) < 1e-6 else 2)
    s = f"{v:.{d}f} [{fin(v)}]"
    return s + (f" {tol}" if tol else "")


def _defs():
    return ('<defs>'
            '<pattern id="hA" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" stroke="#546e7a" stroke-width="1"/></pattern>'
            '<pattern id="hB" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(135)"><line x1="0" y1="0" x2="0" y2="8" stroke="#546e7a" stroke-width="1"/></pattern>'
            '<pattern id="hC" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="#546e7a" stroke-width="0.9"/></pattern>'
            '<pattern id="hS" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="14" stroke="#546e7a" stroke-width="0.8"/><line x1="4" y1="0" x2="4" y2="14" stroke="#546e7a" stroke-width="0.8"/></pattern>'
            '</defs>')


class Sheet:
    """ARCH D shop sheet. tb: dict(title, number, project, scale, material, finish, mass, rev, sheet, tol, qty, drawn)."""

    def __init__(self, **tb):
        self.tb = dict(rev="A", sheet="1 of 1", scale="AS SHOWN", qty="1", drawn="Anatomy plant/mechsheet.py", date="2026-11-17",
                       tol="LINEAR ±0.5 [±.02] · HOLES +0.2/-0 · ANGLES ±0.5° · MACHINED X.X ±0.1, X.XX ±0.05", material="-", finish="-", mass="-")
        self.tb.update(tb)
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" viewBox="0 0 {SW} {SH}" font-family="Helvetica,Arial,sans-serif">',
                  '<rect width="100%" height="100%" fill="#fff"/>', _defs(),
                  f'<rect x="24" y="24" width="{SW - 48}" height="{SH - 48}" fill="none" stroke="{INK}" stroke-width="3"/>']
        for i in range(8):
            x = 24 + (SW - 48) * (i + 0.5) / 8
            self.o.append(f'<text x="{x}" y="18" font-size="14" text-anchor="middle">{8 - i}</text><text x="{x}" y="{SH - 6}" font-size="14" text-anchor="middle">{8 - i}</text>')
        for i in range(6):
            y = 24 + (SH - 48) * (i + 0.5) / 6
            self.o.append(f'<text x="12" y="{y}" font-size="14" text-anchor="middle">{"FEDCBA"[i]}</text><text x="{SW - 12}" y="{y}" font-size="14" text-anchor="middle">{"FEDCBA"[i]}</text>')
        self._title_block()

    def _title_block(self):
        t = self.tb
        x, y, w, h = SW - 900, SH - 350, 876, 326
        o = [f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="{INK}" stroke-width="2"/>',
             f'<text x="{x + 12}" y="{y + 34}" font-size="26" font-weight="bold">{escape(t["title"])}</text>',
             f'<text x="{x + 12}" y="{y + 58}" font-size="15">{escape(t["project"])}</text>',
             f'<line x1="{x}" y1="{y + 70}" x2="{x + w}" y2="{y + 70}" stroke="{INK}"/>']
        cells = [("DRAWING NO.", t["number"], 0, 0, 2), ("REV", t["rev"], 2, 0, 1), ("SCALE", t["scale"], 3, 0, 1),
                 ("MATERIAL", t["material"], 0, 1, 4), ("FINISH", t["finish"], 0, 2, 4),
                 ("MASS (CALC.)", t["mass"], 0, 3, 1), ("QTY PER MACHINE", t["qty"], 1, 3, 1), ("UNITS", "mm [in]", 2, 3, 1), ("SHEET", f"ARCH D · {t['sheet']}", 3, 3, 1),
                 ("DRAWN", t["drawn"], 0, 4, 2), ("DATE", t["date"], 2, 4, 1), ("STATUS", "FOR REVIEW", 3, 4, 1)]
        cw, rh = w / 4, 44
        for lab, val, c, r, span in cells:
            cx, cy = x + c * cw, y + 70 + r * rh
            o.append(f'<rect x="{cx}" y="{cy}" width="{cw * span}" height="{rh}" fill="none" stroke="#90a4ae" stroke-width="0.8"/>'
                     f'<text x="{cx + 6}" y="{cy + 13}" font-size="10.5" fill="#555">{lab}</text>')
            fs = 17 if len(str(val)) * 9 < cw * span else max(10, int(17 * cw * span / (len(str(val)) * 9.5)))
            o.append(f'<text x="{cx + 6}" y="{cy + 35}" font-size="{fs}" font-weight="{"bold" if lab in ("DRAWING NO.", "REV") else "normal"}">{escape(str(val))}</text>')
        o.append(f'<text x="{x + 12}" y="{y + h - 10}" font-size="10.5">UNLESS NOTED: {escape(t["tol"])} · THIRD-ANGLE PROJECTION · BREAK EDGES 0.5 · ASME Y14.5</text>')
        o.append('</g>')
        self.o += o

    def add(self, s):
        self.o.append(s)

    def view(self, ox, oy, s, label=None, label_at=None):
        v = V(self, ox, oy, s)
        if label:
            lx, ly = label_at or (ox, oy - 30)
            self.add(f'<text x="{lx}" y="{ly}" font-size="20" font-weight="bold">{escape(label)}</text>')
        return v

    def text(self, x, y, s, fs=15, anchor="start", bold=False, color=INK):
        self.add(f'<text x="{x}" y="{y}" font-size="{fs}" text-anchor="{anchor}" fill="{color}"{" font-weight=\"bold\"" if bold else ""}>{escape(s)}</text>')

    def table(self, x, y, cols, rows, title=None, fs=14, rh=24):
        o = []
        if title:
            o.append(f'<text x="{x}" y="{y - 9}" font-size="{fs + 5}" font-weight="bold">{escape(title)}</text>')
        W = sum(w for _, w in cols)
        o.append(f'<rect x="{x}" y="{y}" width="{W}" height="{rh}" fill="#eceff1" stroke="{INK}"/>')
        cx = x
        for hname, w in cols:
            o.append(f'<text x="{cx + 5}" y="{y + rh - 7}" font-size="{fs - 1}" font-weight="bold">{escape(hname)}</text>'); cx += w
        yy = y + rh
        for i, r in enumerate(rows):
            o.append(f'<rect x="{x}" y="{yy}" width="{W}" height="{rh}" fill="{"#fafafa" if i % 2 else "#fff"}" stroke="#b0bec5" stroke-width="0.6"/>')
            cx = x
            for (hname, w), v in zip(cols, r):
                maxc = int(w / ((fs - 1) * 0.5))
                s = str(v); s = s if len(s) <= maxc else s[: maxc - 1] + "…"
                o.append(f'<text x="{cx + 5}" y="{yy + rh - 7}" font-size="{fs - 1}">{escape(s)}</text>'); cx += w
            yy += rh
        self.add("".join(o))
        return yy - y

    def notes(self, x, y, w, lines, title="NOTES", fs=14):
        wrapped = []
        for i, l in enumerate(lines):
            chunks = _wrap(f"{i + 1}. {l}", int(w / (fs * 0.5)))
            wrapped += [(c, j > 0) for j, c in enumerate(chunks)]
        h = 34 + (fs + 5) * len(wrapped)
        o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="{INK}"/><text x="{x + 10}" y="{y + 24}" font-size="{fs + 3}" font-weight="bold">{escape(title)}</text>']
        for i, (l, cont) in enumerate(wrapped):
            o.append(f'<text x="{x + (28 if cont else 10)}" y="{y + 46 + (fs + 5) * i}" font-size="{fs}">{escape(l)}</text>')
        self.add("".join(o))
        return h

    def svg(self):
        return "\n".join(self.o) + "\n</svg>"

    def save(self, path):
        open(path, "w").write(self.svg())


def _wrap(s, n):
    out, cur = [], ""
    for w in s.split(" "):
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return out + [cur]


STY = {"vis": f'stroke="{INK}" stroke-width="2"', "thin": f'stroke="{INK}" stroke-width="1"', "hid": f'stroke="{HID}" stroke-width="1.2" stroke-dasharray="8,4"',
       "cen": f'stroke="{CEN}" stroke-width="0.9" stroke-dasharray="22,4,4,4"', "phan": f'stroke="#607d8b" stroke-width="1.1" stroke-dasharray="20,4,4,4,4,4"',
       "cut": f'stroke="{INK}" stroke-width="3" stroke-dasharray="26,5,5,5"', "bend": f'stroke="{DIM}" stroke-width="1.2" stroke-dasharray="14,5"'}


class V:
    """2D view: model (x right, y up, mm) -> sheet px."""

    def __init__(self, sheet, ox, oy, s):
        self.S, self.ox, self.oy, self.s = sheet, ox, oy, s

    def p(self, x, y):
        return self.ox + x * self.s, self.oy - y * self.s

    def add(self, s):
        self.S.add(s)

    # ---- geometry
    def line(self, x1, y1, x2, y2, k="vis"):
        a, b = self.p(x1, y1), self.p(x2, y2)
        self.add(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" {STY[k]} fill="none"/>')

    def poly(self, pts, k="vis", closed=True, fill="none", op=1.0):
        d = " ".join(f"{a:.2f},{b:.2f}" for a, b in (self.p(*q) for q in pts))
        tag = "polygon" if closed else "polyline"
        self.add(f'<{tag} points="{d}" {STY[k]} fill="{fill}" fill-opacity="{op}" stroke-linejoin="round"/>')

    def rect(self, x, y, w, h, k="vis", fill="none"):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], k, True, fill)

    def hatch(self, pts, pat="hA", k="vis"):
        self.poly(pts, k, True, f"url(#{pat})")

    def circle(self, cx, cy, r, k="vis", fill="none"):
        c = self.p(cx, cy)
        self.add(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{r * self.s:.2f}" {STY[k]} fill="{fill}"/>')

    def arc(self, cx, cy, r, a0, a1, k="vis", n=None):
        n = n or max(8, int(abs(a1 - a0) / 3))
        pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
        self.poly(pts, k, False)

    def centre(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y2, "cen")

    def cmark(self, cx, cy, r):
        e = r + 4 / self.s * 3
        self.centre(cx - e, cy, cx + e, cy); self.centre(cx, cy - e, cx, cy + e)

    def text(self, x, y, s, fs=14, anchor="middle", color=INK, rot=0, bold=False):
        a = self.p(x, y)
        tr = f' transform="rotate({rot},{a[0]:.1f},{a[1]:.1f})"' if rot else ""
        self.add(f'<text x="{a[0]:.1f}" y="{a[1]:.1f}" font-size="{fs}" text-anchor="{anchor}" fill="{color}"{tr}{" font-weight=\"bold\"" if bold else ""}>{escape(s)}</text>')

    # ---- dimensions (offset in px, + = above / right / left-of-direction)
    def dim(self, p1, p2, off, label=None, d="a", tol=None, fs=14, ext=True, txt_shift=0):
        (x1, y1), (x2, y2) = self.p(*p1), self.p(*p2)
        if d == "h":
            ux, uy = 1.0, 0.0
            L = abs(p2[0] - p1[0])
        elif d == "v":
            ux, uy = 0.0, -1.0
            L = abs(p2[1] - p1[1])
        else:
            L = math.hypot(p2[0] - p1[0], p2[1] - p1[1]); ux, uy = (x2 - x1), (y2 - y1); n = math.hypot(ux, uy) or 1; ux, uy = ux / n, uy / n
        nx, ny = uy, -ux                                       # left normal on screen
        if d == "h":
            nx, ny = 0, -1
        if d == "v":
            nx, ny = -1, 0
        # dimension line points: project p1,p2 onto the line through base point offset
        if d == "h":
            yb = min(y1, y2) - off if off > 0 else max(y1, y2) - off
            a, b = (x1, yb), (x2, yb); e1, e2 = (x1, y1), (x2, y2)
        elif d == "v":
            xb = min(x1, x2) - off if off > 0 else max(x1, x2) - off
            a, b = (xb, y1), (xb, y2); e1, e2 = (x1, y1), (x2, y2)
        else:
            a, b = (x1 + nx * off, y1 + ny * off), (x2 + nx * off, y2 + ny * off); e1, e2 = (x1, y1), (x2, y2)
        lab = label if label is not None else mmi(L)
        if tol:
            lab += " " + tol
        o = [f'<g stroke="{DIM}" fill="{DIM}" stroke-width="0.9">']
        if ext:
            for (ex, ey), (bx, by) in ((e1, a), (e2, b)):
                dx, dy = bx - ex, by - ey; ll = math.hypot(dx, dy)
                if ll > 1:
                    o.append(f'<line x1="{ex + dx / ll * 3:.1f}" y1="{ey + dy / ll * 3:.1f}" x2="{bx + dx / ll * 6:.1f}" y2="{by + dy / ll * 6:.1f}" stroke-width="0.7"/>')
        o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        for (px, py), s in ((a, 1), (b, -1)):
            r = math.radians(ang + (0 if s > 0 else 180))
            c, sn = math.cos(r), math.sin(r)
            q1 = (px + c * 11 - sn * 3.5, py + sn * 11 + c * 3.5); q2 = (px + c * 11 + sn * 3.5, py + sn * 11 - c * 3.5)
            o.append(f'<path d="M{px:.1f},{py:.1f} L{q1[0]:.1f},{q1[1]:.1f} L{q2[0]:.1f},{q2[1]:.1f} z" stroke="none"/>')
        mx, my = (a[0] + b[0]) / 2 + txt_shift * math.cos(math.radians(ang)), (a[1] + b[1]) / 2 + txt_shift * math.sin(math.radians(ang))
        if ang > 90 or ang <= -90:
            ang -= 180
        o.append(f'<text transform="translate({mx:.1f},{my:.1f}) rotate({ang:.1f})" y="-6" font-size="{fs}" text-anchor="middle" stroke="none">{escape(lab)}</text></g>')
        self.add("".join(o))

    def leader(self, at, to, lines, fs=14, color=DIM, anchor=None):
        a = self.p(*at); t = to if isinstance(to, tuple) and len(to) == 2 else to
        tx, ty = self.p(*t)
        anchor = anchor or ("start" if tx >= a[0] else "end")
        sh = 6 if anchor == "start" else -6
        o = [f'<g stroke="{color}" fill="{color}" stroke-width="0.9"><line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{tx:.1f}" y2="{ty:.1f}"/>'
             f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{tx + sh * 3:.1f}" y2="{ty:.1f}"/>']
        ang = math.atan2(a[1] - ty, a[0] - tx)
        c, s = math.cos(ang), math.sin(ang)
        o.append(f'<path d="M{a[0]:.1f},{a[1]:.1f} L{a[0] - c * 12 - s * 3.5:.1f},{a[1] - s * 12 + c * 3.5:.1f} L{a[0] - c * 12 + s * 3.5:.1f},{a[1] - s * 12 - c * 3.5:.1f} z" stroke="none"/>')
        for i, l in enumerate(lines if isinstance(lines, (list, tuple)) else [lines]):
            o.append(f'<text x="{tx + sh * 4:.1f}" y="{ty + 5 + i * (fs + 3):.1f}" font-size="{fs}" text-anchor="{anchor}" stroke="none">{escape(l)}</text>')
        o.append("</g>")
        self.add("".join(o))

    def dia(self, cx, cy, r, ang, to, label=None, tol=None, fs=14):
        a = math.radians(ang)
        lab = label or f"Ø{mmi(2 * r)}"
        self.leader((cx + r * math.cos(a), cy + r * math.sin(a)), to, [lab + (" " + tol if tol else "")], fs)

    def rad(self, cx, cy, r, ang, to, label=None, fs=14):
        a = math.radians(ang)
        self.leader((cx + r * math.cos(a), cy + r * math.sin(a)), to, [label or f"R{mmi(r)}"], fs)

    def angle(self, c, r, a0, a1, label=None, fs=14):
        self.arc(c[0], c[1], r, a0, a1, "thin")
        am = math.radians((a0 + a1) / 2)
        self.text(c[0] + (r + 8 / self.s) * math.cos(am), c[1] + (r + 8 / self.s) * math.sin(am), label or f"{abs(a1 - a0):.1f}°", fs, color=DIM)

    def note(self, x, y, lines, fs=14, anchor="start", color=INK):
        a = self.p(x, y)
        for i, l in enumerate(lines if isinstance(lines, (list, tuple)) else [lines]):
            self.add(f'<text x="{a[0]:.1f}" y="{a[1] + i * (fs + 4):.1f}" font-size="{fs}" text-anchor="{anchor}" fill="{color}">{escape(l)}</text>')

    def tag(self, x, y, n, at=None, color=BAL):
        """balloon n at model (x,y), leader to model point at."""
        c = self.p(x, y)
        o = ""
        if at:
            q = self.p(*at)
            o += f'<line x1="{q[0]:.1f}" y1="{q[1]:.1f}" x2="{c[0]:.1f}" y2="{c[1]:.1f}" stroke="{color}" stroke-width="1.1"/><circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="3.5" fill="{color}"/>'
        o += (f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="20" fill="#fff" stroke="{color}" stroke-width="2"/>'
              f'<text x="{c[0]:.1f}" y="{c[1] + 6:.1f}" font-size="{17 if len(str(n)) < 3 else 13}" font-weight="bold" text-anchor="middle" fill="{color}">{n}</text>')
        self.add(o)

    # ---- AWS A2.4 weld symbol
    def weld(self, at, to, kind="fillet", size="", other=None, length="", allround=False, field=False, tail=None, side="arrow", contour=None):
        """kind: fillet | sq | v | bevel | plug | flare ; other = same kinds for the other side (both sides when equal);
        side 'arrow' draws the symbol under the reference line (arrow side), 'other' above."""
        a = self.p(*at); t = self.p(*to)
        L = 120
        right = t[0] >= a[0]
        x0, y0 = t; x1 = x0 + (L if right else -L)
        o = [f'<g stroke="{WELD}" fill="none" stroke-width="1.4"><line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{x0:.1f}" y2="{y0:.1f}"/>'
             f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y0:.1f}"/>']
        ang = math.atan2(a[1] - y0, a[0] - x0); c, s = math.cos(ang), math.sin(ang)
        o.append(f'<path d="M{a[0]:.1f},{a[1]:.1f} L{a[0] - c * 13 - s * 4:.1f},{a[1] - s * 13 + c * 4:.1f} L{a[0] - c * 13 + s * 4:.1f},{a[1] - s * 13 - c * 4:.1f} z" fill="{WELD}"/>')
        sx = x0 + (L * 0.42 if right else -L * 0.42)

        def sym(k, sgn):          # sgn +1 below line (arrow side), -1 above (other side)
            y = y0
            if k == "fillet":
                return f'<path d="M{sx - 9:.1f},{y:.1f} L{sx - 9:.1f},{y + sgn * 17:.1f} L{sx + 9:.1f},{y:.1f}"/>'
            if k == "sq":
                return f'<path d="M{sx - 5:.1f},{y:.1f} v{sgn * 15} M{sx + 5:.1f},{y:.1f} v{sgn * 15}"/>'
            if k == "v":
                return f'<path d="M{sx - 11:.1f},{y + sgn * 15:.1f} L{sx:.1f},{y:.1f} L{sx + 11:.1f},{y + sgn * 15:.1f}"/>'
            if k == "bevel":
                return f'<path d="M{sx - 6:.1f},{y:.1f} v{sgn * 16} M{sx - 6:.1f},{y:.1f} L{sx + 8:.1f},{y + sgn * 15:.1f}"/>'
            if k == "plug":
                return f'<rect x="{sx - 9:.1f}" y="{(y if sgn > 0 else y - 10):.1f}" width="18" height="10"/>'
            if k == "flare":
                return f'<path d="M{sx - 10:.1f},{y:.1f} v{sgn * 6} M{sx + 10:.1f},{y:.1f} v{sgn * 6} M{sx - 10:.1f},{y + sgn * 6:.1f} q 10 {sgn * 10} 20 0"/>'
            return ""
        main_sgn = 1 if side == "arrow" else -1
        o.append(sym(kind, main_sgn))
        if other:
            o.append(sym(other, -main_sgn))
        if contour == "flush":
            o.append(f'<line x1="{sx - 11:.1f}" y1="{y0 + main_sgn * 22:.1f}" x2="{sx + 11:.1f}" y2="{y0 + main_sgn * 22:.1f}"/>')
        tx = sx - (16 if right else -16)
        o.append(f'<text x="{tx:.1f}" y="{y0 + (16 if main_sgn > 0 else -5):.1f}" font-size="14" fill="{WELD}" stroke="none" text-anchor="end">{escape(size)}</text>')
        if other:
            o.append(f'<text x="{tx:.1f}" y="{y0 + (-5 if main_sgn > 0 else 16):.1f}" font-size="14" fill="{WELD}" stroke="none" text-anchor="end">{escape(size)}</text>')
        if length:
            o.append(f'<text x="{sx + 16:.1f}" y="{y0 + (16 if main_sgn > 0 else -5):.1f}" font-size="14" fill="{WELD}" stroke="none">{escape(length)}</text>')
        if allround:
            o.append(f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="6"/>')
        if field:
            o.append(f'<path d="M{x0:.1f},{y0:.1f} v-20 l13,5 l-13,5" fill="{WELD}"/>')
        if tail:
            o.append(f'<path d="M{x1:.1f},{y0:.1f} l{10 if right else -10},-9 M{x1:.1f},{y0:.1f} l{10 if right else -10},9"/>'
                     f'<text x="{x1 + (16 if right else -16):.1f}" y="{y0 + 5:.1f}" font-size="13" fill="{WELD}" stroke="none" text-anchor="{"start" if right else "end"}">{escape(tail)}</text>')
        o.append("</g>")
        self.add("".join(o))

    def finish(self, at, ra, to=None):
        a = self.p(*at)
        x, y = a
        self.add(f'<g stroke="{INK}" fill="none" stroke-width="1.1"><path d="M{x - 9:.1f},{y - 11:.1f} L{x:.1f},{y:.1f} L{x + 20:.1f},{y - 30:.1f} h22"/>'
                 f'<line x1="{x - 9:.1f}" y1="{y - 11:.1f}" x2="{x + 12:.1f}" y2="{y - 11:.1f}"/>'
                 f'<text x="{x + 22:.1f}" y="{y - 34:.1f}" font-size="12.5" fill="{INK}" stroke="none">Ra {escape(ra)}</text></g>')

    def fcf(self, x, y, cells, fs=15):
        """feature control frame at model (x, y): cells like ['⌭', '0.05', 'A'] ; returns nothing."""
        a = self.p(x, y)
        cx = a[0]; o = []
        for c in cells:
            w = max(30, 10 + len(c) * fs * 0.6)
            o.append(f'<rect x="{cx:.1f}" y="{a[1] - 14:.1f}" width="{w:.1f}" height="28" fill="#fff" stroke="{INK}" stroke-width="1.2"/>'
                     f'<text x="{cx + w / 2:.1f}" y="{a[1] + 6:.1f}" font-size="{fs}" text-anchor="middle">{escape(c)}</text>')
            cx += w
        self.add("".join(o))

    def datum(self, at, label, d=(0, -1)):
        a = self.p(*at)
        x2, y2 = a[0] + d[0] * 40, a[1] - d[1] * 40
        self.add(f'<g stroke="{INK}" stroke-width="1.2"><path d="M{a[0] - 8:.1f},{a[1]:.1f} L{a[0] + 8:.1f},{a[1]:.1f} L{a[0]:.1f},{a[1] + (12 if d[1] < 0 else -12):.1f} z" fill="{INK}"/>'
                 f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/><rect x="{x2 - 15:.1f}" y="{y2 - 15 + (15 if d[1] < 0 else -15):.1f}" width="30" height="30" fill="#fff"/>'
                 f'<text x="{x2:.1f}" y="{y2 + 6 + (15 if d[1] < 0 else -15):.1f}" font-size="18" font-weight="bold" text-anchor="middle" stroke="none">{escape(label)}</text></g>')

    def cut(self, p1, p2, label, arrow=(0, 1)):
        a, b = self.p(*p1), self.p(*p2)
        o = [f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" {STY["cut"]}/>']
        for q in (a, b):
            ex, ey = q[0] + arrow[0] * 40, q[1] - arrow[1] * 40
            o.append(f'<line x1="{q[0]:.1f}" y1="{q[1]:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{INK}" stroke-width="3"/>'
                     f'<path d="M{ex:.1f},{ey:.1f} l{-6 + arrow[0] * 0:.1f},{6} l12,0 z" fill="{INK}" transform="rotate({math.degrees(math.atan2(-arrow[1], arrow[0])) - 90:.0f},{ex:.1f},{ey:.1f})"/>'
                     f'<text x="{ex + arrow[0] * 22:.1f}" y="{ey - arrow[1] * 22 + 8:.1f}" font-size="24" font-weight="bold" text-anchor="middle">{escape(label)}</text>')
        self.add("".join(o))

    def detail(self, cx, cy, r, label):
        self.circle(cx, cy, r, "phan")
        self.text(cx + r * 0.75, cy + r * 0.8, label, 20, bold=True)


# ------------------------------------------------------------------ DXF cut files
def dxf_profile(path_stem, outer, holes=(), arcs=(), lines=(), bends=(), text=None):
    """outer: list of (x,y) closed polyline (mm) or list of such; holes: (cx, cy, r); arcs: (cx, cy, r, a0, a1); bends: ((x1,y1),(x2,y2)) on BEND layer.
    Writes <stem>_mm.dxf and <stem>_in.dxf."""
    import ezdxf
    for unit, k in (("mm", 1.0), ("in", 1 / IN)):
        doc = ezdxf.new("R2010"); doc.units = 4 if unit == "mm" else 1
        msp = doc.modelspace()
        for name, col in (("CUT", 7), ("BEND", 1), ("MARK", 3)):
            doc.layers.add(name, color=col)
        polys = outer if outer and isinstance(outer[0][0], (list, tuple)) else [outer]
        for pl in polys:
            if pl:
                msp.add_lwpolyline([(x * k, y * k) for x, y in pl], close=True, dxfattribs={"layer": "CUT"})
        for cx, cy, r in holes:
            msp.add_circle((cx * k, cy * k), r * k, dxfattribs={"layer": "CUT"})
        for cx, cy, r, a0, a1 in arcs:
            msp.add_arc((cx * k, cy * k), r * k, a0, a1, dxfattribs={"layer": "CUT"})
        for (x1, y1), (x2, y2) in lines:
            msp.add_line((x1 * k, y1 * k), (x2 * k, y2 * k), dxfattribs={"layer": "CUT"})
        for (x1, y1), (x2, y2) in bends:
            msp.add_line((x1 * k, y1 * k), (x2 * k, y2 * k), dxfattribs={"layer": "BEND"})
        if text:
            msp.add_text(text, dxfattribs={"layer": "MARK", "height": 5 * k}).set_placement((0, -15 * k))
        doc.saveas(f"{path_stem}_{unit}.dxf")
