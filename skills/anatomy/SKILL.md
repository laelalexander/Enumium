---
name: anatomy
description: Dissect an existing product (web app, website, SaaS, mobile app, CLI, API, library, desktop/binary tool, or physical/hardware product) and produce a clean-room reengineering blueprint - features, architecture, data model, UX flows, inferred tech stack, and a build-ready rebuild spec - then prove it with a prototype (a running build demo, interactive application viewer, 3D-printable model, full hardware package with KiCad PCB files, or technical drawings). Use this whenever the user wants to reverse engineer, reengineer, teardown, clone, recreate, "rebuild X", understand how a product works under the hood, or map a competitor or legacy system, even if they never say "anatomy". Works from a live URL, a local repo, docs/API specs, CLI/binary behavior, or measurements and photos of a physical product.
---

# Anatomy

Dissect a product into a blueprint that another engineer (or Claude) could rebuild it from, without ever seeing the original. The value is in separating **what the product does and why** from **how this particular implementation does it**, then recording both with honest confidence levels.

## Principles

- **Clean-room.** Capture behavior, requirements, data shapes and architecture. Do not copy source code, proprietary assets, copy text, logos, or branding into the blueprint. Quote only short fragments needed as evidence. Add a "Legal & IP notes" section flagging licenses, ToS limits on scraping/reverse engineering, patents or trademarks you noticed. You are not giving legal advice; you are making risks visible.
- **Evidence over guesses.** Every claim gets a tag: `[observed]` (saw it directly), `[documented]` (public docs/spec), `[inferred]` (deduced from signals; say which), or `[assumed]` (a design choice for the rebuild). A blueprint that blurs these misleads whoever builds from it.
- **Stay within authorization.** Analyze what you are legitimately able to access: public pages, your own accounts, repos and binaries the user owns or has rights to. Do not bypass auth, rate limits, paywalls or access controls, and do not run load against someone else's service. Passive observation of normal use is fine.
- **Rebuild-oriented.** Everything gathered should answer: "what would I need to know to build this?" Skip trivia that does not change the rebuild.

## Workflow

### 1. Scope
Confirm with the user (ask only what you cannot infer): the target, the goal (faithful clone, "same but better", migration off a legacy system, learning), depth (quick pass vs. thorough), and any constraints for the rebuild (preferred stack, budget, must-have vs. skip features). Create the output folder `anatomy-<product-slug>/`.

### 2. Gather evidence
Pick the sources that match the input; use several when available. Read `references/recon-playbook.md` for concrete techniques per input type:
- **Live URL / web app**: pages and routes, DOM and CSS patterns, network calls (endpoints, payloads, auth style, realtime channels), response headers, bundles/sourcemaps, third-party scripts, SEO/meta, pricing and plan pages. Use a browser tool or Playwright if available; otherwise curl.
- **Local repo**: manifests and lockfiles, entry points, directory structure, routing, schema/migrations, config and env vars, infra files (Docker, CI, IaC), tests as behavior documentation.
- **Docs / API spec / description**: OpenAPI/GraphQL schemas, changelogs, help center, SDK reference, status pages, engineering blog posts, job postings (hint at stack), pricing pages.
- **CLI / binary / package**: `--help` trees, man pages, config and file formats, exit codes, stdin/stdout contracts, packaging metadata, linked libraries, observable I/O and side effects.

Keep a running evidence log (source, what it showed) so claims can be traced.

**Look at every image.** Concept renders, sketches, photos and drawings carry the intended form, and text extraction misses them. Rasterise every PDF page that has little text (PyMuPDF `fitz`: `page.get_pixmap(dpi=110).save(...)`, or `pdftoppm`). Pull the images out of .docx and .pptx files, and Read each one. If no rasteriser is installed, install PyMuPDF (`python -m pip install --user pymupdf`). Do not go on with "could not render". Write a short description of each image into the evidence log, saying what it shows about the form, size, materials and placement.

**When inputs disagree, the design intent comes from the newest and most specific source.** Concept renders and sketches set the form, and so does the user's own review or markup. A long text brief or proposal does not, even when it is the project prompt. If inputs give different forms (for example an open visor in the text and a closed lattice headband in the renders), build the prototype to the renders and the user's own guidance. Record the other form as a conflict. Do not prototype the text version and leave the concept for "rev B". If it is still truly unclear, ask the user in Scope before any CAD, and show the options side by side.

### 3. Analyze
Work through the layers in `references/blueprint-template.md`. In order:
1. Purpose, users, jobs-to-be-done, business model
2. Feature inventory, prioritized (core / supporting / incidental)
3. UX flows (key user journeys, states, edge cases)
4. System architecture (components, boundaries, sync vs. async, realtime, third-party services)
5. Data model (entities, relationships, lifecycle, ownership, multi-tenancy, retention)
6. Interfaces (public/internal APIs, events, auth and permissions)
7. Tech stack inference with confidence and the signals behind each guess (see `references/stack-signals.md`)
8. Non-functional traits (performance, scale hints, security posture, accessibility, i18n, offline)
9. Gaps and unknowns, listed explicitly

