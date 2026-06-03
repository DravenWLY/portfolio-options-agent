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

Phase 20D - Dashboard Information Architecture And Contract Readiness.

- Codex A completed `P20D-T0` on 2026-05-26 as a docs-only planning task in `docs/codex-a-product/DASHBOARD_CONTENT_DECISION.md`.
- The approved Dashboard direction is a compact review-readiness cockpit: prioritize the start-review action, broker/market freshness limitations, and later approved private summary/history surfaces rather than expanding synthetic activity cards.
- Codex A approved private authenticated account-detail display in principle on 2026-05-26. Codex B defined the backend display-label boundary in `docs/codex-b-architecture/PHASE_20D_DASHBOARD_ACCOUNT_DETAIL_CONTRACT.md`.
- `P20D-T1`, `P20D-T2`, and `P20D-T3` are complete and reviewed: the backend account-summary contract is refined, the Dashboard cockpit is cleaned up from reviewed contracts, and the first visual/content polish pass is accepted.
- The next Dashboard design step may use Claude Design only as a constrained visual exploration tool: it may propose hierarchy and future panels, but every panel must be classified as available now, future backend contract needed, or out of scope before Claude A implements it.
- First-viewport principles are review readiness, broker/portfolio context freshness, market-data availability/data mode, and a clear start-new-review action.
- 2026-05-29 Stock Rover persona pressure test: Portfolio Copilot should be
  positioned as a complement to serious research/portfolio tools, not a
  replacement. Dashboard priorities are real-source account summary plus
  broker freshness, visible market-data limitations, a promoted plain-English
  readiness verdict, high-level risk/red-folder context, and a clear start
  review action. Do not copy research-terminal, screener, watchlist,
  holdings-grid, fair-value, or market-terminal patterns.
- Synthetic plausible headline values should not appear as if they are real;
  hide synthetic amounts by default or use unmistakable placeholders. Agent
  provider status belongs off the Dashboard first viewport.
- `P20D-T5` is complete and reviewed: the Dashboard now promotes the
  backend-owned readiness verdict, moves agent-provider status off the first
  viewport, hides plausible synthetic headline account values, and removes
  dead quick-review presets.
- Do not turn this planning task into frontend changes, backend endpoints, a market terminal, a watchlist, a brokerage-account mirror, an AI recommendation feed, or an options screener.

Paused design reference - Phase 21A Realtime Agent Console backend contract.

- Codex B drafted a mock-first realtime console option and proposed ADR 0007; both are preserved as reference material.
- PM paused further agentic/realtime architecture and implementation on 2026-05-25 while the founder studies agentic AI concepts and decides which patterns belong in the product.
- Do not begin Phase 21A backend work, live-agent work, debate/routing/memory work, SSE follow-up work, or agent-thread persistence work unless Codex A explicitly reactivates a scoped slice.
- Ownership update (2026-06-01): if an agentic AI workflow slice is reactivated, Claude E owns design/coding and Codex B reviews the result. Codex C should not implement the agentic AI system workflow unless Codex A later changes ownership explicitly.
- The existing Agent Console composer remains disabled and must not imply an active interactive-agent roadmap commitment.

Phase 25A - Agentic Workflow Foundation.

- Claude E owns approved agentic workflow design/coding slices; Codex B reviews.
- ADR 0008 is accepted: app-owned safety spine, custom runner first, LangGraph /
  SSE / MCP / parallelism deferred and gated, OpenAI Agents SDK rejected, memory
  disabled, role rename separate.
- P25A backend foundation slices have begun behind review gates: run state /
  mock runner, eval harness, tool-governance schema, live-provider smoke paths,
  OpenAI provider adapter, and backend-owned Agent Console display labels.
- ADR 0009 is accepted for machine role key vs user-facing display-label
  separation. User-facing labels are Fundamentals Analyst, News Analyst,
  Technical Analyst, Risk Manager, and Portfolio Manager. Backend role keys stay
  unchanged.
- Agent Console composer remains disabled; no unapproved route change,
  persistence, raw private-data prompting, TradingAgents execution, advice, or
  execution behavior is authorized.

Phase 22A - Provider-Neutral Market Data Evaluation Foundation.

- Codex A approved Phase 22A on 2026-05-25 as a backend-only evaluation phase while Phase 21A stays paused; `P22A-T1` synthetic/replay contracts are complete.
- `P22A-T4` is complete after Codex B PASS re-review on 2026-05-26: the Alpaca Basic local/internal mapping adapter is exercised only through injected fake clients and synthetic responses.
- Tradier is no longer the assumed scalable production provider; it remains a possible prototype/reference candidate only.
- No production market-data provider is selected. The commercial vendor/RFI track is parked until commercial-scale or external-display planning reopens it.
- `P22A-T4` represents Alpaca evaluation results as indicative, preserves `limited_source` coverage/provenance, remains analysis-only unless existing policy blocks more strictly, and authorizes no external provider call or frontend/agent consumption.
- No credentials, actual API smoke test, frontend live-price surface, streaming, agent ingestion, or TradingAgents work is authorized.
- Market-data work remains split into an approved local/internal evaluation
  path (`P22A-T4`) and a parked commercial provider/RFI path that may reopen
  only for later scale or external-display planning.

Phase 23A - Symbol Lookup / Instrument Reference Foundation.

- Current backend/frontend utility priority after Dashboard visual checkpoint.
- `P23A-T1` through `P23A-T4` proved provider-neutral symbol search,
  validation, recent/default lists, exact-first contains search, and Trade
  Review autocomplete consumption against synthetic fixtures.
