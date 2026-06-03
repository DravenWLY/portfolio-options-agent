# ADR 0008: Agentic Orchestration Spine — App-Owned Safety Core, Custom Runner First, LangGraph Later

Status: accepted
Date: 2026-06-02
Owner: Codex B — Architecture / Tech Lead (adjudication)
Drafted by: Claude E — Agentic AI Systems Design / Implementation
Related: ADR 0002 (TradingAgents-inspired, not -centered), ADR 0005 (real LLM
provider gate, Google-first, mock-default), ADR 0007 (Agent Console HTTP commands
+ SSE, proposed/paused). Design reference:
`docs/claude-e-agentic/AGENTIC_SYSTEM_DESIGN_MEMO.md`.

## Context

Portfolio Copilot is a read-only, portfolio-aware trade-review copilot. Two
agentic foundations already exist: an app-owned deterministic stage graph
(`backend/app/services/agents/`, Phase 16B) with ADR-0002 review roles and typed
context envelopes, and a mock-first LLM agent team
(`backend/app/services/agent_team/`, Phase 19A–C) with an agent-safe
deterministic-evidence projection and strong output-safety validators
(invented-metric detection, private-key forbidding, advice/execution phrase
blocking). The stateless route `POST /agent-team/trade-review-analysis/preview`
is the stable regression surface; the Agent Console follow-up composer is
disabled; Phase 21A (realtime console + persistence) is paused.

The founder's forward vision is a durable, multi-turn, multi-agent **conversation**
(user selects agents, human-in-the-loop steering, live streaming). That vision
raised a core question the founder flagged as bet-the-project: which orchestration
substrate should Portfolio Copilot build on — LangGraph, the OpenAI Agents SDK,
Anthropic/Claude MCP, a custom lightweight orchestrator, or a hybrid — for both
MVP and a later product stage, chosen so a wrong early bet does not force a
rebuild.

The dominant architectural force is the product's safety model: the agent layer
is **safety-validated commentary over pre-computed, tier-scoped evidence**, not
autonomous agents that fetch data and act. Deterministic backend services own all
financial metrics; LLMs explain approved structured evidence and must not compute,
fetch, or invent numbers; and a three-tier data model (public / agent-safe /
private-never) must be enforced so public-evidence roles never receive
portfolio-aware context and raw private brokerage data never reaches any LLM or
tool.

## Decision

Adopt a **layered hybrid** in which Portfolio Copilot **owns the safety spine
permanently** and any orchestration framework is deferred and gated.

Layers:

1. **Custom safety/spine layer — app-owned, permanent.** Owns the
   provider-neutral `LLMProvider` Protocol, tier-scoped immutable context
   envelopes, the safety validators (privacy/wording/invented-metric),
   deterministic-evidence ownership, the run-state model, the evaluation harness,
   and the safe read/event contracts. No framework may own any of these.
2. **Orchestration engine — staged.** Phase 25A begins with a **thin custom
   app-owned runner** over the existing agent-team foundations. LangGraph (or any
   engine) is introduced later, and only when its primitives are load-bearing
   (see *Engine staging*).
3. **Tool-access boundary — future, optional.** If/when agents invoke tools, MCP
   may be the provider-neutral boundary for **public / agent-safe** tools only.
4. **Provider layer.** Keep the app-owned Protocol with Gemini/mock-default
   (ADR 0005). The OpenAI Agents SDK is rejected for this product path.

Governing principle: **pay for an engine only when its primitives are
load-bearing; never let a framework own the safety boundary.**

## Reversibility classification

**Hard-to-reverse core — must be designed correctly now, and lives in app-owned
code:**

- the data-tier model (public / agent-safe / private-never) and its enforcement
  point;
- deterministic-evidence ownership;
- the provider-Protocol shape;
- the role-as-pure-function seam;
- the run-state shape;
- the safe read/event contract shape;
- the persistence schema **once accepted**;
- the frontend-consumed event/read contracts **once shipped**.

**Reversible (two-way door) — but conditionally:** the engine/framework choice is
reversible **only while roles remain pure and state remains app-owned.** If a
framework comes to own the checkpoint schema, a shared message state, or event
IDs, it becomes load-bearing and is no longer a simple two-way door. Crossing that
line requires a new ADR.

