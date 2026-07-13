# Phase 36 - Five-Agent Activation Contract

Status: draft architecture contract; pending Claude G review.
Owner: Codex B.
Date: 2026-07-11.
Related: Phase 34A live tool-mediated contract, Phase 34A-T6 source-rights
gate, Phase 36 five-role domain design, and Phase 36 gate/prompt
compatibility review.

## Purpose And Precedence

Phase 36 makes the internal working version of Portfolio Copilot a five-role,
read-only review desk. It does not make the product an execution system, an AI
stock picker, or a source crawler.

This contract amends the Phase 34A contract only for Phase 36 v3 runs. Where
the Phase 34A contract conflicts with this document, this document controls for
the Phase 36 scope. All other Phase 34A privacy, source-rights, frozen-readback,
and backend-mediation protections remain in force.

The locked product question remains:

> What would a manual reviewer acting right now overlook in the saved evidence?

The five live roles are Technical Analyst, Risk Manager, Fundamentals Analyst,
News Analyst, and Portfolio Manager. Planner and Evidence Auditor remain
run-state-only meta roles; they are not user-facing analysts and are not part of
the five-role acceptance count.

## 1. Unchanged Hard Boundaries

Phase 36 does not relax these boundaries:

- Read-only: no order placement, staging, cancellation, execution, or broker
  automation.
- Backend mediation: an LLM may propose a structured request, but the backend
  validates role, source lane, arguments, budget, and tier before it executes a
  tool. The LLM never receives a provider, broker, database, browser, or tool
  binding.
- Deterministic ownership: backend code computes every financial value,
  calculation, and value label. Agents may analyze only sanitized evidence and
  deterministic calculation results.
- Privacy: LLM-visible data may contain the reviewed public symbol/company name,
  the account nickname, and reviewed envelope- or calculation-sourced portfolio
  values. It may never contain raw account or provider identifiers, account
  numbers, credentials, secrets, raw payloads, tax-lot detail, unreviewed
  account fields, prompts, traces, or logs.
- Evidence mediation: prompts receive only role-approved sanitized envelopes,
  accepted prior sections, and frozen calculation results. They never receive
  raw `summary_payload`, current selectors, current Account Details, or source
  URLs.
- Frozen reproducibility: generation freezes used evidence, tool results,
  accepted live content, safe provider metadata, and version keys. Reopening or
  regenerating a saved report must not refetch sources, rerun providers, or
  recompute from current account state.
- No-advice boundary: no recommendation, rating, action cue, sizing, target,
  horizon, forecast, likelihood claim, guaranteed-return claim, or overall
  trade verdict. Verification-only imperatives remain allowed.

The revised Phase 36 identifier-privacy rule is internal-prototype-only. Any
external or multi-user deployment reopens the privacy and source-rights decisions
before deployment. It does not authorize a broader product surface today.

## 2. P34A Amendment: Gated Live Portfolio Manager

The deterministic-only Portfolio Manager decision -- recorded as the M1
milestone posture in
`PHASE_34A_T2_LIVE_ROLE_PROMPT_AUDITOR_DESIGN.md` (Codex B Q2:
`portfolio_manager_agent stays deterministic in M1`) and carried into
`PHASE_35_T7C_ROLE_PROMPT_CONTRACT_DESIGN.md` section 3e (`Portfolio Manager:
stays deterministic -- no PM live prose`; `final_synthesis_authored_by:
deterministic_template`) -- is superseded for Phase 36 v3 runs. Both prior
statements are explicitly retired for v3. The P34A-T0 contract already permits
LLM synthesis; only the M1 milestone deferred a live PM. V2-frozen reports
continue to render their deterministic PM under F-13 version-keyed readback.

The Portfolio Manager may run one gated, structured live synthesis after the
four analyst loops complete. It receives only:

- accepted analyst sections with role attribution;
- deterministic findings, approved values, gaps, and Auditor flags;
- the reviewed trade-intent summary; and
- its own validated calculation results from the frozen package.

