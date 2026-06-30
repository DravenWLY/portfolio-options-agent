# Phase 33A-T2 — Planner, Evidence Auditor, and Role Behavior Design

Status: design / contract-aligned behavior spec (no implementation).
Owner: Claude E. Reviewer: Codex B.
Builds on: P33A-T0 contract
(`docs/codex-b-architecture/PHASE_33A_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md`),
P33A-T1 tool layer (`backend/app/services/agent_team/tools.py`, review-passed),
ADR 0008, ADR 0009, and the P33A architecture memo
(`docs/claude-e-agentic/PHASE_33A_TOOL_RICH_AGENT_TEAM_ARCHITECTURE_MEMO.md`).

Product line unchanged: a read-only review desk that answers **"What would I be
ignoring if I acted manually now?"** — never "should I trade?".

This memo specifies how the tool-mediated Agent Team reasons over the **P33A-T1
`ToolResult` envelopes only**. It defines planner behavior, role projections,
the Evidence Auditor, the citation graph, output shapes, the bounded one-pass
critique, the test matrix for T3, and the Codex B decisions required before any
T3 code is written.

---

## 0. The single most important finding (read first)

P33A-T1 shipped **two independently-defined role→evidence maps that do not
agree**:

1. The **tool role-allowlist** — which tools a role may *receive*
   (`default_tool_registry()`, `tools.py:380`, enforced by
   `assert_role_tier_allowed` / `ToolRegistryEntry.role_allowlist`).
2. The **report citation role-allowlist** — which `evidence_ref`s a role may
   *cite* in persisted output (`ROLE_ALLOWED_EVIDENCE_KEYS`,
   `report_output_safety.py:40`, enforced by `_validate_reference_set`).

A role can therefore **receive a `ToolResult` whose `evidence_ref` it is not
allowed to cite**, and can be **allowed to cite refs that no T1 tool produces**.
Worked cross-walk (receivable = tool allowlist; citable = report allowlist;
**usable = intersection**):

| role | receivable evidence_refs (T1 tools) | citable refs (report) | **usable (intersection)** | receivable-but-not-citable (would FAIL output safety) |
| --- | --- | --- | --- | --- |
| `fundamentals_analyst` | trade_intent_summary, market_quote_freshness, public_company_profile | trade_intent_summary, public_company_profile, public_fundamentals_snapshot, public_events_calendar | **trade_intent_summary, public_company_profile** | market_quote_freshness |
| `news_analyst` | trade_intent_summary, market_quote_freshness, public_company_profile | trade_intent_summary, public_news_snapshot, public_events_calendar, public_market_context, economic_awareness_snapshot, market_mood_snapshot | **trade_intent_summary** | market_quote_freshness, public_company_profile |
| `technical_analyst` | trade_intent_summary, market_quote_freshness, public_company_profile | trade_intent_summary, public_technical_context, public_market_context, market_quote_freshness | **trade_intent_summary, market_quote_freshness** | public_company_profile |
| `risk_management_agent` | trade_intent_summary, scope_state, actionability, portfolio_impact_summary, concentration_risk_drift, liquidity_collateral_caveats, options_exposure_summary, freshness, market_quote_freshness, public_company_profile, + gap-inspector refs | trade_intent_summary, scope_state, actionability, account_readiness, freshness, portfolio_impact_summary, before_after_portfolio_impact, concentration_risk_drift, liquidity_collateral_caveats, options_exposure_summary, market_quote_freshness | **trade_intent_summary, scope_state, actionability, freshness, portfolio_impact_summary, concentration_risk_drift, liquidity_collateral_caveats, options_exposure_summary, market_quote_freshness** | public_company_profile, plus gap-inspector refs that fall outside the citable set (economic_awareness_snapshot, market_mood_snapshot, public_*) |
| `portfolio_manager_agent` | all of the above | risk set + economic_awareness_snapshot, market_mood_snapshot + all public-evidence keys | **everything risk can use + public_company_profile + economic/mood (when a tool supplies them)** | (none in T1) |

Two structural consequences fall out of this and shape the entire design:

- **The system fails *closed*, not *useless-by-accident*.** If a role cites a
  received-but-not-citable ref, `validate_agent_team_report_output` rejects the
  payload and the role/report degrades. That is safe, but it produces empty
  reports instead of useful ones unless the planner and auditor are built to the
  intersection from the start.
- **Public roles are near-empty on T1 evidence.** `news_analyst` can usably cite
  exactly **one** ref (`trade_intent_summary`); `technical_analyst` two;
  `fundamentals_analyst` two. The public snapshots they are *allowed* to cite
  (`public_news_snapshot`, `public_technical_context`, etc.) have **no T1 tool**.
  This is acceptable for "what would I be ignoring" *if* it is a deliberate
  choice — those roles become **gap-reporting roles** (absence is the finding) —
  but it must be ratified, not stumbled into.

