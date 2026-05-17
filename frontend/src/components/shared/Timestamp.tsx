/**
 * Timestamp — formats an ISO 8601 datetime string for display.
 *
 * Always shows timezone. Used across all broker-data panels.
 * Never merge broker sync timestamps with market quote timestamps.
 */
export default function Timestamp({
  iso,
  prefix = "As of",
}: {
  iso: string | null | undefined;
  prefix?: string;
}) {
  if (!iso) {
    return <span style={unknown}>timestamp unknown</span>;
  }

  let display: string;
  try {
    const d = new Date(iso);
    display = d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    });
  } catch {
    display = iso;
  }

  return (
    <time dateTime={iso} style={stamp} title={iso}>
      {prefix} {display}
    </time>
  );
}

const stamp: React.CSSProperties = {
  fontSize: "var(--font-size-xs)",
  color: "var(--color-text-muted)",
};
const unknown: React.CSSProperties = {
  fontSize: "var(--font-size-xs)",
  color: "var(--color-text-muted)",
  fontStyle: "italic",
};
