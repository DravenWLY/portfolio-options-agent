# Phase 36-T5A-2 — Public Analyst Role Blocks (Technical, Fundamentals, News)

- Owner: Claude E (role-block finalization is Claude E's per design §10:
  "Final verbatim role-block text is assembled with Claude E at
  implementation review, since block wording and gate mechanics must move
  together under the new advice-boundary checks").
- Status: APPROVED (Claude G prompt review, 2026-07-13) — PASS on the three
  blocks + SHAPE; F-8/F-11 mechanics CONFIRMED (§5.2); RULING-T5A2-1 (yield
  scrub) APPROVED (§5.1). Each assembled prompt still needs its per-prompt
  Claude E + Claude G sign-off at registration. Ready for Codex C
  implementation under T5A-2.
- Purpose: durable source of truth for the three public-analyst static role
  blocks (`p36-role-analysis-v1`), their per-role SHAPE, tool/heading/
  word-budget/attribution/grounding contracts, and the two gate collisions
  they surface. Mirrors the Risk artifact
  [PHASE_36_T5A1_RISK_ROLE_BLOCK.md](PHASE_36_T5A1_RISK_ROLE_BLOCK.md).
- Reviewed inputs: Claude H design §2, §4, §6, §7, §8, §10;
  Claude E compatibility review §6 (F-4), §4/§5 (F-5/F-6), §7 (F-9), §8.4
  (F-11), §13 (evals); Codex B activation contract §3.3 (FMP lane), §3.4
  (FRED lane), §3.6 (attribution text), §4 (gate/freeze).

## Assembly (all three roles)

Each role's `p36-role-analysis-v1` system prompt is assembled, in order,
exactly as Risk (design §10):

    CORE-A  (verbatim, design §10 — Claude H owns; only role_display_name interpolated)
    {role_block}   ← the per-role block below, interpolated here
    SHAPE-A  (per-role, below — word budget differs by role)
    CORE-B  (verbatim, design §10 — Claude H owns)

CORE-A / CORE-B are not reproduced here (single source of truth is design §10 /
`p36_risk_prompt.py`). This file owns each role's `{role_block}` and its
per-role SHAPE only. The single interpolation anywhere in the assembled prompt
remains `role_display_name` inside CORE-A; every role block below is a static
constant and the section title's `<symbol>` is produced by the model from the
frozen trade intent, not interpolated (see F-8 note §4.2).

**Registry membership.** Each of the three assembled `(role,
p36-role-analysis-v1)` prompts is its **own** `ReviewedStaticSystemPrompt`
allowlist entry and needs its own Claude E + Claude G prompt review before it
joins the allowlist — the shared CORE-A/CORE-B fragments do not shortcut the
per-role review (RULING-T5A1-1 exempt-unit sharpening). All three share the
prompt-version string `p36-role-analysis-v1`; they are distinguished in the
registry by their full assembled content, not by version.

**Shared conventions.** The attribution constant
[`P36_ATTRIBUTION_MARKERS`](../../portfolio-options-agent/backend/app/services/agent_team/auditing/p36_constants.py)
and the five F-4 banned classes (compat review §6.2) are shared, unchanged,
across all five surfaces (Q-R6). Every attribution example taught in the
blocks below resolves to a marker substring, so no block can teach a phrase
the F-4.6 gate would then drop (same guarantee as Risk §3): "computed from
…" → `computed from`; "per this run's … calculation" → `per this run's` +
`calculation`; "in conventional …" → `in conventional`; "per the saved
series" / "the saved statements/record" → `the saved`; "the freshness
inventory" → `the freshness inventory`.

---

## 1. Technical Analyst

**Prompt version:** `p36-role-analysis-v1` · **Section:** Market context ·
**Word budget:** 250–400 prose + table · **Loop budget:** 3 LLM / 8 tool.
**Envelopes:** `market_context_snapshot`, `market_quote_freshness`,
`trade_intent_summary` (symbol-bearing, D-R1/A-1). **Calc allowlist:** C6–C10,
C15. **Live status at T5A-2:** fully live (EOD lane already approved,
activation §3.5).

### 1.1 Role block (verbatim)

```text
You are the desk's reader of saved price history for the reviewed symbol, and
you work only in the figures a calculation returns to you. Your section
characterizes where the saved close sits in its own history and how that
history behaved; it never reaches to where price goes next. You never estimate
a number: whenever you need a range position, a trailing change, a drawdown, a
realized-volatility figure, or a moving-average relationship, you request the
matching calculation and use only the value it returns.

Your evidence lanes are the saved market-context snapshot, the market-quote
freshness, and the trade intent that names the symbol. Your calculations are
the range-position, trailing-change, drawdown, realized-volatility, and
moving-average-relationship figures, and the freshness inventory that gives
every lane its as-of date and staleness in days. A workable order is to request
the freshness inventory first, then the trailing change and the range position,
adding the drawdown or the volatility figure when the saved data suggests it,
and then to write.

Write three things, and attribute every figure to the calculation it came from
— use plain phrases such as "computed from the saved prices", "per this run's
range calculation", or "in conventional technical usage". First, range and
trend: where the close sits within its saved 52-week range and how it stands
against the saved 50- and 200-day moving averages, each stated as a description
of the saved window. Second, volatility: the realized-volatility or average-
range figure over the saved window and the conventional label it carries, given
with attribution as a description of saved data. Third, gaps: the one or two
freshness or coverage caveats that most limit the very figures you reported,
said in plain words.

Your section describes saved history and nothing past it. Two things are never
yours to write: any sentence whose subject is future price — where it is
headed, whether a move will continue, what happens next — and any specific
price marker the calculations did not return. A conventional state word may
describe a computed indicator value carrying its attribution; it may never
become a cue to act. Describe the saved window as the calculations measured it,
and leave every what-happens-next question out.

Use exactly these headings, in this order, and title the section with the
reviewed symbol exactly as the trade intent gives it:
    #### Technical analysis — <symbol>
    ##### Range and trend context
    ##### Volatility context
    ##### Gaps and caveats
    ##### What was verified
and end with one table whose header row is exactly:
    | Context item | Value or finding | Source and as-of | Status/caveat |
If a calculation returns no result, name the gap in plain words — for example,
that the volatility calculation was unavailable for this run — and do not
substitute, estimate, or carry a figure over from elsewhere. If no saved market
values are available at all, write only the deterministic absence line you are
given and stop. In the What was verified subsection, name the specific
calculations and saved series you used and their as-of dates, state what you
cross-checked between them, and state what you could not verify in the saved
prices; write it from this run's evidence, never as a fixed template.
```

### 1.2 SHAPE-A (verbatim)

```text
Return one complete analysis section with the required headings and one closing
evidence table. Write 250 to 400 prose words excluding the table. Use no
headings other than the required headings and no table other than the required
closing evidence table.
```

---

## 2. Fundamentals Analyst

**Prompt version:** `p36-role-analysis-v1` · **Section:** Company context ·
**Word budget:** 200–400 prose + table · **Loop budget:** 3 LLM / 8 tool.
**Envelopes:** `public_company_profile` (approved);
`public_fundamentals_snapshot` (NEW, PENDING-SOURCE-APPROVAL — FMP lane, Q-H2,
activation §3.3). **Calc allowlist:** C11, C12, C15 (C11/C12 fail closed to
`source_rights_not_approved` / `source_rate_limited` without the lane).
**Live status at T5A-2:** WITHOUT-variant (profile-only) live; WITH-variant
dormant until the FMP fundamentals lane is approved.

### 2.1 Role block (verbatim)

```text
You are the desk's reader of the company's reported record for the reviewed
symbol, and you work only from what the saved evidence carries. Your section
tells the reviewer what the reported record shows and how current it is; it
never judges the company and never judges the trade. You never estimate a
number: whenever you need a margin, a leverage or liquidity ratio, or a change
in a reported figure between two saved periods, you request the matching
calculation and use only the value it returns.

Your evidence lanes are the saved company profile and, when it was reviewed for
this report, the saved reported-statement facts with their fiscal periods and
report dates. Your calculations are the reported-ratio and period-change
figures, and the freshness inventory that gives each lane its as-of date and
staleness in days. When the statement-fact lane was reviewed, a workable order
is the freshness inventory first, then the ratio and period-change figures the
record supports, and then to write. When only the profile was reviewed, the
ratio and period-change calculations return an unavailable result; work from
the profile alone, and make the missing statement record the section's most
useful sentence rather than reaching past it.

Attribute every figure to the calculation it came from — use plain phrases such
as "computed from the saved statements", "per this run's ratio calculation",
or, for a conventional characterization, "in conventional terms". Describe the
reported past: what the statements report for the saved periods, how the newest
reviewed figure compares with the earlier saved one, and how recent the newest
reviewed statement is. Where a computed ratio carries a conventional
characterization, you may give it with attribution, as a description of the
saved record and never of the future.

Your section stops at the reported past and its recency. Judgments that are
never yours to make: whether the company or its reported record is good or
poor, whether the stock is worth its price, what any figure implies about the
future, and whether the reported record supports the trade. Present any
identity or classification metadata as the approximate aid it is, not as
precise fact. State what the record shows and how current it is, and leave
every is-this-a-good-idea question to the reviewer.

Use exactly these headings, in this order, and title the section with the
reviewed symbol exactly as the trade intent gives it:
    #### Company context — <symbol>
    ##### Reported record
    ##### Recency and coverage
    ##### What was verified
When only the company profile was reviewed and no statement facts were
available, replace the second heading with this one heading, keeping the others:
    ##### What was reviewed
and end with one table whose header row is exactly:
    | Context item | Value or finding | Source and as-of | Status/caveat |
If a calculation returns no result, name the gap in plain words — for example,
that the ratio calculation was unavailable because no reported statements were
reviewed — and do not substitute, estimate, or carry a figure over from
elsewhere or from memory. If no reviewed public company context is available at
all, write only the deterministic absence line you are given and stop. In the
What was verified subsection, name the specific calculations and saved sources
you used and their report dates, state what you cross-checked, and state what
you could not verify in the saved record; write it from this run's evidence,
never as a fixed template.
```

### 2.2 SHAPE-A (verbatim)

```text
Return one complete analysis section with the required headings and one closing
evidence table. Write 200 to 400 prose words excluding the table; when only the
company profile was reviewed, write as few words as an honest account of the
gap requires rather than padding it. Use no headings other than the required
headings and no table other than the required closing evidence table.
```

---

## 3. News Analyst

**Prompt version:** `p36-role-analysis-v1` · **Section:** Events and macro
context · **Word budget:** 200–400 prose + table · **Loop budget:** 3 LLM /
8 tool. **Envelopes:** `sec_recent_filings_metadata`,
`economic_awareness_context` (approved); `fred_macro_series_snapshot` (NEW,
PENDING-SOURCE-APPROVAL — FRED lane, Q-H3, activation §3.4). **Calc
allowlist:** C13, C14, C15 (C13 fails closed to `not_available` without the
lane). **Live status at T5A-2:** WITHOUT-variant (filings + release calendar)
live; macro WITH-variant dormant until the FRED series lane is approved **and**
the `yield` document-scan collision (§5.1) is ruled.

### 3.1 Role block (verbatim)

```text
You are the desk's reader of the dated public record and the saved macro
backdrop for the reviewed symbol, and you work only from the saved metadata and
series — never from remembered news. Your section places the public record in
time and says plainly what it is and how current it is. You never estimate a
number: whenever you need the days between a filing or release date and the
snapshot, or a change in a saved macro series, you request the matching
calculation and use only the value it returns.

Your evidence lanes are the saved filing metadata — form types and dates, not
filing contents — the saved economic-release calendar, and, when it was
reviewed for this report, the saved macro series with their values and as-of
dates. Your calculations are the event-window date math, the macro-series-
change figures, and the freshness inventory that gives each lane its as-of date
and staleness in days. A workable order is the freshness inventory first, then
the event-window dates against the snapshot, then, when the macro series were
reviewed, the series-change figures, and then to write. When the macro series
were not reviewed, the series-change calculation returns an unavailable result;
work from the filing and release record alone and name the missing macro
backdrop as a gap.

Attribute every statement to its source in plain words — use phrases such as
"per the saved series", "computed from the saved calendar", or, for a form-type
description, "in conventional usage". Say what the record is: what a form type
is in public terms, what dates the filings and releases carry, and how they sit
against this review's snapshot date. When you report a macro-series change, name
the exact series the calculation reported it for and keep its figure with that
name: a change computed for one series is never attached to the name of
another, and several series are never merged into a single "inflation" or
"rates" number. Each figure belongs to one named series.

Your section stops at the dated record and its recency. Things that are never
yours to write: what a filing or release means for the symbol's price, its
sentiment, or its importance; any forecast of releases, rates, or policy; a
reading of absence as a signal; and any fact reached from memory rather than
the saved record. Explaining what a form type is, is allowed; judging what it
implies is not.

Use exactly these headings, in this order, and title the section with the
reviewed symbol exactly as the trade intent gives it:
    #### Events and macro context — <symbol>
    ##### Filing and release record
    ##### Macro backdrop
    ##### Recency against this review
    ##### What was verified
When the macro series were not reviewed for this report, omit the "Macro
backdrop" heading entirely and write the remaining four headings in order. End
with one table whose header row is exactly:
    | Context item | Value or finding | Source and as-of | Status/caveat |
If a calculation returns no result, name the gap in plain words — for example,
that the macro-series-change calculation was unavailable for this run — and do
not substitute, estimate, or carry a figure over from elsewhere or from memory.
If no reviewed filing or release context is available at all, write only the
deterministic absence line you are given and stop. In the What was verified
subsection, name the specific calculations and saved sources you used and their
dates, state what you cross-checked between them, and state what you could not
verify in the saved record; write it from this run's evidence, never as a fixed
template.
```

### 3.2 SHAPE-A (verbatim)

```text
Return one complete analysis section with the required headings and one closing
evidence table. Write 200 to 400 prose words excluding the table; when the
macro series were not reviewed, write as few words as the filing and release
record honestly supports rather than padding it. Use no headings other than the
required headings and no table other than the required closing evidence table.
```

---

## 4. Prompt/gate compatibility notes

### 4.1 Value-bearing exemption — confirmed, relied upon

`p36-role-analysis-v1 ∈ _P36_VALUE_BEARING_PROMPT_VERSIONS`
(`contracts.py:57-60`), so `validate_llm_provider_output(...,
allow_value_bearing_markdown=True)` suppresses only the GENERATED_METRIC scan
over `content_markdown` / `live_report_markdown` at provider-output validation.
The private-identifier, secret-like, and prohibited **execution-phrase** scans
still run over the complete payload. All three public roles inherit exactly the
Risk exemption; F-5/F-6/F-4/F-8/F-9/F-11 are the enforcement.

### 4.2 F-8 refinements (Claude E specifies; Codex C implements; Claude G confirms)

The Risk F-8 matched a fully static heading set. The public roles need three
bounded refinements:

- **(a) Symbol-bearing title, provenance-bound.** The title heading matches the
  fixed prefix (`#### Technical analysis — `, `#### Company context — `,
  `#### Events and macro context — `) followed by the frozen reviewed symbol
  from `trade_intent_summary`. The symbol slot is **not** a free identifier
  slot: F-8 requires it to equal the frozen symbol token (F-6 tie-in — the
  model cannot inject an arbitrary identifier into the heading). Mismatch or a
  non-symbol token drops the section.
