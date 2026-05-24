import type { ReactNode } from "react";
import { mpToneFg, mpToneSoft, type MpTone } from "./tokens";

interface BadgeProps {
  tone?: MpTone;
  dot?: boolean;
  children: ReactNode;
  title?: string;
}

/**
 * MP Badge — small status pill (icon-dot optional + text).
 * Translated from `Badge` in the TSX prototype's components.tsx.
 * Color is always paired with text — never color-only.
 */
export default function Badge({ tone = "info", dot = true, children, title }: BadgeProps) {
  const fg = mpToneFg[tone];
  return (
    <span
      title={title}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: "var(--font-size-xs)",
        fontWeight: 600,
        letterSpacing: "0.02em",
        padding: "2px 8px",
        border: `1px solid ${fg}`,
        borderRadius: "var(--radius-sm)",
        color: fg,
        backgroundColor: mpToneSoft[tone],
        lineHeight: 1.4,
        whiteSpace: "nowrap",
      }}
    >
      {dot && <span aria-hidden="true" style={{ width: 6, height: 6, borderRadius: 999, backgroundColor: fg }} />}
      {children}
    </span>
  );
}
