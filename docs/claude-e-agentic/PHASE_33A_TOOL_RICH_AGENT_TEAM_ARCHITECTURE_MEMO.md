# Tool-Rich Agent Team Prototype — Architecture Discussion Memo

Status: discussion memo (design/architecture only; no implementation)
Author: Claude E (agentic AI system design)
For reaction by: Codex B (architecture/privacy/safety), Codex A / founder (product)
Proposed phase: **Phase 33A — Tool-Rich Agent Team Prototype** (alt label P32B)
Builds on / must reconcile with:
- ADR 0008 (`docs/codex-b-architecture/adr/0008-agentic-orchestration-spine.md`)
- ADR 0009 (stable machine role keys, backend-owned display labels)
- `backend/app/services/agent_team/tools.py` (P25A-T3 tool-governance scaffold)
- `backend/app/services/agent_team/review_runner.py` (app-owned runner)
- `backend/app/services/agent_team/report_output_safety.py` (output-safety spine)
- `backend/app/schemas/reports.py` (`SavedEvidencePackageRead`, freeze pattern)
- P29A/B/C output, public-evidence, and EDGAR freeze designs; P30A briefing shape

Product framing is unchanged: a read-only specialist review desk that answers
**"What would I be ignoring if I acted manually now?"**, never "should I make this
trade?".

## 0. The Founder's Shift, Restated Safely

Old model: deterministic review is the analysis brain; the Agent Team summarizes
reviewed deterministic evidence. The founder is right that this caps usefulness —
if we could predefine every review dimension deterministically, the team would be
redundant.

New model: the Agent Team becomes a **discovery and synthesis layer** that reasons
over *broad reviewed evidence* to surface ignored risks, missing context,
contradictions, and open questions. Deterministic review stays the **guardrail and
calculation layer**, not the whole brain.

The crucial safety reconciliation, and the spine of this whole memo:

> Deterministic backend services still own **every number and calculation**
> (collateral, concentration, risk-rule evaluation, freshness). Agents never
> compute, fetch, or invent metrics. What expands is the **qualitative reasoning**:
> which dimensions matter, what is absent, what contradicts, what to verify. Agents
> reason *about* the reviewed evidence; they do not become the source of the
> evidence.

This keeps ADR 0008's hard rule ("LLMs never compute, fetch, or invent metrics")
intact while genuinely growing the agent's analytical role.

## 1. Recommended Prototype Direction

Build a **tool-mediated, app-owned, planner+critique Agent Team** that runs once
at explicit generation time over a saved evidence package, freezes the tool
results it used, and produces an audited, citation-bound "what you'd be ignoring"
briefing.

Five design commitments:
1. **Tool-mediated, never tool-autonomous.** Agents emit a *structured tool
   request* (tool name + safe args); the backend executes the tool and validates
   the result; the LLM only ever sees a privacy-safe `ToolResult` envelope. The
   LLM never holds an API client, broker client, or raw payload. This is the
   single most important difference from a generic "tool-using agent."
2. **Reuse the existing three-tier governance** (`public` / `agent_safe` /
   `private_forbidden`) already scaffolded in `tools.py`. The private tier may
   never back a tool — enforced by allowlist, not convention (ADR 0008).
3. **Add a critique/audit node** (Evidence Auditor) that enforces citation
   discipline, contradiction detection, and the no-verdict boundary *before*
   synthesis. This is what makes broader reasoning trustworthy.
4. **Freeze for reproducibility.** The exact `ToolResult` envelopes used at
   generation are persisted into the saved package (same pattern as P29C EDGAR);
   reopening never re-fetches; regeneration reuses frozen results.
5. **Mock-first, app-owned, no new sources, no LangGraph for the prototype**
   (sections 2, 6.5).

## 2. LangGraph / "LongGraph": Not Yet — Build Engine-Agnostic Now

Recommendation: **do not introduce LangGraph for this prototype. Build the graph
in app-owned code now; adopt LangGraph later when its gate trips.**

Why, grounded in ADR 0008's explicit gate (introduce LangGraph only when ≥2–3 of:
durable multi-turn threads; persisted/resumable state; HITL interrupts; dynamic
agent selection/loops the fixed pipeline cannot cleanly express):
- This prototype is still **generate-once, read-only saved reports** — no chat
  composer, no human-in-the-loop steering, no durable conversation. That is 0 of
  the first three gate conditions.
- It does add **dynamic tool/agent selection and a bounded critique loop** — that
  is *one* condition, and a small DAG with a single capped re-pass expresses it
  cleanly in app code. One condition does not meet the gate.
