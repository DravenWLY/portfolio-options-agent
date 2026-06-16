# Changelog

- 2026-06-15: Added P29B-T3A backend public evidence persistence and projection
  seam. Explicit Agent Team generation now persists generation-time
  `public_evidence` inside the saved artifact JSON alongside `agent_summary`,
  and `SavedEvidencePackageRead.from_saved_review_artifact` reads saved public
  sections back before falling back to legacy `not_reviewed` defaults. Added a
  role-scoped public evidence projection contract for fundamentals, news, and
  technical analysts; projections expose only role-allowed sanitized public
  sections plus minimal instrument context. Providers remain offline/synthetic
  only; no public-role generation, frontend, live source, runtime tool, LLM,
  TradingAgents, or provider integration was added.
- 2026-06-15: Added P29B-T1 backend public evidence contract foundation.
  `SavedEvidencePackageRead` now has an additive `public_evidence` block with
  stable public section keys for company profile, fundamentals, news, events,
  technical context, and market context. Current saved reports default every
  public section to `not_reviewed`; the new offline provider boundary returns
  no reviewed public evidence and makes no external calls. Public evidence
  validators reject private fields, raw source fields, URLs/article bodies, raw
  payload hints, prompts/traces/secrets, and unsafe trading wording. Agent Team
  report-output validation now recognizes the public evidence keys and enforces
  role-specific allowlists plus recursive availability checks before public roles
  can cite nested public sections.
- 2026-06-15: Added P29A-T6 backend report-generation timing semantics. Saved
  Agent Team summaries now carry nullable `report_generated_at`, surfaced on
  `AgentTeamReportRead` separately from saved-source `generated_at` and
  read-projection `report_built_at`. Explicit regeneration remains manual via
  `POST /users/{uid}/reports/{thread_id}/agent-team-report` and replaces only
  `saved_artifact_json.agent_summary`, preserving immutable saved source/scope/
  deterministic evidence. Source-only and legacy reports read with
  `report_generated_at=null`; no auto-generation, queue, frontend, provider, or
  TradingAgents behavior was added.
- 2026-06-15: Closed the remaining Phase 29A foundation loop. P29A-T3 Agent
  Team report generation backend is now complete and PASSed after Codex B's
  blocker fix for persisted-summary evidence-reference validation
  (`role_summaries` and top-level `evidence_references` now obey the same role
  boundary and availability rules as the read-model report shape). P29A-T4
  Reports Library / Report Detail redesign and P29A-T4A visual closeout polish
  are also fully accepted: Reports now centers saved Agent Team analysis with
  deterministic evidence and provenance as supporting context, and the narrow
  closeout fixed the mute-state banner icon contrast plus the border
  shorthand/longhand React warning without changing contracts, endpoints, or
  rendered backend values.
- 2026-06-14: Completed P29A-T1 saved evidence package backend contract after
  Codex B blocker fixes. `SavedEvidencePackageRead` now carries an immutable,
  agent-safe source snapshot from `SavedReviewArtifactRead`, preserves
  `source_kind` / `source_reference`, projects lossy scope/freshness/actionability
  and deterministic evidence sections, excludes account labels/refs/context refs
  and raw private data, and expands prohibited wording checks for broad
  advice/recommendation phrases. P29A-T2 should reuse or tighten this validation
  for generated Agent Team output.
- 2026-06-14: Added the Phase 29A Agent Team Report Architecture direction.
  Saved deterministic/source artifacts are now framed as the evidence and audit
  foundation, not the final product endpoint. The next workstream should generate
  Agent Team reports from immutable backend evidence packages, while allowing
  high-fidelity deterministic portfolio-impact views (before/after exposure
  changes, risk-pattern alerts, scope/freshness/caveat drilldowns) as supporting
  analysis surfaces. Runtime private agent tools remain deferred/prohibited by
  default.
