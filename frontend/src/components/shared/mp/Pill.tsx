import type { ReactNode } from "react";
import { mpToneFg, mpToneIcon, type MpTone } from "./tokens";

interface PillProps {
  tone: MpTone;
  children: ReactNode;
  icon?: string;
  title?: string;
}

/**
 * MP Pill — severity tag for list rows (icon + text + colored outline).
 * Translated from the `Pill` primitive in components.tsx of the typed
 * prototype. Severity is conveyed by icon glyph AND text — never color
 * alone.
 */
export default function Pill({ tone, children, icon, title }: PillProps) {
  const fg = mpToneFg[tone];
  return (
    <span
      title={title}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: "var(--font-size-xs)",
        fontWeight: 700,
        padding: "1px 7px",
        border: `1px solid ${fg}`,
        borderRadius: "var(--radius-sm)",
        color: fg,
        whiteSpace: "nowrap",
      }}
    >
      <span aria-hidden="true">{icon ?? mpToneIcon[tone]}</span>
      {children}
    </span>
  );
}
