# Repo-Specific Agent Workflows

These workflows adapt useful patterns from external agent-skill systems into
Portfolio Copilot's own operating model. They are **not installed external
skills**, slash commands, GitHub issue workflows, or replacements for
`AGENTS.md`, `CLAUDE.md`, `docs/shared/AI_TEAM.md`, or
`docs/shared/implementation_plan.md`.

Repo docs remain authoritative. Active tasks stay in
`docs/shared/implementation_plan.md`; completed verification history stays in
`docs/shared/completed_phases_log.md`. Generic upstream conventions such as
`CONTEXT.md`, external issue trackers, alternate ADR folders, or broad
slash-command assumptions do not apply unless Codex A PM and Codex B explicitly
approve them later.

Finance, privacy, and product boundaries are hard constraints for every
workflow:

- no automatic trading, order placement, order cancellation, or destructive
  broker actions;
- no broker scraping, Fidelity credential storage, MFA bypass, or credential
  automation;
- no guaranteed-return, "safe to trade", "ready to trade", AI-picked, or
  "you should buy/sell" wording;
- no LLM-generated financial metrics;
- no raw holdings, raw positions, cash balances, buying power, account values,
  broker/provider ids, provider contract ids, raw provider payloads, trade
  journal entries, account-specific thresholds, secrets, prompts, provider
  traces, API keys, or access tokens in prompts, tests, docs, screenshots,
  frontend contracts, reports, logs, or review summaries;
- no real brokerage data, broker exports, local DB contents, generated reports,
  screenshots, logs, or `.env` files may be inspected by default.

## Workflow Selection

Use the smallest workflow that fits the task:

- Use `portfolio-frontend-contract-review` for Claude A frontend work, Claude B
  frontend review, or Codex B integration review of frontend/backend seams.
- Use `portfolio-backend-tdd-slice` for Codex C backend implementation tasks.
- Use `portfolio-grill-with-docs` before product/architecture roadmap changes,
  phase splits, or decisions that could duplicate docs or change task sources
  of truth.

Deferred workflow candidates are listed at the end of this file. Do not apply
or implement them yet.

## CodeGraph-First Context Rule

When CodeGraph is available, agents should use it before broad file reading:

- start implementation/review exploration with one focused `codegraph_explore`
  naming the relevant symbols, contract, route, component, or flow;
- use `codegraph_search` only to locate a specific symbol;
- use `codegraph_callers`, `codegraph_callees`, or `codegraph_impact` for
  dependency and blast-radius checks;
- read files directly only for changed files, directly related contracts/tests,
  or recently edited files that may not be indexed yet;
- do not ask Claude or Codex agents to read large source lists, archived docs,
  generated logs, or broad directories by default.

This rule exists to reduce session usage and avoid turning a narrow task into a
repo-wide audit. Prompts should name the CodeGraph exploration target and then
list only the task docs, changed files, and directly related tests.

## portfolio-frontend-contract-review

### Purpose

Prevent frontend/backend contract drift, prototype adoption mistakes, unsafe
finance language, and privacy leaks during frontend implementation or review.

### When To Use

- Phase 20A Modern Portfolio Desk prototype integration.
- Any Claude A frontend task that consumes backend schemas, API clients, or
  trade/agent review data.
- Any Claude B frontend safety/quality review.
- Any Codex B final integration signoff for frontend/backend seams.

### Owner Agents

- Primary implementer: Claude A.
- Safety/quality reviewer: Claude B.
- Architecture/integration reviewer: Codex B.
- Backend contract owner when fixes are needed: Codex C, only after a reviewed
  backend task exists.

### Required Docs To Read

Read only the current task scope and directly relevant files:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `docs/shared/current_roadmap.md`
4. `docs/shared/AI_TEAM.md`
5. the current task or handoff in `docs/shared/implementation_plan.md`
6. relevant backend schema/API contract files named by the task
7. relevant frontend API/type/component files named by the task
8. design prototype files only when the task explicitly references them

Do not load `docs/shared/completed_phases_log.md` unless historical
verification details are directly needed.

### Forbidden Inputs / Data

Do not inspect or use real brokerage data, `.env` files, local DB rows, broker
exports, generated reports, screenshots, logs, raw provider payloads, API keys,
or access tokens. Do not copy prototype JavaScript into the TypeScript frontend.
Do not introduce real-looking personal names, account names, cash values, or
policy strings as placeholders.

### Checklist

- Backend contracts:
  - frontend types mirror backend response schemas one-to-one;
  - no frontend-invented fields;
  - no ad hoc API clients for unimplemented backend paths;
  - existing endpoint paths remain unchanged unless the task explicitly changes
    the backend contract.