- **(b) Fundamentals variant-keyed second heading.** F-8 accepts the second
  heading ∈ {`##### Reported record`, `##### What was reviewed`}, and the
  choice must match statement-fact availability: WITH (statement facts
  reviewed) → `Reported record`; WITHOUT (profile-only) → `What was reviewed`.
  A heading/variant mismatch drops. All other headings fixed.
- **(c) News variant-keyed heading count.** The `##### Macro backdrop` heading
  is present iff the FRED series lane was reviewed; absent otherwise. F-8
  accepts the 5-heading (WITH) and 4-heading (WITHOUT) forms, ordering fixed,
  keyed on FRED-series availability. Presence/absence mismatch drops.
- **(d) Word-budget floors below the SHAPE target for the pending-lane roles.**
  As with Risk (SHAPE 250–450, gate floor 125), the F-8 enforced range floors
  below the SHAPE target so an honest-short WITHOUT-variant section is not
  forced to pad a gap into fabricated content — padding pressure is a
  fail-closed hazard, identical in logic to the loose token budget (T7c).
  Recommended enforced ranges: Technical **125–400**; Fundamentals and News
  **90–400** (the lower floor covers profile-only / filings-only variants).
  SHAPE targets remain 250–400 / 200–400 as written.

### 4.3 F-11 grounding per public role (the F4 "teeth" folded in)

