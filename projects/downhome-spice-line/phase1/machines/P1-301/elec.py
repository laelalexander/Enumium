"""P1-301 control panel CP-301: one table of components, wires, terminals and cables that the E01..E04 sheets draw from."""

SUPPLY = "230 V 1-phase 60 Hz, 2-wire + PE, from MS-P1 breaker 40 A 2-pole, 8 AWG [10 mm²] THHN in conduit (load ≈ 24 A at full load)"

# tag, description, maker, part number, qty, unit USD (estimate), where
COMPONENTS = [
    ("CP-301", "Enclosure 24 x 20 x 8 in, 304 SS, NEMA 4X, with back panel and mounting feet", "nVent Hoffman", "CSD24208SS + CP2420 + CMFK (confirm)", 1, 760, "frame rails 410"),
    ("Q1", "Disconnect switch 40 A 3-pole, door handle, lockable", "ABB", "OT40F3 + OHB45J6 handle + OXP6X shaft", 1, 95, "back panel"),
    ("F1, F2", "Fuse Class J 35 A time delay", "Mersen", "AJT35", 2, 22, "in FH1"),
    ("FH1", "Fuse holder Class J 30/60 A 2-pole, indicating", "Mersen", "US6J2I (confirm 60 A frame for 35 A)", 1, 70, "back panel"),
    ("U1", "VFD 2 HP 230 V 1/3-ph input, STO, RS-485 Modbus", "AutomationDirect", "GS21-22P0", 1, 300, "back panel"),
    ("Q2", "Miniature breaker 2-pole C2", "ABB", "S202-C2", 1, 30, "DIN rail"),
    ("G1", "Power supply 24 V DC 150 W DIN", "Mean Well", "HDR-150-24", 1, 45, "DIN rail"),
    ("F3", "Fuse holder + 4 A fuse, 24 V distribution", "Phoenix Contact", "UK 5-HESI + 5x20 4 A", 1, 12, "DIN rail"),
    ("K0", "Safety relay 24 V DC, 3 NO safety + 1 NC aux, manual monitored reset", "Pilz", "PNOZ s4 750104", 1, 330, "DIN rail"),
    ("K1", "Run seal-in relay 24 V DC 2 CO with socket", "Phoenix Contact", "PLC-RSC-24DC/21-21", 1, 28, "DIN rail"),
    ("K331", "Valve interposing relay 24 V DC 1 CO with socket", "Phoenix Contact", "PLC-RSC-24DC/21", 1, 18, "DIN rail"),
    ("K2", "Motor thermistor relay 24 V DC", "Eaton", "EMT6-DB", 1, 120, "DIN rail"),
    ("S0", "E-stop 40 mm mushroom, turn release, 2 NC + legend", "Schneider", "ZB5AS844 + ZB5AZ104 + ZBY9330", 1, 55, "door"),
    ("S1", "Push button green flush START 1 NO", "Schneider", "XB5AA31", 1, 18, "door"),
    ("S2", "Push button red STOP 1 NC", "Schneider", "XB5AA42", 1, 18, "door"),
    ("S3", "Push button blue RESET 1 NO", "Schneider", "XB5AA61", 1, 18, "door"),
    ("S4", "Selector 3-position LOCAL / OFF / REMOTE, 2 NO", "Schneider", "XB5AD33", 1, 25, "door"),
    ("H1", "Pilot light green RUN 24 V LED", "Schneider", "XB5AVB3", 1, 18, "door"),
    ("H2", "Pilot light red FAULT 24 V LED", "Schneider", "XB5AVB4", 1, 18, "door"),
    ("X1-X3", "Terminal blocks (feed-through, ground, fused, 2-level) and end stops", "Phoenix Contact", "UT 2.5 / UT 6 / PT 2.5-PE + E/UK", 1, 90, "DIN rail"),
    ("-", "DIN rail, wire duct 40 x 60, cable glands M20/M25 SS, ferrules, labels", "various", "NS 35/7.5; Panduit G2X3; Lapp SKINTOP MS-SC", 1, 160, "back panel"),
    ("W-M1", "VFD motor cable 4 x 14 AWG shielded, 600 V, oil res., 4 m", "Lapp", "ÖLFLEX VFD 2XL 14/4 (confirm)", 1, 60, "panel to motor"),
    ("W-M2", "Thermistor cable 2 x 18 AWG shielded, 4 m", "Belden", "8760", 1, 15, "panel to motor"),
    ("W-F1", "Interlock and level cable 8 x 20 AWG shielded, washdown, 6 m", "Lapp", "ÖLFLEX ROBUST 215 C 8G0.5 (confirm)", 1, 45, "panel to sensors"),
    ("W-P04", "Plant I/O cable 12 x 20 AWG shielded to the line PLC panel, 15 m", "Lapp", "ÖLFLEX ROBUST 215 C 12G0.5 (confirm)", 1, 110, "panel to CP-P1"),
    ("W-P07", "Valve cable 7 x 20 AWG, 6 m", "Lapp", "ÖLFLEX ROBUST 215 C 7G0.5 (confirm)", 1, 35, "panel to P1-331"),
    ("W-P30", "RS-485 cable 1 pair shielded 120 Ω, 15 m", "Belden", "3105A", 1, 30, "panel to CP-P1"),
]

