# Phase 34A-T8 — LangGraph Integration Architecture Spike (Design Only)

Status: design-only (no implementation). PASS recommendation for a dev-only
prototype, with explicit blockers before any coding starts (§10).
Owner: Claude E. Reviewer: Codex B. Stop for Codex B review before implementation.
Inputs: P34A-T0 contract
(`docs/codex-b-architecture/PHASE_34A_LIVE_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md`);
current runner (`backend/app/services/agent_team/tool_mediated_report.py`,
`tools.py`, `run_state.py`); P34A-T2 design
(`PHASE_34A_T2_LIVE_ROLE_PROMPT_AUDITOR_DESIGN.md`); `../TradingAgents`
studied as an architectural reference pattern only (no source copied, no
dependency taken, `../TradingAgents` unmodified).

Locked product question (unchanged): **"What would I be ignoring if I acted
manually now?"** — never "should I trade?".

Governing constraint from the plan (P34A-T8 line, repeated here verbatim in
spirit): **LangGraph may wrap reviewed app-owned nodes but must not become the
privacy/safety boundary.** The app-owned backend remains responsible for tool
execution, evidence tiering, validation, citation ownership, persistence, and
redaction. LangGraph, if adopted, is an orchestration shell — nothing more.

---

## 0. Verdict up front

**PASS — for a dev-only, parallel LangGraph runner prototype (proposed
P34A-T8A), gated behind the blockers in §10.**

**BLOCKED — for everything beyond that**: wiring LangGraph into the Reports
route, Agent Console active runs, checkpoint persistence, any hosted tracing
(LangSmith), and any LLM-driven tool selection. These stay blocked until the
prototype proves output parity with the current runner and Codex B + Claude B
review the trace/redaction and dependency posture.

**Recommended architecture: wrap, as a parallel runner.** Not replace, not
"beside forever." The existing pure functions become graph nodes unchanged;
the graph is an alternative driver selected only by a backend-only dev flag;
`run_tool_mediated_agent_team` remains the production path and the rollback
path.

Honest cost/benefit summary: the current M1 runner is a **linear, bounded,
deterministic pipeline** (catalog → plan → tools → roles → audit → ≤1 re-pass →
synthesis → freeze). LangGraph adds little to M1 execution itself. What it
buys is (a) node-level observability during development, (b) a natural home
for the bounded re-pass as a conditional edge, (c) checkpoint/resume and
streamed per-node progress that a future durable Agent Console run needs, and
(d) a per-node seam for the eval harness. If Agent Console durable runs are
not on the roadmap, LangGraph is optional polish; if they are, adopting it as
a shell now — while the pipeline is small — is cheaper than retrofitting.

---

## 1. Replace, wrap, or sit beside? (question 1)

| Option | Assessment |
| --- | --- |
| **Replace** the runner with a LangGraph-native rewrite | Rejected. It would move control flow *and* logic into framework idioms (`MessagesState`, `ToolNode`, LLM tool-calling loops), re-opening every reviewed safety property: citation ownership, tier allowlists, fail-closed fallback, freeze contract. Highest risk, no unique benefit. |
| **Sit beside** (independent second orchestrator with its own node logic) | Rejected. Two implementations of planner/audit/synthesis drift apart; evals then compare two different products. |
| **Wrap (recommended)** | LangGraph nodes are thin adapters over the existing pure functions (`build_evidence_catalog`, `build_planner_plan`, `execute_tool_request`, `build_role_findings`, `_live_provider_role_findings`, `audit_findings`, `_portfolio_manager_finding_set`, `_summary_payload_from_run_state`). All validation stays where it is today — inside those functions and the dataclass `__post_init__` validators. The graph owns only sequencing. Introduced as a **parallel runner**: same inputs (`SavedEvidencePackageRead`, registry, provider resolution), same output (`SavedAgentTeamSummaryRead` with `tool_run_artifact`), selected by a backend-only flag that defaults to the app-owned runner. |

