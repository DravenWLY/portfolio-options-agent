---
name: implementation-plan-review
description: Enforce the repository's incremental implementation plan, one-task-at-a-time workflow, expected files, tests, rollback notes, and safety boundaries.
---

# implementation-plan-review

Use this skill to keep work in `portfolio-options-agent` aligned with `docs/implementation_plan.md` and `AGENTS.md`. The plan controls incremental work. This skill is the checkpoint.

## When to use

- A user asks Claude Code to "start the next task", "do task X", or "implement X".
- Claude Code is about to make changes that touch more than one file or domain.
- A PR or diff claims to close a plan task.
- The user asks for a plan or roadmap update.

## Required reading

- `AGENTS.md`
- `docs/implementation_plan.md` (the full file, top to bottom; do not just read the first task)
- `docs/architecture.md` for any task that touches structure
- The files listed under the task's "Files expected to change"

## Hard rules to enforce

- Implement only one task at a time unless the user explicitly approves a broader batch.
- Do not modify `../TradingAgents`.
- Do not mix backend and frontend phases in one task unless the user explicitly approves it.
- Do not read or modify `.env`, `.env.*`, broker credential files, private configs, real account data, real reports, broker CSVs, statements, transactions, imports, exports, or PDFs.
- No API keys, tokens, or provider secrets anywhere in code, fixtures, or env files exposed to bundles.
- No real holdings, real account values, real trades, or real broker exports. Synthetic data only.
- No automatic trading, broker order execution, broker scraping, Fidelity scraping, MFA bypass, or credential automation.
- Deterministic financial calculations live in tested backend Python code, not in LLM prompts or in frontend guesses.
- Do not claim tests passed unless they were actually run; cite the exact command and result.
- Update `docs/implementation_plan.md` only when a real implementation task is completed, or when the user explicitly asks for planning updates. Do not retro-fit acceptance criteria after the fact.

## Pre-task review

Before any implementation work starts, confirm:

1. The task exists in `docs/implementation_plan.md` with a task id (for example `P1-T4`).
2. The task has all required fields: task id, title, objective, files expected to change, dependencies, implementation steps, acceptance criteria, tests, rollback notes, and status.
3. The task is the next eligible task in order. No earlier `not_started` or `in_progress` task is being skipped.
4. Dependencies listed by the task are `done` or do not exist.
5. The proposed change set matches "Files expected to change". Files outside that list are flagged.
6. The task does not bundle multiple phases or domains. If it does, propose splitting before coding.
7. The current branch and `git status` are clean enough that the diff will be reviewable.

If any of these fail, stop and report. Do not start implementation.

## During-task review

While work is happening:

- New files outside "Files expected to change" must be justified explicitly in the response.
- No drive-by refactors of unrelated code.
- No changes to public API shape unless the task says so.
- Tests are added or updated for any behavior change.
- All tests added are synthetic and do not require real provider credentials or network calls.
- External boundaries (broker, market-data, LLM, TradingAgents) are mocked.

## Post-task / close-out review

When closing a task, verify in this order:

1. Every acceptance criterion is met. Cite evidence (file paths, test output, command output).
2. Tests in the "Tests to run" section were actually run. Do not claim a test passed unless it was run. Include the exact command and its result.
3. No denied files were read, printed, or modified.
4. `git status --short --branch` is captured for the verification notes.
5. Rollback notes are still accurate. Update them if the file list changed.
6. Status is moved to `done` only after the above. Otherwise leave as `in_progress` or `blocked` with a clear reason.
7. Verification notes list the exact commands run and their results.

## Anti-patterns to reject

Reject and call out:

- "While I'm in here, I also refactored ..."
- "I added a new task to the plan and immediately implemented it" without user approval.
- "Tests pass" without showing the command and the result.
- "I temporarily disabled the deny rules" or "I read the `.env` to check".
- "I integrated TradingAgents directly to save time".
- "I added a small Fidelity scraper because the user wanted positions imported".
- "I hardcoded an API key just for now".
- "I used real holdings from the user as a fixture".
- "I closed task X and Y together because they were related".
- "I started the frontend phase while finishing the backend phase".

## Output format

1. Active task: id, title, status.
2. Pre-task or post-task verdict: PASS / FAIL with reasons.
3. Findings, grouped as Blocker / Important / Polish.
4. Proposed `docs/implementation_plan.md` status change, if any, with the exact diff to apply.
5. Proposed next action: continue, split task, stop for user input, or close.

Do not write production code as part of this review. The skill is a gate, not an implementer.
