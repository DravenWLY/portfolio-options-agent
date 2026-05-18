import type { MarketDataProviderStatusRead } from "../../types/marketData";

/**
 * MarketDataStatusPanel — read-only Phase 12 market-data status surface.
 *
 * No real provider is connected. This renders a static, contract-faithful
 * SAMPLE of the manual/mock `MarketDataProviderStatusRead` shape. It performs
 * NO network calls and stores nothing in browser storage.
 *
 * Safety invariants:
 *  - freshness_status is NEVER shown alone — always paired with data_mode
 *    and actionability_status (Codex Phase 12 adjudication).
 *  - freshness_scope="market_quote" is labelled distinctly from broker
 *    portfolio sync freshness.
 *  - No live / intraday / guaranteed-return / trade-execution language.
 */

// Static sample of the Phase 12 manual contract. The manual/mock provider
// cannot mint actionability_status="actionable_snapshot"; manual inputs are
// always "analysis_only".
const SAMPLE_STATUS: MarketDataProviderStatusRead = {
  provider: "manual",
  freshness_scope: "market_quote",
  data_mode: "manual",
  freshness_status: "manual",
  actionability_status: "analysis_only",
  checked_at: "2026-05-18T15:00:00Z",
  message: "Market data provider not connected yet. Manual/mock quote inputs only.",
  capabilities: {
    provider: "manual",
    supports_stock_quotes: true,
    supports_intraday_bars: false,
    supports_option_expirations: true,
    supports_option_chain: true,
    supports_option_snapshots: true,
    supports_iv: true,
    supports_greeks: true,
    supports_streaming: false,
    supports_historical_options: false,
    supported_data_modes: ["manual", "delayed", "cached", "eod", "unknown"],
    notes: ["Manual/mock provider; no network calls."],
  },
};

const DATA_MODE_LABEL = "Data mode";
const FRESHNESS_LABEL = "Quote freshness";
const ACTIONABILITY_LABEL = "Actionability";

export default function MarketDataStatusPanel() {
  const s = SAMPLE_STATUS;

  return (
    <section
      style={styles.panel}
      role="region"
      aria-label="Market data provider status (manual/mock, not connected)"
    >
      <div style={styles.header}>
        <span style={styles.title}>Market data status</span>
        <span style={styles.scopeBadge} title='freshness_scope = "market_quote"'>
          scope: market_quote
        </span>
      </div>

      <p style={styles.notConnected} role="status">
        <span aria-hidden="true">○ </span>
        Market data provider not connected yet — manual/mock quote inputs only.
      </p>

      {/* freshness_status is rendered ONLY together with data_mode and
          actionability_status, never on its own. */}
      <dl style={styles.statusCluster} aria-label="Quote status (read together)">
        <StatusItem label={DATA_MODE_LABEL} value={s.data_mode} icon="◐" />
        <StatusItem label={FRESHNESS_LABEL} value={s.freshness_status} icon="◔" />
        <StatusItem label={ACTIONABILITY_LABEL} value={s.actionability_status} icon="□" />
      </dl>

      <p style={styles.clusterNote}>
        These three are read together. A quote being “fresh” by recency never
        means it is actionable — manual/mock inputs are analysis-only.
      </p>

      <ul style={styles.facts}>
        <li>
          <span style={styles.factKey}>Provider</span>
          <span style={styles.factVal}>{s.provider} (mock)</span>
        </li>
        <li>
          <span style={styles.factKey}>Checked at</span>
          <span style={styles.factVal}>{s.checked_at}</span>
        </li>
        <li>
          <span style={styles.factKey}>Provider note</span>
          <span style={styles.factVal}>{s.capabilities.notes.join(" ")}</span>
        </li>
        <li>
          <span style={styles.factKey}>Supported data modes</span>
          <span style={styles.factVal}>{s.capabilities.supported_data_modes.join(", ")}</span>
        </li>
      </ul>

      <p style={styles.safety} role="note">
        Do not treat this as live market pricing. Broker holdings and cash come
        from broker sync; market quotes are a separate, not-yet-connected source.
      </p>
    </section>
  );
}

function StatusItem({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div style={styles.statusItem}>
      <dt style={styles.statusLabel}>{label}</dt>
      <dd style={styles.statusValue}>
        <span style={styles.chip}>
          <span aria-hidden="true">{icon} </span>
          {value}
        </span>
      </dd>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  panel: {
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderLeft: "3px solid var(--color-unknown)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-5) var(--space-6)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-3)",
    flexWrap: "wrap",
  },
  title: {
    fontWeight: 700,
    fontSize: "var(--font-size-base)",
    color: "var(--color-text-primary)",
  },
  scopeBadge: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid var(--color-unknown)",
    borderRadius: "var(--radius-sm)",
    color: "var(--color-unknown)",
    fontWeight: 600,
    letterSpacing: "0.03em",
  },
  notConnected: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-secondary)",
    margin: 0,
    fontWeight: 600,
  },
  statusCluster: {
    display: "flex",
    gap: "var(--space-4)",
    flexWrap: "wrap",
    margin: 0,
    padding: "var(--space-3) var(--space-4)",
    backgroundColor: "var(--color-surface-2)",
    border: "1px solid var(--color-border-subtle)",
    borderRadius: "var(--radius-sm)",
  },
  statusItem: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
  },
  statusLabel: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    margin: 0,
  },
  statusValue: {
    margin: 0,
  },
  chip: {
    display: "inline-block",
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid var(--color-unknown)",
    borderRadius: "var(--radius-sm)",
    color: "var(--color-text-secondary)",
    fontWeight: 600,
  },
  clusterNote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    margin: 0,
    lineHeight: 1.6,
  },
  facts: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
    margin: 0,
    padding: 0,
    listStyle: "none",
    fontSize: "var(--font-size-xs)",
  },
  factKey: {
    display: "inline-block",
    minWidth: 160,
    color: "var(--color-text-muted)",
  },
  factVal: {
    color: "var(--color-text-secondary)",
  },
  safety: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-secondary)",
    margin: 0,
    lineHeight: 1.6,
    fontWeight: 600,
  },
};
