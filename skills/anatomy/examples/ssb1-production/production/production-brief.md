# SSB-1 replacement traction battery for the Super Soco TS

Engineering and Manufacturing Summary, revision B (design), brief rev 1, 2026-11-15

Tags: measured/observed, quoted, documented, estimate, assumed. Full tables, charts and sources are in production-brief.html.

## Executive summary

SSB-1 is a removable 17S6P lithium-ion pack (61.2 V nominal, about 30 Ah, about 1.84 kWh) for the Super Soco TS, a 60 V light electric motorcycle. It pairs 102 Samsung 50S 21700 cells with a bought 17S smart BMS, a 60 A Class T fuse and a small custom gateway board that answers the bike's RS-485 battery polls, so the dash still shows charge and faults. The prototype housing is 3D printed PETG on four steel tie rods.

The design package is complete and machine-checked: parametric CAD, drawings in mm and inches, sliced G-code, a 6-gate bill-of-materials check, a KiCad board with 0 ERC and 0 DRC errors and a turnkey PCBA order package, and gateway firmware that builds and passes 120 host unit tests. Nothing has been built, flashed, fitted to a bike or ridden. Three facts that decide whether the pack fits a given bike (plug pin-out, lock geometry, bus protocol on a TS) are open and can be settled with under 100 USD of measurement.

The parts for one prototype cost about 1,866 USD at 2026-11-15 list prices; the comparable branded replacement lists at 1,250 EUR and was out of stock with a lead time of up to 12 weeks. Estimated cost of goods falls to about 860 USD at 100 units, about 510 USD at 1,000 and about 410 USD at 10,000, driven by cell price and by replacing the printed housing with flame-retardant moulded parts. Those volume figures are estimates; the cell figures rest on one distributor's published 600-piece price.

The largest gaps between this prototype and a product that can be sold are safety certification (UN 38.3 for transport, UL 2271 or EN 50604-1 for sale), a flame-retardant enclosure (proposal PROP-001), and tooling. Reaching a first 1,000-unit production run is estimated at 0.9 to 1.7 million USD over 18 to 30 months, most of it in certification test packs, tooling and inventory.

## Unit cost of goods by tier

| Category | 1 | 100 | 1,000 | 10,000 |
|---|---:|---:|---:|---:|
| Cells | $1,019 | $342 | $316 | $286 |
| BMS | $42.10 | $32.00 | $26.00 | $20.00 |
| Gateway board | $95.00 | $30.00 | $16.00 | $6.00 |
| Housing and insulation | $89.98 | $159 | $33.00 | $21.00 |
| Power path and harness | $216 | $80.00 | $55.00 | $42.00 |
| Hardware and consumables | $341 | $45.00 | $25.00 | $15.00 |
| Assembly labour | $875 | $140 | $22.50 | $7.20 |
| Test, packaging, shipping prep | $0.00 | $35.00 | $20.00 | $14.00 |
| **Total** | **$2,678** | **$863** | **$514** | **$411** |

## Verification status

Verified:
- Bill of materials complete and consistent: 6-gate script check: every part BUY or BUILD, files on disk, assembly steps, CAD and schematic agree. PASS.
- Gateway circuit board: KiCad 10.0.8: 0 ERC errors, 0 DRC errors, 0 unconnected; Gerbers and turnkey PCBA package generated.
- Gateway firmware v0.1.0: Builds for ESP32-C3; 120 of 120 host unit tests pass, including the whole gateway against simulated BMS and bike bus.
- Printed parts: Meshes watertight; all 7 parts sliced in Bambu Studio; G-code checked by script (49.3 h, 1,523 g PETG).
- Electrical and thermal sizing: Hand calculations for current, voltage drop, fuse coordination and worst-case heating (no simulation).

On paper only:
- Fit in a real TS bay and lock engagement (closes in S0)
- Bike plug pin-out (closes in S0)
- Bus protocol on a TS (closes in S0)
- Gateway board built and brought up (closes in S0)
- Any cell brick or full pack (closes in S1)
- Fire behaviour of the enclosure (closes in S1)
- Vibration, drop, water ingress, abuse tests (closes in S2)
- Any certification (closes in S2)

## Stages

| Stage | Months | Capital | Basis |
|---|---|---|---|
| S0 Validate | 2–3 | $5,000–$15,000 | estimate |
| S1 Engineering build (EVT) | 3–5 | $40,000–$100,000 | estimate |
| S2 Design verification and certification (DVT) | 6–9 | $180,000–$380,000 | estimate |
| S3 Pilot production (PVT) | 4–6 | $250,000–$500,000 | estimate |
| S4 First volume run | 3–7 | $450,000–$700,000 | estimate |