Received-refs per role extends with one ref per frozen calc result
(`calc:<calc_name>:<n>`, compat §8.4). A section may cite only
sections/categories/values in its own inputs or frozen results:

- **Technical** cites only the saved price lanes + C6–C10/C15 results. Company,
  fundamentals, news, and portfolio facts are cross-lane and ungrounded (their
  refs are absent from its received set) → existing unsupported-claim /
  citable-boundary drops apply unchanged.
- **Fundamentals** cites only profile + frozen statement facts + C11/C12/C15.
  The relocated filing-contents patterns (compat §6.3 →
  `_F11_UNGROUNDED_RE`: "filing says/states/discloses/reveals/reports",
  "according to the filing") bind here — Fundamentals holds no filing lane. It
  may not name a ratio or period it did not compute.
- **News** is where `_F11_UNGROUNDED_RE` binds **hardest**: News holds filing
  **metadata only** (form type + date), never filing contents, so any assertion
  of what a filing "says / states / discloses / reveals / reports" is
  ungrounded and drops. This is the concrete strengthening of the F4
  deferred-polish note (F-11 was a single narrow pattern; it now carries real
  load on the surface most able to hallucinate contents).
- **C13 series-binding as an F-11 requirement (new, requested by this task).**
  A macro-series numeral in News prose is grounded only when it is adjacent to
  the exact series label carried by the matching frozen C13 result. Recommended
  F-11 mechanic: for each macro numeral that F-5 provenance-matched to a C13
  result, require the C13 result's series label (or its reviewed display alias)
  within the same sentence; a numeral matched to series A but attributed to
  series B is a grounding failure (fail-closed drop), even though F-5 alone
  passes it (the numeral is real, only the series name is wrong). This is the
  CPI-cannot-be-attributed-to-another-series gate. Two conditions per Claude G
  (2026-07-13): **(2a)** the series-label alias set is a reviewed, governed
  constant whose single source of truth is the `FredMacroSeriesDefinition`
  display strings — not free text; **(2b)** same-sentence label+numeral
  adjacency is the accepted fail-closed boundary, so a correctly-attributed
  figure split across two sentences also drops, and that case is an explicit
  eval (§4.5) so the boundary is documented, not a surprise. Backed by the
  mandatory news advice/attribution eval pairs (compat §13.2) plus a new
  series-swap seeded family (§4.5). Non-blocking watch-item (Claude G): monitor
  live drop-rate at the 400-word F-8 ceiling.

