# P35-T1 — Trade-Impact Analysis Methodology

Status: accepted 2026-07-08 — Claude G review PASS as amended. Blocker B1
(SMH mislabeled "broad-market" in three narrative examples, contradicting the
§2.2 taxonomy that theme-maps SMH to Semiconductors) fixed in place per the
review's wording spec; amendments marked by this note. Recorded decisions:
D-R1 — the §2.4 "semiconductor ETFs commonly hold NVDA" sentence is
backend-rendered fixed text, never LLM-authored; D-R2 — the §5 narrative is
deterministic backend-rendered prose in v1 (outside the T17 live-gate $/% ban),
and any LLM-authored narrative is a separate Claude E v4 + Claude G decision.
Implementers note: §7's "add"/"trim"/"rebalance" bans apply to instruction
(imperative/second-person) use only — descriptive use ("would add a new
position") is compliant; validators must not substring-match these.
Mode: knowledge/design memo only. No code. Reviewer: Claude G.
Consumers: Codex C (deterministic engine), Claude E (report contract v4),
Codex A/founder (product read).

Locked question: **"What would I be ignoring if I acted manually now?"**
This memo defines how the answer becomes portfolio-relative instead of
symbol-relative: the proposed trade analyzed against the real synced
portfolio. All numbers in this memo are synthetic examples.

## 0. Layer note (read first, Claude G)

Everything below is **deterministic backend math and backend-rendered
wording**. Nothing here authorizes new LLM inputs. The user's own dollars and
percentages appearing in their own report is a backend read-contract matter
(the numbers never leave the deterministic layer); whether any of these
values later enter LLM prompt envelopes — and in what form (exact, banded,
fact-label) — is a separate Claude E v4 + Claude G decision, out of scope
here. Note one known interaction: the T17 live-gate bans `%`/`$` symbols in
LLM-authored prose. That ban applies to the live layer only; deterministic
report sections render normal `$1,234` / `12.3%` formatting. Contract v4
must keep that distinction explicit so the gates don't fire on
backend-rendered text.

Data reality assumed throughout: synced positions with market values are
available; per-symbol sector/industry classification is available (free FMP
endpoints); ETF constituent weights are **not** available in v1 (paid tier).
§1–§2 must work under that reality; §3 is the v2 design for when
constituents arrive.

---

## 1. Exposure decomposition

### 1.1 Dimensions

Four dimensions, coarse to fine, each answering a different "what would I be
ignoring" question for a retail portfolio:

| Dimension | Question it answers | v1 source |
| --- | --- | --- |
| **Asset class** | How much is cash vs single stocks vs funds vs options? | position type from the synced snapshot |
| **Sector** | Is one broad slice of the economy carrying this portfolio? | FMP sector string per classified symbol |
| **Industry** | Is the concentration narrower than the sector shows (semis inside tech)? | FMP industry string per classified symbol |
| **Single name (issuer)** | How much rides on one company? | direct positions in v1; direct + look-through in v2 (§3) |

Rules that keep the math honest:

- **One taxonomy.** All sector/industry strings come from one vendor (FMP)
  plus the internal ETF theme map (§2.2). Never mix vendors' taxonomies in
  one table — "Information Technology" (GICS-style) and "Technology"
  (vendor-style) are different buckets and will silently split exposure.
- **Issuer, not ticker,** is the single-name unit (dual share classes roll
  up). v1 may implement ticker-level and note the limitation; flag known
  dual-class pairs as a later refinement.
- **Options positions** count at their market value inside an "Options"
  asset-class bucket in v1. Attributing their underlying exposure to
  single-name/sector buckets is the §6 slice; until then the report says
  options were valued but not decomposed.
- **Short positions or margin debt** in the snapshot: out of scope for v1
  math; if detected, the exposure tables still render but carry a named
  caveat that short/margin positions were not modelled.

### 1.2 The denominator (define once, use everywhere)

`total_portfolio_value` = cash + market value of stock/ETF positions +
market value of option positions, **within the reviewed account scope, as of
the broker snapshot timestamp**. Every percentage in the report uses this
one denominator, and the report states its as-of date wherever percentages
appear. Do not offer a second "percent of invested value" figure in v1 — two
denominators in one report is how users misread their own concentration.

### 1.3 Proposed-trade notional and price basis

`trade_notional` = quantity × price basis. The price basis is, in order of
preference: the user-entered limit price, else the saved end-of-day close
from the approved market-context lane. The report always names the basis and
its date ("40 shares at the $175.00 July 7 closing price ≈ $7,000"). EOD
prices move; that is a verification item (§5), not something to hide.

### 1.4 Funding assumption (decision point for Codex C)

Percentages after a buy depend on where the money comes from. v1 uses two
clean deterministic regimes:

- **Cash-covered** (`snapshot_cash ≥ trade_notional`): assume the purchase
  is funded from account cash. The denominator is unchanged; cash bucket
  falls by the notional; the symbol/industry/sector buckets rise by it.
- **Not covered** (`snapshot_cash < trade_notional`): assume the full
  notional is new money from outside the account. Denominator grows by the
  notional; cash bucket unchanged. This avoids negative-cash nonsense and
  mixed-funding guesswork. It must carry a prominent finding: the snapshot
  does not show enough cash for this purchase, and funding was assumed
  external — verify buying power at the broker.

The chosen regime is stated in the report in plain words ("assuming this
purchase is paid from the cash in this account"). Partial/mixed funding and
margin are explicitly not modelled in v1.

### 1.5 Before/after table computation

For each dimension: bucket every position by its classification, sum market
values, divide by the denominator. Then apply the trade delta (notional
added to the proposed symbol's buckets; cash or denominator adjusted per
§1.4) and recompute. Table columns: **Before $, Before %, Trade Δ$,
After $, After %.** Rows: every affected bucket, plus the largest unaffected
buckets down to 95% cumulative coverage, plus an "Other" row so each table
visibly sums to ~100%.

Presentation rules: dollars to the nearest dollar; percentages to one
decimal; deltas written in words as "from 35.0% to 42.0%" (never "pp" or
"bps"); a position already held shows growth of the existing row, a new
symbol shows a new row labeled "new position".

### 1.6 Worked example (synthetic; used throughout this memo)

Reviewed scope holds, per the July 3 snapshot ($100,000 total):

| Position | Value | % |
| --- | --- | --- |
| Cash | $12,000 | 12.0% |
| SMH (VanEck Semiconductor ETF) | $35,000 | 35.0% |
| VTI (Vanguard Total Stock Market ETF) | $40,000 | 40.0% |
| AAPL (Apple) | $13,000 | 13.0% |

Proposed trade: buy 40 NVDA at the $175.00 July 7 close ≈ **$7,000**.
Cash-covered ($12,000 ≥ $7,000), so the denominator stays $100,000.

Single-name/asset view after: Cash $5,000 (5.0%), SMH $35,000 (35.0%), VTI
$40,000 (40.0%), AAPL $13,000 (13.0%), **NVDA $7,000 (7.0%, new position)**.

Industry view (v1, classification-level): Semiconductors = SMH (theme-mapped,
§2.2) $35,000 (35.0%) before → **$42,000 (42.0%)** after. VTI is a
broad-market fund and is excluded from industry/sector totals (§2.3), which
the coverage caveat names.

## 2. Overlap detection WITHOUT constituent data (v1)

### 2.1 What classification honestly buys us

Sector/industry classification turns "you are buying NVDA" into "you are
adding to a semiconductor bucket that already contains your SMH position."
That is a real, truthful, useful statement — it catches the canonical case.
What it cannot do: measure the overlap. Whether SMH itself holds NVDA, and
how much, is invisible without constituents. v1 must say the first thing
plainly and the second thing honestly.

### 2.2 Classifying ETFs is the trap

FMP profile sector/industry fields describe **companies** well and **funds**
badly — an ETF's profile often carries the wrapper's classification (blank,
"Financial Services", "Asset Management"), i.e. the fund *issuer's*
business, not the fund's holdings. Feeding that into sector math produces
garbage (every ETF becomes "financials"). v1 therefore classifies ETFs in
three tiers:

1. **Reviewed theme map** (backend-owned, versioned, auditable): a small
   internal table mapping narrow sector/industry ETFs to one
   industry/sector — SMH → Semiconductors, XLE → Energy, XLK → Technology,
   etc. Start with the few dozen most common thematic ETFs. Each mapping
   records `classification_source = internal_etf_theme_map_v<N>` so reports
   can attribute it. A theme-mapped fund's **entire** market value joins
   that one bucket — itself an approximation the caveat must name (SMH is
   ~100% semis, but XLK is not 100% software).
2. **Broad-market/diversified funds** (VTI, SPY, QQQ, target-date, total
   bond, etc. — also a reviewed internal list): bucketed as their own
   asset-class row "Broad-market funds — holdings not reviewed" and
   **excluded from sector/industry totals**. This is the single most
   important anti-distortion rule in v1: smashing a $40,000 VTI position
   into any one sector would dominate and falsify every sector figure.
3. **Unmapped funds**: "Funds — classification not reviewed", excluded from
   sector totals, counted into the coverage metric below.

### 2.3 Classified coverage (the honesty metric)

`classified_coverage` = market value of sector-classified securities ÷
market value of all securities (cash excluded). The report states it
whenever a sector/industry table appears. When coverage < 80%, every
sector/industry finding carries a mandatory coverage caveat. In the worked
example, coverage is $48,000 / $88,000 = **54.5%** (VTI is unclassified by
design), so the caveat fires:

> "Sector and industry figures cover $48,000 of your $88,000 in securities
> (55%). Your $40,000 VTI position is a broad-market fund whose holdings
> were not reviewed and is not counted in any sector."

### 2.4 Phrasing the SMH + NVDA finding truthfully at this granularity

What v1 can assert: both instruments are semiconductor-classified; the
bucket grows; the fund's holdings were not reviewed. What v1 must not
assert: that SMH holds NVDA, any weight, or any measured overlap. The
truthful v1 finding:

> "This purchase would add a new $7,000 NVDA position to a portfolio that
> already holds $35,000 of SMH, a semiconductor ETF. Your
> semiconductor-classified holdings would go from $35,000 (35.0% of your
> portfolio) to $42,000 (42.0%). SMH's individual holdings were not
> reviewed: semiconductor ETFs commonly hold NVDA, so your total NVDA
> exposure after this purchase could be larger than the $7,000 direct
> position shown. To measure the overlap, check SMH's current holdings on
> the fund issuer's site."

Note the construction: the possibility sentence asserts *what was not
reviewed* and *why it matters*, not a fact about SMH's contents. "Commonly
hold" is a statement about the category (acceptable general knowledge in a
caveat), never "SMH holds NVDA" (unverified specific claim). If Claude G
prefers zero category-knowledge claims, the fallback is: "SMH may itself
hold NVDA; its holdings were not reviewed." Either form is truthful; the
first is more useful.

### 2.5 Misclassification risks and their caveats

| Risk | Failure it causes | Required caveat / rule |
| --- | --- | --- |
| Vendor classifies fund wrapper, not holdings | ETFs land in "Financial Services", sector math falsified | never use vendor sector strings for ETFs; tiers of §2.2 only |
| Theme map treats fund as 100% its theme | over/understates the theme bucket | "Fund values are counted entirely in their labeled sector; actual fund composition differs." |
| Broad fund concentrated in same sector anyway | QQQ-heavy portfolio shows low tech % | "Broad-market funds may themselves concentrate in the sectors shown; their holdings were not reviewed." |
| Stale/wrong vendor classification | company re-bucketed after restructuring | "Classifications as of <date> from <source>; they can be broad, out of date, or wrong." |
| Conglomerates / multi-line companies | single label hides the mix | inherent to single-label taxonomies; covered by the general caveat above |
| Taxonomy mixing across sources | one exposure split across two same-meaning buckets | one-taxonomy rule (§1.1); engine must reject mixed sources per report |

## 3. Overlap detection WITH constituent data (v2)

### 3.1 Effective single-name exposure

For issuer *i*:

    effective_exposure(i) = direct_market_value(i)
                          + Σ over funds f [ weight_f(i) × market_value(f) ]

with each `weight_f(i)` carrying its own as-of date (constituent files lag
days to weeks — state the oldest as-of used). Weights summing to <100%
inside a fund (cash, other assets) is normal and needs no correction.
Surface effective exposures either ≥1.0% of the portfolio or in the top 10,
whichever is larger; everything else aggregates to "Other".

Look-through sector exposure: compute from constituents × *their* FMP
classifications (keeps the one-taxonomy rule) rather than fund-provided
sector breakdowns; use fund-provided breakdowns only as a labeled fallback.

### 3.2 No double counting — the mode switch

v2 reports run in **look-through mode**: the "Broad-market funds" bucket
dissolves into constituents, the §2.2 theme map stops feeding sector totals,
and the sector table is computed entirely from look-through. A report must
be entirely in one mode and labeled ("Fund holdings as of Jun 30 are
included in these figures"). Never show a fund-level sector table and a
look-through sector table as if they were comparable — they share neither
coverage nor as-of dates.

Single-name tables show **both** columns — direct and effective — because
the difference *is* the overlap insight.

### 3.3 What changes in the report (worked example continued)

Suppose constituents show NVDA at 20.0% of SMH and 5.0% of VTI (as of
Jun 30). Then before the trade, effective NVDA = $0 direct + $7,000 via SMH
+ $2,000 via VTI = **$9,000 (9.0%)** — a position the v1 report could not
see at all. After the $7,000 purchase: **$16,000 (16.0%)**.

The §2.4 possibility statement upgrades to measurement:

> "You already hold about $9,000 of NVDA through your funds ($7,000 via
> SMH at its 20.0% weight, $2,000 via VTI at 5.0%, holdings as of Jun 30).
> This purchase would take your total NVDA exposure from $9,000 (9.0% of
> your portfolio) to $16,000 (16.0%) — $7,000 held directly and $9,000
> through funds."

(In the canonical founder example — account holds SMH, buys NVDA at a
notional equal to the fund-held amount — the same math shows the doubling
directly: $7,000 effective → $14,000.)

Also new in v2: a "Largest effective exposures" top-5 table
(direct + through-funds columns); §4 thresholds run against **effective**
values as well as direct ones, with crossings labeled which basis fired
("16.0% of your portfolio including fund holdings, above the 10% single-
company reference point; your direct position alone is 7.0%"); and the
overlap check runs both directions (proposed symbol found inside held funds,
and — for a proposed *fund* purchase — held single names found inside the
proposed fund).

## 4. Threshold findings (deterministic, backend constants)

### 4.1 Design rules

- Thresholds are **reference points, not limits**. Every report that names
  one carries once: *"Reference points are common rule-of-thumb levels used
  to organize this report. They are not personalized limits, targets, or
  recommendations."* Provenance for choosing them: retail rules of thumb
  and the diversification bands regulators apply to *funds* (e.g. 5/25-type
  diversification tests) — borrowed as familiar orientation levels, never
  cited as rules the user is subject to.
- Report **both** kinds of state: a crossing caused by the trade
  (before < level ≤ after) *and* an already-above state (before ≥ level) —
  pre-existing concentration is exactly the thing a manual actor ignores.
- Compare on values rounded to one decimal (no findings from float dust).
- Constants are backend-owned in v1, not user-configurable: letting users
  set their own thresholds turns reference points into personalized
  suitability limits, which is advice-shaped. Revisit only with a reviewed
  design.
- Single-issuer thresholds apply to single-company securities only.
  Diversified funds get their own fund-level reference instead — a large
  VTI position is fund concentration, not issuer concentration, and
  flagging it at 10% like a stock would train users to ignore the finding.

### 4.2 Proposed defaults

| Finding | Trigger (v1 basis; v2 also effective §3) | Defaults | Neutral wording sketch |
| --- | --- | --- | --- |
| Single-company position share | one issuer's direct value ÷ portfolio | name at ≥10%, name prominently at ≥20% | "After this purchase, NVDA would be 12.4% of your portfolio, above the 10% single-company reference point used in this report." |
| Single-fund position share | one fund ÷ portfolio | ≥40% | "VTI would remain 40.0% of your portfolio — above the 40% single-fund reference point. Its holdings were not reviewed." |
| New-position size | trade notional ÷ portfolio | ≥5%, prominently ≥10% | "This single purchase equals 7.0% of your portfolio's total value." |
| Sector share | sector bucket ÷ portfolio (coverage caveat attached when §2.3 fires) | ≥25%, prominently ≥40% | "Technology-classified holdings would reach 55.0%, above the 40% sector reference point. These figures cover 55% of your securities (see coverage note)." |
| Industry share | industry bucket ÷ portfolio | ≥20%, prominently ≥30% | "Semiconductor-classified holdings were already above the 30% industry reference point before this trade (35.0%) and would reach 42.0%." |
| Cash consumption | notional ÷ snapshot cash | ≥50% | "This purchase would use 58% of the cash shown in your July 3 snapshot, leaving $5,000." |
| Cash shortfall | notional > snapshot cash | any | "The snapshot shows $4,000 in cash against a ≈$7,000 purchase. Percentages were computed assuming outside funds; verify buying power at your broker." |
| Holdings-count context | count of single-company positions and top-3 share | always stated, **no threshold** | "Your three largest holdings would make up 88% of the portfolio; two of the three are exchange-traded funds — one broad-market (VTI), one semiconductor-focused (SMH) — whose individual holdings were not reviewed." |

Why top-3/position-count carries no threshold: any ETF-core portfolio
trivially exceeds a top-3 level, so a flag there is noise; the *stated
composition* of the top-3 (funds vs single companies) is the useful fact.

### 4.3 Wording pattern (binding for the generator)

`[computed fact with numbers] + [reference-point name] + [nothing else]`.
The sentence ends after the reference point. No evaluative adjective
(high/heavy/excessive/comfortable), no imperative except the §5
verification items, no comparison to other investors, no "consider".

## 5. The trade-impact narrative checklist ("If you proceed")

The 5–10 statements a genuinely useful section must contain, in this order
(magnitude of change first, gaps last), every one backend-computed, in plain
language with zero jargon codes, each ideally ≤25 words. Worked-example
prose shown; bracketed items are conditional.

1. **Trade size in context.** "This purchase (≈$7,000 at the July 7 closing
   price) equals 7.0% of your $100,000 portfolio (July 3 sync)."
2. **Cash effect + funding basis.** "Paid from account cash, it would use
   58% of your $12,000 cash, leaving $5,000." [Or the shortfall statement,
   §4.2.]
