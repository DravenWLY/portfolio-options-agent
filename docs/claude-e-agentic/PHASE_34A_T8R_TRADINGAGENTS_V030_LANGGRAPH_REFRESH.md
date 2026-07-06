# Phase 34A-T8R — TradingAgents v0.3.0 Refresh of the LangGraph Integration Design

Status: research/design done (no implementation, no Portfolio Copilot code
changes, no dependencies added).
Owner: Claude E. Reviewer: Codex B. Stop for Codex B review before any coding.
Refreshes: `PHASE_34A_T8_LANGGRAPH_INTEGRATION_ARCHITECTURE.md` (P34A-T8, PASS
for dev-only prototype).
Reference repo: `../TradingAgents`, updated 2026-07-03 by fast-forwarding local
`main` from the fork's v0.2.5 (`a5cb7cb`, 2026-05-11) to upstream
TauricResearch v0.3.0 (`85946c2`, 2026-06-22), 66 commits. Working tree had no
modified tracked files before the pull (only untracked `.DS_Store` artifacts
and a gitignored generated `reports/` directory, which was not inspected).
Reference-only: no TradingAgents source copied, no dependency taken, no
TradingAgents runtime executed, no real data or APIs touched.

Locked product question (unchanged): **"What would I be ignoring if I acted
manually now?"** — never "should I trade?".

---

## 1. Executive recommendation

**Proceed with the dev-only LangGraph prototype (P34A-T8A/T8B) as designed in
P34A-T8. The core recommendation does not change after v0.3.0**: wrap the
app-owned tool-mediated runner as a parallel dev runner; LangGraph owns
sequencing and dev tracing only; the backend keeps tools, validators, citation
ownership, evidence tiering, output safety, and the freeze contract; hosted
tracing, checkpoint persistence, route wiring, and Agent Console durable runs
stay blocked pending separate approval.

v0.3.0 *strengthens* the prior design's two central bets rather than
challenging them:

1. **Traces from state deltas, not callbacks.** TradingAgents' new
   observability layer (`graph/analyst_execution.py`) derives analyst wall
   times by watching streamed state chunks for report keys — exactly the
   "derive traces from validated state deltas" approach in P34A-T8 §6, chosen
   there for privacy. The pattern is now field-proven in the reference repo.
