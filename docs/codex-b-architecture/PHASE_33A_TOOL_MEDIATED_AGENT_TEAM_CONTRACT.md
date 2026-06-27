# Phase 33A Tool-Mediated Agent Team Prototype Contract

Status: accepted architecture contract; implementation not started.
Owner: Codex B.
Related: ADR 0008, ADR 0009, Phase 29A/B/C, Phase 30A/B, Phase 32A.

## Product Direction

Portfolio Copilot is a read-only specialist review desk for busy self-directed
investors. The Agent Team should help answer:

> What would I be ignoring if I acted manually now?

It must not answer whether the user should make a trade, and it must not become
an AI stock picker, broker clone, order-entry system, or autonomous research bot.

Phase 33A shifts the Agent Team from deterministic-template summarization toward
a tool-rich qualitative analysis prototype. The shift is real, but the privacy
boundary stays strict:

- agents may request reviewed evidence through tools;
- the backend validates and executes every tool request;
- agents see only privacy-safe `ToolResult` envelopes;
- raw broker/provider/account payloads never enter prompts, tool results, logs,
  saved reports, examples, or tests.

## Core Decision

Build an app-owned, tool-mediated graph now. Do not introduce LangGraph in this
prototype.

The graph shape is:

1. Planner sees only an evidence catalog.
2. Backend executes allowed tools.
3. Role agents reason over `ToolResult` envelopes.
4. Evidence Auditor checks citations, contradictions, private-data leakage, and
   no-verdict wording.
5. Portfolio Manager synthesis produces the final "what would be ignored"
   briefing.
6. Existing output-safety validation runs before persistence/readback.

LangGraph remains deferred until at least two or three of these become committed
requirements: durable multi-turn threads, resumable state, human-in-the-loop
interrupts, or dynamic loops that the app-owned runner cannot cleanly express.

## Tool Tier Model

Reuse the existing governance scaffold in
`backend/app/services/agent_team/tools.py`.

Allowed tiers:

- `public`: public/source-rights-reviewed evidence only.
- `agent_safe`: lossy, privacy-safe portfolio/account evidence approved for
  portfolio-aware roles.

Prohibited tier:

- `private_forbidden`: must never back a tool.

The runner must reject:

- private-tier tools;
- public roles requesting `agent_safe` tools;
- tool args carrying account/provider/broker ids, account numbers, raw balances,
  buying power, holdings, positions, quantities, lots, raw payloads, secrets, or
  traces;
- tool results containing raw URLs/payloads unless a separate source-rights
  contract explicitly approves them.

## Tool Request Shape

The first implementation should use a narrow structured request, not free-form
tool calls:

- `tool_name`
- `requesting_role`
- `saved_report_thread_id` or saved evidence reference
- safe args only, such as section key, symbol/underlying, role key, or scope
  category
- optional reason code for audit

The model may propose a request. The backend decides whether it is allowed,
executes it, and returns either a safe result or a safe degraded result.

## ToolResult Envelope

Phase 33A `ToolResult` should extend the existing schema seam only as needed.
Every result must carry:

- `tool_name`
- `role_name`
- `status`
- `evidence_tier`
- `source_key`
- `source_label`
- `availability`
- `freshness` or `as_of`
- `scope`
- `caveat_codes`
- `evidence_refs`
- sanitized summary payload
- `is_mock` / data mode

It must not carry raw account/provider/broker identifiers, account numbers,
balances, buying power, holdings, positions, quantities, lots, raw provider
payloads, prompts, traces, secrets, or unreviewed URLs.

## Initial Tool Allowlist

Phase 33A starts with existing saved evidence only. No new public source, broker
source, market-data provider, web search, MCP, TradingAgents runtime, or live LLM
tool is approved by this contract.

Allowed first tools:

- `trade_intent_summary`
- `portfolio_scope_context`
- `deterministic_review_findings`
- `broker_snapshot_freshness`
- `market_quote_freshness`
- `public_company_profile`
- `evidence_gap_inspector`

Deferred tools, each requiring separate Codex B/source-rights review:

- `market_mood_context`
- `economic_awareness_context`
- `prior_report_context`
- `public_news_events`

## Agent Roles

Reuse existing role keys where possible. Additive roles require schema/backward
compatibility review before shipping to frontend read contracts.

Prototype roles:

