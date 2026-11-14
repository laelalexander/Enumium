"""Interactive arm console (Windows / macOS / Linux).
    python -m arm.cli --sim                 # no hardware
    python -m arm.cli                       # auto-detect the Arduino serial port
    python -m arm.cli --port COM4           # or /dev/ttyACM0, /dev/tty.usbmodem1101
"""
import argparse, shlex, sys
from pathlib import Path
from .control import Arm, SimDriver, SerialDriver

HELP = """commands:
  ports                      list serial ports
  home                       home all joints (limit switches)
  go X Y Z [pitch]           move wrist to X Y Z mm (IK; shoulder axis = origin)
  joints YAW SH EL WR        move by joint angles in degrees
  grip MM                    gripper opening 0-70 mm
  stop                       stop and disable drivers (arm may drop!)
  help | quit"""

def find_port():
    from serial.tools import list_ports
    cands = [p for p in list_ports.comports()
             if p.vid == 0x2341 or any(k in (p.description or "") + p.device for k in ("Arduino", "ACM", "usbmodem", "wchusb", "CH340"))]
    return cands[0].device if cands else None

def run_line(arm, line):
    a = shlex.split(line)
    if not a: return
    c, args = a[0].lower(), [float(x) for x in a[1:]] if a[0].lower() in ("go", "joints", "grip") else a[1:]
    if c == "go" and len(args) in (3, 4): print("joints:", arm.move_to(*args))
    elif c == "joints" and len(args) == 4: arm.move_joints(*args)
    elif c == "grip" and len(args) == 1: arm.grip(args[0])
    elif c == "home": arm.home()
    elif c == "stop": arm.d.stop()
    elif c == "ports":
        from serial.tools import list_ports
        for p in list_ports.comports(): print(p.device, "-", p.description)
    elif c in ("help", "?"): print(HELP)
    else: print("unrecognised; type help")

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--port")
    ap.add_argument("--design", default=str(Path(__file__).parent.parent / "design" / "design.json"))
    a = ap.parse_args(argv)
    if a.sim:
        drv = SimDriver()
    else:
        port = a.port or find_port()
        if not port: sys.exit("No Arduino found. Plug it in, or use --port COMx / --sim. (try: python -m arm.cli then 'ports')")
        print("using", port); drv = SerialDriver(port)
    arm = Arm.from_design(drv, a.design)
    print(HELP)
    while True:
        try: line = input("arm> ")
        except (EOFError, KeyboardInterrupt): print(); break
        if line.strip() in ("quit", "exit"): break
        try: run_line(arm, line)
        except Exception as e: print("error:", e)

if __name__ == "__main__":
    main()
