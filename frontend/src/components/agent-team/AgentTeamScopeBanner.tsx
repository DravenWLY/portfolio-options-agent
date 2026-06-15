import type { CSSProperties } from "react";
import type { AgentTeamScopeSummaryRead } from "../../types/agentTeam";
import { Badge } from "../shared/mp";
import { MpIcon } from "../shared/mp";

interface AgentTeamScopeBannerProps {
  scope?: AgentTeamScopeSummaryRead | null;
}

export default function AgentTeamScopeBanner({ scope }: AgentTeamScopeBannerProps) {
  if (!scope?.scope_present) {
    return (
      <section className="mp-agent-scope-banner" style={styles.bannerBase} aria-label="Agent analysis scope">
        <div style={styles.titleCluster}>
          <MpIcon name="info" size={16} style={styles.iconMuted} />
          <div>
            <p style={styles.kicker}>Review scope</p>
            <p style={styles.title}>Scope metadata unavailable</p>
          </div>
        </div>
        <Badge tone="mute" dot={false}>Generic context</Badge>
      </section>
    );
  }

  const caveatCodes = Array.isArray(scope.scope_caveat_codes)
    ? scope.scope_caveat_codes.filter(Boolean)
    : [];

  return (
    <section className="mp-agent-scope-banner" style={styles.bannerBase} aria-label="Agent analysis scope">
      <div style={styles.titleCluster}>
        <MpIcon name="circle" size={16} style={styles.iconAccent} />
        <div>
          <p style={styles.kicker}>Review scope</p>
          <p style={styles.title}>{scopeSummaryTitle(scope)}</p>
        </div>
      </div>

      <div style={styles.badges} aria-label="Scope details">
        <Badge tone={scope.review_account_present ? "info" : "mute"} dot={scope.review_account_present}>
          {scope.review_account_present ? "Review account selected" : "No review account"}
        </Badge>
        <Badge
          tone={scope.account_level_feasibility_evaluated ? "live" : "mute"}
          dot={scope.account_level_feasibility_evaluated}
        >
          {scope.account_level_feasibility_evaluated
            ? "Account feasibility evaluated"
            : "Account feasibility not evaluated"}
        </Badge>
        <Badge tone="info" dot={false}>
          {portfolioModeLabel(scope.portfolio_scope_mode)}
        </Badge>
        {scope.selected_context_present && (
          <Badge tone="mute" dot={false}>{contextSelectionLabel(scope.portfolio_context_selection_mode)}</Badge>
        )}
        {scope.included_account_count > 0 && (
          <Badge tone="mute" dot={false}>{scope.included_account_count} included</Badge>
        )}
        {scope.excluded_account_count > 0 && (
          <Badge tone="stale" dot={false}>{scope.excluded_account_count} excluded</Badge>
        )}
      </div>

      {caveatCodes.length > 0 && (
        <details className="mp-agent-scope-notes" style={styles.notes}>
          <summary style={styles.notesSummary}>
            <span>Scope notes</span>
            <span style={styles.notesCount}>{caveatCodes.length}</span>
          </summary>
          <div style={styles.noteChips}>
            {caveatCodes.map((code) => (
              <code key={code} style={styles.codeChip}>{code}</code>
            ))}
          </div>
        </details>
      )}
    </section>
  );
}

function scopeSummaryTitle(scope: AgentTeamScopeSummaryRead): string {
  if (scope.review_account_present && scope.account_level_feasibility_evaluated) {
    return "Review account and portfolio context included";
  }
  if (scope.review_account_present) return "Review account selected with portfolio context";
  return "Portfolio context without a review account";
}

function portfolioModeLabel(mode: AgentTeamScopeSummaryRead["portfolio_scope_mode"]): string {
  const labels: Record<AgentTeamScopeSummaryRead["portfolio_scope_mode"], string> = {
    all_connected_accounts: "All connected accounts",
    single_account: "Single-account context",
    selected_account_group: "Selected account group",
    selected_context: "Selected portfolio context",
    unavailable: "Context unavailable",
  };
  return labels[mode] ?? "Portfolio context";
}

function contextSelectionLabel(
  mode: AgentTeamScopeSummaryRead["portfolio_context_selection_mode"],
): string {
  if (mode === "selected_context") return "Selected context";
  if (mode === "latest_available") return "Latest available context";
  return "Context selected";
}

const styles: Record<string, CSSProperties> = {
  bannerBase: {
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderLeft: "4px solid var(--mp-accent)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3) var(--space-4)",
    minWidth: 0,
  },
  titleCluster: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  iconAccent: {
    color: "var(--mp-accent)",
    flexShrink: 0,
  },
  iconMuted: {
    color: "var(--mp-mute)",
    flexShrink: 0,
  },
  kicker: {
    margin: 0,
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    fontWeight: 700,
  },
  title: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    lineHeight: 1.35,
  },
  badges: {
    display: "flex",
    flexWrap: "wrap",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  notes: {
    justifySelf: "end",
    minWidth: 0,
    position: "relative",
  },
  notesSummary: {
    cursor: "pointer",
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    listStyle: "none",
  },
  notesCount: {
    color: "var(--mp-mute)",
    fontVariantNumeric: "tabular-nums",
  },
  noteChips: {
    position: "absolute",
    right: 0,
    top: "calc(100% + 8px)",
    zIndex: 2,
    display: "flex",
    flexDirection: "column",
    gap: 6,
    minWidth: 220,
    maxWidth: 360,
    padding: "var(--space-3)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--mp-card)",
    boxShadow: "var(--mp-shadow-md)",
  },
  codeChip: {
    color: "var(--mp-ink-2)",
    backgroundColor: "var(--mp-card-2)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "3px 6px",
    fontSize: "var(--font-size-xs)",
    overflowWrap: "anywhere",
  },
};
