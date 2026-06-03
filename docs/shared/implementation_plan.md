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
- A future dedicated Market Context page may show all eight indicators with charts and explanations.

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
- P26A-T2 - Dashboard Market Mood compact card: next frontend task for Claude A.
- P26A-T3 - Market Context detail page with all indicators: deferred until compact card is accepted.
- P26A-T4 - Source/rights and production-readiness review: required before production/public display.

Next handoff:

- Ask Claude A to implement P26A-T2 from the reviewed backend contract and Portfolio Copilot visual language.
- Ask Claude B or Codex B to review before marking done.

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

Next possible work:

- Safe read-only Agent Console handoff using reviewed display labels.
- Single-run real-provider gate if explicitly approved and cost/rate-limit caveats are clear.
- P25A-T12 - Migrate Gemini adapter from deprecated SDK to `google-genai`: proposed, low priority.

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
- `docs/shared/deferred_items.md`
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
