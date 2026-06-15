/**
 * AgentRoleSection — one Agent Team role's contribution to a saved report.
 *
 * Renders the backend-owned `display_name`, the role/provider status, and
 * either the sanitized narrative (when completed) or an honest unavailable note
 * built from the sanitized `unavailable_reason`. Cited evidence is shown as
 * keys-only provenance chips. No raw provider output, prompt, trace, metric, or
 * private value is ever rendered (the backend validator guarantees the saved
 * content is sanitized; the frontend adds no values).
 */
import { Badge, MpIcon } from "../shared/mp";
import type { SavedAgentTeamRoleSummaryRead } from "../../types/api";
import ReportProse from "./ReportProse";
import {
  evidenceKeyLabel,
  humanizeCode,
  providerStatusLabel,
  roleStatusMeta,
} from "./reportStatus";

interface AgentRoleSectionProps {
  role: SavedAgentTeamRoleSummaryRead;
}

export default function AgentRoleSection({ role }: AgentRoleSectionProps) {
  const statusMeta = roleStatusMeta(role.role_status);
  const hasNarrative = role.role_status === "completed" && Boolean(role.summary_markdown);

  return (
    <article
      style={{
        ...styles.card,
        borderLeft: `3px solid var(--mp-${statusMeta.tone === "mute" ? "rule" : statusMeta.tone})`,
      }}
      aria-label={`${role.display_name} section`}
    >
      <header style={styles.header}>
        <h4 style={styles.name}>{role.display_name}</h4>
        <Badge tone={statusMeta.tone} dot={role.role_status === "completed"}>
          {statusMeta.label}
        </Badge>
      </header>

      {hasNarrative && role.summary_markdown ? (
        <ReportProse text={role.summary_markdown} />
      ) : (
        <p style={styles.unavailable}>
          <MpIcon name="info" size={14} style={styles.unavailableIcon} />
          <span>
            {role.unavailable_reason
              ? `No narrative for this role: ${humanizeCode(role.unavailable_reason)}.`
              : "No narrative was produced for this role."}
          </span>
        </p>
      )}

      {role.evidence_references.length > 0 && (
        <div style={styles.evidence}>
          <span style={styles.evidenceLabel}>Evidence cited</span>
          <ul style={styles.chipList}>
            {role.evidence_references.map((key) => (
              <li key={key} style={styles.evidenceChip}>
                {evidenceKeyLabel(key)}
              </li>
            ))}
          </ul>
        </div>
      )}

      <footer style={styles.footer}>
        <span style={styles.providerNote}>
          Provider: {providerStatusLabel(role.provider_status)}
        </span>
        {role.warning_codes.length > 0 && (
          <ul style={styles.codeList}>
            {role.warning_codes.map((code) => (
              <li key={code} style={styles.codeChip} title={code}>
                {code}
              </li>
            ))}
          </ul>
        )}
      </footer>
    </article>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4)",
    backgroundColor: "var(--mp-card)",
    minWidth: 0,
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-3)",
    flexWrap: "wrap",
    minWidth: 0,
  },
  name: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-md)",
    fontWeight: 600,
    lineHeight: 1.25,
  },
  unavailable: {
    margin: 0,
    display: "flex",
    gap: 8,
    alignItems: "flex-start",
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.6,
  },
  unavailableIcon: {
    color: "var(--mp-mute-2)",
    flexShrink: 0,
    marginTop: 2,
  },
  evidence: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    minWidth: 0,
  },
  evidenceLabel: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
  },
  chipList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
  },
  evidenceChip: {
    color: "var(--mp-ink-2)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "2px 8px",
    fontSize: "var(--font-size-xs)",
    backgroundColor: "var(--mp-card-2)",
    overflowWrap: "anywhere",
  },
  footer: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
    flexWrap: "wrap",
    borderTop: "1px solid var(--mp-rule)",
    paddingTop: "var(--space-2)",
    minWidth: 0,
  },
  providerNote: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
  },
  codeList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
  },
  codeChip: {
    color: "var(--mp-mute)",
    backgroundColor: "var(--mp-card-2)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "1px 6px",
    fontSize: "var(--font-size-xs)",
    fontFamily: "var(--mp-font-mono)",
    overflowWrap: "anywhere",
  },
};
