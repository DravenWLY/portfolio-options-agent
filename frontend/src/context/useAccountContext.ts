import { useContext } from "react";
import { AccountContext, type AccountContextValue } from "./accountContextDef";

export function useAccountContext(): AccountContextValue {
  const ctx = useContext(AccountContext);
  if (ctx === null) {
    throw new Error("useAccountContext must be used within <AccountProvider>");
  }
  return ctx;
}
