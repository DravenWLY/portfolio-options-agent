import { useState } from "react";
import { Link } from "react-router-dom";
import { saveReviewSnapshotFromTradeReview } from "../../api/reports";
import { ApiRequestError } from "../../api/client";
import { MpIcon } from "../shared/mp";

/**
 * SaveReviewSnapshot — Phase 28A "Save review snapshot" action, with the
 * Phase 30A golden-path handoff framing.
 *
 * Renders only when the backend has exposed an opaque, app-owned
 * `saved_review_source_reference` (e.g. `trrev_…`) for a completed review. The
 * frontend sends ONLY the approved create-request fields:
 *   source_kind, source_reference, title, report_type.
 *
 * It never sends scope_metadata, deterministic_summary, agent_summary, Account
 * Details data, selector state, cached frontend state, or any
 * account/provider/broker/holdings/position/balance data. The backend resolves
 * the reviewed source server-side and builds the immutable artifact.
 *
 * P30A choreography: this is the bridge between the deterministic Trade Review
 * above and the later, explicit Agent Team briefing in Reports. The copy frames
 * the save as freezing the evidence package and points — optionally, without
 * auto-generating anything — to Reports to generate the briefing on "what you
 * might be overlooking before acting". Generation stays manual and lives in
 * Reports; nothing here runs the Agent Team, infers a report id/status, or
 * deep-links to a specific report. It links to Reports generally.
 *
 * Wording stays quiet and read-only — no advice, recommendation, buy/sell,
 * safe/ready-to-trade, order, or execution language. The opaque source
 * reference is used in the request body but is never rendered.
 */

type SaveState = "idle" | "saving" | "saved" | "error";

export default function SaveReviewSnapshot({
  userId,
  sourceReference,
  defaultTitle,
}: {
  userId: string;
  sourceReference: string;
  defaultTitle: string;
}) {
  const [state, setState] = useState<SaveState>("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setState("saving");
    setError(null);
    try {
      await saveReviewSnapshotFromTradeReview(userId, {
        source_kind: "trade_review_workspace",
        source_reference: sourceReference,
        title: defaultTitle,
        report_type: "saved_review_artifact",
      });
      setState("saved");
    } catch (err) {
      const msg =
        err instanceof ApiRequestError
          ? err.detail
          : err instanceof Error
            ? err.message
            : "Could not save the snapshot.";
      setError(msg);
      setState("error");
    }
  }

  if (state === "saved") {
    return (
      <section style={styles.wrap} aria-label="Evidence snapshot saved" role="status">
        <span style={{ ...styles.icon, color: "var(--mp-live)" }}>
          <MpIcon name="check" size={16} />
        </span>
        <div style={styles.body}>
          <p style={styles.title}>Evidence snapshot saved</p>
          <p style={styles.sub}>
            This review is frozen as a read-only evidence package — the same scope,
            freshness, and caveats shown here. Open it in Reports to generate the
            Agent Team briefing on what you might be overlooking before acting;
            nothing is generated until you ask.
          </p>
          <Link to="/reports" style={styles.cta}>
            Open in Reports
            <MpIcon
              name="arrow-r"
              size={13}
              style={{ verticalAlign: "middle", marginLeft: 4 }}
            />
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section style={styles.wrap} aria-label="Save evidence snapshot">
      <span style={{ ...styles.icon, color: "var(--mp-mute)" }}>
        <MpIcon name="reports" size={16} />
      </span>
      <div style={styles.body}>
        <div style={styles.row}>
          <p style={styles.title}>Save evidence snapshot</p>
          <button
            type="button"
            onClick={handleSave}
            disabled={state === "saving"}
            style={{ ...styles.button, ...(state === "saving" ? styles.buttonBusy : {}) }}
          >
            {state === "saving" ? (
              <>
                <MpIcon
                  name="refresh"
                  size={12}
                  style={{ verticalAlign: "middle", marginRight: 4 }}
                />
                Saving…
              </>
            ) : state === "error" ? (
              "Try again"
            ) : (
              "Save snapshot"
            )}
          </button>
        </div>
        <p style={styles.sub}>
          Freeze this review — its scope, freshness, and caveats — as a read-only
          evidence package. Later, open it in Reports to generate the Agent Team
          briefing on what you might be overlooking before acting.
        </p>
        {state === "error" && (
          <p style={styles.errorMsg} role="status">
            <MpIcon
              name="alert"
              size={12}
              style={{ color: "var(--mp-stale)", verticalAlign: "middle", marginRight: 4 }}
            />
            Snapshot was not saved{error ? ` (${error})` : ""}. You can try again.
          </p>
        )}
      </div>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    display: "flex",
    gap: "var(--space-3)",
    alignItems: "flex-start",
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-4)",
    minWidth: 0,
  },
  icon: { flexShrink: 0, lineHeight: 1, marginTop: 1 },
  body: { display: "flex", flexDirection: "column", gap: "var(--space-1)", minWidth: 0, flex: 1 },
  row: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-3)",
    flexWrap: "wrap",
  },
  title: { fontWeight: 700, fontSize: "var(--font-size-sm)", color: "var(--mp-ink)", margin: 0 },
  sub: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0, lineHeight: 1.6 },
  button: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    padding: "var(--space-1) var(--space-4)",
    border: "1px solid var(--mp-accent)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "transparent",
    color: "var(--mp-accent)",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  buttonBusy: { opacity: 0.6, cursor: "progress" },
  cta: {
    alignSelf: "flex-start",
    maxWidth: "100%",
    display: "inline-flex",
    alignItems: "center",
    marginTop: "var(--space-1)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    padding: "var(--space-1) var(--space-4)",
    border: "1px solid var(--mp-accent)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "transparent",
    color: "var(--mp-accent)",
    textDecoration: "none",
    whiteSpace: "nowrap",
  },
  errorMsg: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-ink-2)",
    margin: "var(--space-1) 0 0",
    lineHeight: 1.5,
  },
};
