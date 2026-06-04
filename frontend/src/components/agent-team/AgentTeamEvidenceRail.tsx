import type {
  AgentTeamAnalysisConsoleRead,
  AgentTeamStageRead,
} from "../../types/agentTeam";
import type { ReviewActionabilityStatus } from "../../types/tradeReview";
import { Badge, KV, Panel, type MpTone } from "../shared/mp";
import { MpIcon } from "../shared/mp";

/**
 * AgentTeamEvidenceRail — right deterministic evidence rail (P20C-T5).
 *
 * Shows backend-provided deterministic evidence summary, actionability,
 * broker snapshot freshness, market quote freshness, safety labels,
 * and workflow stages in a compact right rail.
 *
 * Broker snapshot freshness and market quote freshness remain separate.
 * No frontend financial computation. Loose-typed Records rendered verbatim
 * as key/value lists per P19A deferred polish notes.
 */

const ACTIONABILITY_LABEL: Record<ReviewActionabilityStatus, string> = {
  normal_review: "Normal review",
  analysis_only: "Analysis only",
  manual_confirmation_required: "Manual confirmation required",
  blocked_stale_broker_snapshot: "Blocked — stale broker snapshot",
  blocked_stale_market_quote: "Blocked — stale market quote",
  blocked_unknown_freshness: "Blocked — unknown freshness",
  blocked_provider_error: "Blocked — provider error",
};

function actionabilityTone(status: ReviewActionabilityStatus): MpTone {
  if (status.startsWith("blocked")) return "block";
  if (status === "manual_confirmation_required") return "stale";
  if (status === "analysis_only") return "info";
  return "live";
}

export default function AgentTeamEvidenceRail({
  data,
}: {
  data: AgentTeamAnalysisConsoleRead;
}) {
  return (
    <div style={styles.wrap}>
      {/* Actionability */}
      <Panel title="Actionability" tag="status">
        <div style={styles.badgeRow}>
          <Badge tone={actionabilityTone(data.review_actionability_status)} dot>
            {ACTIONABILITY_LABEL[data.review_actionability_status]}
          </Badge>
        </div>
      </Panel>

      {/* Broker snapshot freshness — separate scope */}
      <Panel title="Broker snapshot" tag="freshness">
        <KeyValueList record={data.broker_snapshot_freshness} />
        <span style={styles.scopeLabel}>
          <MpIcon name="clock" size={10} style={{ verticalAlign: "middle", marginRight: 3 }} />
          scope: broker_snapshot
        </span>
      </Panel>

      {/* Market quote freshness — separate scope */}
      <Panel title="Market quotes" tag="freshness">
        <KeyValueList record={data.market_quote_freshness} />
        <span style={styles.scopeLabel}>
          <MpIcon name="clock" size={10} style={{ verticalAlign: "middle", marginRight: 3 }} />
          scope: market_quote
        </span>
      </Panel>

      {/* Deterministic evidence summary */}
      <Panel title="Evidence summary" tag="deterministic">
        <KeyValueList record={data.deterministic_evidence_summary} />
        <p style={styles.foot}>
          <MpIcon name="info" size={10} style={{ verticalAlign: "middle", marginRight: 3 }} />
          Counts and categories only — never values, holdings, or identifiers.
        </p>
      </Panel>

      {/* Safety labels */}
      <Panel title="Safety labels">
        <div style={styles.safetyList}>
          {[
            { label: "Analysis only", icon: "shield" as const, tone: "var(--mp-live)" },
            { label: "Manual trade review", icon: "info" as const, tone: "var(--mp-info)" },
            { label: "Not an order recommendation", icon: "shield" as const, tone: "var(--mp-mute)" },
            { label: "Data freshness may affect quality", icon: "clock" as const, tone: "var(--mp-stale)" },
          ].map((item) => (
            <div key={item.label} style={styles.safetyRow}>
              <MpIcon name={item.icon} size={12} style={{ color: item.tone, flexShrink: 0 }} />
              <span style={styles.safetyLabel}>{item.label}</span>
            </div>
          ))}
        </div>
      </Panel>

      {/* Workflow stages */}
      {data.stages.length > 0 && (
        <Panel title="Workflow stages" tag={String(data.stages.length)}>
          <StageList stages={data.stages} />
        </Panel>
      )}
    </div>
  );
}

/* ── Key-value list for loose-typed Records ─────────────────────────────── */

function KeyValueList({ record }: { record: Record<string, unknown> }) {
  const entries = Object.entries(record);
  if (entries.length === 0) {
    return <p style={styles.emptyMsg}>No data.</p>;
  }
  return (
    <KV
      compact
      rows={entries.map(([k, v]) => [k, renderValue(v)])}
    />
  );
}

function renderValue(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") return String(v);
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}

/* ── Stage list ─────────────────────────────────────────────────────────── */

function StageList({ stages }: { stages: AgentTeamStageRead[] }) {
  return (
    <ol style={styles.stageList}>
      {stages.map((s, i) => (
        <li key={`${s.stage}-${i}`} style={styles.stageRow}>
          <span style={styles.stageIndex}>{i + 1}</span>
          <div style={styles.stageBody}>
            <span style={styles.stageName}>{s.stage}</span>
            <span style={styles.stageStatus}>{s.status}</span>
            {/* Backend-owned persona label verbatim when present; for null
                display_name stages keep the deterministic stage/status only —
                never surface the machine role_name or invent a persona. */}
            {s.display_name && (
              <span style={styles.stageMeta}>{s.display_name}</span>
            )}
            {s.provider_status && (
              <span style={styles.stageMeta}>provider: {s.provider_status}</span>
            )}
            {s.unavailable_reason && (
              <span style={styles.stageReason}>
                <MpIcon name="info" size={9} style={{ verticalAlign: "middle", marginRight: 2 }} />
                {s.unavailable_reason}
              </span>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}

/* ── Styles ──────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    display: "flex", flexDirection: "column", gap: "var(--space-3)",
  },
  badgeRow: {
    display: "flex", gap: "var(--space-2)", flexWrap: "wrap",
  },
  scopeLabel: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    fontFamily: "var(--mp-font-mono, monospace)",
  },
  foot: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: 0,
    lineHeight: 1.6,
  },
  emptyMsg: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: 0,
  },
  safetyList: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
  },
  safetyRow: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-ink-2)",
  },
  safetyLabel: {
    lineHeight: 1.4,
  },
  stageList: {
    margin: 0, padding: 0, listStyle: "none",
    display: "flex", flexDirection: "column", gap: "var(--space-1)",
  },
  stageRow: {
    display: "grid",
    gridTemplateColumns: "20px 1fr",
    gap: "var(--space-2)",
    fontSize: "var(--font-size-xs)",
    alignItems: "baseline",
  },
  stageIndex: {
    fontFamily: "var(--mp-font-mono, monospace)",
    color: "var(--mp-mute)",
    textAlign: "right",
  },
  stageBody: {
    display: "flex", flexDirection: "column", gap: 1, minWidth: 0,
  },
  stageName: {
    fontWeight: 700,
    color: "var(--mp-ink-2)",
    fontFamily: "var(--mp-font-mono, monospace)",
    wordBreak: "break-all",
  },
  stageStatus: {
    fontFamily: "var(--mp-font-mono, monospace)",
    color: "var(--mp-ink-2)",
  },
  stageMeta: { color: "var(--mp-mute)", fontSize: "var(--font-size-xs)" },
  stageReason: { color: "var(--mp-mute)", fontStyle: "italic", fontSize: "var(--font-size-xs)" },
};
