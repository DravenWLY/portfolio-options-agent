# Phase 34A-T15 - Market-Data Agent-Tool Source-Rights Gate

Status: source-rights decision (accepted)
Owner: Claude G - Architecture / Contract / Privacy
Founder decisions recorded: 2026-07-07
Related: P34A contract (T4 gate lane), P22A market-data evaluation contract,
P34A-T6 news/event gate, P34A-T13 forced-model live-run quality read.

## Decision

P34A-T15 conditionally approves **one narrow real market-data lane** for Agent
Team tools:

> FMP (Financial Modeling Prep) end-of-day historical OHLCV for the reviewed
> symbol only, with all indicators computed by deterministic backend Python.

Purpose: give Agent Team roles real, citable public price/indicator values so
role reports can be specific instead of label-shuffling (the P34A-T13 finding).
This is the TradingAgents "verified snapshot" idea expressed under our rules:
deterministic code computes every number; the LLM may only reference frozen
envelope values; consistency is enforced by a validator, not by prompt
politeness.

## Founder decisions recorded (2026-07-07)

- **D1 - Source**: FMP daily historical prices, reusing the existing
  `FMP_API_KEY` and the reviewed injected-client pattern from the economic
  calendar lane. Alpaca (no live client, no keys) and yfinance (unacceptable
  ToS posture) were declined.
- **D2 - LLM use**: public symbol price/indicator values MAY be sent to the
  configured LLM provider (Gemini) inside sanitized ToolResult envelopes and
  MAY be frozen into saved reports. **Internal prototype only.** Private
  account data remains prohibited exactly as before.

## Source decisions

| Source | Decision | Reason |
| --- | --- | --- |
| FMP daily historical OHLCV (stocks/ETFs) | Conditionally approved | Existing key + reviewed runtime-client precedent in this repo; free tier includes EOD history; internal/personal-use tier matches the internal-prototype scope. |
| FMP news / fundamentals / analyst data | Not approved | News already rejected in P34A-T6; fundamentals need their own gate. |
| FMP intraday/live quotes | Not approved | "Live price" claims need licensing/display-rights review (P22A posture unchanged). |
| Alpaca | Declined for this slice | No live client or credentials exist; no data advantage for daily bars. |
| yfinance | Rejected | ToS-unstable scraping-adjacent source; not acceptable in the product repo. |

## Approved scope

Symbol scope: **exactly one symbol per report run** — the reviewed
instrument's (or option's underlying) symbol from the frozen saved evidence.
No agent-selected symbols, no watchlists, no crawling.

Allowed normalized fields (all backend-computed, frozen in
`tool_run_artifact`):

- `source_key = "fmp_eod_history"`;
- `source_label = "FMP end-of-day data (internal evaluation use)"`;
- symbol, as-of date, freshness category, data-window metadata (row count,
  first/last date);
- latest close, prior close, 52-week high/low;
- indicator snapshot: SMA50, SMA200, EMA10, RSI14, MACD/signal/histogram,
  Bollinger middle/upper/lower, ATR14 (deterministic, unit-tested backend
  Python; indicator omitted with an explicit `insufficient_history` caveat
  when the window is too short);
- backend-derived relationships (e.g., "close above/below SMA200",
  percent distance), computed deterministically, never by the LLM;
- caveat codes, including a mandatory `eod_not_live_prices` caveat.

Not allowed:

- raw FMP payload persistence, raw URLs, API keys anywhere;
- intraday/live-quote claims;
- options chains/Greeks from FMP (separate later slice);
- forecasts, price targets, ratings, or recommendation framing;
- LLM-computed or LLM-adjusted numbers of any kind.

## Validation requirements (binding for T16/T17)

1. Every numeric value in the envelope comes from tested deterministic code.
2. New auditor gate: any number appearing in live role prose must match a
   frozen envelope value (string/rounding-tolerant match, fail-closed drop of
   the finding otherwise). This upgrades the invented-number scan from "no
   numbers" to "only envelope numbers".
3. Existing advice/order/execution/leak scans unchanged.
4. Provider failure degrades to the existing honest unavailable behavior;
   the deterministic floor never depends on FMP availability.

## Retention, budget, failure

- Frozen values persist in saved reports (that is the readback model).
- Fetch budget: at most 2 FMP requests per report run; optional same-day
  per-symbol cache; no background refresh, no bulk ingestion.
- Attribution + `eod_not_live_prices` caveat must render wherever values are
  displayed.

## Production boundary

NOT approved: public/production display, redistribution, marketing use, or
any non-internal exposure of FMP-derived values. Before public launch this
lane requires a paid-plan/licensing review (tracked as a named follow-up in
the plan).

## Follow-up tasks

- P34A-T16 (Codex C): deterministic market-context tool pack per this gate.
- P34A-T17 (Claude E design, Claude G review): role report contract v3 +
  numeric-consistency auditor gate.
- P34A-T18 (Claude G): forced-model live rerun over rich evidence + founder
  usefulness read.
