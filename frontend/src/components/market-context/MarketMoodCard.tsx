import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Panel } from "../shared/mp";
import { LoadingSkeleton, ErrorState, EmptyState } from "../shared/StateViews";
import { marketMoodApi } from "../../api/marketMood";
import { ApiRequestError } from "../../api/client";
import type { MarketMoodRead } from "../../types/marketMood";
import { SpectrumRamp } from "./marketMoodVisuals";
import { dataModeBadge } from "./marketMoodHelpers";

/**
 * MarketMoodCard — compact, glanceable secondary Dashboard card (P26A-T2).
 *
 * Backend-backed via the reviewed Phase 26A contract:
 *   GET /api/market-context/market-mood
 *
 * Hierarchy: header (title + compact data-mode badge) → hero (large score +
 * rating) → 0–100 gradient spectrum ramp with a marker → one quiet footer
 * line (compact source label only; generic safety boundaries live in the
 * product disclaimers, not per-card). Components, trend, and comparisons are
 * deferred to the P26A-T3 detail page.
 *
 * Safety:
 *   - Broad market sentiment context only — not a trading signal / not an
 *     actionability input / not a risk-rule input (backend invariants).
 *   - All display labels render verbatim; the numeric score is used ONLY for
 *     presentational marker placement on the 0–100 ramp. The frontend never
 *     parses, compares, computes, or derives trading meaning.
 *   - No CNN logo/branding/visual clone, no refresh control, no drilldown,
 *     no agent/LLM use, no external provider call, no storage writes.
 */

type LoadStatus = "idle" | "loading" | "success" | "error";

function errMsg(err: unknown): string {
  if (err instanceof ApiRequestError) return err.detail;
  if (err instanceof Error) return err.message;
  return "Request failed.";
}

export default function MarketMoodCard() {
  const [status, setStatus] = useState<LoadStatus>("idle");
  const [data, setData] = useState<MarketMoodRead | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    setError(null);
    try {
      const res = await marketMoodApi.get();
      setData(res);
      setStatus("success");
    } catch (err) {
      setError(errMsg(err));
      setStatus("error");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const isUnavailable = status === "success" && data?.data_mode !== "provider_reference";
  const badge = data ? dataModeBadge(data.data_mode) : null;

  // Tag is rendered with a freshness title attribute (tooltip) instead of an
  // always-visible timestamp line, to keep the card glanceable.
  const tagTooltip = data
    ? [data.freshness_label, data.updated_at_label ? `Updated ${data.updated_at_label}` : null]
        .filter(Boolean)
        .join(" · ")
    : undefined;

  return (
    <Panel
      title="Market Mood"
      tag="market context"
      right={
        <div style={styles.headerRight}>
          {badge && (
            <Badge tone={badge.tone} dot title={badge.title}>{badge.label}</Badge>
          )}
          <Link to="/market-context/market-mood" style={styles.detailsLink}>
            Details →
          </Link>
        </div>
      }
    >
      {status === "loading" && <LoadingSkeleton rows={3} label="Loading market mood…" />}

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
            <Hero data={data} />
            <SpectrumRamp score={data.score} min={data.score_min} max={data.score_max} />
            <Footer data={data} freshnessTooltip={tagTooltip} />
          </>
        )
      )}
    </Panel>
  );
}

/* ── Hero: score + rating ──────────────────────────────────────────────── */

function Hero({ data }: { data: MarketMoodRead }) {
  const scoreText = data.score_label ?? (data.score != null ? String(data.score) : "—");
  return (
    <div style={styles.hero}>
      <span className="mp-mono" style={styles.score}>{scoreText}</span>
      <span style={styles.rating}>{data.rating_label}</span>
    </div>
  );
}

/* ── Footer: compact source label only ──────────────────────────────────── */

function Footer({ data, freshnessTooltip }: { data: MarketMoodRead; freshnessTooltip?: string }) {
  // One quiet line — compact source label only. Generic safety boundaries
  // (analysis-only, not a trading signal, not affiliated, internal demo) are
  // covered by the product disclaimers, not repeated on every Dashboard card.
  return (
    <p style={styles.footer} title={freshnessTooltip}>
      {compactSourceLabel(data)}
    </p>
  );
}

/** Short, neutral source attribution. Backend `source_label` verbatim for
 *  non-CNN sources; a compact phrase for CNN-derived data (no logo, no clone). */
function compactSourceLabel(data: MarketMoodRead): string {
  if (/cnn/i.test(data.source_label)) return "CNN-derived Fear & Greed Index";
  return data.source_label;
}

/* ── Styles ───────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  hero: {
    display: "flex", alignItems: "baseline", gap: "var(--space-3)", flexWrap: "wrap",
    minWidth: 0,
  },
  score: {
    fontSize: "var(--font-size-2xl)", fontWeight: 700, color: "var(--mp-ink)",
    lineHeight: 1, letterSpacing: "-0.01em",
  },
  rating: {
    fontSize: "var(--font-size-md)", fontWeight: 600, color: "var(--mp-info)",
    textTransform: "uppercase", letterSpacing: "0.06em", lineHeight: 1.2,
  },

  headerRight: { display: "flex", alignItems: "center", gap: "var(--space-2)" },
  detailsLink: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-accent)", textDecoration: "none",
    fontWeight: 600,
  },

  footer: {
    margin: 0, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    lineHeight: 1.5, overflowWrap: "anywhere",
  },
};
