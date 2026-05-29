# Changelog

This changelog is for human-readable project changes. It should summarize meaningful architecture, product, security, workflow, backend, frontend, or documentation changes. Detailed phase verification notes remain in `docs/shared/implementation_plan.md` and `docs/shared/completed_phases_log.md`.

## Unreleased

- Completed P23B-T6 Browser-Local Symbol Recents LRU For Trade Review Autocomplete: the autocomplete now keeps a true per-browser "Recently viewed" list in a single UI-only localStorage key (`poa-symbol-recents`, capacity 5, newest-first, deduped). Empty focus shows local recents, or a neutral empty state when none exist — never backend default symbols and never "Symbol Not Found". Recents are recorded only on intentional selection, and an existing recent is promoted to the top on successful submit. Only the 7 public reference fields are persisted (no prices, quotes, volume, account/portfolio/broker context, prompts, LLM context, or trade history). No backend changes, no new endpoints, no provider/external/LLM calls, and no other storage key.
- Completed P23B-T3 Trade Review Autocomplete Uppercase And Recent Selection Polish: Symbol and Underlying inputs now force uppercase as the user types, so the displayed value, search query, and submitted payload are uppercase (`nvda` → `NVDA`, `nok` → `NOK`). Backend-owned ordering, recent/default list, section labels, and "Symbol Not Found" message are preserved verbatim; no frontend ranking/sorting/filtering, no validation wiring, no storage writes, no provider calls.
- Completed P23A-T4 Autocomplete UX V2 Recent And Contains Search Consumption: Trade Review autocomplete now shows the backend "Recently viewed" list on empty focus/input and exact-first backend search results while typing, consuming `result_mode`, `section_label`, items, and messages verbatim. Frontend does not rank, sort, filter, or fuzzy match. No quotes, prices, recommendations, validation wiring, storage writes, provider calls, or LLM/agent use.
- Completed P23A-T2 Trade Review Symbol Autocomplete Frontend: wired backend symbol search contracts into Trade Review Symbol and Underlying inputs with debounced typeahead, keyboard navigation, ARIA combobox pattern, "Symbol Not Found" handling, and no-search-on-mount guard. No prices, quotes, recommendations, or localStorage writes.
- Opened Phase 23A symbol lookup and Phase 24A economic/news awareness as backend-first, synthetic/replay-first contract phases; symbol lookup is the next preferred implementation slice, and economic awareness follows with explicit `is_trading_signal=false` boundaries.
- Completed P20D-T4 Dashboard Claude Design visual refinement: added action context bar surfacing recommended_user_action_label and overall_review_mode from readiness contract, restructured readiness section with section label and section-level DemoChip, added account summary section headers, and improved spacing/density. All data from reviewed backend contracts rendered verbatim.
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
