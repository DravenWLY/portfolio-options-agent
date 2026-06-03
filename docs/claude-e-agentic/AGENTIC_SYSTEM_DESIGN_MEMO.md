# Agentic AI System Design Memo

Status: **revised after Codex B architecture adjudication** — decisions encoded in
`docs/codex-b-architecture/adr/0008-agentic-orchestration-spine.md` (proposed).
The Phase 25A tasks in `docs/shared/implementation_plan.md` remain
`proposed`/`not_started` pending Codex A go-ahead on the first coding slice.
Date: 2026-06-02 (rev. 2; original 2026-06-01)
Author: Claude E — Agentic AI Systems Design / Implementation
Adjudicated by: Codex B (architecture/safety). Final product approval: Codex A.
Privacy/safety-sensitive review: Claude B.

> This memo is a design artifact only. It authorizes no implementation, no route
> changes, no frontend composer activation, no live LLM/provider/tool calls, no
> persistence migration, and no TradingAgents execution. Frameworks (LangGraph,
> OpenAI Agents SDK, MCP) are **not** introduced now; see §0 and ADR 0008.

---

## 0. Codex B adjudication — encoded decisions

Codex B reviewed the orchestration-core proposal and the reversibility analysis.
The following are now the accepted direction (full record: ADR 0008):

1. **Layered hybrid.** Portfolio Copilot owns the **safety spine permanently**.
   Frameworks may help later, but must **never** own prompts, the privacy
   boundary, evidence tiers, validation, deterministic-evidence ownership, safe
   state, or safe read/event contracts.
2. **Custom app-owned runner first — not LangGraph.** Phase 25A begins with a
   thin custom runner over the existing agent-team foundations. LangGraph is
   deferred until durable multi-turn threads, resumable state, human-in-the-loop
   interrupts, or complex dynamic routing become *committed* product
   requirements.
3. **SSE remains the first realtime transport later.** Transport is independent
   from the orchestration engine. Future Agent Console activation uses HTTP
   commands + SSE first; WebSocket/Socket.IO stays deferred.
4. **Reject the OpenAI Agents SDK** for this product path. Keep the app-owned
   provider Protocol and the Gemini/mock-default posture (ADR 0005).
5. **MCP is future-only and public/agent-safe only.** No MCP in MVP. A
   private-tier (broker-data) MCP tool/server is prohibited.
6. **No TradingAgents copy or execution in the portfolio-aware path.** Reference
   architecture only; any future adapter is public-evidence-only and separately
   reviewed.
7. **Role rename is a separate slice.** Do not fold the Phase 19 role rename into
   P25A-T1.
8. **Parallelism is a design seam, not active behavior yet.** Make P25A
   async-ready; keep the first implementation sequential.
9. **Memory stays disabled for MVP.** Only within-run validated summaries may be
   reused; reflection exists only as process/eval flags.
10. **First coding slice (P25A-T1):** app-owned `AgentReviewRunState` + mock
    workflow runner + timing/budget/eval scaffolding. No live LLM, no persistence
    migration, no route behavior change, no frontend composer activation, no real
    parallel execution, no role rename.

### Reversibility ruling (Codex B)

**Hard-to-reverse core (must be designed right now, lives in app-owned code):**
- the data-tier model (public / agent-safe / private-never) and its enforcement
  point;
- deterministic-evidence ownership;
- the provider-Protocol shape;
- the role-as-pure-function seam;
- the run-state shape;
- the safe read/event contract shape;
- the persistence schema *once accepted*;
- the frontend-consumed event/read contracts *once shipped*.

**Reversible (two-way door) — but only while the conditions hold:** the
engine/framework choice is reversible **only if roles remain pure and state
remains app-owned.** If LangGraph (or any framework) comes to own the checkpoint
schema, a shared message state, or event IDs, it becomes load-bearing and is no
longer a simple two-way door. That is the line we do not cross without a new ADR.

---

## 1. Executive recommendation

