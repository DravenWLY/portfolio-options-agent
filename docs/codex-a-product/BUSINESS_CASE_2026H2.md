# Portfolio Copilot Business Case - 2026 H2

Task: P36-BIZ - Business case, positioning refresh, and decisiveness model
Status: conditional go for customer validation; not approved as a commercial launch
Owner: Codex A - Product / Founder Strategy / PM
Date: 2026-07-11

## Executive Decision

Portfolio Copilot can become a business, but the current evidence supports only
a focused validation attempt, not a broad commercial claim.

The business is not "five AI agents write an investment report." Reports and
ratings are abundant. The paid job is a fast, connected pre-trade check that
tests a proposed manual trade against the user's selected account scope,
portfolio impact, options obligations, data freshness, and the user's own risk
rules. The Agent Team supplies evidence depth and explanation beneath that
check; it does not own the check result.

Approved product frame:

> Portfolio Copilot is a Pre-Trade Check for self-directed investors. It checks
> a proposed trade against your portfolio, your rules, and the available
> evidence before you place it manually in your broker.

The existing question, "What would I be ignoring if I acted manually now?",
remains useful as an internal analysis objective. It should no longer be the
main user-facing headline.

The commercial decision is therefore:

- Go: finish one bounded five-role Phase 36 working version and run customer
  validation this quarter.
- Do not go yet: production launch, broad source expansion, more agent roles,
  billing, or claims of product-market fit.
- Reassess by 2026-09-30 using the explicit demand, behavior, and willingness
  to pay gates in this memo.

## 1. Demand Thesis

### Primary ICP

The first customer hypothesis is narrower than "busy self-directed investor":

- A U.S. self-directed investor who chooses and places trades manually.
- Uses one to three taxable or retirement brokerage accounts.
- Reviews at least two candidate trades per month.
- Uses stocks and ETFs and writes covered calls or cash-secured puts at least
  occasionally.
- Already has an idea source, broker, or research workflow; does not need the
  product to generate picks.
- Has enough portfolio complexity that concentration, ETF overlap, available
  cash, collateral, account scope, assignment, or call-away exposure requires
  manual reconciliation.
- Values avoiding a preventable portfolio mistake more than receiving another
  opinion about whether a ticker is attractive.

Recruiting hypothesis: prioritize investors with roughly $50,000-$500,000 of
self-directed investable assets. This range is not a product eligibility rule.
It is a research filter for finding people whose potential error cost can
plausibly exceed an annual software subscription.

### Beachhead Decision

Keep the covered-call / cash-secured-put user as the beachhead. Keep stock and
ETF checks as the wider expansion path.

The options-income wedge is stronger initially because:

- The decision recurs and has visible mechanics: coverage, collateral,
  assignment, call-away, expiration, and event timing.
- A mechanically valid trade can still create an unwanted portfolio outcome.
- Errors can be concrete enough to justify a paid prevention workflow.
- U.S. listed-options activity continues to grow; Cboe reported 2025 as a sixth
  consecutive record year, with average daily volume of 61 million contracts.

The concentration-blind stock or ETF buyer is a larger audience but a weaker
initial paid wedge. The problem is less urgent, occurs less frequently for many
investors, and competes more directly with free broker allocation views and
general portfolio analytics. It remains essential as the lower-complexity entry
flow and expansion door.

### Top Three Jobs To Be Done

1. Before writing a covered call or cash-secured put, check whether the selected
   account and broader portfolio context support the intended mechanics and
   understand coverage, collateral, assignment/call-away, concentration, and
   event-timing implications.
2. Before adding to or trimming a stock or ETF, see the quantified pre/post
   change in cash state, single-name and look-through exposure, concentration,
   and the user's own portfolio rules.
3. Immediately before opening the broker order ticket, determine which facts
   are current, which checks are outside the user's rules, which checks cannot
   be verified, and which items require manual confirmation.

All three jobs occur after the user has a candidate trade and before the user
acts elsewhere. Idea discovery is not the wedge.

## 2. Competitive Reality Check

### What The Market Already Provides

