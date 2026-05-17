import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles/globals.css";
import App from "./App";

/**
 * Pre-render theme bootstrap — set <html data-theme> before first paint so
 * there is no light/dark flash. Reads only the non-sensitive UI preference.
 */
(function applyInitialTheme() {
  try {
    const stored = window.localStorage.getItem("poa-appearance");
    const mode = stored === "light" || stored === "dark" ? stored : "system";
    const resolved =
      mode === "system"
        ? window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : mode;
    document.documentElement.setAttribute("data-theme", resolved);
  } catch {
    document.documentElement.setAttribute("data-theme", "dark");
  }
})();

const rootEl = document.getElementById("root");
if (!rootEl) throw new Error("Root element #root not found in index.html");

createRoot(rootEl).render(
  <StrictMode>
    <App />
  </StrictMode>
);
