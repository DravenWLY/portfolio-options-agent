import { type ReactNode } from "react";
import { useLocation } from "react-router-dom";

interface TopBarProps {
  /** Slot for the account selector chip — wired in P11-T2. */
  accountSlot?: ReactNode;
}

/**
 * TopBar — P20A-T2 prototype topology.
 *
 * Translated from `AppTopBar` in
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/app.tsx
 *
 * The bar now lives **inside** the main column (no longer `position: fixed`
 * full-width across the viewport). The Sidebar owns its own brand header
 * separately, so this strip carries only the workspace-eyebrow breadcrumb +
 * screen title + right-side controls (appearance + account).
 *
 * No global freshness dials in this slice (no aggregate freshness endpoint).
 *
 * Safety: no trade-execution controls, no live market quote widgets, no
 * recommendation language.
 */

const ROUTE_TITLE: Array<{ match: RegExp; eyebrow: string; title: string }> = [
  { match: /^\/broker/, eyebrow: "Workspace · broker", title: "Broker Connection" },
  { match: /^\/market-data/, eyebrow: "Workspace · market data", title: "Market Data" },
  { match: /^\/risk/, eyebrow: "Workspace · risk review", title: "Risk Review" },
  { match: /^\/trade-review/, eyebrow: "Workspace · trade review", title: "Review trade" },
  { match: /^\/agent-team-analysis/, eyebrow: "Workspace · agent console", title: "Agent team analysis" },
  { match: /^\/reports/, eyebrow: "Workspace · reports", title: "Reports" },
  { match: /^\/portfolio-context/, eyebrow: "Workspace · portfolio context", title: "Portfolio context" },
  { match: /^\/settings/, eyebrow: "Workspace · settings", title: "Settings" },
  { match: /^\/landing/, eyebrow: "Marketing · landing", title: "Landing (placeholder)" },
  { match: /^\/pricing/, eyebrow: "Marketing · pricing", title: "Pricing (placeholder)" },
  { match: /^\/auth/, eyebrow: "Marketing · sign-in", title: "Sign in (placeholder)" },
  { match: /^\/$/, eyebrow: "Workspace · overview", title: "Dashboard" },
];

function titleFor(pathname: string): { eyebrow: string; title: string } {
  for (const r of ROUTE_TITLE) if (r.match.test(pathname)) return { eyebrow: r.eyebrow, title: r.title };
  return { eyebrow: "Workspace", title: "Portfolio Copilot" };
}

export default function TopBar({ accountSlot }: TopBarProps) {
  const { pathname } = useLocation();
  const { eyebrow, title } = titleFor(pathname);
  return (
    <header className="mp-surface" style={styles.bar} role="banner">
      <div style={styles.left}>
        <span style={styles.eyebrow}>{eyebrow}</span>
        <span style={styles.sep} aria-hidden="true">›</span>
        <span className="mp-display" style={styles.title}>{title}</span>
      </div>
      <div style={styles.right}>
        {accountSlot ?? (
          <span style={styles.accountPlaceholder}>— account selector —</span>
        )}
      </div>
    </header>
  );
}

const styles: Record<string, React.CSSProperties> = {
  bar: {
    position: "sticky",
    top: 0,
    zIndex: 90,
    backgroundColor: "var(--mp-card)",
    borderBottom: "1px solid var(--mp-rule)",
    color: "var(--mp-ink)",
    height: "var(--topbar-height)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    paddingInline: "var(--space-6)",
    gap: "var(--space-4)",
  },
  left: { display: "flex", alignItems: "baseline", gap: 12, minWidth: 0 },
  eyebrow: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.06em",
  },
  sep: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute-2)" },
  title: { fontSize: 16, color: "var(--mp-ink)", fontWeight: 500 },
  right: { display: "flex", alignItems: "center", gap: "var(--space-3)" },
  accountPlaceholder: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", fontStyle: "italic" },
};
