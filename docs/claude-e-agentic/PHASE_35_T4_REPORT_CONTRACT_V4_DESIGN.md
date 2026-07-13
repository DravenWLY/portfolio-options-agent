# Phase 35-T4 — Report Contract v4: The Trade-Centered Markdown Document

Status: design accepted — Claude G review **PASS as amended**. Decisions D1–D6
recorded (D2 amended: the portfolio-claim gate additionally blocks
comparative-magnitude word forms — see §3.2 amendment). Riders folded into §8
on 2026-07-09 (marked "Claude G rider"): R1 comparative-magnitude vocabulary;
R2 section-keyed narrative statements — **revised same day per Claude G's
rider-confirmation check**: the keying must be frozen structurally (engine →
T3a adapter → additive structured field on the frozen derived section →
composer reads frozen groups; semantic group definitions, no fixed indices;
no parse, no recompute, honest-unavailable for pre-T5 packages); R3a the §2
risk-note example's "should" is not an acceptable eval exemplar (imperative
"re-verify" is); R3b TC4 tolerates the engine's current always-$0 "Other" row.
Implementation authorized: the §8 prompt goes to Claude G for
rider-confirmation, then to Codex C (P35-T2/T3/T3a/T3b all merged, PASS).
Owner: Claude E (design), Codex C (P35-T5 implementation after PASS). Reviewer:
Claude G. Binding inputs (in order): P35 contract
(`docs/codex-b-architecture/PHASE_35_REAL_ACCOUNT_TRADE_IMPACT_PROTOTYPE_CONTRACT.md`,
founder criteria + D1–D6); P35-T1 methodology as amended
(`docs/claude-h-knowledge/P35_T1_TRADE_IMPACT_METHODOLOGY.md`, §5 narrative
core, §0 layering, §4 thresholds, §7 ban list, D-R1/D-R2); current v3 machinery
(`orchestration/tool_mediated_runner.py`, `auditing/live_report_gates.py`,
`reports/display_labels.py`); T18 rejection evidence
(`reports/agent-team-test-results/20260708T13*.md`). Design against the T1 memo
outputs, not against in-flight T3 code.

Locked question (unchanged): **"What would I be ignoring if I acted manually
now?"** — answered portfolio-relative. No verdicts, no advice, ever.

---

## 0. Why T18 was rejected, precisely (what v4 must fix)

The T18 artifact is technically clean (numbers gate-verified, categories
checked) yet fails all four founder criteria — because v3 built a *role-
findings dump*, not a *document*:

1. **Not trade-centered.** Title is "Tool-Mediated Saved Agent Team Report".
   Nothing states "you are buying 40 NVDA and here is what it does to your
   portfolio." The content is freshness categories and indicator values.
2. **Not account-aware.** No positions, no before/after exposure, no overlap.
   (This is exactly what the T3 engine now produces and v4 must feature.)
3. **Token-polluted.** Raw snake_case in user prose: `Eod_not_live_prices.`,
   `Options_exposure_summary is not available.`, and bare caveat-code lists
   (`selected_context_scope, account_level_feasibility_not_evaluated, …`) —
   from both the LLM live reports and deterministic text.
4. **Poorly formatted.** The PM synthesis is one wall-of-text paragraph with
   `###` headings mashed inline; each live report is dumped *inside* that
   paragraph **and** repeated verbatim under Per-Role Findings. Duplicated,
   unreadable, no lede, no trade in the title.

v4's thesis, aligned with the founder read and D-R2: **the document is a
deterministic, backend-composed trade-review narrative.** The T1 §5 statements
and T3 exposure tables are the spine and carry all the value. Live role prose
becomes a short, gated, token-scrubbed *supporting note* — never the main
content, never a duplicated dump.

## 1. The document (deliverable 1)

One markdown report a busy investor reads top to bottom. `final_synthesis_
markdown` becomes this whole document (composed deterministically, §4).
Every heading and label is display-language; **no token, code, or snake_case
string ever appears in prose** (§3.4 gate). Worked example uses the T1
synthetic portfolio; all values shown are illustrative.

### 1.1 Outline with exact heading text

