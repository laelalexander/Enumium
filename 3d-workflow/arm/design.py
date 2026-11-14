"""Static sizing for a 4-DOF (yaw, shoulder, elbow, wrist pitch) arm with a
tube-and-printed-joint structure.  Worst case: arm fully horizontal."""
from .actuators import DRIVES

G = 9.81
LB = 0.45359
SAFETY = 2.0            # rated torque must exceed required by this factor
TUBE_KG_PER_M = 0.49    # 1.5 in OD x 0.065 in wall 6061 aluminium tube
JOINT_HW_KG = 0.20      # printed fittings + hardware per link end
GRIPPER_KG = 0.45       # printed gripper + NEMA17 + lead screw
TOOL_LEN = 0.20         # wrist axis to fingertip, m
PAYLOAD_ARM = 0.12      # wrist axis to payload CoM, m
BASE_OFFSET = 0.05      # base axis to shoulder axis, m
MAX_EXTENSION = 1.219   # 4 ft
FOOTPRINT_NOTE = "extension = base axis to fingertip, arm horizontal"

def links_for(extension):
    l = (extension - TOOL_LEN - BASE_OFFSET) / 2
    return l, l

def torques(extension, payload_kg, drives):
    """drives: dict joint->Drive.  Returns required torque (N·m) per joint."""
    l1, l2 = links_for(extension)
    m1, m2 = TUBE_KG_PER_M * l1 + JOINT_HW_KG, TUBE_KG_PER_M * l2 + JOINT_HW_KG
    mw, me = drives["wrist"].mass_kg, drives["elbow"].mass_kg
    wrist = G * (payload_kg * PAYLOAD_ARM + GRIPPER_KG * 0.07)
    elbow = G * (m2 * l2 / 2 + mw * l2 + GRIPPER_KG * (l2 + 0.07) + payload_kg * (l2 + PAYLOAD_ARM))
    shoulder = G * (m1 * l1 / 2 + me * l1 + m2 * (l1 + l2 / 2) + mw * (l1 + l2)
                    + GRIPPER_KG * (l1 + l2 + 0.07) + payload_kg * (l1 + l2 + PAYLOAD_ARM))
    return {"shoulder": shoulder, "elbow": elbow, "wrist": wrist}

def select(extension, payload_kg):
    """Smallest-mass drive per joint meeting SAFETY; None if infeasible."""
    pick = {j: DRIVES[0] for j in ("shoulder", "elbow", "wrist")}
    for _ in range(8):
        req = torques(extension, payload_kg, pick)
        new = {}
        for j, t in req.items():
            ok = [d for d in DRIVES if d.rated_nm >= SAFETY * t]
            if not ok:
                return None, req
            new[j] = min(ok, key=lambda d: d.mass_kg)
        if new == pick:
            return pick, req
        pick = new
    return pick, req

def max_extension(payload_kg, lo=0.5, hi=MAX_EXTENSION, step=0.005):
    e = hi
    while e >= lo:
        pick, req = select(e, payload_kg)
        if pick:
            return round(e, 3), pick, req
        e -= step
    return None, None, None

def design(payload_lb=5.0, extension=None):
    payload = payload_lb * LB
    if extension is None:
        extension, pick, req = max_extension(payload)
        if extension is None:
            raise ValueError("No catalog drive meets the payload at any extension >= 0.5 m")
    else:
        pick, req = select(extension, payload)
        if pick is None:
            raise ValueError(f"Infeasible at {extension} m with {payload_lb} lb: required {req}")
    l1, l2 = links_for(extension)
    return {"payload_lb": payload_lb, "extension_m": extension, "extension_in": round(extension / 0.0254, 1),
            "l1_mm": round(l1 * 1000), "l2_mm": round(l2 * 1000),
            "joints": {j: {"drive": pick[j].key, "required_nm": round(req[j], 2),
                           "rated_nm": round(pick[j].rated_nm, 1),
                           "margin": round(pick[j].rated_nm / req[j], 2)} for j in req}}
