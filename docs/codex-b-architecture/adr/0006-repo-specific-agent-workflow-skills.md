# ADR 0006: Repo-Specific Agent Workflow Skills

Status: accepted
Date: 2026-05-23
Owner: Codex B - Architecture / Systems / Integration Lead

## Context

The team reviewed external agent-workflow patterns from `mattpocock/skills`,
including `grill-with-docs`, `tdd`, `diagnose`,
`improve-codebase-architecture`, `to-issues`, `zoom-out`, and `prototype`.

Those patterns are useful because `portfolio-options-agent` now has multiple
specialized AI agents, a long implementation history, strict finance/privacy
constraints, and active frontend/backend coordination work. The project needs
better reusable workflows for frontend contract review, backend test-driven
slices, and product/architecture decision stress-testing.

However, this repository already has its own operating model:

- `AGENTS.md`
- `CLAUDE.md`
- `docs/shared/AI_TEAM.md`
- `docs/shared/current_roadmap.md`
- `docs/shared/TASKS.md`
- `docs/shared/implementation_plan.md`
- `docs/shared/completed_phases_log.md`
- ADRs under `docs/codex-b-architecture/adr/`
- strict no-secrets, no-real-brokerage-data, no-execution, no-advice, and
  no-guarantee rules
- Codex A/B/C and Claude A/B role separation

Installing or adopting upstream skills wholesale would risk creating a second
source of truth, conflicting docs conventions, generic workflows that ignore
finance/privacy constraints, or accidental migration away from the current
implementation-plan source of truth.

## Decision

Do **not** install upstream `mattpocock/skills` wholesale.

Adapt selected patterns into repo-specific workflow guidance in
`docs/shared/agent_workflows.md`.

Start with three approved workflows:

1. `portfolio-frontend-contract-review`
2. `portfolio-backend-tdd-slice`
3. `portfolio-grill-with-docs`

Keep the following deferred unless separately approved:

- external skill installation;
- GitHub Issues migration as an active task source of truth;
- broader `portfolio-diagnose`;
- broader `portfolio-architecture-deepening`;
- `to-issues`;
- `zoom-out`;
- `prototype`.

`docs/shared/implementation_plan.md` remains the active task source of truth.
Completed verification history remains in
`docs/shared/completed_phases_log.md`.

Finance/privacy/product constraints remain authoritative over every workflow.
No workflow may allow real brokerage data, secrets, API keys, raw holdings, cash
balances, account ids, provider ids, raw provider payloads, raw prompts,
provider traces, or account-specific thresholds into prompts, docs, tests,
frontend contracts, logs, screenshots, or reports.

No workflow may override the product boundary: Portfolio Copilot is read-only
manual decision support. It must not become an automated trading system, broker
scraper, order tool, guaranteed-return product, AI stock picker, or thin
TradingAgents wrapper.

## Consequences

Positive:

- Gives Codex and Claude agents reusable workflow guidance without installing
  external skills.
- Improves Phase 20A frontend contract review, Phase 20B backend contract
  discipline, and future product/architecture decision quality.
- Preserves the existing repo docs structure and role model.
- Keeps implementation tasks in one source of truth.
- Makes safety/privacy constraints explicit inside the workflows themselves.

Tradeoffs:

- The team does not get automatic upstream skill updates.
- The repo now has one more shared doc agents must know about.
- Workflows may need periodic pruning if they become too verbose.
- Deferred workflows such as diagnosis and architecture-deepening still need
  separate approval before becoming formal process.

## Alternatives Considered

### Install upstream skills directly

Rejected. Direct installation could introduce generic conventions such as
`CONTEXT.md`, external issue tracker assumptions, alternate ADR paths, or
slash-command behavior that conflicts with this repo's docs and safety model.

### Do nothing

Rejected. The team has already experienced plan drift, frontend/backend contract
risk, and slow handoff loops. Lightweight workflow guidance is justified.

### Move active planning to GitHub Issues

Deferred. GitHub Issues may become useful later, but
`docs/shared/implementation_plan.md` remains the active task source of truth for
now.

### Put full workflows into `AGENTS.md` and `CLAUDE.md`

Rejected for now. Those files should stay concise and authoritative. They may
link to `docs/shared/agent_workflows.md`, but the detailed workflow checklists
belong in one canonical shared doc.

## Review Guidance

Block future changes that:

- install external skills without PM/architecture approval;
- create a duplicate task source of truth;
- move active planning out of `docs/shared/implementation_plan.md` without a new
  PM decision;
- weaken no-secrets, no-real-brokerage-data, no-execution, no-advice, or
  no-guarantee rules;
- let frontend work invent backend fields or calculate financial metrics;
- let backend work call live providers in default tests;
- let generic upstream conventions override this repo's agent ownership model;
- add broad workflows such as diagnosis, architecture-deepening, or prototype
  without defining repo-specific constraints first.

When reviewing workflow use:

- Codex A owns product and roadmap decisions.
- Codex B owns architecture, API/data contracts, ADRs, and integration gates.
- Codex C owns backend implementation under approved task specs.
- Claude A owns frontend UI/UX implementation under approved contracts.
- Claude B owns safety, QA, and code-review checks.
