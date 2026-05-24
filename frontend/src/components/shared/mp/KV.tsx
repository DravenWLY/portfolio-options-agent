import type { ReactNode } from "react";

interface KVProps {
  rows: ReadonlyArray<readonly [label: string, value: ReactNode]>;
  compact?: boolean;
}

/**
 * MP KV — definition list. Translated from the `KV` primitive in the typed
 * prototype's components.tsx. Values are rendered verbatim; no formatting
 * is applied here (the page is responsible for any locale/units).
 */
export default function KV({ rows, compact = false }: KVProps) {
  return (
    <dl style={{ display: "flex", flexDirection: "column", gap: compact ? 4 : "var(--space-1)", margin: 0 }}>
      {rows.map(([k, v], i) => (
        <div
          key={`${k}-${i}`}
          style={{
            display: "flex",
            gap: "var(--space-4)",
            justifyContent: "space-between",
            alignItems: "baseline",
            fontSize: "var(--font-size-xs)",
            lineHeight: 1.5,
          }}
        >
          <dt style={{ color: "var(--mp-mute)", margin: 0 }}>{k}</dt>
          <dd className="mp-mono" style={{ margin: 0, color: "var(--mp-ink-2)", textAlign: "right", wordBreak: "break-word" }}>
            {v}
          </dd>
        </div>
      ))}
    </dl>
  );
}