| Product/category | Existing strength | Implication for Portfolio Copilot |
| --- | --- | --- |
| Fidelity and other brokers | Fidelity offers consolidated analyst sentiment, research reports, options strategy tools, probability/P&L modeling, and account-position views. | "Broker aware" and "analysis only" are not unique. The product must work across selected account scope and combine mechanics, portfolio deltas, rules, and evidence in one check. |
| TradingView | Deep charts, alerts, screeners, news, portfolio analytics, and broker integrations. | Do not compete on charts, alerts, watchlists, or market monitoring. Consume reviewed context only when it changes a candidate-trade check. |
| Stock Rover | Multi-broker portfolio tracking, hundreds of metrics, ratings, warnings, screening, and research. | Generic portfolio analytics is already a paid category. Our differentiation must be the short candidate-trade workflow, not a smaller research terminal. |
| Seeking Alpha | Research, transcripts, portfolio sync/health, and prominent Quant/author/sell-side ratings. | Another narrative or rating has low scarcity. Portfolio-specific impact and user-rule enforcement must lead. |
| AI stock-picking apps | Products such as Danelfin reduce a stock to an AI score and buy/hold/sell-style rating. | They sell prediction and conviction. We should not imitate them; we must prove that error prevention has independent willingness to pay. |
| TradingAgents-style systems | Broad role research, debate, ratings, sizing, targets, and a directional decision. | Adopt research depth and structured synthesis, but reject the rating as both a safety boundary and a weak point of differentiation from abundant signal products. |

### Direct Answer: Why Pay Without A Rating?

The statement "ratings describe the stock; we describe your portfolio and your
rules" is directionally right but incomplete.

It survives the competitive test only in this stronger form:

> A rating says what someone thinks about a security. Portfolio Copilot checks
> whether a specific candidate trade fits the user's selected accounts and
> explicit rules, quantifies what changes, exposes options obligations and data
> gaps, and preserves the evidence used for the check.

Even that is not yet a proven business. Fidelity can model options against an
account, while Stock Rover, TradingView, and Seeking Alpha increasingly provide
portfolio-aware analytics. Customers will pay only if Portfolio Copilot is:

- Faster than manually reconciling those tools.
- More specific to the candidate trade than a portfolio dashboard.
- Trustworthy about account scope, freshness, and unavailable data.
- Decisive at the check level without pretending to predict returns.
- Useful often enough to become a pre-order habit.

A customer who primarily wants a stock pick, price target, or conviction score
is not the customer. If most target users require a rating before they perceive
value, the B2C thesis should stop rather than weakening the no-advice boundary.

### Defensibility Ruling

The five-agent team is not the moat. The potential moat is the compound system:

- Connected, selected-scope portfolio context.
- Correct deterministic pre/post calculations.
- User-defined policy enforcement.
- Options mechanics and account-feasibility checks.
- Provenance, freshness, and frozen historical evidence.
- Role-separated explanation over those owned facts.

Each part can be copied. Reliability and workflow integration across all six is
the defensible product, if users demonstrate a recurring habit.

## 3. Decisiveness Model

### Product Rule

Portfolio Copilot may be decisive about facts, rule outcomes, data sufficiency,
and scenarios. It must not issue an overall trade rating or decide whether the
user should place the trade.

Use check-level states:

- Within rule
- Outside rule
- Unable to verify
- Not applicable

Do not use an overall "trade passed," "approved," "safe," "ready," "buy," or
"sell" state. The top summary may say, for example, "2 items need attention and
1 check cannot be verified." That is decisive without converting the product
into individualized investment advice.

### Ranked Decision Outputs

| Rank | Output | MVP ruling | Deterministic-engine requirement |
| --- | --- | --- | --- |
| 1 | Objective feasibility and mechanics checks | P0 | Trusted selected-scope holdings/cash/collateral inputs; covered-share, assignment, call-away, account-permission, expiry, and required-input checks; fail closed when semantics are incomplete. |
| 2 | Quantified pre/post impact deltas | P0 | Backend-owned cash/collateral, position, concentration, ETF look-through where licensed, assignment/call-away, and exposure calculations with provenance and as-of labels. |
| 3 | User-defined policy enforcement | P0, narrow | Persisted backend-only policy values and deterministic evaluators. Start with at most three policies: maximum post-trade single-name exposure, minimum remaining cash/collateral buffer, and maximum hypothetical assignment exposure. No LLM access to raw thresholds. |
| 4 | Scenario math | P0 for simple options; P1 expansion | User-selected or contract-defined scenarios, payoff/obligation math, and expiration/assignment outcomes. No price prediction or probability claim unless separately sourced and approved. |
| 5 | Timing and evidence flags | P0 context | Broker and market freshness, earnings/filing/macro-event timing where approved, source limitations, and required confirmations. These do not alter deterministic risk rules unless a separate policy explicitly says so. |

