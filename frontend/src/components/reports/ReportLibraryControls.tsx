/**
 * ReportLibraryControls — search + status filter for the saved-analysis rail.
 *
 * Pure presentational; the parent owns the query/filter state and applies them
 * client-side over the already-loaded threads (no backend call, no new field).
 * Search matches title/report-type only (display-safe saved fields); the status
 * filter operates on the derived report status. Status options stay text labels
 * — never color-only.
 */
import { MpIcon } from "../shared/mp";
import { REPORT_FILTER_OPTIONS, type ReportFilterValue } from "./reportStatus";

interface ReportLibraryControlsProps {
  query: string;
  onQueryChange: (value: string) => void;
  statusFilter: ReportFilterValue;
  onStatusChange: (value: ReportFilterValue) => void;
}

export default function ReportLibraryControls({
  query,
  onQueryChange,
  statusFilter,
  onStatusChange,
}: ReportLibraryControlsProps) {
  return (
    <div style={styles.wrap}>
      <div style={styles.searchWrap}>
        <MpIcon name="search" size={14} style={styles.searchIcon} />
        <input
          type="search"
          className="report-rail-search"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search title or type"
          aria-label="Search saved reports"
          style={styles.input}
        />
        {query !== "" && (
          <button
            type="button"
            className="report-rail-clear"
            onClick={() => onQueryChange("")}
            aria-label="Clear search"
            style={styles.clearBtn}
          >
            <MpIcon name="x" size={13} />
          </button>
        )}
      </div>
      <select
        value={statusFilter}
        className="report-rail-select"
        onChange={(e) => onStatusChange(e.target.value as ReportFilterValue)}
        aria-label="Filter saved reports by status"
        style={styles.select}
      >
        {REPORT_FILTER_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  searchWrap: {
    position: "relative",
    display: "flex",
    alignItems: "center",
    minWidth: 0,
  },
  searchIcon: {
    position: "absolute",
    left: 10,
    color: "var(--mp-mute)",
    pointerEvents: "none",
  },
  input: {
    // border + hover/focus live in the .report-rail-search class so the
    // accent ring can override the rest-state border.
    width: "100%",
    minWidth: 0,
    boxSizing: "border-box",
    appearance: "none",
    font: "inherit",
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink)",
    background: "var(--reports-card-surface)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) 30px var(--space-2) 30px",
  },
  clearBtn: {
    // color + hover/focus live in the .report-rail-clear class.
    position: "absolute",
    right: 6,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    appearance: "none",
    border: 0,
    background: "transparent",
    cursor: "pointer",
    padding: 4,
    borderRadius: "var(--radius-sm)",
  },
  select: {
    // border + hover/focus live in the .report-rail-select class.
    width: "100%",
    minWidth: 0,
    boxSizing: "border-box",
    appearance: "none",
    font: "inherit",
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink-2)",
    background: "var(--reports-card-surface)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-3)",
    cursor: "pointer",
  },
};
