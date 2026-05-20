# Task Routing and Current Work

This file is a lightweight task index. The detailed task specs remain in `docs/shared/implementation_plan.md`; completed verification history belongs in `docs/shared/completed_phases_log.md`.

## Current State

- Completed foundation: Phases 1-16.
- Active roadmap phase: Phase 17 - TradingAgents/Public Research Evidence Adapter.
- Current safety foundation: broker portfolio snapshot freshness/actionability is explicit, Phase 16 agent components consume it, and Phase 16B enforces private/public context boundaries.
- Current architecture concern: Phase 17 must remain optional public ticker/company evidence only, not the portfolio-aware decision engine.

## Current Primary Owners

| Workstream | Owner | Supporting reviewer |
| --- | --- | --- |
| Product scope, MVP, positioning | Codex A PM | Claude C |
| Architecture, API/data contracts, ADRs | Codex B | Claude B |
| Backend implementation | Codex C | Claude B |
| Frontend UI/UX | Claude A | Codex B for contract review |
| Security/privacy/compliance | Claude D later | Codex B/C until active |
| DevOps/production readiness | Codex D later | Codex C until active |

## Near-Term Task Candidates

Do not treat this list as authorization to implement. Each item needs an approved task spec before code changes.

1. Backend: start Phase 17 optional dependency detection for TradingAgents/Public Research Evidence Adapter.
2. Backend: keep Phase 17 public ticker/company evidence only; do not send private portfolio context to TradingAgents or public evidence roles.
3. Frontend: wait for safe read schema and Phase 17 evidence contracts before rich research/debate UI; the first trade-review workspace can consume completed Phase 16 outputs.
4. Market data: keep real provider integration deferred for local MVP; plan Tradier REST snapshots before external paid beta or quote-current options review.
5. Security: formalize broker-data handling policy before any hosted deployment.

## Routine Task Checklist

- Confirm owner and phase/task id.
- Read `AGENTS.md`, `docs/shared/current_roadmap.md`, and the specific task section.
- Keep scope to one task.
- Use synthetic data only.
- Run relevant tests/checks.
- Update `docs/shared/implementation_plan.md` verification notes for implementation tasks.
- Add a short entry to `docs/shared/CHANGELOG.md` only for meaningful user-facing, architecture, security, or workflow changes.
