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
  TradeReviewWorkspaceRead,
} from "../types/tradeReview";

export const tradeReviewsApi = {
  preview: (body: TradeReviewWorkspacePreviewRequest) =>
    // apiClient prefixes /api; the Vite proxy strips it to /trade-reviews/preview.
    apiClient.post<TradeReviewWorkspaceRead>("/trade-reviews/preview", body),
};
