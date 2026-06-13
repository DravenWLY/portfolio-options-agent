/**
 * TypeScript mirror of backend/app/schemas/trade_review_workspace.py
 * and the actionability slice it depends on (PortfolioActionabilityDecision).
 *
 * Strictly mirror the backend. The frontend never invents fields and never
 * performs financial calculations — values are rendered as the backend
 * provides them (Decimals are serialized as JSON strings by pydantic).
 */

import type { RiskSeverity } from "./api";
import type {
  ActionabilityStatus,
  DataMode,
  FreshnessStatus,
} from "./marketData";
// Phase 27C scope metadata reuses the existing Account Details mirrors so the
// review-account and portfolio-scope shapes stay identical across surfaces.
// This is a type-only import (erased at build), so the cyclic reference with
// accountDetails.ts carries no runtime cost.
import type { ReviewAccountRead, PortfolioScopeRead } from "./accountDetails";

/* ── Enum literals (backend TypeAliases) ─────────────────────────────────── */

export type SupportedTradeReviewFlow =
  | "stock_buy"
  | "stock_sell_trim"
  | "etf_buy"
  | "etf_sell_trim"
  | "covered_call"
  | "cash_secured_put";

export type WorkspaceCaveatSeverity = "info" | "warning" | "blocker";

export type ReviewActionabilityStatus =
  | "normal_review"
  | "analysis_only"
  | "manual_confirmation_required"
  | "blocked_stale_broker_snapshot"
  | "blocked_stale_market_quote"
  | "blocked_unknown_freshness"
  | "blocked_provider_error";

export type ActionabilityLanguageTier = "normal_review" | "analysis_only" | "blocked";

export type SnapshotSource = "snaptrade" | "manual" | "csv" | "synthetic_mock";

export type ProviderStatus =
  | "available"
  | "unavailable"
  | "error"
  | "reauth_required"
  | "not_applicable"
  | "unknown";

export type ActionabilityReasonScope = "broker_snapshot" | "market_quote" | "review";

export type ActionabilityReasonSeverity = "info" | "warning" | "blocker";

export type UserConfirmationState = "unconfirmed" | "confirmed" | "expired";

export type PortfolioContextSelectionMode = "latest_available" | "selected_context";

export type PortfolioContextSource = "snaptrade" | "manual" | "csv" | "synthetic_mock";

export type PortfolioCashState = "available" | "unavailable" | "not_exposed";

export type BrokerDataFreshnessStatus =
  | "fresh"
  | "cached"
  | "delayed"
  | "stale"
  | "unknown"
  | "error"
  | "reauth_required";

/* ── Request body for POST /api/trade-reviews/preview ────────────────────── */

export interface TradeReviewPreviewOptionLeg {
  underlying_symbol: string;
  option_type: "call" | "put";
  leg_action: "buy_to_open" | "sell_to_open" | "buy_to_close" | "sell_to_close";
  expiration_date: string; // YYYY-MM-DD
  strike: string; // Decimal as string
  quantity: string;
  premium?: string | null;
  multiplier?: string;
  occ_symbol?: string | null;
  support_status?: "supported" | "manual_review_required" | "unsupported";
  unsupported_reason?: string | null;
}

export interface TradeReviewWorkspacePreviewRequest {
  supported_flow: SupportedTradeReviewFlow;
  symbol?: string | null;
  quantity?: string | null;
  price_assumption?: string | null;
  option_leg?: TradeReviewPreviewOptionLeg | null;
}

/* ── Phase 18C portfolio-backed request (server-owned context) ───────────── */

export interface PortfolioContextSelectionRequest {
  mode: PortfolioContextSelectionMode;
  context_reference?: string | null;
}

/* ── Phase 27C review-account selection (request side) ─────────────────────
 * Mirrors backend `ReviewAccountSelectionRequest`. The frontend submits only
 * the opaque `account_reference` from Account Details; it never sends broker
 * IDs, provider IDs, balances, or holdings. "unselected" must carry no
 * account_reference (the backend rejects it otherwise). */
export type ReviewAccountSelectionMode = "unselected" | "selected_account";

export interface ReviewAccountSelectionRequest {
  mode: ReviewAccountSelectionMode;
  account_reference?: string | null;
}

