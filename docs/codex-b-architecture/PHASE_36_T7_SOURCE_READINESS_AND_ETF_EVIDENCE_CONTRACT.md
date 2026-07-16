# Phase 36 T7 Source Readiness And ETF Evidence Contract

Status: approved architecture contract for implementation slicing

Owner: Codex B

## 1. Problem

The current saved-report generation path accepts a reviewed symbol and then
asks issuer-oriented public sources for company profile, filings, statement
fundamentals, and end-of-day history. That is correct for an operating company
when each source supports the symbol. It is not a valid instrument classifier.

An ETF may be active and supported by Trade Review while SEC company-ticker and
company-statement lookups return no issuer match. Those source outcomes mean
only that the requested evidence lane is unavailable or inapplicable. They do
not mean that the symbol is invalid.

The product must resolve instrument identity before public-source acquisition,
freeze that identity with the saved review, and report source readiness before
spending an LLM run.

## 2. Binding Decisions

### 2.1 Backend-owned instrument identity

For stock/ETF review flows, the normalized Nasdaq Symbol Directory record is
the preferred backend-owned classifier. The frozen identity is one of:

- `operating_company_equity`
- `etf_or_fund`
- `unknown`

The saved identity also carries a safe resolution status:

- `confirmed`: the normalized directory record resolved the instrument kind;
- `declared_only`: directory data was unavailable and the review flow supplied
  the only classification;
- `mismatch_reconciled`: the submitted stock/ETF flow disagreed with the
  normalized directory record and the backend used the directory record;
- `unresolved`: neither reviewed source established the kind.

The directory source label and as-of label may be frozen as safe provenance.
No raw directory rows, URLs, payloads, or provider identifiers may be frozen.

Options reviews keep their reviewed strategy flow. Their public-source target
is the normalized underlying instrument, with `unknown` used when the
underlying kind was not resolved.

### 2.2 Reconciliation behavior

For a stock/ETF preview, the backend reconciles the submitted flow with the
directory asset class before deterministic exposure calculations. A confirmed
ETF uses the ETF intent path even if the client submitted the stock variant,
and the inverse applies to a confirmed operating-company equity.

The response includes an honest caveat when reconciliation occurred. The
client does not compute or override instrument identity.

When directory data is unavailable, the backend may preserve the submitted
flow as `declared_only`, but report generation must not present that declaration
as externally confirmed.

Historical saved reviews are immutable. A previously frozen review is never
reclassified from a current directory snapshot. A corrected review requires a
new preview and saved source.

### 2.3 Source readiness is separate from LLM generation

Add a backend-only report preparation operation:

`POST /users/{user_id}/reports/{thread_id}/prepare-evidence`

It performs no LLM call. It resolves only reviewed, enabled public-source
clients, acquires normalized evidence for a fresh package, freezes the package,
and returns a privacy-safe readiness summary.

The response contains only:

- frozen instrument kind and resolution status;
- overall readiness: `ready`, `partial`, or `not_ready`;
- per-lane requirement: `required`, `optional`, or `not_applicable`;
- per-lane availability and safe caveat codes;
- whether the result came from newly prepared or already frozen evidence.

It must not return facts, values, holdings, account labels, raw references,
URLs, provider payloads, credentials, prompts, traces, or report prose.

Calling preparation again on the same frozen package performs zero source
calls. Report generation reads the frozen package and performs zero source
calls when preparation has already completed. Readback never recomputes.

### 2.4 Capability matrix

#### Operating-company equity

For the five-role Phase 36 acceptance profile:

- FMP end-of-day history: required;
- SEC company profile: required;
- SEC recent filing metadata: required;
- FMP normalized statement fundamentals: required;
- ETF-specific evidence: not applicable.

Any missing required lane makes readiness `partial` or `not_ready`. It does not
make the symbol invalid.

#### ETF or fund

For the future five-role ETF acceptance profile:

- reviewed end-of-day history: required when the approved provider supports it;
- reviewed ETF identity/profile metadata: required;
- reviewed holdings or exposure-composition evidence: required for
  holdings-aware fundamental and overlap claims;
- reviewed fund filing/event metadata: optional unless a later contract makes
  it required;
- operating-company statement fundamentals: not applicable;
- operating-company SEC profile and issuer filing lanes: not applicable unless
  a separate reviewed mapping explicitly establishes the fund issuer boundary.

Until ETF-specific lanes are approved and implemented, an ETF preparation
result is `not_ready` for five-role acceptance and carries an explicit
`etf_evidence_contract_not_available` caveat. Deterministic Trade Review may
still complete with honest classification and evidence gaps.

#### Unknown instrument

Unknown instruments are `not_ready` for five-role generation. No source result
may be used to infer that the symbol is invalid. The safe reason is
`instrument_kind_unresolved`.

### 2.5 Exposure narration

Sector and industry narratives must use the proposed trade's own reviewed
classification. They must never choose a pre-existing portfolio bucket merely
because that bucket exists.

If the trade classification is unavailable, the narrative must state that the
reviewed trade is excluded from classification buckets. It must not display an
unchanged bucket as though it were the proposed trade's impact, and it must not
infer ETF overlap from unrelated holdings.

