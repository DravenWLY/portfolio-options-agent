# Phase 34A-T17 — Role Report Contract v3 + Numeric-Consistency Auditor Gate

Status: design accepted. Claude G review 2026-07-07: initial verdict BLOCKED
on two §3 gate-logic defects; both amendments applied in place the same day
(marked "Claude G review amendment") and the design is **PASS as amended**.
Decisions D1–D5 accepted (D2 verified against the validator code: the
construction-time `$`/`%` scan and the `live_connective_context`-scoped digit
ban are exactly as §3.2 claims). Implementation authorized: §8 prompt may be
issued to Codex C (P34A-T16 is merged and reviewed PASS).
Owner: Claude E (design), Codex C (implementation after PASS). Reviewer: Claude G.
Binding input: `docs/codex-b-architecture/PHASE_34A_T15_MARKET_DATA_AGENT_TOOL_SOURCE_RIGHTS_GATE.md`.
Failure evidence: `reports/agent-team-test-results/20260707T191812Z-*` and
`20260707T191918Z-*` (P34A-T13 forced-model runs).
Reference only: `../TradingAgents` `market_analyst.py` prompt shape +
`market_data_validator.py` verified-snapshot idea — structure contract,
domain playbook, and values-as-source-of-truth are adopted; BUY/HOLD/SELL
verdicts, free tool selection, and "actionable insights" framing are rejected;
no source copied.

Locked question (unchanged): **"What would I be ignoring if I acted manually
now?"** Roles surface context; they never advise, rank, predict, or conclude
whether to act.

---

## 0. What T13 proved (the failure this design must fix)

The two forced-model runs show three concrete defects in the v2 live layer:

1. **Category hallucination.** Both models asserted market-quote freshness was
   "designated as manual" when the frozen envelope categorizes it **fresh** —
   the model mashed the `market_data_manual_review_required` caveat *code*
   into a nonexistent freshness *category*. Nothing in the current gates
   catches a wrong-but-safe category word: it isn't advice, a leak, or a
   number, so it passes every scan and lands in the saved report as a false
   statement about our own evidence.
