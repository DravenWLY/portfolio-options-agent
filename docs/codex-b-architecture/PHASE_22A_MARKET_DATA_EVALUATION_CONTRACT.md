# Phase 22A Market Data Evaluation Foundation Contract

Status: approved architecture contract for initial backend slice
Date: 2026-05-25
Owner: Codex B - Architecture / Systems / Integration
Product approval: Codex A - APPROVE WITH REVISIONS

## Decision Summary

Phase 22A creates a provider-neutral, synthetic/replay-first foundation for
evaluating U.S. stock, ETF, and listed-options market data used by deterministic
trade review.

The first implementation task is backend-only and offline. It does not select
a provider, call a real provider, display live prices, add streaming, feed
agents, or alter frontend behavior.

Tradier is no longer the assumed scalable production provider. It may remain a
prototype/reference candidate only. Production provider selection is reopened
and requires written commercial-rights, licensing, pricing, and engineering
review.

Phase 21A remains paused. The Agent Console composer remains disabled.

## Phase Goal

Create a provider-neutral, synthetic/replay-first market-data evaluation
foundation for U.S. stock, ETF, and listed-options trade review that:

- keeps deterministic Python services responsible for financial metrics;
- represents the provenance and limitations of quote and option-chain inputs;
- protects the separation between portfolio snapshot freshness and quote
  freshness;
- supports later licensed provider comparison without coupling product
  contracts to one vendor.

## Scope Boundary

### Included In Initial Phase 22A Slice

- Review and narrowly refine existing market-data domain contracts where
  required for evaluation semantics.
- Synthetic/replay fixtures for underlying equity quotes, listed-option quotes,
  option chains, IV, and Greeks provenance.
- Offline deterministic tests for availability, freshness, data mode,
  unavailable/failure behavior, and provenance.
- Contract-gap documentation when an existing type does not yet encode an
  approved Phase 22A concept.

### Explicitly Excluded From Initial Slice

- Real provider calls, accounts, SDK setup, credentials, or `.env` changes.
- Paid, realtime, delayed-trial, or indicative external integrations.
- Public live/current-price UI or frontend edits.
- Streaming, WebSocket, or SSE market-data behavior.
- News/economic-calendar ingestion.
- LLM or agent consumption of market data.
- Phase 21A, realtime Agent Console, or composer activation work.
- TradingAgents integration or execution.
- Order placement, cancellation, execution, or broker destructive behavior.
- Raw provider payload exposure.

## Two-Stage Strategy

### Stage 1 - Early Evaluation

The only authorized initial implementation is synthetic/replay-based and
offline. Synthetic fixtures are not disposable test scaffolding; they are the
permanent CI and regression foundation for market-data behavior.

Optional later evaluation paths may be considered only after a separate PM and
architecture approval:

- **Alpaca Basic smoke testing**: limited-source or IEX-equity and indicative
  options evaluation only. Any output must be labelled `indicative` or
  `limited_source`. It must never be described as official, current, or live
  market truth.
- **Intrinio delayed-options trial**: only after written trial/use terms are
  reviewed. Output must be labelled `delayed` and `evaluation_only`.
- **Tradier Sandbox testing**: only for internal/local evaluation of its
  documented 15-minute delayed U.S. equity and options data. Sandbox Greeks
  are documented as unavailable, and application distribution requires a
  Tradier Partner relationship. Output must be labelled `delayed` and
  `analysis_only`.

None of these external evaluation paths is authorized by `P22A-T1` or
`P22A-T3`; each requires a separate PM-approved implementation task.

### Stage 2 - Commercial Provider Selection

Before selecting or implementing a production market-data provider, obtain
written responses for coverage, entitlements, display rights, derived-use
rights, retention/replay, possible later sanitized agent-evidence use,
engineering behavior, and scaling cost.

The RFI template and vendor comparison may be prepared in parallel as
documentation. Actual RFI outreach is deferred until early evaluation
clarifies the required product fields and Codex A reopens the commercial-scale
selection gate.

The initial vendor RFI set is:

- Intrinio;
- Databento;
- dxFeed;
- Massive only if it materially improves the comparison.

No provider is selected by this contract.

## Required Market-Data Concepts

The application must preserve distinct concepts for:

| Concept | Meaning | Must Not Be Collapsed Into |
| --- | --- | --- |
| Broker portfolio snapshot freshness | Recency/status of holdings, cash, and option positions | Market quote freshness |
| Underlying equity quote freshness | Recency/mode of stock or ETF quote used in analysis | Broker freshness or option chain freshness |
| Option quote/chain freshness | Recency/mode of selected contract or chain input | Underlying quote freshness |
| IV/Greeks provenance | Whether values are provider-supplied, backend-calculated, synthetic/replay, or unavailable | Generic provider readiness |

