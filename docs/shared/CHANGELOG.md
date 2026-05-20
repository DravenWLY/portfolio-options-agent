# Changelog

This changelog is for human-readable project changes. It should summarize meaningful architecture, product, security, workflow, backend, frontend, or documentation changes. Detailed phase verification notes remain in `docs/shared/implementation_plan.md` and `docs/shared/completed_phases_log.md`.

## Unreleased

- Archived completed Phase 16A/16B into `docs/shared/completed_phases_log.md` and made Phase 17 the active implementation phase.
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