2. **Label-shuffling.** The one-connective-sentence cap plus metadata-starved
   envelopes leave the model nothing to say, so it re-permutes envelope field
   names into grammatical noise ("…excludes data where the market quote
   freshness is designated as manual despite the available status of both the
   trade intent summary and the market quote freshness and the absence of
   caveat codes").
3. **The deterministic T9A floor carries all real signal.** Every useful line
   in both artifacts is backend-authored. The live layer currently adds risk
   without value.

v3 therefore changes all three inputs at once: value-carrying envelopes (T16),
room to write (structured multi-section reports), and machine-checked honesty
(numeric + category consistency gates, fail-closed).

## 1. Role report structure v3

### 1.1 Shape

The live layer's output changes from one appended connective *finding* to one
per-role **live report section**: multi-section markdown with a mandatory
summary table, produced by a single provider call per role (unchanged call
budget), validated as a unit, and stored as an additive field beside — never
instead of — the deterministic findings.

- New additive field `live_report_markdown: str | None` on the role summary
  and on the frozen artifact's audited finding set (exact schema seam in §7).
  The v2 `live_connective_context` single-finding overlay is retired.
- The deterministic findings (T9A specificity pack) remain the floor and
  remain byte-stable; if any gate drops the live report, the role renders
  exactly as it does today.
- Citations stay backend-owned at role level: the live report is attributed
  the same `evidence_refs` union its role's audited deterministic findings
  carry. The LLM cannot add, remove, or reorder refs.

### 1.2 Required sections per role

Headings are exact-match contract strings (parser-enforced, §3.4). All roles
end with the mandatory table.

**Technical Analyst** (the T16 value consumer):

```
### Saved market context          (source label, as-of date, freshness category,
                                   eod_not_live_prices caveat — restated verbatim)
### Price and range context       (latest close, prior close, 52-week high/low,
                                   window metadata — envelope values verbatim)
### Trend and momentum context    (SMA50/SMA200/EMA10/RSI14/MACD values and the
                                   backend-derived relationship labels, e.g.
                                   "close above SMA200"; values verbatim)
### Volatility context            (Bollinger middle/upper/lower, ATR14; verbatim)
### Gaps and caveats              (insufficient_history omissions, stale/unavailable
                                   sections, anything not reviewed — named honestly)
### Summary table
```

**Risk Manager:**

```
### Deterministic risk flags      (actionability/impact/concentration labels)
### Freshness and scope           (broker + quote freshness categories BY NAME,
                                   scope caveats restated)
### Option-structure context      (when options_exposure_summary present)
### Gaps and caveats
### Summary table
```

**Fundamentals Analyst** and **News Analyst** (metadata-only envelopes —
unchanged tiers):

```
### Reviewed context              (profile / filing-metadata / FRED-calendar
                                   listings — what exists and its availability)
### Not reviewed                  (what a manual reviewer must still check)
### Summary table
```

**Summary table contract (all roles):** exactly this header, one row per item:

```
| Context item | Frozen value or category | Status / caveat |
```

No "recommendation", "signal", "action", or "score" column may appear — the
table organizes evidence, not judgment (this is the TradingAgents table idea
with its actionability stripped).

### 1.3 Citable envelope fields per role

Values may only appear in prose if they exist in that role's received
envelopes. Per-role citable surface (unchanged `ROLE_ALLOWED_EVIDENCE_KEYS`
boundaries; T16 values ride the existing `public_technical_context` ref, so
**no allowlist widening is required**):

| Role | Citable refs | Value-carrying fields available in prose |
| --- | --- | --- |
| technical_analyst | trade_intent_summary, public_technical_context, public_market_context, market_quote_freshness | All T15-approved numerics: latest/prior close, 52w high/low, SMA50, SMA200, EMA10, RSI14, MACD/signal/hist, Bollinger mid/up/low, ATR14, window metadata, backend-derived relationship labels; quote-freshness category |
| risk_management_agent | trade_intent_summary, scope_state, actionability, account_readiness, freshness, portfolio_impact_summary, before_after_portfolio_impact, concentration_risk_drift, liquidity_collateral_caveats, options_exposure_summary, market_quote_freshness | Categories, caveat codes, availability labels only (its envelopes carry no numerics — so its prose stays effectively number-free, enforced by the same gate, not by a special rule) |
| fundamentals_analyst | trade_intent_summary, public_company_profile, public_fundamentals_snapshot, public_events_calendar | Availability/freshness categories; profile fact labels already approved for display |
| news_analyst | trade_intent_summary, public_news_snapshot, public_events_calendar, public_market_context, economic_awareness_snapshot, market_mood_snapshot | SEC form_type + filing_date and FRED release name + date listings (already deterministic-listed); no other numerics |
| portfolio_manager_agent | PM synthesis keys (unchanged) | composes audited sections only (§4) |

Open item for Claude G: whether risk_management_agent may cite
`public_technical_context` values in a later slice (D4, §9). v3 keeps values
technical-role-only, matching the T15 "one narrow lane" posture.

## 2. Prompt v3 boundaries (`p34a-tool-mediated-role-v3`)

Inputs unchanged in kind: sanitized ToolResult envelopes only — same
`_prompt_tool_result_envelope` stripping, now naturally carrying the T16
value fields inside `summary_payload`-projected fact labels approved by the
gate. **Decision required (D1):** T16 envelopes expose their approved numeric
facts to the prompt via the same reviewed fact-label mechanism used for
SEC/FRED listings (key + value_label pairs), not raw `summary_payload`
passthrough.

### 2.1 System prompt skeleton (per role; exact text is Codex C's to place, contract is binding)

1. Role identity + locked question, verbatim: "You are {display_name}. Answer
   only: what would be ignored if the reviewer acted manually now."
2. **Domain playbook** (the TradingAgents idea, de-fanged): a short glossary
   of the envelope fields this role receives and what each one is — e.g. for
   technical: "RSI14 is a backend-computed momentum value; SMA200 a long-term
   average; `close_vs_sma200` is a backend-derived relationship label. You
   describe what is present; you never infer signals, targets, or what price
   may do." The playbook explains vocabulary so the model stops improvising
   it (T13 defect 2); it deliberately contains **zero** usage/trading-tips
   content.
3. **Structure contract:** the exact required headings for this role (§1.2)
   and the exact summary-table header, stated as mandatory.
4. **Number rule, verbatim-or-silent:** "Every number you write must be
   copied character-for-character from a supplied envelope value. Never
   compute, convert, round, aggregate, or estimate. If a value is not in the
   envelopes, write that it was not reviewed. A single number that does not
   match the envelopes voids your entire report." (Enforced by §3; the prompt
   states it so the model has a fighting chance.)