- `P23A-T5` is complete: backend parser/importer/cache/refresh foundations can
  normalize Nasdaq-style symbol directory files into provider-neutral records
  while preserving synthetic fallback and offline tests.
- The product goal is Trade Review input autocomplete and a clear
  `Symbol Not Found` state, not quotes, recommendations, watchlists,
  screeners, or broker tradability.
- Frontend contracts remain provider-neutral and unchanged by the refresh
  foundation.

Phase 23B - Complete Symbol Lookup Personal Demo.

- Next scope is the end-to-end personal-demo completion phase for symbol
  lookup.
- Codex C should first add persistent last-good normalized symbol snapshots
  (`P23B-T1`) and opt-in local refresh wiring (`P23B-T2`). Default startup and
  default tests must still make no network calls.
- Claude A may then finish frontend autocomplete polish (`P23B-T3`): uppercase
  symbol/underlying input as the user types, preserve backend-owned ordering
  and messages, and keep recent/default list behavior.
- This phase still excludes quotes, prices, volumes, options chains,
  watchlists, screeners, recommendations, broker tradability, direct frontend
  provider calls, and commercial/public data-use claims.

Phase 24B - FRED Economic Awareness.

- FMP was not usable as the free personal-demo economic-calendar source.
- FRED is the current backend-owned official macro foundation; `is_trading_signal=false`
  and source/freshness/attribution stay visible.
- Dashboard economic awareness remains macro context only, not ticker/company
  news, not a market terminal, not a trading signal, and not an agent/news-tool
  input by default.
- Per-underlying earnings date remains a separate narrow future review-context
  candidate for options flows.

Phase 26A - Market Context: Market Mood.

- P26A-T1 backend contract is reviewed PASS. Contract reference:
  `docs/codex-b-architecture/PHASE_26A_MARKET_MOOD_CONTRACT.md`.
- Claude A may start P26A-T2 Dashboard compact card using
  `GET /market-context/market-mood`.
- Dashboard card shows only overall Fear & Greed score/rating as secondary
  Market Context. Full 7-component detail belongs on the later Market Mood page.
- Source is CNN-derived/internal-demo only pending source-rights review. No CNN
  branding, no `live`/`real_time` claims, no actionability/risk-rule/LLM-agent
  use, and no advice/recommendation/market-timing wording.

## Next Phases

Phase 20B / 20C delivery sequence.

- Codex C owns one backend read-contract slice at a time.
- Codex B reviews schema safety, endpoint placement, forbidden-field coverage, actionability/freshness semantics, and whether Claude A may consume the contract.
- Claude A wires completed endpoints into the Modern Portfolio Desk only after Codex B review, keeping demo labels visible for synthetic/demo data.
- Claude B reviews frontend safety, UX clarity, no execution affordances, and no private-data leakage after wiring.
- Phase 20C is complete; new Dashboard work begins with a content-definition gate rather than opportunistic new cards or endpoints.

Phase 20D, docs-only planning.

- `P20D-T0` is complete in `docs/codex-a-product/DASHBOARD_CONTENT_DECISION.md`; it authorizes no implementation.
- `P20D-T1` through `P20D-T3` are complete and reviewed. The next Dashboard step is a constrained Claude Design concept pass or follow-up implementation task based only on reviewed contracts; unsupported content must be marked as future-contract-needed or out of scope before implementation.
- Founder decisions are still needed before persisted review-history work, real market-data display, news/economic-calendar content, or profile-backed personalization. Claude A may later refine visual hierarchy only from approved contracts.
- After the Stock Rover pressure test, the first data-readiness sequence is:
  real-source account summary plus broker freshness before persisted review
  history; display-rights-cleared REST quote snapshots before external beta
  quote-current claims; per-underlying earnings date as a narrow options
  review-context follow-up.

Phase 21A, paused.

- No current Claude E or Claude A implementation assignment exists for Phase 21A.
- If PM later reactivates a slice, the retained contract/ADR must first be reviewed against founder learning and any updated product direction. Claude E, not Codex C, is the implementation owner for approved agentic workflow slices.

Phase 22A, evaluation checkpoint.

- `P22A-T1` provider-neutral synthetic/replay contract work is complete.
- `P22A-T3` identified Alpaca Basic as the recommended first local/internal
  evaluation candidate. `P22A-T4` is complete and reviewed as backend-only,
  injected/mock-client mapping labelled `limited_source`/`indicative` and
  `analysis_only`.
- Actual Alpaca network or credential testing, frontend display, or agent
  market-evidence consumption requires a separate future PM decision.
- Tradier Sandbox remains a secondary delayed-data candidate without sandbox
  Greeks; Intrinio delayed remains conditional on written trial terms.
- Stage 2 RFI materials for Intrinio, Databento, dxFeed, and Massive are
  retained as parked commercial-scale references; no outreach or selection is
  active.

Phase 23A / 23B / 24A, next backend-first user-facing utility slices.

- Phase 23A/23B symbol lookup is complete through browser-local recents and
  offline fixture cleanup.
- `P24A-T1` should define and implement economic calendar contracts with
  synthetic fixtures; `P24A-T2` adds deterministic importance classification;
  `P24A-T3` adds the opt-in FMP REST adapter; `P24A-T4` adds last-good refresh;
  `P24A-T5` adds the Dashboard table.
- Phase 24A must keep ticker/company news, agents, WebSockets, Forex Factory
  scraping, Trading Economics, and commercial provider positioning out of
  scope unless Codex A opens a separate task.

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
