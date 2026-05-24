import type {
  AgentTeamAnalysisConsoleRead,
  AgentTeamRole,
  AgentTeamRoleOutputRead,
  AgentTeamRunStatus,
  AgentTeamStageRead,
  LLMProviderStatus,
} from "../../types/agentTeam";
import { AGENT_TEAM_STAGE_ORDER } from "../../types/agentTeam";
import type { ReviewActionabilityStatus } from "../../types/tradeReview";

/**
 * AgentTeamAnalysisConsole — renders AgentTeamAnalysisConsoleRead.
 *
 * Safety invariants (Phase 19A):
 *  - Read-only and analysis-only. No execution / buy / sell / submit / cancel.
 *  - `content_markdown` and `final_synthesis` render inside <pre> so no HTML
 *    is interpreted. The frontend never parses these for numbers.
 *  - Broker and market freshness are rendered as parallel, separately-labelled
 *    panels (different scopes — never merged).
 *  - Severity / status pairs always icon + text (never color-only).
 *  - Loose-typed Records (broker_snapshot_freshness, market_quote_freshness,
 *    deterministic_evidence_summary) are rendered verbatim as key/value lists
 *    per the P19A-T2..T5 deferred polish notes.
 */

const ROLE_DISPLAY: Record<AgentTeamRole, string> = {
  fundamentals_analyst: "Fundamentals analyst",
  news_analyst: "News analyst",
  technical_analyst: "Technical analyst",
  risk_management_agent: "Risk management agent",
  portfolio_manager_agent: "Portfolio manager agent",
};

const RUN_STATUS_META: Record<
  AgentTeamRunStatus,
  { icon: string; label: string; cssVar: string }
> = {
  completed: { icon: "●", label: "Completed", cssVar: "var(--mp-live)" },
  partially_completed: { icon: "△", label: "Partially completed", cssVar: "var(--mp-stale)" },
  failed: { icon: "✕", label: "Failed", cssVar: "var(--mp-block)" },
};

const ACTIONABILITY_LABEL: Record<ReviewActionabilityStatus, string> = {
  normal_review: "Normal review",
  analysis_only: "Analysis only",
  manual_confirmation_required: "Manual confirmation required",
  blocked_stale_broker_snapshot: "Blocked — stale broker snapshot",
  blocked_stale_market_quote: "Blocked — stale market quote",
  blocked_unknown_freshness: "Blocked — unknown freshness",
  blocked_provider_error: "Blocked — provider error",
};

const PROVIDER_STATUS_META: Record<
  LLMProviderStatus,
  { icon: string; label: string; cssVar: string }
> = {
  ok: { icon: "●", label: "ok", cssVar: "var(--mp-live)" },
  skipped: { icon: "○", label: "skipped", cssVar: "var(--mp-mute)" },
  failed: { icon: "✕", label: "failed", cssVar: "var(--mp-block)" },
  rate_limited: { icon: "△", label: "rate limited", cssVar: "var(--mp-stale)" },
  quota_exceeded: { icon: "△", label: "quota exceeded", cssVar: "var(--mp-stale)" },
  provider_timeout: { icon: "△", label: "provider timeout", cssVar: "var(--mp-stale)" },
  provider_auth_error: { icon: "⚠", label: "provider auth error", cssVar: "var(--mp-info)" },
  provider_unavailable: { icon: "△", label: "provider unavailable", cssVar: "var(--mp-stale)" },
  invalid_response: { icon: "△", label: "invalid response", cssVar: "var(--mp-stale)" },
  safety_validation_failed: { icon: "✕", label: "safety validation failed", cssVar: "var(--mp-block)" },
};

const ROLE_STATUS_META: Record<
  AgentTeamRoleOutputRead["status"],
  { icon: string; cssVar: string; label: string }
> = {
  completed: { icon: "●", label: "completed", cssVar: "var(--mp-live)" },
  unavailable: { icon: "△", label: "unavailable", cssVar: "var(--mp-stale)" },
  skipped: { icon: "○", label: "skipped", cssVar: "var(--mp-mute)" },
};

export default function AgentTeamAnalysisConsole({
  data,
}: {
  data: AgentTeamAnalysisConsoleRead;
}) {
  return (
    <div style={styles.wrap}>
      <HeaderBlock data={data} />
      <SafetyFlagsBlock flags={data.safety_flags} />
      <FreshnessRow
        broker={data.broker_snapshot_freshness}
        market={data.market_quote_freshness}
      />
      <DeterministicEvidenceBlock evidence={data.deterministic_evidence_summary} />
      <RoleOutputsBlock outputs={data.role_outputs} />
      <FinalSynthesisBlock text={data.final_synthesis} />
      <ProviderWarningsBlock warnings={data.provider_warnings} />
      <StagesBlock stages={data.stages} />
    </div>
  );
}

