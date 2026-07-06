# Phase 34A-T11 — Agent Team Code Structure Review and Refactor Plan

Status: design only (no implementation, no runtime behavior change proposed).
Owner: Claude E. Reviewer: Codex B (structure/contracts) + founder (naming).
Reference: `../TradingAgents` v0.3.0 read-only for layout comparison — nothing
copied, nothing modified, no dependency taken.

---

## 1. Diagnosis — why the current structure feels unclear

`backend/app/services/agent_team/` is one flat directory of 22 modules
(~7,000 lines) that interleaves **four architectural layers** and **three
generations of runners** with no visible boundaries:

1. **The god-module hides the architecture.** `tool_mediated_report.py`
   (1,822 lines) contains the evidence catalog, the planner, the tool
   execution loop, deterministic role findings, the live-prose overlay, the
   Evidence Auditor, PM synthesis, summary assembly, the freeze payload, and
   several safety pattern sets. The product's signature pipeline
   (plan → tools → findings → audit → synthesize → validate → freeze) exists
   only as function order inside one file. Everything else in the folder
   looks flat because this file absorbed the actual structure.
2. **Two live generations coexist without demarcation.** The current product
   path (saved tool-mediated reports: `tool_mediated_report.py`, `tools.py`,
   `report_output_safety.py`, driven from
   `services/reports/agent_team_report.py`) sits beside the legacy P19/P25
   console-preview path (`orchestrator.py`, `review_runner.py`, `prompts.py`,
   `prompt_inputs.py`, `evidence.py`, `state.py`, `run_state.py`,
   `frontend_read.py`), which still backs the `/agent-team/…/preview` route
   and the standalone Gemini smoke. Nothing in naming or layout says which is
   canonical. `orchestrator.py` has **zero app importers** (tests only).
3. **Names don't say what things are.** `llm_provider.py` is the
   contracts/validators module, not a provider. `prompts.py` is legacy-only
   but sounds canonical (the live prompt actually lives inside
   `tool_mediated_report.py`). `tools.py` is three concerns (registry,
   envelope contract, executors). `state.py` vs `run_state.py` are different
   generations. Three *safety* modules (`output_safety`,
   `report_output_safety`, `prompt_safety`) sound interchangeable but have
   different scopes (provider output vs saved report vs prompt payloads).
4. **The provider stack is fine code in the wrong geography.** Six provider
   modules (config/factory/contracts/google/openai/mock, now plus the chain)
   are alphabetically shuffled among runners and validators, which is exactly
   the founder's "where do LLM clients live?" complaint.
5. **Evidence tiers/projections are split across packages** —
   `evidence_projection.py` (agent-safe deterministic projection, legacy+eval
   use) lives here while the public-role projection lives in
   `services/reports/public_evidence.py`. Defensible, but undocumented.

The structure is *safe* (validators everywhere, small blast radius per
module) — the problem is discoverability, not correctness.

## 2. TradingAgents comparison

What TA v0.3.0 does better structurally:

- **Package-per-concern with self-describing names**: `llm_clients/` (one
  vendor per file + `base_client.py` + `factory.py` + `model_catalog.py` +
  `capabilities.py` + `validators.py`), `agents/` (grouped by role family:
  `analysts/`, `researchers/`, `risk_mgmt/`, `managers/`, `trader/`),
  `graph/` (orchestration), `dataflows/` (data boundary). You can guess where
  anything lives from the question you're asking.
- **Factory as the single composition point** — nothing else constructs
  clients.
- **One file per agent** makes each role's behavior findable and reviewable.

What TA does *worse*, which Portfolio Copilot should not copy:

- `agents/utils/` is its own junk drawer (state, memory, tool wrappers,
  ratings, structured-output glue all mixed).
- **Tools live under `agents/utils/`** — fine when tools are thin fetch
  wrappers the LLM calls; wrong for PC, where the tool layer is a *governed
  privacy boundary* (registry allowlists, tiers, envelope validation) and
  deserves first-class placement.
- **No safety layer exists at all** — PC's validator modules have no TA
  analogue; they are the differentiator and must become more visible, not
  less.