### MVP Check Set

The first public-alpha check set should be limited to:

- Scope and provenance: which selected account or combined context was checked.
- Data sufficiency: broker freshness, market freshness, and missing required
  fields shown separately.
- Cash/collateral: projected state only where the backend can verify semantics;
  otherwise "Unable to verify."
- Concentration: pre/post single-name exposure and approved ETF look-through.
- Options mechanics: covered-share availability, collateral requirement,
  assignment share change, call-away share change, expiration, and known event
  timing.
- Three user-defined policies at most.
- A short manual-confirmation list generated from deterministic caveat codes.

The Agent Team may explain why an item matters, compare available evidence, and
surface tensions among company, market, and portfolio context. It may not
change a deterministic check state or create an overall trade verdict.

## 4. Product Voice And Information Hierarchy

### Surface Frame

Use "Pre-Trade Check" as the primary feature name.

Primary promise:

> Check the trade against your portfolio before you place it.

Supporting copy:

> See what changes, what falls outside your rules, and what still needs to be
> verified. You decide and place the trade in your broker.

Keep "specialist review desk" as a positioning description, not the main call
to action. Keep the internal "what would I be ignoring" question in prompts,
evaluation criteria, and team synthesis instructions only.

### Summary-First Report Hierarchy

1. Pre-Trade Check summary
   - Items needing attention.
   - Checks unable to verify.
   - Checks within the user's rules.
   - Scope and freshness timestamp.
2. What changes
   - The largest backend-computed portfolio, cash/collateral, concentration, and
     options-obligation deltas.
3. Your rules
   - Each rule, its user-owned threshold label, observed result, and state.
4. Scenarios and mechanics
   - Assignment, call-away, expiration, and user-selected scenario outcomes.
5. Verify before acting
   - Missing, stale, ambiguous, or broker-confirmation items.
6. Specialist analysis
   - Fundamentals, news/macro, technical context, Risk Manager, and Portfolio
     Manager synthesis, each with evidence and availability labels.
7. Evidence and provenance
   - Deterministic calculations, source/as-of information, limitations, and the
     frozen saved snapshot.

This ordering gives the user a verdict-like orientation without a trade
verdict. Agent depth is valuable, but it is below the owned facts.

## 5. Validation Plan - July Through September 2026

### Research Objective

Test whether the target user has a frequent, costly pre-trade reconciliation
problem and values a check without needing a buy/sell rating.

### Participants

Complete 12-15 one-on-one sessions by 2026-08-15:

- At least 8 participants who have written a covered call or cash-secured put
  in the last six months.
- At least 3 active stock/ETF investors who trade at least twice per month but
  do not use options regularly.
- At least 2 users of a paid research or portfolio product.

Do not recruit only friends who already agree with the concept. Include users
who rely heavily on their broker and users who prefer ratings/signals.

### Synthetic Stimuli

Use three synthetic Portfolio Copilot artifacts only:

1. A stock/ETF addition with a hidden concentration or look-through overlap.
2. A covered-call candidate with coverage, call-away, and event-timing context.
3. A cash-secured-put candidate with collateral, assignment, and stale/missing
   data states.

Use synthetic tickers such as `XYZ` and `QQQ`, synthetic account nicknames, and
clearly labeled illustrative values. Never use founder reports, founder account
values, screenshots of real accounts, or real identifiers.

### Interview Sequence

1. Ask the participant to reconstruct their most recent relevant trade: idea,
   tools opened, checks performed, time spent, and anything discovered late.
2. Ask them to demonstrate or describe their current pre-order workflow before
   showing Portfolio Copilot.
3. Give one synthetic scenario and ask them to make sense of it with their
   current workflow.
4. Show the Pre-Trade Check artifact without a sales explanation. Ask them to
   think aloud and state what they would do next.
5. Compare the artifact with their current broker/research process.
6. Test willingness to use, connect data, and pay.

### Falsification Questions

- How often in the last three months did you evaluate a trade where portfolio
  context or options mechanics required more than one tool?
