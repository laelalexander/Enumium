"""Fastener schedule: one numbered line per screw type, with standard, length, washer, nut, torque,
and where it goes. The drawings call these numbers out in their hole tables, procurement buys them,
and the assembly guide refers to them. Lengths are worked out from the stack each screw clamps.

Torques: into or through printed PETG with washers, keep low so the plastic does not creep;
metal-to-metal values are for A2-70 stainless. Use medium (blue) threadlocker on every metal thread
that does not have a nyloc nut."""

# id: (description, standard, qty per arm, torque N·m, stack / why, where)
FASTENERS = {
    "F01": ("M5 x 90 socket head cap screw, A2-70 stainless", "ISO 4762", 15, 2.5,
            "12 cheek + 56 block + 12 cheek + 2 x 1.0 washer + 5.0 nyloc + 2 thread = 89",
            "cheek-block-cheek stack, 4 per pitch joint (12); tube cross pin through each tube block (3)"),
    "F01W": ("M5 flat washer, A2", "ISO 7089", 30, None, "", "2 per F01"),
    "F01N": ("M5 nyloc nut, A2", "ISO 10511", 15, None, "", "1 per F01"),
    "F02": ("M5 x 60 socket head cap screw, A2-70", "ISO 4762", 3, 2.5,
            "50 socket OD + 2 x 1.0 washer + 5.0 nyloc + 2 thread = 59", "cross pin through each tube_socket and its tube"),
    "F02W": ("M5 flat washer, A2", "ISO 7089", 6, None, "", "2 per F02"),
    "F02N": ("M5 nyloc nut, A2", "ISO 10511", 3, None, "", "1 per F02"),
    "F03": ("M5 x 16 socket head cap screw, A2-70", "ISO 4762", 16, 2.5,
            "10 printed flange + 1.0 washer + 5 thread engagement in hub flange (MEASURE hub flange: need >= 5)",
            "tube_socket to clamp-hub flange, 4 per pitch joint (12); base_top_plate to yaw clamp hub (4)"),
    "F03W": ("M5 flat washer, A2", "ISO 7089", 16, None, "", "1 per F03"),
    "F04": ("M5 x 20 socket head cap screw, A2-70", "ISO 4762", 12, 2.5,
            "12 cheek + 1.0 washer + 7 thread engagement in gearbox flange (check gearbox thread depth >= 8)",
            "gearmotor flange to motor cheek, through the tension slots, 4 per pitch joint"),
    "F04W": ("M5 flat washer, A2", "ISO 7089", 12, None, "", "1 per F04"),
    "F05": ("M5 x 16 socket head cap screw, A2-70", "ISO 4762", 4, 4.0,
            "7 board left under the flange pocket + 1.5 fender washer + 7.5 thread in gearbox flange", "yaw gearmotor to BASE-01"),
    "F05W": ("M5 fender washer 15 mm OD, A2", "ISO 7093", 4, None, "", "spreads the load on the plywood"),
    "F06": ("M6 x 25 socket head cap screw, A2-70", "ISO 4762", 8, 3.5,
            "10 printed plate + 6 YAW-01 + 2 x 1.6 washer + 6.0 nyloc + 2 thread = 24.2", "base_top_plate to YAW-01 adapter disc"),
    "F06W": ("M6 flat washer, A2", "ISO 7089", 16, None, "", "2 per F06"),
    "F06N": ("M6 nyloc nut, A2", "ISO 10511", 8, None, "", "1 per F06"),
    "F07": ("M5 x 30 button head screw, A2-70", "ISO 7380", 4, 3.0,
            "turntable fixed ring 3 + GSK-01 1.5 + 19 board, into M5 tee nut from below (MEASURE ring holes)", "turntable fixed ring to BASE-01"),
    "F07T": ("M5 four-prong tee nut, 8 mm barrel x 9 mm", "DIN 1624", 4, None, "", "pressed into BASE-01 from below"),
    "F08": ("M5 x 20 socket head cap screw, A2-70", "ISO 4762", 4, 4.0,
            "6 YAW-01 + 3 turntable ring + 1.0 washer + 5.0 nyloc + 2 thread = 17 (MEASURE ring thickness)",
            "turntable rotating ring to YAW-01"),
    "F08W": ("M5 flat washer, A2", "ISO 7089", 4, None, "", "1 per F08"),
    "F08N": ("M5 nyloc nut, A2", "ISO 10511", 4, None, "", "1 per F08"),
    "F09": ("M4 x 14 socket head cap screw, A2-70", "ISO 4762", 4, 1.2,
            "8 adapter plate + 0.8 washer + 5 into the insert", "gripper_adapter to gripper_body"),
    "F09W": ("M4 flat washer, A2", "ISO 7089", 4, None, "", "1 per F09"),
    "F10": ("M4 brass heat-set insert, OD 5.7-6.0 x 8.1 long", "knurled, for plastics", 4, None,
            "hole Ø5.60 x 11 deep in gripper_body; set with 230-250 °C iron tip", "gripper_body, for F09"),
    "F11": ("M3 x 10 socket head cap screw, A2-70", "ISO 4762", 4, 1.0,
            "5 printed wall + 5 thread engagement in NEMA 17 face", "NEMA 17 to gripper_body"),
    "F12": ("M3 x 40 socket head cap screw, A2-70", "ISO 4762", 4, 0.6,
            "30 jaw + 3.5 T8 nut flange + 0.5 washer + 2.4 nyloc + 2 thread = 38.4", "T8 lead-screw nut flange through gripper_jaw"),
    "F12N": ("M3 nyloc nut, A2", "ISO 10511", 4, None, "", "1 per F12"),
    "F13": ("M3 x 12 pan head screw + M3 nut + 2 washers, A2", "ISO 7045 / ISO 4032", 10, 0.5,
            "switch body 6.4 + bracket 3 + nut", "limit switches, 2 per switch (5 switches)"),
    "F14": ("No.10 x 3 in flat head wood screw (5 x 75 mm)", "ASME B18.6.1", 8, None,
            "19 board + 56 into the leg; drill 3.0 pilot in the leg, countersink the board", "LEG-01 to BASE-01, 2 per leg"),
    "F15": ("M3 x 8 button head screw + M3 nyloc nut, A2", "ISO 7380 / ISO 10511", 0, 0.6,
            "3 panel + 1.5 angle leg + nut", "enclosure panels to the 10 x 10 corner angles (count from the ENC drawings)"),
    "F16": ("M3 x 10 brass standoff M-F + M3 x 6 screw + M3 nut", "-", 4, 0.4, "", "Arduino Mega to ENC-01 (drill from the board)"),
    "F17": ("M4 x 10 pan head screw + M4 nyloc + washer, A2", "ISO 7045", 24, 1.2, "",
            "DM542 drivers (4 each, 20) and PSU (4) to ENC-01: drill from the parts (patterns vary by maker)"),
    "F18": ("Rubber bumper foot 20 x 10 mm with M4 x 12 screw", "-", 4, None, "", "under ENC-01"),
}


