import { useState } from "react";
import { agentTeamApi } from "../api/agentTeam";
import { ApiRequestError } from "../api/client";
import TradeReviewForm from "../components/trade-review/TradeReviewForm";
import AgentTeamAnalysisConsole from "../components/agent-team/AgentTeamAnalysisConsole";
import AgentTeamPipelineRail from "../components/agent-team/AgentTeamPipelineRail";
import { LoadingSkeleton, ErrorState, EmptyState } from "../components/shared/StateViews";
import { Badge, PageHeader, SafetyStrip } from "../components/shared/mp";
import type { TradeReviewSubmission } from "../types/tradeReview";
import type { AgentTeamAnalysisConsoleRead } from "../types/agentTeam";

/**
 * AgentTeamAnalysisPage — Modern Portfolio Desk re-skin (P20A-T1).
 *
 * Translated (not pasted) from
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/agent-console.tsx
 *
 * Layout (success state):  [ form 320 | pipeline 240 | transcript 1fr ]
 * Layout (other states):   [ form 320 | state placeholder 1fr ]
 *
 * Backend wiring unchanged: POST /agent-team/trade-review-analysis/preview.
 * Single network path. No localStorage / sessionStorage writes for analysis,
 * role, prompt, provider, credential, or account data.
 *
 * Per P20A-T1: no chat composer, no streaming, no follow-up controls, no
 * direct-to-role routing, no broadcast — none of these map to existing
 * endpoint fields and all are omitted.
 */

type Status = "idle" | "loading" | "success" | "error";

export default function AgentTeamAnalysisPage() {
  const [status, setStatus] = useState<Status>("idle");
  const [data, setData] = useState<AgentTeamAnalysisConsoleRead | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(submission: TradeReviewSubmission) {
    if (submission.kind !== "portfolio") {
      setError("The agent-team analysis console only accepts portfolio-backed submissions.");
      setStatus("error");
      return;
    }
    setStatus("loading");
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

      <div style={status === "success" && data ? styles.gridSuccess : styles.gridDefault}>
        <aside style={styles.formRail}>
          <TradeReviewForm onSubmit={handleSubmit} busy={status === "loading"} hideSyntheticMode />
        </aside>

        {status === "success" && data ? (
          <>
            <aside style={styles.pipelineRail}>
              <AgentTeamPipelineRail data={data} />
            </aside>
            <section style={styles.transcriptCol}>
              {data.run_status === "partially_completed" && <PartialBanner />}
              <AgentTeamAnalysisConsole data={data} />
            </section>
          </>
        ) : (
          <section style={styles.transcriptCol}>
            {status === "idle" && (
              <EmptyState
                icon="○"
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
        )}
      </div>

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
      }}
    >
      <span aria-hidden="true">△ </span>
      The run is <strong>partially completed</strong>. Some roles produced no output —
      see provider warnings and the unavailable-state messages on each role panel below.
    </aside>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", gap: "var(--space-6)", maxWidth: 1440, margin: "0 auto", color: "var(--mp-ink)" },
  gridDefault: { display: "grid", gridTemplateColumns: "320px 1fr", gap: "var(--space-6)", minWidth: 0 },
  gridSuccess: { display: "grid", gridTemplateColumns: "320px 240px 1fr", gap: "var(--space-5)", minWidth: 0 },
  formRail: {
    position: "sticky", top: "var(--space-4)", alignSelf: "flex-start",
    maxHeight: "calc(100vh - var(--topbar-height) - var(--space-8))",
    overflowY: "auto", paddingRight: 2, minWidth: 0,
  },
  pipelineRail: { position: "sticky", top: "var(--space-4)", alignSelf: "flex-start", minWidth: 0 },
  transcriptCol: { display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0 },
};
