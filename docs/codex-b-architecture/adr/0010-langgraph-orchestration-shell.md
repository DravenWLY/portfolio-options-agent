# ADR 0010: LangGraph as Orchestration Shell, App-Owned Safety Boundary

Status: accepted; implementation deferred
Date: 2026-07-03
Owner: Codex B - Architecture / Privacy / Safety
Drafted from: Claude E P34A-T8 and P34A-T8R design memos
Related: ADR 0008, ADR 0009, Phase 33A, Phase 34A, `PHASE_34A_LIVE_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md`

## Context

Portfolio Copilot now has an app-owned, tool-mediated Agent Team runner. The
runner builds a frozen evidence catalog, plans bounded backend tool requests,
executes tools through reviewed tier gates, produces role findings, audits
citations and safety, allows at most one bounded re-pass, synthesizes the report,
validates output, and freezes the saved report artifact for rerun-free readback.

The founder is interested in LangGraph because the future Agent Console may need
clearer developer traces, streamed per-node progress, and eventually durable
checkpoint/resume behavior. Claude E reviewed the current runner and the latest
TradingAgents v0.3.0 architecture as a reference only. The review found useful
patterns in graph modularization, state-delta-derived observability, and future
checkpointing, but also confirmed that Portfolio Copilot must reject LLM-owned
tool loops, debate-to-verdict flows, outcome memory, BUY/SELL/HOLD extraction,
hosted tracing, and full prompt/state dumps.

The question is whether LangGraph should replace the current runner, sit beside
it as an independent implementation, or wrap the same app-owned nodes as an
optional orchestration shell.

## Decision

Approve the **architecture** for a future dev-only LangGraph prototype as a
wrapper around the existing app-owned runner nodes, not as a replacement and not
as a second independent Agent Team implementation. On 2026-07-03, founder/Codex B
deferred implementation so Phase 34A can stay focused on live Agent Team quality,
real approved evidence, and the current app-owned runner.

LangGraph may own sequencing only. Portfolio Copilot continues to own:

- tool execution;
- source-rights gates;
- data-tier allowlists;
- citation ownership;
- prompt projection;
- live-provider gates;
- deterministic fallback;
- output-safety validators;
- freeze validation;
- saved-report persistence/readback semantics.

The approved graph topology is:

```text
saved evidence
-> build catalog
-> plan
-> backend tool execution
-> role findings
-> Evidence Auditor
-> optional bounded re-pass
-> Portfolio Manager synthesis
-> output safety
-> freeze
```

Any node failure must route to the same deterministic fallback posture as the
current runner. LangGraph must not introduce LLM-selected tools, `ToolNode`,
`MessagesState`, framework-owned prompt history, checkpoint persistence, route
wiring, hosted tracing, MCP, web search, TradingAgents runtime, or frontend LLM
calls in P34A-T8A/T8B.

## State Contract

The graph state must be a typed, validated mirror of the existing
`ToolMediatedRunState` and saved freeze contract.

Allowed in in-memory state for the dev prototype:

- the input `SavedEvidencePackageRead`;
- evidence catalog;
- planner plan;
- sanitized `ToolResult` envelopes;
- role finding sets;
- auditor record;
- open questions;
- safe provider-run metadata;
- provider mode;
- re-pass count;
- status/version metadata.

Forbidden in state:

- prompt text;
- raw provider requests or responses;
- completion text outside validated `claim_text`;
- LangChain message history;
- secrets or `.env` values;
- raw broker/provider payloads;
- account numbers, balances, holdings, quantities, lots, buying power, or raw
  private account data;
- URLs, raw SEC paths, filing bodies, or raw public-source payloads;
- cross-run memory or outcome reflection;
- any private-forbidden tier data.

Every node delta must pass the existing app-owned freeze/private-data validators
before it is merged into graph state. If validation fails, the graph must fail
closed to deterministic fallback.

Checkpoint persistence is not approved by this ADR. A future checkpoint design
requires a separate P35x contract and review.

## Tracing Policy

Hosted tracing is not approved. The graph runner must refuse to construct or run
when LangChain/LangSmith hosted tracing environment variables are set, including
the common tracing/API key/endpoint/project variables. This must be covered by a
test.

Approved T8A traces are dev-only, local-only, and derived from validated state
deltas after the node validation wrapper runs. They may contain only codes and
metadata, such as:

- node name;
- node status;
- wall time;
- warning codes;
- dropped-claim codes;
- tool names;
- evidence refs;
- evidence tiers;
- availability/freshness categories;
- token counts;
- mock/live provider metadata flags;
- plan/audit/contract versions.

Traces must not include prompt text, completion text, `claim_text` bodies,
`summary_payload`, raw scope values, source URLs, private values, account data,
or raw evidence values. Trace persistence, trace API exposure, and frontend trace
display are not approved in T8A/T8B.

## Parity Criteria

Before any route wiring or product adoption, the LangGraph runner must prove
parity against the current app-owned runner over synthetic/offline fixtures.

Required parity fields:

- role summaries;
- evidence references;
- warning codes;
- final synthesis markdown;
- frozen `tool_run_artifact`;
- provider-run metadata where deterministic or fake-provider comparable.

Volatile timestamps and wall-time trace values must be normalized before
comparison. Ordering must remain canonical.

The parity matrix must include degraded evidence, unavailable evidence, hard
blocks, provider failures, contradiction/re-pass, SEC metadata present/absent,
and no-provider-rerun readback.

## Consequences

Positive:

- We can evaluate LangGraph's developer-trace and graph-shape value without
  weakening the current runner.
- Rollback remains simple: default stays app-owned and the graph module can be
  removed without schema/read-contract changes.
- Future Agent Console work has a plausible path to durable progress streaming
  and checkpoint/resume, but only after a separate persistence contract.

Negative:

- T8A/T8B temporarily create two execution paths to maintain.
- The optional dependency increases supply-chain surface and must be separately
  approved and pinned.
- LangGraph adds little product value unless Agent Console durable runs become
  a real priority.

## Required Gates Before Implementation

- Founder/Codex A approval to add `langgraph` as an optional pinned backend extra.
- Codex B approval of the exact trace allowlist and kill-switch behavior.
- Claude B privacy review of the trace-event shape before any UI or persisted
  trace work.
- No checkpointer in T8A/T8B.
- No route wiring until parity and decision-gate review pass.
- No TradingAgents dependency, runtime execution, or copied source.

## Rejected Alternatives

### Replace the current runner with LangGraph

Rejected. This would move too much reviewed safety behavior into framework shape
at once and risks reopening citation, privacy, and fallback guarantees.

### Build an independent LangGraph Agent Team implementation

Rejected. Two separate implementations would drift and make parity unclear.

### Use LangGraph ToolNode or LLM tool-calling loops

Rejected. Portfolio Copilot's backend planner and tool registry own tool
selection and execution. The LLM may reason only over sanitized envelopes.

### Enable hosted LangSmith tracing

Rejected. Hosted tracing can capture prompts, completions, and full state. That
conflicts with Portfolio Copilot's no raw prompt/trace/private-data persistence
boundary.
