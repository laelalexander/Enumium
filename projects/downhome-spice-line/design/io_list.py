"""I/O list, motor list and network list for the Down Home Creole plant controls.

One source for ELE-001 (power one-line + control network), ELE-002 (I/O list and wire/cable schedule),
the PLC tag database (software/plc/tags.csv) and the I/O module count on the equipment list.

Wire numbering: <PLC>-<slot>-<channel>, e.g. 601-02-07 is PLC-601 slot 2 channel 7. Every field device gets a
cable number W-<area><nn> (W-301, W-302 ... blending; W-401 ... line A; W-501 ... station B).
Power feeders are F-<nn>. Motor full-load amps are NEC Table 430.250 values at 460 V.
Running this file writes io.json.
"""
import json, math, pathlib

HERE = pathlib.Path(__file__).parent

# tag, description, type, PLC, device (equipment tag)
IO = []


def io(tag, desc, typ, plc, dev, sig="24 V DC"):
    IO.append(dict(tag=tag, desc=desc, type=typ, plc=plc, device=dev, signal=sig))


# ------------------------------------------------------------ PLC-601 blending (panel CP-300)
for dev, name in (("BD-301", "bag dump screw"), ("BB-302", "salt discharger screw"), ("SC-304", "sifter motor"), ("FC-307", "bag filler screw"), ("DC-310", "dust collector fan")):
    io(f"{dev.replace('-', '')}_RUN", f"{name} running (aux contact)", "DI", "601", dev)
    io(f"{dev.replace('-', '')}_START", f"{name} start command", "DO", "601", dev)
io("BD301_LIDCLOSED", "bag dump grate lid closed", "DI", "601", "BD-301")
io("BD301_DCFAN_RUN", "bag dump integral collector fan running", "DI", "601", "BD-301")
io("BB302_SPOUT_CLOSED", "salt bag spout access door closed", "DI", "601", "BB-302")
io("BB302_HOPPER_LOW", "salt outlet hopper low level", "DI", "601", "BB-302")
io("RB303_RUN", "ribbon blender motor running", "DI", "601", "RB-303")
io("RB303_START", "ribbon blender motor start", "DO", "601", "RB-303")
io("RB303_COVER_CLOSED", "blender cover interlock closed (status; safety via SR-607)", "DI", "601", "RB-303")
io("RB303_VALVE_OPEN", "discharge valve open limit switch", "DI", "601", "RB-303")
io("RB303_VALVE_CLOSED", "discharge valve closed limit switch", "DI", "601", "RB-303")
io("RB303_VALVE_OPEN_SOL", "discharge valve open solenoid", "DO", "601", "RB-303")
io("RB303_VALVE_CLOSE_SOL", "discharge valve close solenoid", "DO", "601", "RB-303")
io("RB303_WEIGHT", "blender load cells 4-20 mA (lb)", "AI", "601", "RB-303", "4-20 mA")
io("RB303_AMPS", "blender motor current 4-20 mA", "AI", "601", "RB-303", "4-20 mA")
io("SC304_OVERS_FULL", "sifter oversize bin full", "DI", "601", "SC-304")
io("MD305_DETECT", "metal detected (reject cycle)", "DI", "601", "MD-305")
io("MD305_FAULT", "metal detector fault / not ready", "DI", "601", "MD-305")
io("MD305_REJ_VERIFY", "reject valve reached reject position", "DI", "601", "MD-305")
io("MD305_REJBIN_FULL", "locked reject container full", "DI", "601", "MD-305")
io("FC307_HOPPER_HIGH", "screw inlet hopper high level", "DI", "601", "FC-307")
io("FC307_HOPPER_LOW", "screw inlet hopper low level", "DI", "601", "FC-307")
io("BF306_BAG_PRESENT", "bulk bag spout clamped / bag present", "DI", "601", "BF-306")
io("BF306_FILL_DONE", "bag at target weight (from filler controller)", "DI", "601", "BF-306")
io("BF306_FILL_START", "start bag fill", "DO", "601", "BF-306")
io("BF306_SEAL_INFLATE", "inflatable spout seal", "DO", "601", "BF-306")
io("BF306_DENSIFY", "vibratory densification deck", "DO", "601", "BF-306")
io("DC310_DP", "filter differential pressure 4-20 mA (in w.c.)", "AI", "601", "DC-310", "4-20 mA")
io("DC310_VENT_BURST", "explosion vent burst indicator", "DI", "601", "DC-310")
io("DC310_ISO_CLOSED", "inlet isolation flap valve closed", "DI", "601", "DC-310")
io("AC311_PRESS", "plant air header pressure 4-20 mA (psi)", "AI", "601", "AC-311", "4-20 mA")
io("AC311_LOWPRESS", "plant air low pressure switch", "DI", "601", "AC-311")
io("SR601_OK", "blending safety relay outputs on (all e-stops reset)", "DI", "601", "SR-607")
io("PB601_RESET", "safety reset push button (blue)", "DI", "601", "SR-607")
for c in ("RED", "AMBER", "GREEN", "HORN"):
    io(f"SL601_{c}", f"blending stack light {c.lower()}", "DO", "601", "CP-300")