3. **Position effect.** "You hold no NVDA directly today; this would create
   a new 7.0% position." [Or "your NVDA position would grow from $X (a%)
   to $Y (b%)".]
4. **Concentration effect (the overlap finding).** v1: the §2.4 statement.
   v2: the §3.3 measured statement.
5. **Sector/industry effect.** "Semiconductor-classified holdings would go
   from $35,000 (35.0%) to $42,000 (42.0%) — already above the 30% industry
   reference point before this trade."
6. **Portfolio shape after.** "Your three largest holdings would be VTI
   (40.0%), SMH (35.0%), and AAPL (13.0%) — 88% of the portfolio; two are
   exchange-traded funds — one broad-market (VTI), one semiconductor-focused
   (SMH) — whose individual holdings were not reviewed."
7. **[Reference-point crossings]** not already stated above, one sentence
   each (§4.2 wording).
8. **What this analysis did not review.** "Not reviewed: VTI's and SMH's
   individual holdings, upcoming earnings or dividend dates, taxes, and any
   account outside the reviewed scope. Prices are July 7 end-of-day, not
   live."
9. **Verify before acting.** Two to four checklist items: "Check your
   current buying power (snapshot is 5 days old). Check NVDA's current
   price against the $175.00 basis used here. Check SMH's holdings for NVDA
   overlap on the issuer's site."

