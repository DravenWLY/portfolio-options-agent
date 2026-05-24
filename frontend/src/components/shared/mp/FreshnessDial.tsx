import { mpToneFg, type MpTone } from "./tokens";

interface FreshnessDialProps {
  label: string;
  ago: string;
  tone: MpTone;
}

/**
 * MP FreshnessDial — translated from `FreshnessDial` in the typed prototype's
 * components.tsx. Per-page use only — no aggregated freshness endpoint exists.
 */
export default function FreshnessDial({ label, ago, tone }: FreshnessDialProps) {
  const fg = mpToneFg[tone];
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" }}>
      <span aria-hidden="true" style={{
        width: 8, height: 8, borderRadius: 999, backgroundColor: fg,
        boxShadow: tone === "live" ? `0 0 0 3px ${fg}22` : undefined,
      }} />
      <span className="mp-mono" style={{ color: "var(--mp-ink-2)", minWidth: 28 }}>{ago}</span>
      <span>{label}</span>
    </span>
  );
}
