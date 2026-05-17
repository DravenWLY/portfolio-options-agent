import { useState, useEffect, useCallback } from "react";
import { brokerSyncApi } from "../api/brokerSync";
import type { BrokerConnectionPublicRead, BrokerAccountPublicRead } from "../types/api";

type Status = "idle" | "loading" | "success" | "error";

interface UseBrokerConnectionsResult {
  connections: BrokerConnectionPublicRead[] | null;
  accountsByConnection: Record<string, BrokerAccountPublicRead[]>;
  status: Status;
  error: string | null;
  reload: () => void;
}

export function useBrokerConnections(userId: string | null): UseBrokerConnectionsResult {
  const [connections, setConnections] = useState<BrokerConnectionPublicRead[] | null>(null);
  const [accountsByConnection, setAccountsByConnection] = useState<Record<string, BrokerAccountPublicRead[]>>({});
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!userId) {
      setConnections(null);
      setAccountsByConnection({});
      setStatus("idle");
      setError(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setError(null);

    brokerSyncApi.listBrokerConnections(userId)
      .then(async (conns) => {
        if (cancelled) return;
        setConnections(conns);

        const accountMap: Record<string, BrokerAccountPublicRead[]> = {};
        await Promise.all(
          conns.map(async (conn) => {
            try {
              const accts = await brokerSyncApi.listBrokerAccountsForConnection(userId, conn.id);
              if (!cancelled) accountMap[conn.id] = accts;
            } catch {
              if (!cancelled) accountMap[conn.id] = [];
            }
          })
        );

        if (!cancelled) {
          setAccountsByConnection(accountMap);
          setStatus("success");
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const msg = err instanceof Error ? err.message : "Failed to load broker connections";
        setError(msg);
        setStatus("error");
      });

    return () => { cancelled = true; };
  }, [userId, tick]);

  return { connections, accountsByConnection, status, error, reload };
}
