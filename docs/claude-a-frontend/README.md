# Claude A Frontend Docs

This folder is reserved for frontend UI/UX briefs, frontend handoffs, accessibility notes, and trust-language review notes.

Current frontend guidance still lives in:

- `docs/shared/current_roadmap.md`
- `docs/shared/AI_TEAM.md`
- `frontend/README.md`

Do not add speculative frontend task specs before backend contracts exist.

## Claude Code Skills

Claude Code skills such as `frontend-design`, `finance-dashboard-ux-review`, and `implementation-plan-review` should stay in `.claude/skills/`.

Reason:

- `.claude/skills/` is runtime/tooling context for Claude Code.
- `docs/claude-a-frontend/` is project documentation and handoff context for frontend work.
- Moving skills into `docs/` could make Claude Code stop discovering them.
- Moving all Claude-facing docs into `.claude/` would hide product, review, and security decisions from Codex and future maintainers.

Use `.claude/skills/` for reusable Claude execution instructions. Use `docs/claude-*` folders for project-specific plans, handoffs, reviews, and decisions.