export interface TradeReviewPortfolioPreviewRequest
  extends TradeReviewWorkspacePreviewRequest {
  portfolio_context_selection: PortfolioContextSelectionRequest;
  /** Phase 27C: the account where the user would manually place the trade.
   *  Separate from the broader `portfolio_context_selection` exposure scope. */
  review_account_selection: ReviewAccountSelectionRequest;
}

/** Discriminated submission shape used between form and page. */
export type TradeReviewSubmission =
  | { kind: "synthetic"; payload: TradeReviewWorkspacePreviewRequest }
  | { kind: "portfolio"; payload: TradeReviewPortfolioPreviewRequest };

/* ── Actionability sub-shapes ────────────────────────────────────────────── */

export interface BrokerSnapshotMetadata {
  source: SnapshotSource;
  freshness_scope: "broker_snapshot";
  freshness_status: BrokerDataFreshnessStatus;
  sync_status?: string | null;
  as_of?: string | null;
  received_at?: string | null;
  last_successful_sync_at?: string | null;
  provider_status: ProviderStatus;
  sanitized_error_code?: string | null;
  retryable?: boolean | null;
}

export interface MarketQuotesMetadata {
  freshness_scope: "market_quote";
  freshness_status: FreshnessStatus;
  data_mode: DataMode;
  actionability_status: ActionabilityStatus;
  as_of_min?: string | null;
  as_of_max?: string | null;
  received_at_min?: string | null;
  received_at_max?: string | null;
  provider_status: ProviderStatus;
  sanitized_error_code?: string | null;
  retryable?: boolean | null;
}

export interface UserConfirmationMetadata {
  state: UserConfirmationState;
  confirmed_at?: string | null;
  expires_at?: string | null;
  confirmation_scope: "broker_snapshot" | "market_quote" | "review";
}

export interface ActionabilityReason {
  code: string;
  scope: ActionabilityReasonScope;
  severity: ActionabilityReasonSeverity;
  message: string;
}

export interface PortfolioActionabilityDecision {
  policy_version: string;
  evaluated_at: string;
  review_actionability_status: ReviewActionabilityStatus;
  can_run_deterministic_review: boolean;
  can_run_agent_explanation: boolean;
  requires_user_confirmation: boolean;
  language_tier: ActionabilityLanguageTier;
  broker_snapshot: BrokerSnapshotMetadata;
  market_quotes: MarketQuotesMetadata;
  reasons: ActionabilityReason[];
  user_confirmation?: UserConfirmationMetadata | null;
}

/* ── Workspace sub-shapes ────────────────────────────────────────────────── */

export interface WorkspaceOptionLegSummaryRead {
  underlying_symbol: string;
  option_type: "call" | "put";
  leg_action: string;
  expiration_date: string;
  strike: string;
  quantity: string;
  premium?: string | null;
  multiplier: string;
  occ_symbol?: string | null;
  support_status: string;
  unsupported_reason?: string | null;
}

export interface TradeIntentSummaryRead {
  intent_id: string;
  supported_flow: SupportedTradeReviewFlow;
  asset_class: "stock" | "etf" | "option";
  intent_type: string;
  status: string;
  symbol?: string | null;
  action?: string | null;
  quantity?: string | null;
  price_assumption?: string | null;
  strategy_type?: string | null;
  underlying_symbol?: string | null;
  legs: WorkspaceOptionLegSummaryRead[];
}

export interface ScenarioPayoffPointRead {
  label: string;
  underlying_price: string;
  net_cash_flow: string;
  scenario_value: string;
  scenario_pnl: string;
  description: string;
}

export interface ScenarioPayoffSummaryRead {
  points: ScenarioPayoffPointRead[];
  max_loss: string | null;
  max_gain: string | null;
  calculation_notes: string[];
}

export interface PortfolioImpactSummaryRead {
  broker_freshness_status: string;
  market_freshness_status: string;
  market_manual_review_required: boolean;
  concentration_symbol: string | null;
  notes: string[];
}

export interface CashCollateralImpactRead {
  estimated_trade_cash_change: string | null;
  estimated_premium_cash_change: string | null;
  estimated_collateral_requirement_change: string | null;
  projected_free_cash_state: "not_exposed";
  notes: string[];
}

