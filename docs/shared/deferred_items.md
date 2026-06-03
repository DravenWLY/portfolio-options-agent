# Deferred Items

This file tracks known non-blocking work so active plans can stay small. Do not treat these as authorized implementation tasks until they are pulled into `docs/shared/implementation_plan.md`.

## Paused / Incomplete Phase Backlog

This section preserves the important paused or incomplete threads from the archived implementation plan without re-expanding the active plan. Details remain in `docs/shared/implementation_plan_archive_2026-06-03.md`.

- Phase 18B: `P18B-T3` research-evidence display remains deferred until reviewed Phase 17 backend evidence contracts exist.
- Phase 20B: `P20B-T5` reports remains blocked until report persistence and report-read contracts are approved.
- Phase 20B: `P20B-T6` profile/private-alpha display remains blocked until auth/session/profile display decisions are approved.
- Phase 21A: realtime Agent Console backend contract remains paused. Do not implement follow-up composer activation, SSE follow-up, agent-thread persistence, live debate/routing/reflection/memory, or realtime multi-agent expansion unless PM reactivates a scoped slice.
- Phase 22A: commercial market-data provider selection and RFI outreach are parked. Internal provider-neutral evaluation is complete; no production provider is selected.
- Phase 23B: symbol lookup is functional for the personal demo. Deferred cleanup includes reducing demo fixture prominence once the refreshed directory path is reliable and only adding typed-but-never-selected recents after a reviewed validation/display-field path exists.
- Phase 24A/24B: economic awareness backend foundations exist, but frontend/economic-news expansion can remain paused while Market Mood or agentic workflow is higher priority. FMP is not usable as the free calendar source; FRED is the current official-source backend direction.
- Phase 25A: agentic workflow remains mock-first and gated. Deferred items include real parallel fan-out, persistence/checkpointing, MCP/tool runtime, memory, LangGraph adoption, role rename, and frontend composer activation.
- Phase 25A: `P25A-T12` Gemini SDK migration to `google-genai` is proposed low priority.
- Phase 26A: Market Mood compact Dashboard card is active next work; full Market Context detail page and source/rights production review remain deferred until after the compact card is accepted.
- Product/research: Claude Design exploration and competitor/Product B pressure-test follow-ups may continue, but unsupported fields must be labelled future-contract-needed and must not be implemented without reviewed backend contracts.

## Storage and Migration Hardening

- Evaluate service-layer transaction boundaries and a future Unit of Work pattern before larger sync/report workflows need multi-table atomicity.
- Evaluate DB-level CHECK constraints for enum-like string columns.
- Evaluate snapshot uniqueness constraints or provider-source idempotency keys for repeated sync payloads.
- Evaluate covering indexes for high-volume snapshot queries.
- Evaluate a dedicated Alembic migration round-trip pytest strategy using an isolated migration test database.
- Add a DB-level CHECK that exactly one of `secret_ref` or `encrypted_secret_ref` is set if provider credential storage expands.

## Broker Sync and SnapTrade

- `GET /option-contracts/{id}` — `OptionPositionsView` lazy-fetches contract details (underlying symbol, expiry, strike, type) via this path. No corresponding backend route was confirmed in the reviewed route files. If the route is missing, contract-dependent columns silently show "—" (fetch failure is caught and ignored). Codex must add this route to `backend/app/api/routes/` returning an `OptionContractRead` response, or confirm it exists under a different prefix.
- Explicit SnapTrade key rotation path.
- External secret manager backend.
- Webhook ingestion.
- Explicit account remap/edit UI.
- More resilient OCC parsing beyond the current MVP.
- Cost basis provider mapping where safe and supported.
- More advanced provider payload sanitizer value heuristics.

## Broker Activities and Transactions

- Add a future read-only broker activities sync layer after current-position sync and deterministic risk foundations are stable.
- Store sanitized provider activities separately first, for example in `broker_activities` plus activity sync-run metadata, before normalizing into app-level trade or strategy records.
- Do not treat activities as intraday real-time execution data; they may be cached, delayed, partial, or daily depending on provider and broker.
- Keep broker orders separate from broker activities. Orders are read-only status/intent data; activities are historical account events.
- Later normalization candidates: `trade_journal_entries`, `premium_income_records`, `wheel_cycles`, and `wheel_cycle_events`.
- Use activities to support realized premium tracking, assignment/exercise/expiration detection, and wheel lifecycle reconstruction only after deterministic reconciliation tests exist.

## CSV and Manual Fallback

- Project-specific CSV exception hierarchy.
- Accounting-style negative parsing for Fidelity CSV values.
- Typed row models for provider-specific CSV previews.
- Resource limits beyond the current preview size and row guards if import volume grows.

## Market Data

- Real provider integrations after Phase 12 contracts are stable.
- Real-time or streaming quotes only for actively viewed symbols/contracts.
- OPRA/data redistribution review before any public/hosted product surface.
- Keep broker sync freshness and market quote freshness separate in all APIs and UI.

## Reports and Agents

- Full report restore/permanent-delete behavior.
- Report artifacts and PDF export.
- Agent retry/resume orchestration.
- LLM provider abstraction and cost controls.
- TradingAgents integration after custom report/agent foundations exist.

## Documentation

- Update `README.md` after roadmap realignment.
- Split `docs/codex-b-architecture/architecture.md` if it continues growing:
  - `product_architecture.md`
  - `technical_architecture.md`
  - `agent_architecture.md`
  - `data_architecture.md`
  - `roadmap.md`
