/**
 * ReportDetail — the report "reading view" (right pane of the Reports
 * workspace), in the "analyst memo" direction.
 *
 * Hierarchy: a compact provenance trust strip, then (when an analysis exists)
 * the Agent Team final synthesis as the serif lede, then per-role analyst
 * sections grouped into a PRIMARY portfolio-aware band (full editorial memo
 * blocks) and a SECONDARY public "market context" band (compact cards), with
 * deterministic scope/evidence/caveats as supporting provenance below. When no
 * analysis exists yet, the saved snapshot is shown honestly as a complete kept
 * analysis with an optional action to generate one.
 *
 * Within each primary memo block the agent narrative and the deterministic
 * evidence it cited are kept in explicitly labeled, visually distinct zones.
 *
 * Timestamps stay honest and distinct (snapshot saved vs report generated) and
 * live in the trust strip; the technical read/build time is not surfaced.
 *
 * Generation is manual and explicit; while a request is in flight the body shows
 * a transient generating affordance over the prior status (parent owns the
 * single-flight request) and the prior body stays visible — no skeleton flash.
 * Stale guard: a newly selected report shows a skeleton until its own detail
 * loads. All content is read from the saved record only.
 */
import { Badge, MpIcon } from "../shared/mp";
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
import ReportTrustStrip from "./ReportTrustStrip";
import ToolMediatedEvidence from "./ToolMediatedEvidence";
import {
  deriveReportStatus,
  humanizeCode,
  publicCoverage,
  reportStatusMeta,
  runCompleteness,
  runCompletenessLabel,
  splitRoles,
} from "./reportStatus";

export type ReportDetailStatus = "idle" | "loading" | "success" | "error";

interface ReportDetailProps {
  selectedThread: ReportThreadRead | null;
  detail: ReportThreadDetailRead | null;
  status: ReportDetailStatus;
  error: string | null;
  onRetry: () => void;
  isGenerating: boolean;
  generateError: string | null;
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

