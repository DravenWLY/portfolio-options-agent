import { useEffect, useState } from "react";
import { listUserAccounts } from "../api/accounts";
import { type AccountRead } from "../types/api";

type Status = "idle" | "loading" | "success" | "error";

export interface UseAccountsResult {
  accounts: AccountRead[];
  status: Status;
  error: string | null;
}

export function useAccounts(userId: string | null): UseAccountsResult {
  const [accounts, setAccounts] = useState<AccountRead[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (userId === null) {
      setAccounts([]);
      setStatus("idle");
      setError(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setError(null);

    listUserAccounts(userId)
      .then((data) => {
        if (!cancelled) {
          setAccounts(data);
          setStatus("success");
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load accounts"
          );
          setStatus("error");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [userId]);

  return { accounts, status, error };
}
