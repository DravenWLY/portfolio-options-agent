import type { BrokerConnectionPublicRead, BrokerAccountPublicRead } from "../../types/api";
import Timestamp from "../shared/Timestamp";
import BrokerAccountRow from "./BrokerAccountRow";

interface BrokerConnectionListProps {
  connections: BrokerConnectionPublicRead[];
  accountsByConnection: Record<string, BrokerAccountPublicRead[]>;
  userId: string;
  onRefreshNeeded: () => void;
}

/**
 * BrokerConnectionList — renders one card per broker connection.
 *
 * Each card shows connection status, last sync, and per-account rows.
 * Safety: no trade controls, no credential fields.
 */
export default function BrokerConnectionList({
  connections,
  accountsByConnection,
  userId,
  onRefreshNeeded,
}: BrokerConnectionListProps) {
  if (connections.length === 0) {
    return (
      <div style={styles.empty}>
        <span style={styles.emptyIcon} aria-hidden="true">⊙</span>
        <p style={styles.emptyTitle}>No broker connections yet</p>
        <p style={styles.emptyBody}>
          Use "Connect Broker via SnapTrade" above to link a read-only broker account.
          No trades will be placed.
        </p>
      </div>
    );
  }

  return (
    <div style={styles.list}>
      {connections.map((conn) => (
        <ConnectionCard
          key={conn.id}
          connection={conn}
          accounts={accountsByConnection[conn.id] ?? []}
          userId={userId}
          onRefreshNeeded={onRefreshNeeded}
        />
      ))}
    </div>
  );
}

function ConnectionCard({
  connection,
  accounts,
  userId,
  onRefreshNeeded,
}: {
  connection: BrokerConnectionPublicRead;
  accounts: BrokerAccountPublicRead[];
  userId: string;
  onRefreshNeeded: () => void;
}) {
  const statusColor = connectionStatusColor(connection.connection_status);
  const freshnessColor = freshnessStatusColor(connection.data_freshness_status);

  return (
    <div style={styles.card}>
      <div style={styles.cardHeader}>
        <div style={styles.brokerInfo}>
          <span style={styles.brokerName}>{connection.broker_name}</span>
          <span style={styles.provider}>via {connection.provider}</span>
        </div>

        <div style={styles.statusRow}>
          <span style={{ ...styles.chip, color: statusColor, borderColor: statusColor }}>
            <span aria-hidden="true">● </span>
            {connection.connection_status}
          </span>
          <span style={{ ...styles.chip, color: freshnessColor, borderColor: freshnessColor }}>
            {connection.data_freshness_status}
          </span>
          {connection.last_successful_sync_at ? (
            <Timestamp iso={connection.last_successful_sync_at} prefix="Last sync" />
          ) : (
            <span style={styles.neverSynced}>Never synced</span>
          )}
        </div>
      </div>

      {connection.connection_status === "reauth_required" && (
        <div style={styles.reauth} role="alert">
          <span aria-hidden="true">⚠ </span>
          Re-authorization required. Reconnect via the SnapTrade portal to restore access.
        </div>
      )}

      <div style={styles.accountsSection}>
        <span style={styles.accountsLabel}>
          {accounts.length === 0 ? "No broker accounts yet — sync after connecting." : `${accounts.length} account${accounts.length !== 1 ? "s" : ""}`}
        </span>
        {accounts.map((acct) => (
          <BrokerAccountRow
            key={acct.id}
            account={acct}
            userId={userId}
            onSyncComplete={onRefreshNeeded}
          />
        ))}
      </div>
    </div>
  );
}

function connectionStatusColor(status: string): string {
  if (status === "connected") return "var(--color-live)";
  if (status === "reauth_required") return "var(--color-reauth)";
  if (status === "error") return "var(--color-error)";
  if (status === "disconnected") return "var(--color-unknown)";
  return "var(--color-text-muted)";
}

function freshnessStatusColor(status: string): string {
  if (status === "fresh") return "var(--color-live)";
  if (["stale", "delayed", "cached"].includes(status)) return "var(--color-stale)";
  if (status === "error") return "var(--color-error)";
  if (status === "reauth_required") return "var(--color-reauth)";
  return "var(--color-unknown)";
}

const styles: Record<string, React.CSSProperties> = {
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-4)",
  },
  card: {
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-md)",
    overflow: "hidden",
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "var(--space-4) var(--space-6)",
    flexWrap: "wrap",
    gap: "var(--space-3)",
    borderBottom: "1px solid var(--color-border-subtle)",
  },
  brokerInfo: {
    display: "flex",
    alignItems: "baseline",
    gap: "var(--space-2)",
  },
  brokerName: {
    fontWeight: 700,
    fontSize: "var(--font-size-base)",
    color: "var(--color-text-primary)",
  },
  provider: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
  },
  statusRow: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
    flexWrap: "wrap",
  },
  chip: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid",
    borderRadius: "var(--radius-sm)",
    fontWeight: 600,
  },
  neverSynced: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    fontStyle: "italic",
  },
  reauth: {
    padding: "var(--space-3) var(--space-6)",
    backgroundColor: "rgba(255, 120, 40, 0.08)",
    color: "var(--color-reauth)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 600,
    borderBottom: "1px solid var(--color-border-subtle)",
  },
  accountsSection: {
    display: "flex",
    flexDirection: "column",
  },
  accountsLabel: {
    padding: "var(--space-2) var(--space-4)",
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  empty: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "var(--space-3)",
    padding: "var(--space-12) var(--space-6)",
    textAlign: "center",
  },
  emptyIcon: {
    fontSize: 32,
    color: "var(--color-text-muted)",
  },
  emptyTitle: {
    fontSize: "var(--font-size-base)",
    fontWeight: 600,
    color: "var(--color-text-secondary)",
  },
  emptyBody: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    maxWidth: 400,
    lineHeight: 1.6,
  },
};
