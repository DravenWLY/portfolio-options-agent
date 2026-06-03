# Agent Persona & Role Analysis (Phase 25A-T10)

Status: analysis / planning — no code change. Owner: Claude E. Product owner:
Codex A. Architecture/safety: Codex B. Compliance/UX copy: Claude D.
Date: 2026-06-02. Boundary record: ADR 0008 (safety spine), ADR 0002
(TradingAgents-inspired, not -centered), ADR 0005 (provider gate).

> Scope: which user-facing specialist personas Portfolio Copilot should expose
> now and later, how the 12 TradingAgents roles map onto a read-only,
> portfolio-aware, **no-advice** product, and what stays internal/deterministic.
> This authorizes no implementation; a scoped display-label slice is proposed at
> the end for Claude A + Codex B.

## 0. Framing & approved direction (from Codex A)

- **Specialist review team** positioning (decision-support, not advice): "helps
  you review proposed trades, understand portfolio risk, and manage your own
  portfolio decisions with clearer evidence, freshness context, and analysis-only
  explanations."
- UI labels carry **no "Agent"/`_agent"`. Backend keys may stay unchanged.
- Hard guardrail: Portfolio Copilot **helps the user think**; it does not manage
  the portfolio, recommend trades, allocate, place orders, or decide buy/sell.
- Forbidden product phrases: *manages your portfolio, your AI portfolio manager,
  tells you what to do, recommends trades, optimizes your portfolio, safe to
  trade, ready to trade, guaranteed return, buy/sell instruction, order/execution
  language.*

Two structural facts that drive the analysis:
1. Portfolio Copilot already has **two layers**: deterministic agent *components*
   (internal: portfolio context, trade review, freshness/actionability, report
   composition, output-safety/eval) and LLM *personas* (the user-facing team).
   Many TradingAgents "roles" map to our internal layer or to structured output
   **sections**, not to chat personas.
2. **Three of the five MVP personas currently run on mock/unwired evidence**
   (public fundamentals, news, market/technical data are not yet wired). The
   personas with real evidence today are **Risk Manager** and **Portfolio
   Manager** (they consume the real deterministic projection). This matters for
   private-alpha expectation-setting.

## 1. Current 5-persona team

| Persona (UI) | Evidence tier | May say | Must not say | UI now? |
| --- | --- | --- | --- | --- |
| **Fundamentals Analyst** | public only | synthesize approved public company/fundamental evidence; state what's available/unknown | invent P/E, valuation, price targets; "good/bad to own"; buy/sell | Yes (evidence mock today → must state availability honestly) |
| **News Analyst** | public only | summarize approved public news/macro/event context; note event proximity (e.g., earnings near expiry) as context | predict moves; "buy before earnings"; invented figures | Yes (evidence mock today) |
| **Technical Analyst** | public only | qualitative public market-context framing; explicitly note when data is unavailable | signals, support/resistance, price targets, entry/exit, "oversold→buy", invented indicator values | Yes, **highest-watch** (most advice-prone; market data unwired) |
| **Risk Manager** | agent-safe (deterministic projection) | interpret deterministic concentration/collateral/assignment/risk-rule outputs + freshness; "what to confirm" | invent risk numbers; verdicts like "risky/safe to trade"; position-sizing advice | Yes — **core, real value today** |
| **Portfolio Manager** | agent-safe synthesis | synthesize the team's analysis-only points; open questions; restate limitations | fiduciary management, allocation advice, "best path", optimize, buy/sell | Yes — **with mandatory guardrail copy** |

**Are 5 enough for MVP/private alpha? — Yes.** They cover public evidence (3),
portfolio-aware risk (1), and synthesis (1): coherent, minimal, safe. Adding
personas now raises LLM cost/latency and advice-surface without proportional
comprehension gain — especially while 3 of 5 run on mock evidence. The clearest
near-term gap is an **Options specialist (P1)** because options is the product
wedge. Honesty flag for Codex A: in private alpha the three public analysts may
feel thin until research/market adapters land; consider emphasizing Risk Manager
+ Portfolio Manager, or clearly labeling public-analyst evidence availability.

## 2. TradingAgents 12-role comparison

