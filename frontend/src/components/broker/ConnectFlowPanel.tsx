import { useState } from "react";
import { brokerSyncApi } from "../../api/brokerSync";
import { ApiRequestError } from "../../api/client";

type FlowState =
  | { kind: "idle" }
  | { kind: "registering" }
  | { kind: "fetching_portal" }
  | { kind: "awaiting_user"; portalUrl: string; expiresAt: string | null }
  | { kind: "refreshing" }
  | { kind: "error"; message: string };

interface ConnectFlowPanelProps {
  userId: string;
  onConnectionsRefreshed: () => void;
  alreadyConnected?: boolean;
}

/**
 * ConnectFlowPanel — guides through SnapTrade broker connection.
 *
 * Steps:
 *   1. Register SnapTrade user (one-time, backend handles idempotency)
 *   2. Get portal URL from backend
 *   3. User opens portal in new tab and connects their broker
 *   4. User clicks "I've connected" → refresh-connections → done
 *
 * Safety:
 *   - Portal opens in new tab, never embedded.
 *   - Safety copy visible at every step.
 *   - No credentials collected by this app.
 */
export default function ConnectFlowPanel({
  userId,
  onConnectionsRefreshed,
  alreadyConnected = false,
}: ConnectFlowPanelProps) {
  const [flow, setFlow] = useState<FlowState>({ kind: "idle" });

  async function handleConnect() {
    setFlow({ kind: "registering" });
    try {
      await brokerSyncApi.registerSnapTradeUser(userId);
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 409) {
        // already registered — continue to portal
      } else {
        const msg = err instanceof ApiRequestError ? err.detail : err instanceof Error ? err.message : "Registration failed";
        setFlow({ kind: "error", message: `Registration: ${msg}` });
        return;
      }
    }

    setFlow({ kind: "fetching_portal" });
    try {
      const portal = await brokerSyncApi.createConnectionPortal(userId);
      setFlow({ kind: "awaiting_user", portalUrl: portal.portal_url, expiresAt: portal.expires_at });
    } catch (err) {
      const msg = err instanceof ApiRequestError ? err.detail : err instanceof Error ? err.message : "Could not create portal";
      setFlow({ kind: "error", message: `Portal: ${msg}` });
    }
  }

  async function handleRefresh() {
    setFlow({ kind: "refreshing" });
    try {
      await brokerSyncApi.refreshConnections(userId);
      onConnectionsRefreshed();
      setFlow({ kind: "idle" });
    } catch (err) {
      const msg = err instanceof ApiRequestError ? err.detail : err instanceof Error ? err.message : "Refresh failed";
      setFlow({ kind: "error", message: `Refresh: ${msg}` });
    }
  }

  function handleReset() {
    setFlow({ kind: "idle" });
  }

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <span style={styles.title}>
          {alreadyConnected ? "Add another broker connection" : "Connect a broker via SnapTrade"}
        </span>
        <span style={styles.badge}>read-only</span>
      </div>

      {flow.kind === "idle" && (
        <div style={styles.step}>
          <p style={styles.description}>
            Connect your broker account for read-only portfolio sync. No trades are placed.
            Your broker credentials go directly to the SnapTrade portal — not to this app.
          </p>
          <button style={styles.btnPrimary} onClick={handleConnect} type="button">
            Connect Broker via SnapTrade
          </button>
        </div>
      )}

      {(flow.kind === "registering" || flow.kind === "fetching_portal") && (
        <div style={styles.step}>
          <span style={styles.loading} role="status" aria-live="polite">
            <span aria-hidden="true">◌ </span>
            {flow.kind === "registering" ? "Setting up SnapTrade user…" : "Generating secure portal link…"}
          </span>
        </div>
      )}

      {flow.kind === "awaiting_user" && (
        <div style={styles.step}>
          <div style={styles.portalBox}>
            <p style={styles.portalInstruction}>
              <strong>Step 1:</strong> Click the button below to open the secure SnapTrade portal in a new tab.
              Connect your broker (e.g. Fidelity) there.
            </p>
            <a
              href={flow.portalUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={styles.portalLink}
              aria-label="Open SnapTrade secure broker portal in a new tab"
            >
              Open Secure Provider Portal ↗
            </a>
            {flow.expiresAt && (
              <p style={styles.expiry}>
                Portal link valid until approximately {new Date(flow.expiresAt).toLocaleTimeString()}.
              </p>
            )}
            <div style={styles.safetyNote}>
              <span aria-hidden="true">⚠ </span>
              Do not enter Fidelity credentials into this app.
              Use the secure provider portal that opened in the new tab.
            </div>
          </div>

          <p style={styles.step2}>
            <strong>Step 2:</strong> After connecting in the portal, come back here and click the button below.
          </p>
          <div style={styles.actions}>
            <button style={styles.btnPrimary} onClick={handleRefresh} type="button">
              I've connected — refresh my connections
            </button>
            <button style={styles.btnGhost} onClick={handleReset} type="button">
              Cancel
            </button>
          </div>
        </div>
      )}

      {flow.kind === "refreshing" && (
        <div style={styles.step}>
          <span style={styles.loading} role="status" aria-live="polite">
            <span aria-hidden="true">◌ </span>Refreshing broker connections…
          </span>
        </div>
      )}

      {flow.kind === "error" && (
        <div style={styles.step}>
          <div style={styles.errorBox} role="alert">
            <span aria-hidden="true">⚠ </span>
            {flow.message}
          </div>
          <button style={styles.btnGhost} onClick={handleReset} type="button">
            Try again
          </button>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  panel: {
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-5) var(--space-6)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-4)",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
  },
  title: {
    fontWeight: 700,
    fontSize: "var(--font-size-base)",
    color: "var(--color-text-primary)",
  },
  badge: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid var(--color-live)",
    borderRadius: "var(--radius-sm)",
    color: "var(--color-live)",
    fontWeight: 600,
    letterSpacing: "0.04em",
  },
  step: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
  },
  description: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    lineHeight: 1.6,
    margin: 0,
  },
  loading: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
  },
  portalBox: {
    backgroundColor: "var(--color-surface-2)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-4)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
  },
  portalInstruction: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-secondary)",
    margin: 0,
    lineHeight: 1.5,
  },
  portalLink: {
    display: "inline-flex",
    alignItems: "center",
    gap: "var(--space-2)",
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    color: "var(--color-accent)",
    padding: "var(--space-2) var(--space-4)",
    border: "2px solid var(--color-accent)",
    borderRadius: "var(--radius-sm)",
    textDecoration: "none",
    alignSelf: "flex-start",
  },
  expiry: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    margin: 0,
    fontStyle: "italic",
  },
  safetyNote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-stale)",
    fontWeight: 600,
    lineHeight: 1.5,
  },
  step2: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-secondary)",
    margin: 0,
    lineHeight: 1.5,
  },
  actions: {
    display: "flex",
    gap: "var(--space-3)",
    flexWrap: "wrap",
  },
  btnPrimary: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    padding: "var(--space-2) var(--space-5)",
    border: "2px solid var(--color-accent)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--color-accent)",
    color: "var(--color-bg)",
    cursor: "pointer",
  },
  btnGhost: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
    padding: "var(--space-2) var(--space-4)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "transparent",
    color: "var(--color-text-secondary)",
    cursor: "pointer",
  },
  errorBox: {
    padding: "var(--space-3) var(--space-4)",
    backgroundColor: "rgba(220, 60, 60, 0.08)",
    border: "1px solid var(--color-error)",
    borderRadius: "var(--radius-sm)",
    fontSize: "var(--font-size-sm)",
    color: "var(--color-error)",
    lineHeight: 1.5,
  },
};
