/**
 * ReportDetail — the report "reading view" (right pane of the Reports
 * workspace). When an Agent Team analysis exists it is the primary content:
 * final synthesis first, then per-role analyst sections, with deterministic
 * scope/evidence/caveats as supporting provenance below. When no analysis
 * exists yet, the saved snapshot is shown honestly as a complete kept analysis
 * with an optional action to generate one.
 *
 * Timestamps are kept honest and distinct: the source snapshot's saved time and
 * (when a report exists) the Agent Team generation time are shown separately so
 * neither is mistaken for the other. The technical read/build time is not
 * surfaced.
 *
 * Generation is manual and explicit. While a request is in flight the body shows
 * a transient "generating" affordance over the last persisted status (the parent
 * owns the single-flight request), and the prior body stays visible — no
 * skeleton flash. Stale guard: a newly selected report shows a skeleton until its
 * own detail loads; the previous report's body is never shown for it.
 *
 * All content is read from the saved record only; nothing is reconstructed from
 * the current account selector, Account Details, route, or cache.
 */
import { Badge, MpIcon } from "../shared/mp";
import Timestamp from "../shared/Timestamp";
import { EmptyState, ErrorState, LoadingSkeleton } from "../shared/StateViews";
import type {
  AgentTeamReportStatus,
  ReportThreadDetailRead,
  ReportThreadRead,
  SavedAgentTeamSummaryRead,
} from "../../types/api";
import AgentRoleSection from "./AgentRoleSection";
import GenerateAgentTeamReport from "./GenerateAgentTeamReport";
import ReportProse from "./ReportProse";
import ReportProvenance from "./ReportProvenance";
import {
  coverageNote,
  deriveReportStatus,
  humanizeCode,
  reportStatusMeta,
  runCompleteness,
  runCompletenessLabel,
} from "./reportStatus";

export type ReportDetailStatus = "idle" | "loading" | "success" | "error";

interface ReportDetailProps {
  selectedThread: ReportThreadRead | null;
  detail: ReportThreadDetailRead | null;
  status: ReportDetailStatus;
  error: string | null;
  onRetry: () => void;
  /** Transient: a generation request for this report is in flight. */
  isGenerating: boolean;
  /** Sanitized generation error for this report, or null. */
  generateError: string | null;
  /** Explicit, manual trigger to run/re-run the Agent Team report. */
  onGenerate: () => void;
}

export default function ReportDetail({
  selectedThread,
  detail,
  status,
  error,
  onRetry,
  isGenerating,
  generateError,
  onGenerate,
}: ReportDetailProps) {
  if (!selectedThread) {
    return (
      <section style={styles.pane} aria-label="Opened report">
        <EmptyState
          icon={<MpIcon name="reports" size={28} />}
          title="Select a saved report"
          body="Choose a saved analysis from the library to read its Agent Team report and the deterministic evidence behind it."
        />
      </section>
    );
  }

  const detailMatchesSelection = Boolean(detail && detail.id === selectedThread.id);
  const reportStatus = deriveReportStatus(
    detailMatchesSelection && detail ? detail : selectedThread,
  );
  const headerMeta = reportStatusMeta(reportStatus);
  // Keep the matched body visible during a background refetch (e.g. after
  // generation) so the transient state sits over the prior status; only show a
  // skeleton when we have no matching detail yet (stale guard for new
  // selections).
  const showBody = detailMatchesSelection && detail;

  return (
    <section style={styles.pane} aria-label="Opened report">
      <ReportHeader thread={selectedThread} reportStatus={reportStatus} />

      {!showBody && status === "error" && (
        <ErrorState message={error ?? "Failed to load the report."} onRetry={onRetry} />
      )}
      {!showBody && status !== "error" && (
        <LoadingSkeleton rows={6} label="Loading report…" />
      )}
      {showBody && detail && (
        <ReportBody
          detail={detail}
          reportStatus={reportStatus}
          statusDescription={headerMeta.description}
          isGenerating={isGenerating}
          generateError={generateError}
          onGenerate={onGenerate}
        />
      )}
    </section>
  );
}

