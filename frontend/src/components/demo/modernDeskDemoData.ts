/**
 * P20A-T3 — centralised placeholder/demo constants for the Modern Portfolio
 * Desk re-skin.
 *
 * These values illustrate the prototype layout. None of them are real
 * holdings, real account values, real trades, or real provider responses.
 * Every consumer of this module renders a `DemoChip` on the surrounding card
 * so the user can never mistake a placeholder for a connected datum.
 *
 * Rules in this file:
 *  - Synthetic tickers only (XYZ, QQQ, ZYX, AAA).
 *  - Neutral labels — "Trader", "Demo brokerage", "Demo IRA" — never a real
 *    broker name on an account-context label, never a personal name.
 *  - No raw private fields (account_id, provider_account_id, OAuth tokens,
 *    raw provider payloads, trade-journal entries).
 *  - No real-looking dollar precision that mimics a specific real portfolio.
 */

export const DEMO_DISPLAY_NAME = "Trader";

export interface DemoReadinessTile {
  title: string;
  subtitle: string;
  /** Single-line status, e.g. "Connected", "Synced 47s ago", "Not connected". */
  status: string;
  tone: "live" | "stale" | "block" | "mute" | "info";
  rows: ReadonlyArray<readonly [label: string, value: string]>;
}

export const DEMO_READINESS_TILES: ReadonlyArray<DemoReadinessTile> = [
  {
    title: "Broker connection",
    subtitle: "Demo brokerage · taxable",
    status: "Connected",
    tone: "live",
    rows: [
      ["Status", "● healthy"],
      ["Last sync", "47 seconds ago"],
      ["Auth", "OAuth · read-only"],
    ],
  },
  {
    title: "Broker snapshot",
    subtitle: "positions, cash, options",
    status: "Synced 47s ago",
    tone: "live",
    rows: [["As of", "demo · not yet connected"]],
  },
  {
    title: "Market quotes",
    subtitle: "position values shown are book values",
    status: "Not connected",
    tone: "mute",
    rows: [["Mode", "not_configured"]],
  },
  {
    title: "Agent provider",
    subtitle: "real provider gated by operator",
    status: "Mock provider",
    tone: "info",
    rows: [["Workflow", "v3.2"]],
  },
];

export interface DemoRecentReview {
  ref: string;
  flow: string;
  symbol: string;
  actionability: string;
  tone: "live" | "stale" | "block" | "mute" | "info";
  ago: string;
}

export const DEMO_RECENT_REVIEWS: ReadonlyArray<DemoRecentReview> = [
  { ref: "r_demo_a7c4", flow: "Stock · buy",        symbol: "XYZ", actionability: "BLOCKED · concentration", tone: "block", ago: "11m ago" },
  { ref: "r_demo_b91d", flow: "Covered call · sto", symbol: "QQQ", actionability: "MANUAL CONFIRM",          tone: "stale", ago: "1h 04m" },
  { ref: "r_demo_d20a", flow: "Cash-secured put",   symbol: "ZYX", actionability: "NORMAL REVIEW",            tone: "live",  ago: "3h 22m" },
  { ref: "r_demo_8f1c", flow: "ETF · sell / trim",  symbol: "AAA", actionability: "ANALYSIS ONLY · stale data", tone: "stale", ago: "yesterday" },
  { ref: "r_demo_5e3a", flow: "Stock · buy",        symbol: "XYZ", actionability: "NORMAL REVIEW",            tone: "live",  ago: "yesterday" },
];

export interface DemoRiskAlert {
  code: string;
  msg: string;
  ref: string;
  sev: "block" | "stale" | "info";
}

export const DEMO_RISK_ALERTS: ReadonlyArray<DemoRiskAlert> = [
  { sev: "block", code: "POS_CONCENTRATION_HIGH", msg: "Concentration in XYZ would exceed the configured cap after the proposed buy.", ref: "r_demo_a7c4" },
  { sev: "stale", code: "FRESH_BROKER_STALE",     msg: "Broker snapshot in the demo IRA is older than the configured policy.",          ref: "r_demo_b91d" },
  { sev: "stale", code: "OPT_CC_COVERAGE_HINT",   msg: "An existing covered call may leave only some shares unencumbered.",              ref: "r_demo_d20a" },
];

export interface DemoQuickReview { flow: string; label: string; sub: string }
export const DEMO_QUICK_REVIEWS: ReadonlyArray<DemoQuickReview> = [
  { flow: "stock_buy",        label: "Stock buy",         sub: "New review" },
  { flow: "stock_sell_trim",  label: "Stock sell / trim", sub: "New review" },
  { flow: "covered_call",     label: "Covered call",      sub: "New review" },
  { flow: "cash_secured_put", label: "Cash-secured put",  sub: "New review" },
];

export interface DemoWhatsRunning { label: string; status: string; tone: "live" | "stale" | "block" | "mute" | "info" }
export const DEMO_WHATS_RUNNING: ReadonlyArray<DemoWhatsRunning> = [
  { label: "Broker sync",            status: "operating",            tone: "live" },
  { label: "Deterministic rules",    status: "operating",            tone: "live" },
  { label: "Market data provider",   status: "not configured (mock)", tone: "mute" },
  { label: "LLM agent provider",     status: "mock provider",         tone: "info" },
];

export interface DemoPortfolioSource { name: string; mode: string; ago: string; tone: "live" | "stale" | "block" | "mute" | "info" }
export const DEMO_PORTFOLIO_SOURCES: ReadonlyArray<DemoPortfolioSource> = [
  { name: "Demo brokerage · taxable", mode: "OAuth · read-only", ago: "47s ago",        tone: "live"  },
  { name: "Demo IRA",                 mode: "OAuth · read-only", ago: "4h 12m ago",     tone: "stale" },
  { name: "CSV fallback",             mode: "manual snapshot",   ago: "yesterday",      tone: "mute"  },
];

export interface DemoContextRef { ref: string; source: string; label: string; counts: string; cash: string }
export const DEMO_CONTEXT_REFS_TABLE: ReadonlyArray<DemoContextRef> = [
  { ref: "ctx_demo_latest",  source: "manual", label: "Latest-like demo context",        counts: "27 stock · 6 options",  cash: "available"   },
  { ref: "ctx_demo_stale",   source: "manual", label: "Stale broker snapshot demo",      counts: "27 stock · 6 options",  cash: "available"   },
  { ref: "ctx_demo_missing", source: "manual", label: "Missing market quotes demo",      counts: "27 stock · 6 options",  cash: "available"   },
  { ref: "ctx_demo_empty",   source: "manual", label: "Empty / unavailable context",     counts: "0 stock · 0 options",   cash: "not_exposed" },
];

export interface DemoReportRow { ref: string; flow: string; symbol: string; actionability: string; tone: "live" | "stale" | "block" | "mute" | "info"; ago: string }
export const DEMO_REPORTS_TABLE: ReadonlyArray<DemoReportRow> = DEMO_RECENT_REVIEWS;

export const DEMO_SETTINGS_PROVIDER_INFO = {
  provider: "Mock provider (default)",
  workflowVersion: "agent-team v3.2 · mock",
  rolesEnabled: ["fundamentals_analyst", "news_analyst", "technical_analyst", "risk_management_agent", "portfolio_manager_agent"],
};
