/**
 * Shared presentational ramp for Market Mood surfaces (compact card +
 * detail page). Pure rendering only — no parsing, comparison, or computation
 * beyond placing the marker on the 0–100 spectrum at the backend score.
 *
 * The matching `dataModeBadge` helper lives in `./marketMoodHelpers.ts` so
 * this module keeps the React Fast Refresh component-only export boundary.
 */

/**
 * 0–100 gradient spectrum ramp with an ink-ring marker. Color stops use MP
 * tone tokens (fear → mid → greed). The marker position is derived from the
 * backend score only and clamped to [0, 100]; null score hides the marker.
 *
 * Accessibility: rendered as role="img" with an aria-label describing the
 * band range and current score; color is supplementary, never the sole signal.
 */
export function SpectrumRamp({
  score,
  min,
  max,
  height = 8,
  markerSize = 12,
}: {
  score: number | null;
  min: number;
  max: number;
  height?: number;
  markerSize?: number;
}) {
  const span = max - min;
  const pct =
    score == null || span <= 0
      ? null
      : Math.max(0, Math.min(100, ((score - min) / span) * 100));
  const gradient =
    "linear-gradient(90deg, var(--mp-block) 0%, var(--mp-stale) 35%, var(--mp-mute) 50%, var(--mp-info) 65%, var(--mp-live) 100%)";
  return (
    <div
      style={{ display: "flex", flexDirection: "column", gap: 3, minWidth: 0 }}
      role="img"
      aria-label={`Sentiment ramp ${min} to ${max}${score != null ? `, score ${score}` : ", score unavailable"}`}
    >
      <div
        style={{
          position: "relative",
          height,
          borderRadius: 999,
          border: "1px solid var(--mp-rule)",
          backgroundImage: gradient,
          overflow: "visible",
        }}
      >
        {pct != null && (
          <div
            aria-hidden="true"
            style={{
              position: "absolute",
              top: "50%",
              left: `${pct}%`,
              width: markerSize,
              height: markerSize,
              borderRadius: 999,
              backgroundColor: "var(--mp-card)",
              border: "2px solid var(--mp-ink)",
              transform: "translate(-50%, -50%)",
              boxShadow: "0 0 0 1px var(--mp-card)",
            }}
          />
        )}
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: "var(--font-size-xs)",
          color: "var(--mp-mute)",
          fontFamily: "var(--mp-font-mono)",
        }}
      >
        <span>{min}</span>
        <span>{Math.round((min + max) / 2)}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}
