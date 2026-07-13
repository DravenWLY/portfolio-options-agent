# Phase 36 — Five-Role Domain Design: Charters, Calculation Tools, Prompt Contract v3

Status: REVISED 2026-07-10 by Claude H (P36-T2 addendum — founder autonomy
directive). This revision fully replaces the same-day v1 of this document;
the governing input is the REVISION section of
`docs/shared/PHASE_36_TRADINGAGENTS_REFERENCE_ADOPTION_NOTES.md`
(three-tier boundary model), which supersedes parts of that document's
original Adapt/Reject verdicts and parts of the original P36-T2 prompt.
Mode: design only; no code. Review chain: Claude E (prompt/gate
compatibility) -> Claude G (architecture/safety + rulings) -> founder.
Supersedes: `docs/claude-e-agentic/PHASE_35_T7C_ROLE_PROMPT_CONTRACT_DESIGN.md`
(p35-role-note-v2) as the prompt contract.
Other binding inputs: Phase 36 plan section,
`PHASE_34A_LIVE_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md` (mediation seam,
freeze/readback), `PHASE_34A_T6_PUBLIC_NEWS_EVENT_SOURCE_RIGHTS_GATE.md`
(as re-tiered), `docs/claude-h-knowledge/P35_T1_TRADE_IMPACT_METHODOLOGY.md`
(the deterministic math the new calculation tools expose).
Reference: `../TradingAgents` studied read-only; patterns paraphrased, no
source or prompt text copied. All examples synthetic.

Locked question: **"What would I be ignoring if I acted manually now?"**
Roles now answer it with substantive, attributed, uncertainty-qualified
analysis — and still never with a rating, a recommendation, sizing, a
target, a horizon, or a forecast.

---

## 0. What this revision changes (summary)

Three posture shifts, one new surface, one thing that does not move:

1. **From notes to analysis sections.** Each analyst produces a structured
   analysis section (role-specific required headings, a closing summary
   table, a "What was verified" statement), not a 2–4 sentence note. The
   deterministic floor stays first and intact; the section renders beneath
   it; every gate drop still falls closed to the floor.
2. **From copy-only numbers to verifiable numbers.** Every numeral in role
   output must be traceable to an evidence envelope or a mediated
   calculation-tool result frozen in this run's artifact. Agents still
   never do arithmetic — they now have deterministic calculation tools so
   they never need to. The auditor's numeric job becomes provenance
   matching, not digit banning.
3. **From interpretation bans to advice-boundary checks.** Attributed,
   uncertainty-qualified interpretation of public data (price context,
   filings metadata, macro series, reported statements) is allowed.
   Forecasts, ratings, action cues, and suitability verdicts remain
   banned everywhere, PM included.

New surface: **per-role deterministic calculation tools** (§3) and bounded
mediated multi-step tool loops (§11.2). LLMs still never touch providers
or compute financial math; the request -> validate -> execute -> sanitized
envelope seam is unchanged — it now carries calculations as well as
evidence.

Unmoved (Tier 1): read-only product; privacy as identifier-privacy
(account nickname only; no raw account/provider identifiers, secrets,
payloads, credentials in any LLM-visible surface); source-rights gates
(PENDING-SOURCE-APPROVAL markers below; new-source requests encouraged);
deterministic financial math in tested backend code; no advice framing;
frozen evidence readback; per-run cost/latency budgets.

## 1. Boundary model and superseded-decisions ledger

Design inputs, restated from the REVISION table: Tier 1 hard boundaries
(above). Tier 2 adjustable posture — section shape, verifiable numbers,
interpretation with attribution, multi-step mediated loops, broader
allowlists — is exercised throughout this document by domain judgment.
Tier 3 agent responsibility — depth, tool choice, truthfulness and
freshness verification, evidence-quality statements — is written into
every charter as a verification protocol (§1.1).

Superseded from this document's v1 (explicit, so reviewers do not hold
both versions in mind):

- v1 D-H1 (magnitude-free PM; portfolio magnitudes excluded from all
  prompts) is **superseded**. Tier 1 privacy is identifier-privacy, not
  magnitude-privacy. Portfolio values and percentages may appear in
  agent-safe envelopes and calculation results for portfolio-aware roles
  and the PM, and may be cited in their output when tool-verifiable. New
  boundary: D-R1 (§1.2).
