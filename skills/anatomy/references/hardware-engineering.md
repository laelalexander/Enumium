# Hardware engineering: the full build package

For physical products a shape file is not a product. A rebuildable hardware design needs the mechanics, the electronics (or thermal/fluid systems), the firmware or controls, and written instructions that take someone from a parts order to a working, tested unit. Produce all the disciplines that apply, in one consistent package, because the disciplines constrain each other (the PCB outline sets the enclosure; the heat load sets the airflow; the bill of materials sets the budget).

Everything is original work derived from the blueprint. Tag every number `[observed]`, `[documented]`, `[inferred]` or `[assumed]`, and ask the user for missing critical measurements or requirements rather than inventing them.

## Package layout (`prototype/`)
```
00-design-basis.md      requirements, operating conditions, key numbers and their sources, system block diagram
mechanical/             parametric CAD source, STEP/STL, drawings, tolerance + fastener notes, mechanism analysis
electrical/             schematic, netlist, BOM, PCB design files and layout notes, power budget, test points
firmware-controls/      state machine, pinout, driver plan, code skeleton that compiles or simulates
thermal-fluid/          (when relevant) heat load, airflow or refrigerant cycle calculations
bom/bom.csv             unified bill of materials: ref, description, manufacturer, MPN, qty, unit cost, supplier link or source, alt part
build-instructions.md   step by step assembly, wiring, programming, calibration
test-and-commissioning.md  bring-up checklist, acceptance tests, expected readings, failure diagnosis
safety-and-compliance.md   hazards, protections, applicable standards, what must be certified before sale or install
renders/                images of every model, drawing and board so the user can see them without CAD tools
README.md               what is verified (built, rendered, simulated, calculated) versus not verified
```
Scale the package to the product. A bracket needs mechanics and notes; an e-ink display needs all of electrical, mechanical, firmware and instructions; an HVAC system needs thermal-fluid, controls and safety front and center.

## Mechanical
- Parametric source (CadQuery/build123d or OpenSCAD) with all key dimensions as named parameters. Export STEP (for CAD handoff) and STL (for printing). Check watertightness, units (mm), wall thickness, overhangs, and split large parts with alignment features.
- Mechanisms are more than shapes: state the degrees of freedom, motion range, loads and forces, fits and clearances (e.g. H7/g6 or print-tolerance offsets), and fastener choices (thread, length, torque, boss/insert design). Do first-order checks by calculation: torque and gear ratio, spring rate, beam deflection and stress against material yield with a safety factor, bearing loads, snap-fit strain. Show the arithmetic.
- Enclosures: board mounting, connector and button cutouts aligned to the actual PCB outline, cable strain relief, ingress protection goal, thermal path, serviceability, tolerance stack-up for anything that must align.
- Drawings: dimensioned orthographic views with title block, units, tolerances, section views; an exploded assembly with numbered balloons that match the BOM.
- Manufacturing route per part: FDM/SLA print, CNC, sheet metal, injection molding (note draft angles, wall thickness, undercuts), with a note on what changes between prototype and production.