- 2026-06-13: Implemented the P28A-T3 frontend "Save review snapshot" action
  (Claude A); Codex B contract/privacy/safety review PASS. A compact
  `SaveReviewSnapshot` control appears on completed Trade Review results only
  when the backend exposes a non-null `saved_review_source_reference` and a
  user-id route context exists, and calls
  `POST /users/{uid}/reports/from-trade-review` with only `source_kind`,
  `source_reference` (verbatim backend value, never displayed or invented),
  `title`, and `report_type`. It sends no scope metadata, deterministic summary,
  Agent Team output, Account Details, selector state, cached state, or raw
  account/provider/broker/holdings data; success is quiet with a Reports link,
  failure is retryable, and no advice/order/execution wording was added. Static
  checks (typecheck, lint, build, git diff --check) pass. P28A-T3A fixed the
  alembic `0020` migration `down_revision` typo that initially blocked
  data-backed browser smoke; full-stack save-flow smoke remains the P28A-T4
  closeout gate.
- 2026-06-13: Added the P28A-T3 backend unblock for saved review snapshots:
  `TradeReviewWorkspaceRead` now exposes nullable
  `saved_review_source_reference` values, with `trrev_...` references populated
  only after the authenticated portfolio-preview backend path materializes a
  matching server-owned `saved_review_sources` row. Synthetic/stateless previews
  remain null, the save endpoint still resolves sources server-side, and no raw
  account/provider/broker data or frontend implementation was added. Codex B
  PASS; frontend save action is unblocked.
- 2026-06-13: P28A-T3 frontend "Save review snapshot" is BLOCKED pending a
  backend contract field. Codex B confirmed `POST /reports/from-trade-review`
  requires an app-owned `source_reference` (`trrev_`/`workspace_`/`agentrun_`)
  that resolves to a `saved_review_sources` row, but the Trade Review read
  contract exposes only `review_reference` (a `trv_`/intent value that fails the
  source regex) and no production path persists a source row
  (`record_saved_review_source` has no production caller). Next: backend (Codex C)
  adds an opaque `saved_review_source_reference` to `TradeReviewWorkspaceRead`
  plus production materialization of the matching source row, then re-review and
  unblock the frontend action.
- 2026-06-13: Closed Phase 27C scope integration after the P27C-T7 blocker fix:
  Trade Review results no longer render the visible opaque context reference,
  while safe context labels/status/counts remain. Added the Phase 28A Saved
  Review Artifact architecture contract as the next recommended workstream:
  durable saved reports must persist generation-time scope, caveats, freshness,
  deterministic summary, and optional sanitized Agent Team output without
  reconstructing from current account state or exposing raw private data.
- 2026-06-13: Completed P27C-T5 Reports saved scope metadata backend
  contract. Report create/list/detail reads now include nullable
  `scope_metadata` using the reviewed `ReportScopeMetadataRead` shape; current
  legacy/unknown report rows return explicit `null` and do not infer scope from
  current account state, route params, selectors, or mutable context. Codex B
  review PASS.
- 2026-06-12: Closed the Market Mood source-update follow-up: backend refresh
  now reports refreshed/unchanged/failed source checks with separate
  `last_checked_at` metadata, while the detail page refreshes from backend state
  only and preserves provider `updated_at` as source time. Also added the Market
  Mood sidebar shortcut, fixed collapsed sidebar controls, and preserved Account
  Details scroll/detail context during selected-account refresh.
- 2026-06-12: Reorganized coordination docs so routine agents start from the
  short active plan and current roadmap instead of historical task logs. Archived
  the pre-cleanup active plan as
  `docs/shared/implementation_plan_archive_2026-06-12.md`, refreshed roadmap
  direction toward Phase 27C Trade Review / Agent Team scope integration, and
  clarified copyable prompt format plus full-stack preview proof for
  data-backed pages.
- 2026-06-11: Added a shared full-stack preview rule for data-backed frontend
  pages so agents start Postgres, backend, and frontend before claiming
  Account Details / Dashboard / Agent Console data-state browser smoke.

This changelog is for human-readable project changes. It should summarize meaningful architecture, product, security, workflow, backend, frontend, or documentation changes. Keep `docs/shared/implementation_plan.md` concise; detailed phase verification notes belong in `docs/shared/completed_phases_log.md`, phase-specific docs, or the archived implementation plan.

## Unreleased

- Completed P27C-T6 Report detail saved-scope display: opening a saved report
  now fetches `GET /users/{uid}/reports/{thread_id}` and renders only
  `ReportThreadDetailRead.scope_metadata` for the detail view. Null detail scope
  shows "Scope metadata unavailable for this report.", stale detail responses
  are gated by selected report id, and the UI does not infer saved scope from
  current account/portfolio state. Codex B re-review PASS; browser smoke was
  intentionally not run to avoid inspecting private saved report content.
