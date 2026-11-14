"""Programmable control layer.  Write motion scripts against `Arm`; swap the driver
to move from simulation to hardware.
    arm = Arm.from_design(SimDriver(), "out/arm/design.json")
    arm.home(); arm.move_to(600, 0, 200); arm.grip(30)"""
import json, time
from .kinematics import ik

MICROSTEP = 4            # DM542 set to 800 pulses/rev
STEPS_PER_MM_GRIP = 200 * MICROSTEP / 8.0   # T8 lead screw, 8 mm/rev

class SimDriver:
    def move(self, ch, steps): print(f"  ch{ch} -> {steps:+d} steps")
    def home(self, ch, direction): print(f"  ch{ch} home dir {direction}")
    def wait(self): pass

class SerialDriver:
    """Talks to firmware/arm_controller (Arduino Mega + AccelStepper). 115200 8N1."""
    def __init__(self, port, baud=115200):
        import serial
        self.s = serial.Serial(port, baud, timeout=60); time.sleep(2)
    def _cmd(self, line):
        self.s.write((line + "\n").encode())
        r = self.s.readline().decode().strip()
        if not r.startswith("OK"): raise RuntimeError(f"{line!r} -> {r!r}")
    def set_speed(self, ch, steps_per_s, accel): self._cmd(f"V {ch} {int(steps_per_s)} {int(accel)}")
    def move(self, ch, steps): self._cmd(f"G {ch} {int(steps)}")
    def home(self, ch, direction): self._cmd(f"H {ch} {direction}")
    def wait(self): self._cmd("W")
    def stop(self): self._cmd("X")

class Arm:
    CH = {"yaw": 0, "shoulder": 1, "elbow": 2, "wrist": 3}
    GRIP = 4
    LIMITS = {"yaw": (-150, 150), "shoulder": (-10, 100), "elbow": (-135, 135), "wrist": (-100, 100)}  # CALIBRATE
    HOME_DIR = {"yaw": -1, "shoulder": -1, "elbow": -1, "wrist": -1}
    def __init__(self, driver, l1, l2, total_ratio, max_dps=None):
        self.d, self.l1, self.l2, self.ratio = driver, l1, l2, total_ratio
        self.max_dps = max_dps or {"yaw": 30, "shoulder": 10, "elbow": 15, "wrist": 30}
        for j, ch in self.CH.items():
            sps = self.max_dps[j] * self.steps_per_deg(j)
            if hasattr(driver, "set_speed"): driver.set_speed(ch, sps, sps)   # 1 s to full speed
    @classmethod
    def from_design(cls, driver, path):
        d = json.load(open(path))
        ratio = {"yaw": 20.0}
        from .actuators import BY_KEY
        for j, v in d["joints"].items():
            ratio[j] = BY_KEY[v["drive"]].ratio * (1 if j != "wrist" else 1)
        return cls(driver, d["l1_mm"], d["l2_mm"], ratio)
    def steps_per_deg(self, joint): return 200 * MICROSTEP * self.ratio[joint] / 360.0
    def home(self):
        for j, ch in self.CH.items(): self.d.home(ch, self.HOME_DIR[j])
    def move_joints(self, yaw, shoulder, elbow, wrist):
        for (j, ch), a in zip(self.CH.items(), (yaw, shoulder, elbow, wrist)):
            lo, hi = self.LIMITS[j]
            if not lo <= a <= hi: raise ValueError(f"{j} {a} deg outside [{lo},{hi}]")
        for (j, ch), a in zip(self.CH.items(), (yaw, shoulder, elbow, wrist)):
            self.d.move(ch, round(a * self.steps_per_deg(j)))
        self.d.wait()
    def move_to(self, x, y, z, pitch=0.0):
        a = ik(x, y, z, self.l1, self.l2, pitch)
        self.move_joints(*a); return a
    def grip(self, width_mm):
        """0 = closed on part, up to ~70 mm open (calibrate)."""
        if not 0 <= width_mm <= 70: raise ValueError("grip width 0-70 mm")
        self.d.move(self.GRIP, round(width_mm * STEPS_PER_MM_GRIP)); self.d.wait()
