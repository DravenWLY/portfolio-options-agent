# Agent Team Tool-Mediated Architecture Diagram — Notes

Task: P34A-T8D (Claude E, 2026-07-03). Editable source:
`agent-team-tool-mediated.drawio`; exports: `agent-team-tool-mediated.png`
(embedded diagram XML — opening it in draw.io recovers the editable diagram)
and `agent-team-tool-mediated.svg` (also embedded). Regenerate exports with:

```bash
drawio -x -f png -e -s 2 -o agent-team-tool-mediated.png agent-team-tool-mediated.drawio
drawio -x -f svg -e -o agent-team-tool-mediated.svg agent-team-tool-mediated.drawio
```

## What the diagram shows

Six horizontal lanes plus a blocked band and a legend:

1. **Frontend** — the golden-path user flow (Trade Review → Save Evidence
   Snapshot → Reports → Generate Agent Team Report → Reopen Saved Report).
   No LLM calls, tools, or provider keys in the browser.
2. **Backend API** — the route spine (`portfolio-preview`,
   `from-trade-review`, `agent-team-report`, report readback) and the amber
   backend-only generation-mode gate
   (`POA_AGENT_TEAM_REPORT_GENERATION_MODE`, default deterministic template).
3. **Evidence & Tools (backend-owned)** — deterministic calculations → saved
   review artifact → frozen `SavedEvidencePackageRead` (public/agent_safe
   tiers only) → role-allowlisted tool registry → sanitized `ToolResult`
   envelopes. The seven approved tools are listed in the registry box; the
   two rights-gated metadata tools (FRED `economic_awareness_context`,
   SEC EDGAR `sec_recent_filings_metadata`) are amber.
4. **Agent Runtime (app-owned runner)** — planner (clamped) → backend tool
   execution → role agents → Evidence Auditor → bounded re-pass (≤1, amber)
   → PM synthesis → output safety validators → freeze, with a gray
   fail-closed deterministic-fallback sink. The dashed amber frame is the
   optional dev-only LangGraph wrapper from P34A-T8: sequencing + local
   redacted tracing only, no hosted tracing (env kill-switch), no checkpoint
   persistence until a separate contract.
5. **External Providers (gated)** — the live LLM boundary (Gemini via
   `LLMProviderResolution`; disabled by default; sanitized envelopes in,
   validated prose out, unsafe/failed output falls back to the deterministic
   finding; saved readback never re-runs the provider) and the backend-only
   gated acquisition lane (FRED / SEC EDGAR normalized metadata → frozen
   evidence only, outside agent runs).
6. **Persistence (frozen)** — Reports DB holding saved review artifacts,
   evidence packages, saved reports, and the frozen `tool_run_artifact`.
   Readback reads frozen artifacts only: no recompute from current account
   state, no tool/provider re-runs, no raw prompts/traces/payloads persisted.

**Blocked band (red)** — broker execution/order placement; raw
brokerage/private data in prompts or tool results; generic public news
providers; web search/MCP/TradingAgents runtime; frontend LLM/tool calls;
direct LLM tool calling.

**Color legend** — green: approved/reviewed path; amber: gated / opt-in /
approval required; dashed amber: optional dev-only (planned); red: blocked.

## Sources

Drawn from `backend/app/services/agent_team/tool_mediated_report.py`,
`tools.py`, `report_output_safety.py`, the P34A-T0 contract
(`docs/codex-b-architecture/PHASE_34A_LIVE_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md`),
and the P34A-T8/T8R LangGraph design memos in `docs/claude-e-agentic/`.
Synthetic labels only; no real account data anywhere in the diagram.

## Known simplifications

- The five role agents are one box; per-role evidence allowlists live in
  `report_output_safety.py` (`ROLE_ALLOWED_EVIDENCE_KEYS`), not the diagram.
- The SEC/news deterministic-listing special case (no live overwrite in M1)
  is not drawn separately.
- Blocked-actionability drafts (deterministic draft without
  `tool_run_artifact`) are folded into the fallback sink.
