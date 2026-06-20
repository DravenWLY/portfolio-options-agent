/**
 * ReportTrustStrip — a compact, always-visible provenance ribbon at the top of a
 * report: derived public coverage, the source "snapshot saved" time, the Agent
 * Team "report generated" time (when present), and the saved scope summary.
 *
 * Track A only: every value is read from the saved record (or derived from saved
 * role status). The structured coverage meter and per-section freshness/rights
 * chips from the design concept are Track B (they need an additive read field via
 * Codex C / Codex B) and are intentionally NOT rendered here. Deeper audit detail
 * lives in ReportProvenance's disclosure.
 */
import { MpIcon } from "../shared/mp";
import Timestamp from "../shared/Timestamp";
import type { ReportScopeMetadataRead } from "../../types/tradeReview";
import type { SavedAgentTeamSummaryRead } from "../../types/api";
import { publicCoverage } from "./reportStatus";

interface ReportTrustStripProps {
  summary: SavedAgentTeamSummaryRead | null;
  createdAt: string;
  reportGeneratedAt: string | null;
  scope: ReportScopeMetadataRead | null;
}

export default function ReportTrustStrip({
  summary,
  createdAt,
  reportGeneratedAt,
  scope,
}: ReportTrustStripProps) {
  const coverage = publicCoverage(summary);
  const savedScope = scope?.scope_summary_label ?? "Saved scope unavailable";

  return (
    <div role="note" aria-label="Provenance trust strip" style={styles.strip}>
      <span style={styles.item}>
        <MpIcon name="agent" size={14} style={styles.icon} />
        <span>{coverage.text}</span>
      </span>

      <span aria-hidden="true" style={styles.divider} />

      <span style={styles.item}>
        <MpIcon name="clock" size={14} style={styles.icon} />
        <Timestamp iso={createdAt} prefix="Snapshot saved" />
      </span>

      {reportGeneratedAt && (
        <span style={styles.item}>
          <MpIcon name="agent" size={14} style={{ ...styles.icon, color: "var(--mp-accent)" }} />
          <Timestamp iso={reportGeneratedAt} prefix="Report generated" />
        </span>
      )}

      <span aria-hidden="true" style={styles.divider} />

      <span style={styles.item}>
        <MpIcon name="lock" size={14} style={styles.icon} />
        <span style={styles.scope}>{savedScope}</span>
      </span>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  strip: {
    display: "flex",
    flexWrap: "wrap",
    alignItems: "center",
    gap: "8px 16px",
    padding: "var(--space-3) var(--space-4)",
    border: "1px solid var(--reports-rule-strong)",
    borderRadius: "var(--radius-md)",
    background: "var(--reports-trust-surface)",
    minWidth: 0,
  },
  item: {
    display: "inline-flex",
    alignItems: "center",
    gap: 7,
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink-2)",
    minWidth: 0,
  },
  icon: {
    color: "var(--mp-mute)",
    flexShrink: 0,
  },
  divider: {
    width: 1,
    height: 13,
    backgroundColor: "var(--reports-rule-strong)",
  },
  scope: {
    overflowWrap: "anywhere",
  },
};