- Prototype integration:
  - prototype is treated as visual reference, not pasted implementation source;
  - translated components are TypeScript/React with typed props;
  - placeholder/demo cards are visibly labeled `demo · not yet connected`;
  - unsupported prototype fields are dropped or deferred.
- Financial/data boundaries:
  - no frontend financial computation;
  - numeric/backend values render from backend-owned fields only;
  - broker snapshot freshness and market quote freshness remain separate;
  - deterministic facts and LLM/agent commentary remain visually and
    structurally separate.
- Safety UX:
  - no order tickets, place/submit/confirm/cancel/execute controls, broker
    disconnect/delete controls, or execution-style flows;
  - no "safe to trade", "ready to trade", guaranteed-return, AI-picked, or
    "you should buy/sell" wording;
  - severity, freshness, and actionability use icon plus text, never color
    alone.
- Browser/storage/network hygiene:
  - no new `localStorage` or `sessionStorage` keys except approved UI-only keys;
  - Trade Review uses only approved trade-review endpoints;
  - Agent Console uses only the approved agent-team preview endpoint;
  - no frontend calls to SnapTrade, brokers, market providers, LLM providers,
    TradingAgents, or external APIs.
- Preview verification:
  - data-backed pages (`/account-details`, Agent Console success states,
    Dashboard account panels, broker/market pages) need the **full stack** —
    Postgres + backend + the local dev user/account data — not just the
    frontend. See `Full-stack preview for data-backed pages` below. A
    frontend-only start renders the app shell but cannot show connected data.
  - if the stack cannot start, or backend `/users` / proxy `/api/users` does not
    return the local dev user, report that blocker and do not describe the smoke
    as a complete data-state preview.

## Full-stack preview for data-backed pages

Do not trust `.claude/launch.json` or a tool label such as `frontend` as proof
that a preview is full-stack. Some preview tools start only a standalone Vite
frontend. That can render the shell but fail every connected-data request.

For `/account-details` and other data-backed pages, the required proof is the
probe sequence below: Postgres is up, backend is healthy, backend `/users`
returns the local dev user, frontend proxy `/api/users` returns the same local
dev user, and the route renders connected data. If any probe fails, report a
preview blocker instead of judging the page's data state.

Standard command sequence (run from the repo root):

```bash
cd /Users/wulingyun/Desktop/Trading_Agents_Projects/portfolio-options-agent
docker compose up -d postgres backend frontend
curl -i http://localhost:8000/health     # backend liveness
curl -i http://localhost:8000/users      # backend direct route (authed dev user)
curl -i http://localhost:5173/api/users  # Vite proxy → same backend route
```

Then open the real route in a browser:

```
http://localhost:5173/account-details
```

Success conditions (all must hold before trusting a data-state smoke):

- `http://localhost:8000/health` returns `200`;
- backend `http://localhost:8000/users` returns the local dev user;
- Vite proxy `http://localhost:5173/api/users` returns the **same** local dev
  user (confirms the proxy is forwarding with the dev access token);
- `http://localhost:5173/account-details` renders connected account data — the
  account rail and selected-account detail — not only the shell.

Route difference (do not get fooled by this):

- backend direct route is `/users` (no `/api` prefix);
- frontend / Vite proxy route is `/api/users` (the proxy strips `/api` and adds
  the local dev access-token header before forwarding to the backend);
- `http://localhost:8000/api/users` will typically `404` — that is expected and
  **not** an app failure. Use `http://localhost:8000/users` against the backend
  and `http://localhost:5173/api/users` against the proxy.

Warning — Claude Preview vs the Docker frontend:

- The Docker `frontend` service is the safest default for data-backed pages
  because it runs with the local dev proxy configuration expected by the repo.
- If a review tool insists on starting a standalone Claude Preview / Vite
  process, keep Docker `postgres` and `backend` running and verify the Vite proxy
  can read the local dev token (for example through the approved, gitignored
  `frontend/.env.local` path). Do not read or print that token.
- Do not stop the Docker frontend just to run a frontend-only preview unless the
  preview is started with equivalent proxy configuration and the probes above
  pass. If `/api/*` returns `401`, the preview is not a valid connected-data
  smoke.

Copyable Preview Review Instruction (paste into Claude B / Codex F visual-review
prompts for data-backed pages):

```text
Preview (full stack required — frontend-only is insufficient for connected data):
  cd /Users/wulingyun/Desktop/Trading_Agents_Projects/portfolio-options-agent
  docker compose up -d postgres backend frontend
  curl -i http://localhost:8000/health     # expect 200
  curl -i http://localhost:8000/users      # backend route → dev user
  curl -i http://localhost:5173/api/users  # proxy route → same dev user
Then open: http://localhost:5173/account-details
Expect: account rail + selected-account detail render with connected data, not just the shell.
Notes:
  - Backend route is /users; frontend/proxy route is /api/users.
  - http://localhost:8000/api/users may 404 — that is expected, not a failure.
  - Do NOT judge connected-data UI from a frontend-only preview unless the
    /api/users proxy probe passes; a standalone Vite process without the local
    dev token returns 401 and only proves the route shell can render.
```

