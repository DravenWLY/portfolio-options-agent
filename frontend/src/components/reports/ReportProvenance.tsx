/**
 * ReportProvenance — supporting evidence + audit/provenance for a saved report.
 *
 * Deliberately NOT the hero. Carries the deterministic scope (via the existing
 * ReportScopeSummary), the keys-only evidence the analysis cited, and a compact
 * audit disclosure (run/provider status, warning codes, evidence schema
 * version, generated/saved timestamps). All values come from the saved record;
 * none are inferred from current state, and no raw identifiers/values appear.
 */
import { MpIcon } from "../shared/mp";
import Timestamp from "../shared/Timestamp";
import ReportScopeSummary from "./ReportScopeSummary";
import type { ReportScopeMetadataRead } from "../../types/tradeReview";
import type { AgentTeamReportStatus, SavedAgentTeamSummaryRead } from "../../types/api";
import { evidenceKeyLabel, humanizeCode } from "./reportStatus";

interface ReportProvenanceProps {
  status: AgentTeamReportStatus;
  scope: ReportScopeMetadataRead | null;
  agentSummary: SavedAgentTeamSummaryRead | null;
  /** Source snapshot saved time (immutable). */
  createdAt: string;
  /** Saved-record last-updated time (technical). */
  updatedAt: string;
}

export default function ReportProvenance({
  status,
  scope,
  agentSummary,
  createdAt,
  updatedAt,
}: ReportProvenanceProps) {
  const evidenceRefs = agentSummary?.evidence_references ?? [];
  const warningCodes = agentSummary?.warning_codes ?? [];

  return (
    <section style={styles.wrap} aria-label="Supporting evidence and provenance">
      <header style={styles.heading}>
        <MpIcon name="shield" size={15} style={styles.headingIcon} />
        <h3 style={styles.headingText}>Supporting evidence &amp; provenance</h3>
      </header>
      <p style={styles.note}>
        Deterministic scope, freshness, and caveats are read from this saved
        report only. The current account selector does not expand, narrow, or
        rename them.
      </p>

      <ReportScopeSummary
        scope={scope}
        unavailableText="This report does not include a saved evidence snapshot, so no Agent Team report can be generated from it."
      />

      {evidenceRefs.length > 0 && (
        <div style={styles.block}>
          <span style={styles.blockLabel}>Evidence cited (keys)</span>
          <ul style={styles.chipList}>
            {evidenceRefs.map((key) => (
              <li key={key} style={styles.evidenceChip}>
                {evidenceKeyLabel(key)}
              </li>
            ))}
          </ul>
        </div>
      )}

      <details className="mp-disclosure" style={styles.details}>
        <summary style={styles.summary}>
          <MpIcon
            name="chevron-r"
            size={14}
            className="mp-disclosure-chevron"
            style={{ color: "var(--mp-mute)" }}
          />
          Audit detail
        </summary>
        <dl style={styles.auditGrid}>
          <AuditRow label="Report state" value={humanizeCode(status)} />
          {agentSummary && (
            <>
              <AuditRow label="Run status" value={humanizeCode(agentSummary.run_status)} />
              <AuditRow label="Provider mode" value={humanizeCode(agentSummary.provider_mode)} mono />
              {agentSummary.final_synthesis_authored_by && (
                <AuditRow
                  label="Synthesis author"
                  value={humanizeCode(agentSummary.final_synthesis_authored_by)}
                />
              )}
              {agentSummary.evidence_schema_version && (
                <AuditRow
                  label="Evidence schema"
                  value={agentSummary.evidence_schema_version}
                  mono
                />
              )}
            </>
          )}
          <div style={styles.auditRow}>
            <dt style={styles.auditLabel}>Snapshot saved</dt>
            <dd style={styles.auditValue}>
              <Timestamp iso={createdAt} prefix="" />
            </dd>
          </div>
          {agentSummary?.report_generated_at && (
            <div style={styles.auditRow}>
              <dt style={styles.auditLabel}>Report generated</dt>
              <dd style={styles.auditValue}>
                <Timestamp iso={agentSummary.report_generated_at} prefix="" />
              </dd>
            </div>
          )}
          <div style={styles.auditRow}>
            <dt style={styles.auditLabel}>Saved record updated</dt>
            <dd style={styles.auditValue}>
              <Timestamp iso={updatedAt} prefix="" />
            </dd>
          </div>
        </dl>

        {warningCodes.length > 0 && (
          <div style={styles.block}>
            <span style={styles.blockLabel}>Report warnings</span>
            <ul style={styles.codeList}>
              {warningCodes.map((code) => (
                <li key={code} style={styles.codeChip} title={code}>
                  {code}
                </li>
              ))}
            </ul>
          </div>
        )}
      </details>
    </section>
  );
}

function AuditRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={styles.auditRow}>
      <dt style={styles.auditLabel}>{label}</dt>
      <dd style={{ ...styles.auditValue, ...(mono ? styles.auditValueMono : undefined) }}>
        {value}
      </dd>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-5)",
    background: "var(--reports-soft-surface)",
    minWidth: 0,
  },
  heading: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  headingIcon: {
    color: "var(--mp-mute)",
    flexShrink: 0,
  },
  headingText: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-md)",
    fontWeight: 600,
  },
  note: {
    margin: 0,
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.6,
  },
  block: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    minWidth: 0,
  },
  blockLabel: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
  },
  chipList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
  },
  evidenceChip: {
    color: "var(--mp-ink-2)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "2px 8px",
    fontSize: "var(--font-size-xs)",
    background: "var(--reports-card-surface)",
    overflowWrap: "anywhere",
  },
  details: {
    minWidth: 0,
  },
  summary: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    cursor: "pointer",
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  auditGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "var(--space-2)",
    margin: "var(--space-3) 0 var(--space-2)",
  },
  auditRow: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-3)",
    background: "var(--reports-card-surface)",
    minWidth: 0,
  },
  auditLabel: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.05em",
    textTransform: "uppercase",
  },
  auditValue: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-sm)",
    overflowWrap: "anywhere",
  },
  auditValueMono: {
    fontFamily: "var(--mp-font-mono)",
    fontSize: "var(--font-size-xs)",
  },
  codeList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
  },
  codeChip: {
    color: "var(--mp-mute)",
    background: "var(--reports-card-surface)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "1px 6px",
    fontSize: "var(--font-size-xs)",
    fontFamily: "var(--mp-font-mono)",
    overflowWrap: "anywhere",
  },
};
