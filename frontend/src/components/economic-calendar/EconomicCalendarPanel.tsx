import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, MpIcon, Panel, type MpTone } from "../shared/mp";
import { LoadingSkeleton, ErrorState, EmptyState } from "../shared/StateViews";
import { economicCalendarApi } from "../../api/economicCalendar";
import { ApiRequestError } from "../../api/client";
import EconomicCalendarRangePicker from "./EconomicCalendarRangePicker";
import type {
  EconomicCalendarEventListRead,
  EconomicCalendarEventRead,
  EconomicEventImportance,
  EconomicEventImportanceSource,
} from "../../types/economicCalendar";

/**
 * EconomicCalendarPanel — Dashboard US macro economic-awareness panel
 * (Phase 24A, P24A-T9 table polish + range-calendar revision).
 *
 * Backend-backed via the reviewed Phase 24A contract:
 *   GET  /api/economic-calendar/events?start_date=…&end_date=…
 *   POST /api/economic-calendar/refresh   (manual control only)
 *
 * Compact US macro calendar: a single dual-month range picker (≤7 days),
 * browser-local event times (AM/PM), a leading Date column, chronological
 * (date-then-time) ordering, and rows zebra-grouped by calendar date.
 *
 * Safety:
 *   - Economic awareness only. "Not a trading signal" is always visible.
 *   - actual/forecast/previous render backend labels verbatim. The frontend
 *     never parses, compares, color-codes by value, or computes anything from
 *     them. Row order is neutral chronological ordering by the backend-provided
 *     `event_datetime_utc` instant — NOT ranking by importance or outcome.
 *   - Date/time columns only *format* the backend `event_datetime_utc` instant
 *     into the browser timezone; when it is null we fall back to the backend
 *     date/time labels and never fabricate a conversion.
 *   - Row background encodes calendar date only (zebra by date group); it never
 *     encodes value, surprise, or outcome. Past events carry a text "past"
 *     marker so occurrence is never conveyed by color alone.
 *   - Importance is a text-labelled badge (never color-only) and never implies
 *     trading urgency. US-only filtering is backend-owned; no frontend
 *     country/currency filtering.
 *   - Read endpoint loads on mount (current day); the provider is only contacted
 *     via the manual refresh control — never automatically, never in a loop.
 *   - Frontend consumes the backend only; no provider calls or API keys in
 *     React. No storage writes. Failures stay local to this panel.
 */

type LoadStatus = "idle" | "loading" | "success" | "error";

function errMsg(err: unknown): string {
  if (err instanceof ApiRequestError) return err.detail;
  if (err instanceof Error) return err.message;
  return "Request failed.";
}

