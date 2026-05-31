/**
 * TypeScript mirror of backend economic calendar read schemas (P24A-T5
 * frontend consumption of the Codex B-reviewed Phase 24A contract).
 *
 * Mirrors:
 *   backend/app/schemas/economic_calendar.py
 *     EconomicCalendarEventRead, EconomicCalendarEventListRead,
 *     EconomicCalendarRefreshStatusRead
 *
 * Strictly mirror the backend. The frontend never invents fields, never
 * classifies importance, never parses/compares actual/forecast/previous
 * values, never shows quotes/prices/volume, and never performs financial
 * calculations. Economic awareness only — not a trading signal.
 */

/* ── Enum literals ─────────────────────────────────────────────────────── */

export type EconomicCalendarDataMode =
  | "synthetic"
  | "replay"
  | "provider_reference"
  | "unavailable";

export type EconomicEventImportance = "high" | "medium" | "low" | "unknown";

export type EconomicEventImportanceSource =
  | "provider"
  | "app_classified"
  | "unavailable";

export type EconomicEventType =
  | "economic_release"
  | "central_bank"
  | "holiday"
  | "speech"
  | "other";

export type EconomicCalendarRefreshStatus = "refreshed" | "failed";

/* ── Event item ────────────────────────────────────────────────────────── */

export interface EconomicCalendarEventRead {
  event_reference: string;
  /** Backend-owned UTC instant (ISO 8601) or null when the time is unknown. */
  event_datetime_utc: string | null;
  /** Backend-owned occurrence flag; null when the timestamp is unknown. */
  event_has_occurred: boolean | null;
  event_date_label: string;
  event_time_label: string;
  event_title: string;
  event_type: EconomicEventType;
  importance: EconomicEventImportance;
  importance_source: EconomicEventImportanceSource;
  country: string;
  currency: string;
  /** Backend display label; render verbatim, never parse or compare. */
  actual_label: string | null;
  /** Backend display label; render verbatim, never parse or compare. */
  forecast_label: string | null;
  /** Backend display label; render verbatim, never parse or compare. */
  previous_label: string | null;
  unit_label: string | null;
  source_label: string;
  freshness_label: string;
  is_trading_signal: boolean;
  data_mode: EconomicCalendarDataMode;
}

/* ── Event list wrapper ────────────────────────────────────────────────── */

export interface EconomicCalendarEventListRead {
  data_mode: EconomicCalendarDataMode;
  source_label: string;
  as_of_label: string;
  freshness_label: string;
  /** ISO date (YYYY-MM-DD) from backend. */
  window_start: string;
  /** ISO date (YYYY-MM-DD) from backend. */
  window_end: string;
  timezone: string;
  importance_source: EconomicEventImportanceSource;
  items: EconomicCalendarEventRead[];
  demo_notice: string | null;
  is_trading_signal: boolean;
  limitations: string[];
}

/* ── Refresh wrapper ──────────────────────────────────────────────────── */

export interface EconomicCalendarRefreshStatusRead {
  status: EconomicCalendarRefreshStatus;
  data_mode: EconomicCalendarDataMode;
  source_label: string;
  as_of_label: string;
  imported_at: string | null;
  record_count: number;
  message: string;
}
