# Supply and change: keep every purchase line orderable, and every change tracked

Parts sell out, get discontinued and change price between the day the package is written and the day someone orders. A build package is only finished if the builder can still get every part, and if any substitution, cheaper part or redesign is carried through the whole design and recorded. This file sets the rules. The tool is `tools/supply/supply.js` (Node 18+, no dependencies). The Anatomy app's Build tab uses the same tool for its stock badges, alternates, "sold out or changed?" button and change log.

Never place an order, fill in a checkout or create an account at a seller. The user orders.

## 1. Quantities are traced to the design

Every purchase line records the quantity the design needs and where that number comes from, separately from the order quantity. Write it in `build/1-purchase/supply.json` under `lines.<LINE>.need`:

```json
"E-1": { "need": { "qty": 102, "expr": "17*6", "spares": 4,
  "basis": "17S6P pack: 17 series groups x 6 in parallel (params.py N_S, N_Y) = 102; order 106 = 102 + 4 spares for weld practice" } }
```

- `expr` is the design count as arithmetic (series × parallel, fasteners × places). The audit evaluates it and fails if it does not equal `qty`.
- For parts sold by the spool, roll, sheet or length, give `per_unit` and `unit` (`"per_unit": 1000, "unit": "g"` for a 1 kg spool). The audit then compares amounts, not counts.
- The order quantity is the need plus spares and pack rounding, and the line's notes say why (`+2 spares`, `pack of 100`, `2 x 1 m, cut 4 x 308`).

`node supply.js <project> audit` writes `build/1-purchase/qty-audit.md`. It exits 1 if any line orders less than the design needs. Lines it cannot trace are marked CHECK. Fix every FAIL and CHECK before you hand off. When the user questions a quantity, answer from the `basis`.

## 2. Each line has its requirements and vetted alternates

For every BUY line, `supply.json` holds:

- **`requirements`**: what any substitute must meet, derived from the design and not from the current part's datasheet. Each requirement has a `key`, a `min`, `max` or `eq` value, and a `why` that names the file and number it protects. For example: `diameter_mm max 21.6, because the printed pocket is 21.9 mm (params.py POCKET_D)`, or `cont_discharge_A min 9.4, because the 45 A BMS limit over 6 in parallel is 7.5 A, kept under 80 %`. Cover the following:
  - fit: dimensions, footprint, pinout, thread
  - ratings: voltage, current, power, temperature
  - interface: connector mate, protocol, logic level
  - anything a calculation in the package depends on
- **`primary`**: `specs` (the same keys) and `stock`.
- **`alternates`**: an array. Each entry has `id` (`<LINE>-A1`…), `supplier`, `url`, `mfr`, `mpn`, `unit_price` (at the quantity needed), `specs`, `notes`, and `same_part: true` when it is the identical MPN from another seller. An alternate that is not a drop-in also gets `engineering: {effort, changes[]}`, listing what in the design would change.

The minimum is another seller for every line, and an equivalent part from a second maker for anything critical, single-source or likely to sell out. That covers cells, BMS, MCU modules, motors, drivers, custom connectors and anything with no stock today. Take specs from the maker's datasheet, and say in `notes` whenever you used a reseller page instead.

`evaluate` checks each alternate against the requirements and sets its fit:
- `in-kind`: meets every requirement (or is the same MPN). It can be swapped in without touching the design.
- `needs-change`: fails at least one requirement. It can only be used through an engineering change (section 4).
- `unverified`: one or more specs are missing. Vet it before anyone relies on it.

Do not call an alternate "equivalent" because the headline numbers look close. A 21700 cell that is 0.2 mm wider than the pocket, or a 10 A cell where the design needs 9.4 A with margin, is not a drop-in. Say exactly which requirement it fails and what would have to change.

## 3. Stock is checked, and supply feedback is taken in

