# MVP Scope

Status: PM scope decision
Owner: Codex A - Product / Founder Strategy / PM
Last updated: 2026-05-20

## MVP Definition

The MVP is a read-only pre-trade review workflow for self-directed investors who manually place trades outside the app. It proves that Portfolio Copilot can turn a portfolio snapshot plus a proposed stock/ETF/options trade into a deterministic, freshness-aware, educational review that helps the user understand portfolio impact before acting elsewhere.

The broader product framing is a TradingAgents-inspired, portfolio-aware trade review agent team. For MVP, this means safe deterministic agent components and an app-owned agent-team orchestration contract, not autonomous trading, not one-shot stock research, and not a thin TradingAgents wrapper.

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
| Output | Deterministic review report with optional AI explanation of structured facts. |
| Storage | Durable report/review history for synthetic/local development and later beta. |
| UI posture | Operational cockpit and review workspace, not a marketing page or trading terminal. |

## Out Of Scope

- Automatic trading or broker order execution.
- Broker order placement, cancellation, modification, or order-ticket UI.
- Broker disconnect/delete flows in first MVP UX.
- Broker scraping, Fidelity credential storage, or MFA bypass.
- Direct Fidelity login/API assumptions.
- Market-data terminal, option-chain browser, or real-time streaming surface.
- Options-income screener, wheel app, CSP screener, covered-call screener, or AI stock picker.
- Advanced option strategies: spreads, collars, rolls, diagonals, iron condors, multi-leg optimization.
- TradingAgents in the fast review path.
- Raw broker holdings/account values/cash/ids sent to LLMs or TradingAgents by default.
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

### Gate 4 - Frontend Trade Review Workspace

Required before a beta-style product demo.

The frontend must show:

- Trade intent input.
- Deterministic results.
- Broker freshness and market quote freshness separately.
- Analysis-only or blocked states.
- Report history.
- Clear read-only/manual-decision language.

Phase 18 may use deterministic review plus Phase 16A/16B outputs for the first workspace. Rich public research/debate UI should wait for Phase 17 evidence contracts.

### Gate 5 - Real Market Data For Paid Beta

Real market-data provider integration is not required before a local MVP demo. It is required before external paid beta or any polished UI/report that implies quote-current options review.

The preferred first real provider candidate is Tradier for backend-only REST snapshots: quotes, option expirations, option chains, and Greeks/IV where available. WebSocket/streaming real-time data is deferred to Phase 19+ or paid beta only if users prove the need.

## First Beta Scope

The first local beta/demo can be useful with manual/CSV snapshots and synthetic/manual market data if the product labels outputs as analysis-only where appropriate. A paid beta should aim for read-only broker sync plus a clear refresh/confirm path and real REST snapshot market data for quote-current options review. Broad provider coverage and streaming are not required before validating the core pre-trade review job.

## Scope Admission Rule

A feature belongs in MVP only if it directly improves the user's ability to understand a proposed manual trade's portfolio impact, cash/collateral impact, assignment/call-away exposure, concentration risk, risk-rule violations, or data freshness.

Features that mainly improve discovery, screening, research breadth, automation, execution, or dashboard polish should wait unless they unblock the core review workflow.

## Open Questions

These do not block the current MVP direction:

- Whether the first external beta requires broker sync or can start with manual/CSV snapshots.
- Final market-data provider purchase/licensing decision after rechecking current Tradier pricing, OPRA/data rights, and API capabilities.
- How much AI explanation is acceptable before security/compliance review.
- Exact pricing and packaging.
- Whether advisors become a later segment.

## Current PM Decision

Phase 16A deterministic components and Phase 16B portfolio-aware agent-team orchestration are complete. The next implementation gate is Phase 17 TradingAgents/Public Research Evidence Adapter, which must remain optional public ticker/company evidence and not become the portfolio-aware decision engine.
