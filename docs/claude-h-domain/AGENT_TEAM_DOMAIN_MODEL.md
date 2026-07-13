# Agent Team Domain Model — Portfolio/Trading Domain Review

Status: proposed (Claude H initial domain review, 2026-07-08). No code change.
Owner: Claude H (portfolio management and trading domain lead).
Suggested reviewers: Codex A/founder (product), Claude E (agentic alignment),
Codex B / Claude G (architecture/privacy/safety), Codex C (backend feasibility).

Scope: reviews the current Agent Team direction as of P34A-T18 ("working
version achieved") and proposes the domain model for the first genuinely
useful working prototype. Everything here is analysis-only decision support
framing; nothing authorizes advice, execution, or new sources without the
existing source-rights gates.

Locked question (unchanged): **"What would I be ignoring if I acted manually
now?"** Roles surface context; they never advise, rank, predict, or conclude
whether to act.

---

## 0. Verdict on the current direction

The architecture is right and unusually disciplined: deterministic backend owns
every number; roles are evidence-tiered (public vs agent-safe); the Evidence
Auditor is a non-authoring compliance function; freshness is split honestly
between broker snapshot and market quote; reports freeze and replay without
recomputation. The v3 structure/numeric/category gates directly answer the T13
failure ("live layer adds risk without value"). Do not restructure any of this.

The domain problem is no longer safety or plumbing. It is that **the two roles
a self-directed investor would pay attention to — Risk Manager and the options
review — are evidence-starved on exactly the facts a manual trader most often
ignores.** The deterministic read models say so themselves:

- `ConcentrationAllocationImpactRead.allocation_drift_status` is the literal
  `"not_modelled_in_phase_18a"`.
- `OptionsExposureRead.covered_call_coverage_model` is `"not_applicable" |
  "not_fully_modelled"`; `cash_secured_put_collateral_model` is
  `"generic_rule_only"`.
- The Risk Manager's prompt envelopes carry **no numerics at all** (T17 §1.3),
  so its live prose can only shuffle category labels.
- No approved evidence lane can answer "does an earnings date or ex-dividend
  date fall before this option's expiry?" — the single most commonly ignored
  fact in covered-call and cash-secured-put decisions.

The highest-leverage work is therefore deterministic evidence depth for the
portfolio-aware lane, not more roles, more prose, or more sources of news text.

## 1. Recommended roster for the first real working prototype

Keep the current five reporting roles plus two meta roles. Add nothing.

| Role (backend key) | Tier | v1 posture |
| --- | --- | --- |
| `risk_management_agent` | agent-safe | **Flagship.** Absorbs the options-structure checklist (see §2.1); the deferred `options_structure_analyst` stays deferred. |
| `portfolio_manager_agent` | agent-safe synthesis | Deterministic-compositional (per T17 D5). Owns report ordering and the manual verification checklist (§4). |
| `technical_analyst` | public | The value-carrying lane (FMP EOD + deterministic indicators). Already the strongest public role after T16/T17. |
| `news_analyst` | public | Honest-gap reporter today (SEC filing metadata + FRED release names/dates). Becomes the **Events Analyst** in substance once an earnings/ex-div lane is approved (§5.1). No renaming needed; display labels are backend-owned. |
| `fundamentals_analyst` | public | Honest-gap reporter over EDGAR identity metadata. Keep thin; do not pad. |
| Planner (meta) | run-state only | Keep out of `AGENT_TEAM_ROLES`. |
| Evidence Auditor (meta) | run-state only | Keep out of `AGENT_TEAM_ROLES`; fail-closed hard blocks never re-passed. |

Why not add roles: a sixth persona (Options, Macro, Sentiment) would today
receive either no approved evidence or the same envelopes the Risk Manager
already receives. In a real review desk, options structure review sits inside
risk review until options flow justifies a dedicated desk seat; same logic
applies here. Every added role multiplies advice surface, latency, and eval
cost without new evidence to stand on.

Permanently rejected (reaffirming the P25A persona analysis): any Trader /
execution / order-staging role, debate-to-conviction researchers, and any role
whose output is a verdict. Also recommend keeping bull/bear "considerations
for/against" **rejected rather than deferred**: a one-sided "considerations
against acting" section in a pre-trade report is functionally a
recommendation-shaped artifact, and the gaps/caveats framing already carries
the useful half of it safely.

## 2. Role-by-role domain responsibilities

Compact per-role contract. "Needs from backend" = deterministic fields; the
LLM layer never computes them. Wording examples are illustrative synthetic
examples, not template text.

### 2.1 Risk Manager (`risk_management_agent`) — flagship

**Purpose:** name what the deterministic review found that a manual actor
would most plausibly ignore: portfolio impact, concentration, cash/collateral
lock-up, option structure mechanics, freshness, and scope limits.

**Analyzes (v1 checklist, in priority order):**
1. Post-trade symbol concentration change (banded, §3.1).
2. Cash/collateral commitment the trade would freeze (CSP collateral,
   CC share coverage), and for how long (days to expiry).
3. Assignment/call-away mechanics as scenario facts: what enters/leaves the
   account if assigned/exercised (`assignment_share_delta` /
   `exercise_share_delta` already exist).
4. Event proximity vs option lifetime: earnings date or ex-dividend date
   before expiry (blocked until §5.1 lane approved — until then, named as an
   explicit not-reviewed gap, never silently omitted).
5. Freshness categories by name (broker snapshot vs market quote), and
   whether the review ran on a stale snapshot.
6. Scope caveats: which accounts/positions the review could not see
   (`account_feasibility_not_evaluated`, `liquidity_model_unverified`).
7. Risk-rule violations verbatim from `RiskRuleViolationSummaryRead`.

**Evidence it may use:** its current citable set (`trade_intent_summary`,
`scope_state`, `actionability`, `account_readiness`, `freshness`,
`portfolio_impact_summary`, `before_after_portfolio_impact`,
`concentration_risk_drift`, `liquidity_collateral_caveats`,
`options_exposure_summary`, `market_quote_freshness`) plus, if approved,
banded impact values (§3.1).

**Must not use:** raw cash balances, buying power, account values, tax lots,
provider IDs, technical indicator values (D4 kept values technical-role-only
for v3; revisit only after banded-values review).

**Answers:** "What does this trade do to concentration/collateral that the
saved evidence can show?" "What could not be verified?" — **Refuses:** "Is this
too risky?" "Should I size it differently?" "Is now a good time?"

**Needs from backend (the deterministic gap list, §3):** banded concentration
before/after, real CSP collateral figure per contract (generic rule is fine;
label it), CC coverage status vs saved share count, days-to-expiry,
moneyness band label, event-before-expiry flag (later), account-type caveat
code (later).

**Safe wording:** "If assigned, 200 shares of the underlying would be
purchased at the strike; the saved evidence does not show whether cash for
this collateral is committed elsewhere." — **Unsafe:** "The collateral is
manageable", "assignment is unlikely", "this position is safe/oversized",
any probability, any comfort adjective attached to a risk fact.

**Eval checks:** every numeric verbatim-from-envelope (existing gate); every
checklist item either present or named as a gap — an options review that
mentions neither event proximity nor its absence fails usefulness eval;
category words envelope-exact (existing gate).

### 2.2 Portfolio Manager (`portfolio_manager_agent`)

**Purpose:** compose audited role sections into the one-screen answer to the
locked question. Stays deterministic-compositional (T17 D5); live PM prose
remains deferred (T17B).

**Ordering rule (domain recommendation, deterministic):** contradictions
first (auditor-detected conflicts between sections), then the top gaps, then
impact facts, then confirmations. A busy investor reads the first five lines;
those lines must be the five most decision-relevant omissions, not
boilerplate. Cap the synthesis lead at ~5 items; everything else stays in
role sections.

**Owns the manual verification checklist (§4).** Refuses: any net
characterization ("overall this looks fine/risky"), any weighing of roles
against each other into a lean.

### 2.3 Technical Analyst (`technical_analyst`)

Working as designed post-T17/T18: verbatim envelope values, backend-derived
relationship labels, honest gaps, no levels/targets/signals vocabulary. Two
domain guards worth keeping explicit in evals: (a) relationship labels
(`close above SMA200`) must remain backend-derived — the model may quote,
never coin one; (b) "EOD, not live prices" caveat must appear whenever values
appear (it is the freshness fact a manual actor ignores most).

### 2.4 News / Events Analyst (`news_analyst`)

Today: deterministic listings of SEC filing metadata (`form_type`,
`filing_date`) and FRED release names/dates; no interpretation (the
`SEC_INTERPRETATION_TOKENS` guard stays). This is correct but thin — the role
earns its seat when it can answer **"what dated public events sit inside this
trade's time window?"** That requires the §5.1 events lane, not news text.
Until then its most valuable output is the honest gap: "No earnings or
dividend calendar was reviewed; verify upcoming events before acting."
Refuses: event impact interpretation, "market is reacting to…", sentiment.

### 2.5 Fundamentals Analyst (`fundamentals_analyst`)

EDGAR identity/listing metadata context + honest gaps. Keep deliberately
thin. UI should render its empty state as a first-class "not reviewed" card,
not padded prose (expectation-setting, per the P25A honesty flag). The next
fundamentals lane (EDGAR XBRL company facts) is interpretation-heavy;
defer (§6).

### 2.6 Evidence Auditor + Planner (meta)

No change. Domain endorsement: never let the auditor author user-visible
prose; a compliance function that writes narrative becomes another analyst.
Its outputs remain warning codes, drops, and structured contradiction flags.

## 3. Deterministic evidence gaps (what the backend must compute next)

These are numbers/flags, so they are Codex C work behind Codex B review —
never LLM work. Ordered by domain value per unit of effort:

### 3.1 Banded portfolio-impact values (privacy-preserving numerics for the risk lane)

Problem: risk envelopes carry no numerics by privacy design (no raw balances/
values may leave the backend), so risk prose is category-shuffling. Proposal:
backend-owned **band labels** as envelope strings, e.g.
`symbol_concentration_band_before: "5-10%"`, `after: "10-15%"`,
`concentration_direction: "increases"`, `estimated_collateral_band` for CSPs.
Bands are computed deterministically from private values but expose only a
coarse, backend-chosen vocabulary — analogous to the already-approved
freshness categories. The LLM quotes band strings verbatim under the existing
verbatim-or-silent gate; band strings join the category-gate vocabulary.
Needs an explicit Codex B privacy review (band granularity is the whole
question: recommend coarse fixed bands, no user-configurable thresholds in
v1). This single change makes Risk Manager prose substantive without leaking
a single account value.

### 3.2 Real allocation drift v1 (retire `not_modelled_in_phase_18a`)

Minimum useful model, not full drift analytics: per-symbol weight band
before/after (needs saved position values already in the snapshot), cash
allocation band before/after, and a `single_position_over_10pct` /
`over_20pct` flag family. Sector/asset-class drift stays deferred (no
approved classification source; SIC is explicitly caveated as too
broad/legacy for allocation math).

### 3.3 Options structure facts v1 (retire `not_fully_modelled` for the two wedge strategies)

For covered calls: coverage check vs saved share count (covered / partially
covered / not verifiable in scope), strike-vs-EOD-close moneyness **band
label** (e.g. `near_the_money`, backend-derived from the already-approved FMP
EOD close — never a level the LLM computes), days-to-expiry integer,
call-away scenario share delta (exists). For CSPs: collateral per generic
rule (strike × 100 × contracts) as an explicit banded or exact-string value
(it derives from the user's own proposed trade, not from account data — so
exact should be privacy-fine; flag for Codex B), assignment scenario share
delta (exists), days-to-expiry. All are trivial deterministic computations
over evidence that already exists in the saved package.

### 3.4 Days-to-expiry and event-window fields

`days_to_expiry` computed at freeze time (frozen evidence is timestamped, so
this is deterministic and replay-stable). Once §5.1 lands:
`earnings_before_expiry: true/false/not_reviewed`,
`ex_dividend_before_expiry: true/false/not_reviewed`. The three-valued form
is essential: `not_reviewed` is the honest state today and must render as a
named gap, not `false`.

## 4. Promote the manual verification checklist to a first-class artifact

Today the checklist lives as prose inside PM synthesis (P30A-T2 carried it
in existing fields; the additive `manual_verification_checklist` field was
deferred pending Codex B review). Domain view: this checklist is the
product's single most user-valuable output — the concrete, safe,
non-advisory answer to the locked question is literally "here is what to
verify at your broker before you act." Recommend reopening the deferred
additive field: deterministic, backend-composed from caveat codes, gaps,
freshness states, and (later) event flags. Example synthetic items:

- "Verify current buying power at your broker — this review could not see
  cash availability." (from `liquidity_model_unverified`)
- "Check for an earnings date before 2026-08-21 expiry — no event calendar
  was reviewed." (from `not_reviewed` event flag)
- "Your broker snapshot is from 3 days ago — re-sync before relying on
  position counts." (from freshness category)

Wording note for the safety validators: checklist items are imperative
*verification* instructions ("verify/check/confirm/re-sync"), which is
decision-support, not trading action. The validator vocabulary should
explicitly allow the verification-imperative class while continuing to block
action imperatives (buy/sell/roll/close/exercise/place/execute). This
distinction should be recorded in the validator spec so a future tightening
pass does not accidentally kill the checklist.

## 5. Real data sources: useful but not yet required

Priority-ordered domain view of the next source-rights gates. None are
required for the first working prototype; #1 is required before the options
wedge is honestly served.

1. **Corporate events calendar — earnings date + ex-dividend date only**
   (per reviewed symbol). Feeds §3.4 flags, the News/Events role, and the
   Risk Manager checklist. Structured, dated, low-interpretation-risk — by
   far the best value-to-risk ratio of any unapproved lane. Candidate
   providers need a fresh T15-style gate (FMP has calendar endpoints but was
   explicitly declined beyond EOD OHLCV in T15; that decision stands until
   the founder reopens it). Normalized fields only: event type, date,
   confirmed/estimated status. No estimates commentary, no surprise history.
2. **EDGAR XBRL company facts** (revenue/net income/shares outstanding as
   reported): would give Fundamentals real substance, but every number
   invites valuation talk; needs the strictest interpretation guard yet.
   Defer until after the events lane proves the gate pattern.
3. **Option chain snapshot for the reviewed contract only** (bid/ask/OI/IV
   at freeze time): would let the deterministic layer state liquidity facts
   (spread width band, open interest present/absent) — real assignment- and
   exit-relevant context. Provider licensing is the blocker; keep parked but
   name it in the roadmap.
4. **FRED release values** (not just names/dates): only if a macro lane ever
   earns a seat; currently no role needs it. Keep deferred.

Not recommended at any near-term point: general news text lanes
(NewsAPI/Benzinga/GDELT etc., already blocked), social sentiment, analyst
ratings/price targets (recommendation-shaped data poisons the no-advice
posture from the evidence side).

## 6. Deferred / rejected (domain confirmation)

- `options_structure_analyst` persona — deferred; duties live in Risk
  Manager v1 (§2.1). Revisit only when multi-leg strategies (spreads,
  collars) enter scope.
- Macro Analyst persona, sentiment persona — deferred/none.
- Bull/bear "for/against" sections — recommend moving from deferred to
  rejected (§1).
- Sector/asset-class concentration — deferred until a licensed
  classification source exists; do not build on SIC.
- Tax-lot / holding-period / wash-sale awareness — deferred (matches the
  existing "do not infer tax lots" rule). v1 may ship only a static
  account-type caveat code (e.g. `tax_context_not_reviewed`) rendered in the
  checklist.
- EDGAR XBRL fundamentals, option-chain liquidity, FRED values — §5 order.
- Live PM synthesis — deferred (T17B), agreed.

## 7. What makes the saved report genuinely useful (usefulness rubric)

For the pending founder usefulness read (T18) and future Claude E evals,
judge a report against what a busy self-directed investor does with 60
seconds. Proposed rubric — score each 0–2:

1. **Impact specificity:** does it state what this trade changes
   (concentration band, collateral lock, shares in/out on assignment) in
   numbers/bands, not adjectives?
2. **Top-gap prominence:** are the 3 most decision-relevant unreviewed
   things (events calendar, cash availability, staleness) in the first
   screenful?
3. **Checklist actionability:** could the user execute every verification
   item at their broker without interpreting anything?
4. **Freshness honesty:** is every value dated/categorized, with EOD-not-live
   stated wherever prices appear?
5. **Contradiction surfacing:** if two evidence sections disagree, is the
   disagreement named first?
6. **Silence discipline:** zero filler — no sentence that merely restates
   that evidence exists ("the trade intent summary is available") without a
   fact or a gap. This is the anti-T13-label-shuffling test as a usefulness
   criterion, not just a safety one.

A report scoring high on 1–3 with today's evidence is possible for stock/ETF
flows; for CC/CSP flows, criterion 1–2 cannot score full marks until §3.3
and §5.1 land — which is the quantified case for that work.

## 8. Gaps in the current product direction (summary)

1. **Events lane absent** — the options wedge cannot be honestly served
   without earnings/ex-div-before-expiry awareness (§5.1, §3.4).
2. **Risk numerics absent from envelopes** — banded values proposal (§3.1).
3. **Allocation drift literally not modelled** — §3.2.
4. **CC/CSP models placeholder-grade** — §3.3, despite options being the
   product wedge.
5. **Manual verification checklist buried in prose** — §4.
6. **No usefulness rubric** — safety evals are mature; usefulness evals are
   not (§7). The T13 "too generic" finding was caught by a human read, not a
   harness.
7. **Expectation-setting for thin public roles** — Fundamentals/News should
   render as honest "not reviewed" cards in the UI rather than short prose
   that looks like weak analysis (relevant to the open P34A-T14 integrated
   console direction).

## 9. Highest-leverage next implementation tasks (proposed sequence)

1. **Founder usefulness read of the T18 artifact against the §7 rubric**
   (founder + Claude H; no code). Calibrates everything below.
2. **Options/impact deterministic pack** (§3.3 + `days_to_expiry`): Codex C
   behind Codex B review. Small, high-value, no new sources, no privacy
   change.
3. **Banded portfolio-impact envelope proposal** (§3.1): Claude H writes the
   band vocabulary + wording spec with Claude E; Codex B privacy decision;
   then Codex C.
4. **Corporate events calendar source-rights gate** (§5.1): Codex B/founder
   decision doc, T15 pattern. Implementation follows only after PASS.
5. **Manual verification checklist additive field** (§4): reopen the
   deferred Codex B contract review; deterministic composition by Codex C.
6. **Usefulness eval pack** (§7): Claude E + Claude H encode the rubric as
   offline eval checks where mechanizable (e.g. silence discipline, gap
   prominence) and as a human-read scorecard where not.
7. **Allocation drift v1** (§3.2): after 2–3 land, since bands depend on it
   for before/after framing.

Items 2, 3, and 5 together convert the Risk Manager from a category-reader
into the report's centerpiece without touching a single safety boundary.
