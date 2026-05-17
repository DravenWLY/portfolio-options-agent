import { useAccountContext } from "../../context/useAccountContext";
import { usePortfolioSummary } from "../../hooks/usePortfolioSummary";
import { type PortfolioWarningRead } from "../../types/api";

/**
 * PortfolioWarningsPanel — surfaces broker_data_warnings from the portfolio summary.
 *
 * Returns null when there are no warnings — invisible when clean.
 * Severity levels: info / warning / violation / blocker.
 * Each warning shows icon + text so removal of color still conveys meaning.
 *
 * Safety: copy is factual. No trade instructions. No guaranteed-return language.
 */
export default function PortfolioWarningsPanel() {
  const { selectedAccount } = useAccountContext();
  const { summary, status } = usePortfolioSummary(selectedAccount?.id ?? null);

  if (!selectedAccount || status !== "success" || !summary) return null;

  const warnings = summary.broker_data_warnings;
  if (warnings.length === 0) return null;

  return (
    <section aria-label="Portfolio warnings" style={styles.panel}>
      <p style={styles.heading}>
        <span aria-hidden="true">◈</span> Portfolio Warnings · broker data
      </p>
      <ul style={styles.list} role="list">
        {warnings.map((w, i) => (
          <WarningItem key={i} warning={w} />
        ))}
      </ul>
    </section>
  );
}

function WarningItem({ warning }: { warning: PortfolioWarningRead }) {
  const cfg = severityConfig(warning.severity);

  return (
    <li style={{ ...styles.item, borderColor: cfg.borderColor }}>
      <span style={{ ...styles.badge, backgroundColor: cfg.bg, color: cfg.color }}>
        {cfg.icon} {warning.severity.toUpperCase()}
      </span>
      <span style={styles.code}>{warning.code}</span>
      <span style={styles.message}>{warning.message}</span>
      <span style={styles.meta}>
        {warning.source} · {warning.freshness_status}
      </span>
    </li>
  );
}

function severityConfig(severity: string): {
  icon: string;
  color: string;
  bg: string;
  borderColor: string;
} {
  switch (severity) {
    case "blocker":
      return { icon: "⬛", color: "var(--color-error)",   bg: "var(--color-error-bg)",   borderColor: "var(--color-error)" };
    case "violation":
      return { icon: "▲",  color: "var(--color-error)",   bg: "var(--color-error-bg)",   borderColor: "var(--color-error)" };
    case "warning":
      return { icon: "◑",  color: "var(--color-stale)",   bg: "var(--color-stale-bg)",   borderColor: "var(--color-stale)" };
    case "info":
    default:
      return { icon: "○",  color: "var(--color-unknown)", bg: "var(--color-unknown-bg)", borderColor: "var(--color-border)" };
  }
}

const styles: Record<string, React.CSSProperties> = {
  panel: {
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
  },
  heading: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    color: "var(--color-text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    marginBottom: "var(--space-3)",
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
  },
  list: {
    listStyle: "none",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
  },
  item: {
    display: "flex",
    alignItems: "baseline",
    gap: "var(--space-3)",
    padding: "var(--space-2) var(--space-3)",
    borderLeft: "3px solid",
    borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
    flexWrap: "wrap",
    backgroundColor: "var(--color-surface-2)",
  },
  badge: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    padding: "1px 6px",
    borderRadius: "var(--radius-sm)",
    whiteSpace: "nowrap",
    flexShrink: 0,
  },
  code: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    fontWeight: 600,
    whiteSpace: "nowrap",
    flexShrink: 0,
  },
  message: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-secondary)",
    flex: 1,
    minWidth: 200,
  },
  meta: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    whiteSpace: "nowrap",
    flexShrink: 0,
  },
};
