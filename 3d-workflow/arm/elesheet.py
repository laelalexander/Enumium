"""Electrical drawings from one netlist: ELE-001 schematic (every wire numbered, every terminal named) and ELE-002
wire list (from / to / signal / gauge / colour / cut length), plus fab/WIRELIST.csv for the kit.

Pins come from arm/twin.py WIRING (the same table the firmware uses). Designators:
X0 IEC inlet (switch + fuse)   PSU1 24 V 15 A   F1 20 A fuse   S1 E-stop (NC)   TB1 +24 V bus   TB2 0 V bus
TB3 +5 V logic bus   TB4 logic GND bus   A1 Arduino Mega 2560   U1..U5 stepper drivers   M1..M5 motors
S2..S6 limit switches (NC)   C1..C5 100 nF   E1 enclosure earth stud."""
import csv
from html import escape

from . import sheets as S
from .twin import WIRING, ENABLE_PIN
from .fab import harness

JOINTS = [("J1", "yaw", "NEMA23 20:1", "DM542"), ("J2", "shoulder", "NEMA23 20:1 + 5:1 belt", "DM542"),
          ("J3", "elbow", "NEMA23 20:1 + 3:1 belt", "DM542"), ("J4", "wrist", "NEMA23 20:1 + 1:1 belt", "DM542"),
          ("J5", "gripper", "NEMA17 + T8 lead screw", "TB6600 or DM542")]
COL = {"mains": "#6d4c41", "pe": "#2e7d32", "24v": "#c62828", "0v": "#212121", "5v": "#ef6c00", "sig": "#1565c0",
       "motor": "#6a1b9a", "limit": "#00838f"}
PHASE_COL = {"A+": "black", "A-": "green", "B+": "red", "B-": "blue"}


def netlist():
    """Every wire: (no, from, to, signal, awg, colour, cut_m, kind)."""
    cut = {r[0]: r[2] for r in harness()}
    w = [("W001", "X0:L", "PSU1:L", "mains live", "18", "brown", 0.4, "mains"),
         ("W002", "X0:N", "PSU1:N", "mains neutral", "18", "blue", 0.4, "mains"),
         ("W003", "X0:PE", "PSU1:PE", "protective earth", "18", "green/yellow", 0.4, "pe"),
         ("W004", "E1", "PSU1:PE", "enclosure earth bond", "14 (2.5 mm²)", "green/yellow", 0.3, "pe"),
         ("W010", "PSU1:V+", "F1:1", "+24 V", "14", "red", 0.15, "24v"),
         ("W011", "F1:2", "S1:11", "+24 V fused", "14", "red", 0.2, "24v"),
         ("W012", "S1:12", "TB1:1", "+24 V switched", "14", "red", 0.25, "24v"),
         ("W013", "PSU1:V-", "TB2:1", "0 V", "14", "black", 0.4, "0v"),
         ("W020", "A1:5V", "TB3:1", "+5 V logic", "22", "orange", 0.2, "5v"),
         ("W021", "A1:GND", "TB4:1", "logic GND", "22", "black", 0.2, "0v")]
    for c, (j, name, motor, drv) in enumerate(JOINTS):
        u, p = f"U{c + 1}", WIRING[c]
        w += [(f"W1{c}1", f"TB1:{c + 2}", f"{u}:VCC", f"+24 V {j}", "18", "red", 0.35, "24v"),
              (f"W1{c}2", f"TB2:{c + 2}", f"{u}:GND", f"0 V {j}", "18", "black", 0.35, "0v"),
              (f"W2{c}1", f"TB3:{c + 2}", f"{u}:PUL+", f"+5 V {j}", "22", "orange", 0.3, "5v"),
              (f"W2{c}2", f"{u}:PUL+", f"{u}:DIR+", "+5 V jumper", "22", "orange", 0.05, "5v"),
              (f"W2{c}3", f"{u}:DIR+", f"{u}:ENA+", "+5 V jumper", "22", "orange", 0.05, "5v"),
              (f"W2{c}4", f"A1:D{p['step']}", f"{u}:PUL-", f"STEP {j}", "22", "blue", 0.3, "sig"),
              (f"W2{c}5", f"A1:D{p['dir']}", f"{u}:DIR-", f"DIR {j}", "22", "white", 0.3, "sig"),
              (f"W2{c}6", f"A1:D{ENABLE_PIN}" if c == 0 else f"U{c}:ENA-", f"{u}:ENA-", "ENABLE (HIGH = off)", "22", "yellow", 0.3 if c == 0 else 0.15, "sig")]
        mc = cut.get(f"{j} {name} motor cable", 1.5)
        for k, ph in enumerate(("A+", "A-", "B+", "B-"), 1):
            w.append((f"W3{c}{k}", f"{u}:{ph}", f"M{c + 1}:{ph}", f"{j} phase {ph}", "18", PHASE_COL[ph], mc, "motor"))
        w.append((f"W3{c}5", f"C3{c}:shield", "E1", f"{j} cable shield (enclosure end only)", "18", "drain", 0.15, "pe"))
        lc = cut.get(f"{j} {name} limit switch", 1.5)
        w += [(f"W4{c}1", f"A1:D{p['limit']}", f"S{c + 2}:NC", f"LIMIT {j}", "22", "white", lc, "limit"),
              (f"W4{c}2", f"TB4:{c + 2}", f"S{c + 2}:C", f"limit GND {j}", "22", "black", lc, "limit")]
    return w


