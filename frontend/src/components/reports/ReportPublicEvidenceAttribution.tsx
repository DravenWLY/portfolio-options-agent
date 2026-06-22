/**
 * ReportPublicEvidenceAttribution — frontend-only SEC EDGAR attribution chrome
 * for a saved report's public company-profile evidence (P29C-T4).
 *
 * Lives in the provenance/supporting area, deliberately secondary but
 * discoverable. It renders ONLY from the sanitized, backend-owned
 * `public_evidence_attribution` read field; the EDGAR source is never inferred
 * from role prose, evidence_references, the section key, the report title, or
 * any fallback text.
 *
 * The full attribution sentence (containing "investment advice") is fixed
 * frontend display boilerplate per the P29C-T3B design: it must not be
 * persisted, generated, or sent to any backend/agent field, because it trips
 * the saved/report advice-phrase validators. No literal SIC value, CIK,
 * fiscal-year-end, company name, ticker, exchange, fact, URL, or payload is
 * shown — only provider-neutral source identity, availability, and the
 * SIC-presence flag this component receives.
 */
import { MpIcon } from "../shared/mp";
import type { ReportPublicEvidenceAttributionRead } from "../../types/api";

/** Exact approved wording (P29C-T4 / Codex A source-rights record). */
const FULL_ATTRIBUTION =
  "Source: SEC EDGAR submissions metadata. Company identity and listing metadata only. Not investment advice or a trading signal.";
const SHORT_LABEL = "SEC EDGAR metadata - company profile only";
const LAG_CAVEAT =
  "EDGAR metadata may lag company changes and does not include financial analysis, filing text, or investment conclusions.";
const SIC_CAVEAT = "SEC SIC metadata may be broad, legacy, and may lag company changes.";
const LIMITED_CAVEAT =
  "Limited: only part of the company-profile metadata was available for this saved report.";

interface ReportPublicEvidenceAttributionProps {
  attribution: ReportPublicEvidenceAttributionRead | null;
}

export default function ReportPublicEvidenceAttribution({
  attribution,
}: ReportPublicEvidenceAttributionProps) {
  // Render only for the reviewed SEC EDGAR source in an available/limited
  // state. The literal-union types already constrain these, but the gate stays
  // explicit so the source can never be implied from anything else.
  if (
    !attribution ||
    attribution.source_key !== "sec_edgar_submissions" ||
    (attribution.availability !== "available" && attribution.availability !== "limited")
  ) {
    return null;
  }

  const isLimited = attribution.availability === "limited";

  return (
    <section style={styles.wrap} aria-label="Public evidence source attribution">
      <div style={styles.head}>
        <MpIcon name="info" size={14} style={styles.icon} />
        <span style={styles.label}>{SHORT_LABEL}</span>
        {isLimited && (
          <span style={styles.limitedBadge}>
            <MpIcon name="alert" size={11} aria-hidden="true" />
            Limited
          </span>
        )}
      </div>

      <p style={styles.attribution}>{FULL_ATTRIBUTION}</p>

      <ul style={styles.caveats}>
        <li style={styles.caveat}>{LAG_CAVEAT}</li>
        {isLimited && <li style={styles.caveat}>{LIMITED_CAVEAT}</li>}
        {attribution.has_sic_label && <li style={styles.caveat}>{SIC_CAVEAT}</li>}
      </ul>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    border: "1px solid var(--reports-rule)",
    borderLeft: "2px solid var(--reports-rule-strong)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-3) var(--space-4)",
    background: "var(--reports-card-surface)",
    minWidth: 0,
  },
  head: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    flexWrap: "wrap",
    minWidth: 0,
  },
  icon: {
    color: "var(--mp-mute)",
    flexShrink: 0,
  },
  label: {
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.05em",
    textTransform: "uppercase",
    overflowWrap: "anywhere",
  },
  limitedBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
    color: "var(--mp-stale)",
    border: "1px solid var(--mp-stale)",
    borderRadius: 999,
    padding: "0 7px",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  attribution: {
    margin: 0,
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.6,
    overflowWrap: "anywhere",
  },
  caveats: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexDirection: "column",
    gap: 3,
  },
  caveat: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.5,
    overflowWrap: "anywhere",
  },
};
