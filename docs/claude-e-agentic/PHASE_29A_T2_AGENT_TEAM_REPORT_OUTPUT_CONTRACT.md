# Phase 29A-T2 Agent Team Report Output Contract

Status: contract accepted (design-only; no runtime/backend implementation).
Codex B review PASS 2026-06-14; section 4.4 availability carve-out and section
4.3 layer attribution folded in from review.
Owner: Claude E
Reviewer: Codex B
Related plan: `docs/shared/implementation_plan.md` Phase 29A, task `P29A-T2`
Architecture: `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`
Consumes: `SavedEvidencePackageRead` (P29A-T1, `backend/app/schemas/reports.py`)
Extends: P28A saved artifact model (`SavedReviewArtifactRead`, `SavedAgentTeamSummaryRead`)

## 1. Purpose And Boundaries

This document defines the **output contract** for an Agent Team report: the
read shape the frontend consumes, the per-role section rules, how the report
attaches to the saved review artifact, the generated-output safety validator,
and the report status vocabulary.

It is a contract/design deliverable only. It does not implement provider calls,
report generation, persistence, frontend UI, TradingAgents integration, or a
runtime tool registry. Proposed Python shapes below are illustrative contract
sketches for P29A-T3 to implement after Codex B review; they are intentionally
not wired into `backend/`.

Hard constraints inherited from architecture (P29A-T0) and ADR 0008:

- Evidence-package-first. The Agent Team consumes **only** the approved
  `SavedEvidencePackageRead`, or a stricter per-role projection of it
  (section 4). No runtime private tools, no private MCP.
- No silent recomputation from current Account Details, current account
  selector, route state, cached frontend state, or live market data. The
  report is reproducible from generation-time evidence.
- Deterministic facts/numbers are backend-owned. The Agent Team narrates; it
  never emits financial metrics, quantities, or new calculations.
- Memory disabled. Agent Console composer disabled.

## 2. Report Output Shape

The report is a read-only projection derived from a `SavedReviewArtifactRead`
plus the `SavedEvidencePackageRead` built from it. Like
`SavedEvidencePackageRead.from_saved_review_artifact`, it is reproducible from
the saved artifact and never reads current mutable state.

Top-level read contract: `AgentTeamReportRead`.

- `report_schema_version: str` — e.g. `p29a_t2_v1`.
- `report_status: AgentTeamReportStatus` — section 6.
- `run_completeness: "full" | "partial" | "none"` — whether every requested
  role produced a validated section, some did, or none did.
- `source_snapshot: SavedEvidenceSourceSnapshotRead` — provenance only
  (artifact reference, source kind, generated/saved timestamps). Reused
  verbatim from the evidence package; never the headline.
- `evidence_schema_version: str` — echoes the consumed package version
  (`p29a_t1_v1`) for provenance/reproducibility.
- `report_headline: str | None` — one short, sanitized, non-advice summary
  line for the report; null when no validated narrative exists.
- `role_sections: tuple[AgentTeamReportRoleSectionRead, ...]` — section 3,
  ordered by the canonical `AGENT_TEAM_ROLES` order.
- `final_synthesis: AgentTeamReportSynthesisRead | None` — section 3.5; null
  when synthesis is unavailable/withheld.
- `evidence_references: tuple[str, ...]` — the union of all safe evidence
  `section_key`s actually cited by surviving sections. Keys only, never
  values. Audit/provenance.
- `limitations: tuple[str, ...]` — carried from the evidence package plus any
  report-level limitation lines. Always non-empty.
- `caveat_codes: tuple[str, ...]` — carried from the evidence package; never
  expanded or reinterpreted by the Agent Team.
- `provider_mode: str` — e.g. `mock` / a provider-neutral label. Provenance.
- `warning_codes: tuple[str, ...]` — provider-neutral, report-level warnings
  (e.g. `agent_team_partially_unavailable`, `synthesis_withheld_validation`).
- `safety_flags: tuple[str, ...]` — e.g. `analysis_only`,
  `deterministic_metrics_owned_by_backend`.
- `generated_at: datetime` — generation-time of the agent run.
- `report_built_at: datetime` — when this read view was projected.

