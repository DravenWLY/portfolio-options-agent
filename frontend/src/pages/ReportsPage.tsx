import { DemoChip, PageHeader, Panel, Pill, SafetyStrip } from "../components/shared/mp";
import { DEMO_REPORTS_TABLE } from "../components/demo/modernDeskDemoData";

/**
 * ReportsPage — Modern Portfolio Desk reports list (P20A-T3 placeholder).
 *
 * Translated from
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/reports.tsx
 *
 * Backed by demo data only — visible `demo · not yet connected` chip on the
 * panel. Real wiring requires P20B-T5 (reports list + detail contracts).
 */
export default function ReportsPage() {
  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Workspace · reports"
        title="Reports"
        sub="Saved deterministic trade-review reports and agent-team analyses. Read-only. No order is placed from this screen."
        right={<DemoChip />}
      />

      <Panel title="Recent reports" tag="placeholder · last 7 days" right={<DemoChip />}>
        <table style={styles.tbl}>
          <thead>
            <tr><Th>Reference</Th><Th>Flow</Th><Th>Symbol</Th><Th>Actionability</Th><Th align="right">Saved</Th></tr>
          </thead>
          <tbody>
            {DEMO_REPORTS_TABLE.map((r) => (
              <tr key={r.ref}>
                <Td mono>{r.ref}</Td>
                <Td>{r.flow}</Td>
                <Td mono>{r.symbol}</Td>
                <Td><Pill tone={r.tone}>{r.actionability}</Pill></Td>
                <Td mono align="right">{r.ago}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <SafetyStrip items={["Analysis only", "Manual review", "Not an order recommendation"]} />
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
  page: { display: "flex", flexDirection: "column", gap: "var(--space-6)", maxWidth: 1280, margin: "0 auto", color: "var(--mp-ink)" },
  tbl: { width: "100%", borderCollapse: "collapse" },
};
