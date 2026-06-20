/**
 * AgentRoleSection — one Agent Team role's contribution to a saved report.
 *
 * Two variants:
 * - `primary` — a full-width editorial "memo" block for the portfolio-aware
 *   roles (Risk Manager, Portfolio Manager). The agent narrative (serif) and the
 *   deterministic evidence it cited (mono ledger) are kept in explicitly labeled,
 *   visually distinct zones — never blended.
 * - `context` — a compact card for the secondary public "market context"
 *   analysts; lighter weight, a short snippet or honest unavailable note.
 *
 * Renders backend-owned fields only (`display_name`, status, sanitized
 * narrative, keys-only evidence citations, warning codes). No raw provider
 * output, metric, or private value is ever rendered.
 */
import { Badge, MpIcon } from "../shared/mp";
import type { SavedAgentTeamRoleSummaryRead } from "../../types/api";
import ReportProse from "./ReportProse";
import {
  evidenceKeyLabel,
  firstParagraph,
  providerStatusLabel,
  roleStatusIcon,
  roleStatusMeta,
  roleUnavailableText,
} from "./reportStatus";

interface AgentRoleSectionProps {
  role: SavedAgentTeamRoleSummaryRead;
  variant?: "primary" | "context";
}

export default function AgentRoleSection({ role, variant = "primary" }: AgentRoleSectionProps) {
  return variant === "context" ? <ContextCard role={role} /> : <PrimaryCard role={role} />;
}

function StatusBadge({ role, small }: { role: SavedAgentTeamRoleSummaryRead; small?: boolean }) {
  const meta = roleStatusMeta(role.role_status);
  return (
    <Badge tone={meta.tone} dot={false}>
      <MpIcon name={roleStatusIcon(role.role_status)} size={small ? 11 : 12} />
      {meta.label}
    </Badge>
  );
}

function PrimaryCard({ role }: { role: SavedAgentTeamRoleSummaryRead }) {
  const hasNarrative = role.role_status === "completed" && Boolean(role.summary_markdown);

  return (
    <article style={styles.primaryCard} aria-label={`${role.display_name} section`}>
      <header style={styles.primaryHeader}>
        <h4 className="mp-display" style={styles.primaryName}>
          {role.display_name}
        </h4>
        <StatusBadge role={role} />
      </header>

      {/* Narrative zone — agent-authored, analysis only */}
      <div style={styles.zone}>
        <span style={{ ...styles.zoneLabel, color: "var(--mp-accent-ink)" }}>
          Agent narrative · analysis only
        </span>
        {hasNarrative && role.summary_markdown ? (
          <div style={styles.narrative}>
            <ReportProse text={role.summary_markdown} display />
          </div>
        ) : (
          <p style={styles.unavailable}>
            <MpIcon name="info" size={14} style={styles.unavailableIcon} />
            <span>{roleUnavailableText(role.unavailable_reason)}</span>
          </p>
        )}
      </div>

      {/* Deterministic evidence zone — backend-owned, keys only */}
      {role.evidence_references.length > 0 && (
        <div style={styles.evidenceZone}>
          <span style={{ ...styles.zoneLabel, color: "var(--mp-mute)" }}>
            Deterministic evidence cited · backend-owned
          </span>
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
        <span style={styles.providerNote}>Provider: {providerStatusLabel(role.provider_status)}</span>
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

function ContextCard({ role }: { role: SavedAgentTeamRoleSummaryRead }) {
  const hasNarrative = role.role_status === "completed" && Boolean(role.summary_markdown);
  const snippet = firstParagraph(role.summary_markdown);

  return (
    <article style={styles.contextCard} aria-label={`${role.display_name} section`}>
      <header style={styles.contextHeader}>
        <h5 style={styles.contextName}>{role.display_name}</h5>
        <StatusBadge role={role} small />
      </header>
      {hasNarrative && snippet ? (
        <p style={styles.contextSnippet}>{snippet}</p>
      ) : (
        <p style={styles.contextUnavailable}>{roleUnavailableText(role.unavailable_reason)}</p>
      )}
    </article>
  );
}

const styles: Record<string, React.CSSProperties> = {
  /* ── primary (memo) ── */
  primaryCard: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    border: "1px solid var(--reports-rule)",
    borderLeft: "3px solid var(--mp-accent)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-5) var(--space-6)",
    background: "var(--reports-card-surface)",
    boxShadow: "var(--reports-section-shadow)",
    minWidth: 0,
  },
  primaryHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-3)",
    flexWrap: "wrap",
    minWidth: 0,
  },
  primaryName: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-lg)",
    fontWeight: 500,
    lineHeight: 1.2,
  },
  zone: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    minWidth: 0,
  },
  zoneLabel: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.07em",
    textTransform: "uppercase",
  },
  narrative: {
    maxWidth: "64ch",
    minWidth: 0,
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
  evidenceZone: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    border: "1px solid var(--reports-rule)",
    borderTop: "1px solid var(--reports-rule-strong)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-3)",
    background: "var(--reports-evidence-surface)",
    minWidth: 0,
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
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "2px 8px",
    fontSize: "var(--font-size-xs)",
    fontFamily: "var(--mp-font-mono)",
    background: "var(--reports-card-surface)",
    overflowWrap: "anywhere",
  },
  footer: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
    flexWrap: "wrap",
    borderTop: "1px solid var(--reports-rule)",
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
    background: "var(--reports-evidence-surface)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "1px 6px",
    fontSize: "var(--font-size-xs)",
    fontFamily: "var(--mp-font-mono)",
    overflowWrap: "anywhere",
  },
  /* ── context (compact) ── */
  contextCard: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-4)",
    background: "var(--reports-card-surface)",
    minWidth: 0,
  },
  contextHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-2)",
    flexWrap: "wrap",
  },
  contextName: {
    margin: 0,
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
    lineHeight: 1.25,
  },
  contextSnippet: {
    margin: 0,
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.55,
    overflowWrap: "anywhere",
  },
  contextUnavailable: {
    margin: 0,
    color: "var(--mp-mute-2)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.5,
    overflowWrap: "anywhere",
  },
};
