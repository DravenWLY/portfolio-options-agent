import { useEffect, useMemo, useRef, useState } from "react";
import { MpIcon } from "../shared/mp";

/**
 * EconomicCalendarRangePicker — single dual-month range calendar (P24A-T9
 * revision). Click a start date, then an end date; the inclusive span is
 * highlighted (flight-ticket style). The selectable end is capped at
 * `maxDays` so the window can never exceed the backend's limit. Pure date
 * selection only — no data, no backend calls, no storage.
 */

const MS_PER_DAY = 86_400_000;
const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function pad2(n: number): string { return String(n).padStart(2, "0"); }
function partsToISO(y: number, m: number, d: number): string { return `${y}-${pad2(m)}-${pad2(d)}`; }
function isoParts(iso: string): { y: number; m: number; d: number } {
  const [y, m, d] = iso.split("-").map(Number);
  return { y, m, d };
}
function parseISOUTC(iso: string): number { return Date.parse(`${iso}T00:00:00Z`); }
function addDaysISO(iso: string, days: number): string {
  const t = parseISOUTC(iso);
  if (Number.isNaN(t)) return iso;
  return new Date(t + days * MS_PER_DAY).toISOString().slice(0, 10);
}
function fmtISO(iso: string, opts: Intl.DateTimeFormatOptions): string {
  const { y, m, d } = isoParts(iso);
  return new Date(y, m - 1, d).toLocaleDateString([], opts);
}
function todayISO(): string {
  const n = new Date();
  return partsToISO(n.getFullYear(), n.getMonth() + 1, n.getDate());
}

/** Human-readable label for the applied window (used on the trigger button). */
function formatRangeLabel(start: string, end: string): string {
  if (start === end) return fmtISO(start, { year: "numeric", month: "long", day: "numeric" });
  const sameYear = isoParts(start).y === isoParts(end).y;
  const startOpts: Intl.DateTimeFormatOptions = sameYear
    ? { month: "long", day: "numeric" }
    : { year: "numeric", month: "long", day: "numeric" };
  return `${fmtISO(start, startOpts)} – ${fmtISO(end, { year: "numeric", month: "long", day: "numeric" })}`;
}

interface Props {
  start: string;
  end: string;
  /** Optional cap on the inclusive window length. Omit for an unbounded range. */
  maxDays?: number;
  onApply: (start: string, end: string) => void;
  onResetToday: () => void;
}