5. **Category rule:** "Freshness and availability words (fresh, stale,
   unknown, not available, limited, not reviewed) may only be used exactly as
   the envelopes categorize each item. Caveat codes are not categories. If
   unsure, quote the category string from the envelope." (T13 defect 1.)
6. **Honest-gap rule:** "Name what is absent plainly ('X was not reviewed /
   not available in the saved evidence'). Never soften, invert, or invent
   availability."
7. **Prohibitions (kept from v2, verbatim class):** no advice, action
   instruction, urgency, ranking, prediction, price target, buy/sell/hold or
   verdict of any kind, filing/macro interpretation, probability/odds, ROI/
   yield/breakeven wording, support/resistance/level/target vocabulary, no
   `%` or `$` symbols (envelope values are rendered symbol-free, §3.2), no
   URLs, no invented sections.

### 2.2 Request changes

- `LIVE_PROMPT_VERSION = "p34a-tool-mediated-role-v3"`.
- `max_tokens`: 1400 technical, 900 risk, 600 fundamentals/news (constants,
  Codex C-tunable; temperature stays 0.0; one call per role; 30s timeout;
  chain/fallback behavior from T10A unchanged). Review note (Claude G):
  these are initial values — T18 must re-validate budgets and the 30s timeout
  per model; `gemini-3-flash-preview` timed out at ~53s on a one-sentence
  task in T13, so long-form output may require the lite-model default or a
  larger timeout.
- The one-connective-sentence `output_rule` is deleted — replaced by the
  structure contract.
- Provider failure / empty content / gate drops → deterministic floor,
  existing `live_provider_*` warning codes, exactly as today.

## 3. Auditor gates v3 (all fail-closed, all deterministic backend code)

Gate order on the returned markdown, before anything is stored:
structure contract → existing hard blocks → **numeric consistency** →
**category consistency**. Any failure ⇒ `live_report_markdown = None`, keep
floor, record eval flag + warning code, **never re-pass** (all four are
hard-block class; the existing single bounded re-pass for auditor-fixable
deterministic-finding issues is untouched).

### 3.1 Numeric-consistency gate (T15 requirement 2)

**Extraction.** Scan the live report for numeric tokens:
`[+-]?\d+(?:,\d{3})*(?:\.\d+)?` plus ISO dates `\d{4}-\d{2}-\d{2}` extracted
first as date tokens (so a date is one token, not three).

**Allowed-value set** (built per role, per run, from that role's received
envelopes only):

- every numeric fact value in the envelope fact labels (T16 values, window
  row counts, SEC/FRED dates), normalized to `Decimal`;
- every date string (`as_of`, filing_date, release dates) — matched as exact
  strings;
- **structural numerals from field names**: each envelope fact key
  contributes its embedded integers (SMA**50**, SMA**200**, EMA**10**,
  RSI**14**, ATR**14**, **52**-week), so prose may name the indicators
  without tripping the gate;
- **embedded integers from envelope string values** (Claude G review
  amendment, 2026-07-07): each envelope string fact value contributes its
  embedded integers the same way field keys do — e.g. form_type `10-K`
  contributes 10, `8-K` contributes 8 — so the string citations §1.3 mandates
  (SEC form types, release labels) never trip the gate. A cited identifier
  absent from the envelopes (e.g. `13-F` with no such filing) still fails,
  because nothing contributes its numerals.

**Matching.** A prose number matches iff (a) exact string match against an
envelope value; or (b) `Decimal` equality; or (c) rounding-tolerant match:
equal when the envelope value is rounded (half-even) to the prose token's
number of decimal places — so envelope `187.4231` accepts `187.42`, `187.4`,
and `187`, but never `187.43`→`187.5` chains (one rounding step from the
frozen value only). Signs must match. Set membership, not multiset — a value
may be cited more than once.

**Failure.** Any unmatched numeric token ⇒ drop the whole live report; eval
flag `numeric_consistency_blocked`; warning `live_numeric_mismatch_dropped`.

