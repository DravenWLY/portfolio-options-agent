# ADR 0007: Agent Console HTTP Commands and SSE Progress Streaming

Status: proposed - paused pending product reactivation
Date: 2026-05-24
Owner: Codex B - Architecture / Systems / Integration

## Pause Note

Codex A paused further agentic/realtime architecture and implementation on
2026-05-25 while the founder studies agentic AI concepts. This ADR records an
option for future review; it is not accepted and does not authorize Phase 21A
implementation.

## Context

Phase 19 established a mock-first, app-owned portfolio-aware agent team and
privacy-safe prompt/evidence boundaries. Phase 20C shaped the Agent Console
frontend around a run summary, ordered agent pipeline, transcript, deterministic
evidence rail, and a disabled follow-up composer.

The console needs a backend interaction model before the composer can be
enabled. The founder specifically wants role progress, transcript history,
direct-to-agent follow-up questions, and broadcast-to-team questions. These
interactions must remain analysis-only and must not send raw private brokerage
data or unsafe provider output to the frontend.

The architecture document already selected Server-Sent Events (SSE) as the
first transport for agent progress, with WebSocket deferred until genuine
bidirectional streaming needs exist.

## Decision

For Phase 21A, use:

- authenticated HTTP `POST` commands to create an analysis run and submit
  follow-up questions;
- ordinary HTTP `GET` reads for run and transcript reload;
- SSE for ordered, reconnectable run/stage/message progress.

Keep the current stateless
`POST /agent-team/trade-review-analysis/preview` endpoint unchanged.

SSE events must contain only validated frontend-safe status or transcript
objects. Phase 21A does not stream raw LLM tokens, raw prompts, provider
payloads, traces, or exceptions.

Do not introduce Socket.IO or native WebSocket in Phase 21A. Reconsider a
bidirectional transport only if a later reviewed requirement needs live
in-run controls or collaboration that cannot be expressed as HTTP commands.

## Safety and Persistence Rules

- Mock provider remains the default implementation and test path.
- HTTP request bodies cannot select provider/model, submit arbitrary prompt
  templates or evidence, or override actionability/freshness metadata.
- Public analyst roles stay public-evidence-only; portfolio-aware roles receive
  only the approved agent-safe deterministic projection.
- Follow-up input is untrusted and must pass length and private-data safety
  validation before prompt construction or persistence.
- Provider failures become safe role-unavailable/partial-run events while the
  deterministic evidence rail remains available.
- Reuse existing app-owned run/step/thread/message persistence where the
  semantics fit. Any new persistence model requires a scoped design review
  first.

## Consequences

Positive:

- Enables a realtime-feeling console with a small, inspectable protocol.
- Preserves browser-native reconnect/replay behavior through event IDs.
- Lets validation finish before transcript content reaches the client.
- Avoids coupling the MVP console to market-streaming or socket infrastructure.

Tradeoffs:

- Follow-up submission remains request/response rather than conversational
  full-duplex messaging.
- Event replay requires an ordered safe persistence or reconstruction strategy.
- Token-by-token generation is deferred.

## Alternatives Considered

### Native WebSocket

Deferred. It provides full-duplex transport, but the first console only needs
discrete commands followed by one-way progress and transcript events.

### Socket.IO

Rejected for this phase. It adds a library/protocol layer without a present
need that SSE and HTTP cannot satisfy.

### Polling Only

Rejected as the primary UX path. It could read terminal run state, but it is a
poor match for visible stage progress and ordered transcript arrival. Polling
may remain a fallback recovery mechanism.

## Review Guidance

Block changes that:

- stream raw provider tokens or unvalidated content to the frontend;
- add client-selected provider/model/prompt/evidence inputs;
- introduce private account/broker/provider data into prompts, events, or
  transcript reads;
- make live LLM calls necessary for default tests or UI function;
- conflate deterministic evidence and agent commentary;
- add order/execution/advice/guarantee wording;
- adopt WebSocket or Socket.IO without a separately approved requirement.
