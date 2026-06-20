import MarketDataStatusPanel from "../components/marketdata/MarketDataStatusPanel";
import SkyframeSurface from "../components/shared/SkyframeSurface";

/**
 * MarketDataPage — Phase 12 thin market-data status slice.
 *
 * Route: /market-data
 *
 * Safety:
 *  - No real market-data provider is connected; manual/mock contract only.
 *  - Market-quote freshness (scope="market_quote") is shown separately from
 *    broker portfolio sync freshness (which lives on the Dashboard/Broker pages).
 *  - No live/intraday implication, no guaranteed-return language, no option
 *    chain/screener UI, no trade-execution UI.
 */
export default function MarketDataPage() {
  return (
    <SkyframeSurface className="mp-surface" maxWidth={900}>
      <div style={styles.pageHeader}>
        <h1 style={styles.pageTitle}>Market Data</h1>
        <p style={styles.pageSubtitle}>
          Quote availability and freshness — manual/mock inputs only, no provider connected.
        </p>
      </div>

      <aside style={styles.separationNotice} role="note" aria-label="Freshness scope separation">
        <span style={styles.noticeIcon} aria-hidden="true">⊘</span>
        <div>
          <p style={styles.noticeTitle}>Market quotes are separate from broker sync</p>
          <p style={styles.noticeBody}>
            Broker holdings and cash come from broker sync (see Dashboard / Broker).
            Market quotes are a different source with their own freshness scope
            (<code>market_quote</code>) and are not yet connected to a real provider.
          </p>
        </div>
      </aside>

      <MarketDataStatusPanel />

      <aside style={styles.footerNotice} role="note" aria-label="Market data limitations">
        <p style={styles.footerText}>
          Phase 12 provides the market-data contract only. Quote values shown
          anywhere in the app are manual/mock inputs for analysis — do not treat
          them as live market pricing or as a basis for guaranteed outcomes.
          No trades, orders, or automated actions are performed.
        </p>
      </aside>
    </SkyframeSurface>
  );
}

const styles: Record<string, React.CSSProperties> = {
  pageHeader: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
  },
  pageTitle: {
    fontSize: "var(--font-size-xl)",
    fontWeight: 700,
    color: "var(--color-text-primary)",
    margin: 0,
    letterSpacing: "-0.02em",
  },
  pageSubtitle: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink-2)",
    margin: 0,
  },
  separationNotice: {
    backgroundColor: "var(--color-surface-2)",
    border: "1px solid var(--color-border)",
    borderLeft: "3px solid var(--color-unknown)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
    display: "flex",
    gap: "var(--space-4)",
    alignItems: "flex-start",
  },
  noticeIcon: {
    color: "var(--color-unknown)",
    fontSize: "var(--font-size-lg)",
    marginTop: 2,
    flexShrink: 0,
  },
  noticeTitle: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
    color: "var(--color-text-secondary)",
    margin: 0,
    marginBottom: "var(--space-1)",
  },
  noticeBody: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink-2)",
    lineHeight: 1.6,
    margin: 0,
  },
  footerNotice: {
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-border-subtle)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
  },
  footerText: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-ink-2)",
    lineHeight: 1.6,
    margin: 0,
  },
};
