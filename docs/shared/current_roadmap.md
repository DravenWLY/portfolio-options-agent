# Current Roadmap

This is the short context file for routine Codex and Claude reviews. Prefer this file over the full architecture document when the task only needs current direction.

## Product North Star

`portfolio-options-agent` is a TradingAgents-inspired, portfolio-aware trade review agent team for manual investors. It combines broker portfolio state, market context, proposed stock/ETF/option trade intents, deterministic trade-review and risk calculations, strategy-extensible evaluators, app-owned portfolio-aware agents, optional TradingAgents/public stock-company research evidence, and durable report history.

TradingAgents-inspired does not mean TradingAgents-centered. The product center remains broker-aware `TradeIntent` review. The dashboard is the cockpit, not the whole product. SnapTrade, market data providers, and TradingAgents are inputs/components, not the center. Options remain a strong wedge, but wheel/CSP/covered-call workflows are not the product boundary.

## Safety Boundary

- Manual decision support only.
- No automatic trading.
- No broker scraping.
- No Fidelity credential storage.
- No MFA bypass.
- No guaranteed-return language.
- No "you should buy/sell" advice wording.
- No real account data, API keys, broker CSVs, or private strategy thresholds in git.
- Deterministic Python services calculate financial metrics. LLMs may explain structured outputs but must not invent metrics.

## Completed Foundation

- Phase 1: database foundation.
- Phase 2: users and accounts.
- Phase 3: internal portfolio storage primitives.
- Phase 4: broker sync foundation.
- Phase 5: SnapTrade read-only adapter, mock-first.
- Phase 6: SnapTrade connection flow backend.
- Phase 7: SnapTrade portfolio normalization.
- Phase 8: portfolio dashboard backend from synced data.
- Phase 9: manual input and Fidelity CSV fallback.
- Phase 10: thin report/agent persistence foundation.
- Phase 11: React/Vite frontend dashboard shell, broker connection UI, market-data status slice, risk-review slice, collapsible sidebar, and appearance mode.
- Phase 12: strategy-neutral market data contracts, snapshots, manual provider, and thin market status UI slice.
- Phase 13: generic options metrics and portfolio risk engine plus frontend deterministic risk review slice.
- Phase 14: TradeIntent foundation for proposed stock, ETF, and options trade review.
- Phase 15: deterministic trade review engine MVP with payoff, portfolio impact, risk integration, strategy wrappers, deterministic report, and agent-safe projection.
- Phase 16: deterministic agent components plus portfolio-aware agent-team orchestrator, including actionability policy, context envelopes, run/step mapping, and privacy-safe fallbacks.
- Phase 18A: first visible Trade Review Workspace readiness, including the sanitized backend read contract, synthetic preview endpoint, first read-only frontend workspace, and integration review.

Detailed verification history lives in `docs/shared/completed_phases_log.md`.

## Active Phases

Phase 18B - Frontend Trade Review Workspace expansion.

- Expand the completed Phase 18A workspace in small vertical slices.
- Keep the workspace read-only, deterministic-first, and actionability/freshness-aware.
- Preserve the approved Phase 18A frontend read contract unless Codex B/Codex C explicitly revise the backend schema first.
- Optional research evidence display still waits for Phase 17 contracts and must remain subordinate to deterministic review.

Temporarily frozen: deep Phase 17 TradingAgents/Public Research Evidence Adapter implementation.

- Phase 17 remains optional public ticker/company evidence only.
- It must not become the main sprint, fast-path decision engine, or source of portfolio-aware conclusions.
- No holdings, account values, cash, broker ids, journal entries, or account-specific thresholds are sent by default.

## Next Phases

Phase 18B - Frontend Trade Review Workspace expansion.

- Expand the first Phase 18A workspace after the safe read contract, first UI slice, and review gates pass.
- Optional research evidence display waits for Phase 17 contracts and must remain subordinate to deterministic review.

Before expanding beyond the Phase 18A workspace:

- Keep Phase 17 frozen unless Codex A PM explicitly reactivates it.
- Resolve backend contract fast-follows before asking frontend to consume new fields.
- Coverage-aware covered-call/CSP portfolio netting may be implemented later, but until then the visible caveats must remain.
- Real market data is not required for local MVP demo, but real REST snapshot market data is required before external paid beta or any polished UI/report that implies quote-current options review.

Phase 19+ - Streaming Market Data, TradingAgents Evidence UI, and broader workflow polish.

- Add async research evidence display after backend adapter and safety boundaries are stable.
- Add WebSocket/streaming market data only if paid-beta users prove the need. Do not build an option-chain browser, screener, or market-data terminal for MVP.

Market data timing:

- Manual/mock market data remains acceptable for local MVP demo with clear analysis-only labeling where appropriate.
- Tradier is the preferred first real provider candidate for backend-only REST snapshots: quotes, option expirations, option chains, and Greeks/IV where available.
- Before purchase/public beta, recheck current Tradier pricing, licensing, OPRA/data rights, and API capabilities.

Future Broker Activities / Transactions layer.

- Read-only activity sync for historical buys, sells, dividends, deposits, withdrawals, fees, option open/close events, assignment, exercise, and expiration where the broker provider supports it.
- Store sanitized raw broker activities separately first; normalize selected events into trades, premium income records, and wheel lifecycle records later.
- Treat activity freshness separately from broker position freshness and market quote freshness. Activities may be cached/daily and must not be treated as real-time execution data.
- Keep orders separate from activities and read-only only.

## Delivery Rhythm

Each new capability should now ship as a small vertical slice:

1. Codex implements the backend contract/service with synthetic tests.
2. Claude reviews frontend implications and finance-safety language.
3. Claude implements the corresponding frontend view only after the backend contract exists.
4. Codex performs the final integration/security review.

Do not build speculative frontend fields before backend contracts exist, and do not run backend phases far ahead without a minimal reviewable UI surface.

## Review Guidance

Use `docs/claude-b-review/OPUS_REVIEW_BRIEF.md` for high-stakes Opus reviews. Use `docs/codex-c-backend/WORKING_CONTEXT.md` for implementation tasks. Load `docs/codex-b-architecture/architecture.md` only when the task needs the full design. Load `docs/shared/completed_phases_log.md` only when historical verification details are directly relevant.
