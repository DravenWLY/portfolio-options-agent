# Phase 36 - TradingAgents Reference Adoption Notes

Status: reference analysis (read-only study of ../TradingAgents; patterns
paraphrased, no source copied per the project boundary)
Owner: Claude G
Date: 2026-07-10
Purpose: input for Claude H's five-role design (P36) and Codex B's
activation contract / source-rights delta.

## What TradingAgents does, per role

### Fundamentals Analyst
- Four LLM-callable tools: comprehensive company fundamentals, balance
  sheet, cash flow, income statement - vendor-routed (Alpha Vantage
  primary, yfinance fallback).
- Prompt asks for a comprehensive company report ("financial documents,
  company profile, basic financials, financial history") with "specific,
  actionable insights ... to help traders make informed decisions" and a
  closing markdown summary table.
- The LLM binds tools directly (LangGraph loop) and writes a long
  free-form report stored as role state.

### News Analyst
- Four LLM-callable tools: ticker news (Alpha Vantage/yfinance), global
  macro news, FRED macro indicator series (cpi, core_pce, unemployment,
  fed_funds_rate, 10y_treasury, yield_curve), and Polymarket prediction
  markets (market-implied event probabilities).
- Prompt asks for a comprehensive "state of the world" trading/macro
  report with actionable insights and a closing table.

### Portfolio Manager
- A judge, not an author: synthesizes the risk-analyst debate plus the
  research plan and trader proposal in ONE structured-output LLM call.
- Structured output schema: a five-point rating (Buy / Overweight / Hold /
  Underweight / Sell), an executive summary (entry strategy, sizing, risk
  levels, horizon), an investment thesis grounded in the analysts'
  evidence, optional price target and time horizon. Rendered to fixed
  markdown sections for downstream parsers.

## Adoption verdicts for Portfolio Copilot

Hard constraints that bind adoption: read-only decision support, no
advice/ratings/targets, deterministic financial math, sanitized envelopes
only (LLMs never call providers or tools directly), gated short notes,
per-source rights approval, fail-closed to the deterministic floor.

### Adopt (pattern level)
- Fundamentals evidence decomposition: profile + balance sheet + cash
  flow + income statement as SEPARATE reviewed evidence facts feeding one
  role - maps to a deterministic "Company context" floor section with
  normalized statement-level facts, with the live note on top.
- News layering: company-specific events + macro grounding as distinct
  evidence lanes for one role - maps to our EDGAR filing-metadata lane
  plus a FRED macro lane (we already carry FRED calendar metadata;
  TradingAgents grounds macro in FRED data series values, which is a
  reviewable extension of our existing FRED boundary).
- PM as single structured-output synthesis call over the other roles'
  outputs: adopt the SHAPE (one gated call, typed fields, fixed rendered
  sections, graceful fallback) - not the content.

### Adapt (required transformations)
- Tool mediation: TradingAgents binds tools to the LLM; ours must keep the
  request->validate->execute->sanitized-envelope seam. The four
  fundamentals tools become four envelope fact-groups, not LLM tools.
- Report shape: their analysts write long reports; our roles stay
  two-to-four-sentence gated notes on a deterministic floor.
- PM output: their rating/summary/thesis schema becomes a typed
  no-advice synthesis: evidence-weighting narrative (what matters most in
  this saved evidence), verification priorities (ordered
  verify-before-acting items), and trust assessment (which caveats
  dominate) - every number envelope-copied, no directional language,
  rendered into the Summary/synthesis area of the composed report with
  the deterministic composer retaining document authorship and serving
  as fail-closed fallback.

### Reject (incompatible with hard rules)
- Buy/Overweight/Hold/Underweight/Sell ratings, entry strategy, position
  sizing, price targets, time horizons ("no advice" hard rule; PM
  included).
- "Actionable insights to inform traders" prompt framing anywhere.
- Direct LLM tool binding; free-running tool loops.
- Polymarket prediction markets (market-implied probabilities collide
  with the no-likelihood-claims gate); out of working-version scope.

## Source-rights deltas required (Codex B lane, founder decisions)

| Lane | TradingAgents uses | Our approved today | Delta needed |
| --- | --- | --- | --- |
| Fundamentals statements | Alpha Vantage / yfinance | EDGAR-bounded company profile only (34A-T6 disallows XBRL company facts) | New review: FMP fundamentals endpoints are the natural candidate (FMP already licensed for EOD market context); alternatively revisit the XBRL exclusion or review Alpha Vantage |
| Company news | Alpha Vantage news / yfinance news | SEC EDGAR filing metadata only | Article-level news needs a new commercial source-rights review; NOT required for the working version |
| Macro grounding | FRED data series values | FRED macro calendar metadata | Modest extension of an existing lane (US government data); needs freshness/as-of + interpretation-gate review |
| Prediction markets | Polymarket | none | Rejected for working version |

## Open questions routed onward
1. Founder/Codex B: approve FMP fundamentals as the statement-facts lane?
2. Founder: is filing-metadata + FRED-grounded macro sufficient for the
   News Analyst's working version, or open the commercial news review now?
3. Claude H: per-role fact-group design, per-role tool allowlists, and
   prompt contract v3 (supersedes p35-role-note-v2 through Claude E +
   Claude G review; PM synthesis prompt is new).

## REVISION 2026-07-10 - founder autonomy directive (supersedes parts of
## the Adapt/Reject sections above)

Founder direction: TradingAgents is the golden standard for product-agent
capability and autonomy. Give the agents as much permission, freedom, and
resources as possible; define hard safety boundaries and limit specific
behaviors, but the agents own in-depth analysis and truthfulness
verification. Team members exercise their own judgment.

Re-tiered boundaries (this table governs where it conflicts with the
earlier verdicts):

TIER 1 - HARD (legal/safety; unchanged and non-negotiable):
- Read-only product: no order execution, no broker automation, no
  credential/MFA handling.
- Privacy: no raw account identifiers, secrets, provider payloads, or
  credentials in any LLM-visible surface; account nickname-only.
- Source licensing: source-rights gates are legal constraints; new
  sources need Codex B review before use (approval requests welcome).
- Deterministic financial calculations are computed by tested backend
  code - but agents MAY invoke them freely as mediated calculation tools.
- No investment advice framing: no buy/sell/hold/overweight ratings, no
  "you should", no guaranteed returns. Educational analysis language.
- Frozen evidence readback; per-run cost/latency budgets.

TIER 2 - ADJUSTABLE POSTURE (previously over-constrained by Claude G;
now design freedom for Claude H / Claude E with verification-based
auditing):
- Note length/shape: roles may produce substantive analysis sections,
  TradingAgents-style, not just 2-4 sentence notes. Domain judgment
  decides.
- Numbers: "copy-only from envelope" relaxes to "verifiable" - agents may
  use values returned by mediated calculation/data tools; the auditor
  verifies provenance instead of banning derivation.
- Interpretation: attributed, uncertainty-qualified analytical
  interpretation of public data (filings, macro series, price context) is
  allowed; the blanket SEC/FRED interpretation bans become advice-boundary
  checks instead.
- Tool use: multi-step mediated tool loops allowed; broader per-role
  allowlists; agents are expected to cross-check sources and state what
  they verified.

TIER 3 - AGENT RESPONSIBILITY (by founder direction):
- Depth of analysis, choosing which tools to call and when, verifying
  truthfulness/freshness of resources, and stating evidence quality are
  the agents' job. The auditor is the backstop, not the analyst.
