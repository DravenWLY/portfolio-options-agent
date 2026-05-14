---
name: finance-dashboard-ux-review
description: Review portfolio/options dashboard UI for fintech safety, data freshness clarity, risk visibility, accessibility, and misleading trading language.
---

# finance-dashboard-ux-review

Use this skill to review any UI in `portfolio-options-agent` that displays portfolio holdings, options data, market quotes, risk metrics, scanner results, or recommendations. The goal is to keep the dashboard honest, calm, and safe for a human trader, and to prevent it from drifting toward an "automated trading product" feel.

## When to use

- A frontend PR or design is ready for review.
- A new screen or component shows broker, account, position, or quote data.
- An options screen, scanner, or chain view is added or changed.
- A risk or alert UI is added or changed.
- The user asks for a UX audit of the dashboard.

Pair with `frontend-design` for visual and component quality, and with `implementation-plan-review` to confirm scope discipline.

## What to read first

- `AGENTS.md`
- `docs/architecture.md`
- `docs/implementation_plan.md` (find the active task)
- `frontend/README.md`
- Component files in scope under `frontend/`

Do not read denied paths. If you need to know data shape, ask for synthetic fixtures.

## Review categories

Group findings into:

- Blocker - violates a safety boundary or hides risk from the user.
- Important - misleading, missing key option fields, missing required state, or accessibility failure.
- Polish - visual or copy improvements.

## Checklist

### 1. Broker sync freshness vs market quote freshness

- Every panel that shows broker positions has a visible broker sync timestamp and source.
- Every panel that shows market quotes has a visible quote timestamp and source.
- Broker timestamp and quote timestamp are shown separately, never merged into one global timestamp.
- Mixed sources are labeled clearly (for example: "Positions as of 09:42 ET (Tradier sync), Quotes as of 09:58 ET (delayed, source: market-data-provider)").
- Aging is computed and visible. Examples: "Live", "Delayed 15m", "Cached 2h", "Stale - last sync 11h ago", "Unknown - sync never completed".

### 2. Stale, cached, delayed, unknown, and error warnings

- Stale, delayed, cached, and unknown states each have a distinct visible label and icon, not color alone.
- "Unknown" is a real state. Components do not silently show zero, dash, or empty values when the underlying data has never loaded.
- A stale-data badge does not disappear after a failed refresh. Failed refresh keeps prior staleness visible and surfaces the failure.
- Vocabulary is consistent across screens: Live, Delayed, Cached, Stale, Unknown, Error, Reauth required, Offline.

### 3. No automatic trading or order execution UI

- No "Place order", "Execute", "Submit trade", "Auto-trade", "Auto-sell", "One-click sell", "Buy now", or similar action buttons.
- No order ticket, no order preview, no order confirmation flow.
- "Suggestions", "ideas", "candidates", "screen results", and "risk flags" must be clearly framed as research support. Copy should require the human to act outside the app, for example "review in broker before manual action".
- No flow that says "we will execute this for you", "we will place this order at broker X", or "auto-rebalance".

### 4. No guaranteed-return language

- Reject copy like "guaranteed return", "risk-free", "you will earn", "expected profit", "AI-picked winner", "this trade will".
- Use neutral framing: "modeled return assumes ...", "probability estimate uses method ...", "scenario, not a prediction".
- Returns shown must cite the assumption, the method, and the timestamp of the inputs used.

### 5. Options-specific field completeness

For each row of an options scanner, option position, or option-chain view, confirm presence and labeling of:

- Underlying symbol and current underlying price (with quote timestamp and source).
- Option type (call or put), strike, expiration date, and DTE (days to expiration).
- Premium fields: bid, ask, mid, last, with bid-ask spread visible.
- Volume and open interest, with timestamp.
- Collateral or buying power impact for the strategy.
- Breakeven price.
- Annualized ROI assumption, with the formula or method named.
- Probability metric, with method named (for example "delta proxy", "Black-Scholes p(ITM)", "historical frequency").
- Quote timestamp and source per row.
- Position origin label: "real (imported)", "manual entry", or "synthetic demo".

If any field is unknown, the row shows an explicit "unknown" badge rather than blanking the cell.

### 6. Required UI states

For every data-driven component, confirm explicit handling of:

- loading
- empty (no data yet)
- no-account
- no-position
- error (request failed)
- partial / degraded
- stale / cached / delayed
- reauth required
- unauthorized / forbidden
- offline

Reauth-required state has a clear primary action (for example "Reconnect broker") that explains what will happen and does not auto-trigger broker login flows.

### 7. Accessibility and non-color-only risk communication

- Risk and freshness states use icon + text + color. Removing color must still leave the meaning clear.
- WCAG AA contrast for normal text. AA Large for large text.
- All controls reachable by keyboard. `:focus-visible` preserved.
- Tooltips that contain critical info also appear as static text or accessible labels.
- Tables use proper headers and row associations.
- Charts have text alternatives or accessible summaries.
- Numeric columns use tabular numerals so values align.

### 8. Copy and tone

- Calm, factual, time-stamped. Avoid hype, emoji, and exclamation marks for risk-bearing content.
- Use precise verbs: "modeled", "assumed", "based on inputs as of HH:MM", "subject to change".
- Avoid second-person promises ("you will earn ...", "you can lock in ..."). Prefer scenario framing.
- Preferred labels for research output: "candidate", "screen result", "risk flag". Always pair with a "review in broker before manual action" reminder where the user might confuse output with a trade instruction.

### 9. Demo and example data

- Demo data is clearly labeled as synthetic on screen.
- No real tickers paired with real personal position sizes that look like a real user's portfolio.
- No real broker filenames or real account numbers, even redacted.

### 10. Security and bundle hygiene

- No API keys, broker credentials, or provider secrets in frontend source, env files exposed to the bundle, or fixtures.
- No `localStorage` / `sessionStorage` for tokens or personal account data.
- Network calls go through the project's backend or a clearly named proxy, not directly from the browser to a broker.

## Output format

1. One-paragraph summary of what was reviewed.
2. Findings grouped as Blocker / Important / Polish, each with file path, brief description, and suggested fix.
3. Short checklist confirming the ten categories above were considered.
4. A note on what remains out of scope and why (for example, "did not review backend calculation correctness; that belongs to backend tests").

Do not write code unless the user explicitly approves an implementation task in `docs/implementation_plan.md`.