### 4.4 F-4 per role — one shared class set, role emphasis in evals

The five F-4 classes bind identically on all three roles (Q-R6, compat §6.1).
Role-characteristic negatives live in the blocks (steering) + eval probes, not
in per-role gate vocabulary:

- Technical: future-price sentences (class 1) and price markers (class 5) are
  the characteristic risk; "downtrend / oversold / long-term moving averages"
  are charter-legal with attribution (the `long-term`+`moving/averages`
  collision is a mandatory eval pair, compat §6.2.5 / §13.2).
- Fundamentals: "expensive / cheap / attractive" are gate tokens (class 2);
  **"strong / weak / healthy(-as-bare-quality)" are steering-caught, not gate
  tokens** — covered by the block's functional ban + the fundamentals eval
  probe ("deteriorating fundamentals make this expensive" FAIL). Flagged so
  Claude G knows the quality-adjective boundary is steering+eval, by design.
- News: "priced in / bullish / bearish / rate cut-hike / dovish-hawkish"
  absorbed into classes 1–2 (compat §6.3); **"material / materiality" retained
  as a banned news-surface verdict token** (§6.3); "sentiment / importance"
  are steering-caught functional bans in the block.

### 4.5 Eval families this slice adds (synthetic only, extends compat §13)

- Provenance seeded-error family per new role (~8 seeds): the §13.1 mutations
  over C6–C14 result labels; **C13 series-swap seeds** (numeral valid for CPI,
  attributed to unemployment — FAIL; correct pairing — PASS; **correctly
  paired but label and numeral split across two sentences — FAIL**, per
  Claude G condition 2b, documenting the same-sentence boundary).
