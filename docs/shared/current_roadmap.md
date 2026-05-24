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
- Phase 17A: public research evidence adapter boundary, including optional TradingAgents dependency detection, public ticker/company evidence contracts, cache/budget policy, mocked parser/report mapping, and adapter-boundary review.
- Phase 18A: first visible Trade Review Workspace readiness, including the sanitized backend read contract, synthetic preview endpoint, first read-only frontend workspace, and integration review.
- Phase 18B: frontend Trade Review Workspace expansion over the T0-T2 + T4 scope, including frontend-read privacy guard unification, deterministic report UI, and Codex integration review. P18B-T3 research-evidence display remains deferred pending reviewed Phase 17 backend evidence contracts.
- Phase 18C: real portfolio-backed Trade Review Workspace, including a distinct portfolio-backed preview endpoint, safe portfolio context summary, frontend integration, and final architecture signoff.
- Phase 19A: basic portfolio-aware LLM agent team plus analysis console, using an app-owned mock-provider agent workflow and role-by-role frontend console.
- Phase 19B: real LLM provider gate, including backend-owned provider config/factory, Google/Gemini candidate adapter behind explicit opt-in, prompt/output safety hardening, and safe partial-output fallback. Mock remains default.
- Phase 19C: agent-team evidence and prompt foundation, including agent-safe deterministic evidence projection, role-specific prompt inputs, scenario coverage, and privacy-preserving prompt boundaries.
- Phase 20A: Modern Portfolio Desk frontend integration, including prototype-fidelity shell/topbar/sidebar, workspace placeholder screens, marketing placeholders, and self-hosted font assets.

Detailed verification history lives in `docs/shared/completed_phases_log.md`.

## Active Phases

Phase 20B - Modern Portfolio Desk backend contracts.

- Phase 20A prototype-fidelity frontend work is complete; keep its visual direction stable while wiring placeholder surfaces through reviewed backend contracts.
- Active backend focus: sanitized read contracts for Dashboard, Portfolio Context, Reports, and safe profile/display surfaces.
- P20B-T1/T1A/T2/T3 are complete as demo-labeled frontend-readiness contracts for recent trade reviews, risk alerts, and readiness.
- Next backend task: P20B-T4 portfolio context enumeration and detail contracts.
- Claude A may consume completed P20B endpoints only with visible `demo · not yet connected` labeling until data_mode becomes persisted/real.
- Preserve safety boundaries: no execution UI, no invented backend fields, no frontend financial computation, no raw private data exposure, and no new storage keys beyond approved UI preferences.

## Next Phases

Phase 20B delivery sequence.

- Codex C owns one backend read-contract slice at a time.
- Codex B reviews schema safety, endpoint placement, forbidden-field coverage, actionability/freshness semantics, and whether Claude A may consume the contract.
- Claude A wires completed endpoints into the Modern Portfolio Desk only after Codex B review, keeping demo labels visible for synthetic/demo data.
- Claude B reviews frontend safety, UX clarity, no execution affordances, and no private-data leakage after wiring.

Phase 19D / live LLM smoke gate, future only.

- Real Google/Gemini calls remain disabled by default.
- A future backend-only smoke gate may exercise synthetic prompts against a live provider after explicit human approval, budget/rate-limit checks, and privacy review.
- Frontend API keys, frontend provider selection, deep TradingAgents execution, real news/macro providers, and debate loops remain out of scope until separately approved.

Phase 19+ / 20+ - UI Refinement, Streaming Market Data, TradingAgents Evidence UI, and broader workflow polish.

- Refine the analysis console and Trade Review Workspace after the current Modern Portfolio Desk integration is reviewed and backend agent/provider gates remain safe.
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
