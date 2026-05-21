# Task Routing and Current Work

This file is a lightweight task index. The detailed task specs remain in `docs/shared/implementation_plan.md`; completed verification history belongs in `docs/shared/completed_phases_log.md`.

## Current State

- Completed foundation: Phases 1-16 and Phase 18A.
- Active roadmap phase: Phase 18B - Frontend Trade Review Workspace expansion.
- Current safety foundation: broker portfolio snapshot freshness/actionability is explicit, Phase 16 agent components consume it, and Phase 16B enforces private/public context boundaries.
- Current architecture concern: expand the completed Phase 18A workspace without breaking the sanitized read contract, freshness/actionability separation, read-only manual-review scope, or Phase 17 freeze.

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

1. Backend fast-follow: unify the frontend-read forbidden-field key set in `app/services/privacy.py` before new response fields are added.
2. Architecture: keep `docs/codex-b-architecture/PHASE_18A_FRONTEND_READINESS_CONTRACT.md` as the baseline frontend/backend boundary until a Phase 18B contract revision exists.
3. Frontend: expand the read-only Trade Review Workspace only after backend contract implications are clear.
4. Review: ask Claude B to check frontend safety language, stale-data clarity, no execution controls, private-data leakage, UX clarity, and implementation quality for any Phase 18B UI changes.
5. Market data: keep real provider integration deferred for local MVP; plan Tradier REST snapshots before external paid beta or quote-current options review.
6. Phase 17: keep TradingAgents/Public Research Evidence optional and frozen unless PM explicitly reactivates it.

## Routine Task Checklist

- Confirm owner and phase/task id.
- Read `AGENTS.md`, `docs/shared/current_roadmap.md`, and the specific task section.
- Keep scope to one task.
- Use synthetic data only.
- Run relevant tests/checks.
- Update `docs/shared/implementation_plan.md` verification notes for implementation tasks.
- Add a short entry to `docs/shared/CHANGELOG.md` only for meaningful user-facing, architecture, security, or workflow changes.
