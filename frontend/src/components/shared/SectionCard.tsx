import { type ReactNode } from "react";

interface SectionCardProps {
  id?: string;
  label: string;
  /** Optional right-side slot for timestamps, badges, etc. */
  headerRight?: ReactNode;
  children: ReactNode;
}

/**
 * SectionCard — consistent panel wrapper for dashboard sections.
 * Provides the surface, border, label, and layout used by all data panels.
 */
export default function SectionCard({ id, label, headerRight, children }: SectionCardProps) {
  return (
    <section id={id} aria-label={label} style={styles.card}>
      <div style={styles.header}>
        <h2 style={styles.label}>{label}</h2>
        {headerRight && <div style={styles.headerRight}>{headerRight}</div>}
      </div>
      <div style={styles.body}>{children}</div>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-md)",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "var(--space-4) var(--space-6)",
    borderBottom: "1px solid var(--color-border-subtle)",
    gap: "var(--space-4)",
  },
  label: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
    color: "var(--color-text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-3)",
    flexShrink: 0,
  },
  body: {
    padding: "var(--space-5) var(--space-6)",
  },
};
