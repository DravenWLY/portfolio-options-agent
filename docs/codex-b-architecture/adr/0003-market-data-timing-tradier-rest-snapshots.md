# ADR 0003: Market-Data Timing and Provider-Neutral REST Snapshots

Status: amended
Date: 2026-05-20
Amended: 2026-05-25; 2026-05-26
Owner: Codex B - Architecture / Tech Lead

## Amendment Note

Codex A approved Phase 22A on 2026-05-25 after review of market-data
coverage, redistribution, and scale constraints. This ADR is amended in place
because its REST-snapshot-versus-streaming decision remains valid, while its
earlier Tradier-first provider posture no longer reflects product direction.

Tradier is no longer the assumed scalable production provider. It may remain a
prototyping or reference candidate only. No production market-data provider is
currently selected.

Codex A further decided on 2026-05-26 to park the commercial provider/RFI
track until commercial-scale or external-display planning makes it timely.
Codex A approved a bounded Alpaca Basic local/internal evaluation-adapter
implementation task only as an injected/mock-client mapping exercise:
`indicative`/`limited_source`, analysis-only, backend-only, and with no
authorized external request or runtime provider selection.

## Context

Portfolio Copilot needs market quotes, option quotes, chains, IV, Greeks, quote timestamps, data mode, and provider status to review proposed trades. Broker portfolio freshness and market quote freshness are separate.

Phase 12 intentionally created provider-agnostic market-data contracts and a manual/mock provider only. Real provider calls were deferred so the product could stabilize trade-review, actionability, report, and agent boundaries before taking on provider cost, licensing, OPRA, and quote-freshness complexity.

## Decision

Do not implement a real market-data provider during Phase 16A or Phase 16B.

Real market-data provider integration is **not required for local MVP demo**. Manual/mock market data remains acceptable for local MVP as long as outputs are labeled analysis-only when appropriate.

Real backend REST snapshot market data is required before:

- external paid beta;
- any polished UI/report that implies quote-current options review;
- any public-facing claim that options quotes, Greeks, or IV are provider-current.

Phase 22A reopens provider selection. The first authorized work is an offline,
provider-neutral, synthetic/replay-based backend evaluation foundation:

- stock/ETF underlying quote snapshot contracts;
- listed-option quote and option-chain snapshot contracts;
- IV and Greeks provenance or unavailable-state contracts;
- explicit market-data mode and freshness semantics;
- deterministic synthetic/replay scenario tests only.

Optional external evaluations, including Alpaca Basic limited-source/indicative
smoke testing or an Intrinio delayed-options trial, are not authorized by the
initial Phase 22A slice and require separate approval.

`P22A-T4` authorizes only an Alpaca Basic-shaped mapping adapter exercised by
injected fake clients and synthetic responses. It does not authorize Alpaca
smoke testing, credential/config loading, network access, frontend display, or
production selection.

Before purchase, paid beta, or any public live/current quote claim, select a
provider only after written RFI/licensing review of U.S. equity coverage,
OPRA-derived listed-options coverage, external display rights, deterministic
backend calculation rights, retention/replay rights, derived-summary rights,
possible later sanitized agent-evidence rights, entitlement fees, reporting,
rate limits, outage handling, and pricing at scale.

The initial commercial vendor comparison should include Intrinio, Databento,
and dxFeed, with Massive included only if it materially improves comparison.
This is an evaluation list, not a provider selection.

REST snapshot semantics remain the first implementation posture. WebSocket or
streaming real-time market data remains separately deferred and requires a
reviewed user need, licensing approval, and architecture decision.

## Non-Goals

- No option-chain browser for MVP.
- No market-data terminal.
- No options screener.
- No streaming entire option markets.
- No real provider calls or credentials in the Phase 22A initial slice.
- No public live-price UI claims in the Phase 22A initial slice.
- No market-data ingestion by LLM agents in Phase 22A.
- No frontend calls directly to market-data providers.
- No storing provider secrets in frontend code, reports, logs, tests, or public docs.

## Implementation Guidance

For the Phase 22A synthetic/replay slice:

- Reuse or refine provider-neutral contracts only where tests demonstrate a
  contract gap.
- Treat `synthetic`, `indicative`, `delayed`, `live`, and `unavailable` as
  required product concepts. `live` may exist in schemas/tests as reserved
  vocabulary but may not be emitted as a production/public claim before
  provider and licensing approval.
- Preserve underlying quote freshness, option quote/chain freshness, and
  broker snapshot freshness as distinct concepts.
- Record IV and Greeks provenance, including unavailable states.
- Keep tests offline, deterministic, and synthetic/replay-only.

When a later real provider slice is separately approved:

- Keep provider calls backend-only.
- Add a provider adapter behind existing `MarketDataProvider` and `OptionDataProvider` contracts.
- Preserve `freshness_scope="market_quote"` separately from broker snapshot freshness.
- Persist or freeze enough quote/chain payload data for report reproducibility.
- Mark `data_mode` and quote freshness explicitly. Never silently downgrade live to delayed.
- Mock all provider tests by default. Any real-provider tests must be marked external and skipped by default.
- Return sanitized API shapes without raw provider payloads, provider account ids, secrets, or account-specific thresholds.

## Consequences

Positive:

- Keeps the local MVP from turning into a market-data integration project.
- Creates a provider-neutral, licensing-aware path to quote-current options review.
- Avoids premature WebSocket, OPRA, or terminal-style UI complexity.
- Aligns with the product center: pre-trade portfolio review, not market-data viewing.

Tradeoffs:

- Local MVP demos cannot honestly claim real quote-current options review.
- Paid beta readiness will need a provider/licensing check before launch.
- Vendor RFI and commercial-rights review are required before final selection.
- Free or trial evaluation sources cannot be treated as production quote truth.

## Alternatives Considered

1. Implement real-time streaming now. Rejected because the MVP does not need a terminal and streaming creates cost, licensing, UI, and reliability complexity.
2. Use broker provider data as market data. Rejected because broker account sync and market quotes are separate subsystems.
3. Use free/unofficial data as product-grade options data. Rejected for reliability/licensing/freshness reasons.
4. Retain Tradier as the assumed production provider. Rejected because
   realtime access/account assumptions constrain scalable commercial design
   before licensing and coverage evaluation is complete.

## Review Guidance

Architecture reviews should block changes that:

- call manual/mock data live or quote-current;
- add provider calls from frontend code;
- collapse broker freshness and market quote freshness;
- add option-chain browser, screener, market terminal, or streaming UI before PM approval;
- expose provider secrets, raw payloads, private account data, or account-specific thresholds.
- implement external provider evaluation, LLM/agent ingestion, or public live
  display as part of the initial synthetic/replay-only Phase 22A slice.
