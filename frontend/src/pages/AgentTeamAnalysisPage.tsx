import { useState } from "react";
import { agentTeamApi } from "../api/agentTeam";
import { ApiRequestError } from "../api/client";
import TradeReviewForm from "../components/trade-review/TradeReviewForm";
import AgentTeamPipelineRail from "../components/agent-team/AgentTeamPipelineRail";
import AgentTeamTranscript from "../components/agent-team/AgentTeamTranscript";
import AgentTeamEvidenceRail from "../components/agent-team/AgentTeamEvidenceRail";
import AgentTeamRunSummary from "../components/agent-team/AgentTeamRunSummary";
import AgentTeamComposerPlaceholder from "../components/agent-team/AgentTeamComposerPlaceholder";
import { LoadingSkeleton, ErrorState, EmptyState } from "../components/shared/StateViews";
import { Badge, PageHeader, SafetyStrip } from "../components/shared/mp";
import { MpIcon } from "../components/shared/mp";
import type { TradeReviewSubmission } from "../types/tradeReview";
import type { AgentTeamAnalysisConsoleRead } from "../types/agentTeam";

/**
 * AgentTeamAnalysisPage — prototype-aligned Agent Console (P20C-T5).
 *
 * Layout (success state):
 *   [ top: run summary band ]
 *   [ left: pipeline rail + re-run form | middle: transcript + composer | right: evidence rail ]
 *
 * Layout (idle/loading/error):
 *   [ form 320 | status placeholder 1fr ]
 *
 * Backend wiring unchanged: POST /agent-team/trade-review-analysis/preview.
 * Single network path. No localStorage / sessionStorage writes for analysis,
 * role, prompt, provider, credential, or account data.
 *
 * The disabled composer is visually attached to the bottom of the middle
 * transcript panel. It makes no API calls and stores nothing.
 * Follow-up controls are disabled placeholders and are not active in this
 * build.
 */

type Status = "idle" | "loading" | "success" | "error";

export default function AgentTeamAnalysisPage() {
  const [status, setStatus] = useState<Status>("idle");
  const [data, setData] = useState<AgentTeamAnalysisConsoleRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(submission: TradeReviewSubmission) {
    if (submission.kind !== "portfolio") {
      setError("The agent-team analysis console only accepts portfolio-backed submissions.");
      setStatus("error");
      return;
    }
    setStatus("loading");
    setBusy(true);
    setError(null);
    try {
      const result = await agentTeamApi.previewTradeReviewAnalysis(submission.payload);
      setData(result);
      setStatus("success");
    } catch (err) {
      const msg =
        err instanceof ApiRequestError ? err.detail :
        err instanceof Error ? err.message :
        "Agent-team analysis request failed.";
      setError(msg);
      setStatus("error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Workspace · agent console"
        title="Agent team analysis"
        sub="Five role-separated agents review the proposed trade in fixed order. Deterministic facts come from the backend; agent commentary sits next to them, never instead of them. Analysis only — not advice, not a recommendation."
        right={
          <>
            <Badge tone="info" dot>mock provider</Badge>
            <Badge tone="mute" dot={false}>analysis-only</Badge>
          </>
        }
      />

      {status === "success" && data ? (
        /* ── Prototype 5-zone layout ─────────────────────────────── */
        <div style={styles.consoleWrap}>
          {/* 1. Top run summary band */}
          <AgentTeamRunSummary data={data} />
          {data.run_status === "partially_completed" && <PartialBanner />}

          {/* 2–4. Three-column body: rail | transcript+composer | evidence.
               Responsive breakpoint in globals.css collapses to single-column
               at constrained widths (≤1120px). */}
          <div className="mp-agent-console-body">
            <aside className="mp-ac-rail">
              <AgentTeamPipelineRail data={data} />
              {/* Inline form for re-run */}
              <TradeReviewForm onSubmit={handleSubmit} busy={busy} hideSyntheticMode />
            </aside>

            <section className="mp-ac-transcript">
              <AgentTeamTranscript
                data={data}
                footer={<AgentTeamComposerPlaceholder />}
              />
            </section>

            <aside className="mp-ac-evidence">
              <AgentTeamEvidenceRail data={data} />
            </aside>
          </div>
        </div>
      ) : (
        /* ── Pre-run layout: form + status ───────────────────────── */
        <div style={styles.gridDefault}>
          <aside style={styles.formRail}>
            <TradeReviewForm onSubmit={handleSubmit} busy={busy} hideSyntheticMode />
          </aside>

          <section style={styles.statusCol}>
            {status === "idle" && (
              <EmptyState
                icon={<MpIcon name="circle" size={28} />}
                title="No analysis generated yet"
                body="Fill in the trade intent and portfolio context, then click Generate analysis."
              />
            )}
            {status === "loading" && (
              <LoadingSkeleton rows={5} label="Running agent-team analysis (mock provider)…" />
            )}
            {status === "error" && (
              <ErrorState message={error ?? "Agent-team analysis request failed."} onRetry={() => setStatus("idle")} />
            )}
          </section>
        </div>
      )}

      <SafetyStrip
        items={[
          "Analysis only",
          "Manual trade review",
          "Not an order recommendation",
          "Data freshness may affect review quality",
        ]}
      />
    </div>
  );
}

function PartialBanner() {
  return (
    <aside
      role="status"
      style={{
        fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)",
        backgroundColor: "var(--mp-stale-soft)",
        border: "1px solid var(--mp-stale)",
        borderLeft: "4px solid var(--mp-stale)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-3) var(--space-5)",
        lineHeight: 1.6,
        display: "flex",
        alignItems: "flex-start",
        gap: "var(--space-2)",
      }}
    >
      <MpIcon name="alert" size={14} style={{ color: "var(--mp-stale)", flexShrink: 0, marginTop: 2 }} />
      <span>
        The run is <strong>partially completed</strong>. Some roles produced no output —
        see provider warnings and the unavailable-state messages on each role panel below.
      </span>
    </aside>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex", flexDirection: "column", gap: "var(--space-6)",
    maxWidth: 1440, margin: "0 auto", color: "var(--mp-ink)",
  },
  /* Pre-run layout */
  gridDefault: {
    display: "grid", gridTemplateColumns: "320px 1fr",
    gap: "var(--space-6)", minWidth: 0,
  },
  formRail: {
    position: "sticky", top: "var(--space-4)", alignSelf: "flex-start",
    maxHeight: "calc(100vh - var(--topbar-height) - var(--space-8))",
    overflowY: "auto", paddingRight: 2, minWidth: 0,
  },
  statusCol: {
    display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0,
  },
  /* Prototype console layout — grid columns and responsive breakpoints
     are now in globals.css (.mp-agent-console-body and children). */
  consoleWrap: {
    display: "flex", flexDirection: "column", gap: "var(--space-4)",
  },
};
