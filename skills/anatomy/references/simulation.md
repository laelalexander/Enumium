# Simulation and test environment

Every project that has behaviour (moving parts, electronics, firmware, controls, a process, or software with
external dependencies) ends with a **simulator the user can run and test against**, not only files. The bar is the
desktop robot arm in laelalexander/Enumium (PR #2, `3d-workflow/control/`). It is a digital twin with:
- the assembled 3D model;
- stepper and firmware emulation using the real firmware's command grammar;
- IK and joint control, presets, and teach-and-play;
- a live load and torque check against the motors' ratings;
- automated tests (joint sweep, worst-case load, gripper, reach envelope);
- a pin and signal view;
- a Web Serial hardware link that drives the real arm with the same UI.

Match that depth for the product at hand.

## What to deliver (`sim/`)
1. **The twin.** A local web app (three.js for anything physical), served by a small server with no extra dependencies, listed in `anatomy.json` `apps` with `"kind": "simulator"`.
   - It loads the same assembled model as the package (`assembly.json`), so the simulation is the design, not a lookalike.
   - Moving parts move about their real axes, within their real limits.
   - **It runs in a plain browser from its files alone.** Keep the simulation, tests-in-the-UI and hardware link in the page's own JavaScript, load everything by relative URLs, and treat the server as optional (static files plus extras such as headless jobs). The pyrails.com web console opens the twin straight from the hub's copy with no server behind it. Name the entry page in the app's `"web"` field (for example `"web": "sim/index.html"`).
2. **A behaviour model, from the design's own numbers.** Each parameter comes from the BOM, the datasheets or the calculations; none is invented for the sim.
   - **Actuators:** step rate and acceleration limits, motor torque curves or rated torque, gear ratios, servo speed, deadband.
   - **Sensors:** limit switches, encoders, IMU, current, temperature, with noise where it matters.
   - **Mechanics:** kinematics (FK and IK), mass and gravity load, joint torque against what is available, reach, collisions, and hard stops slightly beyond the soft limits.
   - **Power:** current draw per rail against the PSU and fuse ratings, plus battery runtime for mobile products.
   - **Thermal or fluid** where the product has it: a lumped model with the time constants from the calculations.
3. **Firmware in the loop.** The simulator speaks **exactly** the firmware's protocol: the same command grammar, replies and timing rules.
   - Prefer running the real firmware logic. Compile it for the host with a PlatformIO `native` environment, or factor the command parser and motion planner into a library that builds for both targets. Failing that, write a faithful emulator and test it against the firmware source.
   - Commands go through one `send()` path, so the same UI can drive the real device over Web Serial, WebSocket or MQTT when it is connected.
4. **Controls a tester needs:** per-axis control, goal or IK control, presets, record and playback (teach mode), keyboard and gamepad input, an E-stop that behaves like the real one, and a live view of every pin and signal.
5. **A test environment:**
   - **Tests in the UI:** automated scenarios you can click, each traced to a requirement or acceptance criterion in the blueprint. Examples: full-range sweep, worst-case load at full reach, duty cycle, power-on and homing, E-stop, sensor failure, comms loss, battery low, thermal soak.
   - **Pass/fail with margins:** each scenario reports a result with its margin (for example "shoulder torque margin 1.8× against 1.5× required"), not just "ok".
   - **Headless runs:** the same scenarios run with `node sim/run-tests.js` or `python -m sim.tests` and write `sim/results/latest.json`: `{"when", "passed", "failed", "tests": [{"name", "requirement", "result": "pass|fail|warn", "detail", "margin"}]}`. The Anatomy app shows this file in the Simulate tab.
   - **Live checks:** limits, collisions, torque, current and temperature light up while the user drives the twin.
6. **Hardware link:** the same UI connects to the real device and runs the same tests on it, with a clear SIM / HARDWARE indicator. Ship it disabled until the user connects.

## Runs on the hub (required)
The user opens most twins from the Anatomy Hub web console (pyrails.com), which serves the project's synced files as
plain static files at `/anatomy-hub/console/p/<project>/<path>`. There is no sim server, no `/api`, no WebSocket, and no
`node_modules`, `.venv`, `.pio` or `__pycache__` (they never sync). A twin that only works through its own server opens
there as an unstyled page stuck on "connecting…", or an error. That has happened on nearly every project, so these
rules are not optional:
- **Relative URLs only**, in HTML, CSS, JS, import maps and loaders: `./app.js`, `../vendor/three/...`,
  `../../prototype/mechanical/assembled/assembly.json`. Never `/vendor/...`, `/api/...`, `/static/...`, `/model/...`.
  Make the sim server answer the same relative paths (map the project-tree path, e.g. `/prototype/...`), so one set of
  URLs works on both. A server-only call that the page makes only after detecting its server may stay root-relative
  if its line carries the comment `simcheck:server-only`.
- **Vendor files inside the project, outside `node_modules`** (copy three.js `build/three.module.js` and the
  `examples/jsm` files you import into the sim, e.g. `sim/public/vendor/three/`).
- **The shared loading screen.** Copy `tools/simcheck/twinload.js` next to the page and load the app through it:
  `<script src="twinload.js" data-title="Opening the <product> digital twin" data-sub="..." data-entry="app.js"></script>`
  (keep the import map; drop the page's own `<script type="module" src="app.js">`). It shows real staged progress
  (engine and code bytes, data, model bytes of total, scene), plain-language errors naming the file and HTTP status,
  Try again, and a stall timeout. In the app call `TwinLoad.stage('model')` before loading meshes and `TwinLoad.done()`
  when the scene is up.
- **Server detection without 404s.** Ship a static `twin-server.json` containing `{"server": false}` next to the page and
  have the sim server answer `{"server": true}` at the same relative path. Probe that, not `/api/...`.
- **Browser-only mode when there is no server.** Run the behaviour model in the page (port it to JS, or load the JS/WASM
  core directly), read saved data by relative path (design numbers, `sim/results/latest.json`, a `static-data/` snapshot
  with a note on how to regenerate it), and keep the 3D view, controls and live checks working. What truly needs the PC
  (native firmware, Python-only models, the hardware link, headless test runs) is disabled with a tooltip, under one
  polite banner: "Browser-only mode: ... runs in Anatomy on your PC". Never an error page, never "connecting…" forever.
- **The model stands the right way up.** CAD exports are Z-up (mm); three.js is Y-up. Convert once, from the export's
  own declaration: write `"up": "Z"` in `assembly.json` (trimesh GLBs keep the CAD coordinates and add no root rotation)
  and rotate a Z-up model by -90 degrees about X; never decide from the model's proportions (a long duct or arm makes
  a tall machine "deeper than tall" and the guess lays it on its side). Put it on the floor (lowest point at y = 0), keep
  the orbit above the floor (`controls.maxPolarAngle` just under 90 degrees), and register the assembled model for the
  check: `window.TwinModel = { object: root, THREE }` (or `TwinLoad.model(root, THREE)`).
- **The hub check passes** (see below). It is part of finishing the simulator, like the headless tests.

### The hub check
```
node <skill>/tools/simcheck/simcheck.mjs <project folder>
```
It serves the project like the hub (deep sub-path, unsynced folders hidden, no server), opens every simulator and
viewer page in headless Chromium, and fails on any root-absolute URL in the page or its scripts, any console error or
uncaught exception, any failed request or HTTP error, a missing or failed loading screen, a loader that never finishes,
a blank canvas, or a model lying on its side (the registered model's height share on screen against its height share
in the GLB along the declared up axis). It writes `sim/results/hub-check.json`. Needs Playwright once (the script prints the one-line install).
Fix every failure in the twin itself and run it again until it passes; then also start the twin through its own server
(the `anatomy.json` url) and check it still works there.

## By product type
- **Robots and mechanisms:** everything above. Add path planning and the payload as an adjustable test fixture.
- **Mobile robots and vehicles:**
  - differential or Ackermann drive kinematics, wheel slip, odometry against ground truth;
  - battery discharge;
  - a simple arena with obstacles for sensor tests: ultrasonic, lidar raycast, camera frustum.
- **Electronics and PCBA:**
  - SPICE (ngspice) runs for power stages, filters and analog front ends;
  - a power-tree budget, plus thermal rise on regulators;
  - a logic or protocol-level emulation of the MCU's peripherals that the firmware uses.
  Show the waveforms in the app.
- **Appliances, HVAC and fluid systems:** a time-step model of the cycle and controls, with setpoint changes, faults and defrost, and plots of temperature, pressure and power.
- **Software products, SaaS and APIs:** a local staging environment with seeded data, mocks for every external service, scripted user journeys and load tests, and a dashboard of the results.
- **IoT:** a device emulator per device type, a local broker, and fleet scenarios (provisioning, OTA update, offline and reconnect).

## Wiring it into the Anatomy app
`anatomy.json` gets the simulator as an app, plus a `tests` entry for the headless run. The app's **Simulate** tab opens the twin, runs the tests and shows the results table:
```json
{"apps": [{"name": "TwinArm simulator", "kind": "simulator", "description": "...", "cwd": "sim", "run": ["node server.js"], "url": "http://127.0.0.1:8770/", "web": "sim/index.html", "startup_ms": 3000}],
 "tests": {"cwd": "sim", "run": "node run-tests.js", "results": "sim/results/latest.json"}}
```

## Quality bar
- It starts with one click from the Anatomy app (an `anatomy.json` entry) and works with no hardware attached.
- It also opens and runs in the pyrails.com web console (static files, relative URLs, no server needed): the hub check
  (`tools/simcheck/simcheck.mjs`) passes, and `sim/results/hub-check.json` says so.
- Every number in the model traces to the design. Put a `sim/README.md` table of parameters, each with its source.
- All tests run headless, and their results are in `sim/results/latest.json`. Any failure is reported as a design finding, not hidden.
- Start it yourself, run every scenario, and take screenshots of the twin and the test results before you present it.
- Say plainly what the simulation does not model. For example: "no belt stretch, no thermal derating, rigid links".
