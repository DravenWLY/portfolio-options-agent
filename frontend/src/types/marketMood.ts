/**
 * TypeScript mirror of backend Market Mood read schemas (Phase 26A).
 *
 * Mirrors:
 *   backend/app/schemas/market_mood.py
 *     MarketMoodTrendPointRead, MarketMoodComparisonRead,
 *     MarketMoodComponentRead, MarketMoodIndicatorHistoryPointRead,
 *     MarketMoodIndicatorRead, MarketMoodRead, MarketMoodDetailRead,
 *     MarketMoodRefreshStatusRead
 *
 * Strictly mirror the backend. The frontend never invents fields, never parses
 * or computes financial/trading meaning, and renders backend display labels
 * verbatim. Market Mood is broad sentiment context only — not a trading signal,
 * not an actionability input, not a risk-rule input.
 */

/* ── Enum literals ─────────────────────────────────────────────────────── */

export type MarketMoodDataMode = "synthetic" | "provider_reference" | "unavailable";

export type MarketMoodFreshnessStatus = "fresh" | "stale" | "unavailable";

export type MarketMoodRating =
  | "extreme_fear"
  | "fear"
  | "neutral"
  | "greed"
  | "extreme_greed"
  | "unknown";

export type MarketMoodComparisonWindow = "1w" | "1m" | "1y";

export type MarketMoodRefreshStatus = "refreshed" | "unchanged" | "failed";

export type MarketMoodAxisValueFormat =
  | "number"
  | "percent"
  | "ratio"
  | "index"
  | "currency"
  | "spread"
  | "unknown";

export type MarketMoodValueMeaning = "fear" | "greed" | "neutral_or_contextual" | "unknown";

/* ── Nested reads ──────────────────────────────────────────────────────── */

export interface MarketMoodTrendPointRead {
  date: string;
  score: number | null;
  score_label: string | null;
  rating: MarketMoodRating;
  rating_label: string;
}

export interface MarketMoodComparisonRead {
  window: MarketMoodComparisonWindow;
  prior_score: number | null;
  prior_score_label: string | null;
  change_label: string | null;
  is_available: boolean;
}

export interface MarketMoodComponentRead {
  component_key: string;
  display_name: string;
  score: number | null;
  score_label: string | null;
  rating: MarketMoodRating;
  rating_label: string;
}

/* ── Detail reads (per-indicator history) ──────────────────────────────── */

export interface MarketMoodIndicatorHistoryPointRead {
  date: string;
  /** Raw indicator value (provider/native scale); presentational only. */
  value: number | null;
  /** Backend-formatted display label for the raw value; render verbatim. */
  value_label: string | null;
  /** Normalized 0–100 sub-score for this point (secondary context). */
  score: number | null;
  score_label: string | null;
  rating: MarketMoodRating;
  rating_label: string;
}

export interface MarketMoodIndicatorRead {
  component_key: string;
  display_name: string;
  subtitle: string;
  description: string;
  current_score: number | null;
  current_score_label: string | null;
  current_rating: MarketMoodRating;
  current_rating_label: string;
  current_value: number | null;
  current_value_label: string | null;
  unit_label: string | null;
  axis_label: string | null;
  axis_value_format: MarketMoodAxisValueFormat;
  higher_value_meaning: MarketMoodValueMeaning;
  lower_value_meaning: MarketMoodValueMeaning;
  history: MarketMoodIndicatorHistoryPointRead[];
}

/* ── Top-level read ────────────────────────────────────────────────────── */

export interface MarketMoodRead {
  data_mode: MarketMoodDataMode;
  source_label: string;
  source_detail_label: string;
  source_rights_notice: string;
  /** ISO 8601 datetime string from backend. */
  generated_at: string;
  /** ISO 8601 datetime string from backend, or null when unknown. */
  updated_at_utc: string | null;
  updated_at_label: string | null;
  freshness_status: MarketMoodFreshnessStatus;
  freshness_label: string;
  is_trading_signal: boolean;
  is_actionability_input: boolean;
  is_risk_rule_input: boolean;
  score: number | null;
  score_label: string | null;
  score_min: number;
  score_max: number;
  rating: MarketMoodRating;
  rating_label: string;
  trend_series: MarketMoodTrendPointRead[];
  comparisons: MarketMoodComparisonRead[];
  components: MarketMoodComponentRead[];
  caveat_codes: string[];
  limitations: string[];
  status_message: string | null;
}

/* ── Detail read (overall + 7 indicators with raw-scale history) ───────── */

export interface MarketMoodDetailRead {
  data_mode: MarketMoodDataMode;
  source_label: string;
  source_detail_label: string;
  source_rights_notice: string;
  generated_at: string;
  updated_at_utc: string | null;
  updated_at_label: string | null;
  freshness_status: MarketMoodFreshnessStatus;
  freshness_label: string;
  is_trading_signal: boolean;
  is_actionability_input: boolean;
  is_risk_rule_input: boolean;
  score: number | null;
  score_label: string | null;
  score_min: number;
  score_max: number;
  rating: MarketMoodRating;
  rating_label: string;
  trend_series: MarketMoodTrendPointRead[];
  comparisons: MarketMoodComparisonRead[];
  indicators: MarketMoodIndicatorRead[];
  caveat_codes: string[];
  limitations: string[];
  status_message: string | null;
}

/* ── Refresh status (manual/backend-only; not consumed by the dashboard card) ─ */

export interface MarketMoodRefreshStatusRead {
  status: MarketMoodRefreshStatus;
  data_mode: MarketMoodDataMode;
  source_label: string;
  generated_at: string | null;
  updated_at_utc: string | null;
  source_changed: boolean | null;
  last_checked_at_utc: string | null;
  last_checked_at_label: string | null;
  record_count: number;
  message: string;
}