Portfolio Copilot already has most of an industry-grade agentic spine; the
adjudicated path is to **formalize and unify the app-owned, stage-based state
machine that already exists** — not adopt a framework, not rebuild. Two
orchestrators exist today:
[`agents/orchestrator.py`](../../backend/app/services/agents/orchestrator.py)
(Phase 16B — deterministic, ADR-0002 review roles, typed context envelopes, maps
to `agent_runs`/`agent_steps`) and
[`agent_team/orchestrator.py`](../../backend/app/services/agent_team/orchestrator.py)
(Phase 19 — mock-first LLM roles, agent-safe evidence projection, strong
output-safety validators). These are the foundation. The custom runner is the
spine now; frameworks are deferred and gated (§0, ADR 0008).

Principle: **"Pay for an engine only when its primitives are load-bearing; never
let a framework own the safety boundary."**

---

## 2. TradingAgents patterns to transfer (adapt, never copy source)

| Pattern (TradingAgents) | How it transfers |
| --- | --- |
| Explicit stage state machine | Already present as typed stages; keep stage-based and auditable, never autonomous. |
| Role specialization | Keep, re-scoped to *review* roles (rename is a separate slice — §6, decision 7). |
| Structured outputs with graceful fallback | Adopt; fallback is a safe "unavailable" record, never rendering arbitrary model numbers. |
| Bounded conditional loops | Adopt the *bounding mechanism* for a future, optional, public-evidence-only "considerations for/against" pass; default 0–1 rounds, budget-capped. |
| Checkpoint/resume | Map to app-owned `agent_runs`/`agent_steps` reload — only if/when a durable need is approved; the app owns the checkpoint schema (reversibility ruling). |
| Deep/quick LLM split + thinking config | Adopt as a cost/latency lever. |
| Tool-vendor routing config | Adopt later as a *governed* per-role registry; tools are app-owned safe wrappers, never raw provider SDKs in LLM hands. |
| Context-window management (msg-clear) | Adopt as explicit per-role envelopes that *prevent* cross-role context bleed. |
| Reflection (as a mechanic) | Re-point at **process/eval** reflection only, never outcome/alpha lessons. |

## 3. TradingAgents patterns to reject or heavily modify

| Pattern | Decision | Why |
| --- | --- | --- |
| Buy/Hold/Sell + `signal_processing` | **Reject** | Analysis-only product; no verdict-to-act. |
| Trader / Portfolio-Manager transaction plan, sizing, entry/stop | **Reject** | No advice, no execution, no sizing. |
| Raw ticker tools in LLM hands (ReAct on yfinance/alpha_vantage) | **Reject** | Deterministic backend owns metrics; LLMs never fetch/compute numbers. |
| Outcome-alpha memory + cross-ticker "lessons" | **Reject** | No outcome/alpha tracking; memory disabled (decision 9). |
| Shared message-state accumulation across the graph | **Reject for portfolio-aware path** | Would smear portfolio-aware context into public roles. |
| Bull/Bear + risk-debate-to-conviction | **Heavily modify** | Only as a future, bounded, public-evidence-only "considerations for/against" pass with no recommendation. |
| Generic stock-picking center; autonomous high-recursion graph | **Reject** | Center is broker-aware `TradeIntent` review; stages stay bounded/auditable. |

## 4. Proposed Portfolio Copilot multi-agent workflow

A fixed, auditable, deterministic-first pipeline (not a free-form graph),
unifying the two existing orchestrators:

```
0. validate_trade_intent            (deterministic)
1. build_portfolio_context          (deterministic, sanitized projection)
2. resolve_market_snapshot          (deterministic; mock/manual today → "unavailable" allowed)
3. run_deterministic_review         (deterministic; OWNS all numbers)
4. evaluate_actionability           (deterministic gate)
   ── GATE: blocked/analysis_only ⇒ skip LLM roles, emit deterministic-only review
5. build_agent_safe_evidence        (deterministic → the ONLY numbers roles see)
6. public_evidence_roles            (optional LLM, PUBLIC evidence only;
                                     async-READY dispatch seam, SEQUENTIAL first)
7. portfolio_aware_review_roles     (optional LLM, agent-safe projection only; gated + ordered)
8. run_freshness_guardrail          (deterministic; gates language)
9. compose_review_narrative         (deterministic structure + validated commentary)
10. evaluate_run                     (eval harness → eval_flags; process-level only)
11. persist_run_steps                (skipped unless a persisted need is later approved)
```

