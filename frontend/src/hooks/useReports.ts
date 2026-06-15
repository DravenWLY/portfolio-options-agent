import { useCallback, useEffect, useState } from "react";
import { listReportThreads } from "../api/reports";
import { type ReportThreadRead } from "../types/api";

type Status = "idle" | "loading" | "success" | "error";

export interface UseReportsResult {
  threads: ReportThreadRead[];
  status: Status;
  error: string | null;
  /** Re-fetch the saved report list from the backend (e.g. after generating an
   *  Agent Team report). Saved reports are always read from the backend, never
   *  reconstructed from current frontend state. */
  refetch: () => void;
}

export function useReports(userId: string | null): UseReportsResult {
  const [threads, setThreads] = useState<ReportThreadRead[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const refetch = useCallback(() => setReloadKey((value) => value + 1), []);

  useEffect(() => {
    if (userId === null) {
      setThreads([]);
      setStatus("idle");
      setError(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setError(null);

    listReportThreads(userId)
      .then((data) => {
        if (!cancelled) {
          setThreads(data);
          setStatus("success");
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load reports");
          setStatus("error");
        }
      });

    return () => { cancelled = true; };
  }, [userId, reloadKey]);

  return { threads, status, error, refetch };
}
