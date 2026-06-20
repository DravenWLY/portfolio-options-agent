import { useEffect, useMemo, useState } from "react";
import { generateAgentTeamReport, getReportThread } from "../api/reports";
import { ApiRequestError } from "../api/client";
import { useAccountContext } from "../context/useAccountContext";
import { useReports } from "../hooks/useReports";
import { useMediaQuery } from "../hooks/useMediaQuery";
import ReportLibraryList from "../components/reports/ReportLibraryList";
import ReportLibraryControls from "../components/reports/ReportLibraryControls";
import ReportDetail, { type ReportDetailStatus } from "../components/reports/ReportDetail";
import {
  deriveReportStatus,
  matchesQuery,
  matchesStatusFilter,
  type ReportFilterValue,
} from "../components/reports/reportStatus";
import { EmptyState, ErrorState, LoadingSkeleton } from "../components/shared/StateViews";
import SkyframeSurface from "../components/shared/SkyframeSurface";
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
  // Rail layout: at ≤1100px the workspace collapses to one column, so the rail
  // becomes a disclosure (default closed) and the reading pane leads.
  const isNarrow = useMediaQuery("(max-width: 1100px)");
  const [railOpen, setRailOpen] = useState(false);
  // Rail search + status filter (client-side, over already-loaded threads).
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<ReportFilterValue>("all");

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

  // Client-side search + status filter over the loaded threads. Selection is
  // independent of the filter — a selected report stays open in the pane even if
  // it is filtered out of the rail.
  const filteredThreads = useMemo(
    () =>
      sortedThreads.filter(
        (thread) =>
          matchesQuery(thread, query) &&
          matchesStatusFilter(deriveReportStatus(thread), statusFilter),
      ),
    [sortedThreads, query, statusFilter],
  );
  const filtersActive = query.trim() !== "" || statusFilter !== "all";
  const clearFilters = () => {
    setQuery("");
    setStatusFilter("all");
  };
  const railCountLabel = filtersActive
    ? `${filteredThreads.length} / ${sortedThreads.length}`
    : String(sortedThreads.length);

  // On the narrow single-column layout, picking a report collapses the rail so
  // the reading pane is shown immediately.
  const handleSelect = (threadId: string) => {
    setSelectedThreadId(threadId);
    if (isNarrow) setRailOpen(false);
  };

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
    <SkyframeSurface className="mp-surface reports-skyframe">
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
          {isNarrow ? (
            <aside style={styles.railNarrow} aria-label="Report library">
              <button
                type="button"
                aria-expanded={railOpen}
                onClick={() => setRailOpen((open) => !open)}
                style={styles.railToggle}
              >
                <span style={styles.railToggleHead}>
                  <span style={styles.railTitle}>Saved analyses</span>
                  <span style={styles.railCount}>{railCountLabel}</span>
                </span>
                <span style={styles.railToggleSel}>
                  {selectedThread?.title ?? "Select a saved report"}
                </span>
                <MpIcon
                  name="chevron-d"
                  size={16}
                  style={{
                    color: "var(--mp-mute)",
                    flexShrink: 0,
                    transform: railOpen ? "rotate(180deg)" : "none",
                    transition: "transform 120ms ease",
                  }}
                />
              </button>
              {railOpen && (
                <div style={styles.railScrollNarrow}>
                  <ReportLibraryControls
                    query={query}
                    onQueryChange={setQuery}
                    statusFilter={statusFilter}
                    onStatusChange={setStatusFilter}
                  />
                  <div style={styles.railListBelowControls}>
                    {filteredThreads.length > 0 ? (
                      <ReportLibraryList
                        threads={filteredThreads}
                        selectedThreadId={selectedThreadId}
                        onSelect={handleSelect}
                      />
                    ) : (
                      <RailEmpty onClear={clearFilters} />
                    )}
                  </div>
                </div>
              )}
            </aside>
          ) : (
            <aside style={styles.rail} aria-label="Report library">
              <div style={styles.railHead}>
                <span style={styles.railTitle}>Saved analyses</span>
                <span style={styles.railCount}>{railCountLabel}</span>
              </div>
              <ReportLibraryControls
                query={query}
                onQueryChange={setQuery}
                statusFilter={statusFilter}
                onStatusChange={setStatusFilter}
              />
              <div style={styles.railScroll}>
                {filteredThreads.length > 0 ? (
                  <ReportLibraryList
                    threads={filteredThreads}
                    selectedThreadId={selectedThreadId}
                    onSelect={handleSelect}
                  />
                ) : (
                  <RailEmpty onClear={clearFilters} />
                )}
              </div>
            </aside>
          )}

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
    </SkyframeSurface>
  );
}

function RailEmpty({ onClear }: { onClear: () => void }) {
  return (
    <div style={styles.railEmpty} role="status">
      <MpIcon name="search" size={20} style={{ color: "var(--mp-mute-2)" }} />
      <p style={styles.railEmptyText}>No saved reports match your search or filter.</p>
      <button type="button" onClick={onClear} style={styles.railEmptyBtn}>
        Clear search &amp; filter
      </button>
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
  workspace: {
    display: "grid",
    gap: "var(--space-5)",
    alignItems: "start",
    minWidth: 0,
  },
  rail: {
    // Sticky, independently scrolling rail so the reading pane scrolls on its
    // own and a long archive never pushes it off-screen.
    position: "sticky",
    top: "var(--space-4)",
    maxHeight: "calc(100vh - var(--topbar-height) - var(--space-8))",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    padding: "var(--space-3)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-md)",
    background: "var(--reports-rail-surface)",
    boxShadow: "var(--reports-section-shadow)",
    minWidth: 0,
    overflow: "hidden",
  },
  railScroll: {
    flex: 1,
    minHeight: 0,
    overflowY: "auto",
    paddingRight: 4,
  },
  railNarrow: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  railToggle: {
    appearance: "none",
    font: "inherit",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
    width: "100%",
    textAlign: "left",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-4)",
    background: "var(--reports-card-surface)",
    color: "var(--mp-ink)",
    minWidth: 0,
  },
  railToggleHead: {
    display: "inline-flex",
    alignItems: "center",
    gap: "var(--space-2)",
    flexShrink: 0,
  },
  railToggleSel: {
    flex: 1,
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-sm)",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    minWidth: 0,
  },
  railScrollNarrow: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    maxHeight: "60vh",
    overflowY: "auto",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3)",
    background: "var(--reports-rail-surface)",
    boxShadow: "var(--reports-section-shadow)",
  },
  railListBelowControls: {
    minWidth: 0,
  },
  railEmpty: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    textAlign: "center",
    gap: "var(--space-2)",
    padding: "var(--space-6) var(--space-4)",
    color: "var(--mp-mute)",
  },
  railEmptyText: {
    margin: 0,
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.5,
    maxWidth: 240,
  },
  railEmptyBtn: {
    appearance: "none",
    cursor: "pointer",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "transparent",
    color: "var(--mp-accent)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 600,
    fontFamily: "inherit",
    padding: "var(--space-1) var(--space-3)",
  },
  railHead: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-2)",
    paddingBottom: "var(--space-2)",
    borderBottom: "1px solid var(--reports-rule-strong)",
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
    border: "1px solid var(--reports-rule)",
    borderRadius: 999,
    padding: "0 7px",
    lineHeight: 1.7,
  },
};
