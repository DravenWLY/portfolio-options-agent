/**
 * Symbol lookup API — P23A-T2 frontend wrapper.
 *
 * Provider-neutral symbol search and validation through the app-owned
 * backend. The frontend never calls Nasdaq, Yahoo, Alpaca, broker APIs,
 * or market-data providers directly.
 *
 * Endpoints (GET-only, read-only):
 *   GET /symbols/search?q={query}&limit={limit}
 *   GET /symbols/validate?symbol={symbol}
 *
 * No order placement, no quotes, no prices, no volume, no recommendations.
 */
import { apiClient } from "./client";
import type { SymbolSearchRead, SymbolValidationRead } from "../types/symbols";

export const symbolsApi = {
  /**
   * Search for symbols by prefix.
   * Returns deterministic strict-prefix suggestions from the backend.
   * The frontend must not rank results as recommendations.
   */
  search: (query: string, limit = 10) =>
    apiClient.get<SymbolSearchRead>(
      `/symbols/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    ),

  /**
   * Validate an exact symbol.
   * Returns found/supported status with backend-owned display labels.
   */
  validate: (symbol: string) =>
    apiClient.get<SymbolValidationRead>(
      `/symbols/validate?symbol=${encodeURIComponent(symbol)}`,
    ),
};
