/**
 * TypeScript types mirroring backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/.
 *
 * All UUIDs are strings (JSON serialization). Dates are ISO 8601 strings.
 */
import type { ReportScopeMetadataRead } from "./tradeReview";

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

/* ── Phase 29A saved Agent Team report (read side) ──────────────────────────
 * Mirrors backend `SavedAgentTeamSummaryRead` / `SavedAgentTeamRoleSummaryRead`
 * attached to a saved review artifact. The frontend renders ONLY these
 * sanitized, backend-owned fields: display labels, status codes, evidence
 * `section_key`s (keys only, never values), provider-neutral warning codes, and
 * pre-sanitized narrative markdown. It never derives report scope/status from
 * the current account selector, Account Details, route, or cached state. */
export type SavedReviewAgentRunStatus =
  | "completed"
  | "partially_completed"
  | "failed";

export type AgentTeamReportStatus =
  | "source_snapshot"
  | "deterministic_draft"
  | "full_agent_report"
  | "agent_unavailable"
  | "validation_failed";

export type AgentTeamReportRunCompleteness = "full" | "partial" | "none";

export type AgentTeamReportRoleStatus =
  | "completed"
  | "unavailable"
  | "skipped"
  | "gated"
  | "validation_failed";

export type AgentTeamReportSynthesisAuthor =
  | "portfolio_manager_agent"
  | "deterministic_template";

export interface SavedAgentTeamRoleSummaryRead {
  role_name: string;
  display_name: string;
  role_status: AgentTeamReportRoleStatus;
  /** Provider-neutral status label (e.g. ok, skipped, provider_unavailable). */
  provider_status: string;
  /** Pre-sanitized narrative; null unless the role completed. */
  summary_markdown: string | null;
  /** Evidence `section_key`s cited — keys only, never values. */
  evidence_references: string[];
  warning_codes: string[];
  /** Sanitized code/label, never a raw provider error or trace. */
  unavailable_reason: string | null;
}

export interface SavedAgentTeamSummaryRead {
  run_status: SavedReviewAgentRunStatus;
  provider_mode: string;
  /** When the Agent Team run executed (ISO 8601). Null for source snapshots and
   *  legacy artifacts. Distinct from the source snapshot's saved time. */
  report_generated_at: string | null;
  role_summaries: SavedAgentTeamRoleSummaryRead[];
  warning_codes: string[];
  report_status: AgentTeamReportStatus | null;
  final_synthesis_markdown: string | null;
  final_synthesis_authored_by: AgentTeamReportSynthesisAuthor | null;
  evidence_schema_version: string | null;
  evidence_references: string[];
}

/* ── Phase 29C-T4A saved public-evidence attribution (read side) ─────────────
 * Mirrors backend `ReportPublicEvidenceAttributionRead`. A sanitized, keys-only
 * projection of the frozen `public_company_profile` saved section: it carries
 * only provider-neutral source identity, availability, and a SIC-presence flag —
 * never the literal SIC value, CIK, fiscal-year-end, company name, ticker,
 * exchange, facts, URLs, or payloads. It is the ONLY field the frontend may use
 * to decide whether SEC EDGAR attribution chrome renders (P29C-T4); the source
 * must never be inferred from role prose, evidence_references, the section key,
 * the report title, or any other fallback. Null when no reviewed EDGAR
 * company-profile evidence is attached. */
export interface ReportPublicEvidenceAttributionRead {
  section_key: "public_company_profile";
  source_key: "sec_edgar_submissions";
  source_label: "SEC EDGAR metadata - company profile only";
  availability: "available" | "limited";
  has_sic_label: boolean;
}

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
  scope_metadata: ReportScopeMetadataRead | null;
  /** Phase 29A: saved Agent Team analysis, or null for a deterministic-only
   *  source snapshot that has not had a report generated yet. */
  agent_summary: SavedAgentTeamSummaryRead | null;
  /** Phase 29C-T4A: sanitized SEC EDGAR company-profile attribution, or null. */
  public_evidence_attribution: ReportPublicEvidenceAttributionRead | null;
}

