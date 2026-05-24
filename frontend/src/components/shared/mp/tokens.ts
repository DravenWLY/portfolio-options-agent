/**
 * Modern Portfolio Desk — tone → CSS-variable map.
 *
 * Translated from the typed prototype primitive at
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/components.tsx
 *
 * Tones are presentation labels, not backend enums; pages translate
 * `RiskSeverity` / `ReviewActionabilityStatus` / `LLMProviderStatus` into
 * a tone here. Severity meaning is always paired with an icon and text by
 * the consuming primitive — never color-only.
 */

export type MpTone = "live" | "stale" | "block" | "info" | "mute" | "accent";

export const mpToneFg: Record<MpTone, string> = {
  live: "var(--mp-live)",
  stale: "var(--mp-stale)",
  block: "var(--mp-block)",
  info: "var(--mp-info)",
  mute: "var(--mp-mute)",
  accent: "var(--mp-accent)",
};

export const mpToneSoft: Record<MpTone, string> = {
  live: "var(--mp-live-soft)",
  stale: "var(--mp-stale-soft)",
  block: "var(--mp-block-soft)",
  info: "var(--mp-info-soft)",
  mute: "transparent",
  accent: "var(--mp-accent-soft)",
};

export const mpToneIcon: Record<MpTone, string> = {
  live: "●",
  stale: "△",
  block: "■",
  info: "ⓘ",
  mute: "○",
  accent: "◆",
};
