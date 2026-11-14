"""Joint drive catalog: NEMA stepper + planetary gearbox, the kind sold on Amazon
(StepperOnline/OMC and generic).  Numbers are from vendor listings and are
APPROXIMATE: confirm on the product page before ordering.  rated_nm is the output
torque we allow = min(motor_hold*ratio*eff, gearbox max permissible)."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Drive:
    key: str
    search_terms: str     # what to type into Amazon
    motor_hold_nm: float
    ratio: float
    eff: float
    gear_max_nm: float    # gearbox max permissible output torque (intermittent)
    mass_kg: float        # motor + gearbox
    backlash_arcmin: float
    amps: float

    @property
    def rated_nm(self):
        return min(self.motor_hold_nm * self.ratio * self.eff, self.gear_max_nm)

    @property
    def deg_per_fullstep(self):
        return 1.8 / self.ratio

DRIVES = [
    Drive("n17_14", "NEMA 17 stepper motor 14:1 planetary gearbox", 0.45, 14, 0.9, 10.0, 0.50, 40, 1.7),
    Drive("n23_20", "NEMA 23 stepper motor 20:1 planetary gearbox 2.8A", 1.89, 20, 0.9, 25.0, 1.60, 20, 2.8),
    Drive("n23_20_b3", "NEMA 23 20:1 planetary gearbox + 3:1 HTD 5M belt/pulley stage", 1.89, 60, 0.85, 75.0, 2.10, 25, 2.8),
    Drive("n23_20_b5", "NEMA 23 20:1 planetary gearbox + 5:1 HTD 5M belt/pulley stage", 1.89, 100, 0.80, 125.0, 2.20, 25, 2.8),
    Drive("n23_50", "NEMA 23 stepper motor 50:1 planetary gearbox 2.8A", 1.89, 50, 0.75, 20.0, 1.70, 16, 2.8),
]
BY_KEY = {d.key: d for d in DRIVES}
