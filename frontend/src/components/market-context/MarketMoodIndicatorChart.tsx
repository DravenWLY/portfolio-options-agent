import { useLayoutEffect, useMemo, useRef, useState } from "react";
import type {
  MarketMoodIndicatorHistoryPointRead,
  MarketMoodAxisValueFormat,
} from "../../types/marketMood";
import { formatAxisValue } from "./marketMoodHelpers";

/**
 * MarketMoodIndicatorChart — small interactive SVG line chart (P26A-T4).
 *
 * Plots a single indicator's RAW history (`history[].value`) on its own
 * native scale — never forced onto the normalized 0–100 score. Hovering shows
 * a date + the backend `value_label` (verbatim), with the normalized rating /
 * score as secondary context.
 *
 * Pure presentation: the only math is min/max autoscale + linear interpolation
 * for pixel placement. No surprise/compare/forecast logic; no value is invented
 * (axis min/max ticks are light display formatting of backend-provided numbers,
 * keyed off the backend `axis_value_format`). Color is supplementary; meaning is
 * carried by the labels and the higher/lower-value caption.
 */

const DEFAULT_H = 168;
const PAD_T = 14;
const PAD_B = 22;
const PAD_L = 8;
const PAD_R = 8;

type PlottedHistoryPoint = MarketMoodIndicatorHistoryPointRead & {
  historyIndex: number;
  dateMs: number;
  value: number;
};

type MovingAveragePoint = {
  date: string;
  dateMs: number;
  value: number | null;
  historyIndex: number;
};

interface ChartProps {
  history: MarketMoodIndicatorHistoryPointRead[];
  axisValueFormat: MarketMoodAxisValueFormat;
  unitLabel: string | null;
  ariaLabel: string;
  height?: number;
  primarySeriesLabel?: string;
  movingAverageWindow?: number;
  movingAverageLabel?: string;
  movingAverageTooltipLabel?: string;
  /** When true, format axis ticks and the tooltip raw value as plain numbers
   *  (no "%", "$", or unit suffix) and prefer the formatted neutral string
   *  over backend `value_label` (which carries the misleading unit). Used when
   *  the page detects the live provider unit does not match the value scale. */
  neutralScale?: boolean;
}

