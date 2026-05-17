/**
 * SafetyNoticePanel — always-visible, non-dismissible safety banner.
 *
 * Required copy for every broker connection surface. Must not be removed
 * or hidden by any UI state.
 */
export default function SafetyNoticePanel() {
  return (
    <aside style={styles.panel} role="note" aria-label="Broker connection safety information">
      <div style={styles.header}>
        <span style={styles.icon} aria-hidden="true">⚠</span>
        <span style={styles.title}>Read-only broker sync — no trades are placed</span>
      </div>
      <ul style={styles.list}>
        <li>
          <strong>Do not enter Fidelity credentials into this app.</strong>{" "}
          Use the secure provider portal that opens in a new tab. Your credentials stay with the broker — never with this app.
        </li>
        <li>
          Broker holdings may be stale. Verify holdings in Fidelity directly before taking any manual action.
        </li>
        <li>
          Market quotes are not available yet. Position values shown are broker snapshot data (cost basis / last sync), not current market prices.
        </li>
        <li>
          This is a decision-support tool only. No trades, orders, or automated actions are placed on your behalf.
        </li>
      </ul>
    </aside>
  );
}

const styles: Record<string, React.CSSProperties> = {
  panel: {
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-stale)",
    borderLeft: "4px solid var(--color-stale)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
  },
  icon: {
    color: "var(--color-stale)",
    fontSize: "var(--font-size-base)",
    flexShrink: 0,
  },
  title: {
    fontWeight: 700,
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-secondary)",
    letterSpacing: "0.02em",
  },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    paddingLeft: "var(--space-5)",
    margin: 0,
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    lineHeight: 1.6,
  },
};
