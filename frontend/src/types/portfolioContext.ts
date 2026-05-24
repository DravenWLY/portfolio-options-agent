/**
 * TypeScript mirror of backend P20B-T4 portfolio-context read schemas.
 *
 * Mirrors:
 *   backend/app/schemas/trade_review_workspace.py
 *     PortfolioContextShapeRead
 *     PortfolioContextFreshnessRead
 *     PortfolioContextActionabilityPreviewRead
 *     PortfolioContextRead
 *     PortfolioContextListRead
 *     PortfolioContextDetailRead
 *
 * Strictly mirror the backend. The frontend never invents fields and never
 * performs financial calculations — values are rendered as the backend
 * provides them.
 */

import type {
  PortfolioCashState,
  ReviewActionabilityStatus,
  SupportedTradeReviewFlow,
} from "./tradeReview";

/* ── Enum literals ─────────────────────────────────────────────────────── */

export type PortfolioContextSourceKind =
  | "broker_snapshot"
  | "manual"
  | "csv"
  | "synthetic_demo";

export type ReadinessSnapshotStatus =
  | "fresh"
  | "manual_review"
  | "stale"
  | "unknown"
  | "unavailable";

export type ReviewReadinessMode =
  | "normal_review"
  | "analysis_only"
  | "manual_confirmation_required"
  | "blocked";

export type Phase20BDataMode = "synthetic_demo" | "persisted";

/* ── Sub-shapes ────────────────────────────────────────────────────────── */

export interface PortfolioContextShapeRead {
  stock_position_count: number;
  option_position_count: number;
}

export interface PortfolioContextFreshnessRead {
  freshness_scope: "broker_snapshot" | "market_quote";
  status: ReadinessSnapshotStatus;
  as_of_label: string | null;
  display_label: string;
  reason_codes: string[];
  is_blocking: boolean;
}

export interface PortfolioContextActionabilityPreviewRead {
  review_actionability_status: ReviewActionabilityStatus;
  overall_review_mode: ReviewReadinessMode;
  display_label: string;
  is_blocking: boolean;
}

/* ── Top-level shapes ──────────────────────────────────────────────────── */

export interface PortfolioContextRead {
  context_reference: string;
  context_label: string;
  source_kind: PortfolioContextSourceKind;
  portfolio_shape: PortfolioContextShapeRead;
  cash_state: PortfolioCashState;
  cash_state_label: string;
  broker_snapshot_freshness: PortfolioContextFreshnessRead;
  market_quote_freshness: PortfolioContextFreshnessRead | null;
  market_data_unavailable: boolean;
  actionability_preview: PortfolioContextActionabilityPreviewRead;
  available_flows: SupportedTradeReviewFlow[];
  caveat_codes: string[];
}

export interface PortfolioContextListRead {
  data_mode: Phase20BDataMode;
  demo_notice: string | null;
  items: PortfolioContextRead[];
}

export interface PortfolioContextDetailRead {
  data_mode: Phase20BDataMode;
  demo_notice: string | null;
  context: PortfolioContextRead;
}
