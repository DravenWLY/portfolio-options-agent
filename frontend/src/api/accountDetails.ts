/**
 * Account Details API — P27A-T2 / P27B-T19 / P32A-T3 frontend consumption.
 *
 * Approved endpoints (read-only, opaque selected-account sync, safe
 * review-account selector, and user-owned nickname update):
 *   GET   /users/{uid}/account-details
 *   GET   /users/{uid}/account-details/{account_reference}
 *   POST  /users/{uid}/account-details/{account_reference}/sync
 *   GET   /users/{uid}/review-account-candidates
 *   PATCH /users/{uid}/account-details/{account_reference}/nickname
 *
 * Read-only private account context plus an opaque selected-account sync
 * bridge (P27B-T18), a safe review-account candidate list, and a user-owned
 * display-nickname update (P32A-T3). Every route accepts only opaque
 * `acctref_...` references and returns sanitized, backend-owned display
 * labels. No broker management, no disconnect/delete, no provider/SnapTrade
 * calls from the frontend, no credential handling. The frontend never sends
 * or requests raw account IDs, provider IDs, balances, buying power,
 * positions, lots, or raw payloads.
 */
import { apiClient } from "./client";
import type {
  AccountDetailsRead,
  AccountDetailsSyncRead,
  ReviewAccountCandidateListRead,
  ReviewAccountCandidateRead,
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
  /**
   * P32A-T3: list safe review-account candidates for Trade Review's
   * review-account selector. Returns backend-owned display labels plus
   * freshness/shape summaries only — never raw account IDs, balances,
   * positions, lots, or provider payloads.
   */
  listReviewAccountCandidates: (userId: string) =>
    apiClient.get<ReviewAccountCandidateListRead>(
      `/users/${userId}/review-account-candidates`,
    ),
  /**
   * P32A-T3: set or clear a user-owned display nickname for one opaque
   * account reference. Passing `null` (or a blank string) clears it. The
   * backend validates and normalizes the nickname and returns the updated
   * candidate. The frontend sends only the opaque `acctref_...` and the
   * nickname text — no provider data is touched.
   */
  updateNickname: (
    userId: string,
    accountReference: string,
    nickname: string | null,
  ) =>
    apiClient.patch<ReviewAccountCandidateRead>(
      `/users/${userId}/account-details/${encodeURIComponent(accountReference)}/nickname`,
      { nickname },
    ),
};
