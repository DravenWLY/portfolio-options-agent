# Phase 29A Agent Team Report Architecture

Status: proposed
Owner: Codex B
Related plan: `docs/shared/implementation_plan.md` Phase 29A

## Purpose

Phase 28A made a reviewed Trade Review saveable as an immutable source
snapshot. Phase 29A should turn that foundation into the product's main review
experience: an Agent Team report generated from a validated evidence package.

Portfolio Copilot should not become a deterministic report viewer. The
deterministic layer is the trusted calculation, validation, and provenance
foundation. The user-facing report should center the Agent Team's structured
analysis, with deterministic facts and caveats attached for auditability.

## Product Direction

The product should have one saved-review artifact model with layered content:

- deterministic evidence package: always present for reviewed saved sources;
- high-fidelity deterministic analysis surfaces: allowed and useful for
  portfolio-impact inspection;
- Agent Team synthesis: the primary narrative report when available.

This avoids a false split between "deterministic reports" and "agent reports."
The deterministic layer answers what the app knew and calculated. The Agent
Team answers what that evidence means in a well-rounded review.

## Core Architecture Decision

Use an evidence-package-first architecture.

For Phase 29A, Agent Team report generation must consume an immutable,
backend-built evidence package. Runtime agent tools are deferred until a
specific product interaction requires them.

Reasons:

- deterministic backend services own financial calculations;
- private broker/account data must not be fetched directly by LLM agents;
- saved reports must be reproducible;
- evidence can be validated before prompt use;
- ADR 0008 keeps the app-owned safety spine permanent;
- no private-tier MCP/tool path should be introduced by default.

## Evidence Package Contents

The saved evidence package should include only reviewed, display-safe,
agent-safe data:

- trade intent summary;
- generated timestamp and saved source reference;
- explicit review account state and portfolio context scope;
- account readiness and data freshness categories;
- deterministic actionability/review mode;
- portfolio impact summary;
- stock/ETF buy/sell or option-leg impact summary;
- before/after concentration or allocation deltas when backend-calculated;
- cash/collateral caveats and cash-state categories, not raw buying power;
- options exposure summary and same-account feasibility caveats;
- risk rule violation categories and severity labels;
- market quote freshness;
- economic awareness snapshot when available;
- Market Mood snapshot when available;
- company/news/earnings context only after a separate source/rights and
  evidence contract is reviewed;
- limitations and caveat codes.

It must not include raw account/provider/broker identifiers, account numbers,
raw balances, raw holdings, raw positions, quantities, tax lots, raw provider
payloads, prompts, traces, transactions, orders, secrets, or private strategy
thresholds.

## Deterministic Analysis Surfaces

High-fidelity deterministic views are still valuable. They should be designed
as analysis surfaces, not as the final report narrative.

Examples:

- portfolio before/after position-weight changes for a proposed stock/ETF
  trade;
- cash/collateral state and limitation explanations;
- concentration drift by account scope;
- risk-pattern alerts from deterministic policy rules;
- options exposure and assignment/exercise impact summaries;
- scope/freshness/caveat drilldowns.

These surfaces may live inside Trade Review, inside the saved report detail, or
inside a modal/drawer. The exact presentation belongs to the frontend/product
design agents. Architecture only requires that the data comes from reviewed
backend contracts and stays separate from Agent Team narrative generation.

## Agent Team Report Artifact

The Agent Team report should be generated from a saved evidence package and
persisted as part of the saved review artifact.

Recommended report states:

- `source_snapshot`: deterministic source package saved, no Agent Team report;
- `draft`: Agent Team report generation pending or in progress;
- `full_agent_report`: Agent Team report generated from the saved package;
- `agent_unavailable`: source saved, but Agent Team generation failed or was
  skipped safely.

The report read contract should expose:

- report metadata;
- saved scope metadata;
- deterministic evidence summary;
- deterministic analysis sections when available;
- Agent Team report sections when available;
- role summaries and provider-neutral warnings;
- limitations and caveats;
- generated/saved timestamps.

The report must never silently recompute from current Account Details, current
account selector, current portfolio context, current market data, or route
state.

## Runtime Tool Boundary

Do not introduce a runtime agent tool registry in Phase 29A.

Agent Team members should receive precomputed evidence, not callable private
data tools. Future callable tools may be considered only after a reviewed
product workflow needs them.

Allowed later candidates:

- explain a caveat code;
- summarize cached public market context;
- compare saved evidence sections;
- request an app-owned deterministic recalculation from an approved backend
  service.

Prohibited by default:

- fetch broker/account data;
- fetch balances, buying power, positions, lots, or transactions;
- fetch raw provider payloads;
- call SnapTrade, broker APIs, market-data providers, LLM APIs, or
  TradingAgents from agent tools;
- place, cancel, or modify orders;
- use private-tier MCP/tooling.

## UI Direction