  return (
    <header style={styles.header}>
      <div style={styles.headerText}>
        <span style={styles.eyebrow}>{meta.label}</span>
        <h2 className="mp-display" style={styles.title}>
          {thread.title}
        </h2>
        <span style={styles.headerMeta}>
          <span style={styles.type}>{thread.report_type}</span>
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
  const { primary, context } = splitRoles(summary);
  const coverage = publicCoverage(summary);
  const hasRoles = (summary?.role_summaries.length ?? 0) > 0;
  const hasBriefing = Boolean(summary?.final_synthesis_markdown);
  // The state banner explains states that have no leading briefing (source
  // snapshot, agent unavailable, narrative withheld). When a blocked
  // deterministic draft now carries an incomplete-review briefing (P30A-T2A),
  // the briefing's own "review incomplete" framing leads instead, so the
  // generic "narrative was not generated" banner is suppressed to avoid a
  // contradiction. The report state stays visible in the header label/badge.
  const showStateBanner = !(reportStatus === "deterministic_draft" && hasBriefing);

  return (
    <div style={styles.body}>
      <ReportTrustStrip
        summary={summary}
        createdAt={detail.created_at}
        reportGeneratedAt={summary?.report_generated_at ?? null}
        scope={detail.scope_metadata}
      />

      {showStateBanner && (
        <StateBanner reportStatus={reportStatus} description={statusDescription} />
      )}

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

      {summary?.final_synthesis_markdown && (
        <FinalSynthesis summary={summary} reportStatus={reportStatus} />
      )}

      {hasRoles && (
        <section style={styles.roles} aria-label="Analyst sections">
          {primary.length > 0 && (
            <>
              <BandHeader label="Portfolio-aware roles" pill="Primary" tone="accent" />
              {primary.map((role) => (
                <AgentRoleSection key={role.role_name} role={role} variant="primary" />
              ))}
            </>
          )}

          {context.length > 0 && (
            <div style={styles.contextBand}>
              <div style={styles.contextBandHead}>
                <span style={styles.contextBandTitle}>Market context · public analysts</span>
                <span style={styles.secondaryPill}>Secondary</span>
                <span style={styles.bandSpacer} />
                {coverage.note && <span style={styles.contextNote}>{coverage.note}</span>}
              </div>
              <div style={styles.contextGrid}>
                {context.map((role) => (
                  <AgentRoleSection key={role.role_name} role={role} variant="context" />
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      <ReportProvenance
        status={reportStatus}
        scope={detail.scope_metadata}
        agentSummary={summary}
        publicEvidenceAttribution={detail.public_evidence_attribution}
        createdAt={detail.created_at}
        updatedAt={detail.updated_at}
      />

      {summary?.tool_run_artifact && (
        <ToolMediatedEvidence artifact={summary.tool_run_artifact} />
      )}
    </div>
  );
}

function BandHeader({ label, pill, tone }: { label: string; pill: string; tone: "accent" }) {
  return (
    <div style={styles.bandHead}>
      <span style={styles.bandTitle}>{label}</span>
      <span
        style={{
          ...styles.bandPill,
          color: `var(--mp-${tone})`,
          borderColor: `var(--mp-${tone}-line)`,
          backgroundColor: `var(--mp-${tone}-soft)`,
        }}
      >
        {pill}
      </span>
      <span style={styles.bandRule} />
    </div>
  );
}

function FinalSynthesis({
  summary,
  reportStatus,
}: {
  summary: SavedAgentTeamSummaryRead;
  reportStatus: AgentTeamReportStatus;
}) {
  if (!summary.final_synthesis_markdown) return null;
  // The briefing is the primary reading surface for the saved report; the
  // deterministic scope/evidence/provenance sit beneath it as supporting audit.
  // Framing is read-only and analysis-only — it surfaces what the review does
  // not cover, never a verdict or instruction to act. The eyebrow notes when the
  // underlying review did not complete (deterministic_draft) so the briefing is
  // read honestly; the synthesis prose itself is backend-owned (P30A-T2A).
  const eyebrow =
    reportStatus === "deterministic_draft"
      ? "Agent Team briefing · review incomplete · analysis only"
      : "Agent Team briefing · analysis only";
  return (
    <section style={styles.synthesis} aria-label="Agent Team briefing">
      <div style={styles.synthesisHead}>
        <span style={styles.synthesisEyebrow}>{eyebrow}</span>
        {summary.final_synthesis_authored_by && (
          <span style={styles.synthesisAuthor}>
            Authored by {humanizeCode(summary.final_synthesis_authored_by)}
          </span>
        )}
      </div>
      <h3 className="mp-display" style={styles.synthesisHeadline}>
        What you would be overlooking if you acted now
      </h3>
      <div style={styles.synthesisProse}>
        <ReportProse text={summary.final_synthesis_markdown} display color="var(--mp-ink)" />
      </div>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  pane: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-4)",
    padding: "var(--space-5)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-lg)",
    background: "var(--reports-reading-surface)",
    boxShadow: "var(--reports-section-shadow)",
    minWidth: 0,
  },
  header: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "var(--space-4)",
    flexWrap: "wrap",
    paddingBottom: "var(--space-4)",
    borderBottom: "1px solid var(--reports-rule-strong)",
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
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--reports-rule)",
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
    background: "var(--reports-card-surface)",
    boxShadow: "var(--reports-section-shadow)",
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
  synthesisHeadline: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-xl)",
    fontWeight: 500,
    lineHeight: 1.25,
    overflowWrap: "anywhere",
  },
  synthesisAuthor: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
  },
  synthesisProse: {
    maxWidth: "64ch",
    minWidth: 0,
  },
  roles: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-4)",
    minWidth: 0,
  },
  bandHead: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  bandTitle: {
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
  },
  bandPill: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    border: "1px solid var(--mp-accent-line)",
    borderRadius: 999,
    padding: "1px 8px",
  },
  bandRule: {
    flex: 1,
    height: 1,
    backgroundColor: "var(--reports-rule-strong)",
  },
  contextBand: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4)",
    background: "var(--reports-soft-surface)",
    border: "1px solid var(--reports-rule)",
    minWidth: 0,
  },
  contextBandHead: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    flexWrap: "wrap",
    minWidth: 0,
  },
  contextBandTitle: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
  },
  secondaryPill: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    border: "1px solid var(--reports-rule-strong)",
    borderRadius: 999,
    padding: "1px 8px",
  },
  bandSpacer: {
    flex: 1,
  },
  contextNote: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.5,
  },
  contextGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
    gap: "var(--space-3)",
    alignItems: "start",
    minWidth: 0,
  },
};
