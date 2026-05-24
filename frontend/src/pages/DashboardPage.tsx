import { useNavigate } from "react-router-dom";
import { Badge, DemoChip, KV, PageHeader, Panel, Pill, SafetyStrip, type MpTone } from "../components/shared/mp";
import {
  DEMO_DISPLAY_NAME,
  DEMO_READINESS_TILES,
  DEMO_RECENT_REVIEWS,
  DEMO_RISK_ALERTS,
  DEMO_QUICK_REVIEWS,
  DEMO_WHATS_RUNNING,
} from "../components/demo/modernDeskDemoData";

/**
 * DashboardPage — Modern Portfolio Desk overview (P20A-T3 placeholder).
 *
 * Translated from
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/dashboard.tsx
 *
 * Every card on this page is currently backed by demo data only and carries a
 * visible `demo · not yet connected` chip. Real wiring requires the Phase 20B
 * backend stubs (P20B-T1 trade-reviews list, P20B-T2 risk alerts, P20B-T3
 * readiness aggregate, P20B-T6 user/profile).
 */
export default function DashboardPage() {
  const nav = useNavigate();
  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Workspace · overview"
        title={`Good morning, ${DEMO_DISPLAY_NAME}.`}
        sub="Your readiness snapshot. Numbers shown on this page are demo placeholders — real market prices are not connected; broker values arrive from broker sync when a real account is bound. Manual decision support only."
        right={
          <button style={styles.primaryBtn} type="button" onClick={() => nav("/trade-review")}>
            New trade review →
          </button>
        }
      />

      <section style={styles.readinessGrid}>
        {DEMO_READINESS_TILES.map((t) => (
          <ReadinessTile key={t.title} {...t} />
        ))}
      </section>

      <section style={styles.body}>
        <div style={styles.col}>
          <Panel title="Recent trade reviews" tag="last 7 days" right={<DemoChip />}>
            <table style={styles.tbl}>
              <thead>
                <tr><Th>Reference</Th><Th>Flow</Th><Th>Symbol</Th><Th>Actionability</Th><Th align="right">When</Th></tr>
              </thead>
              <tbody>
                {DEMO_RECENT_REVIEWS.map((r) => (
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

          <Panel title="Risk alerts" tag="deterministic · placeholder" right={<DemoChip />}>
            <ul style={styles.alertList}>
              {DEMO_RISK_ALERTS.map((a, i) => (
                <li key={i} style={{ ...styles.alertRow, borderLeftColor: a.sev === "block" ? "var(--mp-block)" : "var(--mp-stale)" }}>
                  <Pill tone={a.sev === "block" ? "block" : "stale"}>
                    {a.sev === "block" ? "violation" : "warning"}
                  </Pill>
                  <div style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0 }}>
                    <span style={styles.alertMsg}>{a.msg}</span>
                    <span style={styles.alertCode}>{a.code} · ref {a.ref}</span>
                  </div>
                </li>
              ))}
            </ul>
          </Panel>
        </div>

        <div style={styles.col}>
          <Panel title="Portfolio context" tag="placeholder" accent right={<DemoChip />}>
            <KV rows={[
              ["Connected accounts", "—"],
              ["Total positions", "—"],
              ["Snapshot as of", "demo · not yet connected"],
              ["Cash state", "—"],
            ]} />
          </Panel>

          <Panel title="Quick reviews" tag="presets" right={<DemoChip />}>
            <div style={styles.quickGrid}>
              {DEMO_QUICK_REVIEWS.map((q) => (
                <button key={q.flow} type="button" onClick={() => nav("/trade-review")} style={styles.quickBtn}>
                  <span style={styles.quickLabel}>{q.label}</span>
                  <span style={styles.quickSub}>{q.sub}</span>
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="What's running" tag="provider status" right={<DemoChip />}>
            <ul style={styles.facts}>
              {DEMO_WHATS_RUNNING.map((r) => (
                <li key={r.label} style={styles.factRow}>
                  <span style={styles.factLabel}>{r.label}</span>
                  <Badge tone={r.tone} dot>{r.status}</Badge>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </section>

      <SafetyStrip items={["Manual decision support only", "No order is placed", "Demo data on this overview until backend tiles land"]} />
    </div>
  );
}

function ReadinessTile({
  title, subtitle, status, tone, rows,
}: {
  title: string;
  subtitle: string;
  status: string;
  tone: MpTone;
  rows: ReadonlyArray<readonly [string, string]>;
}) {
  return (
    <div style={{ ...styles.readinessCard, borderLeftColor: `var(--mp-${tone === "mute" ? "mute" : tone})` }}>
      <div style={styles.readEyebrow}>{title}</div>
      <div style={styles.readSub}>{subtitle}</div>
      <div><Badge tone={tone} dot>{status}</Badge></div>
      <KV compact rows={rows} />
      <div><DemoChip tight /></div>
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
  primaryBtn: {
    fontSize: "var(--font-size-sm)", fontWeight: 600, padding: "8px 14px",
    backgroundColor: "var(--mp-accent)", color: "var(--mp-card)",
    border: "1px solid var(--mp-accent)", borderRadius: "var(--radius-sm)", cursor: "pointer",
  },
  readinessGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "var(--space-3)",
    minWidth: 0,
  },
  readinessCard: {
    backgroundColor: "var(--mp-card)", border: "1px solid var(--mp-rule)",
    borderLeft: "2px solid var(--mp-mute)", borderRadius: "var(--radius-md)",
    padding: "var(--space-4)", display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  readEyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 },
  readSub: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)" },
  body: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
    gap: "var(--space-6)",
    minWidth: 0,
  },
  col: { display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0 },
  tbl: { width: "100%", borderCollapse: "collapse" },
  alertList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  alertRow: {
    display: "grid", gridTemplateColumns: "auto 1fr", gap: "var(--space-3)",
    padding: "var(--space-3) var(--space-4)", backgroundColor: "var(--mp-paper-2)",
    border: "1px solid var(--mp-rule)", borderLeft: "3px solid", borderRadius: "var(--radius-sm)",
    alignItems: "center",
  },
  alertMsg: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.4 },
  alertCode: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", fontFamily: "var(--mp-font-mono)" },
  quickGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" },
  quickBtn: {
    display: "flex", flexDirection: "column", gap: 2, alignItems: "flex-start",
    padding: "var(--space-3) var(--space-4)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)", backgroundColor: "var(--mp-card)", color: "var(--mp-ink)",
    cursor: "pointer", fontSize: "var(--font-size-sm)", textAlign: "left",
  },
  quickLabel: { fontWeight: 600 },
  quickSub: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  facts: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  factRow: { display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "var(--font-size-sm)" },
  factLabel: { color: "var(--mp-ink-2)" },
};
