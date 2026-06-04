import type {
  AgentTeamAnalysisConsoleRead,
  AgentTeamRole,
  AgentTeamRoleOutputRead,
  LLMProviderStatus,
} from "../../types/agentTeam";
import { AGENT_TEAM_STAGE_ORDER } from "../../types/agentTeam";
import { Badge, Pill, type MpTone } from "../shared/mp";
import { MpIcon, type MpIconName } from "../shared/mp";

/**
 * AgentTeamTranscript — unified chat-like transcript pane (P20C-T5).
 *
 * Renders the five role outputs as conversation turns inside one bounded
 * panel, with each turn showing a role avatar, name, status badges, and
 * content. Final synthesis appears as a distinct final narrative turn.
 *
 * The disabled composer is rendered outside this component (passed as
 * `children` or composed by the page); this component owns the transcript
 * header, message stream, provider warnings, and safety flags.
 *
 * Safety: read-only, no execution controls, no frontend financial
 * computation, no HTML interpretation of content_markdown.
 */

/** Local fallback labels — used ONLY for pending/no-output placeholder rows,
 *  where no backend `display_name` is available yet. When a role output
 *  exists, its backend-owned `display_name` is rendered verbatim instead. */
const ROLE_DISPLAY: Record<AgentTeamRole, string> = {
  fundamentals_analyst: "Fundamentals analyst",
  news_analyst: "News analyst",
  technical_analyst: "Technical analyst",
  risk_management_agent: "Risk management agent",
  portfolio_manager_agent: "Portfolio manager agent",
};

/** Quiet guardrail shown wherever the Portfolio Manager persona is identified. */
const PORTFOLIO_MANAGER_GUARDRAIL =
  "Synthesizes the team's analysis for your review — does not manage your portfolio or recommend trades.";

const ROLE_ICON: Record<AgentTeamRole, MpIconName> = {
  fundamentals_analyst: "spark",
  news_analyst: "reports",
  technical_analyst: "review",
  risk_management_agent: "alert",
  portfolio_manager_agent: "agent",
};

const ROLE_ACCENT: Record<AgentTeamRole, string> = {
  fundamentals_analyst: "var(--mp-accent)",
  news_analyst: "var(--mp-info)",
  technical_analyst: "var(--mp-stale)",
  risk_management_agent: "var(--mp-block)",
  portfolio_manager_agent: "var(--mp-accent)",
};

function statusToTone(status: AgentTeamRoleOutputRead["status"]): MpTone {
  if (status === "completed") return "live";
  if (status === "unavailable") return "stale";
  return "mute";
}

function providerToTone(provider: LLMProviderStatus): MpTone {
  if (provider === "ok") return "live";
  if (provider === "skipped") return "mute";
  if (provider === "failed" || provider === "safety_validation_failed") return "block";
  if (provider === "provider_auth_error") return "info";
  return "stale";
}

interface AgentTeamTranscriptProps {
  data: AgentTeamAnalysisConsoleRead;
  /** Optional slot rendered at the bottom of the transcript panel (e.g. disabled composer). */
  footer?: React.ReactNode;
}

