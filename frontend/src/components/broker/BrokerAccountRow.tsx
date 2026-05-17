import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { brokerSyncApi } from "../../api/brokerSync";
import { ApiRequestError } from "../../api/client";
import { useAccountContext } from "../../context/useAccountContext";
import type { BrokerAccountPublicRead, BrokerSyncRunPublicRead } from "../../types/api";
import Timestamp from "../shared/Timestamp";
import SyncRunStatus from "./SyncRunStatus";

interface BrokerAccountRowProps {
  account: BrokerAccountPublicRead;
  userId: string;
  onSyncComplete?: () => void;
}

type SyncState =
  | { kind: "idle" }
  | { kind: "syncing" }
  | { kind: "polling"; runId: string }
  | { kind: "done"; run: BrokerSyncRunPublicRead }
  | { kind: "error"; message: string }
  | { kind: "conflict"; message: string };

/**
 * BrokerAccountRow — shows per-broker-account status and sync controls.
 *
 * Safety: no trade execution. Sync is read-only. Credentials never entered here.
 */
export default function BrokerAccountRow({ account, userId, onSyncComplete }: BrokerAccountRowProps) {
  const [syncState, setSyncState] = useState<SyncState>({ kind: "idle" });
  const { setSelectedAccount } = useAccountContext();
  const navigate = useNavigate();

  async function handleSync() {
    setSyncState({ kind: "syncing" });
    try {
      const run = await brokerSyncApi.syncBrokerAccount(userId, account.id);
      setSyncState({ kind: "polling", runId: run.id });
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 409) {
        setSyncState({ kind: "conflict", message: "Sync already running — wait and try again." });
        return;
      }
      const msg = err instanceof ApiRequestError ? err.detail : err instanceof Error ? err.message : "Sync request failed";
      setSyncState({ kind: "error", message: msg });
    }
  }

  function handleSyncComplete(run: BrokerSyncRunPublicRead) {
    setSyncState({ kind: "done", run });
    onSyncComplete?.();
  }

  function handleViewPortfolio() {
    if (!account.account_id) return;
    setSelectedAccount({
      id: account.account_id,
      user_id: userId,
      broker_name: account.display_name,
      account_type: account.account_type as "taxable_individual" | "roth_ira" | "traditional_ira" | "other",
      display_name: account.display_name,
      base_currency: account.base_currency,
      is_manual: false,
      created_at: account.created_at,
      updated_at: account.updated_at,
      deleted_at: null,
    });
    navigate("/");
  }

  const freshnessColor = freshnessCssVar(account.data_freshness_status);
  const syncStatusColor = syncStatusCssVar(account.sync_status);

  return (
    <div style={styles.row}>
      <div style={styles.main}>
        <div style={styles.nameRow}>
          <span style={styles.name}>{account.display_name}</span>
          <span style={{ ...styles.chip, color: freshnessColor, borderColor: freshnessColor }}>
            {account.data_freshness_status}
          </span>
          <span style={{ ...styles.chip, color: syncStatusColor, borderColor: syncStatusColor }}>
            {account.sync_status}
          </span>
        </div>
        <div style={styles.meta}>
          <span style={styles.metaItem}>{account.account_type}</span>
          <span style={styles.metaItem}>{account.base_currency}</span>
          {account.last_successful_sync_at ? (
            <Timestamp iso={account.last_successful_sync_at} prefix="Last sync" />
          ) : (
            <span style={styles.metaItem}>Never synced</span>
          )}
        </div>
      </div>

      <div style={styles.actions}>
        {syncState.kind === "idle" || syncState.kind === "error" || syncState.kind === "conflict" || syncState.kind === "done" ? (
          <button style={styles.btn} onClick={handleSync} type="button">
            {syncState.kind === "done" ? "Sync Again" : "Sync Account"}
          </button>
        ) : (
          <button style={{ ...styles.btn, ...styles.btnDisabled }} disabled type="button">
            Syncing…
          </button>
        )}

        {account.account_id && (
          <button style={{ ...styles.btn, ...styles.btnSecondary }} onClick={handleViewPortfolio} type="button">
            View Portfolio →
          </button>
        )}
      </div>

      {syncState.kind === "syncing" && (
        <span style={styles.statusLine} role="status" aria-live="polite">
          <span aria-hidden="true">◌ </span>Requesting sync…
        </span>
      )}
      {syncState.kind === "polling" && (
        <div style={styles.statusLine}>
          <SyncRunStatus
            userId={userId}
            syncRunId={syncState.runId}
            onComplete={handleSyncComplete}
          />
        </div>
      )}
      {syncState.kind === "done" && (
        <div style={styles.statusLine}>
          <SyncRunStatus
            userId={userId}
            syncRunId={syncState.run.id}
          />
        </div>
      )}
      {syncState.kind === "error" && (
        <span style={{ ...styles.statusLine, color: "var(--color-error)" }} role="alert">
          <span aria-hidden="true">⚠ </span>{syncState.message}
        </span>
      )}
      {syncState.kind === "conflict" && (
        <span style={{ ...styles.statusLine, color: "var(--color-stale)" }}>
          {syncState.message}
        </span>
      )}
    </div>
  );
}

function freshnessCssVar(status: string): string {
  if (status === "fresh") return "var(--color-live)";
  if (status === "stale" || status === "delayed" || status === "cached") return "var(--color-stale)";
  if (status === "error") return "var(--color-error)";
  if (status === "reauth_required") return "var(--color-reauth)";
  return "var(--color-unknown)";
}

function syncStatusCssVar(status: string): string {
  if (status === "succeeded") return "var(--color-live)";
  if (status === "partially_succeeded" || status === "running" || status === "queued") return "var(--color-stale)";
  if (status === "failed") return "var(--color-error)";
  if (status === "cancelled") return "var(--color-text-muted)";
  return "var(--color-unknown)";
}

const styles: Record<string, React.CSSProperties> = {
  row: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    padding: "var(--space-3) var(--space-4)",
    borderTop: "1px solid var(--color-border-subtle)",
  },
  main: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
  },
  nameRow: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    flexWrap: "wrap",
  },
  name: {
    fontWeight: 600,
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-primary)",
  },
  chip: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 5px",
    border: "1px solid",
    borderRadius: "var(--radius-sm)",
    fontWeight: 600,
  },
  meta: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-4)",
    flexWrap: "wrap",
  },
  metaItem: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
  },
  actions: {
    display: "flex",
    gap: "var(--space-2)",
    flexWrap: "wrap",
  },
  btn: {
    fontSize: "var(--font-size-xs)",
    padding: "var(--space-1) var(--space-3)",
    border: "1px solid var(--color-accent)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "transparent",
    color: "var(--color-accent)",
    cursor: "pointer",
    fontWeight: 600,
  },
  btnSecondary: {
    borderColor: "var(--color-border)",
    color: "var(--color-text-secondary)",
  },
  btnDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
    borderColor: "var(--color-border)",
    color: "var(--color-text-muted)",
  },
  statusLine: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
  },
};
