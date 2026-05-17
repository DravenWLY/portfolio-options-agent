import { useContext } from "react";
import { UIPreferenceContext, type UIPreferenceContextValue } from "./uiPreferenceContextDef";

export function useUIPreference(): UIPreferenceContextValue {
  const ctx = useContext(UIPreferenceContext);
  if (ctx === null) {
    throw new Error("useUIPreference must be used within <UIPreferenceProvider>");
  }
  return ctx;
}