| TradingAgents role | Classification for Portfolio Copilot | Why |
| --- | --- | --- |
| Market Analyst | **Merge → Technical Analyst** | Same function (market/technical context). TA gives the LLM raw indicator tools; we give public/deterministic evidence only — no raw market tools in LLM hands. |
| Sentiment/Social Analyst | **Merge → News (MVP); Adapt later (P2)** | TA renamed social→sentiment because it lacked social data; we likewise have no sentiment source. Fold sentiment-as-context into News; separate persona only if an approved public sentiment source appears. |
| News Analyst | **Adopt now** | Already a persona. |
| Fundamentals Analyst | **Adopt now** | Already a persona. |
| Bull Researcher | **Adapt later as a structured section** ("Considerations For"), **not a persona** | TA's bull exists to win a debate → conviction. We forbid conviction/recommendation. Keep the *tradeoff surfacing*, drop the "bull" persona. P2. |
| Bear Researcher | **Adapt later → "Considerations Against" section** | Same as bull. |
| Research Manager | **Reject as persona / internal-only** | TA's research manager judges the bull/bear debate into an investment plan (a conviction). We have no debate-to-conviction. Its safe synthesis aspect is already covered by our Portfolio Manager. |
| Trader | **Reject (user-facing); replaced by deterministic Trade Review; optional internal-only "Trade Intent Interpreter"** | Produces a trade plan/decision — exactly what we forbid. See §5. |
| Aggressive Analyst | **Adapt later → "Risk Lens: Aggressive" section within Risk Manager**, not a persona | TA's risk debators argue to a conviction. Keep the *lens* framing over the SAME deterministic risk; drop the debate/conviction. P2. |
| Neutral Analyst | **Adapt later → "Risk Lens: Balanced"** | Same. |
| Conservative Analyst | **Adapt later → "Risk Lens: Conservative"** | Same. |
| Portfolio Manager | **Adopt the NAME, reject the function** | TA's PM emits final BUY/HOLD/SELL. Ours synthesizes educationally and emits no decision. Keep label (per Codex A) + guardrail copy; strip the decision behavior (already done). |

Net: **Adopt now** = News, Fundamentals, Portfolio-Manager-as-synthesis. **Merge**
= Market→Technical, Sentiment→News, Research-Manager-synthesis→Portfolio Manager.
**Adapt later as structured sections (not personas)** = Bull/Bear → For/Against,
Aggressive/Neutral/Conservative → Risk Lenses. **Reject as persona** = Trader,
Research Manager (as debate judge), and all debators as separate conviction
personas. (Our **Risk Manager** has no direct TA analog — it's our
portfolio-aware addition that interprets the deterministic risk engine.)

## 3. Additional Portfolio Copilot-specific role candidates

| Candidate | Product value | Placement | Data tier | Advice-drift risk | User-facing? |
| --- | --- | --- | --- | --- | --- |
| **Options Strategist / Options Risk Specialist** | HIGH — options is the wedge (covered call, CSP, assignment, collateral, expiry×earnings) | **P1** (top add) | agent-safe (deterministic options/collateral/assignment) + public option concepts | MED-HIGH ("strategist" implies suggesting strategies) → frame as "explains the deterministic risk of YOUR proposed leg," not "suggests a better strategy" | Yes (P1), tightly bounded; may start merged into Risk Manager |
| **Macro / Economic Specialist** | MED — macro/red-folder events (Phase 24A) | P2 (MVP: fold into News) | public | LOW-MED (keep `is_trading_signal=false`) | Later; merge into News for now |
| **Sentiment Analyst** | LOW-MED, no data source | P2/later | public | MED | Deferred; merge into News |
| **Income / Cashflow Analyst** | MED-HIGH for option-income/wheel flows | P2 (or merge into Options) | agent-safe (deterministic premium/income) | MED-HIGH (yield/return language) → numbers deterministic-owned, analysis-only | Later; careful copy |
| **Tax / Realized-Gain Specialist** | MED awareness on sells | **Reject MVP/P1; defer** | tax lots/cost basis are private-forbidden raw; needs a future deterministic awareness projection | HIGH (tax advice is regulated) | No — compliance-sensitive (Claude D); at most awareness-not-advice later |
| **Liquidity / Concentration Specialist** | MED | **Merge → Risk Manager** | agent-safe | LOW | Not a separate persona |
| **Data Quality / Freshness Specialist** | HIGH for trust | **Internal + structured UI badges**, not a chat persona | n/a (deterministic) | LOW | No — already the deterministic freshness/actionability layer; surface as freshness/data-mode badges |
| **Compliance / Safety Guardrail** | HIGH | **Internal-only** | n/a | n/a | No — it's the output-safety/eval harness + actionability gate; surfaces as safety badges/`eval_flags`, never a chat persona |

Standout user-facing add: **Options Strategist/Risk Specialist (P1)**. Everything
else either merges into Risk Manager, stays internal/deterministic, or defers.

## 4. Debate roles (Bull/Bear/Research-Manager, Aggressive/Neutral/Conservative)

**Decision: do not add debate personas. Defer to P2; if adopted, render as
structured output SECTIONS produced by existing personas — never as separate
conviction personas, debate loops, judges, winners, conviction scores, or "best
path."**

- The *information* (tradeoffs, risk appetite lenses) is genuinely useful for
  comprehension; the *debate-to-conviction* structure is too close to advice.
- Safe framing (all approved): **"Considerations For" / "Considerations Against"
  / "Risk Lens: Conservative / Balanced / Aggressive" / "Open Questions" / "What
  to Confirm Before Acting."**
