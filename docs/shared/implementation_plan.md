# Implementation Plan

This file is the active coordination index for Portfolio Copilot work. It should stay short.

Detailed historical task notes were archived on 2026-06-03:

- `docs/shared/implementation_plan_archive_2026-06-03.md`
- `docs/shared/completed_phases_log.md`
- `docs/shared/CHANGELOG.md`

Use this file for current owner routing, active phases, and the next implementation handoff. Put long verification transcripts, review checklists, and completed task detail in the archive or changelog instead of expanding this file again.

## Working Rules

- Backend contracts and deterministic services own financial calculations, display labels, actionability policy, freshness, provenance, and privacy boundaries.
- Frontend renders reviewed backend fields verbatim and may only add presentational formatting.
- No automatic trading, order placement, order cancellation, broker scraping, credential storage, MFA bypass, advice wording, guaranteed-return wording, or safe/ready-to-trade wording.
- Do not expose raw holdings, raw positions, quantities, cash balances, buying power, account values, account/provider/broker IDs, raw provider payloads, prompts, provider traces, or LLM traces in frontend or agent prompts by default.
- No `.env`, secrets, real brokerage data, local DB contents, broker exports, generated reports, screenshots, logs, or `../TradingAgents` edits during ordinary implementation/review.
- Phase 21A realtime Agent Console remains paused. The disabled Agent Console composer remains disabled.
- Market/news/agent data may enter LLM or agent paths only through separately approved sanitized evidence contracts.

## Owner Map

- Codex A: PM / product approval.
- Codex B: architecture, privacy, safety, contract review.
- Codex C: backend implementation, except the agentic AI workflow.
- Claude A: frontend implementation.
- Claude B: frontend/privacy/safety review.
- Claude E: agentic AI system design and implementation.
- Codex D: DevOps, build, deployment, CI/CD.

## Active Work

### Phase 26A - Market Mood Context

Status: active P1/internal-demo planning and implementation.

Architecture contract:

- `docs/codex-b-architecture/PHASE_26A_MARKET_MOOD_CONTRACT.md`

Purpose:

- Add broad market sentiment context using CNN-derived Fear & Greed style data.
- Dashboard shows only a compact Market Mood context card.
- A dedicated Market Context page shows the overall index plus the seven component indicators with native-scale charts and explanations.

Safety boundaries:

- Internal-demo only pending source/rights review.
- Backend fetch/cache only; no frontend-direct provider calls.
- Do not label as live or real-time.
- Do not use CNN logo, CNN branding treatment, or clone CNN visual design.
- Do not affect trade-review actionability or deterministic risk rules.
- Do not send Market Mood data to LLM/agent prompts by default.
- No advice, recommendation, buy/sell, urgency, risk-on/risk-off, execution, safe-to-trade, or ready-to-trade wording.

Tasks:

