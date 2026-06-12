import { NavLink } from "react-router-dom";
import { useEffect, useState, type PointerEvent as ReactPointerEvent } from "react";
import { useUIPreference } from "../../context/useUIPreference";
import AppearanceControl from "./AppearanceControl";
import { Badge, MpIcon, type MpIconName } from "../shared/mp";

/**
 * Sidebar — P20A Modern Portfolio Desk styling.
 *
 * Translated (not pasted) from the `Sidebar` block in
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/app.tsx
 *
 * Navigation taxonomy follows the prototype direction:
 *   Product  → Landing, Pricing, Sign in (marketing pages)
 *   Workspace → Overview, Trade Review, Agent Console, Reports,
 *               Portfolio Context, Settings
 *   Data sources → Broker, Market Data, Risk Review (secondary extension,
 *               not in the prototype primary groups — kept for route access,
 *               positioned last with reduced visual weight)
 *
 * Icons: monochrome stroke-based SVGs via MpIcon. No emoji.
 *
 * Safety: no broker-action, market screener, or TradingAgents links.
 * The Private-alpha / read-only / analysis-only workspace copy
 * remains visible in both expanded and collapsed states (via the footer).
 */

const SHOW_PRODUCT_GROUP = true as boolean;
const SIDEBAR_MIN_WIDTH = 188;
const SIDEBAR_DEFAULT_WIDTH = 220;
const SIDEBAR_MAX_WIDTH = 340;

interface NavEntry { label: string; icon: MpIconName; to: string; end?: boolean; tag?: string }
interface NavGroup { label: string; items: NavEntry[]; secondary?: boolean }

const PRODUCT_NAV: NavGroup = {
  label: "Product",
  items: [
    { label: "Landing",  icon: "logo",    to: "/landing",  tag: "Marketing" },
    { label: "Pricing",  icon: "reports", to: "/pricing",  tag: "Marketing" },
    { label: "Sign in",  icon: "lock",    to: "/auth",     tag: "Marketing" },
  ],
};

const WORKSPACE_NAV: NavGroup = {
  label: "Workspace",
  items: [
    { label: "Overview",          icon: "overview",  to: "/", end: true },
    { label: "Trade Review",      icon: "review",    to: "/trade-review" },
    { label: "Agent Console",     icon: "agent",     to: "/agent-team-analysis" },
    { label: "Reports",           icon: "reports",   to: "/reports" },
    { label: "Portfolio Context", icon: "portfolio", to: "/portfolio-context" },
    { label: "Settings",          icon: "settings",  to: "/settings" },
  ],
};

const DATA_NAV: NavGroup = {
  label: "Data sources",
  secondary: true,
  items: [
    { label: "Broker",          icon: "broker",    to: "/broker" },
    { label: "Account Details", icon: "portfolio", to: "/account-details" },
    { label: "Market Data",     icon: "spark",     to: "/market-data" },
    { label: "Market Mood",     icon: "spark",     to: "/market-context/market-mood" },
    { label: "Risk Review",     icon: "alert",     to: "/risk" },
  ],
};

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIPreference();
  const [sidebarWidth, setSidebarWidth] = useState(SIDEBAR_DEFAULT_WIDTH);

  useEffect(() => {
    document.documentElement.style.setProperty("--sidebar-width", `${sidebarWidth}px`);
    return () => {
      document.documentElement.style.removeProperty("--sidebar-width");
    };
  }, [sidebarWidth]);

  const onResizePointerDown = (event: ReactPointerEvent<HTMLButtonElement>) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = sidebarWidth;

    const onMove = (moveEvent: PointerEvent) => {
      const next = Math.min(
        SIDEBAR_MAX_WIDTH,
        Math.max(SIDEBAR_MIN_WIDTH, startWidth + moveEvent.clientX - startX),
      );
      setSidebarWidth(next);
    };

    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp, { once: true });
  };

  return (
    <nav
      id="primary-sidebar"
      className="mp-surface"
      style={styles.sidebar}
      aria-label="Main navigation"
    >
      {sidebarCollapsed ? (
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
            <MpIcon name="chevron-r" size={12} style={{ transform: "rotate(180deg)" }} />
          </button>
        </header>
      )}

      <div style={styles.scroll}>
        {SHOW_PRODUCT_GROUP && (
          <NavGroupBlock group={PRODUCT_NAV} collapsed={sidebarCollapsed} />
        )}
        <NavGroupBlock group={WORKSPACE_NAV} collapsed={sidebarCollapsed} />
        <NavGroupBlock group={DATA_NAV} collapsed={sidebarCollapsed} />
      </div>

      <footer style={{ ...styles.footer, ...(sidebarCollapsed ? styles.footerCollapsed : {}) }}>
        {!sidebarCollapsed && <div style={styles.footerEyebrow}>Appearance</div>}
        <AppearanceControl compact={sidebarCollapsed} />
        {sidebarCollapsed ? (
          <span
            style={styles.footerBadgeMini}
            role="note"
            aria-label="Private alpha. Read-only. Analysis-only workspace."
            title="Private alpha · read-only · analysis-only workspace"
          >α</span>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <Badge tone="info" dot>Private alpha</Badge>
            <span style={styles.footerNote} role="note">
              Read-only · analysis-only workspace
            </span>
          </div>
        )}
      </footer>

      {!sidebarCollapsed && (
        <button
          type="button"
          aria-label="Resize sidebar"
          title="Drag to resize sidebar"
          onPointerDown={onResizePointerDown}
          style={styles.resizeHandle}
        />
      )}
    </nav>
  );
}

