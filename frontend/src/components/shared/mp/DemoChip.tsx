/**
 * MP DemoChip — visible "demo · not yet connected" badge for placeholder
 * cards on screens that do not have a backing API contract yet.
 *
 * Every Phase 20A-T3 placeholder card MUST surface this chip so the screen
 * is never mistaken for real connected brokerage data. The wording is fixed.
 */
export default function DemoChip({ tight = false }: { tight?: boolean }) {
  return (
    <span
      role="note"
      aria-label="Demo data — not yet connected to a backend contract"
      title="Demo data — not yet connected"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: "var(--font-size-xs)",
        fontWeight: 600,
        letterSpacing: "0.04em",
        padding: tight ? "1px 6px" : "2px 8px",
        border: "1px dashed var(--mp-mute)",
        borderRadius: "var(--radius-sm)",
        color: "var(--mp-mute)",
        backgroundColor: "transparent",
        textTransform: "uppercase",
        lineHeight: 1.4,
        whiteSpace: "nowrap",
      }}
    >
      <span aria-hidden="true">○</span>
      demo · not yet connected
    </span>
  );
}
