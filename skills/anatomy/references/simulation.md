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
   - **It never looks stuck.** From the first paint, the page shows a loading screen with a real progress bar and the stage it is on (3D engine and code, design data, firmware, the 3D model with MB downloaded of total, building the scene). The model download reports byte progress. Any failure (a missing file, a module that will not load, no word after 45 s) turns the screen into a plain-language error naming the file, with a Try again button. A bare "loading..." line is not acceptable. The worked example is `sim/public/index.html` and `app.js` of the pilot XPS line project (`window.TwinLoad`).
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
- It also opens and runs in the pyrails.com web console (static files, relative URLs, no server needed).
- Every number in the model traces to the design. Put a `sim/README.md` table of parameters, each with its source.
- All tests run headless, and their results are in `sim/results/latest.json`. Any failure is reported as a design finding, not hidden.
- Start it yourself, run every scenario, and take screenshots of the twin and the test results before you present it.
- Say plainly what the simulation does not model. For example: "no belt stretch, no thermal derating, rigid links".
