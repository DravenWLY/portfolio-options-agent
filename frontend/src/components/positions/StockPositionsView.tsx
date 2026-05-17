import { useStockPositions } from "../../hooks/usePositions";
import { useAccountContext } from "../../context/useAccountContext";
import Timestamp from "../shared/Timestamp";
import { LoadingSkeleton, ErrorState, EmptyState } from "../shared/StateViews";
import { type StockPositionRead } from "../../types/api";

/**
 * StockPositionsView — displays stock/ETF positions from internal storage.
 *
 * Safety:
 * - market_price/market_value shown only if present; otherwise "—" not zero.
 * - Labeled as "broker data" not "live market price".
 * - No trade execution controls.
 */
export default function StockPositionsView() {
  const { selectedAccount } = useAccountContext();
  const { data: positions, status, error, reload } = useStockPositions(
    selectedAccount?.id ?? null
  );
  const currency = selectedAccount?.base_currency ?? "USD";

  if (status === "loading") return <LoadingSkeleton rows={4} label="Loading stock positions…" />;
  if (status === "error") return <ErrorState message={error ?? "Unknown error"} onRetry={reload} />;
  if (status === "success" && positions?.length === 0) {
    return <EmptyState icon="⊞" title="No stock positions" body="Stock and ETF positions appear here after a broker sync or manual entry." />;
  }
  if (!positions) return null;

  return <StockTable positions={positions} currency={currency} />;
}

function StockTable({
  positions,
  currency,
}: {
  positions: StockPositionRead[];
  currency: string;
}) {
  const fmtMoney = (val: string | null) => {
    if (val === null) return null;
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
    }).format(parseFloat(val));
  };

  const fmtQty = (val: string) =>
    new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 }).format(
      parseFloat(val)
    );

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={styles.table} aria-label="Stock positions">
        <thead>
          <tr>
            {["Symbol", "Type", "Qty", "Cost Basis", "Book Value", "Freshness", "As of", "Source"].map(
              (h) => <th key={h} style={styles.th} scope="col">{h}</th>
            )}
          </tr>
        </thead>
        <tbody>
          {positions.map((pos) => (
            <tr key={pos.id}>
              <td style={styles.tdBold}>{pos.symbol}</td>
              <td style={styles.tdMuted}>{pos.asset_type}</td>
              <td style={{ ...styles.td, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                {fmtQty(pos.quantity)}
              </td>
              <td style={{ ...styles.td, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                {fmtMoney(pos.cost_basis) ?? <span style={styles.unknown}>—</span>}
              </td>
              <td style={{ ...styles.td, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                {fmtMoney(pos.market_value) ?? (
                  <span style={styles.unknown} title="Market price not available">○ n/a</span>
                )}
              </td>
              <td style={styles.td}>
                <FreshnessChip status={pos.data_freshness_status} />
              </td>
              <td style={styles.tdMuted}>
                <Timestamp iso={pos.as_of} prefix="" />
              </td>
              <td style={styles.tdMuted}>{pos.source}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={styles.footnote}>
        ○ Book value reflects broker-reported data. Market prices not available in this version.
      </p>
    </div>
  );
}

function FreshnessChip({ status }: { status: string }) {
  const map: Record<string, { label: string; color: string }> = {
    fresh:          { label: "Synced",  color: "var(--color-live)" },
    cached:         { label: "Cached",  color: "var(--color-stale)" },
    delayed:        { label: "Delayed", color: "var(--color-stale)" },
    stale:          { label: "Stale",   color: "var(--color-stale)" },
    unknown:        { label: "Unknown", color: "var(--color-unknown)" },
    error:          { label: "Error",   color: "var(--color-error)" },
    reauth_required:{ label: "Reauth",  color: "var(--color-reauth)" },
  };
  const cfg = map[status] ?? { label: status, color: "var(--color-unknown)" };
  return (
    <span style={{ ...styles.chip, color: cfg.color, borderColor: cfg.color }}>
      {cfg.label}
    </span>
  );
}

const styles: Record<string, React.CSSProperties> = {
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "var(--font-size-sm)",
    minWidth: 640,
  },
  th: {
    padding: "var(--space-2) var(--space-3)",
    textAlign: "left",
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    borderBottom: "1px solid var(--color-border)",
    whiteSpace: "nowrap",
  },
  td: {
    padding: "var(--space-2) var(--space-3)",
    color: "var(--color-text-primary)",
    borderBottom: "1px solid var(--color-border-subtle)",
    whiteSpace: "nowrap",
  },
  tdBold: {
    padding: "var(--space-2) var(--space-3)",
    color: "var(--color-text-primary)",
    fontWeight: 600,
    borderBottom: "1px solid var(--color-border-subtle)",
    whiteSpace: "nowrap",
  },
  tdMuted: {
    padding: "var(--space-2) var(--space-3)",
    color: "var(--color-text-muted)",
    borderBottom: "1px solid var(--color-border-subtle)",
    whiteSpace: "nowrap",
  },
  chip: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 5px",
    border: "1px solid",
    borderRadius: "var(--radius-sm)",
    fontWeight: 600,
  },
  unknown: {
    color: "var(--color-unknown)",
    fontSize: "var(--font-size-xs)",
  },
  footnote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    marginTop: "var(--space-3)",
  },
};
