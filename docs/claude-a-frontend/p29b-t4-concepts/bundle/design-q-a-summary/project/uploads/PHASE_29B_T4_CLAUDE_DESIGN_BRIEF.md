# Phase 29B-T4 Claude Design Brief — Richer Agent Team Report

Status: discussion accepted; design brief ready (no frontend implementation yet).
Owner: Claude A (frontend). Design tool: Claude Design (concepts), Stitch optional later.
Reviewers: Claude B (visual/safety), Codex B (contract/privacy only if a read field changes).
Related plan: `docs/shared/implementation_plan.md` Phase 29B, task `P29B-T4`.
Builds on (shipped & reviewed):
- `docs/codex-b-architecture/PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md`
- `docs/claude-e-agentic/PHASE_29B_T2_PUBLIC_ROLE_AGENTIC_DESIGN.md`
- P29A Reports UI (`frontend/src/pages/ReportsPage.tsx`,
  `frontend/src/components/reports/*`).

How to use this brief: run Claude Design with the **current codebase attached**
(the founder will attach it). This brief defines the job, the locked direction,
the exact data Claude Design may use, the hard rails, and the artifacts to
produce. Claude Design produces **concepts only** — no code, no fields, no
contracts.

## 1. Job

Explore **2–3 information-hierarchy concept directions** for a richer saved Agent
Team report now that public analyst roles (`fundamentals_analyst`,
`news_analyst`, `technical_analyst`) can contribute. Concept mockups only, light
+ dark, at the 1024 / 1280 / 1440 content widths (sidebar is ~220px, so usable
content is narrower — design for no horizontal overflow).

## 2. Locked product direction (founder decisions)

- **Feel: analyst memo.** Synthesis-led editorial reading column; reasoned memo,
  not a dashboard or terminal.
- **Role weight: public analysts are secondary "market context."** Portfolio-aware
  roles (Risk Manager, Portfolio Manager) stay primary. Use a **grouped** layout,
  not the current flat five-card grid.
- **Provenance: compact trust strip + disclosure.** A small always-visible strip
  (coverage · saved time · saved scope) for trust; full audit in a disclosure.
- **Process: multiple directions, then decide.** 2–3 concepts → Claude B + Codex B
  rail-check → founder picks one → implement (Stitch vs Claude A decided then).

## 2.1 Claude Design's right to expand (founder directive)

Claude Design is the **divergent-concept** stage and **is encouraged to expand
beyond the current plan and read contract** — propose new additive read fields,
richer coverage/provenance structures, new role-grouping or comparison
affordances, or a better hierarchy than exists today. The P29B contract reserves
the "must not create new API fields" rule for **Stitch** (the later
implementation-acceleration stage), not for Claude Design's exploration.

That freedom is governed by exactly two things:

1. **Bright lines that never expand** (§4): safety wording; privacy / no raw
   private data; deterministic-vs-narrative distinction; manual-decision-support
   posture (no stock-picker / terminal); saved-report reproducibility; synthetic
   data only for design.
2. **Expansions are proposals, not facts.** Anything beyond the current read
   contract (§5, "Track B") is welcome — mock it — but must be **clearly labeled
   as a proposed additive field/structure** and routed to Codex C (contract) +
   Codex B (privacy/safety) before implementation. The live product never renders
   an unreviewed field or a fabricated value.

In short: explore and propose freely, including changes to the plan/contract;
just label what is new and let review decide what ships.

## 3. Current state to improve (reference; attached codebase)

- `ReportsPage.tsx` — library rail (saved analyses) + reading pane.
- `ReportDetail.tsx` — status banner → generate/retry → final synthesis (hero) →
  **Analyst sections (one uniform grid of all five roles)** → provenance.
- `AgentRoleSection.tsx` — per role: name, status badge, narrative or honest
  unavailable note, cited section-key chips, provider + warning-code footer.
- `ReportProvenance.tsx` — saved scope, cited evidence keys, audit disclosure
  (run/provider status, evidence schema, snapshot-saved / report-generated /
  saved-record-updated timestamps).
- `reportStatus.ts` — status vocabulary, tones, coverage helpers.

The main thing to redesign: the flat role grid flattens the portfolio-aware vs
public distinction, and public coverage/provenance is hard to scan.

## 4. Hard rails (bright lines — never expand, even in concepts)

These are the non-negotiables. Everything else is open to expansion (§2.1).

- The **shipped frontend** renders **reviewed backend fields only** and never
  fabricates values, role states, citations, freshness, rights, timestamps, or
  evidence. Claude Design concepts MAY *propose* additive fields/structures
  (§2.1, §5 Track B) — those are labeled proposals routed to contract review, not
  values invented in the live UI.
