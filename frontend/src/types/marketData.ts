/**
 * TypeScript types mirroring backend market-data schemas.
 * Keep in sync with backend/app/schemas/market_data.py and
 * backend/app/services/market_data/models.py.
 *
 * Phase 12 is manual/mock only. No real market-data provider is connected.
 * Market-quote freshness (freshness_scope="market_quote") is intentionally
 * separate from broker portfolio sync freshness.
 */

export type DataMode =
  | "live"
  | "delayed"
  | "indicative"
  | "cached"
  | "eod"
  | "manual"
  | "unknown";

export type FreshnessStatus =
  | "fresh"
  | "delayed"
  | "stale"
  | "eod_only"
  | "manual"
  | "unknown"
  | "error";

export type ActionabilityStatus =
  | "actionable_snapshot"
  | "analysis_only"
  | "manual_review_required"
  | "blocked_stale_quote"
  | "blocked_unknown_quote"
  | "blocked_provider_error";

export interface ProviderCapabilitiesRead {
  provider: string;
  supports_stock_quotes: boolean;
  supports_intraday_bars: boolean;
  supports_option_expirations: boolean;
  supports_option_chain: boolean;
  supports_option_snapshots: boolean;
  supports_iv: boolean;
  supports_greeks: boolean;
  supports_streaming: boolean;
  supports_historical_options: boolean;
  supported_data_modes: DataMode[];
  notes: string[];
}

export interface MarketDataProviderStatusRead {
  provider: string;
  freshness_scope: "market_quote";
  data_mode: DataMode;
  freshness_status: FreshnessStatus;
  actionability_status: ActionabilityStatus;
  checked_at: string;
  capabilities: ProviderCapabilitiesRead;
  message: string | null;
}
