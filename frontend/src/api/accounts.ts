import { apiClient } from "./client";
import { type AccountRead } from "../types/api";

/** GET /users/{userId}/accounts — list accounts for a user. */
export function listUserAccounts(userId: string): Promise<AccountRead[]> {
  return apiClient.get<AccountRead[]>(`/users/${userId}/accounts`);
}
