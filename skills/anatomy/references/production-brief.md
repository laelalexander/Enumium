# Engineering and Manufacturing Summary: prototype to production

Every hardware project ends with this report. It is written for two readers who were not part of the design work: an **investor** deciding whether to fund the next stage, and a **manufacturer** deciding whether and how to build it. It answers five questions plainly:

1. What is this product, and what problem does it solve for whom?
2. What has actually been built and tested, and what exists only on paper?
3. What does one unit cost now, and what would it cost at 100, 1,000 and 10,000?
4. What has to change, be certified and be paid for to get there, and in what order?
5. What could go wrong, and how is each risk retired?

The Anatomy app shows it on the **Production** tab and its **Prepare production brief** button asks for it. Produce it after the build package (`build-package.md`), and refresh it whenever the design, prices or plan change.

## Honesty rules (these come before polish)

- **Every figure has a basis tag**, the same evidence idea as the blueprint:
  - `measured` / `observed`: seen on this project (a test log, a slicer report, a checked file).
  - `quoted`: a written price or quote from a named supplier, with the date.
  - `documented`: a published source (datasheet, standard, regulator, published price list).
  - `estimate`: reasoned from stated inputs; the note says how.
  - `assumed`: a placeholder. It must be replaced before anyone relies on it, and the report says so.
- `quoted` and `documented` figures carry a source ID that resolves to the sources list (title, URL or project file, date read). The generator fails the check otherwise.
- **Status is two lists, never one:** *verified* (done and checked, with how) and *on paper only* (not built, not tested, with the stage that closes it). If no hardware exists, say "nothing has been built" in the executive summary.
- No hype words ("revolutionary", "disruptive", "guaranteed"), no invented market sizes, no implied endorsement by a named company. If market size is unknown, list it under "not yet established" and say where to get it.
- Readiness uses TRL and MRL levels with one sentence of justification each, marked `estimate`.
- Costs are per unit of cost of goods. One-time costs (tooling, certification, fixtures) are listed separately and also shown spread over each tier, never hidden inside unit cost.
- State the disclaimer in the report: not an offer of securities, not a quotation, not legal advice. Partner names are candidates for quotes, not endorsements, unless contacted.
- Dual units everywhere a physical quantity appears: mm [in], kg [lb], °C [°F]. The generator converts any spec given as `{"v": …, "u": "mm"}`.

## Research to do before writing

- **Prototype cost** from `build/build.json` and `bom/bom.csv` (`quoted`, dated). Note where pack sizes inflate the one-off figure.
- **Volume prices** for the top cost lines (usually 80 % of cost sits in 5 lines): look for published quantity breaks (distributor price tiers, LCSC/Digi-Key/Mouser breaks, published volume lists). Use them as `documented`; extrapolate past the last break as `estimate` and say so.
- **Process change per tier** for each BUILD part: FDM → vacuum casting or SLS (about 10–500), → aluminium injection tooling (about 1k–10k), → steel tooling (10k+); hand welding → fixtures → automation; bought module → custom board. Tooling costs from published ranges are `estimate` and say "get a quote".
- **Compliance** for the product type and target markets. Typical lines: batteries UN 38.3, UL 2271 / UL 2849 / UL 2054, IEC 62133-2, EN 50604-1, EU Battery Regulation 2023/1542; electronics FCC Part 15, CE (EMC, LVD, RED), RoHS, REACH, WEEE; mains products UL/IEC 62368-1 or 60335; vehicles UNECE regulations; food contact, medical (FDA, MDR) and toys have their own regimes. Give cost and time ranges with sources; say which test samples are needed (they cost money too).
- **Market evidence**: the closest existing product's price and availability, the problem in the user's words, any published sales or installed-base data. Mark anything weak as weak.
- Search the web for current figures where possible and record the date read. If the network is blocked, use `assumed` and list the figure under open questions.

## Files

