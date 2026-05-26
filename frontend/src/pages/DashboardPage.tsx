import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Badge, DemoChip, KV, PageHeader, Panel, Pill, SafetyStrip, type MpTone } from "../components/shared/mp";
import { LoadingSkeleton, ErrorState, EmptyState } from "../components/shared/StateViews";
import { useAccountContext } from "../context/useAccountContext";
import { dashboardApi } from "../api/dashboard";
import { portfolioContextApi } from "../api/portfolioContext";
import { ApiRequestError } from "../api/client";
import type {
  TradeReviewListRead,
  TradeReviewListItemRead,
  RiskAlertListRead,
  RiskAlertItemRead,
  ReviewReadinessRead,
  DashboardAccountSummaryRead,
} from "../types/dashboard";
import type { PortfolioContextListRead, PortfolioContextRead } from "../types/portfolioContext";
import { DEMO_QUICK_REVIEWS } from "../components/demo/modernDeskDemoData";

/**
 * DashboardPage — Modern Portfolio Desk overview (P20C-T1).
 *
 * Backend-backed via reviewed P20B contracts:
 *   GET /api/users/{uid}/trade-reviews
 *   GET /api/users/{uid}/risk-alerts
 *   GET /api/users/{uid}/readiness
 *   GET /api/users/{uid}/dashboard-account-summary
 *   GET /api/users/{uid}/portfolio-contexts
 *
 * Safety:
 *   - Read-only. No order ticket / execute / cancel / buy / sell.
 *   - Demo labeling visible whenever data_mode is "synthetic_demo".
 *   - Broker snapshot freshness and market quote freshness are separate.
 *   - Agent provider readiness is separate from broker/market freshness.
 *   - No frontend financial computation. Backend display labels rendered verbatim.
 *   - No localStorage / sessionStorage writes.
 */

type LoadStatus = "idle" | "loading" | "success" | "error";

interface DashboardState {
  reviews: { status: LoadStatus; data: TradeReviewListRead | null; error: string | null };
  alerts: { status: LoadStatus; data: RiskAlertListRead | null; error: string | null };
  readiness: { status: LoadStatus; data: ReviewReadinessRead | null; error: string | null };
  summary: { status: LoadStatus; data: DashboardAccountSummaryRead | null; error: string | null };
  contexts: { status: LoadStatus; data: PortfolioContextListRead | null; error: string | null };
}

const INIT_SLOT = { status: "idle" as const, data: null, error: null };

function errMsg(err: unknown): string {
  if (err instanceof ApiRequestError) return err.detail;
  if (err instanceof Error) return err.message;
  return "Request failed.";
}