/** Browser-local today as an ISO YYYY-MM-DD string. */
function todayLocalISO(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Local calendar date (ISO) for an event, from its UTC instant or date label. */
function localDateKey(ev: EconomicCalendarEventRead): string {
  if (ev.event_datetime_utc) {
    const d = new Date(ev.event_datetime_utc);
    if (!Number.isNaN(d.getTime())) {
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    }
  }
  return ev.event_date_label || "—";
}

/** Format a backend UTC instant into browser-local time with AM/PM. */
function formatLocalTime(utc: string | null, fallback: string): string {
  if (!utc) return fallback || "—";
  const d = new Date(utc);
  if (Number.isNaN(d.getTime())) return fallback || "—";
  return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit", hour12: true });
}

/** Format a browser-local weekday + date label for the Date column. */
function formatLocalDate(ev: EconomicCalendarEventRead): string {
  if (ev.event_datetime_utc) {
    const d = new Date(ev.event_datetime_utc);
    if (!Number.isNaN(d.getTime())) {
      return d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
    }
  }
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(ev.event_date_label || "");
  if (m) {
    return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
      .toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
  }
  return ev.event_date_label || "—";
}

/** Neutral chronological sort key (date then time) from backend timing fields. */
function eventSortKey(ev: EconomicCalendarEventRead): number {
  if (ev.event_datetime_utc) {
    const t = Date.parse(ev.event_datetime_utc);
    if (!Number.isNaN(t)) return t;
  }
  const dateMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(ev.event_date_label || "");
  if (dateMatch) {
    const base = Date.parse(`${ev.event_date_label}T00:00:00Z`);
    if (!Number.isNaN(base)) {
      const tm = /^(\d{1,2}):(\d{2})/.exec(ev.event_time_label || "");
      const offset = tm ? (Number(tm[1]) * 60 + Number(tm[2])) * 60_000 : 0;
      return base + offset;
    }
  }
  return Number.MAX_SAFE_INTEGER; // unknown-timed events sort last
}

export default function EconomicCalendarPanel() {
  const [startDate, setStartDate] = useState(todayLocalISO);
  const [endDate, setEndDate] = useState(todayLocalISO);

  const [status, setStatus] = useState<LoadStatus>("idle");
  const [data, setData] = useState<EconomicCalendarEventListRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  const load = useCallback(async (start: string, end: string) => {
    setStatus("loading");
    setError(null);
    try {
      const res = await economicCalendarApi.events({ startDate: start, endDate: end });
      setData(res);
      setStatus("success");
    } catch (err) {
      setError(errMsg(err));
      setStatus("error");
    }
  }, []);

  // On mount (incl. page refresh): always show the current day.
  useEffect(() => {
    const t = todayLocalISO();
    setStartDate(t);
    setEndDate(t);
    void load(t, t);
  }, [load]);

  // Apply a window chosen from the range picker.
  const applyRange = useCallback((start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
    void load(start, end);
  }, [load]);

  // Jump to today from the picker (no provider refresh).
  const resetToToday = useCallback(() => {
    const t = todayLocalISO();
    setStartDate(t);
    setEndDate(t);
    void load(t, t);
  }, [load]);

  // Manual refresh: ask the backend to refresh, then snap back to the current day.
  const refreshToToday = useCallback(async () => {
    const t = todayLocalISO();
    setStartDate(t);
    setEndDate(t);
    setIsRefreshing(true);
    setRefreshMessage(null);
    try {
      const refresh = await economicCalendarApi.refresh();
      if (refresh.status === "failed") setRefreshMessage(refresh.message);
    } catch (err) {
      setRefreshMessage(errMsg(err));
    } finally {
      setIsRefreshing(false);
    }
    await load(t, t);
  }, [load]);

  const isUnavailable = status === "success" && data?.data_mode === "unavailable";
  const isDemo =
    status === "success" && !!data && (data.data_mode === "synthetic" || !!data.demo_notice);

  // Chronological ordering + date-group index for zebra coloring.
  const sortedItems = useMemo(
    () => (data ? [...data.items].sort((a, b) => eventSortKey(a) - eventSortKey(b)) : []),
    [data],
  );
  const groupIndexByDate = useMemo(() => {
    const map = new Map<string, number>();
    for (const ev of sortedItems) {
      const key = localDateKey(ev);
      if (!map.has(key)) map.set(key, map.size);
    }
    return map;
  }, [sortedItems]);

  return (
    <Panel
      title="Economic awareness"
      tag="US macro"
      right={
        <div style={styles.headerActions}>
          {isDemo && (
            <Badge
              tone="mute"
              dot
              title="Synthetic fixture data from the backend — the live economic-calendar provider is not connected in this environment"
            >
              Synthetic data
            </Badge>
          )}
          <button
            type="button"
            onClick={() => { void refreshToToday(); }}
            disabled={isRefreshing}
            aria-label="Refresh and show today"
            title="Refresh and show today"
            style={{
              ...styles.refreshBtn,
              opacity: isRefreshing ? 0.62 : 1,
              cursor: isRefreshing ? "wait" : "pointer",
            }}
          >
            <MpIcon name="refresh" size={14} />
            <span>{isRefreshing ? "Refreshing" : "Refresh"}</span>
          </button>
        </div>
      }
    >
      {/* Compact economic-awareness / not-a-trading-signal line */}
      <div style={styles.awarenessRow}>
        <MpIcon name="info" size={13} style={{ color: "var(--mp-mute)", flexShrink: 0, marginTop: 1 }} />
        <span style={styles.awarenessText}>Economic awareness only · Not a trading signal.</span>
      </div>

      {/* Single dual-month range picker (today default, ≤7 days) */}
      <div style={styles.pickerRow}>
        <EconomicCalendarRangePicker
          start={startDate}
          end={endDate}
          onApply={applyRange}
          onResetToday={resetToToday}
        />
      </div>
      {refreshMessage && <div style={styles.refreshNotice}>{refreshMessage}</div>}

      {status === "loading" && <LoadingSkeleton rows={4} label="Loading economic calendar…" />}

      {status === "error" && (
        <ErrorState
          message={error ?? "Failed to load economic calendar."}
          onRetry={() => { void load(startDate, endDate); }}
        />
      )}

      {status === "success" && data && (
        <>
          {isUnavailable && (
            <EmptyState
              title="Economic calendar unavailable"
              body="The public economic calendar is currently unavailable. No events to display."
            />
          )}

          {!isUnavailable && sortedItems.length === 0 && (
            <EmptyState
              title="No economic events"
              body="No public US economic-calendar events for the selected window."
            />
          )}

          {!isUnavailable && sortedItems.length > 0 && (
            <div style={styles.tableScroll}>
              <table style={styles.tbl}>
                <thead>
                  <tr>
                    <Th>Date</Th>
                    <Th>Time</Th>
                    <Th>Impact</Th>
                    <Th>Event</Th>
                    <Th align="right">Actual</Th>
                    <Th align="right">Forecast</Th>
                    <Th align="right">Previous</Th>
                  </tr>
                </thead>
                <tbody>
                  {sortedItems.map((ev, i) => {
                    const key = localDateKey(ev);
                    const isGroupStart = i === 0 || localDateKey(sortedItems[i - 1]) !== key;
                    const evenGroup = (groupIndexByDate.get(key) ?? 0) % 2 === 0;
                    return (
                      <EventRow
                        key={ev.event_reference}
                        ev={ev}
                        showDate={isGroupStart}
                        dateLabel={formatLocalDate(ev)}
                        evenGroup={evenGroup}
                      />
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Compact, non-dominant provenance — only for synthetic/unavailable data */}
          {(isDemo || isUnavailable) && (
            <div style={styles.provenance}>
              <Badge tone={dataModeTone(data.data_mode)} dot title={`Data mode: ${data.data_mode}`}>
                {dataModeLabel(data.data_mode)}
              </Badge>
              <span style={styles.provText}>
                {data.source_label} · {data.freshness_label} · As of {data.as_of_label}
              </span>
            </div>
          )}
        </>
      )}
    </Panel>
  );
}

/* ── Event row ────────────────────────────────────────────────────────── */

function EventRow({
  ev, showDate, dateLabel, evenGroup,
}: {
  ev: EconomicCalendarEventRead;
  showDate: boolean;
  dateLabel: string;
  evenGroup: boolean;
}) {
  const occurred = ev.event_has_occurred === true;
  const impactTitle = `Impact: ${ev.importance} · source: ${importanceSourceLabel(ev.importance_source)}`;

  return (
    <tr style={evenGroup ? styles.rowGroupA : styles.rowGroupB}>
      <Td mono>{showDate ? <span style={styles.dateCell}>{dateLabel}</span> : ""}</Td>
      <Td mono>
        <span style={styles.timeCell}>
          <span>{formatLocalTime(ev.event_datetime_utc, ev.event_time_label)}</span>
          {occurred && <span style={styles.pastTag}>past</span>}
        </span>
      </Td>
      <Td>
        <Badge tone={importanceTone(ev.importance)} dot title={impactTitle}>
          {ev.importance}
        </Badge>
        {ev.importance_source === "app_classified" && (
          <span style={styles.appClassified}>app classified</span>
        )}
      </Td>
      <Td>
        <span style={styles.eventTitle}>{ev.event_title}</span>
        <span style={styles.eventMeta}>
          {eventTypeLabel(ev.event_type)}
          {ev.unit_label ? ` · ${ev.unit_label}` : ""}
        </span>
      </Td>
      <Td mono align="right">{ev.actual_label ?? "—"}</Td>
      <Td mono align="right">{ev.forecast_label ?? "—"}</Td>
      <Td mono align="right">{ev.previous_label ?? "—"}</Td>
    </tr>
  );
}

/* ── Label / tone helpers (presentation only — no classification) ──────── */

function importanceTone(importance: EconomicEventImportance): MpTone {
  switch (importance) {
    case "high": return "block";
    case "medium": return "stale";
    case "low": return "info";
    case "unknown": return "mute";
    default: return "mute";
  }
}

function dataModeTone(mode: EconomicCalendarEventListRead["data_mode"]): MpTone {
  switch (mode) {
    case "provider_reference": return "info";
    case "replay": return "info";
    case "synthetic": return "mute";
    case "unavailable": return "mute";
    default: return "mute";
  }
}

function dataModeLabel(mode: EconomicCalendarEventListRead["data_mode"]): string {
  switch (mode) {
    case "synthetic": return "Synthetic fixture";
    case "replay": return "Replay";
    case "provider_reference": return "Provider reference";
    case "unavailable": return "Unavailable";
    default: return mode;
  }
}

function importanceSourceLabel(source: EconomicEventImportanceSource): string {
  switch (source) {
    case "provider": return "provider";
    case "app_classified": return "app classified";
    case "unavailable": return "unavailable";
    default: return source;
  }
}

function eventTypeLabel(type: EconomicCalendarEventRead["event_type"]): string {
  return type.replace(/_/g, " ");
}

/* ── Local table primitives ───────────────────────────────────────────── */

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th style={{
      textAlign: align, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
      textTransform: "uppercase", letterSpacing: "0.08em", padding: "8px 12px",
      borderBottom: "1px solid var(--mp-rule)", fontWeight: 600, whiteSpace: "nowrap",
    }}>{children}</th>
  );
}

function Td({ children, mono, align = "left" }: { children: React.ReactNode; mono?: boolean; align?: "left" | "right" }) {
  return (
    <td style={{
      textAlign: align, fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)",
      padding: "10px 12px", borderBottom: "1px solid var(--mp-rule)", verticalAlign: "top",
      fontFamily: mono ? "var(--mp-font-mono)" : undefined,
    }}>{children}</td>
  );
}

/* ── Styles ───────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  awarenessRow: { display: "flex", gap: "var(--space-2)", alignItems: "flex-start" },
  awarenessText: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.5 },

  headerActions: { display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" },
  refreshBtn: {
    display: "inline-flex", alignItems: "center", gap: 5,
    minHeight: 28, padding: "4px 8px",
    borderRadius: "var(--radius-sm)",
    border: "1px solid var(--mp-rule)",
    backgroundColor: "var(--mp-paper)",
    color: "var(--mp-ink-2)",
    fontFamily: "var(--mp-font-sans)",
    fontSize: "var(--font-size-xs)",
  },

  pickerRow: { display: "flex", flexWrap: "wrap", alignItems: "center", gap: "var(--space-2)" },
  refreshNotice: {
    padding: "6px 8px", border: "1px dashed var(--mp-rule)", borderRadius: "var(--radius-sm)",
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.45,
  },

  tableScroll: { width: "100%", overflowX: "auto" },
  tbl: { width: "100%", borderCollapse: "collapse", minWidth: 600 },

  // Zebra-by-date: all rows of one calendar date share a color; consecutive
  // dates alternate between these two neutral surfaces. Encodes date only.
  rowGroupA: { backgroundColor: "transparent" },
  rowGroupB: { backgroundColor: "var(--mp-paper-2)" },

  dateCell: { fontWeight: 600, color: "var(--mp-ink)", whiteSpace: "nowrap" },
  timeCell: { display: "flex", flexDirection: "column", gap: 1 },
  pastTag: {
    marginTop: 2, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.06em", fontFamily: "var(--mp-font-sans)",
  },

  appClassified: {
    display: "block", marginTop: 3, fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)", letterSpacing: "0.04em",
  },

  eventTitle: { display: "block", color: "var(--mp-ink)", lineHeight: 1.3 },
  eventMeta: {
    display: "block", marginTop: 2, fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.04em",
  },

  provenance: {
    display: "flex", flexWrap: "wrap", alignItems: "center", gap: "var(--space-2)",
    paddingTop: "var(--space-2)", borderTop: "1px solid var(--mp-rule)",
  },
  provText: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.45 },
};
