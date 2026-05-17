# AGENTS.md

Rules for coding agents working in `portfolio-options-agent`.

## Project Boundary

- This repository is an independent project. Do not modify `../TradingAgents` as part of routine work here.
- Prefer wrappers, adapters, and new modules over modifying TradingAgents core.
- Do not copy TradingAgents source code into this repository.
- Do not vendor TradingAgents as a subfolder.
- Do not add a git submodule unless explicitly requested.

## Safety Rules

- Do not store API keys, access tokens, broker credentials, or secrets in code.
- Do not commit real account data, real reports, real trades, broker CSVs, statements, transactions, or private configs.
- Do not implement broker scraping.
- Do not scrape Fidelity or any broker through browser automation.
- Do not bypass MFA or automate credential entry.
- Do not implement automatic trading or broker order execution.
- Do not present outputs as guaranteed financial advice.
- Do not rely on LLMs for deterministic financial calculations. Use explicit, testable code for calculations.

## Engineering Rules

- Keep changes small, focused, and reviewable.
- Before major edits, inspect the relevant files and explain the plan.
- Add tests for behavior changes when practical.
- Keep examples synthetic. Never use real holdings, real thresholds, real account values, or real user data.
- After edits, list changed files and tests run.

## Secret Handling Rules

- Never read, open, print, summarize, modify, or expose `.env`, `.env.*`, broker credential files, private configs, API keys, or access tokens.
- Use `.env.example` only to document variable names with placeholder values.
- If a command requires real credentials, tell the user exactly what command to run locally instead of trying to inspect secrets.
- Do not log API keys, broker data, account values, real reports, or private strategy parameters.
- Never put API keys in frontend code.

## Real Brokerage Data Access Rules

This project may connect to real read-only brokerage data through SnapTrade. Treat all synced brokerage data as private user data.

- Do not read, print, summarize, export, screenshot, query, or inspect real brokerage data unless the user explicitly grants narrow permission for that specific diagnostic action.
- Protected brokerage data includes account names, account numbers, provider account IDs, balances, buying power, cash, holdings, quantities, positions, cost basis, option positions, transaction history, statements, broker sync payloads, reports, screenshots, database dumps, generated logs, SnapTrade user IDs, SnapTrade user secrets, portal URLs, access tokens, and API keys.
- Do not query a local database, API endpoint, browser screen, log file, report, or generated artifact if it may contain real brokerage holdings, balances, transactions, account identifiers, or provider raw payloads.
- Do not call live SnapTrade, Fidelity, broker, market-data, or LLM APIs unless the active task explicitly requires it and the user confirms the real-data access boundary.
- Prefer source-code review, schemas, synthetic fixtures, mocked API responses, redacted examples, and UI layout with fake/demo data.
- Never paste real brokerage values into docs, tests, fixtures, prompts, commits, screenshots, examples, logs, or responses.
- If a task appears to require real brokerage data, stop and ask for explicit permission. State exactly what data would be accessed and prefer a redacted or synthetic alternative.

## Implementation Loop Rule

- For multi-step work, maintain `docs/implementation_plan.md`.
- Each task in `docs/implementation_plan.md` must include task id, objective, expected files, dependencies, implementation steps, acceptance criteria, tests, rollback notes, and status.
- Implement only one task at a time unless explicitly told otherwise.
- After each task, update `docs/implementation_plan.md`.
- Stop for review after each task.

## Context Efficiency Rules

- Prefer `docs/current_roadmap.md` for high-level project direction.
- Prefer `docs/agent_context/codex_working_context.md` before implementation tasks.
- Prefer `docs/agent_context/opus_review_brief.md` for high-stakes Claude Opus reviews.
- Keep `docs/implementation_plan.md` focused on active and future tasks.
- Keep completed verification history in `docs/completed_phases_log.md`.
- Do not load `docs/completed_phases_log.md` unless historical verification details are directly relevant.
- Do not ask Claude or another review agent to perform broad repo-wide reviews by default.
- For Claude review prompts, provide a strict read whitelist with only the current task docs, changed files, and directly related tests.
- Use Opus only for high-risk architecture, finance semantics, schema/migration, broker/security, or disagreement-resolution reviews.
- Use Sonnet for normal code review, frontend UI/UX, copy, accessibility, and implementation-plan scope checks.

## Testing Rules

- Treat the backend test framework as production engineering infrastructure, not as throwaway scaffolding.
- Use `pytest` as the default backend test runner.
- Default backend test command: `cd backend && pytest`.
- If the global `pytest` command is broken by local machine plugins or Python installation issues, use the project virtual environment command: `cd backend && ./.venv/bin/python -m pytest`.
- Keep tests fast, deterministic, isolated, and synthetic by default.
- Prefer the test pyramid: many unit tests, focused service tests, API tests for route contracts, database/migration tests for persistence boundaries, and only a small number of explicit integration tests.
- Register and use pytest markers consistently: `unit`, `api`, `db`, `migration`, `integration`, `external`, `slow`, `regression`, `adapter`, and `smoke`.
- `external` and `slow` tests must not run by default.
- Run relevant tests after behavior changes.
- Any deterministic finance calculation must have unit tests.
- Any API route should have API tests.
- Any database schema change should include migration verification.
- Any bug fix should include a regression test.
- Any adapter boundary should have mocked adapter/contract tests before real integration tests.
- External API tests must be mocked by default.
- LLM calls must be mocked by default.
- TradingAgents adapter tests must be mocked by default unless explicitly marked `integration` or `external`.
- Broker, market-data, LLM-provider, and TradingAgents tests must not make network calls in the default test suite.
- Do not use real broker exports, real account data, real reports, or real credentials in fixtures.
- Tests must not require real OpenAI, Claude, Gemini, Tradier, Alpaca, Fidelity, broker, or market-data credentials.
- Tests must use synthetic data only.
- Do not use real holdings, real account values, real reports, real broker files, or real strategy thresholds in tests.
- Keep test fixtures small, reusable, and explicit.
- Prefer clear Arrange-Act-Assert test structure.
- Avoid brittle assertions that depend on wall-clock time, external market state, network availability, API rate limits, or provider-specific response ordering.
- Use monkeypatching, fakes, or dependency injection for external boundaries.
- API tests should verify status codes, response shape, important validation failures, and permission/ownership behavior.
- Database tests should clean up after themselves and must not depend on data left by previous tests.
- If database migrations are involved, explain Alembic commands and test migration upgrade/downgrade when practical.
- If a command cannot be run, explain why and provide the exact command for the user to run.
- Do not claim tests passed unless they were actually run.

## Git Hygiene Rules

- Start by checking `git status` when making changes.
- Keep diffs small.
- Do not commit automatically.
- Do not create large unrelated refactors.
- Do not modify generated/private data.
- After edits, summarize changed files and tests run.

## Task Scope Rules

- Do not build multiple phases in one pass.
- Do not implement frontend, backend, database, agent adapter, and market data all at once.
- Prefer small sequential tasks:
  1. `docs/implementation_plan.md`
  2. Docker Compose Postgres
  3. backend config loading
  4. SQLAlchemy session
  5. Alembic setup
  6. users/accounts schema
  7. portfolio core
  8. deterministic option formulas
  9. report history
  10. TradingAgents adapter
- If the requested task is too broad, propose a smaller first task before coding.