Reports should feel like a saved analysis library, not a raw thread or contract
viewer.

Recommended hierarchy:

1. Agent Team synthesis when available.
2. Deterministic portfolio-impact analysis as visual supporting evidence.
3. Scope, freshness, and caveats as audit/provenance.
4. Technical details only in compact disclosure.

Design agents have freedom to choose the exact layout and interaction model.
Architecture constraints are:

- no order placement or execution UI;
- no advice/recommendation/buy/sell instruction wording;
- no AI stock-picker positioning;
- no market terminal, broad screener, or copied broker dashboard;
- multi-account scope stays explicit;
- deterministic values come from backend-owned labels/contracts;
- no raw private brokerage/account data in UI, prompts, tools, state, or logs.

## Suggested Surface Design Order

1. Agent Team Report detail
   - Product job: primary saved review experience.
   - Dependency: Phase 29A evidence and report contract.
   - Design path: Claude Design for concepts, Figma MCP for durable spec if the
     concept is accepted.
   - Implementation owner: Claude A or Codex F; visual review by Claude B;
     contract review by Codex B.

2. Reports Library
   - Product job: browse saved analyses and drafts.
   - Dependency: saved artifact statuses and report summary fields.
   - Design path: Claude Design, then Figma MCP if needed.
   - Implementation owner: Claude A or Codex F.

3. Trade Review deterministic impact view
   - Product job: show proposed-trade effect before Agent Team generation.
   - Dependency: backend deterministic before/after impact contract.
   - Design path: design-agent owned; may use modal/drawer/page section.
   - Implementation owner: Claude A or Codex F after Codex C contract.

4. Agent Console
   - Product job: diagnostic role-separated run view.
   - Dependency: real Agent Team output.
   - Design path: defer until report generation is clear.

5. Dashboard and Account Details
   - Product job: readiness and context, not report generation.
   - Dependency: existing contracts; polish can continue independently.

## Phase 29A Task Split

### P29A-T0 Architecture Alignment

Owner: Codex B. Product input: Codex A/founder.

Define evidence-package-first architecture, deterministic analysis surface
scope, Agent Team report artifact shape, runtime-tool deferral, and UI workflow.

Acceptance:

- deterministic layer is foundation, not final product endpoint;
- Agent Team report is the primary narrative output;
- high-fidelity deterministic impact views are allowed as supporting analysis;
- runtime private tools are deferred/prohibited by default;
- no silent recomputation from current mutable state.

### P29A-T1 Evidence Package Backend Contract

Owner recommendation: Codex C. Reviewer: Codex B.

Define the backend read schema for saved evidence packages consumed by Agent
Team report generation.

Acceptance:

- includes scope, actionability, impact, risk, freshness, and caveat summaries;
- includes deterministic before/after portfolio-impact fields only if backend
  can calculate them safely;
- excludes raw private data and prompt/tool traces;
- validator rejects forbidden keys/values/wording.

### P29A-T2 Agent Team Report Output Contract

Owner recommendation: Claude E. Reviewer: Codex B.

Define role outputs, report sections, synthesis structure, provider status, and
failure/degraded states.

Acceptance:

- output references only evidence package sections;
- no advice/order/execution wording;
- no private data expansion;
- role summaries can be saved into the report artifact.

### P29A-T3 Report Generation Backend Path

Owner recommendation: Codex C. Reviewers: Codex B and Claude E.

Generate and persist an Agent Team report from a saved evidence package.

Acceptance:

- resolves saved source by current user;
- uses saved evidence only;
- does not recompute from current account state;
- stores sanitized report output;
- handles provider unavailable states safely.

### P29A-T4 Reports UX Redesign

Owner recommendation: Claude A or Codex F. Reviewers: Claude B and Codex B.

Redesign Reports Library and Report Detail around Agent Team report content,
with deterministic evidence and scope/caveats as supporting sections.

Acceptance:

- product feels like a report library;
- deterministic-only artifacts are clearly drafts/source snapshots;
- full Agent Team reports are primary;
- no raw thread/contract-viewer layout.

## Open Founder Questions

- Should Agent Team report generation happen immediately after Trade Review, or
  on demand from the saved source?
- Should deterministic-only saved artifacts be visible to users as drafts, or
  hidden behind a "source snapshot" state?
- Which deterministic impact surfaces are P29A must-haves: before/after
  portfolio weights, risk-pattern alerts, options exposure, cash/collateral, or
  all of them?
- Should company/news/earnings context be included in P29A or deferred to a
  separate source/rights phase?
- Should Agent Console remain diagnostic-only once Agent Team report generation
  exists?

## Deferred

- Runtime agent tools.
- Streaming Agent Team report generation.
- Agent memory.
- Public/private MCP paths.
- Report export/share/version comparison.
- Transaction-derived tax-lot history.
- Broker action or execution workflows.
