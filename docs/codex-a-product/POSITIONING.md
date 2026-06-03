# Positioning

Status: PM positioning decision
Owner: Codex A - Product / Founder Strategy / PM
Last updated: 2026-06-02

## Core Positioning

Portfolio Copilot is a specialist review team for self-directed investors. It
helps users review proposed trades, understand portfolio risk, and manage their
own portfolio decisions with clearer evidence, freshness context, and
analysis-only explanations.

Portfolio Copilot is not a broker, investment adviser, automated trading
system, research terminal, screener, or portfolio manager. It does not manage
the portfolio for the user, recommend trades, allocate assets, place orders, or
decide what the user should buy or sell.

## Complement, Not Replace

Portfolio Copilot complements serious research and portfolio tools such as
Stock Rover, TradingView, or broker dashboards. Those products help users
research, monitor, screen, chart, or execute. Portfolio Copilot focuses on the
moment before a user manually acts elsewhere: what the proposed stock, ETF, or
options trade could do to the user's portfolio, cash/collateral posture,
concentration, assignment/exercise exposure, and data freshness.

## Approved Persona Labels

User-facing persona labels should be clean human titles with no "Agent" suffix:

| UI label | Product meaning |
| --- | --- |
| Fundamentals Analyst | Reviews approved public company/fundamental evidence. |
| News Analyst | Reviews approved public news, macro, and event context. |
| Technical Analyst | Reviews approved public market/technical context and states when data is unavailable. |
| Risk Manager | Explains portfolio risk using sanitized deterministic evidence. |
| Portfolio Manager | Synthesizes the team's analysis for the user's review. |

Backend role keys may remain unchanged unless a separate compatibility task
approves a machine-key rename.

Required Portfolio Manager guardrail copy:

> Synthesizes the team's analysis for your review - does not manage your
> portfolio or recommend trades.

Approved fallback labels if user testing or compliance review finds fiduciary
confusion:

1. Portfolio Lead
2. Portfolio Synthesis
3. Review Synthesizer

Avoid "Portfolio Strategist" because it can imply strategy recommendations.

## Product Language

Use:

- "specialist review team"
- "manual decision support"
- "scenario analysis"
- "helps you manage your own portfolio decisions"
- "review proposed trades"
- "understand portfolio risk"
- "analysis-only"
- "no order is placed"

Avoid:

- "manages your portfolio"
- "your AI portfolio manager"
- "recommends trades"
- "tells you what to do"
- "optimizes your portfolio"
- "safe to trade"
- "ready to trade"
- "guaranteed return"
- buy/sell instructions
- allocation instructions
- order or execution language

## Role Roadmap

MVP/private alpha keeps the five approved personas. Three public-evidence roles
may be thin until public evidence adapters are reviewed; Risk Manager and
Portfolio Manager carry the core portfolio-aware value.

P1 candidate:

- Options Strategist / Options Risk Specialist, likely starting as a bounded
  extension of Risk Manager. This role may explain deterministic options,
  collateral, assignment, exercise, expiry, and earnings-timing exposure for the
  user's proposed options leg. It must not suggest a different options strategy
  or recommend a trade.

Later candidates:

- Macro / Economic Specialist after approved economic-calendar/event contracts.
- Sentiment Analyst only after an approved public sentiment source exists.
- Income / Cashflow awareness only as deterministic, analysis-only context.
- Considerations For / Considerations Against and Risk Lens sections as
  non-conviction report sections, not debate personas.

Rejected as user-facing personas:

- Trader
- Bull Researcher
- Bear Researcher
- Research Manager as debate judge
- Aggressive / Neutral / Conservative debate personas
- Tax or realized-gain advice persona
- Data-quality chat persona
- Compliance chat persona

Trader-like behavior is replaced by deterministic Trade Review services. Data
quality, freshness, and compliance remain internal deterministic/evaluation
layers surfaced through labels, caveats, and safety badges.
