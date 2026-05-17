import { createContext } from "react";

export type AppearanceMode = "system" | "light" | "dark";
export type ResolvedTheme = "light" | "dark";

export interface UIPreferenceContextValue {
  /** User's chosen appearance mode. "system" follows prefers-color-scheme. */
  appearance: AppearanceMode;
  setAppearance: (mode: AppearanceMode) => void;
  /** The theme actually applied to <html> after resolving "system". */
  resolvedTheme: ResolvedTheme;
  /** Sidebar collapsed (compact icon-only) vs expanded. */
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

export const UIPreferenceContext = createContext<UIPreferenceContextValue | null>(null);

/* localStorage keys — UI preference ONLY. Never account, broker, credential,
   token, or report data is persisted by this layer. */
export const APPEARANCE_STORAGE_KEY = "poa-appearance";
export const SIDEBAR_STORAGE_KEY = "poa-sidebar-collapsed";
