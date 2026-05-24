import { mpToneFg, type MpTone } from "./tokens";

interface StatProps {
  label: string;
  value: string;
  sub?: string;
  tone?: MpTone | "ink";
}

/**
 * MP Stat — large monospaced stat with label + sub-line.
 * Translated from the `Stat` primitive in components.tsx of the typed
 * prototype. No frontend computation: the caller passes a string that
 * came verbatim from the backend.
 */
export default function Stat({ label, value, sub, tone = "ink" }: StatProps) {
  const color = tone === "ink" ? "var(--mp-ink)" : mpToneFg[tone];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{
        fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
        textTransform: "uppercase", letterSpacing: "0.06em",
      }}>{label}</span>
      <span className="mp-mono" style={{ fontSize: "var(--font-size-xl)", color, lineHeight: 1.2 }}>{value}</span>
      {sub && <span style={{ fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" }}>{sub}</span>}
    </div>
  );
}