- ADR 0008's bet-the-project protection is "keep roles pure and state app-owned so
  the engine is a two-way door." If we design the graph topology now as pure nodes
  over app-owned, tier-scoped state, **migrating to LangGraph later is cheap and
  non-rebuilding** — which is exactly the founder's stated concern.

What would change the recommendation (the trigger to write a LangGraph ADR):
durable multi-turn Agent Console conversation, resumable/checkpointed runs, HITL
interrupts, or the critique loop becoming genuinely dynamic/many-step rather than
a single bounded re-pass. At that point: wrap the *same* pure nodes, keep state
app-owned and tier-scoped (no shared cross-tier message state), and emit messages
only after output-safety validation (no raw-token streaming) — all per ADR 0008.

MCP stays deferred too: the prototype's tools are in-process backend functions, so
no tool protocol is needed; MCP would only ever wrap public/agent_safe tools later,
never the private tier (ADR 0008).

## 3. Proposed Graph Structure (engine-agnostic)

A small directed graph of pure nodes over app-owned, tier-scoped state. Runs on
the existing `ReviewRunner` seam now; portable to LangGraph later.

1. **Plan node (Planner agent).** Input: an *evidence catalog* — the tool registry
   plus each section's availability / freshness / tier / caveat metadata (labels
   only, never values). Output: a bounded plan of which dimensions to inspect,
   which roles to run, and which tools each role may call. The planner is the
   "discover what matters" brain and sees **no data values**, only the catalog.
2. **Evidence/tool nodes.** Execute the planned, tier-allowed tools backend-side;
   return validated `ToolResult` envelopes (labels/categories/availability/caveats/
   provenance only). Results are collected and (later) frozen into the saved
   package.
3. **Role agent nodes.** Each role reasons over its tier-allowed `ToolResult`
   envelopes + deterministic evidence and emits structured findings:
   ignored-risk flags, missing-context notes, contradictions, and open questions —
   each carrying evidence-reference citations. Public roles get public-tier tools
   only; portfolio-aware roles additionally get agent_safe tools.
4. **Critique/audit node (Evidence Auditor / Safety Reviewer).** Validates role
   outputs: every claim cites a real evidence reference; flags contradictions
   across roles; rejects unsupported claims, invented numbers, verdict/advice
   wording, and private-data leakage. May trigger **one** bounded re-pass
   (planner → tools/roles) when a contradiction or unsupported claim is found.
   Hard cap = 1 extra pass to stay cost-bounded and reproducible.
5. **Synthesis node (Portfolio Manager).** Produces the four-bucket "what you'd be
   ignoring" synthesis (per P30A-T2) from validated, audited findings, plus the
   manual verification checklist. No verdict.
6. **Output-safety + freeze.** The existing
   `validate_agent_team_report_output(..., evidence_package=evidence)` runs over
   the whole payload; then the used `ToolResult` set + sanitized findings are
   frozen into the saved package for reproducibility.

Bounded iteration, app-owned state, ordered portfolio-aware roles, parallel-ready
public roles, synthesis last — all consistent with ADR 0008's parallelism and
determinism stances.

## 4. Proposed Agent Roles

Keep ADR 0009 stable machine keys; display labels backend-owned. Existing five
keys are reused; three are added. Tiering is the load-bearing safety property.

| role (machine key) | tier | primacy | job |
| --- | --- | --- | --- |
| `portfolio_manager_agent` | agent_safe | primary | plan-aware synthesizer; four-bucket "what you'd be ignoring"; no verdict |
| `risk_management_agent` | agent_safe | primary | deterministic risk/concentration/collateral/freshness flags + gaps |
| `options_structure_analyst` (new) | agent_safe | primary (options flows) | reasons about the proposed option structure: collateral/assignment/exercise/expiry caveats; no Greeks values it didn't get from deterministic evidence |
| `fundamentals_analyst` | public | secondary | EDGAR company identity/listing context only (P29C); financial-statement gaps |
| `news_analyst` | public | secondary | reviewed news/event context; absence is a flagged gap |
| `technical_analyst` | public | secondary | reviewed public market/technical context labels; non-directional |
| `macro_market_context_analyst` (new) | public | secondary | reviewed macro / Market Mood / economic-calendar context as availability + labels |
| `evidence_auditor` (new) | meta (sees sanitized outputs + catalog, **not** raw data) | gate | citation discipline, contradiction detection, no-verdict / no-leak enforcement, bounded re-pass trigger |
| `planner` (new) | meta (sees catalog only) | orchestration | selects dimensions/roles/tools; sees no data values |