- Completed P27C-T2 Reports scope metadata display and history-scope honesty:
  `/reports` now renders data-backed saved report snapshots and shows each
  report's saved `scope_metadata` only. If scope metadata is null, the UI shows
  honest unavailable copy and explicitly does not reinterpret the report through
  the current account selector. The older report-history surface also uses the
  same saved-scope component and no longer filters or labels reports from
  mutable account-selector state. No raw refs/IDs, balances, holdings,
  quantities, provider payloads, prompts, storage writes, new endpoints,
  provider calls, frontend financial math, or action/advice wording was added.
  Codex B contract/privacy/safety re-review PASS; visual re-review PASS.
- Completed the Agent Console compact scope banner (tracked in the plan as
  P27C-T3; implemented under user task label P27C-T4): the console now renders
  a compact `Review scope` band from the backend-owned lossy `scope_summary`
  contract only — scope modes, selected-context presence, included/excluded
  counts, review-account presence, account-feasibility evaluated flag, and
  sanitized scope caveat codes. The banner uses generic copy when account labels
  are unavailable, stacks responsively at the Agent Console breakpoint, and adds
  no raw refs/IDs, balances, holdings, quantities, provider payloads, prompt
  exposure, storage writes, new endpoints, provider calls, frontend financial
  math, or advice/order/execution wording. Codex B contract/privacy/safety PASS;
  visual re-review PASS.
