# Phase 21A Realtime Agent Console Backend Contract

Status: paused design reference - not approved for implementation
Date: 2026-05-24
Owner: Codex B - Architecture / Systems / Integration

## PM Pause Note

On 2026-05-25, Codex A paused further agentic/realtime architecture and
implementation while the founder studies agentic AI concepts and evaluates
which patterns genuinely belong in Portfolio Copilot. This draft is retained
as reference material only. It does not authorize Codex C implementation or
Claude A activation of the Agent Console composer.

## Draft Recommendation Before Pause

**Previously proposed:** prepare Phase 21A as a backend-only, mock-first phase.

Phase 21A should supply the durable and realtime-safe backend foundation for
the Agent Console prototype only if PM later reactivates this work.
It must not activate the prototype composer in production UI until the backend
contracts have been implemented and reviewed.

The recommended transport is:

- normal authenticated `POST` requests for creating analysis runs and
  submitting follow-up questions;
- Server-Sent Events (SSE) for ordered run/stage/transcript progress;
- ordinary `GET` endpoints for reload and recovery.

Do not introduce Socket.IO or native WebSocket in Phase 21A. The first console
needs one-way server progress after discrete user commands, not simultaneous
bidirectional control or streaming market data.

## Why This Phase Was Drafted

Phase 19 established the agent-team boundary:

- Phase 19A added five app-owned roles and a mock-provider analysis response;
- Phase 19B added the backend-only real-provider gate while keeping mock as
  default;
- Phase 19C added agent-safe deterministic evidence and role-specific prompt
  boundaries.

Phase 20C-T2 translated the prototype Agent Console into a static five-zone
layout:

- run summary at the top;
- stage and role pipeline at left;
- transcript in the center;
- deterministic evidence at right;
- a disabled follow-up composer below the transcript.

The missing foundation is not more visual styling. It is a safe persisted
conversation/run model and an event contract that allows the console to show
role progress and later accept follow-up questions without bypassing privacy,
actionability, or provider-safety rules.

## Existing Baseline

The current endpoint `POST /agent-team/trade-review-analysis/preview` is a
valuable stable regression surface. It is stateless and returns a completed or
partially completed safe console read model. Its orchestrator deliberately
records the `persist_run_steps` stage as skipped because no persistent console
run exists yet.

If Phase 21A is later reactivated, it must preserve that preview endpoint
unchanged while adding an opt-in persisted run path. The preview remains useful
for deterministic demo and UI smoke tests.

Existing reusable foundations include:

- `AgentTeamAnalysisConsoleRead` and five approved roles;
- the Phase 19C agent-safe deterministic evidence projection;
- strict prompt/input and generated-output validation;
- safe provider-status and partial-run vocabulary;
- app-owned `agent_runs`, `agent_steps`, `report_threads`, and
  `report_messages` persistence primitives, subject to a Codex C mapping
  assessment.

## Non-Goals

Phase 21A does not include:

- live Google/Gemini calls or changes to the Phase 19B provider gate;
- TradingAgents execution, public research fetches, news providers, or market
  data providers;
- broker calls, order placement/cancellation, or account mutations;
- frontend implementation or enabling the disabled composer;
- token-by-token model streaming;
- raw prompt, raw provider response, provider trace, or exception-body
  persistence;
- market quote streaming, option-chain UI, screener, or trading-terminal UI.

## Transport Decision

### Selected Pattern

Use HTTP commands plus an SSE event feed.

| Need | Contract direction |
| --- | --- |
| Start an analysis | `POST /agent-team/analysis-runs` |
| Read current safe snapshot | `GET /agent-team/analysis-runs/{run_reference}` |
| Receive live progress | `GET /agent-team/analysis-runs/{run_reference}/events` as SSE |
| Reload transcript | `GET /agent-team/analysis-threads/{thread_reference}/messages` |
| Ask a follow-up | `POST /agent-team/analysis-runs/{run_reference}/follow-ups` |

