import { useState } from "react";
import { useRiskReview } from "../hooks/useRiskReview";
import { RISK_REVIEW_STUB_NOTICE, type RiskReviewScenario } from "../api/riskReview";
import RiskReviewPanel from "../components/risk/RiskReviewPanel";
import { LoadingSkeleton, ErrorState, EmptyState } from "../components/shared/StateViews";

/**
 * RiskReviewPage — read-only deterministic risk review (P13-T8).
 *
 * Route: /risk
 *
 * Data source is STUBBED: there is no backend risk HTTP route yet. The
 * scenario selector below exists only to exercise required UI states until a
 * real endpoint lands. No network calls, no browser storage, no trade/order
 * controls, no LLM/agent output, no guaranteed-return language.
 */
const SCENARIOS: { value: RiskReviewScenario; label: string }[] = [
  { value: "ok", label: "Golden path" },
  { value: "blocker", label: "Blocker" },
  { value: "stale_quote", label: "Stale quote" },
  { value: "missing_market", label: "Missing market data" },
  { value: "broker_stale", label: "Broker-stale" },
  { value: "empty", label: "Empty" },
  { value: "loading", label: "Loading" },
  { value: "error", label: "Error" },
];

export default function RiskReviewPage() {
  const [scenario, setScenario] = useState<RiskReviewScenario>("ok");
  const { status, report, error, reload } = useRiskReview(scenario);

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h1 style={styles.title}>Risk Review</h1>
        <p style={styles.subtitle}>
          Deterministic option, collateral, assignment, and allocation facts —
          read-only. Not advice, not a recommendation, not a forecast.
        </p>
      </div>

      <aside style={styles.stubNotice} role="note" aria-label="Stubbed data source">
        <span aria-hidden="true">⚑ </span>
        {RISK_REVIEW_STUB_NOTICE}
      </aside>

      <div style={styles.scenarioBar} role="group" aria-label="Preview state (stub only)">
        <span style={styles.scenarioLabel}>Preview state:</span>
        {SCENARIOS.map((s) => (
          <button
            key={s.value}
            type="button"
            onClick={() => setScenario(s.value)}
            aria-pressed={scenario === s.value}
            style={{
              ...styles.scenarioBtn,
              ...(scenario === s.value ? styles.scenarioBtnActive : {}),
            }}
          >
            {s.label}
          </button>
        ))}
      </div>

      {status === "loading" && <LoadingSkeleton rows={4} label="Loading deterministic risk report…" />}
      {status === "error" && <ErrorState message={error ?? "Could not load risk report"} onRetry={reload} />}
      {status === "empty" && (
        <EmptyState
          icon="○"
          title="No deterministic risk report available"
          body="Nothing has been computed for the current selection. This is expected when no position context is provided."
        />
      )}
      {status === "success" && report && <RiskReviewPanel report={report} />}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", gap: "var(--space-6)", maxWidth: 940 },
  header: { display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  title: {
    fontSize: "var(--font-size-xl)",
    fontWeight: 700,
    color: "var(--color-text-primary)",
    margin: 0,
    letterSpacing: "-0.02em",
  },
  subtitle: { fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)", margin: 0 },
  stubNotice: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-secondary)",
    backgroundColor: "var(--color-surface-2)",
    border: "1px solid var(--color-border)",
    borderLeft: "3px solid var(--color-stale)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-5)",
    lineHeight: 1.6,
  },
  scenarioBar: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    flexWrap: "wrap",
  },
  scenarioLabel: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  scenarioBtn: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 600,
    padding: "var(--space-1) var(--space-3)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "transparent",
    color: "var(--color-text-secondary)",
    cursor: "pointer",
  },
  scenarioBtnActive: {
    borderColor: "var(--color-accent)",
    color: "var(--color-accent)",
  },
};
