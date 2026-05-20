# Task Routing and Current Work

This file is a lightweight task index. The detailed task specs remain in `docs/shared/implementation_plan.md`; completed verification history belongs in `docs/shared/completed_phases_log.md`.

## Current State

- Completed foundation: Phases 1-15.
- Active roadmap phase: Phase 16 - Custom Portfolio-Aware Agent Orchestrator.
- Immediate safety concern before deeper agent work: broker portfolio snapshot freshness/actionability must be explicit before polished account-specific agent outputs sound current.

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

1. Architecture pass: add ADRs for broker freshness/actionability, agent-safe projections, and TradingAgents-as-async-evidence.
2. Backend: implement a Portfolio Snapshot Actionability Policy before Phase 16 agents produce polished account-specific outputs.
3. Backend: continue Phase 16 only after the actionability gate is accepted.
4. Frontend: wait for backend agent contracts before building the trade-review workspace.
5. Security: formalize broker-data handling policy before any hosted deployment.

## Routine Task Checklist

- Confirm owner and phase/task id.
- Read `AGENTS.md`, `docs/shared/current_roadmap.md`, and the specific task section.
- Keep scope to one task.
- Use synthetic data only.
- Run relevant tests/checks.
- Update `docs/shared/implementation_plan.md` verification notes for implementation tasks.
- Add a short entry to `docs/shared/CHANGELOG.md` only for meaningful user-facing, architecture, security, or workflow changes.