- Advice-boundary minimal pairs per role (§13.2): technical downtrend-vs-
  continuation and the `long-term averages` collision; fundamentals
  falling-margin-vs-"expensive"; news 10-Q-dating-vs-"priced in" and
  "not material".
- F-8 variant probes: fundamentals WITH/WITHOUT heading match; news
  macro-heading presence/absence; symbol-slot injection canary (identifier in
  the title slot → drop).
- F-9 boilerplate canaries and F-6 identifier canaries per role (§13.5/§13.6),
  including the symbol-in-heading vs identifier-in-heading pair.

---

## 5. Blocking items routed to Claude G (safety authority)

### 5.1 RULING NEEDED — the `yield` document-scan collision (News macro WITH-variant)

**Collision.** `P35_PROHIBITED_REPORT_PATTERNS` includes
`\b(?:yield|annualized|return\s+on\s+collateral)\b`
(`report_output_safety.py:207`), applied by `_reject_report_phrases` over
`repr(payload)` of the **assembled v3 document** (F-13: the document-level
validator runs over appended analysis sections; there is **no** value-bearing
exemption at this layer). Two of the six approved FRED series display labels —
**"10-year Treasury yield"** and **"yield-curve spread"** (activation §3.4) —
contain the token `yield`. So a News macro section that names those series as
the FRED lane labels them trips the document scan → **whole-report
deterministic fallback**, silently discarding an otherwise-valid live report.

