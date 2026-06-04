import type { AgentTeamAnalysisConsoleRead, AgentTeamRunStatus } from "../../types/agentTeam";
import type { ReviewActionabilityStatus } from "../../types/tradeReview";
import { Badge, type MpTone } from "../shared/mp";
import { MpIcon, type MpIconName } from "../shared/mp";

/**
 * AgentTeamRunSummary — compact top run/trade summary band (P20C-T5).
 *
 * Prototype-aligned 4-column grid showing: reviewing context, run reference,
 * overall status, and actionability. Uses MpIcon for status indicators.
 *
 * Uses only fields already returned by the backend. Does not invent
 * trade/account fields. Read-only, no execution controls.
 */

const RUN_STATUS_META: Record<
  AgentTeamRunStatus,
  { icon: MpIconName; label: string; tone: MpTone }
> = {
  completed: { icon: "check", label: "Completed", tone: "live" },
  partially_completed: { icon: "alert", label: "Partially completed", tone: "stale" },
  failed: { icon: "x", label: "Failed", tone: "block" },
};

const ACTIONABILITY_LABEL: Record<ReviewActionabilityStatus, string> = {
  normal_review: "Normal review",
  analysis_only: "Analysis only",
  manual_confirmation_required: "Manual confirmation required",
  blocked_stale_broker_snapshot: "Blocked — stale broker snapshot",
  blocked_stale_market_quote: "Blocked — stale market quote",
  blocked_unknown_freshness: "Blocked — unknown freshness",
  blocked_provider_error: "Blocked — provider error",
};

function actionabilityTone(status: ReviewActionabilityStatus): MpTone {
  if (status.startsWith("blocked")) return "block";
  if (status === "manual_confirmation_required") return "stale";
  if (status === "analysis_only") return "info";
  return "live";
}

export default function AgentTeamRunSummary({
  data,
}: {
  data: AgentTeamAnalysisConsoleRead;
}) {
  const m = RUN_STATUS_META[data.run_status];
  const hasMock = data.role_outputs.some((r) => r.is_mock);

  return (
    <section style={styles.band} aria-label="Agent-team run summary">
      <div style={styles.grid}>
        {/* Column 1: Reviewing */}
        <div>
          <p style={styles.eyebrow}>Reviewing</p>
          <p style={styles.flowLabel}>{data.review_flow_label}</p>
        </div>

        {/* Column 2: Run reference */}
        <div>
          <p style={styles.eyebrow}>Run reference</p>
          <p style={styles.mono}>{data.run_reference}</p>
          <p style={styles.subMeta}>workflow {data.workflow_version}</p>
        </div>

        {/* Column 3: Overall status */}
        <div>
          <p style={styles.eyebrow}>Overall status</p>
          <Badge tone={m.tone} dot>
            <MpIcon name={m.icon} size={10} style={{ marginRight: 3, verticalAlign: "middle" }} />
            {m.label}
          </Badge>
          {hasMock && (
            <Badge tone="info" dot>mock provider</Badge>
          )}
        </div>

        {/* Column 4: Actionability */}
        <div>
          <p style={styles.eyebrow}>Actionability</p>
          <Badge tone={actionabilityTone(data.review_actionability_status)} dot>
            {ACTIONABILITY_LABEL[data.review_actionability_status]}
          </Badge>
        </div>
      </div>

      <p style={styles.note}>
        <MpIcon name="info" size={10} style={{ verticalAlign: "middle", marginRight: 3, color: "var(--mp-mute)" }} />
        Read-only analysis output · Generated {data.generated_at}
      </p>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  band: {
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-5)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1.4fr 1fr 1fr 1fr",
    gap: "var(--space-4)",
    alignItems: "start",
  },
  eyebrow: {
    margin: 0,
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
    color: "var(--mp-mute)",
    marginBottom: 4,
  },
  flowLabel: {
    margin: 0,
    fontSize: "var(--font-size-md)",
    fontWeight: 500,
    color: "var(--mp-ink)",
    fontFamily: "var(--mp-font-display, serif)",
    letterSpacing: "-0.005em",
  },
  mono: {
    margin: 0,
    fontSize: "var(--font-size-sm)",
    fontFamily: "var(--mp-font-mono, monospace)",
    color: "var(--mp-ink-2)",
    fontVariantNumeric: "tabular-nums",
  },
  subMeta: {
    margin: 0,
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    marginTop: 2,
  },
  note: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: 0,
    lineHeight: 1.6,
    fontStyle: "italic",
  },
};