Notes:
- Planner and Auditor are **meta-agents**: planner sees only the evidence catalog
  (availability/freshness/tier), auditor sees only already-sanitized role outputs +
  the citation graph. Neither receives raw private data.
- `options_structure_analyst` is agent_safe (it reasons about the user's proposed
  structure), not a public "options education" role. Public option *concepts* stay
  inside it as non-account framing.
- Role keys are additive; the ADR 0008 role-rename remains a separate
  contract/back-compat slice, not folded here.

## 5. Proposed Tool Inventory

All tools return a governed `ToolResult` envelope (source label, tier, freshness
category/label, scope, availability, caveat codes, `collected_at`, stable
`evidence_ref`). Grouped by the founder's categories, with tier and today-vs-new.

| group | tool (proposed) | tier | backed by existing data today? |
| --- | --- | --- | --- |
| portfolio/account context | `portfolio_scope_context` (lossy sanitized scope + portfolio-shape categories) | agent_safe | Yes — existing scope projection / portfolio-shape summary |
| proposed trade details | `trade_intent_summary` | agent_safe | Yes — existing |
| deterministic review output | `deterministic_review_findings` (actionability, severities, caveat codes, impact category labels, concentration drift, liquidity/collateral, options exposure) | agent_safe | Yes — existing `SavedEvidencePackageRead` sections |
| broker/account freshness | `broker_snapshot_freshness` (category/label) | agent_safe | Yes — existing |
| market quote freshness | `market_quote_freshness` (category/label) | agent_safe | Yes — existing |
| Market Mood | `market_mood_context` (availability + reviewed label) | public | Partial — exists internal-demo; **rights-gated** |
| macro / economic calendar | `economic_awareness_context` | public | Partial — `not_reviewed` by default; **rights-gated** |
| company profile / EDGAR | `public_company_profile` (identity/listing only) | public | Yes — P29C, frozen at generation |
| company / news events | `public_news_events` (reviewed metadata, no bodies/URLs) | public | Contract exists but `not_reviewed`/unsourced; **highest source-rights risk (P29C)** |
| saved report history | `prior_report_context` (sanitized prior-briefing summaries/citations for same instrument/scope) | agent_safe | **New contract needed** |
| missing-data / caveat inspector | `evidence_gap_inspector` (the availability/freshness/caveat map = the "what's NOT here" catalog) | agent_safe | Mostly — derivable from existing availability fields |

`evidence_gap_inspector` is the keystone tool for "what would I be ignoring": it
enumerates the gaps the user would act without. The planner and auditor lean on it.

### 5.5 Q5/Q6 — Today vs new contracts

- **Usable with existing backend data today (in-process, no new source):**
  `trade_intent_summary`, `portfolio_scope_context`, `deterministic_review_findings`,
  `broker_snapshot_freshness`, `market_quote_freshness`, `public_company_profile`,
  `evidence_gap_inspector`. These are "read-the-saved-package" tools — minimal new
  contract, mock-first, the right place to start the prototype.
- **Require a new reviewed contract / source-rights slice (deferred, each its own
  P29C-style gate):** `market_mood_context`, `economic_awareness_context`,
  `public_news_events` (highest risk), `prior_report_context`, plus the
  tool-result-freeze persistence contract (section 7).

### 5.6 Q7/Q8 — Safe for prompts vs UI/report-only vs prohibited

- **Safe for agent prompts (tool envelopes):** all `public`/`agent_safe`
  `ToolResult` envelopes — labels, categories, availability, freshness, caveats,
  provenance, and section-key citations only. Public-tier → all roles; agent_safe →
  portfolio-aware roles only; meta-agents per section 4.
- **UI/report-only (never agent input):** exact display labels such as account
  nicknames and exact cash/buying-power labels, and any per-account display string
  — consistent with the lossy scope projection and ADR 0009.
- **Prohibited everywhere (private_forbidden — never a tool):** raw holdings,
  quantities, lots, exact cash balances, buying power, account values,
  account/provider/broker IDs, raw provider payloads, EDGAR/news raw bodies, URLs,
  secrets, logs, prompts, traces.

## 6. Safe Data-Access Model

1. **Registry + execution boundary.** Tools are backend functions registered with a
   `ToolRegistryEntry` (existing scaffold) carrying tier + role allowlist. The
   runner — not the LLM — executes them. The LLM emits a structured request; the
   runner validates the request against the calling role's tier allowlist, executes
   the backend function, validates the `ToolResult`, and returns the envelope.
