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

For physical products the full hardware build package is the default, not an optional extra. Three standards apply to every hardware package and are checked before hand-off:
- **Every part is BUY or BUILD** (`references/parts-and-bom.md`): each item needed to assemble the product, down to fasteners and wire, is either a purchasable part with manufacturer, MPN or standard designation, spec and supplier link, or a part made from a design file that is in the package. Run the BOM completeness check.
- **Production-quality drawings** (`references/drawings.md`): maximum detail, never minimal. Every dimension in mm [inch], hole tables for every hole, toleranced part drawings with title blocks, exploded assembly drawings ballooned to the BOM, DXF cut files in both mm and inch for every plate, gasket and flat part, and an illustrated step-by-step assembly guide. Look at every page.
- **3D printed parts end in verified G-code** (`references/3d-print-gcode.md`): designed for printing, meshes checked, sliced headless for the user's printer, G-code checked by script, with a print plan. This is a major part of the prototype phase, not an afterthought.

If the product runs code anywhere (firmware, BIOS/bootloader, embedded OS, companion app, backend), software is its own development phase with the same bar: read `references/software-phase.md` and deliver requirements, architecture, buildable source, a real build, tests, flashing/update instructions and an honest verified/unverified status for each layer. Ask which the user wants only if the product type does not make it obvious; the reference file has a default for each. Build it from the spec, not from the original's code or files, run or render it to confirm it works, and record in the README which acceptance criteria it covers. Skip this phase only if the user asks for analysis alone.

### 6. Verify and hand off
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
- Cloning blindly. If the user's goal is "better", record the original's weaknesses and propose improvements in the spec.