- **Deterministic-first fallback:** stages 0–4, 8, 9 work with zero LLM/provider
  availability.
- **Actionability gate (stage 4)** is also the cost gate (skip LLM when blocked).
- **Structural separation** of deterministic evidence vs agent commentary is
  preserved end to end.
- **Stage 6 is async-ready but runs sequentially first** (decision 8). Real
  fan-out arrives with the real-LLM commentary slice, not in P25A-T1.
- No in-run human-approval step (read-only review). HITL is a *future* Console
  concern (gated; ADR 0008 engine-staging).

## 5. Proposed state model

`AgentReviewRunState` — immutable, validated, **persistence-ready but not
persisted** (generalizes today's `AgentTeamAnalysisState`); `__post_init__` runs
recursive safety validation:

- Identity/version: `run_reference` (opaque), `workflow_version`,
  `generated_at`, `is_mock`, `analysis_only=True`.
- Sanitized input: `review_reference` (opaque), `supported_flow`,
  `review_flow_label` — no raw `TradeIntent`, no account/provider ids.
- Deterministic snapshot (single source of numbers):
  `review_actionability_status`, `broker_snapshot_freshness`,
  `market_quote_freshness`, `deterministic_evidence_summary`.
- Per-stage records: `stage`, `status`
  (`planned|completed|skipped|unavailable|gated|blocked`), `execution_mode`,
  `role_name?`, `provider_status?`, `unavailable_reason?`, `latency_ms?`,
  `tokens_in/out?`, `estimated_cost?`.
- Per-role outputs: `role_name`, `status`, `content_markdown?` (validated text
  only), `provider_status`, `is_mock`.
- Aggregate: `run_status` (`completed|partially_completed|failed_safe`),
  `provider_warnings`, `safety_flags`, `budget_used`.
- Evaluation: `eval_flags` — structured pass/fail for faithfulness,
  role-boundary, forbidden-wording, invented-metric, prompt-privacy.

Invariants (validated on construction, defense-in-depth at every hop): no raw
prompts, payloads, chain-of-thought, internal ids, private values, secrets,
advice/execution wording, or LLM-generated metric patterns. The **shape** of this
state is part of the hard-to-reverse core (reversibility ruling) and stays
app-owned. `failed_safe` still returns a usable deterministic review.

## 6. Proposed role model

Two layers. The Phase 19 role **rename is a separate back-compat slice**
(decision 7) and is **not** part of P25A-T1.

**Layer A — deterministic-first review roles (already in `agents/`):**
`portfolio_context_agent`, `trade_review_agent`, `risk_concentration_behavior`,
`freshness_guardrail_agent`, `report_composer_agent`.

**Layer B — optional LLM commentary roles (`agent_team/`), eventual rename:**

| Phase 19 name (today, unchanged in P25A-T1) | Eventual review-oriented name | Tier |
| --- | --- | --- |
| `fundamentals_analyst` | `public_fundamentals_evidence_agent` | public only |
| `news_analyst` | `public_news_evidence_agent` | public only |
| `technical_analyst` | `public_market_context_agent` | public only |
| `risk_management_agent` | `risk_review_agent` | agent-safe |
| `portfolio_manager_agent` | `review_synthesis_agent` | agent-safe |

Role→evidence allowlist is enforced: public roles → `PublicEvidenceBundle` only;
portfolio-aware roles → `AgentSafeDeterministicEvidenceProjection` only; **no
role** ever receives raw private context.

## 7. Proposed tool-use governance

Today there are **zero LLM-invoked tools**, and that stays true for MVP:
deterministic evidence is *pre-computed by the backend and injected*, not fetched
by an agent. This section is the governance model for *if/when* a public-data
tool is later approved — **schema-only**, no live tools.

- Tools are app-owned safe wrappers with typed input/output schemas; no raw
  provider SDK is exposed to an LLM; no ReAct "model picks the tool" loop in the
  portfolio-aware path.
- Three tiers gate every tool: **public** → public roles; **agent-safe**
  (deterministic projection) → portfolio-aware roles; **private** → never to any
  tool or LLM.
- Registry entry: `tool_name`, `role_allowlist`, `evidence_tier`, `input_schema`,
  `output_schema`, `mode` (`sync|async|queued`), `timeout_s`, `max_retries`,
  `per_call_cost_cap`, `is_mock`.
- `ToolResult` envelope: `tool_name`, `role_name`, `status`, `evidence_tier`,
  `data_mode`, validated `payload`, `provenance`, `freshness`, `latency_ms`,
  `estimated_cost`, `is_mock`. Audit log records status/latency/cost only — never
  inputs/outputs carrying private data.
- **MCP** (decision 5): future-only, and only as the provider-neutral boundary
  for **public/agent-safe** tools; a private-tier MCP server is **prohibited**.

## 8. Proposed memory / reflection policy

**Memory is disabled for MVP** (decision 9). No run-to-run, symbol-level,
user-level, outcome, or alpha memory. Only within-run **validated** role
summaries (already scoped to a run) may be reused. **Reflection exists only as
process/eval flags** (`eval_flags`) — never re-injected "lessons," never
outcome-based. Any future memory would be run/thread-level only, sanitized,
opt-in, deletable, retention-bounded, and reviewed by Claude B / Claude D.

## 9. Proposed evaluation and observability plan

Generalize the existing validators into a reusable `agent_eval` harness used by
both tests and the runtime `evaluate_run` stage:

| Check | Mechanism (existing → extension) |
| --- | --- |
| Evidence faithfulness | Flag any LLM-introduced figure not traceable to the deterministic projection (extend `GENERATED_METRIC_PATTERNS`). |
| Forbidden wording | `PROHIBITED_OUTPUT_PHRASES`. |
| Invented metric detection | `GENERATED_METRIC_PATTERNS`. |
| Role-boundary | Public roles never receive private/agent-safe evidence. |
| Prompt privacy | Recursive `find_forbidden_keys` / value / secret scans. |
| Tool-call correctness | When tools exist: role allowlist + envelope schema + audit record. |
| Deterministic-evidence consistency | State evidence == workspace deterministic values. |
| Latency & cost | Per-role + per-run timing and token/cost (`agent_steps`). |
| Failure classification | Provider statuses → `run_status`; partial-success semantics. |

Observability: structured `agent_runs`/`agent_steps`, a safe event vocabulary,
`eval_flags`, and per-run safety counters. Never log raw prompts/payloads/private
values. Extend `test_agent_team_scenarios.py` into a snapshot suite across flows ×
actionability states × provider-failure modes.

## 10. Latency and cost optimization plan

- Deterministic-first ⇒ p50 = deterministic path ($0, fast); LLM roles are
  additive only.
- Early-exit on blocked actionability ⇒ skip all LLM roles (largest saver).
- Mock default = $0 in dev/test/CI.
- Budget ceilings (reuse `agent_runs` budgets); on exceed → stop remaining roles,
  mark partial.
- Model tiering (cheap model for commentary, none for structure); short
  `max_tokens`; bounded loops (0–1).
- **Parallelism is a design seam (decision 8), not active now.** Public roles may
  later fan out in parallel and **aggregate by stable role key** (not completion
  order, to preserve determinism). Portfolio-aware roles remain gated and ordered.
  Real concurrency is switched on with the real-LLM commentary slice — mock has no
  latency to hide.

## 11. Error handling and partial-success behavior

- Every external/LLM/tool call degrades to a typed safe status → role unavailable
  + `provider_warning`. Deterministic evidence + actionability always survive
  (already implemented/tested).
- `run_status`: `completed | partially_completed | failed_safe`; `failed_safe`
  still returns the deterministic review.
- Blocked actionability **gates** (not fails) LLM roles.
- No raw exceptions/traces/payloads reach the client.

## 12. Security / privacy boundaries

- Three tiers: public / agent-safe (deterministic projection) / private (never to
  any LLM or tool). Role allowlists enforce the tier; this is the
  hardest-to-reverse decision and lives in app-owned code.
- No raw private account data in prompts, tools, state, logs, persistence,
  events, or reads — validated at every hop.
- No live external calls in the default path; mock default; live providers behind
  the backend-only gate (ADR 0005); no client provider/model/prompt selection.
- No execution/advice/guarantee wording; no LLM-generated metrics.
- No TradingAgents source copied; any adapter is public-evidence-only.
- Opaque references to the frontend; no internal ids/payloads/prompts/CoT.

## 13. First dirty-but-safe implementation slice (P25A-T1)

**App-owned `AgentReviewRunState` + mock workflow runner + timing/budget/eval
scaffolding.** Explicit scope constraints (per Codex B):

- **async-READY dispatch seam only — no real parallel execution** (roles run
  sequentially against mock);
- **no role rename** (keep Phase 19 names);
- **no persistence / no migration**;
- **no route behavior change** (the stateless preview route is untouched);
- **no frontend change / no composer activation**;
- **no live provider calls** (mock default).

Maximally additive: new modules + new synthetic tests; no change to external
behavior; fully offline. Eval harness (P25A-T2) and tool-governance envelope
(P25A-T3, schema-only) follow.

## 14. Files likely to change

**This task (design only):**
- `docs/claude-e-agentic/AGENTIC_SYSTEM_DESIGN_MEMO.md` (revised — this memo)
- `docs/codex-b-architecture/adr/0008-agentic-orchestration-spine.md` (new)
- `docs/shared/implementation_plan.md` (Phase 25A refinement)
- minimal routing notes in `current_roadmap.md`, `TASKS.md`, `CHANGELOG.md`

**P25A-T1 (first code, later):**
- new `backend/app/services/agent_team/run_state.py`,
  `review_runner.py`
- new tests `test_run_state.py`, `test_review_runner.py`
- touch (additive) `backend/app/services/agent_team/__init__.py`

**Explicitly NOT changed:** API routes, frontend (composer disabled), provider
gate, persistence/migrations, `../TradingAgents`.

## 15. Risks and open PM decisions

1. MVP shape: deterministic-only review first, or include mock LLM commentary in
   the first agentic slice? (Affects T1 scope.)
2. Role rename (decision 7) — schedule the separate back-compat slice when?
3. When (if) a durable/persisted/HITL need is committed — this gates LangGraph,
   persistence (T4), and async tooling (ADR 0008 engine-staging).
4. Budget defaults (per-run token/cost ceilings) need an owner.
5. Is a future bounded, public-evidence-only "considerations for/against" pass
   desired at all?

## 16. Questions for Codex A / founder

1. Confirm **deterministic-only review vs mock commentary** for P25A-T1.
2. Confirm Phase 25A may proceed to **P25A-T1 coding** after ADR 0008 acceptance.
3. Confirm **role rename** is scheduled as a separate slice (not now).
4. Confirm **memory stays disabled** for MVP.
5. Any **budget ceiling** guidance to encode now?

## 17. Recommended Phase 25A implementation-plan draft

See `Phase 25A — Agentic Workflow Foundation` in
`docs/shared/implementation_plan.md` (all tasks `proposed`/`not_started`, owner
Claude E, Codex B architecture/safety review). Decision record: ADR 0008.

- **P25A-T0** — Architecture contract + state/tool/eval design (this memo +
  ADR 0008). *Design only.*
- **P25A-T1** — App-owned `AgentReviewRunState` + mock runner + timing/budget/eval
  scaffolding; async-ready seam, sequential first. *First code.*
- **P25A-T2** — Reusable `agent_eval` harness.
- **P25A-T3** — Tool-use governance + safe `ToolResult` envelopes (schema-only).
- **P25A-T4** — Persistence/reload boundary — deferred until a persisted need is
  approved.
- **P25A-T5** — Codex B architecture/safety review (+ Claude B for
  prompt/memory/persistence-sensitive parts).
- **P25A-T6** — Claude A frontend handoff — after backend review only; does not
  enable the composer.

### Engine-staging gate (adjudicated)

Introduce LangGraph **only** when ≥2–3 are committed product requirements:
durable multi-turn threads; persisted/resumable state; human-in-the-loop
interrupts; dynamic agent selection/loops the fixed pipeline can't express. Even
then, wrap the same pure roles, keep state app-owned and tier-scoped, and never
stream raw tokens. Transport (SSE-first, WebSocket deferred) is decided
independently of the engine. Full record: ADR 0008.
