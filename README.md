# Portfolio Options Agent / Portfolio Copilot

Portfolio Copilot is a full-stack, read-only **portfolio-aware trade review and risk copilot for manual investors**.

The product goal is not to become a brokerage dashboard, market-data viewer, option-chain browser, wheel-strategy app, options-income screener, AI stock picker, automated trading system, or thin TradingAgents wrapper. Before a user manually places a stock, ETF, or options trade outside this app, Portfolio Copilot should help them understand how that proposed action affects portfolio context, cash, collateral, exposures, data freshness, and risk rules.

Options remain a strong wedge because they make collateral, assignment, payoff, and freshness issues obvious. Covered calls and cash-secured puts are early high-value workflows, not the product identity.

## Safety Boundaries

- Manual decision support only.
- No automatic trading.
- No broker order placement, cancellation, disconnect, or destructive brokerage actions in normal app runtime.
- No broker password storage, MFA bypass, or broker scraping.
- SnapTrade is used only through read-only connection and sync flows.
- Broker portfolio freshness and market quote freshness are separate.
- Market quotes are not connected yet; current portfolio values are broker/manual/CSV snapshots, not live market prices.
- No guaranteed-return language.
- Avoid "you should buy/sell" advice wording.
- Deterministic Python services calculate financial metrics; LLMs may explain structured results but must not invent metrics.
- Real brokerage data, secrets, `.env` files, broker CSVs, statements, reports, exports, PDFs, XLS/XLSX files, and private configs must stay out of git and out of agent prompts unless explicitly scoped and sanitized.

## Current Status

The project is past initial scaffold. It currently includes:

- FastAPI backend with PostgreSQL, SQLAlchemy, Alembic, and pytest.
- Users and multi-account portfolio system of record.
- Cash, stock/ETF, option contract, and option position storage.
- Portfolio summary and broker-data warning logic.
- SnapTrade read-only broker sync foundation and connection flow.
- Encrypted SnapTrade user-secret storage and local-dev access guard.
- Manual entry and Fidelity CSV preview fallback.
- Report and agent history foundation.
- Market data contracts with manual/mock provider only.
- Generic deterministic options/risk services and risk report contract.
- React/Vite dashboard shell with broker connection, portfolio summary, positions, freshness, warnings, report placeholder, market-data status, risk-review stub, collapsible sidebar, and System/Light/Dark appearance mode.

The next backend direction is the trade-review foundation: `TradeIntent`, `StockTradeIntent`, `ETFTradeIntent`, `OptionStrategyIntent`, `OptionLeg`, portfolio context resolution, market snapshot resolution, deterministic portfolio-impact review, and risk-rule evaluation.

## Current Manual UI Workflow

Local UI routes:

- `/` - portfolio dashboard with user/account selector, portfolio summary, cash/stock/option positions, broker freshness, and warnings.
- `/broker` - read-only broker connection and account sync flow.
- `/market-data` - manual/mock market-data status slice; no real provider calls.
- `/risk` - deterministic risk review slice using synthetic stubbed data until backend risk APIs are wired.

Typical local workflow:

1. Start Postgres, backend, and frontend.
2. Select the local user in the top bar.
3. Open `/broker`.
4. Connect through the SnapTrade portal in a new browser tab. Do not enter broker credentials into this app.
5. Refresh broker connections.
6. Sync a broker account.
7. Use "View Portfolio" or return to `/` to inspect the account snapshot.
8. Review broker freshness and warnings before taking any manual action outside the app.

The UI is intentionally read-only. It should never show order tickets, buy/sell execution buttons, broker disconnect buttons, or language that implies automated portfolio management.

## Architecture Direction

The core architecture is layered:

