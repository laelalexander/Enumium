"""Actuator catalog.  Values are nominal/approximate from vendor listings:
VERIFY AGAINST THE DATASHEET before ordering parts or cutting material.
body = (length along long axis, width, height) in mm, torque = rated stall (N·m)."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Actuator:
    name: str
    body: tuple          # (l, w, h) mm
    torque_nm: float     # stall torque
    mass_kg: float
    shaft_offset: float  # shaft centre distance from one end of long axis, mm
    interface: str       # control interface
    voltage: str

CATALOG = [
    Actuator("SG90 micro servo",       (22.2, 11.8, 31.0), 0.18, 0.009, 5.5,  "PWM", "4.8-6V"),
    Actuator("MG996R servo",           (40.7, 19.7, 42.9), 0.92, 0.055, 10.0, "PWM", "4.8-7.2V"),
    Actuator("DS3218 servo",           (40.0, 20.0, 40.5), 2.0,  0.060, 10.0, "PWM", "5-6.8V"),
    Actuator("Dynamixel XL430-W250",   (46.5, 28.5, 34.0), 1.4,  0.057, 14.0, "TTL serial", "10-12V"),
]
BY_NAME = {a.name: a for a in CATALOG}