The market-data product vocabulary must explicitly support:

- `synthetic`
- `indicative`
- `delayed`
- `live`
- `unavailable`

Current Phase 12 models already express some, but not all, of this vocabulary.
`P22A-T1` may make the smallest backwards-conscious contract refinement required
to represent these modes and separate quote scopes. Existing modes such as
`manual`, `cached`, `eod`, and `unknown` must not be removed casually; any
compatibility choice must be documented in verification notes and tests.

`live` is reserved vocabulary during Phase 22A. Synthetic tests may cover its
policy behavior, but no production provider or frontend surface may emit or
claim live/current quote status until licensing, external-display rights, and
provider selection are approved.

## Snapshot And Provenance Boundary

Provider-neutral domain records must make safe metadata available for:

- quote/chain as-of time and received time;
- data mode and limitation label;
- underlying quote availability and freshness;
- selected option quote or chain availability and freshness;
- IV and Greeks availability;
- IV and Greeks source/provenance;
- failure or unavailable state without raw exception/provider content.

Do not expose through frontend- or agent-facing contracts:

- raw provider payloads;
- provider credentials, tokens, entitlement metadata, or account references;
- vendor-specific private identifiers;
- unsupported live/current-data claims.

Internal provider adapters may eventually require provider-specific mappings,
but those mappings are not part of the initial Phase 22A slice.

## Actionability Boundary

Actionability policy remains backend-owned. Phase 22A does not invent new
financial decision rules or let the frontend infer review status.

At a conceptual level:

| Data condition | Permitted review posture |
| --- | --- |
| `synthetic` | Analysis-only/demo behavior |
| `indicative` or `limited_source` | Analysis-only or manual confirmation, according to backend policy |
| `delayed` | Analysis-only or manual confirmation, according to backend policy |
| stale, unknown, unavailable, or provider failure | Warning or blocked review, according to backend policy |
| `live` and fresh | Only later eligible for normal-review consideration after provider/licensing approval and existing broker-freshness gates |

Even an approved live market quote does not prove that broker holdings, cash,
collateral, or option positions are current. Broker portfolio snapshot
freshness remains a separate gate.

## Agent And Frontend Boundary

- Phase 22A does not feed market or news data to LLM agents.
- A future sanitized market-evidence projection for agents requires separate PM,
  architecture, and privacy/security approval.
- Raw provider quote payloads must not enter prompts by default.
- Phase 22A initial implementation makes no frontend changes.
- The UI must not make public live-price or current-quote claims from
  synthetic, indicative, delayed, stale, or unavailable inputs.

## P22A-T1 Implementation Handoff

The only authorized implementation task is:

`P22A-T1 - Provider-Neutral Market-Data Snapshot Contracts And Synthetic/Replay Scenario Tests`

Codex C may inspect and, only where necessary, narrowly change:

- `backend/app/services/market_data/models.py`
- `backend/app/services/market_data/interfaces.py`
- `backend/app/services/market_data/freshness.py`
- `backend/app/services/market_data/snapshots.py`
- `backend/app/services/market_data/manual_provider.py` or a small
  synthetic/replay-only sibling module
- `backend/app/schemas/market_data.py` only if domain vocabulary changes require
  schema alignment
- focused market-data tests under `backend/tests/services/market_data/` and
  `backend/tests/unit/test_market_data_schemas.py`
- `docs/shared/implementation_plan.md` verification notes

Codex C must stop and report a contract gap rather than introducing a real
provider, route, persistence migration, frontend contract, streaming behavior,
or agent ingestion outside that bounded slice.

## Review Gates

1. `P22A-T1` completed provider-neutral synthetic/replay fixtures and offline
   tests only.
2. `P22A-T3` completed an official-public-documentation assessment and
   recommends Alpaca Basic for PM consideration as a bounded local/internal
   indicative evaluation candidate.
3. Codex A decides whether to authorize a new adapter task; until then there
   are no provider calls, accounts, credentials, SDKs, or trials.
4. External provider evaluation or later RFI-driven implementation requires a
   separately approved task and the rights review appropriate to its intended
   use.

## Acceptance Summary

Phase 22A may proceed when:

- the initial task remains offline and provider-neutral;
- the market-data vocabulary and provenance boundary are testable;
- broker freshness, underlying quote freshness, and option quote/chain
  freshness are not collapsed;
- no live/current UI claim, provider call, frontend change, or agent ingestion
  is introduced;
- no vendor is presented as selected.