- Implementation when reached: the **Portfolio Manager** synthesis emits
  For/Against + Open Questions; the **Risk Manager** emits the three Risk Lenses
  over the SAME deterministic risk. No bounded debate loop required (≤0–1 rounds
  if ever, per ADR 0008). Not separate UI personas.

## 5. Trader role

**Confirmed: reject as a user-facing persona.** The "what does this trade do"
job is owned by the **deterministic Trade Review services** (payoff, collateral,
assignment, portfolio impact). At most an **internal-only "Trade Intent
Interpreter"** concept — which is effectively the existing deterministic
trade-intent validation/review — never an LLM persona, never user-facing, never a
plan/decision producer.

## 6. "Portfolio Manager" label safety

The label is the single closest to the advice line — "Portfolio Manager"
connotes fiduciary management / "your AI portfolio manager" (a forbidden phrase),
and the label arguably says the opposite of the guardrail copy.

**Recommendation: keep "Portfolio Manager" now** (Codex A approved; behavior is
constrained to educational synthesis) **with mandatory always-visible guardrail
copy** — a persistent subtitle/tooltip like *"Synthesizes the team's analysis for
your review — does not manage your portfolio or recommend trades."* **No serious
safety reason to change it now**, given copy + constrained behavior.

But flag it as the **highest-risk label** for Claude D (compliance/UX copy)
review and user testing. **Pre-approved fallbacks** if testing shows fiduciary
confusion, in order of preference:
1. **Portfolio Lead** (keeps team-capstone gravitas, less fiduciary than "Manager")
2. **Portfolio Synthesis** / **Review Synthesizer** (most function-accurate)
3. (Avoid "Portfolio Strategist" — "strategist" implies recommending strategy.)

## 7. Recommended role roadmap

- **MVP / private alpha — user-facing personas (5):** Fundamentals Analyst,
  News Analyst, Technical Analyst *(highest-watch; tight no-signal copy)*, Risk
  Manager, Portfolio Manager *(with guardrail copy)*.
  - **Internal (not personas, power the UI):** deterministic Portfolio Context,
    Trade Review, Freshness/Actionability (data-quality), Output-Safety/Eval
    (compliance) → surface as evidence panels, freshness/data-mode badges, and
    safety/`eval_flags` badges.
- **P1:** **Options Strategist / Options Risk Specialist** (the wedge) —
  agent-safe deterministic options/collateral/assignment interpretation; may
  begin merged into Risk Manager.
- **P2 / later:** Macro/Economic Specialist (after Phase 24A is consumable);
  structured **Considerations For/Against** + **Risk Lenses (Conservative/
  Balanced/Aggressive)** sections (not debate personas); Income/Cashflow
  awareness; Sentiment (only with an approved data source).
- **Rejected:** Trader (→ deterministic trade review); Bull/Bear/Research-Manager
  and Aggressive/Neutral/Conservative as separate conviction personas; Tax/
  Realized-Gain *advice* persona (defer; compliance-sensitive, awareness-only at
  most); standalone Data-Quality and Compliance *chat* personas (internal
  deterministic/eval instead).

## 8. Documentation & routing

I can update (my lane): this doc; `AGENTIC_SYSTEM_DESIGN_MEMO.md` §6 role model;
the `P25A-T10` entry in `implementation_plan.md`.

Recommend (route to owners — not edited here):
- **Codex A:** `PRD.md`, `MVP_SCOPE.md`, `POSITIONING.md` — specialist-review-team
  positioning, the 5 persona descriptions, the no-advice guardrail, the
  Portfolio-Manager label policy + fallbacks, and the role roadmap.
- **Codex A / shared:** `docs/shared/AI_TEAM.md` "Educational Financial Language
  Rules" — add the forbidden product phrases (manages your portfolio, your AI
  portfolio manager, optimizes your portfolio, …) and the persona-label policy.
- **Codex B:** an `ARCHITECTURE_HANDOFF.md` note (or a short ADR 0009) for the
  **persona model + display-label read-contract** (display name vs machine key
  separation; per-persona evidence tier) **if** the read contract gains a
  `display_name` field.
- **Claude D:** Portfolio-Manager label + "manage your own portfolio decisions"
  framing review.

## 9. Proposed follow-up: display-label slice (Claude A + Codex B)

Scoped, separate task (not authorized here):
- Backend keys unchanged. Add a clean, backend-owned `display_name` per persona to
  the Agent Console read contract (or have the frontend map machine key → label).
- Display labels (no "Agent"): Fundamentals Analyst, News Analyst, Technical
  Analyst, Risk Manager, Portfolio Manager.
- Mandatory guardrail copy/tooltip for the Portfolio Manager persona.
- Composer stays disabled; analysis-only; no behavior change.
- Codex B reviews any read-contract field; Claude A implements the display layer;
  Claude D reviews the Portfolio-Manager copy.