### 4. Write the blueprint
Write a folder of markdown files (the structure is in `references/blueprint-template.md`). Always include `00-overview.md` (summary, goals, how to read the rest, confidence summary) and `90-rebuild-spec.md` (the actionable part). Use Mermaid diagrams for architecture, flows and entity relationships; they diff well and render in most viewers. Keep each file focused; link between them.

The rebuild spec is the deliverable people will act on, so make it concrete: recommended stack (with reasons, and noting where it diverges from the original), module breakdown, data schema draft, API surface, phased milestones (MVP, parity, polish), acceptance criteria per feature, and the open questions that must be answered before building.

### 5. Prototype
Turn the rebuild spec into something the user can see. Read `references/prototype-phase.md` and pick the mode that fits the product:
- **Build demo**: a thin, actually-running vertical slice of the core flow with screenshots or recorded output
- **Application viewer**: a self-contained interactive walkthrough (published as an artifact when possible) combining clickable screens with the architecture, data model and API views
- **3D print**: a parametric model exported to STL with preview renders and print notes
- **Drawings**: dimensioned orthographic and exploded views, bill of materials, and schematics where relevant
- **Full hardware build package**: for any product with moving parts, electronics, or thermal/fluid systems (an e-ink display, an appliance, an HVAC system), shape files are not enough. Read `references/hardware-engineering.md` (and `references/kicad-pcb.md` for any circuit board; that KiCad step is experimental and untested, so say so to the user) and deliver the mechanics (parametric CAD, tolerances, mechanism and load calculations), the electronics (real-part BOM, schematic and netlist, power budget, real KiCad schematic and PCB files that pass KiCad's ERC/DRC with Gerber export (or, only if KiCad cannot run, a precise layout spec labeled as unverified)), firmware or controls, thermal/fluid calculations where relevant, and complete build, bring-up and test instructions

Before any CAD, write a one-paragraph **design-intent check** at the top of `prototype/00-design-basis.md`. It names the source of the form (which render, sketch or user note) and lists the must-have features from it (shape, structure such as a lattice, materials, placement of each user-visible element, weight or size targets). It also says how each one shows up in the model. When the first renders exist, compare them side by side with the concept image and fix any mismatch before drawings and G-code.

For physical products the full hardware build package is the default, not an optional extra. Three standards apply to every hardware package and are checked before hand-off:
- **Every part is BUY or BUILD** (`references/parts-and-bom.md`): each item needed to assemble the product, down to fasteners and wire, is either a purchasable part with manufacturer, MPN or standard designation, spec and supplier link, or a part made from a design file that is in the package. Run the BOM completeness check.
- **Production-quality drawings** (`references/drawings.md`): maximum detail, never minimal. Every dimension in mm [inch], hole tables for every hole, toleranced part drawings with title blocks, exploded assembly drawings ballooned to the BOM, DXF cut files in both mm and inch for every plate, gasket and flat part, and an illustrated step-by-step assembly guide. Assemblies get a general arrangement drawn from the real assembled model and true-scale hatched sections through every joint, with balloons, an item list, fits and torques. Electronics get a schematic with every wire numbered, plus a from/to wire list. The approved robot arm sheets (named in drawings.md) are the minimum bar. Look at every page.
- **3D printed parts end in verified G-code** (`references/3d-print-gcode.md`): designed for printing, meshes checked, sliced headless for the user's printer, G-code checked by script, with a print plan. This is a major part of the prototype phase, not an afterthought.

**Simulate and test** (`references/simulation.md`): any product with behaviour (moving parts, electronics, firmware, controls, a process, or software with external dependencies) ends with a runnable simulator and test environment in `sim/`. It is a digital twin built from the package's own assembly and numbers, with firmware in the loop on the real protocol, controls, live checks, automated test scenarios traced to the requirements with pass/fail and margins, headless test runs writing `sim/results/latest.json`, and a hardware link that drives the real device from the same UI. List it in `anatomy.json` with `"kind": "simulator"`. The robot arm test table is the bar.

If the product runs code anywhere (firmware, BIOS/bootloader, embedded OS, companion app, backend), software is its own development phase with the same bar: read `references/software-phase.md` and deliver requirements, architecture, buildable source, a real build, tests, flashing/update instructions and an honest verified/unverified status for each layer. Ask which the user wants only if the product type does not make it obvious; the reference file has a default for each. Build it from the spec, not from the original's code or files, run or render it to confirm it works, and record in the README which acceptance criteria it covers. Skip this phase only if the user asks for analysis alone.

### 6. Verify and hand off
**Build package.** For anything physical, finish with the build package in `references/build-package.md`: `build/build.json` plus the purchase list with supplier carts, print list with G-code, fabrication files, illustrated assembly steps, and firmware and test steps. The Anatomy app's Build wizard reads it so a person can order, print, fabricate, assemble and test without the designer.

**Make the result something the user can experience, not just a folder.** The Anatomy app shows every project in a Results view (3D model and part inspector, drawings, BOM, G-code toolpaths, electronics, software, assembly guide). Help it:
- Write `anatomy.json` at the project root: `{"title": "...", "summary": "one paragraph", "apps": [{"name": "...", "description": "what the user can do with it", "cwd": "path relative to anatomy.json", "run": ["command 1", "command 2"], "url": "http://127.0.0.1:PORT/", "needs": ["e.g. webcam, Ollama"], "startup_ms": 4000}]}`. Every runnable thing the project built (a console, simulator, web app, digital twin, demo) gets an entry. Commands run in background processes, so use servers that stay up, prefer the project's own `.venv`, and start simulators for any hardware so it works with no device attached. Start each app yourself and open its URL to prove the entry works.
- If the product has a physical form, build an interactive viewer or digital twin (three.js page loading the exported STL/GLB in assembled positions, with each part clickable to its drawing and BOM line) and list it in `apps`.
- Give the 3D view the assembly. **Always write an `assembly.json`** in a folder of in-place part meshes, for example `prototype/mechanical/assembled/`:
  - Format: `{"units": "mm", "in_place": true, "parts": [{"file", "name", "kind": "buy"|"build", "line", "supplier", "mpn", "matrix"?}], "steps": [{"n", "title", "add": [file, ...]}]}`. Files are relative to assembly.json. `kind`, `line` (the BOM line), `supplier` and `mpn` let the viewer colour bought parts and label them ("BUY: McMaster 78155T51").
  - Every custom PCBA goes in as its KiCad STEP export (board plus components) at its mounting position, with its own step. A board that exists only as files is not finished.
  - Export every part in world coordinates, bought parts (motors, boards, PSU) included, so `in_place` is true. Otherwise give each part a 16-number column-major `matrix` in mm.
  - Take `steps` from the assembly guide. Each step's `n` must equal the matching `build.json` `assembly[].step` number. Bench-only guide steps (inserts, wiring) can have no 3D step. The viewer's **Assemble** build-along walks every guide step, shows its card (parts to get ready, tools, instructions, torque, check and picture), and moves the parts listed in `add`.
  - Export from the CAD assembly with a script saved in that folder (for example `export_assembly.py`), so it can be re-run.
  - Check it with the mechanism check in `references/hardware-engineering.md`: real bought-part geometry, wheels on their axles and shafts and on the ground, no interference, fasteners where the holes are, and nothing left at the origin.
- Next to the part meshes, write a `parts.json` keyed by file name: `{name, part_no, category, qty, material, note, drawing, step}`. The viewer shows it when a part is clicked. Parts without an assembly.json can instead carry a `pose` there: `{"position": [x, y, z] mm, "rotation": [rx, ry, rz] deg XYZ}`.
- Also keep each part's STL, STEP, drawing, CAD source and G-code under the same base name, so they link to each other.
Reread the blueprint as a builder who has never seen the product: are there steps with no data source, features with no acceptance criteria, claims with no tag? Fix those. Then summarize for the user in chat: what the product is, the three most important architectural findings, biggest unknowns, the folder path, and the prototype (how to view it and what it does not cover). Offer next steps (start the build from the spec, go deeper on a subsystem, compare against a second product).

## Depth calibration
- **Quick pass** (user wants a fast read): overview, feature inventory, architecture sketch, stack guess, a short rebuild outline. One or two files is fine; the prototype can be a single viewer page or one drawing.
- **Standard**: the full template.
- **Thorough**: add per-feature deep dives, sequence diagrams for critical flows, a risk register, cost/effort estimates, and multiple prototype modes.
Default to standard unless told otherwise.

## Things that go wrong
- Treating a stack guess as fact. Header and bundle signals can be spoofed or stale; keep confidence honest.
- Describing the UI instead of the system. Screens matter, but the blueprint should explain state, data and rules behind them.
- Missing the invisible parts: background jobs, permissions, billing, notifications, admin tooling, data export/import. Check for these explicitly.
- A BOM line that says "generic", "TBD" or "any": it is not buyable. Name the part or the standard, or mark it as an open item.
- G-code that was never sliced for the user's printer, or a drawing sheet nobody looked at.
- Treating firmware or the companion app as a stub. If the product runs code, that code is part of the build.
- A prototype that was never run or rendered. Always execute the build, open the viewer, or render the model and drawings before presenting them.
- Prototyping the wrong form: building from the text brief when the renders, sketches or the user's notes show a different device. The concept images set the form. Check the first render against them before going further.
- Cloning blindly. If the user's goal is "better", record the original's weaknesses and propose improvements in the spec.