```
production/
  production.json         the data, written by you (schema below)
  production-brief.html   generated: self-contained, prints to PDF, charts inline
  production-brief.pdf    generated (Letter, page numbers) when Chromium/Chrome/Edge or playwright is present
  production-brief.md     generated plain-text version
  cost-model.csv          generated: every cost line at every tier, with basis and source
  brief-check.md          generated: PASS/FAIL, figures counted by basis
```

Generate with `python <skill>/tools/production/make_brief.py <project-dir>` (standard library only). It exits 1 and writes nothing but `brief-check.md` if a figure lacks a basis, a `quoted` or `documented` figure lacks a source, a source ID does not resolve, or a section is missing. Fix and re-run until PASS, then open the PDF and look at every page (charts, tables cut across pages, labels) before handing it over.

## production.json schema

Top level: `schema` (1), `title`, `short_title`, `product`, `revision`, `date`, `prepared_by`, `currency`, `fx` (`{"EUR_USD": 1.16, "note": "…"}`), `audience_note`, then the sections below. Any object may carry `basis` and `source` (one ID or a list).

| Section | Shape |
|---|---|
| `executive_summary` | `one_liner`, `paragraphs[]` (3–4: what it is, what is verified vs not, cost now vs at volume, what it takes to reach production), `key_numbers[] {label, value, basis, source}` (4–6), `asks[]` (what the project needs: money for which stages, which kind of partner) |
| `problem` | `paragraphs[]`, `evidence[] {claim, basis, source}`, `not_known[]` |
| `product` | `description`, `specs[] {name, value \| v+u, basis, source}` |
| `status` | `trl {level, why, basis}`, `mrl {…}`, `verified[] {item, how, basis, source}`, `on_paper[] {item, why, closes_in}` |
| `cost_model` | `intro`, `tiers` ([1, 100, 1000, 10000]), `categories[] {name, lines[] {item, qty_per_unit, unit_cost {"1": …}, basis (one tag, or one per tier), source, note}}`, `price_context[] {item, price, basis, source}`, `nre[] {item, from_tier, cost_low, cost_high, basis, source, note}` |
| `dfm` | `[] {part, prototype, production, change, tooling_low, tooling_high, from_tier, basis, source}` |
| `supply_chain` | `[] {item, prototype, volume, alternates[], lead_time, risk}` (take alternates and stock from `supply.json` when it exists) |
| `compliance` | `[] {standard, scope, markets, required, status, cost_low, cost_high, time, basis, source}` |
| `partners` | `[] {process, prototype, candidates[], note}`, plus `partners_note` |
| `risks` | `[] {risk, likelihood, impact, mitigation, stage}` (take from `80-gaps-and-risks.md` and add commercial ones) |
| `stages` | `[] {id, name, goal, exit[], units, months_low, months_high, capital_low, capital_high, basis, includes[]}`; the usual set is S0 Validate, S1 Engineering build (EVT), S2 Design verification and certification (DVT), S3 Pilot (PVT), S4 First volume run. Add `capital_note`. |
| `ip` | `[] {topic, note}` (clean-room basis, licences of anything reused, trademarks, patents searched or not, own IP candidates) |
| `assumptions` | `[] {id, text}`; `open_questions[]` |
| `sources` | `[] {id, title, url?, accessed, note?}`; project files are sources too (give the path) |

Rules the numbers must keep:
- Tier 1 equals the build package's real order cost (minus accessories you exclude, said in `intro`), plus labour at a stated rate.
- The executive summary's figures match the tables (the generator does not re-check prose: do it yourself).
- Stage capital adds up to the total quoted in the summary.

## Quality bar

The SSB-1 sample in `examples/ssb1-production/` is the bar: 14 sections, cost chart by tier, timeline chart, every figure tagged, 19 sources, check PASS, an 18-page PDF a manufacturer can quote from and an investor can read in ten minutes (the executive summary and key numbers on the first two pages).
