# Phase 34A-T7A - Live Prototype Readiness Audit

Status: readiness audit
Owner: Codex B - Architecture / Contract / Privacy
Date: 2026-07-02

## Verdict

**NO-GO for a true end-to-end live saved-report smoke today.**

The core service-level live runner is ready enough for backend-only smoke once
credentials are explicitly authorized, but the product route used by the golden
path still calls the older deterministic-template report generator. Therefore
the current app cannot yet prove:

`Trade Review -> save evidence snapshot -> Reports -> Generate report -> live tool-mediated Agent Team report -> frozen readback`

without a backend wiring slice.

## What Is Ready

- Live LLM use is disabled by default.
- `LLMProviderResolution` / provider factory controls provider activation.
- Provider config records only key availability, never secret values.
- Tool-mediated prompts send sanitized `ToolResult` envelopes only.
- Prompt envelopes exclude `summary_payload`, raw saved evidence, raw SEC/FRED
  payloads, raw private data, prompts/traces, and secrets.
- Provider output never owns citations; backend-owned refs/caveats are
  reattached.
- Unsafe provider output fails closed to deterministic floor where available.
- Hard blocks are not retried; fixable unsupported/contradiction failures are
  bounded.
- `tool_run_artifact` freezes safe tool/model metadata for readback.
- Approved public-source lanes are narrow:
  - SEC EDGAR company-profile metadata;
  - FRED economic awareness metadata;
  - SEC EDGAR recent filing metadata.
- General public-news providers remain blocked.

## Blocking Gap

`POST /users/{user_id}/reports/{thread_id}/agent-team-report` still calls
`generate_agent_team_report_for_thread(...)`, which builds the deterministic
template summary.

The endpoint is not yet wired to:

- resolve a live/mock `LLMProviderResolution`;
- choose the tool-mediated summary path through a backend-only gate;
- preserve deterministic-template default behavior;
- attach/generate reviewed public evidence needed by the tool pack;
- persist the resulting `tool_run_artifact` through the saved report route;
- verify route-level readback without rerunning providers/tools.

Until that is done, P34A can only run service-level live tests, not the live
golden-path saved-report smoke.

## Required Pre-Smoke Conditions

Before any live smoke:

1. Commit or explicitly close the current P34A-T6C/T6D backend/doc changes.
2. Land backend route wiring for a tool-mediated report generation mode that is
   disabled by default.
3. Keep deterministic-template report generation as the default.
4. Enable live mode only through backend-owned configuration and explicit
   founder credential authorization.
5. Do not read, print, commit, or echo `.env` or secret values.
6. Use only approved tools/sources.
7. Run one stock/ETF and one simple-options saved report.
8. Confirm saved report readback does not rerun provider/tool calls.
9. Confirm no private leaks, raw URLs/payloads, advice/order/execution,
   safe-to-trade, ready-to-trade, guaranteed-return, or AI-stock-picker wording.

## Next Task

Open `P34A-T7B - Tool-mediated saved-report generation route wiring`.

Owner: Codex C.
Reviewer: Codex B.

Goal: wire the saved-report generation route to the reviewed tool-mediated
runner behind a backend-only disabled-by-default gate, preserving deterministic
template generation as default. This is the missing bridge before a live
end-to-end smoke can be meaningful.

## Not Approved Yet

- Frontend changes.
- New read fields.
- General public-news tools.
- Web search/scraping.
- MCP or TradingAgents runtime.
- LangGraph orchestration.
- Production/public activation.
