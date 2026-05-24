import type {
  AgentTeamAnalysisConsoleRead,
  AgentTeamRole,
  AgentTeamRoleOutputRead,
  LLMProviderStatus,
} from "../../types/agentTeam";
import { AGENT_TEAM_STAGE_ORDER } from "../../types/agentTeam";
import { Panel, Pill, type MpTone } from "../shared/mp";

/**
 * AgentTeamPipelineRail — Modern Portfolio Desk left rail (P20A-T1).
 *
 * Translated (not pasted) from the agent-team pipeline list in
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/agent-console.tsx
 *
 * Renders the five roles in fixed stage order with their `status`,
 * `provider_status`, and `is_mock` indicator. Each chip pairs an icon
 * glyph with text — never color-only. No streaming animation: the
 * backend response is single-shot.
 */

const ROLE_DISPLAY: Record<AgentTeamRole, string> = {
  fundamentals_analyst: "Fundamentals analyst",
  news_analyst: "News analyst",
  technical_analyst: "Technical analyst",
  risk_management_agent: "Risk management agent",
  portfolio_manager_agent: "Portfolio manager agent",
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

interface PipelineRailProps {
  data: AgentTeamAnalysisConsoleRead | null;
}

export default function AgentTeamPipelineRail({ data }: PipelineRailProps) {
  const byRole = new Map(data?.role_outputs.map((o) => [o.role_name, o]) ?? []);
  return (
    <Panel title="Agent team" tag="pipeline · fixed order">
      <ol style={styles.list}>
        {AGENT_TEAM_STAGE_ORDER.map((role, idx) => {
          const out = byRole.get(role);
          const stageTone: MpTone = out ? statusToTone(out.status) : "mute";
          const statusLabel = out?.status ?? "pending";
          return (
            <li key={role} style={styles.item}>
              <span style={styles.index}>{String(idx + 1).padStart(2, "0")}</span>
              <div style={styles.body}>
                <span style={styles.roleName}>{ROLE_DISPLAY[role]}</span>
                <div style={styles.chips}>
                  <Pill tone={stageTone} title={`role status = ${statusLabel}`}>{statusLabel}</Pill>
                  {out && (
                    <Pill tone={providerToTone(out.provider_status)} title={`provider_status = ${out.provider_status}`}>
                      provider · {out.provider_status}
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
  list: { listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "var(--space-3)" },
  item: { display: "grid", gridTemplateColumns: "auto 1fr", gap: "var(--space-3)", alignItems: "flex-start" },
  index: { fontFamily: "var(--mp-font-mono)", fontSize: "var(--font-size-xs)", color: "var(--mp-mute-2)", paddingTop: 2, width: 22 },
  body: { display: "flex", flexDirection: "column", gap: "var(--space-1)", minWidth: 0 },
  roleName: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink)", fontWeight: 500 },
  chips: { display: "flex", gap: "var(--space-1)", flexWrap: "wrap" },
};
