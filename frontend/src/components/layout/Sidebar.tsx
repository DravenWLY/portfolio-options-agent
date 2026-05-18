import { NavLink } from "react-router-dom";
import { useUIPreference } from "../../context/useUIPreference";

/**
 * Sidebar navigation. Collapsible to a compact icon rail.
 *
 * Safety: no trade-execution, market screener, or TradingAgents links.
 * The "manual decision support / no trades" framing stays visible in both
 * states — full text when expanded, a labelled compact badge when collapsed.
 */
export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIPreference();

  return (
    <nav
      id="primary-sidebar"
      style={{
        ...styles.sidebar,
        width: sidebarCollapsed
          ? "var(--sidebar-width-collapsed)"
          : "var(--sidebar-width)",
      }}
      aria-label="Main navigation"
    >
      <div style={styles.top}>
        <button
          type="button"
          onClick={toggleSidebar}
          aria-pressed={sidebarCollapsed}
          aria-controls="primary-sidebar"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          style={{
            ...styles.toggle,
            justifyContent: sidebarCollapsed ? "center" : "flex-end",
          }}
        >
          <span aria-hidden="true">{sidebarCollapsed ? "»" : "«"}</span>
        </button>

        <ul style={styles.navList} role="list">
          <NavItem label="Dashboard" icon="⬡" to="/" collapsed={sidebarCollapsed} end />
          <NavItem label="Broker" icon="⊛" to="/broker" collapsed={sidebarCollapsed} />
          <NavItem label="Market Data" icon="◷" to="/market-data" collapsed={sidebarCollapsed} />
          <NavItem label="Risk Review" icon="◭" to="/risk" collapsed={sidebarCollapsed} />
          <NavItem label="Reports" icon="⊙" to="#reports" collapsed={sidebarCollapsed} />
        </ul>
      </div>

      <div style={styles.footer}>
        {sidebarCollapsed ? (
          <span
            style={styles.footerBadge}
            role="note"
            aria-label="Manual decision support only. No trades are placed."
            title="Manual decision support only. No trades are placed."
          >
            RO
          </span>
        ) : (
          <span style={styles.footerNote} role="note">
            Manual decision support only.
            <br />
            No trades are placed.
          </span>
        )}
      </div>
    </nav>
  );
}

function NavItem({
  label,
  icon,
  to,
  collapsed,
  end,
}: {
  label: string;
  icon: string;
  to: string;
  collapsed: boolean;
  end?: boolean;
}) {
  return (
    <li>
      <NavLink
        to={to}
        end={end}
        aria-label={collapsed ? label : undefined}
        title={collapsed ? label : undefined}
        style={({ isActive }) => ({
          ...styles.navLink,
          justifyContent: collapsed ? "center" : "flex-start",
          ...(isActive ? styles.navLinkActive : {}),
        })}
      >
        <span style={styles.navIcon} aria-hidden="true">
          {icon}
        </span>
        {!collapsed && <span style={styles.navLabel}>{label}</span>}
      </NavLink>
    </li>
  );
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    position: "fixed",
    top: "var(--topbar-height)",
    left: 0,
    bottom: 0,
    backgroundColor: "var(--color-surface)",
    borderRight: "1px solid var(--color-border)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    paddingBlock: "var(--space-4)",
    overflowX: "hidden",
    overflowY: "auto",
    transition: "width 160ms ease",
  },
  top: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
  },
  toggle: {
    display: "flex",
    alignItems: "center",
    marginInline: "var(--space-3)",
    padding: "var(--space-1) var(--space-2)",
    height: "28px",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "transparent",
    color: "var(--color-text-secondary)",
    cursor: "pointer",
    fontSize: "var(--font-size-base)",
    lineHeight: 1,
  },
  navList: {
    listStyle: "none",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
    paddingInline: "var(--space-3)",
  },
  navLink: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
    padding: "var(--space-2) var(--space-3)",
    borderRadius: "var(--radius-sm)",
    color: "var(--color-text-secondary)",
    fontSize: "var(--font-size-sm)",
    letterSpacing: "0.02em",
    textDecoration: "none",
    whiteSpace: "nowrap",
    overflow: "hidden",
    transition: "background-color 120ms, color 120ms",
  },
  navLinkActive: {
    backgroundColor: "var(--color-surface-2)",
    color: "var(--color-text-primary)",
  },
  navIcon: {
    width: "16px",
    flexShrink: 0,
    textAlign: "center",
    color: "var(--color-text-muted)",
    fontSize: "var(--font-size-base)",
  },
  navLabel: {
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  footer: {
    paddingInline: "var(--space-4)",
    display: "flex",
    justifyContent: "flex-start",
  },
  footerNote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    lineHeight: 1.5,
    display: "block",
  },
  footerBadge: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.06em",
    color: "var(--color-text-secondary)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    padding: "2px 6px",
    margin: "0 auto",
  },
};