function NavGroupBlock({ group, collapsed }: { group: NavGroup; collapsed: boolean }) {
  return (
    <div style={styles.group}>
      <div style={collapsed ? styles.groupRule : styles.groupHead}>
        {!collapsed && (
          <span style={{
            ...styles.groupLabel,
            ...(group.secondary ? { opacity: 0.7 } : {}),
          }}>
            {group.label}
          </span>
        )}
      </div>
      <ul style={styles.navList} role="list">
        {group.items.map((item) => (
          <NavItem key={item.to} {...item} collapsed={collapsed} />
        ))}
      </ul>
    </div>
  );
}

function NavItem({ label, icon, to, collapsed, end, tag }: NavEntry & { collapsed: boolean }) {
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
          ...(collapsed ? styles.navLinkCollapsed : {}),
          ...(isActive ? styles.navLinkActive : styles.navLinkIdle),
        })}
      >
        {({ isActive }) => (
          <>
            <MpIcon
              name={icon}
              size={14}
              style={{ color: isActive ? "var(--mp-accent)" : "var(--mp-mute)" }}
            />
            {!collapsed && <span style={styles.navLabel}>{label}</span>}
            {!collapsed && tag && <span style={styles.navTag}>{tag}</span>}
          </>
        )}
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
    width: "100%",
    backgroundColor: "var(--mp-card)",
    borderRight: "1px solid var(--mp-rule)",
    color: "var(--mp-ink-2)",
    display: "flex",
    flexDirection: "column",
    paddingBlock: "var(--space-4)",
    overflowX: "hidden",
    transition: "width 160ms ease",
  },
  resizeHandle: {
    position: "absolute",
    top: 0,
    right: -4,
    width: 8,
    height: "100%",
    border: "none",
    padding: 0,
    cursor: "col-resize",
    background: "transparent",
    zIndex: 2,
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
    paddingInline: "var(--space-2)",
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
    cursor: "pointer", lineHeight: 1,
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
    display: "flex", alignItems: "center", gap: 10,
    padding: "7px 12px",
    borderRadius: "var(--radius-sm)",
    fontSize: 13, fontWeight: 450, letterSpacing: "-0.005em",
    textDecoration: "none", whiteSpace: "nowrap", overflow: "hidden",
    border: "1px solid transparent",
    transition: "background-color 120ms, color 120ms, border-color 120ms",
  },
  navLinkCollapsed: {
    width: 34,
    height: 34,
    padding: 0,
    marginInline: "auto",
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
  navLabel: { overflow: "hidden", textOverflow: "ellipsis" },
  navTag: {
    marginLeft: "auto",
    fontSize: 9.5,
    textTransform: "uppercase",
    letterSpacing: "0.10em",
    color: "var(--mp-mute)",
    fontFamily: "var(--mp-font-mono, monospace)",
  },
  footer: {
    paddingInline: "var(--space-4)", paddingTop: "var(--space-3)",
    borderTop: "1px solid var(--mp-rule)",
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  footerCollapsed: {
    paddingInline: "var(--space-2)",
    alignItems: "center",
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