export default function MarketMoodIndicatorChart({
  history,
  axisValueFormat,
  unitLabel,
  ariaLabel,
  height = DEFAULT_H,
  primarySeriesLabel = "Value",
  movingAverageWindow,
  movingAverageLabel = "moving average",
  movingAverageTooltipLabel = movingAverageLabel,
  neutralScale = false,
}: ChartProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(560);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const gradientId = useGradientId();

  useLayoutEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const update = () => setWidth(Math.max(180, Math.round(el.clientWidth)));
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const visibleWindowStartMs = useMemo(() => {
    const now = new Date();
    const start = new Date(Date.UTC(now.getUTCFullYear() - 1, now.getUTCMonth(), now.getUTCDate()));
    return start.getTime();
  }, []);

  // Only points with a numeric value and parseable date can be plotted; keep order from backend.
  const points = useMemo(
    () => history
      .map((p, historyIndex) => ({ ...p, historyIndex, dateMs: parseHistoryDateMs(p.date) }))
      .filter((p): p is PlottedHistoryPoint => (
        p.value != null && Number.isFinite(p.value) && p.dateMs != null
      )),
    [history],
  );

  const movingAveragePoints = useMemo(() => {
    if (!movingAverageWindow || movingAverageWindow <= 1 || points.length < movingAverageWindow) return [];
    const values = points.map((p) => p.value);
    const result: MovingAveragePoint[] = points.map((p) => ({
      date: p.date,
      dateMs: p.dateMs,
      value: null,
      historyIndex: p.historyIndex,
    }));
    let rolling = 0;
    for (let i = 0; i < values.length; i += 1) {
      rolling += values[i];
      if (i >= movingAverageWindow) rolling -= values[i - movingAverageWindow];
      if (i >= movingAverageWindow - 1) {
        result[i].value = rolling / movingAverageWindow;
      }
    }
    return result;
  }, [movingAverageWindow, points]);

  const visiblePoints = useMemo(
    () => points.filter((p) => p.dateMs >= visibleWindowStartMs),
    [points, visibleWindowStartMs],
  );

  const visibleMovingAveragePoints = useMemo(
    () => movingAveragePoints.filter((p) => p.dateMs >= visibleWindowStartMs),
    [movingAveragePoints, visibleWindowStartMs],
  );

  const movingAverageByHistoryIndex = useMemo(() => {
    const byIndex = new Map<number, number>();
    for (const point of movingAveragePoints) {
      if (point.value != null && Number.isFinite(point.value)) {
        byIndex.set(point.historyIndex, point.value);
      }
    }
    return byIndex;
  }, [movingAveragePoints]);

  const geom = useMemo(() => {
    if (visiblePoints.length < 2) return null;
    const drawableMovingAveragePoints = visibleMovingAveragePoints
      .map((p, i) => ({ ...p, pointIndex: i }))
      .filter((p): p is MovingAveragePoint & { value: number; pointIndex: number } => (
        p.value != null && Number.isFinite(p.value)
      ));
    const values = [
      ...visiblePoints.map((p) => p.value),
      ...drawableMovingAveragePoints.map((p) => p.value),
    ];
    let lo = Math.min(...values);
    let hi = Math.max(...values);
    if (lo === hi) { lo -= 1; hi += 1; }
    const padV = (hi - lo) * 0.08;
    lo -= padV; hi += padV;
    const innerW = width - PAD_L - PAD_R;
    const innerH = height - PAD_T - PAD_B;
    const firstVisibleDateMs = visiblePoints[0].dateMs;
    const lastVisibleDateMs = visiblePoints[visiblePoints.length - 1].dateMs;
    const dateSpan = Math.max(1, lastVisibleDateMs - firstVisibleDateMs);
    const xOf = (dateMs: number) => PAD_L + ((dateMs - firstVisibleDateMs) / dateSpan) * innerW;
    const yOf = (v: number) => PAD_T + (1 - (v - lo) / (hi - lo)) * innerH;
    const coords = visiblePoints.map((p) => ({ x: xOf(p.dateMs), y: yOf(p.value) }));
    const maCoords = drawableMovingAveragePoints.map((p) => ({
      x: xOf(p.dateMs),
      y: yOf(p.value),
      value: p.value,
      pointIndex: p.pointIndex,
      historyIndex: p.historyIndex,
    }));
    const linePath = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");
    const maPath = maCoords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");
    const areaPath = `${linePath} L${coords[coords.length - 1].x.toFixed(1)},${(height - PAD_B).toFixed(1)} L${coords[0].x.toFixed(1)},${(height - PAD_B).toFixed(1)} Z`;
    return { coords, maCoords, linePath, maPath, areaPath, lo, hi };
  }, [visiblePoints, visibleMovingAveragePoints, width, height]);

  if (visiblePoints.length < 2) {
    return (
      <div ref={wrapRef} style={{ ...styles.emptyWrap, height }}>
        <span style={styles.emptyTitle}>Insufficient history</span>
        <span style={styles.emptyText}>The backend did not provide enough one-year raw values to draw this indicator.</span>
      </div>
    );
  }

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!geom) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const px = e.clientX - rect.left;
    // Nearest plotted point by x.
    let best = 0;
    let bestD = Infinity;
    for (let i = 0; i < geom.coords.length; i++) {
      const d = Math.abs(geom.coords[i].x - px);
      if (d < bestD) { bestD = d; best = i; }
    }
    setHoverIdx(best);
  };

  const hovered = hoverIdx != null ? visiblePoints[hoverIdx] : null;
  const hoveredCoord = hoverIdx != null && geom ? geom.coords[hoverIdx] : null;
  const hoveredValue =
    hovered == null
      ? ""
      : neutralScale
        ? formatTooltipValue(hovered.value, axisValueFormat, unitLabel, true)
        : (hovered.value_label ?? formatAxisValue(hovered.value, axisValueFormat, unitLabel));
  const hoveredMeta =
    hovered == null
      ? ""
      : `${hovered.rating_label}${hovered.score_label ? ` - ${hovered.score_label}/100` : ""}`;
  const hoveredMa =
    hovered != null
      ? movingAverageByHistoryIndex.get(hovered.historyIndex) ?? null
      : null;
  const hoveredMaLabel =
    hoveredMa == null
      ? null
      : formatTooltipValue(hoveredMa, axisValueFormat, unitLabel, neutralScale);
  const tooltipDate = hovered == null ? "" : formatTooltipDate(hovered.date);

  return (
    <div ref={wrapRef} style={styles.wrap}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={ariaLabel}
        style={styles.svg}
        onMouseMove={onMove}
        onMouseLeave={() => setHoverIdx(null)}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--mp-accent)" stopOpacity="0.20" />
            <stop offset="100%" stopColor="var(--mp-accent)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Baseline + top reference gridlines (subtle). */}
        <line x1={PAD_L} y1={PAD_T} x2={width - PAD_R} y2={PAD_T} stroke="var(--mp-rule)" strokeWidth="1" strokeDasharray="2 4" />
        <line x1={PAD_L} y1={height - PAD_B} x2={width - PAD_R} y2={height - PAD_B} stroke="var(--mp-rule)" strokeWidth="1" />

        {geom && <path d={geom.areaPath} fill={`url(#${gradientId})`} />}
        {geom?.maPath && (
          <path
            d={geom.maPath}
            fill="none"
            stroke="var(--mp-stale)"
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        )}
        {geom && (
          <path
            d={geom.linePath}
            fill="none"
            stroke="var(--mp-accent)"
            strokeWidth="2"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        )}

        {/* Hover guide + marker. */}
        {hoveredCoord && (
          <>
            <line x1={hoveredCoord.x} y1={PAD_T} x2={hoveredCoord.x} y2={height - PAD_B} stroke="var(--mp-mute)" strokeWidth="1" strokeDasharray="2 3" />
            <circle cx={hoveredCoord.x} cy={hoveredCoord.y} r="4.5" fill="var(--mp-card)" stroke="var(--mp-accent)" strokeWidth="2" />
          </>
        )}
      </svg>

      {/* Y-axis min/max ticks (light formatting of backend values). */}
      {geom && (
        <>
          <span style={{ ...styles.yTick, top: PAD_T - 7 }}>{formatAxisValue(geom.hi, axisValueFormat, unitLabel, { neutral: neutralScale })}</span>
          <span style={{ ...styles.yTick, top: height - PAD_B - 7 }}>{formatAxisValue(geom.lo, axisValueFormat, unitLabel, { neutral: neutralScale })}</span>
        </>
      )}

      {/* X-axis end dates. */}
      <div style={styles.xAxis}>
        <span>{visiblePoints[0].date}</span>
        <span>{visiblePoints[visiblePoints.length - 1].date}</span>
      </div>

      {/* Tooltip. */}
      {hovered && hoveredCoord && (
        <div
          style={{
            ...styles.tooltip,
            left: clampTooltip(hoveredCoord.x, width),
            top: Math.max(0, hoveredCoord.y - 8),
          }}
          role="status"
          aria-label={`${tooltipDate}, ${primarySeriesLabel}, ${hoveredValue}${hoveredMaLabel ? `, ${movingAverageTooltipLabel}, ${hoveredMaLabel}` : ""}${hoveredMeta ? `, ${hoveredMeta}` : ""}`}
        >
          <span style={styles.ttDate}>{tooltipDate}</span>
          <span style={styles.ttRow}>
            <span style={{ ...styles.ttDot, backgroundColor: "var(--mp-accent)" }} />
            <span style={styles.ttLabel}>{primarySeriesLabel}</span>
            <span style={styles.ttValue}>{hoveredValue}</span>
          </span>
          {hoveredMaLabel && (
            <span style={styles.ttRow}>
              <span style={{ ...styles.ttDot, backgroundColor: "var(--mp-stale)" }} />
              <span style={styles.ttLabel}>{movingAverageTooltipLabel}</span>
              <span style={styles.ttValue}>{hoveredMaLabel}</span>
            </span>
          )}
        </div>
      )}

      {visibleMovingAveragePoints.some((p) => p.value != null) && (
        <div style={styles.legend} aria-hidden="true">
          <span style={styles.legendLine} />
          <span>{movingAverageLabel}</span>
        </div>
      )}
    </div>
  );
}