export interface ReportMessageRead {
  id: string;
  thread_id: string;
  sender_type: string;
  message_type: string;
  content_markdown: string | null;
  content_json: Record<string, unknown> | null;
  sequence: number;
  visibility: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface ReportThreadDetailRead extends ReportThreadRead {
  messages: ReportMessageRead[];
}

/* ── Phase 28A saved review artifact (save-from-trade-review) ────────────────
 * Mirrors backend `SavedReviewArtifactCreateRequest` / `SavedReviewArtifactRead`.
 * The frontend sends ONLY `source_kind`, `source_reference`, `title`, and
 * `report_type`. It never sends scope_metadata, deterministic_summary,
 * agent_summary, Account Details, selector state, cached frontend state, or any
 * account/provider/broker/holdings/position/balance data — the backend builds
 * the immutable artifact from the server-owned reviewed source row. */
export type SavedReviewSourceKind = "trade_review_workspace" | "agent_team_run";

export interface SavedReviewArtifactCreateRequest {
  source_kind: SavedReviewSourceKind;
  source_reference: string;
  title: string;
  report_type?: string;
}

export type SavedReviewArtifactStatus = "saved" | "unavailable";

export interface SavedReviewReportMetadataRead {
  report_reference: string;
  title: string;
  report_type: string;
  status: string;
  created_at: string;
  updated_at: string;
}

/** Read side of a saved snapshot. The optional scope/summary snapshot bodies the
 *  backend also returns are intentionally omitted here — the save action renders
 *  only the saved/quiet confirmation, never the saved scope or summary, which
 *  the Reports surfaces own. */
export interface SavedReviewArtifactRead {
  artifact_reference: string;
  status: SavedReviewArtifactStatus;
  report: SavedReviewReportMetadataRead;
  generated_at: string;
  saved_at: string;
  review_pipeline_label: string;
  limitations: string[];
  caveat_codes: string[];
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

/* ── Deterministic risk review (P13) ─────────────────────────────────────── */
/* Mirrors backend/app/schemas/risk.py exactly. Pydantic serializes Decimal as
   a JSON string, so `Decimal | str | None` → `string | null` and
   `Decimal | str | int | None` → `string | number | null`. The backend Read
   schema deliberately omits account_id and other broker/private keys — do not
   reintroduce them client-side. */

export type RiskSeverity = "info" | "warning" | "violation" | "blocker";

export type SnapshotKind = "stock_quote" | "option_quote" | "option_chain";

export type SnapshotPurpose =
  | "current_chain_cache"
  | "selected_candidate_snapshot"
  | "report_input_snapshot";

export interface RiskRuleViolationRead {
  code: string;
  severity: RiskSeverity;
  message: string;
  source: string;
  metric: string | null;
  actual: string | null;
  threshold: string | null;
}

export interface RiskReportSectionRead {
  title: string;
  facts: Record<string, string | number | null>;
}

export interface MarketDataSnapshotReferenceRead {
  snapshot_id: string;
  kind: SnapshotKind;
  purpose: SnapshotPurpose;
  provider: string;
  stable_key: string;
  captured_at: string;
  quote_time: string | null;
  freshness_scope: "market_quote";
  data_mode: string;
  freshness_status: string;
  actionability_status: string;
}

export interface RiskReportInputSnapshotRead {
  report_input_snapshot_id: string;
  quote_references: MarketDataSnapshotReferenceRead[];
  chain_references: MarketDataSnapshotReferenceRead[];
  captured_at: string;
  uses_current_quotes: boolean;
}

export interface DeterministicRiskReportRead {
  generated_at: string;
  calculation_version: string;
  sections: RiskReportSectionRead[];
  risk_rule_violations: RiskRuleViolationRead[];
  highest_severity: RiskSeverity | null;
  has_blocker: boolean;
  input_snapshot: RiskReportInputSnapshotRead | null;
  markdown: string;
}
