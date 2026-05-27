# Phase 22A Alpaca Basic Local/Internal Evaluation Adapter Contract

Status: approved architecture handoff for implementation planning
Date: 2026-05-26
Owner: Codex B - Architecture / Systems / Integration
Product approval: Codex A - APPROVE WITH REVISIONS
Task: `P22A-T4`

## Decision Summary

Portfolio Copilot may implement an Alpaca Basic-shaped adapter only to test
whether an early, low-cost market-data source can map into the existing
provider-neutral stock/ETF and listed-options snapshot contracts.

This is not a live-provider integration gate. `P22A-T4` is backend-only,
injected-client and mock-response first, and has no authorized network-call
path. The adapter must produce `indicative`, analysis-only market-data
semantics and must preserve a safe `limited_source` coverage/provenance label
where Alpaca Basic does not represent consolidated licensed market truth.

Commercial provider comparison and RFI material remain reference documents.
Commercial outreach and production selection are parked until Codex A reopens
that track for scale or external-display planning.

Phase 21A remains paused. The Agent Console composer remains disabled. Market
data from this adapter must not enter any LLM or agent-team workflow.

## Purpose

Determine, through deterministic mock-driven backend tests, whether the
documented Alpaca Basic response shapes are sufficient to exercise:

- a stock or ETF underlying quote snapshot;
- an option quote snapshot;
- an option chain snapshot;
- IV and Greeks availability or unavailable states;
- provider failure and incomplete-field behavior;
- underlying quote freshness separately from option quote/chain freshness.

The slice exists to validate mapping and safety behavior, not to validate
provider uptime, credentials, entitlements, redistribution rights, or
production suitability.

## Authorized Boundary

### Included

- An app-owned adapter under `backend/app/services/market_data/` that
  implements existing provider-neutral market/option protocols where
  practical.
- A narrow injected client protocol or callable boundary used only with fake
  clients in default tests.
- Mapping from synthetic Alpaca-shaped responses into existing domain
  snapshots and freshness/actionability policy.
- A smallest reasonable provider-neutral representation of the
  `limited_source` coverage/provenance constraint, if the existing typed
  contracts cannot represent it.
- Focused deterministic unit/service tests using synthetic payloads only.

### Not Included

- Alpaca credentials, `.env` changes, account creation, SDK installation, or
  API/network calls.
- A runtime provider factory, route, scheduled job, default provider switch,
  or frontend API surface.
- An external smoke test, even if marked optional.
- Public or private-alpha user display of provider data.
- `live`, realtime, official, NBBO, OPRA-current, or production-data claims.
- Commercial provider selection, vendor outreach, or licensing negotiation.
- Tradier or Intrinio adapter work.
- Frontend changes, market dashboard cards, news, symbol search, streaming, or
  persistence.
- Agent/LLM market-evidence ingestion, Phase 21A, or TradingAgents work.

## Existing Contract Mapping

The implementation should adapt into the existing app-owned concepts:

| Alpaca evaluation concept | Required app-owned representation |
| --- | --- |
| Basic equity feed | `data_mode="indicative"` plus a typed/safe `limited_source` provenance or coverage representation |
| Indicative option quote or chain | `data_mode="indicative"` and `analysis_only` unless existing policy yields a stricter blocked state |
| Underlying quote input | `freshness_scope="underlying_quote"` |
| Selected option quote input | `freshness_scope="option_quote"` |
| Option chain input | `freshness_scope="option_chain"` |
| Risk/report compatibility reference | Aggregate `freshness_scope="market_quote"` plus preserved granular `input_freshness_scope` |
| IV/Greeks supplied in synthetic Alpaca response | Provider provenance with the same indicative/limited-source boundary |
| IV/Greeks absent or incomplete | Explicit unavailable or missing provenance; no inferred value |
| Provider/client error | Sanitized unavailable/error result or domain exception handled by existing backend policy; no raw payload/exception leakage |

`limited_source` is an approved product concept but is not currently a
`DataMode`. Codex C must not overload `live`, conceal the limitation in
free-form copy alone, or change frontend contracts opportunistically. If the
existing provider-neutral contract does not support a narrow typed coverage
or provenance representation, Codex C may propose the smallest backend-only
contract addition with tests, or stop with a bounded blocker for Codex B.

## Activation And Transport Boundary

`P22A-T4` must have no live transport:

- no HTTP client is instantiated by app startup or default test execution;
- no credential/config loading is introduced;
- no adapter registration makes Alpaca a default or selectable runtime
  provider;
- tests construct the adapter with an injected fake client only.

An actual Alpaca request using credentials is a separate future PM-approved
smoke-test task. Such a task would need explicit opt-in configuration, rate
limit/failure handling, human-controlled credential setup, and a renewed
review of data-use constraints.

## Actionability And Safety Rules

- Alpaca Basic evaluation output is never labelled `live`.
- Indicative or limited-source market data cannot independently make a review
  actionable.
- Output remains `analysis_only` unless existing backend-owned policy returns
  a stricter blocked state for stale, missing, unknown, or failed inputs.
- Deterministic Python services remain responsible for financial metrics.
- Broker portfolio snapshot freshness remains distinct from underlying quote
  freshness and option quote/chain freshness.
- Raw provider payloads, provider credentials, entitlement information,
  exception bodies, and vendor-private identifiers must not reach frontend
  schemas, report messages, prompts, or agent inputs.

## Expected Implementation Surface

Codex C may inspect or narrowly change:

- `backend/app/services/market_data/interfaces.py`
- `backend/app/services/market_data/models.py`
- `backend/app/services/market_data/freshness.py`
- `backend/app/services/market_data/snapshots.py`
- a new bounded adapter module such as
  `backend/app/services/market_data/alpaca_evaluation_provider.py`
- `backend/app/services/market_data/__init__.py`, only for safe exports
- focused tests under `backend/tests/services/market_data/`
- `backend/tests/unit/test_market_data_schemas.py` or
  `backend/tests/unit/test_risk_schemas.py` only if a narrow typed provenance
  refinement requires schema/read alignment
- `docs/shared/implementation_plan.md`, verification notes only

It must not modify routes, frontend code, agent-team code, provider secrets,
database migrations, or `../TradingAgents`.

## Required Test Scenarios

All tests use fake/injected clients and synthetic Alpaca-shaped data:

1. Indicative/limited-source stock or ETF quote maps to an underlying quote
   snapshot and is not actionable.
2. Indicative option quote maps with separate `option_quote` scope.
3. Indicative option chain maps with separate `option_chain` scope.
4. IV and Greeks present map with explicit provenance.
5. IV and Greeks missing or unsupported map as unavailable/missing rather than
   fabricated values.
6. Incomplete quote fields degrade safely.
7. Stale or unavailable responses cannot become actionable.
8. Injected client failure becomes a sanitized failure/unavailable outcome.
9. Snapshot references preserve aggregate report compatibility and granular
   input freshness scope.
10. Tests prove no runtime network client, route, frontend surface, agent
    ingestion, or raw payload exposure was introduced.

## Review Gate

After Codex C completes `P22A-T4`:

1. Codex B reviews provider-neutral mapping, typed limitation provenance,
   actionability/freshness separation, privacy, and no-runtime-network
   boundary.
2. No frontend consumption or actual Alpaca API call may begin from that
   review.
3. Any future external smoke test requires a separate Codex A decision and a
   new scoped task.

