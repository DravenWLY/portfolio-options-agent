import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  UIPreferenceContext,
  APPEARANCE_STORAGE_KEY,
  SIDEBAR_STORAGE_KEY,
  type AppearanceMode,
  type ResolvedTheme,
} from "./uiPreferenceContextDef";

/**
 * UIPreferenceProvider — holds non-sensitive UI preferences only:
 * appearance mode (system/light/dark) and sidebar collapsed state.
 *
 * Context definition lives in ./uiPreferenceContextDef.ts.
 * Hook lives in ./useUIPreference.ts.
 * Splitting the three satisfies react-refresh/only-export-components:
 * this file exports only a React component.
 *
 * Persistence: localStorage stores ONLY the UI preference values. No account,
 * broker, credential, token, or report data is ever written here.
 */

const DARK_QUERY = "(prefers-color-scheme: dark)";

function safeGet(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSet(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* private mode / storage disabled — preference simply won't persist */
  }
}

function readStoredAppearance(): AppearanceMode {
  const raw = safeGet(APPEARANCE_STORAGE_KEY);
  return raw === "light" || raw === "dark" || raw === "system" ? raw : "system";
}

function systemPrefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia(DARK_QUERY).matches;
}

export function UIPreferenceProvider({ children }: { children: ReactNode }) {
  const [appearance, setAppearanceState] = useState<AppearanceMode>(readStoredAppearance);
  const [systemDark, setSystemDark] = useState<boolean>(systemPrefersDark);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(
    () => safeGet(SIDEBAR_STORAGE_KEY) === "true",
  );

  // Track the OS preference so "System Default" stays live without a reload.
  useEffect(() => {
    const mql = window.matchMedia(DARK_QUERY);
    const onChange = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  const resolvedTheme: ResolvedTheme =
    appearance === "system" ? (systemDark ? "dark" : "light") : appearance;

  // Apply the resolved theme to <html>. The pre-render bootstrap in main.tsx
  // sets the initial value, so this only keeps it in sync (no flash).
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", resolvedTheme);
  }, [resolvedTheme]);

  const setAppearance = useCallback((mode: AppearanceMode) => {
    setAppearanceState(mode);
    safeSet(APPEARANCE_STORAGE_KEY, mode);
  }, []);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      safeSet(SIDEBAR_STORAGE_KEY, String(next));
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ appearance, setAppearance, resolvedTheme, sidebarCollapsed, toggleSidebar }),
    [appearance, setAppearance, resolvedTheme, sidebarCollapsed, toggleSidebar],
  );

  return (
    <UIPreferenceContext.Provider value={value}>{children}</UIPreferenceContext.Provider>
  );
}