### Why SSE First

- A user submits a discrete command; the server then emits one-way progress.
- SSE is browser-native, reconnectable, and supports event IDs for safe
  resume/replay.
- The system can emit only validated stage/message objects rather than unsafe
  partial model tokens.
- It preserves existing HTTP authentication/local-access handling and has a
  smaller failure surface than a bidirectional socket protocol.
- This matches the existing architecture preference for SSE agent progress.

### WebSocket / Socket.IO Deferral

Consider a socket protocol only after a reviewed need exists for simultaneous
bidirectional in-run commands, collaborative sessions, cancellation, or other
control not adequately represented by HTTP commands. Do not use a WebSocket
decision for unrelated market-data streaming to drive the Agent Console.

## Phase 21A Execution Flow

### Initial Analysis Run

1. Client submits the existing safe portfolio-backed trade-review input shape
   to `POST /agent-team/analysis-runs`.
2. Backend creates an opaque thread reference and run reference, attaches the
   deterministic safe evidence snapshot, and returns an accepted response.
3. Backend evaluates the existing app-owned five-role sequence:
   fundamentals analyst, news analyst, technical analyst, risk management
   agent, portfolio manager agent.
4. SSE emits safe lifecycle events and validated transcript messages in order.
5. Provider failures produce role-unavailable events and a partial completion
   result; deterministic evidence remains available.
6. Client can reload the final snapshot and transcript through ordinary `GET`
   reads.

### Follow-Up Run

1. Client submits a sanitized question with either one approved target role or
   broadcast-to-team mode.
2. Backend validates question content, routing, references, and safe context
   availability.
3. Backend creates a follow-up run inside the same analysis thread, returning
   a new opaque run reference.
4. SSE for the follow-up run emits validated events and message additions.
5. Transcript reload shows the original analysis and follow-up in sequence.

Quick-question suggestions are frontend conveniences only. When submitted,
they become ordinary follow-up question text and pass through the same backend
validation and routing policy.

## Conceptual API Contracts

Endpoint names are recommended; Codex C may propose a small naming refinement
before implementation if it preserves the boundary and does not alter the
existing preview route.

| Endpoint | Purpose | Key boundary |
| --- | --- | --- |
| `POST /agent-team/analysis-runs` | Create persisted mock-first initial analysis | Request reuses safe portfolio-preview input; no client provider or private metadata |
| `GET /agent-team/analysis-runs/{run_reference}` | Read run summary/evidence snapshot | Safe read model only |
| `GET /agent-team/analysis-runs/{run_reference}/events` | Stream SSE progress/replay | Validated event records only; no raw tokens |
| `POST /agent-team/analysis-runs/{run_reference}/follow-ups` | Add a follow-up run | Sanitized question plus approved role routing only |
| `GET /agent-team/analysis-threads/{thread_reference}/messages` | Reload transcript | Ordered validated user-visible message records |

Keep:

- `POST /agent-team/trade-review-analysis/preview` unchanged and stateless.

## Conceptual Read and Write Models

### `AgentConsoleRunCreateRequest`

Reuse the approved safe portfolio-backed review request used by the existing
analysis preview. The client must not send provider, model, prompt template,
temperature, account details, raw evidence, actionability, or freshness
metadata.

### `AgentConsoleRunAcceptedRead`

- `thread_reference`: opaque frontend-safe reference;
- `run_reference`: opaque frontend-safe reference;
- `run_status`: queued/running/completed/partially_completed/failed-safe
  vocabulary finalized by Codex C against existing types;
- `workflow_version`;
- `is_mock`;
- `analysis_only`;
- `events_path`: relative backend path for the SSE subscription.

### `AgentConsoleThreadRead`

- opaque thread and current run references;
- safe review reference and supported trade-flow label;
- created/updated display timestamps;
- workflow version and mock/provider display status;
- actionability status;
- separate broker snapshot freshness and market quote freshness summaries;
- analysis-only and no-execution safety labels.

