# ADR 0003: Market-Data Timing and Tradier-First REST Snapshots

Status: accepted
Date: 2026-05-20
Owner: Codex B - Architecture / Tech Lead

## Context

Portfolio Copilot needs market quotes, option quotes, chains, IV, Greeks, quote timestamps, data mode, and provider status to review proposed trades. Broker portfolio freshness and market quote freshness are separate.

Phase 12 intentionally created provider-agnostic market-data contracts and a manual/mock provider only. Real provider calls were deferred so the product could stabilize trade-review, actionability, report, and agent boundaries before taking on provider cost, licensing, OPRA, and quote-freshness complexity.

## Decision

Do not implement a real market-data provider during Phase 16A or Phase 16B.

Real market-data provider integration is **not required for local MVP demo**. Manual/mock market data remains acceptable for local MVP as long as outputs are labeled analysis-only when appropriate.

Real backend REST snapshot market data is required before:

- external paid beta;
- any polished UI/report that implies quote-current options review;
- any public-facing claim that options quotes, Greeks, or IV are provider-current.

Preferred first real provider candidate: **Tradier Market Data API**, backend-only, REST snapshots first:

- quotes;
- option expirations;
- option chains;
- Greeks/IV where available.

Before purchase or public beta, re-verify current pricing, licensing, OPRA/data rights, plan requirements, data freshness, Greeks/IV behavior, redistribution limits, and API capabilities from official provider documentation.

WebSocket/streaming real-time market data is explicitly deferred to Phase 19+ or paid beta, and only if active users prove the need.

## Non-Goals

- No option-chain browser for MVP.
- No market-data terminal.
- No options screener.
- No streaming entire option markets.
- No frontend calls directly to market-data providers.
- No storing provider secrets in frontend code, reports, logs, tests, or public docs.

## Implementation Guidance

When the provider slice is approved:

- Keep provider calls backend-only.
- Add a provider adapter behind existing `MarketDataProvider` and `OptionDataProvider` contracts.
- Preserve `freshness_scope="market_quote"` separately from broker snapshot freshness.
- Persist or freeze enough quote/chain payload data for report reproducibility.
- Mark `data_mode` and quote freshness explicitly. Never silently downgrade live to delayed.
- Mock all provider tests by default. Any real-provider tests must be marked external and skipped by default.
- Return sanitized API shapes without raw provider payloads, provider account ids, secrets, or account-specific thresholds.

## Consequences

Positive:

- Keeps the local MVP from turning into a market-data integration project.
- Gives paid beta a clear path to quote-current options review.
- Avoids premature WebSocket, OPRA, or terminal-style UI complexity.
- Aligns with the product center: pre-trade portfolio review, not market-data viewing.

Tradeoffs:

- Local MVP demos cannot honestly claim real quote-current options review.
- Paid beta readiness will need a provider/licensing check before launch.
- Tradier remains a candidate, not a permanent provider lock-in.

## Alternatives Considered

1. Implement real-time streaming now. Rejected because the MVP does not need a terminal and streaming creates cost, licensing, UI, and reliability complexity.
2. Use broker provider data as market data. Rejected because broker account sync and market quotes are separate subsystems.
3. Use free/unofficial data as product-grade options data. Rejected for reliability/licensing/freshness reasons.

## Review Guidance

Architecture reviews should block changes that:

- call manual/mock data live or quote-current;
- add provider calls from frontend code;
- collapse broker freshness and market quote freshness;
- add option-chain browser, screener, market terminal, or streaming UI before PM approval;
- expose provider secrets, raw payloads, private account data, or account-specific thresholds.