function HeaderBlock({ data }: { data: AgentTeamAnalysisConsoleRead }) {
  const m = RUN_STATUS_META[data.run_status];
  return (
    <section
      style={{ ...styles.header, borderColor: m.cssVar }}
      role="status"
      aria-label={`Agent-team run status: ${m.label}`}
    >
      <div style={styles.headerTopRow}>
        <span style={{ ...styles.runStatusIcon, color: m.cssVar }} aria-hidden="true">
          {m.icon}
        </span>
        <div>
          <p style={styles.headerLabel}>{m.label}</p>
          <p style={styles.headerSub}>
            Flow: <span style={styles.mono}>{data.review_flow_label}</span> · Actionability:{" "}
            <span style={styles.mono}>
              {ACTIONABILITY_LABEL[data.review_actionability_status]}
            </span>
          </p>
          <p style={styles.headerMeta}>
            Run reference: <span style={styles.mono}>{data.run_reference}</span> · Workflow{" "}
            <span style={styles.mono}>{data.workflow_version}</span> · Generated{" "}
            <span style={styles.mono}>{data.generated_at}</span>
          </p>
        </div>
      </div>
      <p style={styles.analysisOnlyNote}>
        Analysis-only output. Not advice, not a recommendation, not a forecast. No order is
        placed and no broker action is taken from this screen.
      </p>
    </section>
  );
}

function SafetyFlagsBlock({ flags }: { flags: string[] }) {
  if (flags.length === 0) {
    return null;
  }
  return (
    <section style={styles.card} aria-label="Safety flags">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Safety flags</span>
        <span style={styles.detTag}>{flags.length}</span>
      </div>
      <ul style={styles.chipRow}>
        {flags.map((f) => (
          <li
            key={f}
            style={{
              ...styles.sevChip,
              color: "var(--mp-stale)",
              borderColor: "var(--mp-stale)",
            }}
          >
            <span aria-hidden="true">△ </span>
            {f}
          </li>
        ))}
      </ul>
    </section>
  );
}

function FreshnessRow({
  broker,
  market,
}: {
  broker: Record<string, unknown>;
  market: Record<string, unknown>;
}) {
  return (
    <div style={styles.freshnessRow}>
      <section style={{ ...styles.card, flex: "1 1 320px" }} aria-label="Broker snapshot freshness">
        <div style={styles.cardHead}>
          <span style={styles.cardTitle}>Broker snapshot freshness</span>
          <span style={styles.scopeBadge}>scope: broker_snapshot</span>
        </div>
        <KeyValueList record={broker} />
      </section>
      <section style={{ ...styles.card, flex: "1 1 320px" }} aria-label="Market quote freshness">
        <div style={styles.cardHead}>
          <span style={styles.cardTitle}>Market quote freshness</span>
          <span style={styles.scopeBadge}>scope: market_quote</span>
        </div>
        <KeyValueList record={market} />
      </section>
    </div>
  );
}

function DeterministicEvidenceBlock({
  evidence,
}: {
  evidence: Record<string, unknown>;
}) {
  return (
    <section style={styles.card} aria-label="Deterministic evidence summary">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Deterministic evidence summary</span>
        <span style={styles.detTag}>counts &amp; categories only</span>
      </div>
      <KeyValueList record={evidence} />
      <p style={styles.cardFoot}>
        Only counts and categories appear here — never values, holdings, or identifiers.
      </p>
    </section>
  );
}

