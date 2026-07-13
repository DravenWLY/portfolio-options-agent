# Documentation Map

Status: docs index
Owner: shared
Last updated: 2026-07-10

The docs folder is organized by agent ownership plus a shared source-of-truth area. Prefer the smallest relevant file before loading large architecture or history documents.

## Read Order

Unless a task gives a narrower read list:

1. `AGENTS.md` for safety and task discipline.
2. `docs/shared/current_roadmap.md` for current direction.
3. `docs/shared/implementation_plan.md` for active work and next handoff.
4. `docs/shared/agent_workflows.md` for repo-specific workflow rules such as
   CodeGraph-first reviews and full-stack preview.
5. `docs/shared/AGENT_REPORT_FORMAT.md` for copyable prompt/report format.
6. `docs/shared/AI_TEAM.md` for agent ownership when ownership is unclear.
7. The role-specific folder for the active agent.
8. `docs/codex-b-architecture/architecture.md` only when full architecture context is needed.
9. `docs/shared/completed_phases_log.md` or dated archives only when historical verification details are directly needed.

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
| `docs/codex-g-research/` | Codex G Research | Frontier agentic-AI / multi-agent cooperation literature briefs with applicability analyses. |

## Current Architecture / Agentic Design Trail

For current Agent Team work, prefer this narrow trail before loading older
phase archives:

- `docs/shared/implementation_plan.md` - active phase status and handoffs.
- `docs/shared/current_roadmap.md` - current product/architecture direction.
- `docs/codex-b-architecture/PHASE_33A_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md` -
  mock/offline tool-mediated Agent Team boundary.
- `docs/codex-b-architecture/PHASE_34A_LIVE_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md` -
  live LLM/tool-mediated prototype boundary.
- `docs/claude-e-agentic/PHASE_33A_TOOL_RICH_AGENT_TEAM_ARCHITECTURE_MEMO.md` -
  tool-rich architecture discussion.
- `docs/claude-e-agentic/PHASE_34A_T2_LIVE_ROLE_PROMPT_AUDITOR_DESIGN.md` -
  live role prompt and Evidence Auditor design.
- `docs/codex-b-architecture/PHASE_34A_T6_PUBLIC_NEWS_EVENT_SOURCE_RIGHTS_GATE.md` -
  public news/event source-rights decision for Agent Team tools.

## Agent Context Decision

The previous generic agent-context folder was removed because it became a vague catch-all. Its useful content was retained and moved into role-specific folders:

- The backend working-context brief now lives at `docs/codex-c-backend/WORKING_CONTEXT.md`.
- The Opus review brief now lives at `docs/claude-b-review/OPUS_REVIEW_BRIEF.md`.

## Large Files

- `docs/codex-b-architecture/architecture.md` is the full architecture reference. Load it only when necessary.
- `docs/shared/implementation_plan.md` is the short active work index. Historical task detail is archived in `docs/shared/implementation_plan_archive_2026-06-03.md`, `docs/shared/implementation_plan_archive_2026-06-12.md`, and `docs/shared/completed_phases_log.md`.
- `docs/shared/completed_phases_log.md` is historical verification archive. Avoid loading it by default.
- `docs/shared/frontend_design_change_playbook.md` is the reference for future redesigns, prototype adoption, Figma/Claude Design integration, and frontend design-system migrations.

## Review Framework

Use `docs/shared/ENGINEERING_REVIEW_FRAMEWORK.md` as the lifecycle quality framework. It is not a prompt; it defines how product, architecture, implementation, review, security, DevOps, and maintenance work should be evaluated across the development process.