function clampTooltip(x: number, width: number): number {
  const half = 78;
  return Math.max(half, Math.min(width - half, x));
}

/** Stable-per-instance gradient id so multiple charts don't collide. */
function useGradientId(): string {
  const ref = useRef<string>("");
  if (!ref.current) ref.current = `mm-grad-${Math.random().toString(36).slice(2, 9)}`;
  return ref.current;
}

/* ── Styles ───────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  wrap: { position: "relative", width: "100%", minWidth: 0 },
  svg: { display: "block", width: "100%", cursor: "crosshair" },
  yTick: {
    position: "absolute", left: 0, fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)", fontFamily: "var(--mp-font-mono)",
    backgroundColor: "var(--mp-card)", padding: "0 3px", pointerEvents: "none",
  },
  xAxis: {
    display: "flex", justifyContent: "space-between", marginTop: 2,
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", fontFamily: "var(--mp-font-mono)",
  },
  legend: {
    display: "inline-flex", alignItems: "center", gap: 6, marginTop: 6,
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
  },
  legendLine: {
    width: 22, height: 0, borderTop: "3px solid var(--mp-stale)", flexShrink: 0,
  },
  emptyWrap: {
    width: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
    gap: 4, textAlign: "center", padding: "var(--space-4)",
    border: "1px dashed var(--mp-rule)", borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
  },
  emptyTitle: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", fontWeight: 700 },
  emptyText: { maxWidth: 360, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.45 },
  tooltip: {
    position: "absolute", transform: "translate(-50%, -100%)",
    display: "flex", flexDirection: "column", gap: 1,
    padding: "7px 9px", minWidth: 158,
    backgroundColor: "var(--mp-ink)", color: "var(--mp-card)",
    borderRadius: "var(--radius-sm)", pointerEvents: "none", zIndex: 5,
    boxShadow: "0 10px 24px rgba(15, 23, 42, 0.24)",
  },
  ttDate: { fontSize: "var(--font-size-xs)", color: "color-mix(in srgb, var(--mp-card) 76%, transparent)", fontFamily: "var(--mp-font-sans)" },
  ttRow: {
    display: "grid", gridTemplateColumns: "8px minmax(70px, 1fr) auto",
    alignItems: "center", gap: 5,
    fontSize: "var(--font-size-xs)", lineHeight: 1.25,
  },
  ttDot: { width: 7, height: 7, borderRadius: 999 },
  ttLabel: { color: "color-mix(in srgb, var(--mp-card) 82%, transparent)", whiteSpace: "nowrap" },
  ttValue: { color: "var(--mp-card)", fontWeight: 700, fontFamily: "var(--mp-font-mono)", textAlign: "right" },
};

function formatTooltipValue(
  v: number | null,
  fmt: MarketMoodAxisValueFormat,
  unit: string | null,
  neutral: boolean,
): string {
  if (v == null || !Number.isFinite(v)) return "—";
  if (neutral) {
    return new Intl.NumberFormat("en-US", {
      maximumFractionDigits: 2,
    }).format(v);
  }
  return formatAxisValue(v, fmt, unit);
}

function parseHistoryDateMs(date: string): number | null {
  const parsed = new Date(`${date}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed.getTime();
}

function formatTooltipDate(date: string): string {
  const parsed = new Date(`${date}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}