function ReportHeader({
  thread,
  reportStatus,
}: {
  thread: ReportThreadRead;
  reportStatus: AgentTeamReportStatus;
}) {
  const meta = reportStatusMeta(reportStatus);
  const completeness = runCompleteness(thread.agent_summary);
  const showCompleteness = reportStatus === "full_agent_report" && completeness !== "full";
  const reportGeneratedAt = thread.agent_summary?.report_generated_at ?? null;

  return (
    <header style={styles.header}>
      <div style={styles.headerText}>
        <span style={styles.eyebrow}>{meta.label}</span>
        <h2 className="mp-display" style={styles.title}>
          {thread.title}
        </h2>
        <span style={styles.headerMeta}>
          <span style={styles.type}>{thread.report_type}</span>
          <span aria-hidden="true" style={styles.dot}>·</span>
          <Timestamp iso={thread.created_at} prefix="Snapshot saved" />
          {reportGeneratedAt && (
            <>
              <span aria-hidden="true" style={styles.dot}>·</span>
              <Timestamp iso={reportGeneratedAt} prefix="Report generated" />
            </>
          )}
        </span>
      </div>
      <div style={styles.headerBadges}>
        <Badge tone={meta.tone} dot={reportStatus !== "source_snapshot"}>
          {meta.chipLabel}
        </Badge>
        {showCompleteness && (
          <Badge tone="stale" dot={false}>
            {runCompletenessLabel(completeness)}
          </Badge>
        )}
      </div>
    </header>
  );
}

function StateBanner({
  reportStatus,
  description,
}: {
  reportStatus: AgentTeamReportStatus;
  description: string;
}) {
  const meta = reportStatusMeta(reportStatus);
  // Mute states (source_snapshot / agent_unavailable) carry no alert tone, so
  // the icon takes the readable body-ink color instead of the faint rule color
  // — clearly legible in both themes while staying neutral. Toned states keep
  // their semantic color.
  const iconColor = meta.tone === "mute" ? "var(--mp-ink-2)" : `var(--mp-${meta.tone})`;
  return (
    <div
      role="note"
      style={{
        ...styles.banner,
        borderColor:
          meta.tone === "mute" ? "var(--mp-rule)" : `var(--mp-${meta.tone}-line, var(--mp-${meta.tone}))`,
        backgroundColor: meta.tone === "mute" ? "var(--mp-card-2)" : `var(--mp-${meta.tone}-soft)`,
      }}
    >
      <span aria-hidden="true" style={{ ...styles.bannerIcon, color: iconColor }}>
        <MpIcon name={meta.icon} size={16} />
      </span>
      <p style={styles.bannerText}>{description}</p>
    </div>
  );
}

function ReportBody({
  detail,
  reportStatus,
  statusDescription,
  isGenerating,
  generateError,
  onGenerate,
}: {
  detail: ReportThreadDetailRead;
  reportStatus: AgentTeamReportStatus;
  statusDescription: string;
  isGenerating: boolean;
  generateError: string | null;
  onGenerate: () => void;
}) {
  const summary = detail.agent_summary;
  const hasScope = detail.scope_metadata !== null;
  const canGenerate = reportStatus === "source_snapshot" && hasScope;
  const canRetry =
    (reportStatus === "agent_unavailable" || reportStatus === "validation_failed") && hasScope;
  const note = coverageNote(summary);

  return (
    <div style={styles.body}>
      <StateBanner reportStatus={reportStatus} description={statusDescription} />

      {canGenerate && (
        <GenerateAgentTeamReport
          variant="generate"
          generating={isGenerating}
          error={generateError}
          onGenerate={onGenerate}
        />
      )}
      {canRetry && (
        <GenerateAgentTeamReport
          variant="retry"
          generating={isGenerating}
          error={generateError}
          onGenerate={onGenerate}
        />
      )}

      {summary?.final_synthesis_markdown && <FinalSynthesis summary={summary} />}

      {summary && summary.role_summaries.length > 0 && (
        <section style={styles.rolesSection} aria-label="Analyst sections">
          <div style={styles.sectionHeading}>
            <MpIcon name="agent" size={15} style={styles.sectionIcon} />
            <h3 style={styles.sectionTitle}>Analyst sections</h3>
            <span style={styles.sectionCount}>{summary.role_summaries.length}</span>
          </div>
          {note && (
            <p style={styles.coverageNote}>
              <MpIcon name="info" size={13} style={styles.coverageIcon} />
              <span>{note}</span>
            </p>
          )}
          <div style={styles.rolesGrid}>
            {summary.role_summaries.map((role) => (
              <AgentRoleSection key={role.role_name} role={role} />
            ))}
          </div>
        </section>
      )}

      <ReportProvenance
        status={reportStatus}
        scope={detail.scope_metadata}
        agentSummary={summary}
        createdAt={detail.created_at}
        updatedAt={detail.updated_at}
      />
    </div>
  );
}

