import { createContext } from "react";
import { type UserRead, type AccountRead } from "../types/api";

export interface AccountContextValue {
  selectedUser: UserRead | null;
  selectedAccount: AccountRead | null;
  setSelectedUser: (user: UserRead | null) => void;
  setSelectedAccount: (account: AccountRead | null) => void;
}

export const AccountContext = createContext<AccountContextValue | null>(null);