It may re-request any approved calculation for verification within its budget;
it cannot access a provider, current account state, dropped content, or raw tool
payloads. Pending or unavailable source lanes return a named unavailable
envelope, including for the PM.

`PmSynthesis` is structurally limited to these required fields:

1. `evidence_weighting`: what portions of the saved evidence deserve more or
   less confidence and why.
2. `evidence_tensions`: unresolved conflicts, differing vintages, or coverage
   gaps, plus what evidence would resolve them.
3. `verification_priorities`: two to five verification-only imperatives using
   the approved verb set: verify, check, confirm, review, re-sync, compare.
4. `trust_assessment`: how much weight the saved evidence can bear and which
   caveats dominate that assessment.

There is deliberately no rating, verdict, conclusion, action, position, price,
time-horizon, or overall-status field. The validator must reject any extra or
renamed field that could encode an overall trade verdict.

The deterministic composer remains document author. It always renders the
deterministic summary floor. It appends the PM block only when strict JSON shape,
content, provenance, identifier-privacy, grounding, and advice-boundary gates
all pass. Any PM hard block, parse failure, timeout, or provider failure drops
the whole PM block and leaves the deterministic summary intact. A blocked or
deterministic-draft report never calls the PM.

## 3. Free-Tier Operations Policy

All external API use in Phase 36 is free-tier-only and internal-prototype-only.
There is no scraping, key sharing, silent provider substitution, background
crawling, bulk ingestion, or multi-user deployment assumption.

All outbound-source budgets are backend Tier 1 configuration. Defaults are
deliberately conservative and must be test-overridable:

| Constant | Default | Rule |
| --- | ---: | --- |
| `P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET` | 10 | Count every FMP endpoint call; stop at the cap for the UTC day. |
| `P36_FRED_SERIES_DAILY_REQUEST_BUDGET` | 18 | Count every FRED series request; stop at the cap for the UTC day. |
| `P36_EDGAR_DAILY_REQUEST_BUDGET` | 60 | Count every EDGAR submissions/index request; stop at the cap for the UTC day. |
| `P36_EDGAR_MAX_REQUESTS_PER_SECOND` | 1 | Process-wide upper bound, intentionally below SEC fair-access guidance. |
| `P36_LLM_CALLS_TYPICAL` / `P36_LLM_CALLS_HARD_CAP` | 10 / 19 | Per saved-report run. |
| `P36_TOOL_REQUESTS_TYPICAL` / `P36_TOOL_REQUESTS_HARD_CAP` | 20 / 40 | Per saved-report run. |

The defaults are operations guardrails, not statements of a provider's current
free-tier entitlement. Codex C verifies current endpoint eligibility and
servable behavior through an explicit opt-in smoke before claiming a lane is
available. A denial, quota response, malformed response, unsupported endpoint,
or exhausted local budget returns an honest unavailable result with a named
caveat; it never falls back to an unapproved source.

Every approved external result follows the same lifecycle:

1. Explicit saved-review/report generation may fetch once.
2. The backend normalizes and validates the allowed fields.
3. The normalized snapshot freezes into the saved evidence package with
   source/as-of/period/freshness metadata.
4. All tools and role loops for that frozen package reuse the frozen snapshot.
5. Readback and regeneration reuse frozen evidence; they make zero outbound
   source calls.

Raw responses may exist transiently only while normalizing. They are never
persisted, logged, exposed to prompts, or rendered.

The reusable cache is the normalized snapshot frozen into one saved evidence
package. It is reusable by every role, retry, regeneration, and readback of
that package, and retained with the historical report evidence. There is no
cross-package raw-response cache. A future normalized cross-package cache needs
its own source-rights, revision, and invalidation review.

### 3.1 Gemini Free Tier

Analyst loops run sequentially in the existing `AGENT_TEAM_ROLES` order; the PM
runs last. Sequential execution is both the Phase 36 run-order decision and the
free-tier RPM control. It prevents concurrent roles from racing the shared,
forward-only model fallback chain and makes call/tool counters deterministic.

