import { useState } from "react";
import { useAccountContext } from "../context/useAccountContext";
import { useBrokerConnections } from "../hooks/useBrokerConnections";
import { brokerSyncApi } from "../api/brokerSync";
import { ApiRequestError } from "../api/client";
import SafetyNoticePanel from "../components/broker/SafetyNoticePanel";
import ConnectFlowPanel from "../components/broker/ConnectFlowPanel";
import BrokerConnectionList from "../components/broker/BrokerConnectionList";
import { EmptyState, ErrorState, LoadingSkeleton } from "../components/shared/StateViews";

/**
 * BrokerConnectionPage — read-only SnapTrade broker connection flow.
 *
 * Route: /broker
 *
 * Safety:
 * - Read-only broker sync. No trades placed.
 * - No Fidelity credentials entered into this app.
 * - Portal opens in new tab (external SnapTrade surface).
 * - Broker data may be stale — verify in Fidelity before acting.
 * - Market quotes not available yet.
 */
export default function BrokerConnectionPage() {
  const { selectedUser } = useAccountContext();

  return (
    <div style={styles.page}>
      <div style={styles.pageHeader}>
        <h1 style={styles.pageTitle}>Broker Connection</h1>
        <p style={styles.pageSubtitle}>
          Read-only broker sync — no trades are placed from this app.
        </p>
      </div>

      <SafetyNoticePanel />

      {selectedUser ? (
        <BrokerConnectionContent userId={selectedUser.id} />
      ) : (
        <EmptyState
          icon="⬡"
          title="Select a user to manage broker connections"
          body="Use the account selector in the top bar to choose a user first."
        />
      )}

      <aside style={styles.marketQuoteNotice} role="note" aria-label="Market data availability">
        <span style={styles.noticeIcon} aria-hidden="true">○</span>
        <div>
          <p style={styles.noticeTitle}>Market quotes are not available yet</p>
          <p style={styles.noticeBody}>
            Position values shown after sync are broker snapshot data (cost basis / last sync),
            not current market prices. Do not rely on these as current market values.
          </p>
        </div>
      </aside>
    </div>
  );
}

function BrokerConnectionContent({ userId }: { userId: string }) {
  const {
    connections,
    accountsByConnection,
    status,
    error,
    reload,
  } = useBrokerConnections(userId);

  const [showConnectFlow, setShowConnectFlow] = useState(false);
  const [refreshingLabel, setRefreshingLabel] = useState<string | null>(null);

  async function handleRefreshAll() {
    setRefreshingLabel("Refreshing…");
    try {
      await brokerSyncApi.refreshConnections(userId);
      reload();
    } catch (err) {
      const msg = err instanceof ApiRequestError ? err.detail : err instanceof Error ? err.message : "Refresh failed";
      setRefreshingLabel(`Failed: ${msg}`);
      setTimeout(() => setRefreshingLabel(null), 4000);
      return;
    }
    setRefreshingLabel(null);
  }

  const hasConnections = connections && connections.length > 0;

  if (status === "loading") {
    return <LoadingSkeleton rows={3} label="Loading broker connections…" />;
  }

  if (status === "error") {
    return <ErrorState message={error ?? "Could not load broker connections"} onRetry={reload} />;
  }

  return (
    <div style={styles.content}>
      {(!hasConnections || showConnectFlow) && (
        <ConnectFlowPanel
          userId={userId}
          onConnectionsRefreshed={() => {
            reload();
            setShowConnectFlow(false);
          }}
          alreadyConnected={!!hasConnections}
        />
      )}

      <div style={styles.connectionsHeader}>
        <span style={styles.connectionsTitle}>Broker Connections</span>
        <div style={styles.headerActions}>
          {hasConnections && !showConnectFlow && (
            <button style={styles.btnSecondary} onClick={() => setShowConnectFlow(true)} type="button">
              + Add Connection
            </button>
          )}
          <button
            style={styles.btnSecondary}
            onClick={handleRefreshAll}
            type="button"
            disabled={refreshingLabel !== null}
          >
            {refreshingLabel ?? "Refresh Connections"}
          </button>
        </div>
      </div>

      {refreshingLabel && (
        <span style={styles.refreshStatus} role="status" aria-live="polite">
          {refreshingLabel}
        </span>
      )}

      <BrokerConnectionList
        connections={connections ?? []}
        accountsByConnection={accountsByConnection}
        userId={userId}
        onRefreshNeeded={reload}
      />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-6)",
    maxWidth: 900,
  },
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
    color: "var(--color-text-muted)",
    margin: 0,
  },
  content: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-5)",
  },
  connectionsHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: "var(--space-3)",
  },
  connectionsTitle: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    color: "var(--color-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  headerActions: {
    display: "flex",
    gap: "var(--space-2)",
    flexWrap: "wrap",
  },
  btnSecondary: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 600,
    padding: "var(--space-1) var(--space-3)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "transparent",
    color: "var(--color-text-secondary)",
    cursor: "pointer",
  },
  refreshStatus: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    fontStyle: "italic",
  },
  marketQuoteNotice: {
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
    marginBottom: "var(--space-1)",
    margin: 0,
  },
  noticeBody: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    lineHeight: 1.6,
    margin: 0,
  },
};
