/**
 * TypeScript types mirroring backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/.
 *
 * All UUIDs are strings (JSON serialization). Dates are ISO 8601 strings.
 */

/* ── Users ─────────────────────────────────────────────────────────────── */

export interface UserRead {
  id: string;
  display_name: string;
  email: string | null;
  auth_provider: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

/* ── Accounts ───────────────────────────────────────────────────────────── */

export type AccountType =
  | "taxable_individual"
  | "roth_ira"
  | "traditional_ira"
  | "other";

export interface AccountRead {
  id: string;
  user_id: string;
  broker_name: string;
  account_type: AccountType;
  display_name: string;
  base_currency: string;
  is_manual: boolean;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

/* ── Data freshness ─────────────────────────────────────────────────────── */

/** Mirrors backend DataFreshnessStatus literal. */
export type DataFreshnessStatus =
  | "fresh"
  | "cached"
  | "delayed"
  | "stale"
  | "unknown"
  | "error"
  | "reauth_required";

/* ── Portfolio summary ──────────────────────────────────────────────────── */

export interface PortfolioWarningRead {
  code: string;
  severity: string;
  message: string;
  freshness_status: string;
  source: string;
}

export interface PortfolioSummaryRead {
  account_id: string;
  as_of: string;
  cash_as_of: string | null;
  stock_positions_as_of: string | null;
  option_positions_as_of: string | null;
  latest_snapshot_as_of: string | null;
  total_cash: string;              // Decimal serialized as string
  stock_position_count: number;
  stock_market_value: string;
  option_position_count: number;
  long_option_position_count: number;
  short_option_position_count: number;
  option_market_value: string;
  total_internal_value: string;
  data_sources: string[];
  data_freshness_statuses: string[];
  broker_data_warnings: PortfolioWarningRead[];
}

/* ── Cash balances ──────────────────────────────────────────────────────── */

export interface CashBalanceRead {
  id: string;
  account_id: string;
  total_cash: string;
  reserved_collateral_cash: string;
  free_cash: string;
  premium_income_cash: string;
  dca_cash: string;
  source: string;
  source_ref: string | null;
  data_freshness_status: DataFreshnessStatus;
  as_of: string;
  created_at: string;
}

/* ── Stock positions ────────────────────────────────────────────────────── */

export type AssetType = "stock" | "etf" | "mutual_fund" | "cash_equivalent" | "other";
export type PositionSource = "manual" | "csv" | "snaptrade";

export interface StockPositionRead {
  id: string;
  account_id: string;
  symbol: string;
  asset_type: AssetType;
  quantity: string;
  cost_basis: string | null;
  market_price: string | null;
  market_value: string | null;
  source: PositionSource;
  source_ref: string | null;
  data_freshness_status: DataFreshnessStatus;
  as_of: string;
  created_at: string;
  updated_at: string;
}

/* ── Option contracts ───────────────────────────────────────────────────── */

export type OptionType = "call" | "put";
export type OptionStyle = "american" | "european" | "unknown";

export interface OptionContractRead {
  id: string;
  occ_symbol: string;
  underlying_symbol: string;
  expiration_date: string;   // YYYY-MM-DD
  strike: string;
  option_type: OptionType;
  style: OptionStyle;
  multiplier: string;
  created_at: string;
  updated_at: string;
}

/* ── Option positions ───────────────────────────────────────────────────── */

export type PositionSide = "long" | "short";
export type OptionPositionStatus =
  | "open"
  | "closed"
  | "assigned"
  | "expired"
  | "called_away";

export interface OptionPositionRead {
  id: string;
  account_id: string;
  option_contract_id: string;
  position_side: PositionSide;
  quantity: string;
  average_price: string | null;
  market_price: string | null;
  market_value: string | null;
  status: OptionPositionStatus;
  source: PositionSource;
  source_ref: string | null;
  data_freshness_status: DataFreshnessStatus;
  as_of: string;
  opened_at: string | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

/* ── Reports ────────────────────────────────────────────────────────────── */

export type ReportThreadStatus =
  | "draft"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface ReportThreadRead {
  id: string;
  user_id: string;
  account_id: string | null;
  title: string;
  report_type: string;
  status: ReportThreadStatus;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

/* ── Generic API error shape ────────────────────────────────────────────── */

export interface ApiError {
  detail: string;
}

/* ── Broker sync ─────────────────────────────────────────────────────────── */

export interface SnapTradeUserRegistrationRead {
  provider: "snaptrade";
  credential_metadata_id: string;
}

export interface SnapTradeConnectionPortalRead {
  provider: "snaptrade";
  portal_url: string;
  expires_at: string | null;
}

export interface BrokerConnectionPublicRead {
  id: string;
  user_id: string;
  provider: string;
  broker_name: string;
  connection_status: string;
  sync_status: string;
  data_freshness_status: string;
  last_successful_sync_at: string | null;
  last_attempted_sync_at: string | null;
  consent_expires_at: string | null;
  scopes: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface BrokerAccountPublicRead {
  id: string;
  broker_connection_id: string;
  account_id: string | null;
  display_name: string;
  account_type: string;
  base_currency: string;
  sync_status: string;
  data_freshness_status: string;
  last_successful_sync_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BrokerSyncErrorRead {
  type: string;
  message: string;
}

export interface BrokerSyncPartialFailureRead {
  occ_symbol: string | null;
  reason: string;
}

export interface BrokerSyncSummaryRead {
  balance_currency: string | null;
  stock_positions_count: number | null;
  option_positions_count: number | null;
  partial_failures: BrokerSyncPartialFailureRead[];
  warnings: string[];
}

export interface BrokerSyncRunPublicRead {
  id: string;
  broker_connection_id: string;
  broker_account_id: string | null;
  trigger: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  accounts_count: number;
  positions_count: number;
  transactions_count: number;
  error: BrokerSyncErrorRead | null;
  summary: BrokerSyncSummaryRead | null;
  created_at: string;
  updated_at: string;
}

export interface BrokerSyncFreshnessRead {
  user_id: string;
  broker_connection_id: string;
  broker_account_id: string;
  account_id: string | null;
  provider: string;
  broker_name: string;
  freshness_scope: "broker_portfolio";
  connection_status: string;
  sync_status: string;
  data_freshness_status: string;
  last_successful_sync_at: string | null;
  last_attempted_sync_at: string | null;
  latest_sync_run_id: string | null;
  latest_sync_run_status: string | null;
  latest_sync_run_completed_at: string | null;
  requires_reauth: boolean;
  has_error: boolean;
}

export interface BrokerSyncConflictRead {
  sync_run_id: string;
  status: string;
}
