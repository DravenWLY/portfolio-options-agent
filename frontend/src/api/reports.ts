import { apiClient } from "./client";
import {
  type ReportThreadDetailRead,
  type ReportThreadRead,
  type SavedReviewArtifactCreateRequest,
  type SavedReviewArtifactRead,
} from "../types/api";

/** GET /users/{userId}/reports */
export function listReportThreads(userId: string): Promise<ReportThreadRead[]> {
  return apiClient.get<ReportThreadRead[]>(`/users/${userId}/reports`);
}

/** GET /users/{userId}/reports/{threadId} */
export function getReportThread(
  userId: string,
  threadId: string,
): Promise<ReportThreadDetailRead> {
  return apiClient.get<ReportThreadDetailRead>(
    `/users/${userId}/reports/${encodeURIComponent(threadId)}`,
  );
}

/**
 * POST /users/{userId}/reports/from-trade-review
 *
 * Saves an immutable review snapshot from a completed Trade Review. The backend
 * resolves the reviewed source from the opaque `source_reference` and builds the
 * saved artifact from the server-owned `saved_review_sources` row; the frontend
 * sends only the approved create-request fields (no scope/summary/private data).
 */
export function saveReviewSnapshotFromTradeReview(
  userId: string,
  body: SavedReviewArtifactCreateRequest,
): Promise<SavedReviewArtifactRead> {
  return apiClient.post<SavedReviewArtifactRead>(
    `/users/${userId}/reports/from-trade-review`,
    body,
  );
}

/**
 * POST /users/{userId}/reports/{threadId}/agent-team-report
 *
 * Generates an Agent Team report for an existing saved review snapshot from its
 * immutable backend-owned evidence package only. The frontend sends no body and
 * no private/account/scope data; the backend resolves ownership server-side and
 * fails closed for unknown references. After a successful call, refetch the
 * report list/detail rather than trusting this response as render state.
 */
export function generateAgentTeamReport(
  userId: string,
  threadId: string,
): Promise<SavedReviewArtifactRead> {
  return apiClient.post<SavedReviewArtifactRead>(
    `/users/${userId}/reports/${encodeURIComponent(threadId)}/agent-team-report`,
    {},
  );
}