- `portfolio_manager_agent`: final synthesis from audited findings.
- `risk_management_agent`: risk/freshness/caveat review from agent-safe tools.
- `fundamentals_analyst`: public company profile and reviewed public evidence.
- `news_analyst`: reviewed public event/news evidence when available.
- `technical_analyst`: reviewed public market/technical context when available.
- `options_structure_analyst`: proposed option-structure caveats, using only
  backend-owned deterministic labels and reviewed agent-safe tool results.
- `planner`: meta role; sees the evidence catalog only, not values.
- `evidence_auditor`: meta role; sees sanitized role outputs and citation graph
  only, not raw data.

## Reproducibility Boundary

The exact tool results used by a saved Agent Team report must be frozen for
readback. Reopening a report must not re-fetch tools, re-read current Account
Details, or silently recompute from current selectors.

Implementation may choose one of two reviewed patterns:

1. Additive saved `agent_tool_evidence` section on the saved evidence package.
2. Additive saved Agent Team report tool-results section.

Either pattern requires Codex B review before live UI renders the fields.

## Validator Requirements

Every tool request, result, role finding, auditor output, and final synthesis must
pass the existing safety spine plus any P33A-specific checks:

- forbidden key/value/private token scan;
- secret/log/prompt/trace scan;
- raw URL/payload ban unless separately approved;
- advice/order/execution/safe-to-trade/ready-to-trade/guaranteed-return wording
  ban;
- generated metric / invented number guard;
- citation completeness check;
- role/tool tier allowlist check;
- no public role receiving agent-safe evidence.

Deterministic backend services continue to own all numbers and calculations.
Agents may reason qualitatively about missing context, caveats, contradictions,
and open questions, but may not compute balances, collateral, concentration,
current-position truth, Greeks, probability, valuation, or feasibility.

## Phase 33A Task Sequence

### P33A-T0 - Contract

Owner: Codex B. Status: this document.

Acceptance:

- tool-mediated boundary accepted;
- LangGraph deferred with triggers documented;
- initial tool allowlist and deferred tools documented;
- next implementation owners named.

### P33A-T1 - Tool Registry And Envelopes

Owner: Codex C. Reviewer: Codex B.

Implement the in-process registry, safe request shape, safe `ToolResult`
envelope, initial mock/offline tool functions over existing saved evidence, and
tests for tier enforcement and private-data rejection.

No live providers, new sources, frontend changes, or LangGraph.

### P33A-T2 - Planner/Auditor/Role Design

Owner: Claude E. Reviewer: Codex B.

Define planner behavior, role prompts/projections, Evidence Auditor rules,
citation graph, and bounded one-pass critique behavior using only the P33A-T1
tool envelopes.

### P33A-T3 - First Tool-Mediated Saved Report Run

Owner: Codex C + Claude E. Reviewer: Codex B.

Wire a mock-first saved-report generation path that lets the Agent Team request
allowed tools through the backend runner and emits audited role findings. Use
existing saved evidence only.

### P33A-T4 - Reproducibility Freeze

Owner: Codex C. Reviewer: Codex B.

Persist the used tool-result envelopes through an additive reviewed saved-report
or saved-evidence contract. Readback must use frozen results only.

### P33A-T5 - Evaluation Harness

Owner: Claude E. Reviewer: Codex B.

Add synthetic/offline eval cases for useful ignored-risk discovery, honest
missing-data handling, citation completeness, contradiction rejection, no private
leaks, and no advice/order wording.

### P33A-T6 - Report UI Handoff

Owner: Claude A or Codex F. Reviewer: Claude B; Codex B if new fields are
rendered.

Only after T1-T5 produce stable sample outputs, design how reports display tool
citations, evidence gaps, audited role findings, and provenance.

## Block Conditions

Block any implementation that:

- gives an LLM direct broker/provider/market/web/EDGAR/TradingAgents clients;
- introduces LangGraph before the deferred triggers are met;
- introduces MCP or private-tier tools;
- sends raw account/provider/broker data, balances, holdings, positions,
  quantities, lots, raw payloads, prompts, traces, or secrets to prompts/results;
- lets agents compute or invent financial metrics;
- lets public roles receive portfolio/account evidence;
- renders new frontend fields before Codex B reviews the read contract;
- introduces advice, recommendation, order, execution, safe-to-trade,
  ready-to-trade, guaranteed-return, or AI-stock-picker posture.

## Next Implementation Prompt

Start with P33A-T1. Codex C should implement only the registry/request/result
layer plus mock/offline tools over existing saved evidence. Claude E work begins
after that envelope is concrete, unless a design-only prompt iteration is needed.
