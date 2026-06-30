# Phase 34A Live Tool-Mediated Agent Team Prototype Contract

Status: accepted architecture contract; implementation not started.
Owner: Codex B.
Related: ADR 0008, ADR 0009, Phase 29C, Phase 30A/B, Phase 32A, Phase 33A.

## Product Direction

Portfolio Copilot is a read-only specialist review desk for busy self-directed
investors. The live Agent Team prototype should help answer:

> What would I be ignoring if I acted manually now?

The product must not answer whether the user should make a trade. It must not
become an AI stock picker, broker clone, order-entry system, automated research
crawler, or autonomous trading agent.

Phase 33A proved the app-owned tool-mediated scaffold with mock/offline tools.
Phase 34A moves toward the working prototype the founder asked for:

- live LLM role reasoning;
- real reviewed data sources where approved;
- backend-executed tools only;
- frozen saved-report reproducibility;
- no raw private data in prompts, tool results, saved reports, logs, screenshots,
  examples, docs, or tests.

## Working Prototype Definition

For Phase 34A, "working prototype" means an internal, read-only, backend-owned
Agent Team run that:

1. Starts from a saved trade-review evidence package.
2. Uses live LLM calls for role reasoning only when explicitly enabled.
3. Lets roles request reviewed backend tools through structured tool requests.
4. Gives LLMs only sanitized `ToolResult` envelopes and approved prompt context.
5. Uses real app-owned/saved data where approved instead of synthetic fixtures.
6. Freezes every used tool result and model output for saved-report readback.
7. Passes privacy, source-rights, citation, no-advice, and reproducibility gates.

This is still not production/public SaaS behavior. Production scale, broad
background refresh, autonomous crawling, public launch, and user-facing Agent
Console conversation are outside Phase 34A.

## Core Decisions

### Keep App-Owned Mediation

Even with live LLMs, agents do not receive direct clients for broker, provider,
market data, EDGAR, web search, news, MCP, TradingAgents, or databases.

Allowed flow:

1. Planner proposes tool requests from an allowed catalog.
2. Backend validates role, tier, args, source approval, and budget.
3. Backend executes the tool.
4. Backend validates and sanitizes the `ToolResult`.
5. LLM role receives only the sanitized result envelope.
6. Evidence Auditor checks role output before persistence.

### Live LLMs Are Allowed Only Behind Existing Backend Provider Gate

The repo already has backend-owned provider boundaries for mock, Google, and
OpenAI modes. Phase 34A may use those seams, but only with:

- disabled-by-default live mode;
- explicit backend configuration;
- no frontend provider selection;
- no frontend LLM calls;
- fake/injected transports in default tests;
- live smoke only with explicit founder authorization and no secret printing;
- timeout, retry, per-run token budget, and partial-report fallback;
- provider failure degrading to honest unavailable/skipped roles.

### Real Tools Arrive In Stages

Phase 34A does not approve an enormous live tool list all at once. It approves a
catalog process and staged real-tool rollout:

- M1: live LLM over already-reviewed saved evidence tools.
- M2: real market/macro context tools after source-rights and LLM-use review.
- M3: public company/news/event tools after separate source-rights review.

The user experience can still call this a live prototype once M1 runs with live
LLMs over real saved evidence. M2/M3 make it more useful, but they are not
allowed to skip review.

### LangGraph Is Optional, Not Load-Bearing Yet

Phase 34A should remain engine-agnostic for the first live run. A LangGraph spike
is allowed later in this phase only if it wraps the same app-owned nodes:

- planner node;
- backend tool execution node;
- role reasoning nodes;
- Evidence Auditor node;
- synthesis node;
- output-safety node;
- freeze node.

LangGraph must not own private data access, source clients, prompt safety, or
persistence. It is an orchestration library candidate, not the safety boundary.

## Approved Phase 34A Data Tiers

### Agent-Safe Real Data

Allowed only after backend sanitization into `ToolResult` envelopes:

- saved trade intent summary;
- saved deterministic review findings;
- saved portfolio scope/caveats;
- broker snapshot freshness labels/timestamps;
- market quote freshness labels/timestamps;
- account-level feasibility caveats, when represented as caveats only;
- normalized EDGAR public company profile already approved by Phase 29C;
- reviewed market mood/economic calendar summaries only after a Phase 34A
  source-rights task approves LLM/persistence use.

### User-Visible But Not Agent-Safe By Default

These may appear in existing account/detail surfaces if already reviewed, but
must not enter prompts/tool results without a separate contract:

- account nicknames/display labels;
- account reference handles;
- account detail table values;
- raw position rows;
- cash/buying-power/account-value labels;
- provider connection or broker status internals;
- source handles or raw refs.

### Prohibited In Prompts/Tool Results

Never send or freeze into LLM-visible tool results:

- raw account/provider/broker IDs;
- account numbers;
- balances, buying power, account values, cash values;
- raw holdings, positions, quantities, lots;
- raw provider payloads;
- raw URLs unless a source-rights contract explicitly approves display/use;
- prompts, traces, logs, secrets, API keys, access tokens;
- broker exports;
- generated reports with real private data as examples/tests.

## Initial Live Tool Catalog

### Approved For P34A-M1 Implementation

These use already-reviewed saved evidence and may become real, non-synthetic
tools without new source expansion:

- `trade_intent_summary`
- `portfolio_scope_context`
- `deterministic_review_findings`
- `broker_snapshot_freshness`
- `market_quote_freshness`
- `public_company_profile`
- `evidence_gap_inspector`

Conditions:

- consume frozen saved evidence, not current selectors;
- return lossy summaries and caveats, not raw private values;
- pass the P33A validators and P34A live-provider prompt validators;
- freeze exact used results in `tool_run_artifact`.

### Requires P34A Source-Rights Review Before Implementation

- `market_mood_context`
- `economic_awareness_context`
- `prior_report_context`
- `company_event_calendar`
- `public_news_events`
- `sec_recent_filings_metadata`

Each review must decide:

1. Source and rights.
2. Allowed normalized fields.
3. Whether LLM use is approved.
4. Whether saved-report persistence is approved.
5. Display attribution/caveat.
6. Retention/cache boundary.
7. Rate/budget limits.
8. Failure/degradation behavior.

### Explicitly Deferred

- raw SEC filing bodies, filing text, exhibits, XBRL facts;
- web search;
- MCP tools;
- TradingAgents runtime;
- broker/order/execution tools;
- autonomous background crawlers;
- bulk ingestion;
- Agent Console composer/interactive chat.

## Live Prompt Boundary

Live LLM prompts must include only:

- role name and role-safe instructions;
- locked product question;
- approved `ToolResult` envelopes;
- allowed citation refs;
- report-state and caveat instructions;
- output JSON/markdown schema if needed.

Prompts must not include:

- raw saved artifact payloads;
- raw account details;
- raw provider payloads;
- source URLs;
- developer/debug traces;
- secrets or config values;
- examples containing real private data.

The LLM may produce qualitative findings, contradictions, caveats, missing-data
questions, and synthesis. It may not compute financial metrics, infer private
portfolio values, generate target prices, rank trades, or produce action
instructions.

## Required Validators

Phase 34A inherits all P33A checks and adds live-provider checks:

- provider mode disabled by default;
- live mode requires explicit backend config;
- no secret values in provider config snapshots;
- prompt payload private-key/value scan;
- prompt raw URL/payload scan;
- output private-key/value scan;
- output advice/order/execution/safe-to-trade/ready-to-trade/guaranteed-return
  scan;
- generated metric/invented number scan;
- citation refs close against available/limited tool results;
- unavailable/gap refs are not cited as evidence;
- public roles do not receive agent-safe evidence;
- Evidence Auditor drops hard-block findings fail-closed;
- report survives partial provider/tool failures as honest skipped/unavailable
  sections.

## P34A Milestones

### P34A-M1 - Live LLM Over Reviewed Saved Evidence

Acceptance:

- live provider can be enabled only explicitly;
- default tests use fake/injected provider;
- live role outputs use only M1 tools;
- frozen `tool_run_artifact` contains used real saved-evidence tools and model
  outputs;
- no new public source implementation;
- no frontend contract expansion unless separately reviewed;
- saved report readback does not re-run providers or tools.

### P34A-M2 - Real Market/Macro Context

Acceptance:

- source-rights contract approved;
- normalized fields approved for LLM and saved-report persistence;
- tools return source labels, freshness, caveats, and unavailable states;
- no raw URLs/payloads or broad crawling;
- failure degrades honestly.

### P34A-M3 - Public Company/News/Event Context

Acceptance:

- source-rights contract approved before implementation;
- rights/retention/attribution documented;
- no source text/excerpts unless explicitly approved;
- no recommendations, ratings, or AI-stock-picker posture.

## Task Sequence

### P34A-T0 - Live Prototype Contract

Owner: Codex B. Status: this document.

Acceptance:

