import type {
  DeterministicRiskReportRead,
  RiskRuleViolationRead,
  RiskReportSectionRead,
  RiskSeverity,
  MarketDataSnapshotReferenceRead,
} from "../../types/api";

/**
 * RiskReviewPanel — renders a DeterministicRiskReportRead as calculated facts.
 *
 * Invariants:
 *  - Overall risk state is driven ONLY by backend has_blocker / highest_severity.
 *    Severity is never recomputed or re-ranked here.
 *  - Every value is shown verbatim from the backend (no reformatting that could
 *    drift). Only key labels are humanized; values are not mutated.
 *  - These are deterministic Python outputs, explicitly labelled as such and
 *    visually separated from any (future) LLM explanation. No LLM text here.
 *  - Market-quote provenance (scope="market_quote") is shown distinctly from
 *    broker-portfolio freshness; the market/broker asymmetry is presented as-is.
 *  - No buy/sell/order/execute language; no guaranteed-return language.
 */

const SEVERITY_META: Record<
  RiskSeverity,
  { icon: string; label: string; cssVar: string }
> = {
  info: { icon: "ⓘ", label: "Info", cssVar: "var(--color-unknown)" },
  warning: { icon: "△", label: "Warning", cssVar: "var(--color-stale)" },
  violation: { icon: "✕", label: "Violation", cssVar: "var(--color-error)" },
  blocker: { icon: "■", label: "Blocker", cssVar: "var(--color-error)" },
};

const SEVERITY_ORDER: RiskSeverity[] = ["blocker", "violation", "warning", "info"];

function humanizeKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function isAnnualizedRoiKey(key: string): boolean {
  return key.toLowerCase().includes("annualized_roi") || key.toLowerCase().includes("annualized roi");
}

export default function RiskReviewPanel({ report }: { report: DeterministicRiskReportRead }) {
  return (
    <div style={styles.wrap}>
      <OverallState report={report} />

      <p style={styles.deterministicBanner} role="note">
        <span aria-hidden="true">∑ </span>
        Deterministic Python output — calculated facts, not advice, not a forecast.
        Calculation version: <span style={styles.mono}>{report.calculation_version}</span>.
        Generated at <span style={styles.mono}>{report.generated_at}</span>.
      </p>

      {report.sections.map((section) => (
        <SectionCard key={section.title} section={section} />
      ))}

      <ViolationsBlock violations={report.risk_rule_violations} />

      <MarketProvenance snapshot={report.input_snapshot} />
    </div>
  );
}

function OverallState({ report }: { report: DeterministicRiskReportRead }) {
  let icon = "○";
  let label = "No rule violations reported";
  let color = "var(--color-unknown)";
  let detail = "Deterministic checks produced no info/warning/violation/blocker entries.";

  if (report.has_blocker) {
    const m = SEVERITY_META.blocker;
    icon = m.icon;
    label = "Blocker — deterministic report should not be relied upon";
    color = m.cssVar;
    detail = "A blocker-severity rule fired. Resolve the blocking input before using these figures.";
  } else if (report.highest_severity) {
    const m = SEVERITY_META[report.highest_severity];
    icon = m.icon;
    label = `Highest severity: ${m.label}`;
    color = m.cssVar;
    detail = "Severity is taken directly from the backend; it is not recomputed here.";
  }

  return (
    <section
      style={{ ...styles.overall, borderColor: color }}
      role="status"
      aria-label={`Overall deterministic risk state: ${label}`}
    >
      <span style={{ ...styles.overallIcon, color }} aria-hidden="true">
        {icon}
      </span>
      <div>
        <p style={styles.overallLabel}>{label}</p>
        <p style={styles.overallDetail}>{detail}</p>
      </div>
    </section>
  );
}

