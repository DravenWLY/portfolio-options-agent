/**
 * Market Mood API — Phase 26A frontend consumption.
 *
 * Approved endpoints (read-only):
 *   GET /market-context/market-mood          (compact Dashboard card)
 *   GET /market-context/market-mood/detail   (detail page: 7 indicators + history)
 *
 * The frontend consumes the backend contract only. It never calls CNN or any
 * external provider, and it does not trigger the backend refresh in this slice
 * (refresh is manual/backend-only). Broad market sentiment context only —
 * not a trading signal; the backend guarantees is_trading_signal=false,
 * is_actionability_input=false, is_risk_rule_input=false.
 */
import { apiClient } from "./client";
import type { MarketMoodRead, MarketMoodDetailRead } from "../types/marketMood";

export const marketMoodApi = {
  /** Read the latest backend-owned Market Mood snapshot (compact). */
  get: () => apiClient.get<MarketMoodRead>("/market-context/market-mood"),
  /** Read the full Market Mood detail snapshot (overall + 7 indicators). */
  detail: () => apiClient.get<MarketMoodDetailRead>("/market-context/market-mood/detail"),
};