HTTP 429, timeout, and other configured availability failures use the existing
same-provider model-candidate fallback chain. Authentication and safety failures
do not advance the chain. There is no new provider, no client-selected model,
and no frontend LLM configuration. Exhaustion leaves honest deterministic floors
and unavailable warnings; it cannot be disguised as completed live analysis.

Phase 36 deliberately sets no daily LLM-request constant. Its free-tier LLM
control is the per-run hard cap, sequential execution, and the provider's own
quota response/fallback behavior. A cross-run daily LLM budget requires
production telemetry and a separate operational decision; it is not silently
assumed here.

Parallel analyst loops may be proposed only after P36-T6 records measured quota
headroom and the chain provider passes a dedicated concurrency-safety review.

### 3.2 SEC EDGAR Operations

The P34A-T6 decision remains unchanged: SEC EDGAR is metadata-only. It may use
only normalized form type, filing date, opaque filing reference, freshness, and
approved attribution/caveats. Filing body text, XBRL facts, exhibits, raw paths,
raw URLs, raw accession data, filing interpretation, and SEC-endorsement wording
remain prohibited.

Every EDGAR request requires a configured descriptive product User-Agent with a
maintained contact channel. The User-Agent is backend operational configuration,
never prompt or report content. The one-request-per-second and daily budget
limits above are mandatory. No background crawler or bulk replay is allowed.

### 3.3 FMP Fundamentals Lane

FMP fundamentals is approved only as a normalized reported-statement facts lane
for this internal free-tier prototype. It enables the Fundamentals Analyst's
WITH variant and C11/C12. It does not approve FMP news, article text, URLs,
price targets, ratings, ownership data, or any other FMP product.

The approved normalized `public_fundamentals_snapshot` contains only:

- company/profile identity already allowed by the existing public-company
  profile boundary;
- statement fact groups for income statement, balance sheet, and cash flow;
- reviewed headline facts needed by C11/C12, such as revenue, gross/operating/
  net income, EPS, assets, liabilities, debt, current assets/liabilities,
  operating cash flow, capital expenditure, and free cash flow;
- fiscal period, report date, currency, source label, as-of/freshness labels,
  period-comparison labels, availability, and caveat codes.

Each fact group must identify its fiscal period and report date. Values without
both labels are unavailable, not silently current. The backend computes ratios,
growth, and period changes; the LLM never performs the arithmetic.

At most one provider acquisition sequence may populate a report's FMP snapshot.
The frozen normalized snapshot is reused by all role tools, by the PM, and by
later readback/regeneration of that package. If the daily budget, provider
endpoint, or free-tier entitlement does not permit a fact group, the role uses
the profile-only WITHOUT variant and states the gap with
`source_rate_limited`, `provider_unavailable`, or
`source_endpoint_not_available`, as applicable. It may not substitute EDGAR
XBRL, another vendor, or remembered knowledge.

The profile-only WITHOUT variant reads the existing approved
`public_company_profile` snapshot already frozen in the package. It does not
issue an FMP request and therefore remains available after the FMP fundamentals
budget is exhausted. Any future FMP profile acquisition would count against the
same FMP daily budget and needs its own source-rights decision.

Exact free-tier endpoint availability is an implementation smoke question, not
an assumption in this contract.

### 3.4 FRED Data-Series Lane

FRED series are approved as normalized macro-series context for the internal
free-tier prototype. They enable the News Analyst's macro WITH variant and C13.
The initial named set is CPI, core PCE, unemployment, federal funds rate,
10-year Treasury yield, and yield-curve spread.

The approved normalized `fred_macro_series_snapshot` contains only the reviewed
series identifier/display label, observation value, unit, observation/as-of date,
frequency, source label, availability/freshness, and caveat codes. The backend
computes changes and direction labels through C13. The LLM may describe a
saved-series change only with attribution and a provenance-matched calculation
result; it may not forecast policy, rates, markets, or outcomes.

One normalized observation snapshot is acquired and frozen per report package;
the package cache serves all later tool requests and readback. A local budget or
provider failure returns `not_available` with `source_rate_limited` or
`provider_unavailable`; it never falls back to commercial macro/news sources.

### 3.5 Existing FMP EOD And Blocked News Lanes

