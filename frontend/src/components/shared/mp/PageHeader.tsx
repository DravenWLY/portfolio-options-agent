import type { ReactNode } from "react";

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  sub?: string;
  right?: ReactNode;
}

/**
 * MP PageHeader — translated from `PageHeader` in the typed prototype's
 * components.tsx. Eyebrow + serif display title + optional subtitle +
 * right-side actions slot.
 */
export default function PageHeader({ eyebrow, title, sub, right }: PageHeaderProps) {
  return (
    <header
      style={{
        display: "flex",
        gap: "var(--space-4)",
        alignItems: "flex-start",
        justifyContent: "space-between",
        flexWrap: "wrap",
        paddingBottom: "var(--space-4)",
        borderBottom: "1px solid var(--mp-rule)",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 0 }}>
        {eyebrow && (
          <span style={{
            fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
            textTransform: "uppercase", letterSpacing: "0.08em",
          }}>{eyebrow}</span>
        )}
        <h1 className="mp-display" style={{
          fontWeight: 500, fontSize: "var(--font-size-2xl)",
          color: "var(--mp-ink)", margin: 0, lineHeight: 1.2,
        }}>{title}</h1>
        {sub && (
          <p style={{ fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", margin: 0, maxWidth: 720, lineHeight: 1.6 }}>{sub}</p>
        )}
      </div>
      {right && <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>{right}</div>}
    </header>
  );
}