- working-prototype definition recorded;
- live LLM boundary recorded;
- real-tool staging recorded;
- source-rights gates recorded;
- task owners and review gates named.

### P34A-T1 - Live LLM Runner Gate For Tool-Mediated Reports

Owner: Codex C. Reviewer: Codex B.

Use the existing backend provider boundary to let the tool-mediated saved-report
runner call live providers only when explicitly configured. Add fake/injected
transport tests by default. Do not add new tools or sources.

Acceptance:

- default remains mock/offline;
- live mode disabled unless explicit config is present;
- no secret values logged, persisted, or surfaced;
- prompt payload contains only sanitized `ToolResult` envelopes;
- provider failures degrade to skipped/unavailable role output;
- freeze includes safe provider metadata, not raw provider payloads;
- no frontend change.

### P34A-T2 - Live Role Prompt And Auditor Design

Owner: Claude E. Reviewer: Codex B.

Design live role prompts, planner behavior, and Evidence Auditor checks over the
M1 tool catalog. Preserve the locked product question and no-verdict posture.

Acceptance:

- prompts consume `ToolResult` only;
- roles cite only usable evidence refs;
- auditor rejects advice, unsupported claims, invented numbers, and private leaks;
- one bounded re-pass rule remains;
- no LangGraph dependency.

### P34A-T3 - Real Saved-Evidence Tool Pack V1

Owner: Codex C. Reviewer: Codex B.

Convert the M1 tools from mock/offline placeholders to real saved-evidence-backed
tools where they are still not using current selectors or unreviewed private
fields.

Acceptance:

- tools read frozen saved evidence packages only;
- no current Account Details recomputation;
- no raw private values in `summary_payload`;
- exact tool results freeze into saved report;
- tests cover stock/ETF and simple options saved reports.

### P34A-T4 - Market/Macro Source-Rights Gate

Owner: Codex B. Reviewer: Codex A/founder.

Decide whether existing Market Mood and Economic Awareness surfaces may be used
as Agent Team tool sources.

Acceptance:

- approved fields listed;
- LLM use/persistence/display/retention decisions recorded;
- attribution/caveats recorded;
- implementation prompt for Codex C prepared.

### P34A-T5 - Market/Macro Tool Pack

Owner: Codex C. Reviewer: Codex B.

Implement only the tools approved by P34A-T4.

Acceptance:

- tools are backend-only and disabled/fail-closed if source unavailable;
- no raw URLs/payloads;
- freshness/caveats preserved;
- LLM sees only normalized `ToolResult`;
- eval and report-generation tests cover unavailable/stale/fresh states.

### P34A-T6 - Public News/Event Source-Rights Gate

Owner: Codex B. Reviewer: Codex A/founder.

Choose whether to add a news/company-event source for the prototype. Do not
implement a news tool before this gate.

Acceptance:

- source rights and retention understood;
- attribution/caveat wording approved;
- excerpt/URL/raw-payload policy approved;
- rate/budget and failure behavior approved.

### P34A-T7 - Live End-To-End Prototype Smoke

Owner: Codex B. Reviewers: Claude B for product-safety/visual if UI changes;
Codex A/founder for product usefulness.

Run a gated internal smoke only with explicit authorization for credentials and
without printing secrets or inspecting `.env` files.

Acceptance:

- one stock/ETF saved report and one simple-options saved report;
- live LLM role output;
- real saved account/review evidence;
- approved public/macro/news tools only if implemented;
- saved report reopens from frozen historical tool/model artifact;
- no private leaks, no advice/order/execution wording;
- failure states remain honest.

### P34A-T8 - LangGraph Architecture Spike

Owner: Claude E. Reviewer: Codex B.

Optional after M1. Compare app-owned runner vs LangGraph for durable Agent
Console and multi-turn orchestration.

Acceptance:

- no product dependency introduced;
- no private data or live tools executed;
- migration shape documented if/when Agent Console needs durable runs.

## Block Conditions

Block any implementation that:

- gives an LLM direct access to broker/provider/market/news/EDGAR clients;
- reads `.env`, prints credentials, logs secrets, or persists provider payloads;
- sends raw account/provider/broker data to prompts;
- lets agents compute financial metrics or feasibility;
- treats market/news/macro context as a recommendation signal;
- adds web search, MCP, TradingAgents runtime, or LangGraph as a safety boundary;
- introduces frontend fields before Codex B reviews the read contract;
- silently recomputes saved reports from current account state;
- introduces advice, recommendation, order, execution, safe-to-trade,
  ready-to-trade, guaranteed-return, or AI-stock-picker wording.
