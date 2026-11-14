"""Programmable control layer.  Write motion scripts against `Arm`; swap the
driver to move from simulation to hardware."""
import time
from .kinematics import ik

class SimDriver:
    def set_angle(self, channel, deg): print(f"  ch{channel} -> {deg:7.2f}°")

class PCA9685Driver:
    """Hobby PWM servos via Adafruit PCA9685 (pip install adafruit-circuitpython-servokit).
    Angles are 0-180: joint zero is mapped to `center` (default 90)."""
    def __init__(self, channels=16, center=90):
        from adafruit_servokit import ServoKit
        self.kit, self.center = ServoKit(channels=channels), center
    def set_angle(self, channel, deg):
        self.kit.servo[channel].angle = max(0, min(180, self.center + deg))

class Arm:
    CH = {"yaw": 0, "shoulder": 1, "elbow": 2, "wrist": 3}
    LIMITS = {"yaw": (-90, 90), "shoulder": (-80, 80), "elbow": (-120, 120), "wrist": (-90, 90)}
    def __init__(self, driver, l1, l2):
        self.d, self.l1, self.l2 = driver, l1, l2
    def move_to(self, x, y, z, pitch=0.0, settle=0.0):
        angles = ik(x, y, z, self.l1, self.l2, pitch)
        for name, a in zip(self.CH, angles):
            lo, hi = self.LIMITS[name]
            if not lo <= a <= hi:
                raise ValueError(f"{name} angle {a}° outside limit [{lo},{hi}]")
        for name, a in zip(self.CH, angles):
            self.d.set_angle(self.CH[name], a)
        time.sleep(settle)
        return angles