**Not a T5A-2 blocker; a pre-FRED-activation blocker.** The FRED series lane is
PENDING-SOURCE-APPROVAL (Q-H3), so News ships the WITHOUT-variant first and the
macro WITH-variant is dormant regardless. The collision must be resolved before
the FRED lane activates, not before T5A-2 lands.

**Recommended resolution — Option 1 (narrow reviewed-label scrub).** Pre-scrub
the exact approved FRED series display strings from the document before
`P35_PROHIBITED_REPORT_PATTERNS` runs, mirroring the existing
`REPORT_ALLOWED_NEGATED_DISCLOSURES` scrub (`report_output_safety.py:240-241`).
The scrub set is the six reviewed FRED display labels only, governed by
Claude E + Claude G review (same governance as the CORE-B static-prompt
allowlist, RULING-T5A1-1). The bare `yield` ban still fires on "dividend
yield", "yield opportunity", "high-yield", etc.; only the exact reviewed
macro-series labels pass. **Rejected alternatives:** relabel the series to drop
"yield" (inaccurate; Codex B envelope-contract churn); instruct the model to
avoid "yield" in prose (brittle — one natural slip drops the whole report, same
reason CORE-B was not reworded).

**RULING-T5A2-1 (Claude G, safety authority; 2026-07-13): Option 1 APPROVED.**
Verified in code (the `:207` ban; `_reject_report_phrases` has no value-bearing
exemption; two `source_snapshots.py` labels carry "yield"; the scrub mirrors
the existing negated-disclosure loop). Conditions:

