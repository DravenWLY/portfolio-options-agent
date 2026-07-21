# Phase 36 T7-K2A — Analyst Gate-Survival Prompt and Eval Design

Status: approved (K2A-R2) — Codex B design blockers resolved; Claude G
static-prompt review PASS (2026-07-20) with three required edits applied in
place (Section 8); cleared for Codex C implementation (the K2B slice)
Owner: Claude E (gate/eval + agentic systems design)
Mode: design only. No implementation in this slice.

## 0. Scope and hard boundaries

The 2026-07-20 five-role internal run completed safely: every analyst live
section was withheld by the existing output gates, and the PM synthesis
survived. This design tunes the four analyst prompts **to** the gates so
honest, evidence-bound prose survives review. It changes no gate, threshold,
validator, source, schema, provider, frontend, or live-run behavior, and it
does not touch the Portfolio Manager prompt.

**Structural constraint discovered during design (load-bearing):** the PM
system prompt is composed from the same shared cores as the analysts —
`p36_pm_prompt.py` joins `P36_CORE_A + … + P36_CORE_B`
(`p36_pm_prompt.py:76-79`). Therefore `P36_CORE_A` and `P36_CORE_B` are
**frozen for this slice**: editing either would silently change the passed PM
prompt. All shared guidance below lands in a **new analyst-only constant**
(§3.1) appended in the risk and public renderers only. The PM render path is
byte-identical by construction.

Sanitized failure map this design answers (metadata only; no artifact prose
was read):

| Role | Dropping gate families |
| --- | --- |
| Fundamentals | numeric provenance (F-5) |
| News | numeric provenance (F-5) |
| Technical | source attribution (F-4.6) |
| Risk | advice boundary (F-4) + numeric provenance (F-5) + attribution (F-4.6) |

Each validation returns its first flag only, so a multi-family listing for
Risk reflects flags across bounded-loop iterations/runs, not one block failing
three ways at once. The design treats every family as live for every role.

## 1. Gate mechanics the prompts must be written against

All references are to the current committed gate code. Nothing here proposes
changing any of it.