export default function EconomicCalendarRangePicker({ start, end, maxDays, onApply, onResetToday }: Props) {
  const [open, setOpen] = useState(false);
  const [pendingStart, setPendingStart] = useState(start);
  const [pendingEnd, setPendingEnd] = useState<string | null>(end);
  const [hoverDay, setHoverDay] = useState<string | null>(null);
  const [viewYear, setViewYear] = useState(() => isoParts(start).y);
  const [viewMonth, setViewMonth] = useState(() => isoParts(start).m);
  const containerRef = useRef<HTMLDivElement>(null);
  const today = todayISO();

  // Seed the pending selection / view from the applied value each time we open.
  useEffect(() => {
    if (!open) return;
    setPendingStart(start);
    setPendingEnd(end);
    setHoverDay(null);
    setViewYear(isoParts(start).y);
    setViewMonth(isoParts(start).m);
  }, [open, start, end]);

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const selecting = !!pendingStart && pendingEnd === null;
  const maxSelectableEnd = useMemo(
    () => (pendingStart && maxDays && maxDays > 0 ? addDaysISO(pendingStart, maxDays - 1) : null),
    [pendingStart, maxDays],
  );

  const rangeStart = pendingStart;
  const rangeEnd =
    pendingEnd ??
    (selecting && hoverDay && hoverDay >= pendingStart && (!maxSelectableEnd || hoverDay <= maxSelectableEnd)
      ? hoverDay
      : pendingStart);

  const handleDayClick = (iso: string) => {
    if (selecting) {
      if (iso < pendingStart) {
        // Clicking before the start restarts the selection.
        setPendingStart(iso);
        setPendingEnd(null);
        return;
      }
      if (maxSelectableEnd && iso > maxSelectableEnd) return; // beyond max — disabled
      onApply(pendingStart, iso);
      setPendingEnd(iso);
      setOpen(false);
    } else {
      setPendingStart(iso);
      setPendingEnd(null);
    }
  };

  const shiftMonths = (delta: number) => {
    const base = new Date(viewYear, viewMonth - 1 + delta, 1);
    setViewYear(base.getFullYear());
    setViewMonth(base.getMonth() + 1);
  };

  const isDisabledDay = (iso: string): boolean =>
    !!(selecting && maxSelectableEnd && iso > maxSelectableEnd);

  const renderMonth = (y: number, m: number) => {
    const firstWeekday = new Date(y, m - 1, 1).getDay();
    const daysInMonth = new Date(y, m, 0).getDate();
    const leading = Array.from({ length: firstWeekday });
    const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
    return (
      <div style={styles.month} key={`${y}-${m}`}>
        <div style={styles.monthTitle}>
          {new Date(y, m - 1, 1).toLocaleDateString([], { month: "long", year: "numeric" })}
        </div>
        <div style={styles.weekRow}>
          {WEEKDAYS.map((w) => <div key={w} style={styles.weekday}>{w}</div>)}
        </div>
        <div style={styles.grid}>
          {leading.map((_, i) => <div key={`pad-${i}`} />)}
          {days.map((d) => {
            const iso = partsToISO(y, m, d);
            const disabled = isDisabledDay(iso);
            const isStart = iso === rangeStart;
            const isEnd = iso === rangeEnd;
            const isEndpoint = isStart || isEnd;
            const inRange = !!rangeStart && iso >= rangeStart && iso <= rangeEnd;
            const isToday = iso === today;
            const cellStyle: React.CSSProperties = {
              ...styles.day,
              ...(inRange && !isEndpoint ? styles.dayInRange : null),
              ...(isEndpoint ? styles.dayEndpoint : null),
              ...(isToday && !isEndpoint ? styles.dayToday : null),
              ...(disabled ? styles.dayDisabled : null),
            };
            return (
              <button
                key={iso}
                type="button"
                disabled={disabled}
                aria-pressed={isEndpoint}
                aria-label={fmtISO(iso, { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
                onClick={() => handleDayClick(iso)}
                onMouseEnter={() => setHoverDay(iso)}
                style={cellStyle}
              >
                {d}
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  const nextMonthDate = new Date(viewYear, viewMonth, 1);

  return (
    <div ref={containerRef} style={styles.wrap}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="dialog"
        aria-expanded={open}
        style={styles.trigger}
      >
        <MpIcon name="clock" size={14} style={{ color: "var(--mp-mute)", flexShrink: 0 }} />
        <span style={styles.triggerLabel}>{formatRangeLabel(start, end)}</span>
        <MpIcon name="chevron-d" size={14} style={{ color: "var(--mp-mute)", flexShrink: 0 }} />
      </button>

      {open && (
        <div style={styles.popover} role="dialog" aria-label="Select date range">
          <div style={styles.navRow}>
            <button type="button" onClick={() => shiftMonths(-1)} aria-label="Previous month" style={styles.navBtn}>
              <span style={{ display: "inline-flex", transform: "scaleX(-1)" }}>
                <MpIcon name="chevron-r" size={14} />
              </span>
            </button>
            <span style={styles.navHint}>
              {selecting ? "Select end date" : "Select start date"}
              {maxDays && maxDays > 0 ? ` · up to ${maxDays} days` : ""}
            </span>
            <button type="button" onClick={() => shiftMonths(1)} aria-label="Next month" style={styles.navBtn}>
              <MpIcon name="chevron-r" size={14} />
            </button>
          </div>

          <div style={styles.months} onMouseLeave={() => setHoverDay(null)}>
            {renderMonth(viewYear, viewMonth)}
            {renderMonth(nextMonthDate.getFullYear(), nextMonthDate.getMonth() + 1)}
          </div>

          <div style={styles.footer}>
            <button
              type="button"
              onClick={() => { onResetToday(); setOpen(false); }}
              style={styles.todayBtn}
            >
              Today
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Styles ───────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  wrap: { position: "relative", display: "inline-block" },
  trigger: {
    display: "inline-flex", alignItems: "center", gap: 6,
    minHeight: 32, padding: "5px 10px",
    border: "1px solid var(--mp-rule)", borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-card)", color: "var(--mp-ink)",
    fontFamily: "var(--mp-font-sans)", fontSize: "var(--font-size-sm)", cursor: "pointer",
  },
  triggerLabel: { fontWeight: 500 },

  popover: {
    position: "absolute", top: "calc(100% + 6px)", left: 0, zIndex: 50,
    backgroundColor: "var(--mp-card)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)", boxShadow: "0 12px 32px rgba(0,0,0,0.18)",
    padding: "var(--space-3)", width: "max-content", maxWidth: "calc(100vw - 32px)",
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  navRow: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    gap: "var(--space-2)",
  },
  navBtn: {
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    width: 28, height: 28, borderRadius: "var(--radius-sm)",
    border: "1px solid var(--mp-rule)", backgroundColor: "var(--mp-paper)",
    color: "var(--mp-ink-2)", cursor: "pointer",
  },
  navHint: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600,
    textAlign: "center",
  },
  months: { display: "flex", flexWrap: "wrap", gap: "var(--space-4)" },
  month: { display: "flex", flexDirection: "column", gap: 4, minWidth: 196 },
  monthTitle: {
    fontSize: "var(--font-size-sm)", fontWeight: 600, color: "var(--mp-ink)",
    textAlign: "center", paddingBottom: 2,
  },
  weekRow: { display: "grid", gridTemplateColumns: "repeat(7, 1fr)" },
  weekday: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textAlign: "center",
    padding: "2px 0", fontWeight: 600,
  },
  grid: { display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 2 },
  day: {
    minHeight: 28, padding: 0, borderRadius: "var(--radius-sm)",
    border: "1px solid transparent", backgroundColor: "transparent",
    color: "var(--mp-ink)", fontFamily: "var(--mp-font-sans)",
    fontSize: "var(--font-size-sm)", cursor: "pointer",
  },
  dayInRange: { backgroundColor: "var(--mp-accent-soft)", color: "var(--mp-ink)" },
  dayEndpoint: {
    backgroundColor: "var(--mp-accent)", color: "var(--mp-card)", fontWeight: 700,
    borderColor: "var(--mp-accent)",
  },
  dayToday: { borderColor: "var(--mp-accent-line)", fontWeight: 600 },
  dayDisabled: { color: "var(--mp-mute)", opacity: 0.4, cursor: "not-allowed" },

  footer: { display: "flex", justifyContent: "flex-end", borderTop: "1px solid var(--mp-rule)", paddingTop: "var(--space-2)" },
  todayBtn: {
    minHeight: 28, padding: "4px 10px", borderRadius: "var(--radius-sm)",
    border: "1px solid var(--mp-rule)", backgroundColor: "var(--mp-paper)",
    color: "var(--mp-ink-2)", fontFamily: "var(--mp-font-sans)",
    fontSize: "var(--font-size-xs)", fontWeight: 600, cursor: "pointer",
  },
};
