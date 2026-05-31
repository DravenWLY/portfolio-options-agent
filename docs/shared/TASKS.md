# Task Routing and Current Work

This file is a lightweight task index. The detailed task specs remain in `docs/shared/implementation_plan.md`; completed verification history belongs in `docs/shared/completed_phases_log.md`.

## Current State

- Completed foundation: Phases 1-16, Phase 17A, Phase 18A, Phase 18B, Phase 18C, Phase 19A, Phase 19B, Phase 19C, and Phase 20A.
- Active roadmap phases: Phase 20B - remaining blocked Modern Portfolio Desk contracts; Phase 20D - completed Dashboard cockpit cleanup/polish/Claude Design visual refinement (P20D-T1 through P20D-T4); Phase 22A - completed internal adapter evaluation checkpoint with no external test authorized; Phase 23A/23B - symbol lookup complete through local recents; Phase 24A - economic calendar awareness next.
- Completed frontend integration sequence: Phase 20C - Modern Portfolio Desk reviewed wiring and presentation refinements.
- Paused design reference: Phase 21A - Realtime Agent Console backend contract. Do not begin implementation unless Codex A explicitly reactivates a scoped task.
- Current safety foundation: broker portfolio snapshot freshness/actionability is explicit, Phase 16 agent components consume it, and Phase 16B enforces private/public context boundaries.
- Current architecture concern: wire Modern Portfolio Desk placeholders through small sanitized backend read contracts while preserving privacy, freshness semantics, and deterministic/agent-commentary separation, while separately building an offline provider-neutral market-data evaluation foundation. Further interactive agent-console design is paused.
- Current product-positioning decision: Portfolio Copilot should complement,
  not replace, serious research/portfolio tools such as Stock Rover. The
  Dashboard is a review-readiness cockpit, not a research terminal, screener,
  watchlist, holdings grid, fair-value surface, or market terminal.

## Current Primary Owners

| Workstream | Owner | Supporting reviewer |
| --- | --- | --- |
| Product scope, MVP, positioning | Codex A PM | Claude C |
| Architecture, API/data contracts, ADRs | Codex B | Claude B |
| Backend implementation | Codex C | Claude B |
| Frontend UI/UX | Claude A | Codex B for contract review |
| Security/privacy/compliance | Claude D later | Codex B/C until active |
| DevOps/production readiness | Codex D later | Codex C until active |
| Agentic AI learning / applied research advice | Codex E advisory only | Codex A PM |

## Near-Term Task Candidates

Do not treat this list as authorization to implement. Each item needs an approved task spec before code changes.

1. Dashboard design checkpoint: `P20D-T1` through `P20D-T5` are complete and reviewed. `P20D-T5` applied the Stock Rover/Product B pressure-test cleanup using existing reviewed contracts: promoted the readiness verdict, demoted agent-provider status, hid plausible synthetic headline account values, and removed dead quick-review presets. Future Dashboard visual work requires a new approved task with reviewed contracts for any new data surfaces.
2. Dashboard Product B pressure-test outcome: accepted decisions are complement-not-replace positioning, no plausible synthetic headline account values, real-source account summary plus broker freshness before persisted review history, display-rights-cleared REST quotes before external-beta quote-current claims, narrow per-underlying earnings-date review context, and agent-provider status off the Dashboard first viewport.
3. Next Dashboard backend priority candidate: real-source account summary plus broker freshness mapping, if Codex A opens a task. Do not jump to persisted history, quote-current display, or new Dashboard panels before this trust foundation.
4. Market-data evaluation checkpoint: `P22A-T4` is complete after Codex B PASS re-review. No actual Alpaca API request, credential path, frontend data display, agent ingestion, or production-provider work is authorized.
5. Symbol lookup: Phase 23A/23B is complete through broad Nasdaq-traded local refresh, uppercase autocomplete, browser-local LRU recents (`poa-symbol-recents`), and offline fixture cleanup. Keep frontend contracts provider-neutral; no quotes, recommendations, frontend provider calls, broker tradability claims, or storage beyond the approved UI-only recents key.
6. Economic calendar awareness: `P24A-T1` is next unless Codex A reorders based on FRED/FMP access. Macro red-folder events require reviewed contracts and `is_trading_signal=false`; per-underlying earnings date is a separate narrow options-review-context candidate, not a generic company-news feed.
7. Product/architecture: commercial vendor/RFI work is parked. Retain reference documentation for later scale planning; do not begin outreach, licensing/pricing negotiation, or provider selection now.
8. Remaining data contracts: P20B-T5 reports and P20B-T6 profile/display stay blocked until their persistence/auth and product decisions are approved.
9. Pause gate: do not start any Phase 21A realtime/agent expansion work or activate the Agent Console composer until Codex A explicitly reactivates a scoped slice.
10. Advisory: Codex E may produce agentic-AI learning memos for Codex A; those memos do not authorize implementation or roadmap changes.
11. Completed frontend boundary: `P20C-T1` through `P20C-T6` are reviewed as the current Modern Desk integration checkpoint; future redesign or data wiring requires a new approved task.

## Routine Task Checklist

- Confirm owner and phase/task id.
- Read `AGENTS.md`, `docs/shared/current_roadmap.md`, and the specific task section.
- Keep scope to one task.
- Use synthetic data only.
- Run relevant tests/checks.
- Update `docs/shared/implementation_plan.md` verification notes for implementation tasks.
- Add a short entry to `docs/shared/CHANGELOG.md` only for meaningful user-facing, architecture, security, or workflow changes.