- P26A-T0 - Market Mood architecture contract: done.
- P26A-T1 - Backend contract, adapter, cache, and tests: done; Codex B review PASS.
- P26A-T2 - Dashboard Market Mood compact card: done (Claude B visual/design PASS).
  - New `frontend/src/types/marketMood.ts` (exact mirror of `market_mood.py`; verified all 24 read keys match the live payload), `frontend/src/api/marketMood.ts` (GET `/market-context/market-mood` only — no refresh, no provider call), `frontend/src/components/market-context/MarketMoodCard.tsx` (compact, self-fetching, secondary card in the Dashboard left column under account/portfolio + economic-awareness surfaces).
  - Glanceable hierarchy: header (title + compact data-mode badge) → hero (large score + uppercase rating) → 0–100 gradient spectrum ramp with a marker placed by the backend score → one quiet footer line (compact source label only; generic safety boundaries live in the product disclaimers, not per-card). Components, trend graph, and 1w/1m/1y comparisons intentionally deferred to P26A-T3. Runtime UI displays provider-reference data only and treats synthetic/unavailable as unavailable. No CNN branding, no forbidden wording, no storage writes, no external calls.
  - Same pass also cleaned up Dashboard noise: ReviewReadiness verdict reworded to plain-English headline + quiet secondary line (overall-mode chip removed), DemoChip de-duped in the visible area from 5 spots to 2 (verdict + Account summary), raw `caveat_codes` no longer rendered as user-visible badges, and the literal "demo · not yet connected" cell content removed.
  - Verified: `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, `git diff --check` all clean; live backend returns a valid `MarketMoodRead` (200) whose keys/shape match the new TS types exactly. Live visual smoke at 1024/1280/1440 (light + dark) confirmed by Claude B in an authenticated preview.
- P26A-T3 - Market Mood detail-page backend contract extension: done; Codex B review PASS.
  - Added `GET /market-context/market-mood/detail` with a provider-neutral `MarketMoodDetailRead` contract. Existing compact `GET /market-context/market-mood` and protected `POST /market-context/market-mood/refresh` remain unchanged.
  - Added detail schemas for per-indicator history points and seven `MarketMoodIndicatorRead` items, including backend-owned subtitles, descriptions, raw value labels, unit labels, axis labels, axis value format, and higher/lower value meaning. Detail graphs are not forced onto 0-100; each indicator has its own raw scale while retaining normalized score/rating labels.
  - Added synthetic history for all seven detail indicators so P26A-T4 frontend design can proceed without live provider access. Provider-reference detail preserves safe component histories only when the provider payload supplies them; missing provider-reference histories remain empty/unavailable and are not fabricated.
  - Verification: `./.venv/bin/python -m pytest tests/services/test_market_mood.py tests/api/test_market_context.py -q` passed (`16 passed`); `./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q` passed (`52 passed`). No frontend work, external API calls, LLM/agent ingestion, actionability/risk-rule integration, raw provider payload exposure, or forbidden advice/execution wording added.
- P26A-T4 - Market Mood detail-page frontend redesign: done; Claude B visual/design + frontend-safety PASS; Codex B contract/safety PASS.
  - Consumes only the reviewed detail contract `GET /market-context/market-mood/detail` → `MarketMoodDetailRead`. Frontend types extended to mirror it exactly (`MarketMoodAxisValueFormat`, `MarketMoodValueMeaning`, `MarketMoodIndicatorHistoryPointRead`, `MarketMoodIndicatorRead`, `MarketMoodDetailRead`); no invented fields. `marketMoodApi.detail()` added (the compact card still uses `marketMoodApi.get()`, unchanged).
  - Files: new `frontend/src/pages/MarketMoodPage.tsx` (rewritten to the detail contract), new `frontend/src/components/market-context/MarketMoodIndicatorChart.tsx` (interactive SVG line chart — no chart lib in the stack), `frontend/src/components/market-context/marketMoodHelpers.ts` (+`formatAxisValue`), `frontend/src/types/marketMood.ts`, `frontend/src/api/marketMood.ts`. Route `/market-context/market-mood` unchanged (added in T3); Dashboard card untouched.
  - Design (frontend-design skill, within Modern Portfolio Desk language): editorial analyst-desk layout — a confident overall band (large score + rating + 0–100 ramp + freshness + "versus prior" 1w/1m/1y aside), then all 7 indicators as cards, each with its own interactive raw-scale history chart, current value (verbatim `current_value_label`), normalized index/rating as secondary, `axis_label`, higher/lower-value meaning, and `description`. One compact source/attribution section at the end; broad disclaimers not repeated per card.
  - Charts plot RAW `history[].value` on each indicator's native scale (%, index, ratio, bps) — never forced onto the 0–100 score. Hover shows date + backend `value_label` verbatim, with rating_label + score_label/100 as secondary. Only math is autoscale + light axis formatting keyed off `axis_value_format`. States handled: loading / error+retry / unavailable / empty-history (per chart) / synthetic / provider_reference.
  - Safety: minimal CNN wording ("CNN-derived Fear & Greed Index"); no logo/branding/gauge clone; no advice/recommendation/urgency/order/execution wording; no external provider call; no storage writes; no new endpoint; no backend change; no Agent Console / Phase 21A change.
  - Verified: `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, backend Market Mood tests, and `git diff --check` all clean. Browser smoke against backend detail payload confirmed all 7 indicators render with raw-scale charts, hover tooltip shows date + value label, and the layout responds 1-up (1024) / 2-up (1280, 1440).
  - Claude B visual/design + frontend-safety review (2026-06-04): PASS. Verified: polished editorial layout (overall band → Indicator Desk rail+focused panel → Source Status), confident hierarchy with the large score/rating as the focus and a deliberate type/spacing scale; per-indicator charts plot RAW `history[].value` autoscaled to native min/max (never forced 0–100) with readable line/area/marker/clamped tooltip and a per-chart "Insufficient history" fallback (<2 points); `role="img"`+aria-labels on charts; color supplementary (meaning in labels); no CNN logo/branding/gauge clone (linear ramp + text attribution only); no advice/recommendation/urgency/order/execution/risk-on-off/buy-sell wording; typed primitives/tokens only, no emoji/ambiguous glyphs; no storage/external calls/new endpoint/backend change; Dashboard `MarketMoodCard.tsx` unchanged (absent from the diff) — no regression. Re-ran `npm run typecheck`, `npm run lint -- --max-warnings 0`, `git diff --check` clean (build per Claude A). Live authenticated browser smoke not run in this environment — responsiveness assessed statically (minWidth:0 throughout, ResizeObserver-driven SVG width, clampTooltip); rely on Claude A's recorded 1024/1280/1440 light + 1280 dark smoke.
  - Codex B alignment: detail-page source copy now uses "CNN-derived Fear & Greed Index", matching the contract posture and compact card; backend `source_rights_notice` remains rendered in Source Status.
  - Deferred polish: empty-history copy reads "Insufficient history" / "The backend did not provide enough raw values…" rather than the spec's "Not enough history to chart." — cosmetic.
  - Status: `done`.
