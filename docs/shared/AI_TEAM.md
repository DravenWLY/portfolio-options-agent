# AI Team Operating Model

## Project Goal

Portfolio Copilot is a broker-connected, read-only portfolio-aware trade review and risk copilot for manual investors. It connects to broker portfolio snapshots through SnapTrade or future provider adapters, normalizes stock/ETF/options holdings, runs deterministic portfolio/risk calculations, and produces educational review/report outputs.

The product is not an automated trading system, broker scraper, market-data terminal, option-chain browser, or thin TradingAgents wrapper. Human users remain responsible for any real trades placed outside the app.

## Source of Truth

Repo docs are the source of truth over chat memory.

Read in this order unless a task says otherwise:

1. `AGENTS.md` and `CLAUDE.md` for safety and task discipline.
2. `docs/shared/current_roadmap.md` for current direction.
3. `docs/shared/AI_TEAM.md` for agent ownership.
4. `docs/shared/TASKS.md` for active task routing.
5. `docs/shared/implementation_plan.md` for task-level specs.
6. `docs/codex-b-architecture/architecture.md` for full architecture context.
7. `docs/shared/completed_phases_log.md` only when historical verification details are directly needed.

If docs conflict, stop and surface the conflict. Do not silently use chat memory to override repo docs.

## Active Agents and Ownership

### Codex A - Product / Founder Strategy / PM

Owns:

- Product definition, MVP scope, positioning, roadmap, user value, success metrics, feature priority, and scope boundaries.
- Product-facing docs such as `docs/codex-a-product/PRD.md`, `docs/codex-a-product/MVP_SCOPE.md`, `docs/codex-a-product/ROADMAP.md`, `docs/codex-a-product/POSITIONING.md`, `docs/codex-a-product/FEATURE_PRIORITY.md`, and `docs/codex-a-product/METRICS.md` when created.

Does not own:

- Backend implementation details, database migrations, API route code, frontend component implementation, or security sign-off.

Reads first:

- `docs/codex-a-product/PM_ONBOARDING_PROMPT.md`
- `docs/codex-a-product/PM_HANDOFF.md`
- `docs/shared/current_roadmap.md`
- `docs/codex-b-architecture/architecture.md` sections on product north star, trade intent, roadmap, and safety.

### Codex B - Architecture / Tech Lead

Owns:

- System architecture, component boundaries, API contracts, data model direction, ADRs, integration plans, and architecture-level review of frontend/backend seams.
- Review of Claude frontend work when it affects contracts, state management, API shape, or integration boundaries.

Does not own:

- Product-market positioning, visual design details, or routine backend implementation.

Reads first:

- `docs/codex-b-architecture/ARCHITECTURE_HANDOFF.md`
- `docs/shared/current_roadmap.md`
- `docs/codex-b-architecture/architecture.md`
- relevant sections of `docs/shared/implementation_plan.md`

### Codex C - Backend Implementation

Owns:

- Backend coding, broker provider adapters, database implementation, API implementation, background jobs if introduced, backend tests, deterministic calculation services, backend reliability, and implementation according to approved product/architecture docs.

Does not own:

- Final product scope, broad roadmap tradeoffs, visual design, competitor strategy, production infrastructure, or compliance sign-off. Codex C may flag risks and propose options, but PM/Architecture/Security decide.

Reads first:

- `docs/codex-c-backend/WORKING_CONTEXT.md`
- `docs/shared/current_roadmap.md`
- the current task section in `docs/shared/implementation_plan.md`
- relevant backend source and tests

### Claude A - Frontend UI/UX Design

Owns:

- Frontend flows, dashboard design, information hierarchy, report readability, loading/error/empty states, visual design, accessibility, and trust/security messaging from a UX perspective.

Does not own:

- Backend persistence, SnapTrade secrets, database migrations, deterministic finance calculations, or hidden product scope expansion.

Reads first:

- `docs/shared/current_roadmap.md`
- frontend README and changed frontend files
- relevant backend API contracts/schemas
- `docs/shared/AI_TEAM.md`

### Claude B - Code Review / QA / Security Review for Codex Work

Owns:

- Review of Codex backend implementation, QA checklist, test coverage, error handling, secret leakage risk, API contract consistency, maintainability, and financial-advice wording risk.

Does not own:

- Large implementation changes unless explicitly asked. Review output should be adjudicated by Codex C or Codex B before implementation.

Reads first:

- changed files and directly related tests
- relevant `docs/shared/implementation_plan.md` task section
- `docs/shared/AI_TEAM.md`
- relevant skills or review checklists

### Claude C - Competitor / Product Intelligence

Owns:

- Competitor analysis, feature matrix, differentiation, pricing/positioning comparison, and product opportunity recommendations to Codex A PM.

Does not own:

- Direct implementation authority, architecture decisions, or scope expansion without PM approval.

Reads first:

- `docs/shared/current_roadmap.md`
- future PM docs such as `docs/codex-a-product/PRD.md`, `docs/codex-a-product/POSITIONING.md`, and `docs/codex-a-product/MVP_SCOPE.md`