- Which part of your current workflow is slow, uncertain, or error prone?
- What does your broker already show well enough that this duplicates?
- Which item in this check would have changed a verification step, and which is
  merely interesting?
- What is missing that would prevent you from relying on the check?
- Would you use this if it never gave a buy/sell/hold rating? Why or why not?
- Would you connect read-only brokerage access? If not, would you maintain a
  manual/CSV snapshot?
- For which trade types would you skip the product entirely?
- If this disappeared tomorrow, what would you return to?
- What price would make the product obviously not worth it?

### Willingness-To-Pay Probe

Test one concrete B2C hypothesis: $19/month or $180/year for connected account
scope, simple stock/ETF and options checks, saved history, and specialist
analysis. Do not ask only "would you pay?"

Ask participants to choose among:

- Keep the current free broker/research workflow.
- Join a free four-week alpha and run at least four checks.
- Reserve a paid founding plan in the $15-$25/month range, using a refundable
  deposit only after the project has an appropriate payment and consent process.

Record the choice and reason. A verbal compliment is not purchase evidence.

### Monetization Decision

B2C subscription is the first validation model because it creates the shortest
learning loop with the current product and user. The initial hypothesis is a
single paid individual plan, not complex tiers.

B2B2C through a broker or advisory platform is a later option. The no-advice
posture may reduce product and
compliance risk for a partner, but it does not eliminate regulatory, privacy,
security, or supervisory obligations. Broker/RIA distribution has longer sales
cycles and should not be used to avoid testing direct user value.

### Public-Alpha Evidence Gate

Proceed from research to a small public alpha only if, by 2026-09-30:

- At least 8 of 12 qualified participants report the target problem at least
  twice per month.
- At least 7 of 12 identify one check they do not receive clearly in their
  current workflow.
- No more than 4 of 12 say a directional rating is required for the product to
  be useful.
- At least 5 commit to a four-week pilot with repeated use.
- At least 3 accept the $15-$25/month value range or take an equivalent concrete
  purchase-intent action.
- The synthetic workflow can be completed in under three minutes without PM
  explanation.

Before any participant supplies private brokerage data, run a separate
security/privacy/compliance readiness gate. Synthetic interviews do not
authorize real-data collection.

## 6. Founder Go / No-Go Frame

### Current Verdict

Conditional go for a commercial validation attempt. No-go for commercial
launch or substantial scope expansion today.

### Go Evidence

Move from internal prototype to public-alpha attempt only when all are true:

- The public-alpha evidence gate above passes.
- At least one options scenario and one stock/ETF scenario work end to end with
  trustworthy deterministic checks and honest unavailable states.
- The product demonstrates a repeatable advantage over the participant's broker
  or spreadsheet, not only a more attractive report.
- Users understand the check without interpreting it as advice or trade
  approval.
- Unit-cost estimates support the tested price after broker, data, and LLM
  costs.
- Security/privacy review and qualified legal/compliance review approve the
  external-alpha posture.

### Stop Evidence

Stop the B2C commercial attempt, or return it to a personal/internal tool, if by
2026-09-30 any two of these are true:

- Fewer than 6 of 12 qualified participants have the problem at least twice per
  month.
- Most participants say their existing broker or spreadsheet solves it well
  enough.
- A majority require a buy/sell rating or trade recommendation to perceive
  value.
- Fewer than 3 participants commit to a repeated-use pilot.
- No participant takes a concrete purchase-intent action in the tested range.
- Read-only broker connection or manual snapshot maintenance creates more
  friction than the problem is worth.

Do not answer weak demand by adding ratings, stock picks, execution, a screener,
or more agents. A later B2B2C discovery effort may be evaluated separately only
if a real partner expresses the need.

## 7. Phase 36 Scope Check

### Decision

Continue the existing Phase 36 five-live-role build. It produces the complete
artifact needed for validation and gives useful evidence depth below the
Pre-Trade Check. Do not treat completion of Phase 36 as proof of a business.

No reversal is required for P36-T3 through P36-T6. Before implementation, Codex
B should make three acceptance relationships explicit:

1. Deterministic check states and impact deltas remain available when any or all
   live roles fail.
2. Agent outputs may explain or prioritize evidence but cannot override a check
   state, create a trade rating, or become the source of a financial metric.
3. The future top summary can be rendered entirely from backend-owned
   deterministic outputs, with Agent Team depth below it.