# ------------------------------------------------------------ PLC-602 line A + station B (panel CP-400)
for dev, name in (("BU-401", "line A bag discharger screw"), ("UN-402", "unscrambler"), ("BU-502", "station B bag discharger screw")):
    io(f"{dev.replace('-', '')}_RUN", f"{name} running", "DI", "602", dev)
    io(f"{dev.replace('-', '')}_START", f"{name} start", "DO", "602", dev)
io("FL403_HOPPER_HIGH", "filler hopper high level", "DI", "602", "FL-403")
io("FL403_HOPPER_LOW", "filler hopper low level", "DI", "602", "FL-403")
io("NW501_HOPPER_HIGH", "station B hopper high level", "DI", "602", "NW-501")
io("NW501_HOPPER_LOW", "station B hopper low level", "DI", "602", "NW-501")
io("CV417_RUN_CMD", "line A conveyor drives run", "DO", "602", "CV-417")
io("CV417_FAULT", "conveyor drive fault (any of 4)", "DI", "602", "CV-417")
for m in ("FL-403", "CP-404", "IS-405", "LB-406", "CW-409", "CE-411", "CK-412", "CS-413", "PA-414", "PL-415", "NW-501"):
    t = m.replace("-", "")
    io(f"{t}_READY", f"{m} ready / running (OEM machine handshake)", "DI", "602", m)
    io(f"{t}_FAULT", f"{m} fault", "DI", "602", m)
    io(f"{t}_PERMIT", f"line permissive to {m}", "DO", "602", m)
PE = [("PE401", "container present at filler infeed"), ("PE402", "backup before capper"), ("PE403", "backup before labeler"),
      ("PE404", "label sensor confirm after labeler"), ("PE405", "vision trigger"), ("PE406", "reject confirm after vision reject"),
      ("PE407", "checkweigher infeed spacing"), ("PE408", "accumulation table full"), ("PE409", "accumulation table low"),
      ("PE410", "case infeed to sealer"), ("PE501", "pouch at sealer infeed"), ("PE502", "pouch out of sealer"),
      ("PE503", "tub at fill station"), ("PE504", "carton at fill station")]
for t, d in PE:
    io(f"{t}_BLOCKED", d, "DI", "602", "CV-417" if t.startswith("PE4") else "NW-501")
io("VS408_FAIL", "vision inspection fail", "DI", "602", "VS-408")
io("RJ408_FIRE", "reject pusher after vision", "DO", "602", "VS-408")
io("CW409_BIN_FULL", "checkweigher locking reject bin full", "DI", "602", "CW-409")
io("CW409_BIN_DOOR", "reject bin door closed and locked", "DI", "602", "CW-409")
io("TT407_FAULT", "TTO coder fault / ribbon low", "DI", "602", "TT-407")
io("TJ505_FAULT", "TIJ coder fault / cartridge low", "DI", "602", "TJ-505")
io("SR602_OK", "line safety relay outputs on", "DI", "602", "SR-607")
io("PB602_RESET", "safety reset push button (blue)", "DI", "602", "SR-607")
for c in ("RED", "AMBER", "GREEN", "HORN"):
    io(f"SL602_{c}", f"line A stack light {c.lower()}", "DO", "602", "CP-400")

