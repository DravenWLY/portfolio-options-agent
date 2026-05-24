import { NavLink } from "react-router-dom";
import { useUIPreference } from "../../context/useUIPreference";
import AppearanceControl from "./AppearanceControl";
import { Badge } from "../shared/mp";

/**
 * Sidebar — P20A Modern Portfolio Desk styling.
 *
 * Translated (not pasted) from the `Sidebar` block in
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/app.tsx
 *
 * Layout intent (matching the prototype):
 *  - Expanded mode: BrandMark + stacked wordmark ("Portfolio" / "Copilot" in
 *    accent), with a small inline collapse chevron at the right edge that
 *    does not dominate the brand area.
 *  - Collapsed mode: the BrandMark itself is the click-to-expand affordance.
 *    There is no separate arrow control.
 *
 * Safety: no trade-execution, market screener, or TradingAgents links.
 * The Private-alpha / read-only / analysis-only / no-order-placement copy
 * remains visible in both expanded and collapsed states (via the footer).
 */

// P20A-T4: marketing placeholder pages (Landing / Pricing / Sign-in/up) are
// now available, so the Marketing nav group is visible. The pages themselves
// are static; the workspace routes remain ungated.
const SHOW_MARKETING_GROUP = true as boolean;

interface NavEntry { label: string; icon: string; to: string; end?: boolean }
interface NavGroup { label: string; items: NavEntry[] }

const WORKSPACE_NAV: NavGroup = {
  label: "Workspace",
  items: [
    { label: "Dashboard", icon: "▦", to: "/", end: true },
    { label: "Trade Review", icon: "☑", to: "/trade-review" },
    { label: "Agent Team", icon: "⇶", to: "/agent-team-analysis" },
    { label: "Reports", icon: "▤", to: "/reports" },
    { label: "Portfolio Context", icon: "◈", to: "/portfolio-context" },
    { label: "Settings", icon: "⚙", to: "/settings" },
  ],
};

const DATA_NAV: NavGroup = {
  label: "Data sources",
  items: [
    { label: "Broker", icon: "⊞", to: "/broker" },
    { label: "Market Data", icon: "◷", to: "/market-data" },
    { label: "Risk Review", icon: "⚠", to: "/risk" },
  ],
};

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIPreference();

  return (
    <nav
      id="primary-sidebar"
      className="mp-surface"
      style={styles.sidebar}
      aria-label="Main navigation"
    >
      {sidebarCollapsed ? (
        // Collapsed: the BrandMark is the only top affordance, and it is the
        // expand button. No arrow control.
        <header style={styles.brandHeadCollapsed}>
          <button
            type="button"
            onClick={toggleSidebar}
            aria-controls="primary-sidebar"
            aria-label="Expand sidebar"
            title="Expand sidebar"
            style={styles.brandButton}
          >
            <BrandMark size={22} />
          </button>
        </header>
      ) : (
        // Expanded: brand mark + stacked wordmark + small inline collapse chevron.
        <header style={styles.brandHead}>
          <BrandMark size={22} />
          <div style={styles.brandStack}>
            <span className="mp-display" style={styles.brandLine1}>Portfolio</span>
            <span className="mp-display" style={styles.brandLine2}>Copilot</span>
          </div>
          <button
            type="button"
            onClick={toggleSidebar}
            aria-controls="primary-sidebar"
            aria-label="Collapse sidebar"
            title="Collapse sidebar"
            style={styles.collapseChevron}
          >
            <span aria-hidden="true">‹</span>
          </button>
        </header>
      )}

      <div style={styles.scroll}>
        <NavGroupBlock group={WORKSPACE_NAV} collapsed={sidebarCollapsed} />
        <NavGroupBlock group={DATA_NAV} collapsed={sidebarCollapsed} />
        {SHOW_MARKETING_GROUP && (
          <NavGroupBlock
            collapsed={sidebarCollapsed}
            group={{
              label: "Marketing",
              items: [
                { label: "Landing", icon: "⌂", to: "/landing" },
                { label: "Pricing", icon: "¤", to: "/pricing" },
                { label: "Sign in", icon: "⍟", to: "/auth" },
              ],
            }}
          />
        )}
      </div>

      <footer style={styles.footer}>
        {!sidebarCollapsed && <div style={styles.footerEyebrow}>Appearance</div>}
        <AppearanceControl />
        {sidebarCollapsed ? (
          <span
            style={styles.footerBadgeMini}
            role="note"
            aria-label="Private alpha. Read-only. Analysis-only. No order placement."
            title="Private alpha · read-only · analysis-only · no order placement"
          >α</span>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <Badge tone="info" dot>Private alpha</Badge>
            <span style={styles.footerNote} role="note">
              Read-only · analysis-only · no order placement
            </span>
          </div>
        )}
      </footer>
    </nav>
  );
}

function NavGroupBlock({ group, collapsed }: { group: NavGroup; collapsed: boolean }) {
  return (
    <div style={styles.group}>
      <div style={collapsed ? styles.groupRule : styles.groupHead}>
        {!collapsed && <span style={styles.groupLabel}>{group.label}</span>}
      </div>
      <ul style={styles.navList} role="list">
        {group.items.map((item) => (
          <NavItem key={item.to} {...item} collapsed={collapsed} />
        ))}
      </ul>
    </div>
  );
}

