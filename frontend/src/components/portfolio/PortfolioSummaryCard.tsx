import { useAccountContext } from "../../context/useAccountContext";
import { usePortfolioSummary } from "../../hooks/usePortfolioSummary";
import SectionCard from "../shared/SectionCard";
import Timestamp from "../shared/Timestamp";
import { LoadingSkeleton, ErrorState } from "../shared/StateViews";
import { type PortfolioSummaryRead } from "../../types/api";

/**
 * PortfolioSummaryCard — displays the portfolio summary from the backend.
 *
 * Safety rules:
 * - Values labeled as "book value" / "internal value" — NOT "market value".
 * - Timestamps shown per data type (cash / stock / option), never merged.
 * - Market quote data explicitly shown as "not available".
 * - No trade execution controls.
 */
export default function PortfolioSummaryCard() {
  const { selectedAccount } = useAccountContext();
  const { summary, status, error, reload } = usePortfolioSummary(
    selectedAccount?.id ?? null
  );

  const headerRight = summary ? (
    <Timestamp iso={summary.as_of} prefix="Snapshot" />
  ) : null;

  return (
    <SectionCard id="portfolio-summary" label="Portfolio Summary" headerRight={headerRight}>
      {status === "loading" && <LoadingSkeleton rows={4} label="Loading portfolio summary…" />}
      {status === "error" && (
        <ErrorState message={error ?? "Unknown error"} onRetry={reload} />
      )}
      {status === "success" && summary && (
        <SummaryContent summary={summary} currency={selectedAccount?.base_currency ?? "USD"} />
      )}
    </SectionCard>
  );
}

/* ── Summary content ────────────────────────────────────────────────────── */

function SummaryContent({
  summary,
  currency,
}: {
  summary: PortfolioSummaryRead;
  currency: string;
}) {
  const fmt = (val: string) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
    }).format(parseFloat(val));

  return (
    <div style={styles.grid}>
      {/* Internal value — book only, never called "market value" */}
      <ValueTile
        label="Total Internal Value"
        sublabel="book value · not market price"
        value={fmt(summary.total_internal_value)}
        as_of={summary.latest_snapshot_as_of}
        highlight
      />

      <ValueTile
        label="Cash"
        sublabel={`source: ${summary.data_sources.join(", ") || "unknown"}`}
        value={fmt(summary.total_cash)}
        as_of={summary.cash_as_of}
      />

      <ValueTile
        label="Stock Book Value"
        sublabel={`${summary.stock_position_count} position${summary.stock_position_count !== 1 ? "s" : ""} · book only`}
        value={fmt(summary.stock_market_value)}
        as_of={summary.stock_positions_as_of}
        marketNote
      />

      <ValueTile
        label="Option Book Value"
        sublabel={`${summary.option_position_count} position${summary.option_position_count !== 1 ? "s" : ""} · ${summary.long_option_position_count} long / ${summary.short_option_position_count} short`}
        value={fmt(summary.option_market_value)}
        as_of={summary.option_positions_as_of}
        marketNote
      />
    </div>
  );
}

/* ── Value tile ─────────────────────────────────────────────────────────── */

function ValueTile({
  label,
  sublabel,
  value,
  as_of,
  highlight = false,
  marketNote = false,
}: {
  label: string;
  sublabel: string;
  value: string;
  as_of: string | null;
  highlight?: boolean;
  marketNote?: boolean;
}) {
  return (
    <div style={{ ...styles.tile, ...(highlight ? styles.tileHighlight : {}) }}>
      <p style={styles.tileLabel}>{label}</p>
      <p style={styles.tileValue} className="tabular-nums">{value}</p>
      <p style={styles.tileSublabel}>{sublabel}</p>
      <Timestamp iso={as_of} />
      {marketNote && (
        <p style={styles.tileMarketNote}>
          ○ market price not available
        </p>
      )}
    </div>
  );
}

/* ── Styles ─────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "var(--space-4)",
  },
  tile: {
    backgroundColor: "var(--color-surface-2)",
    border: "1px solid var(--color-border-subtle)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-5)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
  },
  tileHighlight: {
    borderColor: "var(--color-accent)",
    backgroundColor: "var(--color-accent-dim)",
  },
  tileLabel: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 600,
    color: "var(--color-text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.07em",
  },
  tileValue: {
    fontSize: "var(--font-size-xl)",
    fontWeight: 600,
    color: "var(--color-text-primary)",
    letterSpacing: "-0.01em",
    margin: "var(--space-1) 0",
  },
  tileSublabel: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
  },
  tileMarketNote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-unknown)",
    marginTop: "var(--space-1)",
  },
};