Illustrative sketch (not wired):

    class AgentTeamReportRead(BaseModel):
        model_config = ConfigDict(from_attributes=True, extra="forbid")

        report_schema_version: str = "p29a_t2_v1"
        report_status: AgentTeamReportStatus
        run_completeness: Literal["full", "partial", "none"]
        source_snapshot: SavedEvidenceSourceSnapshotRead
        evidence_schema_version: str
        report_headline: str | None = None
        role_sections: tuple[AgentTeamReportRoleSectionRead, ...]
        final_synthesis: AgentTeamReportSynthesisRead | None = None
        evidence_references: tuple[str, ...] = ()
        limitations: tuple[str, ...]
        caveat_codes: tuple[str, ...]
        provider_mode: str
        warning_codes: tuple[str, ...] = ()
        safety_flags: tuple[str, ...] = ()
        generated_at: datetime
        report_built_at: datetime

        @model_validator(mode="after")
        def report_must_be_safe(self) -> "AgentTeamReportRead":
            validate_agent_team_report_output(
                self.model_dump(mode="python"), label="agent-team report"
            )
            return self

Display hierarchy (architecture UI direction, restated for contract clarity):
final synthesis and role narrative first; deterministic evidence sections as
supporting analysis; scope/freshness/source snapshot/caveats as
audit/provenance; technical detail in compact disclosure. Layout is the design
agents' choice; the contract only fixes the data and its provenance role.

## 3. Role Section Contract

Per-role read contract: `AgentTeamReportRoleSectionRead`.

- `role_name: AgentTeamRole` — one of the canonical five (section 3.1).
- `display_name: str` — backend-owned label (e.g. "Risk Manager").
- `role_status: "completed" | "unavailable" | "skipped" | "gated" | "validation_failed"`.
- `provider_status: LLMProviderStatus` — provenance (`ok`, `skipped`,
  `failed`, `rate_limited`, `provider_unavailable`, `safety_validation_failed`,
  …).
- `section_markdown: str | None` — sanitized narrative; null unless
  `role_status == "completed"`.
- `evidence_references: tuple[str, ...]` — the safe evidence `section_key`s
  this role cited. Must be a subset of the role's allowed citation set
  (section 3.2) **and** restricted to sections whose `availability` is
  `available` or `limited`. Keys only.
- `warning_codes: tuple[str, ...]` — provider-neutral category codes.
- `unavailable_reason: str | None` — sanitized code/label (e.g.
  `provider_unavailable`, `blocked_actionability_llm_roles_skipped`,
  `agent_output_failed_safety_validation`, `no_reviewed_public_evidence`).
  Never a raw provider error body, prompt, or trace.

This maps onto the already-existing P28A `SavedAgentTeamRoleSummaryRead`
(`role_name`, `display_name`, `provider_status`, `summary_markdown`,
`warning_codes`); see section 5.

### 3.1 Canonical roles

From `backend/app/services/agent_team/roles.py` (unchanged here):

| role_name | display_name | data boundary | portfolio evidence |
| --- | --- | --- | --- |
| `fundamentals_analyst` | Fundamentals Analyst | public ticker/company evidence only | No |
| `news_analyst` | News Analyst | public news/macro evidence only | No |
| `technical_analyst` | Technical Analyst | public/mock market context only | No |
| `risk_management_agent` | Risk Manager | sanitized deterministic review evidence | Yes |
| `portfolio_manager_agent` | Portfolio Manager | prior role summaries + sanitized deterministic evidence | Yes |

### 3.2 What each role may output and may cite

Each role narrates only its own boundary and may cite only the evidence
`section_key`s listed for it. A role must never cite a section outside its set
or a section whose availability is `not_available` / `not_reviewed` /
`not_applicable` — in those cases it degrades honestly (section 3.3).

Canonical citation keys (the package's real `section_key`s plus package-level
categories that act as evidence): `trade_intent_summary`, `scope_state`,
`actionability`, `freshness`, `account_readiness`, `portfolio_impact_summary`,
`before_after_portfolio_impact`, `concentration_risk_drift`,
`liquidity_collateral_caveats`, `options_exposure_summary`,
`market_quote_freshness`, `economic_awareness_snapshot`,
`market_mood_snapshot`. (Note: the `cash_collateral_caveats` field carries
`section_key="liquidity_collateral_caveats"`; citation uses the `section_key`.)

Public roles (no portfolio evidence):

- `fundamentals_analyst`
  - May output: qualitative framing of the reviewed instrument from approved
    public company/fundamental evidence; explicit statements of what is
    available vs. unknown.
  - May cite: `trade_intent_summary`, plus a reviewed public-fundamentals
    section **only if** the package later carries one. In the current P29A-T1
    package no public company/fundamentals section exists, so this role
    degrades to "no reviewed public evidence available."
  - Must not: invent P/E, valuation, price targets; say "good/bad to own";
    any buy/sell framing.