### Expected Output Format

For reviews, use:

1. `PASS` or `BLOCKED`
2. Blockers
3. Important issues
4. Deferred polish
5. Suggested fixes with file/line references where practical
6. Test/build/browser checks run
7. Recommendation for whether the next task may start

For implementation prompts to Claude A, include:

- exact task id and scope;
- allowed files;
- backend contracts that must remain unchanged;
- prototype fields to adopt vs drop;
- safety/product boundaries;
- required checks.

### Review Gate

Claude B should review safety/UX and implementation quality before Codex B final
signoff when frontend changes affect finance wording, API data rendering, or
the app shell. Codex B owns final architecture/integration readiness when
contracts, state shape, or cross-layer boundaries are involved.

### Implementation-Plan Update Rule

Claude A may propose verification notes for the current task. The task should
only be marked `done` after acceptance criteria, typecheck/lint/build, and the
required review gate are complete. If a backend contract is missing, add or
reference a future Phase 20B task instead of inventing frontend fields.

### What Not To Do

- Do not broaden Phase 20A into backend implementation.
- Do not create fake connected data to satisfy prototype fidelity.
- Do not normalize broker and market freshness into one generic readiness
  value.
- Do not use frontend code to calculate risk, readiness, allocation,
  collateral, cash impact, or portfolio metrics.
- Do not ask review agents to inspect real brokerage screens or payloads.

## portfolio-backend-tdd-slice

### Purpose

Keep Codex C backend work small, test-first, contract-safe, synthetic, and tied
to the next visible product capability.

### When To Use

- Any new backend API route, schema, mapper, service, provider adapter, or
  persistence slice.
- Phase 20B backend read-contract tasks.
- Agent-team, LLM-provider, market-data, report, or broker adapter changes.

### Owner Agents

- Primary implementer: Codex C.
- Architecture/task owner: Codex B.
- Backend safety/QA reviewer: Claude B.
- Frontend consumer reviewer when applicable: Claude A or Codex B.

### Required Docs To Read

1. `AGENTS.md`
2. `docs/shared/current_roadmap.md`
3. `docs/shared/AI_TEAM.md`
4. `docs/shared/TASKS.md`
5. the exact task in `docs/shared/implementation_plan.md`
6. relevant architecture contract or ADR
7. directly related source files and tests

### Forbidden Inputs / Data

Use synthetic fixtures only. Do not inspect `.env`, secrets, real brokerage
data, local DB contents, broker exports, generated reports, screenshots, logs,
provider raw payloads, or `../TradingAgents`. Default tests must not call
SnapTrade, brokers, market-data providers, LLM providers, TradingAgents, or
external APIs.

### Checklist

- Scope:
  - implement one task only;
  - keep the route/service/schema surface minimal;
  - do not run backend phases far ahead without a frontend/review surface.
- Tests first-class:
  - add or update unit/service tests for core behavior;
  - add API tests for new or changed routes;
  - add forbidden-field tests for every frontend/public response shape;
  - add failure-path tests for provider, freshness, missing-data, and
    validation cases;
  - mark external/slow tests so they do not run by default.
- Contract safety:
  - use typed schemas with `extra="forbid"` where appropriate;
  - keep provider selection, freshness, actionability, prompts, credentials,
    and private metadata server-owned;
  - return display-ready labels/statuses where frontend should not calculate;
  - preserve broker vs market vs agent/provider freshness distinctions.
- Privacy/security:
  - use shared forbidden-field constants where they exist;
  - do not expose raw private data, secrets, prompts, traces, provider ids, or
    account-specific thresholds;
  - sanitize errors before returning them to frontend or reports.
- Reliability:
  - provider failures degrade to safe partial/unavailable outputs where the
    architecture requires it;
  - deterministic review remains available when optional providers fail;
  - default app startup and default tests work without optional providers.

### Expected Output Format

For Codex C handoffs or completion notes:

1. Task id and short summary
2. Files changed
3. Schema/API contract summary
4. Privacy/safety boundaries preserved
5. Tests run with exact commands and summary lines
6. Deferred items or open questions
7. Recommendation for review gate

### Review Gate

Claude B reviews backend safety, tests, privacy, reliability, and maintainability.
Codex B reviews architecture/API/data-contract alignment before frontend work
consumes new fields. High-risk provider, finance, migration, or security changes
may require an Opus-level review prompt.

### Implementation-Plan Update Rule