1. **Portfolio System of Record** - users, accounts, broker/manual/CSV input, cash balances, stock/ETF positions, option positions, broker sync status, and broker freshness.
2. **Report and Agent History** - report threads, report messages, agent runs, agent steps, input/output snapshots, calculation version, and data freshness snapshots.
3. **Dashboard Shell** - cockpit for portfolio review, broker sync, freshness, warnings, report placeholders, market-data status, and risk review.
4. **Market Data Layer** - provider-agnostic stock quotes, option quotes, option chains, IV/Greeks, data mode, quote freshness, and actionability. Manual/mock only for now.
5. **Trade Intent Review Layer** - `TradeIntent`, `StockTradeIntent`, `ETFTradeIntent`, `OptionStrategyIntent`, and `OptionLeg`.
6. **Deterministic Trade/Risk Engine** - payoff scenarios, portfolio impact, cash/collateral impact, assignment/exercise scenarios, allocation/concentration impact, and risk-rule violations.
7. **Strategy Evaluators** - stock buy/sell/trim, ETF review, long call, long put, cash-secured put, covered call first; collars, spreads, hedges, and other strategies later.
8. **Custom Portfolio-Aware Agents** - deterministic-first agents that consume structured outputs and optionally use LLMs for explanation.
9. **TradingAgents Adapter** - optional asynchronous stock/company research evidence stream, not the fast-path decision engine.

TradingAgents should not receive account holdings, account values, cash balances, broker account ids, trade journal entries, or account-specific risk thresholds by default. It should be used later for public ticker/company research evidence only.

## Documentation Map

- `docs/architecture.md` - product and technical architecture.
- `docs/current_roadmap.md` - short current direction and active phase.
- `docs/implementation_plan.md` - active and future task plan.
- `docs/completed_phases_log.md` - archived completed phase history and verification notes.
- `docs/deferred_items.md` - known non-blocking follow-up work.
- `docs/agent_context/` - short Codex and Claude handoff briefs for context-efficient reviews.

## Relationship to `../TradingAgents`

`../TradingAgents` is a separate repository and should remain separate. This project may later integrate with it through an optional adapter layer or editable Python dependency, but this repository must not modify TradingAgents core files, copy its source code, vendor it as a subfolder, or add it as a git submodule.

## Local Development

Keep `.env` private. Use `.env.example` only for placeholder variable names. Do not paste secrets into prompts, logs, commits, screenshots, or issue text.

For the normal local stack, run Docker Compose from the repo root:

```bash
docker compose up --build -d
```

Then open:

```text
http://localhost:5173
```

Stop the local stack with:

```bash
docker compose down
```

Plain `docker compose down` keeps the local Postgres volume. Use `docker compose down -v` only when you intentionally want to delete local database state.

For backend-only or frontend-only development, you can still run services directly:

```bash
cd backend
./.venv/bin/alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

The Docker Compose path is the preferred all-in-one startup flow.

The frontend proxies `/api` requests to the backend. Browser code must never call SnapTrade, market-data providers, LLM APIs, or TradingAgents directly.

## Local Access Guard

The backend uses a local development access guard for data routes. The frontend dev proxy injects the local token server-side. The token is a local secret and must not be committed, displayed in the browser, or stored in frontend code.

If a direct API request returns 401/503 from protected routes, check the local backend/frontend configuration rather than weakening the guard.

## Validation Commands

Backend:

```bash
cd backend
./.venv/bin/python -m pytest
./.venv/bin/alembic current
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run lint
npm run build
```

Documentation-only changes can be checked with:

```bash
git diff --check
```

## Current Roadmap

Near-term phases are organized so backend contracts and frontend slices grow together:

1. Keep Phase 10/11/12/13 foundations stable: reports, dashboard, market-data contracts, and generic risk services.
2. Build Phase 14: Trade Intent Review Foundation.
3. Build Phase 15: Deterministic Trade Review Engine MVP.
4. Add custom portfolio-aware agents after deterministic outputs are stable.
5. Add TradingAgents later as optional async ticker/company research evidence.
6. Add the frontend trade review workspace after backend trade-review contracts are stable.

## Disclaimer

This project is not financial advice and is not an automated trading system. It does not execute trades. Outputs are scenario analysis and decision support for a human investor, who remains responsible for any real-world action taken outside the app.
