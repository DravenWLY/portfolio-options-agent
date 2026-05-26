/**
 * Dashboard API — P20C-T1 read contracts.
 *
 * Approved endpoints (GET-only, read-only):
 *   GET /users/{uid}/trade-reviews
 *   GET /users/{uid}/risk-alerts
 *   GET /users/{uid}/readiness
 *   GET /users/{uid}/dashboard-account-summary
 *
 * Portfolio contexts use the existing portfolioContext.ts client.
 *
 * All responses are currently synthetic_demo and carry a demo_notice.
 * No broker actions, no credential handling, no order placement.
 */
import { apiClient } from "./client";
import type {
  TradeReviewListRead,
  RiskAlertListRead,
  ReviewReadinessRead,
  DashboardAccountSummaryRead,
} from "../types/dashboard";

export const dashboardApi = {
  /** List recent trade reviews for a user. */
  tradeReviews: (userId: string) =>
    apiClient.get<TradeReviewListRead>(
      `/users/${userId}/trade-reviews`,
    ),

  /** List risk alerts for a user. */
  riskAlerts: (userId: string) =>
    apiClient.get<RiskAlertListRead>(
      `/users/${userId}/risk-alerts`,
    ),

  /** Get review readiness for a user. */
  readiness: (userId: string) =>
    apiClient.get<ReviewReadinessRead>(
      `/users/${userId}/readiness`,
    ),

  /** Get dashboard account summary for a user. */
  accountSummary: (userId: string) =>
    apiClient.get<DashboardAccountSummaryRead>(
      `/users/${userId}/dashboard-account-summary`,
    ),
};