Plain-language rules: absolute dates ("July 3"), never relative-only or
code-form (`broker_snapshot_freshness: manual` is banned from this section);
funds named ticker + full name on first mention; no abbreviation a
non-professional wouldn't know; percentages always anchored to "of your
portfolio" or "of your cash" — a bare "42%" is meaningless.

## 6. Options-trade impact framing (later slice; design intent)

The unifying idea: **an option's portfolio impact is a conditional version
of §1** — run the same before/after machinery on the scenario where the
option is exercised/assigned, and present at most two states: *as placed*
and *if assigned/called*.

**Cash-secured put:** As placed — collateral = strike × 100 × contracts is
set aside: "Selling 2 puts at the $95 strike sets aside $19,000 as
collateral — that is 87% of your snapshot cash — until the August 15 expiry
(38 days) or an earlier close. The $410 premium would be added to cash."
Premium is stated flat, **never** annualized, never as yield/ROI/return
(banned vocabulary). If assigned — a synthetic §1 buy of 200 shares at $95:
"If assigned, $19,000 of cash would become 200 NVDA shares — an 18.8%
position — and semiconductor-classified holdings would reach 37%." All §4
thresholds run on the if-assigned portfolio and are labeled as conditional.

**Covered call:** Coverage check first (100 shares per contract against the
snapshot; covered / partially covered / not verifiable in scope — a
partially covered call is a materially different instrument and is a
prominent finding, stated factually). If called — a synthetic §1 sale at
the strike: "If the shares are called away at $190, your NVDA position
would go from 12.0% to 0% and semiconductor-classified holdings from 42% to
30%; ≈$19,000 in cash would be received." Cost-basis, gain/loss, and tax
consequences of assignment are **not** computable without lot data and get
a named not-reviewed caveat, never an estimate.

