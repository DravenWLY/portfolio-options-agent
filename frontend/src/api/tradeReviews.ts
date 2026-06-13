/**
 * Trade-review workspace API.
 *
 * Routes through the existing /api Vite proxy to the FastAPI backend route
 * `POST /trade-reviews/preview`. The endpoint is synthetic/stateless: no DB,
 * no broker sync, no market-data provider, no TradingAgents, no LLMs, no
 * broker actions. It returns a sanitized read contract that the UI displays
 * verbatim. No frontend financial computation.
 */
import { apiClient } from "./client";
import type {
  TradeReviewWorkspacePreviewRequest,
  TradeReviewPortfolioPreviewRequest,
  TradeReviewWorkspaceRead,
} from "../types/tradeReview";

export const tradeReviewsApi = {
  /**
   * Synthetic/manual preview — Phase 18A/18B fallback. Kept as a secondary
   * dev-safe mode; never confuse with a portfolio-backed review.
   */
  preview: (body: TradeReviewWorkspacePreviewRequest) =>
    apiClient.post<TradeReviewWorkspaceRead>("/trade-reviews/preview", body),
  /**
   * Phase 18C portfolio-backed review. The backend owns the portfolio context
   * and freshness; the frontend never sends broker/market freshness, provider
   * status, cash, holdings, or thresholds. Context selection is opaque.
   *
   * Phase 27C: pass the selected app `userId` so the backend can resolve a
   * selected `review_account_selection` against that user's accounts (the
   * route reads the existing `X-User-Id` header). The header carries only the
   * app's own user id — never a broker/provider id, balance, or holding.
   */
  portfolioPreview: (body: TradeReviewPortfolioPreviewRequest, userId?: string | null) =>
    apiClient.post<TradeReviewWorkspaceRead>(
      "/trade-reviews/portfolio-preview",
      body,
      userId ? { "X-User-Id": userId } : undefined,
    ),
};