export default function DashboardPage() {
  const nav = useNavigate();
  const { selectedUser } = useAccountContext();
  const userId = selectedUser?.id ?? null;
  const displayName = selectedUser?.display_name ?? "Trader";

  const [state, setState] = useState<DashboardState>({
    reviews: INIT_SLOT,
    alerts: INIT_SLOT,
    readiness: INIT_SLOT,
    summary: INIT_SLOT,
    contexts: INIT_SLOT,
  });

  const loadAll = useCallback(() => {
    if (!userId) return;

    // Set all slots to loading
    setState({
      reviews: { status: "loading", data: null, error: null },
      alerts: { status: "loading", data: null, error: null },
      readiness: { status: "loading", data: null, error: null },
      summary: { status: "loading", data: null, error: null },
      contexts: { status: "loading", data: null, error: null },
    });

    // Fire all five requests in parallel
    dashboardApi.tradeReviews(userId)
      .then(data => setState(s => ({ ...s, reviews: { status: "success", data, error: null } })))
      .catch(err => setState(s => ({ ...s, reviews: { status: "error", data: null, error: errMsg(err) } })));

    dashboardApi.riskAlerts(userId)
      .then(data => setState(s => ({ ...s, alerts: { status: "success", data, error: null } })))
      .catch(err => setState(s => ({ ...s, alerts: { status: "error", data: null, error: errMsg(err) } })));

    dashboardApi.readiness(userId)
      .then(data => setState(s => ({ ...s, readiness: { status: "success", data, error: null } })))
      .catch(err => setState(s => ({ ...s, readiness: { status: "error", data: null, error: errMsg(err) } })));

    dashboardApi.accountSummary(userId)
      .then(data => setState(s => ({ ...s, summary: { status: "success", data, error: null } })))
      .catch(err => setState(s => ({ ...s, summary: { status: "error", data: null, error: errMsg(err) } })));

    portfolioContextApi.list(userId)
      .then(data => setState(s => ({ ...s, contexts: { status: "success", data, error: null } })))
      .catch(err => setState(s => ({ ...s, contexts: { status: "error", data: null, error: errMsg(err) } })));
  }, [userId]);

  useEffect(() => {
    if (userId) loadAll();
  }, [userId, loadAll]);

  /* ── No user ─────────────────────────────────────────────────────────── */
  if (!userId) {
    return (
      <div className="mp-surface" style={styles.page}>
        <PageHeader
          eyebrow="Workspace · overview"
          title="Dashboard"
          sub="Select a user from the developer account selector to load the dashboard."
        />
        <EmptyState title="No user selected" body="Select a user from the developer account selector to load dashboard data." />
        <DashboardSafetyStrip />
      </div>
    );
  }

  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Workspace · overview"
        title={`Good morning, ${displayName}.`}
        sub="Your readiness snapshot. Numbers shown on this page come from backend demo contracts — real market prices are not connected; broker values arrive from broker sync when a real account is bound. Manual decision support only."
        right={
          <button style={styles.primaryBtn} type="button" onClick={() => nav("/trade-review")}>
            New trade review →
          </button>
        }
      />

      {/* ── Readiness strip ──────────────────────────────────────────── */}
      <ReadinessStrip slot={state.readiness} onRetry={loadAll} />

      {/* ── Main body ────────────────────────────────────────────────── */}
      <section style={styles.body}>
        <div style={styles.colLeft}>
          {/* Recent trade reviews */}
          <RecentReviewsPanel slot={state.reviews} onRetry={loadAll} />

          {/* Risk alerts */}
          <RiskAlertsPanel slot={state.alerts} onRetry={loadAll} />
        </div>

        <div style={styles.colRight}>
          {/* Account summary — moved from readiness strip for legibility */}
          <AccountSummaryPanel slot={state.summary} onRetry={loadAll} />

          {/* Portfolio context summary */}
          <PortfolioContextSummaryPanel slot={state.contexts} onRetry={loadAll} />

          {/* Quick reviews — static presets, not backend-driven */}
          <Panel title="Quick reviews" tag="presets" right={<DemoChip />}>
            <div style={styles.quickGrid}>
              {DEMO_QUICK_REVIEWS.map((q) => (
                <button key={q.flow} type="button" onClick={() => nav("/trade-review")} style={styles.quickBtn}>
                  <span style={styles.quickLabel}>{q.label}</span>
                  <span style={styles.quickSub}>{q.sub}</span>
                </button>
              ))}
            </div>
          </Panel>

          {/* What's running — from readiness */}
          <WhatsRunningPanel slot={state.readiness} onRetry={loadAll} />
        </div>
      </section>

      <DashboardSafetyStrip />
    </div>
  );
}

/* ── Readiness strip ────────────────────────────────────────────────────── */

function ReadinessStrip({
  slot,
  onRetry,
}: {
  slot: DashboardState["readiness"];
  onRetry: () => void;
}) {
  if (slot.status === "loading") {
    return <LoadingSkeleton rows={2} label="Loading readiness…" />;
  }
  if (slot.status === "error") {
    return <ErrorState message={slot.error ?? "Failed to load readiness."} onRetry={onRetry} />;
  }
  if (!slot.data) return null;

  const r = slot.data;
  const isDemoMode = r.data_mode === "synthetic_demo";

  return (
    <section style={styles.readinessGrid}>
      {/* Broker snapshot — wider primary card */}
      <ReadinessTile
        title="Broker snapshot"
        subtitle={r.broker_snapshot.display_label}
        status={r.broker_snapshot.status}
        tone={readinessTone(r.broker_snapshot.status, r.broker_snapshot.is_blocking)}
        rows={[
          ["Status", r.broker_snapshot.status],
          ["As of", r.broker_snapshot.as_of_label ?? "—"],
        ]}
        isDemoMode={isDemoMode}
      />
      {/* Market quotes */}
      <ReadinessTile
        title="Market quotes"
        subtitle={r.market_quotes.display_label}
        status={r.market_quotes.status}
        tone={readinessTone(r.market_quotes.status, r.market_quotes.is_blocking)}
        rows={[
          ["Status", r.market_quotes.status],
          ["As of", r.market_quotes.as_of_label ?? "—"],
        ]}
        isDemoMode={isDemoMode}
      />
      {/* Agent provider */}
      <ReadinessTile
        title="Agent provider"
        subtitle={r.agent_provider.display_label}
        status={r.agent_provider.provider_mode}
        tone={agentProviderTone(r.agent_provider.provider_status)}
        rows={[
          ["Mode", r.agent_provider.provider_mode],
          ["Mock default", r.agent_provider.is_mock_default ? "yes" : "no"],
        ]}
        isDemoMode={isDemoMode}
      />
    </section>
  );
}

