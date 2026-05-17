import { useState, useEffect, useRef } from "react";
import { brokerSyncApi } from "../../api/brokerSync";
import { ApiRequestError } from "../../api/client";
import type { BrokerSyncRunPublicRead } from "../../types/api";

const TERMINAL_STATUSES = new Set(["succeeded", "partially_succeeded", "failed", "cancelled"]);
const POLL_INTERVAL_MS = 2500;

interface SyncRunStatusProps {
  userId: string;
  syncRunId: string;
  onComplete?: (run: BrokerSyncRunPublicRead) => void;
}

/**
 * SyncRunStatus — polls a broker sync run until it reaches a terminal state.
 *
 * Shows: running spinner, succeeded/partial summary, or error with retry.
 * Stops polling when status is succeeded | partially_succeeded | failed | cancelled.
 */
export default function SyncRunStatus({ userId, syncRunId, onComplete }: SyncRunStatusProps) {
  const [run, setRun] = useState<BrokerSyncRunPublicRead | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    let cancelled = false;
    let timerId: ReturnType<typeof setTimeout> | null = null;

    async function poll() {
      try {
        const result = await brokerSyncApi.getBrokerSyncRun(userId, syncRunId);
        if (cancelled) return;
        setRun(result);
        setFetchError(null);
        if (TERMINAL_STATUSES.has(result.status)) {
          onCompleteRef.current?.(result);
          return;
        }
        timerId = setTimeout(poll, POLL_INTERVAL_MS);
      } catch (err) {
        if (cancelled) return;
        const msg = err instanceof ApiRequestError
          ? err.detail
          : err instanceof Error ? err.message : "Failed to fetch sync status";
        setFetchError(msg);
      }
    }

    poll();
    return () => {
      cancelled = true;
      if (timerId) clearTimeout(timerId);
    };
  }, [userId, syncRunId]);

  if (fetchError) {
    return (
      <span style={styles.error}>
        <span aria-hidden="true">⚠ </span>
        Could not load sync status: {fetchError}
      </span>
    );
  }

  if (!run || run.status === "queued" || run.status === "running") {
    return (
      <span style={styles.running} role="status" aria-live="polite">
        <span style={styles.spinner} aria-hidden="true">◌</span>
        {" "}Sync in progress…
      </span>
    );
  }

  if (run.status === "succeeded" || run.status === "partially_succeeded") {
    const summary = run.summary;
    const isPartial = run.status === "partially_succeeded";
    return (
      <span style={isPartial ? styles.partial : styles.completed} role="status">
        <span aria-hidden="true">● </span>
        {isPartial ? "Sync partially complete" : "Sync complete"} — {run.positions_count} position{run.positions_count !== 1 ? "s" : ""}
        {summary?.stock_positions_count != null && `, ${summary.stock_positions_count} stock`}
        {summary?.option_positions_count != null && `, ${summary.option_positions_count} option`}
        {summary?.warnings && summary.warnings.length > 0 && (
          <span style={styles.warn}>
            {" · "}{summary.warnings.length} warning{summary.warnings.length > 1 ? "s" : ""}
          </span>
        )}
        {summary?.partial_failures && summary.partial_failures.length > 0 && (
          <span style={styles.warn}>
            {" · "}{summary.partial_failures.length} partial failure{summary.partial_failures.length > 1 ? "s" : ""}
          </span>
        )}
      </span>
    );
  }

  if (run.status === "failed") {
    return (
      <span style={styles.error} role="alert">
        <span aria-hidden="true">⚠ </span>
        Sync failed
        {run.error && `: ${run.error.message}`}
      </span>
    );
  }

  return (
    <span style={styles.muted} role="status">
      Sync {run.status}
    </span>
  );
}

const styles: Record<string, React.CSSProperties> = {
  running: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    display: "inline-flex",
    alignItems: "center",
    gap: "var(--space-1)",
  },
  spinner: {
    display: "inline-block",
    animation: "spin 1.2s linear infinite",
  },
  completed: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-live)",
  },
  warn: {
    color: "var(--color-stale)",
  },
  partial: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-stale)",
  },
  error: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-error)",
  },
  muted: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
  },
};