C7-C9 derived public-price statistics remain inside the existing FMP EOD
internal-prototype approval. They use already-frozen licensed EOD data and
backend calculations only. Every output must carry method, window, and as-of
labels. This is a confirmation, not a new source-rights lane.

Commercial or general public-news providers remain not approved, including FMP
news, NewsAPI, Benzinga, Finnhub, Polygon, GDELT, web search, scraping, and MCP
news tools. The News Analyst may use only approved SEC metadata, approved FRED
metadata/series, and named gaps.

### 3.6 Attribution And Caveat Text

The following backend-owned text is the approved disclosure baseline. It is
displayed only when the corresponding normalized source was used; roles may not
rewrite it into an endorsement, signal, or conclusion.

| Lane | Attribution | Caveat |
| --- | --- | --- |
| FMP fundamentals | `Source: Financial Modeling Prep normalized reported statement facts, with labeled fiscal periods and report dates.` | `Reported-statement coverage may be delayed, incomplete, revised, or unavailable on the free tier. This report does not treat statement facts as a trading signal.` |
| FRED series | `Source: Federal Reserve Economic Data (FRED), normalized series observations and dates.` | `Economic observations may be revised, delayed, or unavailable. This report describes the saved series only and does not predict policy, markets, or outcomes.` |
| SEC EDGAR metadata | The P34A-T6 attribution remains binding: `Source: SEC EDGAR submissions/index metadata. Recent filing metadata only. Not investment advice or a trading signal.` | The P34A-T6 caveat and non-endorsement text remain binding without modification. |

Provider names are attribution, not endorsement. No URL, raw provider response,
accession/path, API-plan detail, or API key may accompany the display text.

## 4. Gate And Freeze Conditions

All five role surfaces, including the PM, use one shared F-4 advice-boundary
set. The banned class includes overall-verdict language and equivalents:
`approved`, `passed`, `safe`, `ready`, `trade-ready`, `ready to trade`, and
equivalent all-clear phrases. A green check, score, rating, or status label
cannot encode the same outcome.

The first slice that does any of the following must land F-5, F-6, and F-12 in
the same reviewable change, with their provenance and identifier-canary eval
families green:

- admits a value-bearing prompt fact label;
- registers C1-C5 or any other calculation with value labels; or
- activates a `p36-role-analysis-v1` prompt.

F-5 runs before F-6. Every numeric span must provenance-match a role's frozen
input or calculation result; unmatched values drop the full role section or PM
block. F-6 then rejects identifiers, secret-like values, raw paths, and raw
payload shapes while allowing plain topic words such as cash, holdings,
positions, and portfolio. F-12 reconciles legacy scanners in the same slice so
they neither weaken the protection nor reject the approved v3 value-label form.

F-13 version-keyed freeze/readback lands with the first v3 freeze. Reports frozen
under v2 revalidate using their v2 gates; reports frozen under
`p36-role-analysis-v1` or `p36-pm-synthesis-v1` revalidate only under the v3
gates. No mixed gate set, parse fallback, recomputation, or provider rerun is
permitted.

F-1 through F-4 and F-7 through F-11 apply as specified by the Phase 36
compatibility review. In particular, PM typed JSON validation, heading and table
contract, source/method/as-of verification, bounded request budgets, and
grounding are release gates, not optional polish.

The future P37 user-policy store is backend-only. Phase 36 must not create a
read field, prompt field, envelope field, or UI assumption that user policy
thresholds enter an LLM prompt. P37 remains a separate policy-consumption phase.

## 5. Options Mechanics Boundary

C4 `calc_option_structure` and C5 `calc_scenario_exposure` are
beachhead-critical. They ship in the first calculation slice, not after the
five-role activation work.

Options mechanics calculations must fail closed to `unable_to_verify` when the
frozen broker semantics are incomplete. This includes, at minimum:

- no pending-order awareness in the synced snapshot;
- no claim that shares are available to cover a covered call unless the frozen
  coverage inputs substantiate it;
- no claim that collateral, assignment, call-away, or scenario effects are fully
  modeled when prerequisite inputs are absent or stale.

