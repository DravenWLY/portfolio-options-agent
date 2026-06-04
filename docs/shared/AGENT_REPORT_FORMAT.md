# Agent Handoff And Review Format

Use this format for Codex and Claude implementation handoffs, review requests, and completion reports. Keep it short. Do not paste large file contents, repeated safety text, or full verification logs unless a reviewer asks.

## Purpose

- Make Codex and Claude outputs consistent.
- Reduce token usage during reviews.
- Prevent prompts from turning a simple UI or backend task into a broad audit.
- Separate implementation, contract review, and visual review responsibilities.

## Prompt Format

Use this structure when asking another agent to work.

```text
Agent: <Claude A | Claude B | Claude E | Codex C | Codex D>
Task: <task id and short title>
Mode: <implement | review | re-review | docs-only>

Skill:
- <required skill path, if any>

Goal:
<one or two sentences>

Read:
- <only task docs and directly changed files>
- Read additional files only if necessary.

Scope:
- <what is allowed>

Out of scope:
- <only the important exclusions for this task>

Acceptance:
- <3-7 concrete checks>

Verify:
- <exact commands or "do not run tests">

Return:
- Verdict or summary
- Files changed or reviewed
- Tests run
- Blockers only, if any
- Next step
```

## Completion Report Format

Implementation agents should return this structure.

```text
Task: <task id>
Status: done | blocked

Summary:
- <1-3 bullets>

Files changed:
- <path>

Verification:
- <command> -> <pass/fail/not run>

Safety/contract:
- <only task-relevant confirmations>

Blockers:
- None

Next step:
- <who should review or implement next>
```

## Review Report Format

Review agents should return this structure.

```text
Task: <task id>
Verdict: PASS | BLOCKED

Blockers:
- None

Important issues:
- <only if relevant>

Deferred polish:
- <optional, max 3>

Verification:
- <commands run or "not run">

Next step:
- <what should happen next>
```

## Prompt Rules

- Always include the required skill path when a task depends on a Claude/Codex skill.
- Use a strict read list for reviews, but allow "read additional files only if necessary."
- Do not ask a reviewer to re-run all implementation verification unless that is the purpose of the review.
- Do not ask Claude B to review backend contracts. Claude B reviews visual/design quality unless explicitly assigned otherwise.
- Do not ask Codex B to do visual polish unless the issue is also contract/safety related.
- Keep copied verification output to one-line results.
- Do not include giant archived docs in read lists by default:
  - `docs/shared/completed_phases_log.md`
  - `docs/shared/implementation_plan_archive_2026-06-03.md`
- For frontend work, cite:
  - `.claude/skills/frontend-design/SKILL.md`
- For fintech UX review, cite:
  - `.claude/skills/finance-dashboard-ux-review/SKILL.md`

## Standard Ownership

- Codex A: product/PM decisions.
- Codex B: architecture, contract, privacy, safety review.
- Codex C: backend implementation, except agentic AI system work.
- Codex D: DevOps, packaging, CI, deployment.
- Claude A: frontend implementation.
- Claude B: frontend visual/design review.
- Claude E: agentic AI system design and implementation.

## When To Block

Block only for:

- contract mismatch;
- unsafe data exposure;
- forbidden advice/execution wording;
- wrong endpoint/provider path;
- broken build/tests for the touched area;
- missing core behavior requested by the task;
- visual defect that makes the feature unusable.

Do not block for optional polish, wording preferences, or future enhancements. Put those under `Deferred polish`.