### `AgentConsoleTranscriptMessageRead`

- opaque `message_reference`;
- monotonically ordered `sequence`;
- `message_kind`:
  `user_trade_intent_summary`, `deterministic_evidence_attachment`,
  `agent_role_output`, `manager_synthesis`, `provider_warning`,
  `system_status`, or `user_follow_up`;
- optional approved `role_name`;
- message status and provider status, where applicable;
- validated user-visible plain text or safe markdown string;
- generated timestamp, mock indicator, and analysis-only label.

The frontend may render this record as text. It must not receive raw model
prompts, raw provider responses, chain-of-thought, tool traces, private fields,
or internal persistence IDs.

### `AgentConsoleEventRead`

- monotonically increasing sequence and opaque event reference;
- opaque thread and run references;
- event type:
  `run_started`, `stage_started`, `stage_completed`, `message_appended`,
  `role_unavailable`, `run_partially_completed`, `run_completed`,
  `run_failed`, or `heartbeat`;
- safe stage metadata or a safe transcript message record;
- timestamp.

Do not emit token chunks in Phase 21A. A message is emitted only after the
existing output-safety boundary accepts it.

### `AgentConsoleFollowUpCreateRequest`

- `question_text`: required, length limited, and safety validated;
- `target_mode`: `specific_role` or `broadcast_team`;
- `target_role`: one approved role only when `target_mode=specific_role`;
- optional safe prior run reference for UI traceability.

It must not include custom prompts, arbitrary evidence attachments, provider
selection, model selection, freshness/actionability overrides, raw portfolio
data, account/broker/provider identifiers, or credentials.

## Persistence Recommendation

Use app-owned persistence; do not introduce an external chat store.

Codex C must first evaluate whether existing primitives can safely represent
the console:

| Need | Preferred existing primitive | Rule |
| --- | --- | --- |
| Analysis or follow-up execution | `agent_runs` | Store safe status/reference metadata only |
| Role/stage progress | `agent_steps` | Store validated stage outcomes only |
| Conversation container | `report_threads` if semantically compatible | Expose an opaque console-thread reference, not DB ids |
| Transcript entries | `report_messages` if its safe message contract fits | Store frontend-safe rendered content only |
| SSE replay | Persisted safe step/message sequence or minimal safe event record | No raw provider stream persistence |

If existing thread/message tables cannot represent follow-up transcript
semantics without confusing report history, Codex C must stop after a mapping
memo and request approval for a minimal console-specific persistence addition.
It must not quietly overload report tables or add a migration as part of a
route implementation.

## Prompt and Role Boundaries

### Public Analysts

`fundamentals_analyst`, `news_analyst`, and `technical_analyst` may receive:

- public or synthetic ticker/company context;
- sanitized user question text relevant to public evidence;
- safe provider mode labels.

They must not receive:

- deterministic portfolio projection;
- holdings, positions, cash, collateral, buying power, or account values;
- actionability or broker snapshot context;
- account/broker/provider identifiers;
- prior transcript text containing portfolio-specific evidence.

If directly asked a portfolio-specific follow-up, the backend should either
route it to an eligible role or return a safe limitation message rather than
leaking portfolio evidence to a public analyst.

### Risk Management Agent

May receive:

- sanitized TradeIntent summary;
- agent-safe deterministic evidence projection;
- actionability and separate freshness statuses;
- sanitized prior role summaries needed for risk interpretation;
- sanitized question text.

### Portfolio Manager Agent

May receive:

- prior validated agent summaries;
- agent-safe deterministic evidence projection;
- actionability and separate freshness statuses;
- sanitized question text.

It produces educational synthesis and limitations, never order instructions,
recommendations, or invented financial metrics.

### Broadcast

Broadcast must not mean every role gets the same prompt. It means the backend
runs the approved role sequence while constructing role-specific prompt inputs
under the boundaries above.

