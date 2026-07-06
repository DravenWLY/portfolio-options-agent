# Phase 34A-T11 — Agent Team Package Structure (final map)

Status: implemented (T11A–T11F). Behavior-preserving reorganization of
`backend/app/services/agent_team/`; no runtime behavior change, no validator
weakening. Each slice was Codex B-reviewed PASS.

## End-state layout

```
backend/app/services/agent_team/
  __init__.py                       # package facade (canonical imports)
  tool_mediated_report.py           # RETAINED facade -> orchestration/ + auditing/
  llm_clients/                      # LLM provider layer (T11A)
    contracts.py    # request/response/protocol dataclasses + payload validators
    config.py       # sanitized provider config + POA_LLM_MODEL_CANDIDATES parsing
    factory.py      # backend-owned provider resolution (no client-side selection)
    chain.py        # ordered same-provider model-candidate fallback
    google.py · openai.py · mock.py # provider adapters
  agents/                           # role/agent layer (T11B)
    roles.py        # role vocabulary + prompt-boundary metadata
  tools/                            # tool governance + execution (T11D)
    envelopes.py    # tier constants, contracts, validators, ToolRequest/Result/RegistryEntry
    registry.py     # default reviewed registry + role allowlists
    executors.py    # execute_tool_request + per-tool saved-evidence projections
  auditing/                         # Evidence Auditor (T11E)
    evidence_auditor.py # audit_findings, fail-closed hard blocks, contradiction detection
  orchestration/                    # tool-mediated runner (T11E)
    models.py       # shared dataclasses + pipeline constants (breaks runner<->auditor cycle)
    tool_mediated_runner.py # catalog/planner/run loop/findings/live overlay/synthesis/freeze
  safety/                           # validator layer (T11B)
    output_safety.py · report_output_safety.py · prompt_safety.py
  legacy_console/                   # QUARANTINED P19/P25 preview path (T11C) — bug-fix only
    orchestrator.py · review_runner.py · prompts.py · prompt_inputs.py ·
    evidence.py · evidence_projection.py · state.py · run_state.py · frontend_read.py
```

Unchanged siblings (Codex B-approved to leave in place): `agent_eval/`
(evaluates the team from outside), `services/reports/agent_team_report.py` +
`public_evidence.py` (report-domain services that consume the team),
`schemas/reports.py` (freeze read-models).

## Old → new import map (flat shims removed in T11F)

| Removed flat path (`agent_team.…`) | Canonical path |
| --- | --- |
| `llm_provider` | `llm_clients.contracts` |
| `provider_config` | `llm_clients.config` |
| `provider_factory` | `llm_clients.factory` (chain in `llm_clients.chain`) |
| `google_provider` / `openai_provider` / `mock_provider` | `llm_clients.google` / `.openai` / `.mock` |
| `output_safety` / `report_output_safety` / `prompt_safety` | `safety.output_safety` / `.report_output_safety` / `.prompt_safety` |
| `roles` | `agents.roles` |
| `orchestrator` / `review_runner` / `prompts` / `prompt_inputs` / `evidence` / `evidence_projection` / `state` / `run_state` / `frontend_read` | `legacy_console.<same>` |

`tools` and `tool_mediated_report` are **retained package/facade APIs** (not
removed): `from agent_team.tools import …` and
`from agent_team.tool_mediated_report import …` continue to resolve to the same
objects, now re-exported from `tools/*` and `orchestration/` + `auditing/`.

## Guardrails

- `tests/services/agent_team/test_agent_team_no_flat_shims.py` fails if any of
  the 19 removed flat shims is reintroduced, and asserts the canonical packages
  + retained facades still expose their surface.
- `test_tools_layout.py` and `test_orchestration_layout.py` assert the
  package/facade identity for the two retained facades.

## Model-id note (T11A)

`llm_clients/config.py` `DEFAULT_LIVE_MODEL = "gemini-2.5-flash-lite"` verified
as a current stable generateContent id on
https://ai.google.dev/gemini-api/docs/models (2026-07-06). The live model and
`POA_LLM_MODEL_CANDIDATES` chain stay env-configured. Note `gemini-3-flash` is
not a stable bare id there (it is `gemini-3-flash-preview`); the founder should
verify any candidate list against current stable ids.

## Deferred cleanup

- Per-module unused imports in `orchestration/models.py`,
  `auditing/evidence_auditor.py`, and `orchestration/tool_mediated_runner.py`
  (full uncurated headers were kept for behavior-exactness during the split;
  lint-only, no runtime effect).
- `legacy_console/orchestrator.py` has no app importers (test-only). Deleting
  it entirely is a separate call pending Codex B/founder approval (T11 kept it).
- Further decomposition of `tool_mediated_runner.py` (findings / live overlay /
  summary-freeze into their own modules) was intentionally deferred — the
  founder chose the conservative "relocate + extract auditor" scope for T11E.