function SectionCard({ section }: { section: RiskReportSectionRead }) {
  const entries = Object.entries(section.facts);
  return (
    <section style={styles.card} aria-label={`${section.title} (deterministic)`}>
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>{section.title}</span>
        <span style={styles.detTag} title="Deterministic Python calculation output">
          deterministic
        </span>
      </div>
      {entries.length === 0 ? (
        <p style={styles.emptyFacts}>No facts in this section.</p>
      ) : (
        <dl style={styles.facts}>
          {entries.map(([key, value]) => (
            <div key={key} style={styles.factRow}>
              <dt style={styles.factKey}>{humanizeKey(key)}</dt>
              <dd style={styles.factVal}>
                <span style={styles.mono}>{value === null ? "—" : String(value)}</span>
                {isAnnualizedRoiKey(key) && (
                  <span style={styles.caveat}>
                    {" "}
                    simple annualized — not a forecast, not guaranteed
                  </span>
                )}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}

function ViolationsBlock({ violations }: { violations: RiskRuleViolationRead[] }) {
  if (violations.length === 0) {
    return (
      <section style={styles.card} aria-label="Risk rule violations">
        <div style={styles.cardHead}>
          <span style={styles.cardTitle}>Risk Rule Violations</span>
          <span style={styles.detTag}>deterministic</span>
        </div>
        <p style={styles.emptyFacts}>No rule entries were produced.</p>
      </section>
    );
  }

  return (
    <section style={styles.card} aria-label="Risk rule violations grouped by severity">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Risk Rule Violations</span>
        <span style={styles.detTag}>deterministic</span>
      </div>
      {SEVERITY_ORDER.map((sev) => {
        const group = violations.filter((v) => v.severity === sev);
        if (group.length === 0) return null;
        const m = SEVERITY_META[sev];
        return (
          <div key={sev} style={styles.sevGroup}>
            <h3 style={{ ...styles.sevHeading, color: m.cssVar }}>
              <span aria-hidden="true">{m.icon} </span>
              {m.label} ({group.length})
            </h3>
            <ul style={styles.sevList}>
              {group.map((v) => (
                <li key={v.code} style={styles.violation}>
                  <div style={styles.violationTop}>
                    <span
                      style={{ ...styles.sevChip, color: m.cssVar, borderColor: m.cssVar }}
                    >
                      {m.icon} {m.label}
                    </span>
                    <span style={styles.mono}>{v.code}</span>
                  </div>
                  <p style={styles.violationMsg}>{v.message}</p>
                  <div style={styles.violationMeta}>
                    <span>source: <span style={styles.mono}>{v.source}</span></span>
                    {v.metric && (
                      <span>
                        metric: <span style={styles.mono}>{v.metric}</span>
                      </span>
                    )}
                    {v.actual !== null && (
                      <span>
                        actual: <span style={styles.mono}>{v.actual}</span>
                      </span>
                    )}
                    {v.threshold !== null && (
                      <span>
                        threshold: <span style={styles.mono}>{v.threshold}</span>
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}

function MarketProvenance({
  snapshot,
}: {
  snapshot: DeterministicRiskReportRead["input_snapshot"];
}) {
  if (snapshot === null) {
    return (
      <section style={{ ...styles.card, borderLeft: "3px solid var(--color-stale)" }}>
        <div style={styles.cardHead}>
          <span style={styles.cardTitle}>Market Input Provenance</span>
          <span style={styles.scopeBadge}>scope: market_quote</span>
        </div>
        <p style={styles.missingMarket} role="status">
          <span aria-hidden="true">○ </span>
          No market-data input snapshot is attached to this report. Metrics that
          depend on market quotes may be unavailable or based on manual inputs.
          This is separate from broker-portfolio sync freshness.
        </p>
      </section>
    );
  }

  const refs = [...snapshot.quote_references, ...snapshot.chain_references];
  return (
    <section style={styles.card} aria-label="Market input provenance (scope market_quote)">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Market Input Provenance</span>
        <span style={styles.scopeBadge} title='freshness_scope = "market_quote"'>
          scope: market_quote
        </span>
      </div>
      <p style={styles.provNote}>
        Market-quote freshness below is a separate scope from broker-portfolio
        sync freshness. The market/broker severity asymmetry is intentional and
        is shown as the backend reports it — not normalized.
      </p>
      <ul style={styles.facts}>
        <li style={styles.factRow}>
          <span style={styles.factKey}>Snapshot id</span>
          <span style={styles.mono}>{snapshot.report_input_snapshot_id}</span>
        </li>
        <li style={styles.factRow}>
          <span style={styles.factKey}>Captured at</span>
          <span style={styles.mono}>{snapshot.captured_at}</span>
        </li>
        <li style={styles.factRow}>
          <span style={styles.factKey}>Uses current quotes</span>
          <span style={styles.mono}>{String(snapshot.uses_current_quotes)}</span>
        </li>
      </ul>
      {refs.length > 0 && (
        <ul style={styles.refList}>
          {refs.map((r) => (
            <SnapshotRefRow key={r.snapshot_id + r.kind} r={r} />
          ))}
        </ul>
      )}
    </section>
  );
}

function SnapshotRefRow({ r }: { r: MarketDataSnapshotReferenceRead }) {
  return (
    <li style={styles.refRow}>
      <div style={styles.refTop}>
        <span style={styles.mono}>{r.kind}</span>
        <span style={styles.refKey}>{r.stable_key}</span>
        <span style={styles.refProvider}>{r.provider}</span>
      </div>
      {/* data_mode + freshness_status + actionability_status always together */}
      <div style={styles.refStatus}>
        <span style={styles.statusChip}>mode: {r.data_mode}</span>
        <span style={styles.statusChip}>freshness: {r.freshness_status}</span>
        <span style={styles.statusChip}>actionability: {r.actionability_status}</span>
      </div>
      <div style={styles.refTimes}>
        <span>captured: <span style={styles.mono}>{r.captured_at}</span></span>
        <span>
          quote_time:{" "}
          <span style={styles.mono}>{r.quote_time ?? "—"}</span>
        </span>
      </div>
    </li>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: { display: "flex", flexDirection: "column", gap: "var(--space-4)" },
  overall: {
    display: "flex",
    gap: "var(--space-4)",
    alignItems: "flex-start",
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderLeftWidth: 4,
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
  },
  overallIcon: { fontSize: "var(--font-size-lg)", flexShrink: 0, lineHeight: 1.2 },
  overallLabel: {
    fontWeight: 700,
    fontSize: "var(--font-size-base)",
    color: "var(--color-text-primary)",
    margin: 0,
  },
  overallDetail: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    margin: "var(--space-1) 0 0",
    lineHeight: 1.6,
  },
  deterministicBanner: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    backgroundColor: "var(--color-surface-2)",
    border: "1px solid var(--color-border-subtle)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-4)",
    margin: 0,
    lineHeight: 1.6,
  },
  card: {
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
  },
  cardHead: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-3)",
    flexWrap: "wrap",
  },
  cardTitle: {
    fontWeight: 700,
    fontSize: "var(--font-size-base)",
    color: "var(--color-text-primary)",
  },
  detTag: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid var(--color-unknown)",
    borderRadius: "var(--radius-sm)",
    color: "var(--color-unknown)",
    fontWeight: 600,
    letterSpacing: "0.04em",
  },
  scopeBadge: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid var(--color-unknown)",
    borderRadius: "var(--radius-sm)",
    color: "var(--color-unknown)",
    fontWeight: 600,
  },
  facts: { margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "var(--space-1)", listStyle: "none" },
  factRow: {
    display: "flex",
    gap: "var(--space-4)",
    fontSize: "var(--font-size-xs)",
    alignItems: "baseline",
  },
  factKey: { minWidth: 200, color: "var(--color-text-muted)" },
  factVal: { color: "var(--color-text-secondary)", margin: 0 },
  caveat: { color: "var(--color-stale)", fontStyle: "italic" },
  emptyFacts: { fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", margin: 0 },
  mono: { fontFamily: "var(--font-mono, monospace)", color: "var(--color-text-secondary)" },
  sevGroup: { display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  sevHeading: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    margin: 0,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  sevList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  violation: {
    border: "1px solid var(--color-border-subtle)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-3)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
  },
  violationTop: { display: "flex", gap: "var(--space-3)", alignItems: "center", flexWrap: "wrap" },
  sevChip: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid",
    borderRadius: "var(--radius-sm)",
    fontWeight: 700,
  },
  violationMsg: { fontSize: "var(--font-size-sm)", color: "var(--color-text-secondary)", margin: 0, lineHeight: 1.5 },
  violationMeta: {
    display: "flex",
    gap: "var(--space-4)",
    flexWrap: "wrap",
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
  },
  provNote: { fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", margin: 0, lineHeight: 1.6 },
  missingMarket: { fontSize: "var(--font-size-sm)", color: "var(--color-text-secondary)", margin: 0, lineHeight: 1.6, fontWeight: 600 },
  refList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  refRow: {
    border: "1px solid var(--color-border-subtle)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-3)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
  },
  refTop: { display: "flex", gap: "var(--space-3)", flexWrap: "wrap", alignItems: "baseline" },
  refKey: { fontSize: "var(--font-size-xs)", color: "var(--color-text-secondary)" },
  refProvider: { fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)" },
  refStatus: { display: "flex", gap: "var(--space-2)", flexWrap: "wrap" },
  statusChip: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 5px",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    color: "var(--color-text-muted)",
  },
  refTimes: {
    display: "flex",
    gap: "var(--space-4)",
    flexWrap: "wrap",
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
  },
};
