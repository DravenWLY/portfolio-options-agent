/**
 * TypeScript mirror of backend P20B dashboard-related read schemas.
 *
 * Mirrors:
 *   backend/app/schemas/trade_review_workspace.py
 *     TradeReviewListItemRead, TradeReviewListRead
 *     RiskAlertItemRead, RiskAlertListRead
 *     BrokerSnapshotReadinessRead, MarketQuoteReadinessRead,
 *     AgentProviderReadinessRead, ReviewReadinessRead
 *     DashboardSummaryDisplaySectionRead, DashboardAccountSummaryRead
 *
 * Strictly mirror the backend. The frontend never invents fields and never
 * performs financial calculations.
 */

import type { RiskSeverity } from "./api";
import type {
  ReviewActionabilityStatus,
  SupportedTradeReviewFlow,
  PortfolioCashState,
} from "./tradeReview";
import type {
  PortfolioContextShapeRead,
  PortfolioContextFreshnessRead,
  Phase20BDataMode,
  ReadinessSnapshotStatus,
  ReviewReadinessMode,
} from "./portfolioContext";

/* ── Enum literals ─────────────────────────────────────────────────────── */

export type TradeReviewReportStatus =
  | "preview_only"
  | "saved"
  | "generated"
  | "unavailable";

export type TradeReviewListSourceMode =
  | "synthetic_preview"
  | "portfolio_preview"
  | "saved_review";

export type RiskAlertCategory =
  | "concentration"
  | "cash_collateral"
  | "stale_broker_snapshot"
  | "stale_market_quote"
  | "missing_data"
  | "agent_provider";

export type RiskAlertFreshnessScope =
  | "broker_snapshot"
  | "market_quote"
  | "agent_provider"
  | "review";

export type AgentProviderMode = "mock" | "live" | "unavailable";

export type ReadinessAgentProviderStatus =
  | "available"
  | "unavailable"
  | "error"
  | "mock_default";

export type DashboardDisplaySectionKind =
  | "summary"
  | "freshness"
  | "shape"
  | "caveats";

/* ── Trade review list ─────────────────────────────────────────────────── */

export interface TradeReviewListItemRead {
  review_reference: string;
  created_at: string;
  supported_flow: SupportedTradeReviewFlow;
  review_flow_label: string;
  symbol_or_underlying: string;
  review_actionability_status: ReviewActionabilityStatus;
  highest_severity: RiskSeverity | null;
  report_status: TradeReviewReportStatus;
  source_mode: TradeReviewListSourceMode;
  broker_snapshot_freshness_label: string | null;
  market_quote_freshness_label: string | null;
}

export interface TradeReviewListRead {
  data_mode: Phase20BDataMode;
  demo_notice: string | null;
  items: TradeReviewListItemRead[];
}

/* ── Risk alerts ───────────────────────────────────────────────────────── */

export interface RiskAlertItemRead {
  alert_reference: string;
  generated_at: string;
  severity: RiskSeverity;
  category: RiskAlertCategory;
  title: string;
  summary: string;
  related_symbol_or_underlying: string | null;
  related_review_reference: string | null;
  freshness_scope: RiskAlertFreshnessScope | null;
  is_blocking: boolean;
}

export interface RiskAlertListRead {
  data_mode: Phase20BDataMode;
  demo_notice: string | null;
  items: RiskAlertItemRead[];
}

/* ── Review readiness ──────────────────────────────────────────────────── */

export interface BrokerSnapshotReadinessRead {
  freshness_scope: "broker_snapshot";
  status: ReadinessSnapshotStatus;
  as_of_label: string | null;
  reason_codes: string[];
  display_label: string;
  is_blocking: boolean;
}

export interface MarketQuoteReadinessRead {
  freshness_scope: "market_quote";
  status: ReadinessSnapshotStatus;
  as_of_label: string | null;
  reason_codes: string[];
  display_label: string;
  is_blocking: boolean;
}

export interface AgentProviderReadinessRead {
  provider_mode: AgentProviderMode;
  provider_status: ReadinessAgentProviderStatus;
  is_mock_default: boolean;
  last_checked_at: string | null;
  display_label: string;
  is_blocking: boolean;
}

export interface ReviewReadinessRead {
  data_mode: Phase20BDataMode;
  demo_notice: string | null;
  generated_at: string;
  overall_review_mode: ReviewReadinessMode;
  broker_snapshot: BrokerSnapshotReadinessRead;
  market_quotes: MarketQuoteReadinessRead;
  agent_provider: AgentProviderReadinessRead;
  recommended_user_action_label: string;
}

/* ── Dashboard account summary ─────────────────────────────────────────── */

export interface DashboardSummaryDisplaySectionRead {
  section_key: DashboardDisplaySectionKind;
  title: string;
  display_label: string;
}

export interface DashboardAccountSummaryRead {
  data_mode: Phase20BDataMode;
  demo_notice: string | null;
  generated_at: string;
  summary_reference: string;
  source_label: string;
  broker_snapshot_freshness: PortfolioContextFreshnessRead;
  market_quote_freshness: PortfolioContextFreshnessRead | null;
  market_data_unavailable: boolean;
  portfolio_shape: PortfolioContextShapeRead;
  cash_state: PortfolioCashState;
  cash_state_label: string;
  total_value_label: string | null;
  cash_label: string | null;
  stock_exposure_label: string | null;
  option_exposure_label: string | null;
  caveat_codes: string[];
  display_sections: DashboardSummaryDisplaySectionRead[];
}

/* ── Re-exports used by DashboardPage ──────────────────────────────────── */

export type { Phase20BDataMode, ReadinessSnapshotStatus, ReviewReadinessMode } from "./portfolioContext";