def label(fid):
    d, std, q, tq, stack, where = FASTENERS[fid]
    extra = [k for k in FASTENERS if k.startswith(fid) and k != fid]
    with_ = " + ".join(FASTENERS[k][0].split(",")[0].replace(" flat", "") for k in extra)
    t = f"{fid} {d.split(',')[0]} {std}" + (f" + {with_}" if with_ else "")
    return t + (f"; {tq:g} N·m" if tq else "")


def _near(a, b, tol=0.06):
    return abs(a - b) <= tol


# per printed part: list of (kind, diameter, axis or None, text)
RULES = {
    "cheek": [("hole", 5.5, "Y", label("F01")), ("slot", 5.5, None, label("F04") + "; slots give ±4 [.17] belt tension"),
              ("hole", 20.0, None, "6001-2RS (12x28x8) bearing, light press into the CBORE; 12 mm shaft passes through"),
              ("hole", 38.6, None, "Gearbox pilot Ø38.10 [1.500] clearance (MEASURE pilot)")],
    "tube_block": [("hole", 38.4, None, "1.5 in OD tube, slip fit 0.30 [.012] clearance"),
                   ("hole", 5.5, "Z", label("F01") + "; cross pin, transfer-drill tube Ø5.5"),
                   ("hole", 5.5, "Y", label("F01") + "; through both cheeks")],
    "tube_socket": [("hole", 14.0, None, "Clamp-hub spigot clearance (MEASURE hub)"), ("hole", 5.5, "Y", label("F03")),
                    ("hole", 38.4, None, "1.5 in OD tube socket, slip fit 0.30 [.012]"),
                    ("hole", 5.5, "Z", label("F02") + "; cross pin, transfer-drill tube Ø5.5")],
    "base_top_plate": [("hole", 14.0, None, "Yaw clamp-hub spigot clearance"), ("hole", 5.5, None, label("F03") + " (yaw hub)"),
                       ("hole", 6.5, None, label("F06")), ("hole", 38.4, None, "Riser tube socket: bond with structural epoxy")],
    "gripper_body": [("hole", 22.5, None, "NEMA 17 pilot boss clearance"), ("hole", 3.4, None, label("F11")),
                     ("hole", 10.0, None, "T8 lead screw clearance"), ("hole", 8.1, None, "8 mm rod: press fit + retaining compound"),
                     ("hole", 5.6, None, label("F10"))],
    "gripper_adapter": [("hole", 38.4, None, "Wrist stub socket: bond with epoxy or add an M5 cross pin"), ("hole", 4.5, None, label("F09"))],
    "gripper_jaw": [("hole", 15.4, None, "LM8UU (8x15x24) linear bearing, press fit"), ("hole", 11.0, None, "T8 lead screw / nut clearance"),
                    ("hole", 3.4, None, label("F12"))],
}

GENERIC = [(3.4, "M3 clearance (ISO 273 medium)"), (4.5, "M4 clearance"), (5.5, "M5 clearance (ISO 273 medium)"),
           (6.5, "M6 clearance"), (9.0, "M8 clearance"), (12.0, "12 mm shaft")]


def for_part(name):
    key = next((k for k in RULES if k in name), None)

    def spec(f):
        for kind, dia, ax, txt in RULES.get(key, []):
            if f["kind"] == kind and _near(f["dia"], dia, 0.25) and (ax is None or ax == f["axis"]):
                return txt
        for dia, txt in GENERIC:
            if _near(f["dia"], dia, 0.15):
                return txt
        return "Fit to the mating part (see assembly)"
    return spec