/* ── Account summary panel (body column) ───────────────────────────────── */

function AccountSummaryPanel({ slot, onRetry }: { slot: DashboardState["summary"]; onRetry: () => void }) {
  if (slot.status === "loading") {
    return (
      <Panel title="Account summary" tag="book-value">
        <LoadingSkeleton rows={3} label="Loading account summary…" />
      </Panel>
    );
  }
  if (slot.status === "error") {
    return (
      <Panel title="Account summary" tag="book-value" right={<DemoChip />}>
        <ErrorState message={slot.error ?? "Failed to load account summary."} onRetry={onRetry} />
      </Panel>
    );
  }
  if (!slot.data) return null;

  const s = slot.data;
  const isDemoMode = s.data_mode === "synthetic_demo";

  return (
    <Panel title="Account summary" tag="book-value" right={isDemoMode ? <DemoChip /> : undefined}>
      <KV rows={[
        ["Source", s.source_label],
        ["Total value", s.total_value_label ?? "—"],
        ["Cash", s.cash_label ?? s.cash_state_label],
        ["Stock exposure", s.stock_exposure_label ?? "—"],
        ["Option exposure", s.option_exposure_label ?? "—"],
        ["Stock positions", String(s.portfolio_shape.stock_position_count)],
        ["Option positions", String(s.portfolio_shape.option_position_count)],
      ]} />
      {s.market_data_unavailable && (
        <p style={styles.acctNote}>
          Market data unavailable — values shown are book values from broker snapshot.
        </p>
      )}
    </Panel>
  );
}

function ReadinessTile({
  title, subtitle, status, tone, rows, isDemoMode,
}: {
  title: string;
  subtitle: string;
  status: string;
  tone: MpTone;
  rows: ReadonlyArray<readonly [string, string]>;
  isDemoMode: boolean;
}) {
  return (
    <div style={{ ...styles.readinessCard, borderLeftColor: `var(--mp-${tone === "mute" ? "mute" : tone})` }}>
      <div style={styles.readEyebrow}>{title}</div>
      <div style={styles.readSub}>{subtitle}</div>
      <div><Badge tone={tone} dot>{status}</Badge></div>
      <KV compact rows={rows} />
      {isDemoMode && <div><DemoChip tight /></div>}
    </div>
  );
}

/* ── Recent trade reviews ───────────────────────────────────────────────── */