Consequence for sequencing: the irreversible core is small and app-owned, so it is
built first and cheaply; the large builds (durable Console, parallel real-LLM
team, tool layer) come later behind stable seams. This is the structural
protection against "build large, then rebuild."

## Safety boundaries

The whole agentic program preserves:

- mock provider default; no live LLM/provider/tool/broker/market-data calls in the
  default path; live providers only behind the ADR-0005 backend-only gate;
- no raw private brokerage/account data in prompts, provider requests/responses,
  tool payloads, run state, events, reads, logs, persistence, docs, or tests
  (recursive forbidden-key / value / secret validation at every hop);
- deterministic backend services own all financial metrics; LLMs never compute,
  fetch, or invent metrics;
- deterministic evidence stays structurally separate from agent commentary;
- no order placement/cancellation, no broker actions, no broker scraping, no MFA
  bypass, no credential storage;
- no advice / recommendation / safe-to-trade / ready-to-trade / guaranteed-return
  / urgency / execution wording;
- no TradingAgents source copied and no TradingAgents execution in the
  portfolio-aware path;
- the stateless preview route keeps unchanged external behavior; the frontend
  composer stays disabled until a separately reviewed activation slice exists.

## Engine staging

- **Now (Phase 25A):** custom app-owned runner. No framework.
- **Later — introduce LangGraph only when ≥2–3 of these are *committed* product
  requirements:** durable multi-turn conversation threads; persisted/resumable
  state; human-in-the-loop interrupts; dynamic agent selection/loops the fixed
  pipeline cannot cleanly express. Even then: wrap the same pure roles; keep state
  app-owned and tier-scoped (no shared message state across tiers); deliver
  messages only after output-safety validation (no raw-token streaming).
- **Transport is independent of the engine.** Future Agent Console activation uses
  HTTP commands + SSE first (ADR 0007); WebSocket/Socket.IO stays deferred until a
  separately reviewed bidirectional-control need exists.

## Provider stance

Keep the app-owned `LLMProvider` Protocol with `MockLLMProvider` as default and
Google/Gemini as the first live candidate behind the ADR-0005 backend gate.
**Reject the OpenAI Agents SDK** for this product path: it is provider-coupled to a
model we are not adopting, and its agent/handoff/guardrail/session primitives
either duplicate or weaken our deterministic, tier-scoped, provider-neutral safety
boundary. Additional providers (e.g. Claude) may be added behind the same Protocol
without changing roles.

## MCP / tool stance

No MCP in MVP — there are zero LLM-invoked tools; deterministic evidence is
pre-computed and injected, so no tool protocol is needed. Later, MCP may wrap
**public or sanitized (agent-safe) tools only**, behind an explicit tier gate and
a governed `ToolResult` envelope. A **private-tier (broker-data) MCP tool or
server is prohibited** — the same class of rule as no-broker-scraping. MCP lowers
the friction of wiring a data source to a model, so the private-tier prohibition
is enforced by allowlist, not convention.

## Parallelism stance

Parallelism is a **design seam, not active behavior yet**. Phase 25A is made
**async-ready** while the first implementation runs **sequentially**. Later,
**public-evidence roles may fan out in parallel** with bounded concurrency
(semaphore + shared budget guard) and **aggregate by stable role key** (never by
completion order, to preserve determinism and test stability); each parallel task
receives its own immutable pre-scoped context. **Portfolio-aware roles remain
gated and ordered**, and synthesis runs last. Real concurrency is switched on with
the real-LLM commentary slice (mock has no latency to hide). Parallelism is
available in both the custom runner and a future engine, so it is not a
framework-forcing factor.

## Role rename deferral

The Phase 19 role names (`fundamentals_analyst`, `news_analyst`,
`technical_analyst`, `risk_management_agent`, `portfolio_manager_agent`) should
eventually become review-oriented names (`public_*_evidence_agent`,
`risk_review_agent`, `review_synthesis_agent`) so intent matches the existing
public/portfolio-aware boundary. Because this changes the console read schema and
touches the stable preview route, it is a **separate contract/back-compat slice**
and is **not** folded into P25A-T1.

## Memory / reflection stance

