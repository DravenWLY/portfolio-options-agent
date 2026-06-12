# CLAUDE.md

Project-level guide for Claude Code working inside `portfolio-options-agent`.

This file is loaded automatically by Claude Code when it works in this repository. It is layered on top of `AGENTS.md`. If anything in this file conflicts with `AGENTS.md`, `AGENTS.md` wins.

## What this project is

`portfolio-options-agent` is a fintech decision-support dashboard for manual portfolio and options analysis. The product helps a human trader review positions, risks, income opportunities, and research context. It is not an automated trading system. It does not place orders. It does not log into brokers on the user's behalf.

## What Claude Code should optimize for here

- Frontend UI and UX work (React, Vite, TypeScript when the frontend is scaffolded).
- UI / UX review of dashboard screens, components, tables, charts, and option workflows.
- Code review with safety in mind: small, reviewable diffs and respect for project boundaries.
- Documentation work that supports the above.

Treat backend, agent, broker, and market-data work as out of scope by default unless the active task in `docs/shared/implementation_plan.md` explicitly calls for it.

## Required reading before making changes

Always inspect these first:

1. `AGENTS.md`
2. `docs/shared/current_roadmap.md`
3. `docs/shared/implementation_plan.md` (find the current handoff)
4. `docs/shared/agent_workflows.md` when preview, review, or workflow rules matter
5. `docs/codex-b-architecture/architecture.md` only when full architecture context is needed
6. `README.md` and `frontend/README.md` when frontend work is involved

## Working rules

- Implement one task at a time. Use `docs/shared/implementation_plan.md` for
  the current handoff and next recommended task.
- Treat `docs/shared/implementation_plan.md` as a short active-work index, not a historical ledger. Do not load dated archives or `completed_phases_log.md` unless the task explicitly needs historical verification.
- Keep changes small and reviewable. No multi-phase rewrites in one pass.
- Do not run unrelated refactors.
- Use CodeGraph first when it is available for codebase exploration. Start with one focused `codegraph_explore` for the relevant symbols/flow, then use `codegraph_search`, `codegraph_callers`, `codegraph_callees`, or `codegraph_impact` as needed. Avoid broad file-reading loops; direct file reads should be targeted confirmations, especially for files edited after the index.
- After each task, propose a status update for
  `docs/shared/implementation_plan.md`. Only mark a task `done` after
  acceptance criteria are met and verified.
- Stop for review after each task.
- Default backend test command: `cd backend && pytest`. Fallback: `cd backend && ./.venv/bin/python -m pytest`.

## Required output format

- Use `docs/shared/AGENT_REPORT_FORMAT.md` for implementation handoffs, completion reports, review requests, and review reports.
- Keep reports short and role-specific. Do not paste long logs or broad safety boilerplate.
- Every report must include: `Task`, `Status` or `Verdict`, `Files changed` or `Files reviewed`, `Verification`, `Blockers`, and `Next step`.
- Review prompts should ask for `PASS` or `BLOCKED`; put non-blocking improvements under `Deferred polish`.
- When frontend UI design or review is involved, explicitly follow `.claude/skills/frontend-design/SKILL.md`.
- When portfolio/options UX judgment is involved, also follow `.claude/skills/finance-dashboard-ux-review/SKILL.md`.

## Project boundary

- Do not modify `../TradingAgents`.
- Do not copy `../TradingAgents` source into this repo.
- Do not vendor or submodule `../TradingAgents` unless the user explicitly asks.
- Future integration with `../TradingAgents` happens through an adapter layer only.

## Safety boundaries (hard rules)

Claude Code must not, in this repository:

- Implement automatic trading or broker order execution.
- Implement broker scraping or any Fidelity / broker browser automation.
- Bypass MFA. Automate credential entry. Store broker usernames, passwords, or MFA secrets.
- Read, print, summarize, or modify `.env`, `.env.*`, broker credential files, private configs, real account data, real reports, broker CSVs, statements, transactions, imports, exports, or PDFs.
- Put API keys, access tokens, or provider secrets in frontend code or in any code that is bundled to the browser.
- Present output as guaranteed financial advice or guaranteed returns.
- Rely on LLMs for deterministic financial calculations. Those must live in tested backend Python code.

## Data rules

- Use synthetic demo data only. Never use real holdings, real account values, real trades, real broker exports, or real provider responses in code, tests, fixtures, or screenshots.
- `.env.example` is the only `.env`-style file Claude Code may read or modify, and only to document variable names with placeholder values.
- Generated artifacts in `data/`, `reports/`, `imports/`, `exports/`, `statements/`, `transactions/`, `logs/`, `cache/`, and `checkpoints/` are out of bounds. Do not read them.