The Pre-Trade Check decision layer is mostly deterministic-engine and frontend
work. It should be specified as a separate architecture/product slice, not
silently added to P36-T4 or P36-T5. The slice should cover:

- Check-state taxonomy.
- Three-policy MVP contract.
- Pre/post impact summary contract.
- Manual-confirmation derivation.
- Summary-first frontend read contract.

Do not add more roles, public sources, prediction features, or orchestration
complexity until the customer-validation gate is reached. Finish one stable five-
role version, then freeze agent breadth while validating demand.

## Decisions Made

- Business verdict: conditional validation go; commercial launch not approved.
- Beachhead: covered-call/CSP users; stock/ETF concentration is the expansion
  path.
- Product frame: `Pre-Trade Check` replaces the locked question on user-facing
  surfaces.
- Decisiveness: check-level facts and user-rule outcomes, never an overall trade
  rating.
- Product hierarchy: deterministic summary first; Agent Team analysis below.
- Monetization hypothesis: B2C first at $19/month or $180/year; B2B2C later.
- Phase 36: continue the bounded working version; specify the deterministic
  decision layer separately.

## Open Questions And Recommendations

- Founder approval of `Pre-Trade Check` as the external feature name.
  Recommendation: approve and update PRD/positioning/roadmap after validation
  materials are ready.
- Policy defaults. Recommendation: begin with user-entered policies only. Any
  product-suggested thresholds require separate product, architecture, and
  compliance review.
- External-alpha portfolio input. Recommendation: read-only broker sync is the
  target paid experience; manual/CSV is acceptable for interviews and early
  workflow testing, not the long-term paid habit.
- Public-alpha legal posture. Recommendation: obtain qualified counsel before
  external users receive individualized portfolio checks, even without ratings
  or execution.
- B2B2C segment. Recommendation: do not prioritize until direct-user validation
  produces either positive demand or a concrete partner lead.

## Blockers

- Zero external customer validation.
- No evidence yet that users will pay for error prevention without a rating.
- Production data rights, security/privacy readiness, and compliance posture
  remain unresolved for public alpha.
- User-defined policy storage and check semantics do not yet have an approved
  cross-layer contract.

## Next Step

1. Founder accepts or revises this business-case decision.
2. Codex B adds the three Phase 36 acceptance relationships without broadening
   the current implementation slices.
3. Codex A prepares three synthetic stimulus artifacts and begins 12-15
   customer conversations in July 2026.
4. Codex B drafts a separate Pre-Trade Check decision-layer contract; Codex C
   does not implement that slice until founder approval and initial interviews
   confirm the output hierarchy.

## Market Evidence Reviewed

Official product and industry sources reviewed on 2026-07-11:

- [Fidelity Equity Summary Score](https://www.fidelity.com/research/equity/popups/stock-research-starmine-learn-more.shtml)
- [Fidelity options tools](https://www.fidelity.com/options-trading/tools)
- [Fidelity options analytics help](https://www.fidelity.com/products/atbt/help/ActiveTraderTools_Option_Analytics_Help.html)
- [Stock Rover plans and portfolio capabilities](https://www.stockrover.com/plans/)
- [TradingView features](https://www.tradingview.com/features/)
- [TradingView Portfolios announcement](https://www.tradingview.com/blog/en/introducing-portfolios-on-tradingview-52661/)
- [Seeking Alpha Premium features](https://help.seekingalpha.com/premium/seeking-alpha-premium-feature-list)
- [Seeking Alpha Quant Ratings methodology](https://help.seekingalpha.com/premium/quant-ratings-and-factor-grades-faq)
- [Danelfin AI Score](https://support.danelfin.com/hc/en-us/articles/4404382038545-What-is-the-AI-Score-How-it-rates-stocks-and-ETFs)
- [Cboe State of the Options Industry 2025](https://www.cboe.com/insights/posts/the-state-of-the-options-industry-2025)
- [FINRA investor trends discussion](https://www.finra.org/media-center/finra-unscripted/investors-in-the-united-states-key-trends-and-insights-from-the-national-financial-capability-study)

Research limitation: public product pages establish advertised capabilities,
not customer satisfaction, workflow quality, or the absence of an unadvertised
feature. No external Portfolio Copilot user research has been completed. The
validation plan, not competitor feature comparison, is the deciding evidence.