function FinalSynthesis({ summary }: { summary: SavedAgentTeamSummaryRead }) {
  if (!summary.final_synthesis_markdown) return null;
  return (
    <section style={styles.synthesis} aria-label="Final synthesis">
      <div style={styles.synthesisHead}>
        <span style={styles.synthesisEyebrow}>Final synthesis · Analysis only</span>
        {summary.final_synthesis_authored_by && (
          <span style={styles.synthesisAuthor}>
            Authored by {humanizeCode(summary.final_synthesis_authored_by)}
          </span>
        )}
      </div>
      <div style={styles.synthesisProse}>
        <ReportProse text={summary.final_synthesis_markdown} />
      </div>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  pane: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-4)",
    minWidth: 0,
  },
  header: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "var(--space-4)",
    flexWrap: "wrap",
    paddingBottom: "var(--space-4)",
    borderBottom: "1px solid var(--mp-rule)",
    minWidth: 0,
  },
  headerText: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    minWidth: 0,
  },
  eyebrow: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
  title: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-2xl)",
    fontWeight: 500,
    lineHeight: 1.2,
    overflowWrap: "anywhere",
  },
  headerMeta: {
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
  headerBadges: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    flexWrap: "wrap",
    justifyContent: "flex-end",
  },
  body: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-4)",
    minWidth: 0,
  },
  banner: {
    display: "flex",
    gap: "var(--space-3)",
    alignItems: "flex-start",
    // Longhand border props (not the `border` shorthand) so the per-status
    // `borderColor` override below does not trip React's shorthand/longhand
    // style conflict warning.
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-4)",
    minWidth: 0,
  },
  bannerIcon: {
    flexShrink: 0,
    marginTop: 1,
  },
  bannerText: {
    margin: 0,
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.6,
  },
  synthesis: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    border: "1px solid var(--mp-accent-line)",
    borderLeft: "3px solid var(--mp-accent)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-5) var(--space-6)",
    backgroundColor: "var(--mp-card)",
    minWidth: 0,
  },
  synthesisHead: {
    display: "flex",
    alignItems: "baseline",
    justifyContent: "space-between",
    gap: "var(--space-3)",
    flexWrap: "wrap",
  },
  synthesisEyebrow: {
    color: "var(--mp-accent-ink)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
  synthesisAuthor: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
  },
  synthesisProse: {
    maxWidth: "64ch",
    minWidth: 0,
  },
  rolesSection: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    minWidth: 0,
  },
  sectionHeading: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  sectionIcon: {
    color: "var(--mp-mute)",
    flexShrink: 0,
  },
  sectionTitle: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-md)",
    fontWeight: 600,
  },
  sectionCount: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontVariantNumeric: "tabular-nums",
    border: "1px solid var(--mp-rule)",
    borderRadius: 999,
    padding: "0 7px",
    lineHeight: 1.7,
  },
  coverageNote: {
    margin: 0,
    display: "flex",
    gap: 6,
    alignItems: "flex-start",
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.6,
  },
  coverageIcon: {
    color: "var(--mp-mute-2)",
    flexShrink: 0,
    marginTop: 2,
  },
  rolesGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: "var(--space-3)",
    alignItems: "start",
    minWidth: 0,
  },
};