- No finance calculations / no metrics in copy.
- No advice / recommendation / buy / sell / hold / order / execution /
  submit / cancel / auto-trade / safe-to-trade / ready-to-trade / guaranteed-return /
  "you should buy/sell" / AI-stock-picker wording.
- Avoid the literal token **"prompt"** in visible copy (it is a forbidden value
  token in the saved-review validator).
- Deterministic evidence and Agent Team narrative must stay **visually and
  structurally distinct**.
- Multi-account / saved-scope honesty must remain explicit; never imply the
  current account selector reinterprets a saved report.
- Reports stays a **saved-analysis library**, not a raw thread/contract viewer.
- Synthetic/demo data only. No real account data, no real generated reports, no
  broker/provider payloads, no source URLs/bodies.

## 5. What the frontend actually has — Track A vs Track B

This is the most important constraint, to prevent invented fields.

**Track A — already in the report read contract (`GET /users/{uid}/reports[/{id}]`
→ `agent_summary`). Design freely with these; ships frontend-only:**

- Thread level: `title`, `report_type`, `created_at` (snapshot saved),
  `updated_at`, `scope_metadata` (saved scope labels).
- `agent_summary`: `run_status`, `provider_mode`, `report_generated_at` (nullable),
  `report_status`, `final_synthesis_markdown`, `final_synthesis_authored_by`,
  `evidence_schema_version`, `evidence_references` (section **keys**),
  `warning_codes` (incl. run-level coverage codes
  `public_evidence_roles_included` / `public_evidence_partial_coverage` /
  `public_evidence_roles_skipped`).
- Per role (`role_summaries[]`): `role_name`, `display_name`, `role_status`
  (`completed` / `unavailable` / `skipped` / `gated` / `validation_failed`),
  `provider_status`, `summary_markdown`, `evidence_references` (section **keys**),
  `warning_codes`, `unavailable_reason`.

Note: per-section **freshness / rights_status / source_label / facts / as_of**
are NOT in this read contract. Citations are section-key granularity; freshness
and limitations are expressed **inside the narrative text** and via warning
codes. Coverage is derivable from `role_status` + the run-level coverage codes.

**Track B — expansion proposals beyond today's read contract (encouraged).**
Claude Design may propose per-section freshness/rights/source chips, a structured
coverage object (e.g. the deferred `public_evidence_coverage` descriptor, T2 §8),
or other additive read fields/structures that make the report better. These are
welcome — mock them with synthetic data and **label every Track-B element
clearly** as a proposed additive field. They become contract requests for
Codex C + Codex B and are not assumed to ship until reviewed; the live UI never
renders an unreviewed field.

Scope note: Track A can ship as a frontend-only change; Track B adoption depends
on which proposals review accepts. **Do not pre-constrain the exploration** —
pick scope at the design review, after seeing the concepts.

## 6. Synthetic payload set (use these; all values are demo-only)

Instrument label is a neutral demo (e.g. "Trade review · stock buy · DEMOCO").
Narratives are analysis-only, non-directional, no metrics, no forbidden wording.

### 6a. `source_snapshot`
`agent_summary = null`. Detail shows: only "Snapshot saved" time, the honest
"saved deterministic snapshot" banner, an optional Generate action, and saved
scope. No role sections. (Frame as a complete kept analysis, not unfinished.)

### 6b. `full_agent_report` — public roles included (partial run)
```
report_status: "full_agent_report"
run_status: "partially_completed"
report_generated_at: "2026-06-15T20:06:00Z"   (distinct from created_at)
final_synthesis_authored_by: "deterministic_template"
final_synthesis_markdown: "Agent Team analysis is generated from the saved
  evidence package. Deterministic backend services own all calculations; scope,
  freshness, and caveats remain attached for audit."
warning_codes: ["public_evidence_partial_coverage"]
role_summaries:
  - risk_management_agent / "Risk Manager" / completed / ok
    summary: "Risk review uses the saved deterministic evidence package only. It
      highlights the saved actionability mode, freshness labels, and caveats for
      manual review."
    evidence_references: [trade_intent_summary, scope_state, actionability,
      account_readiness, freshness, portfolio_impact_summary,
      concentration_risk_drift, liquidity_collateral_caveats,
      options_exposure_summary, market_quote_freshness]
  - portfolio_manager_agent / "Portfolio Manager" / completed / ok
    summary: "Portfolio synthesis uses validated role summaries and the saved
      evidence package only. Deterministic backend services own all calculations."
  - fundamentals_analyst / "Fundamentals Analyst" / completed / ok
    summary: "Reviewed public company-profile and fundamentals labels describe
      the instrument's sector and business category. Specific figures are not
      provided in the reviewed evidence and are not generated here."
    evidence_references: [trade_intent_summary, public_company_profile,
      public_fundamentals_snapshot]
    warning_codes: ["public_evidence_limited"]
  - news_analyst / "News Analyst" / completed / ok
    summary: "Reviewed public news and event metadata note an upcoming scheduled
      event. The reviewed summary is limited and may be stale; treat it as
      historical context to verify manually."
    evidence_references: [trade_intent_summary, public_news_snapshot,
      public_events_calendar]
    warning_codes: ["public_evidence_limited"]
  - technical_analyst / "Technical Analyst" / skipped / skipped
    summary: null
    unavailable_reason: "no_reviewed_public_evidence"
    evidence_references: [trade_intent_summary]
    warning_codes: ["no_reviewed_public_evidence"]
```