Wrap-as-parallel is also what makes rollback trivial (§9): flip the flag,
delete one module, zero contract changes.

## 2. Proposed graph topology (question 2)

Linear spine with one conditional loop and one fail-closed sink. All nodes are
backend-owned functions; no LangGraph prebuilt `ToolNode`, no LLM-selected
edges.

```
entry
  → build_catalog          (deterministic; build_evidence_catalog)
  → plan                   (deterministic planner; clamped MAX_TOOL_CALLS_*)
  → execute_tools          (app-owned execute_tool_request per RolePlan;
                            sequential in M1 for reproducibility)
  → role_findings          (per non-PM role: deterministic finding floor,
                            then optional live-provider prose overlay via the
                            reviewed T2/T3A seam; SEC/news finding stays
                            deterministic, unchanged)
  → evidence_auditor       (audit_findings: ref filtering, hard blocks,
                            contradiction detection)
  → [conditional edge] repass_needed?
        yes AND repass_count == 0 → bounded_repass → evidence_auditor
        no  OR  repass_count == 1 → continue        (MAX_PLANNER_REPASSES=1
                                                     stays a hard constant)
  → pm_synthesis           (deterministic template in M1; Codex B Q2 decision
                            unchanged)
  → output_safety          (report_output_safety / validate_or_fallback)
  → freeze                 (summary payload + SavedToolMediatedRunArtifactRead;
                            terminal)

any node failure (TypeError/ValueError/provider failure without floor)
  → deterministic_fallback (terminal; _deterministic_draft_summary /
                            _validate_or_fallback failed-safe payload —
                            exactly today's except-branch behavior)
```

Notes:

- **Planner stays deterministic in M1.** A future LLM-assisted planner may
  *propose* tool requests, but the backend validates against the registry
  allowlists and clamps to `MAX_TOOL_CALLS_PER_ROLE`/`MAX_TOOL_CALLS_TOTAL`
  before any execution. The planner node can never mint a tool name, arg key,
  or role pairing outside `default_tool_registry()`.
- **Role fan-out:** LangGraph `Send` could parallelize the four role branches.
  Do **not** do this in the first prototype — sequential execution preserves
  byte-for-byte reproducibility against the current runner. If parallelized
  later, merge must re-sort by `AGENT_TEAM_ROLES` order and
  `CANONICAL_EVIDENCE_ORDER` so frozen artifacts stay deterministic.
- **The auditor is a node, not an afterthought** — this is the main structural
  win. Node-level tracing then shows exactly which claims the auditor dropped
  and why, which is the debugging pain point today.
- The bounded re-pass maps naturally onto a conditional edge with a
  `repass_count` counter in state; the graph makes the "exactly once, never
  for hard blocks" rule visible instead of buried in the runner body.

## 3. Graph state contract (question 3)

State is a **typed, frozen, validated mirror of `ToolMediatedRunState`** plus
bookkeeping — effectively "the freeze contract, in motion." Every field must
already be legal to freeze; anything not persistable is not stateable.

Allowed in state:

- `evidence`: the input `SavedEvidencePackageRead` (already app-sanitized,
  frozen saved evidence — same object the runner receives today);
- `catalog: EvidenceCatalog`, `plan: PlannerPlan`;
- `tool_results: tuple[ToolResult, ...]` (the reviewed envelopes, unmodified);
- `findings: tuple[RoleFindingSet, ...]`, `auditor: AuditorRecord`,
  `open_questions`, `provider_runs: tuple[ProviderRunMeta, ...]` (safe
  metadata only), `provider_mode`, `repass_count: int`, `run_status`;
- opaque `run_id` / plan/audit/contract version strings.

Never in state (hard rule, enforced not just documented):

- raw provider request/response objects, prompt text, completion text other
  than auditor-validated `claim_text`;
- LangChain/LangGraph `messages` channels — **do not subclass
  `MessagesState`**; conversation history is not a concept in this product;
