import { useState } from "react";
import { Badge, DemoChip, MpIcon, PageHeader, Panel, SafetyStrip, type MpIconName } from "../components/shared/mp";
import AppearanceControl from "../components/layout/AppearanceControl";
import { DEMO_SETTINGS_PROVIDER_INFO } from "../components/demo/modernDeskDemoData";

/**
 * SettingsPage — sectioned settings workspace (P20C-T3).
 *
 * Layout: left settings navigation (220px) + right detail panel (1fr).
 * Only one section is active at a time.
 *
 * Section list aligned to the prototype:
 *   Account, Broker connection, Data freshness,
 *   Agents / LLM, Private alpha status, Analysis disclaimers.
 *
 * Icons: monochrome stroke-based SVGs via MpIcon. No emoji.
 *
 * Safety:
 *  - No broker disconnect/delete/destructive actions.
 *  - No credential storage or input fields.
 *  - No provider API key input or model/provider selection.
 *  - No execution controls.
 *  - No localStorage/sessionStorage writes beyond approved UI-only keys
 *    (poa-appearance, poa-sidebar-collapsed).
 *  - No new API clients or endpoint paths.
 */

type SettingsSection =
  | "account"
  | "broker"
  | "freshness"
  | "agents"
  | "alpha"
  | "disclaimers";

interface SectionMeta {
  id: SettingsSection;
  label: string;
  icon: MpIconName;
}

const SECTIONS: SectionMeta[] = [
  { id: "account",     label: "Account",              icon: "lock" },
  { id: "broker",      label: "Broker connection",    icon: "broker" },
  { id: "freshness",   label: "Data freshness",       icon: "clock" },
  { id: "agents",      label: "Agents / LLM",         icon: "agent" },
  { id: "alpha",       label: "Private alpha status", icon: "shield" },
  { id: "disclaimers", label: "Analysis disclaimers", icon: "info" },
];

export default function SettingsPage() {
  const [active, setActive] = useState<SettingsSection>("account");

  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Workspace · settings"
        title="Settings"
        sub="Preferences for data freshness, analysis availability, and account state. Destructive flows — disconnect broker, delete reports — are intentionally not exposed in this build."
        right={<Badge tone="info" dot>private alpha</Badge>}
      />

      <div style={styles.layout}>
        {/* Left settings navigation */}
        <nav style={styles.nav} aria-label="Settings sections">
          <ul style={styles.navList}>
            {SECTIONS.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => setActive(s.id)}
                  aria-current={active === s.id ? "page" : undefined}
                  style={{
                    ...styles.navItem,
                    ...(active === s.id ? styles.navItemActive : {}),
                  }}
                >
                  <MpIcon
                    name={s.icon}
                    size={13}
                    style={{ color: active === s.id ? "var(--mp-accent)" : "var(--mp-mute)" }}
                  />
                  <span>{s.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Right detail panel */}
        <main style={styles.detail}>
          {active === "account" && <AccountSection />}
          {active === "broker" && <BrokerSection />}
          {active === "freshness" && <FreshnessSection />}
          {active === "agents" && <AgentsSection />}
          {active === "alpha" && <AlphaSection />}
          {active === "disclaimers" && <DisclaimersSection />}
        </main>
      </div>

      <SafetyStrip items={[
        "Read-only",
        "Analysis-only",
        "No broker order placement",
        "No destructive provider controls",
      ]} />
    </div>
  );
}

/* ── Section components ─────────────────────────────────────────────────── */

function AccountSection() {
  return (
    <>
      <Panel title="Account" tag="private alpha" right={<DemoChip />}>
        <SettingsRow
          title="Status"
          right={<Badge tone="info" dot>Private alpha</Badge>}
        />
        <p style={styles.body}>
          Account profile, operator mode, and scope details will appear here
          once a reviewed backend contract exists (P20B-T6). During private
          alpha the app operates as a single-user local instance with no
          authentication or account management.
        </p>
        <p style={styles.note}>
          No signup, billing, waitlist, or invite flow is exposed from this
          screen.
        </p>
      </Panel>

      <Panel title="Appearance" tag="local-only · UI preference">
        <p style={styles.body}>
          Switch between System, Light, and Dark. Your choice is stored in{" "}
          <code style={styles.code}>localStorage</code> only (key{" "}
          <code style={styles.code}>poa-appearance</code>) — no portfolio, broker,
          or analysis data is persisted in browser storage.
        </p>
        <AppearanceControl />
      </Panel>

      <FutureRows items={[
        { label: "Session lifetime", description: "Session duration configuration. Requires auth backend contract." },
        { label: "Profile editing", description: "Display name, avatar, and notification email. Requires auth backend contract." },
      ]} />
    </>
  );
}