# wire no, from, to, size, colour, function
WIRES = [
    ("1L1", "X1:L1", "Q1:1", "8 AWG", "BK", "supply L1"), ("1L2", "X1:L2", "Q1:3", "8 AWG", "BK", "supply L2"), ("PE", "X1:PE", "PE bar", "8 AWG", "GN/YE", "earth"),
    ("2L1", "Q1:2", "FH1:1", "10 AWG", "BK", ""), ("2L2", "Q1:4", "FH1:3", "10 AWG", "BK", ""),
    ("3L1", "FH1:2", "U1:R/L1", "10 AWG", "BK", "VFD input"), ("3L2", "FH1:4", "U1:S/L2", "10 AWG", "BK", "VFD input"),
    ("4L1", "FH1:2", "Q2:1", "14 AWG", "BK", "24 V supply feed"), ("4L2", "FH1:4", "Q2:3", "14 AWG", "BK", ""),
    ("5L1", "Q2:2", "G1:L", "14 AWG", "BK", ""), ("5L2", "Q2:4", "G1:N", "14 AWG", "BK", ""),
    ("U", "U1:U/T1", "X2:U", "14 AWG", "BK", "motor (W-M1)"), ("V", "U1:V/T2", "X2:V", "14 AWG", "BK", ""), ("W", "U1:W/T3", "X2:W", "14 AWG", "BK", ""),
    ("100", "G1:+V", "F3:1", "16 AWG", "BU", "+24 V"), ("101", "F3:2", "X3:1..6", "18 AWG", "BU", "+24 V fused"), ("0", "G1:-V", "X3:0 (bridge)", "16 AWG", "WH/BU", "0 V"),
    ("110", "X3:1", "S0:11", "18 AWG", "BU", "safety ch1 feed (K0 S11 via S0, P1-332)"), ("111", "S0:12", "X4:3", "18 AWG", "BU", "E-stop ch1 to cover switch"),
    ("112", "X4:4", "K0:S12", "18 AWG", "BU", "ch1 return"), ("113", "K0:S21", "S0:21", "18 AWG", "BU", "safety ch2"), ("114", "S0:22", "X4:5", "18 AWG", "BU", ""),
    ("115", "X4:6", "K0:S22", "18 AWG", "BU", "ch2 return"), ("116", "K0:S33", "S3:13", "18 AWG", "BU", "reset"), ("117", "S3:14", "K0:S34", "18 AWG", "BU", ""),
    ("120", "K0:13", "U1:STO1", "18 AWG", "BU", "STO channel 1 (+24 V via K0 13-14)"), ("121", "K0:23", "U1:STO2", "18 AWG", "BU", "STO channel 2"),
    ("122", "X3:2", "K0:14/24 feed", "18 AWG", "BU", "+24 V to K0 safety outputs"), ("123", "U1:SCM", "X3:0", "18 AWG", "WH/BU", "STO common"),
    ("130", "X3:3", "S4:13 (LOCAL)", "18 AWG", "BU", "local control feed"), ("131", "S4:14", "S2:11", "18 AWG", "BU", ""), ("132", "S2:12", "S1:13 / K1:11", "18 AWG", "BU", "stop"),
    ("133", "S1:14 / K1:14", "K1:A1", "18 AWG", "BU", "run seal-in coil"), ("134", "X4:9 (REMOTE RUN)", "K1:A1 via S4:24", "18 AWG", "BU", "remote run from plant"),
    ("140", "K1:21", "U1:DCM", "18 AWG", "WH/BU", "VFD FWD common (sink)"), ("141", "K1:24", "U1:FWD/DI1", "18 AWG", "WH/BU", "VFD FWD"),
    ("142", "K2:13", "U1:DI3 (EF)", "18 AWG", "WH/BU", "motor over-temp to external fault"), ("143", "K2:14", "U1:DCM", "18 AWG", "WH/BU", ""),
    ("150", "U1:R1A", "H1:X1", "18 AWG", "BU", "RUN lamp (VFD relay 1 = running)"), ("151", "U1:R2A", "H2:X1", "18 AWG", "BU", "FAULT lamp (VFD relay 2 = fault)"),
    ("152", "X3:4", "U1:R1C / R2C", "18 AWG", "BU", "+24 V to VFD relay commons"),
    ("160", "X3:5", "X4:1", "18 AWG", "BU", "+24 V to level switch P1-337"), ("161", "X4:2", "X5:3", "18 AWG", "BU", "HIGH level to plant"),
    ("170", "X5:1", "K331:A1", "18 AWG", "BU", "valve open cmd from plant"), ("171", "K331:14", "X6:1", "18 AWG", "BU", "valve OPEN drive"), ("172", "K331:12", "X6:2", "18 AWG", "BU", "valve CLOSE drive"),
    ("173", "X6:3", "X5:6", "18 AWG", "BU", "valve OPEN limit"), ("174", "X6:4", "X5:7", "18 AWG", "BU", "valve CLOSED limit"),
    ("180", "K0:31/32 aux", "X5:4", "18 AWG", "BU", "SAFETY OK (cover closed, E-stop out) to plant"), ("181", "U1:MO1", "X5:5", "18 AWG", "BU", "VFD ready to plant"),
    ("A+", "U1:RS485+", "X7:1", "22 AWG pair", "-", "Modbus RTU to CP-P1"), ("A-", "U1:RS485-", "X7:2", "22 AWG pair", "-", ""),
]

