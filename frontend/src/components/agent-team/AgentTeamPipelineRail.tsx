import type {
  AgentTeamAnalysisConsoleRead,
  AgentTeamRole,
  AgentTeamRoleOutputRead,
  LLMProviderStatus,
} from "../../types/agentTeam";
import { AGENT_TEAM_STAGE_ORDER } from "../../types/agentTeam";
import { Panel, Pill, type MpTone } from "../shared/mp";
import { MpIcon, type MpIconName } from "../shared/mp";

/**
 * AgentTeamPipelineRail — left rail with pipeline status (P20C-T5).
 *
 * Prototype-aligned: circular step indicators with MpIcon status,
 * role name and subtitle, and compact status/provider pills. Roles
 * display in fixed pipeline order.
 *
 * Each status indicator uses icon + text — never color alone.
 */

/** Local fallback name + presentational subtitle. The `name` is used only when
 *  no role output exists yet (pending); when output exists, the backend-owned
 *  `display_name` is rendered verbatim. Subtitles/icons/order are presentational
 *  helpers only and are never derived from the machine `role_name` as a label. */
const ROLE_DISPLAY: Record<AgentTeamRole, { name: string; sub: string }> = {
  fundamentals_analyst: { name: "Fundamentals analyst", sub: "Earnings, valuation, margins" },
  news_analyst: { name: "News analyst", sub: "Catalysts, sentiment, events" },
  technical_analyst: { name: "Technical analyst", sub: "Trend, range, momentum" },
  risk_management_agent: { name: "Risk management agent", sub: "Coverage, collateral, rules" },
  portfolio_manager_agent: { name: "Portfolio manager", sub: "Synthesis, final stance" },
};

/** Quiet guardrail tooltip on the Portfolio Manager persona. */
const PORTFOLIO_MANAGER_GUARDRAIL =
  "Synthesizes the team's analysis for your review — does not manage your portfolio or recommend trades.";

function statusIcon(status: AgentTeamRoleOutputRead["status"]): { icon: MpIconName; tone: MpTone } {
  if (status === "completed") return { icon: "check", tone: "live" };
  if (status === "unavailable") return { icon: "alert", tone: "stale" };
  return { icon: "circle", tone: "mute" };
}

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

interface PipelineRailProps {
  data: AgentTeamAnalysisConsoleRead | null;
}

export default function AgentTeamPipelineRail({ data }: PipelineRailProps) {
  const byRole = new Map(data?.role_outputs.map((o) => [o.role_name, o]) ?? []);
  return (
    <Panel title="Agent team" tag="pipeline">
      <ol style={styles.list}>
        {AGENT_TEAM_STAGE_ORDER.map((role, idx) => {
          const out = byRole.get(role);
          const st = out ? statusIcon(out.status) : { icon: "circle" as MpIconName, tone: "mute" as MpTone };
          const statusLabel = out?.status ?? "pending";
          const display = ROLE_DISPLAY[role];
          // Backend-owned label verbatim when output exists; local fallback only
          // while the role is still pending (no output yet).
          const roleName = out ? out.display_name : display.name;
          const isPortfolioManager = role === "portfolio_manager_agent";
          const toneColor =
            st.tone === "live" ? "var(--mp-live)" :
            st.tone === "stale" ? "var(--mp-stale)" :
            st.tone === "block" ? "var(--mp-block)" :
            "var(--mp-mute)";

          return (
            <li key={role} style={styles.item}>
              {/* Step circle */}
              <div style={{ ...styles.stepCircle, borderColor: toneColor, color: toneColor }}>
                {out?.status === "completed" ? (
                  <MpIcon name="check" size={11} />
                ) : out?.status === "unavailable" ? (
                  <MpIcon name="alert" size={11} />
                ) : (
                  <span style={styles.stepNum}>{idx + 1}</span>
                )}
              </div>

              {/* Body */}
              <div style={styles.body}>
                <span
                  style={styles.roleName}
                  title={isPortfolioManager ? PORTFOLIO_MANAGER_GUARDRAIL : undefined}
                >
                  {roleName}
                </span>
                <span style={styles.roleSub}>{display.sub}</span>
                <div style={styles.chips}>
                  <Pill tone={out ? statusToTone(out.status) : "mute"} title={`role status = ${statusLabel}`}>
                    {statusLabel}
                  </Pill>
                  {out && (
                    <Pill tone={providerToTone(out.provider_status)} title={`provider_status = ${out.provider_status}`}>
                      {out.provider_status}
                    </Pill>
                  )}
                  {out?.is_mock && (
                    <Pill tone="mute" title="produced by the app-owned mock LLM provider">mock</Pill>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </Panel>
  );
}

const styles: Record<string, React.CSSProperties> = {
  list: {
    listStyle: "none",
    margin: 0,
    padding: 0,
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
  },
  item: {
    display: "grid",
    gridTemplateColumns: "24px 1fr",
    gap: "var(--space-3)",
    alignItems: "flex-start",
  },
  stepCircle: {
    width: 22,
    height: 22,
    borderRadius: 999,
    backgroundColor: "var(--mp-card-2)",
    border: "1px solid currentColor",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    marginTop: 1,
  },
  stepNum: {
    fontSize: 10,
    fontFamily: "var(--mp-font-mono, monospace)",
    fontWeight: 500,
  },
  body: {
    display: "flex",
    flexDirection: "column",
    gap: 1,
    minWidth: 0,
  },
  roleName: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink)",
    fontWeight: 500,
    lineHeight: 1.3,
  },
  roleSub: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    lineHeight: 1.3,
  },
  chips: {
    display: "flex",
    gap: "var(--space-1)",
    flexWrap: "wrap",
    marginTop: 2,
  },
};
