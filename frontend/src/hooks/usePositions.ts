import { useEffect, useState } from "react";
import {
  getLatestCashBalance,
  listStockPositions,
  listOptionPositions,
} from "../api/portfolio";
import {
  type CashBalanceRead,
  type StockPositionRead,
  type OptionPositionRead,
} from "../types/api";

type Status = "idle" | "loading" | "success" | "error";

function useResource<T>(
  fetcher: (accountId: string) => Promise<T>,
  accountId: string | null
) {
  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [rev, setRev] = useState(0);

  useEffect(() => {
    if (accountId === null) {
      setData(null);
      setStatus("idle");
      setError(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setError(null);

    fetcher(accountId)
      .then((d) => {
        if (!cancelled) { setData(d); setStatus("success"); }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Request failed");
          setStatus("error");
        }
      });

    return () => { cancelled = true; };
  }, [accountId, rev]); // eslint-disable-line react-hooks/exhaustive-deps

  return { data, status, error, reload: () => setRev((r) => r + 1) };
}

export function useCashBalance(accountId: string | null) {
  return useResource<CashBalanceRead>(getLatestCashBalance, accountId);
}

export function useStockPositions(accountId: string | null) {
  return useResource<StockPositionRead[]>(listStockPositions, accountId);
}

export function useOptionPositions(accountId: string | null) {
  return useResource<OptionPositionRead[]>(listOptionPositions, accountId);
}
