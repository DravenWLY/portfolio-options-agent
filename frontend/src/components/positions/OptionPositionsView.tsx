import { useEffect, useState } from "react";
import { useOptionPositions } from "../../hooks/usePositions";
import { useAccountContext } from "../../context/useAccountContext";
import { apiClient } from "../../api/client";
import { LoadingSkeleton, ErrorState, EmptyState } from "../shared/StateViews";
import { type OptionPositionRead, type OptionContractRead } from "../../types/api";

/**
 * OptionPositionsView — displays open option positions from internal storage.
 *
 * Safety:
 * - No Greeks, no collateral calculations, no risk metrics — Phase 13.
 * - market_price / market_value shown only if present; otherwise "○ n/a".
 * - No trade execution controls. No option chain or screener.
 * - Long/short side clearly labeled.
 * - Position origin labeled (real/manual/csv).
 */
export default function OptionPositionsView() {
  const { selectedAccount } = useAccountContext();
  const { data: positions, status, error, reload } = useOptionPositions(
    selectedAccount?.id ?? null
  );
  const currency = selectedAccount?.base_currency ?? "USD";

  if (status === "loading") return <LoadingSkeleton rows={4} label="Loading option positions…" />;
  if (status === "error") return <ErrorState message={error ?? "Unknown error"} onRetry={reload} />;
  if (status === "success" && positions?.length === 0) {
    return (
      <EmptyState
        icon="⊙"
        title="No option positions"
        body="Open option positions appear here after a broker sync or manual entry. No trades are placed from this panel."
      />
    );
  }
  if (!positions) return null;

  return <OptionTable positions={positions} currency={currency} />;
}

/* ── Option table with lazy contract fetch ──────────────────────────────── */

function OptionTable({
  positions,
  currency,
}: {
  positions: OptionPositionRead[];
  currency: string;
}) {
  const [contracts, setContracts] = useState<Record<string, OptionContractRead>>({});

  // Fetch contracts for all unique contract IDs
  useEffect(() => {
    const ids = [...new Set(positions.map((p) => p.option_contract_id))];
    ids.forEach((id) => {
      if (contracts[id]) return;
      apiClient
        .get<OptionContractRead>(`/option-contracts/${id}`)
        .then((c) => setContracts((prev) => ({ ...prev, [id]: c })))
        .catch(() => {
          // contract fetch failure doesn't block position display
        });
    });
  }, [positions]); // eslint-disable-line react-hooks/exhaustive-deps

  const fmtMoney = (val: string | null) => {
    if (val === null) return null;
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
    }).format(parseFloat(val));
  };

  const fmtPrice = (val: string | null) => {
    if (val === null) return null;
    return parseFloat(val).toFixed(2);
  };

  const dteLabel = (expiry: string | undefined) => {
    if (!expiry) return "—";
    const days = Math.ceil(
      (new Date(expiry).getTime() - Date.now()) / 86400000
    );
    if (days < 0) return `exp ${Math.abs(days)}d ago`;
    return `${days}d`;
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={styles.table} aria-label="Option positions">
        <thead>
          <tr>
            {[
              "Side", "Underlying", "Type", "Strike", "Expiry", "DTE",
              "Qty", "Avg Price", "Book Value", "Freshness", "Status", "Origin",
            ].map((h) => (
              <th key={h} style={styles.th} scope="col">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {positions.map((pos) => {
            const c = contracts[pos.option_contract_id];
            return (
              <tr key={pos.id}>
                <td style={pos.position_side === "short" ? styles.tdShort : styles.tdLong}>
                  {pos.position_side.toUpperCase()}
                </td>
                <td style={styles.tdBold}>{c?.underlying_symbol ?? "—"}</td>
                <td style={styles.td}>{c?.option_type?.toUpperCase() ?? "—"}</td>
                <td style={{ ...styles.td, fontVariantNumeric: "tabular-nums" }}>
                  {c ? `$${parseFloat(c.strike).toFixed(2)}` : "—"}
                </td>
                <td style={styles.td}>{c?.expiration_date ?? "—"}</td>
                <td style={styles.tdMuted}>{dteLabel(c?.expiration_date)}</td>
                <td style={{ ...styles.td, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                  {parseFloat(pos.quantity).toFixed(0)}
                </td>
                <td style={{ ...styles.td, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                  {fmtPrice(pos.average_price) ?? <span style={styles.na}>—</span>}
                </td>
                <td style={{ ...styles.td, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                  {fmtMoney(pos.market_value) ?? (
                    <span style={styles.na} title="Market price not available">○ n/a</span>
                  )}
                </td>
                <td style={styles.td}>
                  <FreshnessChip status={pos.data_freshness_status} />
                </td>
                <td style={styles.tdMuted}>{pos.status}</td>
                <td style={styles.tdMuted}>{pos.source}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p style={styles.footnote}>
        ○ Book value reflects broker-reported data. Market prices, Greeks, and collateral calculations are not available in this version.
        <br />
        DTE = days to expiration (computed from expiry date, not market hours).
        No trades are placed from this panel.
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
    minWidth: 800,
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
    fontWeight: 600,
    color: "var(--color-text-primary)",
    borderBottom: "1px solid var(--color-border-subtle)",
    whiteSpace: "nowrap",
  },
  tdMuted: {
    padding: "var(--space-2) var(--space-3)",
    color: "var(--color-text-muted)",
    borderBottom: "1px solid var(--color-border-subtle)",
    whiteSpace: "nowrap",
  },
  tdLong: {
    padding: "var(--space-2) var(--space-3)",
    color: "var(--color-live)",
    fontWeight: 700,
    fontSize: "var(--font-size-xs)",
    letterSpacing: "0.06em",
    borderBottom: "1px solid var(--color-border-subtle)",
  },
  tdShort: {
    padding: "var(--space-2) var(--space-3)",
    color: "var(--color-stale)",
    fontWeight: 700,
    fontSize: "var(--font-size-xs)",
    letterSpacing: "0.06em",
    borderBottom: "1px solid var(--color-border-subtle)",
  },
  chip: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 5px",
    border: "1px solid",
    borderRadius: "var(--radius-sm)",
    fontWeight: 600,
  },
  na: {
    color: "var(--color-unknown)",
    fontSize: "var(--font-size-xs)",
  },
  footnote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    marginTop: "var(--space-3)",
    lineHeight: 1.6,
  },
};
