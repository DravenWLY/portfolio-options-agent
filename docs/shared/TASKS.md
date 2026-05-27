# Task Routing and Current Work

This file is a lightweight task index. The detailed task specs remain in `docs/shared/implementation_plan.md`; completed verification history belongs in `docs/shared/completed_phases_log.md`.

## Current State

- Completed foundation: Phases 1-16, Phase 17A, Phase 18A, Phase 18B, Phase 18C, Phase 19A, Phase 19B, Phase 19C, and Phase 20A.
- Active roadmap phases: Phase 20B - remaining blocked Modern Portfolio Desk contracts; Phase 20D - completed Dashboard cockpit cleanup/polish checkpoint with constrained Claude Design exploration next; Phase 22A - completed internal adapter evaluation checkpoint with no external test authorized.
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

1. Dashboard design checkpoint: `P20D-T1` through `P20D-T3` are complete and reviewed. Claude Design may be used next only for constrained Dashboard visual exploration. Every proposed panel must be classified as available now, future backend contract needed, or out of scope before Claude A implements anything. Do not add fields, endpoints, market/news data, or real/demo values that feel connected without a reviewed contract.
2. Market-data evaluation checkpoint: `P22A-T4` is complete after Codex B PASS re-review. No actual Alpaca API request, credential path, frontend data display, agent ingestion, or production-provider work is authorized.
3. Product/architecture: commercial vendor/RFI work is parked. Retain reference documentation for later scale planning; do not begin outreach, licensing/pricing negotiation, or provider selection now. News/economic-calendar data and symbol-search remain separate future evaluations.
4. Remaining data contracts: P20B-T5 reports and P20B-T6 profile/display stay blocked until their persistence/auth and product decisions are approved.
5. Pause gate: do not start any Phase 21A realtime/agent expansion work or activate the Agent Console composer until Codex A explicitly reactivates a scoped slice.
6. Advisory: Codex E may produce agentic-AI learning memos for Codex A; those memos do not authorize implementation or roadmap changes.
7. Completed frontend boundary: `P20C-T1` through `P20C-T6` are reviewed as the current Modern Desk integration checkpoint; future redesign or data wiring requires a new approved task.

## Routine Task Checklist

- Confirm owner and phase/task id.
- Read `AGENTS.md`, `docs/shared/current_roadmap.md`, and the specific task section.
- Keep scope to one task.
- Use synthetic data only.
- Run relevant tests/checks.
- Update `docs/shared/implementation_plan.md` verification notes for implementation tasks.
- Add a short entry to `docs/shared/CHANGELOG.md` only for meaningful user-facing, architecture, security, or workflow changes.