function NavItem({ label, icon, to, collapsed, end }: NavEntry & { collapsed: boolean }) {
  return (
    <li>
      <NavLink
        to={to}
        end={end}
        aria-label={collapsed ? label : undefined}
        title={collapsed ? label : undefined}
        className={({ isActive }) => isActive ? "mp-nav-active" : "mp-nav-idle"}
        style={({ isActive }) => ({
          ...styles.navLink,
          justifyContent: collapsed ? "center" : "flex-start",
          ...(isActive ? styles.navLinkActive : styles.navLinkIdle),
        })}
      >
        <span style={styles.navIcon} aria-hidden="true">{icon}</span>
        {!collapsed && <span style={styles.navLabel}>{label}</span>}
      </NavLink>
    </li>
  );
}

function BrandMark({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={{ color: "var(--mp-accent)", flexShrink: 0 }} aria-hidden="true">
      <rect x="0.5" y="0.5" width="23" height="23" rx="3" fill="none" stroke="currentColor" strokeWidth="1.2" />
      <path d="M5 16L9 10L13 13L19 6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="9" cy="10" r="1.2" fill="currentColor" />
      <circle cx="13" cy="13" r="1.2" fill="currentColor" />
      <circle cx="19" cy="6" r="1.2" fill="currentColor" />
    </svg>
  );
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    position: "sticky",
    top: 0,
    height: "100vh",
    backgroundColor: "var(--mp-card)",
    borderRight: "1px solid var(--mp-rule)",
    color: "var(--mp-ink-2)",
    display: "flex",
    flexDirection: "column",
    paddingBlock: "var(--space-4)",
    overflowX: "hidden",
    transition: "width 160ms ease",
  },
  brandHead: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    paddingInline: "var(--space-5)",
    paddingBottom: "var(--space-3)",
    borderBottom: "1px solid var(--mp-rule)",
  },
  brandHeadCollapsed: {
    display: "flex",
    justifyContent: "center",
    paddingBottom: "var(--space-3)",
    borderBottom: "1px solid var(--mp-rule)",
  },
  brandButton: {
    width: 36,
    height: 36,
    border: "none",
    background: "transparent",
    color: "var(--mp-accent)",
    borderRadius: "var(--radius-sm)",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 0,
    transition: "background-color 120ms ease",
  },
  brandStack: {
    display: "flex",
    flexDirection: "column",
    flex: 1,
    minWidth: 0,
    lineHeight: 1.05,
  },
  brandLine1: {
    fontSize: 15,
    fontWeight: 500,
    color: "var(--mp-ink)",
    letterSpacing: "-0.01em",
    lineHeight: 1,
  },
  brandLine2: {
    fontSize: 15,
    fontWeight: 500,
    color: "var(--mp-accent)",
    letterSpacing: "-0.01em",
    lineHeight: 1.2,
  },
  collapseChevron: {
    width: 24, height: 24, borderRadius: "var(--radius-sm)",
    display: "flex", alignItems: "center", justifyContent: "center",
    color: "var(--mp-mute)", border: "none", background: "transparent",
    cursor: "pointer", fontSize: 14, lineHeight: 1, fontWeight: 600,
  },
  scroll: { flex: 1, overflowY: "auto", paddingTop: "var(--space-3)", display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  group: { display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  groupHead: { paddingInline: "var(--space-4)", paddingTop: "var(--space-2)" },
  groupRule: { height: 1, backgroundColor: "var(--mp-rule)", margin: "var(--space-2) var(--space-3)" },
  groupLabel: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.10em", fontWeight: 600,
  },
  navList: { listStyle: "none", display: "flex", flexDirection: "column", gap: 2, paddingInline: "var(--space-3)", margin: 0 },
  navLink: {
    display: "flex", alignItems: "center", gap: "var(--space-3)",
    padding: "var(--space-2) var(--space-3)",
    borderRadius: "var(--radius-sm)",
    fontSize: "var(--font-size-sm)", letterSpacing: "0.01em",
    textDecoration: "none", whiteSpace: "nowrap", overflow: "hidden",
    border: "1px solid transparent",
    transition: "background-color 120ms, color 120ms, border-color 120ms",
  },
  navLinkIdle: {
    color: "var(--mp-ink-2)",
    backgroundColor: "transparent",
    borderColor: "transparent",
  },
  navLinkActive: {
    backgroundColor: "var(--mp-card-2, var(--mp-accent-soft))",
    color: "var(--mp-ink)",
    borderColor: "var(--mp-rule)",
  },
  navIcon: { width: 16, flexShrink: 0, textAlign: "center", color: "var(--mp-accent)", fontSize: "var(--font-size-base)" },
  navLabel: { overflow: "hidden", textOverflow: "ellipsis" },
  footer: {
    paddingInline: "var(--space-4)", paddingTop: "var(--space-3)",
    borderTop: "1px solid var(--mp-rule)",
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  footerEyebrow: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.10em", fontWeight: 600,
  },
  footerNote: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.5 },
  footerBadgeMini: {
    fontSize: "var(--font-size-xs)", fontWeight: 700, letterSpacing: "0.06em",
    color: "var(--mp-accent)",
    border: "1px solid var(--mp-accent-line)",
    borderRadius: "var(--radius-sm)",
    padding: "2px 6px", margin: "0 auto",
    backgroundColor: "var(--mp-accent-soft)",
  },
};