export interface ConcentrationAllocationImpactRead {
  concentration_symbol: string | null;
  estimated_concentration_value_change: string | null;
  allocation_drift_status: "not_modelled_in_phase_18a";
  notes: string[];
}

export interface OptionsExposureRead {
  underlying_symbol: string | null;
  assignment_share_delta: string;
  exercise_share_delta: string;
  covered_call_coverage_model: "not_applicable" | "not_fully_modelled";
  cash_secured_put_collateral_model: "not_applicable" | "generic_rule_only";
  notes: string[];
}

export interface RiskRuleViolationSummaryRead {
  code: string;
  severity: RiskSeverity;
  message: string;
  source: string;
  metric?: string | null;
  actual?: string | null;
  policy_label?: string | null;
}

export interface MissingDataWarningRead {
  code: string;
  scope: string;
  severity: "info" | "warning" | "blocker";
  message: string;
}

export interface DeterministicTradeReviewRead {
  highest_severity: RiskSeverity | null;
  has_blocker: boolean;
  portfolio_impact: PortfolioImpactSummaryRead;
  cash_collateral_impact: CashCollateralImpactRead;
  concentration_allocation_impact: ConcentrationAllocationImpactRead;
  options_exposure: OptionsExposureRead;
  risk_rule_violations: RiskRuleViolationSummaryRead[];
  missing_data_warnings: MissingDataWarningRead[];
  scenario_payoff_summary: ScenarioPayoffSummaryRead;
}

export interface AgentOrchestrationSummaryRead {
  run_reference: string;
  workflow_version: string;
  review_actionability_status: ReviewActionabilityStatus | null;
  stage_order: string[];
  stage_statuses: Record<string, string>;
  unavailable_stages: Record<string, string>;
  source_agent_names: string[];
  report_composed: boolean;
}

export interface AnalysisOnlyReportOutputRead {
  title: string;
  content_markdown: string;
  deterministic_sections: string[];
  llm_generated_sections: string[];
  source_agent_names: string[];
}

export interface PortfolioContextSummaryRead {
  context_reference: string;
  context_source: PortfolioContextSource;
  selection_mode: PortfolioContextSelectionMode;
  summary_as_of: string | null;
  latest_snapshot_as_of: string | null;
  broker_snapshot: BrokerSnapshotMetadata;
  stock_position_count: number;
  option_position_count: number;
  cash_state: PortfolioCashState;
  label: string | null;
}

export interface WorkspaceCaveatRead {
  code: string;
  severity: WorkspaceCaveatSeverity;
  applies_to: string;
  message: string;
}

/* ── Phase 27C report scope metadata (read side) ───────────────────────────
 * Mirrors backend `ReportScopeMetadataRead`. Renders only backend-owned
 * display labels: `review_account` / `portfolio_context_scope` carry opaque
 * references that the UI must NOT display — only their display labels. */
export interface ReportScopeMetadataRead {
  review_account: ReviewAccountRead | null;
  portfolio_context_scope: PortfolioScopeRead;
  scope_summary_label: string;
  account_level_feasibility_evaluated: boolean;
  scope_caveat_codes: string[];
}

export interface TradeReviewWorkspaceRead {
  review_reference: string;
  generated_at: string;
  calculation_version: string;
  supported_flow: SupportedTradeReviewFlow;
  trade_intent_summary: TradeIntentSummaryRead;
  actionability: PortfolioActionabilityDecision;
  deterministic_review: DeterministicTradeReviewRead;
  agent_orchestration?: AgentOrchestrationSummaryRead | null;
  report_output?: AnalysisOnlyReportOutputRead | null;
  caveats: WorkspaceCaveatRead[];
  /** Phase 18C: present on responses from /trade-reviews/portfolio-preview;
   *  null on the synthetic /trade-reviews/preview path. */
  portfolio_context?: PortfolioContextSummaryRead | null;
  /** Phase 27C: scope used to generate this review (review account +
   *  broader portfolio context). Present on portfolio-preview responses. */
  scope_metadata?: ReportScopeMetadataRead | null;
}