2. **Deterministic ground truth beats LLM numerics.** v0.3.0 added a
   deterministic "verified market snapshot" specifically because their LLM
   analysts confabulated exact numbers (their #830), plus deterministic
   instrument-identity resolution at run start because agents hallucinated the
   wrong company (their #814). Portfolio Copilot already solved both harder:
   deterministic findings are the *only* numeric/citation source, LLM prose is
   digit-free, and identity comes from the frozen evidence package. The
   reference project converging on weaker versions of our guards is evidence
   the P34A posture is right, not that it needs loosening.

Three **refinements** (no verdict change) are folded into the design below:
a declarative node-spec registry for graph construction and parity naming
(§4, R1); per-node wall time explicitly added to the trace allowlist, tracked
from state deltas (§6, R2); and a noted stream-dedup pitfall for any future
Agent Console streaming (§7/§8, R3). One **optional follow-up outside T8
scope**: schema-validated structured output for live role prose (§3, R4).

## 2. TradingAgents v0.3.0 architecture summary

What v0.2.5 → v0.3.0 actually changed (66 commits, +6,685/−5,152 across 130
files):

- **Graph topology** (`graph/setup.py`): same overall spine — sequential
  analysts (market / sentiment / news / fundamentals), each an
  agent-node ⇄ `ToolNode` loop with a message-clear node between analysts;
  then bull/bear researcher debate (conditional rounds), Research Manager,
  Trader, three-way risk debate (aggressive/conservative/neutral), Portfolio
  Manager, END. New: node wiring is now driven by a declarative
  `AnalystNodeSpec` registry + `build_analyst_execution_plan()` instead of
  inline if/else per analyst.
- **Observability** (`graph/analyst_execution.py`, new): `AnalystWallTimeTracker`
  computes per-analyst wall time; `sync_analyst_tracker_from_chunk()` infers
  start/completion purely from which `*_report` keys appear in streamed state
  chunks. No callback handlers, no prompt access. A debug-stream fix
  (`709fe2b`) dedupes the trailing message chunk so streamed output isn't
  double-counted.
- **State** (`agent_states.py`): still `MessagesState`-based free-prose
  channels. Added `asset_type` (stock/crypto pipeline switch) and
  `instrument_context` — a deterministic ticker-identity string resolved once
  at run start (`resolve_instrument_context`, cached yfinance lookup) and
  carried in state so every agent anchors to the real company.
- **Roles**: Social Media Analyst became a broader Sentiment Analyst
  (news + StockTwits + Reddit) with structured output; decision agents
  (Research Manager, Trader, Portfolio Manager) now emit **Pydantic
  structured output** (`agents/schemas.py`) using each provider's native
  structured mode, with enum ratings (Buy/Overweight/Hold/Underweight/Sell;
  Trader Buy/Hold/Sell), nullish-float coercion, and a renderer back to
  markdown.
- **Tools/data**: LLM-selected `@tool` functions routed through a vendor
  layer. New: **FRED macro vendor** (`dataflows/fred.py` +
  `get_macro_indicators` tool) returning full numeric time series (latest
  value, window change, observation table) into LLM context, with a curated
  alias map plus raw-series-ID passthrough; **Polymarket prediction markets**
  vendor; **verified market snapshot** (`dataflows/market_data_validator.py`)
  — a deterministic OHLCV/indicator table the market analyst must treat as
  the source of truth for exact numeric claims; a typed **`VendorError`
  hierarchy** (`NoMarketDataError` / `VendorRateLimitError` /
  `VendorNotConfiguredError`) sized by router *reaction*, not by cause;
  stale-data rejection; look-ahead (future-news) filtering; symbol
  normalization everywhere.
- **Tracing/checkpointing**: no hosted tracing added (still none). SQLite
  checkpoint/resume per ticker+date is unchanged (2-line touch). Full-state
  JSON dumps and a new shared markdown report-tree writer
  (`reporting.py`) persist complete prose reports — including debate
  histories — to disk.
- **Memory/reflection**: unchanged mechanism (decision log + realized-return
  reflection), now symbol-normalized; configurable alpha benchmark.
- **Config/infra**: provider registry unification (Bedrock, NIM, Groq, Kimi,
  Mistral…), env-var config precedence, exposed sampling temperature with a
  reproducibility note, CI with lint/tests, i18n output-language guard tests.

## 3. Apply / adapt / reject table

| TradingAgents v0.3.0 pattern | Verdict | Reason / Portfolio Copilot safety impact |
| --- | --- | --- |
| Declarative node-spec registry driving graph construction (`AnalystNodeSpec`, execution plan) | **Apply** (R1) | Pure structure, no data exposure. Gives PC stable node names, a single place to bind node → state keys → validators, and a parity-test anchor. |
| Wall-time tracking derived from streamed state deltas, not callbacks | **Apply** (R2) | Matches P34A-T8 §6 privacy posture exactly; callbacks see raw LLM I/O, state deltas (in PC) are validator-checked first. Adds per-node wall time to the trace allowlist — timing metadata only. |
| Debug-stream trailing-chunk dedup fix | **Adapt** (R3) | A correctness pitfall to design around when Agent Console later streams per-node progress; note in the P35x contract, nothing to build now. |
| Deterministic verified snapshot as sole source of numeric truth | **Already stronger in PC** | PC's deterministic findings/evidence are the *only* numeric source and live prose is digit-free with `invented_metric_blocked` hard blocks. Their version trusts the LLM to obey a prompt instruction; ours rejects output. Keep ours; treat theirs as validation. |
| Deterministic instrument identity resolved once at run start, carried in state | **Already present in PC** | The frozen `SavedEvidencePackageRead` + `build_evidence_catalog` entry node is PC's identity anchor. Confirms "resolve deterministic context at graph entry" as the right entry-node design. |
| Typed vendor-error hierarchy sized by router reaction | **Already present in PC** | `ToolResult.status`/`availability` enums are behavior-typed the same way. Their design note — "number of types = number of distinct reactions" — is worth keeping as a principle when new degraded states are proposed. |
| Pydantic structured output with provider-native modes for role output | **Adapt later** (R4, optional, out of T8 scope) | The *mechanism* (schema-validated output instead of free prose, rendered by the backend) could harden PC's live role sentence against format drift. Enum *contents* (Buy/Sell ratings) are prohibited. Requires its own Codex B-reviewed design; current regex/blocklist validators remain regardless. |
| FRED vendor returning numeric macro time series into LLM context, LLM-chosen series with raw-ID passthrough | **Reject** | Violates the P34A source-rights gate (FRED is approved for calendar/release *metadata only*, no observation values), injects numbers the roles must not cite, and free-form series selection is agent overreach. PC's FRED lane stays: backend-normalized metadata, planner-selected, `observation`/`actual_label` keys forbidden. |
| Polymarket prediction-markets vendor | **Reject** | Unapproved source; prediction-market odds are directional/probability framing adjacent to advice; no rights review. |
| Sentiment Analyst over StockTwits/Reddit/news | **Reject** | Sources explicitly blocked by the P34A-T6 gate; social sentiment is mood-as-signal framing PC's market-mood snapshot already covers in gated, non-signal form. |
| LLM-selected `@tool` calls via `ToolNode` loops | **Reject** (unchanged) | PC's planner is backend-owned and clamped; LLMs never call tools. Core boundary. |
| `MessagesState` + per-analyst message-clear nodes | **Reject** (unchanged) | No conversation channel in PC state. Notably, even TA treats messages as disposable enough to clear between analysts — the channel earns nothing for a bounded pipeline. |
| Bull/bear + risk debates, ratings enums, BUY/SELL/HOLD signal extraction | **Reject** (unchanged) | Debate-to-verdict answers "should I trade?"; PC's auditor + structured contradiction → open-questions is the compliant analogue. |
| Outcome-scored memory/reflection (realized returns, alpha benchmark) | **Reject** (unchanged) | Performance framing = advice drift; would persist derived real-account data. |
| Full-state JSON dumps + markdown report-tree writer to disk | **Reject** (unchanged) | Persists prompts/debate prose — exactly what PC's freeze contract exists to prevent. `tool_run_artifact` remains the only persisted run record. |
| Exposed sampling temperature + reproducibility note | **Already present** | PC pins `temperature=0.0` in the live request. |
| Guard tests sweeping every agent (i18n coverage test pattern) | **Adapt** | Same shape as PC's eval matrix; reinforces "one property, asserted across all roles" parity tests in §7. |

## 4. Proposed Portfolio Copilot LangGraph topology (updated)

Unchanged spine from P34A-T8 §2, with R1 applied — construction is driven by a
**backend-owned node-spec registry** (name, wrapped function, state keys
written, validators to run on the delta), mirroring `AnalystNodeSpec` in shape
only:

```
entry
  → build_catalog          build_evidence_catalog (deterministic identity +
                           availability anchor, resolved once at entry)
  → plan                   build_planner_plan (backend planner; clamped
                           MAX_TOOL_CALLS_PER_ROLE / MAX_TOOL_CALLS_TOTAL)
  → execute_tools          app-owned execute_tool_request per RolePlan;
                           sequential in M1; no ToolNode, no LLM selection
  → role_findings          per non-PM role: deterministic floor, optional
                           live prose overlay (T2/T3A seam); SEC/news finding
                           stays deterministic
  → evidence_auditor       audit_findings (ref filtering, hard blocks,
                           structured contradiction detection)
  → [conditional] repass_needed? and repass_count == 0
        yes → bounded_repass → evidence_auditor   (≤1 by constant)
        no  → continue
  → pm_synthesis           deterministic template (M1)
  → output_safety          report_output_safety / validate_or_fallback
  → freeze                 summary payload + SavedToolMediatedRunArtifactRead
                           (terminal)
any node failure → deterministic_fallback (terminal failed-safe payload,
                   identical to today's except-branch)
```

Role fan-out stays sequential in M1; if ever parallelized, fan-in re-sorts by
`AGENT_TEAM_ROLES` and `CANONICAL_EVIDENCE_ORDER`.

## 5. Graph state contract (unchanged, restated with v0.3.0 lessons)

**Allowed**: input `SavedEvidencePackageRead`; `EvidenceCatalog`;
`PlannerPlan`; `ToolResult` envelopes unmodified
(`contract_version="p33a_tool_result_v1"`); `RoleFindingSet` tuples;
`AuditorRecord`; `open_questions`; `ProviderRunMeta` (safe metadata only);
`provider_mode`; `repass_count`; `run_status`; opaque run/version ids.

**Forbidden (hard, enforced)**: `MessagesState`/message channels of any kind;
prompt or completion text beyond auditor-validated `claim_text`; secrets/keys/
provider config; anything `private_forbidden`; raw broker payloads, account
numbers, balances, quantities, lots; raw URLs/SEC paths; numeric macro/market
observation values (the v0.3.0 FRED/snapshot tables are the counterexample to
avoid); cross-run memory or reflection text; non-opaque user identifiers.

**Validator checkpoints**: one state-update wrapper on every node runs
`validate_saved_tool_freeze_payload`, `find_forbidden_keys(TOOL_FORBIDDEN_KEYS)`,
`find_secret_like_values`, and the wording/metric pattern guards over the
node's returned delta before merge; failure routes to
`deterministic_fallback`. The node-spec registry (R1) is where each node
declares which validators apply, so the wrapper is table-driven and testable.

**Trace-safe delta format** (feeds §6): after validation, each node emits
`{node, status, wall_ms, warning_codes, dropped_claim_codes, tool_names,
availability, evidence_tiers, evidence_refs, token_counts, is_mock, versions}`
— codes and metadata only, never prose.

## 6. Tracing policy (unchanged verdict, one addition)

- Dev-only, local-only, in-memory/stdout, synthetic evidence only; discarded
  after the run. No persistence, no API, no frontend exposure in M1.
- **Hosted tracing prohibited permanently**: startup guard hard-fails graph
  construction if `LANGCHAIN_TRACING_V2` / `LANGSMITH_TRACING` /
  `LANGSMITH_API_KEY`-style env is set; a unit test asserts the kill-switch.
  (v0.3.0 added no hosted tracing either; the risk remains env-activated
  LangSmith, unchanged.)
- Traces derive from **validated state deltas** (§5 format), never LangChain
  callbacks. v0.3.0's chunk-watching tracker confirms deltas are sufficient
  even for timing.
- **Addition (R2)**: per-node wall time is explicitly on the trace allowlist.
- Redaction allowlist = exactly the §5 delta fields; anything not freezable is
  not traceable. `claim_text` bodies stay out of traces pre- and post-audit.

## 7. Parity / eval plan

Run both runners over the synthetic eval fixture matrix; all tests offline,
fake/injected provider only:

1. **Deterministic parity**: identical `role_summaries`,
   `evidence_references`, `warning_codes`, `final_synthesis_markdown`, and
   `tool_run_artifact` payloads (timestamps normalized) between
   `run_tool_mediated_agent_team` and the graph runner, across: full
   evidence; degraded/unavailable sections; blocked-actionability drafts;
   live-enabled with fake provider; provider timeout/auth-failure; hard-block
   injections; contradiction → re-pass; SEC metadata present/absent.
2. **Privacy leak tests**: adversarial fixtures seeding forbidden keys/values
   into node deltas must route to `deterministic_fallback`; assert no
   forbidden key/value in any trace event or state snapshot
   (`find_forbidden_keys` / `find_secret_like_values` sweep over emitted
   deltas).
3. **Citation-boundary tests**: LLM output attempting to add/reorder refs
   never changes `evidence_refs`; SEC role/citation guard holds (only
   `news_analyst`/`portfolio_manager_agent` cite `public_events_calendar`
   from SEC source); refs always ⊆ received ∩ usable ∩ available.
4. **Fail-closed tests**: each node forced to raise produces the exact
   failed-safe payload of today's except-branch; re-pass never exceeds 1;
   hard blocks never re-pass.
5. **No-provider-rerun readback tests**: saved report list/detail readback
   after a graph-runner report never reconstructs the graph, re-executes
   tools, or resolves providers (spy/counter assertions), matching the frozen
   readback guarantee.
6. **Kill-switch test**: graph construction refuses under LangSmith/LangChain
   tracing env vars.
7. **Stream-dedup guard (R3, deferred to P35x)**: when streaming is
   introduced for Agent Console, assert per-node events are emitted exactly
   once (v0.3.0's trailing-chunk dedup bug is the regression to prevent).

## 8. Implementation sequence (one owner per task)

| Task | Owner | Scope | Review |
| --- | --- | --- | --- |
| P34A-T8 / T8R | Claude E | Design + v0.3.0 refresh (this memo) | **Codex B: review both memos next** |
| P34A-T8A | Claude E | Dev-only prototype: optional `agent-graph` extra; `graph_runner.py` wrapping existing functions via the node-spec registry (R1); §5 state + validation wrapper; §6 kill-switch; parity/fail-closed/kill-switch tests. No route/API/schema changes, no checkpointer. | Codex B (contract/privacy) |
| P34A-T8B | Claude E | Runner-selection shim `POA_AGENT_TEAM_RUNNER=app_owned\|langgraph_dev` (default `app_owned`; `langgraph_dev` refuses outside dev/test); dual-runner eval diff in the P33A harness; trace-event shape | Codex B; **Claude B privacy review of trace events** |
| Decision gate | Codex A/founder + Codex B | Adopt for Agent Console or retire the spike (parity results + dependency audit) | — |
| P35x-1 | Codex B | Checkpoint-persistence contract (serializer allowlist = §5 state, Postgres saver, opaque thread ids, retention/deletion, resume + stream-once semantics per R3) | Codex A/founder |
| P35x-2 | Codex C | Persistence/route wiring per the P35x-1 contract (backend lane) | Codex B; Claude B for persisted-state privacy |
| P35x-3 | Claude A | Agent Console run-progress UI over backend run-state reads only | Claude B (copy safety: progress labels must not imply advice/urgency) |
| Optional R4 | Claude E (design first) | Schema-validated structured output for live role prose (provider-native modes; no ratings/enums/verdicts; regex/blocklist validators retained) | Codex B |

## 9. Blockers before implementation (unchanged, reconfirmed)

1. Codex B PASS on P34A-T8 + this T8R memo, plus the short ADR ("LangGraph as
   orchestration shell; app-owned validators remain the safety boundary").
2. Founder/Codex A approval to add the `langgraph` dependency (optional extra;
   pin `langgraph`/`langchain-core`; dependency audit at the decision gate).
3. Trace policy sign-off (§6 kill-switch + allowlist), with Claude B review.
4. Parity criteria pinned (§7 item 1 field list, timestamp normalization).
5. **No checkpoint persistence of any kind** until the P35x-1 contract exists;
   T8A/T8B compile without a checkpointer.
6. **No route wiring** until the dev-only prototype passes parity and the
   decision gate approves adoption.
7. P34A-M1 exit confirmed; T3B/T4/T5/T7 retain priority for Codex C/Codex B.
