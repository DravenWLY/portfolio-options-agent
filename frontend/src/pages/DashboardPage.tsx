import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Badge, DemoChip, FreshnessDial, KV, MpIcon, PageHeader, Panel, Pill, SafetyStrip, Stat, type MpTone } from "../components/shared/mp";
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
import EconomicCalendarPanel from "../components/economic-calendar/EconomicCalendarPanel";
import MarketMoodCard from "../components/market-context/MarketMoodCard";
import SkyframeSurface from "../components/shared/SkyframeSurface";

/**
 * DashboardPage — compact review-readiness cockpit (P20D-T2 → T5).
 *
 * Backend-backed via reviewed P20B / P20D contracts:
 *   GET /api/users/{uid}/trade-reviews
 *   GET /api/users/{uid}/risk-alerts
 *   GET /api/users/{uid}/readiness
 *   GET /api/users/{uid}/dashboard-account-summary  (P20D-T1 refined)
 *   GET /api/users/{uid}/portfolio-contexts
 *
 * P20D-T5 Product B pressure-test cleanup (Stock Rover persona, Codex A
 * 2026-05-29 decisions — complement, don't replace a research terminal):
 *   - Promote the backend-owned plain-English readiness verdict
 *     (recommended_user_action_label) to the first meaningful answer.
 *   - Move agent-provider readiness off the first viewport into a thin
 *     lower-priority operational status row, so it no longer competes with
 *     broker snapshot and market quote freshness.
 *   - Never render plausible synthetic dollar amounts: in synthetic_demo,
 *     the account headline shows an unmistakable placeholder and monetary
 *     breakdown rows are suppressed (counts/shape/cash-state remain).
 *   - Remove the dead flow-specific quick-review presets that only navigated
 *     to a blank Trade Review form; the header action remains the single,
 *     honest start-review entry point.
 *
 * First-viewport hierarchy: readiness verdict → data-freshness tiles →
 * account summary → portfolio context → economic awareness; agent-provider
 * status and synthetic recent/risk panels are demoted below.
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
      <SkyframeSurface className="mp-surface" maxWidth={1280}>
        <PageHeader
          eyebrow="Workspace · overview"
          title="Dashboard"
          sub="Select a user from the developer account selector to load the dashboard."
        />
        <EmptyState title="No user selected" body="Select a user from the developer account selector to load dashboard data." />
        <DashboardSafetyStrip />
      </SkyframeSurface>
    );
  }

  return (
    <SkyframeSurface className="mp-surface" maxWidth={1280}>
      <PageHeader
        eyebrow="Workspace · overview"
        title="Dashboard"
        sub="Review readiness, account summary, and portfolio context. Manual decision support only."
        right={
          <button style={styles.primaryBtn} type="button" onClick={() => nav("/trade-review")}>
            New trade review →
          </button>
        }
      />

      {/* ── 1. Readiness verdict — first meaningful answer (P20D-T5) ──── */}
      <ReadinessVerdict slot={state.readiness} onRetry={loadAll} />

      {/* ── 2. Supporting data freshness — broker + market only; agent
              provider moved off the first viewport (P20D-T5) ─────────── */}
      <ReadinessStrip slot={state.readiness} />

      {/* ── Main body ────────────────────────────────────────────────── */}
      <section style={styles.body}>
        <div style={styles.colLeft}>
          {/* Account summary — primary: reviewed P20D-T1 contract */}
          <AccountSummaryPanel slot={state.summary} onRetry={loadAll} />

          {/* Portfolio context summary */}
          <PortfolioContextSummaryPanel slot={state.contexts} onRetry={loadAll} />

          {/* Economic awareness — self-fetching, failures stay local (P24A-T5) */}
          <EconomicCalendarPanel />

          {/* Market Mood — secondary market-context card, self-fetching (P26A-T2) */}
          <MarketMoodCard />
        </div>

        <div style={styles.colRight}>
          {/* Recent trade reviews — collapsed when synthetic demo */}
          <RecentReviewsPanel slot={state.reviews} onRetry={loadAll} />

          {/* Risk alerts — collapsed when synthetic demo */}
          <RiskAlertsPanel slot={state.alerts} onRetry={loadAll} />
        </div>
      </section>

      {/* Thin operational status row — agent provider, deliberately off the
          first viewport so it does not compete with broker/market freshness. */}
      <AgentProviderStatusRow slot={state.readiness} />

      <DashboardSafetyStrip />
    </SkyframeSurface>
  );
}

/* ── Readiness verdict (hero answer) ───────────────────────────────────── */