# ------------------------------------------------------------ motors and feeders (NEC 430.250 FLA at 460 V)
FLA = {0.5: 1.1, 0.75: 1.6, 1: 2.1, 2: 3.4, 3: 4.8, 5: 7.6, 7.5: 11, 10: 14, 15: 21, 20: 27}
MOTORS = [  # tag, load, hp, starter, panel
    ("M-301", "BD-301 bag dump screw", 3, "starter", "CP-300"), ("M-302", "BD-301 integral collector fan", 1, "starter", "CP-300"),
    ("M-303", "BB-302 salt discharger screw", 3, "starter", "CP-300"), ("M-304", "RB-303 ribbon blender", 15, "VFD", "CP-300"),
    ("M-305", "SC-304 sifter", 2, "starter", "CP-300"), ("M-306", "FC-307 flexible screw", 3, "starter", "CP-300"),
    ("M-307", "PM-210 V-cone premix blender", 5, "VFD", "CP-300"), ("M-308", "BF-306 densifier deck", 1, "starter", "CP-300"),
    ("M-310", "DC-310 collector fan", 10, "starter", "DC-310 local"), ("M-311", "AC-311 compressor", 15, "OEM", "AC-311 local"),
    ("M-401", "BU-401 discharger screw", 3, "starter", "CP-400"), ("M-402", "CV-417 conveyor zone 1", 0.5, "VFD", "CP-400"),
    ("M-403", "CV-417 conveyor zone 2", 0.5, "VFD", "CP-400"), ("M-404", "CV-417 conveyor zone 3", 0.5, "VFD", "CP-400"),
    ("M-405", "CV-417 conveyor zone 4", 0.5, "VFD", "CP-400"), ("M-501", "BU-502 discharger screw", 3, "starter", "CP-400"),
]
OEM_FEEDS = [  # OEM machines with their own panel: feeder from the distribution panel (estimates until OEM nameplates)
    ("FL-403", "480 V 3-ph", 20), ("NW-501", "480 V 3-ph", 15), ("CP-404", "208 V 3-ph via XFMR", 15), ("CE-411", "240 V 1-ph", 15),
    ("IS-405", "240 V 1-ph", 20), ("LB-406", "120 V", 15), ("CW-409", "120 V", 15), ("CK-412", "120 V", 20), ("PL-415", "120 V", 20),
    ("CS-413", "120 V", 15), ("PA-414", "120 V", 15), ("SW-416", "120 V", 20), ("UN-402", "120 V", 15),
]
NET = [  # EtherNet/IP and IT nodes: tag, device, switch, protocol
    ("PLC-601", "CompactLogix 5069-L320ER blending", "SWI-1", "EtherNet/IP"), ("HMI-601", "PanelView 5510 blending", "SWI-1", "EtherNet/IP"),
    ("VFD-304", "PowerFlex drive RB-303", "SWI-1", "EtherNet/IP"), ("VFD-307", "PowerFlex drive PM-210", "SWI-1", "EtherNet/IP"),
    ("WS-201", "IND570 terminal majors", "SWI-1", "EtherNet/IP"), ("WS-202", "ICS685 60 kg", "SWI-1", "TCP SICS"),
    ("WS-203", "ICS685s micro scale", "SWI-1", "TCP SICS"), ("BF-306", "bag filler weigh controller", "SWI-1", "EtherNet/IP"),
    ("MD-305", "Safeline GF Profile", "SWI-1", "Ethernet (ProdX)"), ("WS-206A", "Zebra ZT411 weigh room", "SWI-1", "TCP 9100 ZPL"),
    ("PLC-602", "CompactLogix 5069-L320ER line", "SWI-2", "EtherNet/IP"), ("HMI-602", "PanelView 5510 line", "SWI-2", "EtherNet/IP"),
    ("FL-403", "Spee-Dee filler PLC", "SWI-2", "EtherNet/IP"), ("NW-501", "Spee-Dee net weigher PLC", "SWI-2", "EtherNet/IP"),
    ("CW-409", "C33 checkweigher", "SWI-2", "OPC UA"), ("VS-408", "In-Sight 2800", "SWI-2", "EtherNet/IP"),
    ("TT-407", "Videojet 6330 TTO", "SWI-2", "TCP (Videojet protocol)"), ("TJ-505", "Videojet 8610", "SWI-2", "TCP (Videojet protocol)"),
    ("PA-414", "ZE511 print engine", "SWI-2", "TCP 9100 ZPL"), ("CK-412", "Omega/UR10e cell", "SWI-2", "EtherNet/IP"),
    ("PL-415", "Robotiq PE20 / UR20", "SWI-2", "EtherNet/IP"), ("VFD-402", "PowerFlex 525 x 4 conveyor", "SWI-2", "EtherNet/IP"),
    ("SRV-611", "MES / line manager server", "SWI-3", "OPC UA client, EtherNet/IP (pycomm3), SICS, ZPL"),
    ("WS-207", "panel PCs x 3 (browser to MES)", "SWI-3", "HTTPS"), ("WS-206B", "Zebra ZT411 blending", "SWI-3", "TCP 9100 ZPL"),
    ("FW-1", "plant firewall to office / internet (one-way history push)", "SWI-3", "routed"),
]