## Data and Safety Boundary

All requests, persistence writes, SSE payloads, and reads must reject or omit:

- raw holdings, positions, quantities, tax lots, or account-level allocations;
- cash balances, buying power, free cash, account values, or raw collateral;
- account, broker, provider, provider-account, or provider-contract ids;
- raw CSV rows, provider payloads, raw metadata, or trade-journal entries;
- account-specific policy thresholds;
- credentials, API keys, access tokens, secrets, or portal URLs;
- raw prompt templates, provider traces, exception bodies, or chain-of-thought.

The existing prohibited wording/output checks remain mandatory:

- no order placement, cancellation, or execution instructions;
- no guaranteed-return language;
- no trade-readiness claims;
- no "you should buy/sell" advice;
- no LLM-generated financial metrics.

Follow-up text is untrusted input. It must have length limits and private-value
guards before being used in prompt construction or stored for display. A safe
rejection should tell the user to ask about the reviewed proposal and its
displayed evidence, not paste account records, broker exports, or credentials.

## Failure, Rate-Limit, and Reconnect Behavior

- Mock provider remains default for all Phase 21A tests and local acceptance.
- A role-level timeout/rate-limit/quota/provider failure emits a safe
  `role_unavailable` event and keeps deterministic evidence available.
- The run resolves to `partially_completed` when useful safe output survives.
- SSE closes gracefully after a terminal event; it must not leak stack traces
  or raw exceptions.
- Every non-heartbeat event has a monotonically increasing ID.
- A reconnect with `Last-Event-ID` replays only missing safe events and then
  resumes live progress, or returns the terminal state if already complete.
- Heartbeat events contain no analysis content.

## Frontend Handoff After Backend Review

Claude A may activate the prototype console interactions only after Phase 21A
backend implementation and safety/integration review pass.

The later frontend slice may:

- start or select a safe analysis run;
- subscribe to the SSE event path returned by the backend;
- render pipeline states and transcript messages;
- keep the right rail limited to deterministic safe evidence;
- enable the follow-up composer with role/broadcast routing after its endpoint
  is reviewed.

It must not:

- call an LLM, provider, broker, or TradingAgents directly;
- implement socket transport independently;
- surface raw prompt/provider payloads or private portfolio data;
- calculate financial metrics;
- represent analysis as advice or execution.

## Review Gates

### Codex B Gate Before Backend Implementation

- Founder/Codex A approves the SSE-first decision and conceptual API boundary.
- Existing persistence primitives are explicitly mapped before a migration is
  considered.

### Codex C Implementation Gates

- Synthetic/mock tests first.
- Contract and privacy tests for every request, read, and event payload.
- Provider failure, reconnect/replay, and role-routing tests.
- No frontend changes and no live external calls.

### Claude B Safety Gate

- Transcript/event privacy boundary.
- Follow-up prompt and output safety.
- Partial-run/rate-limit clarity.
- No advice/execution/guarantee leakage.

### Codex B Final Integration Gate

- Persistence mapping is coherent and recoverable.
- Existing stateless preview is unchanged.
- SSE/HTTP command contract is stable for Claude A.
- Deterministic evidence remains separate from commentary.

## Proposed Delivery Order If Reactivated

1. Codex A explicitly reactivates a scoped Phase 21A slice after reviewing
   founder learning and any revised product direction.
2. Re-review this contract and ADR 0007 before implementation.
3. `P21A-T1`: map persistence and add typed safe thread/run/transcript/event
   contracts.
4. `P21A-T2`: add mock-first persisted initial-run and read endpoints.
5. `P21A-T3`: add SSE safe-event replay and failure/reconnect behavior.
6. `P21A-T4`: add follow-up routing for specific role and broadcast mode.
7. `P21A-T5`: Claude B safety/privacy/reliability review.
8. `P21A-T6`: Codex B final integration signoff and frontend handoff.