- Completed P27C-T1 Trade Review review-account selector frontend wiring (Codex B contract/privacy/safety review PASS). Trade Review now separates the **Review account** (where the user would manually place the trade) from the **Broader portfolio context** (exposure awareness), consuming the existing reviewed backend contract. The form populates a review-account selector from the Account Details overview and submits only the opaque `account_reference` via `review_account_selection` (`unselected` vs `selected_account`); the result panel renders `scope_metadata` using backend-owned display labels only — review-account label/kind, account-level-feasibility evaluated/not-evaluated, portfolio-context scope label, included/excluded account labels, and scope caveat codes — never `account_reference`, `scope_reference`, `context_reference`, broker/provider IDs, balances, holdings, quantities, payloads, prompts, or traces. The portfolio-preview call now forwards the existing `X-User-Id` route header (the app's own user UUID, already used in `/users/{uid}/...` paths) so a selected real account resolves server-side; no backend route/field/migration/provider/storage change. No frontend financial computation and no advice/order/execution/safe-to-trade wording. Deferred follow-ups (non-blocking): forward the user id on the Agent Team analysis-preview path for review-account parity (P27C-T3), and add an aria-live announcement for the account-list loading→ready/error transition.
- Added a CodeGraph-first context rule for all agent workflows: future implementation and review prompts should start code understanding with focused CodeGraph exploration, avoid broad grep/read loops and giant read lists, and keep direct file reads to changed files, directly related contracts/tests, or recently edited files. This is intended to reduce Claude/Codex session usage and prevent narrow tasks from becoming repo-wide audits.
- Completed P27B-T14 Account Details selected-detail visual polish and backend-label contract confirmation: the selected-account panel can rely on backend gain/loss labels where losses are signed and gains are unsigned, backend freshness display labels for broker snapshot and market quotes are distinct self-describing phrases, and selected-account summary labels remain self-prefixed display strings with only opaque refs plus display labels exposed. Recommended non-blocking frontend cleanup: remove or narrow the `cached` -> `Available` compact freshness remap so future bare cached labels remain honest.
- Completed P27B-T13 backend enforcement for the display-only cash/buying-power/collateral policy: real-broker CSP and covered-call reviews cannot treat private Account Details cash, available-cash, buying-power, or collateral labels as account-level feasibility inputs. CSP remains analysis-only/generic/unverified, covered-call coverage remains unverified, and Agent Team evidence receives sanitized status/caveat categories only, with cash/buying-power tokens rewritten away from prompt payloads.
- Accepted P27B-T9 buying-power/collateral policy: Account Details may privately display broker-reported cash, available cash, buying power, and balance-source labels, but those labels are display-only for deterministic feasibility. Buying power is not treated as CSP collateral, real-broker CSP/covered-call reviews remain caveated or downgraded until later broker/account-type collateral and same-account coverage models are approved, and Agent Team evidence may receive only safe caveat/status codes rather than cash/buying-power values or account identifiers.
- Completed P27B-T11/T12 Account Details selected-detail frontend cleanup: the page now uses the enriched backend display-label contract in a denser selected-account panel, with compact cash display, broker-style position tables, sticky first columns, row-click expansion for secondary details/tax lots, collapsed data notes, and sign-only gain/loss coloring. Endpoint usage remains the two approved Account Details GETs; no provider calls, storage writes, frontend financial math, raw refs, broker actions, or advice/execution wording were added.
- Completed P27B-T10 Account Details enrichment contract: selected-account details now expose backend-owned private display labels for broker-reported price, average cost, cost basis, open P/L, gain/loss percent, valuation source, cash availability/buying power labels, and optional opaque tax-lot display rows. Option market value and option cost basis now consistently apply contract multipliers, including mini-options. Overview remains broker-readiness only; no raw provider/account/lot IDs, raw payloads, transactions, orders, Agent Team evidence widening, or deterministic feasibility use was added.
- Added P25A-T16 dev-only live LLM runtime profile: ordinary `docker compose build backend` remains lean/offline/mock-default, while the explicit `docker-compose.live-llm.yml` override builds `portfolio-options-agent-backend:live-llm` with the optional `live-llm` extra installed for local read-only Agent Console development. Live mode still requires backend env gates; no frontend provider selector, streaming, composer activation, persistence, new endpoints, inline keys, or live provider calls were added.
- Completed a founder-approved Gemini live smoke of the Agent Console route function through the P25A-T16 live-capable backend profile using `gemini-2.5-flash-lite`: the route returned `run_status=completed`, five non-mock Google role outputs with provider status `ok`, no provider warnings, and the expected analysis-only safety flags. No key value was printed; host HTTP ports were unavailable from the sandbox, so the route function was invoked inside the live backend container. Backend was restored to ordinary mock-default Compose after the smoke.
- Completed P25A-T15: the read-only Agent Console route (`POST /agent-team/trade-review-analysis/preview`) now runs the reviewed `ReviewRunner` safety/eval/timing/budget spine instead of the older `AgentTeamOrchestrator`. A new backend projection `build_console_read_from_review_run_state` maps `AgentReviewRunState` onto the unchanged `AgentTeamAnalysisConsoleRead` contract (backend-owned `display_name` per ADR 0009; `run_status` `failed_safe -> failed`; sanitized provider-neutral warnings with no raw payload/URL/key/exception body; legacy `stock_position_count` key kept for payload parity). Fixed the hardcoded "Mock portfolio-team synthesis" wording to provider-neutral "Portfolio-team synthesis" so it reads correctly on live runs. Blocked-actionability snapshots now correctly degrade to a deterministic-only console (no LLM role commentary) rather than emitting mock commentary that ignored the gate. Endpoint, response shape, and frontend route preserved; mock stays default; live providers only via backend env; composer stays disabled; no new endpoint, streaming, persistence, parallel dispatch, or tool execution. Default tests stay offline/mock.
- Migrated the Gemini provider adapter (P25A-T14) off the deprecated `google-generativeai` SDK to the supported `google-genai` SDK: the adapter now lazily imports `google.genai` and calls `genai.Client(...).models.generate_content(...)`, preserving the app-owned `LLMProvider` protocol, injected/fake-client testability, response shape, safe status mapping (auth/rate-limit/quota/timeout/unavailable/invalid-response), and no raw-provider-detail leakage. The `live-llm` optional extra in `pyproject.toml` and `uv.lock` were updated (removed `google-generativeai`; added `google-genai` v2.8.0, slimming the transitive tree). Founder-run post-migration Gemini live smoke passed (`1 passed in 0.03s`) with no `google.generativeai` deprecation warning. Mock remains default; default tests stay offline/mock; no route/persistence/frontend/composer change.
- Hardened the P25A-T13 single-run real-provider gate: the opt-in, backend-only Gemini/OpenAI live-smoke tests (synthetic data only, excluded from the default suite, skipped unless explicitly opted in) now assert a single controlled live `ReviewRunner` run passes the existing safety/eval path with no forbidden private keys/values, no secret/key/URL patterns, no advice/order/execution wording, and safe degradation on provider failure (no raw provider details leaked). Gemini uses a cheap Flash model by default and treats rate-limit/quota/unavailable as safe non-blocking; OpenAI requires an additional explicit paid-acknowledgement gate and never runs by default. Live-smoke docstrings no longer show inline keys. Founder-run Gemini live smoke passed (`1 passed, 1 warning in 1.77s`); the warning tracks the known `google.generativeai` deprecation and is covered by P25A-T14. Mock remains default; no route/persistence/frontend/composer change.
- Completed P25A-T12 read-only Agent Console handoff polish: the console now frames completed agent-team output as a read-only analysis report rather than an interactive chat, consumes backend-owned `display_name` labels, keeps the disabled composer permanently non-interactive, and removes repeated analysis-only boilerplate without changing endpoints, payloads, storage, providers, LLM behavior, TradingAgents, MCP, LangGraph, or financial computation.
- Closed P26A-T8/T9/T10 Market Mood detail-page polish: removed the selected-indicator focus-box regression, added colored rating states, removed distracting point-count/source-status clutter, tightened the explanation tooltip, and changed indicator charts to a one-year visible window. Market Momentum now computes the 125-day moving average from full raw history while rendering only the one-year slice; tooltips show the MA only where a computed value exists. No backend/provider call, refresh, storage write, or trading-action wording was added.
- Completed P26A-T6 Market Mood runtime refresh wiring: the protected backend refresh path can now fetch CNN-derived Fear & Greed data through an injected HTTP boundary, normalize it into a provider-reference last-good snapshot, persist app-owned JSON only, and keep product GETs provider-reference-or-unavailable. Default tests remain mocked/offline; a founder-approved live smoke passed with provider-reference data, 1323 trend points, and all 7 indicators carrying provider history. Follow-up: calibrate live component unit/value labels before considering the detail page polished.
- Closed P26A-T5 Market Mood real-data-only behavior: product reads for the Dashboard card and detail page now display only provider-reference last-good snapshots and otherwise return/render unavailable. Synthetic Market Mood fixtures remain test/design injection only and are ignored by default runtime GETs, so product UI no longer shows synthetic values, synthetic histories, or demo-history wording.
- Completed the Market Mood detail page (P26A-T4, frontend): a dedicated `/market-context/market-mood` view consuming only `GET /market-context/market-mood/detail`. Shows the overall sentiment band plus all 7 indicators, each with an interactive SVG line chart of its raw history (native scale — not a forced 0–100), a hover tooltip showing the date + backend value label, and backend-owned subtitle/description/unit/axis/value-meaning metadata. Editorial Modern Portfolio Desk styling; minimal CNN-derived wording, no logo/branding/gauge clone, no provider calls, storage writes, or new endpoints. Claude B visual/design PASS and Codex B contract/safety PASS.
- Revised the Phase 26A Market Mood plan so the full detail page is not built from insufficient summary fields: P26A-T3 is now a single backend contract extension for per-indicator histories, raw value labels, units, axis hints, explanations, and synthetic fixtures; P26A-T4 is the single Claude A frontend detail-page redesign after Codex B review.
- Added the Dashboard "Market Mood" compact card (P26A-T2, frontend): a secondary market-context card consuming the reviewed `GET /market-context/market-mood` backend contract only. Shows the overall sentiment score/rating and a presentational 0–100 band, with generic safety boilerplate kept out of the compact card. Components, trend, and comparisons are handled by the P26A-T4 detail page. No CNN branding, no frontend provider calls, no refresh control, no storage writes. Claude B/Codex B review PASS.
- Reduced `docs/shared/implementation_plan.md` from the long historical task ledger into a concise active-work index, preserving the previous full file as `docs/shared/implementation_plan_archive_2026-06-03.md`; updated `TASKS.md` and `docs/README.md` so future agents keep long verification details out of the active plan.
- Added a compact paused/incomplete phase backlog to `docs/shared/deferred_items.md` so blocked or paused work remains visible without re-bloating `implementation_plan.md`.
- Cleaned up current coordination docs for the next frontend handoff: moved the detailed Phase 26A Market Mood architecture contract into `docs/codex-b-architecture/PHASE_26A_MARKET_MOOD_CONTRACT.md`, compacted the Phase 26A task tracker in `implementation_plan.md`, marked P25A-T11 and P26A-T1 review outcomes as done, and updated `TASKS.md` / `current_roadmap.md` so Claude A can start the Dashboard Market Mood compact card from the reviewed backend contract.
- Migrated the backend to an industry-standard PEP 621 `backend/pyproject.toml` (setuptools build backend, matching TradingAgents) as the single dependency source of truth, replacing `backend/requirements.txt`. Core runtime deps live in `[project].dependencies`; test/dev tooling in the `dev` extra; optional backend-only live LLM provider SDKs (`google-generativeai`, `openai`) in the `live-llm` extra — kept out of core so the base install and default offline/mock test suite stay lean (adapters import provider SDKs lazily; mock remains default). Install variants: `pip install .`, `pip install -e ".[dev]"`, `pip install ".[live-llm]"`. Codex D added `backend/uv.lock` as the backend reproducibility lockfile and updated `backend/Dockerfile` to export locked core runtime deps with `uv --quiet export --frozen --no-dev --no-emit-project`, then install the project with `pip install --no-deps .`; Docker build and backend/Postgres Compose startup passed, and the default image does not include optional `google-generativeai` or `openai` SDKs.
- Completed Phase 25A P25A-T8 (Codex B PASS) and added P25A-T9 provider live-smoke completion: Gemini stays the routine manual smoke (free-tier/Flash friendly; rate_limited/quota_exceeded/provider_unavailable treated as safe non-blocking failures), and a new opt-in OpenAI live smoke test was added — paid API usage, gated behind external/slow markers plus BOTH `POA_LLM_LIVE_TESTS=1` and a dedicated `POA_LLM_OPENAI_LIVE=1` acknowledgement plus `OPENAI_API_KEY`, with the model configurable via `POA_LLM_MODEL` (default `gpt-4o-mini`). The OpenAI live smoke was NOT run (awaits explicit approval); the Gemini live smoke was not run here because no key is exported in the shell. Mock remains default; no frontend/routes/persistence/composer/MCP/LangGraph/OpenAI Agents SDK/TradingAgents changes.
- Completed Phase 25A P25A-T7 (Codex B PASS) and added P25A-T8: a backend-only OpenAI provider adapter behind the existing app-owned `LLMProvider` protocol. Uses the plain OpenAI chat-completions client (NOT the OpenAI Agents SDK), imported lazily only when a live OpenAI provider is explicitly configured with `OPENAI_API_KEY`; default tests inject a fake client and make no live call. Provider config/factory now accept `openai` only when explicitly configured (mock stays default, OpenAI is never default); errors map to existing safe statuses with no raw exception/payload/key leakage, and output passes the same `LLMProviderResponse`/output-safety boundary (unsafe output degrades to `safety_validation_failed`). No OpenAI live call was run. No routes, persistence, migrations, frontend, composer, MCP, LangGraph, or TradingAgents changes.
- Added Phase 25A P25A-T7 LLM provider key setup and a controlled Gemini live-smoke path: `.env.example` now documents backend-only `GOOGLE_API_KEY` (implemented Gemini provider) and a backend-only `OPENAI_API_KEY` (the OpenAI provider is implemented, paid API usage, opt-in only, and never default; mock remains default), with internal `POA_LLM_*` knobs intentionally kept out of normal setup. Added `docs/claude-e-agentic/LLM_PROVIDER_SMOKE_TEST.md` and an opt-in Gemini smoke test (marked external/slow and skipped unless `POA_LLM_LIVE_TESTS=1` + `GOOGLE_API_KEY`) that runs the Phase 25A `ReviewRunner` through the normal safety/eval path on synthetic data. Mock remains default; the default test suite stays fully offline and needs no keys; no OpenAI Agents SDK, MCP, LangGraph, routes, persistence, frontend, or composer changes.
- Implemented Phase 25A P25A-T2 (reusable `agent_eval` harness) and P25A-T3 (tool-use governance, schema-only), mock-first and additive. The harness centralizes generated-output safety, forbidden wording, ungrounded-figure/invented-metric detection, prompt-privacy key/value scans, role-boundary checks, deterministic-evidence consistency, and failure classification, and now backs `ReviewRunner` runtime `eval_flags`. Tool governance defines evidence-tier-gated registry entries, a safe `ToolResult` envelope, and audit records (status/latency/cost only) with private-tier tools prohibited and no execution/MCP/external calls. No live calls, persistence, routes, frontend, real parallelism, role rename, OpenAI Agents SDK, MCP runtime, or TradingAgents. P25A-T4 stays deferred.
- Formalized the Phase 25A agentic-workflow foundation as architecture/planning only: revised the Agentic AI System Design Memo and drafted proposed ADR 0008 (Agentic Orchestration Spine) per Codex B's adjudication — a layered hybrid where Portfolio Copilot owns the safety spine permanently, Phase 25A starts with a thin app-owned runner (not LangGraph), LangGraph/SSE/MCP/parallelism are deferred and gated, the OpenAI Agents SDK is rejected, memory stays disabled, and the Phase 19 role rename is a separate slice. No code, route, persistence, frontend, live-provider, or TradingAgents behavior changed; all Phase 25A tasks remain proposed/not_started.
- Updated agentic AI ownership: Claude E is now the design/coding owner for future approved agentic workflow slices, Codex B reviews architecture/safety, and Codex C should not implement the agentic AI system workflow unless Codex A explicitly changes ownership.
- Expanded Phase 24A into a full Economic Calendar Awareness implementation plan: synthetic contracts first, deterministic app-owned importance classification, opt-in FMP Economic Calendar REST adapter, last-good refresh/cache, and a Dashboard macro calendar table. Ticker/company news, WebSockets, Forex Factory scraping, Trading Economics evaluation, and agent ingestion remain deferred.
- Completed P23B-T6 Browser-Local Symbol Recents LRU For Trade Review Autocomplete: the autocomplete now keeps a true per-browser "Recently viewed" list in a single UI-only localStorage key (`poa-symbol-recents`, capacity 5, newest-first, deduped). Empty focus shows local recents, or a neutral empty state when none exist — never backend default symbols and never "Symbol Not Found". Recents are recorded only on intentional selection, and an existing recent is promoted to the top on successful submit. Only the 7 public reference fields are persisted (no prices, quotes, volume, account/portfolio/broker context, prompts, LLM context, or trade history). No backend changes, no new endpoints, no provider/external/LLM calls, and no other storage key.
- Completed P23B-T3 Trade Review Autocomplete Uppercase And Recent Selection Polish: Symbol and Underlying inputs now force uppercase as the user types, so the displayed value, search query, and submitted payload are uppercase (`nvda` → `NVDA`, `nok` → `NOK`). Backend-owned ordering, recent/default list, section labels, and "Symbol Not Found" message are preserved verbatim; no frontend ranking/sorting/filtering, no validation wiring, no storage writes, no provider calls.
- Completed P23A-T4 Autocomplete UX V2 Recent And Contains Search Consumption: Trade Review autocomplete now shows the backend "Recently viewed" list on empty focus/input and exact-first backend search results while typing, consuming `result_mode`, `section_label`, items, and messages verbatim. Frontend does not rank, sort, filter, or fuzzy match. No quotes, prices, recommendations, validation wiring, storage writes, provider calls, or LLM/agent use.
- Completed P23A-T2 Trade Review Symbol Autocomplete Frontend: wired backend symbol search contracts into Trade Review Symbol and Underlying inputs with debounced typeahead, keyboard navigation, ARIA combobox pattern, "Symbol Not Found" handling, and no-search-on-mount guard. No prices, quotes, recommendations, or localStorage writes.
- Opened Phase 23A symbol lookup and Phase 24A economic calendar awareness as backend-first contract phases; symbol lookup is now complete through the local personal-demo path, and Phase 24A is scoped to macro calendar awareness with explicit `is_trading_signal=false` boundaries.
- Completed P20D-T4 Dashboard Claude Design visual refinement: added action context bar surfacing recommended_user_action_label and overall_review_mode from readiness contract, restructured readiness section with section label and section-level DemoChip, added account summary section headers, and improved spacing/density. All data from reviewed backend contracts rendered verbatim.
- Completed and reviewed Phase 20D Dashboard account-summary contract, cockpit cleanup, visual/content polish, Claude Design refinement, and P20D-T5 Product B pressure-test cleanup; the Dashboard now presents a tighter review-readiness cockpit, with synthetic headline values hidden or unmistakably non-real and agent-provider status demoted from the first viewport.
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
