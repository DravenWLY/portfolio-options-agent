# Agent Handoff And Review Format

Use this format for Codex and Claude implementation handoffs, review requests, and completion reports. Keep it short. Do not paste large file contents, repeated safety text, or full verification logs unless a reviewer asks.

## Purpose

- Make Codex and Claude outputs consistent.
- Reduce token usage during reviews.
- Prevent prompts from turning a simple UI or backend task into a broad audit.
- Separate implementation, contract review, and visual review responsibilities.

## Prompt Format

Use this structure when asking another agent to work. When sending a prompt to
another agent, wrap the entire prompt in one fenced `text` block. Do not use a
`markdown` fence for agent prompts, and do not put nested triple-backtick code
fences inside the prompt body; use indented commands or bullet lists instead.

```text
Agent: <Claude A | Claude B | Claude E | Codex C | Codex D>
Task: <task id and short title>
Mode: <implement | review | re-review | docs-only>

Skill:
- <required skill path, if any>

Goal:
<one or two sentences>

Read:
- Use CodeGraph first when available:
  - start with one focused `codegraph_explore` for the main symbols/flow;
  - use `codegraph_search` for locations;
  - use `codegraph_callers` / `codegraph_callees` / `codegraph_impact` for dependency checks;
  - direct file reads should be targeted confirmations, not broad read loops.
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

## Review-Only Sub-Agent Pattern

Implementation agents may request a review-only sub-agent after their assigned
work is complete and local verification has run. The review sub-agent must not
implement, broaden scope, inspect private data, or mark the task done. It returns
`PASS` or `BLOCKED`; if blocked, the original implementation owner fixes the
blocker and requests a narrow re-review.

### Who May Request Which Review

- Codex C may request Codex B review for backend/API/schema/DB/provider work.
- Claude A may request Claude B visual/design review, and Codex B review when
  the frontend work consumes or changes backend contracts.
- Codex F may request Claude B visual/design review, and Codex B review when
  the frontend work consumes or changes backend contracts.
- Claude E may request Codex B review for agentic workflow architecture,
  contracts, tool-use boundaries, prompt/evidence boundaries, and safety.
- Codex D may request Codex B review for Docker, build, runtime, environment,
  CI, and deployment-boundary work.
- Codex B may request a specialist second opinion: Claude B for visual/UX,
  Claude E for agentic workflow, Codex C for backend feasibility, or Codex A for
  product scope.
- Codex A may request Codex B architecture review, Claude C product/competitor
  research, or other review support for roadmap decisions.
- Claude B may request Codex B review only when a visual review finds a contract,
  privacy, endpoint, or safety uncertainty.

Review agents should not chain more reviewers unless they hit a clear blocker.
Review-only agents should not spawn implementation agents.

### Review Agent Types

- Codex B contract/privacy/architecture reviewer: backend contracts, API routes,
  schemas, Account Details, Trade Review, Agent Team evidence, provider
  boundaries, and cross-layer integration.
- Claude B visual/design reviewer: frontend layout, readability, accessibility,
  responsive behavior, fintech UX quality, and visible safety copy.
- Claude E agentic AI workflow reviewer: multi-agent flow, tool-use policy,
  eval harness, prompt/evidence boundary, latency/cost design.
- Codex D devops/runtime reviewer: Docker, Compose, build packaging, CI,
  runtime profiles, deployment boundaries.
- Codex A product acceptance reviewer: product scope, user value, priority,
  wording intent, and whether a feature is enough.
- Claude D security/privacy reviewer, when available: threat model, broker-data
  exposure, data deletion/export, credentials, compliance language.

### Review-Only Prompt Template

Use this exact shape when asking a sub-agent to review completed work.

```text
Agent: <Codex B | Claude B | Claude E | Codex D | Codex A>
Task: <phase-task id> - <short title>
Mode: review-only

Goal:
Review the completed work and return PASS or BLOCKED. Do not implement changes. Do not edit files.

Read:
- Use CodeGraph first when available:
  - explore <main symbols/routes/components/contracts>
- <current task or architecture doc>
- <changed files>
- <directly related tests/contracts>
- Read additional files only if necessary.

Scope:
- Review only <contract/privacy/safety | visual/design | agentic workflow | devops/runtime | product scope>.

Out of scope:
- Do not edit files.
- Do not broaden into unrelated repo audit.
- Do not inspect .env, secrets, DB contents, logs, broker payloads, screenshots, generated reports, or real brokerage data.
- Do not call external providers unless explicitly authorized.

Acceptance:
- <criterion 1>
- <criterion 2>
- <criterion 3>
- <criterion 4>

Verification already run:
- <command> -> <result>
- <command> -> <result>
- git diff --check -> <result>

Return:
- Task
- Verdict: PASS or BLOCKED
- Files reviewed
- Blockers with file/line references, if any
- Important issues, if any
- Deferred polish, max 3
- Verification, including anything not run
- Next step
```

### Cautions

- Keep review prompts narrow. Include exact changed files, directly related
  contracts/tests, and the relevant task doc.
- Say `Do not edit files` for review-only work.
- Do not ask review sub-agents to rerun broad verification unless the review
  requires it.
- Do not mark a task `done` until the required review gate returns `PASS`.
- Close the review sub-agent after it returns the report.
- A review sub-agent never receives broader data access than the original task.

## Prompt Rules

- Agent prompts must be copyable as one fenced `text` block. Avoid nested code
  fences, HTML textareas, or markdown fences that render awkwardly in the app.
- Always include the required skill path when a task depends on a Claude/Codex skill.
- For code implementation or code review prompts, include a short "Use CodeGraph first when available" instruction instead of asking the agent to read many large source files. Name the key symbols/flows to explore, then list only changed files and directly related contracts/tests.
- Use a strict read list for reviews, but allow "read additional files only if necessary."
- Do not ask a reviewer to re-run all implementation verification unless that is the purpose of the review.
- Do not ask Claude B to review backend contracts. Claude B reviews visual/design quality unless explicitly assigned otherwise.
- Do not ask Codex B to do visual polish unless the issue is also contract/safety related.
- For data-backed frontend pages, include the full-stack preview instruction
  instead of a frontend-only dev-server instruction:
  `docker compose up -d postgres backend frontend`, then
  `curl -i http://localhost:8000/health`,
  `curl -i http://localhost:8000/users`, and
  `curl -i http://localhost:5173/api/users`, then open the target frontend route.
  If the full stack cannot start, the agent must report the exact blocker and
  label any browser check as route-shell only.
- Keep copied verification output to one-line results.
- Avoid token-heavy prompt bodies: do not paste large source excerpts, screenshots as text, full logs, broad file trees, or repeated safety boilerplate. Put the narrow objective, changed files, acceptance checks, and verification result only.
- Do not include giant archived docs in read lists by default:
  - `docs/shared/completed_phases_log.md`
  - `docs/shared/implementation_plan_archive_2026-06-03.md`
  - `docs/shared/implementation_plan_archive_2026-06-12.md`
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
