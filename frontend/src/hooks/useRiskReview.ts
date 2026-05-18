import { useEffect, useState, useCallback } from "react";
import type { DeterministicRiskReportRead } from "../types/api";
import { fetchRiskReportStub, type RiskReviewScenario } from "../api/riskReview";

type Status = "loading" | "success" | "empty" | "error";

interface UseRiskReview {
  status: Status;
  report: DeterministicRiskReportRead | null;
  error: string | null;
  reload: () => void;
}

/**
 * Read-only hook over the stubbed risk-report source. No network, no storage.
 * `scenario` lets the page exercise loading/empty/error/stale states until a
 * real backend route exists.
 */
export function useRiskReview(scenario: RiskReviewScenario): UseRiskReview {
  const [status, setStatus] = useState<Status>("loading");
  const [report, setReport] = useState<DeterministicRiskReportRead | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setStatus("loading");
    setError(null);
    fetchRiskReportStub(scenario)
      .then((result) => {
        if (cancelled) return;
        if (result === null) {
          setReport(null);
          setStatus("empty");
          return;
        }
        setReport(result);
        setStatus("success");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load risk report");
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [scenario]);

  useEffect(() => load(), [load]);

  return { status, report, error, reload: load };
}