```
# Trade review: Buy 40 NVDA — Fidelity Individual — July 8, 2026
                (verb + qty + symbol — reviewed account nickname — report date)

_Read-only analysis for your manual review. Not advice, not a recommendation,
and not an instruction to trade._                         ← standing italic lede line

## Summary
<1 short paragraph, plain language: what trade, which account, as-of dates,
and the one-line headline of the exposure finding.>

## If you proceed
<the T1 §5 statements 1–7, in order, as complete sentences/short paragraphs;
deterministic; renders $ and % normally (D-R2). Each is present or explicitly
named as a gap.>

## Exposure before and after
<T3 tables. Asset-class / single-name table (Before $, Before %, Trade Δ$,
After $, After %); then the sector/industry table with the coverage note
(T1 §2.3) rendered as plain prose beneath it.>

## Reference points
<T1 §4 threshold findings that fired (crossings AND already-above), one
§4.3-shaped sentence each; then the standing reference-point disclaimer once.>

## Market context
<T16 values as a compact table (indicator, value, as-of), the eod_not_live
caveat in plain words; then — if it survives its gate — the technical role's
one short connective note (§2).>

## Risk and scope notes
<deterministic scope/freshness/feasibility caveats in plain language; then —
if it survives its gate — the risk role's one short connective note (§2).>

## What was not reviewed
<T1 §5 statement 8: fund holdings not reviewed, earnings/dividends, taxes,
out-of-scope accounts, prices are end-of-day not live, any coverage gap.>

## Verify before acting
<T1 §5 statement 9: 2–4 imperative-verification items (verify/check/confirm
only, per T1 §7 allowed imperatives).>

---
_Reference points are common rule-of-thumb levels used to organize this report.
They are not personalized limits, targets, or recommendations. Figures are
from your <date> account sync and <date> end-of-day prices; end-of-day prices
are not live. Source: FMP end-of-day data (internal evaluation use). Not
investment advice._                                       ← standing footer
```

### 1.2 Which blocks are deterministic vs LLM-authored

| Block | Author | May contain $/%? | Gate |
| --- | --- | --- | --- |
| Title, lede, Summary | deterministic | yes | display-token (§3.4) |
| If you proceed (§5 statements) | deterministic | yes (D-R2) | display-token, §7-ban, reconciliation (§3.5) |
| Exposure tables + coverage note | deterministic | yes | display-token, reconciliation |
| Reference points + disclaimer | deterministic | yes | display-token, §7-ban, §4.3 shape |
| Market context table + caveat | deterministic | yes | display-token |
| Market context **connective note** | LLM (technical) | **no** (symbol-free) | full v3 live gate + token + portfolio-claim (§3) |
| Risk/scope caveats (plain prose) | deterministic | n/a | display-token |
| Risk **connective note** | LLM (risk) | **no** | full v3 live gate + token + portfolio-claim |
| What was not reviewed, Verify | deterministic | yes | display-token, §7-ban |
| Footer | deterministic | yes | fixed text |

The layering is exactly D-R2: deterministic prose renders `$1,234` / `12.3%`
freely; the two LLM notes stay symbol-free and gated. Contract v4 keeps this
split structurally so the live-gate `%`/`$` scans never fire on backend text
(they already only run on `live_report_markdown`, never on deterministic
fields — confirmed in `live_report_gates.py`).

## 2. Role redefinition for v4 (deliverable 2)

With the deterministic narrative carrying trade size, exposure, overlap,
thresholds, and gaps, the live roles must **add connective interpretation of
their own envelope data or add nothing.** Restatement of portfolio math is
prohibited (it is deterministic-owned and higher-stakes). The v3 six-section
role reports are **retired**; each live role now produces at most **one short
titled note** (2–4 sentences), or is dropped.