function ReadinessVerdict({
  slot,
  onRetry,
}: {
  slot: DashboardState["readiness"];
  onRetry: () => void;
}) {
  if (slot.status === "loading") {
    return <LoadingSkeleton rows={2} label="Loading review readiness…" />;
  }
  if (slot.status === "error") {
    return <ErrorState message={slot.error ?? "Failed to load readiness."} onRetry={onRetry} />;
  }
  if (!slot.data) return null;

  const r = slot.data;
  const isDemoMode = r.data_mode === "synthetic_demo";

  return (
    <section style={styles.verdict}>
      <div style={styles.verdictTop}>
        <span style={styles.verdictEyebrow}>Review readiness</span>
        {isDemoMode && <DemoChip tight />}
      </div>
      {/* Primary user-facing answer — backend-owned plain-English verdict. */}
      <div style={styles.verdictAnswerRow}>
        <MpIcon name="review" size={18} style={{ color: "var(--mp-accent)", flexShrink: 0, marginTop: 2 }} />
        <span style={styles.verdictAnswer}>{readinessHeadline(r)}</span>
      </div>
      {/* Quiet secondary line — what affects review quality, in plain copy. */}
      <p style={styles.verdictSub}>{readinessQualityHint(r)}</p>
    </section>
  );
}

/* Plain-English headline derived from the backend overall_review_mode. */
function readinessHeadline(r: ReviewReadinessRead): string {
  switch (r.overall_review_mode) {
    case "normal_review":
      return "Reviews are available.";
    case "analysis_only":
      return "Reviews are available with data limitations.";
    case "manual_confirmation_required":
      return "Reviews need manual confirmation before they can run.";
    case "blocked":
      return "Reviews are currently blocked.";
    default:
      // Backend verdict — kept as a safe fallback if a new mode is introduced.
      return r.recommended_user_action_label;
  }
}

/* Quiet secondary line — what limits review quality. Stays generic and
 * user-facing; backend display labels are not exposed as internal enum text. */
function readinessQualityHint(r: ReviewReadinessRead): string {
  const issues: string[] = [];
  if (r.broker_snapshot.status !== "fresh") issues.push("refresh broker snapshot");
  if (r.market_quotes.status !== "fresh") issues.push("refresh market data");
  if (issues.length === 0) {
    return "Broker snapshot and market data are fresh.";
  }
  if (issues.length === 1) {
    return `Connect a portfolio and ${issues[0]} for higher-confidence context.`;
  }
  return "Connect a portfolio and refresh broker / market data for higher-confidence context.";
}

/* ── Agent provider operational status (off first viewport) ────────────── */

function AgentProviderStatusRow({ slot }: { slot: DashboardState["readiness"] }) {
  if (slot.status !== "success" || !slot.data) return null;
  const ap = slot.data.agent_provider;
  return (
    <div style={styles.opStatusRow}>
      <span style={styles.opStatusLabel}>Agent provider</span>
      <span style={styles.opStatusValue}>{ap.display_label}</span>
      <Badge tone={agentProviderTone(ap.provider_status)} dot>{ap.provider_mode}</Badge>
    </div>
  );
}

/* ── Readiness strip ────────────────────────────────────────────────────── */

function ReadinessStrip({ slot }: { slot: DashboardState["readiness"] }) {
  // Loading/error are owned by the verdict above; the strip only adds the
  // supporting freshness tiles on success.
  if (slot.status !== "success" || !slot.data) return null;

  const r = slot.data;

  return (
    <section style={styles.readinessSection}>
      <div style={styles.sectionLabelRow}>
        <span style={styles.sectionLabel}>Data freshness</span>
      </div>

      {/* Broker snapshot and market quote freshness are kept distinct. */}
      <div style={styles.readinessGrid}>
        <ReadinessTile
          title="Broker snapshot"
          subtitle={r.broker_snapshot.display_label}
          status={r.broker_snapshot.status}
          tone={readinessTone(r.broker_snapshot.status, r.broker_snapshot.is_blocking)}
          asOf={r.broker_snapshot.as_of_label ?? undefined}
        />
        <ReadinessTile
          title="Market quotes"
          subtitle={r.market_quotes.display_label}
          status={r.market_quotes.status}
          tone={readinessTone(r.market_quotes.status, r.market_quotes.is_blocking)}
          asOf={r.market_quotes.as_of_label ?? undefined}
        />
      </div>
    </section>
  );
}

/* ── Account summary panel (body column) ───────────────────────────────── */