The covered-call model may graduate from `not_fully_modelled` only when C4/C5
have tested evidence semantics for available covered shares and all documented
limitations remain explicit. `unable_to_verify` is an honest terminal result,
not a failed UI state and not a silent omission.

## 6. Deterministic Standalone Read Contract

The composed-report read contract must render the summary/check surface wholly
from backend-owned deterministic data when no live role is available. This
includes deterministic trade-impact facts, calculation results, source/as-of
labels, freshness, caveats, gaps, and verification items. The UI must not need
an agent response to show the report's core facts.

Live analyst sections and the PM synthesis are additive, gated layers. Their
absence, drop, timeout, or tool/source failure must leave a complete,
historical, plainly caveated deterministic report rather than an empty or
invented substitute.

## 7. Binding Codex C Slice Plan

Each item below is one implementation slice with one owner (Codex C), one
review, and a clean acceptance boundary. A later slice may not rely on a
partially landed earlier slice.

### P36-T4A - V3 Calculation And Safety Foundation

Scope: introduce versioned calc-envelope contracts and register C1-C5, including
C4/C5; implement F-5 numeric provenance, F-6 identifier privacy, F-12 scanner
reconciliation, and F-13 version-keyed freeze/readback together. Add the
deterministic standalone summary/check read contract.

This is an atomic contract slice: implementation work may be organized into
reviewable commits, but no commit, flag, prompt, report surface, or registry
state may expose C1-C5 or any value-bearing v3 data before the F-5/F-6/F-12
bundle is active and its evals are green. F-13 ships with the first v3 freeze.

Acceptance:

- C1-C5 consume frozen saved evidence only; C4/C5 use the options failure rules
  in section 5.
- Value-bearing calc labels cannot reach prompts or reports until F-5/F-6/F-12
  are green in the same slice.
- Synthetic identifier canaries, unmatched-number probes, v2/v3 readback
  separation, and no-rerun tests pass.
- No provider acquisition, live LLM, or frontend work is introduced.

### P36-T4B - Free-Tier Source Snapshot Boundaries

Scope: implement disabled-by-default, fake/replay-tested normalization and
package-freeze boundaries for FMP statement fact groups and the six FRED series.
Apply daily budget, one-fetch-per-package, cache-reuse, as-of/period labels, and
honest unavailable rules. Add EDGAR User-Agent/rate-budget enforcement without
expanding its metadata scope.

Acceptance:

- No raw provider response, URL, request log, secret, or private account data
  persists or reaches prompts.
- Each lane returns only the normalized fields in section 3 and freezes once per
  saved package.
- Rate-limit, endpoint denial, and budget-exhaustion tests produce named
  WITHOUT variants with no alternate-source fallback.
- An opt-in smoke validates actual free-tier endpoint eligibility without
  assuming it from this contract.

### P36-T4C - Deterministic Company And Events Floors

Scope: render backend-owned deterministic Company context and Events/macro
sections from approved frozen FMP, FRED, and EDGAR snapshots, preserving
honest-unavailable paths. Add C6-C15 wrappers where their saved evidence and
source lane are available, including backend-computed humanized recency labels.

Acceptance:

- Source, method, period, and as-of labels render from frozen data.
- C7-C9 retain the existing FMP EOD approval; C11-C13 operate only when their
  approved lane is frozen; C14/C15 stay role-filtered.
- No role prompt changes, live calls, or new frontend read fields are needed to
  render the deterministic floor.

### P36-T5A - V3 Analyst Activation And Bounded Loops

Scope: activate v3 prompts and sequential, bounded mediated loops for all four
analysts. Apply F-7 through F-11 together with the role section/heading/table
contract, source/method/as-of verification, and the Tier 1 budgets.

Acceptance:

- Technical, Risk, Fundamentals, and News roles each complete an accepted live
  section when their lane is available; each names an honest gap when it is not.
- The LLM requests only allowlisted frozen-package calculations using
  enum/reference arguments; no free numeric inputs or direct provider access.