def build():
    out = {"io": [], "modules": {}, "cables": [], "motors": [], "feeders": [], "network": []}
    slot_map = {"DI": "5069-IB16", "DO": "5069-OB16", "AI": "5069-IF8"}
    per = {"DI": 16, "DO": 16, "AI": 8}
    spare = 0.25
    for plc in ("601", "602"):
        slot = 1
        for typ in ("DI", "DO", "AI"):
            pts = [p for p in IO if p["plc"] == plc and p["type"] == typ]
            n_mod = math.ceil(len(pts) * (1 + spare) / per[typ]) if pts else 0
            out["modules"][f"{plc}-{typ}"] = dict(points=len(pts), modules=n_mod, catalog=slot_map[typ], spare_pct=round(100 * (n_mod * per[typ] - len(pts)) / max(1, n_mod * per[typ])))
            for i, p in enumerate(pts):
                s = slot + i // per[typ]; ch = i % per[typ]
                p = dict(p, slot=s, channel=ch, wire=f"{plc}-{s:02d}-{ch:02d}", address=f"Local:{s}:{'I' if typ != 'DO' else 'O'}.{'Pt' if typ != 'AI' else 'Ch'}{ch:02d}")
                out["io"].append(p)
            slot += n_mod
    # one multi-core cable per field device per panel
    cab = {}
    for p in out["io"]:
        key = (p["plc"], p["device"])
        cab.setdefault(key, []).append(p)
    n = {"601": 300, "602": 400}
    for (plc, dev), pts in sorted(cab.items()):
        n[plc] += 1
        cores = sum(2 if p["type"] == "AI" else 1 for p in pts) + 2          # + 0 V/24 V commons
        size = next(c for c in (4, 7, 12, 19, 25) if c >= cores)
        cable = f"W-{n[plc]}"
        for p in out["io"]:
            if p["plc"] == plc and p["device"] == dev:
                p["cable"] = cable
        out["cables"].append(dict(cable=cable, plc=plc, device=dev, cores=cores, spec=f"{size}C x 18 AWG [0.82 mm²] shielded TC-ER, 600 V" if any(x["type"] == "AI" for x in pts)
                                  else f"{size}C x 18 AWG [0.82 mm²] TC-ER, 600 V", from_=f"CP-{'300' if plc == '601' else '400'} TB-{n[plc] % 100:02d}", to=dev))
    total_fla = 0
    for i, (tag, load, hp, st, panel) in enumerate(MOTORS, 1):
        fla = FLA[hp]; total_fla += fla
        wire = "12 AWG [3.3 mm²]" if fla <= 16 else "10 AWG [5.3 mm²]"
        out["motors"].append(dict(tag=tag, load=load, hp=hp, fla_460=fla, starter=st, panel=panel, cable=f"F-{100 + i}", conductor=f"3 x {wire} + GND, XHHW-2 in conduit"))
    for i, (dev, sup, brk) in enumerate(OEM_FEEDS, 1):
        out["feeders"].append(dict(tag=dev, supply=sup, breaker_a=brk, cable=f"F-{200 + i}"))
    out["service"] = dict(voltage="480Y/277 V 3-ph 4-w", main_a=400, src="assumed; size after OEM nameplates",
                          motor_fla_sum_460=round(total_fla, 1), note="NEC 430.24: 125% of largest + sum of others for the motor feeder")
    out["network"] = [dict(tag=a, device=b, switch=c, protocol=d) for a, b, c, d in NET]
    out["photo_eyes"] = len(PE)
    return out


if __name__ == "__main__":
    o = build()
    (HERE / "io.json").write_text(json.dumps(o, indent=1))
    for k, v in o["modules"].items():
        print(k, v)
    print(len(o["io"]), "points,", len(o["cables"]), "field cables,", len(o["motors"]), "motors,", o["photo_eyes"], "photo-eyes")