- `news_analyst`
  - May output: summary of approved public news/macro/event context; event
    proximity as context (e.g. earnings near expiry) — qualitative only.
  - May cite: `trade_intent_summary`, `economic_awareness_snapshot`,
    `market_mood_snapshot`. (Both are `not_reviewed` in the current package →
    degrade until a source/rights contract lands.)
  - Must not: predict moves; "buy before earnings"; invented figures.
- `technical_analyst`
  - May output: qualitative public market-context framing; explicit
    unavailability notes.
  - May cite: `trade_intent_summary`, `market_quote_freshness` (the freshness
    **category/label** only — never quote values).
  - Must not: signals, support/resistance, price targets, entry/exit,
    "oversold → buy", invented indicator values.

Portfolio-aware roles:

- `risk_management_agent`
  - May output: interpretation of deterministic concentration / collateral /
    assignment / risk-rule outputs and freshness; "what to confirm" framing.
  - May cite: `trade_intent_summary`, `scope_state`, `actionability`,
    `account_readiness`, `freshness`, `portfolio_impact_summary`,
    `before_after_portfolio_impact`, `concentration_risk_drift`,
    `liquidity_collateral_caveats`, `options_exposure_summary`,
    `market_quote_freshness`.
  - Receives deterministic evidence only — **not** prior role summaries (per
    `roles.py` boundary).
  - Must not: invent risk numbers; verdicts like "risky/safe to trade";
    position-sizing advice.
- `portfolio_manager_agent`
  - May output: educational synthesis of the team's analysis-only points; open
    questions; restated limitations. Authors the `final_synthesis`
    (section 3.5).
  - May cite: the full risk-role set **plus** `economic_awareness_snapshot`
    and `market_mood_snapshot`, **plus** prior role summaries (the only role
    that consumes them).
  - Must not: fiduciary/allocation advice; "best path"; "optimize"; buy/sell;
    any decision verdict.

The per-role allowed-citation map is the single source of truth the validator
enforces (section 4) and a stricter per-role evidence projection (section 4.4)
materializes for prompt assembly.

### 3.3 Handling missing evidence, stale data, gating, and failures

- Missing/unreviewed section (availability `not_available` / `not_reviewed` /
  `not_applicable`): the role states it honestly and does not fabricate.
  `role_status = "completed"` is still allowed if the role produced a valid
  "evidence not available" narrative; otherwise `role_status = "skipped"` with
  `unavailable_reason = "no_reviewed_public_evidence"` (or equivalent). The
  section must never imply data it did not receive.
- Stale data: the role surfaces the freshness label/category from the evidence
  package as a caveat; it must not re-time, recompute, or minimize staleness.
- Blocked/unknown deterministic actionability (status `blocked_*`): all LLM
  roles are gated — mirrors `ReviewRunner._deterministic_only_state`. Each role
  section is `role_status = "gated"`, `provider_status = "skipped"`,
  `unavailable_reason = "blocked_actionability_llm_roles_skipped"`,
  `section_markdown = None`. Report falls to `deterministic_draft`
  (section 6).
- Agent Team unavailable (provider failure for a role): `role_status =
  "unavailable"`, `provider_status` carries the failure category,
  `section_markdown = None`, `unavailable_reason = "provider_unavailable"` (or
  the specific provider status). If **all** roles are unavailable, report =
  `agent_unavailable`.
- Failed validation (generated output rejected by the validator): `role_status
  = "validation_failed"`, `provider_status = "safety_validation_failed"`,
  `section_markdown = None`, `unavailable_reason =
  "agent_output_failed_safety_validation"`. The offending text is **never**
  surfaced or persisted. See section 4.5.

### 3.5 Final synthesis contract

`AgentTeamReportSynthesisRead`:

- `synthesis_markdown: str | None` — sanitized narrative; null when withheld.
- `authored_by: "portfolio_manager_agent" | "deterministic_template"` — the
  PM role authors synthesis; a deterministic, non-LLM template line is the
  fallback when the PM role is unavailable/gated/validation-failed (mirrors
  `_compose_final_synthesis` style: states completed-vs-unavailable role counts
  and "Deterministic backend services own all calculations.").
- `evidence_references: tuple[str, ...]` — subset of the PM role's allowed
  citation set.
- `warning_codes: tuple[str, ...]`.