## 3. Source Rights Boundary

The current approved lanes remain unchanged:

- FMP end-of-day history;
- FMP normalized company statement facts;
- SEC EDGAR company profile metadata;
- SEC EDGAR recent filing metadata;
- approved FRED metadata/series lanes where separately enabled.

This contract does not approve an ETF holdings, ETF profile, fund filing, or
general-news source. Each new ETF source requires a separate review of official
access method, attribution, retention, request budget, normalized fields, and
prompt use. No scraping or silent source substitution is allowed.

## 4. Privacy And Safety

- Public-source requests receive only the reviewed normalized symbol required
  by that lane.
- Instrument identity and readiness never include account references, account
  labels, balances, buying power, holdings, positions, quantities, lots, or
  broker/provider identifiers.
- LLM prompts continue to receive only sanitized frozen ToolResult envelopes.
- Missing evidence remains a gap, never a conclusion or an overall verdict.
- The read-only posture, backend-owned calculations, citation ownership,
  frozen readback, and no broker-action boundary remain unchanged.
- No advice, recommendation, order, execution, safety-to-act, readiness-to-act,
  or return-guarantee posture may be introduced.

## 5. Implementation Slices

### P36-T7-J4A - Instrument reconciliation and freeze

Owner: Codex C

- Resolve stock/ETF identity through the normalized symbol directory.
- Reconcile stock/ETF preview intent before deterministic calculations.
- Freeze the resolved identity, status, and safe provenance in the saved review
  and `SavedEvidencePackageRead`.
- Preserve legacy saved artifacts with an `unknown`/derived compatibility path.
- Add stock, ETF, mismatch, unavailable-directory, options-underlying, and
  frozen-readback tests.

Acceptance: a synthetic ETF submitted through the stock variant is processed
as an ETF, the mismatch is visible as a caveat, and readback does not consult a
newer directory snapshot.

### P36-T7-J4B - Evidence preparation and readiness

Owner: Codex C

- Add the no-LLM preparation operation and safe response model.
- Reuse the reviewed route source resolvers; do not add source configuration.
- Freeze normalized public evidence once per saved package.
- Add idempotency and source-call tripwire tests.
- Add operating-company, ETF, unknown, partial, and all-ready readiness tests.

Acceptance: readiness is available before generation, preparation never calls
an LLM, and a repeated call or report readback makes zero source calls.

### P36-T7-J4C-backend - Generation gate

Owners: Codex B contract, Codex C implementation

- Founder acceptance runs require frozen readiness=`ready`. `partial` and
  `not_ready` do not enter five-role generation.
- Consult the thread's frozen readiness before provider resolution or any
  generation work. Generation does not acquire, refresh, or replace evidence.
- Refuse every Section 7 stop condition with a closed-enum, privacy-safe
  response containing no source facts, values, labels, raw references, URLs,
  payloads, prompts, or free-form provider prose.
- Keep deterministic Trade Review available and honest when five-role
  generation is refused.

Acceptance: every refusal path resolves zero LLM providers, makes zero source
calls, writes no Agent Team summary, and leaves the frozen artifact unchanged;
the `ready` path preserves the existing generation behavior.

### P36-T7-J4C-frontend - Readiness presentation (deferred)

Owners: Claude A or Claude F frontend, Claude B visual/accessibility review

- Present readiness and role availability without exposing raw codes or
  financial values.
- Keep frontend logic display-only.
- Design the ordinary-user explicit continue-with-`partial` workflow under a
  separate contract review; no partial override exists in J4C-backend.

This surface is deferred until after the live five-agent milestone and does not
gate the founder acceptance run.

### P36-T7-J4D - ETF source-rights and tool pack

Owners: Codex B source contract, Codex C implementation, Claude H domain review

- Select official ETF profile/holdings/fund-event sources.
- Approve only normalized evidence necessary for the ETF analyst roles.
- Add source budgets, freeze rules, prompt/tool boundaries, and offline fakes.

This slice is blocked until the source-rights decision exists.

### P36-T7-J4E - Stock and ETF acceptance

Owner: Codex B coordination

- Run one synthetic/disposable operating-company report and one synthetic ETF
  report through prepare, generate, and frozen readback.
- A real-data run still requires separate founder authorization.

## 6. Review Gates

- Codex B: schema/API/privacy/source-readiness contract review for J4A/J4B.
- Claude H: ETF evidence sufficiency and role-domain review before J4D closes.
- Claude E: Agent Team role/eval review only when ETF ToolResult envelopes or
  role behavior change.
- Claude B: visual/accessibility review for the deferred J4C-frontend surface.
- Founder: separate authorization for any external-source or live-LLM run on a
  private saved review.

## 7. Stop Conditions

Stop and report rather than generating when:

- instrument kind is unresolved for a five-role acceptance run;
- a required source lane is not configured or is unavailable;
- an ETF has no reviewed ETF-specific evidence contract;
- source preparation detects private or raw provider data;
- evidence is already frozen and a caller asks to replace it in place.

These stop conditions protect acceptance claims. They do not prevent an honest
deterministic Trade Review from showing what was and was not evaluated.
