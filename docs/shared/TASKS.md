# Task Routing and Current Work

This file is a lightweight task index. The detailed task specs remain in `docs/shared/implementation_plan.md`; completed verification history belongs in `docs/shared/completed_phases_log.md`.

## Current State

- Completed foundation: Phases 1-16, Phase 17A, Phase 18A, Phase 18B, Phase 18C, Phase 19A, Phase 19B, Phase 19C, and Phase 20A.
- Active roadmap phase: Phase 20B - Modern Portfolio Desk backend contracts.
- Current safety foundation: broker portfolio snapshot freshness/actionability is explicit, Phase 16 agent components consume it, and Phase 16B enforces private/public context boundaries.
- Current architecture concern: wire Modern Portfolio Desk placeholders through small sanitized backend read contracts without exposing private data, inventing frontend fields, or collapsing broker freshness, market freshness, and agent-provider readiness.

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

1. Backend: Codex C continues Phase 20B with P20B-T4 portfolio context enumeration/detail contracts.
2. Architecture: Codex B reviews every P20B endpoint before Claude A consumes it.
3. Frontend: Claude A may wire P20B-T1/T1A/T2/T3 only with visible demo/not-connected labels; no ad hoc fields or frontend calculations.
4. Review: Claude B checks any frontend wiring for safety language, no execution controls, private-data leakage, and UX clarity.
5. Future gate: Phase 19D live LLM smoke testing remains explicit, backend-only, synthetic-only, and separate from frontend polish.

## Routine Task Checklist

- Confirm owner and phase/task id.
- Read `AGENTS.md`, `docs/shared/current_roadmap.md`, and the specific task section.
- Keep scope to one task.
- Use synthetic data only.
- Run relevant tests/checks.
- Update `docs/shared/implementation_plan.md` verification notes for implementation tasks.
- Add a short entry to `docs/shared/CHANGELOG.md` only for meaningful user-facing, architecture, security, or workflow changes.
