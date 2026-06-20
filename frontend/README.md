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

For reviewed local Skyframe fixture smoke runs, the development proxy can read
`SKYFRAME_FIXTURE_HEADER=private-safe-v1` and
`SKYFRAME_DASHBOARD_STATE=unavailable|populated|empty` and forward their
corresponding request headers to the backend. These variables are proxy-only:
they must not use a `VITE_` prefix and are never bundled into browser code.
Backend fixture activation still requires its separate local-only safety gates.

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

## Trade Review Workspace (P18A-T3 · P18B-T1/T2 verified · P18C-T3)

Route: `/trade-review` — Trade Review Workspace, now portfolio-backed (Phase 18C).

Review modes:
- **Portfolio-backed (default)** — `POST /trade-reviews/portfolio-preview`. The
  backend owns the portfolio context and freshness. The frontend never sends
  broker/market freshness, provider status, cash, holdings, or thresholds.
  Context selection is an opaque server-owned reference (e.g.
  `ctx_demo_latest`, `ctx_demo_stale`, `ctx_demo_missing`, `ctx_demo_empty`)
  or **Latest available**.
- **Synthetic preview (secondary/dev)** — the original `POST
  /trade-reviews/preview` is retained as a clearly labelled dev fallback that
  carries no portfolio context.

The response's `portfolio_context` summary surfaces only safe metadata —
opaque reference, source, selection mode, broker snapshot freshness, position
counts, cash-state **category**, and label — never holdings, balances, or
provider/account identifiers. Broker snapshot freshness and market quote
freshness remain separate scopes; the backend severity asymmetry is
presented as-is.

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
- `src/components/trade-review/` — Trade Review Workspace (P18A-T3 + P18C-T3 + P20A-T1 re-skin)
- `src/components/agent-team/` — Agent-team analysis console (P19A-T6 + P20A-T1 re-skin)
- `src/components/shared/mp/` — **Modern Portfolio Desk shared primitives** (P20A-T1).
  Broker-/data-agnostic: `Badge`, `Pill`, `Panel`, `KV`, `Stat`, `FreshnessDial`,
  `PageHeader`, `SafetyStrip`. Translated (not pasted) from the typed prototype's
  `components.tsx`. Consume `--mp-*` tokens only; never coupled to a backend
  schema. Re-skinned surfaces opt in with `className="mp-surface"`.

## Agent-team analysis console (P19A-T6)

Route: `/agent-team-analysis` — first role-by-role analysis console.

- Reuses the portfolio-backed Trade Review form (synthetic mode hidden) and
  posts to `POST /agent-team/trade-review-analysis/preview` via the existing
  `/api` Vite proxy. The backend route is stateless and uses the app-owned
  **mock LLM provider** by default; real provider calls remain a later gate.
- Renders the five roles in approved stage order: `fundamentals_analyst →
  news_analyst → technical_analyst → risk_management_agent →
  portfolio_manager_agent`. Each role panel shows display name, role status,
  `provider_status` badge (icon + text, never color-only), an `is_mock`
  indicator when applicable, and either `content_markdown` (rendered inside a
  `<pre>` — no HTML interpretation, no number parsing) or the
  `unavailable_reason`.
- The header surfaces `run_status`, `review_actionability_status`,
  `review_flow_label`, `workflow_version`, `generated_at`, and `run_reference`.
- Broker snapshot freshness and market quote freshness are rendered as two
  parallel, separately-scoped panels — never collapsed.
- `deterministic_evidence_summary` is rendered verbatim as a key/value list
  (counts and categories only; never values, holdings, or identifiers).
- `final_synthesis` is in its own analysis-only-labelled section, structurally
  separated from per-role outputs.
- `provider_warnings` and `stages` are rendered as plain lists.
- Required states: idle, loading, error, success, partial-success (banner when
  `run_status === "partially_completed"`).
- No order / execute / submit / cancel / disconnect / delete / buy-now /
  sell-now controls. No guaranteed-return / recommendation language. No
  `localStorage` / `sessionStorage` of portfolio, review, analysis, role,
  prompt, provider, credential, or account data.
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
