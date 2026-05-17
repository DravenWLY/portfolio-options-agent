/**
 * Broker sync API calls.
 *
 * All calls route through /api → Vite proxy → FastAPI backend.
 * The frontend never calls SnapTrade or broker APIs directly.
 * No credentials or secrets are stored or transmitted from the frontend.
 */
import { apiClient } from "./client";
import type {
  SnapTradeUserRegistrationRead,
  SnapTradeConnectionPortalRead,
  BrokerConnectionPublicRead,
  BrokerAccountPublicRead,
  BrokerSyncRunPublicRead,
  BrokerSyncFreshnessRead,
} from "../types/api";

export const brokerSyncApi = {
  registerSnapTradeUser: (userId: string) =>
    apiClient.post<SnapTradeUserRegistrationRead>(
      `/users/${userId}/broker-sync/snaptrade/register`
    ),

  createConnectionPortal: (userId: string) =>
    apiClient.post<SnapTradeConnectionPortalRead>(
      `/users/${userId}/broker-sync/snaptrade/connection-portal`
    ),

  refreshConnections: (userId: string) =>
    apiClient.post<BrokerSyncRunPublicRead>(
      `/users/${userId}/broker-sync/snaptrade/refresh-connections`
    ),

  listBrokerConnections: (userId: string) =>
    apiClient.get<BrokerConnectionPublicRead[]>(
      `/users/${userId}/broker-connections`
    ),

  listBrokerAccountsForConnection: (userId: string, connectionId: string) =>
    apiClient.get<BrokerAccountPublicRead[]>(
      `/users/${userId}/broker-connections/${connectionId}/accounts`
    ),

  syncBrokerAccount: (userId: string, brokerAccountId: string) =>
    apiClient.post<BrokerSyncRunPublicRead>(
      `/users/${userId}/broker-accounts/${brokerAccountId}/sync`,
      { trigger: "manual" }
    ),

  getBrokerSyncRun: (userId: string, syncRunId: string) =>
    apiClient.get<BrokerSyncRunPublicRead>(
      `/users/${userId}/broker-sync-runs/${syncRunId}`
    ),

  getBrokerAccountFreshness: (userId: string, brokerAccountId: string) =>
    apiClient.get<BrokerSyncFreshnessRead>(
      `/users/${userId}/broker-accounts/${brokerAccountId}/freshness`
    ),
};
