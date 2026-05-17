import { apiClient } from "./client";
import {
  type PortfolioSummaryRead,
  type CashBalanceRead,
  type StockPositionRead,
  type OptionPositionRead,
} from "../types/api";

/** GET /accounts/{accountId}/portfolio */
export function getPortfolioSummary(
  accountId: string
): Promise<PortfolioSummaryRead> {
  return apiClient.get<PortfolioSummaryRead>(`/accounts/${accountId}/portfolio`);
}

/** GET /accounts/{accountId}/cash-balances/latest */
export function getLatestCashBalance(
  accountId: string
): Promise<CashBalanceRead> {
  return apiClient.get<CashBalanceRead>(
    `/accounts/${accountId}/cash-balances/latest`
  );
}

/** GET /accounts/{accountId}/stock-positions */
export function listStockPositions(
  accountId: string
): Promise<StockPositionRead[]> {
  return apiClient.get<StockPositionRead[]>(
    `/accounts/${accountId}/stock-positions`
  );
}

/** GET /accounts/{accountId}/option-positions */
export function listOptionPositions(
  accountId: string
): Promise<OptionPositionRead[]> {
  return apiClient.get<OptionPositionRead[]>(
    `/accounts/${accountId}/option-positions`
  );
}
