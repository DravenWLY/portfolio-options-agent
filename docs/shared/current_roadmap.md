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
- P20B-T1/T1A/T2/T3/T4/T7 are complete as demo-labeled frontend-readiness contracts for recent trade reviews, risk alerts, readiness, portfolio context, and dashboard account summary.
- P20B-T5 reports and P20B-T6 profile/display remain blocked until their persistence/auth and product contracts are approved.
- Claude A may consume completed P20B endpoints only with visible `demo · not yet connected` labeling until data_mode becomes persisted/real.
- Preserve safety boundaries: no execution UI, no invented backend fields, no frontend financial computation, no raw private data exposure, and no new storage keys beyond approved UI preferences.

Phase 20C - Modern Portfolio Desk contract wiring and layout follow-through.

- P20C-T1 through P20C-T6 are complete and reviewed: Dashboard wiring, Agent Console five-zone layout and visual refinement, sectioned Settings, Trade Review disclosure, and shared Modern Desk state/icon cleanup.
- This phase is a stable frontend integration checkpoint. Deferred cleanup on legacy Broker, Market Data, and Risk Review surfaces is not authorization for a new implementation task.
- Before expanding the Dashboard, create a product/UX content definition that separates currently backed panels from proposed market/news/account/report additions and identifies the backend contract required for each approved addition.
- Phase 21A remains paused after these frontend refinements: the Agent Console composer stays visibly disabled and makes no network or storage writes.

Paused design reference - Phase 21A Realtime Agent Console backend contract.

- Codex B drafted a mock-first realtime console option and proposed ADR 0007; both are preserved as reference material.
- PM paused further agentic/realtime architecture and implementation on 2026-05-25 while the founder studies agentic AI concepts and decides which patterns belong in the product.
- Do not begin Phase 21A backend work, live-agent work, debate/routing/memory work, SSE follow-up work, or agent-thread persistence work unless Codex A explicitly reactivates a scoped slice.
- The existing Agent Console composer remains disabled and must not imply an active interactive-agent roadmap commitment.

Phase 22A - Provider-Neutral Market Data Evaluation Foundation.

- Codex A approved Phase 22A on 2026-05-25 as the next backend-only evaluation phase while Phase 21A stays paused.
- The only initial implementation task is offline and synthetic/replay-only: provider-neutral stock/ETF and listed-options snapshot contracts, provenance/freshness semantics, and deterministic scenario tests.
- Tradier is no longer the assumed scalable production provider; it remains a possible prototype/reference candidate only.
- No production market-data provider is selected. Written RFI/licensing review is required before any commercial provider choice or live/current quote claim.
- No external provider calls, credentials, frontend live-price surface, streaming, agent ingestion, or TradingAgents work is authorized by the initial slice.
- Market-data work now has two tracks: early free/delayed evaluation first, and
  commercial-scale provider/RFI selection later. RFI outreach is deferred
  while PM decides whether to authorize a bounded local/internal evaluation
  adapter.

## Next Phases

Phase 20B / 20C delivery sequence.

- Codex C owns one backend read-contract slice at a time.
- Codex B reviews schema safety, endpoint placement, forbidden-field coverage, actionability/freshness semantics, and whether Claude A may consume the contract.
- Claude A wires completed endpoints into the Modern Portfolio Desk only after Codex B review, keeping demo labels visible for synthetic/demo data.
- Claude B reviews frontend safety, UX clarity, no execution affordances, and no private-data leakage after wiring.
- Phase 20C is complete; new Dashboard work begins with a content-definition gate rather than opportunistic new cards or endpoints.

Phase 21A, paused.

- No current Codex C or Claude A implementation assignment exists for Phase 21A.
- If PM later reactivates a slice, the retained contract/ADR must first be reviewed against founder learning and any updated product direction.

Phase 22A, current decision gate.

- `P22A-T1` provider-neutral synthetic/replay contract work is complete.
- `P22A-T3` identifies Alpaca Basic as the recommended first local/internal
  evaluation candidate, labelled `limited_source`/`indicative` and
  `analysis_only`; Codex A approval is required before any adapter task.
- Tradier Sandbox remains a secondary delayed-data candidate without sandbox
  Greeks; Intrinio delayed remains conditional on written trial terms.
- Stage 2 RFI materials for Intrinio, Databento, dxFeed, and Massive are
  retained for commercial scale, but outreach is deferred and does not select
  or integrate a provider.

Phase 19D / live LLM smoke gate, future only.

- Real Google/Gemini calls remain disabled by default.
- A future backend-only smoke gate may exercise synthetic prompts against a live provider after explicit human approval, budget/rate-limit checks, and privacy review.
- Frontend API keys, frontend provider selection, deep TradingAgents execution, real news/macro providers, and debate loops remain out of scope until separately approved.

Phase 20+ / future research - UI Refinement, Market/News Data Evaluation, Agentic AI Learning, and broader workflow polish.

- Refine approved read-only surfaces after the current Modern Portfolio Desk integration is reviewed; do not activate interactive Agent Console behavior during the Phase 21A pause.
- Add async research evidence display after backend adapter and safety boundaries are stable.
- Evaluate real market/news data and symbol discovery as separate product/backend contracts before implementation. Do not build an option-chain browser, screener, or market-data terminal for MVP.

Market data timing:

- Manual/mock market data remains acceptable for local MVP demo with clear analysis-only labeling where appropriate.
- Phase 22A now owns provider-neutral, synthetic/replay-first evaluation of stock/ETF quote and listed-options snapshot semantics.
- Tradier is no longer the assumed production foundation; it is reference/prototyping-only unless later reconsidered through the same written review process.
- Production selection requires written review of equity coverage, OPRA-derived options coverage, display/derived/retention rights, possible later sanitized agent-evidence rights, entitlements/reporting, and cost at scale.
- REST snapshots remain the first architecture posture. Streaming remains deferred until a separately approved user need and licensing decision exist.

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
