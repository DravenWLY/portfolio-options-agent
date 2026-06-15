/**
 * Report status vocabulary + display metadata for the Reports library.
 *
 * Single source of truth for turning the saved, backend-owned
 * `agent_summary` (or its absence) into an honest `AgentTeamReportStatus` and
 * the labels/tones the UI renders. Pure functions only — no rendering, no
 * network, no current-state inference. Saved report state is read ONLY from the
 * saved record (`agent_summary` + its `report_status`), never from the current
 * account selector, Account Details, route, or cached frontend state.
 *
 * Mirrors backend `_agent_team_report_status_from_summary` /
 * `_agent_team_run_completeness` (backend/app/schemas/reports.py) so the
 * frontend degrades to the same honest state when `report_status` is absent.
 *
 * Wording rule (P28A/P29A safety): never imply advice, recommendation, buy/sell,
 * order/execute, safe/ready-to-trade, guaranteed return, or an automated/AI
 * stock-picker decision. "Analysis only" and "manual decision support" framing
 * only.
 */
import type { MpTone, MpIconName } from "../shared/mp";
import type {
  AgentTeamReportRoleStatus,
  AgentTeamReportRunCompleteness,
  AgentTeamReportStatus,
  ReportThreadRead,
  SavedAgentTeamSummaryRead,
} from "../../types/api";

export interface ReportStatusMeta {
  /** Detail-header label for the report state. */
  label: string;
  /** Compact chip label used in the library list. */
  chipLabel: string;
  tone: MpTone;
  icon: MpIconName;
  /** Honest one-line description of what this saved state means. */
  description: string;
}

/**
 * Derive the report status from a saved report thread, reading only the saved
 * `agent_summary`. No `agent_summary` → `source_snapshot`. Otherwise prefer the
 * persisted `report_status`, falling back to the backend derivation rule.
 */
export function deriveReportStatus(thread: ReportThreadRead): AgentTeamReportStatus {
  const summary = thread.agent_summary;
  if (!summary) return "source_snapshot";
  return summary.report_status ?? deriveStatusFromSummary(summary);
}

function deriveStatusFromSummary(summary: SavedAgentTeamSummaryRead): AgentTeamReportStatus {
  if (summary.run_status === "failed") return "agent_unavailable";
  if (summary.final_synthesis_markdown) return "full_agent_report";
  return "deterministic_draft";
}

/** True only when a generated, validated Agent Team narrative is the body. */
export function hasAgentReport(status: AgentTeamReportStatus): boolean {
  return status === "full_agent_report";
}

/** Count completed role sections → run completeness, mirroring the backend. */
export function runCompleteness(
  summary: SavedAgentTeamSummaryRead | null,
): AgentTeamReportRunCompleteness {
  const roles = summary?.role_summaries ?? [];
  if (roles.length === 0) return "none";
  const completed = roles.filter((r) => r.role_status === "completed").length;
  if (completed === roles.length) return "full";
  if (completed > 0) return "partial";
  return "none";
}

/** Number of analyst roles that were skipped (derived from role_summaries —
 *  no new backend field). */
export function skippedRoleCount(summary: SavedAgentTeamSummaryRead | null): number {
  return (summary?.role_summaries ?? []).filter((r) => r.role_status === "skipped").length;
}

/** Compact, honest coverage note for a generated report. Derived from the
 *  existing `role_summaries`; today the only skipped roles are the public market
 *  analysts, which are not yet enabled. Returns null when nothing was skipped. */
export function coverageNote(summary: SavedAgentTeamSummaryRead | null): string | null {
  if (skippedRoleCount(summary) === 0) return null;
  return "Public market analysts are not yet enabled, so this report covers the portfolio-aware roles only.";
}

export function runCompletenessLabel(value: AgentTeamReportRunCompleteness): string {
  switch (value) {
    case "full":
      return "All roles completed";
    case "partial":
      return "Some roles completed";
    case "none":
      return "No roles completed";
  }
}

export const REPORT_STATUS_META: Record<AgentTeamReportStatus, ReportStatusMeta> = {
  full_agent_report: {
    label: "Agent Team report",
    chipLabel: "Agent Team analysis",
    tone: "accent",
    icon: "agent",
    description:
      "Agent Team analysis generated from the saved evidence package. Analysis only — deterministic backend services own all calculations.",
  },
  deterministic_draft: {
    label: "Deterministic draft",
    chipLabel: "Deterministic draft",
    tone: "stale",
    icon: "info",
    description:
      "Deterministic evidence is saved as a draft. The Agent Team narrative was not generated for this snapshot.",
  },
  agent_unavailable: {
    label: "Agent Team unavailable",
    chipLabel: "Agent Team unavailable",
    tone: "mute",
    icon: "alert",
    description:
      "Agent Team generation was skipped safely. The saved deterministic evidence remains available for manual review.",
  },
  validation_failed: {
    label: "Narrative withheld",
    chipLabel: "Narrative withheld",
    tone: "block",
    icon: "shield",
    description:
      "The generated narrative was withheld by safety validation. The saved deterministic evidence remains available for manual review.",
  },
  source_snapshot: {
    label: "Source snapshot",
    chipLabel: "Source snapshot",
    tone: "mute",
    icon: "clock",
    description:
      "Saved deterministic review snapshot. No Agent Team report has been generated from it yet.",
  },
};

export function reportStatusMeta(status: AgentTeamReportStatus): ReportStatusMeta {
  return REPORT_STATUS_META[status];
}

export interface RoleStatusMeta {
  label: string;
  tone: MpTone;
}

const ROLE_STATUS_META: Record<AgentTeamReportRoleStatus, RoleStatusMeta> = {
  completed: { label: "Completed", tone: "live" },
  skipped: { label: "Skipped", tone: "mute" },
  gated: { label: "Gated", tone: "stale" },
  unavailable: { label: "Unavailable", tone: "mute" },
  validation_failed: { label: "Withheld", tone: "block" },
};

export function roleStatusMeta(status: AgentTeamReportRoleStatus): RoleStatusMeta {
  return ROLE_STATUS_META[status];
}

/** Friendly labels for evidence `section_key`s cited by roles/synthesis.
 *  Keys come from the P29A-T2 canonical citation vocabulary (keys only — the
 *  underlying values are never exposed to the frontend). */
const EVIDENCE_KEY_LABELS: Record<string, string> = {
  trade_intent_summary: "Trade intent summary",
  scope_state: "Review scope state",
  actionability: "Actionability / review mode",
  freshness: "Data freshness",
  account_readiness: "Account readiness",
  portfolio_impact_summary: "Portfolio impact summary",
  before_after_portfolio_impact: "Before / after portfolio impact",
  concentration_risk_drift: "Concentration & risk drift",
  liquidity_collateral_caveats: "Liquidity & collateral caveats",
  options_exposure_summary: "Options exposure summary",
  market_quote_freshness: "Market quote freshness",
  economic_awareness_snapshot: "Economic awareness snapshot",
  market_mood_snapshot: "Market Mood snapshot",
};

export function evidenceKeyLabel(key: string): string {
  return EVIDENCE_KEY_LABELS[key] ?? humanizeCode(key);
}

/** Turn a snake/kebab code into a readable phrase for audit display.
 *  Display-only; the raw code is still shown in monospace where it is audit
 *  provenance, matching the existing scope-caveat treatment. */
export function humanizeCode(code: string): string {
  const spaced = code.replace(/[_-]+/g, " ").trim();
  if (!spaced) return code;
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

/** Humanize a provider-status label (e.g. `provider_unavailable`). */
export function providerStatusLabel(status: string): string {
  return humanizeCode(status);
}
