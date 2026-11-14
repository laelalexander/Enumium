"""Sizing: choose actuators from joint torque, then emit CadQuery source for
each structural part so it can go through pipeline.run (validate + export)."""
import json
from .actuators import CATALOG, Actuator

G = 9.81
SAFETY = 2.0          # required torque margin
WALL, THICK = 3.0, 4.0
CLEAR = 0.3           # pocket clearance per side
LINK_KG_PER_MM = 0.00022   # ~PLA/PETG beam of this cross-section, rough

def select(reach_mm, payload_kg, links=(0.5, 0.5)):
    """Return dict of joint -> (Actuator, required_nm). links = fractions of reach."""
    L = [reach_mm * f / 1000 for f in links]            # metres
    chosen = {j: CATALOG[0] for j in ("shoulder", "elbow", "wrist")}
    for _ in range(6):                                  # actuator mass feeds back into torque
        m = {j: a.mass_kg for j, a in chosen.items()}
        wrist_t = G * (payload_kg * 0.06 + m["wrist"] * 0.02)          # gripper ~60 mm out
        lw = 0.06
        elbow_t = G * (L[1] * LINK_KG_PER_MM * 1000 * L[1] / 2 + m["wrist"] * L[1]
                       + (payload_kg + 0.03) * (L[1] + lw))
        shoulder_t = G * (L[0] * LINK_KG_PER_MM * 1000 * L[0] / 2 + m["elbow"] * L[0]
                          + L[1] * LINK_KG_PER_MM * 1000 * (L[0] + L[1] / 2)
                          + m["wrist"] * (L[0] + L[1]) + (payload_kg + 0.03) * (L[0] + L[1] + lw))
        req = {"shoulder": shoulder_t, "elbow": elbow_t, "wrist": wrist_t}
        new = {}
        for j, t in req.items():
            ok = [a for a in CATALOG if a.torque_nm >= t * SAFETY]
            if not ok:
                raise ValueError(f"No catalog actuator gives {SAFETY}x margin at {j} "
                                 f"({t:.2f} N·m needed). Reduce reach/payload or add a stronger actuator.")
            new[j] = min(ok, key=lambda a: (a.torque_nm, a.mass_kg))
        if new == chosen:
            break
        chosen = new
    return {j: (chosen[j], round(req[j], 3)) for j in chosen}

def link_code(length_mm: float, act: Actuator) -> str:
    """Beam between joint axes: actuator pocket at the start, horn hole at the end."""
    l, w, h = act.body
    return f"""length, thickness, wall = {length_mm}, {THICK}, {WALL}
act_l, act_w = {l + 2 * CLEAR}, {w + 2 * CLEAR}
width = act_w + 2 * wall
horn_hole_d, screw_d = 6.0, 3.2
total = length + act_l
beam = cq.Workplane("XY").box(total, width, thickness, centered=(False, True, False)).edges("|Z").fillet(width / 4)
pocket = cq.Workplane("XY").box(act_l, act_w, thickness, centered=(False, True, False))
result = (beam.cut(pocket)
          .faces(">Z").workplane().center(total - 8, 0).hole(horn_hole_d)
          .faces(">Z").workplane().pushPoints([(total - 8, 8), (total - 8, -8)]).hole(screw_d))
"""

def base_code(act: Actuator) -> str:
    l, w, h = act.body
    return f"""size, base_t, act_l, act_w, act_h = 100.0, 8.0, {l + 2*CLEAR}, {w + 2*CLEAR}, {h}
plate = cq.Workplane("XY").box(size, size, base_t, centered=(True, True, False)).edges("|Z").fillet(8)
plate = plate.faces(">Z").workplane().rect(act_l, act_w).cutBlind(-base_t + 2)  # yaw actuator seat
result = plate.faces("<Z").workplane().rarray(80, 80, 2, 2).hole(4.5)           # clamp-down holes
"""

def design(reach_mm=300.0, payload_kg=0.1):
    sel = select(reach_mm, payload_kg)
    (sh, _), (el, _), (wr, _) = sel["shoulder"], sel["elbow"], sel["wrist"]
    l1, l2 = reach_mm * 0.5, reach_mm * 0.5
    parts = [
        {"name": "base", "code": base_code(el), "actuator": el.name, "qty": 1},
        {"name": "upper_arm", "code": link_code(l1, el), "actuator": sh.name, "qty": 1},
        {"name": "forearm", "code": link_code(l2, wr), "actuator": el.name, "qty": 1},
    ]
    for p in parts:
        p["spec"] = {"name": p["name"], "units": "mm", "min_feature_mm": 2.0, "process": "fdm"}
    bom = [{"item": a.name, "qty": q, "interface": a.interface, "voltage": a.voltage}
           for a, q in _count([el, sh, el, wr])]
    return {"reach_mm": reach_mm, "payload_kg": payload_kg,
            "joints": {j: {"actuator": a.name, "required_nm": r, "rated_nm": a.torque_nm}
                       for j, (a, r) in sel.items()},
            "parts": parts, "bom": bom}

def _count(acts):
    out = {}
    for a in acts: out[a] = out.get(a, 0) + 1
    return list(out.items())
