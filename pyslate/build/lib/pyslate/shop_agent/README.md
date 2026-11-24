# Pyslate shop agent

A small program for a shop PC (Windows, macOS or Linux, Python 3.11+). It picks up the
jobs you send from **Shop console > Production** on pyslate.com, hands each one to its
machine on the shop network, and reports machine status and progress back.

Pyslate can't reach machines inside the shop, so the agent calls out to Pyslate every few
seconds over HTTPS. Nothing needs to be opened on the shop's router.

## Start it

1. In the shop console, open **Shop agent** and download `pyslate-shop-agent.zip`.
2. Unzip it, for example to `C:\Pyslate\agent`.
3. Edit `agent.json` (see below). The server address and token are already filled in.
4. Check the machines: `py -3 -m shop_agent --config agent.json --status`
5. Start it: double-click `run-agent.bat`, or `py -3 -m shop_agent --config agent.json`.
   Leave the window open. Stop it with Ctrl+C.

## agent.json

```json
{
  "server": "https://pyslate.com",
  "token": "…",
  "name": "yaeger",
  "poll_seconds": 10,
  "machines": [
    {"id": "m2", "driver": "xtool", "host": "192.168.1.61", "mode": "studio", "enabled": true},
    {"id": "bambu", "driver": "bambu", "host": "192.168.1.50", "serial": "…", "access_code": "…",
     "slicer": {"command": ["…/bambu-studio.exe", "--slice", "0", "--export-3mf", "{output}", "{input}"],
                "output_ext": ".gcode.3mf"}, "enabled": true},
    {"id": "a8s", "driver": "marlin", "port": "COM4", "baud": 115200,
     "slicer": {"command": ["…/prusa-slicer-console.exe", "--export-gcode", "--load", "a8s.ini",
                            "--output", "{output}", "{input}"], "output_ext": ".gcode"}, "enabled": true},
    {"id": "24r", "driver": "folder", "folder": "\\\\pathpilot\\gcode", "enabled": true}
  ]
}
```

`id` must match the machine's id in **Rates and machines**. One run per machine at a time.

## Drivers

| Driver | Machines | What it does |
| --- | --- | --- |
| `xtool` | X1, M2, F2, MetalFab | Saves the laid-out SVG sheet (red = cut, blue = engrave) and opens it in xTool Studio, with speed, power and passes in the run's note. The operator frames it and presses start on the machine. With `host` set, status shows whether the laser answers on the network (port 28900). |
| `bambu` | Bambu Lab printers | Slices with Bambu Studio's command line, uploads the `.gcode.3mf` over FTPS, starts it over MQTT, and reports progress and time left. Needs LAN mode on, the printer's serial and access code, and `pip install paho-mqtt`. |
| `marlin` | JG Maker A8S, A6 | Slices with your slicer's command line, then streams the G-code over USB serial with line numbers and checksums. Stopping a run turns heaters off and lifts the nozzle. Needs `pip install pyserial`. Only one program can hold the COM port, so close Nero 8 while the agent prints. |
| `folder` | Tormach, plasma, molding, anything else | Copies the file into a folder (a share PathPilot can see, a USB stick) and optionally opens it (`"open": true` or a command list with `{file}`). |

Runs that end with an operator (xTool hand-off, folder) stay **Running** until someone
clicks **Mark done** on the Production page.

## Slicer commands

`{input}`, `{output}` and `{copies}` are filled in for each run. If a run has more than
one copy and the command has no `{copies}`, the run fails with a clear message. Send one
copy per run, or add your slicer's duplicate option (PrusaSlicer: `--duplicate {copies}`).

Export your printer, filament and process presets from the slicer and point the command
at them, so the agent slices exactly as you would by hand.

## Not done yet

* Sending laser jobs straight to xTool machines without xTool Studio (`"mode": "direct"`).
  This needs the file-upload framing captured from xTool Studio with Wireshark first.
* Slicing inside Pyslate, so prices use real print times.
