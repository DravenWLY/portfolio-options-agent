import { apiClient } from "./client";
import { type ReportThreadRead } from "../types/api";

/** GET /users/{userId}/reports */
export function listReportThreads(userId: string): Promise<ReportThreadRead[]> {
  return apiClient.get<ReportThreadRead[]>(`/users/${userId}/reports`);
}
