import type { ReactNode } from "react";

interface PanelProps {
  title: string;
  tag?: string;
  right?: ReactNode;
  accent?: boolean;
  toneLeft?: "stale" | "block" | "info" | "mute";
  children: ReactNode;
}

/**
 * MP Panel — translated from the `Panel` primitive in components.tsx of the
 * typed prototype. Backend / data agnostic.
 */
export default function Panel({ title, tag, right, accent, toneLeft, children }: PanelProps) {
  const leftBorder =
    accent ? "3px solid var(--mp-accent)" :
    toneLeft === "stale" ? "3px solid var(--mp-stale)" :
    toneLeft === "block" ? "3px solid var(--mp-block)" :
    toneLeft === "info"  ? "3px solid var(--mp-info)"  :
    undefined;

  return (
    <section
      style={{
        backgroundColor: "var(--mp-card)",
        border: "1px solid var(--mp-rule)",
        borderLeft: leftBorder ?? "1px solid var(--mp-rule)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-4) var(--space-5)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-3)",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-3)",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-3)" }}>
          <span
            className="mp-display"
            style={{ fontWeight: 500, fontSize: "var(--font-size-md)", color: "var(--mp-ink)" }}
          >
            {title}
          </span>
          {tag && (
            <span style={{
              fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
              textTransform: "uppercase", letterSpacing: "0.08em",
            }}>{tag}</span>
          )}
        </div>
        {right}
      </header>
      {children}
    </section>
  );
}
