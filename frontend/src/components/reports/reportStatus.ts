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
  SavedAgentTeamRoleSummaryRead,
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

/** Portfolio-aware roles, shown as the primary band. Everything else (the
 *  public analysts) is the secondary "market context" band. Backend-owned role
 *  names — never renamed in the UI. */
export const PRIMARY_ROLE_NAMES: readonly string[] = [
  "risk_management_agent",
  "portfolio_manager_agent",
];

export interface SplitRoles {
  primary: SavedAgentTeamRoleSummaryRead[];
  context: SavedAgentTeamRoleSummaryRead[];
}

/** Split saved role summaries into the primary portfolio-aware band and the
 *  secondary public "market context" band, preserving canonical primary order. */
export function splitRoles(summary: SavedAgentTeamSummaryRead | null): SplitRoles {
  const roles = summary?.role_summaries ?? [];
  const primary = PRIMARY_ROLE_NAMES.map((name) =>
    roles.find((r) => r.role_name === name),
  ).filter((r): r is SavedAgentTeamRoleSummaryRead => Boolean(r));
  const context = roles.filter((r) => !PRIMARY_ROLE_NAMES.includes(r.role_name));
  return { primary, context };
}

export interface PublicCoverage {
  done: number;
  total: number;
  /** Compact text for the trust strip. */
  text: string;
  /** Longer, honest note for the market-context band header (null when N/A). */
  note: string | null;
}

/** Public-analyst coverage, derived only from saved `role_status` (Track A —
 *  no new backend field). Honest and non-defect: skipped public roles read as
 *  "not yet enabled", never as an error. */
export function publicCoverage(summary: SavedAgentTeamSummaryRead | null): PublicCoverage {
  if (!summary) {
    return { done: 0, total: 0, text: "Coverage pending — no analysis generated", note: null };
  }
  const { context } = splitRoles(summary);
  const total = context.length;
  const done = context.filter((r) => r.role_status === "completed").length;
  if (total === 0) {
    return { done: 0, total: 0, text: "Portfolio-aware roles only", note: null };
  }
  if (done === 0) {
    return {
      done,
      total,
      text: "Portfolio-aware roles only",
      note: "Public market analysts are not yet enabled, so this report covers the portfolio-aware roles only.",
    };
  }
  return {
    done,
    total,
    text: `${done} of ${total} public analysts contributing`,
    note: `${done} of ${total} public analysts contributed; the rest had no reviewed public evidence.`,
  };
}

/** Rail status filter (client-side, over already-loaded threads). */
export type ReportFilterValue =
  | "all"
  | "full_agent_report"
  | "source_snapshot"
  | "no_narrative";

export const REPORT_FILTER_OPTIONS: { value: ReportFilterValue; label: string }[] = [
  { value: "all", label: "All reports" },
  { value: "full_agent_report", label: "Agent Team report" },
  { value: "source_snapshot", label: "Source snapshot" },
  { value: "no_narrative", label: "Draft / unavailable" },
];

/** Whether a derived report status passes the rail status filter. */
export function matchesStatusFilter(
  status: AgentTeamReportStatus,
  filter: ReportFilterValue,
): boolean {
  switch (filter) {
    case "all":
      return true;
    case "full_agent_report":
      return status === "full_agent_report";
    case "source_snapshot":
      return status === "source_snapshot";
    case "no_narrative":
      return (
        status === "deterministic_draft" ||
        status === "agent_unavailable" ||
        status === "validation_failed"
      );
  }
}

/** Whether a saved report matches a free-text query (title + report type only —
 *  both are display-safe saved fields; no inference, no private data). */
export function matchesQuery(thread: ReportThreadRead, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (q === "") return true;
  return (
    thread.title.toLowerCase().includes(q) ||
    thread.report_type.toLowerCase().includes(q)
  );
}

/** Status badge icon per role status (paired with text — never color-only). */
export function roleStatusIcon(status: AgentTeamReportRoleStatus): MpIconName {
  if (status === "completed") return "check";
  if (status === "validation_failed") return "shield";
  return "info";
}

/** First paragraph of a role narrative, for the compact context-card snippet. */
export function firstParagraph(markdown: string | null): string {
  if (!markdown) return "";
  return markdown.replace(/\r\n/g, "\n").split("\n\n")[0].trim();
}

/** Honest, non-defect copy for a role with no narrative, keyed on the sanitized
 *  `unavailable_reason`. Falls back to a neutral line. */
export function roleUnavailableText(reason: string | null): string {
  switch (reason) {
    case "no_reviewed_public_evidence":
      return "No reviewed public evidence was attached for this analyst.";
    case "public_evidence_not_available":
      return "Public evidence was not available for this analyst.";
    case "public_evidence_not_applicable":
      return "Public evidence is not applicable to this saved scope.";
    case "provider_unavailable":
      return "The provider was unavailable, so no narrative was produced.";
    case "safety_validation_failed":
      return "The narrative was withheld by safety validation.";
    case "blocked_actionability_llm_roles_skipped":
      return "The review was gated, so analyst narratives were not generated.";
    default:
      return "No narrative was produced for this role.";
  }
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
      "The generated narrative was withheld by safety validation; the offending text is never shown. The saved deterministic evidence remains available for manual review.",
  },
  source_snapshot: {
    label: "Source snapshot",
    chipLabel: "Source snapshot",
    tone: "mute",
    icon: "clock",
    description:
      "Saved deterministic review snapshot. This is a complete kept analysis; no Agent Team report has been generated from it yet.",
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

/** Friendly display labels for backend-owned scope-note / caveat / warning codes
 *  (P31A-T3). Static presentation copy over existing reviewed code fields only —
 *  no new evidence, freshness, actionability, feasibility, or status semantics.
 *  The raw code stays reachable for audit (title/disclosure). Wording approved by
 *  Codex B (P31A-T2) and Claude B pre-implementation review. */
const SCOPE_NOTE_LABELS: Record<string, string> = {
  buying_power_display_only: "Broker capacity label is context only; not a feasibility input",
  account_level_feasibility_not_evaluated: "Account-level feasibility not evaluated",
  current_position_truth_unstable: "Current positions not confirmed",
  cash_collateral_not_fully_modeled: "Collateral not fully modeled",
  cash_collateral_policy_not_reviewed: "Cash-collateral policy not reviewed",
  review_account_scope_membership_unknown: "Account scope membership not confirmed",
  selected_context_scope: "Specific saved portfolio context",
  public_evidence_roles_skipped: "Public analyst roles not run",
};

/** Friendly label for a scope-note / caveat / warning code. Unmapped codes fall
 *  back to humanizeCode so nothing renders as raw snake_case on the golden path. */
export function scopeNoteLabel(code: string): string {
  return SCOPE_NOTE_LABELS[code] ?? humanizeCode(code);
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
