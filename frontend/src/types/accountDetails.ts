/**
 * TypeScript mirror of backend Account Details read schemas (P27A-T1).
 *
 * Mirrors:
 *   backend/app/schemas/trade_review_workspace.py
 *     ReviewAccountRead, PortfolioScopeRead,
 *     AccountDetailAccountRead, AccountDetailsRead
 *
 * Strictly mirror the backend. The frontend never invents fields, never
 * performs financial computation, and renders backend display labels verbatim.
 * No raw holdings, raw quantities, raw balances, account IDs, provider IDs, or
 * provider payloads are present in this contract. Selected-account display
 * rows are backend-formatted labels only.
 */
import type { DashboardPrivacyDisplayMode } from "./dashboard";
import type { PortfolioContextShapeRead, PortfolioContextFreshnessRead } from "./portfolioContext";
import type { PortfolioCashState, PortfolioContextSelectionMode } from "./tradeReview";

/* ── Enum literals ─────────────────────────────────────────────────────── */

export type PortfolioScopeMode =
  | "all_connected_accounts"
  | "single_account"
  | "selected_account_group"
  | "selected_context"
  | "unavailable";

export type AccountDetailsDataMode = "synthetic_demo" | "private_real_source" | "unavailable";

export type AccountDetailSourceKind = "snaptrade" | "manual" | "csv" | "synthetic_demo" | "unknown";

export type AccountScopeRole = "review_account" | "included_in_scope" | "excluded_from_scope";

export type AccountDetailsReadinessCaveatSeverity = "info" | "warning" | "blocking";

export interface AccountDetailsReadinessCaveatRead {
  code: string;
  severity: AccountDetailsReadinessCaveatSeverity;
  title: string;
  message: string;
}

/* ── Scope / review account ────────────────────────────────────────────── */

export interface ReviewAccountRead {
  account_reference: string;
  display_label: string;
  account_kind_label: string | null;
  is_review_account: boolean;
  is_included_in_portfolio_scope: boolean;
  is_account_level_feasibility_source: boolean;
}

export interface PortfolioScopeRead {
  scope_reference: string;
  scope_mode: PortfolioScopeMode;
  display_label: string;
  selection_mode: PortfolioContextSelectionMode | null;
  context_reference: string | null;
  included_account_labels: string[];
  excluded_account_labels: string[];
  account_level_feasibility_evaluated: boolean;
  account_level_feasibility_label: string;
  caveat_codes: string[];
}

/* ── Per-account detail ────────────────────────────────────────────────── */

export interface AccountDetailAccountRead {
  account_reference: string;
  display_label: string;
  account_kind_label: string;
  source_kind: AccountDetailSourceKind;
  source_label: string;
  connection_status_label: string;
  last_successful_sync_label: string | null;
  privacy_display_mode: DashboardPrivacyDisplayMode;
  broker_snapshot_freshness: PortfolioContextFreshnessRead;
  market_quote_freshness: PortfolioContextFreshnessRead | null;
  portfolio_shape: PortfolioContextShapeRead;
  cash_state: PortfolioCashState;
  cash_state_label: string;
  total_value_label: string | null;
  cash_label: string | null;
  stock_etf_exposure_label: string | null;
  options_exposure_label: string | null;
  collateral_usage_label: string | null;
  scope_roles: AccountScopeRole[];
  account_level_feasibility_evaluated: boolean;
  readiness_caveats: AccountDetailsReadinessCaveatRead[];
  caveat_codes: string[];
}

/* ── Phase 32A review-account selector candidates ──────────────────────────
 * Mirrors backend `ReviewAccountCandidateRead` / `ReviewAccountCandidateListRead`
 * (P32A-T2). This is the *safe* selector contract for Trade Review's
 * review-account picker: backend-owned display labels plus freshness/shape
 * summaries only. It deliberately omits raw account IDs, provider IDs,
 * balances, cash values, buying power, positions, quantities, lots, and raw
 * payloads — those never reach the selector. The frontend submits only the
 * opaque `account_reference` and renders the labels verbatim. */
export interface ReviewAccountCandidateRead {
  account_reference: string;
  display_label: string;
  account_kind_label: string;
  source_kind: AccountDetailSourceKind;
  source_label: string;
  connection_status_label: string;
  last_successful_sync_label: string | null;
  broker_snapshot_freshness: PortfolioContextFreshnessRead;
  market_quote_freshness: PortfolioContextFreshnessRead | null;
  portfolio_shape: PortfolioContextShapeRead;
  cash_state_label: string;
  account_level_feasibility_evaluated: boolean;
  account_level_feasibility_label: string;
  caveat_codes: string[];
}

export interface ReviewAccountCandidateListRead {
  data_mode: AccountDetailsDataMode;
  /** ISO 8601 datetime string from backend. */
  generated_at: string;
  candidates: ReviewAccountCandidateRead[];
  caveat_codes: string[];
}

/* ── Top-level read ────────────────────────────────────────────────────── */

