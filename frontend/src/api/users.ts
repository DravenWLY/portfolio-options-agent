import { apiClient } from "./client";
import { type UserRead } from "../types/api";

/** GET /users — list all users (local MVP, no auth). */
export function listUsers(): Promise<UserRead[]> {
  return apiClient.get<UserRead[]>("/users");
}
