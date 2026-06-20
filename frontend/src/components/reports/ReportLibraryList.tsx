/**
 * ReportLibraryList — the saved-analysis index (left rail of the Reports
 * workspace). Newest-first, grouped into date buckets (Today / Earlier this week
 * / Earlier this month / by month) with sticky group headers so it reads as a
 * calm memo archive rather than a flat log as history grows.
 *
 * Each row leads with report identity, the saved timestamp, an honest
 * Agent-Team-analysis status indicator, and a muted secondary line (saved scope
 * hint) so near-identical rows disambiguate without opening them.
 *
 * Reads only saved record fields. Status is derived from the saved
 * `agent_summary` via `deriveReportStatus`, never from current app state. The
 * scrolling/containment is owned by the parent rail.
 */
import { useMemo } from "react";
import { Badge, MpIcon } from "../shared/mp";
import Timestamp from "../shared/Timestamp";
import type { ReportThreadRead } from "../../types/api";
import {
  deriveReportStatus,
  reportStatusMeta,
  runCompleteness,
  runCompletenessLabel,
} from "./reportStatus";

interface ReportLibraryListProps {
  /** Newest-first (by saved time). */
  threads: ReportThreadRead[];
  selectedThreadId: string | null;
  onSelect: (threadId: string) => void;
}

interface ThreadGroup {
  key: string;
  label: string;
  items: ReportThreadRead[];
}

function dateBucket(iso: string): { key: string; label: string } {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return { key: "unknown", label: "Saved earlier" };
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDays = Math.floor((startOfToday.getTime() - day.getTime()) / 86_400_000);
  if (diffDays <= 0) return { key: "today", label: "Today" };
  if (diffDays < 7) return { key: "week", label: "Earlier this week" };
  if (d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()) {
    return { key: "month", label: "Earlier this month" };
  }
  return {
    key: `m-${d.getFullYear()}-${d.getMonth()}`,
    label: d.toLocaleString("en-US", { month: "long", year: "numeric" }),
  };
}

/** Group newest-first threads into date buckets, preserving order. */
function groupThreads(threads: ReportThreadRead[]): ThreadGroup[] {
  const groups: ThreadGroup[] = [];
  const index = new Map<string, ThreadGroup>();
  for (const thread of threads) {
    const bucket = dateBucket(thread.created_at);
    let group = index.get(bucket.key);
    if (!group) {
      group = { key: bucket.key, label: bucket.label, items: [] };
      index.set(bucket.key, group);
      groups.push(group);
    }
    group.items.push(thread);
  }
  return groups;
}

export default function ReportLibraryList({
  threads,
  selectedThreadId,
  onSelect,
}: ReportLibraryListProps) {
  const groups = useMemo(() => groupThreads(threads), [threads]);

  return (
    <nav style={styles.list} aria-label="Saved report library">
      {groups.map((group) => (
        <div key={group.key} style={styles.group}>
          <div style={styles.groupHeader}>
            <span style={styles.groupLabel}>{group.label}</span>
            <span style={styles.groupCount}>{group.items.length}</span>
          </div>
          {group.items.map((thread) => (
            <ReportRow
              key={thread.id}
              thread={thread}
              selected={thread.id === selectedThreadId}
              onSelect={onSelect}
            />
          ))}
        </div>
      ))}
    </nav>
  );
}

function ReportRow({
  thread,
  selected,
  onSelect,
}: {
  thread: ReportThreadRead;
  selected: boolean;
  onSelect: (threadId: string) => void;
}) {
  const status = deriveReportStatus(thread);
  const meta = reportStatusMeta(status);
  const completeness = runCompleteness(thread.agent_summary);
  const showCompleteness = status === "full_agent_report" && completeness !== "full";
  const scopeHint = thread.scope_metadata?.scope_summary_label ?? null;

  return (
    <button
      type="button"
      className="report-thread-button"
      aria-pressed={selected}
      aria-current={selected ? "true" : undefined}
      onClick={() => onSelect(thread.id)}
      style={{ ...styles.card, ...(selected ? styles.cardSelected : undefined) }}
    >
      <span
        aria-hidden="true"
        style={{
          ...styles.iconChip,
          color: `var(--mp-${meta.tone === "mute" ? "mute" : meta.tone})`,
          borderColor:
            meta.tone === "mute"
              ? "var(--mp-rule)"
              : `var(--mp-${meta.tone}-line, var(--mp-${meta.tone}))`,
          backgroundColor:
            meta.tone === "mute" ? "var(--mp-card-2)" : `var(--mp-${meta.tone}-soft)`,
        }}
      >
        <MpIcon name={meta.icon} size={15} />
      </span>

      <span style={styles.body}>
        <span style={styles.title}>{thread.title}</span>
        <span style={styles.meta}>
          <span style={styles.type}>{thread.report_type}</span>
          <span aria-hidden="true" style={styles.dot}>·</span>
          <Timestamp iso={thread.created_at} prefix="Saved" />
        </span>
        {scopeHint && <span style={styles.scopeHint}>{scopeHint}</span>}
        <span style={styles.chips}>
          <Badge tone={meta.tone} dot={status !== "source_snapshot"}>
            {meta.chipLabel}
          </Badge>
          {showCompleteness && (
            <Badge tone="stale" dot={false}>
              {runCompletenessLabel(completeness)}
            </Badge>
          )}
        </span>
      </span>

      <MpIcon
        name="chevron-r"
        size={16}
        style={{
          ...styles.chevron,
          color: selected ? "var(--mp-accent)" : "var(--mp-mute-2)",
        }}
      />
    </button>
  );
}

const styles: Record<string, React.CSSProperties> = {
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    minWidth: 0,
  },
  group: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  groupHeader: {
    position: "sticky",
    top: 0,
    zIndex: 1,
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    padding: "var(--space-1) 2px",
    background: "var(--reports-rail-surface)",
  },
  groupLabel: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    fontFamily: "var(--mp-font-mono)",
  },
  groupCount: {
    color: "var(--mp-mute-2)",
    fontSize: "var(--font-size-xs)",
    fontVariantNumeric: "tabular-nums",
  },
  card: {
    appearance: "none",
    font: "inherit",
    textAlign: "left",
    cursor: "pointer",
    display: "grid",
    gridTemplateColumns: "auto minmax(0, 1fr) auto",
    alignItems: "start",
    gap: "var(--space-3)",
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--reports-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-4)",
    backgroundColor: "var(--reports-card-surface)",
    color: "var(--mp-ink)",
    transition: "border-color 120ms ease, background-color 120ms ease",
    minWidth: 0,
  },
  cardSelected: {
    borderColor: "var(--mp-accent-line)",
    backgroundColor: "var(--mp-accent-soft)",
    boxShadow: "inset 3px 0 0 var(--mp-accent)",
  },
  iconChip: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: 30,
    height: 30,
    borderRadius: "var(--radius-sm)",
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--reports-rule)",
    flexShrink: 0,
    marginTop: 1,
  },
  body: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    minWidth: 0,
  },
  title: {
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-md)",
    fontWeight: 600,
    lineHeight: 1.3,
    overflowWrap: "anywhere",
  },
  meta: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    flexWrap: "wrap",
    minWidth: 0,
  },
  type: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontFamily: "var(--mp-font-mono)",
    overflowWrap: "anywhere",
  },
  dot: {
    color: "var(--mp-mute-2)",
  },
  scopeHint: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.4,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    maxWidth: "100%",
  },
  chips: {
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
    marginTop: 2,
  },
  chevron: {
    marginTop: 8,
    flexShrink: 0,
  },
};