TERMINALS = [
    ("X1", "L1, L2, PE", "UT 10 / PT 10-PE", "incoming supply"),
    ("X2", "U, V, W, PE, TP1, TP2", "UT 4 / PT 4-PE / UT 2.5", "motor W-M1 and thermistor W-M2 (shields on the gland/EMC clamp)"),
    ("X3", "1..6 (+24 V), 0 (bridged x 6)", "UT 2.5 + FBS bridges", "24 V distribution"),
    ("X4", "1 +24 V LS, 2 HIGH, 3-4 cover sw ch1, 5-6 cover sw ch2, 7 cover aux, 8 0 V, 9 remote run", "UT 2.5", "field: P1-337, P1-332 (W-F1); plant run (W-P04)"),
    ("X5", "1 VALVE CMD, 3 HIGH, 4 SAFETY OK, 5 READY, 6 OPEN, 7 CLOSED, 8 RUNNING, 9 0 V, 10 +24 V", "UT 2.5", "plant PLC CP-P1 via W-P04"),
    ("X6", "1 OPEN, 2 CLOSE, 3 LS OPEN, 4 LS CLOSED, 5 +24 V, 6 0 V, PE", "UT 2.5", "valve P1-331 via W-P07"),
    ("X7", "1 D+, 2 D-, 3 SG, 4 shield", "UT 2.5", "RS-485 W-P30 (120 Ω end resistor in the VFD)"),
]

# GS21 parameters (numbers per the GS20/GS21 user manual: confirm on the installed firmware)
VFD = [
    ("P00.20", "Frequency command source", "0 = keypad / 1 = RS-485", "1 (REMOTE speed from CP-P1); keypad 60.0 Hz in LOCAL"),
    ("P00.21", "Operation command source", "1 = external terminals", "1"),
    ("P01.00", "Max output frequency", "Hz", "60.0"),
    ("P01.01", "Motor base frequency", "Hz", "60.0"),
    ("P01.02", "Motor rated voltage", "V", "230"),
    ("P01.12", "Accel time 1", "s", "5.0 (soft start, full batch)"),
    ("P01.13", "Decel time 1", "s", "3.0"),
    ("P01.11", "Min output frequency (lower limit)", "Hz", "30.0"),
    ("P05.01", "Motor rated current", "A", "per nameplate (≈ 6.2 A at 230 V, confirm)"),
    ("P05.03", "Motor rated speed", "rpm", "per nameplate (≈ 1,740)"),
    ("P06.03", "Over-torque detection", "-", "enabled while running, 150 %, 2 s -> fault (jam)"),
    ("P02.01", "DI1 function", "-", "FWD run (2-wire)"),
    ("P02.03", "DI3 function", "-", "external fault N.O. (K2 thermistor)"),
    ("P02.13", "Relay 1", "-", "running"),
    ("P02.14", "Relay 2", "-", "fault"),
    ("P09.00..04", "Modbus address / baud / format", "-", "addr 31, 19.2 k, 8E1 (match CP-P1)"),
    ("STO", "Safe torque off", "hard wired", "STO1/STO2 from K0; SIL2/PLd with PNOZ s4"),
]

IO_PLANT = [  # signal, direction (from blender), type, cable/terminal, PLC tag
    ("RUN REQUEST", "in", "24 V DC dry contact", "W-P04 / X4:9", "P1_301_RunReq"),
    ("VALVE OPEN CMD", "in", "24 V DC sourcing output", "W-P04 / X5:1", "P1_331_OpenCmd"),
    ("HIGH LEVEL", "out", "24 V PNP", "W-P04 / X5:3", "P1_337_High"),
    ("SAFETY OK", "out", "24 V via K0 aux", "W-P04 / X5:4", "P1_301_SafetyOK"),
    ("VFD READY", "out", "24 V", "W-P04 / X5:5", "P1_301_Ready"),
    ("VALVE OPEN", "out", "24 V limit", "W-P04 / X5:6", "P1_331_ZSO"),
    ("VALVE CLOSED", "out", "24 V limit", "W-P04 / X5:7", "P1_331_ZSC"),
    ("RUNNING", "out", "24 V via relay 1", "W-P04 / X5:8", "P1_301_Running"),
    ("SPEED / CURRENT / FAULT CODE", "both", "Modbus RTU", "W-P30 / X7", "P1_301_VFD.*"),
]
