import type { MpTone } from "../shared/mp";
import type {
  MarketMoodRead,
  MarketMoodAxisValueFormat,
  MarketMoodIndicatorRead,
} from "../../types/marketMood";

/**
 * Tiny pure helpers for Market Mood surfaces. Kept in a non-tsx file so the
 * companion `marketMoodVisuals.tsx` module exports only components and is
 * compatible with Vite's React Fast Refresh boundary rules.
 *
 * Pure presentation only: no parsing, no comparison, no computation beyond a
 * deterministic data-mode-to-badge mapping.
 */
export function dataModeBadge(mode: MarketMoodRead["data_mode"]): { tone: MpTone; label: string; title: string } {
  switch (mode) {
    case "provider_reference":
      return { tone: "info", label: "Provider reference", title: "Backend provider-reference snapshot" };
    case "synthetic":
      return { tone: "mute", label: "Unavailable", title: "Market Mood provider-reference snapshot unavailable" };
    case "unavailable":
      return { tone: "mute", label: "Unavailable", title: "Market Mood snapshot unavailable" };
    default:
      return { tone: "mute", label: mode, title: mode };
  }
}

/**
 * Light display formatting of a raw indicator value, keyed off the backend
 * `axis_value_format`. Presentational only — it formats a number the backend
 * already provided (it never derives, compares, or computes a new value).
 *
 * `neutral` strips fmt-specific suffixes (no "%", no "$", no unit). It's used
 * when the live provider's declared unit/format doesn't match the magnitude of
 * the values it actually emits (e.g. an "index"-shaped number labelled "%"),
 * where forcing a unit would be misleading.
 */
export function formatAxisValue(
  v: number | null,
  fmt: MarketMoodAxisValueFormat,
  unit: string | null,
  opts: { neutral?: boolean } = {},
): string {
  if (v == null || !Number.isFinite(v)) return "—";
  const rounded = Math.round(v * 100) / 100;
  const n = String(rounded);
  if (opts.neutral) return n;
  switch (fmt) {
    case "percent": return `${n}%`;
    case "currency": return `$${n}`;
    case "ratio":
    case "spread":
    case "index":
    case "number":
      return n;
    default:
      return unit ? `${n} ${unit}` : n;
  }
}

/**
 * Detect when an indicator's live raw values clearly don't match the declared
 * `axis_value_format`/`unit_label`, so the page can fall back to neutral
 * "provider value" rendering instead of imposing a misleading unit.
 *
 * Frontend-only honesty layer: it never alters or fabricates values. It just
 * decides whether to PRINT the unit suffix on this snapshot. The heuristics
 * intentionally only suppress clearly-implausible unit combinations.
 *
 * Returns `{ neutral, reason }` where:
 *   - `neutral=true` means "render values without the declared unit/format
 *     suffix; show a small caption explaining native scale is uncertain".
 *   - `reason` is a short user-facing phrase suitable for a caption.
 */
export function indicatorScaleCalibration(ind: MarketMoodIndicatorRead): {
  neutral: boolean;
  reason: string | null;
} {
  const sample =
    ind.current_value != null && Number.isFinite(ind.current_value)
      ? ind.current_value
      : ind.history.find((p) => p.value != null && Number.isFinite(p.value as number))?.value ?? null;
  if (sample == null) return { neutral: false, reason: null };
  const abs = Math.abs(sample);

  // Provider "percent" with values far outside any plausible percent range
  // (CNN-derived index-level numbers came through as "7553.7%"). 150 is a
  // generous ceiling — any healthy percent indicator is well below it.
  if (ind.axis_value_format === "percent" && abs > 150) {
    return { neutral: true, reason: "Native scale uncertain — provider raw value shown." };
  }

  // Provider "spread" labelled in basis points but emitted as small unitless
  // numbers (e.g. value 3.77 labelled "4 bps", or 1.46 labelled "1 bps").
  // Real bp spreads are typically 5+; values below 10 strongly imply the
  // unit is not actually basis points.
  if (
    ind.axis_value_format === "spread" &&
    (ind.unit_label ?? "").toLowerCase().includes("bp") &&
    abs < 10
  ) {
    return { neutral: true, reason: "Native scale uncertain — provider raw value shown." };
  }

  return { neutral: false, reason: null };
}
