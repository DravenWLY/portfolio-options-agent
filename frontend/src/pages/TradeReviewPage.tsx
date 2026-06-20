import { useState } from "react";
import { tradeReviewsApi } from "../api/tradeReviews";
import { ApiRequestError } from "../api/client";
import TradeReviewForm from "../components/trade-review/TradeReviewForm";
import TradeReviewResults from "../components/trade-review/TradeReviewResults";
import { LoadingSkeleton, ErrorState, EmptyState } from "../components/shared/StateViews";
import { Badge, PageHeader, SafetyStrip } from "../components/shared/mp";
import SkyframeSurface from "../components/shared/SkyframeSurface";
import { useAccountContext } from "../context/useAccountContext";
import type { TradeReviewSubmission, TradeReviewWorkspaceRead } from "../types/tradeReview";

/**
 * TradeReviewPage — Modern Portfolio Desk re-skin (P20A-T1).
 *
 * Translated (not pasted) from
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/trade-review.tsx
 *
 * Layout: two-column (form sticky-left, results right). Backend wiring
 * unchanged: POST /trade-reviews/preview (synthetic dev fallback) and
 * POST /trade-reviews/portfolio-preview (portfolio-backed, primary).
 *
 * Safety: read-only. No order ticket / execute / cancel / disconnect / buy-now
 * / sell-now / trade-readiness-assertion / outcome-guarantee wording.
 * No localStorage / sessionStorage writes added. Every field rendered traces
 * to `TradeReviewWorkspaceRead`; prototype-only literals (cash buffer,
 * call-away dollar exposure, pre/post stack-bar, invented context refs,
 * personal-name policy strings) are intentionally dropped.
 */

type Status = "idle" | "loading" | "success" | "empty" | "error";

export default function TradeReviewPage() {
  const { selectedUser } = useAccountContext();
  const [status, setStatus] = useState<Status>("idle");
  const [data, setData] = useState<TradeReviewWorkspaceRead | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(submission: TradeReviewSubmission) {
    setStatus("loading");
    setError(null);
    try {
      const result =
        submission.kind === "portfolio"
          ? await tradeReviewsApi.portfolioPreview(submission.payload, selectedUser?.id ?? null)
          : await tradeReviewsApi.preview(submission.payload);
      if (!result) {
        setData(null);
        setStatus("empty");
        return;
      }
      setData(result);
      setStatus("success");
    } catch (err) {
      const msg =
        err instanceof ApiRequestError ? err.detail :
        err instanceof Error ? err.message :
        "Preview request failed.";
      setError(msg);
      setStatus("error");
    }
  }

  return (
    <SkyframeSurface className="mp-surface" maxWidth={1280}>
      <PageHeader
        eyebrow="Workspace · trade review"
        title="Review trade"
        sub="Inputs validate for shape only. The backend owns every financial calculation. Outputs separate deterministic facts, agent commentary, and any narrative report. Manual review only — no order is placed, no broker action is taken."
        right={
          <>
            <Badge tone="info" dot>read-only</Badge>
            <Badge tone="mute" dot={false}>analysis-only</Badge>
          </>
        }
      />

      <div className="mp-trade-review-grid" style={styles.grid}>
        <aside className="mp-trade-review-form-rail" style={styles.formRail}>
          <TradeReviewForm onSubmit={handleSubmit} busy={status === "loading"} />
        </aside>

        <section style={styles.resultsCol}>
          {status === "idle" && (
            <EmptyState
              title="No analysis generated yet"
              body="Fill in the trade intent and portfolio context, then click Generate analysis."
            />
          )}
          {status === "loading" && <LoadingSkeleton rows={5} label="Generating deterministic preview…" />}
          {status === "error" && (
            <ErrorState message={error ?? "Preview request failed."} onRetry={() => setStatus("idle")} />
          )}
          {status === "empty" && (
            <EmptyState title="No content returned" body="The preview returned an empty payload. Adjust inputs and try again." />
          )}
          {status === "success" && data && (
            <TradeReviewResults data={data} userId={selectedUser?.id ?? null} />
          )}
        </section>
      </div>

      <SafetyStrip
        items={[
          "Analysis only",
          "Manual trade review",
          "Not an order recommendation",
          "Data freshness may affect review quality",
        ]}
      />
    </SkyframeSurface>
  );
}

const styles: Record<string, React.CSSProperties> = {
  grid: { display: "grid", gap: "var(--space-6)", minWidth: 0 },
  formRail: {
    alignSelf: "flex-start", paddingRight: 2, minWidth: 0,
  },
  resultsCol: { display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0 },
};