function BrokerSection() {
  return (
    <>
      <Panel title="Broker connection" tag="read-only · scope" right={<DemoChip />}>
        <p style={styles.body}>
          When a broker account is connected, the app receives read-only data only.
          No order placement, cancellation, or modification is possible from this
          application.
        </p>
        <ul style={styles.scopeList}>
          <ScopeRow allowed label="Read-only positions, cash state, and option contracts via broker OAuth" />
          <ScopeRow allowed label="Lot-level cost basis where available" />
          <ScopeRow allowed={false} label="Order placement" />
          <ScopeRow allowed={false} label="Order cancellation or modification" />
          <ScopeRow allowed={false} label="Withdrawals, transfers, or any movement of funds" />
        </ul>
        <p style={styles.note}>
          Broker auth happens inside the broker's own portal, not in this app.
          Disconnect / delete-broker flows are intentionally not exposed.
        </p>
      </Panel>

      <FutureRows items={[
        { label: "Broker account management", description: "Disconnect, reconnect, and account lifecycle controls. Requires reviewed backend contract." },
      ]} />
    </>
  );
}

function FreshnessSection() {
  return (
    <>
      <Panel title="Broker snapshot freshness" tag="informational">
        <SettingsRow title="Scope" sub="broker_snapshot" mono />
        <p style={styles.body}>
          Broker-snapshot freshness measures how recently the app received
          position and cash data from the connected broker. Stale snapshots
          can cause reviews to be flagged or blocked.
        </p>
        <p style={styles.note}>
          Freshness thresholds are tuned server-side. A user-facing preference
          surface will land once the backend contract is reviewed.
        </p>
      </Panel>

      <Panel title="Market quote freshness" tag="separate scope">
        <SettingsRow title="Scope" sub="market_quote" mono />
        <p style={styles.body}>
          Market-quote freshness is a separate scope from broker snapshots.
          It measures how recently the app received market price data.
          Unknown or unavailable market freshness can limit review quality.
        </p>
        <p style={styles.note}>
          Market data mode and freshness interpretation are configured
          server-side during alpha.
        </p>
      </Panel>

      <FutureRows items={[
        { label: "Snapshot age thresholds", description: "Warn and block thresholds for broker-snapshot and market-quote freshness." },
        { label: "Auto-resync on workspace open", description: "Trigger a broker sync request when opening Overview or a new Trade Review." },
        { label: "Market data mode", description: "Choose between not_configured, delayed, or realtime_via_broker." },
      ]} />
    </>
  );
}

function AgentsSection() {
  return (
    <>
      <Panel title="Agent / LLM availability" tag="informational" right={<DemoChip />}>
        <SettingsRow title="Provider" sub={DEMO_SETTINGS_PROVIDER_INFO.provider} mono />
        <SettingsRow title="Workflow version" sub={DEMO_SETTINGS_PROVIDER_INFO.workflowVersion} mono />
        <SettingsRow title="Roles enabled" sub={DEMO_SETTINGS_PROVIDER_INFO.rolesEnabled.join(", ")} mono />
        <p style={styles.note}>
          Real-provider opt-in is gated by the operator and configured
          server-side. This view is informational only — no API key input,
          model selection, or provider toggle is exposed here.
        </p>
      </Panel>

      <FutureRows items={[
        { label: "Provider selection", description: "Choose between mock, live, or off. Requires operator approval." },
        { label: "Role toggles", description: "Enable/disable individual agent-team roles." },
        { label: "Workflow version pinning", description: "Pin or upgrade the agent-team workflow version." },
      ]} />
    </>
  );
}

function AlphaSection() {
  return (
    <Panel title="Private alpha status" tag="invite-gated" accent right={<DemoChip />}>
      <SettingsRow title="Plan" sub="Personal preview" />
      <SettingsRow
        title="Account state"
        right={<Badge tone="info" dot>private-alpha · single user</Badge>}
      />
      <p style={styles.note}>
        Read-only and analysis-only. No order placement. Manual decision support
        only. No signup, billing, waitlist, or invite flow is exposed. Visible
        to operators only, used for invite gating. Account and profile data
        require a reviewed backend contract (P20B-T6).
      </p>
    </Panel>
  );
}

