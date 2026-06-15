/**
 * ReportLibraryList — the saved-analysis index (left rail of the Reports
 * workspace). Each row leads with report identity, the saved timestamp, and an
 * honest indicator of whether an Agent Team analysis exists for that snapshot.
 *
 * Reads only saved record fields. The status indicator is derived from the
 * saved `agent_summary` via `deriveReportStatus`, never from current app state.
 */
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
  threads: ReportThreadRead[];
  selectedThreadId: string | null;
  onSelect: (threadId: string) => void;
}

export default function ReportLibraryList({
  threads,
  selectedThreadId,
  onSelect,
}: ReportLibraryListProps) {
  return (
    <nav style={styles.list} aria-label="Saved report library">
      {threads.map((thread) => {
        const isSelected = thread.id === selectedThreadId;
        const status = deriveReportStatus(thread);
        const meta = reportStatusMeta(status);
        const completeness = runCompleteness(thread.agent_summary);
        const showCompleteness =
          status === "full_agent_report" && completeness !== "full";

        return (
          <button
            key={thread.id}
            type="button"
            className="report-thread-button"
            aria-pressed={isSelected}
            aria-current={isSelected ? "true" : undefined}
            onClick={() => onSelect(thread.id)}
            style={{
              ...styles.card,
              ...(isSelected ? styles.cardSelected : undefined),
            }}
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
                  meta.tone === "mute"
                    ? "var(--mp-card-2)"
                    : `var(--mp-${meta.tone}-soft)`,
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
                color: isSelected ? "var(--mp-accent)" : "var(--mp-mute-2)",
              }}
            />
          </button>
        );
      })}
    </nav>
  );
}

const styles: Record<string, React.CSSProperties> = {
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    minWidth: 0,
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
    // Longhand border props so the selected-state `borderColor` override does
    // not trip React's shorthand/longhand style conflict warning.
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-4)",
    backgroundColor: "var(--mp-card)",
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
    // Longhand border props so the per-status `borderColor` override does not
    // trip React's shorthand/longhand style conflict warning.
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--mp-rule)",
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
