/**
 * Portfolio-context API — P20B-T4 read contracts.
 *
 * Approved endpoints (GET-only, read-only):
 *   GET /users/{uid}/portfolio-contexts
 *   GET /users/{uid}/portfolio-context/latest
 *   GET /users/{uid}/portfolio-context/{ctx_ref}
 *
 * All responses are currently synthetic_demo and carry a demo_notice.
 * No broker actions, no credential handling, no order placement.
 */
import { apiClient } from "./client";
import type {
  PortfolioContextListRead,
  PortfolioContextDetailRead,
} from "../types/portfolioContext";

export const portfolioContextApi = {
  /** List all portfolio contexts for a user. */
  list: (userId: string) =>
    apiClient.get<PortfolioContextListRead>(
      `/users/${userId}/portfolio-contexts`,
    ),

  /** Get the latest portfolio context detail for a user. */
  latest: (userId: string) =>
    apiClient.get<PortfolioContextDetailRead>(
      `/users/${userId}/portfolio-context/latest`,
    ),

  /** Get a specific portfolio context detail by opaque reference. */
  detail: (userId: string, ctxRef: string) =>
    apiClient.get<PortfolioContextDetailRead>(
      `/users/${userId}/portfolio-context/${ctxRef}`,
    ),
};