- P26A-T5 - Market Mood real-data-only page behavior: done; Codex B review PASS.
  - Backend runtime product reads are now provider-reference-only: `GET /market-context/market-mood` and `GET /market-context/market-mood/detail` return last-good CNN-derived/provider-reference snapshots when available, otherwise `data_mode="unavailable"`. Synthetic fixtures remain injectable for tests only and are ignored by the default runtime service, including if an old synthetic snapshot is active/restored.
  - Frontend Market Mood surfaces now treat anything other than `provider_reference` as unavailable. Removed visible "Synthetic", "Demo history", and synthetic chart overlay behavior from the Dashboard card/detail page path; indicators without real provider history render the existing insufficient-history state instead of a sample chart.
  - Provider-reference detail still renders overall score/rating and any safe component histories supplied by the provider payload; it does not fabricate missing component histories. Safety invariants remain false (`is_trading_signal`, `is_actionability_input`, `is_risk_rule_input`).
  - Verification: `./.venv/bin/python -m pytest tests/services/test_market_mood.py tests/api/test_market_context.py -q` passed (`21 passed`); `npm run typecheck` passed; `npm run lint -- --max-warnings 0` passed; `npm run build` passed; `git diff --check` clean.
- P26A-T6 - Market Mood runtime refresh wiring for provider-reference snapshots: done; Codex B review PASS.
  - Goal: make the existing protected `POST /market-context/market-mood/refresh` able to fetch the CNN-derived Fear & Greed data through a backend-only injected HTTP boundary and persist a normalized provider-reference last-good snapshot, so the compact Dashboard card and detail page can display real provider-reference data after refresh.
  - Scope: backend only; no frontend-direct provider calls; no startup fetch; no scheduler; no public production claims; no synthetic product fallback. Tests must use mocked/injected HTTP responses only. A live smoke may be documented as founder-run/explicit-only, not part of default tests.
  - Acceptance: refresh success persists and activates provider-reference data; refresh failure preserves last-good and returns sanitized status; product GETs display provider-reference data or unavailable; provider component histories are preserved only when supplied; missing histories are not fabricated; no raw provider payload, URL, headers, cookies, exception body, credential, prompt, trace, broker/private data, advice, execution, or trading-signal language leaks.
  - Implementation: added `CnnFearGreedHttpClient` with injected text transport, `build_cnn_market_mood_refresh_runner(...)`, and wired protected `POST /market-context/market-mood/refresh` to the runner. The runner fetches only when the protected refresh endpoint is explicitly invoked, validates through `CnnDerivedMarketMoodProvider`, persists normalized JSON, then activates the provider-reference last-good snapshot. CNN-shaped key aliases are normalized internally; raw provider URLs/payloads/headers/cookies/provider IDs are not exposed or cached.
  - Verification: `./.venv/bin/python -m pytest tests/services/test_market_mood.py tests/api/test_market_context.py -q` passed (`27 passed`); `git diff --check` clean. One founder-approved live smoke through the backend refresh runner passed on 2026-06-04: `data_mode="provider_reference"`, 1323 trend points, 7 components, 7 indicators, and 7 indicators with provider history. Browser check of `/market-context/market-mood` showed provider-reference detail data and no visible Synthetic/Demo-history wording.