**Design rule adopted by this memo:** there is exactly **one** binding map, the
**`USABLE_EVIDENCE_BY_ROLE = receivable ∩ citable`** intersection. The planner
routes tools by it, roles cite only from it, and the auditor enforces it. The
report-output validator then becomes a *redundant backstop*, never the first
place a violation is discovered. Reconciling the two source maps (or formally
designating the report allowlist as the binding constraint the tool layer must
not exceed) is **Codex B decision #1** below.

---

## 1. Planner behavior

### 1.1 What the planner sees — the Evidence Catalog (labels only, no values)

The planner consumes a backend-built **Evidence Catalog**, never a `ToolResult`
and never the saved evidence payload. The catalog is two label-only lists:

```
EvidenceCatalog:
  tools:    [ {tool_name, display_name, evidence_tier, role_allowlist} ]   # from default_tool_registry()
  sections: [ {section_key, availability, evidence_tier, freshness_category, caveat_codes} ]
  locked_question: "what_would_be_ignored"      # constant; never "should_trade"
```

- `tools` is a direct projection of `ToolRegistryEntry` governance fields
  (`tools.py:225`) — no execution, no payload.
- `sections` is the **availability/tier/caveat map** — exactly the information
  `evidence_gap_inspector` already computes from `_unavailable_evidence_refs`
  (`tools.py:831`). `freshness_category` is a **category label** (e.g.
  `fresh` / `stale` / `unknown` / `not_available`), never a timestamp, `as_of`,
  or numeric value.
- The catalog is built by the backend and passed through `validate_tool_payload`
  (`tools.py:150`) before it can reach the planner, so it cannot carry forbidden
  keys, value tokens, advice phrases, or invented metrics.

The planner sees **no `summary_payload`, no balances, no scope values, no
freshness timestamps, no holdings** — only which tools exist, who may call them,
which sections are available/limited/missing, and their tier and caveat codes.

### 1.2 How the planner chooses tools

The planner's optimization target is **coverage of ignored dimensions**, not
investment conviction. It emits a **structured plan** (no free-form tool calls,
no prose tool selection):

```
PlannerPlan:
  plan_version: "p33a_plan_v1"
  dimensions:  [ "risk_freshness", "scope_feasibility", "public_company_context",
                 "public_event_context", "public_market_context", "evidence_gaps" ]
  role_plan: [
    { role_name, tool_requests: [ {tool_name, args} ], rationale_code }
  ]
```

Selection rules (all enforced by the backend, not trusted to the model):

1. For each role, the planner may only request tools in
   `registry[tool].role_allowlist` **and** whose produced `evidence_ref`(s) fall
   in `USABLE_EVIDENCE_BY_ROLE[role]` (section 0). Anything else is dropped by
   the runner before execution.
2. The planner **always** plans `evidence_gap_inspector` for at least one
   portfolio-aware role — it is the keystone "what's NOT here" tool and the
   product's whole point.
3. The planner prefers tools whose backing section is `available`/`limited`; for
   `not_available`/`not_reviewed` sections it plans the tool anyway **only** when
   the resulting `ToolResult` will be an honest "unavailable" finding (this is
   how a gap becomes a citable finding, not silence).
4. `args` are restricted to `TOOL_REQUEST_ARG_KEYS`
   (`section_key`, `symbol_or_underlying`, `role_key`, `scope_category`;
   `tools.py:70`). The runner rejects any other arg.

### 1.3 How it avoids seeing private values

- The planner receives the **catalog**, not `ToolResult`s. Results flow planner →
  backend executes → **roles**. The planner never holds a result.
- The planner emits **requests** (`tool_name` + safe `args`); the backend
  validates and executes (`execute_tool_request`, `tools.py:433`).
- The catalog passes `validate_tool_payload`; the plan passes
  `validate_tool_payload` before any request is executed. A planner that tries to
  smuggle a private token into `args` is rejected at `ToolRequest.__post_init__`
  (`tools.py:281`).

### 1.4 How it stays bounded and deterministic enough for tests

- **Mock-first planner = pure deterministic function of the catalog.** Default
  tests run the mock planner; identical catalog ⇒ byte-identical plan. Ordering
  is fixed: roles in `AGENT_TEAM_ROLES` order (`llm_provider.py:36`), tools in
  `default_tool_registry()` insertion order.
- **Hard caps** (runner-enforced, independent of mock vs live):
  `MAX_TOOL_CALLS_PER_ROLE = 4`, `MAX_TOOL_CALLS_TOTAL = 16`,
  `MAX_ROLES = len(AGENT_TEAM_ROLES) = 5`, `MAX_PLANNER_REPASSES = 1`.
