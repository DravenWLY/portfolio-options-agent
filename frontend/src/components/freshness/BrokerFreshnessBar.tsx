import { useAccountContext } from "../../context/useAccountContext";
import { usePortfolioSummary } from "../../hooks/usePortfolioSummary";
import Timestamp from "../shared/Timestamp";

/**
 * BrokerFreshnessBar — fixed-top broker sync status strip.
 *
 * Design rules:
 * - Always rendered when an account is selected. Never dismissible while stale.
 * - Labeled explicitly as BROKER SYNC freshness — never market quote freshness.
 * - Four distinct states: fresh/live, stale/cached/delayed, unknown, error/reauth.
 * - Uses icon + text + color — not color alone (accessibility).
 *
 * Phase 11 note: driven by portfolio summary data_freshness_statuses.
 * Per-broker-account freshness detail will be added in a later phase after
 * broker sync is fully active.
 */
export default function BrokerFreshnessBar() {
  const { selectedAccount } = useAccountContext();
  const { summary, status } = usePortfolioSummary(selectedAccount?.id ?? null);

  if (!selectedAccount) return null;

  const freshness = deriveFreshness(summary?.data_freshness_statuses ?? [], status);

  return (
    <div
      style={{ ...styles.bar, borderColor: freshness.borderColor }}
      role="status"
      aria-label={`Broker sync status: ${freshness.label}`}
      aria-live="polite"
    >
      <div style={styles.left}>
        <span style={{ ...styles.icon, color: freshness.color }} aria-hidden="true">
          {freshness.icon}
        </span>
        <span style={styles.scopeLabel}>BROKER SYNC</span>
        <span style={{ ...styles.statusLabel, color: freshness.color }}>
          {freshness.label}
        </span>
        {freshness.detail && (
          <span style={styles.detail}>{freshness.detail}</span>
        )}
      </div>

      <div style={styles.right}>
        <span style={styles.scopeNote}>
          broker data only · market prices separate
        </span>
        {summary && (
          <Timestamp iso={summary.latest_snapshot_as_of} prefix="Last sync" />
        )}
      </div>
    </div>
  );
}

/* ── Freshness derivation ───────────────────────────────────────────────── */

interface FreshnessDisplay {
  label: string;
  icon: string;
  color: string;
  borderColor: string;
  detail?: string;
}

function deriveFreshness(
  statuses: string[],
  fetchStatus: string
): FreshnessDisplay {
  if (fetchStatus === "loading") {
    return {
      label: "Checking…",
      icon: "○",
      color: "var(--color-unknown)",
      borderColor: "var(--color-border)",
    };
  }
  if (fetchStatus === "error") {
    return {
      label: "Error",
      icon: "⚠",
      color: "var(--color-error)",
      borderColor: "var(--color-error)",
      detail: "Failed to load freshness status — broker data may be unavailable",
    };
  }

  const has = (s: string) => statuses.includes(s);

  if (has("reauth_required")) {
    return {
      label: "Reauth Required",
      icon: "⚠",
      color: "var(--color-reauth)",
      borderColor: "var(--color-reauth)",
      detail: "Broker connection requires re-authorization. Review broker settings.",
    };
  }
  if (has("error")) {
    return {
      label: "Error",
      icon: "⚠",
      color: "var(--color-error)",
      borderColor: "var(--color-error)",
      detail: "Broker sync error — data may be outdated",
    };
  }
  if (has("stale")) {
    return {
      label: "Stale",
      icon: "◑",
      color: "var(--color-stale)",
      borderColor: "var(--color-stale)",
      detail: "Holdings data may be outdated — broker sync has not completed recently",
    };
  }
  if (has("delayed") || has("cached")) {
    return {
      label: "Delayed / Cached",
      icon: "◑",
      color: "var(--color-stale)",
      borderColor: "var(--color-stale)",
    };
  }
  if (has("unknown") || statuses.length === 0) {
    return {
      label: "Unknown",
      icon: "○",
      color: "var(--color-unknown)",
      borderColor: "var(--color-border)",
      detail: "Sync status unknown — broker sync may not have run yet",
    };
  }
  if (has("fresh")) {
    return {
      label: "Synced",
      icon: "●",
      color: "var(--color-live)",
      borderColor: "var(--color-live)",
    };
  }

  return {
    label: "Unknown",
    icon: "○",
    color: "var(--color-unknown)",
    borderColor: "var(--color-border)",
  };
}

/* ── Styles ─────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  bar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "var(--space-2) var(--space-6)",
    backgroundColor: "var(--color-surface)",
    border: "1px solid",
    borderRadius: "var(--radius-md)",
    gap: "var(--space-4)",
    flexWrap: "wrap",
    minHeight: 42,
  },
  left: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    flexWrap: "wrap",
  },
  right: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-4)",
    flexShrink: 0,
    flexWrap: "wrap",
  },
  icon: {
    fontSize: "var(--font-size-base)",
    lineHeight: 1,
    flexShrink: 0,
  },
  scopeLabel: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    color: "var(--color-text-muted)",
    letterSpacing: "0.1em",
  },
  statusLabel: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
  },
  detail: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
  },
  scopeNote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    fontStyle: "italic",
  },
};
