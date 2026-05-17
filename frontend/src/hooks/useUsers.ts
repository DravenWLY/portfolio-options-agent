import { useEffect, useState } from "react";
import { listUsers } from "../api/users";
import { type UserRead } from "../types/api";

type Status = "loading" | "success" | "error";

export interface UseUsersResult {
  users: UserRead[];
  status: Status;
  error: string | null;
  reload: () => void;
}

export function useUsers(): UseUsersResult {
  const [users, setUsers] = useState<UserRead[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string | null>(null);
  const [rev, setRev] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    setError(null);

    listUsers()
      .then((data) => {
        if (!cancelled) {
          setUsers(data);
          setStatus("success");
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load users");
          setStatus("error");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [rev]);

  return { users, status, error, reload: () => setRev((r) => r + 1) };
}
