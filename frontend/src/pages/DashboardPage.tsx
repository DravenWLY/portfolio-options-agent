import { useAccountContext } from "../context/useAccountContext";
import BrokerFreshnessBar from "../components/freshness/BrokerFreshnessBar";
import PortfolioWarningsPanel from "../components/freshness/PortfolioWarningsPanel";
import PortfolioSummaryCard from "../components/portfolio/PortfolioSummaryCard";
import PositionsTabs from "../components/positions/PositionsTabs";
import ReportHistoryPlaceholder from "../components/reports/ReportHistoryPlaceholder";

/**
 * DashboardPage — the main portfolio cockpit view.
 *
 * Panel order (reading top to bottom):
 *   1. BrokerFreshnessBar     — broker sync status, always visible
 *   2. PortfolioSummaryCard   — total values with timestamps
 *   3. PortfolioWarningsPanel — broker data warnings (hidden when clean)
 *   4. PositionsTabs          — cash / stocks / options
 *   5. MarketQuoteNotice      — permanent "not available" callout
 *   6. ReportHistoryPlaceholder — agentic report history
 *
 * Safety: no market quote data, no trade execution UI, no guaranteed-return
 * language anywhere in this file or its children.
 */
export default function DashboardPage() {
  const { selectedAccount } = useAccountContext();

  if (selectedAccount === null) {
    return <NoAccountState />;
  }

  return (
    <div style={styles.page}>
      <BrokerFreshnessBar />
      <PortfolioSummaryCard />
      <PortfolioWarningsPanel />
      <PositionsTabs />
      <MarketQuoteNotice />
      <ReportHistoryPlaceholder />
    </div>
  );
}

/* ── No-account state ──────────────────────────────────────────────────── */

function NoAccountState() {
  return (
    <div style={styles.noAccount} role="status" aria-live="polite">
      <span style={styles.noAccountIcon} aria-hidden="true">⬡</span>
      <p style={styles.noAccountTitle}>Select an account to view your portfolio</p>
      <p style={styles.noAccountBody}>
        Use the account selector in the top bar to choose a user and account.
        Your portfolio holdings, positions, and broker sync status will appear here.
      </p>
    </div>
  );
}

/* ── Market quote unavailable notice ──────────────────────────────────── */

/**
 * Permanent notice — market prices are not available in this version.
 * Not a toast. Not dismissible. Always rendered when an account is selected.
 */
function MarketQuoteNotice() {
  return (
    <aside
      style={styles.quoteNotice}
      role="note"
      aria-label="Market data availability"
    >
      <span style={styles.quoteIcon} aria-hidden="true">○</span>
      <div>
        <p style={styles.quoteTitle}>Market prices not available in this version</p>
        <p style={styles.quoteBody}>
          Position values shown are internal book values (cost basis) from your
          broker sync. Real-time or delayed market quotes will be added in a
          future phase. Do not rely on these figures as current market prices.
        </p>
      </div>
    </aside>
  );
}

/* ── Styles ────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-6)",
    maxWidth: 1200,
  },
  noAccount: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: 320,
    gap: "var(--space-4)",
    textAlign: "center",
    maxWidth: 480,
    margin: "var(--space-12) auto",
  },
  noAccountIcon: {
    fontSize: 40,
    color: "var(--color-text-muted)",
    lineHeight: 1,
  },
  noAccountTitle: {
    fontSize: "var(--font-size-lg)",
    fontWeight: 600,
    color: "var(--color-text-secondary)",
  },
  noAccountBody: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    lineHeight: 1.7,
  },
  quoteNotice: {
    backgroundColor: "var(--color-surface-2)",
    border: "1px solid var(--color-border)",
    borderLeft: "3px solid var(--color-unknown)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
    display: "flex",
    gap: "var(--space-4)",
    alignItems: "flex-start",
  },
  quoteIcon: {
    color: "var(--color-unknown)",
    fontSize: "var(--font-size-lg)",
    marginTop: 2,
    flexShrink: 0,
  },
  quoteTitle: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
    color: "var(--color-text-secondary)",
    marginBottom: "var(--space-1)",
  },
  quoteBody: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    lineHeight: 1.6,
  },
};