Synthesis rules: it summarizes across **already-validated** role sections and
the evidence package only; it introduces no new metric, number, or claim not
present in a surviving section; it never produces advice/verdict wording. If the
PM-authored synthesis fails validation, it is withheld (`synthesis_markdown =
None`) and replaced by the deterministic template; report status follows the
rule in section 6.

## 4. Generated-Output Safety Validator

The report validator reuses and **tightens** the P29A-T1 saved-evidence
validator and the existing provider-output validator. It is the gate every
report read model and every persisted role/synthesis summary must pass.

Proposed entry point (P29A-T3 implements):
`validate_agent_team_report_output(payload, *, label,
allowed_keys_by_role=...)` in a new
`backend/app/services/agent_team/report_output_safety.py`.

### 4.1 Reused layers (must all pass)

1. `app.services.agent_team.output_safety.validate_llm_provider_output` —
   already rejects:
   - forbidden private keys (`FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS`);
   - private identifier/secret value patterns (`PRIVATE_VALUE_PATTERNS`);
   - advice/execution phrases (`PROHIBITED_OUTPUT_PHRASES`);
   - generated financial-metric patterns (`GENERATED_METRIC_PATTERNS`:
     `$`/percent/price target/probability/ROI/yield/breakeven/Greeks/
     share+contract counts).
2. P29A-T1 saved-evidence checks from `backend/app/schemas/reports.py`:
   - `_SAVED_REVIEW_PROHIBITED_PHRASES` (financial/investment/trading advice,
     trade/investment recommendation, recommendation to buy/sell, safe/ready to
     trade, guaranteed/guaranteed return, place/submit order, execute trade);
   - `_SAVED_REVIEW_FORBIDDEN_VALUE_TOKENS` (provider/broker/account ids,
     account number, raw payloads, raw holdings/positions, tax lots, raw
     balance, buying power, api key, access token, prompt, llm trace, provider
     trace id);
   - `_SAVED_REVIEW_FORBIDDEN_KEYS` key scan.

To avoid drift, P29A-T3 should factor these phrase/token lists into one shared
vocabulary module (e.g. `safety_vocab.py`) imported by both `reports.py` and
the report validator, rather than duplicating literals.

### 4.2 Report-specific advice superset (tightening)

Reject (case-insensitive substring), as a superset that closes gaps in the
reused lists:

- financial advice, investment advice, trading advice, trade advice;
- trade recommendation, investment recommendation, buy recommendation, sell
  recommendation, our recommendation, we recommend, i recommend;
- recommendation to buy, recommendation to sell, recommend buying, recommend
  selling;
- you should buy, you should sell, should buy, should sell, i would buy, i
  would sell;
- buy now, sell now, buy/sell directive wording, enter the trade, exit the
  trade, take the trade, make the trade, open a position, close the position;
- order/execution wording: place order, place an order, submit order, submit an
  order, execute trade, execute the trade, order instruction;
- safe to trade, ready to trade, safe-to-trade, ready-to-trade;
- guaranteed, guaranteed return, guaranteed returns.

Negated safety copy ("This is not advice", "Not an order recommendation")
stays acceptable when concise; per P28A safety-language guidance the validator
targets affirmative advice/execution wording, not honest negations.

### 4.3 Raw private-data token/field rejection (tightening)

Reject any account refs/IDs, broker/provider IDs, account numbers, raw
balances, holdings, positions, quantities, tax lots, transactions, orders,
provider payloads, prompts, traces, secrets. Coverage by layer:

- structured leakage (a forbidden **key** anywhere in the payload) → key scans
  (`_SAVED_REVIEW_FORBIDDEN_KEYS`, `FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS`);
- identifier/secret **values** → `PRIVATE_VALUE_PATTERNS` plus the saved-evidence
  / provider value-token lists;
- free-text numeric leakage in narrative (e.g. share/contract counts, dollar
  amounts, percentages) → `GENERATED_METRIC_PATTERNS` (note: `quantity` is not a
  value-token literal, so narrative quantities are caught by the metric
  patterns, not the token list).

The report carries **labels and section_keys only**; any literal private value,
identifier, or generated number is a hard reject.

### 4.4 Evidence-reference allowlist enforcement (new)

For every `evidence_references` list (role sections and synthesis):