**Both:** days-to-expiry is always stated; the earnings/ex-dividend-before-
expiry check joins statement 8 of §5 as a named gap until the events lane
is approved (see `docs/claude-h-domain/AGENT_TEAM_DOMAIN_MODEL.md` §5.1);
no probability-of-assignment, moneyness-implies-likelihood, or
"will likely expire worthless" language ever (§7).

## 7. What must NEVER be said — testable phrasing pairs

Ban list for the generator's output validator (extends the existing
prohibited-phrase sets): *overweight, underweight, buy, sell, hold, trim,
add (as instruction), rebalance (as instruction), should, consider, we
recommend, safe, comfortable, healthy, prudent, excessive, too
concentrated, well diversified, opportunity, attractive, cheap, expensive,
likely/unlikely (about market or assignment outcomes), probability/odds,
target, support, resistance, entry point, yield, annualized, return on
collateral, guaranteed.* Allowed imperatives (verification class only):
*verify, check, confirm, review, re-sync, compare.*

Wrong → right pairs (each pair is an eval case: left must never generate;
right is the acceptable shape):

| Never | Instead |
| --- | --- |
| "This would make you overweight semiconductors — consider trimming SMH first." | "Semiconductor-classified holdings would go from 35.0% to 42.0% of your portfolio." |
| "Your portfolio is too concentrated after this trade." | "After this purchase, NVDA would be 12.4% of your portfolio, above the 10% single-company reference point used in this report." |
| "You're well diversified, so this addition is fine." | "Your three largest holdings would make up 88% of the portfolio; two are exchange-traded funds — one broad-market (VTI), one semiconductor-focused (SMH) — whose individual holdings were not reviewed." |
| "Cash is sufficient; you can safely proceed." | "The snapshot shows $12,000 in cash against this ≈$7,000 purchase. Verify current buying power at your broker — the snapshot is 5 days old." |
| "A 7% position is a reasonable size for a new name." | "This single purchase equals 7.0% of your portfolio's total value." |
| "NVDA is attractive here given AI demand." | (nothing — outlook/valuation statements have no compliant form) |
| "Assignment is unlikely with the stock 8% above the strike." | "The July 7 closing price ($103.20) is above the $95 strike. Whether assignment occurs depends on prices through August 15, which this review does not predict." |
| "Selling these puts earns a 14% annualized yield on collateral." | "Selling the puts would add $410 to cash and set aside $19,000 as collateral until August 15." |
| "SMH already gives you plenty of NVDA exposure." | v1: the §2.4 statement. v2: "You already hold about $9,000 of NVDA through your funds; this purchase would take total NVDA exposure to $16,000 (16.0%)." |
| "Consider spreading this across two or three purchases." | (nothing — sizing/execution advice has no compliant form) |
| "You should wait until after earnings." | "No earnings calendar was reviewed. Check whether an earnings date falls before you plan to act." |
| "This breaks your 10% position limit." | "…above the 10% single-company reference point used in this report." + the standing reference-point disclaimer (§4.1) |

Test hooks for Claude E's v4 evals: (a) ban-list scan over generated
narrative; (b) every §5 statement present-or-named-as-gap; (c) every
threshold crossing in the deterministic findings has a matching §4.3-shaped
sentence and no evaluative adjective within its sentence; (d) every
percentage in the narrative reconciles to the §1 tables at one-decimal
precision; (e) the reference-point disclaimer appears exactly once when any
threshold finding fires.

---

*Not investment advice; this memo defines analysis-only decision support.
All portfolio values, weights, and prices above are synthetic examples.*