After a backend task, update only the current task's verification notes and
status. Do not mark downstream tasks done. If a required frontend or architecture
follow-up appears, add it as a blocked/not-started task or ask Codex B to update
the plan.

### What Not To Do

- Do not call live providers in default tests.
- Do not use real brokerage or account data in tests or examples.
- Do not add broad dashboard blobs when a narrow typed endpoint will do.
- Do not let clients supply provider/model/prompt/freshness/actionability.
- Do not put API keys or secrets in frontend-visible schemas.
- Do not implement broker actions, order management, or destructive flows.

## portfolio-grill-with-docs

### Purpose

Stress-test product and architecture decisions before roadmap changes, phase
splits, new backend contracts, provider integrations, or workflow changes create
scope drift or duplicate documentation.

### When To Use

- Before starting a new phase or reactivating a frozen phase.
- Before adding real provider calls, market data, auth, reports, persistence,
  broker activities, or deep TradingAgents execution.
- When Codex A/Codex B disagree or when the founder's desired product identity
  conflicts with the current plan.
- When docs are messy or the source of truth is unclear.

### Owner Agents

- Product decision owner: Codex A.
- Architecture decision owner: Codex B.
- Implementation input: Codex C or Claude A/B only when directly relevant.

### Required Docs To Read

1. `AGENTS.md`
2. `CLAUDE.md` when Claude work is affected
3. `docs/shared/current_roadmap.md`
4. `docs/shared/AI_TEAM.md`
5. `docs/shared/TASKS.md`
6. relevant phase/task sections in `docs/shared/implementation_plan.md`
7. relevant product docs under `docs/codex-a-product/`
8. relevant architecture docs/ADRs under `docs/codex-b-architecture/`

Do not use chat memory to override repo docs. If docs conflict, surface the
conflict.

### Forbidden Inputs / Data

No secrets, `.env`, real brokerage data, local DB rows, generated reports,
screenshots, logs, broker exports, or raw provider payloads. Use synthetic
examples only. Do not inspect `../TradingAgents` unless the task explicitly
allows architectural reference, and never copy source code from it.

### Checklist

- Decision clarity:
  - what decision is being made;
  - who owns it;
  - what phase/task it affects;
  - whether it changes product scope, architecture, data model, API contracts,
    UI scope, safety boundaries, or review gates.
- Docs alignment:
  - current roadmap matches implementation plan;
  - task source of truth remains `docs/shared/implementation_plan.md`;
  - completed work is not left in the active plan;
  - ADRs exist or are proposed for durable architecture decisions;
  - no duplicate docs/processes are introduced.
- Product safety:
  - no execution/advice/guarantee scope drift;
  - deterministic metrics remain backend-owned;
  - LLM/agent outputs remain explanatory and bounded;
  - privacy constraints remain stricter than generic upstream skill defaults.
- Delivery shape:
  - smallest safe vertical slice is identified;
  - implementation order is clear;
  - owner/reviewer gates are clear;
  - frontend does not wait unnecessarily, but does not invent fields.

### Expected Output Format

1. Decision question
2. Current docs/source-of-truth finding
3. Options considered
4. Recommended decision
5. Scope and non-goals
6. Required docs/ADR updates
7. Owner handoffs
8. PASS / BLOCKED / RESCOPE recommendation

### Review Gate

Codex A decides product scope and roadmap priority. Codex B decides architecture,
API/data boundaries, ADR needs, and integration sequence. Do not ask Codex C or
Claude A to implement until Codex A/B have resolved product/architecture
questions.

### Implementation-Plan Update Rule

If a decision is accepted, update the active plan with task ids, dependencies,
expected files, implementation steps, acceptance criteria, tests, rollback
notes, and status. Do not move active planning into GitHub Issues unless a later
PM decision changes the source of truth.

### What Not To Do

- Do not create a parallel `CONTEXT.md` or external issue-tracker source of
  truth.
- Do not use generic upstream workflow assumptions to override this repo's
  finance/privacy constraints.
- Do not turn a product decision into a broad repo review.
- Do not reactivate frozen work by implication.

## Deferred Workflow Candidates

The following patterns may be useful later but are not approved workflows yet:

- `portfolio-diagnose`: structured bug/regression diagnosis with a reproducible
  feedback loop before patching.
- `portfolio-architecture-deepening`: periodic architecture simplification and
  module-boundary review.
- `to-issues`: conversion from implementation-plan tasks into GitHub Issues if
  the team later decides to use issues as a secondary tracker.
- `zoom-out`: periodic strategic review of whether the roadmap still matches
  the product north star.
- `prototype`: throwaway experiment workflow for isolated prototypes only, not
  production frontend integration.

Do not implement or invoke these as formal workflows until Codex A PM and Codex
B approve their scope and location.