## Real brokerage data boundary

Claude Code may review and edit source code, schemas, docs, synthetic fixtures, mocked responses, and UI layouts. Claude Code must not inspect real brokerage content by default.

Claude Code must not:

- Read, print, summarize, export, screenshot, or inspect real SnapTrade/Fidelity/brokerage data.
- Query a local database or API endpoint that may return real account balances, holdings, option positions, transactions, account identifiers, provider account IDs, broker sync raw payloads, reports, logs, or generated artifacts.
- Inspect browser screens, screenshots, terminal output, API payloads, or database rows containing real portfolio values or account details.
- Read or display SnapTrade user IDs, user secrets, portal URLs, consumer keys, access tokens, encrypted secret envelopes, or provider raw payloads.
- Use real brokerage values in docs, tests, examples, fixtures, screenshots, commits, prompts, or review summaries.

If a frontend or review task appears to need real brokerage data, Claude Code must stop and ask for explicit permission for that exact access. Prefer asking the user to run the diagnostic locally and provide redacted output. UI design and review should use synthetic or mocked data only.

## Financial calculation rule

- Any deterministic financial calculation (P/L, breakeven, annualized ROI, probability, Greeks, collateral) must be implemented in backend Python code with unit tests.
- The frontend renders calculation results. The frontend does not guess values, fabricate values, or recompute them in ways that can drift from the backend.

## Frontend preferences

- React + Vite + TypeScript is the assumed stack once the frontend task starts.
- For data-backed pages such as Account Details, Agent Console success states,
  Dashboard account panels, and broker/market pages, do not start only the
  frontend dev server for final preview. Start the full local stack first:
  `docker compose up -d postgres backend frontend`, then verify
  `curl -i http://localhost:8000/health`, `curl -i http://localhost:8000/users`,
  and `curl -i http://localhost:5173/api/users`.
  Only then open the frontend route. If backend/Postgres/dev user setup is
  unavailable, state that the browser smoke was route-shell only and explain the
  exact blocker.
  Do not rely on `.claude/launch.json` or a `frontend` preview label alone as
  proof of connected-data state; the probes above are the proof.
- Component-driven structure. Small composable components, not page-sized blobs.
- Every data-driven component handles loading, empty, error, stale, reauth-required, and offline states.
- Every panel that shows broker positions or market quotes shows its timestamp and source.
- Risk and freshness are never color-only. Always pair with icon and text.
- No `localStorage` / `sessionStorage` for sensitive data.
- No "place order", "execute", "auto-trade", or similar action buttons.
- No guaranteed-return or AI-recommended-trade language.

See the project skill at `.claude/skills/frontend-design/SKILL.md` for full visual and review standards.

## Skills available in this repo

- `docs/shared/agent_workflows.md` - repo-specific workflow guidance for frontend contract review, backend TDD slices, and product/architecture docs grilling. These are not installed external skills and do not override `AGENTS.md`.
- `.claude/skills/frontend-design/` - production-grade React/Vite dashboard UI standards and review checklist.
- `.claude/skills/finance-dashboard-ux-review/` - fintech-specific UX review for portfolio/options dashboards.
- `.claude/skills/implementation-plan-review/` - enforces single-task discipline against `docs/shared/implementation_plan.md`.
- `docs/shared/AGENT_REPORT_FORMAT.md` - canonical copyable prompt and report format. Agent prompts should be one fenced `text` block, not a markdown fence with nested code blocks.

Prefer invoking these explicitly when reviewing or designing UI, or when proposing/closing a plan task.

## Permissions and denied paths

`.claude/settings.local.json` denies reads and edits against secrets, generated data, broker exports, and document blobs. Treat any denial as a signal that the file is intentionally out of scope, not a problem to work around.

## What to do when a request feels out of scope

- If a request would require executing trades, scraping a broker, bypassing MFA, or touching credentials, decline and explain why.
- If a request would require touching `../TradingAgents`, propose an adapter approach in this repo instead.
- If a request spans multiple plan phases at once, propose the smallest first task and stop.
- If a request requires reading a denied file, ask the user for the specific information you need in a safe form instead of bypassing the rule.

## Commit and review behavior

- Do not commit automatically.
- After edits, list changed files and tests run, and propose a brief commit message the user can copy.
- Keep diffs small enough to review by eye.
