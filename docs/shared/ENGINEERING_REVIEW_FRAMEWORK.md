# Engineering Review Framework

Status: shared quality framework
Owner: cross-agent process
Last updated: 2026-05-20

## Purpose

This framework is the project-wide quality bar for turning Portfolio Copilot into a maintainable, deployable, evolvable service. It is not a one-off review prompt. Apply it across product definition, architecture, implementation, review, release readiness, operations, and future maintenance.

Use it to keep each change aligned with the product thesis:

Portfolio Copilot is a TradingAgents-inspired, read-only, portfolio-aware trade review agent team for manual investors. TradingAgents-inspired does not mean TradingAgents-centered: the product center remains broker-aware `TradeIntent` review. It must not drift into automated trading, broker scraping, generic market-data viewing, options-income screening, AI stock picking, or a thin TradingAgents wrapper.

## How To Apply

Apply the full framework for:

- Product or architecture milestones.
- Phase exits and integration reviews.
- Security, privacy, broker-data, or LLM-boundary reviews.
- Production or paid-beta readiness.
- Major handoffs between agents.
- Decisions that affect API contracts, persistence, external providers, financial semantics, or user trust.

Apply only the relevant sections for:

- Small backend implementation tasks.
- Focused frontend UI slices.
- Documentation cleanup.
- Test-only changes.
- Narrow bug fixes.

Small tasks should still respect the same principles, but they do not need a full 21-section writeup.

## Lifecycle Gates

| Stage | Required review lens | Output |
| --- | --- | --- |
| Product definition | User value, target audience, MVP scope, non-goals, success metrics | PRD, MVP scope, feature priority, metrics |
| Architecture planning | Request lifecycle, boundaries, API/data contracts, evolution risk | Architecture docs, ADRs, handoff notes |
| Implementation planning | Task scope, dependencies, tests, rollback, safety boundaries | Implementation plan task |
| Backend implementation | Correctness, deterministic calculations, privacy, tests, error handling | Focused code change and verification notes |
| Frontend implementation | Workflow clarity, trust messaging, loading/error/empty states, accessibility | UI slice and contract check |
| Review / QA | Bugs, regressions, missing tests, privacy leaks, misleading language | PASS/BLOCKED findings |
| Release readiness | CI/CD, observability, rollback, data handling, supportability | Launch checklist |
| Operations / evolution | Metrics, incidents, cost, drift, maintenance burden | Roadmap updates and follow-up tasks |

## Core Review Dimensions

### 1. Product Definition And User Value

Every feature should answer:

- What user problem does this solve?
- Which target user needs it now?
- Does it improve portfolio-aware pre-trade review?
- What is core, what is nice-to-have, and what is explicitly out of scope?
- Which success metric would improve if this worked?

For this project, user value is not "more financial data on screen." User value is a trustworthy answer to: "What changes in my portfolio if I manually place this trade elsewhere?"

### 2. Audience And Communication

The product must be explainable to:

- A self-directed investor.
- A teammate or future maintainer.
- A technical reviewer.
- A potential investor or hiring manager.
- A security/compliance reviewer.

Use language such as "review", "scenario analysis", "risk factors", and "manual decision support." Avoid "safe to trade", "you should buy/sell", "guaranteed return", and "live portfolio" unless the provider and policy truly support it.

### 3. System Design And Life Of Request

For important flows, describe:

- Where the request starts in the frontend.
- Which API endpoint or service receives it.
- What validation runs.
- What deterministic business logic runs.
- Which database, cache, broker, market-data, or LLM boundary is touched.
- What response is returned.
- What can fail.
- How the user sees success, loading, empty, stale, blocked, and error states.

The most important flow is proposed `TradeIntent` to deterministic review to report/agent-safe explanation.

### 4. Architecture And Component Boundaries

Keep responsibilities clear:

- Frontend renders workflows and trust states.
- Backend owns broker integration, persistence, deterministic calculations, actionability, and safe API contracts.
- Broker providers supply read-only account snapshots only.
- Market-data providers supply quote/chain snapshots with separate freshness.
- LLMs explain structured facts; they do not calculate metrics or receive private brokerage data by default.
- TradingAgents is optional async public ticker/company research evidence, not the decision engine.