- `agents/schemas.py` centers on Buy/Sell rating enums; the per-agent-file
  pattern there is LLM-closure-per-agent, which does not map to PC's
  deterministic finding builders + one gated live seam.

**Adopt:** package-per-concern; the `llm_clients/` name and shape; factory as
sole composition point; role behavior grouped in an `agents/` package.
**Reject:** tools-under-agents; utils junk drawer; per-agent LLM closures;
anything memory/rating/signal-shaped.

## 3. Recommended target structure

```
backend/app/services/agent_team/
  __init__.py                  # curated facade; import-compat shims during migration
  llm_clients/
    contracts.py               # ← llm_provider.py (request/response/protocol/validators)
    config.py                  # ← provider_config.py
    factory.py                 # ← provider_factory.py (resolution only)
    chain.py                   # ← ChainedLLMProvider + CHAIN_ADVANCE_STATUSES (split from factory)
    google.py                  # ← google_provider.py
    openai.py                  # ← openai_provider.py
    mock.py                    # ← mock_provider.py
  agents/
    roles.py                   # ← roles.py (definitions, allowlist metadata)
    findings.py                # ← deterministic role-finding builders + claim-text
                               #   helpers (split from tool_mediated_report.py)
    live_overlay.py            # ← live prompt seam + additive connective overlay
                               #   (_live_provider_request / _live_provider_role_findings)
  tools/
    envelopes.py               # ← ToolRequest/ToolResult/registry entry contracts + validation
    registry.py                # ← default registry, tiers, role allowlists
    executors.py               # ← execute_tool_request + per-tool projections
                               #   (all three split from tools.py)
  auditing/
    evidence_auditor.py        # ← audit_findings, contradiction detection,
                               #   hard-block flags (split from tool_mediated_report.py)
  orchestration/
    tool_mediated_runner.py    # ← catalog + planner + run loop + run-state dataclasses
    summary_freeze.py          # ← summary payload, PM synthesis, tool_run_artifact freeze
  safety/
    output_safety.py           # ← output_safety.py (provider output boundary)
    report_output_safety.py    # ← report_output_safety.py (saved report boundary)
    prompt_safety.py           # ← prompt_safety.py (prompt payload boundary)
  legacy_console/              # frozen P19/P25 preview path — do not extend
    orchestrator.py, review_runner.py, prompts.py, prompt_inputs.py,
    evidence.py, evidence_projection.py, state.py, run_state.py,
    frontend_read.py           # each with a deprecation docstring pointing at
                               # orchestration/tool_mediated_runner
```

Deliberate non-moves:

- **`agent_eval/` stays a sibling package** (it evaluates the team from
  outside; renaming to `agent_team/eval/` adds churn, no clarity).
- **`services/reports/agent_team_report.py` and `public_evidence.py` stay
  put** — they are report-domain services that *consume* the agent team; the
  freeze read-models stay in `schemas/reports.py`.
- **No behavior, wording, version-string, or schema changes anywhere.**
  `PLAN_VERSION`, `AUDIT_VERSION`, `LIVE_PROMPT_VERSION`, contract versions,
  validator patterns, and frozen artifact bytes are all invariants.

Answers to the numbered asks: Q5 yes with exactly the subpackages above
(minus `eval/`, minus `reports/`); Q8 yes; Q9 yes (legacy `prompts.py`
goes to `legacy_console/`, *not* `agents/`, so the old path is never
blessed); Q10 yes — the auditor is the product's signature component and
gets its own package for discoverability.

## 4. File-by-file migration map

