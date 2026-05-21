import { useState } from "react";
import { tradeReviewsApi } from "../api/tradeReviews";
import { ApiRequestError } from "../api/client";
import TradeReviewForm from "../components/trade-review/TradeReviewForm";
import TradeReviewResults from "../components/trade-review/TradeReviewResults";
import { LoadingSkeleton, ErrorState, EmptyState } from "../components/shared/StateViews";
import type {
  TradeReviewWorkspacePreviewRequest,
  TradeReviewWorkspaceRead,
} from "../types/tradeReview";

/**
 * TradeReviewPage — Phase 18A first visible Trade Review Workspace (P18A-T3).
 *
 * Route: /trade-review
 *
 * Safety:
 *  - Read-only preview. The backend route is synthetic/stateless: no DB, no
 *    broker sync, no market-data provider, no TradingAgents, no LLMs, no
 *    broker actions. The frontend renders the sanitized contract verbatim
 *    and performs no financial calculations.
 *  - No order ticket, no execute/cancel/disconnect, no buy/sell/safe-to-trade
 *    language, no guaranteed-return language, no automated recommendations.
 *  - No localStorage / sessionStorage of portfolio or review data.
 */

type Status = "idle" | "loading" | "success" | "empty" | "error";

export default function TradeReviewPage() {
  const [status, setStatus] = useState<Status>("idle");
  const [data, setData] = useState<TradeReviewWorkspaceRead | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(req: TradeReviewWorkspacePreviewRequest) {
    setStatus("loading");
    setError(null);
    try {
      const result = await tradeReviewsApi.preview(req);
      if (!result) {
        setData(null);
        setStatus("empty");
        return;
      }
      setData(result);
      setStatus("success");
    } catch (err) {
      const msg =
        err instanceof ApiRequestError
          ? err.detail
          : err instanceof Error
            ? err.message
            : "Preview request failed.";
      setError(msg);
      setStatus("error");
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h1 style={styles.title}>Trade Review Workspace</h1>
        <p style={styles.subtitle}>
          Manual preview only. Renders the sanitized deterministic contract from
          the backend — not advice, not a recommendation, not a forecast. No
          orders are placed. No broker action is taken.
        </p>
      </div>

      <aside style={styles.scopeNotice} role="note" aria-label="Phase 18A scope">
        <p style={styles.scopeTitle}>Phase 18A scope</p>
        <ul style={styles.scopeList}>
          <li>Backend preview is synthetic and stateless — no real broker / market / LLM calls.</li>
          <li>Broker snapshot freshness and market quote freshness are separate scopes.</li>
          <li>Covered-call coverage is not fully netted; CSP collateral uses a generic rule.</li>
          <li>Phase 17 TradingAgents research/debate evidence is intentionally out of scope here.</li>
        </ul>
      </aside>

      <TradeReviewForm onSubmit={handleSubmit} busy={status === "loading"} />

      {status === "idle" && (
        <EmptyState
          icon="○"
          title="No preview generated yet"
          body="Fill in the inputs above and click Preview review to render the sanitized deterministic workspace."
        />
      )}
      {status === "loading" && <LoadingSkeleton rows={4} label="Generating deterministic preview…" />}
      {status === "error" && (
        <ErrorState
          message={error ?? "Preview request failed."}
          onRetry={() => setStatus("idle")}
        />
      )}
      {status === "empty" && (
        <EmptyState
          icon="○"
          title="No content returned"
          body="The preview returned an empty payload. Adjust inputs and try again."
        />
      )}
      {status === "success" && data && <TradeReviewResults data={data} />}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", gap: "var(--space-5)", maxWidth: 980 },
  header: { display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  title: {
    fontSize: "var(--font-size-xl)",
    fontWeight: 700,
    color: "var(--color-text-primary)",
    margin: 0,
    letterSpacing: "-0.02em",
  },
  subtitle: { fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)", margin: 0, lineHeight: 1.6 },
  scopeNotice: {
    backgroundColor: "var(--color-surface-2)",
    border: "1px solid var(--color-border)",
    borderLeft: "3px solid var(--color-unknown)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-5)",
  },
  scopeTitle: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-secondary)",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    margin: 0,
  },
  scopeList: {
    margin: "var(--space-2) 0 0",
    paddingLeft: "var(--space-5)",
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    lineHeight: 1.6,
  },
};