def write_csv(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        cw = csv.writer(f)
        cw.writerow(["wire", "from", "to", "signal", "awg", "colour", "cut_m"])
        for r in netlist():
            cw.writerow(r[:7])


# ---------------------------------------------------------------- drawing helpers
def _t(x, y, s, fs=10, anchor="start", bold=False, fill=None):
    return (f'<text x="{x}" y="{y}" font-size="{fs}" text-anchor="{anchor}"{" font-weight=\"bold\"" if bold else ""}'
            f'{f" fill=\"{fill}\"" if fill else ""}>{escape(str(s))}</text>')


def _w(pts, kind, label=None, at=0, dx=3, dy=-3, width=None):
    d = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    sw = width or (2.2 if kind in ("24v", "0v", "mains", "pe") else 1.3)
    out = f'<path d="{d}" stroke="{COL[kind]}" stroke-width="{sw}" fill="none" stroke-linejoin="round"/>'
    if label:
        x, y = pts[at]
        out += _t(x + dx, y + dy, label, 7.5, fill=COL[kind])
    return out


def _dot(x, y, kind):
    return f'<circle cx="{x}" cy="{y}" r="2.6" fill="{COL[kind]}"/>'


def _term(x, y, name, side="L"):
    """Terminal: small square on the block edge with its name inside the block."""
    tx = x + 6 if side == "L" else x - 6
    return (f'<rect x="{x - 2.5}" y="{y - 2.5}" width="5" height="5" fill="#fff" stroke="{S.INK}" stroke-width="0.8"/>'
            + _t(tx, y + 3.2, name, 8, "start" if side == "L" else "end"))


def _block(x, y, w, h, title, sub=None, fill="#f7f9fb"):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{S.INK}" stroke-width="1.3"/>'
    out += _t(x + w / 2, y - 5, title, 10, "middle", True)
    if sub:
        out += _t(x + w / 2, y + h + 11, sub, 7.5, "middle", fill="#555")
    return out


def ele001():
    N = {r[0]: r for r in netlist()}
    b = ''
    b += _t(40, 46, "WIRING SCHEMATIC: power, logic, 5 axes, limits. Wire numbers Wxxx match ELE-002 and fab/WIRELIST.csv.", 12, bold=True)
    # ---- mains and PSU
    b += _block(40, 70, 90, 80, "X0 IEC C14 INLET", "switch + 5x20 fuse T3.15A, in ENC-04", "#efebe9")
    b += _block(190, 70, 120, 110, "PSU1 24 V 15 A", "360 W, LRS-350-24 class", "#fff3e0")
    for nm, y, wn, k in (("L", 90, "W001", "mains"), ("N", 110, "W002", "mains"), ("PE", 130, "W003", "pe")):
        b += _term(130, y, nm, "R") + _term(190, y, nm, "L") + _w([(130, y), (190, y)], k, wn, 0, 8)
    b += _w([(160, 130), (160, 205)], "pe", "W004", 1, 4, -6) + _dot(160, 130, "pe")
    b += (f'<g stroke="{COL["pe"]}" stroke-width="1.6"><line x1="146" y1="205" x2="174" y2="205"/><line x1="151" y1="210" x2="169" y2="210"/>'
          f'<line x1="156" y1="215" x2="164" y2="215"/></g>' + _t(178, 214, "E1 earth stud (ENC-04)", 8, fill=COL["pe"]))
    b += _term(310, 95, "V+", "R") + _term(310, 155, "V-", "R")
    # F1, S1 on the +24 V line, then TB1 / TB2
    y24, y0 = 95, 155
    b += _w([(310, y24), (345, y24)], "24v", "W010", 0, 4)
    b += f'<rect x="345" y="{y24 - 6}" width="34" height="12" fill="#fff" stroke="{S.INK}" stroke-width="1.2"/><line x1="345" y1="{y24}" x2="379" y2="{y24}" stroke="{S.INK}"/>'
    b += _t(362, y24 - 10, "F1 20 A", 8.5, "middle", True)
    b += _w([(379, y24), (400, y24)], "24v", "W011", 0, 2, 12)
    b += (f'<g stroke="{S.INK}" stroke-width="1.4" fill="none"><circle cx="400" cy="{y24}" r="2.5"/><circle cx="430" cy="{y24}" r="2.5"/>'
          f'<line x1="398" y1="{y24 + 4}" x2="432" y2="{y24 + 4}"/><line x1="415" y1="{y24 + 4}" x2="415" y2="{y24 - 16}"/>'
          f'<path d="M405,{y24 - 16} a10,8 0 0 1 20,0 z" fill="#d32f2f"/></g>')
    b += _t(415, y24 - 26, "S1 E-STOP 11-12 (NC)", 8.5, "middle", True)
    b += _t(415, y24 + 18, "21-22 spare NC", 7.5, "middle", fill="#555")
    b += _w([(432, y24), (470, y24)], "24v", "W012", 0, 6)
    b += _block(470, 82, 46, 26, "TB1 +24 V", None, "#ffebee") + _block(470, 142, 46, 26, "TB2 0 V", None, "#eceff1")
    b += _w([(310, y0), (470, y0)], "0v", "W013", 0, 60)
    XB24, XB0 = 1012, 1027                                       # driver power buses
    DY = [182 + 145 * c for c in range(5)]
    b += _w([(516, y24), (XB24, y24), (XB24, DY[4] + 20 + 17 * 4)], "24v", None, width=2.8)
    b += _w([(516, y0), (XB0, y0), (XB0, DY[4] + 20 + 17 * 5)], "0v", None, width=2.8)
    b += _t(XB24 - 3, 88, "+24 V", 8, "end", fill=COL["24v"]) + _t(XB0 + 3, 148, "0 V", 8, fill=COL["0v"])
    # ---- Mega
    MX, MY, MW, MH = 440, 210, 150, 500
    b += _block(MX, MY, MW, MH, "A1 ARDUINO MEGA 2560", "USB to the PC (115200 baud); powered from USB", "#e8f5e9")
    b += _t(MX + MW / 2, MY + MH / 2, "firmware/arm_controller", 8, "middle", fill="#555")
    pin_y = {"5V": 240}
    for c in range(5):
        pin_y[f"D{WIRING[c]['step']}"] = 280 + 22 * c
        pin_y[f"D{WIRING[c]['dir']}"] = 400 + 22 * c
    pin_y[f"D{ENABLE_PIN}"] = 520
    for nm, y in pin_y.items():
        b += _term(MX + MW, y, {"5V": "5V"}.get(nm, nm + (" STEP" if 280 <= y < 400 else " DIR" if 400 <= y < 520 else " ENA")), "R")
    lim_y = {f"D{WIRING[c]['limit']}": 560 + 22 * c for c in range(5)}
    for nm, y in lim_y.items():
        b += _term(MX, y, nm + " LIM", "L")
    b += _term(MX, 680, "GND", "L")
    # 5 V bus (TB3) and ENABLE bus right of the Mega, STEP/DIR lanes between
    X5, XEN, XD = 800, 780, 840
    b += _w([(MX + MW, 240), (X5, 240)], "5v", "W020 (via TB3)", 0, 6)
    b += _w([(X5, 240), (X5, DY[4] + 20 + 17 * 4)], "5v", None, width=1.8)
    b += _w([(MX + MW, 520), (XEN, 520)], "sig", "W206", 0, 6)
    b += _w([(XEN, DY[0] + 20 + 17 * 5), (XEN, DY[4] + 20 + 17 * 5)], "sig", None, width=1.6)
    b += _dot(XEN, 520, "sig")
    for c, (j, name, motor, drv) in enumerate(JOINTS):
        y = DY[c]
        b += _block(XD, y, 140, 112, f"U{c + 1} {drv.split(' ')[0]}  ({j})", None, "#f3e5f5")
        t = {k: y + 20 + 17 * i for i, k in enumerate(("PUL+", "PUL-", "DIR+", "DIR-", "ENA+", "ENA-"))}
        r = {k: y + 20 + 17 * i for i, k in enumerate(("A+", "A-", "B+", "B-", "VCC", "GND"))}
        for k, yy in t.items():
            b += _term(XD, yy, k, "L")
        for k, yy in r.items():
            b += _term(XD + 140, yy, k, "R")
        # STEP / DIR lanes
        ls, ld = 620 + 30 * c, 632 + 30 * c
        ys, yd = pin_y[f"D{WIRING[c]['step']}"], pin_y[f"D{WIRING[c]['dir']}"]
        b += _w([(MX + MW, ys), (ls, ys), (ls, t["PUL-"]), (XD, t["PUL-"])], "sig", f"W2{c}4", 0, 8)
        b += _w([(MX + MW, yd), (ld, yd), (ld, t["DIR-"]), (XD, t["DIR-"])], "sig", f"W2{c}5", 0, 8)
        # 5 V to PUL+, jumpers to DIR+ / ENA+
        b += _w([(X5, t["PUL+"]), (XD, t["PUL+"])], "5v", f"W2{c}1", 0, 3) + _dot(X5, t["PUL+"], "5v")
        b += _w([(XD - 14, t["PUL+"]), (XD - 14, t["ENA+"]), (XD, t["ENA+"])], "5v") + _w([(XD - 14, t["DIR+"]), (XD, t["DIR+"])], "5v")
        b += _t(XD - 16, t["DIR+"] + 3, f"W2{c}2", 7, "end", fill=COL["5v"]) + _t(XD - 16, t["ENA+"] + 3, f"W2{c}3", 7, "end", fill=COL["5v"])
        b += _dot(XD - 14, t["PUL+"], "5v") + _dot(XD - 14, t["DIR+"], "5v")
        b += _w([(XEN, t["ENA-"]), (XD, t["ENA-"])], "sig", f"W2{c}6" if c else None, 0, 3) + _dot(XEN, t["ENA-"], "sig")
        # power from the buses
        b += _w([(XD + 140, r["VCC"]), (XB24, r["VCC"])], "24v", f"W1{c}1", 0, 4) + _dot(XB24, r["VCC"], "24v")
        b += _w([(XD + 140, r["GND"]), (XB0, r["GND"])], "0v", f"W1{c}2", 0, 4) + _dot(XB0, r["GND"], "0v")
        # motor
        mx = 1110
        for k, ph in enumerate(("A+", "A-", "B+", "B-")):
            b += _w([(XD + 140, r[ph]), (mx, r[ph])], "motor", f"W3{c}{k + 1}", 0, 50)
            b += _term(mx, r[ph], ph, "L")
        b += f'<rect x="{mx}" y="{y + 8}" width="34" height="74" fill="#e0f7fa" stroke="{S.INK}" stroke-width="1.2"/>'
        b += f'<circle cx="{mx + 72}" cy="{y + 45}" r="24" fill="#fff" stroke="{S.INK}" stroke-width="1.5"/>' + _t(mx + 72, y + 51, "M", 16, "middle", True)
        b += f'<line x1="{mx + 34}" y1="{y + 45}" x2="{mx + 48}" y2="{y + 45}" stroke="{S.INK}" stroke-width="1.2"/>'
        b += _t(mx + 102, y + 30, f"M{c + 1} {j} {name}", 10, bold=True) + _t(mx + 102, y + 44, motor, 8.5)
        mc = N[f"W3{c}1"][6]
        b += _t(mx + 102, y + 58, f"cable C3{c}: 4-core shielded 18 AWG, cut {mc} m", 8.5, fill=COL["motor"])
        b += _t(mx + 102, y + 71, f"shield W3{c}5 to E1 at the enclosure end only", 8, fill=COL["pe"])
        b += _t(mx + 102, y + 84, "A+ blk, A- grn, B+ red, B- blu (CHECK pairs)", 8, fill="#555")
    # ---- limit switches left of the Mega
    XG = 330
    b += _w([(MX, 680), (XG, 680)], "limit", "W021 / TB4", 0, -70, -4) + _w([(XG, 470 + 22), (XG, 470 + 52 * 4 + 22)], "limit", None, width=1.6)
    for c, (j, name, motor, drv) in enumerate(JOINTS):
        p = f"D{WIRING[c]['limit']}"
        ys = 300 + 75 * c if False else 470 + 52 * c
        yp = lim_y[p]
        sx = 200
        lane = 420 - 14 * c
        b += _w([(MX, yp), (lane, yp), (lane, ys), (sx + 40, ys)], "limit", f"W4{c}1", 0, -40)
        b += _w([(XG, ys + 22), (sx + 40, ys + 22)], "limit", f"W4{c}2", 0, -40) + _dot(XG, ys + 22, "limit")
        b += (f'<g stroke="{S.INK}" stroke-width="1.3" fill="none"><circle cx="{sx + 40}" cy="{ys}" r="2.2"/><circle cx="{sx + 40}" cy="{ys + 22}" r="2.2"/>'
              f'<line x1="{sx + 36}" y1="{ys + 2}" x2="{sx + 30}" y2="{ys + 22}"/><line x1="{sx + 30}" y1="{ys + 22}" x2="{sx + 38}" y2="{ys + 22}"/></g>')
        b += f'<g stroke="{S.INK}" stroke-width="1.2"><line x1="{sx + 8}" y1="{ys}" x2="{sx + 8}" y2="{ys + 8}"/><line x1="{sx}" y1="{ys + 8}" x2="{sx + 16}" y2="{ys + 8}"/><line x1="{sx}" y1="{ys + 13}" x2="{sx + 16}" y2="{ys + 13}"/><line x1="{sx + 8}" y1="{ys + 13}" x2="{sx + 8}" y2="{ys + 22}"/><line x1="{sx + 8}" y1="{ys}" x2="{sx + 38}" y2="{ys}"/><line x1="{sx + 8}" y1="{ys + 22}" x2="{sx + 38}" y2="{ys + 22}"/></g>'
        b += _t(sx - 6, ys + 6, f"S{c + 2} {j} limit", 9, "end", True) + _t(sx - 6, ys + 18, f"NC, C{c + 1} 100 nF at switch", 7.5, "end", fill="#555")
    b += _t(40, 760, "Limit cables: 2-core twisted 22 AWG, cut lengths in ELE-002. Firmware: INPUT_PULLUP, LOW = not triggered.", 8.5, fill=COL["limit"])
    # ---- legend and notes
    leg = [("mains", "mains 18 AWG H05VV-F (qualified person)"), ("pe", "protective earth / shield"), ("24v", "+24 V 14 AWG (bus), 18 AWG (drivers)"),
           ("0v", "0 V / GND"), ("5v", "+5 V logic 22 AWG (common anode)"), ("sig", "STEP / DIR / ENABLE 22 AWG"), ("motor", "motor phases 18 AWG shielded"),
           ("limit", "limit switches 22 AWG twisted")]
    lx, ly = 40, 800
    b += _t(lx, ly - 8, "LEGEND", 10, bold=True)
    for i, (k, s) in enumerate(leg):
        x, y = lx + (i % 2) * 300, ly + (i // 2) * 16
        b += f'<line x1="{x}" y1="{y}" x2="{x + 26}" y2="{y}" stroke="{COL[k]}" stroke-width="2.4"/>' + _t(x + 32, y + 3.5, s, 8.5)
    notes = ["Every wire: ferrule at screw terminals, label sleeve with its Wxxx number at both ends.",
             "Driver DIP: NEMA23 2.84 A peak, NEMA17 1.46 A; 800 pulses/rev on all (MICROSTEP = 4).",
             "Common anode: +5 V to PUL+/DIR+/ENA+; Mega pins sink PUL-/DIR-/ENA-.",
             "ENABLE: D12 HIGH = drivers off (firmware). E-stop S1 cuts +24 V to every driver.",
             "One 0 V star point at TB2. Mega GND only to limit switches (TB4), not to TB2.",
             "Motor and limit cables leave through the ENC-06 glands (PG9 motor, PG7 limit).",
             "Never plug or unplug a motor with the drivers powered.",
             "Mains wiring (X0 to PSU1) by a qualified person; earth all aluminium panels to E1."]
    for i, n in enumerate(notes):
        b += _t(40, 880 + 14 * i, f"{i + 1}. {n}", 9)
    b += S.title_block(dict(title="WIRING SCHEMATIC", partno="ELE-001", material="see ELE-002 wire list", process="wiring",
                            qty="1", mass="-", scale="NTS", rev="B", assy="electronics enclosure, 5 axes"))
    return _svg(b)


def ele002():
    rows = netlist()
    b = ''
    b += _t(40, 46, "WIRE LIST (one arm). Cut lengths include a 300 mm service loop and 10 % drape for cables to the arm.", 12, bold=True)
    from .asmsheets import table
    cols = [("WIRE", 40), ("FROM", 82), ("TO", 82), ("SIGNAL", 132), ("AWG", 56), ("COLOUR", 66), ("CUT m", 38)]
    half = (len(rows) + 1) // 2
    for i, part in enumerate((rows[:half], rows[half:])):
        t, _ = table(30 + 512 * i, 70, cols, [(r[0], r[1], r[2], r[3], r[4], r[5], f"{r[6]:.2f}") for r in part], fs=7.5)
        b += t
    # devices
    dev = [("X0", "IEC C14 inlet, switch + fuse T3.15A", "ENC-04"), ("PSU1", "24 V 15 A (360 W) supply", "ENC-01"),
           ("F1", "20 A blade fuse + holder", "ENC-01"), ("S1", "E-stop mushroom, latching, 2 NC", "ENC-02 lid"),
           ("TB1", "+24 V bus, 6-way terminal", "ENC-01"), ("TB2", "0 V bus, 6-way terminal", "ENC-01"),
           ("TB3", "+5 V logic, 6-way terminal", "ENC-01"), ("TB4", "logic GND, 6-way terminal", "ENC-01"),
           ("A1", "Arduino Mega 2560 R3", "ENC-01"), ("U1..U5", "DM542 drivers (U5 TB6600 ok)", "ENC-01"),
           ("M1..M5", "motors, see ASM-001", "arm"), ("S2..S6", "limit switches NC", "arm"),
           ("C1..C5", "100 nF 50 V ceramic", "at switch"), ("E1", "M5 earth stud", "ENC-04"),
           ("C30..C34", "motor cables 4-core shielded", "glands PG9"), ("C40..C44", "limit cables 2-core", "glands PG7")]
    t, th = table(1060, 70, [("REF", 62), ("DEVICE", 300), ("WHERE", 158)], dev, "DEVICES", fs=8.5)
    b += t
    dip = [("U1..U4 NEMA23", "2.84 A peak", "SW1-3", "800 (SW5-8)", "half current on (SW4 off)"),
           ("U5 NEMA17", "1.46 A peak", "SW1-3", "800 (SW5-8)", "half current on (SW4 off)")]
    t2, th2 = table(1060, 70 + th + 34, [("DRIVER", 110), ("CURRENT", 80), ("DIP", 60), ("PULSES/REV", 90), ("IDLE", 180)], dip,
                    "DRIVER DIP SETTINGS (check the table printed on your driver)", fs=8.5)
    b += t2
    pin = [("1", "A+", "black"), ("2", "A-", "green"), ("3", "B+", "red"), ("4", "B-", "blue")]
    t3, _ = table(1060, 70 + th + th2 + 68, [("PIN", 40), ("PHASE", 60), ("USUAL COLOUR", 120)], pin,
                  "MOTOR CONNECTOR (4-pin, if fitted)", fs=8.5)
    b += t3
    b += S.notes_block(["Label both ends of every wire with its number.", "Ferrules on all stranded ends at screw terminals.",
                        "Measure phase pairs before connecting (shorted pair = stiff shaft).",
                        "Same list as CSV: fab/WIRELIST.csv (kit: 5-Wire-and-Firmware).",
                        "Schematic: ELE-001. Pins: firmware/arm_controller, arm/twin.py."], y=740, h=110)
    b += S.title_block(dict(title="WIRE LIST", partno="ELE-002", material="see list", process="wiring",
                            qty="1", mass="-", scale="NTS", rev="A", assy=f"{len(rows)} wires"))
    return _svg(b)


def _svg(body):
    return S.halo(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S.W} {S.H}" width="{S.W}" height="{S.H}" '
            f'font-family="Helvetica,Arial,sans-serif">{S.frame()}{body}</svg>')