- A **live** planner only ever *proposes*; its proposal is clamped to the
  allowlist intersection + caps, so a misbehaving LLM cannot exceed bounds or
  reach data it should not. Determinism in live mode is "frozen on read-back,"
  not "identical on re-run" (consistent with the reproducibility-freeze stance,
  T4).

---

## 2. Role behavior

Roles reason over the `ToolResult` envelopes the backend returns for their
planned requests, plus the deterministic-evidence projection they already
receive today. **Every role emits structured findings, never conclusions.**

Shared rules for all roles (extend `BASE_SYSTEM_RULES`, `prompts.py:12`):

- Reason **only** over received `ToolResult` envelopes + deterministic evidence.
- Each finding **must** carry ≥1 `evidence_ref` drawn from a received result.
- Never compute, restate, or invent a number, level, target, probability, Greek,
  ROI, breakeven, valuation, or feasibility (the deterministic backend owns
  these; `tools.py:140` patterns will reject them anyway).
- Never emit advice / verdict / order / execution / safe-or-ready-to-trade /
  guaranteed-return wording (`report_output_safety.py:102`).
- An **unavailable** input is a finding ("this is missing"), not a reason to
  fabricate or stay silent.

### 2.1 `portfolio_manager_agent` (agent_safe, synthesizer, runs last)

- **May cite:** `USABLE_EVIDENCE_BY_ROLE[portfolio_manager_agent]` — the broadest
  set, including audited public-role findings and `public_company_profile`,
  `economic_awareness_snapshot`, `market_mood_snapshot` **when a tool supplies
  them**.
- **Job:** the four-bucket "what you'd be ignoring" synthesis (per P30A-T2):
  (a) deterministic risk flags, (b) data-freshness/availability gaps, (c)
  scope/feasibility caveats, (d) unreviewed public context — **plus** a manual
  verification checklist. Synthesizes from **audited** findings only.
- **Must ignore:** any prior-role claim the auditor dropped; any ref outside its
  citable set; any urge to produce a verdict.

### 2.2 `risk_management_agent` (agent_safe, primary)

- **May cite:** trade_intent_summary, scope_state, actionability, freshness,
  portfolio_impact_summary, concentration_risk_drift,
  liquidity_collateral_caveats, options_exposure_summary, market_quote_freshness.
- **Job:** deterministic risk / concentration / collateral / freshness flags and
  the **gaps** around them (via `evidence_gap_inspector`). Surfaces
  option-structure caveats from `options_exposure_summary` (see 2.6).
- **Must ignore:** `public_company_profile` even though it can *receive* it (not
  citable → would fail output safety); any gap-inspector ref that is not in its
  citable set (the auditor filters these — section 3).

### 2.3 `fundamentals_analyst` (public, secondary)

- **May cite:** trade_intent_summary, public_company_profile (the only two backed
  by a T1 tool); `public_fundamentals_snapshot` / `public_events_calendar` are
  citable but **have no T1 tool** → they appear only as *gap findings*.
- **Job:** reviewed public company identity/listing context (EDGAR profile,
  P29C) and an explicit gap note for the unreviewed fundamentals/events sections.
- **Must ignore:** market_quote_freshness (receivable, not citable); any
  portfolio/account evidence (it is a public role; the tier gate blocks it).

### 2.4 `news_analyst` (public, secondary) — **gap-reporting role in T1**

- **May usably cite:** trade_intent_summary **only**. All of
  public_news_snapshot, public_events_calendar, public_market_context,
  economic_awareness_snapshot, market_mood_snapshot are citable but
  **toolless in T1**.
- **Job in T1:** report the **absence** of reviewed news/event/macro context as a
  flagged gap ("you'd be acting without reviewed news/event context"). This is a
  legitimate "what would I be ignoring" contribution; it is not a defect.
- **Must ignore:** market_quote_freshness, public_company_profile (receivable,
  not citable). Becomes a full role when `public_news_events` /
  `market_mood_context` / `economic_awareness_context` ship (deferred, each its
  own source-rights slice).

### 2.5 `technical_analyst` (public, secondary)

- **May usably cite:** trade_intent_summary, market_quote_freshness.
  public_technical_context / public_market_context are citable but toolless in T1
  → gap findings only.
- **Job:** non-directional public market-freshness context + explicit gap on
  unreviewed technical context. **No** invented levels/targets
  (`INVENTED_LEVEL_PATTERNS`, `report_output_safety.py:153`).
- **Must ignore:** public_company_profile (receivable, not citable).

### 2.6 `options_structure_analyst` — **proposed; recommend DEFER for T3**