## Future Agents

### Codex D - DevOps / Production Readiness

Owns future deployment, CI/CD, Docker/build pipeline, staging/production separation, environment variables, health checks, logging/monitoring, rollback, and launch checklist.

Reads first:

- `docs/codex-d-devops/DEVOPS_READINESS_DRAFT.md`
- `README.md`
- `docker-compose.yml`
- backend and frontend setup docs

### Claude D - Security / Compliance / Privacy

Owns future threat model, broker-data handling policy, privacy/security review, data deletion/export, financial disclaimer, access control, and compliance-oriented product language.

Reads first:

- `docs/claude-d-security/SECURITY_COMPLIANCE_DRAFT.md`
- `AGENTS.md`
- `CLAUDE.md`
- security-relevant backend schemas/services

## Required Handoff Format

Every handoff between agents should include:

- Task name and phase/task id if applicable.
- Goal and non-goals.
- Files to read.
- Files changed or expected to change.
- Safety boundaries, especially broker data and secret handling.
- Decisions already made.
- Open questions.
- Tests or checks run.
- PASS/BLOCKED status for reviews.
- Suggested next owner.

Keep handoffs scoped. Do not ask another agent for a broad repo-wide review unless the task is explicitly a milestone review.

## Architecture Change Rules

Architecture changes require Codex B review when they affect:

- Cross-layer boundaries.
- Database schema or migrations.
- API contracts.
- Broker provider abstraction.
- Market data abstraction.
- Agent/LLM boundaries.
- Security/privacy assumptions.
- Financial calculation semantics.

Use an ADR when a decision is hard to reverse, affects multiple phases, or changes an external boundary. ADRs should state context, decision, alternatives considered, consequences, and rollback/deferral notes.

## Implementation Agent Rules

Implementation agents should:

- Implement one task at a time.
- Use `docs/shared/implementation_plan.md` task specs.
- Keep diffs small and focused.
- Use synthetic tests and fixtures.
- Never inspect real brokerage data unless narrowly authorized.
- Never add trade execution or broker-destructive behavior.
- Update verification notes after the task.

Implementation agents should not:

- Make PM/product decisions by default.
- Reframe the roadmap without PM/Architecture approval.
- Put secrets, account values, provider ids, or real holdings into docs/tests/prompts.

## Review Agent Rules

Review agents should:

- Lead with blockers and important issues.
- Distinguish correctness, safety, polish, and deferrals.
- Cite file paths and lines where practical.
- Recommend precise fixes.
- Avoid broad refactors unless the task is explicitly architecture review.

Review agents should not:

- Modify code during a read-only review.
- Use real brokerage data for verification.
- Treat stale broker snapshots as live data.

## Sensitive Financial and Brokerage Data Rules

All agents must treat real brokerage data as private user data.

Do not read, print, summarize, export, screenshot, query, or inspect:

- `.env` or `.env.*`
- API keys, access tokens, broker credentials, SnapTrade user secrets, portal URLs
- real account names/numbers, balances, buying power, cash, holdings, quantities, cost basis, option positions
- provider account ids, provider connection ids, provider raw payloads
- real reports, broker CSVs, statements, transactions, imports, exports, PDFs, or XLS/XLSX files

Prefer synthetic fixtures, mocked API responses, source-code review, and redacted examples.

## Educational Financial Language Rules

Use:

- "review", "scenario analysis", "risk factors", "manual decision support"
- "based on the available snapshot"
- "not market price" or "market quote freshness separate" where applicable

Avoid:

- "you should buy/sell"
- "safe to trade"
- "guaranteed return"
- "live portfolio" unless provider-verified
- "fully covered" or "cash secured" unless deterministic coverage/collateral modelling supports the claim

## Engineering Review Framework Usage

The project uses `docs/shared/ENGINEERING_REVIEW_FRAMEWORK.md` as the shared engineering quality bar.

Agents should use it differently depending on role:

- Product / PM Agent: product definition, user value, audience communication, metrics, experimentation, and scope control.
- Architecture / Tech Lead Agent: life of request, component boundaries, API design, data model, compatibility, scalability, concurrency, and evolution.
- Backend Implementation Agent: use selectively; daily implementation should mainly follow `docs/shared/TASKS.md`, API contracts/schemas, data model docs, security rules, and changelog notes.
- Frontend UI/UX Agent: audience communication, latency/user experience, error states, product clarity, and trust messaging.
- Code Review / QA / Security Agent: reliability, testing, security, privacy, documentation, handoff readiness, and maintainability.
- DevOps / Production Readiness Agent: CI/CD, deployment, observability, reliability, health checks, rollback, environment variables, and cost.
- Security / Compliance / Privacy Agent: security/privacy, sensitive data handling, logging, access control, financial disclaimer, and compliance-related product language.

Apply the framework deeply during architecture reviews, milestone reviews, launch-readiness reviews, security reviews, and production-readiness reviews. Do not overcomplicate every small implementation task by applying every framework section mechanically.