- secrets, API keys, provider config, `.env` values;
- anything `private_forbidden` tier; raw broker payloads, account numbers,
  quantities, tax lots, balances, provider ids;
- raw SEC paths/URLs/accession numbers/filing bodies; source URLs of any kind;
- cross-run memory, past-run context, or reflection text (§7);
- user identifiers beyond the opaque ids already in the freeze contract.

Enforcement mechanism: a single state-update wrapper (applied to every node)
that runs `validate_saved_tool_freeze_payload` /
`find_forbidden_keys(TOOL_FORBIDDEN_KEYS)` / `find_secret_like_values` over
each node's returned delta before it merges into state, failing closed to the
`deterministic_fallback` sink. This makes "LangGraph is not the safety
boundary" literal: the boundary is the same app-owned validators, executed on
every state write. Checkpointing (if ever enabled, §8) serializes only this
already-validated state, so a checkpoint can never contain what state cannot.

## 4. Preserving the ToolResult envelope contract (question 4)

- The tool-execution node calls `execute_tool_request` exactly as today;
  `ToolResult` dataclasses flow through state unchanged, keeping
  `contract_version="p33a_tool_result_v1"` and construction-time validation.
- **No LangChain tool abstraction**: no `@tool` decorators, no `ToolNode`, no
  `ToolMessage` conversion, no LLM tool-calling schema. The LLM never selects
  tools in this product; the planner does, and the planner is backend code.
- The live-provider node keeps the T1/T3A prompt seam:
  `_prompt_tool_result_envelope` remains the only projection an LLM ever sees
  (still stripped of `summary_payload`, `scope`, `as_of`, latency/cost).
- The freeze node keeps `_frozen_tool_result` as-is; `tool_run_artifact`
  readback stays byte-compatible, so Reports UI and eval fixtures need no
  changes.

## 5. Backend-owned citations and deterministic evidence ownership (question 5)

Unchanged, by construction:

- `evidence_refs` originate only inside `ToolResult` envelopes and
  deterministic findings; the live overlay still replaces `claim_text` only —
  the LLM cannot add, remove, or reorder refs (T2 decision, preserved).
- `audit_findings` still filters refs to
  `received ∩ usable_content_by_role ∩ available`, including the SEC
  role/citation guard (only `news_analyst` / `portfolio_manager_agent` may
  cite SEC recent filing metadata).
- `CANONICAL_EVIDENCE_ORDER` remains the single ordering authority; any future
  parallel fan-in re-sorts before merge (§2), so citations stay deterministic
  even if execution order changes.
- Parity criterion for the prototype (§9): given identical synthetic evidence
  and a fake provider, the graph runner and the current runner must produce
  **identical** `role_summaries`, `evidence_references`, `warning_codes`, and
  `tool_run_artifact` payloads (timestamps normalized).

## 6. Tracing and redaction policy (question 6)

This is where LangGraph's ecosystem is most useful and most dangerous.
LangSmith auto-tracing activates via environment variables and ships prompts,
completions, and full state to a hosted third-party service. That is a
straight violation of "no raw provider payload/prompt/trace persistence" and
of the brokerage-data boundary.

Policy:

1. **Hosted tracing is prohibited, permanently, for any run.** The graph
   runner must include a startup guard that hard-fails (refuses to construct
   the graph) if `LANGCHAIN_TRACING_V2` / `LANGSMITH_TRACING` /
   `LANGSMITH_API_KEY`-style variables are set. A unit test asserts this
   guard. "Fail closed if someone exports an env var" is the posture; relying
   on nobody exporting it is not.
2. **What a trace may contain** — exactly the fields already legal in the
   freeze contract, and nothing else: node name, node status, timing,
   `tool_name`, `status`, `evidence_tier`, `availability`, `freshness`
   category, `caveat_codes`, `evidence_refs`, warning codes, dropped-claim
   codes, plan/audit versions, token counts, `is_mock`, run/thread opaque ids.