### 6c. `full_agent_report` — partial public coverage
Like 6b but only fundamentals `completed`; news + technical `skipped`
(`no_reviewed_public_evidence`). Coverage descriptor should read honestly
(e.g. "1 of 3 public analysts contributed").

### 6d. Public roles skipped (`not_reviewed`) — today's default
All three public roles `skipped` / `no_reviewed_public_evidence`,
`summary_markdown: null`, `evidence_references: [trade_intent_summary]`. Risk +
PM `completed`. `report_status: "full_agent_report"`,
`warning_codes: ["public_evidence_roles_skipped"]`. Show a compact
"Public market analysts are not yet enabled" coverage note; do not frame as
broken. Also include the `not_available` and `not_applicable` skip variants
(different `unavailable_reason`) so the design handles all three honestly.

### 6e. `agent_unavailable`
`report_status: "agent_unavailable"`, `run_status: "failed"`, all roles
`unavailable` / `provider_unavailable`, `summary_markdown: null`. Banner:
deterministic evidence remains; honest "narrative unavailable" + a "Try again"
re-run affordance. Deterministic evidence still present.

### 6f. `validation_failed`
`report_status: "validation_failed"`, `run_status: "failed"`,
`final_synthesis_markdown: null`, role(s) `validation_failed` /
`safety_validation_failed`. Banner: "narrative withheld by safety validation";
offending text is never shown. Deterministic evidence remains; "Try again".

### 6g. Role-summary variants to cover in mocks
Fundamentals `completed`; news `completed` but limited/stale (staleness stated in
narrative + `public_evidence_limited`); technical `completed`; a public role
`skipped` across the three reasons (`no_reviewed_public_evidence`,
`public_evidence_not_available`, `public_evidence_not_applicable`).

### 6h. Track-B mock only (label clearly; needs backend field first)
If exploring richer per-section provenance, mock an optional
`public_evidence_coverage` descriptor (e.g. contributed vs skipped counts/labels;
optional per-section freshness/rights chips). Mark every such element
**"Track B — requires additive read field (Codex C/Codex B)."**

## 7. Artifacts to request from Claude Design

1. **2–3 named concept directions** for the report reading pane, each rendering:
   - the grouped role layout (Portfolio-aware primary / Public market context
     secondary);
   - the compact trust strip (coverage · snapshot-saved + report-generated times ·
     saved scope) with audit in disclosure;
   - all six report states (6a–6f) and the role variants (6g);
   - light + dark, at 1024 / 1280 / 1440.
2. A short rationale per direction (hierarchy choices, how public stays
   secondary, how deterministic vs narrative stays distinct).
3. Explicit **Track A vs Track B labeling** on every element.
4. Library-rail treatment if a direction changes how states/coverage read in the
   list.

## 8. Open decision points (settle at design review, not now)

- **Which Track-B expansions (if any) to adopt** — decided at the design review
  from the concepts, not pre-constrained here. Track A can ship frontend-only;
  accepted Track-B proposals go to Codex C / Codex B as additive contract changes.
- Coverage placement — default: compact, in the trust strip near the top.
- Skipped public roles — default: summarized compactly in the market-context
  band, per-role detail on expand.

## 9. Sequencing & gate

Discussion (done) → assemble/confirm synthetic payloads (this brief) →
Claude Design 2–3 concepts (codebase attached) → Claude B + Codex B rail-check →
founder selects one → implement (Stitch vs Claude A decided then) → Claude B
visual review → Codex B contract review only if a read field changed.

**Gate: no frontend implementation begins until the chosen direction and the
synthetic sample payloads are agreed.** Stitch, if used, comes only after a
direction is accepted, consumes reviewed synthetic payloads, and never defines
fields, semantics, report states, or safety copy.
