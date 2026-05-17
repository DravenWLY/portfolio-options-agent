import { useCashBalance } from "../../hooks/usePositions";
import { useAccountContext } from "../../context/useAccountContext";
import Timestamp from "../shared/Timestamp";
import { LoadingSkeleton, ErrorState, EmptyState } from "../shared/StateViews";
import { type CashBalanceRead } from "../../types/api";

export default function CashPositionsView() {
  const { selectedAccount } = useAccountContext();
  const { data: cash, status, error, reload } = useCashBalance(
    selectedAccount?.id ?? null
  );
  const currency = selectedAccount?.base_currency ?? "USD";

  if (status === "loading") return <LoadingSkeleton rows={5} label="Loading cash balance…" />;
  if (status === "error") return <ErrorState message={error ?? "Unknown error"} onRetry={reload} />;
  if (status === "success" && cash === null) {
    return <EmptyState icon="○" title="No cash balance recorded" body="Cash data appears here after a broker sync or manual entry." />;
  }
  if (!cash) return null;

  return <CashDetail cash={cash} currency={currency} />;
}

function CashDetail({ cash, currency }: { cash: CashBalanceRead; currency: string }) {
  const fmt = (val: string) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
    }).format(parseFloat(val));

  const rows: { label: string; value: string; muted?: boolean }[] = [
    { label: "Total Cash", value: fmt(cash.total_cash) },
    { label: "Free Cash", value: fmt(cash.free_cash) },
    { label: "Reserved Collateral", value: fmt(cash.reserved_collateral_cash), muted: true },
    { label: "Premium Income Cash", value: fmt(cash.premium_income_cash), muted: true },
    { label: "DCA Cash", value: fmt(cash.dca_cash), muted: true },
  ];

  return (
    <div>
      <div style={styles.sourceRow}>
        <span style={styles.sourceLabel}>Source: {cash.source}{cash.source_ref ? ` · ${cash.source_ref}` : ""}</span>
        <FreshnessTag status={cash.data_freshness_status} />
        <Timestamp iso={cash.as_of} />
      </div>
      <table style={styles.table} aria-label="Cash balance breakdown">
        <thead>
          <tr>
            <th style={styles.th} scope="col">Field</th>
            <th style={{ ...styles.th, textAlign: "right" }} scope="col">Amount</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <td style={row.muted ? styles.tdMuted : styles.td}>{row.label}</td>
              <td style={{ ...styles.td, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{row.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FreshnessTag({ status }: { status: string }) {
  const map: Record<string, { label: string; color: string }> = {
    fresh:          { label: "Synced",   color: "var(--color-live)" },
    cached:         { label: "Cached",   color: "var(--color-stale)" },
    delayed:        { label: "Delayed",  color: "var(--color-stale)" },
    stale:          { label: "Stale",    color: "var(--color-stale)" },
    unknown:        { label: "Unknown",  color: "var(--color-unknown)" },
    error:          { label: "Error",    color: "var(--color-error)" },
    reauth_required:{ label: "Reauth ⚠", color: "var(--color-reauth)" },
  };
  const cfg = map[status] ?? { label: status, color: "var(--color-unknown)" };

  return (
    <span
      style={{ ...styles.tag, color: cfg.color, borderColor: cfg.color }}
      aria-label={`Data freshness: ${cfg.label}`}
    >
      {cfg.label}
    </span>
  );
}

const styles: Record<string, React.CSSProperties> = {
  sourceRow: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
    marginBottom: "var(--space-4)",
    flexWrap: "wrap",
  },
  sourceLabel: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
  },
  tag: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid",
    borderRadius: "var(--radius-sm)",
    fontWeight: 600,
    letterSpacing: "0.04em",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "var(--font-size-sm)",
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
  },
  td: {
    padding: "var(--space-2) var(--space-3)",
    color: "var(--color-text-primary)",
    borderBottom: "1px solid var(--color-border-subtle)",
  },
  tdMuted: {
    padding: "var(--space-2) var(--space-3)",
    color: "var(--color-text-muted)",
    borderBottom: "1px solid var(--color-border-subtle)",
  },
};