- P26A-T6A - Market Mood provider component scale calibration: done (frontend honesty layer; Claude B PASS 2026-06-04).
  - Goal: calibrate the live provider-reference component `value` / `value_label` / `axis_value_format` treatment so each detail-page chart uses honest native units. The live refresh path works, but first smoke showed at least one unit mismatch, e.g. Market Momentum appearing as a very large percent-like value.
  - Scope: keep provider-reference data only; no synthetic product fallback; no new provider source; no frontend-direct calls. Backend should own corrected unit/axis/value-label metadata where possible. Frontend should render backend labels and avoid implying an incorrect unit.
  - Acceptance: live-provider component histories remain real/provider-reference; value labels are not misleading; charts still plot native raw values; unavailable/missing histories remain insufficient-history; no actionability/risk/LLM/advice/execution scope added.
  - Implemented (frontend-only honesty layer; backend unit alignment deferred as the optional Codex C follow-up): `marketMoodHelpers.ts` `formatAxisValue({neutral})` strips %/$/unit suffixes; `indicatorScaleCalibration(ind)` flags neutral when `percent` + |v|>150 (catches Market Momentum 7553.68 → was "7553.7%") or `spread`+"bp" + |v|<10 (catches Safe Haven 3.77 → "4 bps", Junk Bond 1.46 → "1 bps"). `MarketMoodIndicatorChart` `neutralScale` neutralizes Y-axis ticks AND the tooltip raw value (bypasses the misleading backend `value_label`). `MarketMoodPage` rail chip + focused panel use the calibration consistently (both show the neutral raw value); the focused panel axis becomes "Provider raw value" with a calm italic muted caption "Native scale uncertain — provider raw value shown." Trustworthy indicators (Stock Price Strength 1.7%, Breadth, Put/Call 0.58, Volatility 16.1, 335 bps) pass the plausibility check and keep their backend `value_label` verbatim. Values are never fabricated — only the misleading unit suffix is suppressed.
  - Claude B review (2026-06-04): PASS. Calibration caption + "Provider raw value" axis read calmly (xs/mute/italic), consistent between rail chip and focused panel; thresholds catch the three implausible live cases without over-firing on plausible ones; honesty preserved; no advice/CNN-clone/forbidden wording; no regression (typecheck/lint/git-diff clean). Deferred polish: the `spread`+bp `|v|<10` rule could false-neutralize a legitimately small (3–9 bp) spread — acceptable for the observed provider payload; the real fix is the optional backend `unit_label`/`axis_value_format` alignment (Codex C). Plan-note hygiene: this task was originally framed as "backend should own corrected metadata"; the shipped fix is the frontend honesty layer with the backend alignment deferred — note retained here for traceability.
- P26A-T8/T9/T10 - Market Mood detail UX polish and one-year chart window: done; Codex B visual/contract re-review PASS.
  - Indicator charts now render only the past one year. Market Momentum computes its 125-day moving average from the full raw history, then renders only the one-year visible slice; other indicators have no moving-average overlay. Tooltips use visible raw points and show the moving-average value only when it exists for the hovered date. Endpoint scope remains `GET /market-context/market-mood/detail` only; no backend/provider/CNN call, refresh, storage write, or trading-action wording was added.
- P26A-T7 - Source/rights and production-readiness review: required before production/public display.

Next handoff:

- Optional backend polish: align provider `unit_label` / `axis_value_format` with emitted Market Mood component value scales so the frontend neutralization heuristic can be removed later.
- Optional design polish: the founder plans to revisit the Market Mood detail-page UI with Claude Design after the current data-fetching and chart behavior is stable.
- Keep P26A-T7 open for source/rights and production-readiness review before production/public display.

### Phase 25A - Agentic Workflow Foundation

Status: active, but mock-first and gated.

Accepted ADRs:

- `docs/codex-b-architecture/adr/0008-agentic-orchestration-spine.md`
- `docs/codex-b-architecture/adr/0009-agent-persona-display-labels.md`

Current posture:

- App-owned safety spine is permanent.
- Custom runner first; LangGraph deferred/gated.
- SSE-first transport remains independent of engine, but realtime Agent Console implementation remains paused.
- OpenAI Agents SDK remains rejected.
- MCP remains future-only and public/agent-safe only; private-tier MCP is prohibited.
- Memory is disabled for MVP.
- Mock remains default. Gemini/OpenAI live provider tests are explicit, opt-in, and backend-only.

Recent status:

- P25A-T7 - Provider key setup and Gemini live-smoke path: done.
- P25A-T8 - OpenAI adapter: done after review.
- P25A-T9 - Backend packaging/build migration cleanup: done after documentation cleanup.
- P25A-T10 - Persona model analysis: done.
- P25A-T11 - Backend display-label contract: done; frontend may render `display_name` verbatim when scheduled.
- P25A-T12 - Read-only Agent Console handoff polish: done; Codex B review PASS.
  - Frontend-only copy/label cleanup. Agent Console now presents itself as a read-only analysis report, not an interactive chat surface. Composer remains disabled and non-interactive; no backend, endpoint, fetch, payload, storage, provider/model selector, LLM, TradingAgents, MCP, LangGraph, or financial-computation behavior changed.
- P25A-T13 - Single-run real-provider gate: done; Codex B review PASS.
  - Hardened the opt-in Gemini/OpenAI live-smoke tests (synthetic data only) so a single controlled live run through `ReviewRunner` asserts: output passes the existing safety/eval path; run status is `completed`/`partially_completed`/`failed_safe`; no forbidden private keys/values, secret/key/URL patterns, or advice/order/execution wording; and provider failures degrade safely with no raw provider details leaked. Gemini path: `POA_LLM_LIVE_TESTS=1` + already-exported `GOOGLE_API_KEY`, cheap Flash model default, rate-limit/quota/unavailable are safe non-blocking. OpenAI path: extra `POA_LLM_OPENAI_LIVE=1` paid-ack gate; not run by default. Default suite stays offline/mock; no route/persistence/frontend/composer change. Founder-run Gemini live smoke passed (`1 passed, 1 warning in 1.77s`); the warning tracks the known `google.generativeai` deprecation and is covered by P25A-T14.

- P25A-T14 - Migrate Gemini adapter to `google-genai`: done; Codex B review PASS.
  - The Gemini adapter now lazily imports `google.genai` and uses `genai.Client(...).models.generate_content(...)`; the app-owned `LLMProvider` protocol, injected/fake-client testability, `LLMProviderResponse` shape, safe status mapping, and mock-default posture are unchanged. `pyproject.toml` `live-llm` extra and `uv.lock` updated (removed deprecated `google-generativeai`; added `google-genai` v2.8.0, which also slimmed the transitive tree). Default suite stays offline/mock with injected fakes; no route/persistence/frontend/composer change. Founder-run post-migration Gemini live smoke passed (`1 passed in 0.03s`) with no `google.generativeai` deprecation warning.
- P25A-T15 - Agent Console read-only run path on `ReviewRunner`: done; Codex B review PASS.
  - The `/agent-team/trade-review-analysis/preview` route now runs the reviewed `ReviewRunner` spine (safety/eval/timing/budget) via a new backend projection `build_console_read_from_review_run_state(AgentReviewRunState) -> AgentTeamAnalysisConsoleRead`, preserving the endpoint, response contract, and backend-owned `display_name` labels (ADR 0009). `run_status` maps `failed_safe -> failed` for the console vocabulary; provider warnings are sanitized and provider-neutral (no raw payload/URL/key/exception body); `deterministic_evidence_summary` keeps the legacy `stock_position_count` key for payload parity. Fixed the hardcoded "Mock portfolio-team synthesis" wording in `ReviewRunner._compose_final_synthesis` to provider-neutral "Portfolio-team synthesis" so it is correct on live runs. Behavior note: blocked-actionability snapshots now correctly degrade to a deterministic-only console (no LLM role commentary) instead of emitting mock commentary that ignored the gate. Mock stays default; live providers via backend env only; composer stays disabled; no new endpoint, streaming, persistence, parallel dispatch, or tool execution.
- P25A-T16 - Live LLM development runtime profile for Agent Console: done.
  - Need: the default Docker backend intentionally excludes optional live-provider SDKs, so the Agent Console route remains mock-only in ordinary Compose runs even when provider keys are present. Add a dev-only, opt-in runtime/build path that installs the `live-llm` extra and lets the existing backend env gate run Gemini/OpenAI from the read-only Agent Console route. Default Docker image must remain lean/offline/mock; no secrets in commands/docs; no frontend provider selector, streaming, composer activation, persistence, or new endpoint.
  - Implementation: added Docker build arg `INSTALL_LIVE_LLM=false` and opt-in
    `docker-compose.live-llm.yml`, which builds
    `portfolio-options-agent-backend:live-llm` with `INSTALL_LIVE_LLM=true`.
    The ordinary `backend` build path remains lean and mock-default. The live
    override still defaults `POA_LLM_MODE`/`POA_LLM_PROVIDER` to mock unless
    backend env gates are explicitly configured in private `.env` or shell
    environment.
  - Verification: `docker compose build backend` passed; default image import
    probe returned `{"google.genai": false, "openai": false}`. Opt-in build
    `docker compose -f docker-compose.yml -f docker-compose.live-llm.yml build
    backend` passed and tagged `portfolio-options-agent-backend:live-llm`; live
    image import probe returned `{"google.genai": true, "openai": true}`. No live
    provider calls were run, no keys were read or printed, touched docs/config
    contained no inline key assignments, and `git diff --check` passed.

