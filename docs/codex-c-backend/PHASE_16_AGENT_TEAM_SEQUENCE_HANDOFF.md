# Codex C Handoff: Phase 16A / 16B / 17 / 18 Sequence

Status: archived architecture handoff - Phase 16 complete
Owner: Codex B - Architecture / Tech Lead
Next owner: Codex C - Backend Implementation
Last updated: 2026-05-20

## Purpose

Clarify the PM-approved sequence after the Phase 16 architecture realignment. Phase 16A and Phase 16B are now complete; this handoff is retained as historical context.

## Product Framing

Portfolio Copilot is a TradingAgents-inspired, portfolio-aware trade review agent team for manual investors. It is TradingAgents-inspired, not TradingAgents-centered. The product center remains broker-aware `TradeIntent` review with deterministic portfolio/risk calculations and strict privacy/actionability boundaries.

## Sequence

### Phase 16A - Deterministic Agent Components

Current P16-T0 through P16-T4 belong here:

- Portfolio Snapshot Actionability Policy.
- Portfolio Context Agent.
- Trade Review Agent.
- Freshness / Guardrail Agent.
- Report Composer Agent.

Outcome: PASS. Phase 16A shipped as deterministic-first safety foundations with tests, forbidden-field boundaries, actionability handling, deterministic-vs-AI separation, and no advice/execution language.

### Phase 16B - Portfolio-Aware Agent Team Orchestrator

Outcome: PASS. Phase 16B implemented the app-owned orchestrator/stage graph, role/context-envelope policy, actionability enforcement, run/step mapping, and unavailable-state fallbacks.

16B must include:

- orchestrator/workflow contract;
- stage order;
- role registry or equivalent role/stage vocabulary;
- actionability gate enforcement;
- agent run and step persistence expectations;
- deterministic vs LLM boundaries;
- private-data and public-evidence context envelopes;
- fallback behavior when research, real market providers, TradingAgents, or LLMs are unavailable.

Recommended stage order:

1. Validate `TradeIntent`.
2. Build approved portfolio context projection.
3. Resolve market snapshot.
4. Run deterministic trade/risk review.
5. Evaluate Portfolio Snapshot Actionability Policy.
6. Optionally retrieve public research evidence.
7. Optionally run bull/bear/risk interpretation over sanitized/public evidence.
8. Run freshness/guardrail review.
9. Compose final educational report.
10. Persist report, run, and step outputs.

### Phase 17 - TradingAgents/Public Research Evidence Adapter

TradingAgents and any other public research adapters are optional async public ticker/company research evidence. They are not the portfolio-aware decision engine and must not receive raw/private brokerage context by default.

### Phase 18 - Frontend Trade Review Workspace

First workspace may use deterministic review plus Phase 16A/16B outputs. Rich public research/debate UI waits for Phase 17 contracts.

Phase 18 depends on:

- Phase 16 complete;
- typed sanitized trade-review read schema and forbidden-field tests;
- coverage/collateral caveat or modelling fix;
- real market data only before external paid beta or polished quote-current options review, not before local MVP demo.

## Market Data Timing

Do not implement a real market-data provider during Phase 16A/16B.

Manual/mock market data is acceptable for local MVP demo with clear analysis-only labeling where appropriate.

Tradier is the preferred first real provider candidate for backend-only REST snapshots before external paid beta:

- quotes;
- option expirations;
- option chains;
- Greeks/IV where available.

Before purchase/public beta, recheck current pricing, licensing, OPRA/data rights, plan requirements, data freshness, Greeks/IV behavior, redistribution limits, and API capabilities.

WebSocket/streaming real-time market data is deferred to Phase 19+ or paid beta only if users prove the need. Do not build an option-chain browser, screener, or market-data terminal for MVP.

## Safety Boundaries

Do not expose or send to LLMs, TradingAgents, public evidence roles, analytics, docs, tests, logs, or frontend schemas by default:

- raw holdings;
- account values;
- cash balances or buying power;
- broker account ids or provider account ids;
- provider connection ids;
- raw provider payloads;
- secrets, portal URLs, API keys, or access tokens;
- trade journal entries;
- account-specific thresholds or private strategy settings.

No automatic trading, broker order placement/cancellation, broker scraping, Fidelity credential storage, MFA bypass, guaranteed-return wording, or "you should buy/sell" language.

## Codex C Recommendation

PASS Phase 16 as complete.

BLOCK Phase 17/18 work that assumes TradingAgents/Public Research Evidence is the portfolio-aware decision engine or that real streaming market data is required for local MVP.