function DisclaimersSection() {
  return (
    <>
      <Panel title="Analysis-only disclaimers" tag="always-on" right={<Badge tone="info" dot={false}>non-removable</Badge>}>
        <ol style={styles.disclaimerList}>
          {DISCLAIMERS.map((text, i) => (
            <li key={i} style={styles.disclaimerRow}>
              <span style={styles.disclaimerNum}>{String(i + 1).padStart(2, "0")}.</span>
              <span>{text}</span>
            </li>
          ))}
        </ol>
      </Panel>

      <Panel title="Where these appear" tag="surface map">
        <div style={styles.surfaceMap}>
          {DISCLAIMER_SURFACES.map(([surface, desc]) => (
            <div key={surface} style={styles.surfaceRow}>
              <span style={styles.surfaceLabel}>{surface}</span>
              <span style={styles.surfaceDesc}>{desc}</span>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Data and privacy boundaries" tag="what this app does and does not do">
        <section style={styles.subSection}>
          <h3 style={styles.subTitle}>Browser storage</h3>
          <ul style={styles.boundaryList}>
            <li>
              <code style={styles.code}>poa-appearance</code> — UI theme preference
              (system / light / dark).
            </li>
            <li>
              <code style={styles.code}>poa-sidebar-collapsed</code> — sidebar
              collapse state.
            </li>
            <li>No portfolio, broker, analysis, credential, or account data in browser storage.</li>
          </ul>
        </section>
      </Panel>
    </>
  );
}

const DISCLAIMERS = [
  "Portfolio Copilot is analysis-only and read-only by design.",
  "No order placement, cancellation, modification, or execution is possible from any screen in this app.",
  "Outputs are not investment advice, recommendations, or forecasts.",
  "Broker snapshot freshness and market quote freshness are two separate scopes — both are surfaced where they matter.",
  "Agent outputs are commentary on top of deterministic facts; the deterministic Python services remain the source of truth.",
  "Past performance — yours, the market's, or the model's — does not promise future outcomes.",
];

const DISCLAIMER_SURFACES: readonly [string, string][] = [
  ["Trade Review", "Below results, on every banner that gates actionability."],
  ["Agent Console", "On the evidence rail, every agent card, and the run header."],
  ["Reports", "On every saved report, frozen at the time of the review."],
  ["Landing", "On the hero strip and the safety section."],
  ["Dashboard", "On the readiness strip and every panel header."],
];

/* ── Shared: settings row ─────────────────────────────────────────────── */

function SettingsRow({ title, sub, right, mono }: {
  title: string;
  sub?: string;
  right?: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div style={styles.settingsRow}>
      <span style={styles.rowLabel}>{title}</span>
      {sub && (
        <span style={{
          ...styles.rowValue,
          ...(mono ? { fontFamily: "var(--mp-font-mono, monospace)" } : {}),
        }}>
          {sub}
        </span>
      )}
      {right && <div style={styles.rowRight}>{right}</div>}
    </div>
  );
}

/* ── Shared: scope row ─────────────────────────────────────────────────── */

function ScopeRow({ allowed, label }: { allowed: boolean; label: string }) {
  return (
    <li style={styles.scopeRow}>
      <MpIcon
        name={allowed ? "check" : "x"}
        size={13}
        style={{ color: allowed ? "var(--mp-live)" : "var(--mp-block)" }}
      />
      <span style={{ color: allowed ? "var(--mp-ink-2)" : "var(--mp-mute)" }}>{label}</span>
    </li>
  );
}

/* ── Shared: future disabled rows ──────────────────────────────────────── */

function FutureRows({ items }: { items: { label: string; description: string }[] }) {
  return (
    <div style={styles.futureWrap}>
      {items.map((item) => (
        <button
          key={item.label}
          type="button"
          disabled
          style={styles.futureBtn}
          title="Not yet active — requires reviewed backend contract"
          aria-disabled="true"
        >
          <div style={styles.futureLeft}>
            <MpIcon name="circle" size={12} style={{ color: "var(--mp-mute)", marginTop: 2 }} />
            <div style={{ minWidth: 0 }}>
              <span style={styles.futureLabel}>{item.label}</span>
              <span style={styles.futureDesc}>{item.description}</span>
            </div>
          </div>
          <span style={styles.futureBadge}>not yet active</span>
        </button>
      ))}
    </div>
  );
}

/* ── Styles ──────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex", flexDirection: "column", gap: "var(--space-5)",
    maxWidth: 1280, margin: "0 auto", color: "var(--mp-ink)",
  },
  layout: {
    display: "grid",
    gridTemplateColumns: "220px minmax(0, 1fr)",
    gap: "var(--space-5)",
    alignItems: "start",
    minWidth: 0,
  },
  /* Navigation */
  nav: {
    position: "sticky",
    top: "var(--space-4)",
    alignSelf: "flex-start",
  },
  navList: {
    listStyle: "none", margin: 0, padding: 0,
    display: "flex", flexDirection: "column", gap: 2,
  },
  navItem: {
    display: "flex", alignItems: "center", gap: 10,
    width: "100%", textAlign: "left",
    padding: "10px 12px",
    border: "1px solid transparent",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "transparent",
    color: "var(--mp-ink-2)",
    fontSize: 13, fontWeight: 450,
    fontFamily: "inherit",
    cursor: "pointer",
    lineHeight: 1.4,
  },
  navItemActive: {
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    color: "var(--mp-ink)",
    fontWeight: 600,
  },
  /* Detail panel */
  detail: {
    display: "flex", flexDirection: "column", gap: "var(--space-4)",
    minWidth: 0,
    overflow: "hidden",
  },
  /* Settings row (prototype Row pattern) */
  settingsRow: {
    display: "flex", flexWrap: "wrap", alignItems: "center",
    justifyContent: "space-between", gap: "var(--space-3)",
    padding: "var(--space-3) 0",
    borderBottom: "1px solid var(--mp-rule)",
  },
  rowLabel: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", flexShrink: 0 },
  rowValue: {
    fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)",
    textAlign: "right", wordBreak: "break-word", minWidth: 0,
  },
  rowRight: { flexShrink: 0 },
  /* Content styles */
  body: {
    fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)",
    lineHeight: 1.6, margin: 0,
  },
  code: {
    fontSize: "var(--font-size-xs)",
    fontFamily: "var(--mp-font-mono, monospace)",
    backgroundColor: "var(--mp-paper-2)",
    padding: "1px 4px",
    borderRadius: 3,
  },
  note: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    lineHeight: 1.6, margin: 0, marginTop: "var(--space-2)",
  },
  boundaryList: {
    fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)",
    lineHeight: 1.6, margin: 0, paddingLeft: "var(--space-5)",
    display: "flex", flexDirection: "column", gap: "var(--space-1)",
  },
  subSection: {
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  subTitle: {
    fontSize: "var(--font-size-sm)", fontWeight: 600,
    color: "var(--mp-ink)", margin: 0,
    textTransform: "uppercase", letterSpacing: "0.06em",
  },
  /* Scope list (broker) */
  scopeList: {
    listStyle: "none", margin: 0, padding: 0,
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  scopeRow: {
    display: "flex", alignItems: "center", gap: 10,
    fontSize: "var(--font-size-sm)",
  },
  /* Disclaimers */
  disclaimerList: {
    listStyle: "none", margin: 0, padding: 0,
    display: "flex", flexDirection: "column", gap: "var(--space-3)",
  },
  disclaimerRow: {
    display: "grid", gridTemplateColumns: "auto 1fr", gap: "var(--space-3)",
    fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.6,
  },
  disclaimerNum: {
    fontFamily: "var(--mp-font-mono, monospace)",
    color: "var(--mp-accent)",
    fontSize: "var(--font-size-xs)",
  },
  surfaceMap: {
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  surfaceRow: {
    display: "grid", gridTemplateColumns: "minmax(100px, 140px) 1fr", gap: "var(--space-4)",
    fontSize: "var(--font-size-sm)",
  },
  surfaceLabel: { color: "var(--mp-mute)" },
  surfaceDesc: { color: "var(--mp-ink-2)", minWidth: 0, overflowWrap: "anywhere" },
  /* Future settings rows */
  futureWrap: {
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
  },
  futureBtn: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    gap: "var(--space-3)", width: "100%", textAlign: "left",
    padding: "var(--space-3) var(--space-4)",
    border: "1px dashed var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
    opacity: 0.55,
    cursor: "not-allowed",
    fontFamily: "inherit",
  },
  futureLeft: {
    display: "flex", gap: "var(--space-3)", alignItems: "flex-start",
    minWidth: 0,
  },
  futureLabel: {
    display: "block", fontSize: "var(--font-size-sm)",
    fontWeight: 600, color: "var(--mp-ink-2)",
  },
  futureDesc: {
    display: "block", fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)", lineHeight: 1.5,
    overflowWrap: "anywhere",
  },
  futureBadge: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px dashed var(--mp-mute)",
    borderRadius: "var(--radius-sm)",
    color: "var(--mp-mute)",
    fontWeight: 600,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    whiteSpace: "nowrap",
    flexShrink: 0,
  },
};
