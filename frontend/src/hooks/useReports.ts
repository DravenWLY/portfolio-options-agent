import { useEffect, useState } from "react";
import { listReportThreads } from "../api/reports";
import { type ReportThreadRead } from "../types/api";

type Status = "idle" | "loading" | "success" | "error";

export interface UseReportsResult {
  threads: ReportThreadRead[];
  status: Status;
  error: string | null;
}

export function useReports(userId: string | null): UseReportsResult {
  const [threads, setThreads] = useState<ReportThreadRead[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

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
  }, [userId]);

  return { threads, status, error };
}
