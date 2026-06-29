/**
 * ToolMediatedEvidence — P33A-T6B.
 *
 * Renders the frozen, safe-subset tool-mediated run artifact as a secondary
 * supporting-provenance band beneath the report narrative and deterministic
 * provenance. Per the P33A-T6A Codex B read-contract decision it shows ONLY
 * approved fields: a persistent "Demo evidence · mock tools" badge while mock,
 * the frozen timestamp, open questions, audited role findings, and — in a
 * collapsed disclosure — a "Sources checked" list plus minimal audit metadata.
 *
 * It never renders summary_payload, raw scope, planner internals, auditor
 * internals, or any raw id/value/payload/URL/trace; it never derives auditor
 * counts. Codes are humanized (raw kept in `title`); citation labels map to the
 * source/evidence label, not raw refs. Everything is read from the saved
 * artifact — no recompute, no live calls. Read-only; no order/advice wording.
 */
import { MpIcon } from "../shared/mp";
import type { MpIconName } from "../shared/mp/MpIcon";
import Timestamp from "../shared/Timestamp";
import type {
  SavedToolMediatedEvidenceAvailability,
  SavedToolMediatedRoleFindingSetRead,
  SavedToolMediatedRunArtifactRead,
  SavedToolMediatedSourceRead,
} from "../../types/api";
import { evidenceKeyLabel, humanizeCode, roleStatusIcon, scopeNoteLabel } from "./reportStatus";

export default function ToolMediatedEvidence({
  artifact,
}: {
  artifact: SavedToolMediatedRunArtifactRead;
}) {
  const isMock =
    artifact.provider_mode === "tool_mediated_mock" ||
    artifact.tool_results.some((source) => source.is_mock);
  const openQuestions = artifact.open_questions ?? [];
  const findingSets = artifact.audited_findings ?? [];
  const sources = artifact.tool_results ?? [];
  const warningCodes = artifact.warning_codes ?? [];
  const synthesisRefs = artifact.synthesis_evidence_references ?? [];

  return (
    <section style={styles.wrap} aria-label="Tool-mediated evidence and audit">
      <header style={styles.heading}>
        <MpIcon name="spark" size={15} style={styles.headingIcon} />
        <h3 style={styles.headingText}>Tool-mediated evidence &amp; audit</h3>
        {isMock && (
          <span style={styles.demoBadge}>
            <MpIcon name="info" size={11} style={styles.badgeIcon} />
            Demo evidence · mock tools
          </span>
        )}
      </header>
      <p style={styles.note}>
        Frozen evidence gathered by analysis tools for this saved review. Read-only
        and historical — it is not live external research.
      </p>
      <p style={styles.frozenRow}>
        <MpIcon name="clock" size={12} style={styles.frozenIcon} />
        <span>
          Frozen snapshot · <Timestamp iso={artifact.frozen_at} prefix="" />
        </span>
      </p>

      {openQuestions.length > 0 && (
        <div style={styles.block}>
          <span style={styles.blockLabel}>Open questions</span>
          <ul style={styles.questionList}>
            {openQuestions.map((question, i) => (
              <li key={i} style={styles.questionItem}>
                {question}
              </li>
            ))}
          </ul>
        </div>
      )}

      {findingSets.length > 0 && (
        <div style={styles.block}>
          <span style={styles.blockLabel}>Audited findings</span>
          <div style={styles.findingSets}>
            {findingSets.map((set) => (
              <FindingSet key={set.role_name} set={set} />
            ))}
          </div>
        </div>
      )}

      <details className="mp-disclosure" style={styles.details}>
        <summary style={styles.summary}>
          <MpIcon
            name="chevron-r"
            size={14}
            className="mp-disclosure-chevron"
            style={{ color: "var(--mp-mute)" }}
          />
          Sources &amp; audit detail
        </summary>

        {sources.length > 0 && (
          <div style={styles.block}>
            <span style={styles.blockLabel}>Sources checked</span>
            <ul style={styles.sourceList}>
              {sources.map((source, i) => (
                <SourceRow key={`${source.tool_name}-${source.role_name}-${i}`} source={source} />
              ))}
            </ul>
          </div>
        )}

        <dl style={styles.auditGrid}>
          <div style={styles.auditRow}>
            <dt style={styles.auditLabel}>Tools run</dt>
            <dd style={styles.auditValue}>{artifact.tool_result_count}</dd>
          </div>
        </dl>

        {synthesisRefs.length > 0 && (
          <div style={styles.block}>
            <span style={styles.blockLabel}>Evidence referenced by synthesis</span>
            <ul style={styles.chipList}>
              {synthesisRefs.map((ref) => (
                <li key={ref} style={styles.evidenceChip} title={ref}>
                  {evidenceKeyLabel(ref)}
                </li>
              ))}
            </ul>
          </div>
        )}

        {warningCodes.length > 0 && (
          <div style={styles.block}>
            <span style={styles.blockLabel}>Notes</span>
            <ul style={styles.codeList}>
              {warningCodes.map((code) => (
                <li key={code} style={styles.codeChip} title={code}>
                  {scopeNoteLabel(code)}
                </li>
              ))}
            </ul>
          </div>
        )}
      </details>
    </section>
  );
}

