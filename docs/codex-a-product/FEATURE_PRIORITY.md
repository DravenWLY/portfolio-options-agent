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
| Portfolio Snapshot Actionability Policy | Prevents polished reports from sounding current when holdings, cash, collateral, or quotes are stale. | First Phase 16A gate before deterministic agent components. |
| Broker freshness vs market quote freshness separation | Avoids the core trust failure of fresh prices with stale positions. | Must be visible in reports and UI. |
| Stock/ETF trade review | Gives the product a broad core beyond options income. | One generic equity flow is enough for MVP. |
| Covered call review | High-value options wedge with coverage and call-away risk. | Must caveat incomplete coverage netting if not fully modelled. |
| Cash-secured put review | High-value options wedge with collateral and assignment risk. | Must caveat incomplete collateral netting if not fully modelled. |
| Deterministic risk-rule violations | Makes output auditable and not AI-invented. | Severity should remain structured. |
| Agent-safe projection boundary | Allows AI explanation without raw sensitive portfolio fields by default. | Required before user-facing AI explanations. |
| Analysis-only language | Keeps stale/manual/EOD outputs useful without implying execution readiness. | Product copy is part of safety. |
| Report history | Lets users compare review outputs and supports agent workflow traceability. | Keep thin for MVP. |
| Phase 16A deterministic agent components | Provides safe agent-shaped report components without autonomous LLM behavior. | Complete. |
| Phase 16B agent-team orchestration contract | Makes the TradingAgents-inspired team shape explicit before polished UI/research work. | Complete. |
| Phase 18A sanitized trade-review read contract | Lets frontend consume completed Phase 16 outputs without raw brokerage/private fields or speculative fields. | Next active backend gate before Claude A UI. |
| Phase 18A first Trade Review Workspace | Converts backend value into a visible product workflow. | Next active UI slice after safe read contract. |

## P1 - Important After P0 Is Stable

| Feature | Why it matters | Deferral reason |
| --- | --- | --- |
| Frontend Trade Review Workspace expansion | Converts backend value into a broader product flow. | Phase 18A first slice comes first. |
| Typed sanitized trade-review read schema extensions | Prevents leaking internal/private fields to frontend or agents. | First Phase 18A contract is P0; extensions are P1. |
| Coverage/collateral netting improvements | Makes covered call and CSP labels more trustworthy. | Could be caveated temporarily, but should be fixed before paid beta. |
| Optional AI report explanation | Improves comprehension of deterministic results. | Must stay behind projection and actionability gates. |
| Manual confirmation workflow | Lets users proceed with analysis when data is stale/manual. | Needs careful copy and audit trail. |
| Basic provider status and missing-data states | Reduces confusion when quotes or broker sync are unavailable. | Should stay operational, not dashboard-heavy. |
| Market Data Agent / public evidence status role | Helps users understand quote/chain/Greeks availability once real snapshots exist. | Backend evidence/status role first; no market terminal. |
| News / Research Evidence Agent | Adds public ticker/company context. | P1 after deterministic workflow and evidence contracts are stable. |
| Bull Case and Bear Case Agents | Adds TradingAgents-inspired debate over public/sanitized evidence. | P1; not required for local MVP demo. |
| Tradier REST snapshot adapter | Enables quote-current options review for paid beta. | Backend-only snapshots before paid beta; not needed for local MVP demo. |

## P2 - Useful Later

| Feature | Why it matters | Reason to wait |
| --- | --- | --- |
| Long call and long put product surface | Supports more options use cases. | Less central to first portfolio-aware cash/collateral wedge. |
| TradingAgents/Public Research Evidence Adapter | Adds optional public ticker/company context. | Temporarily frozen while Phase 18A proves deterministic review UX; should not distract from deterministic review or send account data. |
| Streaming market data | Useful only if users need actively updating quote views. | Explicitly deferred to Phase 19+ or paid beta proof; avoid terminal/screener drift. |
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
- WebSocket/streaming market data before Phase 19+ or proven paid-beta need.

## Competitor Findings Handling

Claude C competitor findings should be converted into product decisions using this rule:

- If a competitor feature improves portfolio-aware review clarity, consider it.
- If it pushes the app toward screening, trading automation, yield chasing, or generic research, defer it.
- If it improves trust language, data freshness disclosure, or user confidence in deterministic results, prioritize it.
- If it requires legal/compliance review before a local MVP can be validated, document it as future beta or launch work.

## Next Owner Handoffs

Codex B Architecture:

- Keep Phase 18A focused on the sanitized trade-review workspace contract and frontend/backend boundary. Keep Phase 17 public-evidence-only and frozen unless PM reactivates it.

Codex C Backend:

- Implement the Phase 18A sanitized trade-review workspace read contract, mapper, and forbidden-field tests before Claude A starts UI work.

Claude A Frontend:

- Design the first trade review workspace only after the Phase 18A backend contract is ready. The UI must show deterministic facts, freshness state, analysis-only state, and read-only manual-decision language.
