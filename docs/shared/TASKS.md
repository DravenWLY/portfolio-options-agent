# Task Routing and Current Work

This file is a lightweight task index. `docs/shared/implementation_plan.md` is now a short active-work index; paused/incomplete backlog items live in `docs/shared/deferred_items.md`, detailed historical task specs live in `docs/shared/implementation_plan_archive_2026-06-03.md`, and completed verification history belongs in `docs/shared/completed_phases_log.md`.

## Current State

- Completed foundation: Phases 1-16, Phase 17A, Phase 18A, Phase 18B, Phase 18C, Phase 19A, Phase 19B, Phase 19C, and Phase 20A.
- Active roadmap phases: Phase 20B - remaining blocked Modern Portfolio Desk contracts; Phase 20D - completed Dashboard cockpit cleanup/polish/Claude Design visual refinement; Phase 22A - completed internal market-data adapter evaluation checkpoint; Phase 23A/23B - symbol lookup complete through local recents; Phase 24B - FRED-backed economic awareness backend path; Phase 25A - approved agentic workflow foundation slices owned by Claude E; Phase 26A - Market Mood internal-demo market context.
- Completed frontend integration sequence: Phase 20C - Modern Portfolio Desk reviewed wiring and presentation refinements.
- Paused design reference: Phase 21A - Realtime Agent Console backend contract. Do not begin implementation unless Codex A explicitly reactivates a scoped task. If reactivated, Claude E owns agentic-system design/coding and Codex B reviews.
- Current safety foundation: broker portfolio snapshot freshness/actionability is explicit, Phase 16 agent components consume it, and Phase 16B enforces private/public context boundaries.
- Current architecture concern: keep new Dashboard context panels contract-backed and source-labelled while preserving privacy, freshness semantics, and deterministic/agent-commentary separation. Agentic workflow slices are owned by Claude E with Codex B review; the Agent Console composer remains disabled until a separate reviewed activation slice.
- Current product-positioning decision: Portfolio Copilot should complement,
  not replace, serious research/portfolio tools such as Stock Rover. The
  Dashboard is a review-readiness cockpit, not a research terminal, screener,
  watchlist, holdings grid, fair-value surface, or market terminal.

## Current Primary Owners

| Workstream | Owner | Supporting reviewer |
| --- | --- | --- |
| Product scope, MVP, positioning | Codex A PM | Claude C |
| Architecture, API/data contracts, ADRs | Codex B | Claude B |
| Backend implementation, excluding agentic AI workflow | Codex C | Claude B |
| Frontend UI/UX | Claude A | Codex B for contract review |
| Security/privacy/compliance | Claude D later | Codex B/C until active |
| DevOps/production readiness | Codex D later | Codex C until active |
| Agentic AI systems design and implementation | Claude E | Codex B architecture/safety review |

## Near-Term Task Candidates

Do not treat this list as authorization to implement. Each item needs an approved task spec before code changes.

1. Dashboard design checkpoint: `P20D-T1` through `P20D-T5` are complete and reviewed. `P20D-T5` applied the Stock Rover/Product B pressure-test cleanup using existing reviewed contracts: promoted the readiness verdict, demoted agent-provider status, hid plausible synthetic headline account values, and removed dead quick-review presets. Future Dashboard visual work requires a new approved task with reviewed contracts for any new data surfaces.
2. Dashboard Product B pressure-test outcome: accepted decisions are complement-not-replace positioning, no plausible synthetic headline account values, real-source account summary plus broker freshness before persisted review history, display-rights-cleared REST quotes before external-beta quote-current claims, narrow per-underlying earnings-date review context, and agent-provider status off the Dashboard first viewport.
3. Next Dashboard backend priority candidate: real-source account summary plus broker freshness mapping, if Codex A opens a task. Do not jump to persisted history, quote-current display, or new Dashboard panels before this trust foundation.
4. Market-data evaluation checkpoint: `P22A-T4` is complete after Codex B PASS re-review. No actual Alpaca API request, credential path, frontend data display, agent ingestion, or production-provider work is authorized.
5. Symbol lookup: Phase 23A/23B is complete through broad Nasdaq-traded local refresh, uppercase autocomplete, browser-local LRU recents (`poa-symbol-recents`), and offline fixture cleanup. Keep frontend contracts provider-neutral; no quotes, recommendations, frontend provider calls, broker tradability claims, or storage beyond the approved UI-only recents key.
6. Market Mood: `P26A-T1` backend is reviewed PASS. Claude A may start `P26A-T2` Dashboard compact card using `GET /market-context/market-mood`; keep it secondary Market Context, overall score/rating only, no CNN branding, no `live`/`real_time` claims, and no trading-signal/actionability wording.
7. Product/architecture: commercial vendor/RFI work is parked. Retain reference documentation for later scale planning; do not begin outreach, licensing/pricing negotiation, or provider selection now.
8. Remaining data contracts: P20B-T5 reports and P20B-T6 profile/display stay blocked until their persistence/auth and product decisions are approved.
9. Pause gate: do not start any Phase 21A realtime/agent expansion work or activate the Agent Console composer until Codex A explicitly reactivates a scoped slice. If reactivated, Claude E owns agentic-system design/coding and Codex B reviews; Codex C should not implement that lane.
10. Agentic AI: Claude E may design and code approved Phase 25A slices, but this does not authorize frontend composer activation, raw private-data prompting, TradingAgents source copying, or unreviewed live provider/tool expansion. ADR 0008 is accepted; ADR 0009 is accepted for backend-owned display labels. Mock remains default and machine role keys remain unchanged.
11. Completed frontend boundary: `P20C-T1` through `P20C-T6` are reviewed as the current Modern Desk integration checkpoint; future redesign or data wiring requires a new approved task.

## Routine Task Checklist

- Confirm owner and phase/task id.
- Read `AGENTS.md`, `docs/shared/current_roadmap.md`, `docs/shared/implementation_plan.md`, and the specific phase contract or task handoff doc.
- Keep scope to one task.
- Use synthetic data only.
- Run relevant tests/checks.
- Keep `docs/shared/implementation_plan.md` concise. Put long verification notes in `docs/shared/CHANGELOG.md`, `docs/shared/completed_phases_log.md`, or a phase-specific architecture/review doc.
- Add a short entry to `docs/shared/CHANGELOG.md` only for meaningful user-facing, architecture, security, or workflow changes.
