# Metrics

Status: PM metrics plan
Owner: Codex A - Product / Founder Strategy / PM
Last updated: 2026-05-20

## Metrics Philosophy

Portfolio Copilot should measure whether users can safely and clearly understand a proposed manual trade's portfolio impact. Metrics should validate trust, review completion, and usefulness without logging sensitive brokerage data.

Do not log raw holdings, account values, cash balances, broker account ids, provider account ids, trade journal text, raw provider payloads, secrets, or account-specific thresholds in product analytics.

## Local MVP Success Metrics

| Metric | Target | Why it matters |
| --- | --- | --- |
| Review completion | User can complete portfolio snapshot to deterministic report in under 2 minutes with synthetic/manual data. | Validates the core workflow. |
| Freshness visibility | 100% of generated reports show broker snapshot freshness and market quote freshness separately. | Prevents misleading confidence. |
| Stale-data guardrail | 0 stale, unknown, manual-only, EOD-only, or provider-error reviews labeled immediately actionable. | Core safety requirement. |
| Deterministic coverage | P0 flows have synthetic tests for cash impact, collateral, assignment/call-away, concentration, and rule violations. | Proves calculations are testable. |
| AI boundary | 0 user-facing AI outputs generated from raw brokerage/private fields by default. | Protects privacy and prevents invented metrics. |
| Founder usefulness | Founder can answer "what changes in my portfolio if I do this?" without a spreadsheet for each P0 flow. | Validates practical product value. |

## Paid Beta Success Metrics

| Metric | Early target | Why it matters |
| --- | --- | --- |
| Weekly active reviewers | Beta users run multiple reviews per week. | Shows the app fits a recurring pre-trade habit. |
| Repeat review rate | 50%+ of beta users run another review within 14 days. | Stronger signal than one-time curiosity. |
| Usefulness rating | 70%+ of completed reviews marked useful or clear. | Measures perceived value. |
| Data-confirmation behavior | Users refresh or manually confirm when stale-data warnings appear. | Shows guardrails influence behavior. |
| Report trust rating | Users report that freshness and assumptions are clear. | Measures trust, not just feature usage. |
| Conversion signal | Users say they would pay for portfolio-aware pre-trade review. | Validates paid wedge before pricing work. |

## Guardrail Metrics

These should be treated as product safety metrics, not vanity metrics:

- Count of analysis-only reports generated.
- Count of reviews blocked by stale broker snapshot.
- Count of reviews blocked by stale market quote.
- Count of manual-confirmation-required reports.
- Count of missing coverage/collateral model caveats shown.
- Count of AI explanations generated from agent-safe projection.
- Count of forbidden-field test failures.
- Count of reports containing prohibited language in automated copy checks, if implemented.

Target guardrail posture:

- More warnings early is acceptable if they are accurate and understandable.
- Any action-ready label on stale/unknown/error data is a release blocker.
- Any raw broker/private field leakage to AI or analytics is a release blocker.

## Product Events To Track Later

Use event names that describe workflow steps without embedding sensitive values:

- `portfolio_snapshot_loaded`
- `portfolio_snapshot_freshness_classified`
- `trade_intent_started`
- `trade_intent_validated`
- `trade_review_generated`
- `trade_review_analysis_only`
- `trade_review_blocked`
- `risk_rule_violation_present`
- `report_saved`
- `ai_explanation_generated`
- `manual_confirmation_selected`
- `broker_refresh_prompt_shown`

Allowed event properties:

- Flow type, such as `equity_review`, `covered_call`, or `cash_secured_put`.
- Freshness category, such as `fresh`, `stale`, `unknown`, `manual`, `eod`, or `provider_error`.
- Data source category, such as `snaptrade`, `manual`, `csv`, or `synthetic`.
- Boolean flags such as `has_risk_violation` or `ai_explanation_used`.
- Coarse severity category, such as `info`, `warning`, `violation`, or `blocker`.

Disallowed event properties:

- Tickers from real portfolios by default.
- Quantities, cash, balances, account values, strikes, premiums, cost basis, broker account ids, provider ids, report text, prompt text, raw payloads, secrets, or real account-specific thresholds.

## System Metrics For Beta Readiness

Track once the app moves beyond local-only development:

- API error rate.
- Median, P90, and P99 review generation latency.
- Broker sync failure rate.
- Broker sync freshness distribution.
- Market quote provider timeout/error rate.
- Background job failure rate if agent or sync jobs are asynchronous.
- Database migration success/failure.
- Frontend build and typecheck status.
- Test suite pass/fail rate.

## Review Funnel

The core funnel is:

1. Portfolio snapshot loaded.
2. Trade intent started.
3. Trade intent validated.
4. Deterministic review generated.
5. Freshness/actionability classified.
6. Report saved or viewed.
7. User marks useful, unclear, or not useful.
8. User refreshes/confirms data when prompted.

The main PM question is not "how many dashboards were opened?" It is "did the user get a trustworthy answer before deciding what to do manually in the broker?"

## Qualitative Questions

Ask beta users:

- What did this review tell you that your broker did not?
- Which assumption or freshness warning changed how you interpreted the trade?
- Was any metric confusing or too advice-like?
- Did the app make you more likely to check cash, collateral, or assignment exposure before trading?
- What would make this worth paying for?

## Release Blockers

Do not launch a paid beta if:

- Stale broker snapshots can be presented as ready for action.
- Market quote freshness can be confused with broker position freshness.
- AI can receive raw brokerage/private fields by default.
- Reports use "you should buy/sell", "safe to trade", "guaranteed return", or execution-like language.
- Covered call or cash-secured put labels imply fully modelled coverage/collateral when the model is incomplete.