- v1 note shape (2–4 sentences), the copy-only number rule, the "no words
  joined with underscores as the only defense" posture, and the blanket
  SEC/FRED interpretation pins are superseded per Tier 2. The SEC/FRED
  deterministic-listing floors remain; the pins on live prose become
  advice-boundary checks (§12).
- v1 D-H2 (no PM tensions field) is revised: the PM gains an
  `evidence_tensions` field (§9.3); the Evidence Auditor keeps mechanical
  contradiction detection as the backstop. Judgment is the PM's; detection
  remains the auditor's.
- v1 absence rules (D-H4), whole-block PM fail-closed (D-H3), pending-lane
  envelope designs (D-H5), and the composer-remains-author rule are
  **retained**.

### 1.1 The verification protocol (Tier 3, common to all five roles)

Each role, as part of producing its section:

1. Establishes freshness first: reads (or requests via
   `calc_freshness_inventory`) the as-of dates, freshness categories, and
   staleness day-counts of every evidence section it uses.
2. Cross-checks: where two evidence lanes bear on the same claim (e.g.
   saved close vs statement period dates; filing dates vs snapshot date),
   the role checks agreement and names any tension it finds.
3. Qualifies: every inferential statement is attributed ("per the saved
   series", "computed from the saved statements", "in conventional
   technical usage") and uncertainty-qualified where it goes beyond
   restating a value.
4. States it: the section ends with a mandatory `What was verified`
   subsection — which sources, their as-of dates, what was cross-checked,
   and what could not be verified in the saved evidence.

The Evidence Auditor remains the backstop (provenance, privacy, advice
boundary, grounding) — it is no longer the only place truthfulness lives.

### 1.2 D-R1 — the revised privacy boundary (design decision)

LLM-visible surfaces may carry: the reviewed public symbol and company
name; account **nickname** only; portfolio market values, percentages,
exposure and cash figures **as produced by envelopes or calculation
tools**; all public evidence. They may never carry: raw account numbers,
provider/broker identifiers, SnapTrade references, secrets, tokens, raw
provider payloads, tax-lot detail, or any non-reviewed account field.
Consequence for gates: the P35 portfolio-claim (magnitude) gate is
retired for v3 surfaces and replaced by an identifier-privacy scan plus
the numeric-provenance check (§12). Flagged as A-1 for Claude G
confirmation, since it reverses a reviewed P35 posture.

## 2. The five-role model at a glance

| Role | Owns (report section) | Output | Evidence lanes | Calc tools (§3) | Loop budget (LLM calls / tool requests) |
| --- | --- | --- | --- | --- | --- |
| Technical Analyst | Market context | Analysis section, 250–400 words + table | market context snapshot, quote freshness, trade intent | C6–C10, C15 | 3 / 8 |
| Risk Manager | Risk and exposure analysis | Analysis section, 250–450 words + table | scope, deterministic findings, freshness, gaps, trade intent, exposure summaries | C1–C5, C15 | 3 / 10 |
| Fundamentals Analyst | Company context | Analysis section, 200–400 words + table | company profile; statement facts (PENDING) | C11–C12, C15 | 3 / 8 |
| News Analyst | Events and macro context | Analysis section, 200–400 words + table | SEC filing metadata, FRED calendar; FRED series (PENDING) | C13–C14, C15 | 3 / 8 |
| Portfolio Manager | Summary synthesis | Typed structured synthesis (§9) | accepted sections + findings + gaps + key figures | any (verification re-runs) | 2 / 6 |

Planner and Evidence Auditor remain meta roles outside the five,
run-state only. Unchanged.

Absence rules (retained from v1): a role whose entire evidence lane set is
unavailable skips its live call and renders a deterministic absence line
(per-role wording in §4–§8); the P36-T6 acceptance package must populate
all lanes so all five roles run. The Risk Manager always runs (its
evidence exists by construction).

## 3. Calculation-tool catalog (new design surface)

Deterministic backend calculations exposed as mediated tools. Agents
request; the backend validates the request against the role's allowlist
and the frozen package, computes with tested code, and returns a result
envelope `{calc_name, inputs_used (evidence refs + args), value_labels,
method_label, as_of_labels, caveats}`. Every result freezes into
`tool_run_artifact`; every numeral in role prose must match an envelope or
a frozen calc result (the provenance rule). Calc tools read frozen saved
evidence only — never current selectors, never live providers.

| # | Tool | Computes (engine basis) | Status | Roles |
| --- | --- | --- | --- | --- |
| C1 | `calc_exposure_delta` | Before/after exposure for a named dimension+bucket (dollars, percents, funding regime, denominator as-of) — P35-T1 §1 math | engine landed in P35; tool wrapper NEW | risk, PM |
| C2 | `calc_concentration_metrics` | Largest single-issuer share, single-fund share, top-3 composition, position counts, reference-point evaluations — P35-T1 §4 | engine landed; wrapper NEW | risk, PM |
| C3 | `calc_cash_impact` | Notional vs snapshot cash, remaining cash, consumption percent, coverage regime | engine landed; wrapper NEW | risk, PM |
| C4 | `calc_option_structure` | Collateral, coverage check, days-to-expiry, moneyness band, assignment share deltas — P35-T1 §6 | partial engine (`OptionsExposureRead`); extensions NEW | risk, PM |
| C5 | `calc_scenario_exposure` | If-assigned / if-called exposure tables (synthetic §1 run) | NEW (options slice) | risk, PM |
| C6 | `calc_price_range_position` | Close's position in saved 52-week range (percent of range, distance from high/low) | NEW, trivial from saved EOD | technical |
| C7 | `calc_return_windows` | Trailing percent changes over saved windows (1m/3m/6m/12m) of public prices | NEW from saved OHLCV | technical |
| C8 | `calc_drawdown_stats` | Max drawdown over saved window; current drawdown from saved 52w high | NEW from saved OHLCV | technical |
| C9 | `calc_volatility_stats` | Realized volatility over saved windows; ATR as percent of close | NEW (ATR14 exists) | technical |
| C10 | `calc_ma_relationships` | Full relationship-label set close-vs-averages, average-vs-average crossovers within saved window | mostly exists (T16 labels); wrapper NEW | technical |
| C11 | `calc_financial_ratios` | Margins (gross/operating/net/FCF), debt-to-equity, current ratio, YoY growth of revenue/net income/EPS — from statement facts | NEW; usable only with the FMP lane (PENDING-SOURCE-APPROVAL) | fundamentals, PM |
| C12 | `calc_period_change` | Absolute + percent change of a named reported fact between two saved periods | NEW; same pending lane | fundamentals, PM |
| C13 | `calc_macro_series_change` | Change of a FRED series vs prior reading / N readings back (absolute, percent, direction) | NEW; FRED series lane (PENDING-SOURCE-APPROVAL) | news, PM |
| C14 | `calc_event_window` | Date math over approved metadata: days between filing/release dates and snapshot date; after-snapshot flags | NEW, approved today (date math on approved metadata) | news, PM |
| C15 | `calc_freshness_inventory` | Freshness categories, as-of dates, staleness day-counts for every evidence section visible to the requesting role | extends `evidence_gap_inspector` | all five |

Notes. (a) C1–C5 expose the user's own portfolio math to portfolio-aware
roles and the PM under D-R1; they are never allowlisted to the three
public analysts. (b) C11–C12 are designed now so the FMP fundamentals
ruling (Q-H2) activates them without redesign; without the lane,
fundamentals runs profile-only and the tools return
`source_rights_not_approved`. (c) C13 likewise rides the FRED series
ruling (Q-H3). (d) Ratio and growth math previously deferred in P35-T1
(§5.2 there) is now in scope precisely because it is deterministic,
tested, and tool-invoked — the agent asks, the engine computes.

## 4. Technical Analyst

**Charter.** The desk's reader of saved price history for the reviewed
symbol. It examines: where the close sits in its saved range (C6), how the
saved window behaved (C7 returns, C8 drawdowns, C9 volatility), the moving-
average relationship structure (C10), and the freshness of all of it
(C15). A genuinely useful section characterizes the saved price context in
conventional technical vocabulary — trend direction over the saved window,
range position, volatility state — each claim tied to a computed value and
attributed as description of saved data. It must never: forecast,
extrapolate, or imply continuation ("poised to", "building momentum");
name support/resistance/targets/entries; convert an indicator state into
an action cue ("oversold" may describe RSI in conventional usage; "a
buying opportunity" may not exist in any form); or touch portfolio topics
(not its lane; C1–C5 are not in its allowlist).

**Interpretation license (Tier 2, bounded).** Allowed: "the saved window
shows a downtrend — trailing three- and six-month changes computed from
the saved prices are negative and the close is below both saved long-term
averages"; "in conventional technical usage an RSI14 of 41 is neither
overbought nor oversold". Not allowed: any sentence whose subject is
future price.

**Evidence + tools.** Envelopes: `market_context_snapshot`,
`market_quote_freshness`, `trade_intent_summary` (now symbol-bearing per
D-R1/A-1). Calc allowlist: C6–C10, C15. Typical loop: C15 → C7 + C6 (+ C8
or C9 as the data suggests) → write.

**Section shape.**

    #### Technical analysis — <symbol>
    ##### Range and trend context
    ##### Volatility context
    ##### Gaps and caveats
    ##### What was verified
    | Context item | Value or finding | Source and as-of | Status/caveat |

**Absence behavior** (retained): no saved market values → no call;
deterministic line: "No saved end-of-day market values were available for
this review; price and range context was not reviewed."

**Synthetic excerpt (good).** "Computed from the saved prices, the
trailing six-month change is -18.4 percent and the close sits at 22
percent of its saved 52-week range — the lower quarter. The close is below
both the 50- and 200-day saved averages, which in conventional usage
describes an established downtrend in the saved window; this describes
saved history, not where price goes next. Saved values are end-of-day as
of July 9, categorized fresh; the volatility calculation could not be
verified beyond the saved 3-month window."

## 5. Risk Manager

**Charter.** The desk's portfolio-impact and input-trust analyst — with
numbers now. It examines: what the proposed trade does to exposure (C1 per
affected dimension), concentration structure (C2), cash (C3), option
structure when applicable (C4/C5), and how much the inputs can be trusted
(C15 + scope caveats). A genuinely useful section walks the reviewer
through the trade's portfolio consequences in figures — "semiconductor-
classified holdings would go from 35.0 to 42.0 percent of the portfolio,
already above the 30 percent industry reference point before the trade" —
then weighs input trust: which caveat (stale sync, manual quotes,
unclassified coverage) most undermines those same figures. It must never:
judge suitability ("too concentrated", "acceptable risk", "well
diversified"); convert reference points into limits; advise mitigation
("consider trimming"); or state any figure it did not receive from an
envelope or calc result.

**Interpretation license.** Allowed: "the purchase concentrates the
portfolio further in one industry and consumes most of the snapshot cash —
both computed from a sync categorized stale, so the true figures may
differ". Not allowed: "that concentration is fine for a long horizon" (a
suitability verdict wearing a time horizon).

**Evidence + tools.** Envelopes: `portfolio_scope_context`,
`deterministic_review_findings`, `broker_snapshot_freshness`,
`market_quote_freshness`, `evidence_gap_inspector`,
`trade_intent_summary`; exposure summaries now value-bearing under D-R1.
Calc allowlist: C1–C5, C15. Typical loop: C15 → C1 (affected buckets) +
C3 → C2 (→ C4/C5 for options intents) → write.

**Section shape.**

    #### Risk and exposure analysis
    ##### What this trade changes
    ##### Concentration and reference points
    ##### Input trust and freshness
    ##### What was verified
    | Context item | Value or finding | Source and as-of | Status/caveat |

**Absence behavior:** always runs (defensive wording retained from v1).

**Synthetic excerpt (good).** "Per the exposure calculation, this purchase
takes semiconductor-classified holdings from 35.0 to 42.0 percent of the
portfolio and uses 58 percent of snapshot cash, leaving 5,000. The
industry bucket was above its 30 percent reference point before the trade.
Every one of those figures rests on a broker sync categorized stale (six
days old per the freshness inventory) — the exposure math is only as
current as that sync. Verified: exposure and cash calculations against the
July 3 snapshot; not verifiable here: current buying power and any
position changes since the sync."

## 6. Fundamentals Analyst

**Charter.** The desk's reader of the company's reported record. It
examines: company identity/listing facts (profile), the as-reported
statement facts and their recency, and — via C11/C12 — the shape of the
reported record: margins, leverage, growth between saved periods. A
genuinely useful section tells the reviewer what the reported record shows
and how current it is: "computed from the saved statements, operating
margin was 18.2 percent in the March quarter against 21.0 a year earlier —
the saved record shows slowing revenue growth with margin compression; the
newest reviewed statement is one quarter old." It must never: issue
valuation or quality verdicts (cheap/expensive/strong/weak/healthy as
judgments); estimate forward figures; connect the reported record to the
merit of the trade; or present SIC metadata as precise classification.

**Interpretation license.** Allowed: descriptive analytics of the reported
past, computed by tools and attributed ("the saved statements show two
consecutive quarters of falling gross margin"). Allowed with
qualification: conventional-usage framing ("debt-to-equity of 0.4,
computed from the saved balance sheet, is low leverage in conventional
terms"). Not allowed: "the balance sheet is strong enough to support the
purchase" — that sentence's subject is the trade.

**Evidence + tools.** Envelopes: `public_company_profile` (approved);
`public_fundamentals_snapshot` (NEW, PENDING-SOURCE-APPROVAL — FMP lane,
Q-H2): as-reported fact-groups exactly as designed in v1 (income /
balance / cash-flow headline items, fiscal-period + report-date + currency
labels, backend direction labels), latest annual + latest quarter + prior-
year quarter. Calc allowlist: C11, C12, C15 (C11/C12 fail closed to
`source_rights_not_approved` without the lane). WITHOUT-variant: profile
facts + statement-absence naming — the section is short and honest, and
its most useful sentence is the gap.

**Section shape.**

    #### Company context — <symbol>
    ##### Reported record (or: What was reviewed, in the WITHOUT-variant)
    ##### Recency and coverage
    ##### What was verified
    | Context item | Value or finding | Source and as-of | Status/caveat |

**Absence behavior** (retained): nothing available → no call;
deterministic line: "No reviewed public company context was available for
this review. Company identity and financial-statement facts were not
reviewed; verify recent company information yourself before acting."

## 7. News Analyst

**Charter.** The desk's reader of the dated public record and macro
backdrop. It examines: the filing trail (form types/dates, C14 windows
against the snapshot), the release calendar, and — via the FRED series
lane — the macro series themselves with C13 changes. A genuinely useful
section places the public record in time and explains, with attribution,
what the record is: "a 10-Q filed June 25 means updated quarterly
financials exist that this report's statement facts may predate — the
saved statement period ends in March; the saved calendar lists a CPI
release dated after this review's snapshot, so the macro picture here is
already one release behind." It must never: infer market impact,
sentiment, or materiality for the reviewed symbol; forecast releases,
rates, or policy; treat absence of filings as a signal; or reach beyond
the saved record to remembered news (the no-outside-knowledge rule binds
hardest here).

**Interpretation license.** Allowed: explaining what a form type is
(public knowledge, attributed: "a 10-Q is a quarterly report"),
characterizing saved series with computed changes ("per the saved series,
CPI's latest reading is 0.2 points below the prior reading — the saved
readings show inflation easing over that span"), and dating the record
against the review. Not allowed: "the market has likely priced in the
filing" (forecast + likelihood), "this filing is not material" (materiality
verdict).

**Evidence + tools.** Envelopes: `sec_recent_filings_metadata`,
`economic_awareness_context` (approved); `fred_macro_series_snapshot`
(NEW, PENDING-SOURCE-APPROVAL — Q-H3): the standard six series with
values, as-of dates, direction labels, exactly as designed in v1. Calc
allowlist: C13, C14, C15. Typical loop: C15 → C14 (dates vs snapshot) →
C13 (series changes) → write.

**Section shape.**

    #### Events and macro context — <symbol>
    ##### Filing and release record
    ##### Macro backdrop (WITH-variant only)
    ##### Recency against this review
    ##### What was verified
    | Context item | Value or finding | Source and as-of | Status/caveat |

**Absence behavior** (retained): all lanes empty → no call; deterministic
line: "No reviewed public filing or economic-release context was available
for this review. Check the public record — recent filings and scheduled
releases — yourself before acting."

## 8. Shared analyst output rules

- Required headings per role as specified; heading contract parser-
  enforced (the T17A/T18 heading-contract mechanism, which survived live
  runs, is the model — Claude E owns reconciliation, §12).
- Closing summary table header, exact: `| Context item | Value or finding
  | Source and as-of | Status/caveat |`. No recommendation, signal,
  action, rating, or score column may exist — the table organizes
  evidence, not judgment.
- `What was verified` is mandatory and is prose, not boilerplate: named
  sources, as-of dates, cross-checks performed, what could not be
  verified.
- Word budgets per §2 (parser-checked as ranges, overruns dropped);
  dollars/percents render per envelope value labels (symbol-free numerals
  with unit words remain the envelope convention; the deterministic
  composer owns `$`/`%` formatting in floors — unchanged).
- Uncertainty and attribution: every inferential sentence carries its
  source ("per the saved series", "computed from the saved statements",
  "in conventional usage"). The advice-boundary checks (§12) look for
  unattributed assertion as a drop signal, not just banned vocabulary.

## 9. Portfolio Manager — live analytical synthesis

### 9.1 Charter

The PM is the desk head reviewing the team's work — now with real
analytical judgment, still without a conclusion about the trade. It reads
the four accepted sections, the deterministic findings (values included),
the gap inventory, and the auditor's structured flags; it may re-run any
calculation (§3, any tool) to verify a figure before leaning on it. A
genuinely useful synthesis: names what matters most in this specific
evidence and why; treats disagreements between sections as first-class
content ("the technical section describes an established downtrend while
the fundamentals section shows a record one quarter old — the tension is
about recency, and it is unresolved in this evidence"); orders what to
verify before acting; and says plainly how much weight the inputs can
bear. It must never: rate, recommend, lean, size, target, time, or
forecast; resolve an evidence tension into a directional takeaway; or
introduce facts or figures absent from its inputs and tool results.

The line it walks, stated as the test the auditor and evals apply: **every
PM sentence is about the evidence; no PM sentence is about what the
reviewer should do with the trade** — except verification imperatives.

### 9.2 Inputs (revised under D-R1)

Runner-assembled: (1) the four accepted analyst sections verbatim, with
role attribution; dropped sections excluded and unmentioned; (2)
deterministic finding labels AND values (exposure figures, reference-point
evaluations, freshness categories with as-of dates); (3) the gap inventory
and auditor structured flags; (4) `trade_intent_summary`. Plus calc access:
the PM may issue tool requests (budget §2) to re-verify or extend a
figure. Still excluded: the composed document itself, raw identifiers
(Tier 1), dropped content, tool `summary_payload`s.

### 9.3 Typed output schema (field descriptions are the output instructions)

`PmSynthesis` — all fields required:

- `evidence_weighting: str` — "Three to six sentences of analytical
  judgment about which parts of this saved evidence matter most for
  reading this report and why, grounded in the supplied sections,
  findings, and calculation results. Weigh evidence quality: freshness,
  coverage, and how much of the report depends on each input. Every
  number must come from the supplied inputs or your tool results. Judge
  the evidence, never the trade."
- `evidence_tensions: list[str]` — "Zero to three items. Each item is one
  or two sentences describing a place where the supplied sections or
  findings pull in different directions or rest on different vintages of
  data. Describe the tension and what would resolve it; leave it
  unresolved. Empty list if the evidence is consistent."
- `verification_priorities: list[str]` — "Two to five items, ordered most
  important first. Each is one plain imperative sentence telling the
  reviewer what to verify or check before relying on this report, drawn
  from the supplied caveats, gaps, and tensions. Verification wording
  only: verify, check, confirm, review, re-sync, compare."
- `trust_assessment: str` — "Two to four sentences stating how much weight
  this report's inputs can bear and which caveats dominate that
  judgment, in plain words. Assess the saved evidence's trustworthiness,
  never the likelihood of any market or trade outcome."

### 9.4 Rendered section shape

The deterministic composer remains the document author. `## Summary`
keeps its deterministic headline and paragraph as the floor, then appends
the attributed block when the synthesis passes gates:

    ## Summary
    <deterministic headline — unchanged>
    <deterministic summary paragraph — unchanged>

    **Portfolio Manager synthesis** (AI-generated analysis of the saved
    evidence; verified against this report's frozen calculations):

    <evidence_weighting>

    Where the evidence pulls apart:
    - <evidence_tensions[0]>
    - ...          (subsection omitted entirely when the list is empty)

    Verify first:
    1. <verification_priorities[0]>
    2. ...

    <trust_assessment>

List structure is composer-rendered from typed items (carve-out F-3
stands). Attribution line is fixed composer text.

### 9.5 Degradation (retained from v1, unchanged in substance)

Whole-block fail-closed; no field-level salvage; hard blocks never
re-passed. Fallback lines: gate drop — "A live Portfolio Manager synthesis
was generated for this report but did not pass its safety checks and was
omitted. The summary above is deterministic." Call failure/timeout/
unparseable — "A live Portfolio Manager synthesis was not available for
this run. The summary above is deterministic." Analyst failures never
block the PM; it synthesizes over what survived (minimum: findings +
gaps). No PM call in blocked/deterministic-draft states.

## 10. Prompt contract v3 (version strings `p36-role-analysis-v1`, `p36-pm-synthesis-v1`)

Assembly retained from v1 with SHAPE-N replaced: CORE-A (identity +
locked question + mediation grounding) + role block + SHAPE-A (analysis-
section shape) or SHAPE-PM (§9.3) + CORE-B (verifiable-numbers rule,
attribution/uncertainty rule, advice-boundary bans, identifier-privacy).
Fail-closed unmapped-role behavior retained. Temperature 0.0. Token
budgets: 2000 per analyst iteration, 1600 PM (word budgets in §2 are the
content constraint; token headroom avoids truncation, and the truncation
finish-reason guard is required for all five calls now).

CORE-A (verbatim):

    You are {role_display_name}, a specialist analyst on a read-only
    portfolio review desk. A deterministic system has computed this
    report's core tables and figures. You write your section's analysis
    on top of that floor, using only the evidence envelopes supplied to
    you and the results of calculation tools you request. You answer one
    question: what would a manual reviewer acting right now overlook in
    the saved evidence? You may analyze and interpret; you never advise.

    {role_block}

CORE-B (verbatim):

    Numbers: every number you write must appear in a supplied envelope or
    in a calculation result returned to you in this run. Never do
    arithmetic yourself — request the calculation instead. If a value you
    want does not exist and no tool provides it, write that it was not
    reviewed.

    Attribution: tie every analytical statement to its source in plain
    words — "per the saved series", "computed from the saved statements",
    "in conventional usage". Qualify uncertainty plainly. When evidence is
    absent, name the absence; never fill it from memory or general
    knowledge, and never soften or invert an availability category.

    Boundaries: describe and analyze the saved evidence only. No
    recommendation, rating, or verdict of any kind; no buy, sell, hold,
    overweight, or underweight vocabulary; no position sizing, price
    targets, time horizons, entry or exit framing; no forecasts or
    likelihood claims about markets, prices, assignment, or outcomes; no
    urgency; no guaranteed returns. The only instructions you may give
    are verification steps (verify, check, confirm, review, re-sync,
    compare). Never include account identifiers other than the supplied
    nickname; never invent links, sources, or sections.

Role blocks: rewritten per charters §4–§7 and §9.1 (drafting pattern:
positive expertise statement + section placement + loop hint + the one
role-characteristic negative — technical: no future-price sentences;
risk: no suitability verdicts; fundamentals: no valuation/quality
verdicts; news: no impact/materiality inference; PM: no resolution of
tensions into a lean). Final verbatim role-block text is assembled with
Claude E at implementation review, since block wording and gate mechanics
must move together under the new advice-boundary checks.

## 11. Run mechanics and budgets

### 11.1 Expected per-run call budget (stated, per founder posture)

| Stage | LLM calls | Mediated tool requests |
| --- | --- | --- |
| 4 analysts | typical 8 (2 each: plan+write), max 12 (3 each) | typical 16–20, max 34 (8–10/role) |
| PM | typical 2, max 2 | typical 3, max 6 |
| Bounded re-pass (existing rule, fixable issues only) | max +5 (one per role) | — |
| **Per-run totals** | **typical ~10, hard cap 19** | **typical ~20, hard cap 40** |

Tier 1 keeps these as enforced per-run budgets (config constants), with
wall-clock and token ceilings alongside. Exceeding a budget fails the
remaining loop closed to what is already frozen, never silently truncates
a section mid-thought.

### 11.2 Loop pattern (bounded, mediated — not free-running)

Iteration 1: role receives evidence envelopes + its calc catalog entry
descriptions, returns either tool requests (structured) or a final
section. Backend validates against allowlist/budget, executes, freezes
results. Iteration 2: role receives results, returns section (or one more
request round). Iteration 3 (max): must return the section. The
"free-running tool loop" rejection from the original adoption notes is
refined by the REVISION, not deleted: loops are bounded, mediated,
budgeted, and frozen per step — the LLM never holds a tool binding.

### 11.3 Sequencing and degradation

Four analyst loops (parallel permitted if provider budgets allow — Q-H5
stands), then gating, then the PM loop over accepted output, then PM
gating, compose, freeze. Degradation matrix retained from v1 with one
addition: a calc-tool failure inside a loop returns a named unavailable
envelope; the role must state the gap ("the volatility calculation was
unavailable for this run") rather than substitute; a role that cannot
complete within its loop budget falls to its deterministic floor with the
existing `live_provider_*` warnings.

## 12. Gate rework flags (for Claude E — needs, not mechanics)

The Tier 2 shift converts several prohibition gates into verification
gates. Flagged work:

- F-1 (revised): typed-field validation for the four PM fields; whole-
  block drop semantics.
- F-2 (retained): verification-imperative whitelist for
  `verification_priorities`.
- F-3 (retained): composer list carve-out.
- F-4 (revised): advice-boundary check replacing blanket interpretation
  bans — the banned classes are forecast/likelihood, rating/lean
  vocabulary, suitability verdicts, action cues, sizing/target/horizon;
  attributed descriptive interpretation passes. Applies to all five
  surfaces.
- F-5 (revised): provenance gate replacing the copy-only numeric gate —
  every numeral matches an envelope value or frozen calc result
  (normalized match; P35-R1 typed taxonomy direction applies).
- F-6 (revised): identifier-privacy scan replacing the portfolio-claim
  magnitude gate on v3 surfaces (D-R1/A-1); magnitudes pass when
  provenance-verified, identifiers never pass.
- F-7 (retained): new-envelope admission (statement facts, FRED values,
  calc result labels) into allowed sets via fact-label projection.
- F-8 (new): heading-contract + word-budget + summary-table validation
  for analysis sections (reconcile with the dormant T17-era
  `ROLE_REQUIRED_HEADINGS`).
- F-9 (new): `What was verified` presence + non-boilerplate check.
- F-10 (new): loop budget enforcement + calc-request validation
  (allowlist, args reference frozen package data only).
- F-11 (new): grounding check extended to calc results (role may cite
  only sections/categories/values present in its inputs or its frozen
  results).

## 13. Decisions and open questions

Decisions made in this revision:

- D-R1 (§1.2): identifier-privacy boundary; magnitudes and the reviewed
  symbol allowed in LLM surfaces when envelope- or calc-sourced; account
  nickname only; identifiers never. (A-1: Claude G to confirm — reverses
  a reviewed P35 posture, on founder direction.)
- D-R2 (§3): fifteen-tool calculation catalog with per-role allowlists;
  C1–C5 never reach public analysts; C11–C13 ride the two pending source
  lanes and fail closed without them.
- D-R3 (§8): analysis-section contract — required headings, closing
  evidence table (no judgment columns), mandatory What-was-verified,
  word budgets.
- D-R4 (§9): PM gains evidence_tensions and analytical depth; the
  evidence-not-the-trade test is the binding line; whole-block fail-
  closed retained.
- D-R5 (§11): stated budgets — typical ~10 LLM calls / ~20 tool requests
  per run, hard caps 19 / 40, enforced as Tier 1 config.
- D-R6 (§11.2): bounded mediated plan-then-write loops (max 3 iterations)
  as the refinement of the free-running-loop rejection.
- Retained from v1: absence rules and wording; PM whole-block fallback
  wording; pending-lane envelope designs (fact-groups, direction labels);
  composer authorship; Planner/Auditor as meta roles.

Open questions:

- Q-R1 (Claude G): confirm D-R1/A-1, including the reviewed symbol in
  prompts and portfolio values in PM/risk surfaces.
- Q-R2 (founder via P36-T3): FMP fundamentals lane (activates C11/C12 and
  the WITH-variant §6). Unblocked WITHOUT-variant ships regardless.
- Q-R3 (founder via P36-T3): FRED data-series lane (activates C13 and §7
  WITH-variant).
- Q-R4 (Claude G): budgets in D-R5 as the Tier 1 config values, and PM
  calc access (any tool) vs a narrower PM calc allowlist.
- Q-R5 (Claude E): parallel analyst loops vs sequential under the current
  runner and provider quotas.
- Q-R6 (Claude E): whether the advice-boundary check (F-4) needs a
  per-role vocabulary split (suitability verdicts for risk, valuation
  verdicts for fundamentals, impact inference for news, future-price for
  technical) or one shared class set suffices.
- Q-R7 (Claude G): C7–C9 compute derived statistics of public prices
  (returns, drawdown, realized vol) — confirm these stay inside the
  existing FMP EOD internal-prototype approval or need a P36-T3 line
  item.