2. **Tier gate at every hop.** `assert_tool_tier_allowed` rejects the private tier;
   `assert_role_tier_allowed` forbids agent_safe tools for public roles. Public
   roles can never even request agent_safe data.
3. **No raw clients in the model.** No broker/provider/market/LLM client is ever
   handed to an agent. "Tool-rich" means rich *envelopes*, not rich *access*.
4. **Args are safe by construction.** Tool args are restricted to non-private
   tokens (symbol, section key, scope category). The runner rejects any arg that
   carries an account/provider/broker id or private value.
5. **Recursive validation.** Every `ToolResult`, request, role finding, and the
   final payload passes the existing recursive forbidden-key/value/secret +
   advice/metric/level/URL scans before it can move to the next node or be
   persisted.

## 7. Evidence / Provenance Model

- Every `ToolResult` carries provenance: `source label`, `tier`, `freshness`,
  `scope`, `availability`, `caveat codes`, `collected_at`, stable `evidence_ref`.
- Agent findings cite `evidence_ref`s; the auditor builds a **citation graph** and
  rejects any claim without a backing reference (anti-hallucination).
- **Reproducibility freeze (new additive contract).** At generation, the set of
  `ToolResult` envelopes used + the sanitized findings + the citation graph are
  frozen into `SavedEvidencePackageRead` (new additive `agent_tool_evidence`
  section), exactly like P29C froze EDGAR. Reopening reads frozen results; it never
  re-fetches or recomputes from current state. Regeneration reuses frozen tool
  results (explicit replace per P29A-T5); the saved report itself is immutable and
  reproducible on read-back. The mock/deterministic path stays fully deterministic
  for default tests; live-LLM prose reproducibility is "frozen on read-back," not
  "identical on re-run."

## 8. Privacy / Safety Boundaries (carried from ADR 0008, extended)

- Mock provider default; no live LLM/provider/tool/broker/market calls in the
  default path; live providers only behind the ADR-0005 gate.
- Three-tier model enforced by allowlist; **private tier may never back a tool**.
- No raw private data in prompts, tool requests/results, run state, findings,
  events, reads, logs, persistence, docs, or tests (recursive validation at every
  hop).
- Deterministic backend owns all metrics; agents never compute/fetch/invent
  numbers; deterministic evidence stays structurally separate from agent
  commentary.
- Analysis-only: no advice/recommendation/buy/sell/hold/order/execution/
  safe-or-ready-to-trade/guaranteed-return/AI-stock-picker wording — enforced by
  the auditor node **and** the output-safety validators.
- No framework owns prompts, tiers, validation, deterministic-evidence ownership,
  run-state, or read/event contracts (ADR 0008). No TradingAgents source/execution
  in the portfolio-aware path (reference only).
- Memory stays disabled; only within-run validated findings may be reused
  (`prior_report_context` is a *separately reviewed*, sanitized, opt-in,
  retention-bounded contract — not free-form memory).

### 8.9 Q9 — How the team avoids becoming an AI stock picker

Defense in depth: (1) the product question is locked to "what would I be ignoring,"
never "should I trade"; (2) roles emit flags / gaps / open questions, never
conclusions; (3) the **Evidence Auditor** rejects any verdict, directional call,
price target, invented number, or buy/sell wording before synthesis; (4) the
output-safety validators reject the same at persistence; (5) deterministic backend
still owns every number; (6) the planner optimizes for *coverage of ignored
dimensions*, not investment conviction. The auditor + locked question are the new,
load-bearing additions.

## 9. Q10 — Evaluation Plan

Extend the existing `agent_eval` harness; all default eval is offline/mock/synthetic.

- **Citation completeness:** 100% of agent claims resolve to a frozen
  `evidence_ref`; uncited claims fail.
- **Zero private leaks:** recursive forbidden-key/value/secret scan over every
  request, envelope, finding, and the final payload — must be empty.
- **Zero advice/order wording:** existing phrase/level/metric validators must pass.
- **Ignored-risk discovery usefulness:** count of *distinct, evidence-backed*
  ignored-dimension flags vs. the P30A deterministic-template baseline (the team
  must add coverage, not just restate the template), plus human spot-rating on a
  synthetic fixture set.
- **Honest missing-data handling:** any "gap" claim must cite
  `evidence_gap_inspector`; unavailable sources degrade to honest skips, never
  invented context.