Next possible work:

- Larger agentic work (Options Strategist persona P1, durable conversational Console, streaming/SSE, persistence, parallel dispatch, or tool execution) needs a separate product decision.

### Phase 24B - FRED Economic Awareness

Status: backend foundation available; frontend/economic-news expansion may be paused if Market Mood or agentic workflow has higher priority.

Current posture:

- FRED API key is backend-only.
- FRED refresh is opt-in and sanitized.
- Forecast remains unavailable unless a future approved source provides it.
- Exact future release times are not claimed when unknown.
- Economic awareness remains context-only and not a trading signal.

Recent status:

- P24B-T1 - FRED backend provider and official macro snapshot: done after review.
- P24B-T1A - FRED refresh resilience and partial success: done after review.
- Frontend follow-up should only proceed if the economic panel is reactivated.

### Phase 23B - Symbol Lookup

Status: functional for personal demo; future cleanup remains.

Current posture:

- Frontend autocomplete uses backend-owned normalized symbol search.
- Browser-local recent symbols are per-browser LRU only.
- Backend empty query returns no symbols.
- Global symbol directory is shared; recents are user/browser local.

Recent status:

- P23B-T1/T2 - Persistent last-good symbol directory and opt-in refresh wiring: done.
- P23B-T3 - Uppercase frontend autocomplete polish: done.
- P23B-T5 - Backend recents/default cleanup: done.
- P23B-T6 - Browser-local recents LRU: done.
- P23B-T7 - Offline fixture cleanup: done.
- P23B-T8 - Agent Console autocomplete parity: done; no code change needed because Agent Console reuses `TradeReviewForm`.

Deferred cleanup:

- Remove demo fixture prominence once real refreshed symbol directory is reliable.
- Avoid duplicate task IDs in future Phase 23 references.

### Phase 22A - Market Data Evaluation

Status: backend evaluation foundation complete; commercial provider track parked.

Current posture:

- Provider-neutral market-data contracts exist.
- Alpaca Basic evaluation adapter is internal/demo only and indicative/limited-source.
- No provider is selected for production.
- Tradier is not the assumed scalable production provider.
- Commercial vendor comparison/RFI is parked until external paid beta or production market-data licensing is planned.

Recent status:

- P22A-T1 - Provider-neutral snapshot contracts and synthetic/replay tests: done.
- P22A-T4 - Alpaca Basic local/internal evaluation adapter: done.

## Paused / Deferred

### Phase 21A - Realtime Agent Console Backend Contract

Status: paused.

Do not implement:

- Agent Console follow-up composer activation.
- SSE follow-up command path.
- Agent-thread persistence.
- Live multi-agent debate/routing/reflection/memory.

Reactivation requires Codex A/PM approval after founder learning and architecture review.

### Commercial Market-Data Provider Selection

Status: parked.

Do not start vendor outreach, licensing negotiation, pricing negotiation, production-provider selection, or public current-quote display until external paid beta or production planning reopens the track.

### Dashboard Claude Design Exploration

Status: allowed only after contract boundaries are defined.

Claude Design may explore hierarchy and visual treatment, but must not invent backend fields, fake real account values, add execution controls, or make demo data appear real.

## Older Phase References

Older phase details remain preserved in:

- `docs/shared/implementation_plan_archive_2026-06-03.md`
- `docs/shared/completed_phases_log.md`
- `docs/shared/CHANGELOG.md`

Key architecture/product docs:

- `docs/shared/current_roadmap.md`
- `docs/shared/TASKS.md`
- `docs/codex-a-product/DASHBOARD_CONTENT_DECISION.md`
- `docs/codex-b-architecture/ARCHITECTURE_HANDOFF.md`
- `docs/codex-b-architecture/architecture.md`

## Current Next Step

If frontend work resumes, the next clean handoff is:

- Claude A: P26A-T2 Dashboard Market Mood compact card.
- Reviewer: Claude B or Codex B.

Keep the implementation prompt narrow: consume reviewed Market Mood backend fields, render the compact Dashboard card below primary review-readiness/portfolio-risk surfaces, and preserve all source-rights and non-signal caveats.