3. **What must never appear in a trace**: prompt text, completion text,
   `claim_text` bodies (pre- *or* post-audit — trace codes, not prose),
   `summary_payload`, evidence section values, scope values, `as_of`
   timestamps tied to real accounts, URLs, secrets, account data.
4. **Implementation**: do not derive traces from LangChain callbacks (they see
   raw LLM I/O). Derive the trace from **validated graph state deltas** — the
   same wrapper from §3 emits a redacted trace event after validation. Then a
   trace is provably a projection of already-safe data.
5. **Dev-only in M1**: traces live in memory / dev stdout during a run over
   synthetic evidence, and are discarded. No trace persistence, no trace API,
   no frontend exposure.
6. **Future internal audit artifact — allowed, later, under conditions**: a
   persisted "run trace" is acceptable only as an additive field that (a) is
   built from the §3 validated state, (b) passes
   `validate_saved_tool_freeze_payload`, (c) goes through Codex B contract
   review and Claude B privacy review, and (d) still contains codes/metadata
   only. Note the existing `tool_run_artifact` already *is* a redacted trace
   of the M1 pipeline; a LangGraph trace only adds node timing/ordering
   detail. This is why trace persistence is not urgent.

## 7. TradingAgents comparison (question 7)

Reference-only reading of `../TradingAgents` (`tradingagents/graph/*`,
`agents/utils/agent_states.py`). No source copied; no dependency taken.

| Dimension | TradingAgents | Portfolio Copilot posture |
| --- | --- | --- |
| Graph | LangGraph `StateGraph` over `MessagesState`; analyst → `ToolNode` loops; conditional debate rounds | Adopt the *shape* (small graph module, separated conditional logic, compiled workflow) — with typed validated state, no messages channel, no tool loops |
| Debate | Bull/bear researcher debate + aggressive/conservative/neutral risk debate, judge decides | **Avoid.** Debate-to-verdict exists to answer "should I trade?" — the question this product refuses. Our analogue is the Evidence Auditor + structured contradiction detection surfacing *open questions*, already implemented and more honest for this product |
| Analyst roles | Market/social/news/fundamentals analysts author reports from live-fetched data | Keep our roles as-is; they consume sanitized `ToolResult` envelopes over frozen saved evidence, never fetch |
| Tool usage | LLM-selected tool calls via `ToolNode`, direct yfinance/news/API fetching inside the graph | **Avoid entirely.** Backend planner selects tools; tools are read-only projections over frozen evidence; acquisition happens outside the run behind source-rights gates |
| Memory | `TradingMemoryLog`: past decisions + realized returns fetched post-hoc, reflections injected into future runs | **Avoid.** Outcome-scored memory is performance framing for trade decisions — advice drift by construction, and it would persist derived real-account data. Cross-run memory is out of scope |
| Tracing/logging | Full state JSON dumped to disk per run, including complete prompt/debate histories | **Avoid.** Violates our no-raw-prompt/trace persistence rule. Our equivalent is the validated frozen `tool_run_artifact` + §6 redacted dev traces |
| Checkpointing | Optional per-ticker SQLite saver; resume by thread_id (ticker+date); cleared on success | **The genuinely useful pattern.** Same idea, but serialize only §3-validated state, Postgres-backed if ever persisted, opaque thread ids, Codex B-reviewed (§8) |
| Signal processing | Extracts BUY/SELL/HOLD from final text | **Avoid absolutely.** No decision extraction of any kind |
| FRED/macro | Direct macro/news fetching as agent tools | Keep our approved FRED-metadata lane (attribution, metadata-only, rights-gated). LangGraph adds no new source authority; T4/T6 gates still govern |

Net: TradingAgents demonstrates that LangGraph handles multi-stage
multi-agent orchestration, streaming debug, and resumable runs well. Nearly
everything else it does — LLM tool loops, debate-to-verdict, outcome memory,
full-state dumps — is exactly what Portfolio Copilot's boundaries exist to
prevent.