- **F-5 numeric provenance** (`_numeric_provenance_flag`,
  `v3_value_gates.py:549`; allowed set `_allowed_numeric_values`, `:514`).
  A number in prose survives only if it matches this role's own tool-result
  facts this run:
  - digit-runs from fact keys and value labels are allowed as structural
    integers (string match after comma-strip);
  - decimals from value labels are allowed with **round-to-fewer-places**
    tolerance (`_numeric_allowed`, `:592`): prose may state a surfaced value
    at fewer decimal places (banker's rounding) or in a numerically equal
    form (Decimal equality admits trailing zeros: 49.90 restates 49.9),
    never as a numerically different value, unit, sign, or
    derived/aggregated figure;
  - ISO dates in prose must each exactly match a surfaced date
    (`_scrub_valid_dates`, `:567`) — one unknown ISO date fails the block;
  - **long-date trap:** any `Capitalized-word + 1-2 digits` bigram is parsed
    as a month-name date (`_LONG_DATE_RE`, `:128`). A non-month capitalized
    word (“The 8…”, “Form 10…”) fails the block outright; a real month must
    normalize to a surfaced date, and a year-less month-date needs exactly one
    year across surfaced dates (`_inferred_year`, `:587`);
  - **spelled-magnitude trap:** a spelled cardinal directly before
    percent / per cent / dollar(s) / point(s) / basis point(s) / share(s) /
    contract(s) / day(s) (`_SPELLED_MAGNITUDE_RE`, `:129`) is checked against
    surfaced decimals — “two days stale” fails unless 2 was surfaced as a
    value.
- **F-4 advice boundary + F-4.6 attribution** (`_advice_boundary_flag`,
  `v3_value_gates.py:641`). Five shared banned classes (forecast, rating,
  suitability, action, sizing/horizon), news-inherited absolutes, and the
  news-only bare materiality ban (RULING-T5B-3). Separately, **every prose
  sentence** (headings exempt) containing an interpretation trigger —
  `downtrend, uptrend, overbought, oversold, compression, easing, elevated,
  low leverage, high leverage, concentrate(s), concentration, drawdown,
  trend, conventional` (`_F4_INTERPRETATION_RE`, `:239`) — must contain one of
  the six attribution markers as a case-insensitive substring
  (`P36_ATTRIBUTION_MARKERS`): `the saved`, `per this run's`,
  `computed from`, `calculation`, `the freshness inventory`,
  `in conventional`.
- **F-8/F-9/F-11** structure, non-boilerplate verification, grounding — per
  role heading sets, word bounds, table header, filing-content ban, C13
  same-sentence series binding (`validate_p36_public_analysis_section`,
  `:289`; `validate_p36_risk_analysis_section`, `:269`).
- **Document-level scan after acceptance** (`report_output_safety.py`,
  `P35_PROHIBITED_REPORT_PATTERNS:194` and neighbors). Runs over the composed
  report; a banned word in an *accepted* section fails the whole report —
  a strictly worse outcome than a role drop. Notable members analysts must
  never write: `yield`, `annualized`, `return on collateral`, `overweight/
  underweight`, `comfortable/healthy/prudent/excessive`, `safe(ly)`,
  `too concentrated`, `well diversified`, `opportunity/attractive/cheap/
  expensive`, `reasonable size`, `plenty of`, plus display-token,
  source-leak, and invented-level scans.

## 2. The shared gate-survival grammar (all four analysts)

These ten rules are the mechanical translation of §1. They are the content of
the new shared prompt constant in §3.1 and the checklist the eval matrix
enforces.

1. **Digits only from this run.** Write a number only if it appears in a
   calculation result or envelope value returned to you this run. You may
   restate it with fewer decimal places; never more places, never a new unit,
   never arithmetic, totals, differences, or averages of your own.
2. **Dates in ISO form only.** Write dates exactly as supplied
   (`YYYY-MM-DD`). Never write month-name dates ("July 14").
3. **Never a capitalized word directly before a number.** Recast so a
   lowercase word touches the digits: "the 8-K filing", "form type 10-Q",
   never "The 8-K…" or "Form 10-Q…" at any position.
4. **Never spell a number before a unit word** (percent, dollars, points,
   basis points, shares, contracts, days). Use the supplied digits or drop
   the quantity.
5. **Attribute every interpretive sentence.** Any sentence using range/trend/
   volatility/leverage/concentration state words carries one of the exact
   attribution phrases; the most reliable form is to name the calculation in
   the same sentence ("…per this run's drawdown calculation").
6. **No advice-class vocabulary, ever** — the five banned classes spelled out
   as a never-use lexicon (§3.1 text). Horizon words are avoided entirely
   rather than relying on the moving-average carve-out.
7. **No document-banned vocabulary, ever** — the §1 list, headlined by
   `annualized` (Technical) and `yield` (Fundamentals). When a supplied label
   itself contains a banned word, name the figure by its calculation instead
   of by that label.
8. **What-was-verified is written from this run** — specific calculations,
   sources, as-of dates, one cross-check, one could-not-verify; never a
   fixed template sentence.
9. **Exact structure** — role headings in order, symbol-bearing title, one
   closing table with the exact header row, within word bounds.
10. **Grounding** — metadata only for filings (never contents); a macro
    change figure stays in the same sentence as its exact series name; series
    are never merged.

## 3. Per-role design

### 3.1 New shared constant — `P36_ANALYST_GATE_DISCIPLINE` (analysts only)

Appended as the final segment in `render_p36_risk_system_prompt()` and
`render_p36_public_system_prompt()` only. The PM renderer is not touched.
Verbatim block Codex C registers:

```text
Write to survive review. Your section is checked mechanically before it is
accepted, and one violation withholds the whole section, so follow these
rules exactly. Numbers: write a number only if it appears in a calculation
result or supplied envelope from this run; you may repeat it with fewer
decimal places, but never add precision, change units, or produce any figure
of your own, including totals and differences. Dates: write dates exactly as
supplied, in year-month-day form; never write a month name with a day
number. Never place a capitalized word directly before a number — write
"the 8-K filing" or "form type 10-Q", never "The 8-K" or "Form 10-Q". Never
spell out a number before percent, dollars, points, basis points, shares,
contracts, or days; use the supplied digits or omit the quantity. Any
sentence that characterizes range, trend, volatility, leverage, drawdown, or
concentration must name its basis in that same sentence using one of these
exact phrases: "per this run's …", "computed from …", "the saved …",
"… calculation", "the freshness inventory", or "in conventional …". Words
you never write, in any form: likely, will, expected, forecast, predict,
poised to, momentum; bullish, bearish, buy, sell, hold, overweight,
underweight, attractive, cheap, expensive, opportunity; comfortable,
healthy, prudent, excessive, reasonable, appropriate, suitable, fine, safe,
safely, too concentrated, well diversified, plenty of; consider, should,
recommend, must, need to; price target, target price, target, or any
long-term, short-term, medium-term, or horizon phrasing; probability, odds;
support, resistance, entry point, pivot, breakout, breakdown, level, levels;
yield, annualized, return on collateral. If a supplied label contains one of
these words, refer to the figure by its calculation name instead of that
label. Write your
What was verified subsection from this run's evidence — the calculations and
sources you actually used, their as-of dates, one thing you cross-checked,
and one thing you could not verify — never as a reusable template.
```

Design notes:
- The lexicon deliberately merges the F-4 classes with the document-scan list
  so the model learns one never-list, not two.
- "momentum" sits in `_F4_FORECAST_RE` — Technical loses a habitual word and
  the passage says so explicitly rather than hoping.
- The passage stays inside the reviewed-static-prompt regime: it contains no
  banned phrase in imperative-example form that the request-time scans would
  reject (it names words as prohibitions, exactly as `P36_CORE_B` already
  does; RULING-T5A1-1 exempts the exact reviewed static prompt from the
  prohibited-phrase scan, and this block goes through the same review).

### 3.2 Fundamentals + News (F-5 survivors)

Role-block deltas (verbatim insertions, placed after each block's "You never
estimate a number…" opening paragraph):

Fundamentals:

```text
Every figure you write must be one the ratio, period-change, or freshness
calculations returned to you in this run, restated at the same or fewer
decimal places. When only the profile was reviewed, your section carries no
figures at all beyond supplied dates — the missing statement record, named
plainly, is the finding. Never describe a payout or income rate with the
banned word for it; name the figure by its ratio calculation instead.
```

News:

```text
Every figure you write is either a supplied date, a day count returned by
the event-window calculation, or a macro-series change returned by the
series calculation, kept in the same sentence as that series' exact name.
Refer to filings as "the 8-K filing" or "form type 10-Q" — a lowercase word
always sits directly before the number. Filing dates and form types come
only from the supplied metadata, and a missing macro lane is named as a gap,
never approximated.
```

Rationale: the run-2 F-5 drops are consistent with exactly three behaviors the
current blocks do not forbid mechanically: derived/aggregated figures, spelled
quantities before unit words, and the capitalized-word+number bigram (form
types and month-dates). The deltas plus §3.1 close all three in the model's
working vocabulary, and the accepted-prose evals (§4) prove the closed form
still yields a useful section.

### 3.3 Technical (F-4.6 survivor)

Role-block delta (verbatim, appended to the paragraph that currently begins
"Write three things, and attribute every figure…"):

```text
Treat attribution as a per-sentence rule, not a section-level one: every
sentence that uses a state word — trend, drawdown, elevated, compressed,
overbought, oversold, or their kin — must itself contain the phrase that
names its basis, and the simplest reliable form is to name the calculation
in that sentence. A sentence you cannot attribute is a sentence you do not
write. Describe realized volatility only by the figure and window the
volatility calculation returned, and never with the annualization word.
```

Rationale: the current block models attribution with examples ("use plain
phrases such as…") and the live model applied them section-wide, not
per-sentence — the exact F-4.6 failure shape. The delta states the per-
sentence contract in the model's own terms and bans the one word
(`annualized`) whose slip would fail the whole report post-acceptance.

### 3.4 Risk (all three families)

Role-block delta (verbatim, appended after "The only instructions you may
give are verification steps."):

```text
Your register is descriptive, and the discipline is mechanical: state what a
calculation reports, where a figure sits relative to a reference point, and
what the freshness inventory says about the inputs — always in sentences
that name the calculation or saved source they come from. You never counsel:
no urging words, no desirability words, no sizing or horizon words, and no
judgment of any figure as acceptable or otherwise — where a reference point
is crossed, say only that it is crossed and by how much per the
calculation. Numbers follow the same rule as figures everywhere in this
desk: only values a calculation returned this run, restated at the same or
fewer decimal places, never recomputed.
```

Rationale: Risk dropped across all three families, which is the signature of
register drift — counseling verbs (F-4 action class), unattributed
interpretation (F-4.6), and helpful arithmetic (F-5). The delta re-anchors
the register and defers the lexicon to §3.1 so there is one source of truth.

### 3.5 Explicitly rejected alternatives

- **Editing `P36_CORE_A`/`P36_CORE_B`:** rejected — shared with the PM
  prompt (§0). Any shared-core edit is a silent PM prompt change.
- **Per-role duplicated lexicons:** rejected — four drifting copies of one
  never-list is how a future word gets missed; one shared constant, four
  small role deltas.
- **Weakening any gate to admit current prose:** out of scope by task
  boundary and by team doctrine — prompts are tuned to gates, never the
  reverse.

## 4. Offline eval matrix (mock provider only; no live calls)

All tests run in the existing offline suites and use fake providers and
synthetic fixtures. Gate modules must show a zero-line diff in this slice.

### 4.1 Accepted-prose canaries (the new proof)

For each of the four roles: a new guidance-compliant section fixture —
realistic prose exercising numbers (surfaced, incl. a fewer-places
restatement), an ISO date, an interpretive sentence with marker, a form-type
mention (news), and the verification subsection — passes its full gate stack:

- publics via `validate_p36_public_analysis_section` and end-to-end through
  `run_tool_mediated_agent_team` with a fake public-loop provider
  (pattern: `_P36PublicLoopProvider`);
- risk via `validate_p36_risk_analysis_section` and the risk-loop pipeline;
- pipeline assertion: all four `live_report_markdown` present and accepted,
  PM synthesis present, `final_synthesis_authored_by=portfolio_manager_agent`.

### 4.2 Adversarial drop canaries (no gate relaxed)

Per role, each canary asserts the exact existing flag:

| Family | Canary shape | Expected flag |
| --- | --- | --- |
| F-5 digit | one unsurfaced decimal in otherwise-accepted prose | `numeric_provenance_blocked` |
| F-5 bigram | `The 8-K…` / `Form 10-Q…` sentence-initial | `numeric_provenance_blocked` |
| F-5 spelled | `two days stale` with 2 unsurfaced | `numeric_provenance_blocked` |
| F-5 precision | surfaced 49.9 restated as 49.958 | `numeric_provenance_blocked` |
| F-5 trailing zeros | surfaced 49.9 restated as 49.90 | accepted (numeric Decimal equality; assert no flag) |
| F-4.6 | trigger word, no marker in sentence | `attribution_required_blocked` |
| F-4 per class | one canary per banned class per role (existing families retained) | `advice_boundary_blocked` |
| F-8 | heading/word-bound/table violations (existing) | `structure_contract_blocked` |
| F-9 | boilerplate verified line (existing) | `what_was_verified_blocked` |
| F-11 | filing-content phrasing; unbound series figure (news) | `grounding_blocked` |
| Document scan | `annualized`/`yield`/`support` inside an *accepted* section | `validate_agent_team_report_output` raises |

### 4.3 Frozen readback and PM invariants

- Freeze the accepted five-role run; `SavedToolMediatedRunArtifactRead
  .model_validate` round-trips byte-stable with **zero** provider calls
  (existing pattern, re-asserted over the new fixtures).
- **PM unchanged, digest-pinned:** the test hard-codes a **SHA-256 baseline
  digest** of `P36_PM_SYSTEM_PROMPT` — computed once from the pre-slice
  module and written into the test as a literal — and asserts the live
  constant still hashes to it. A self-referential "equals its current value"
  comparison is explicitly rejected: it would follow an accidental edit
  instead of catching one. Additionally: `p36-pm-synthesis-v1` untouched,
  the PM renderer's output contains no substring of
  `P36_ANALYST_GATE_DISCIPLINE`, and `p36_pm_prompt.py` shows a zero-line
  diff in this slice.
- Registration test: the four analyst prompts registered are exactly the new
  reviewed contents under `p36-role-analysis-v1`; the superseded contents are
  no longer registered.
- Branch canaries from T6/T7 remain green (legacy-family strings never appear
  in a p36-mode run).

### 4.4 Active-lane label audit (promoted from residual into K2B acceptance)

Required offline synthetic test (Codex B blocker resolution; formerly the §7
deferred residual):

1. build active-lane `ToolResult` fixtures for every lane the run activates
   (FMP EOD/technical calculations, EDGAR profile and filings metadata,
   macro-series and event-window calculations, freshness inventory) with
   realistic value labels; fixture fact labels must come from the real label
   path — `prompt_fact_labels_for_tool_result` over envelopes produced by
   the real lane normalizers from realistic synthetic payloads — never
   hand-authored label strings, so the canary audits the labels the runner
   would actually surface;
2. produce accepted prose for all four analyst roles **plus the PM** over
   those fixtures (the §4.1 guidance-compliant fixtures);
3. compose the full report through the deterministic composer;
4. run the complete document output-safety validator
   (`validate_agent_team_report_output`) over the composed payload;
5. assert it passes — proving active FMP/EDGAR/calculation labels introduce
   no banned document text (`annualized`, `yield`, `return on collateral`,
   or any other `P35_PROHIBITED_REPORT_PATTERNS` / invented-level /
   display-token / source-leak hit) through prose or label-quoting table
   cells.

**Stop rule:** if this canary finds a label conflict, Codex C stops and
requests a separate display-label contract (Codex B + Claude G review). No
automatic label scrub, gate change, or source change is permitted in K2B.

### 4.5 Acceptance criteria

New tests pass, including the §4.4 label-audit canary and the §4.3 PM
SHA-256 digest pin; the full offline suite passes; `git diff` is empty for
`auditing/`, `safety/`, `llm_clients/`, schemas, and `p36_pm_prompt.py`; the
only source diffs are `p36_risk_prompt.py`, `p36_public_prompts.py`, and
tests; doc-parity between this design's verbatim blocks and the registered
constants; **K2B is offline-only** — no live provider, market-data, or EDGAR
call anywhere in the slice.

## 5. Prompt version and migration/readback treatment

**Keep `P36_ROLE_PROMPT_VERSION = "p36-role-analysis-v1"`. No bump; no
migration.**

- The version string is the *gate-contract family key*: frozen-artifact gate
  selection maps `{p36-role-analysis-v1, p36-pm-synthesis-v1}` to the v3 gate
  family (`frozen_artifact_gate_version`, `v3_value_gates.py:397`). A new
  version string would require extending that set — a validator change this
  slice forbids.
- Readback safety is unaffected by wording: frozen artifacts revalidate
  through gates only, never by re-rendering prompts or re-running providers,
  and stored `prompt_version` strings on historical runs remain valid v3
  keys.
- Request-time safety is registration-keyed: `ReviewedStaticSystemPrompt`
  registration is by exact content, so the revised blocks must pass the same
  Claude G static-prompt review to inherit the RULING-T5A1-1 exemption. This
  document is the review vehicle; the revision is recorded here as
  **wording revision r2 within the v1 contract**.

Clarified per Codex B review (K2A-R1): `p36-role-analysis-v1` is a **v3
gate-family key, not an exact-wording identifier** — nothing in the
frozen-artifact contract binds the string to specific prompt bytes. There is
no artifact migration to perform: frozen reports revalidate through the same
v3 gates and never rerun prompts or providers. The `r2` label is
**documentation-only provenance** (this document and the plan record),
carried nowhere in code, schemas, or artifacts. A future additive
`prompt_revision` metadata field was considered and is explicitly deferred
out of K2A/K2B scope.

## 6. Smallest Codex C handoff (the K2B slice, after design review)

1. `p36_risk_prompt.py`: add `P36_ANALYST_GATE_DISCIPLINE` (verbatim §3.1);
   append it in `render_p36_risk_system_prompt()`; insert the §3.4 risk
   delta into `P36_RISK_ROLE_BLOCK`.
2. `p36_public_prompts.py`: insert the §3.2/§3.3 deltas into the three role
   blocks; append the shared constant in `render_p36_public_system_prompt()`.
   Do not touch `p36_pm_prompt.py`.
3. Tests: §4 matrix — new accepted-prose fixtures, adversarial canaries not
   already present, the §4.4 active-lane label-audit canary (stop rule
   honored on any conflict), the §4.3 PM SHA-256 digest pin, registration
   exactness.
4. Doc-parity: blocks in code byte-match this document.
5. Verification: offline pytest only; report exact counts and the zero-diff
   assertion for gate/safety modules. No live calls. Do not commit until
   Codex B review and Claude G's static-prompt review both PASS.

## 7. Resolution record — Codex B design review (K2A-R1)

Both Codex B blockers are resolved in this revision:

1. the active-lane label audit moved from a deferred residual into **K2B
   acceptance** as §4.4 — an end-to-end offline canary (fixtures → accepted
   prose for all five roles → composed report → full document output-safety
   validator), with the stop-and-request-a-display-label-contract rule
   replacing any in-slice remediation. The known candidates remain
   `annualized` in volatility labels and `yield` in ratio labels
   (RULING-T5A2-1 already scrubs FRED display strings);
2. PM invariance strengthened from a self-referential snapshot comparison to
   the hard-coded SHA-256 baseline digest in §4.3, alongside the
   `P36_ANALYST_GATE_DISCIPLINE`-absence assertion and the zero-diff
   requirement on `p36_pm_prompt.py`.

Section 5 was clarified in place: the version string is a v3 gate-family
key, not a wording identifier; no artifact migration exists; `r2` is
documentation-only provenance; the additive `prompt_revision` field is
deferred out of scope.

## 8. Resolution record — Claude G static-prompt review (K2A-G)

PASS with three required edits, applied in place in this revision
(2026-07-20):

1. the Section 4.2 precision canary was corrected to Decimal-equality
   semantics: `_numeric_allowed` compares numerically first, so a
   trailing-zero restatement (49.90 of surfaced 49.9) is accepted; only a
   numerically different added-precision figure (49.958) blocks. Section 1's
   F-5 bullet was reworded to match;
2. the Section 3.1 never-list gained the document-fatal vocabulary that the
   composed-report scan and invented-level patterns ban outside the F-4
   classes — probability, odds, bare target, support, resistance, entry
   point, pivot, breakout, breakdown, level(s) — and the Section 4.2
   document-scan canary now includes `support`;
3. Section 4.4 step 1 now pins fixture fact labels to the real
   `prompt_fact_labels_for_tool_result` label path over envelopes from the
   real lane normalizers, so the label audit exercises the labels the runner
   would actually surface.

Deferred polish recorded by the review, not applied here: add `acceptable`
to the never-list on the next reviewed wording revision; fixture authors
should remember the F-4.6 per-sentence scan covers table rows (only heading
lines are exempt) and the long-date/spelled-magnitude traps apply inside
table cells; refresh drifted gate-code line citations on the next doc touch.

The registrable Section 3.1 block and role deltas as they now stand are the
Claude G-approved verbatim texts for K2B registration. Any further wording
change to them requires a fresh Claude G static-prompt review before
registration.