## Compliance

- **UN 38.3** (Yes): Not started; $4,000–$12,000, 4–6 weeks [estimate]
- **UL 2271** (Yes for US sale): Not designed to pass yet (enclosure not FR); $15,000–$50,000, 10–12 weeks after UN 38.3 [estimate]
- **CPSC proposed rule on e-mobility batteries** (Proposed (June 2026 NPR)): Track; design for it now; —,  [documented]
- **EN 50604-1** (Expected by retailers and insurers): Not started; $8,000–$20,000, 8–10 weeks [estimate]
- **EU Battery Regulation 2023/1542** (Yes): Not started; needs an EU economic operator; —,  [documented]
- **UNECE R136 / R10** (To confirm with a homologation consultant for an aftermarket pack): Open question; —,  [assumed]
- **FCC Part 15** (Module pre-certified; radio off in firmware): Unintentional-radiator check needed for the board; $3,000–$8,000, 2–4 weeks [assumed]

## Risks

- Thermal runaway in the field: Quality cells, BMS plus independent fuse, FR enclosure, certification, conservative 45 A limit
- Does not fit or talk to some bikes: Stage 0 measurements on several bikes and model years before tooling
- Cell price and availability: Qualify two cell models; hold-fits geometry for both; forward-buy at volume
- Certification takes longer or fails first time: Pre-assessment, design to the standard from S1, build spare test packs
- Brand changes the bus protocol or locks out third-party packs: Gateway firmware is field-updatable; sniffer mode; keep the protocol layer separate
- Trademark or design-right claim: No branding, plain housing, freedom-to-operate search before launch
- Product liability claims: Certification, insurance, traceability by serial and cell lot
- Small addressable market: Size the installed base first; extend the platform to related 60 V models

## Sources

- S-1: SSB-1 build package README and BOM check (project file build/README.md) 
- S-2: SSB-1 bill of materials and purchase list with per-line supplier prices (build/build.json, prototype/bom/bom.csv) 
- S-3: Doctibike: Batterie moto Super SOCO TC/TS 60V 30A https://doctibike.com/en/batteries-for-motorbikes-and-electric-scooters/3707-batterie-moto-super-soco-tc-ts-60v-30a.html
- S-4: NKON: Samsung INR21700-50S quantity prices https://www.nkon.nl/en/rechargeable/li-ion/21700-20700-size/samsung-inr21700-50s-5000mah-35a.html
- S-5: Epec Engineered Technologies: Battery pack certifications, what they cost, how long they take https://www.epectec.com/batteries/battery-pack-certifications.html
- S-6: Tritek: Battery certification explained (UL, EN, UN, CE, FCC, IEC) https://tritekbattery.com/battery-certification-explained-ul-en-un-ce-fcc-iec/
- S-7: JJR Lab: How much does UN38.3 testing cost https://www.jjrlab.com/news/how-much-does-un383-testing-cost.html
- S-8: Formlabs: How to estimate injection molding cost https://formlabs.com/blog/injection-molding-cost/
- S-9: Exponent: CPSC proposes new requirements for e-mobility batteries (2026-07-01) https://www.exponent.com/article/cpsc-proposes-new-requirements-e-mobility-batteries
- S-10: Conformance: Batteries Regulation (EU) 2023/1542 https://www.conformance.co.uk/ce-directives-information/batteries-regulation-eu-2023-1542
- S-11: Vmoto Soco technical page for the TS, and blueprint evidence E-03/E-04/E-06 (project file evidence-log.md) https://shop.vmotosoco.com/pages/info-tecniche-ts
- S-12: SSB-1 safety and compliance notes (project file prototype/safety-and-compliance.md) 
- S-13: PROP-001 flame-retardant enclosure proposal (project file changes/proposals/) 
- S-14: ECO-001 cell change to Samsung 50S, revision B (project file changes/ECO-001.md) 
- S-15: SSB-1 electrical calculations and thermal note (project files prototype/electrical/calculations.md, prototype/thermal/thermal-note.md) 
- S-16: SocoLink gateway firmware v0.1.0 test report (project file prototype/software/test-report.md) 
- S-17: Gateway PCBA package status, KiCad 10.0.8 checks (project file kicad/fab/pcba/.../status.json) 
- S-18: Vmoto Ltd 2025 annual report summary https://www.sustainabilityreports.com/vmoto/2025/annual-report
- S-19: stprograms/SuperSoco485Monitor protocol notes (MIT), blueprint evidence E-08 https://github.com/stprograms/SuperSoco485Monitor
