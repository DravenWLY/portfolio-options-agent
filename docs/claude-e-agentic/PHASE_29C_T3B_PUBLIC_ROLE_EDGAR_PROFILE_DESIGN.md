# Phase 29C-T3B Public-Role Behavior Design For Saved EDGAR public_company_profile

Status: design draft (design-only; no backend/frontend code in this task)
Owner: Claude E (agentic-system design)
Reviewer: Codex B (architecture/privacy/safety)
Related plan: `docs/shared/implementation_plan.md` Phase 29C, task `P29C-T3B`
Builds on (shipped):
- `docs/codex-b-architecture/PHASE_29C_PUBLIC_EVIDENCE_SOURCE_GOVERNANCE.md` (+ Codex A source-rights approval, 2026-06-20)
- P29C-T3A: generation-time EDGAR `public_company_profile` integration (Codex C, Codex B PASS)
- `docs/claude-e-agentic/PHASE_29B_T2_PUBLIC_ROLE_AGENTIC_DESIGN.md`
- `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
- Shipped P29B-T3B public-role wiring + validator guards

## 1. Scope And What Already Exists

Design-only: define how the three public analyst roles may safely use saved,
generation-time SEC EDGAR `public_company_profile` evidence in Agent Team
reports. No code in this task; no runtime EDGAR tools, web search, frontend
fields, or new backend fields/endpoints/storage. Output is implementation
guidance for a later Codex C slice plus a test matrix.

Already shipped and reused as-is:
- T3A normalizes EDGAR submissions metadata into the existing
  `SavedPublicEvidenceSectionRead` (`public_evidence.py:_normalize_edgar_profile_section`):
  facts `company_name`, `ticker`, `exchange`, `cik_reference`, `sic_label`,
  `fiscal_year_end`; `availability` `available`/`limited`;
  `source_label = "SEC EDGAR metadata - company profile only"`;
  `rights_status = "reviewed"`; `collected_at`; limitations carrying the
  retention note and the SIC caveat; `caveat_codes`
  (`edgar_profile_partial_metadata` when limited). Unavailable/disabled/
  unresolved cases return an `availability = "not_available"` section with
  honest `caveat_codes`.
- T3A freezes that section in `saved_artifact_json.public_evidence` on the same
  `SavedEvidencePackageRead` used for role projection, package-aware validation,
  and persistence; opening/regenerating reuses saved evidence and never
  re-fetches EDGAR.
- P29B-T3B wires public roles through `build_public_role_evidence_projection`
  with honest fail-closed degradation, and the validator already enforces
  per-role citation allowlists + nested availability via
  `validate_agent_team_report_output(..., evidence_package=evidence)`.

The citation allowlists already encode the correct boundary:
`fundamentals_analyst` may cite `public_company_profile`; `news_analyst` and
`technical_analyst` may not (and the projection's `_PUBLIC_ROLE_SECTION_KEYS`
does not even hand it to them); `portfolio_manager_agent` may reference it for
synthesis.

This task changes **agent narrative behavior** for the fundamentals role and PM
synthesis when `public_company_profile` is `available`/`limited`; it does not
change the schemas or the validator seam.

## 2. Q1 — Fundamentals Analyst Use Of public_company_profile

When the role-scoped projection's `public_company_profile` is `available` or
`limited`, `fundamentals_analyst` becomes `completed` and may cite and summarize
it as **company identity / listing metadata context only**.

Citation: `evidence_references` includes `public_company_profile` (plus the
always-citable `trade_intent_summary`), exactly as the shipped wiring already
produces. No new reference granularity — citations stay at section-key level;
the literal identity values live in the section's structured `facts`, which are
already validated and reproducible.

Narrative rules (deterministic template built by Codex C from the projection
facts; not LLM-authored), the role summary may:
- state that reviewed SEC EDGAR company identity/listing metadata is available;
- name, qualitatively, which identity facts are present — company name, ticker,
  listing exchange, CIK reference, SEC SIC regulatory classification metadata,
  and fiscal year-end metadata — as background for the reviewed instrument;
- carry the short source label `SEC EDGAR metadata - company profile only`;
- carry the SIC caveat (section 6.2);
- state what remains unknown (e.g. fundamentals snapshot / events not reviewed)
  when the other fundamentals sections are not citable.

The narrative must NOT:
- inline digit-bearing literal values (the CIK number, fiscal-year digits) into
  the prose — keep them in the structured `facts` (section 6.3 rationale);
- infer or state a modern sector/industry/sub-industry/peer group from SIC;
- derive valuation, suitability, eligibility, actionability, trade timing, or
  any directional/strategy conclusion from identity metadata;
- imply SEC endorsement;
- use advice/recommendation/buy/sell/hold/order/execution/guaranteed/
  safe-or-ready-to-trade wording.

Realistic near-term shape: EDGAR-only. `public_fundamentals_snapshot` and
`public_events_calendar` remain `not_reviewed`, so a `completed`
fundamentals role typically cites only `public_company_profile` and explicitly
notes the other two are not available.

## 3. Q2 — News And Technical Analysts

`news_analyst` and `technical_analyst` must ignore `public_company_profile`.
This is already enforced two ways and requires no change:
- the validator allowlists (`ROLE_ALLOWED_EVIDENCE_KEYS`) exclude
  `public_company_profile` from both roles, so a citation fails closed;
- `_PUBLIC_ROLE_SECTION_KEYS` does not include `public_company_profile` for
  these roles, so their projections never receive it.

They continue to degrade on their own sections (still `not_reviewed` by
default), so in an EDGAR-only run they remain `skipped`/`no_reviewed_public_evidence`
while fundamentals completes. The design ratifies this; do not widen their
boundary to company-profile metadata in this slice.

## 4. Q3 — Portfolio Manager Synthesis

PM synthesis (and the PM role summary) may use the validated fundamentals
public summary and may note that **company identity/listing metadata context is
included**, strictly as analysis-only background. It must not:
- turn identity/SIC metadata into a verdict, recommendation, signal, suitability
  judgement, or sector-based reasoning;
- introduce new facts or numbers;
- cite `public_company_profile` unless its availability is `available`/`limited`
  (PM allowlist already includes the key; the availability gate still applies).

When the profile is unavailable, PM synthesis simply omits company-identity
context and proceeds from the portfolio-aware roles, per the shipped coverage
logic.

## 5. Q4 — Unavailable / not_reviewed Behavior And Exact Degradation Wording

Degradation reuses the shipped P29B-T3B matrix; EDGAR maps onto it through the
section `availability` that T3A already sets.

| profile state at generation | projection result | fundamentals role outcome |
| --- | --- | --- |
| `available` (all required + optional facts) | citable | `completed`; cites `public_company_profile`; full identity context + SIC caveat |
| `limited` (required facts present, some optional missing) | citable | `completed` + `public_evidence_limited` + the shipped limited caveat; surface only present facts; no SIC claim if `sic_label` absent |
| `not_available` (EDGAR disabled / symbol unresolved / CIK invalid / incomplete / replay error) | not citable; degrade_reason `public_evidence_not_available` | `skipped`, `provider_status="skipped"`, `summary_markdown=None`, `unavailable_reason="public_evidence_not_available"` |
| `not_reviewed` (default, no EDGAR run) | not citable; degrade_reason `no_reviewed_public_evidence` | `skipped`, `unavailable_reason="no_reviewed_public_evidence"` |
| projection assembly raises | exception path | `unavailable`, `provider_status="provider_unavailable"`, `unavailable_reason="public_evidence_provider_unavailable"` |

Exact wording rules:
- skipped/unavailable roles emit no narrative (`summary_markdown=None`); the
  honest reason lives in `unavailable_reason`/`warning_codes` only.
- a `completed`-from-profile-only role must name what is unavailable
  (fundamentals snapshot, events) without defect or trading-readiness framing.
- `limited` profiles must carry the limited caveat and must not present partial
  identity metadata as complete.
- never recompute or re-fetch on read; reopening a saved report shows the frozen
  section verbatim (T3A guarantee).

## 6. Q5 — Validator / Output-Safety Expectations Before Codex C

The package-aware seam stays the enforcement point: Codex C must keep
`validate_agent_team_report_output(payload, label=..., evidence_package=evidence)`
on the full report payload before persistence, with `evidence` being the same
instance whose `public_evidence` holds the EDGAR section. Availability is only
enforced there (the per-role-summary model validator runs without the package).

### 6.1 Attribution wording collides with the advice-phrase validators (key finding)

The mandated **full** attribution sentence — "Source: SEC EDGAR submissions
metadata. Company identity and listing metadata only. **Not investment advice or
a trading signal.**" — contains the substring "investment advice", which is in
both `_SAVED_REVIEW_PROHIBITED_PHRASES` (so `validate_public_evidence_payload`
and `validate_saved_review_artifact_payload` reject it) and
`REPORT_PROHIBITED_PHRASES` (so the report-output validator rejects it). The
validators use naive substring matching and cannot distinguish the negated form.

Consequently the full attribution sentence MUST NOT be stored in any validated
backend/agent field (evidence section, facts, limitations, role
`summary_markdown`, synthesis). This matches what T3A already does — the section
stores only the **short** label `SEC EDGAR metadata - company profile only`
plus the SIC caveat, never the full sentence.

Design decision: the full mandated attribution sentence is **frontend-owned
display chrome**, rendered deterministically whenever the saved
`public_company_profile` source is SEC EDGAR (keyed off `source_label` /
`source_key`), in P29C-T4. It is fixed boilerplate, not generated or persisted,
so reproducibility is preserved (the saved section already records the source
identity). The agent/backend layer conveys the same substance with safe wording
(short source label + "company identity and listing metadata only" + the SIC
caveat) and never the "investment advice" token. Do not weaken the validators to
allow the negation in this slice.

Naming note for Codex C: the stored `source_label` is exactly
`SEC EDGAR metadata - company profile only`. "SEC EDGAR submissions metadata"
appears only as descriptive prose / inside the full frontend attribution
sentence; it is not the stored label and must not be substituted for it in
validated fields.

### 6.2 SIC caveat posture

`sic_label` may be used only as **SEC SIC regulatory classification metadata**,
never as a modern sector/industry/sub-industry/peer-group label. Whenever
`sic_label` is surfaced, the narrative/display must carry the caveat already in
the section limitations: SEC SIC metadata may be broad, legacy, and may lag
company changes, and does not constitute financial analysis or a classification
of the company's current business. If `sic_label` is absent (`limited`), the
role must make no SIC statement at all.

### 6.3 Keep digit-bearing identity facts out of generated prose

`cik_reference` (e.g. `CIK 0000320193`) and `fiscal_year_end` (e.g. `12/31`)
carry digits. They are safe in the structured `facts` (validated by the
public-evidence validator, which has no level/metric guard and is not part of
the report-output phrase scan). They must stay there and not be inlined into
`summary_markdown`, because a company name containing a level keyword (real
example: `Support.com`; also `Target`, `Pivotal`) placed near those digits in
prose could trip `INVENTED_LEVEL_PATTERNS` in the report-output validator. The
deterministic fundamentals template therefore names facts qualitatively and
keeps prose digit-free; literal values render from the structured facts (backend
now, frontend in T4). This both avoids false positives and keeps the narrative
clean.

### 6.4 Other guards (unchanged, must keep passing)

- `SOURCE_LEAK_PATTERNS` (URLs): the section already carries no URLs; CIK
  reference is identity metadata, not a URL, and must not be rendered as a link.
- `GENERATED_METRIC_PATTERNS` / advice / private-data guards continue to apply;
  identity metadata introduces no `$`/`%`/share-count/Greek/price-target tokens.
- No raw EDGAR payload, filing body, XBRL, insider, news, or raw URL may ever
  reach output (already rejected at the evidence layer and by report guards).

### 6.5 Optional future guard (proposal only — not this slice)

A focused additive guard rejecting sector/industry-classification *claim*
wording (e.g. "the company is in the X sector/industry", "classified as X
industry") in public-role output would harden against SIC over-interpretation if
an LLM ever authors this narrative. Labeled **future proposal only**; the
deterministic template makes it unnecessary now, and adding it needs a separate
Codex B contract review.

## 7. Q6 — Report-Output Fields Sufficiency

Existing fields are sufficient; **no additive report-output field is proposed**.
`SavedAgentTeamRoleSummaryRead` (`role_status`, `provider_status`,
`summary_markdown`, section-key `evidence_references`, `warning_codes`,
`unavailable_reason`) carries everything needed. Identity facts, source label,
SIC caveat, freshness, and `collected_at` already live in the frozen
`public_company_profile` section for reproducibility and (future) frontend
rendering. The full attribution sentence is frontend chrome (section 6.1), not a
stored field. Any future additive field (e.g. a discrete attribution field) is
**future proposal only** and would require separate Codex B contract review.

## 8. Reproducibility (unchanged, central)

- No refetch and no current-state recomputation: the frozen
  `public_company_profile` is read back from `saved_artifact_json.public_evidence`;
  regeneration reuses it (T3A guarantee).
- The same `SavedEvidencePackageRead` instance is used for projection,
  package-aware validation, and persistence.
- Provider/agent failure leaves a deterministic report with honest fundamentals
  degradation; it never blocks report generation.

## 9. Test Matrix For Codex C (synthetic, offline, deterministic)

Use injected fake EDGAR clients / synthetic sections only; no network. Validate
each report payload through `validate_agent_team_report_output(...,
evidence_package=evidence)`.

Positive:
- POS-1 EDGAR profile `available` (all facts) -> fundamentals `completed`, cites
  `public_company_profile` + `trade_intent_summary`; prose carries short source
  label + SIC caveat, is digit-free, passes package-aware validation.
- POS-2 EDGAR profile `limited` -> `completed` + `public_evidence_limited` +
  limited caveat. `limited` is reachable whenever any optional fact
  (`exchange`/`sic_label`/`fiscal_year_end`) is missing, so cover both: (a)
  `sic_label` absent -> assert no SIC statement at all; (b) `sic_label` present
  but `exchange`/`fiscal_year_end` missing -> assert the SIC caveat is present
  and no over-claim.
- POS-3 EDGAR profile `available`, other fundamentals sections `not_reviewed` ->
  `completed` citing only `public_company_profile`, names the unavailable
  sections honestly.
- POS-4 company name containing a level keyword (`Support.com`, `Target`) with
  profile `available` -> `completed`, NO invented-level false rejection (proves
  digit-free prose / facts-stay-structured rule).
- POS-5 EDGAR profile `available` but news/technical sections `not_reviewed` ->
  news/technical `skipped` (ignore company profile); coverage `partial`.
- POS-6 PM synthesis with profile `available` -> references identity context as
  background only, no verdict/sector reasoning, passes validation.
- POS-7 regenerate after profile saved -> reuses saved section, no refetch,
  identical citations/availability (ratifies T3A).

Negative (must fail closed):
- NEG-1 `news_analyst` cites `public_company_profile` -> rejected (role boundary).
- NEG-2 `technical_analyst` cites `public_company_profile` -> rejected.
- NEG-3 fundamentals cites `public_company_profile` while availability
  `not_available`/`not_reviewed` -> rejected (availability) via package-aware
  validation.
- NEG-4 any output field containing the literal "...Not investment advice or a
  trading signal." -> rejected (documents why full attribution is frontend
  chrome).
- NEG-5 fundamentals prose asserting a modern sector/industry from SIC -> the
  deterministic template must never emit it (assert absence); optional future
  guard otherwise.
- NEG-6 raw EDGAR payload / filing-body / raw URL token in output -> rejected.
- NEG-7 provider/assembly failure -> fundamentals `unavailable` /
  `public_evidence_provider_unavailable`, no narrative, report still valid.

## 10. Codex B Review Result

Codex B review (review-only sub-agent, architecture/privacy/safety): **PASS**,
2026-06-21. No blockers, no important issues. All seven acceptance criteria were
verified against shipped code:

- role boundary is double-gated (`ROLE_ALLOWED_EVIDENCE_KEYS` +
  `_PUBLIC_ROLE_SECTION_KEYS`); news/technical cannot receive or cite
  `public_company_profile`; PM uses it as background only;
- the attribution finding is correct — "investment advice" is in both
  `_SAVED_REVIEW_PROHIBITED_PHRASES` and `REPORT_PROHIBITED_PHRASES`, all
  report-output guards use naive `repr().lower()` substring matching, and the
  shipped `policy.attribution_label` is defined but never stored; routing the
  full sentence to frontend chrome is governance-compliant;
- the digit-bearing-facts rationale holds (the package is consumed only for
  `section_key`/`availability`, not fact values, so structured facts are not
  phrase/level-scanned);
- degradation, reproducibility, and no-new-fields claims all match shipped code.

Three deferred-polish notes were applied: fixed the 5.x -> 6.x subsection
numbering and cross-references; added a Codex C naming note distinguishing the
stored short `source_label` from the descriptive "submissions metadata" prose
(section 6.1); and broadened POS-2 to cover both `sic_label`-absent and
`sic_label`-present `limited` shapes. Plan status applied to
`docs/shared/implementation_plan.md` P29C-T3B.

Stop for Codex B review before any Codex C implementation or frontend work
(this design is the gate; the next slice is a separate implementation task).