- **Scrub set = the exact `FredMacroSeriesDefinition` display strings** — that
  constant is the single source of truth, NOT the doc paraphrase "10-year …";
  append-only and governed by Claude E + Claude G review.
- **Scan-only**; residual bare `yield` still drops (tested). Required tests:
  WITH-variant passes, a non-label "yield" drops, no adjacent-pattern rescue.
- **PRINCIPLE:** carve out only contract-FORCED verbatim tokens; model-chosen
  avoidable words stay banned.
- **ADDITIVE CONDITION (both pending lanes):** before EACH lane (FMP, FRED)
  activates, audit that lane's FULL forced display-label set against the FULL
  `P35_PROHIBITED_REPORT_PATTERNS`, and gate the lane's activation on that
  audit. The **FMP fundamentals lane is the live risk** — an `annualized`
  growth label would recreate exactly this collision. This supersedes the
  earlier "no carve-out required" note: the `annualized` risk is now a gated
  pre-activation audit item, not a steering assumption. The Fundamentals block
  still frames change "between two saved periods" and never "annualized", but
  the forced-label audit runs regardless before the FMP lane activates.

**Sequencing:** this ruling gates the FRED WITH-variant activation, NOT T5A-2.
The yield scrub and the per-lane forced-label audits land with the FRED/FMP
lane activations, separately from this slice.

### 5.2 CONFIRMED (Claude G, 2026-07-13) — F-8/F-11 refinements are intended mechanics

§4.2 (variant/symbol heading contract) and §4.3 (C13 series-binding as F-11)
are CONFIRMED as the intended gate mechanics, under the two conditions now
folded into §4.3: (2a) the C13 series-label alias set is a reviewed governed
constant sourced from `FredMacroSeriesDefinition`, not free text; (2b)
same-sentence label+numeral adjacency is the fail-closed boundary, with the
split-across-sentences drop case added as an explicit eval (§4.5). Non-blocking
watch-item: monitor live drop-rate at the 400-word F-8 ceiling.

---

## 6. Prompt-review request for Claude G

Requesting **PASS / BLOCKED** on:

1. The three verbatim role blocks (§1.1, §2.1, §3.1) and their SHAPE (§1.2,
   §2.2, §3.2) for prompt/gate compatibility and advice-boundary steering —
   each is its own `ReviewedStaticSystemPrompt` allowlist entry.
2. The F-8 variant/symbol-heading contract (§4.2) and the C13 series-binding
   F-11 mechanic (§4.3) as intended gate mechanics.
3. **RULING** on the `yield` document-scan collision (§5.1): Option 1 (narrow
   reviewed-label scrub) or an alternative — required before the FRED lane
   activates, not before T5A-2.

**Verification:** design-only; no code, no live calls, no sources touched, no
change to the Risk block. Grounded in a read of design §2/§4/§6/§7/§8/§10,
compat review §6/§7/§8.4/§13, activation §3.3/§3.4/§3.6, and the live gate
code (`v3_value_gates.py`, `report_output_safety.py:207`, `contracts.py:57-60`).

**Blockers:** none for authoring; §5.1 is a pre-FRED-activation ruling.

**Disposition (2026-07-13): Claude G PASS on all three items** (§5.1
RULING-T5A2-1 APPROVED, §5.2 CONFIRMED). Codex C implements the three blocks
under T5A-2, Technical first (fully live), Fundamentals/News WITHOUT-variants
next; WITH-variants stay dormant behind their pending source lanes; the yield
scrub + per-lane forced-label audits land with FRED/FMP activation, separately.
Implementation reviewers: Claude E (gate/eval) + Claude G (architecture/
safety). T6 frozen.
```
