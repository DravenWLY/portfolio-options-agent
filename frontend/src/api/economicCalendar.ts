/**
 * Economic calendar API — Phase 24A frontend consumption.
 *
 * Approved endpoints:
 *   GET /economic-calendar/events
 *   POST /economic-calendar/refresh
 *
 * The frontend consumes the backend contract only. It never calls FMP, Forex
 * Factory, Trading Economics, or any external provider. Refresh asks the
 * backend to update its normalized last-good snapshot; API keys remain
 * backend-only.
 *
 * Economic awareness only. No quotes, prices, recommendations, or trading
 * signals; the backend guarantees `is_trading_signal=false`.
 */
import { apiClient } from "./client";
import type {
  EconomicCalendarEventListRead,
  EconomicCalendarRefreshStatusRead,
} from "../types/economicCalendar";

/** Optional ISO (YYYY-MM-DD) window. The backend defaults to the current day. */
export interface EconomicCalendarWindowParams {
  startDate?: string;
  endDate?: string;
}

export const economicCalendarApi = {
  /**
   * List public economic-calendar awareness events for an optional date window.
   * The backend validates the window (≤7 days, valid/ordered dates) and remains
   * the source of truth; an invalid window returns a safe 400.
   */
  events: (params?: EconomicCalendarWindowParams) => {
    const qs = new URLSearchParams();
    if (params?.startDate) qs.set("start_date", params.startDate);
    if (params?.endDate) qs.set("end_date", params.endDate);
    const query = qs.toString();
    return apiClient.get<EconomicCalendarEventListRead>(
      `/economic-calendar/events${query ? `?${query}` : ""}`,
    );
  },
  /** Refresh backend-owned last-good economic-calendar snapshot. */
  refresh: () =>
    apiClient.post<EconomicCalendarRefreshStatusRead>("/economic-calendar/refresh"),
};
