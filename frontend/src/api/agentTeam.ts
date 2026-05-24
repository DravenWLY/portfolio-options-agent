/**
 * Agent-team analysis console API (Phase 19A).
 *
 * Single network path: POST /agent-team/trade-review-analysis/preview via the
 * existing `/api` Vite proxy. The backend route is stateless and uses the
 * mock LLM provider by default; no real LLM/broker/market call leaves the
 * server. The frontend stores nothing in browser storage.
 */
import { apiClient } from "./client";
import type {
  AgentTeamAnalysisPreviewRequest,
  AgentTeamAnalysisConsoleRead,
} from "../types/agentTeam";

export const agentTeamApi = {
  previewTradeReviewAnalysis: (body: AgentTeamAnalysisPreviewRequest) =>
    apiClient.post<AgentTeamAnalysisConsoleRead>(
      "/agent-team/trade-review-analysis/preview",
      body,
    ),
};