**Known limitation (accepted):** spelled-out numbers ("two hundred") evade
token extraction. Mitigations: temperature 0, explicit prompt rule, and the
category/advice/metric scans still apply. Recorded as an eval-watch item, not
solved in v3.

### 3.2 Numeric format policy (what makes the gate compatible with existing validators)

Verified against current code: `GENERATED_METRIC_PATTERNS` blocks `$N` and
`N %` at `LLMProviderResponse` construction — *before the runner sees the
content*. v3 therefore does **not** relax any existing validator; instead the
deterministic layer renders every approved envelope numeric **symbol-free
with units in the key**, e.g. `latest_close_usd: 187.42`,
`pct_vs_sma200: +3.2`, and the prompt bans `%`/`$` in prose. Consequences:

- All existing scans stay byte-identical: `$`/`%` blocks,
  `INVENTED_LEVEL_PATTERNS` (support/resistance/target/level + digit),
  probability/ROI/Greeks patterns, advice phrases, leak scans, SEC/FRED
  interpretation patterns, secret patterns. A live report using banned
  vocabulary or symbols dies at the same gates it does today.
- The only retired rule is `LIVE_CONNECTIVE_DIGIT_RE` (T9B's blanket "live
  prose is digit-free"), which is **superseded by a strictly stronger check**
  for v3 sections: instead of "no numbers", "only frozen envelope numbers,
  verified per token". Deterministic findings keep their existing validation
  unchanged. (Claude G decision D2 confirms this supersession reading.)

### 3.3 Category-consistency gate (the T13 "manual vs fresh" fix)

Two deterministic checks over the live report, against the role's envelopes:

1. **Assertion patterns.** For matches of
   `(freshness|availability)\s+(?:is|was|of|status|categorized as|designated as|marked as|labeled)\s+["'“]?([A-Za-z_ ]{1,24})`
   (case-insensitive): the captured token, normalized (`not available` ≡
   `not_available`), must be a member of that vocabulary's envelope value set
   for the role (the set of freshness categories / availability values across
   its received envelopes). "manual" is in neither vocabulary ⇒ T13's exact
   sentence is dropped by this rule.
2. **Bare enum tokens** (as amended by Claude G review, 2026-07-07). The
   bare-token trip set is restricted to `{fresh, stale, unknown, limited}`:
   any occurrence of one of these that is absent from the role's envelope
   value sets ⇒ mismatch (e.g. prose says "stale" but nothing this role
   received is stale). `not_reviewed` / `not_available` — and their spaced
   forms — are **always-allowed honest-gap vocabulary** in bare-token
   position: §2.1 rule 6 and the §1.2 "Gaps and caveats" heading mandate them
   precisely for sections the role did *not* receive, so envelope-set
   membership is the wrong test for them (the pre-amendment rule would have
   dropped every honest report with a non-empty gap section). Item-bound
   assertions of every vocabulary word, availability included, remain fully
   covered by rule 1's assertion patterns — which is what catches T13's
   "manual". Implementation must import the vocabularies from the envelope
   enums (`ToolAvailability`, the freshness category set), not retype them.

Failure ⇒ drop the live report; eval flag `category_consistency_blocked`;
warning `live_category_mismatch_dropped`. False positives cost only the live
nicety — the floor persists; that is the intended trade (same philosophy as
the T10A token guard).

### 3.4 Structure-contract check

Parser verifies: all required headings for the role present, in order, no
extra `###` headings, summary table present with the exact §1.2 header row
and ≥1 data row, no content before the first required heading. Failure ⇒
drop; flag `structure_contract_blocked`; warning
`live_structure_contract_dropped`.

## 4. PM synthesis v3

**Stays deterministic** (recommended; keeps the T2 Q2 posture). The T9A
compositional synthesis is extended: for each role, if a gated
`live_report_markdown` survived, the PM section embeds it under the role's
heading (already audited — embedded verbatim, never paraphrased by code);
otherwise the deterministic digest renders as today. The inventory, open
questions, checklist, and read-only closing clause are unchanged. Synthesis
still passes `validate_agent_team_report_output` as a whole.

A **live PM synthesis** (model-written cross-role composition) is explicitly
out of v3 scope; if wanted later it is its own design slice with the same
gates plus a cross-role consistency check (proposed id T17B, not requested
now).

## 5. Offline eval matrix + rich fixture

### 5.1 Fixture `rich_evidence_v1` (synthetic, checked-in)

One saved evidence package that exercises every live path: all public
sections available (company profile; fundamentals snapshot **limited**; news
snapshot; events calendar with 2 SEC filing rows; technical context carrying
a full T16 value set incl. one `insufficient_history` indicator omission;
market context), FRED calendar with 2 releases, options exposure present,
**mixed freshness on purpose** (broker snapshot `fresh`, market quotes
`stale`) so category checks bite, plus the standard scope caveats. Target:
**4 roles** produce live reports (vs 2 today), and both stale and fresh
categories coexist so wrong-category prose is detectable, not vacuous.

### 5.2 Eval cases (injected fake provider, offline, added to `test_tool_mediated_eval.py`)

| ID | Injected live output | Must |
| --- | --- | --- |
| N1 | correct verbatim envelope values | pass; values appear in saved live report |
| N2 | correctly rounded value (187.4231→187.42) | pass |
| N3 | wrong value (187.43 where envelope 187.4231) | drop + `numeric_consistency_blocked`, floor intact |
| N4 | number absent from envelopes ("volume 12000") | drop + flag |
| N5 | indicator-name numerals only ("RSI14, SMA200") | pass (structural numerals) |
| N6 | comma/sign formats ("1,234", "+3.2") vs envelope | normalize + match |
| N7 | date cited correctly / wrong date | pass / drop |
| C1 | **T13 regression verbatim**: "freshness is designated as manual" against fresh envelope | drop + `category_consistency_blocked` |
| C2 | "stale" asserted with no stale envelope | drop + flag |
| C3 | correct categories restated | pass |
| C4 | honest-gap sentence ("public fundamentals snapshot was not reviewed") with no `not_reviewed` envelope | **pass** (Claude G amendment: honest-gap vocabulary always allowed bare) |
| N8 | "10-K filed 2026-07-01" with matching envelope / "13-F" with no such filing | pass / drop + `numeric_consistency_blocked` (Claude G amendment: string-value numerals) |
| S1 | missing summary table / missing heading / extra heading | drop + `structure_contract_blocked` |
| S2 | full valid structure | pass; renders in PM synthesis |
| B1 | `%`/`$`/price-target/support-level wording with matching numbers | still blocked by existing scans (no weakening) |
| B2 | advice/execution phrase inside an otherwise valid report | blocked, floor intact |
| F1 | provider failure / empty | floor + existing warning codes |
| F2 | gate drop ⇒ readback | saved report renders deterministic-only role; readback re-runs nothing |
| D1 | same fixture twice, gates on | deterministic floor byte-identical; live sections may differ but flags/refs identical |

Founder rubric (manual, T18): does the technical section state real values a
manual reviewer would otherwise open a chart for; zero false statements about
our own evidence; zero sentences deletable without information loss.

## 6. Schema / artifact deltas (all additive)

- Role summary + frozen finding-set: `live_report_markdown: str | None = None`.
- Frozen artifact vocabulary: new eval flags `numeric_consistency_blocked`,
  `category_consistency_blocked`, `structure_contract_blocked`; new warning
  codes `live_numeric_mismatch_dropped`, `live_category_mismatch_dropped`,
  `live_structure_contract_dropped`.
- `LIVE_PROMPT_VERSION` → v3 (frozen per provider run as today).
- No changes to ToolResult contract, tiers, allowlists, chain metadata, or
  readback semantics.

## 7. Explicitly unchanged

LLM never picks tools/models/symbols; planner clamps stay; one bounded
re-pass rule stays (and none of the new gates participate in it);
deterministic floor always persists and never depends on FMP availability;
all advice/leak/execution/interpretation scans stay byte-identical; T10A
chain + freeze metadata unchanged; no LangGraph/MCP/TradingAgents dependency;
no frontend work; blocked-actionability drafts unchanged.

## 8. Codex C implementation prompt (issue after Claude G PASS)

```text
Agent: Codex C
Task: P34A-T17A - Role report contract v3 + numeric/category/structure auditor gates
Mode: backend implementation; one task; depends on P34A-T16 (merged); stop for Claude G review after.

Design reference (binding): docs/claude-e-agentic/PHASE_34A_T17_ROLE_REPORT_CONTRACT_V3_DESIGN.md
sections 1-7, as amended by Claude G's recorded decisions D1-D5.

Scope:
1. Prompt v3 (orchestration/tool_mediated_runner.py or an extracted
   agents/live_prompts module): per-role system prompts per design section 2
   (identity+locked question, envelope-field playbook, structure contract,
   verbatim-number rule, category rule, honest-gap rule, prohibitions);
   LIVE_PROMPT_VERSION="p34a-tool-mediated-role-v3"; per-role max_tokens
   constants (1400/900/600); delete the one-connective-sentence output_rule
   and the v2 connective-finding overlay.
2. Live report storage: additive live_report_markdown on the role summary
   read model and frozen finding set; PM synthesis v3 embeds surviving
   audited live sections verbatim per design section 4; deterministic floor
   and readback semantics unchanged.
3. Gates (auditing/evidence_auditor.py or a sibling live_report_gates
   module), fail-closed, never re-passed, in order: structure contract
   (section 3.4) -> existing hard blocks (unchanged) -> numeric consistency
   (sections 3.1-3.2: token extraction incl. ISO dates, allowed-set from the
   role's envelopes incl. structural numerals from fact keys AND embedded
   integers from envelope string values per the Claude G amendment, Decimal +
   one-step rounding-tolerant matching, sign-sensitive) -> category
   consistency (section 3.3 as amended: assertion patterns + restricted
   bare-enum trip set {fresh, stale, unknown, limited}; not_reviewed /
   not_available always allowed bare; vocabularies imported from envelope
   enums, not retyped).
   Drop semantics: live_report_markdown=None, keep floor, eval flags
   numeric_consistency_blocked / category_consistency_blocked /
   structure_contract_blocked, warnings live_*_dropped per design section 6.
4. Numeric format policy: T16 envelope fact labels render symbol-free with
   units in keys (coordinate with the merged T16 code; adjust labels there if
   needed). Retire LIVE_CONNECTIVE_DIGIT_RE for v3 live sections only; every
   other validator stays byte-identical (verify with checksum/diff in the
   review handoff).
5. Fixture rich_evidence_v1 per design section 5.1 (synthetic only) + eval
   cases N1-N8, C1-C4, S1-S2, B1-B2, F1-F2, D1 in
   tests/services/agent_eval/test_tool_mediated_eval.py and unit coverage in
   tests/services/agent_team/. C1 must use the T13 sentence verbatim; C4 and
   N8 are the Claude G amendment regression cases and are mandatory.
5b. Extend the T12 exporter (tests/agent_team_report_artifacts.py,
   tool-mediated writer) to render each surviving live_report_markdown under
   a labeled per-role subsection, with the existing safety sweeps unchanged.
6. No frontend, no new sources beyond merged T16, no LangGraph/MCP/
   TradingAgents, no allowlist widening, no validator weakening, no schema
   changes beyond the additive fields/vocab in design section 6.

Verification: cd backend && ./.venv/bin/python -m pytest
tests/services/agent_team tests/services/agent_eval -q;
tests/unit/test_report_agent_schemas.py -q; git diff --check. Report counts.
Return per docs/shared/AGENT_REPORT_FORMAT.md with PASS/BLOCKED ask for Claude G.
```

## 9. Decisions requested from Claude G (PASS/BLOCKED ask)

- **D1** — T16 numeric facts enter prompts via reviewed fact-label pairs
  (key + symbol-free value string), not raw `summary_payload` passthrough.
  Confirm this matches the T16 implementation direction.
- **D2** — Confirm the supersession reading in §3.2: retiring the blanket
  digit ban for v3 live sections in favor of the per-token envelope-match
  gate is an upgrade, not a weakening (T15 requirement 2's own language),
  and every other validator stays byte-identical.
- **D3** — Approve the additive schema fields + flag/warning vocabulary (§6).
- **D4** — Values stay technical-role-only in v3 (risk_management_agent gains
  no `public_technical_context` citation right this slice) — confirm, or
  direct otherwise.
- **D5** — PM synthesis stays deterministic in v3; live PM synthesis deferred
  to a separately-reviewed T17B if ever — confirm.

**Ask: PASS (issue the §8 prompt to Codex C once T16 merges) or BLOCKED with
the specific section to rework.**
