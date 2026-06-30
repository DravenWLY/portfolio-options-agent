# MVP Scope

Status: PM scope decision
Owner: Codex A - Product / Founder Strategy / PM
Last updated: 2026-06-23

## MVP Definition

The current internal validation prototype is a read-only specialist review desk
for busy self-directed investors who manually place trades outside the app. It
proves that Portfolio Copilot can turn a portfolio snapshot plus a proposed
stock/ETF/options trade into a deterministic evidence snapshot and explicit
Agent Team briefing that helps the user answer: "What would I be ignoring if I
acted manually now?"

The broader product framing is a TradingAgents-inspired, portfolio-aware
specialist review team. For MVP validation, this means safe deterministic
review components, immutable saved evidence packages, and an app-owned
agent-team briefing contract, not autonomous trading, not one-shot stock
research, and not a thin TradingAgents wrapper.

The MVP validation loop is not a migration target for research terminals or portfolio
analytics products. It should complement tools such as Stock Rover by covering
the short, high-stakes moment before a user manually places a trade: what the
trade could do, what context or data may be missing, and what the user should
verify before acting elsewhere.

The MVP agent experience is a five-persona specialist review team. The team
helps the user manage their own portfolio decisions with evidence and
freshness-aware analysis; it does not manage the portfolio for the user,
recommend trades, allocate assets, or place orders.

## In Scope

| Area | MVP scope |
| --- | --- |
| User | Active self-directed retail investor with stocks, ETFs, and simple options. |
| Portfolio data | Read-only SnapTrade sync where available; manual entry and CSV fallback remain supported. |
| Portfolio entities | Cash balances, stock/ETF positions, option positions, account snapshot freshness. |
| Trade intent | User-entered hypothetical manual trade intent, not an executable order. |
| Equity review | Stock/ETF buy, sell, add, or trim review as one generic flow. |
| Options review | Single-leg covered call and single-leg cash-secured put review. |
| Calculations | Cash impact, collateral, free cash, assignment exposure, call-away exposure, allocation/concentration impact, deterministic risk-rule violations. |
| Freshness | Separate broker snapshot freshness and market quote freshness. |
| Output | Saved evidence snapshot plus explicit Agent Team briefing, with deterministic facts as the supporting evidence layer. |
| Storage | Durable report/review history for synthetic/local development and later beta. |
| UI posture | Operational cockpit and review workspace, not a marketing page or trading terminal. |
| Agent personas | Fundamentals Analyst, News Analyst, Technical Analyst, Risk Manager, Portfolio Manager. Clean UI labels only; backend keys may stay unchanged. |

## Out Of Scope

- Automatic trading or broker order execution.
- Broker order placement, cancellation, modification, or order-ticket UI.
- Broker disconnect/delete flows in first MVP UX.
- Broker scraping, Fidelity credential storage, or MFA bypass.
- Direct Fidelity login/API assumptions.
- Market-data terminal, option-chain browser, or real-time streaming surface.
- Research terminal, screener, watchlist, holdings-grid Dashboard, fair-value
  rating surface, or Stock Rover replacement.
- Options-income screener, wheel app, CSP screener, covered-call screener, or AI stock picker.
- Advanced option strategies: spreads, collars, rolls, diagonals, iron condors, multi-leg optimization.
- TradingAgents in the fast review path.
- Raw broker holdings/account values/cash/ids sent to LLMs or TradingAgents by default.
- User-facing Trader persona, debate personas, conviction personas, AI
  portfolio manager framing, or any persona that produces allocation/trade
  recommendations.
- Public SaaS auth, payment, mobile app, PDF export, OPRA redistribution, production deployment, or formal compliance launch.

## MVP Trade Flows

### P0 Product Surface

1. Stock/ETF buy review.
2. Stock/ETF sell or trim review.
3. Covered call review.
4. Cash-secured put review.

### Deferred From First Product Surface

- Long call and long put review.
- ETF-specific optimizer or research flow.
- Multi-leg strategies.
- Wheel lifecycle tracking.
- Option screener or chain browser.
- TradingAgents research evidence UI.
- Additional personas beyond the approved five. The top P1 candidate is an
  Options Strategist / Options Risk Specialist, likely starting as a bounded
  extension of Risk Manager. Bull/Bear, aggressive/balanced/conservative, and
  similar debate concepts may become non-conviction report sections later, not
  separate MVP personas.