function AccountSummaryPanel({ slot, onRetry }: { slot: DashboardState["summary"]; onRetry: () => void }) {
  if (slot.status === "loading") {
    return (
      <Panel title="Account summary" tag="summary">
        <LoadingSkeleton rows={4} label="Loading account summary…" />
      </Panel>
    );
  }
  if (slot.status === "error") {
    return (
      <Panel title="Account summary" tag="summary">
        <ErrorState message={slot.error ?? "Failed to load account summary."} onRetry={onRetry} />
      </Panel>
    );
  }
  if (!slot.data) return null;

  const s = slot.data;
  const isDemoMode = s.data_mode === "synthetic_demo";
  const isAmountsHidden = s.privacy_display_mode === "amounts_hidden";
  // Never present plausible synthetic dollars as if they might be real (D2).
  // Suppress monetary labels for synthetic demo or privacy-hidden modes; keep
  // only qualitative shape / counts / cash-state, which are safe context.
  const hideAmounts = isDemoMode || isAmountsHidden;

  return (
    <Panel
      title="Account summary"
      tag={s.display_scope.replace(/_/g, " ")}
      right={isDemoMode ? <DemoChip /> : undefined}
    >
      {isAmountsHidden && !isDemoMode && (
        <div style={styles.privacyNotice}>
          <Badge tone="mute" dot>amounts hidden</Badge>
        </div>
      )}

      {/* Headline — backend label verbatim for real source; an unmistakable
          placeholder for synthetic demo so fake dollars never look real. */}
      {!hideAmounts && s.total_value_label ? (
        <Stat label="Total value" value={s.total_value_label} sub={s.source_label} />
      ) : isDemoMode ? (
        <div style={styles.placeholderBlock}>
          <span style={styles.placeholderValue}>Connect a portfolio to see your value.</span>
          <span style={styles.placeholderSub}>{s.source_label}</span>
        </div>
      ) : (
        <KV compact rows={[["Source", s.source_label]]} />
      )}

      {/* Position context — backend display labels verbatim. Monetary rows are
          suppressed when amounts are hidden/synthetic; safe counts, portfolio
          shape, and qualitative cash state remain. */}
      <div style={styles.kvSection}>
        <div style={styles.kvSectionHeader}>Position breakdown</div>
        <KV rows={hideAmounts ? [
          ["Cash", s.cash_state_label],
          ["Portfolio shape", s.portfolio_shape_label],
          ["Positions", s.position_count_label],
        ] : [
          ["Cash", s.cash_label ?? s.cash_state_label],
          ["Stock/ETF exposure", s.stock_etf_exposure_label ?? s.stock_exposure_label ?? "—"],
          ["Options exposure", s.options_exposure_label ?? s.option_exposure_label ?? "—"],
          ["Collateral usage", s.collateral_usage_label ?? "—"],
          ["Portfolio shape", s.portfolio_shape_label],
          ["Positions", s.position_count_label],
        ]} />
      </div>

      {/* Data provenance — valuation basis, market data, privacy */}
      <div style={styles.kvSection}>
        <div style={styles.kvSectionHeader}>Data provenance</div>
        <KV compact rows={[
          ["Valuation basis", s.valuation_basis.replace(/_/g, " ")],
          ["Market data", s.market_data_mode],
          ["Privacy", s.privacy_display_mode.replace(/_/g, " ")],
        ]} />
      </div>

      {s.market_data_unavailable && (
        <p style={styles.acctNote}>Market data unavailable.</p>
      )}
      {/* Raw backend caveat codes (e.g. summary_demo_only, broker_snapshot_stale)
          are internal labels — they no longer appear in the visible Dashboard.
          The qualitative cash state, portfolio shape, and "amounts hidden" /
          demo signaling above already convey what the user needs to see. */}
    </Panel>
  );
}

function ReadinessTile({
  title, subtitle, status, tone, asOf,
}: {
  title: string;
  subtitle: string;
  status: string;
  tone: MpTone;
  asOf?: string;
}) {
  return (
    <div style={{ ...styles.readinessCard, borderLeftColor: `var(--mp-${tone === "mute" ? "mute" : tone})` }}>
      <div style={styles.readCardHeader}>
        <span style={styles.readEyebrow}>{title}</span>
        <Badge tone={tone} dot>{status}</Badge>
      </div>
      <div style={styles.readSub}>{subtitle}</div>
      {asOf && <FreshnessDial tone={tone} ago={status === "fresh" ? "ok" : "—"} label={asOf} />}
    </div>
  );
}

/* ── Recent trade reviews ───────────────────────────────────────────────── */

