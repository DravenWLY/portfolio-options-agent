# Deferred Items

This file tracks known non-blocking work so active plans can stay small. Do not treat these as authorized implementation tasks until they are pulled into `docs/shared/implementation_plan.md`.

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
