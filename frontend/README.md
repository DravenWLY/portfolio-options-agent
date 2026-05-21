# Frontend — Portfolio Copilot Dashboard

React + Vite + TypeScript dashboard shell for `portfolio-options-agent`.

This is a **decision-support cockpit**, not a trading platform. No trades are placed from this UI.

---

## Prerequisites

- Node 18+ (Node 22 recommended)
- FastAPI backend running on `localhost:8000`

## Setup

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:5173`.

All `/api` requests are proxied to `http://localhost:8000` — see `vite.config.ts`.
The frontend never calls broker APIs or market-data providers directly.

## Available commands

| Command             | Description                        |
|---------------------|------------------------------------|
| `npm run dev`       | Start local dev server (port 5173) |
| `npm run build`     | TypeScript check + production build |
| `npm run typecheck` | TypeScript check only (no emit)    |
| `npm run lint`      | ESLint (zero warnings enforced)    |
| `npm run preview`   | Preview production build locally   |

## Phase 11 scope

This shell implements Phase 11 — Frontend Dashboard Shell A (all tasks complete):

| Task    | Status      | Description                          |
|---------|-------------|--------------------------------------|
| P11-T1  | ✓ done      | React/Vite shell, AppShell, TopBar, DashboardPage |
| P11-T2  | ✓ done      | User/account selector                |
| P11-T3  | ✓ done      | Portfolio summary view               |
| P11-T4  | ✓ done      | Cash / stock / option positions      |
| P11-T5  | ✓ done      | Broker freshness and warnings panel  |
| P11-T6  | ✓ done      | Report history placeholder           |
| P11-T7  | ✓ done      | Broker connection UI (`/broker`)     |

**Out of scope for Phase 11:** market quotes (beyond "not available" notice),
option screener, TradingAgents UI, trade execution UI.

## Broker Connection UI (P11-T7)

Route: `/broker` — read-only SnapTrade/Fidelity connection flow.

Safety copy present throughout:
- "Read-only broker sync — no trades are placed."
- "Do not enter Fidelity credentials into this app; use the secure provider portal."
- "Broker holdings may be stale; verify in Fidelity before taking any manual action."
- "Market quotes are not available yet."

Backend endpoints used (all existing, no new backend code):

| Endpoint | Purpose |
|----------|---------|
| `POST /users/{id}/broker-sync/snaptrade/register` | Register SnapTrade user |
| `POST /users/{id}/broker-sync/snaptrade/connection-portal` | Get portal URL |
| `POST /users/{id}/broker-sync/snaptrade/refresh-connections` | Pull broker accounts |
| `GET /users/{id}/broker-connections` | List connections |
| `GET /users/{id}/broker-connections/{cid}/accounts` | List broker accounts |
| `POST /users/{id}/broker-accounts/{aid}/sync` | Trigger account sync |
| `GET /users/{id}/broker-sync-runs/{rid}` | Poll sync run status |
| `GET /users/{id}/broker-accounts/{aid}/freshness` | Account freshness detail |

## Market Data status (P12-T9)

Route: `/market-data` — a thin read-only status slice for Phase 12.

- No real market-data provider is connected. The page renders a static,
  contract-faithful **sample** of the manual/mock `MarketDataProviderStatusRead`
  shape — it makes **no** network calls and stores nothing in browser storage.
- `data_mode`, `freshness_status`, and `actionability_status` are always shown
  **together** (a quote being recent never implies it is actionable; manual
  inputs are analysis-only).
- Market-quote freshness (`freshness_scope="market_quote"`) is shown explicitly
  **separate** from broker portfolio sync freshness (Dashboard / Broker pages).
- Copy is conservative: provider-not-connected, manual/mock only, not live
  pricing, no guaranteed-return / trade-execution language.

## Trade Review Workspace (P18A-T3, P18B-T1/T2 verified)

Route: `/trade-review` — first visible Trade Review Workspace.