### 5. API Design

API contracts should be:

- Explicitly named.
- Versionable or evolvable.
- Consistent in request/response shapes.
- Clear about validation errors and ownership failures.
- Safe for frontend/backend parallel work.
- Free of provider secrets, raw payloads, account ids, and private values unless explicitly required and reviewed.

Important trade-review APIs must distinguish deterministic facts, freshness/actionability status, optional AI explanation, and optional research evidence.

### 6. Data Model And Persistence

Data models should reflect real usage patterns:

- Users and accounts.
- Broker connections and broker accounts.
- Cash, stock/ETF positions, option contracts, option positions.
- Market quote and option quote snapshots.
- Trade intents, deterministic reviews, risk-rule violations.
- Report threads, messages, agent runs, and agent steps.

Persist calculation versions, freshness snapshots, and enough structured context to audit reports without storing secrets or unnecessary raw broker payloads.

### 7. Data Format And Compatibility

Structured data should tolerate evolution:

- Add optional fields without breaking old clients.
- Keep enums documented and tested.
- Preserve old reports even when schemas evolve.
- Use sanitized read schemas for frontend and agent exposure.
- Keep provider-specific raw fields behind internal boundaries.

### 8. Latency And User Experience

Review perceived latency for each flow:

- Fast local validation should feel immediate.
- Broker sync and market-data fetches need visible progress or background status.
- Agent/report composition should show step state if it takes noticeable time.
- Independent provider calls should not be serialized unnecessarily.

Do not make users wonder whether stale data is still being used.

### 9. Reliability And Failure Handling

Assume every dependency can fail:

- Database unavailable.
- Broker provider timeout.
- Market-data provider rate limit.
- LLM unavailable.
- Background job crash.
- Invalid or duplicate user input.
- Partial sync success.

Failures should degrade gracefully, avoid private data leakage, and surface clear user-facing states such as unavailable, stale, analysis-only, manual confirmation required, or blocked.

### 10. Service Etiquette And Dependency Management

External calls should use:

- Timeouts.
- Bounded retries.
- Rate-limit awareness.
- Clear error categories.
- Health/status reporting.
- Mocked default tests.

Never make default tests require real broker, market-data, LLM, or TradingAgents credentials.

### 11. Complexity Control

Prefer narrow vertical slices. Delay features that do not improve the core pre-trade review job.

Watch for:

- Too many features in one phase.
- Strategy-specific schemas becoming core architecture.
- Hidden frontend/backend coupling.
- Duplicated finance logic.
- Overbroad provider abstractions.
- LLM prompt complexity hiding deterministic gaps.
- Research/screener scope replacing review workflow.

### 12. Scalability And Cost

Do not overbuild early, but design carefully around expensive future changes:

- Broker sync state and provider metadata.
- Report/agent history growth.
- Market quote caching and provider costs.
- Background jobs for longer agent/research work.
- Secrets management and environment separation.

Streaming, OPRA redistribution, multi-provider breadth, and production-scale infrastructure are not MVP needs.

### 13. Concurrency And Execution Model

Review:

- Idempotent broker sync and import operations.
- Duplicate trade-review submissions.
- Background job checkpointing.
- Race conditions in refresh/report generation.
- Shared provider clients and rate limits.
- Database transaction boundaries.

Avoid blocking request handlers on long external or LLM calls when a job model is more appropriate.

### 14. Metrics And Observability

Track product metrics:

- Review completion.
- Repeat review usage.
- Usefulness/clarity rating.
- Stale-data guardrail hits.
- Manual confirmation behavior.
- Paid-beta conversion signal.

Track system metrics:

- API latency and error rate.
- Broker sync success/failure.
- Market-data timeout/error rate.
- Background job failures.
- Database latency.
- CI/test status.

Do not log raw holdings, balances, account values, provider ids, report text, prompt text, raw provider payloads, or secrets.

### 15. Experimentation And Product Decisions

Identify assumptions before expanding scope:

- Does the target user pay for portfolio-aware pre-trade review?
- Is broker sync required for beta, or can manual/CSV prove value first?
- Which trade flows create repeat usage?
- Does AI explanation increase clarity without reducing trust?
- Do freshness warnings change user behavior?

Use metrics and user feedback, but require PM/architecture review before changing product identity.

### 16. Testing Strategy

High-risk areas need tests first:

- Deterministic financial calculations.
- Broker freshness and actionability policy.
- Agent-safe projections and forbidden fields.
- API ownership/authorization.
- Database migrations.
- Provider adapter mocks.
- Error-path behavior.
- Report language and safety boundaries where practical.

Default tests must use synthetic data and mocked external calls.

### 17. CI/CD And Deployment

Before hosted beta, the project needs:

- Backend tests in CI.
- Frontend typecheck/lint/build in CI.
- Alembic migration checks.
- Secret scanning.
- Environment-specific configuration.
- Post-deploy health checks.
- Rollback procedure.
- Staging/production separation.

Local MVP does not need full production automation, but deployment assumptions should not leak secrets or broker data.

### 18. Security And Privacy

Treat these as sensitive by default:

- API keys and `.env` files.
- SnapTrade user secrets and portal URLs.
- Account names/numbers and provider ids.
- Balances, buying power, holdings, quantities, cost basis, option positions.
- Raw provider payloads.
- Reports, prompts, screenshots, imports, exports, PDFs, spreadsheets, and transaction history.

Security reviews must check authentication, authorization, input validation, XSS/CSRF risk, secret management, logging, prompt injection, data deletion/export, and provider permissions.

### 19. Documentation And Maintainability

Maintain:

- README and local setup.
- Docs map.
- Current roadmap.
- Implementation plan.
- Architecture and ADRs.
- Product docs.
- Security/privacy drafts.
- Known deferrals.
- Handoff briefs.

Docs should reduce agent context load, not become an archive everyone has to reread.

### 20. Teamwork And Handoff Readiness

Every handoff should state:

- Task name and phase/task id.
- Goal and non-goals.
- Files to read.
- Files changed or expected to change.
- Safety boundaries.
- Decisions already made.
- Open questions.
- Tests/checks run.
- PASS/BLOCKED status where relevant.
- Suggested next owner.

Avoid broad repo-wide reviews unless a milestone review explicitly requires them.

### 21. Evolution And End-Of-Life

Watch assumptions that may age badly:

- Broker provider coverage and freshness.
- Market-data licensing and cost.
- SnapTrade plan capabilities.
- LLM data policies.
- User segment and paid wedge.
- Option strategy scope.
- Public compliance obligations.
- Report-history volume and retention.

Design carefully where later changes are expensive: data model, provider abstraction, security boundary, actionability policy, and persisted report schema.

## Role-Specific Application

| Role | Primary sections |
| --- | --- |
| Codex A Product / PM | Product value, audience, scope, metrics, experimentation, communication |
| Codex B Architecture | Request lifecycle, boundaries, API, data model, compatibility, reliability, evolution |
| Codex C Backend | Deterministic correctness, data safety, APIs, persistence, tests, reliability |
| Claude A Frontend | Audience communication, UX states, accessibility, trust/freshness labels, AI/deterministic separation |
| Claude B Review / QA | Bugs, regressions, tests, privacy, financial wording, handoff readiness |
| Claude C Competitor | Product differentiation, scope control, pricing/positioning evidence |
| Codex D DevOps | CI/CD, deployment, observability, rollback, environment separation, cost |
| Claude D Security | Security/privacy, broker data handling, logging, access control, compliance language |

## Review Output Shape

For code reviews:

- Findings first, ordered by severity.
- File and line references where practical.
- Open questions or assumptions.
- Test gaps and residual risk.
- Brief summary only after findings.

For milestone reviews:

- PASS or BLOCKED.
- Scope reviewed.
- Decisions confirmed.
- Blockers.
- Important issues.
- Deferred items.
- Required next owner.

For PM or architecture reviews:

- Decision.
- Rationale.
- Alternatives considered.
- Consequences.
- Follow-up tasks.
- Owners.
