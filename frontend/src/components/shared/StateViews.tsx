/**
 * Shared loading / error / empty state components.
 *
 * All data-driven panels must use these rather than rendering null or a blank
 * div — a blank render is indistinguishable from a bug.
 */

/* ── Loading skeleton ───────────────────────────────────────────────────── */

export function LoadingSkeleton({ rows = 3, label = "Loading…" }: { rows?: number; label?: string }) {
  return (
    <div style={skeletonWrap} role="status" aria-label={label} aria-live="polite">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ ...skeletonRow, width: i % 3 === 0 ? "70%" : i % 3 === 1 ? "90%" : "55%" }} />
      ))}
    </div>
  );
}

const skeletonWrap: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "var(--space-2)",
  padding: "var(--space-2) 0",
};
const skeletonRow: React.CSSProperties = {
  height: 14,
  borderRadius: "var(--radius-sm)",
  backgroundColor: "var(--color-surface-2)",
  animation: "pulse 1.6s ease-in-out infinite",
};

/* ── Error state ────────────────────────────────────────────────────────── */

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div style={errorWrap} role="alert">
      <span style={errorIcon} aria-hidden="true">⚠</span>
      <div>
        <p style={errorTitle}>Failed to load data</p>
        <p style={errorMessage}>{message}</p>
        {onRetry && (
          <button style={retryBtn} onClick={onRetry} type="button">
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

const errorWrap: React.CSSProperties = {
  display: "flex",
  gap: "var(--space-3)",
  alignItems: "flex-start",
  padding: "var(--space-4)",
  backgroundColor: "var(--color-error-bg)",
  border: "1px solid var(--color-error)",
  borderRadius: "var(--radius-md)",
};
const errorIcon: React.CSSProperties = {
  color: "var(--color-error)",
  fontSize: "var(--font-size-lg)",
  flexShrink: 0,
  marginTop: 1,
};
const errorTitle: React.CSSProperties = {
  fontWeight: 600,
  fontSize: "var(--font-size-sm)",
  color: "var(--color-error)",
  marginBottom: "var(--space-1)",
};
const errorMessage: React.CSSProperties = {
  fontSize: "var(--font-size-sm)",
  color: "var(--color-text-secondary)",
};
const retryBtn: React.CSSProperties = {
  marginTop: "var(--space-2)",
  padding: "var(--space-1) var(--space-3)",
  fontSize: "var(--font-size-sm)",
  backgroundColor: "transparent",
  color: "var(--color-error)",
  border: "1px solid var(--color-error)",
  borderRadius: "var(--radius-sm)",
  cursor: "pointer",
  fontFamily: "var(--font-family)",
};

/* ── Empty state ────────────────────────────────────────────────────────── */

export function EmptyState({ icon = "○", title, body }: { icon?: string; title: string; body?: string }) {
  return (
    <div style={emptyWrap} role="status" aria-live="polite">
      <span style={emptyIcon} aria-hidden="true">{icon}</span>
      <p style={emptyTitle}>{title}</p>
      {body && <p style={emptyBody}>{body}</p>}
    </div>
  );
}

const emptyWrap: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: "var(--space-2)",
  padding: "var(--space-10) var(--space-6)",
  textAlign: "center",
};
const emptyIcon: React.CSSProperties = {
  fontSize: 28,
  color: "var(--color-text-muted)",
  lineHeight: 1,
};
const emptyTitle: React.CSSProperties = {
  fontSize: "var(--font-size-sm)",
  fontWeight: 600,
  color: "var(--color-text-secondary)",
};
const emptyBody: React.CSSProperties = {
  fontSize: "var(--font-size-sm)",
  color: "var(--color-text-muted)",
  lineHeight: 1.6,
  maxWidth: 360,
};
