import { type ReactNode } from "react";
import TopBar from "./TopBar";
import Sidebar from "./Sidebar";

interface AppShellProps {
  children: ReactNode;
  /** Passed through to TopBar — wired in P11-T2. */
  accountSlot?: ReactNode;
}

/**
 * AppShell — the fixed chrome wrapper for the entire dashboard.
 *
 * Layout:
 *   TopBar  (fixed, full-width, z-index 100)
 *   Sidebar (fixed, left, below topbar)
 *   Main    (scrollable, offset by sidebar and topbar)
 */
export default function AppShell({ children, accountSlot }: AppShellProps) {
  return (
    <>
      <TopBar accountSlot={accountSlot} />
      <Sidebar />
      <main style={styles.main} id="main-content">
        {children}
      </main>
    </>
  );
}

const styles: Record<string, React.CSSProperties> = {
  main: {
    marginTop: "var(--topbar-height)",
    marginLeft: "var(--sidebar-width)",
    minHeight: "calc(100vh - var(--topbar-height))",
    padding: "var(--space-8)",
    overflowY: "auto",
  },
};