## 8. Where to introduce LangGraph first (question 8)

Order of introduction:

1. **Developer trace mode + eval harness (first, recommended).** Parallel
   graph runner over synthetic evidence fixtures; parity evals against the
   app-owned runner; redacted node traces for debugging. Zero production
   surface, zero persistence, full rollback. This is where the "easier to
   develop/debug/evaluate" founder interest is actually tested.
2. **Agent Console active runs (second, and the real payoff — only if
   parity holds).** Durable, resumable, per-node streamed progress ("Risk
   Manager: completed · Auditor: re-pass") is what LangGraph uniquely buys.
   Requires the checkpoint-persistence review in §9 and Claude A/Claude B
   frontend work. Frontend consumes backend run-state reads only — no
   frontend LLM calls, unchanged.
3. **Saved report generation (last, possibly never in M1).** The Reports
   route is the accepted golden path; switching its engine is all risk and no
   user-visible gain until (2) exists. Only after long parity soak, and even
   then behind `POA_AGENT_TEAM_RUNNER` with app-owned as default.

Not "eval harness only" as an end-state: if evals are the only consumer,
maintaining two runners isn't worth it — in that case conclude the spike and
retire the graph.

## 9. Migration plan (question 9)

Proposed task sequence (each one small, reviewable, stop-for-review):

- **P34A-T8 (this doc)** — architecture design. Owner Claude E; reviewer
  Codex B. Codex B decisions requested in §11.
- **P34A-T8A — minimal prototype (dev-only parallel runner).** Owner Claude E
  (agentic lane per AI_TEAM); reviewer Codex B. Scope: `langgraph` behind an
  optional backend extra (e.g. `agent-graph`, mirroring `live-llm`); new
  module `backend/app/services/agent_team/graph_runner.py` wrapping the §2
  nodes; §3 state + validation wrapper; §6 tracing kill-switch guard; no
  route/API/schema changes; no checkpointer. Tests: parity test (§5),
  kill-switch test, fail-closed test (a node raising → deterministic
  fallback payload identical to today's except-branch).
- **P34A-T8B — compatibility shim + eval integration.** Owner Claude E;
  reviewer Codex B. A `build_tool_mediated_agent_team_summary`-shaped entry
  point selecting the runner via backend-only
  `POA_AGENT_TEAM_RUNNER=app_owned|langgraph_dev` (default `app_owned`;
  `langgraph_dev` refuses outside test/dev config). Extend the P33A eval
  harness to run both runners across the fixture matrix and diff
  findings/citations/warnings/artifacts. Claude B privacy review of the trace
  event shape.
- **Decision gate (founder + Codex B):** adopt for Agent Console, or retire
  the spike. Evidence: parity results, dev-experience notes, dependency
  audit.
- **P35x — durable Agent Console runs (only if adopted).** Codex B contract
  first (checkpoint persistence: serializer allowlist = §3 state, Postgres
  saver, opaque thread ids, retention/deletion, resume semantics); Codex C
  implements persistence/route wiring in the backend lane; Claude E implements
  graph-side resume; Claude A builds the console UI on backend run-state
  reads; Claude B reviews UI copy (progress labels must not imply
  advice/urgency) and privacy of persisted state.
- **Rollback path at every step:** flag defaults to `app_owned`; removing
  `graph_runner.py` + the optional extra restores today's system exactly; no
  contract, schema, or frozen-artifact change anywhere in T8A/T8B, so saved
  reports are untouched.

## 10. Risks and mitigations (question 10)

| Risk | Mitigation |
| --- | --- |
| Private data leakage through traces (LangSmith env auto-activation; callbacks seeing raw LLM I/O) | §6: startup kill-switch + test; traces derived from validated state only, codes not prose; no trace persistence in M1 |
| Prompt/raw payload persistence via checkpointer (a checkpointer serializes *whatever is in state*) | §3: nothing unfreezeable enters state; no checkpointer in T8A/T8B at all; future checkpointing gated on Codex B contract review |
| Agent overreach (framework gravity toward LLM tool-calling loops, `MessagesState`, agentic autonomy) | §2/§4: no `ToolNode`, no messages channel, planner deterministic and clamped; graph edges are backend conditionals, never LLM decisions |
| Advice/actionability drift (graph makes multi-pass critique cheap → "richer reasoning" pressure) | Locked question unchanged; auditor hard blocks (advice wording, invented metrics, SEC interpretation) still run on every finding; re-pass stays ≤1 by constant, not config |
| Harder reproducibility (parallel fan-out, framework version churn) | Sequential M1 execution; canonical ordering on any future merge; parity evals in CI; pin `langgraph`/`langchain-core` versions in the optional extra |
| More complex failure modes (framework exceptions, recursion limits, partial-state merges) | Every node failure routes to the same deterministic fallback sink as today's except-branch; recursion limit irrelevant while the graph is a bounded DAG + one loop |
| Dependency/supply-chain surface (`langgraph` pulls `langchain-core` etc.) | Optional extra, not a base dependency; founder/Codex A approval required (§11); dependency audit at the decision gate |
| Two-runner maintenance drift | Nodes are the *same functions*; only sequencing is duplicated; decision gate explicitly retires the spike if not adopted for Agent Console |

## 11. Blockers before any coding (explicit "do not implement yet")

1. **Codex B review of this design** — PASS required, plus a short ADR
   ("LangGraph as orchestration shell; app-owned validators remain the safety
   boundary") since this adds an external boundary-adjacent dependency.
2. **Founder/Codex A approval to add the `langgraph` dependency** (new
   third-party surface, even as an optional extra).
3. **P34A-M1 exit confirmed** — T8 is optional *after* M1; T3B/T4/T5 and the
   active T7 smoke take precedence for Codex C/Codex B bandwidth.
4. **Tracing policy sign-off (§6)** — kill-switch behavior and the
   trace-field allowlist approved by Codex B, with Claude B privacy review.
5. **Parity criteria pinned (§5)** — what "identical output" means
   (normalized timestamps, artifact field list) agreed before T8A starts.
6. **No checkpoint persistence of any kind** until a separate Codex B
   contract exists (P35x); T8A/T8B compile the graph without a checkpointer.

## 12. Return summary

- Recommendation: **PASS for dev-only prototype (P34A-T8A/T8B), BLOCKED beyond
  that** until parity + reviews.
- Architecture: **wrap existing app-owned functions as graph nodes, run as a
  parallel dev runner**; app-owned runner stays production and rollback path.
- Topology: linear spine (catalog → plan → tools → roles → auditor →
  conditional bounded re-pass → PM synthesis → output safety → freeze) with a
  single deterministic-fallback sink.
- State: freeze-contract-shaped, validated on every node write; no messages,
  no prompts, no secrets, no private tier, no memory.
- Tracing: hosted tracing hard-blocked; dev-only redacted traces derived from
  validated state; persistence deferred and separately reviewable.
- TradingAgents: borrow graph modularization, conditional-logic separation,
  checkpointer *pattern*, and debug streaming; reject LLM tool loops,
  debate-to-verdict, BUY/SELL/HOLD signal extraction, outcome memory, and
  full-state prompt dumps.
- First surface: eval harness + developer trace mode; Agent Console durable
  runs are the adoption payoff; Reports route last, if ever in M1.
- Ownership: Claude E (graph design/prototype/eval parity), Codex B
  (review/ADR/gates/checkpoint contract), Codex C (any later
  persistence/route wiring in the backend lane), Claude A (future console UI
  on backend reads), Claude B (privacy/trace review + UI copy safety),
  Codex A/founder (dependency and scope go/no-go).