The contract lists this role "if proposed." Adding it as a real agent-team role
requires **schema changes**: extend the `AgentTeamRole` Literal and
`AGENT_TEAM_ROLES` (`llm_provider.py:15,36`), add it to `PORTFOLIO_AWARE_ROLES`
(`roles.py:13`), add a `ROLE_ALLOWED_EVIDENCE_KEYS` entry
(`report_output_safety.py:40`), and trigger the ADR-0009 read-contract /
back-compat review (the contract explicitly flags additive roles as needing
that review).

**Recommendation: do NOT add it in T3.** For the prototype, option-structure
caveats are already reachable: `risk_management_agent` cites
`options_exposure_summary` (a deterministic, backend-owned section) and surfaces
collateral/assignment/exercise/expiry **caveats** qualitatively. That delivers
the option-structure value with **zero schema change**. Promote
`options_structure_analyst` to a first-class role in a later, separately reviewed
slice once its citable evidence (and any options-specific tool) exists. This is
**Codex B decision #3**.

---

## 3. Evidence Auditor behavior

The auditor is a **meta-role**: it sees the **sanitized role findings + the
citation graph (the set of `evidence_ref`s each role actually received)** — never
raw data, never a `ToolResult` payload, never the catalog values. It runs
**after** all roles and **before** synthesis. Recommend it stay **out of**
`AGENT_TEAM_ROLES` (it issues no `ToolRequest` and owns no `ToolResult`, so it
needs no role identity in the tool layer → **zero schema change**; Codex B
decision #2).

The auditor performs six checks; any failure routes to the one-pass re-pass
(3.7) or drops the offending claim (fail closed).

### 3.1 Citation completeness

Every finding must carry ≥1 `evidence_ref`, and **every cited ref must appear in
the union of `evidence_ref`s the role actually received** from executed
`ToolResult`s this run. A finding citing a ref the role never received is an
**unsupported claim** (3.3). Empty-citation findings are rejected. (Mirrors the
memo's "100% of claims resolve to a frozen `evidence_ref`.")

### 3.2 Citable-boundary enforcement (the section-0 fix, applied here first)

Every cited ref must also be in `USABLE_EVIDENCE_BY_ROLE[role]`. This is what
prevents the `report_output_safety` backstop from ever firing: the auditor
catches a "received-but-not-citable" ref (e.g. `news_analyst` citing
`market_quote_freshness`, or `risk_management_agent` citing a gap-inspector
`economic_awareness_snapshot` ref) and drops it **before** persistence. The
auditor **filters `evidence_gap_inspector` refs down to the role's citable set**
so the role can cite a gap only for sections it is allowed to talk about.

### 3.3 Unsupported-claim rejection

A claim whose `evidence_ref`s do not back its assertion (cited ref not received,
or claim asserts a fact the cited section's availability does not support — e.g.
asserting content from a `not_available` section) is rejected. Availability is
cross-checked against the result's `availability` field; citing
`available`/`limited` only (same rule as `_validate_reference_set`,
`report_output_safety.py:258`).

### 3.4 Private-data-leak rejection

The auditor re-runs the privacy spine over every finding:
`validate_tool_payload` (`tools.py:150`) + `validate_llm_provider_payload`
(`llm_provider.py:204`) — forbidden keys, forbidden value tokens
(`account_id`, `buying_power`, `raw_holdings`, …), secret-like patterns, and raw
URLs/payloads. Any hit fails the finding closed (dropped; not re-passed — a leak
is never "retried into safety").

### 3.5 Advice / order / safe-to-trade wording rejection

The auditor applies `REPORT_PROHIBITED_PHRASES` (`report_output_safety.py:102`)
+ `TOOL_PROHIBITED_PHRASES` (`tools.py:125`) to every finding: no
recommend/buy/sell/hold/order/execute/safe-to-trade/ready-to-trade/
guaranteed-return wording. Any hit fails closed (dropped).

### 3.6 Generated-number / invented-metric / invented-level rejection

The auditor applies `TOOL_GENERATED_METRIC_PATTERNS` (`tools.py:140`) +
`INVENTED_LEVEL_PATTERNS` (`report_output_safety.py:153`): no `$`/`%`/price
target/probability/ROI/share-or-contract counts, no
support/resistance/pivot/level adjacent to a digit. Deterministic numbers live in
backend sections and are referenced by `evidence_ref`, never reproduced in
narrative. Any hit fails closed (dropped).

### 3.7 Contradiction detection + one-pass critique/re-pass trigger

- **Contradiction:** two roles assert opposing qualitative claims about the
  **same `evidence_ref`** (e.g. one says context is fresh, another flags it
  stale). The auditor does **not** pick a winner — it records a `contradiction`
  and converts it into an **open question** for synthesis.
- **Re-pass trigger:** the auditor may request **exactly one** bounded re-pass
  (`MAX_PLANNER_REPASSES = 1`) when a contradiction or an unsupported-but-fixable
  claim (3.1/3.3) is found and a re-plan could resolve it (e.g. plan
  `evidence_gap_inspector` to confirm a gap). Leak/advice/metric failures
  (3.4–3.6) are **never** re-passed — they fail closed immediately.
- After the single re-pass, any still-failing claim is **dropped** (the rest of
  the report survives), and an `eval_flag` + `warning_code` is recorded. The
  system degrades to a smaller honest report; it never degrades to a leak or a
  fabricated claim.

---

## 4. Citation graph

### 4.1 How role findings cite ToolResult evidence_refs

Every executed `ToolResult` carries `evidence_refs` (`tools.py:312`). The runner
builds a per-role **received-refs set** = union of `evidence_refs` across that
role's `ToolResult`s. A role finding cites a subset of that set. The citation
graph is:

```
finding  --cites-->  evidence_ref  --produced_by-->  ToolResult(tool_name, source_key, availability, as_of)
```

The `evidence_ref` vocabulary is **already shared** between the tool layer and
the report layer — every ref a T1 tool emits
(`trade_intent_summary`, `scope_state`, `freshness`, `actionability`,
`portfolio_impact_summary`, `concentration_risk_drift`,
`liquidity_collateral_caveats`, `options_exposure_summary`,
`market_quote_freshness`, `public_company_profile`, + gap-inspector section keys)
is in `CANONICAL_EVIDENCE_KEYS` (`report_output_safety.py:22`). Note the
naming canon: the model field `cash_collateral_caveats` has `section_key =
"liquidity_collateral_caveats"`, and `tools.py` correctly derives the ref via
`section.section_key` — `liquidity_collateral_caveats` is the canonical ref.

### 4.2 How the auditor verifies citations

For each finding: `cited_refs ⊆ received_refs(role)` (3.1) **and** `cited_refs ⊆
USABLE_EVIDENCE_BY_ROLE[role]` (3.2) **and** each cited ref's source result has
`availability ∈ {available, limited}` (3.3). The auditor emits a per-role
`citation_complete` verdict and a list of `violations`; violating refs are
filtered out, not silently kept.

### 4.3 How synthesis cites audited findings without inventing evidence

The `portfolio_manager_agent` synthesis may cite **only** refs that survived the
audit, and its `evidence_references` = `dedup(union of surviving cited refs) ∩
USABLE_EVIDENCE_BY_ROLE[portfolio_manager_agent]`. The synthesizer cannot
introduce a ref no role surfaced (anti-hallucination), and the
`report_output_safety` synthesis check
(`PORTFOLIO_MANAGER_SYNTHESIS_EVIDENCE_KEYS`,
`report_output_safety.py:101`) is the final backstop.

---

## 5. Output shapes

All four shapes below are **run-state only** for T3 (ADR 0008: "state stays
app-owned"). They are *reduced* to the **existing** persisted schema, so **T3
requires no backend schema change** (section 5.5).

### 5.1 Role finding shape (internal)

```
RoleFindingSet:
  role_name: AgentTeamRole
  role_status: "completed" | "skipped" | "unavailable" | "gated"
  findings: [
    {
      finding_type: "ignored_risk" | "missing_context" | "contradiction" | "open_question",
      claim_text: str,                 # qualitative, no numbers/levels/advice
      evidence_refs: tuple[str, ...],  # ⊆ received ∩ usable
      severity_label: str | None,      # from deterministic caveat, never computed
      caveat_codes: tuple[str, ...],
    }
  ]
```

### 5.2 Planner plan shape (internal)

```
PlannerPlan:
  plan_version: "p33a_plan_v1"
  dimensions: tuple[str, ...]
  role_plan: [ { role_name, tool_requests: [ {tool_name, args} ], rationale_code } ]
  caps: { per_role: 4, total: 16, repasses: 1 }
```

### 5.3 Auditor finding shape (internal)

```
AuditorRecord:
  audit_version: "p33a_audit_v1"
  role_verdicts: [ { role_name, citation_complete: bool, violations: tuple[str, ...] } ]
  contradictions: [ { evidence_ref, role_a, role_b, description } ]   # -> open questions
  dropped_claims: tuple[str, ...]      # claim ids dropped, with reason codes
  repass_triggered: bool
  eval_flags: tuple[str, ...]
```

### 5.4 Final synthesis input shape (internal)

```
SynthesisInput:
  audited_findings: tuple[RoleFindingSet, ...]   # post-audit, surviving findings only
  buckets: { ignored_risks, freshness_gaps, scope_feasibility_caveats, unreviewed_context }
  open_questions: tuple[str, ...]                # from auditor contradictions
  evidence_references: tuple[str, ...]           # dedup ∩ PM citable
```

### 5.5 Mapping to persisted schema — what does / does not need a backend change

- **No change for T3.** The four shapes reduce to the existing
  `SavedAgentTeamRoleSummaryRead` (`role_name`, `summary_markdown`,
  `evidence_references`, `warning_codes`; `reports.py:302`) and
  `SavedAgentTeamSummaryRead` (`final_synthesis_markdown`, `evidence_references`,
  `role_summaries`, `warning_codes`; `reports.py:334`). Reduction:
  `summary_markdown` = rendered findings; `evidence_references` =
  `dedup(cited refs) ∩ usable`; `warning_codes` = caveat + eval flags. The
  planner plan, structured findings, auditor record, and citation graph live in
  run-state and are **not** persisted in T3.
- **Schema change later, with Codex B review:**
  - **T4 (freeze):** persisting the used `ToolResult` set + citation graph =
    additive `agent_tool_evidence` section on `SavedEvidencePackageRead` /
    `SavedReviewArtifact` (already a planned T4 item; read-back, no re-fetch).
  - **T6 (UI):** rendering structured findings / per-claim citations / gaps =
    read-contract change (Codex B + Claude B).
  - **`options_structure_analyst`** as a role and **`planner` / `evidence_auditor`
    in `AGENT_TEAM_ROLES`** would each be schema changes — this design avoids
    all three for T3 (sections 2.6, 3).

---

## 6. Safety (how this design satisfies the boundary)

| boundary | enforcement in this design |
| --- | --- |
| no raw account/provider/broker IDs; no account numbers | catalog + plan + every finding pass `validate_tool_payload` (`TOOL_FORBIDDEN_KEYS`/`TOOL_FORBIDDEN_VALUE_TOKENS`, `tools.py:71`); auditor 3.4 |
| no balances, buying power, holdings, positions, quantities, lots | same forbidden-key/value scans + `validate_llm_provider_payload` (`llm_provider.py:57`); planner sees labels only |
| no raw payloads, URLs, prompts, traces, secrets, logs | `SOURCE_LEAK_PATTERNS` (`report_output_safety.py:162`), `SECRET_LIKE_VALUE_PATTERNS` (`llm_provider.py:107`), URL tokens in `TOOL_FORBIDDEN_VALUE_TOKENS`; auditor 3.4 |
| no advice/recommendation/buy/sell/hold/order/execution/safe-or-ready-to-trade/guaranteed-return | `REPORT_PROHIBITED_PHRASES` + `TOOL_PROHIBITED_PHRASES` + `PROHIBITED_LLM_OUTPUT_PHRASES`; auditor 3.5; locked question never "should trade" |
| deterministic backend owns all numbers/calculations | roles cite refs, never reproduce numbers; `TOOL_GENERATED_METRIC_PATTERNS` + `INVENTED_LEVEL_PATTERNS`; auditor 3.6 |
| tier gate | planner routes by `role_allowlist` ∩ usable; runner re-checks `assert_role_tier_allowed`; public roles can never receive `agent_safe` |
| meta-agents never see raw data | planner = catalog only; auditor = sanitized findings + citation graph only |

Defense-in-depth ordering: planner clamp → runner tier gate → `ToolResult`
validation → role finding validation → **auditor (first place violations are
caught)** → `validate_agent_team_report_output` (redundant backstop) →
persistence.

---

## 7. Recommended prompts / contracts

These are behavioral contracts (prompt bodies for the live path; the mock path is
a deterministic function and needs no prose). All extend `BASE_SYSTEM_RULES`.

### 7.1 Planner contract

```
You are the Portfolio Copilot Planner. You see only an Evidence Catalog:
which tools exist, which roles may call them, and which evidence sections are
available / limited / missing, with tier and caveat labels. You NEVER see any
values, balances, holdings, freshness timestamps, or tool results.
Goal: maximize coverage of dimensions the user would IGNORE if acting from
memory — never decide whether to trade.
Output a structured plan only: for each role, the tools to request (by name,
with safe args) and a rationale code. You may only request a tool for a role
when that role is allowed to receive it AND allowed to cite its evidence.
Always plan the evidence_gap_inspector for a portfolio-aware role. Respect the
caps (<=4 tools/role, <=16 total, single re-pass). Propose nothing else.
```

### 7.2 Role contract (all roles)

```
You are the Portfolio Copilot {display_name}. Reason ONLY over the ToolResult
envelopes provided to you and the deterministic evidence bundle. Deterministic
backend services own every number and calculation; never compute, restate, or
invent a number, level, target, probability, Greek, ROI, breakeven, valuation,
or feasibility. Provide analysis-only commentary that answers "what would the
user be ignoring?". Emit structured findings: each finding states a qualitative
claim and cites at least one evidence_ref from a result you received. If an
input is unavailable, say so as a finding — do not fabricate. Never use advice,
recommendation, buy/sell/hold, order, execution, safe-to-trade, ready-to-trade,
or guaranteed-return wording. Cite only evidence you are permitted to cite.
```

### 7.3 Evidence Auditor contract

```
You are the Portfolio Copilot Evidence Auditor. You see sanitized role findings
and the citation graph only — never raw data, never tool payloads. For each
finding verify: (1) it cites at least one evidence_ref the role actually
received; (2) every cited ref is in the role's allowed citation set; (3) the
cited section's availability supports the claim; (4) no private data; (5) no
advice/order/safe-to-trade wording; (6) no invented number, level, or target.
Detect contradictions across roles on the same evidence_ref and convert them
into open questions — never pick a side. You may request exactly ONE bounded
re-pass to resolve a contradiction or a fixable unsupported claim. Privacy,
advice, and invented-number failures are never re-passed; drop them and flag.
After the re-pass, drop any still-failing claim and keep the rest.
```

---

## 8. Proposed test matrix for T3 (Codex C + Claude E)

Default tests are offline/mock/deterministic. `()` = primary assertion.

**Planner**
1. Mock planner is a pure function of the catalog (same catalog ⇒ byte-identical
   plan).
2. Planner never plans a tool for a role outside `role_allowlist ∩
   USABLE_EVIDENCE_BY_ROLE` (e.g. never plans `public_company_profile` for
   `news_analyst` to *cite*).
3. Planner always includes `evidence_gap_inspector` for a portfolio-aware role.
4. Caps enforced: ≤4 tools/role, ≤16 total; a planner proposing more is clamped.
5. Planner receives no values: catalog passes `validate_tool_payload`; injecting
   a forbidden token into the catalog raises.

**Role projections**
6. Each role's received-refs set equals the union of its executed `ToolResult`
   `evidence_refs`.
7. `news_analyst` on T1 evidence cites only `trade_intent_summary` and otherwise
   emits gap findings (no `market_quote_freshness` / `public_company_profile`
   citations).
8. `risk_management_agent` surfaces option-structure caveats via
   `options_exposure_summary` (no `options_structure_analyst` role needed).
9. Public roles never receive `agent_safe` results (tier gate).

**Auditor**
10. Citation completeness: a finding citing a ref the role never received is
    dropped/unsupported.
11. Citable-boundary: a finding citing a received-but-not-citable ref
    (e.g. risk citing `public_company_profile`, or a gap-inspector
    `economic_awareness_snapshot` ref) is filtered before persistence.
12. Availability: citing a `not_available` section is rejected.
13. Private-leak / advice / invented-number findings fail **closed** and are
    **never** re-passed.
14. Contradiction on the same `evidence_ref` becomes an open question, not a
    pick.
15. Re-pass cap: at most one re-pass; still-failing claims dropped, rest survive;
    `eval_flag`/`warning_code` recorded.

**Citation graph / synthesis**
16. Synthesis `evidence_references` ⊆ `dedup(surviving cited refs) ∩ PM citable`;
    cannot introduce a ref no role surfaced.
17. End-to-end: full mock run produces a `SavedAgentTeamSummaryRead` that passes
    `validate_agent_team_report_output(..., evidence_package=evidence)` with the
    real evidence package (the redundant backstop never fires).

**Safety / determinism / degradation**
18. Recursive forbidden-key/value/secret scan over plan, every `ToolResult`,
    every finding, auditor record, and final payload is empty.
19. Deterministic mock path is byte-stable across runs (reproducibility pre-T4).
20. Blocked-actionability and provider-unavailable paths degrade exactly like the
    existing `agent_team_report.py` paths (no behavior regression on the existing
    deterministic-template route).

---

## 9. Codex B review points required before T3

1. **Reconcile the two role→evidence maps.** Adopt `USABLE_EVIDENCE_BY_ROLE =
   tool-allowlist ∩ report-citation-allowlist` as the single binding map, OR
   formally designate `ROLE_ALLOWED_EVIDENCE_KEYS` as the ceiling the tool
   role-allowlist must not exceed. Decide who owns the single source of truth
   (recommend: the report allowlist is binding; planner/auditor consume it).
2. **Confirm `planner` and `evidence_auditor` stay OUT of `AGENT_TEAM_ROLES`**
   (meta, non-persisted, no tool-request identity) → zero schema change for T3.
3. **Confirm `options_structure_analyst` is DEFERRED** (option caveats via
   `risk_management_agent` + `options_exposure_summary` for the prototype).
4. **Ratify public roles as gap-reporting roles in T1** (news/technical/
   fundamentals have near-empty citable T1 evidence; absence-as-finding is
   intended, not a defect).
5. **Confirm the auditor filters `evidence_gap_inspector` refs to each role's
   citable set**, and confirm the `evidence_ref` naming canon
   (`liquidity_collateral_caveats` is the ref; `cash_collateral_caveats` is only
   the model field name).
6. **Confirm structured findings/plan/auditor record stay run-state-only in T3**
   (reduced to existing markdown + `evidence_references` + `warning_codes`);
   freeze/persistence deferred to T4.
7. **Confirm the bounded one-pass re-pass** semantics: re-pass only for
   contradiction/fixable-unsupported; fail-closed (drop, never re-pass) for
   leak/advice/invented-number; whole report survives partial drops.

---

## 10. Return summary

- **Recommendation: PASS to proceed to P33A-T3 design-wise**, gated on Codex B
  resolving review point #1 (the two-map reconciliation) before T3 code is
  written. #1 is a small contract decision, not a redesign; the rest are
  confirmations. Everything in this memo is achievable with **zero backend schema
  change in T3**.
- **Open risks (all surfaced, all mitigated):**
  - tool-allowlist vs citation-allowlist divergence (R1) — mitigated by the
    intersection map + auditor 3.2; needs Codex B #1.
  - public roles near-empty on T1 evidence (R2) — mitigated by gap-reporting
    framing; needs Codex B #4.
  - scope creep into `options_structure_analyst` / meta-roles-as-real-roles (R3)
    — mitigated by deferral; needs Codex B #2/#3.
  - live-planner nondeterminism (R4) — mitigated by clamp-to-allowlist + caps +
    mock-default; live repro is "frozen on read-back" (T4).
- **Files changed:** this design doc only
  (`docs/claude-e-agentic/PHASE_33A_T2_PLANNER_AUDITOR_ROLE_DESIGN.md`). No code.
  Proposed plan update: mark `P33A-T1` done and `P33A-T2` done (design) /
  in-review in `docs/shared/implementation_plan.md` (not auto-edited).

---

## 11. Next implementation prompt draft for Codex C + Claude E (P33A-T3)

```text
Task: P33A-T3 - First tool-mediated saved-report run (mock-first)
Owners: Codex C (runner/graph wiring, tier enforcement) + Claude E (planner/
auditor/role reasoning, citation reduction). Reviewer: Codex B.

Precondition: Codex B has resolved P33A-T2 review point #1 (single binding
USABLE_EVIDENCE_BY_ROLE = tool-allowlist intersect report-citation-allowlist).

Build, mock-first and behind the existing runner seam:
1. EvidenceCatalog projection (labels only) from default_tool_registry() +
   section availability/tier/caveat map. Must pass validate_tool_payload.
2. A deterministic mock Planner: pure function of the catalog -> PlannerPlan,
   clamped to USABLE_EVIDENCE_BY_ROLE and caps (<=4/role, <=16 total, 1 re-pass).
3. Runner extension: planner -> backend executes planned ToolRequests via
   execute_tool_request -> per-role received-refs sets -> role findings ->
   Evidence Auditor -> portfolio_manager synthesis. Sequential; async-ready.
4. Evidence Auditor: the six checks (citation completeness, citable-boundary,
   unsupported-claim, private-leak, advice/wording, invented-number) +
   contradiction->open-question + single bounded re-pass; fail-closed drops.
5. Reduce structured findings to the EXISTING SavedAgentTeamSummaryRead /
   SavedAgentTeamRoleSummaryRead (markdown + evidence_references + warning_codes).
   NO new persisted schema in T3. Run-state holds plan/findings/auditor record.
6. Tests: the P33A-T2 section 8 matrix (1-20), all offline/mock/deterministic.

Hard constraints (block on violation):
- Use existing saved evidence only. No live providers, new sources, web, MCP,
  TradingAgents runtime, or LangGraph.
- planner/evidence_auditor stay OUT of AGENT_TEAM_ROLES; options_structure_analyst
  is NOT added. No frontend fields. No persistence/freeze (that is T4).
- No raw account/provider/broker data, balances, holdings, positions, quantities,
  lots, payloads, URLs, prompts, traces, secrets, or logs anywhere.
- Deterministic backend owns all numbers; agents cite refs, never reproduce them.
- No advice/recommendation/order/execution/safe-or-ready-to-trade/guaranteed-
  return wording. The existing deterministic-template route's external behavior
  must not change.

Deliverable: mock-first tool-mediated run producing an audited, citation-bound
SavedAgentTeamSummaryRead; the section-8 test matrix green; a short completion
report (Task/Status/Files changed/Verification/Blockers/Next step) requesting
Codex B PASS/BLOCKED, with the redundant report-output backstop confirmed never
firing on the mock golden path.
```
