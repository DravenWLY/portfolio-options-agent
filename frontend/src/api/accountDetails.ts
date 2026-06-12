/**
 * Account Details API — P27A-T2 / P27B-T19 frontend consumption.
 *
 * Approved endpoints (read-only plus opaque selected-account sync):
 *   GET  /users/{uid}/account-details
 *   GET  /users/{uid}/account-details/{account_reference}
 *   POST /users/{uid}/account-details/{account_reference}/sync
 *
 * Read-only private account context plus an opaque selected-account sync
 * bridge (P27B-T18). The sync route accepts only opaque `acctref_...`
 * references and returns a sanitized sync status. No broker management,
 * no disconnect/delete, no provider/SnapTrade calls from the frontend, no
 * credential handling. The backend owns every display label.
 */
import { apiClient } from "./client";
import type {
  AccountDetailsRead,
  AccountDetailsSyncRead,
  SelectedAccountDetailsRead,
} from "../types/accountDetails";

export const accountDetailsApi = {
  /** Get the private Account Details snapshot for a user. */
  get: (userId: string) =>
    apiClient.get<AccountDetailsRead>(`/users/${userId}/account-details`),
  /** Get private display rows for one selected account reference. */
  getSelected: (userId: string, accountReference: string) =>
    apiClient.get<SelectedAccountDetailsRead>(
      `/users/${userId}/account-details/${encodeURIComponent(accountReference)}`,
    ),
  /**
   * Refresh a single selected account via its opaque Account Details
   * reference. Returns a sanitized sync status (succeeded, partially
   * succeeded, failed). A 409 conflict (running) is surfaced as an
   * ApiRequestError(409) and should be treated as an in-progress sync.
   */
  sync: (userId: string, accountReference: string) =>
    apiClient.post<AccountDetailsSyncRead>(
      `/users/${userId}/account-details/${encodeURIComponent(accountReference)}/sync`,
    ),
};
