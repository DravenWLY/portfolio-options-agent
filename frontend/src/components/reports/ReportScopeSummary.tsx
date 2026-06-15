import type { ReportScopeMetadataRead } from "../../types/tradeReview";
import { Badge } from "../shared/mp";
import { MpIcon } from "../shared/mp";

interface ReportScopeSummaryProps {
  scope: ReportScopeMetadataRead | null;
  compact?: boolean;
  unavailableText?: string;
}

export default function ReportScopeSummary({
  scope,
  compact = false,
  unavailableText,
}: ReportScopeSummaryProps) {
  if (!scope) {
    return (
      <section style={compact ? styles.compactWrap : styles.wrap} aria-label="Saved report scope">
        <div style={styles.head}>
          <MpIcon name="info" size={13} style={styles.mutedIcon} />
          <span style={styles.label}>Saved scope unavailable</span>
        </div>
        <p style={styles.unavailableText}>
          {unavailableText ??
            "This report does not include saved scope metadata. The current account selector is not used to reinterpret it."}
        </p>
      </section>
    );
  }

  const reviewAccount = scope.review_account;
  const portfolioScope = scope.portfolio_context_scope;

  return (
    <section style={compact ? styles.compactWrap : styles.wrap} aria-label="Saved report scope">
      <div style={styles.head}>
        <MpIcon name="circle" size={13} style={styles.accentIcon} />
        <span style={styles.label}>Scope used</span>
      </div>
      <p style={styles.summary}>{scope.scope_summary_label}</p>
      <div style={styles.badges}>
        <Badge tone={reviewAccount ? "info" : "mute"} dot={Boolean(reviewAccount)}>
          {reviewAccount
            ? reviewAccount.account_kind_label
              ? `Review account: ${reviewAccount.display_label} · ${reviewAccount.account_kind_label}`
              : `Review account: ${reviewAccount.display_label}`
            : "No review account"}
        </Badge>
        <Badge
          tone={scope.account_level_feasibility_evaluated ? "live" : "mute"}
          dot={scope.account_level_feasibility_evaluated}
        >
          {scope.account_level_feasibility_evaluated ? "Account feasibility evaluated" : "Account feasibility not evaluated"}
        </Badge>
        <Badge tone="info" dot={false}>{`Context: ${portfolioScope.display_label}`}</Badge>
      </div>
      {(portfolioScope.included_account_labels.length > 0 ||
        portfolioScope.excluded_account_labels.length > 0 ||
        scope.scope_caveat_codes.length > 0) && (
        <details style={styles.details}>
          <summary style={styles.summaryToggle}>
            Scope details
            <span style={styles.count}>
              {portfolioScope.included_account_labels.length +
                portfolioScope.excluded_account_labels.length +
                scope.scope_caveat_codes.length}
            </span>
          </summary>
          <div style={styles.detailGrid}>
            {portfolioScope.included_account_labels.length > 0 && (
              <ChipGroup label="Included" items={portfolioScope.included_account_labels} />
            )}
            {portfolioScope.excluded_account_labels.length > 0 && (
              <ChipGroup label="Excluded" items={portfolioScope.excluded_account_labels} />
            )}
            {scope.scope_caveat_codes.length > 0 && (
              <ChipGroup label="Scope notes" items={scope.scope_caveat_codes} code />
            )}
          </div>
        </details>
      )}
    </section>
  );
}

function ChipGroup({
  label,
  items,
  code,
}: {
  label: string;
  items: string[];
  code?: boolean;
}) {
  return (
    <div style={styles.chipGroup}>
      <span style={styles.chipLabel}>{label}</span>
      <ul style={styles.chipList}>
        {items.map((item, index) => (
          <li key={`${label}-${index}-${item}`} style={code ? styles.codeChip : styles.chip}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    border: "1px solid var(--mp-rule)",
    borderLeft: "3px solid var(--mp-accent)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-3)",
    backgroundColor: "var(--mp-card-2)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  compactWrap: {
    borderTop: "1px solid var(--mp-rule)",
    paddingTop: "var(--space-2)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  head: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    minWidth: 0,
  },
  accentIcon: {
    color: "var(--mp-accent)",
    flexShrink: 0,
  },
  mutedIcon: {
    color: "var(--mp-mute)",
    flexShrink: 0,
  },
  label: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
  summary: {
    margin: 0,
    color: "var(--mp-ink)",
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    lineHeight: 1.35,
  },
  unavailableText: {
    margin: 0,
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-xs)",
    lineHeight: 1.5,
  },
  badges: {
    display: "flex",
    flexWrap: "wrap",
    gap: "var(--space-2)",
    minWidth: 0,
  },
  details: {
    minWidth: 0,
  },
  summaryToggle: {
    cursor: "pointer",
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
  },
  count: {
    color: "var(--mp-mute)",
    fontVariantNumeric: "tabular-nums",
  },
  detailGrid: {
    display: "grid",
    gap: "var(--space-2)",
    marginTop: "var(--space-2)",
  },
  chipGroup: {
    display: "grid",
    gap: 6,
  },
  chipLabel: {
    color: "var(--mp-mute)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
  },
  chipList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
  },
  chip: {
    color: "var(--mp-ink-2)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "2px 6px",
    fontSize: "var(--font-size-xs)",
    overflowWrap: "anywhere",
  },
  codeChip: {
    color: "var(--mp-ink-2)",
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "2px 6px",
    fontSize: "var(--font-size-xs)",
    fontFamily: "var(--mp-font-mono)",
    overflowWrap: "anywhere",
  },
};
