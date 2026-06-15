import { useEffect, useMemo, useState } from "react";
import { generateAgentTeamReport, getReportThread } from "../api/reports";
import { ApiRequestError } from "../api/client";
import { useAccountContext } from "../context/useAccountContext";
import { useReports } from "../hooks/useReports";
import ReportLibraryList from "../components/reports/ReportLibraryList";
import ReportDetail, { type ReportDetailStatus } from "../components/reports/ReportDetail";
import { EmptyState, ErrorState, LoadingSkeleton } from "../components/shared/StateViews";
import { Badge, MpIcon, PageHeader, SafetyStrip } from "../components/shared/mp";
import type { ReportThreadDetailRead } from "../types/api";

/**
 * ReportsPage — saved-analysis library.
 *
 * The page is a report library, not a thread/contract viewer: the left rail
 * indexes saved analyses (with an honest Agent-Team-analysis indicator) and the
 * right pane reads the selected report — Agent Team synthesis and role sections
 * first, deterministic scope/evidence/caveats as supporting provenance.
 *
 * Scope honesty rule: render only the scope/agent data saved with each report.
 * Never infer saved report scope or status from the current user/account
 * selector, Account Details, route state, or portfolio-context cache.
 */
export default function ReportsPage() {
  const { selectedUser } = useAccountContext();
  const { threads, status, error, refetch } = useReports(selectedUser?.id ?? null);

  const sortedThreads = useMemo(
    () =>
      [...threads].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
    [threads],
  );

  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ReportThreadDetailRead | null>(null);
  const [detailStatus, setDetailStatus] = useState<ReportDetailStatus>("idle");
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailRequestKey, setDetailRequestKey] = useState(0);
  // Transient, UI-only generation state (never a persisted backend status).
  // Single-flight per thread: id of the report whose generation is in flight.
  const [generatingThreadId, setGeneratingThreadId] = useState<string | null>(null);
  const [generateError, setGenerateError] = useState<{ id: string; message: string } | null>(null);

  // Keep a valid selection: preserve the current one if it still exists,
  // otherwise fall back to the newest saved report.
  useEffect(() => {
    if (!selectedUser?.id || sortedThreads.length === 0) {
      setSelectedThreadId(null);
      return;
    }
    setSelectedThreadId((current) =>
      current && sortedThreads.some((thread) => thread.id === current)
        ? current
        : sortedThreads[0].id,
    );
  }, [selectedUser?.id, sortedThreads]);

  // Fetch the opened report detail from the backend. The detailRequestKey lets
  // retry and post-generation refetch re-run this without changing selection.
  useEffect(() => {
    if (!selectedUser?.id || !selectedThreadId) {
      setDetail(null);
      setDetailStatus("idle");
      setDetailError(null);
      return;
    }

    let cancelled = false;
    setDetailStatus("loading");
    setDetailError(null);

    getReportThread(selectedUser.id, selectedThreadId)
      .then((nextDetail) => {
        if (cancelled) return;
        setDetail(nextDetail);
        setDetailStatus("success");
        // Clear the transient generating flag once this report's fresh detail
        // has arrived from the backend.
        setGeneratingThreadId((current) => (current === nextDetail.id ? null : current));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setDetail(null);
        setDetailStatus("error");
        setDetailError(err instanceof Error ? err.message : "Failed to load report detail.");
      });

    return () => {
      cancelled = true;
    };
  }, [detailRequestKey, selectedThreadId, selectedUser?.id]);

  const selectedThread = sortedThreads.find((thread) => thread.id === selectedThreadId) ?? null;

  // Explicit, manual generation (or re-run). Single-flight per thread; the
  // saved state is always re-read from the backend afterward, never invented.
  const handleGenerate = (threadId: string) => {
    if (!selectedUser?.id || generatingThreadId) return;
    setGeneratingThreadId(threadId);
    setGenerateError(null);
    generateAgentTeamReport(selectedUser.id, threadId)
      .then(() => {
        refetch();
        setDetailRequestKey((value) => value + 1);
      })
      .catch((err: unknown) => {
        setGeneratingThreadId(null);
        setGenerateError({ id: threadId, message: sanitizedGenerateMessage(err) });
      });
  };

  const showInitialLoading = status === "loading" && threads.length === 0;
  const showInitialError = status === "error" && threads.length === 0;
  const showEmpty = status === "success" && threads.length === 0;
  const showWorkspace = threads.length > 0;

  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Workspace · reports"
        title="Reports library"
        sub="Saved review analyses. Agent Team synthesis leads each report; the deterministic scope, evidence, and caveats it was generated from stay attached for audit."
        right={
          <Badge tone="mute" dot={false}>
            <MpIcon name="lock" size={12} style={{ marginRight: 4 }} />
            Read-only
          </Badge>
        }
      />

      {!selectedUser && (
        <EmptyState
          icon={<MpIcon name="reports" size={28} />}
          title="No user selected"
          body="Select a local user to load saved report analyses."
        />
      )}

      {selectedUser && showInitialLoading && (
        <LoadingSkeleton rows={6} label="Loading saved reports…" />
      )}

      {selectedUser && showInitialError && (
        <ErrorState message={error ?? "Failed to load saved reports."} onRetry={refetch} />
      )}

      {selectedUser && showEmpty && (
        <EmptyState
          icon={<MpIcon name="reports" size={28} />}
          title="No saved reports yet"
          body="Saved review snapshots appear here after a review is saved. Each can then be turned into an Agent Team analysis."
        />
      )}

      {selectedUser && showWorkspace && (
        <div className="mp-reports-grid" style={styles.workspace}>
          <aside style={styles.rail} aria-label="Report library">
            <div style={styles.railHead}>
              <span style={styles.railTitle}>Saved analyses</span>
              <span style={styles.railCount}>{sortedThreads.length}</span>
            </div>
            <ReportLibraryList
              threads={sortedThreads}
              selectedThreadId={selectedThreadId}
              onSelect={setSelectedThreadId}
            />
          </aside>

          <ReportDetail
            selectedThread={selectedThread}
            detail={detail}
            status={detailStatus}
            error={detailError}
            onRetry={() => setDetailRequestKey((value) => value + 1)}
            isGenerating={generatingThreadId !== null && generatingThreadId === selectedThreadId}
            generateError={generateError?.id === selectedThreadId ? generateError.message : null}
            onGenerate={() => selectedThreadId && handleGenerate(selectedThreadId)}
          />
        </div>
      )}

      <SafetyStrip
        items={[
          "Analysis only",
          "Manual decision support",
          "Read-only saved snapshots",
          "Deterministic metrics owned by backend",
        ]}
      />
    </div>
  );
}

function sanitizedGenerateMessage(err: unknown): string {
  if (err instanceof ApiRequestError) {
    if (err.status === 404) {
      return "This saved snapshot can't produce an Agent Team report. Its reviewed evidence package is unavailable.";
    }
    if (err.status >= 500) {
      return "The Agent Team report couldn't be generated right now. You can try again.";
    }
  }
  return "The Agent Team report couldn't be generated. You can try again.";
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-6)",
    maxWidth: 1320,
    margin: "0 auto",
    color: "var(--mp-ink)",
    minWidth: 0,
  },
  workspace: {
    display: "grid",
    gap: "var(--space-5)",
    alignItems: "start",
    minWidth: 0,
  },
  rail: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    minWidth: 0,
  },
  railHead: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-2)",
    paddingBottom: "var(--space-2)",
    borderBottom: "1px solid var(--mp-rule)",
  },
  railTitle: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
  railCount: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontVariantNumeric: "tabular-nums",
    border: "1px solid var(--mp-rule)",
    borderRadius: 999,
    padding: "0 7px",
    lineHeight: 1.7,
  },
};
