# Task Routing and Current Work

This file is a lightweight task index. The detailed task specs remain in `docs/shared/implementation_plan.md`; completed verification history belongs in `docs/shared/completed_phases_log.md`.

## Current State

- Completed foundation: Phases 1-16, Phase 17A, Phase 18A, Phase 18B, Phase 18C, Phase 19A, Phase 19B, Phase 19C, and Phase 20A.
- Active roadmap phases: Phase 20B - remaining blocked Modern Portfolio Desk contracts; Phase 20D - completed Dashboard cockpit cleanup/polish/Claude Design visual refinement (P20D-T1 through P20D-T4); Phase 22A - completed internal adapter evaluation checkpoint with no external test authorized; Phase 23A/23B/24A - symbol lookup completion first, economic/news awareness second.
- Completed frontend integration sequence: Phase 20C - Modern Portfolio Desk reviewed wiring and presentation refinements.
- Paused design reference: Phase 21A - Realtime Agent Console backend contract. Do not begin implementation unless Codex A explicitly reactivates a scoped task.
- Current safety foundation: broker portfolio snapshot freshness/actionability is explicit, Phase 16 agent components consume it, and Phase 16B enforces private/public context boundaries.
- Current architecture concern: wire Modern Portfolio Desk placeholders through small sanitized backend read contracts while preserving privacy, freshness semantics, and deterministic/agent-commentary separation, while separately building an offline provider-neutral market-data evaluation foundation. Further interactive agent-console design is paused.

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

1. Dashboard design checkpoint: `P20D-T1` through `P20D-T4` are complete and reviewed. `P20D-T4` implemented "Available now" visual refinements from the Claude Design feasibility review (action context bar, readiness section structure, account summary section headers, density polish). Future Dashboard visual work requires a new approved task with reviewed contracts for any new data surfaces.
2. Market-data evaluation checkpoint: `P22A-T4` is complete after Codex B PASS re-review. No actual Alpaca API request, credential path, frontend data display, agent ingestion, or production-provider work is authorized.
3. Symbol lookup: `P23A-T1` through `P23A-T5` are complete/reviewed. Phase 23B: Codex C owns `P23B-T1` persistent last-good normalized snapshots and `P23B-T2` opt-in local refresh wiring; `P23B-T5` (backend recents boundary cleanup) is done and Codex B reviewed PASS. Claude A completed `P23B-T3` uppercase/recent-list autocomplete polish and `P23B-T6` browser-local symbol recents LRU (single UI-only `poa-symbol-recents` key, capacity 5, recents recorded only on intentional selection/submit-promote; both pending Codex B frontend contract review). Keep frontend contracts provider-neutral; no quotes, recommendations, frontend provider calls, or broker tradability claims, and no localStorage beyond the approved `poa-symbol-recents` UI key.
4. Economic/news awareness: `P24A-T1` follows symbol lookup completion unless PM reprioritizes. It must implement synthetic/replay public economic-event awareness only, with `is_trading_signal=false`; no external news APIs or agent ingestion.
5. Product/architecture: commercial vendor/RFI work is parked. Retain reference documentation for later scale planning; do not begin outreach, licensing/pricing negotiation, or provider selection now.
6. Remaining data contracts: P20B-T5 reports and P20B-T6 profile/display stay blocked until their persistence/auth and product decisions are approved.
7. Pause gate: do not start any Phase 21A realtime/agent expansion work or activate the Agent Console composer until Codex A explicitly reactivates a scoped slice.
8. Advisory: Codex E may produce agentic-AI learning memos for Codex A; those memos do not authorize implementation or roadmap changes.
9. Completed frontend boundary: `P20C-T1` through `P20C-T6` are reviewed as the current Modern Desk integration checkpoint; future redesign or data wiring requires a new approved task.

## Routine Task Checklist

- Confirm owner and phase/task id.
- Read `AGENTS.md`, `docs/shared/current_roadmap.md`, and the specific task section.
- Keep scope to one task.
- Use synthetic data only.
- Run relevant tests/checks.
- Update `docs/shared/implementation_plan.md` verification notes for implementation tasks.
- Add a short entry to `docs/shared/CHANGELOG.md` only for meaningful user-facing, architecture, security, or workflow changes.