| Current (`agent_team/`) | Target | Notes |
| --- | --- | --- |
| `llm_provider.py` | `llm_clients/contracts.py` | rename fixes "not actually a provider" |
| `provider_config.py` | `llm_clients/config.py` | |
| `provider_factory.py` | `llm_clients/factory.py` + `llm_clients/chain.py` | chain class split out |
| `google_provider.py` | `llm_clients/google.py` | |
| `openai_provider.py` | `llm_clients/openai.py` | |
| `mock_provider.py` | `llm_clients/mock.py` | |
| `roles.py` | `agents/roles.py` | |
| `tools.py` | `tools/{envelopes,registry,executors}.py` | 3-way split |
| `tool_mediated_report.py` | `orchestration/tool_mediated_runner.py`, `agents/findings.py`, `agents/live_overlay.py`, `auditing/evidence_auditor.py`, `orchestration/summary_freeze.py` | 5-way split; old module becomes a re-export facade until R6 |
| `output_safety.py` | `safety/output_safety.py` | |
| `report_output_safety.py` | `safety/report_output_safety.py` | |
| `prompt_safety.py` | `safety/prompt_safety.py` | |
| `orchestrator.py` | `legacy_console/orchestrator.py` | zero app importers; candidate for deletion after Codex A decision |
| `review_runner.py` | `legacy_console/review_runner.py` | still backs `/agent-team/…/preview` + standalone smoke |
| `prompts.py`, `prompt_inputs.py` | `legacy_console/` | legacy prompt path |
| `evidence.py`, `evidence_projection.py` | `legacy_console/` | verify `agent_eval` importers during the slice; if eval imports projection, it re-exports via facade |
| `state.py`, `run_state.py` | `legacy_console/` | generation-2 state models |
| `frontend_read.py` | `legacy_console/frontend_read.py` | console read model |

## 5. Legacy ReviewRunner policy (Q7)

**Quarantine now, decide later, never extend.** The legacy path stays fully
functional (route + smoke depend on it) but moves under `legacy_console/`
with deprecation docstrings and a README note: "P19/P25 preview path;
superseded by the tool-mediated saved-report pipeline; bug-fix only." A
separate product decision (Codex A + founder, out of scope here) chooses
between (a) re-pointing the Agent Console preview at the tool-mediated
runner, then deleting the package, or (b) keeping it as a lightweight
preview. The refactor must not couple to that decision.

## 6. Safe migration sequence (proposed task IDs)

Every slice is **pure moves + import-compat shims**, one slice per review,
full suite green before and after, zero behavior diffs:

- **P34A-T11A — `llm_clients/`** (first: founder's clearest pain, lowest
  risk). Move 6 provider modules; split `chain.py`; leave one-line
  re-export shims at every old path (`provider_factory.py` →
  `from app.services.agent_team.llm_clients.factory import *` style, with
  explicit names, no `*`). Add a facade test asserting canonical symbols
  import from both old and new paths.
- **P34A-T11B — `safety/` + `agents/roles.py`** with shims.
- **P34A-T11C — `legacy_console/`** move + deprecation docstrings + shims;
  flip the two app importers (`api/routes/agent_team.py`,
  `schemas/agent_team.py` if needed) to the new path in the same slice.
- **P34A-T11D — split `tools.py`** into `tools/` (3 modules) with
  `tools.py` facade preserved.
- **P34A-T11E — split the god-module** into the 5 targets;
  `tool_mediated_report.py` remains a facade re-exporting the complete old
  symbol surface (tests import ~30 names from it). Require a before/after
  symbol inventory in the slice report.
- **P34A-T11F — importer flip + shim removal.** Move external importers
  (`services/reports/*`, `agent_eval/*`, `schemas/*`, routes, tests) to
  canonical paths; delete facades/shims; final full-suite + live-smoke
  re-run; update `docs/codex-b-architecture/architecture.md` module map.

Rollback: each slice is a revertable commit of moves+shims; because shims
keep every old import path alive through T11E, reverting any single slice
never breaks neighbors. No DB, schema, env, or contract migrations involved.

## 7. Test and review gates (Q13)

Per slice: `pytest tests/services/agent_team tests/services/agent_eval`
(372 at time of writing) + `tests/unit/test_report_agent_schemas.py` (104) +
`git diff --check`; before T11C and after T11F additionally
`tests/api/test_reports.py` and full backend `pytest`. Invariant gates that
must never change across the whole sequence: the byte-stable frozen-artifact
eval (`test_s1_to_s3_end_to_end_summary_is_valid_byte_stable_and_no_gaps_cited`),
plan/audit/prompt version constants, validator pattern sets (checksum the
files in review), and the readback no-rerun tests. After T11F: one opt-in
route-backed live smoke re-run (founder-authorized) to confirm the live path
is untouched. Codex B reviews every slice; Claude B is only needed if any
safety-module *content* changes (it must not — moves only).

## 8. Risks

