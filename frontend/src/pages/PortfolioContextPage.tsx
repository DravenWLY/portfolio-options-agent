import { Badge, DemoChip, KV, PageHeader, Panel, SafetyStrip } from "../components/shared/mp";
import { DEMO_PORTFOLIO_SOURCES, DEMO_CONTEXT_REFS_TABLE } from "../components/demo/modernDeskDemoData";

/**
 * PortfolioContextPage — Modern Portfolio Desk standalone context page
 * (P20A-T3 placeholder).
 *
 * Translated from
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/portfolio.tsx
 *
 * Backed by demo data only. Real wiring requires P20B-T4 (standalone
 * portfolio-context enumeration + detail).
 *
 * Safety: no raw holdings, no balances, no provider/account ids, no broker
 * names beyond demo labels.
 */
export default function PortfolioContextPage() {
  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Workspace · portfolio context"
        title="Portfolio context"
        sub="Server-owned portfolio-context references used by Trade Review and Agent Console. The frontend never sends broker freshness, market freshness, provider status, cash, holdings, or thresholds. This page lists only safe metadata."
        right={<DemoChip />}
      />

      <Panel title="Connected sources" tag="read-only · per source" right={<Badge tone="info" dot={false}>no raw holdings exposed</Badge>}>
        <table style={styles.tbl}>
          <thead>
            <tr><Th>Source</Th><Th>Mode</Th><Th>Last sync</Th><Th align="right">Status</Th></tr>
          </thead>
          <tbody>
            {DEMO_PORTFOLIO_SOURCES.map((s) => (
              <tr key={s.name}>
                <Td>{s.name}</Td>
                <Td mono>{s.mode}</Td>
                <Td mono>{s.ago}</Td>
                <Td align="right"><Badge tone={s.tone} dot>{s.tone === "live" ? "healthy" : s.tone === "stale" ? "stale" : "manual"}</Badge></Td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ marginTop: "var(--space-2)" }}><DemoChip /></div>
      </Panel>

      <Panel title="Aggregate position counts" tag="what reviewer sees" right={<Badge tone="info" dot={false}>counts only</Badge>}>
        <KV rows={[
          ["Connected accounts", "—"],
          ["Stock positions (count)", "—"],
          ["Option positions (count)", "—"],
          ["Cash state", "—"],
          ["Snapshot as of", "demo · not yet connected"],
        ]} />
        <div style={{ marginTop: "var(--space-2)" }}><DemoChip /></div>
      </Panel>

      <Panel title="Context references" tag="opaque · server-owned" right={<DemoChip />}>
        <table style={styles.tbl}>
          <thead>
            <tr><Th>Reference</Th><Th>Source</Th><Th>Label</Th><Th>Counts</Th><Th>Cash state</Th></tr>
          </thead>
          <tbody>
            {DEMO_CONTEXT_REFS_TABLE.map((c) => (
              <tr key={c.ref}>
                <Td mono>{c.ref}</Td>
                <Td mono>{c.source}</Td>
                <Td>{c.label}</Td>
                <Td mono>{c.counts}</Td>
                <Td mono>{c.cash}</Td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={styles.note}>
          Context references are opaque and server-owned. Freshness, cash,
          holdings, and thresholds never leave the backend. The four
          <code> ctx_demo_*</code> refs above are the only valid context
          references accepted by the existing Trade Review portfolio-preview
          endpoint today.
        </p>
      </Panel>

      <Panel title="What this screen does and does not show">
        <ul style={styles.disclaimerList}>
          <li>Shows: safe context metadata only — opaque reference, source label, position counts, cash-state category.</li>
          <li>Does not show: raw holdings, balances, account values, account/provider ids, OAuth tokens, raw provider payloads, or trade-journal entries.</li>
          <li>Does not perform any frontend financial computation.</li>
        </ul>
      </Panel>

      <SafetyStrip items={["Analysis only", "Manual review", "Not an order recommendation", "Demo data on this page until P20B-T4 lands"]} />
    </div>
  );
}

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th style={{
      textAlign: align, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
      textTransform: "uppercase", letterSpacing: "0.08em", padding: "8px 12px",
      borderBottom: "1px solid var(--mp-rule)", fontWeight: 600,
    }}>{children}</th>
  );
}
function Td({ children, mono, align = "left" }: { children: React.ReactNode; mono?: boolean; align?: "left" | "right" }) {
  return (
    <td style={{
      textAlign: align, fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)",
      padding: "10px 12px", borderBottom: "1px solid var(--mp-rule)",
      fontFamily: mono ? "var(--mp-font-mono)" : undefined,
    }}>{children}</td>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", gap: "var(--space-5)", maxWidth: 1280, margin: "0 auto", color: "var(--mp-ink)" },
  tbl: { width: "100%", borderCollapse: "collapse" },
  note: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.6, margin: 0, marginTop: "var(--space-2)" },
  disclaimerList: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.6, margin: 0, paddingLeft: "var(--space-5)", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
};
