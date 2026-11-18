# AON-1 build package

What you are building: a 3U CubeSat, 100 x 100 x 340.5 mm [3.94 x 3.94 x 13.41 in], about 1.6 kg current best estimate. Bought parts and stock about $12,941 including spares (estimates, not verified against supplier pages). About 40 hours of assembly and test once parts are in hand. Skills: fine-pitch soldering checks, torque-controlled small fasteners, ESD and clean handling.

Stages
1. Purchase: `1-purchase/purchase-list.csv` (27 lines). Every line still needs its supplier page checked and the SKU picked; `mcmaster-cart.csv` lists the McMaster lines with quantities.
2. Print: none. The structure is machined aluminium, so there is no G-code in this project.
3. Fabricate: machined parts AON-101..107 (STEP in `3-fabricate/machined`, drawings in `drawings/AON-1-drawing-set.pdf`), cut files in mm and inch in `3-fabricate/cut`.
4. Assemble: 7 illustrated steps, matching `assembly.json` one to one (AON-003 sheet).
5. Firmware and test: EOR-1 host build and tests; the flight build needs the E03 board.

Blockers
- Boards E01, E02, E03, E04, E05, E06, E07: KiCad layouts and RushPCB turnkey packages are not made yet (KiCad runs on the user's PC).
- Purchase lines: prices are estimates and no supplier page was fetched.

Cross-check: PASS, every assembly part is a purchase or fabricate line and the step count matches assembly.json.
