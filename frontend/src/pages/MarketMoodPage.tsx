import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { Link } from "react-router-dom";
import { Badge, MpIcon, PageHeader } from "../components/shared/mp";
import { LoadingSkeleton, ErrorState, EmptyState } from "../components/shared/StateViews";
import { marketMoodApi } from "../api/marketMood";
import { ApiRequestError } from "../api/client";
import type {
  MarketMoodDetailRead,
  MarketMoodIndicatorRead,
  MarketMoodComparisonRead,
  MarketMoodRating,
  MarketMoodRefreshStatusRead,
  MarketMoodTrendPointRead,
  MarketMoodValueMeaning,
} from "../types/marketMood";
import { dataModeBadge, formatAxisValue, indicatorScaleCalibration } from "../components/market-context/marketMoodHelpers";
import MarketMoodIndicatorChart from "../components/market-context/MarketMoodIndicatorChart";

type LoadStatus = "idle" | "loading" | "success" | "error";
type RefreshIntent = "initial" | "background";

const MARKET_MOOD_BACKEND_CHECK_INTERVAL_MS = 15 * 60 * 1000;

function errMsg(err: unknown): string {
  if (err instanceof ApiRequestError) return err.detail;
  if (err instanceof Error) return err.message;
  return "Request failed.";
}

