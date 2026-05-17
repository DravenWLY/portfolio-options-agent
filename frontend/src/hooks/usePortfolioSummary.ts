import { useEffect, useState } from "react";
import { getPortfolioSummary } from "../api/portfolio";
import { type PortfolioSummaryRead } from "../types/api";

type Status = "idle" | "loading" | "success" | "error";

export interface UsePortfolioSummaryResult {
  summary: PortfolioSummaryRead | null;
  status: Status;
  error: string | null;
  reload: () => void;
}

export function usePortfolioSummary(
  accountId: string | null
): UsePortfolioSummaryResult {
  const [summary, setSummary] = useState<PortfolioSummaryRead | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [rev, setRev] = useState(0);

  useEffect(() => {
    if (accountId === null) {
      setSummary(null);
      setStatus("idle");
      setError(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setError(null);

    getPortfolioSummary(accountId)
      .then((data) => {
        if (!cancelled) {
          setSummary(data);
          setStatus("success");
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load portfolio summary"
          );
          setStatus("error");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [accountId, rev]);

  return { summary, status, error, reload: () => setRev((r) => r + 1) };
}