- Supported flows: **Stock/ETF buy**, **Stock/ETF sell or trim**, **Covered call**,
  **Cash-secured put** (Phase 18A scope).
- Calls `POST /trade-reviews/preview` via the `/api` Vite proxy. The endpoint is
  **synthetic and stateless**: no DB, no broker sync, no market-data provider,
  no TradingAgents, no LLMs, no broker actions.
- Renders the sanitized `TradeReviewWorkspaceRead` verbatim — the frontend
  performs **no** financial computation and **never invents** backend fields.
- Broker snapshot freshness and market quote freshness are shown as **separate
  scopes**; the backend severity asymmetry is presented as-is.
- Covered-call coverage is **not fully netted** and CSP collateral uses a
  **generic deterministic rule** — both caveats are surfaced inline.
- Deterministic facts, agent orchestration status, and analysis-only narrative
  are visually separated; no order/execute/cancel/disconnect UI; no
  guaranteed-return or recommendation language; no `localStorage`/
  `sessionStorage` of portfolio or review data.
- Phase 18B verification keeps the same safe contract: the workspace shell and
  deterministic report UI are present, while optional public research evidence
  remains deferred until Phase 17 contracts are reactivated.

## Architecture notes

- `src/components/layout/` — AppShell, TopBar, Sidebar (fixed chrome)
- `src/components/broker/` — Broker connection UI components (P11-T7)
- `src/components/marketdata/` — Market data status slice (P12-T9)
- `src/components/risk/` — Deterministic risk review slice (P13-T8)
- `src/components/trade-review/` — Trade Review Workspace (P18A-T3)
- `src/pages/` — top-level page components
- `src/styles/globals.css` — CSS custom properties (design tokens), global resets
- `src/api/` — fetch wrappers per domain
- `src/hooks/` — React data hooks
- `src/types/` — TypeScript types mirroring backend response shapes
- `src/context/` — AccountContext + UIPreferenceContext (each: def + provider + hook, split files)

## Appearance & layout preferences

- Appearance control (TopBar): **System / Light / Dark**. "System" follows
  `prefers-color-scheme` live; Light/Dark explicitly override it. Dark is the
  default cockpit theme; the light theme is a refined "paper cockpit" with
  status/warning colors darkened to keep WCAG-AA contrast.
- Sidebar collapse toggle: compact icon rail vs. full labels. The read-only /
  "no trades placed" framing stays visible in both states.
- Theme is applied to `<html data-theme="…">`; a pre-render bootstrap in
  `main.tsx` sets it before first paint (no flash).
- `localStorage` stores **only** the two non-sensitive UI preferences
  (`poa-appearance`, `poa-sidebar-collapsed`) — never account, broker,
  credential, token, or report data.

## Design tokens

All colors, spacing, and typography are CSS custom properties defined in
`src/styles/globals.css`. Do not hard-code color values in component styles.

Key token groups:
- `--color-bg`, `--color-surface`, `--color-surface-2` — dark background layers
- `--color-live/stale/error/unknown/reauth` — freshness/status palette
- `--color-accent` — interactive accent (links, focus rings)
- `--space-*` — 4px-based spacing scale
- `--font-size-*` — type scale
- `--sidebar-width`, `--sidebar-width-collapsed`, `--topbar-height` — layout constants
- `[data-theme="light"]` block overrides the dark `:root` tokens for the light theme

## Safety rules

- No API keys, broker credentials, or provider secrets in any frontend file.
- No `localStorage` / `sessionStorage` for tokens or account data.
- No direct calls from the browser to broker APIs — all network goes through `/api` → FastAPI backend.
- No trade-execution controls, order tickets, or auto-trade language.
- No guaranteed-return language.
- Demo/synthetic data must be clearly labeled as synthetic on screen.
- Manual broker-maintenance scripts are excluded from built backend images; in local
  Docker Compose they may be visible only because `./backend` is bind-mounted for development.