export default function MarketMoodPage() {
  const [status, setStatus] = useState<LoadStatus>("idle");
  const [data, setData] = useState<MarketMoodDetailRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [refreshStatus, setRefreshStatus] = useState<MarketMoodRefreshStatusRead | null>(null);
  const dataRef = useRef<MarketMoodDetailRead | null>(null);

  const load = useCallback(async (intent: RefreshIntent = "initial") => {
    if (intent === "initial" || !dataRef.current) {
      setStatus("loading");
      setError(null);
    }
    let nextRefreshStatus: MarketMoodRefreshStatusRead | null = null;
    try {
      try {
        nextRefreshStatus = await marketMoodApi.refresh();
        setRefreshStatus(nextRefreshStatus);
      } catch (refreshErr) {
        // Refresh failure should not block reading the latest backend detail.
        if (refreshErr instanceof ApiRequestError || refreshErr instanceof Error) {
          setRefreshStatus(null);
        }
      }
      const res = await marketMoodApi.detail();
      setData((prev) => {
        if (
          prev &&
          intent === "background" &&
          nextRefreshStatus?.status === "unchanged" &&
          prev.updated_at_utc === res.updated_at_utc &&
          prev.generated_at === res.generated_at
        ) {
          dataRef.current = prev;
          return prev;
        }
        dataRef.current = res;
        return res;
      });
      setStatus("success");
    } catch (err) {
      setError(errMsg(err));
      if (intent === "initial" || !dataRef.current) setStatus("error");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") void load("background");
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [load]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      if (document.visibilityState === "visible") void load("background");
    }, MARKET_MOOD_BACKEND_CHECK_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [load]);

  useEffect(() => {
    if (!data?.indicators.length) return;
    const selectedStillExists = selectedKey != null && data.indicators.some((ind) => ind.component_key === selectedKey);
    if (!selectedStillExists) setSelectedKey(data.indicators[0].component_key);
  }, [data, selectedKey]);

  const selectedIndicator = useMemo(() => {
    if (!data?.indicators.length) return null;
    return data.indicators.find((ind) => ind.component_key === selectedKey) ?? data.indicators[0];
  }, [data, selectedKey]);

  const badge = data ? dataModeBadge(data.data_mode) : null;
  const isUnavailable = status === "success" && data?.data_mode !== "provider_reference";

  return (
    <div className="mp-surface" style={styles.page}>
      <div style={styles.crumbRow}>
        <Link to="/" style={styles.crumb}>
          <MpIcon name="chevron-r" size={13} style={styles.backIcon} />
          Back to Overview
        </Link>
      </div>

      <PageHeader
        eyebrow="Workspace / market context"
        title="Market Mood"
        sub="Broad sentiment context from the Fear & Greed index and seven native-scale indicators."
        right={badge ? <Badge tone={badge.tone} dot title={badge.title}>{badge.label}</Badge> : undefined}
      />

      {status === "loading" && <LoadingSkeleton rows={8} label="Loading market mood detail..." />}

      {status === "error" && (
        <ErrorState message={error ?? "Failed to load market mood."} onRetry={() => { void load(); }} />
      )}

      {status === "success" && data && (
        isUnavailable ? (
          <EmptyState
            title="Market Mood unavailable"
            body={data.status_message ?? "No market sentiment snapshot is currently available."}
          />
        ) : (
          <>
            <OverallBand data={data} refreshStatus={refreshStatus} />

            <section style={styles.workbenchSection}>
              <div style={styles.sectionHead}>
                <div>
                  <h2 style={styles.sectionTitle}>Indicator Desk</h2>
                  <p style={styles.sectionSub}>Select an indicator to inspect its raw backend history.</p>
                </div>
                <span style={styles.sectionCount}>{data.indicators.length} indicators</span>
              </div>

              {data.indicators.length === 0 ? (
                <EmptyState title="No indicators" body="The current snapshot has no indicator detail." />
              ) : (
                <div style={styles.workbench}>
                  <div style={styles.indicatorRail} role="list" aria-label="Market Mood indicators">
                    {data.indicators.map((ind) => (
                      <IndicatorRailButton
                        key={ind.component_key}
                        ind={ind}
                        selected={ind.component_key === selectedIndicator?.component_key}
                        onSelect={() => setSelectedKey(ind.component_key)}
                      />
                    ))}
                  </div>

                  {selectedIndicator && <FocusedIndicatorPanel ind={selectedIndicator} />}
                </div>
              )}
            </section>
          </>
        )
      )}
    </div>
  );
}

function OverallBand({
  data,
  refreshStatus,
}: {
  data: MarketMoodDetailRead;
  refreshStatus: MarketMoodRefreshStatusRead | null;
}) {
  const scoreText = data.score_label ?? (data.score != null ? String(data.score) : "Unavailable");
  const visual = ratingVisualFor(data.rating);
  return (
    <section style={styles.hero}>
      <div style={styles.heroMain}>
        <div style={styles.heroTopRow}>
          <span style={styles.heroEyebrow}>Fear & Greed Index</span>
          <div style={styles.heroFresh}>
            <Badge tone={data.freshness_status === "fresh" ? "accent" : data.freshness_status === "stale" ? "stale" : "mute"} dot title={data.freshness_label}>
              {data.freshness_status}
            </Badge>
            <span style={styles.heroSource}>{sourceLabel(data)}</span>
          </div>
        </div>

        <div style={styles.heroScoreRow}>
          <span className="mp-mono" style={{ ...styles.heroScore, color: visual.fg }}>{scoreText}</span>
          <div style={styles.heroScoreMeta}>
            <span style={{ ...styles.heroRating, color: visual.fg }}>{data.rating_label}</span>
            <span style={styles.heroScale}>{data.score_min}-{data.score_max} sentiment index</span>
          </div>
        </div>

        <OverallMoodGauge
          score={data.score}
          scoreLabel={scoreText}
          rating={data.rating}
          ratingLabel={data.rating_label}
          min={data.score_min}
          max={data.score_max}
        />

        <div style={styles.heroBottomRow}>
          <span style={styles.heroFreshLabel}>{data.freshness_label}</span>
          {data.updated_at_label && <span style={styles.heroUpdated}>Updated {data.updated_at_label}</span>}
          {refreshStatus?.last_checked_at_label && (
            <span
              style={styles.heroChecked}
              title={refreshStatusLabel(refreshStatus)}
            >
              Checked {refreshStatus.last_checked_at_label}
            </span>
          )}
        </div>
      </div>

      <div style={styles.heroAside}>
        <div style={styles.asideHeader}>
          <MpIcon name="spark" size={15} />
          <span style={styles.asideTitle}>Recent path</span>
        </div>
        <OverallTrendChart points={data.trend_series} />
        <div style={styles.compList}>
          {data.comparisons.map((c) => (
            <ComparisonRow key={c.window} c={c} />
          ))}
          {data.comparisons.length === 0 && <span style={styles.compEmpty}>No comparison windows available.</span>}
        </div>
      </div>
    </section>
  );
}

function refreshStatusLabel(status: MarketMoodRefreshStatusRead): string {
  switch (status.status) {
    case "refreshed":
      return status.source_changed === false
        ? "Backend checked the source; source data was unchanged."
        : "Backend checked the source and refreshed the stored snapshot.";
    case "unchanged":
      return "Backend checked the source; source data was unchanged.";
    case "failed":
      return "Backend source check failed; latest backend detail is still shown when available.";
    default:
      return status.message;
  }
}

const GAUGE_ZONES: Array<{ rating: MarketMoodRating; label: string }> = [
  { rating: "extreme_fear", label: "Extreme Fear" },
  { rating: "fear", label: "Fear" },
  { rating: "neutral", label: "Neutral" },
  { rating: "greed", label: "Greed" },
  { rating: "extreme_greed", label: "Extreme Greed" },
];

function OverallMoodGauge({
  score,
  scoreLabel,
  rating,
  ratingLabel,
  min,
  max,
}: {
  score: number | null;
  scoreLabel: string;
  rating: MarketMoodRating;
  ratingLabel: string;
  min: number;
  max: number;
}) {
  const span = max - min;
  const pct =
    score == null || span <= 0
      ? null
      : Math.max(0, Math.min(100, ((score - min) / span) * 100));
  const visual = ratingVisualFor(rating);

  return (
    <div
      style={styles.gaugeWrap}
      role="img"
      aria-label={
        score == null
          ? "Fear and Greed gauge unavailable"
          : `Fear and Greed gauge, score ${scoreLabel}, rating ${ratingLabel}`
      }
    >
      <div style={styles.meterReadout}>
        <span className="mp-mono" style={{ ...styles.meterScore, color: score == null ? "var(--mp-mute)" : visual.fg }}>
          {score == null ? "Unavailable" : scoreLabel}
        </span>
        <span style={{ ...styles.meterRating, color: score == null ? "var(--mp-mute)" : visual.fg }}>
          {score == null ? "Score unavailable" : ratingLabel}
        </span>
      </div>

      <div style={styles.meterTrackWrap}>
        {pct != null && (
          <div style={{ ...styles.meterPointer, left: `${pct}%`, borderTopColor: visual.fg }} />
        )}
        <div style={styles.meterTrack}>
          {GAUGE_ZONES.map((zone) => {
            const zoneVisual = ratingVisualFor(zone.rating);
            return (
              <span
                key={zone.rating}
                style={{
                  ...styles.meterSegment,
                  backgroundColor: zoneVisual.fg,
                  boxShadow: `inset 0 0 0 1px ${zoneVisual.border}`,
                }}
              />
            );
          })}
        </div>
      </div>

      <div style={styles.meterLabels}>
        {GAUGE_ZONES.map((zone) => {
          const zoneVisual = ratingVisualFor(zone.rating);
          return (
            <span key={zone.rating} style={{ ...styles.meterLabel, color: zoneVisual.fg }}>
              {zone.label}
            </span>
          );
        })}
      </div>
      <div style={styles.meterScale}>
        <span>{min}</span>
        <span>{Math.round((min + max) / 2)}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

function OverallTrendChart({ points }: { points: MarketMoodTrendPointRead[] }) {
  const plotted = points.filter((p) => p.score != null && Number.isFinite(p.score));
  if (plotted.length < 2) {
    return (
      <div style={styles.overallEmpty}>
        <span style={styles.overallEmptyText}>Overall history unavailable.</span>
      </div>
    );
  }

  const width = 320;
  const height = 92;
  const padX = 8;
  const padY = 10;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;
  const coords = plotted.map((p, i) => {
    const score = p.score as number;
    const x = padX + (i / Math.max(1, plotted.length - 1)) * innerW;
    const y = padY + (1 - score / 100) * innerH;
    return { x, y };
  });
  const path = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Overall market mood history"
      style={styles.overallChart}
    >
      <line x1={padX} y1={padY} x2={width - padX} y2={padY} stroke="var(--mp-accent-line)" strokeWidth="1" strokeDasharray="2 4" />
      <line x1={padX} y1={height - padY} x2={width - padX} y2={height - padY} stroke="var(--mp-accent-line)" strokeWidth="1" />
      <path d={path} fill="none" stroke="var(--mp-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={coords[coords.length - 1].x} cy={coords[coords.length - 1].y} r="3.5" fill="var(--mp-card)" stroke="var(--mp-accent)" strokeWidth="2" />
    </svg>
  );
}

function ComparisonRow({ c }: { c: MarketMoodComparisonRead }) {
  const change = c.is_available ? scoreChangeLabel(c.change_label) : "insufficient history";
  return (
    <div style={styles.compRow}>
      <span style={styles.compWindow}>{windowLabel(c.window)}</span>
      <span className="mp-mono" style={styles.compPrior}>
        {c.is_available ? (c.prior_score_label ?? (c.prior_score != null ? String(c.prior_score) : "Unavailable")) : "Unavailable"}
      </span>
      <span style={styles.compChange}>{change}</span>
    </div>
  );
}

function scoreChangeLabel(label: string | null): string {
  if (!label) return "No change label";
  return `Change ${label.replace(/\s*points?$/i, "")}`;
}

function windowLabel(w: MarketMoodComparisonRead["window"]): string {
  switch (w) {
    case "1w": return "1 week";
    case "1m": return "1 month";
    case "1y": return "1 year";
    default: return w;
  }
}

function IndicatorRailButton({
  ind,
  selected,
  onSelect,
}: {
  ind: MarketMoodIndicatorRead;
  selected: boolean;
  onSelect: () => void;
}) {
  // Honest scale: if the live provider unit doesn't fit the value magnitude,
  // show a neutral raw number here too so the rail chip matches the focused panel.
  const currentValue = indicatorCurrentValue(ind, indicatorScaleCalibration(ind).neutral);
  const visual = ratingVisualFor(ind.current_rating);
  return (
    <button
      type="button"
      className="market-mood-rail-button"
      aria-pressed={selected}
      onClick={onSelect}
      onMouseUp={(event) => event.currentTarget.blur()}
      style={{
        ...styles.railButton,
        "--mood-rating-fg": visual.fg,
        "--mood-rating-bg": visual.bg,
        "--mood-rating-border": visual.border,
        backgroundColor: selected ? visual.bg : "var(--mp-card)",
        borderColor: selected ? visual.border : "var(--mp-rule)",
        boxShadow: selected ? `inset 3px 0 0 ${visual.fg}` : "none",
      } as CSSProperties}
    >
      <span style={styles.railBody}>
        <span style={styles.railTop}>
          <span style={styles.railName}>{ind.display_name}</span>
          <span className="mp-mono" style={styles.railValue}>{currentValue}</span>
        </span>
        <span style={styles.railBottom}>
          <span style={{ ...styles.railStatus, color: visual.fg }}>
            <span style={{ ...styles.railStatusDot, backgroundColor: visual.fg }} />
            {ind.current_rating_label}
          </span>
        </span>
      </span>
    </button>
  );
}

function FocusedIndicatorPanel({ ind }: { ind: MarketMoodIndicatorRead }) {
  // Frontend honesty calibration: when the live provider's unit/format doesn't
  // match the value scale, switch to a neutral "provider raw value" display.
  const calibration = indicatorScaleCalibration(ind);
  const currentValue = indicatorCurrentValue(ind, calibration.neutral);
  const showUnit = !calibration.neutral && !!ind.unit_label && !/[a-zA-Z%]/.test(currentValue);
  const normalized =
    ind.current_score_label != null
      ? `Index ${ind.current_score_label}/100 - ${ind.current_rating_label}`
      : ind.current_rating_label;
  const ariaLabel =
    `${ind.display_name} raw-value history${ind.history.length ? `, latest ${currentValue}` : ", no plotted history"}`;

  return (
    <article style={styles.focusPanel}>
      <header style={styles.focusHeader}>
        <div style={styles.focusTitleBlock}>
          <span style={styles.focusKicker}>Selected indicator</span>
          <div style={styles.focusTitleRow}>
            <h3 style={styles.focusTitle}>{ind.display_name}</h3>
            <IndicatorInfoPopover ind={ind} calibrationReason={calibration.reason} />
          </div>
          <p style={styles.focusSub}>{ind.subtitle}</p>
        </div>
        <div style={styles.focusBadges}>
          <RatingPill rating={ind.current_rating} label={ind.current_rating_label} />
        </div>
      </header>

      <div style={styles.focusMetricRow}>
        <div style={styles.focusMetric}>
          <span style={styles.metricLabel}>Current raw value</span>
          <span style={styles.metricValueLine}>
            <span className="mp-mono" style={styles.focusValue}>{currentValue}</span>
            {showUnit && <span style={styles.cardUnit}>{ind.unit_label}</span>}
          </span>
        </div>
        <div style={styles.focusMetric}>
          <span style={styles.metricLabel}>Normalized sentiment</span>
          <span style={styles.metricText}>{normalized}</span>
        </div>
      </div>

      <MarketMoodIndicatorChart
        history={ind.history}
        axisValueFormat={ind.axis_value_format}
        unitLabel={ind.unit_label}
        ariaLabel={ariaLabel}
        height={248}
        neutralScale={calibration.neutral}
        movingAverageWindow={ind.component_key === "market_momentum" ? 125 : undefined}
        movingAverageLabel="125-day moving average"
        movingAverageTooltipLabel="125-day MA"
        primarySeriesLabel={ind.component_key === "market_momentum" ? "S&P 500" : ind.display_name}
      />

      <div style={styles.focusMetaGrid}>
        <MetaBlock
          label="Axis"
          value={calibration.neutral ? "Provider raw value" : (ind.axis_label ?? "Axis label unavailable")}
        />
        <MetaBlock
          label="Value direction"
          value={`Higher: ${meaningLabel(ind.higher_value_meaning)} / Lower: ${meaningLabel(ind.lower_value_meaning)}`}
        />
      </div>

      {calibration.reason && (
        <p style={styles.calibrationNote}>{calibration.reason}</p>
      )}
    </article>
  );
}

function IndicatorInfoPopover({
  ind,
  calibrationReason,
}: {
  ind: MarketMoodIndicatorRead;
  calibrationReason: string | null;
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLSpanElement | null>(null);
  const axis = calibrationReason ? "Provider raw value" : (ind.axis_label ?? "Axis label unavailable");

  useEffect(() => {
    if (!open) return undefined;
    const onMove = (event: MouseEvent) => {
      const target = event.target;
      if (target instanceof Node && wrapRef.current?.contains(target)) return;
      setOpen(false);
    };
    document.addEventListener("mousemove", onMove);
    return () => document.removeEventListener("mousemove", onMove);
  }, [open]);

  return (
    <span
      ref={wrapRef}
      className="market-mood-info-wrap"
      style={styles.infoDetails}
      onMouseEnter={() => setOpen(true)}
      onMouseMove={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onPointerMove={() => setOpen(true)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      <button
        type="button"
        className="market-mood-info-summary"
        style={styles.infoSummary}
        aria-label={`${ind.display_name} explanation`}
        title={`${ind.display_name} explanation`}
        onMouseUp={(event) => event.currentTarget.blur()}
      >
        <MpIcon name="info" size={15} />
      </button>
      <span
        className="market-mood-info-popover"
        style={{
          ...styles.infoPopover,
          opacity: open ? 1 : 0,
          visibility: open ? "visible" : "hidden",
          transform: open ? "translateY(0)" : "translateY(-4px)",
        }}
        role="tooltip"
      >
        <span style={styles.infoTitle}>{ind.display_name}</span>
        <span style={styles.infoText}>{ind.description}</span>
        <span style={styles.infoMeta}>Axis: {axis}</span>
        <span style={styles.infoMeta}>
          Higher: {meaningLabel(ind.higher_value_meaning)} / Lower: {meaningLabel(ind.lower_value_meaning)}
        </span>
      </span>
    </span>
  );
}

function RatingPill({ rating, label }: { rating: MarketMoodRating; label: string }) {
  const visual = ratingVisualFor(rating);
  return (
    <span
      style={{
        ...styles.ratingPill,
        color: visual.fg,
        backgroundColor: visual.bg,
        borderColor: visual.border,
      }}
    >
      <span style={{ ...styles.ratingDot, backgroundColor: visual.fg }} />
      {label}
    </span>
  );
}

function MetaBlock({ label, value }: { label: string; value: string }) {
  return (
    <div style={styles.metaBlock}>
      <span style={styles.metaLabel}>{label}</span>
      <span style={styles.metaValue}>{value}</span>
    </div>
  );
}

function indicatorCurrentValue(ind: MarketMoodIndicatorRead, neutral = false): string {
  // When the calibration layer flags this indicator's scale as uncertain,
  // bypass the backend `current_value_label` (which carries the misleading
  // unit, e.g. "7553.7%") and re-format the raw number as a plain provider
  // value. Otherwise prefer the backend-provided label verbatim.
  if (neutral) {
    return formatAxisValue(ind.current_value, ind.axis_value_format, ind.unit_label, { neutral: true });
  }
  return ind.current_value_label ?? formatAxisValue(ind.current_value, ind.axis_value_format, ind.unit_label);
}

function meaningLabel(m: MarketMoodValueMeaning): string {
  switch (m) {
    case "fear": return "fear";
    case "greed": return "greed";
    case "neutral_or_contextual": return "neutral or contextual";
    case "unknown": return "unknown";
    default: return "unknown";
  }
}

function ratingVisualFor(rating: MarketMoodRating): { fg: string; bg: string; border: string } {
  switch (rating) {
    case "extreme_fear":
      return { fg: "var(--mp-block)", bg: "var(--mp-block-soft)", border: "rgba(248, 113, 113, 0.34)" };
    case "fear":
      return { fg: "var(--mp-stale)", bg: "var(--mp-stale-soft)", border: "rgba(251, 191, 36, 0.32)" };
    case "neutral":
      return { fg: "var(--mp-mute)", bg: "var(--mp-paper-2)", border: "var(--mp-rule-strong)" };
    case "greed":
      return { fg: "var(--mp-info)", bg: "var(--mp-info-soft)", border: "rgba(96, 165, 250, 0.30)" };
    case "extreme_greed":
      return { fg: "var(--mp-live)", bg: "var(--mp-live-soft)", border: "rgba(52, 211, 153, 0.32)" };
    case "unknown":
    default:
      return { fg: "var(--mp-mute)", bg: "var(--mp-paper-2)", border: "var(--mp-rule)" };
  }
}

function sourceLabel(data: MarketMoodDetailRead): string {
  if (/cnn/i.test(data.source_label)) return "CNN-derived Fear & Greed Index";
  return data.source_label;
}

const styles: Record<string, CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-5)",
    maxWidth: 1320,
    margin: "0 auto",
    color: "var(--mp-ink)",
  },
  crumbRow: { display: "flex", marginBottom: "calc(-1 * var(--space-3))" },
  crumb: {
    display: "inline-flex",
    alignItems: "center",
    gap: "var(--space-1)",
    color: "var(--mp-mute)",
    textDecoration: "none",
    fontSize: "var(--font-size-xs)",
    fontWeight: 600,
  },
  backIcon: { transform: "rotate(180deg)" },

  hero: {
    display: "grid",
    gridTemplateColumns: "minmax(0, 2fr) minmax(280px, 0.9fr)",
    gap: "var(--space-5)",
    padding: "var(--space-6)",
    background:
      "linear-gradient(135deg, var(--mp-accent-soft), transparent 42%), linear-gradient(180deg, var(--mp-card), var(--mp-card-2))",
    border: "1px solid var(--mp-accent-line)",
    borderRadius: "var(--radius-md)",
    boxShadow: "var(--mp-shadow-md)",
    minWidth: 0,
  },
  heroMain: { display: "flex", flexDirection: "column", gap: "var(--space-3)", minWidth: 0 },
  heroTopRow: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap" },
  heroEyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700 },
  heroFresh: { display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" },
  heroSource: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  heroScoreRow: { display: "flex", alignItems: "baseline", gap: "var(--space-4)", flexWrap: "wrap" },
  heroScore: { fontSize: 68, fontWeight: 700, color: "var(--mp-ink)", lineHeight: 0.95, letterSpacing: 0 },
  heroScoreMeta: { display: "flex", flexDirection: "column", gap: 2 },
  heroRating: { fontSize: "var(--font-size-xl)", fontWeight: 700, color: "var(--mp-info)", textTransform: "uppercase", letterSpacing: "0.04em", lineHeight: 1.1 },
  heroScale: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  gaugeWrap: {
    width: "100%",
    minWidth: 0,
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    padding: "var(--space-3) 0 var(--space-1)",
  },
  meterReadout: {
    display: "flex",
    alignItems: "baseline",
    justifyContent: "space-between",
    gap: "var(--space-3)",
    flexWrap: "wrap",
  },
  meterScore: { fontSize: 30, fontWeight: 700, lineHeight: 1 },
  meterRating: { fontSize: "var(--font-size-sm)", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.06em" },
  meterTrackWrap: {
    position: "relative",
    paddingTop: 18,
    width: "100%",
  },
  meterTrack: {
    display: "grid",
    gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
    gap: 3,
    height: 18,
    padding: 3,
    backgroundColor: "var(--mp-paper-2)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    boxShadow: "inset 0 1px 2px rgba(0,0,0,0.18)",
  },
  meterSegment: { borderRadius: 3, minWidth: 0 },
  meterPointer: {
    position: "absolute",
    top: 0,
    width: 0,
    height: 0,
    borderLeft: "7px solid transparent",
    borderRight: "7px solid transparent",
    borderTop: "12px solid var(--mp-ink)",
    transform: "translateX(-50%)",
    filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.24))",
  },
  meterLabels: {
    display: "grid",
    gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
    gap: "var(--space-1)",
  },
  meterLabel: {
    minWidth: 0,
    fontSize: "var(--font-size-xs)",
    fontWeight: 800,
    lineHeight: 1.25,
    textAlign: "center",
    textTransform: "uppercase",
    letterSpacing: "0.03em",
  },
  meterScale: {
    display: "flex",
    justifyContent: "space-between",
    color: "var(--mp-mute)",
    fontFamily: "var(--mp-font-mono)",
    fontSize: "var(--font-size-xs)",
  },
  heroBottomRow: { display: "flex", justifyContent: "space-between", gap: "var(--space-3)", flexWrap: "wrap" },
  heroFreshLabel: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  heroUpdated: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  heroChecked: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  heroAside: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    paddingLeft: "var(--space-5)",
    borderLeft: "1px solid var(--mp-accent-line)",
    minWidth: 0,
  },
  asideHeader: { display: "flex", alignItems: "center", gap: "var(--space-2)", color: "var(--mp-accent)" },
  asideTitle: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 700 },
  overallChart: { display: "block", width: "100%", height: 92, overflow: "visible" },
  overallEmpty: {
    height: 92,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    border: "1px dashed var(--mp-accent-line)",
    borderRadius: "var(--radius-sm)",
  },
  overallEmptyText: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  compList: { display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  compRow: { display: "grid", gridTemplateColumns: "70px auto minmax(0, 1fr)", alignItems: "baseline", gap: "var(--space-2)" },
  compWindow: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)" },
  compPrior: { fontSize: "var(--font-size-md)", fontWeight: 700, color: "var(--mp-ink)" },
  compChange: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textAlign: "right", minWidth: 0 },
  compEmpty: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },

  workbenchSection: { display: "flex", flexDirection: "column", gap: "var(--space-3)", minWidth: 0 },
  sectionHead: { display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "var(--space-3)", flexWrap: "wrap" },
  sectionTitle: { margin: 0, fontFamily: "var(--mp-font-display)", fontSize: "var(--font-size-lg)", fontWeight: 600, color: "var(--mp-ink)" },
  sectionSub: { margin: "2px 0 0", fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.45 },
  sectionCount: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em" },
  workbench: {
    display: "grid",
    gridTemplateColumns: "minmax(260px, 330px) minmax(0, 1fr)",
    gap: "var(--space-4)",
    alignItems: "stretch",
    minWidth: 0,
  },
  indicatorRail: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  railButton: {
    appearance: "none",
    width: "100%",
    display: "grid",
    gridTemplateColumns: "minmax(0, 1fr)",
    alignItems: "center",
    padding: "var(--space-3)",
    textAlign: "left",
    color: "var(--mp-ink)",
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    cursor: "pointer",
    outline: "none",
  },
  railButtonSelected: {
    backgroundColor: "var(--mood-rating-bg)",
    borderColor: "var(--mood-rating-border)",
    boxShadow: "inset 3px 0 0 var(--mood-rating-fg)",
  },
  railBody: { display: "flex", flexDirection: "column", gap: 4, minWidth: 0 },
  railTop: { display: "flex", justifyContent: "space-between", gap: "var(--space-2)", minWidth: 0 },
  railName: { fontSize: "var(--font-size-sm)", fontWeight: 700, color: "var(--mp-ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  railValue: { fontSize: "var(--font-size-sm)", fontWeight: 700, color: "var(--mp-ink-2)", flexShrink: 0 },
  railBottom: { display: "flex", justifyContent: "space-between", gap: "var(--space-2)", fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  railStatus: { display: "inline-flex", alignItems: "center", gap: 5, fontWeight: 700 },
  railStatusDot: { width: 6, height: 6, borderRadius: 999, flexShrink: 0 },

  focusPanel: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-4)",
    padding: "var(--space-5)",
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    boxShadow: "var(--mp-shadow-sm)",
    minWidth: 0,
  },
  focusHeader: { display: "flex", justifyContent: "space-between", gap: "var(--space-3)", alignItems: "flex-start", flexWrap: "wrap" },
  focusTitleBlock: { display: "flex", flexDirection: "column", gap: 2, minWidth: 0 },
  focusKicker: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 700 },
  focusTitleRow: { display: "flex", alignItems: "center", gap: "var(--space-2)", minWidth: 0 },
  focusTitle: { margin: 0, fontFamily: "var(--mp-font-display)", fontSize: 30, fontWeight: 500, color: "var(--mp-ink)", lineHeight: 1.08, letterSpacing: 0 },
  focusSub: { margin: 0, fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", lineHeight: 1.45 },
  focusBadges: { display: "flex", gap: "var(--space-1)", flexWrap: "wrap", justifyContent: "flex-end" },
  ratingPill: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "5px 8px",
    border: "1px solid",
    borderRadius: "var(--radius-sm)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
    whiteSpace: "nowrap",
  },
  ratingDot: { width: 6, height: 6, borderRadius: 999, flexShrink: 0 },
  infoDetails: {
    position: "relative",
    display: "inline-flex",
    color: "var(--mp-mute)",
    flexShrink: 0,
  },
  infoSummary: {
    appearance: "none",
    width: 26,
    height: 26,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
    color: "var(--mp-mute)",
    cursor: "pointer",
    outline: "none",
    listStyle: "none",
  },
  infoPopover: {
    position: "absolute",
    top: "calc(100% + var(--space-2))",
    left: 0,
    zIndex: 10,
    width: 340,
    maxWidth: "min(76vw, 360px)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
    padding: "var(--space-1) 0 0",
    backgroundColor: "transparent",
    border: 0,
    borderRadius: 0,
    boxShadow: "none",
    color: "var(--mp-ink)",
  },
  infoTitle: { fontSize: "var(--font-size-sm)", fontWeight: 700, color: "var(--mp-ink)" },
  infoText: { fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)", lineHeight: 1.5 },
  infoMeta: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.45 },
  focusMetricRow: { display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)", gap: "var(--space-3)" },
  focusMetric: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    padding: "var(--space-3)",
    backgroundColor: "var(--mp-paper-2)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    minWidth: 0,
  },
  metricLabel: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.06em" },
  metricValueLine: { display: "flex", alignItems: "baseline", gap: "var(--space-2)", minWidth: 0 },
  focusValue: { fontSize: "var(--font-size-2xl)", fontWeight: 700, color: "var(--mp-ink)", lineHeight: 1 },
  cardUnit: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  metricText: { fontSize: "var(--font-size-md)", color: "var(--mp-ink-2)", fontWeight: 700 },
  focusMetaGrid: { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "var(--space-3)" },
  metaBlock: { display: "flex", flexDirection: "column", gap: 3, minWidth: 0 },
  metaLabel: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.06em" },
  metaValue: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.4 },
  calibrationNote: {
    margin: 0, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    lineHeight: 1.5, fontStyle: "italic",
  },
};
