import { type ReactNode } from "react";

interface TopBarProps {
  /** Slot for the account selector chip — wired in P11-T2. */
  accountSlot?: ReactNode;
}

/**
 * TopBar — fixed top strip containing the product name and account selector slot.
 *
 * Safety note: This bar must never contain trade-execution controls,
 * market quote widgets, or guaranteed-return language.
 */
export default function TopBar({ accountSlot }: TopBarProps) {
  return (
    <header style={styles.bar} role="banner">
      <div style={styles.brand}>
        <span style={styles.brandMark} aria-hidden="true">◈</span>
        <span style={styles.brandName}>Portfolio Copilot</span>
        <span style={styles.brandTag}>decision support · read-only</span>
      </div>

      <div style={styles.accountArea}>
        {accountSlot ?? (
          <span style={styles.accountPlaceholder}>
            — account selector (P11-T2) —
          </span>
        )}
      </div>
    </header>
  );
}

const styles: Record<string, React.CSSProperties> = {
  bar: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    height: "var(--topbar-height)",
    backgroundColor: "var(--color-surface)",
    borderBottom: "1px solid var(--color-border)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    paddingInline: "var(--space-6)",
    zIndex: 100,
    gap: "var(--space-4)",
  },
  brand: {
    display: "flex",
    alignItems: "baseline",
    gap: "var(--space-3)",
    flexShrink: 0,
  },
  brandMark: {
    color: "var(--color-accent)",
    fontSize: "var(--font-size-lg)",
    lineHeight: 1,
  },
  brandName: {
    fontSize: "var(--font-size-md)",
    fontWeight: 600,
    letterSpacing: "0.02em",
    color: "var(--color-text-primary)",
  },
  brandTag: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  accountArea: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
  },
  accountPlaceholder: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    fontStyle: "italic",
  },
};
