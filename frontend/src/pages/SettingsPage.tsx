import { Badge, DemoChip, PageHeader, Panel, SafetyStrip } from "../components/shared/mp";
import AppearanceControl from "../components/layout/AppearanceControl";
import { DEMO_SETTINGS_PROVIDER_INFO } from "../components/demo/modernDeskDemoData";

/**
 * SettingsPage — Modern Portfolio Desk settings (P20A-T3 placeholder).
 *
 * Translated from
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/settings.tsx
 *
 * Slice scope: appearance + private-alpha display + safe informational
 * sections only. No destructive provider controls, no broker disconnect,
 * no real auth/session controls, no LLM/provider toggles. The provider /
 * roles / freshness preference sections are placeholder-only and carry the
 * `demo · not yet connected` chip until backend contracts exist.
 */
export default function SettingsPage() {
  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Workspace · settings"
        title="Settings"
        sub="Read-only configuration view. Destructive controls (broker disconnect, real provider toggles, session resets) are intentionally not exposed in this slice."
      />

      <Panel title="Appearance" tag="local-only · UI preference">
        <p style={styles.body}>
          Switch between System, Light, and Dark. Your choice is stored in
          <code> localStorage</code> only (key <code>poa-appearance</code>) — no
          portfolio, broker, or analysis data is persisted in browser storage.
        </p>
        <AppearanceControl />
      </Panel>

      <Panel title="Private-alpha status" tag="invite-gated" accent>
        <div style={styles.row}>
          <span style={styles.rowLabel}>Status</span>
          <Badge tone="info" dot>Private alpha</Badge>
        </div>
        <div style={styles.row}>
          <span style={styles.rowLabel}>Operator mode</span>
          <Badge tone="mute" dot={false}>Local trader</Badge>
        </div>
        <p style={styles.note}>
          Read-only · analysis-only · no order placement. Manual decision support only.
        </p>
      </Panel>

      <Panel title="Agent / LLM availability" tag="provider" right={<DemoChip />}>
        <div style={styles.row}>
          <span style={styles.rowLabel}>Provider</span>
          <span style={styles.rowValue}>{DEMO_SETTINGS_PROVIDER_INFO.provider}</span>
        </div>
        <div style={styles.row}>
          <span style={styles.rowLabel}>Workflow version</span>
          <span style={styles.rowValue}>{DEMO_SETTINGS_PROVIDER_INFO.workflowVersion}</span>
        </div>
        <div style={styles.row}>
          <span style={styles.rowLabel}>Roles enabled</span>
          <span style={styles.rowValue}>{DEMO_SETTINGS_PROVIDER_INFO.rolesEnabled.join(", ")}</span>
        </div>
        <p style={styles.note}>
          Real-provider opt-in is gated by the operator. This view is informational only.
        </p>
      </Panel>

      <Panel title="Broker connection scope" tag="what we receive" right={<DemoChip />}>
        <ul style={styles.disclaimerList}>
          <li>Read-only positions, cash, and option contracts via SnapTrade OAuth.</li>
          <li>No order placement. No order cancellation. No broker destructive actions.</li>
          <li>No credential capture in this app — broker auth happens inside the broker's portal.</li>
        </ul>
      </Panel>

      <Panel title="Freshness preferences" tag="placeholder · thresholds" right={<DemoChip />}>
        <p style={styles.body}>
          Broker-snapshot and market-quote freshness thresholds are tuned
          server-side today. A user-facing preference surface will land once the
          aggregate freshness contract (P20B-T3) is reviewed.
        </p>
      </Panel>

      <SafetyStrip items={["Read-only", "Analysis-only", "No broker order placement", "No destructive provider controls"]} />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", gap: "var(--space-5)", maxWidth: 1024, margin: "0 auto", color: "var(--mp-ink)" },
  body: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.6, margin: 0 },
  row: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "var(--space-2) 0", borderTop: "1px solid var(--mp-rule)" },
  rowLabel: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)" },
  rowValue: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", fontFamily: "var(--mp-font-mono)" },
  note: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.6, margin: 0, marginTop: "var(--space-2)" },
  disclaimerList: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.6, margin: 0, paddingLeft: "var(--space-5)", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
};
