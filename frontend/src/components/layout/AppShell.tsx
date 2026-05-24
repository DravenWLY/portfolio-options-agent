import { type ReactNode } from "react";
import TopBar from "./TopBar";
import Sidebar from "./Sidebar";
import { useUIPreference } from "../../context/useUIPreference";

interface AppShellProps {
  children: ReactNode;
  /** Passed through to TopBar — wired in P11-T2. */
  accountSlot?: ReactNode;
}

/**
 * AppShell — P20A-T2 prototype topology.
 *
 * Translated from `app.tsx` in
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/
 *
 * Layout shape (matching the prototype's `.shell`):
 *
 *   <div class="shell" grid-cols="sidebar | 1fr">
 *     <Sidebar/>                  ← full viewport height; owns its own brand header
 *     <div class="main-col">
 *       <TopBar/>                 ← lives INSIDE the right column
 *       <main>{children}</main>
 *     </div>
 *   </div>
 *
 * The old fixed-topbar topology has been replaced. Pages no longer need to
 * offset their content by `var(--topbar-height)`.
 */
export default function AppShell({ children, accountSlot }: AppShellProps) {
  const { sidebarCollapsed } = useUIPreference();
  const sidebarWidth = sidebarCollapsed
    ? "var(--sidebar-width-collapsed)"
    : "var(--sidebar-width)";

  return (
    <div className="mp-surface" style={{ ...styles.shell, gridTemplateColumns: `${sidebarWidth} 1fr` }}>
      <Sidebar />
      <div style={styles.mainCol}>
        <TopBar accountSlot={accountSlot} />
        <main style={styles.main} id="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  shell: {
    display: "grid",
    minHeight: "100vh",
    width: "100%",
    backgroundColor: "var(--mp-paper)",
    color: "var(--mp-ink)",
    transition: "grid-template-columns 160ms ease",
  },
  mainCol: {
    display: "flex",
    flexDirection: "column",
    minWidth: 0,
    minHeight: "100vh",
  },
  main: {
    flex: 1,
    padding: "var(--space-8)",
    overflowY: "auto",
    minWidth: 0,
  },
};