- **Technical Analyst → "Market context" note.** Adds: how the reviewed
  symbol sits in its own recent price context relative to the trade's price
  basis — e.g. the close relative to the 52-week range and to its moving
  averages, using the backend-derived relationship *labels* ("above the
  200-day average") and the price basis, all already in its envelopes. May
  name indicator values **only** as already gated (numeric gate). **Must not**
  mention portfolio percentages, exposure, concentration, or the account.
  Locked lens: what a manual reviewer glancing only at today's price would
  miss about the saved end-of-day context. No trend prediction, no target,
  no support/resistance (existing scans).
- **Risk Manager → "Risk and scope" note.** Adds: which saved scope/freshness
  caveats most affect trust in *this* trade's inputs, in plain connective
  language — e.g. that the position figures come from a sync that may be
  stale — "re-verify the exposure math at your broker" (Claude G rider R3a:
  the imperative verification form is the compliant exemplar; "should" is a
  T1 §7 ban term and must not be encoded as acceptable output in any eval).
  Its envelopes carry no
  numerics, so the note stays number-free by construction. **Must not**
  restate the exposure deltas or thresholds (deterministic-owned).
- **Fundamentals / News Analysts.** With no value-carrying envelopes and the
  deterministic "What was not reviewed" section already naming their gaps,
  their live notes add nothing and are **not requested in v4** (skipped;
  their gaps are covered deterministically). Reduces token-risk surface and
  the T18 "no reviewed public evidence" noise. (Claude G decision D4.)
- **Portfolio Manager → document composer** (§4), not a role note.

Prompt vNext (`p35-role-note-v1`): same envelopes-only input; the six-section
structure contract is replaced by a **single-section note contract**
(one heading = the section's display title, 2–4 sentences, no table, no
lists, no headings-within); all v3 prohibitions retained; new explicit
instructions: plain language only (no snake_case, no code words, no field
names), no portfolio/account/exposure/percentage references, symbol-free.

## 3. Gate evolution (deliverable 3)

v3 gates stay and extend. Every existing scan is retained byte-identical; v4
**adds**, never weakens. Order over a live note: structure → existing hard
blocks → numeric → category → **portfolio-claim (new)** → **display-token
(new)**. Any failure ⇒ drop the note, keep the deterministic document intact,
record flag; never re-pass.

### 3.1 Recommendation on engine-derived values in live prose

**Recommendation: live roles may NOT reference engine-derived portfolio
values in any form — word or digit.** Rationale:

1. The exposure/concentration numbers are the report's highest-stakes claims
   and are already stated perfectly by the deterministic narrative; an LLM
   restatement adds duplication and mismatch risk for zero information gain.
2. The numeric gate extracts *digit* tokens; **spelled-out numbers ("seven
   percent") evade it** (a known v3 limitation). Allowing word-form portfolio
   percentages would create an *ungated* channel for exactly the most
   dangerous unverified claim ("about ten percent of your portfolio"). That
   is unacceptable, so word-form portfolio values must be affirmatively
   blocked, not permitted.
3. D-R2 already assigns the portfolio narrative to the deterministic layer.

### 3.2 New portfolio-claim gate (mechanics)

A live note is dropped if it references portfolio-relative magnitude, in digit
or word form. Deterministic check over the note text:

- **Percent/dollar-of-portfolio phrasing**: match `percent|per cent|%|\$|
  dollars?` within a small window of `portfolio|holdings|position|exposure|
  allocation|account|cash`; OR any comparative-magnitude word form —
  `double|triple|halve|most|majority|bulk|dominant|concentrat*` (stem match
  covering concentrated/concentration) — within that same window (Claude G
  rider R1 / D2 amendment: "this would roughly double your chip exposure" is
  a portfolio claim with no cardinal, so digit+cardinal alone leaves it
  ungated); OR any spelled-out cardinal
  (`one|two|…|ninety|hundred|thousand|…`) within that same window. Match ⇒
  drop, flag `portfolio_claim_blocked`, warning `live_portfolio_claim_dropped`.
- Because deterministic exposure values are **not** in a live role's envelope
  allowed-set, any *digit* portfolio value is already caught by the numeric
  gate; this new gate closes the *word-form* hole for the portfolio-claim
  vocabulary specifically (a targeted list, not a general spelled-number ban,
  to avoid false drops on "two moving averages").

The numeric gate's allowed-set is therefore **unchanged** — still each role's
own envelope values (T16 market context for technical; none for risk). No
exposure values are added to any live allowed-set. (Claude G decision D3.)

### 3.3 T1 §7 ban list joins the hard blocks (instruction-vs-description nuance)

The T1 §7 vocabulary (overweight, buy, sell, hold, trim, rebalance, should,
consider, recommend, safe, healthy, excessive, too concentrated, well
diversified, opportunity, attractive, cheap, expensive, likely/unlikely,
probability, target, support, resistance, yield, annualized, guaranteed, …)
is added to the prohibited-phrase set applied to **all** generated prose
(deterministic narrative *and* live notes). Per the T1 status note, the
add/trim/rebalance bans are **instruction-form only**: the matcher targets
imperative/second-person constructions (`\b(add|trim|rebalance)\b` preceded by
"should/consider/you"/ sentence-initial imperative), NOT descriptive use
("would add a new position"). Exact matcher spec is Codex C's to implement to
this rule; eval pairs from T1 §7 pin it (§6). Allowed imperatives
(verify/check/confirm/review/re-sync/compare) are whitelisted.

### 3.4 Display-token gate over the whole document (the T18 fix)

The fail-closed `find_internal_display_tokens` scanner (T2, already in
`display_labels.py`) runs over **every user-visible prose field of the
assembled document** — title, lede, all deterministic sections, and each
surviving live note — as the final gate. Any internal snake_case/code token
(e.g. `eod_not_live_prices`, `options_exposure_summary`,
`account_level_feasibility_not_evaluated`) ⇒ that source block fails:

- a live note containing a token is **dropped** (flag `display_token_blocked`);
- a **deterministic** block containing a token is a build error the eval
  suite must catch (the deterministic renderer must emit only display labels
  via `display_label_for_code` / `replace_internal_display_tokens`); the
  document must never ship a token, so the whole-document display validator is
  fail-closed and unit-tested against the T18 token inventory.

### 3.5 Reconciliation gate (T1 §7 test-hook d)

Every percentage in the deterministic narrative must reconcile to the exposure
tables at one-decimal precision, and every threshold crossing in the T3
findings must have a matching §4.3-shaped sentence with no evaluative
adjective in that sentence. Deterministic check comparing narrative-emitted
values against the T3 finding set (both backend-owned, so this is an internal
consistency assertion, not an LLM check). Mismatch ⇒ build error (eval-caught).

## 4. PM synthesis v4 (deliverable 4)

**Stays deterministic** (recommended; consistent with D-R2 and T2 Q2 lineage).
The PM synthesis function is repurposed from "wall-of-text digest" into the
**document composer**: it lays out §1.1 top to bottom from audited blocks —
deterministic narrative (from the T3 engine outputs + T1 §5 statement
renderers), the exposure tables, threshold findings, the market-context table,
the deterministic scope/risk prose, and — slotted into the Market context and
Risk sections — the two live notes **iff** they survived every gate (embedded
verbatim, never paraphrased by code, never duplicated elsewhere). The
per-role-findings dump and the inline-heading wall-of-text are removed; live
notes appear exactly once, in their section. The whole assembled document
passes the display-token validator (§3.4) and the existing
`validate_agent_team_report_output` as a unit.

A live PM/document synthesis (model-written composition) stays **out of scope**
and would be its own reviewed slice with a cross-section consistency gate
(proposed T4B; not requested).

## 5. Formatting standards (deliverable 5)

Designed so the same markdown renders in the T12 exporter today and a frontend
markdown renderer later:

- **Headings:** `#` document title (one), `##` sections, no `###` in the
  document body (the v3 `###` role headings are gone; live notes carry a `##`
  section-owned title supplied by the composer, and the note body is plain
  sentences). No heading text contains a code/token.
- **Tables:** GitHub pipe tables, header row + `---` separator; right-aligned
  numeric columns (`---:`); every table preceded by a one-line plain-language
  caption and followed by its as-of/coverage note. Each exposure table visibly
  sums to ~100% (explicit "Other" row, T1 §1.5).
- **Bold:** only for the single headline fact in Summary and for reference-
  point *names* on first use; never for whole sentences.
- **Dates:** absolute long form ("July 8, 2026") in prose; ISO only inside
  table value cells where compactness matters (still gate-allowed as dates).
- **Fund naming:** ticker + full name on first mention ("SMH (VanEck
  Semiconductor ETF)"), ticker thereafter (T1 §5).
- **Numbers:** dollars to the nearest dollar, percentages to one decimal,
  deltas in words ("from 35.0% to 42.0%", never "pp"/"bps") — T1 §1.5.
- **Empty/unavailable:** when the engine reports data unavailable, the section
  renders an honest plain-language line ("Your account positions were not
  available for this run, so exposure could not be computed.") — never a blank
  section, never a token, never a fabricated value. Document must render
  honestly under partial data (boundary requirement).
- **Graphs:** out of scope for v1. Note where a chart would later attach: an
  exposure bar chart under "Exposure before and after" and a price-context
  sparkline under "Market context"; v4 leaves a stable heading anchor for each
  so a later frontend can slot an image block without a contract change.

## 6. Eval matrix (deliverable 6)

Offline, injected fake provider + hand-checked synthetic engine fixtures;
added to `test_tool_mediated_eval.py` + unit tests. Reuse the T1 worked
example as the golden fixture (`trade_impact_golden_v1`, synthetic).

**Founder-criteria cases:**

| ID | Asserts |
| --- | --- |
| TC1 trade-centered | title matches `Trade review: Buy 40 NVDA — Fidelity Individual — <date>`; "If you proceed" present with statements 1–7 |
| TC2 account-aware | exposure before/after table present with the NVDA new-position row and the semiconductor bucket 35.0%→42.0%; §2.4 overlap statement present |
| TC3 token-free | whole-document `find_internal_display_tokens` == ∅ (fixture seeds the exact T18 tokens upstream to prove they are translated, not leaked) |
| TC4 well-formatted | one `#`, section `##`s present in order, no `###` in body, every table has header+separator+≥1 row and an "Other" row summing ~100% |

**T1 §7 wrong/right pairs (each left string must never appear; right shape
must):** WR1–WR12 from the memo table, run as ban-scan + shape assertions.

**Gate regression (every still-applicable v3 case) + new gates:**

| ID | Injected live note | Must |
| --- | --- | --- |
| G-num | value not in envelope | numeric drop, deterministic doc intact |
| G-cat | "freshness is manual" vs fresh envelope (T18 sentence verbatim) | category drop |
| G-struct | wrong single-note structure | structure drop |
| G-port-d | "this is 7.0% of your portfolio" in a live note | `portfolio_claim_blocked` (digit) |
| G-port-w | "about seven percent of your portfolio" | `portfolio_claim_blocked` (word-form) |
| G-port-c | "this would roughly double your chip exposure" | `portfolio_claim_blocked` (comparative — Claude G rider R1) |
| G-tok | live note containing `eod_not_live_prices` | `display_token_blocked` |
| G-ban | live note "you should trim SMH" | prohibited-phrase drop; "would add a new position" (descriptive) passes |
| G-floor | all notes dropped | document renders complete deterministic narrative, no empty sections |
| G-recon | narrative % vs table % mismatch (fault injection) | reconciliation build-error caught |
| G-unavail | engine reports positions unavailable | honest unavailable prose, no token, no fabricated number, readback re-runs nothing |
| G-dr2 | deterministic narrative contains `$8,400` / `42.0%` | passes (no live-gate symbol scan on deterministic fields) |

Founder acceptance rubric (P35-T6, manual): reads top-to-bottom as a trade
review; the double-exposure finding is unmissable; zero code tokens; would a
busy investor understand it without a glossary.

## 7. Schema / artifact deltas (all additive)

- `final_synthesis_markdown` semantics change (now the full document); field
  type unchanged. `final_synthesis_authored_by` stays `deterministic_template`.
- Live notes: reuse `live_report_markdown` (now a single note, not six
  sections); no new field. v3 `ROLE_REQUIRED_HEADINGS` gains a v4 single-note
  variant behind the prompt version; the six-section contract is retired with
  its prompt version.
- New eval flags/warnings: `portfolio_claim_blocked` /
  `live_portfolio_claim_dropped`; `display_token_blocked` /
  `live_display_token_dropped` (display flag already exists in T2; reuse).
- `LIVE_PROMPT_VERSION` → `p35-role-note-v1`.
- No ToolResult/tier/allowlist/readback/chain changes. No frontend.

## 8. Codex C implementation prompt (P35-T5; issue after Claude G PASS + T3 merged)

```text
Agent: Codex C
Task: P35-T5 - Report contract v4: trade-centered markdown document + gate extensions
Mode: backend implementation; one task; depends on P35-T2, P35-T3, P35-T3a, P35-T3b
(all merged, reviewed PASS); stop for Claude G review after.

Design reference (binding): docs/claude-e-agentic/PHASE_35_T4_REPORT_CONTRACT_V4_DESIGN.md
PASS as amended by Claude G (decisions D1-D6, D2 amended; riders R1/R2/R3 folded in
below and marked), and the T1 methodology sections 4/5/7
(docs/claude-h-knowledge/P35_T1_TRADE_IMPACT_METHODOLOGY.md as amended).

Scope:
1. Document composer (deterministic) in the PM-synthesis path
   (orchestration/tool_mediated_runner.py summary/synthesis functions): assemble
   final_synthesis_markdown as the section-1.1 document top to bottom from the T3
   engine outputs (before/after exposure, sector/industry, coverage), the T1 section-5
   statement renderers, the T1 section-4 threshold findings + standing disclaimer,
   the T16 market-context table, deterministic scope/risk prose, and the two surviving
   live notes slotted once into their sections. Remove the per-role-findings dump and the
   inline-heading wall-of-text. Title = "Trade review: <verb> <qty> <symbol> - <account
   nickname> - <long date>"; account selected/labeled by nickname only (D1), with the
   nickname sourced from the reviewed scope_metadata account-display field - never
   string-constructed from account data. Deterministic prose renders $/% normally (D-R2).
2. CLAUDE G RIDER R2 (revised per rider-confirmation) - section-keyed narrative
   statements, frozen structurally. The composer runs at report-generation time over the
   FROZEN evidence package; keyed groups that exist only on the engine's live output do
   not survive the T3a/T3b freeze (which emits a flat detail_labels tuple). Therefore:
   (a) exposure_engine.py: expose the trade-impact narrative statements grouped
       SEMANTICALLY by document section - proceed_statements = every trade-impact
       statement EXCEPT the not-reviewed statement and the verify checklist (order
       preserved; the statement set is conditional - overlap adds statements,
       coverage/top-three are conditional - so groups are defined by statement role,
       never by fixed index or count); not_reviewed_statement = the not-reviewed
       statement; verify_statement = the verify checklist.
   (b) exposure_adapter.py (T3a): carry the three keyed groups into the frozen
       before_after_portfolio_impact derived section as a small ADDITIVE structured
       field; the existing flat detail_labels stay byte-identical alongside it.
   (c) Derived-section schema: only that additive structured field; preserve every T3b
       constraint over the richer structure - only the two approved derived-section keys
       (before_after_portfolio_impact, concentration_risk_drift), fail-closed readback
       re-validation, no recompute on readback.
   (d) Composer: consume ONLY the frozen structured groups. Never re-run the engine at
       generation/readback time, never slice by index, never parse the flat labels or
       split on markers. Frozen packages saved before this slice (no structured field)
       render the honest-unavailable path for the affected blocks - not a parse fallback.
   Do not invent a different keying scheme. Items (a)-(c) are the ONLY permitted changes
   to exposure_engine.py, exposure_adapter.py, and the derived-section schema in this
   slice; everything else in those modules stays untouched.
3. Live role notes: prompt version p35-role-note-v1; single-section note contract per
   design section 2 (technical "Market context" note, risk "Risk and scope" note; skip
   fundamentals/news); retire the v3 six-section contract; envelopes-only input unchanged;
   plain-language + symbol-free + no-portfolio-reference instructions added.
4. Gate extensions in auditing/live_report_gates.py (all additive, fail-closed, never
   re-pass, order per design section 3): keep v3 structure/numeric/category byte-identical;
   add the portfolio-claim gate (section 3.2 as amended) blocking portfolio-magnitude
   phrasing in THREE forms within the portfolio-context window
   (portfolio|holdings|position|exposure|allocation|account|cash):
   (a) digit forms; (b) spelled-out cardinals; (c) CLAUDE G RIDER R1 / D2 AMENDMENT -
   comparative-magnitude word forms: double | triple | halve | most | majority | bulk |
   dominant | concentrat* (stem match covering concentrated/concentration/concentrating).
   Rationale to preserve in a code comment: "this would roughly double your chip exposure"
   carries no cardinal, so digit+cardinal alone leaves it ungated. Keep it a targeted
   window vocabulary, NOT a broad ban (market-context wording like "two moving averages"
   must not trip it). Flags: portfolio_claim_blocked / live_portfolio_claim_dropped.
   Also: run find_internal_display_tokens over each live note -> display_token_blocked;
   add the T1 section-7 ban list to the prohibited-phrase set for ALL generated prose with
   the instruction-vs-description matcher (section 3.3; descriptive "would add" passes;
   allowed imperatives verify/check/confirm/review/re-sync/compare stay whitelisted).
   Numeric allowed-set UNCHANGED (no exposure values added to any live allowed-set).
5. Whole-document display-token validator (fail-closed) + reconciliation check
   (section 3.5) applied to the assembled document; deterministic renderer must emit only
   display labels (display_label_for_code / replace_internal_display_tokens); a token or a
   %-vs-table mismatch in deterministic output is a build error the tests catch.
6. Honest-unavailable rendering per design section 5 for every section when the engine
   reports data unavailable (no blank sections, no tokens, no fabricated values).
7. Fixtures + evals: trade_impact_golden_v1 (synthetic, the T1 worked example) and
   test cases TC1-TC4, WR1-WR12, G-num/cat/struct/port-d/port-w/tok/ban/floor/recon/
   unavail/dr2 in tests/services/agent_eval/test_tool_mediated_eval.py + unit tests; G-cat
   uses the T18 sentence verbatim. Add G-port-c (rider R1): injected live note "this would
   roughly double your chip exposure" -> portfolio_claim_blocked. Two rider-R3 rules:
   (a) no eval fixture may encode "should"-form prose as acceptable output - the compliant
   exemplar for the risk note is the imperative "re-verify the exposure math" ("should" is
   a section-7 ban term and must FAIL where asserted); (b) the TC4 sums-to-~100% assertion
   must tolerate the T3 engine's current always-$0 "Other" row until coverage-aggregation
   lands (assert the row exists and totals reconcile, not that "Other" is nonzero).
   Rider R2 evals: (c) keyed-groups round trip - the structured groups survive
   freeze -> saved-report readback and the composer consumes them with the engine spied
   to prove no re-run at generation/readback time; (d) a pre-T5 frozen package (fixture
   without the structured field) renders the honest-unavailable path for the affected
   blocks, with no parse fallback and no exception. Real derived values never enter
   fixtures/tests (D2 of the P35 contract).

Boundaries: LLM never computes/adjusts numbers or picks tools/models/symbols; deterministic
floor and all existing validators survive byte-identical; no new sources; no LangGraph/MCP/
TradingAgents; no frontend; schema changes additive only (design section 7 plus the
rider-R2 structured field); exposure_engine.py, exposure_adapter.py, and the derived-section
schema change ONLY per rider R2 items (a)-(c), with all T3b constraints preserved
(two approved derived-section keys only, fail-closed readback re-validation, no recompute
on readback); saved reports reopen frozen state and readback re-runs nothing.

Verification: cd backend && ./.venv/bin/python -m pytest tests/services/agent_team
tests/services/agent_eval tests/services/trade_review -q;
tests/unit/test_report_agent_schemas.py -q; git diff --check.
Report counts. Return per docs/shared/AGENT_REPORT_FORMAT.md with PASS/BLOCKED ask for Claude G.
```

## 9. Decisions requested from Claude G (PASS/BLOCKED ask)

- **D1** — The document is deterministically composed; PM synthesis becomes
  the document composer (§4). Confirm (vs a live-authored document, deferred).
- **D2** — Live roles may **not** reference engine-derived portfolio values in
  any form; the new portfolio-claim gate blocks digit *and* word forms (§3.1–
  3.2). Confirm the recommendation and the targeted word-form vocabulary
  approach (vs a broad spelled-number ban).
- **D3** — Numeric allowed-set stays each role's own envelope values only; no
  exposure values enter any live allowed-set. Confirm.
- **D4** — Fundamentals/News live notes are dropped in v4 (their gaps are
  covered deterministically). Confirm, or direct that they stay.
- **D5** — T1 §7 ban list applies to deterministic narrative *and* live notes,
  with the instruction-vs-description matcher (add/trim/rebalance = imperative
  only). Confirm the matcher rule so Codex C does not substring-ban
  descriptive use.
- **D6** — §2.4 overlap wording: adopt the T1-preferred "semiconductor ETFs
  commonly hold NVDA" category-knowledge form (backend fixed text, D-R1), or
  the zero-category-knowledge fallback ("SMH may itself hold NVDA; its
  holdings were not reviewed")? T1 left this to review.

**Ask: PASS (issue the §8 prompt to Codex C once T3 merges) or BLOCKED with
the specific section to rework.**