function RecentReviewsPanel({ slot, onRetry }: { slot: DashboardState["reviews"]; onRetry: () => void }) {
  const isDemoMode = slot.data?.data_mode === "synthetic_demo";

  // Collapse to compact note when synthetic demo — avoids presenting fake history
  if (isDemoMode && slot.status === "success") {
    return (
      <Panel title="Recent trade reviews" tag="history">
        <div style={styles.collapsedRow}>
          <MpIcon name="info" size={14} style={{ color: "var(--mp-mute)", marginTop: 1 }} />
          <p style={styles.collapsedNote}>
            No review history yet. Start a new trade review or connect a real portfolio context to generate review history.
          </p>
        </div>
      </Panel>
    );
  }

  return (
    <Panel title="Recent trade reviews" tag="last 7 days">
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

  // Collapse to compact note when synthetic demo — avoids presenting fake urgency
  if (isDemoMode && slot.status === "success") {
    return (
      <Panel title="Risk alerts" tag="deterministic">
        <div style={styles.collapsedRow}>
          <MpIcon name="shield" size={14} style={{ color: "var(--mp-mute)", marginTop: 1 }} />
          <p style={styles.collapsedNote}>
            No real risk alerts. Deterministic risk rules activate when a real portfolio context is available.
          </p>
        </div>
      </Panel>
    );
  }

  return (
    <Panel title="Risk alerts" tag="deterministic">
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
  return (
    <Panel title="Portfolio context" tag="summary" accent>
      {slot.status === "loading" && <LoadingSkeleton rows={3} label="Loading contexts…" />}
      {slot.status === "error" && <ErrorState message={slot.error ?? "Failed to load portfolio contexts."} onRetry={onRetry} />}
      {slot.status === "success" && slot.data && slot.data.items.length === 0 && (
        <KV rows={[
          ["Available contexts", "0"],
          ["Snapshot as of", "—"],
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
  primaryBtn: {
    fontSize: "var(--font-size-sm)", fontWeight: 600, padding: "8px 16px",
    backgroundColor: "var(--mp-accent)", color: "var(--mp-card)",
    border: "1px solid var(--mp-accent)", borderRadius: "var(--radius-sm)", cursor: "pointer",
    letterSpacing: "0.01em",
  },

  /* ── Readiness verdict (hero answer, P20D-T5) ─────────────────────────── */
  verdict: {
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
    padding: "var(--space-4) var(--space-5)",
    backgroundColor: "var(--mp-accent-soft)", border: "1px solid var(--mp-accent-line)",
    borderRadius: "var(--radius-md)",
  },
  verdictTop: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    gap: "var(--space-3)", flexWrap: "wrap",
  },
  verdictEyebrow: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600,
  },
  verdictAnswerRow: { display: "flex", alignItems: "flex-start", gap: "var(--space-2)", minWidth: 0 },
  verdictAnswer: {
    fontSize: "var(--font-size-lg)", fontWeight: 600, color: "var(--mp-ink)", lineHeight: 1.35,
  },
  verdictSub: {
    margin: 0, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.5,
  },

  /* ── Thin operational status row (agent provider, off first viewport) ─── */
  opStatusRow: {
    display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap",
    padding: "var(--space-2) var(--space-3)",
    border: "1px solid var(--mp-rule)", borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-card)",
  },
  opStatusLabel: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600,
  },
  opStatusValue: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)", marginRight: "auto",
  },

  /* ── Synthetic placeholder (no plausible fake dollars) ────────────────── */
  placeholderBlock: { display: "flex", flexDirection: "column", gap: 2 },
  placeholderValue: { fontSize: "var(--font-size-md)", fontWeight: 600, color: "var(--mp-ink-2)", lineHeight: 1.3 },
  placeholderSub: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },

  /* ── Readiness section ───────────────────────────────────────────────── */
  readinessSection: {
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  sectionLabelRow: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    gap: "var(--space-3)",
  },
  sectionLabel: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600,
  },
  readinessGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "var(--space-3)",
    minWidth: 0,
  },
  readinessCard: {
    backgroundColor: "var(--mp-card)", border: "1px solid var(--mp-rule)",
    borderLeft: "2px solid var(--mp-mute)", borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-4)", display: "flex", flexDirection: "column", gap: 6,
  },
  readCardHeader: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    gap: "var(--space-2)",
  },
  readEyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 },
  readSub: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.4 },

  /* ── Body columns ────────────────────────────────────────────────────── */
  body: {
    display: "grid",
    gridTemplateColumns: "1.2fr 1fr",
    gap: "var(--space-5)",
    minWidth: 0,
  },
  colLeft: { display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0 },
  colRight: { display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0 },

  /* ── Account summary ─────────────────────────────────────────────────── */
  acctNote: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.5, margin: 0 },
  kvSection: { paddingTop: "var(--space-3)", borderTop: "1px solid var(--mp-rule)" },
  kvSectionHeader: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600,
    marginBottom: "var(--space-2)",
  },
  privacyNotice: { marginBottom: "var(--space-2)" },

  /* ── Tables and alerts ───────────────────────────────────────────────── */
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

  /* ── Collapsed demo panels ───────────────────────────────────────────── */
  collapsedRow: { display: "flex", gap: "var(--space-2)", alignItems: "flex-start" },
  collapsedNote: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", lineHeight: 1.5, margin: 0 },
};