| Risk | Mitigation |
| --- | --- |
| Hidden import cycles surface when splitting the god-module | The current file already imports findings→auditor→summary in one namespace; split along the existing call DAG (runner → findings → auditor → summary), keep shared constants in the runner module, and let the facade re-export |
| Test-only import breakage (~60 imports across 21 test files) | Shims until T11F; T11F updates tests mechanically in the same commit as importer flips |
| Silent behavior drift during "mechanical" moves | Byte-stable artifact gate + full suite per slice + no-logic-edit rule stated in every Codex C prompt |
| `dataclasses`/pydantic validators re-running differently after moves | None expected (import-path-independent), but the freeze tests would catch it |
| Two sources of truth during migration confuse contributors more | Shims are one line each with a `# moved to …` comment; sequence is 6 short slices, not a long dual period |

## 9. Codex C implementation prompt — first slice (P34A-T11A)

```text
Agent: Codex C
Task: P34A-T11A - Extract agent_team/llm_clients package (pure move, no behavior change)
Mode: backend refactor; one task; stop for Codex B review after.

Design reference: docs/claude-e-agentic/PHASE_34A_T11_AGENT_TEAM_STRUCTURE_REVIEW.md
(sections 3, 4, 6, 7 binding).

Scope — moves and shims only; zero logic/wording/version/validator changes:

1. Create backend/app/services/agent_team/llm_clients/ with:
   contracts.py  <- full content of llm_provider.py
   config.py     <- provider_config.py
   factory.py    <- provider_factory.py minus ChainedLLMProvider
   chain.py      <- ChainedLLMProvider + CHAIN_ADVANCE_STATUSES (imported by factory)
   google.py     <- google_provider.py
   openai.py     <- openai_provider.py
   mock.py       <- mock_provider.py
   __init__.py   re-exporting the same names the old modules exported.
2. Replace each old module (llm_provider.py, provider_config.py,
   provider_factory.py, google_provider.py, openai_provider.py,
   mock_provider.py) with an explicit named re-export shim:
   "# moved to app.services.agent_team.llm_clients.<name>" + explicit
   from-imports + __all__. No wildcard imports. Do not change
   app/services/agent_team/__init__.py exports' names.
3. Do NOT update any other importers in this slice (they keep working via
   shims). Do NOT touch tool_mediated_report.py, tools.py, safety modules,
   legacy modules, tests (except the new test below), schemas, or routes.
4. Add tests/services/agent_team/test_llm_clients_layout.py asserting:
   - canonical imports work (llm_clients.contracts/config/factory/chain/
     google/openai/mock expose the expected public names);
   - legacy paths still import and are the SAME objects
     (assert app.services.agent_team.provider_factory.resolve_llm_provider
      is app.services.agent_team.llm_clients.factory.resolve_llm_provider);
   - ChainedLLMProvider imported from both factory (compat) and chain paths
     is the same class.

Invariants (verify, do not edit): DEFAULT_LIVE_MODEL and all config defaults;
CHAIN_ADVANCE_STATUSES membership; LLM_PROVIDER_CONTRACT_VERSION; validator
pattern sets byte-identical (pure moves); no .env/secret/frontend/LangGraph/
TradingAgents/new-source changes.

Verification: cd backend && ./.venv/bin/python -m pytest
tests/services/agent_team tests/services/agent_eval -q;
tests/unit/test_report_agent_schemas.py -q; git diff --check. Report counts.

Return per docs/shared/AGENT_REPORT_FORMAT.md with PASS/BLOCKED ask for
Codex B, including a moved-symbol inventory (old path -> new path).
```

## 10. Decisions requested (Codex B / founder)

1. Approve the target package names (`llm_clients`, `agents`, `tools`,
   `auditing`, `orchestration`, `safety`, `legacy_console`) — founder
   explicitly cares about this vocabulary.
2. Approve keeping `agent_eval/` and `services/reports/*` where they are.
3. Approve the legacy policy (quarantine + bug-fix-only) and schedule the
   separate Codex A decision on the console preview route's future.
4. Confirm `orchestrator.py` may be deleted at T11F if it still has no app
   importers (tests would migrate to `review_runner` equivalents or move
   into `legacy_console` coverage).