Long call and long put support may remain as backend capability, but they should not drive the first PM/UX slice.

## MVP Gates

### Gate 1 - Product Scope Docs

Complete when PRD, MVP scope, feature priority, and metrics are documented and accepted.

### Gate 2 - Portfolio Snapshot Actionability Policy

Required before polished Phase 16 agent outputs.

The policy must classify whether a review is:

- Fresh enough for normal review language.
- Analysis-only.
- Manual confirmation required.
- Blocked due to stale, unknown, or error state.

The policy must combine broker snapshot freshness and market quote freshness without collapsing them into one field.

### Gate 3 - Agent Output Safety

Required before user-facing AI explanations.

Agents must consume only approved agent-safe projections and actionability decisions. They must not receive raw holdings, account values, cash balances, broker account ids, trade journal entries, account-specific thresholds, provider raw payloads, or secrets by default.

Phase 16 is split:

- Phase 16A: deterministic agent components such as Portfolio Context, Trade Review, Freshness/Guardrail, and Report Composer.
- Phase 16B: portfolio-aware agent-team orchestrator that defines stage order, run/step persistence, actionability enforcement, private/public context boundaries, and fallback behavior when research or LLMs are unavailable.

### Gate 4 - Frontend Trade Review Workspace And Saved Briefing

Required before a beta-style product demo.

The frontend must show:

- Trade intent input.
- Deterministic results.
- Broker freshness and market quote freshness separately.
- Analysis-only or blocked states.
- Saved evidence snapshot and explicit Agent Team briefing generation.
- Report history/readback from frozen saved evidence.
- Clear read-only/manual-decision language.

Phase 18 may use deterministic review plus Phase 16A/16B outputs for the first workspace. Rich public research/debate UI should wait for Phase 17 evidence contracts.

### Gate 5 - Real Market Data For External Beta

Real market-data provider integration is not required before a local MVP demo. It is required before external paid beta or any polished UI/report that implies quote-current options review.

The external beta ceiling-lifter is a display-rights-cleared backend REST
snapshot path for the underlying and the specific option being reviewed,
including source/freshness/provenance. Indicative/manual pricing can support
local/internal analysis-only demos, but it should not be presented as current
official market data. WebSocket/streaming real-time data remains deferred
unless users later prove the need and licensing is approved.

## First Beta Scope

The first internal validation demo is useful with synthetic/manual snapshots
and mocked or replayed evidence because it proves the golden path without real
brokerage data. A later local beta can be useful with manual/CSV snapshots and
synthetic/manual market data if the product labels outputs as analysis-only
where appropriate. A paid or external beta should aim for read-only broker sync
plus a clear refresh/confirm path and a display-rights-cleared REST snapshot
market-data source for quote-current options review. Broad provider coverage
and streaming are not required before validating the core review-desk job.

## Scope Admission Rule

A feature belongs in MVP only if it directly improves the user's ability to
understand what they might be ignoring before a proposed manual trade:
portfolio impact, cash/collateral impact, assignment/call-away exposure,
concentration risk, risk-rule violations, evidence limitations, or data
freshness.

Features that mainly improve discovery, screening, research breadth, automation, execution, or dashboard polish should wait unless they unblock the core review workflow.

## Open Questions

These do not block the current MVP direction:

- Whether the first external beta requires broker sync or can start with manual/CSV snapshots.
- Final market-data provider purchase/licensing decision after rechecking current Tradier pricing, OPRA/data rights, and API capabilities.
- How much AI explanation is acceptable before security/compliance review.
- Exact pricing and packaging.
- Whether advisors become a later segment.
- Whether the first external beta must include per-underlying earnings date
  for covered call/CSP review, or whether that remains a fast-follow review
  context.

## Current PM Decision

Phase 16A deterministic components and Phase 16B portfolio-aware agent-team orchestration are complete. Deep Phase 17 TradingAgents/Public Research Evidence Adapter implementation is temporarily frozen so the next active delivery focus can shift to Phase 18A: the first visible Trade Review Workspace.

Phase 18A should use completed Phase 16 outputs and deterministic trade-review results through a sanitized frontend read contract. It should not wait for TradingAgents research/debate evidence or real market-data provider integration.