- each key must be in the canonical citation vocabulary (section 3.2);
- each key must be in the **role's** allowed set;
- the availability check applies **only** to `SavedEvidenceSectionRead`-typed
  sections (those that carry `section_key` + `availability`): a cited section
  key must map to a package section whose `availability` is `available` or
  `limited`. The package-level categories `trade_intent_summary`, `scope_state`,
  `freshness`, and `actionability` are not `SavedEvidenceSectionRead` objects
  (they have no `availability` field) and are always citable as provenance when
  in the role's allowed set — they are never subject to the availability gate.

A reference outside the role boundary, to an unknown key, or to a
`SavedEvidenceSectionRead` section that is not-available/not-reviewed is a hard
reject. This is what guarantees a
public role cannot cite portfolio sections and no role can cite data it never
received. The same allowed-keys map should drive a **stricter per-role evidence
projection** (an `AgentSafeReportEvidenceView`) built before prompt assembly,
so each role only ever sees its own permitted sections — defense in depth on
both the prompt input and the generated output.

### 4.5 Failed-safe behavior

The validator fails **closed**. On any rejection:

- the specific failing unit (role section or synthesis) is dropped:
  `section_markdown`/`synthesis_markdown = None`, status set to
  `validation_failed` / withheld, `provider_status =
  "safety_validation_failed"`, generic `warning_codes` /
  `unavailable_reason` only;
- the raw offending text and the matched token/value are **never** surfaced to
  the user or written to the saved artifact; only a generic category code is
  recorded (internal logs may keep a path, never the value);
- the deterministic evidence draft remains the fallback content (it is always
  present because the evidence package is always present);
- if the validator itself errors, or the evidence package / saved scope is
  missing, no narrative is emitted and the report degrades to
  `deterministic_draft` or `source_snapshot`;
- report status is recomputed per section 6 after drops.

No partially-validated text is ever shown. A section is either fully validated
and shown, or withheld.

## 5. Saved Report Artifact Relationship

The report attaches to the **existing** P28A saved artifact model rather than
introducing a parallel report store.

- `SavedReviewArtifactRead.agent_summary: SavedAgentTeamSummaryRead | None`
  already exists and holds the saved Agent Team output. P29A-T2 report content
  maps onto it; deterministic-only artifacts keep `agent_summary = None`.
- `SavedAgentTeamSummaryRead` already carries `run_status`, `provider_mode`,
  `role_summaries` (each `SavedAgentTeamRoleSummaryRead` with `role_name`,
  `display_name`, `provider_status`, `summary_markdown`, `warning_codes`), and
  `warning_codes`.

Saved as sanitized report content (passes section 4 validator before persist):

- per-role `summary_markdown` (the validated `section_markdown`),
  `provider_status`, `warning_codes`, `display_name`, `role_name`;
- the run-level `run_status`, `provider_mode`, `warning_codes`.

Proposed minimal extension to `SavedAgentTeamSummaryRead` (P29A-T3, after
review) to give the report a persisted home for status and synthesis:

- `report_status: AgentTeamReportStatus`;
- `final_synthesis_markdown: str | None`;
- `final_synthesis_authored_by: "portfolio_manager_agent" | "deterministic_template" | None`;
- `evidence_schema_version: str`;
- `evidence_references: tuple[str, ...]` (keys only).

Every added field passes the same validator. If Codex C prefers, synthesis can
instead be stored as the `portfolio_manager_agent` role summary and
`report_status` derived at read time; the contract works either way and the
choice is an open question (section 8).

Audit/provenance only (never the headline, shown in disclosure):

- `source_snapshot` (artifact ref, source kind, generated/saved timestamps);
- `evidence_schema_version`, `provider_mode`, per-role `provider_status`,
  `warning_codes`, `safety_flags`;
- `scope_metadata`, `deterministic_summary`, freshness labels, `caveat_codes`,
  `limitations`.

Deterministic-only artifacts stay draft/fallback, not the primary endpoint:

- when `agent_summary` is `None` or its `run_status == "failed"`, the artifact
  renders as `source_snapshot` or `deterministic_draft` / `agent_unavailable`
  (section 6) — never `full_agent_report`;
- the deterministic evidence package is the fallback body; it is supporting
  analysis, not the product's primary narrative;
- the read view derives `AgentTeamReportRead` from the saved artifact (+ its
  `SavedEvidencePackageRead`) so the report is reproducible from
  generation-time evidence and never recomputed from current state.

## 6. Report Statuses

`AgentTeamReportStatus` — user-honest, never implying advice or readiness to
trade. This refines the architecture doc's recommended states
(`source_snapshot` / `draft` / `full_agent_report` / `agent_unavailable`) by
renaming `draft` to `deterministic_draft` and adding `validation_failed`.

