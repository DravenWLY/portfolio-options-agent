import type { ReactNode } from "react";

interface SectionHProps {
  num: string;
  kicker: string;
  title: string;
  right?: ReactNode;
}

/**
 * SectionH — marketing section header.
 *
 * Translated from the `SectionH` block used by the typed prototype's
 * `screens/landing.tsx` and `screens/pricing.tsx`. Renders a numbered
 * eyebrow (e.g. "01 —"), an uppercase kicker, a serif display title, and
 * an optional right-side slot (e.g. a "See full pricing →" ghost button).
 *
 * Backend / data agnostic. Uses --mp-* tokens only.
 */
export default function SectionH({ num, kicker, title, right }: SectionHProps) {
  return (
    <header style={styles.wrap}>
      <div style={styles.left}>
        <div style={styles.row}>
          <span style={styles.num}>{num}</span>
          <span style={styles.kicker}>{kicker}</span>
        </div>
        <h2 className="mp-display" style={styles.title}>{title}</h2>
      </div>
      {right && <div style={styles.right}>{right}</div>}
    </header>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    display: "flex",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: "var(--space-4)",
    flexWrap: "wrap",
    paddingBottom: "var(--space-3)",
    borderBottom: "1px solid var(--mp-rule)",
    marginBottom: "var(--space-5)",
  },
  left: { display: "flex", flexDirection: "column", gap: "var(--space-2)", minWidth: 0 },
  row: { display: "flex", alignItems: "baseline", gap: "var(--space-3)" },
  num: {
    fontFamily: "var(--mp-font-mono)",
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-accent)",
    letterSpacing: "0.04em",
  },
  kicker: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    textTransform: "uppercase",
    letterSpacing: "0.12em",
    fontWeight: 600,
  },
  title: {
    margin: 0,
    fontSize: "var(--font-size-2xl)",
    fontWeight: 500,
    color: "var(--mp-ink)",
    letterSpacing: "-0.01em",
    lineHeight: 1.2,
    maxWidth: 760,
  },
  right: { display: "flex", alignItems: "center", gap: "var(--space-2)" },
};