export default function AgentTeamTranscript({
  data,
  footer,
}: AgentTeamTranscriptProps) {
  const byRole = new Map(data.role_outputs.map((o) => [o.role_name, o]));
  const completedCount = data.role_outputs.filter((o) => o.status === "completed").length;

  return (
    <div style={styles.panel}>
      {/* ── Transcript header ──────────────────────────────────────── */}
      <div style={styles.panelHeader}>
        <div>
          <p style={styles.eyebrow}>Transcript</p>
          <p style={styles.headerSub}>Role-grouped outputs from the agent team pipeline</p>
        </div>
        <div style={styles.headerRight}>
          <Badge tone="mute" dot={false}>
            {completedCount} / {AGENT_TEAM_STAGE_ORDER.length} roles
          </Badge>
        </div>
      </div>

      {/* ── Message stream ─────────────────────────────────────────── */}
      <div style={styles.stream}>
        {AGENT_TEAM_STAGE_ORDER.map((role) => {
          const out = byRole.get(role);
          return <RoleTurn key={role} role={role} out={out ?? null} />;
        })}

        {/* Final synthesis — distinct narrative turn */}
        <FinalSynthesisTurn text={data.final_synthesis} />

        {/* Provider warnings */}
        {data.provider_warnings.length > 0 && (
          <div style={styles.warningBlock}>
            <div style={styles.warningHeader}>
              <MpIcon name="alert" size={12} style={{ color: "var(--mp-stale)" }} />
              <span style={styles.warningTitle}>
                Provider warnings ({data.provider_warnings.length})
              </span>
            </div>
            <ul style={styles.warningList}>
              {data.provider_warnings.map((w) => (
                <li key={w.code + w.message} style={styles.warningRow}>
                  <span style={styles.warningCode}>{w.code}</span>
                  <span style={styles.warningMsg}>{w.message}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Safety flags */}
        {data.safety_flags.length > 0 && (
          <div style={styles.warningBlock}>
            <div style={styles.warningHeader}>
              <MpIcon name="shield" size={12} style={{ color: "var(--mp-mute)" }} />
              <span style={styles.warningTitle}>Safety flags</span>
            </div>
            <div style={styles.chipRow}>
              {data.safety_flags.map((f) => (
                <Pill key={f} tone="stale">{f}</Pill>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Footer slot (disabled composer) ─────────────────────────── */}
      {footer}
    </div>
  );
}

/* ── Role turn — chat-like message ─────────────────────────────────────── */

function RoleTurn({
  role,
  out,
}: {
  role: AgentTeamRole;
  out: AgentTeamRoleOutputRead | null;
}) {
  const accent = ROLE_ACCENT[role];
  const icon = ROLE_ICON[role];
  // Backend-owned label verbatim when output exists; local fallback only for
  // the pending/no-output placeholder row.
  const name = out ? out.display_name : ROLE_DISPLAY[role];
  const isPortfolioManager = role === "portfolio_manager_agent";

  return (
    <div style={styles.turn}>
      {/* Avatar */}
      <div style={{ ...styles.avatar, borderColor: accent, color: accent }}>
        <MpIcon name={icon} size={14} />
      </div>

      {/* Bubble */}
      <div style={{ ...styles.bubble, borderLeftColor: accent }}>
        {/* Turn header */}
        <div style={styles.turnHeader}>
          <span style={{ ...styles.turnName, color: accent }}>
            {name}
          </span>
          <div style={styles.turnBadges}>
            {out ? (
              <>
                <Pill tone={statusToTone(out.status)}>{out.status}</Pill>
                <Pill tone={providerToTone(out.provider_status)}>
                  provider: {out.provider_status}
                </Pill>
                {out.is_mock && <Pill tone="mute">mock</Pill>}
              </>
            ) : (
              <Pill tone="mute">no output</Pill>
            )}
          </div>
        </div>

        {/* Portfolio Manager persona guardrail — quiet, compact, once per turn */}
        {isPortfolioManager && (
          <p style={styles.roleGuardrail}>{PORTFOLIO_MANAGER_GUARDRAIL}</p>
        )}

        {/* Content */}
        {out ? (
          out.status === "completed" && out.content_markdown ? (
            <pre style={styles.markdownPre}>{out.content_markdown}</pre>
          ) : (
            <p style={styles.unavailable}>
              <MpIcon name="circle" size={11} style={{ color: "var(--mp-mute)", verticalAlign: "middle", marginRight: 4 }} />
              {out.unavailable_reason ?? `Role ${out.status}.`}
            </p>
          )
        ) : (
          <p style={styles.unavailable}>
            <MpIcon name="circle" size={11} style={{ color: "var(--mp-mute)", verticalAlign: "middle", marginRight: 4 }} />
            No output produced for this role.
          </p>
        )}
      </div>
    </div>
  );
}

/* ── Final synthesis turn ──────────────────────────────────────────────── */

function FinalSynthesisTurn({ text }: { text: string | null }) {
  return (
    <div style={styles.turn}>
      {/* Avatar */}
      <div style={{ ...styles.avatar, borderColor: "var(--mp-accent)", color: "var(--mp-accent)" }}>
        <MpIcon name="agent" size={14} />
      </div>

      {/* Bubble */}
      <div style={styles.synthesisBubble}>
        <div style={styles.turnHeader}>
          <span style={styles.synthesisName}>Final synthesis</span>
          <Badge tone="info" dot={false}>analysis-only narrative</Badge>
        </div>
        <p style={styles.synthesisNote}>
          Narrative summary from the portfolio-manager role.
        </p>
        {text ? (
          <pre style={styles.synthesisPre}>{text}</pre>
        ) : (
          <p style={styles.unavailable}>
            <MpIcon name="circle" size={11} style={{ color: "var(--mp-mute)", verticalAlign: "middle", marginRight: 4 }} />
            No final synthesis produced.
          </p>
        )}
      </div>
    </div>
  );
}

/* ── Styles ──────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  /* Panel container */
  panel: {
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    display: "flex",
    flexDirection: "column",
    minHeight: 0,
    overflow: "hidden",
  },
  panelHeader: {
    padding: "var(--space-3) var(--space-5)",
    borderBottom: "1px solid var(--mp-rule)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-3)",
    flexWrap: "wrap",
  },
  eyebrow: {
    margin: 0,
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
    color: "var(--mp-mute)",
  },
  headerSub: {
    margin: 0,
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-ink-2)",
    marginTop: 2,
  },
  headerRight: {
    display: "flex",
    gap: "var(--space-2)",
    alignItems: "center",
  },

  /* Message stream */
  stream: {
    padding: "var(--space-4) var(--space-5)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-5)",
    flex: 1,
  },

  /* Turn layout */
  turn: {
    display: "grid",
    gridTemplateColumns: "30px 1fr",
    gap: "var(--space-3)",
  },
  avatar: {
    width: 30,
    height: 30,
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-card-2)",
    border: "1px solid currentColor",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  bubble: {
    padding: "var(--space-3) var(--space-4)",
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderLeft: "2px solid var(--mp-mute)",
    borderRadius: "var(--radius-md)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  turnHeader: {
    display: "flex",
    alignItems: "baseline",
    justifyContent: "space-between",
    gap: "var(--space-2)",
    flexWrap: "wrap",
  },
  turnName: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
  },
  turnBadges: {
    display: "flex",
    gap: "var(--space-1)",
    flexWrap: "wrap",
  },
  roleGuardrail: {
    margin: 0,
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    lineHeight: 1.5,
    fontStyle: "italic",
  },
  unavailable: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-mute)",
    margin: 0,
    lineHeight: 1.6,
  },
  markdownPre: {
    margin: 0,
    padding: "var(--space-3) var(--space-4)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    color: "var(--mp-ink-2)",
    fontFamily: "var(--mp-font-mono, monospace)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.6,
  },

  /* Synthesis turn */
  synthesisBubble: {
    padding: "var(--space-3) var(--space-4)",
    backgroundColor: "var(--mp-card-2)",
    border: "1px solid var(--mp-rule-2)",
    borderLeft: "3px solid var(--mp-accent)",
    borderRadius: "var(--radius-md)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  synthesisName: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    color: "var(--mp-accent-ink)",
    fontFamily: "var(--mp-font-display, serif)",
  },
  synthesisNote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: 0,
    lineHeight: 1.6,
    fontStyle: "italic",
  },
  synthesisPre: {
    margin: 0,
    padding: "var(--space-3) var(--space-4)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper)",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    color: "var(--mp-ink)",
    fontFamily: "var(--mp-font-sans, sans-serif)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.65,
    fontStyle: "italic",
  },

  /* Warning / safety blocks */
  warningBlock: {
    padding: "var(--space-3) var(--space-4)",
    backgroundColor: "var(--mp-card-2)",
    border: "1px dashed var(--mp-rule-2)",
    borderRadius: "var(--radius-md)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
  },
  warningHeader: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
  },
  warningTitle: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    color: "var(--mp-stale)",
  },
  warningList: {
    margin: 0,
    padding: 0,
    listStyle: "none",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
  },
  warningRow: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
    fontSize: "var(--font-size-xs)",
  },
  warningCode: {
    color: "var(--mp-stale)",
    fontWeight: 700,
    fontFamily: "var(--mp-font-mono, monospace)",
  },
  warningMsg: { color: "var(--mp-ink-2)" },
  chipRow: {
    display: "flex",
    gap: "var(--space-2)",
    flexWrap: "wrap",
  },
};