| status | meaning | agent narrative | saved `run_status` |
| --- | --- | --- | --- |
| `source_snapshot` | deterministic evidence package saved; no Agent Team report attempted yet | none | `agent_summary = None` |
| `deterministic_draft` | deterministic evidence shown as draft/fallback; narrative intentionally not generated (e.g. blocked/unknown actionability gating) or pending | none (gated/pending) | `agent_summary = None` |
| `full_agent_report` | Agent Team narrative generated from the saved package and passed validation; primary product output (may be partial — flagged via `run_completeness` + role statuses) | present | `completed` or `partially_completed` |
| `agent_unavailable` | evidence saved, Agent Team generation failed/skipped safely for all roles (provider unavailable); deterministic draft is the fallback | none | `failed` |
| `validation_failed` | generation produced output but it failed the safety validator and no validated narrative can be shown; deterministic draft is the fallback, honest validation banner | none surfaced | `failed` |

Status decision rule (after validation + drops):

- no agent run requested/attempted → `source_snapshot`;
- actionability `blocked_*` → roles gated → `deterministic_draft`;
- at least one role section **and** the synthesis (PM-authored or deterministic
  template) validated → `full_agent_report`
  (`run_completeness = full` if every role validated, else `partial`);
- generation attempted, every role unavailable due to provider failure →
  `agent_unavailable`;
- generation attempted, output produced, but every role/synthesis narrative was
  rejected by the validator → `validation_failed`.

Wording rules for all statuses and copy:

- never say or imply: advice, recommendation, safe/ready to trade, buy/sell,
  order/execute, guaranteed return, AI-picked/automated decision;
- acceptable framing: "Saved review snapshot", "Agent Team analysis (analysis
  only)", "Generated from reviewed data available at the time", "Manual
  decision support";
- the deterministic fallback is labeled a draft/source snapshot, never a
  completed or approved review.

## 7. Files / Docs Changed

- Added: `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
  (this contract).
- Proposed plan status update for `docs/shared/implementation_plan.md`
  `P29A-T2` (applied after Codex B review PASS): see section 9.

No `backend/` code, schemas, routes, tests, or frontend files were created or
modified by this contract task.

## 8. Open Founder / Product Questions

- Public-analyst roles have almost no reviewed public evidence in the current
  P29A-T1 package (company/news/earnings deferred; economic/market-mood
  `not_reviewed`). Should P29A-T3 (a) include public roles but degrade them to
  "no reviewed public evidence", or (b) skip public roles until the public
  source/rights + evidence contract lands? (Persona analysis leans toward
  emphasizing Risk Manager + Portfolio Manager near-term.)
- Should `final_synthesis` be persisted as a first-class field on
  `SavedAgentTeamSummaryRead`, or stored as the `portfolio_manager_agent` role
  summary with `report_status` derived at read time?
- Should `report_status` be persisted, or always derived from saved
  `run_status` + presence of validated sections at read time?
- Should a partial `full_agent_report` (some roles unavailable) remain the
  primary product surface, or downgrade to `deterministic_draft` until all
  watched roles complete?
- Should `validation_failed` be a distinct user-visible state (recommended for
  honesty), or collapse into `agent_unavailable`?
- Should report generation run immediately after Trade Review save, or on
  demand from the saved source? (Carried from architecture open questions;
  affects whether `deterministic_draft` "pending" is common.)

## 9. Codex B Review Result

Codex B review (review-only sub-agent, contract/privacy/safety): **PASS**,
2026-06-14. No blockers. One important contract-spec inconsistency was raised
(section 4.4 availability rule vs. the four package-level citation categories
that have no `availability` field) and has been folded into section 4.4 as an
explicit carve-out. The section 4.3 layer-attribution polish (narrative
quantities caught by `GENERATED_METRIC_PATTERNS`, not value tokens) was also
applied. Remaining deferred polish from review is carried forward to P29A-T3:

- factor shared phrase/token vocabulary into one module (`safety_vocab.py`)
  with explicit Codex C / Codex B sign-off to avoid drift in shipped P29A-T1
  checks;
- resolve persistence of `report_status` / `final_synthesis` (section 8) in the
  T3 handoff before extending `SavedAgentTeamSummaryRead` so it is not extended
  twice.

Plan status line applied to `docs/shared/implementation_plan.md` P29A-T2:
contract accepted; Codex B PASS 2026-06-14; next P29A-T3 (Codex C).
