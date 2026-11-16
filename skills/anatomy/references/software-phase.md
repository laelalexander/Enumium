# Firmware, BIOS and software: a full development phase

If the product runs code anywhere (a microcontroller, a boot loader or BIOS/UEFI, an embedded Linux image, a companion mobile or desktop app, a cloud backend, a web dashboard), software is its own phase of the build, with the same bar as the hardware: designed, built, tested and documented. A "code skeleton" is not enough. Decide in Scope which software layers the product has and list each one in the rebuild spec.

## Layers to check for
| Layer | Examples | Typical stack |
|---|---|---|
| Boot / BIOS / UEFI / bootloader | x86 boards, SBCs, MCU bootloaders, secure boot | coreboot/EDK II, U-Boot, MCUboot, vendor ROM bootloader |
| Firmware | MCU on the main PCB, motor drivers, sensor hubs, display controllers | C/C++ (ESP-IDF, Zephyr, STM32 HAL, Arduino/PlatformIO), Rust (embassy), MicroPython |
| Embedded OS image | Raspberry Pi / Linux SBC products | Yocto, Buildroot, Raspberry Pi OS + provisioning scripts |
| Companion app | phone or desktop app that sets up or controls the device | Flutter, React Native, Swift/Kotlin, Electron/Tauri |
| Backend / cloud | accounts, sync, OTA server, data APIs | the rebuild spec's chosen stack |
| Tooling | factory test, calibration, flashing scripts | Python, CLI |

## For each layer, deliver
1. **Requirements**: what it must do, mapped to the feature list and acceptance criteria in the rebuild spec.
2. **Architecture**: modules, state machine or task diagram, interfaces (pins, buses, protocols, APIs, data formats), and how it talks to the other layers. Pinouts and register maps must come from the same source table as the schematic.
3. **Source code** in `software/<layer>/`, with a real build: `platformio.ini`, `CMakeLists.txt`, `Cargo.toml`, `package.json`, etc. Pin library and toolchain versions.
4. **Build it** and record the exact command and result. Ship the compiled artifact (`.bin`/`.hex`/`.elf`/`.uf2`, app bundle) when built. If it cannot be built here, say why and what is needed.
5. **Tests**: unit tests for logic, hardware-in-the-loop or simulator tests where possible (Wokwi, QEMU, Renode, emulators), and a test plan for what needs real hardware. Run what can run.
6. **Power, timing and fault behavior**: sleep/wake and battery-life math tied to the power budget, watchdogs, brown-out, error states the user sees, recovery.
7. **Security**: secrets handling, secure boot/flash encryption where relevant, signed OTA updates, default credentials (none), network exposure.
8. **Update path**: how firmware/software is updated in the field (OTA, USB, SD), with rollback.
9. **Flashing and provisioning instructions**: tools, drivers, exact commands, how to verify the device is running the right version. These go into `build-instructions.md` at the right step.

## Development cycle
Treat software like the hardware cycle: requirements, design, implementation, build, test, integration with the hardware (bring-up order in `test-and-commissioning.md`), release. Version everything (`v0.1.0` for the prototype) and keep a `software/CHANGELOG.md`.

## Report honestly
For each layer, mark it **built and tested**, **built** (compiles, untested on hardware), **simulated**, or **specified only**, and list what must be tested on the real device.
