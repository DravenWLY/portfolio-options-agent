# Claude A Frontend Docs

This folder is reserved for frontend UI/UX briefs, frontend handoffs, accessibility notes, and trust-language review notes.

Current frontend guidance still lives in:

- `docs/shared/current_roadmap.md`
- `docs/shared/AI_TEAM.md`
- `docs/codex-b-architecture/PHASE_18A_FRONTEND_READINESS_CONTRACT.md`
- `frontend/README.md`

Do not add speculative frontend fields before backend contracts exist.

Current Phase 18A rule: Claude A should wait for Codex C to deliver the sanitized trade-review workspace read contract before implementing the first visible Trade Review Workspace. The workspace must stay read-only, consume completed Phase 16 deterministic/actionability outputs through the safe contract, and exclude TradingAgents research UI, option-chain browser/screener behavior, broker actions, advice language, and guaranteed-return language.

## Claude Code Skills

Claude Code skills such as `frontend-design`, `finance-dashboard-ux-review`, and `implementation-plan-review` should stay in `.claude/skills/`.

Reason:

- `.claude/skills/` is runtime/tooling context for Claude Code.
- `docs/claude-a-frontend/` is project documentation and handoff context for frontend work.
- Moving skills into `docs/` could make Claude Code stop discovering them.
- Moving all Claude-facing docs into `.claude/` would hide product, review, and security decisions from Codex and future maintainers.

Use `.claude/skills/` for reusable Claude execution instructions. Use `docs/claude-*` folders for project-specific plans, handoffs, reviews, and decisions.
