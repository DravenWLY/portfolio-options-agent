# Phase 32A Real-Source Golden-Path Backend Gap Audit

Status: P32A-T8 accepted blocker map / next-sequence source of truth.

## What Works Today

- Account Details can project synced broker-account rows as `private_real_source`
  using opaque `acctref_...` references and backend-owned display labels.
- Portfolio-backed Trade Review accepts `review_account_selection` with an opaque
  app account reference and keeps it separate from portfolio context scope.
- Saved review source materialization persists backend-owned scope and
  deterministic summary data, with saved-source caveat codes sanitized before
  entering saved artifacts.
- `SavedEvidencePackageRead.from_saved_review_artifact(...)` derives a lossy
  agent-safe evidence package from saved artifact data rather than current
  Account Details state.
- Explicit Agent Team report generation reads saved evidence and regeneration
  replaces only the generated summary while preserving the saved source snapshot,
  saved scope, deterministic summary, source timestamps, and saved public
  evidence.

## P32A-T2/T3 Backend Gaps

### Nickname Contract

- Add a backend-owned nickname/display contract for selector use that is distinct
  from raw broker display names.
- Nicknames should be user-scoped, validated, optional, and safe for Account
  Details and selector surfaces.
- Saved reports should keep generation-time reviewed labels only; current
  nickname edits must not rewrite historical saved scope.

### Searchable Selector Contract

- Add a user-scoped account-selector read model that returns only opaque account
  references, backend-owned labels, source/status/freshness labels, and caveats.
- Search/filter inputs should never accept provider IDs, broker account IDs,
  account numbers, raw broker display names, cash labels, holdings, positions, or
  provider metadata.
- Unknown and cross-user references must fail closed without disclosing account
  existence.

### Deterministic Feasibility Blockers

- Account-level feasibility remains caveated for real-source broker accounts.
- Broker cash, available cash, buying-power, collateral, position rows, option
  rows, quantities, and lots remain display-only until current-position truth,
  collateral semantics, and buying-power interpretation are reviewed.
- Covered-call coverage and cash-secured-put collateral checks must continue to
  emit feasibility-not-evaluated caveats for real-source accounts.
- Broker snapshot freshness and market quote freshness must remain separate.

## Regression Coverage Added

- Strengthened DB-backed golden-path tests now assert `private_real_source`
  Account Details candidates expose only safe selector fields.
- Saved artifact scope assertions now allow reviewed opaque account references in
  saved scope metadata while requiring saved caveat codes to be report-safe.
- Saved evidence packages and persisted Agent Team summaries are asserted not to
  receive account references, raw broker/provider identifiers, raw display hints,
  or buying-power wording.
- Stock/ETF and cash-secured-put golden-path branches share the same assertions.

## P32A-T8 Acceptance And Remaining Blocker Map

### Accepted As Ready

- Backend account nickname and review-account candidate contracts are landed at
  `9c80de2`.
- Frontend searchable review-account selector, Account Details nickname editor,
  and Account Details redesign/polish are landed at `d982dcb`.
- The selector submits only the opaque `account_reference` or explicit
  `unselected` mode; nickname edits send only `{ nickname }`/null to the reviewed
  PATCH route.
- Account Details / nickname-management is closed for implementation purposes.
  The connected browser smoke remains token-gated and does not block the slice
  because static checks plus Codex B/Claude B reviews passed.

### Still Synthetic Or Not Yet Demo-Proven With Real Source

- Browser-level Account Details and review-account selector smoke has not run
  against a token-authorized local stack because the local access token is
  secret-boundary protected.
- The founder demo still relies on synthetic seed data for reproducible
  end-to-end presentation.
- Real-source selected-account golden-path behavior is covered by backend
  contracts/tests, but not yet founder-demo accepted through a browser run.
- Account-level cash, buying-power, collateral, current-position truth, options
  coverage, quantities, lots, and provider raw rows remain display-only / caveated
  and must not enter Agent Team prompts as feasibility facts.

### Blockers Before Replacing Synthetic Demo Context

1. **Token-authorized browser verification** - needs founder-authorized local
   token handling or founder-run smoke; no agent should read or create `.env`.
2. **Disposable DB migration verification** - run Alembic `upgrade head` on a
   disposable/local-safe DB to prove migration `0021` cleanly applies.
3. **Real-source feasibility boundary** - keep selected-account real data
   caveated until cash/collateral/current-position semantics are separately
   reviewed.
4. **Agent-safe evidence boundary** - Agent Team may receive only lossy saved
   evidence, freshness/caveat summaries, and approved deterministic outputs; raw
   account rows and display labels remain report/UI-only unless separately
   approved.

### Next Task Sequence

- `P32A-T9` - Codex C runs disposable DB migration verification and DB-enabled
  account nickname / review-account candidate tests. No real data.
- `P32A-T10` - Claude A runs a token-authorized or founder-run browser smoke for
  Account Details + Trade Review selector using private-safe/synthetic or
  founder-approved local data boundaries. Claude B reviews only if visual issues
  appear.
- `P32A-T11` - Codex B/C define the deterministic feasibility evidence boundary
  for real-source account data: what remains UI/report-only, what can become
  deterministic evidence, and what is prohibited from Agent Team inputs.

Until T9/T10/T11 close, P32A may use the landed selector/nickname contracts but
should not claim that synthetic demo context has been fully replaced by real
connected-account context.
