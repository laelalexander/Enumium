"""Yaw + planar 2-link (shoulder, elbow) + wrist pitch kinematics."""
import math

def ik(x, y, z, l1, l2, tool_pitch_deg=0.0, elbow_up=True):
    """Target (x,y,z) mm of the wrist joint -> joint angles in degrees.
    z measured from shoulder axis.  Raises ValueError if unreachable."""
    yaw = math.atan2(y, x)
    r = math.hypot(x, y)
    d2 = r * r + z * z
    c = (d2 - l1 * l1 - l2 * l2) / (2 * l1 * l2)
    if abs(c) > 1:
        raise ValueError(f"Target unreachable (|cos|={abs(c):.2f}>1)")
    elbow = math.acos(c) * (1 if elbow_up else -1)
    shoulder = math.atan2(z, r) - math.atan2(l2 * math.sin(elbow), l1 + l2 * math.cos(elbow))
    wrist = math.radians(tool_pitch_deg) - shoulder - elbow
    return tuple(round(math.degrees(a), 2) for a in (yaw, shoulder, elbow, wrist))

def fk(yaw, shoulder, elbow, l1, l2):
    yaw, s, e = map(math.radians, (yaw, shoulder, elbow))
    r = l1 * math.cos(s) + l2 * math.cos(s + e)
    z = l1 * math.sin(s) + l2 * math.sin(s + e)
    return r * math.cos(yaw), r * math.sin(yaw), z
