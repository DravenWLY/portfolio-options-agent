interface SafetyStripProps {
  items: ReadonlyArray<string>;
  compact?: boolean;
}

/**
 * MP SafetyStrip — translated from `SafetyStrip` in the typed prototype's
 * components.tsx. Phrases pool: "Analysis only", "Manual trade review",
 * "Not an order recommendation", "Data freshness may affect review quality".
 * Never includes execution-style, recommendation, or guaranteed-return copy.
 */
export default function SafetyStrip({ items, compact = false }: SafetyStripProps) {
  return (
    <div
      role="note"
      aria-label="Safety reminders"
      style={{
        display: "flex",
        gap: compact ? "var(--space-2)" : "var(--space-3)",
        flexWrap: "wrap",
        padding: compact ? "var(--space-2) 0" : "var(--space-3) var(--space-4)",
        backgroundColor: compact ? "transparent" : "var(--mp-paper-2)",
        border: compact ? "none" : "1px dashed var(--mp-rule)",
        borderRadius: "var(--radius-sm)",
      }}
    >
      {items.map((item) => (
        <span key={item} style={{ fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", letterSpacing: "0.02em" }}>
          <span aria-hidden="true" style={{ marginRight: 4, color: "var(--mp-mute-2)" }}>·</span>
          {item}
        </span>
      ))}
    </div>
  );
}
