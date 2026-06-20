/**
 * GenerateAgentTeamReport — explicit, manual trigger to run the Agent Team for a
 * saved snapshot, plus the transient "generating" affordance shown over the
 * prior persisted status.
 *
 * Presentational only: the parent (ReportsPage) owns the single request, the
 * refetch, and the error, so the generating state can sit over the existing
 * report body (no skeleton flash) and stay single-flight per snapshot.
 * Generation is never automatic or silent.
 *
 * `variant="generate"` is the primary card for a source snapshot that has no
 * report yet. `variant="retry"` is the compact affordance for
 * `agent_unavailable` / `validation_failed` — re-running uses the same immutable
 * saved evidence and never touches the source snapshot. Copy is analysis-only.
 */
import { MpIcon } from "../shared/mp";

interface GenerateAgentTeamReportProps {
  variant?: "generate" | "retry";
  generating: boolean;
  error: string | null;
  onGenerate: () => void;
}

export default function GenerateAgentTeamReport({
  variant = "generate",
  generating,
  error,
  onGenerate,
}: GenerateAgentTeamReportProps) {
  const isRetry = variant === "retry";
  const buttonLabel = generating
    ? "Generating analysis…"
    : isRetry || error
      ? "Try again"
      : "Generate report";

  return (
    <section
      style={isRetry ? styles.retryCard : styles.card}
      aria-label={isRetry ? "Run the Agent Team report again" : "Generate Agent Team report"}
      aria-busy={generating}
    >
      {isRetry ? (
        <p style={styles.retryCopy}>
          You can run the Agent Team again from the same saved evidence. The saved
          snapshot stays unchanged.
        </p>
      ) : (
        <div style={styles.head}>
          <span aria-hidden="true" style={styles.icon}>
            <MpIcon name="agent" size={18} />
          </span>
          <div style={styles.copy}>
            <h3 style={styles.title}>Generate Agent Team report</h3>
            <p style={styles.body}>
              Build an Agent Team analysis from this saved snapshot's reviewed
              evidence package — only when you want it. Analysis only;
              deterministic backend services own all calculations, and the saved
              scope and caveats stay attached for audit.
            </p>
          </div>
        </div>
      )}

      <div style={styles.actionRow}>
        <button
          type="button"
          onClick={onGenerate}
          disabled={generating}
          style={{
            ...(isRetry ? styles.retryButton : styles.button),
            ...(generating ? styles.buttonBusy : undefined),
          }}
        >
          <MpIcon
            name={generating ? "refresh" : isRetry ? "refresh" : "spark"}
            size={15}
            style={generating ? { animation: "mp-spin 0.9s linear infinite" } : undefined}
          />
          {buttonLabel}
        </button>
        {generating && (
          <span style={styles.generatingNote} role="status">
            Generating Agent Team report… this can take a moment.
          </span>
        )}
      </div>

      {error && !generating && (
        <p role="alert" style={styles.error}>
          <MpIcon name="alert" size={14} style={{ flexShrink: 0, marginTop: 2 }} />
          <span>{error}</span>
        </p>
      )}
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    border: "1px solid var(--mp-accent-line)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-5)",
    background: "var(--reports-action-surface)",
    minWidth: 0,
  },
  retryCard: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--reports-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-4)",
    background: "var(--reports-soft-surface)",
    minWidth: 0,
  },
  head: {
    display: "flex",
    gap: "var(--space-3)",
    alignItems: "flex-start",
    minWidth: 0,
  },
  icon: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: 34,
    height: 34,
    borderRadius: "var(--radius-sm)",
    border: "1px solid var(--mp-accent-line)",
    color: "var(--mp-accent)",
    background: "var(--reports-card-surface)",
    flexShrink: 0,
  },
  copy: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    minWidth: 0,
  },
  title: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-md)",
    fontWeight: 600,
    lineHeight: 1.3,
  },
  body: {
    margin: 0,
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.6,
  },
  retryCopy: {
    margin: 0,
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.6,
  },
  actionRow: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
    flexWrap: "wrap",
    minWidth: 0,
  },
  button: {
    appearance: "none",
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    cursor: "pointer",
    border: "1px solid var(--mp-accent)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-4)",
    backgroundColor: "var(--mp-accent)",
    color: "var(--mp-paper)",
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
    fontFamily: "inherit",
  },
  retryButton: {
    appearance: "none",
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    cursor: "pointer",
    border: "1px solid var(--mp-accent)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-1) var(--space-4)",
    backgroundColor: "transparent",
    color: "var(--mp-accent)",
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
    fontFamily: "inherit",
  },
  buttonBusy: {
    cursor: "progress",
    opacity: 0.75,
  },
  generatingNote: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.5,
  },
  error: {
    margin: 0,
    display: "flex",
    gap: 6,
    alignItems: "flex-start",
    color: "var(--mp-block)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.5,
  },
};
