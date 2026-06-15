/**
 * TypeScript mirror of backend/app/schemas/agent_team.py.
 *
 * Field names, optionality, Decimal→string semantics, and Literal unions
 * follow the backend exactly. Per P19A-T2..T5 deferred polish notes, the
 * structural Records (broker_snapshot_freshness / market_quote_freshness /
 * deterministic_evidence_summary) stay loose-typed (`Record<string, unknown>`)
 * to mirror the backend `dict[str, object]` shape. Do not invent typed fields.
 */
import type { TradeReviewPortfolioPreviewRequest } from "./tradeReview";
import type { ReviewActionabilityStatus } from "./tradeReview";
import type { PortfolioContextSelectionMode } from "./tradeReview";
import type { PortfolioScopeMode } from "./accountDetails";

/* ── Enums (mirror llm_provider.py + agent_team.py) ─────────────────────── */

export type AgentTeamRole =
  | "fundamentals_analyst"
  | "news_analyst"
  | "technical_analyst"
  | "risk_management_agent"
  | "portfolio_manager_agent";

export const AGENT_TEAM_STAGE_ORDER: readonly AgentTeamRole[] = [
  "fundamentals_analyst",
  "news_analyst",
  "technical_analyst",
  "risk_management_agent",
  "portfolio_manager_agent",
] as const;

export type LLMProviderStatus =
  | "ok"
  | "skipped"
  | "failed"
  | "rate_limited"
  | "quota_exceeded"
  | "provider_timeout"
  | "provider_auth_error"
  | "provider_unavailable"
  | "invalid_response"
  | "safety_validation_failed";

export type AgentTeamRunStatus = "completed" | "partially_completed" | "failed";

export type AgentTeamRoleOutputStatus = "completed" | "unavailable" | "skipped";

/* ── Request — same shape as TradeReviewPortfolioPreviewRequest ──────────── */
/* AgentTeamAnalysisPreviewRequest extends it with `extra="forbid"`. We send
   nothing more than the parent already allows. */

export type AgentTeamAnalysisPreviewRequest = TradeReviewPortfolioPreviewRequest;

/* ── Response — AgentTeamAnalysisConsoleRead 1:1 ─────────────────────────── */

export interface AgentTeamRoleOutputRead {
  role_name: AgentTeamRole;
  /** Backend-owned user-facing label (P25A-T11). Render verbatim. */
  display_name: string;
  status: AgentTeamRoleOutputStatus;
  provider_status: LLMProviderStatus;
  content_markdown: string | null;
  is_mock: boolean;
  unavailable_reason?: string | null;
}

export interface AgentTeamStageRead {
  stage: string;
  status: string;
  role_name?: AgentTeamRole | null;
  /** Backend-owned user-facing label (P25A-T11); null for non-persona stages. */
  display_name?: string | null;
  provider_status?: LLMProviderStatus | null;
  unavailable_reason?: string | null;
}

export interface AgentTeamProviderWarningRead {
  code: string;
  message: string;
}

export interface AgentTeamScopeSummaryRead {
  scope_present: boolean;
  portfolio_scope_mode: PortfolioScopeMode;
  portfolio_context_selection_mode: PortfolioContextSelectionMode | null;
  selected_context_present: boolean;
  included_account_count: number;
  excluded_account_count: number;
  review_account_present: boolean;
  account_level_feasibility_evaluated: boolean;
  scope_caveat_codes: string[];
}

export interface AgentTeamAnalysisConsoleRead {
  run_reference: string;
  workflow_version: string;
  run_status: AgentTeamRunStatus;
  generated_at: string;
  review_flow_label: string;
  review_actionability_status: ReviewActionabilityStatus;
  /** Loose-typed per backend `dict[str, object]`. Render verbatim as a
   *  key/value list; do not infer typed fields. */
  broker_snapshot_freshness: Record<string, unknown>;
  /** Loose-typed per backend `dict[str, object]`. Distinct scope from broker. */
  market_quote_freshness: Record<string, unknown>;
  /** Loose-typed per backend `dict[str, object]` — counts/categories only;
   *  the backend never includes values, holdings, or identifiers here. */
  deterministic_evidence_summary: Record<string, unknown>;
  /** Lossy reviewed scope summary only. It intentionally carries no account
   *  labels, refs, balances, holdings, quantities, provider IDs, or payloads. */
  scope_summary: AgentTeamScopeSummaryRead;
  role_outputs: AgentTeamRoleOutputRead[];
  final_synthesis: string | null;
  provider_warnings: AgentTeamProviderWarningRead[];
  stages: AgentTeamStageRead[];
  safety_flags: string[];
}
