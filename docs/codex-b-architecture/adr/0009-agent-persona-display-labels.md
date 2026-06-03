# ADR 0009: Agent Persona Display Labels — Backend-Owned, Separate From Machine Role Keys

Status: accepted
Date: 2026-06-02
Owner: Codex B — Architecture / Tech Lead (decision)
Drafted by: Claude E — Agentic AI Systems Design / Implementation
Related: ADR 0008 (agentic orchestration spine; frontend-consumed read contracts
are hard-to-reverse once shipped), ADR 0002 (role taxonomy), ADR 0005 (provider
gate). Product input: Codex A (persona labels + positioning). Analysis:
`docs/claude-e-agentic/AGENT_PERSONA_ROLE_ANALYSIS.md`.

## Context

The Agent Console presents a team of specialist personas. Internally each persona
has a stable, snake_case **machine role key** (e.g. `portfolio_manager_agent`),
and the read schema (`AgentTeamAnalysisConsoleRead`) previously exposed only that
key. Product (Codex A) approved clean, human-facing persona **display labels with
no "Agent"** (Fundamentals Analyst, News Analyst, Technical Analyst, Risk Manager,
Portfolio Manager), and the founder confirmed backend variable/file names are not
a product concern — only the UI must be clean.

ADR 0008 treats frontend-consumed read contracts as hard-to-reverse once shipped.
The display label is therefore a contract concern, not a frontend-only string.

## Decision

1. **Separate the machine role key from the user-facing display label.** The
   machine `role_name` stays the stable contract/identity value and is **not
   renamed** in this slice. The display label is a distinct, user-facing string.
2. **Display labels are backend-owned.** They live in the backend role registry
   (`backend/app/services/agent_team/roles.py`, `AgentTeamRoleDefinition.
   display_name`) and are exposed on the read schema as:
   - `AgentTeamRoleOutputRead.display_name: str`
   - `AgentTeamStageRead.display_name: str | None` (null when the stage has no
     `role_name`).
   The frontend renders `display_name` **verbatim** and performs no role→label
   mapping of its own. Single source of truth = the backend registry.
3. **Per-persona evidence-tier boundary is unchanged.** Public-evidence personas
   stay public-only; portfolio-aware personas receive only the agent-safe
   deterministic projection. Display labeling changes nothing about tiers,
   prompts, or behavior.
4. **No behavior change in this slice.** No role-key rename, no new persona, no
   prompt/output change, no advice/execution wording, no Agent Console composer
   activation, no routes/persistence/live-provider change. Mock stays default.

## Consequences

Positive:
- One backend-owned source of truth for persona labels; the frontend can't drift.
- Clean UI titles without exposing machine keys, while the stable `role_name`
  contract is preserved for any consumer/test.
- Future label changes (e.g. the pre-approved "Portfolio Lead" fallback) are a
  single backend registry edit, reviewed as a contract change.

Tradeoffs:
- `display_name` is now part of the frontend-consumed read contract (hard to
  reverse once shipped) — intentional, and the reason it is backend-owned and
  reviewed here.
- A future role-key rename (if ever approved) remains a separate, larger contract
  slice; this ADR deliberately does not do it.

## Alternatives considered

- **Frontend-only role→label mapping.** Rejected: it would put a hard-to-reverse
  contract concern in the UI layer, risk frontend/backend drift, and duplicate the
  registry the backend already owns.
- **Rename the machine role keys to clean names.** Deferred: unnecessary for the
  UI goal (founder: backend names don't matter), and a broader contract change.
- **Add a `specialty` field now.** Deferred to keep this slice narrow (Codex B).

## Review guidance / block conditions

Block changes that:
- rename machine `role_name` values as part of this slice;
- move display labels into the frontend or any non-backend source of truth;
- introduce advice/recommendation/execution/guarantee wording via a label;
- expose private fields, prompts, or provider metadata through the new fields;
- activate the Agent Console composer or alter provider/route/persistence behavior.
