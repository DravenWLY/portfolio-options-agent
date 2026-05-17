import { useState, type ReactNode } from "react";
import { AccountContext } from "./accountContextDef";
import { type UserRead, type AccountRead } from "../types/api";

/**
 * AccountContext provider — holds the locally selected user and account.
 *
 * Context definition lives in ./accountContextDef.ts.
 * Hook lives in ./useAccountContext.ts.
 * Splitting the three satisfies react-refresh/only-export-components:
 * this file exports only a React component (AccountProvider).
 *
 * Phase 11 note: local MVP selector, not production authentication.
 * No tokens, sessions, or credentials stored here.
 * localStorage is intentionally not used — selection resets on page load.
 */
export function AccountProvider({ children }: { children: ReactNode }) {
  const [selectedUser, setSelectedUser] = useState<UserRead | null>(null);
  const [selectedAccount, setSelectedAccount] = useState<AccountRead | null>(null);

  function handleSetUser(user: UserRead | null) {
    setSelectedUser(user);
    setSelectedAccount(null);
  }

  return (
    <AccountContext.Provider
      value={{
        selectedUser,
        selectedAccount,
        setSelectedUser: handleSetUser,
        setSelectedAccount,
      }}
    >
      {children}
    </AccountContext.Provider>
  );
}