## Electrical and PCBA
Deliver design files and the reasoning, not just a picture.
1. **Requirements to architecture**: functions, interfaces, power rails, signal types. Block diagram first.
2. **Part selection with real parts**: manufacturer part numbers, package, key ratings, availability and cost source, and a second-source alternate for critical or scarce parts. Check datasheet facts you rely on (voltage limits, logic levels, pin functions, timing, required external components) and cite the datasheet. Do not invent part numbers; if you cannot confirm a part exists and fits, say so and mark it `[assumed]`.
3. **Schematic**: complete, with power, decoupling, pull-ups, reset, programming/debug header, protection (ESD, reverse polarity, fusing), test points, net names and reference designators. Output a netlist plus a rendered schematic (KiCad `.kicad_sch` if `kicad-cli` or generation is feasible; otherwise SKiDL/schemdraw to SVG with a machine-readable netlist). Run an electrical rules check yourself: unconnected pins, power pins without a source, nets with no driver.
4. **Calculations**: power budget per rail (typical and peak), regulator headroom and dissipation, LED/resistor values, divider ratios, RC timings, battery life estimate, current through connectors and traces.
5. **PCB design**: board outline and mounting holes tied to the mechanical model, stackup (layers, copper weight, thickness), placement strategy (connectors at edges, decoupling at pins, antenna keep-out, thermal pads), trace widths from current and impedance needs, return paths and plane strategy, high-speed or sensitive-signal rules, clearance and creepage if mains voltage is present, fabrication notes. Where tooling allows, produce `.kicad_pcb` or Gerber/drill files; otherwise provide a placement and routing spec precise enough for a layout engineer plus a rendered floorplan image. Say which one you produced.
5b. **Native KiCad files**: for any board, follow `kicad-pcb.md` to generate `.kicad_sch` and `.kicad_pcb`, run KiCad's own ERC and DRC, and export Gerbers, drill, centroid and a board STEP. Install KiCad if it is missing and the machine allows it; if it cannot run, say so and label the PCB specified only.
6. **Manufacturing outputs**: BOM in assembler format (designator, value, footprint, MPN), pick-and-place centroid, assembly drawing, fab notes.
7. **Design for test**: test points, bring-up order (power rails first, then clocks, then peripherals), expected voltages and waveforms.

## Firmware and controls
State machine or task diagram, pin assignments that match the schematic exactly, driver and library plan (named, versioned), timing and power-state behavior (sleep, wake, refresh), update/OTA plan, fault handling. Provide a skeleton that compiles or simulates (PlatformIO/Arduino/ESP-IDF/Python), and say whether you built it. Keep generated pinouts and the schematic in sync by deriving both from one table.

## Thermal / fluid / HVAC systems
- **Design basis**: climate and load (design indoor/outdoor temps, floor area, envelope), capacity target, efficiency target (SEER/COP), noise, refrigerant and its regulatory status.
- **Load and sizing**: heating/cooling load calculation (Manual J style first-order: envelope, infiltration, internal gains, ventilation), airflow from sensible load (CFM from BTU/h and ΔT), duct or hydronic sizing with pressure drop, fan or pump selection against the system curve.
- **Cycle**: for refrigerant systems, state points on the pressure-enthalpy diagram, compressor, evaporator, condenser and expansion device sizing, superheat/subcooling targets, charge estimate. For novel cycles (heat pump variants, thermoelectric, desiccant, evaporative, magnetic), model the cycle, state the efficiency claim and the assumption it rests on, and flag where physics or published data is thin. Compute with a script and include the numbers.
- **Controls**: sensors (placement and accuracy), actuators, control loop and staging logic, defrost, anti-short-cycle, lockouts, communications (Modbus, BACnet, thermostat protocols), wiring diagram for low and line voltage.
- **Safety**: pressure relief, high-pressure and low-pressure cutouts, flame or combustion safety if any, electrical protection, condensate handling, refrigerant handling certification, local code and standards references. HVAC and mains-powered work has life-safety consequences: mark every step that requires a licensed professional, and never present the design as certified.

## Build instructions
Write them for someone who has the parts and tools but not the designer's head.
1. Tools and consumables list; skills assumed; time estimate.
2. Parts procurement by BOM line, with kits (print files, PCB order settings, fasteners).
3. Numbered steps with the expected result of each step and a photo/render reference. Order matters: sub-assemblies, then integration. Call out torque values, solder order, orientation marks, polarity, and anything irreversible.
4. Electrical bring-up before connecting expensive or dangerous parts: continuity checks, current-limited first power-up, rail voltages with expected values.
5. Programming and calibration.
6. Acceptance tests and troubleshooting table (symptom, likely cause, check).
7. Warnings placed at the step where the hazard occurs, not only at the top.

## Verification honesty
Mark each deliverable as one of: **built and tested** (physically), **simulated**, **calculated**, **rendered/checked by script**, **specified only**. In this environment you usually cannot fabricate boards or test hardware, so say so clearly in the README and list what the user must verify on real hardware before relying on it (fit, thermal behavior, RF, safety). Never imply a design has been validated beyond what was actually done.
