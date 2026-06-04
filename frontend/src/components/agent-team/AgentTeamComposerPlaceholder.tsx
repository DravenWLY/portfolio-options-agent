import { AGENT_TEAM_STAGE_ORDER, type AgentTeamRole } from "../../types/agentTeam";
import { MpIcon } from "../shared/mp";

/**
 * AgentTeamComposerPlaceholder — disabled follow-up composer (P20C-T5).
 *
 * Visual placeholder matching the prototype's follow-up area:
 *   - text input placeholder
 *   - direct-to-agent selector
 *   - broadcast-to-team option
 *   - quick question chips
 *   - send button
 *
 * This console is read-only. The composer is a permanently disabled, non-
 * interactive surface — the copy frames it as not part of this build rather
 * than "coming soon". It does not submit, store, call an API, write to
 * localStorage or sessionStorage, or imply realtime behavior.
 *
 * All controls use `disabled`, `pointer-events: none`, and `aria-disabled`.
 * No click or keyboard interaction produces a side-effect.
 */

const ROLE_DISPLAY: Record<AgentTeamRole, string> = {
  fundamentals_analyst: "Fundamentals",
  news_analyst: "News",
  technical_analyst: "Technical",
  risk_management_agent: "Risk mgmt",
  portfolio_manager_agent: "Portfolio mgr",
};

const QUICK_QUESTIONS = [
  "Explain the risk factors",
  "Compare with alternatives",
  "Summarize key concerns",
  "What data is missing?",
];

export default function AgentTeamComposerPlaceholder() {
  return (
    <section
      style={styles.wrap}
      aria-label="Follow-up composer (read-only, disabled)"
      aria-disabled="true"
    >
      {/* Quick question chips */}
      <div style={styles.chipRow}>
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            disabled
            style={styles.chip}
            tabIndex={-1}
          >
            {q}
          </button>
        ))}
        <span style={styles.caveat}>Read-only</span>
      </div>

      {/* Input row */}
      <div style={styles.inputRow}>
        {/* Text input */}
        <input
          type="text"
          disabled
          placeholder="Ask a follow-up question…"
          style={styles.input}
          aria-label="Follow-up question input (read-only, disabled)"
          tabIndex={-1}
        />

        {/* Direct-to-agent selector */}
        <select
          disabled
          style={styles.select}
          aria-label="Direct to agent (read-only, disabled)"
          tabIndex={-1}
        >
          <option>Broadcast to team</option>
          {AGENT_TEAM_STAGE_ORDER.map((role) => (
            <option key={role} value={role}>{ROLE_DISPLAY[role]}</option>
          ))}
        </select>

        {/* Send button */}
        <button
          type="button"
          disabled
          style={styles.sendBtn}
          tabIndex={-1}
        >
          <MpIcon name="send" size={12} style={{ marginRight: 4 }} />
          Send
        </button>
      </div>

      <p style={styles.note}>
        <MpIcon name="lock" size={10} style={{ verticalAlign: "middle", marginRight: 4, color: "var(--mp-mute)" }} />
        This console is read-only. Interactive follow-up is not part of this build.
      </p>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    borderTop: "1px solid var(--mp-rule)",
    backgroundColor: "var(--mp-paper-2)",
    padding: "var(--space-3) var(--space-5)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    opacity: 0.55,
    pointerEvents: "none",
    userSelect: "none",
  },
  chipRow: {
    display: "flex",
    gap: "var(--space-2)",
    flexWrap: "wrap",
    alignItems: "center",
  },
  chip: {
    fontSize: "var(--font-size-xs)",
    padding: "3px 8px",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-card)",
    color: "var(--mp-ink-2)",
    cursor: "not-allowed",
    lineHeight: 1.4,
  },
  caveat: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    fontWeight: 700,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    marginLeft: "auto",
  },
  inputRow: {
    display: "flex",
    gap: "var(--space-2)",
    alignItems: "stretch",
  },
  select: {
    fontSize: "var(--font-size-xs)",
    padding: "5px 8px",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-card)",
    color: "var(--mp-ink-2)",
    cursor: "not-allowed",
    flexShrink: 0,
  },
  input: {
    flex: 1,
    fontSize: "var(--font-size-sm)",
    padding: "5px 12px",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-card)",
    color: "var(--mp-ink-2)",
    cursor: "not-allowed",
    minWidth: 0,
  },
  sendBtn: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
    padding: "5px 14px",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-card)",
    color: "var(--mp-mute)",
    cursor: "not-allowed",
    flexShrink: 0,
    display: "flex",
    alignItems: "center",
  },
  note: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: 0,
    lineHeight: 1.5,
  },
};
