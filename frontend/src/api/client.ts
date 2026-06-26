/**
 * Base API client.
 *
 * All requests go through /api → Vite proxy → FastAPI backend (localhost:8000).
 * The browser never calls broker APIs or market-data providers directly.
 *
 * No API keys are stored or sent from the frontend.
 */

const API_BASE = "/api";

export class ApiRequestError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string
  ) {
    super(`API ${status}: ${detail}`);
    this.name = "ApiRequestError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // Destructure headers out of init so the spread below cannot clobber the
  // merged headers object (which must always carry Content-Type: application/json
  // so the backend parses the JSON body rather than treating it as raw text).
  const { headers: initHeaders, ...restInit } = init ?? {};
  const response = await fetch(`${API_BASE}${path}`, {
    ...restInit,
    headers: {
      "Content-Type": "application/json",
      ...initHeaders,
    },
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json() as { detail?: string };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // ignore parse error — use status text
      detail = response.statusText || detail;
    }
    throw new ApiRequestError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown, headers?: Record<string, string>) =>
    request<T>(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
      headers,
    }),
  patch: <T>(path: string, body?: unknown, headers?: Record<string, string>) =>
    request<T>(path, {
      method: "PATCH",
      body: body !== undefined ? JSON.stringify(body) : undefined,
      headers,
    }),
};