function RecentReviewsPanel({ slot, onRetry }: { slot: DashboardState["reviews"]; onRetry: () => void }) {
  const isDemoMode = slot.data?.data_mode === "synthetic_demo";
  return (
    <Panel title="Recent trade reviews" tag="last 7 days" right={isDemoMode ? <DemoChip /> : undefined}>
      {slot.status === "loading" && <LoadingSkeleton rows={4} label="Loading reviews…" />}
      {slot.status === "error" && <ErrorState message={slot.error ?? "Failed to load reviews."} onRetry={onRetry} />}
      {slot.status === "success" && slot.data && slot.data.items.length === 0 && (
        <EmptyState title="No recent reviews" body="No trade reviews have been generated yet." />
      )}
      {slot.status === "success" && slot.data && slot.data.items.length > 0 && (
        <table style={styles.tbl}>
          <thead>
            <tr><Th>Reference</Th><Th>Flow</Th><Th>Symbol</Th><Th>Actionability</Th><Th align="right">When</Th></tr>
          </thead>
          <tbody>
            {slot.data.items.map((r: TradeReviewListItemRead) => (
              <tr key={r.review_reference}>
                <Td mono>{r.review_reference}</Td>
                <Td>{r.review_flow_label}</Td>
                <Td mono>{r.symbol_or_underlying}</Td>
                <Td><Pill tone={actionabilityTone(r.review_actionability_status)}>{r.review_actionability_status}</Pill></Td>
                <Td mono align="right">{formatTimestamp(r.created_at)}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  );
}

/* ── Risk alerts ────────────────────────────────────────────────────────── */

function RiskAlertsPanel({ slot, onRetry }: { slot: DashboardState["alerts"]; onRetry: () => void }) {
  const isDemoMode = slot.data?.data_mode === "synthetic_demo";
  return (
    <Panel title="Risk alerts" tag="deterministic" right={isDemoMode ? <DemoChip /> : undefined}>
      {slot.status === "loading" && <LoadingSkeleton rows={3} label="Loading alerts…" />}
      {slot.status === "error" && <ErrorState message={slot.error ?? "Failed to load alerts."} onRetry={onRetry} />}
      {slot.status === "success" && slot.data && slot.data.items.length === 0 && (
        <EmptyState title="No active alerts" body="No risk alerts to display." />
      )}
      {slot.status === "success" && slot.data && slot.data.items.length > 0 && (
        <ul style={styles.alertList}>
          {slot.data.items.map((a: RiskAlertItemRead) => (
            <li key={a.alert_reference} style={{ ...styles.alertRow, borderLeftColor: severityColor(a.severity) }}>
              <Pill tone={severityTone(a.severity)}>{a.severity}</Pill>
              <div style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0 }}>
                <span style={styles.alertTitle}>{a.title}</span>
                <span style={styles.alertMsg}>{a.summary}</span>
                <span style={styles.alertCode}>
                  {a.category}{a.related_symbol_or_underlying ? ` · ${a.related_symbol_or_underlying}` : ""}
                  {a.related_review_reference ? ` · ref ${a.related_review_reference}` : ""}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

/* ── Portfolio context summary ──────────────────────────────────────────── */

function PortfolioContextSummaryPanel({ slot, onRetry }: { slot: DashboardState["contexts"]; onRetry: () => void }) {
  const isDemoMode = slot.data?.data_mode === "synthetic_demo";
  return (
    <Panel title="Portfolio context" tag="summary" accent right={isDemoMode ? <DemoChip /> : undefined}>
      {slot.status === "loading" && <LoadingSkeleton rows={3} label="Loading contexts…" />}
      {slot.status === "error" && <ErrorState message={slot.error ?? "Failed to load portfolio contexts."} onRetry={onRetry} />}
      {slot.status === "success" && slot.data && slot.data.items.length === 0 && (
        <KV rows={[
          ["Available contexts", "0"],
          ["Snapshot as of", isDemoMode ? "demo · not yet connected" : "—"],
        ]} />
      )}
      {slot.status === "success" && slot.data && slot.data.items.length > 0 && (
        <PortfolioContextRows items={slot.data.items} />
      )}
    </Panel>
  );
}

function PortfolioContextRows({ items }: { items: PortfolioContextRead[] }) {
  const latest = items[0];
  return (
    <KV rows={[
      ["Available contexts", String(items.length)],
      ["Latest", latest.context_label],
      ["Stocks (count)", String(latest.portfolio_shape.stock_position_count)],
      ["Options (count)", String(latest.portfolio_shape.option_position_count)],
      ["Cash state", latest.cash_state_label],
      ["Broker freshness", latest.broker_snapshot_freshness.display_label],
      ["Market freshness", latest.market_quote_freshness?.display_label ?? "unavailable"],
    ]} />
  );
}

/* ── What's running ────────────────────────────────────────────────────── */

function WhatsRunningPanel({ slot, onRetry }: { slot: DashboardState["readiness"]; onRetry: () => void }) {
  const isDemoMode = slot.data?.data_mode === "synthetic_demo";
  return (
    <Panel title="What's running" tag="provider status" right={isDemoMode ? <DemoChip /> : undefined}>
      {slot.status === "loading" && <LoadingSkeleton rows={3} label="Loading status…" />}
      {slot.status === "error" && <ErrorState message={slot.error ?? "Failed to load status."} onRetry={onRetry} />}
      {slot.status === "success" && slot.data && (
        <ul style={styles.facts}>
          <li style={styles.factRow}>
            <span style={styles.factLabel}>Broker sync</span>
            <Badge tone={readinessTone(slot.data.broker_snapshot.status, slot.data.broker_snapshot.is_blocking)} dot>
              {slot.data.broker_snapshot.status}
            </Badge>
          </li>
          <li style={styles.factRow}>
            <span style={styles.factLabel}>Market data</span>
            <Badge tone={readinessTone(slot.data.market_quotes.status, slot.data.market_quotes.is_blocking)} dot>
              {slot.data.market_quotes.status}
            </Badge>
          </li>
          <li style={styles.factRow}>
            <span style={styles.factLabel}>Agent provider</span>
            <Badge tone={agentProviderTone(slot.data.agent_provider.provider_status)} dot>
              {slot.data.agent_provider.provider_mode} · {slot.data.agent_provider.provider_status}
            </Badge>
          </li>
        </ul>
      )}
    </Panel>
  );
}

/* ── Safety strip ──────────────────────────────────────────────────────── */

function DashboardSafetyStrip() {
  return (
    <SafetyStrip items={[
      "Manual decision support only",
      "No order is placed from this app",
      "Analysis only",
      "Data freshness may affect review quality",
    ]} />
  );
}

/* ── Helpers ──────────────────────────────────────────────────────────── */

function readinessTone(status: string, isBlocking: boolean): MpTone {
  if (isBlocking) return "block";
  switch (status) {
    case "fresh": return "live";
    case "manual_review": return "stale";
    case "stale": return "block";
    case "unknown":
    case "unavailable": return "mute";
    default: return "mute";
  }
}

function agentProviderTone(status: string): MpTone {
  switch (status) {
    case "available": return "live";
    case "mock_default": return "info";
    case "error": return "block";
    case "unavailable": return "mute";
    default: return "mute";
  }
}

function actionabilityTone(status: string): MpTone {
  if (status.startsWith("blocked")) return "block";
  switch (status) {
    case "normal_review": return "live";
    case "analysis_only": return "info";
    case "manual_confirmation_required": return "stale";
    default: return "mute";
  }
}

function severityTone(severity: string): MpTone {
  switch (severity) {
    case "blocker":
    case "violation": return "block";
    case "warning": return "stale";
    case "info": return "info";
    default: return "mute";
  }
}

function severityColor(severity: string): string {
  switch (severity) {
    case "blocker":
    case "violation": return "var(--mp-block)";
    case "warning": return "var(--mp-stale)";
    case "info": return "var(--mp-info)";
    default: return "var(--mp-mute)";
  }
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.round(diffMs / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.round(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    return d.toLocaleDateString();
  } catch {
    return iso;
  }
}

/* ── Local sub-components ─────────────────────────────────────────────── */

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th style={{
      textAlign: align, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
      textTransform: "uppercase", letterSpacing: "0.08em", padding: "8px 12px",
      borderBottom: "1px solid var(--mp-rule)", fontWeight: 600,
    }}>{children}</th>
  );
}
function Td({ children, mono, align = "left" }: { children: React.ReactNode; mono?: boolean; align?: "left" | "right" }) {
  return (
    <td style={{
      textAlign: align, fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)",
      padding: "10px 12px", borderBottom: "1px solid var(--mp-rule)",
      fontFamily: mono ? "var(--mp-font-mono)" : undefined,
    }}>{children}</td>
  );
}

/* ── Styles ───────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", gap: "var(--space-6)", maxWidth: 1280, margin: "0 auto", color: "var(--mp-ink)" },
  primaryBtn: {
    fontSize: "var(--font-size-sm)", fontWeight: 600, padding: "8px 14px",
    backgroundColor: "var(--mp-accent)", color: "var(--mp-card)",
    border: "1px solid var(--mp-accent)", borderRadius: "var(--radius-sm)", cursor: "pointer",
  },
  readinessGrid: {
    display: "grid",
    gridTemplateColumns: "1.4fr 1fr 1fr",
    gap: "var(--space-3)",
    minWidth: 0,
  },
  readinessCard: {
    backgroundColor: "var(--mp-card)", border: "1px solid var(--mp-rule)",
    borderLeft: "2px solid var(--mp-mute)", borderRadius: "var(--radius-md)",
    padding: "var(--space-4)", display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  readEyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 },
  readSub: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)" },
  body: {
    display: "grid",
    gridTemplateColumns: "1.6fr 1fr",
    gap: "var(--space-6)",
    minWidth: 0,
  },
  colLeft: { display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0 },
  colRight: { display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0 },
  acctNote: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.5, margin: 0 },
  tbl: { width: "100%", borderCollapse: "collapse" },
  alertList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  alertRow: {
    display: "grid", gridTemplateColumns: "auto 1fr", gap: "var(--space-3)",
    padding: "var(--space-3) var(--space-4)", backgroundColor: "var(--mp-paper-2)",
    border: "1px solid var(--mp-rule)", borderLeft: "3px solid", borderRadius: "var(--radius-sm)",
    alignItems: "flex-start",
  },
  alertTitle: { fontSize: "var(--font-size-sm)", fontWeight: 600, color: "var(--mp-ink)", lineHeight: 1.3 },
  alertMsg: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.4 },
  alertCode: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", fontFamily: "var(--mp-font-mono)" },
  quickGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" },
  quickBtn: {
    display: "flex", flexDirection: "column", gap: 2, alignItems: "flex-start",
    padding: "var(--space-3) var(--space-4)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)", backgroundColor: "var(--mp-card)", color: "var(--mp-ink)",
    cursor: "pointer", fontSize: "var(--font-size-sm)", textAlign: "left",
  },
  quickLabel: { fontWeight: 600 },
  quickSub: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  facts: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  factRow: { display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "var(--font-size-sm)" },
  factLabel: { color: "var(--mp-ink-2)" },
};