Memory is **disabled for MVP**: no user-level, symbol-level, outcome, or alpha
memory. Only within-run **validated** role summaries may be reused. **Reflection
exists only as process/eval flags** (`eval_flags`), never as learned trading
lessons and never outcome-based. Any future memory would be run/thread-level only,
sanitized, opt-in, deletable, retention-bounded, and reviewed by Claude B /
Claude D.

## Alternatives considered

### LangGraph now
Rejected for MVP. Its value (durable threads, `interrupt()` HITL, streaming) maps
to the future Console, none of which the fixed deterministic-first pipeline needs
yet; and its default shared message state fights the tier-isolation boundary. It
is the planned **future** engine for the durable multi-turn Console — wrapping the
same pure roles — not the MVP substrate.

### OpenAI Agents SDK
Rejected for this product path. Provider-coupled to a model we are not adopting
(Gemini-first per ADR 0005); its guardrails/handoffs/sessions are
redundant-with or contrary-to our deeper, domain-specific safety layer and our
deterministic, evidence-injected model. Reconsider only on a deliberate pivot to
OpenAI-primary with a managed agent loop.

### TradingAgents adapter as the workflow engine
Rejected. TradingAgents cannot safely own broker/private portfolio context,
options collateral, actionability policy, or the no-advice boundary (ADR 0002).
TradingAgents is reference architecture only; no source is copied and no
TradingAgents execution occurs in the portfolio-aware path. Any future adapter is
public-evidence-only and separately reviewed.

### Direct MCP tool use (now)
Rejected for MVP. There are no LLM-invoked tools; evidence is pre-computed and
injected. Introducing MCP now would add a tool-access surface whose entire purpose
(wiring data to a model) is contrary to the private-tier prohibition, with no
present benefit.

### WebSocket / Socket.IO first
Rejected as the first transport. The first realtime need is one-way server
progress after discrete user commands, which SSE serves with browser-native
reconnect/replay (ADR 0007). WebSocket/Socket.IO is reconsidered only for a
reviewed bidirectional-control or collaboration need, and is independent of the
engine decision.

## Consequences

Positive:

- The irreversible safety core stays in app-owned code, minimizing rebuild risk
  from any future engine/provider/tool change.
- MVP stays simple (custom runner only); the large builds are deferred behind
  stable seams.
- Deterministic-first + early-exit + mock-default keep latency and cost low and
  make default tests offline and deterministic.
- Provider neutrality avoids vendor lock-in; Gemini/Claude/mock plug in behind one
  Protocol.

Tradeoffs:

- Engineers must thread new features through the safety seams (provider Protocol →
  tier-scoped envelope → validators → run-state) rather than calling a model
  directly — intentional friction that centralizes safety.
- During a future engine migration, two orchestration mental models coexist for a
  bounded window.
- Hand-rolling durable multi-turn state/resume would be costly — which is exactly
  the trigger to adopt LangGraph at the Console stage rather than build it
  ourselves.

## Review guidance / block conditions

Block changes that:

- let a framework (LangGraph, OpenAI Agents SDK, or other) own prompts, the
  privacy boundary, evidence tiers, validation, deterministic-evidence ownership,
  the run-state, or the safe read/event contracts;
- introduce LangGraph, the OpenAI Agents SDK, or MCP before their gate conditions
  in this ADR are met;
- adopt a framework-owned checkpoint schema, shared cross-tier message state, or
  framework-owned event IDs without a new ADR;
- expose generic `AgentRunRead`, raw `agent_runs` JSON snapshots, raw
  `agent_steps` JSON snapshots, or database ids directly to the frontend instead
  of a dedicated safe read/event contract;
- send raw/private portfolio data to any LLM, tool, prompt, state, event, log, or
  persistence layer;
- let an LLM compute or invent financial metrics, or emit
  advice/execution/guarantee/readiness wording;
- enable real parallel role execution, the role rename, persistence, a route
  behavior change, the frontend composer, or live provider calls as part of
  P25A-T1;
- wire a private-tier (broker-data) MCP tool or server;
- copy TradingAgents source or execute TradingAgents in the portfolio-aware path;
- adopt WebSocket/Socket.IO without a separately reviewed bidirectional need.