- `node supply.js <project> refresh [LINE ...]` checks every primary and alternate. It uses Shopify product data where it exists, then the schema.org offer on the page, then the page text. Sites that block automated checks (Digi-Key, Mouser and McMaster often do) come back `unknown`. In that case the last known status is kept, with a note that the re-check failed. The Build tab's **Check stock now** button runs the same refresh. When you check a page yourself (WebFetch, browser), write what you saw into `stock` with `via` saying how you checked and when.
- **User reports count.** When the user says a part is sold out, discontinued, back-ordered or has a new price, record it with `feedback LINE primary sold_out`. The Build tab's **sold out or changed?** button does the same. When the user finds a source themselves, add it with `candidate LINE URL "note"`. It is `unverified` until you vet it: read the listing and datasheet, fill in its specs, run `evaluate`, and tell the user plainly whether it is a drop-in.
- After any feedback, act on it. If there is an in-kind alternate in stock, offer the switch. If there is none, search for one (the same MPN at other sellers first, then equivalents). Only if nothing in-kind exists, propose engineered options with numbers (section 4).

## 4. Swaps and engineering changes go through the whole system

**Source switch (in-kind).** `node supply.js <project> swap LINE ALT_ID "reason"`, or **Use this source** in the Build tab, does the following:
- updates the line in `build.json`, `purchase-list.csv`, the supplier carts (removes it from the old cart and adds it to the new one) and the design's `bom.csv`, so a regenerated build.json keeps the change
- keeps the old source as an alternate, so it can come back
- recomputes the parts cost
- logs the switch in `changes/`

The same MPN from another seller is a `supplier` change and the revision stays the same. A different, in-kind MPN is a `part` change and raises the revision. The tool refuses to swap a `needs-change` alternate.

**Engineering change (ECO).** A change of part that fails a requirement, a cheaper or more efficient redesign, or any change to the design itself follows these steps:
1. `eco-open LINE ALT_ID "title"` writes `changes/ECO-nnn.md`. It contains the requirement check of the new part, and an impact list of every file in the project that mentions the old part, grouped by area: BOM and purchasing, CAD and 3D twin, drawings, G-code, PCB/PCBA, firmware, assembly guide, simulation, calculations. Its search terms are the MPN and its core token, so `INR-21700-P45B` also finds `P45B`. Add `terms` to the line in supply.json for other names the design uses.
2. Write the decision into the ECO: which parameters change, with the calculation behind each, and what it does to cost, performance, safety margin and build effort.
3. Change the **sources**: CAD parameters, schematic/PCB, firmware constants, calculations. Then regenerate every output from its script, never by hand:
   - STEP and STL
   - drawings (look at them)
   - G-code, then run the G-code check
   - the PCBA package if a board part changed
   - BOM and BOM check, build.json and carts
   - assembly guide, `assembly.json` and the 3D twin
   - simulator tests
4. Switch the purchase line with `swap LINE ALT_ID --force` once the design matches the new part, **before** regenerating the BOM and build package (swap writes `bom.csv`, so the regeneration then carries it; swapping afterwards loses the previous source and is refused). Project generators must keep `build/1-purchase/supply.json`, `changes/` and any PCBA package they did not make.
5. Run `eco-verify ECO-nnn`. It fails while any non-history file still uses the old part. History lines that say "was", "replaced", "alternate" or the ECO id are allowed. Zip packages are not searched, so rebuild them. Once it passes, it closes the ECO, raises the revision in `build.json` and `changes/changes.json`, and writes `changes/CHANGELOG.md`.
6. Report to the user: what changed, cost before and after, the new revision, and anything not verified.

**Cheaper or better design.** When the user asks for a better version, first propose up to three options with numbers, in `changes/proposals/`. Add part-level options to supply.json as alternates with an `engineering` note. Do not change the design until the user picks one (the Build tab's **Engineer this change** button starts the ECO). Examples: fewer cells in parallel when the current allows it, a cheaper cell that meets every requirement, a single board instead of two, a printed part instead of a machined one.

## 5. Gate before hand-off
- `audit` has no FAIL and no unexplained CHECK.
- Every BUY line has `requirements` (at least the ones that matter for fit and safety), at least one alternate seller, and for critical lines an alternate part. Each alternate has a fit.
- `refresh` was run. Lines with no source in stock are listed as open items in `build/README.md`, with the decision they need.
- No ECO is left open without a note saying why.
