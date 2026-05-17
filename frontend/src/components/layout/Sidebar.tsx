import { NavLink } from "react-router-dom";

/**
 * Sidebar navigation.
 *
 * Safety: no trade-execution, market screener, or TradingAgents links.
 * Uses react-router-dom NavLink for active-route highlighting.
 */
export default function Sidebar() {
  return (
    <nav style={styles.sidebar} aria-label="Main navigation">
      <ul style={styles.navList} role="list">
        <NavItem label="Dashboard" icon="⬡" to="/" end />
        <NavItem label="Broker" icon="⊛" to="/broker" />
        <NavItem label="Reports" icon="⊙" to="#reports" />
      </ul>

      <div style={styles.footer}>
        <span style={styles.footerNote}>
          Manual decision support only.
          <br />
          No trades are placed.
        </span>
      </div>
    </nav>
  );
}

function NavItem({
  label,
  icon,
  to,
  end,
}: {
  label: string;
  icon: string;
  to: string;
  end?: boolean;
}) {
  return (
    <li>
      <NavLink
        to={to}
        end={end}
        style={({ isActive }) => ({
          ...styles.navLink,
          ...(isActive ? styles.navLinkActive : {}),
        })}
      >
        <span style={styles.navIcon} aria-hidden="true">{icon}</span>
        <span>{label}</span>
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
    width: "var(--sidebar-width)",
    backgroundColor: "var(--color-surface)",
    borderRight: "1px solid var(--color-border)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    paddingBlock: "var(--space-6)",
    overflowY: "auto",
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
    transition: "background-color 120ms, color 120ms",
  },
  navLinkActive: {
    backgroundColor: "var(--color-surface-2)",
    color: "var(--color-text-primary)",
  },
  navIcon: {
    width: "16px",
    textAlign: "center",
    color: "var(--color-text-muted)",
    fontSize: "var(--font-size-base)",
  },
  footer: {
    paddingInline: "var(--space-6)",
  },
  footerNote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    lineHeight: 1.5,
    display: "block",
  },
};