export interface AccountDetailsRead {
  data_mode: AccountDetailsDataMode;
  demo_notice: string | null;
  /** ISO 8601 datetime string from backend. */
  generated_at: string;
  details_reference: string;
  source_label: string;
  privacy_display_mode: DashboardPrivacyDisplayMode;
  portfolio_scope: PortfolioScopeRead;
  review_account: ReviewAccountRead | null;
  accounts: AccountDetailAccountRead[];
  readiness_caveats: AccountDetailsReadinessCaveatRead[];
  caveat_codes: string[];
}

/* ── Selected-account private detail ───────────────────────────────────── */

export interface SelectedAccountSummaryLabelsRead {
  total_value_label: string | null;
  cash_label: string | null;
  cash_state_label: string;
  stock_etf_exposure_label: string | null;
  options_exposure_label: string | null;
  collateral_usage_label: string | null;
}

export interface AccountCashDisplayRowRead {
  row_reference: string;
  currency_label: string;
  cash_amount_label: string;
  available_cash_label: string | null;
  buying_power_label: string | null;
  balance_source_label: string | null;
  cash_state_label: string;
  freshness_label: string;
  as_of_label: string | null;
  caveat_codes: string[];
}

export interface AccountTaxLotPaginationRead {
  total_count: number;
  displayed_count: number;
  has_more: boolean;
}

export interface AccountTaxLotDisplayRowRead {
  lot_reference: string;
  acquired_date_label: string | null;
  term_label: "short" | "long" | "unknown";
  quantity_label: string | null;
  purchase_price_label: string | null;
  /**
   * Brokerage-style per-share or per-contract average cost label
   * (P27B-T20). For options this is the per-contract premium (e.g. "$2.79"),
   * distinct from `cost_basis_label` which is the total cost (e.g. "$279.33").
   */
  average_cost_label: string | null;
  cost_basis_label: string | null;
  current_value_label: string | null;
  total_gain_loss_label: string | null;
  gain_loss_percent_label: string | null;
  source_label: string;
}

export interface AccountEquityPositionDisplayRowRead {
  row_reference: string;
  symbol_label: string;
  instrument_name_label: string | null;
  asset_class_label: string;
  quantity_label: string;
  last_price_label: string | null;
  market_value_label: string | null;
  average_cost_label: string | null;
  cost_basis_label: string | null;
  total_gain_loss_label: string | null;
  gain_loss_percent_label: string | null;
  valuation_source_label: string | null;
  tax_lot_rows: AccountTaxLotDisplayRowRead[];
  tax_lot_pagination: AccountTaxLotPaginationRead | null;
  freshness_label: string;
  as_of_label: string | null;
  caveat_codes: string[];
}

export interface AccountOptionPositionDisplayRowRead {
  row_reference: string;
  underlying_symbol_label: string;
  contract_label: string;
  option_type_label: string;
  strike_label: string;
  expiration_label: string;
  side_label: string;
  quantity_label: string;
  last_price_label: string | null;
  market_value_label: string | null;
  average_cost_label: string | null;
  cost_basis_label: string | null;
  total_gain_loss_label: string | null;
  gain_loss_percent_label: string | null;
  multiplier_label: string | null;
  valuation_source_label: string | null;
  /** Brokerage-style purchase-history lots when broker supplies them (P27B-T20). */
  tax_lot_rows: AccountTaxLotDisplayRowRead[];
  tax_lot_pagination: AccountTaxLotPaginationRead | null;
  freshness_label: string;
  as_of_label: string | null;
  caveat_codes: string[];
}

/* ── Selected-account sync ─────────────────────────────────────────────── */

export type AccountDetailsSyncStatus =
  | "succeeded"
  | "partially_succeeded"
  | "failed"
  | "running";

export interface AccountDetailsSyncRead {
  account_reference: string;
  status: AccountDetailsSyncStatus;
  message: string;
  /** ISO 8601 datetime string from backend. */
  generated_at: string;
  /** ISO 8601 datetime string from backend, or null. */
  started_at: string | null;
  /** ISO 8601 datetime string from backend, or null. */
  completed_at: string | null;
}

export interface SelectedAccountDetailsRead {
  data_mode: "private_real_source" | "unavailable";
  /** ISO 8601 datetime string from backend. */
  generated_at: string;
  account_reference: string;
  display_label: string;
  account_kind_label: string;
  source_kind: AccountDetailSourceKind;
  source_label: string;
  connection_status_label: string;
  last_successful_sync_label: string | null;
  privacy_display_mode: DashboardPrivacyDisplayMode;
  broker_snapshot_freshness: PortfolioContextFreshnessRead;
  market_quote_freshness: PortfolioContextFreshnessRead | null;
  summary_labels: SelectedAccountSummaryLabelsRead;
  cash_rows: AccountCashDisplayRowRead[];
  equity_position_rows: AccountEquityPositionDisplayRowRead[];
  option_position_rows: AccountOptionPositionDisplayRowRead[];
  caveat_codes: string[];
  limitations: string[];
}
