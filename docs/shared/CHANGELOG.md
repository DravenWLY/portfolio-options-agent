# Changelog

This changelog is for human-readable project changes. It should summarize meaningful architecture, product, security, workflow, backend, frontend, or documentation changes. Detailed phase verification notes remain in `docs/shared/implementation_plan.md` and `docs/shared/completed_phases_log.md`.

## Unreleased

- Completed and reviewed Phase 20D Dashboard account-summary contract, cockpit cleanup, and visual/content polish; the next Dashboard design step is constrained Claude Design exploration with panel-level contract classification before implementation.
- Recorded the Phase 20D private Dashboard account-detail decision: account summary may show backend-formatted private display labels in principle, but only after `P20D-T1` refines the backend contract with privacy mode, display scope, valuation basis, and separate freshness/provenance.
- Completed and reviewed Phase 20C Modern Portfolio Desk wiring and presentation refinements through shared state/icon cleanup; future Dashboard expansion now begins with an explicit content-definition gate.
- Approved planning for P22A-T4 as an Alpaca Basic backend-only injected/mock-client evaluation adapter with no external call path, parked the commercial provider/RFI track, and opened P20D-T0 as docs-only Dashboard information-architecture planning.
- Opened Phase 22A as an offline, provider-neutral market-data evaluation foundation; amended ADR 0003 so Tradier is reference/prototyping-only rather than the assumed scalable production provider, and added a reusable vendor RFI template.
- Split Phase 22A market-data follow-through into early evaluation and later commercial selection tracks; assessed Alpaca Basic, Tradier Sandbox, and Intrinio delayed trial paths, leading to the completed P22A-T4 injected/mock-client Alpaca evaluation adapter while deferring RFI outreach.
- Paused Phase 21A agentic/realtime console expansion pending founder learning and future PM reactivation; retained the contract and ADR 0007 as inactive design references and added Codex E as an advisory-only learning role.
- Drafted Phase 21A realtime Agent Console architecture and proposed ADR 0007: backend-owned HTTP commands plus validated SSE progress, mock-first, with interactive frontend activation deferred until review.
- Archived completed Phase 18A into `docs/shared/completed_phases_log.md` and shifted the active roadmap/task pointers to Phase 18B workspace expansion.
- Added the Phase 18A frontend-readiness contract and shifted active delivery focus from deep Phase 17 research work to the first visible Trade Review Workspace.
- Archived completed Phase 16A/16B into `docs/shared/completed_phases_log.md`; Phase 17 was active briefly before the Phase 18A focus shift.
- Added ADR 0002 and ADR 0003 for the TradingAgents-inspired portfolio-aware agent-team architecture, Phase 16A/16B split, Phase 17 public research evidence boundary, and Tradier-first REST snapshot market-data timing.
- Added ADR 0001 and P16-T0 for the Portfolio Snapshot Actionability Policy so broker snapshot freshness, market quote freshness, and report/agent language are gated by one backend-owned contract.
- Added a multi-agent operating model for PM, architecture, backend, frontend, review, competitor intelligence, DevOps, and security roles.
- Added PM and architecture handoff docs so future agents can start from repo context instead of chat memory.
- Added lightweight DevOps and security/compliance draft checklists for later production-readiness work.
- Reorganized documentation into shared and agent-owned folders, replacing the generic `agent_context` folder with role-specific briefs.
- Converted the engineering review framework from a one-off prompt into a lifecycle quality framework for product, architecture, implementation, review, release, and operations work.
- Moved completed Phases 11-15 out of the active implementation plan and into the completed phases log.
- Documented that Claude Code skills stay in `.claude/skills/` while project handoffs and decisions stay in `docs/claude-*`.

## Maintenance Rules

- Add entries for decisions or changes that future maintainers should notice.
- Do not paste secrets, real brokerage values, real account data, real reports, or private strategy thresholds.
- Keep entries concise; link to task ids or docs when useful.