- The loop cannot exceed three iterations, per-role allowlists, or global hard
  caps; failed or malformed requests fail closed to the deterministic floor.
- All F-4 advice, F-5 provenance, F-6 identifier, F-8 structure, F-9
  non-boilerplate, F-10 budget, and F-11 grounding eval families pass.

### P36-T5B - Live PM Synthesis

Scope: implement the P36 `PmSynthesis` typed call, whole-block fallback, PM calc
verification access, and composer rendering. No new sources or frontend contract
are included.

Acceptance:

- Only the four verdict-incapable fields in section 2 parse and render.
- The PM describes evidence quality and unresolved tensions, never the trade's
  desirability, direction, or outcome.
- A PM failure removes only the PM block; deterministic summary and analyst
  sections remain historical and readable.
- PM provenance, identifier canaries, advice-boundary probes, and frozen
  readback/no-provider-rerun tests pass.

### P36-T6 - Five-Live-Role Founder Acceptance Run

Scope: per-run founder-authorized live acceptance on a selected real account,
using the actual frozen saved-review package. No source or product expansion is
allowed in the run.

Acceptance is defined in section 8.

## 8. P36-T6 Acceptance Definition

P36-T6 is a founder acceptance run, not a generic provider smoke. It requires
two saved-review scenarios and actual accepted live output from all five roles:

1. The standing stock-buy chain.
2. One covered-call review.

For each scenario, the pass bar is:

- a saved review starts from the selected account and frozen scope/evidence;
- each of the four analysts and the PM performs an accepted gated live call;
  none is counted as live when it only renders a deterministic fallback;
- live content cites only approved frozen evidence/calculation results and
  preserves source, period/as-of, freshness, caveat, and unavailable states;
- the deterministic summary/check surface remains complete when the live blocks
  are omitted in a forced-fallback test;
- all source calls respect the configured free-tier budgets and sequential run
  order; rate-limit exhaustion is honest and must not be presented as a passing
  live-role result;
- no raw identifiers, secrets, raw payloads, URLs, advice, order/execution,
  rating, target, forecast, overall verdict, or all-clear language renders;
- list/detail reopen the frozen report with zero provider, source, tool, or
  calculation rerun.

The covered-call scenario additionally requires C4/C5 to run. It passes when
coverage/collateral/assignment limitations are rendered as
`not_fully_modelled` or `unable_to_verify` where the saved snapshot cannot
substantiate them. It fails if the report claims verified covered-share
availability, pending-order awareness, collateral sufficiency, or fully modeled
mechanics without frozen evidence.

No real values, identifiers, raw payloads, or screenshots with private data may
be committed as run evidence. The founder receives only the approved report
surface and a sanitized acceptance record.

## 9. Deferred Or Explicitly Not Approved

- Commercial public-news providers and article/excerpt/URL ingestion.
- FMP news or price-target/rating products.
- EDGAR filing bodies, XBRL facts, exhibits, or filing interpretation.
- Web search, scraping, MCP, TradingAgents runtime, and LangGraph migration.
- Agent Console activation, frontend contract expansion, user-policy prompts,
  and P37 Pre-Trade Check work.
- Parallel analyst execution before the P36-T6 measurement and concurrency gate.

## 10. Required Reviews

Each Codex C slice requires Codex B contract/privacy/source-rights review. The
v3 prompt, loop, and PM slices also require Claude E agentic workflow review.
Any display/read-contract work requires Claude B visual/safety review before
founder acceptance. P36-T6 requires explicit founder authorization for each live
run and founder acceptance after the two scenarios complete.

## Next Step

P36-T4A is complete and review PASS: C1-C5, F-5, F-6, F-12, F-13, and the
deterministic standalone read contract landed as one value-bearing boundary.
The next slice is P36-T4B, limited to disabled-by-default, normalized free-tier
FMP fundamentals and FRED series snapshot/freeze boundaries plus existing EDGAR
operational enforcement. It must not activate v3 role prompts, live role loops,
PM synthesis, or frontend display work. After P36-T4B contract/privacy review
PASS, P36-T4C may render deterministic Company and Events floors from the
approved frozen snapshots.
