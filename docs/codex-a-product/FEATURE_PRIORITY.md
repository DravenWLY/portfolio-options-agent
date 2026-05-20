# Feature Priority

Status: PM prioritization guide
Owner: Codex A - Product / Founder Strategy / PM
Last updated: 2026-05-20

## Prioritization Principle

Prioritize features that make one proposed manual trade easier to review against the user's actual portfolio snapshot. Deprioritize features that mainly make the app look like a broker dashboard, option screener, market-data viewer, AI stock picker, or automated trading system.

## Priority Rubric

A feature moves up when it:

- Improves portfolio-aware pre-trade review.
- Reduces misleading output from stale or incomplete data.
- Makes deterministic calculations more correct or auditable.
- Clarifies cash, collateral, coverage, assignment, call-away, concentration, or risk-rule impact.
- Preserves privacy and keeps sensitive brokerage data out of prompts by default.
- Can ship as a narrow vertical slice with synthetic tests.

A feature moves down when it:

- Requires real broker data inspection by agents.
- Requires production compliance or legal review before basic validation.
- Adds provider breadth without improving the core review job.
- Adds research or screening before the review workflow is clear.
- Encourages trade execution, recommendations, or guaranteed-return framing.
- Expands options-income or wheel workflows into the product identity.

## P0 - Must Have For MVP

| Feature | Why it matters | Notes |
| --- | --- | --- |
| Portfolio Snapshot Actionability Policy | Prevents polished reports from sounding current when holdings, cash, collateral, or quotes are stale. | Next implementation gate before deeper Phase 16 agents. |
| Broker freshness vs market quote freshness separation | Avoids the core trust failure of fresh prices with stale positions. | Must be visible in reports and UI. |
| Stock/ETF trade review | Gives the product a broad core beyond options income. | One generic equity flow is enough for MVP. |
| Covered call review | High-value options wedge with coverage and call-away risk. | Must caveat incomplete coverage netting if not fully modelled. |
| Cash-secured put review | High-value options wedge with collateral and assignment risk. | Must caveat incomplete collateral netting if not fully modelled. |
| Deterministic risk-rule violations | Makes output auditable and not AI-invented. | Severity should remain structured. |
| Agent-safe projection boundary | Allows AI explanation without raw sensitive portfolio fields by default. | Required before user-facing AI explanations. |
| Analysis-only language | Keeps stale/manual/EOD outputs useful without implying execution readiness. | Product copy is part of safety. |
| Report history | Lets users compare review outputs and supports agent workflow traceability. | Keep thin for MVP. |

## P1 - Important After P0 Is Stable

| Feature | Why it matters | Deferral reason |
| --- | --- | --- |
| Frontend Trade Review Workspace | Converts backend value into a usable product flow. | Should wait for actionability and safe read contracts. |
| Typed sanitized trade-review read schema | Prevents leaking internal/private fields to frontend or agents. | Required before broad UI exposure. |
| Coverage/collateral netting improvements | Makes covered call and CSP labels more trustworthy. | Could be caveated temporarily, but should be fixed before paid beta. |
| Optional AI report explanation | Improves comprehension of deterministic results. | Must stay behind projection and actionability gates. |
| Manual confirmation workflow | Lets users proceed with analysis when data is stale/manual. | Needs careful copy and audit trail. |
| Basic provider status and missing-data states | Reduces confusion when quotes or broker sync are unavailable. | Should stay operational, not dashboard-heavy. |

## P2 - Useful Later

| Feature | Why it matters | Reason to wait |
| --- | --- | --- |
| Long call and long put product surface | Supports more options use cases. | Less central to first portfolio-aware cash/collateral wedge. |
| TradingAgents async research evidence | Adds public ticker/company context. | Should not distract from deterministic review or send account data. |
| Real market-data provider adapter | Needed for richer paid beta. | Provider choice, licensing, and quote freshness require care. |
| Broker activities/transactions layer | Enables history, assignments, expirations, and wheel lifecycle later. | Current-position review is the first job. |
| Wheel lifecycle tracking | Could help advanced options users. | Risks narrowing product into options income too early. |
| Advisor or shared-account workflows | Potential future segment. | Not the first user. |

## P3 - Explicitly Defer

- Option-chain browser.
- CSP or covered-call screener.
- Automated trade execution.
- Broker order management.
- AI-generated buy/sell recommendations.
- Portfolio optimizer.
- Production billing.
- Mobile app.
- PDF export.
- Real-time streaming market terminal.

## Competitor Findings Handling

Claude C competitor findings should be converted into product decisions using this rule:

- If a competitor feature improves portfolio-aware review clarity, consider it.
- If it pushes the app toward screening, trading automation, yield chasing, or generic research, defer it.
- If it improves trust language, data freshness disclosure, or user confidence in deterministic results, prioritize it.
- If it requires legal/compliance review before a local MVP can be validated, document it as future beta or launch work.

## Next Owner Handoffs

Codex B Architecture:

- Define actionability/readiness contracts and ADRs for freshness, agent-safe projection, and TradingAgents-as-async-evidence.

Codex C Backend:

- Implement Portfolio Snapshot Actionability Policy as the next backend gate with synthetic tests and no real broker data.

Claude A Frontend:

- Design the first trade review workspace only after backend contracts are ready. The UI must show deterministic facts, freshness state, analysis-only state, and read-only manual-decision language.