function FindingSet({ set }: { set: SavedToolMediatedRoleFindingSetRead }) {
  const unavailable = set.role_status === "unavailable" || set.findings.length === 0;
  return (
    <div style={styles.findingSet}>
      <div style={styles.findingSetHead}>
        <MpIcon name={roleStatusIcon(set.role_status)} size={12} style={styles.findingStatusIcon} />
        <span style={styles.findingRole}>{humanizeCode(set.role_name)}</span>
        <span style={styles.findingStatus}>{humanizeCode(set.role_status)}</span>
      </div>
      {unavailable ? (
        <p style={styles.gapText}>
          {set.unavailable_reason
            ? humanizeCode(set.unavailable_reason)
            : "Not available — no findings recorded."}
        </p>
      ) : (
        <ul style={styles.findingList}>
          {set.findings.map((finding, i) => (
            <li key={i} style={styles.findingItem}>
              <span style={styles.findingClaim}>{finding.claim_text}</span>
              <span style={styles.findingMeta}>
                <span style={styles.findingType}>{humanizeCode(finding.finding_type)}</span>
                {finding.evidence_refs.map((ref) => (
                  <span key={ref} style={styles.citationChip} title={ref}>
                    {evidenceKeyLabel(ref)}
                  </span>
                ))}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function SourceRow({ source }: { source: SavedToolMediatedSourceRead }) {
  const avail = availabilityMeta(source.availability);
  const gap = source.availability === "not_available";
  return (
    <li style={{ ...styles.sourceRow, ...(gap ? styles.sourceRowGap : null) }}>
      <div style={styles.sourceTop}>
        <span style={styles.sourceLabel}>{source.source_label}</span>
        <span style={styles.sourceTier}>{humanizeCode(source.evidence_tier)}</span>
        {source.is_mock && <span style={styles.mockTag}>Mock</span>}
      </div>
      <div style={styles.sourceMeta}>
        <span style={styles.availChip}>
          <MpIcon name={avail.icon} size={11} style={styles.availIcon} />
          {avail.label}
        </span>
        {source.freshness && (
          <>
            <span style={styles.metaDot} aria-hidden="true">·</span>
            <span>{humanizeCode(source.freshness)}</span>
          </>
        )}
        {source.as_of && (
          <>
            <span style={styles.metaDot} aria-hidden="true">·</span>
            <Timestamp iso={source.as_of} prefix="as of " />
          </>
        )}
      </div>
      {source.caveat_codes.length > 0 && (
        <ul style={styles.codeList}>
          {source.caveat_codes.map((code) => (
            <li key={code} style={styles.codeChip} title={code}>
              {scopeNoteLabel(code)}
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

function availabilityMeta(
  availability: SavedToolMediatedEvidenceAvailability,
): { icon: MpIconName; label: string } {
  switch (availability) {
    case "available":
      return { icon: "check", label: "Available" };
    case "limited":
      return { icon: "info", label: "Limited" };
    case "not_available":
      return { icon: "alert", label: "Not available" };
    case "not_reviewed":
      return { icon: "circle", label: "Not reviewed" };
    case "not_applicable":
      return { icon: "circle", label: "Not applicable" };
    default:
      return { icon: "circle", label: "Unknown" };
  }
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-5)",
    background: "var(--reports-soft-surface)",
    minWidth: 0,
  },
  heading: { display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" },
  headingIcon: { color: "var(--mp-mute)", flexShrink: 0 },
  headingText: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-md)",
    fontWeight: 600,
  },
  demoBadge: {
    display: "inline-flex",
    alignItems: "center",
    color: "var(--mp-mute)",
    background: "var(--reports-card-surface)",
    border: "1px dashed var(--reports-rule-strong)",
    borderRadius: 999,
    padding: "1px 8px",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.02em",
  },
  badgeIcon: { marginRight: 4, verticalAlign: "middle" },
  note: { margin: 0, color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", lineHeight: 1.6 },
  frozenRow: {
    margin: 0,
    display: "flex",
    alignItems: "center",
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-xs)",
  },
  frozenIcon: { color: "var(--mp-mute)", marginRight: 5, flexShrink: 0 },
  block: { display: "flex", flexDirection: "column", gap: 6, minWidth: 0 },
  blockLabel: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
  },
  questionList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 4 },
  questionItem: {
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-sm)",
    lineHeight: 1.5,
    paddingLeft: "var(--space-3)",
    borderLeft: "2px solid var(--reports-rule-strong)",
  },
  findingSets: { display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  findingSet: {
    display: "flex",
    flexDirection: "column",
    gap: 5,
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-3)",
    background: "var(--reports-card-surface)",
    minWidth: 0,
  },
  findingSetHead: { display: "flex", alignItems: "center", gap: 6, minWidth: 0 },
  findingStatusIcon: { color: "var(--mp-mute)", flexShrink: 0 },
  findingRole: { color: "var(--mp-ink)", fontSize: "var(--font-size-sm)", fontWeight: 700 },
  findingStatus: { color: "var(--mp-mute)", fontSize: "var(--font-size-xs)" },
  findingList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 6 },
  findingItem: { display: "flex", flexDirection: "column", gap: 3, minWidth: 0 },
  findingClaim: { color: "var(--mp-ink)", fontSize: "var(--font-size-sm)", lineHeight: 1.5 },
  findingMeta: { display: "flex", alignItems: "center", flexWrap: "wrap", gap: 6 },
  findingType: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  gapText: { margin: 0, color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", fontStyle: "italic" },
  details: { minWidth: 0 },
  summary: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    cursor: "pointer",
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  sourceList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 6 },
  sourceRow: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-3)",
    background: "var(--reports-card-surface)",
    minWidth: 0,
  },
  sourceRowGap: { background: "var(--reports-soft-surface)", borderStyle: "dashed" },
  sourceTop: { display: "flex", alignItems: "center", flexWrap: "wrap", gap: 8, minWidth: 0 },
  sourceLabel: { color: "var(--mp-ink)", fontSize: "var(--font-size-sm)", fontWeight: 600, overflowWrap: "anywhere" },
  sourceTier: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  mockTag: {
    color: "var(--mp-mute)",
    border: "1px dashed var(--reports-rule-strong)",
    borderRadius: 999,
    padding: "0 6px",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
  },
  sourceMeta: {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 6,
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-xs)",
  },
  availChip: { display: "inline-flex", alignItems: "center", color: "var(--mp-ink-2)" },
  availIcon: { marginRight: 4, verticalAlign: "middle", color: "var(--mp-mute)" },
  metaDot: { color: "var(--mp-mute)" },
  auditGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "var(--space-2)",
    margin: "var(--space-3) 0 var(--space-2)",
  },
  auditRow: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-3)",
    background: "var(--reports-card-surface)",
    minWidth: 0,
  },
  auditLabel: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.05em",
    textTransform: "uppercase",
  },
  auditValue: { margin: 0, color: "var(--mp-ink)", fontSize: "var(--font-size-sm)" },
  chipList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexWrap: "wrap", gap: 6 },
  evidenceChip: {
    color: "var(--mp-ink-2)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "2px 8px",
    fontSize: "var(--font-size-xs)",
    background: "var(--reports-card-surface)",
    overflowWrap: "anywhere",
  },
  citationChip: {
    color: "var(--mp-ink-2)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "0 6px",
    fontSize: "var(--font-size-xs)",
    background: "var(--reports-soft-surface)",
    overflowWrap: "anywhere",
  },
  codeList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexWrap: "wrap", gap: 6 },
  codeChip: {
    color: "var(--mp-mute)",
    background: "var(--reports-card-surface)",
    border: "1px solid var(--reports-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "1px 6px",
    fontSize: "var(--font-size-xs)",
    overflowWrap: "anywhere",
  },
};
