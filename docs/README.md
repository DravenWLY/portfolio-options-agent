# Documentation Map

Status: docs index
Owner: shared
Last updated: 2026-05-20

The docs folder is organized by agent ownership plus a shared source-of-truth area. Prefer the smallest relevant file before loading large architecture or history documents.

## Read Order

Unless a task gives a narrower read list:

1. `AGENTS.md` for safety and task discipline.
2. `docs/shared/current_roadmap.md` for current direction.
3. `docs/shared/AI_TEAM.md` for agent ownership.
4. `docs/shared/TASKS.md` for current task routing.
5. The role-specific folder for the active agent.
6. `docs/shared/implementation_plan.md` for task-level implementation specs.
7. `docs/codex-b-architecture/architecture.md` only when full architecture context is needed.
8. `docs/shared/completed_phases_log.md` only when historical verification details are directly needed.

## Folder Layout

| Folder | Owner | Purpose |
| --- | --- | --- |
| `docs/shared/` | All agents | Current roadmap, task routing, implementation plan, changelog, deferred items, completed phase log, and shared engineering review framework. |
| `docs/codex-a-product/` | Codex A PM | PRD, MVP scope, feature priority, metrics, PM onboarding, and PM handoff docs. |
| `docs/codex-b-architecture/` | Codex B Architecture | Architecture source of truth, architecture handoff, and future ADRs. |
| `docs/codex-c-backend/` | Codex C Backend | Backend implementation context and backend-specific handoff briefs. |
| `docs/claude-a-frontend/` | Claude A Frontend | Frontend UX briefs and future frontend review notes. |
| `docs/claude-b-review/` | Claude B Review / QA | Review briefs, Opus review context, and QA/security review notes. |
| `docs/claude-c-competitor/` | Claude C Competitor Intel | Competitor analysis and product intelligence for PM synthesis. |
| `docs/codex-d-devops/` | Codex D DevOps | Deployment, CI/CD, observability, and production-readiness drafts. |
| `docs/claude-d-security/` | Claude D Security | Security, compliance, privacy, broker-data handling, and disclaimer drafts. |

## Agent Context Decision

The previous generic agent-context folder was removed because it became a vague catch-all. Its useful content was retained and moved into role-specific folders:

- The backend working-context brief now lives at `docs/codex-c-backend/WORKING_CONTEXT.md`.
- The Opus review brief now lives at `docs/claude-b-review/OPUS_REVIEW_BRIEF.md`.

## Large Files

- `docs/codex-b-architecture/architecture.md` is the full architecture reference. Load it only when necessary.
- `docs/shared/implementation_plan.md` is active/future task planning.
- `docs/shared/completed_phases_log.md` is historical verification archive. Avoid loading it by default.

## Review Framework

Use `docs/shared/ENGINEERING_REVIEW_FRAMEWORK.md` as the lifecycle quality framework. It is not a prompt; it defines how product, architecture, implementation, review, security, DevOps, and maintenance work should be evaluated across the development process.