- **Contradiction handling:** seeded contradictory fixtures must trigger the
  auditor's bounded re-pass and surface as an open question, not a silent pick.
- **Reproducibility:** same saved package → identical read-back report; frozen
  tool results; deterministic mock path is byte-stable in tests.

## 10. Prototype Task Sequence (proposed)

Phase 33A — Tool-Rich Agent Team Prototype (mock-first, app-owned, no new sources
until each is separately gated):

- **P33A-T0** (Codex B + founder): architecture contract — accept this direction,
  the tier-mediated execution boundary, the planner/auditor scope, the
  reproducibility-freeze contract, no-LangGraph-yet, and the AI-stock-picker
  boundary.
- **P33A-T1** (Codex C + Claude E): activate the in-process tool registry +
  `ToolResult` execution over the **existing** saved-evidence-derived tools (the
  Q5 "today" set). Mock-first; no new sources; tier + validator enforcement.
- **P33A-T2** (Claude E): planner + auditor + role tool-consumption design
  (prompts, evidence projections, finding shapes, citation graph, bounded re-pass).
- **P33A-T3** (Claude E + Codex C): app-owned graph runner extension
  (planner→tools→roles→audit→synthesis, 1-pass cap), mock-first, behind the
  existing runner seam.
- **P33A-T4** (Codex C; Codex B review): reproducibility freeze — persist the used
  `ToolResult` set + sanitized findings + citation graph into
  `SavedEvidencePackageRead` (additive `agent_tool_evidence`); read-back, no
  re-fetch.
- **P33A-T5** (Claude E): eval-harness extension (section 9).
- **P33A-T6+** (Codex B + Codex C, each a separate source-rights/contract slice):
  new-contract data tools — `market_mood_context`, `economic_awareness_context`,
  `prior_report_context`, then `public_news_events` (highest risk last) — only
  after the in-process prototype is reviewed.
- **Deferred (own ADRs/phases):** live-LLM activation; LangGraph migration when its
  gate trips; durable multi-turn Agent Console; any frontend richer-briefing work.
- **Later UI** (Claude A / Claude B, P29B-style timing — only after contracts +
  stable sample payloads): render role flags, citations, gaps, and provenance in
  Report Detail.

## 11. Open Questions For Codex B / Founder

1. Accept Phase 33A as the next agentic phase (vs. branching it as P32B)? Confirm
   the proposed task IDs.
2. Confirm "deterministic backend owns all numbers; agents reason qualitatively"
   as the permanent line, even as agents grow more analytical.
3. Confirm no-LangGraph-for-prototype and the explicit re-trigger conditions.
4. Source-rights ordering for the new-contract tools — is Market Mood / macro
   acceptable as agent evidence at internal-demo tier, and is news deferred to last?
5. Is `prior_report_context` (cross-report agent input) acceptable given the
   memory-disabled stance, as a sanitized, opt-in, retention-bounded contract?
6. Acceptable cost/latency envelope for a planner + bounded re-pass under a live
   provider (affects budget guard design)?
7. Does the founder want the auditor's contradiction findings surfaced to users as
   "open questions," or kept internal as eval signal first?

## 12. Return Summary

- **Recommendation: PASS to start the prototype phase**, scoped to in-process,
  app-owned, mock-first tools over existing saved evidence behind a Codex B
  architecture contract (P33A-T0). New data sources, live LLM, and LangGraph stay
  deferred behind their own gates. No implementation should begin before P33A-T0.
- **Suggested IDs:** Phase 33A, tasks T0–T6 (section 10).
- **Codex B must review before implementation:** the tier-mediated execution
  boundary (app executes, LLM consumes envelope); the planner/auditor scope
  (catalog/outputs only, never raw data); the reproducibility-freeze additive
  contract; the no-LangGraph-yet decision and its triggers; and each new
  data-source tool as its own governance slice.
- **Codex C owns:** in-process tool registry/execution, `ToolResult` envelopes,
  saved-package freeze/persistence, new-source data tools, validator wiring.
- **Claude E owns:** graph topology, planner/auditor/role reasoning + prompts +
  evidence projections, citation model, eval harness, tool-consumption contracts,
  this memo and the role/finding shapes.
- **Claude A / Claude B own later (only after stable contracts + samples):**
  Report Detail rendering of richer role flags, citations, gaps, and provenance;
  visual/safety review.
- **Blockers:** none to start the discussion/contract. Implementation is blocked
  until P33A-T0 (Codex B + founder acceptance), per the review rule.