function RoleOutputsBlock({ outputs }: { outputs: AgentTeamRoleOutputRead[] }) {
  // Render in the approved stage order regardless of array order.
  const byRole = new Map(outputs.map((o) => [o.role_name, o]));
  return (
    <section style={styles.card} aria-label="Agent-team role outputs in stage order">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Role outputs</span>
        <span style={styles.detTag}>analysis-only</span>
      </div>
      <ol style={styles.roleList}>
        {AGENT_TEAM_STAGE_ORDER.map((role, idx) => {
          const out = byRole.get(role);
          return (
            <li key={role} style={styles.roleCard}>
              <RoleHeader index={idx + 1} role={role} out={out ?? null} />
              {out
                ? out.status === "completed" && out.content_markdown
                  ? (
                    <pre style={styles.markdownPre}>{out.content_markdown}</pre>
                  )
                  : (
                    <p style={styles.unavailable}>
                      <span aria-hidden="true">○ </span>
                      {out.unavailable_reason ?? `Role ${out.status}.`}
                    </p>
                  )
                : (
                  <p style={styles.unavailable}>
                    <span aria-hidden="true">○ </span>
                    No output produced for this role.
                  </p>
                )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function RoleHeader({
  index,
  role,
  out,
}: {
  index: number;
  role: AgentTeamRole;
  out: AgentTeamRoleOutputRead | null;
}) {
  const ps = out ? PROVIDER_STATUS_META[out.provider_status] : null;
  const rs = out ? ROLE_STATUS_META[out.status] : null;
  return (
    <div style={styles.roleHead}>
      <span style={styles.roleIndex}>
        Stage {index} of {AGENT_TEAM_STAGE_ORDER.length}
      </span>
      <span style={styles.roleName}>{ROLE_DISPLAY[role]}</span>
      {rs && (
        <span style={{ ...styles.sevChip, color: rs.cssVar, borderColor: rs.cssVar }}>
          <span aria-hidden="true">{rs.icon} </span>
          {rs.label}
        </span>
      )}
      {ps && (
        <span
          style={{ ...styles.sevChip, color: ps.cssVar, borderColor: ps.cssVar }}
          title={`provider_status = ${ps.label}`}
        >
          <span aria-hidden="true">{ps.icon} </span>
          provider: {ps.label}
        </span>
      )}
      {out?.is_mock && (
        <span
          style={{ ...styles.sevChip, color: "var(--mp-mute)", borderColor: "var(--mp-mute)" }}
          title="content_markdown was produced by the app-owned mock LLM provider"
        >
          <span aria-hidden="true">⌐ </span>
          mock provider
        </span>
      )}
    </div>
  );
}

function FinalSynthesisBlock({ text }: { text: string | null }) {
  return (
    <section
      style={{ ...styles.card, borderLeft: "3px solid var(--mp-stale)" }}
      aria-label="Final synthesis (analysis-only narrative)"
    >
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Final synthesis</span>
        <span style={styles.detTag}>analysis-only · narrative</span>
      </div>
      <p style={styles.synthesisNote}>
        Narrative summary from the portfolio-manager role, kept structurally separate
        from per-role outputs. Not advice, not a recommendation, not a forecast.
      </p>
      {text ? (
        <pre style={styles.markdownPre}>{text}</pre>
      ) : (
        <p style={styles.unavailable}>
          <span aria-hidden="true">○ </span>
          No final synthesis produced.
        </p>
      )}
    </section>
  );
}

function ProviderWarningsBlock({
  warnings,
}: {
  warnings: AgentTeamAnalysisConsoleRead["provider_warnings"];
}) {
  return (
    <section style={styles.card} aria-label="Provider warnings">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Provider warnings</span>
        <span style={styles.detTag}>{warnings.length}</span>
      </div>
      {warnings.length === 0 ? (
        <p style={styles.emptyMsg}>No provider warnings.</p>
      ) : (
        <ul style={styles.warningList}>
          {warnings.map((w) => (
            <li key={w.code + w.message} style={styles.warningRow}>
              <span style={styles.warningCode}>
                <span aria-hidden="true">△ </span>
                {w.code}
              </span>
              <span style={styles.warningMsg}>{w.message}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function StagesBlock({ stages }: { stages: AgentTeamStageRead[] }) {
  return (
    <section style={styles.card} aria-label="Workflow stages">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Workflow stages</span>
        <span style={styles.detTag}>{stages.length}</span>
      </div>
      {stages.length === 0 ? (
        <p style={styles.emptyMsg}>No stage entries.</p>
      ) : (
        <ol style={styles.stageList}>
          {stages.map((s, i) => (
            <li key={`${s.stage}-${i}`} style={styles.stageRow}>
              <span style={styles.stageIndex}>{i + 1}</span>
              <span style={styles.stageName}>{s.stage}</span>
              <span style={styles.stageStatus}>{s.status}</span>
              {s.role_name && (
                <span style={styles.stageMeta}>role: {ROLE_DISPLAY[s.role_name]}</span>
              )}
              {s.provider_status && (
                <span style={styles.stageMeta}>provider: {s.provider_status}</span>
              )}
              {s.unavailable_reason && (
                <span style={styles.stageReason}>· {s.unavailable_reason}</span>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function KeyValueList({ record }: { record: Record<string, unknown> }) {
  const entries = Object.entries(record);
  if (entries.length === 0) {
    return <p style={styles.emptyMsg}>No data.</p>;
  }
  return (
    <ul style={styles.kvList}>
      {entries.map(([k, v]) => (
        <li key={k} style={styles.kvRow}>
          <span style={styles.kvKey}>{k}</span>
          <span style={styles.kvVal}>{renderValue(v)}</span>
        </li>
      ))}
    </ul>
  );
}

function renderValue(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") return String(v);
  // Render arrays and nested objects as compact JSON so callers see structure
  // without us inventing typed columns the backend doesn't expose.
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}

const styles: Record<string, React.CSSProperties> = {
  wrap: { display: "flex", flexDirection: "column", gap: "var(--space-4)" },
  header: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderLeftWidth: 4,
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
  },
  headerTopRow: {
    display: "flex",
    gap: "var(--space-4)",
    alignItems: "flex-start",
  },
  runStatusIcon: { fontSize: "var(--font-size-lg)", flexShrink: 0, lineHeight: 1.2 },
  headerLabel: {
    fontWeight: 700,
    fontSize: "var(--font-size-base)",
    color: "var(--mp-ink)",
    margin: 0,
  },
  headerSub: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink-2)",
    margin: "var(--space-1) 0 0",
  },
  headerMeta: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: "var(--space-1) 0 0",
  },
  analysisOnlyNote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: 0,
    lineHeight: 1.6,
    fontStyle: "italic",
  },
  card: {
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
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
    color: "var(--mp-ink)",
  },
  cardFoot: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: 0,
    lineHeight: 1.6,
  },
  detTag: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid var(--mp-mute)",
    borderRadius: "var(--radius-sm)",
    color: "var(--mp-mute)",
    fontWeight: 600,
    letterSpacing: "0.04em",
  },
  scopeBadge: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid var(--mp-mute)",
    borderRadius: "var(--radius-sm)",
    color: "var(--mp-mute)",
    fontWeight: 600,
  },
  freshnessRow: { display: "flex", gap: "var(--space-4)", flexWrap: "wrap" },
  chipRow: { margin: 0, padding: 0, listStyle: "none", display: "flex", gap: "var(--space-2)", flexWrap: "wrap" },
  sevChip: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid",
    borderRadius: "var(--radius-sm)",
    fontWeight: 700,
    display: "inline-flex",
    alignItems: "center",
  },
  kvList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  kvRow: { display: "flex", gap: "var(--space-4)", fontSize: "var(--font-size-xs)", alignItems: "baseline" },
  kvKey: { minWidth: 200, color: "var(--mp-mute)" },
  kvVal: { fontFamily: "var(--mp-font-mono, monospace)", color: "var(--mp-ink-2)", wordBreak: "break-all" },
  emptyMsg: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0 },
  mono: { fontFamily: "var(--mp-font-mono, monospace)", color: "var(--mp-ink-2)" },
  roleList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-3)" },
  roleCard: {
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-3) var(--space-4)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
  },
  roleHead: {
    display: "flex",
    gap: "var(--space-2)",
    alignItems: "center",
    flexWrap: "wrap",
  },
  roleIndex: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  roleName: {
    fontWeight: 700,
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink)",
  },
  unavailable: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-mute)",
    margin: 0,
    lineHeight: 1.6,
  },
  markdownPre: {
    margin: 0,
    padding: "var(--space-3) var(--space-4)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    color: "var(--mp-ink-2)",
    fontFamily: "var(--mp-font-mono, monospace)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.6,
  },
  synthesisNote: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0, lineHeight: 1.6 },
  warningList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  warningRow: { display: "flex", flexDirection: "column", gap: "var(--space-1)", fontSize: "var(--font-size-xs)" },
  warningCode: { color: "var(--mp-stale)", fontWeight: 700, fontFamily: "var(--mp-font-mono, monospace)" },
  warningMsg: { color: "var(--mp-ink-2)" },
  stageList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  stageRow: {
    display: "flex",
    gap: "var(--space-3)",
    fontSize: "var(--font-size-xs)",
    alignItems: "baseline",
    flexWrap: "wrap",
  },
  stageIndex: {
    minWidth: 24,
    fontFamily: "var(--mp-font-mono, monospace)",
    color: "var(--mp-mute)",
  },
  stageName: {
    fontWeight: 700,
    color: "var(--mp-ink-2)",
    fontFamily: "var(--mp-font-mono, monospace)",
  },
  stageStatus: {
    fontFamily: "var(--mp-font-mono, monospace)",
    color: "var(--mp-ink-2)",
  },
  stageMeta: { color: "var(--mp-mute)" },
  stageReason: { color: "var(--mp-mute)", fontStyle: "italic" },
};
