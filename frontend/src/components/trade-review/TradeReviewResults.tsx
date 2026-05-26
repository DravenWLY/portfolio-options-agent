import type {
  TradeReviewWorkspaceRead,
  ReviewActionabilityStatus,
  PortfolioActionabilityDecision,
  PortfolioContextSummaryRead,
  TradeIntentSummaryRead,
  DeterministicTradeReviewRead,
  RiskRuleViolationSummaryRead,
  MissingDataWarningRead,
  WorkspaceCaveatRead,
  AgentOrchestrationSummaryRead,
  AnalysisOnlyReportOutputRead,
  WorkspaceCaveatSeverity,
} from "../../types/tradeReview";
import type { RiskSeverity } from "../../types/api";
import { MpIcon, type MpIconName } from "../shared/mp";

/**
 * TradeReviewResults — renders the sanitized TradeReviewWorkspaceRead.
 *
 * P20C-T4 clutter reduction: sections are organized into tiers.
 *
 * Tier 1 — always visible scan path:
 *   actionability banner, deterministic reference, trade intent,
 *   freshness (broker + market, separate), workspace caveats.
 *
 * Tier 2 — collapsible disclosure sections (default closed):
 *   portfolio context, portfolio impact, cash/collateral,
 *   concentration/allocation, options exposure, scenario payoff,
 *   risk-rule violations, missing data warnings.
 *   Options exposure defaults open when safety caveats present.
 *
 * Tier 3 — always visible at bottom (when present):
 *   agent orchestration summary, analysis-only report.
 *
 * Values are rendered verbatim from the backend (no frontend
 * financial computation). Severity/actionability uses MpIcon +
 * text, never color alone.
 */

const SEVERITY_META: Record<
  RiskSeverity,
  { icon: MpIconName; label: string; cssVar: string }
> = {
  info: { icon: "info", label: "Info", cssVar: "var(--mp-mute)" },
  warning: { icon: "alert", label: "Warning", cssVar: "var(--mp-stale)" },
  violation: { icon: "x", label: "Violation", cssVar: "var(--mp-block)" },
  blocker: { icon: "shield", label: "Blocker", cssVar: "var(--mp-block)" },
};

const SEVERITY_ORDER: RiskSeverity[] = ["blocker", "violation", "warning", "info"];

const CAVEAT_META: Record<
  WorkspaceCaveatSeverity,
  { icon: MpIconName; label: string; cssVar: string }
> = {
  info: { icon: "info", label: "Info", cssVar: "var(--mp-mute)" },
  warning: { icon: "alert", label: "Warning", cssVar: "var(--mp-stale)" },
  blocker: { icon: "shield", label: "Blocker", cssVar: "var(--mp-block)" },
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

const ACTIONABILITY_ICON: Record<string, { icon: MpIconName; cssVar: string }> = {
  normal_review: { icon: "check", cssVar: "var(--mp-live)" },
  analysis_only: { icon: "alert", cssVar: "var(--mp-stale)" },
  manual_confirmation_required: { icon: "alert", cssVar: "var(--mp-stale)" },
  blocked: { icon: "shield", cssVar: "var(--mp-block)" },
};

function actionabilityVisual(status: ReviewActionabilityStatus) {
  if (status.startsWith("blocked_")) return ACTIONABILITY_ICON.blocked;
  return ACTIONABILITY_ICON[status] ?? ACTIONABILITY_ICON.analysis_only;
}

function actionabilityLabel(status: ReviewActionabilityStatus): string {
  return ACTIONABILITY_LABEL[status] ?? `Unexpected review status (${String(status)})`;
}

export default function TradeReviewResults({ data }: { data: TradeReviewWorkspaceRead }) {
  const optionsExposure = data.deterministic_review.options_exposure;
  const hasOptionsSafetyCaveat =
    optionsExposure.covered_call_coverage_model === "not_fully_modelled" ||
    optionsExposure.cash_secured_put_collateral_model === "generic_rule_only";

  return (
    <div style={styles.wrap}>
      {/* ── Tier 1: always-visible scan path ──────────────────────────── */}
      <ActionabilityBanner actionability={data.actionability} />

      <p style={styles.deterministicBanner} role="note">
        <MpIcon name="info" size={11} style={{ color: "var(--mp-mute)", verticalAlign: "middle", marginRight: 4 }} />
        Deterministic Python output — calculated facts, not advice, not a forecast.
        Review ref: <span style={styles.mono}>{data.review_reference}</span> · calc{" "}
        <span style={styles.mono}>{data.calculation_version}</span> · generated{" "}
        <span style={styles.mono}>{data.generated_at}</span>.
      </p>

      <IntentSummary intent={data.trade_intent_summary} />
      <FreshnessPanel actionability={data.actionability} />
      <CaveatsBlock caveats={data.caveats} />

      {/* ── Tier 2: collapsible deterministic details ─────────────────── */}
      {data.portfolio_context && (
        <DisclosureSection
          title="Portfolio context"
          tag="server-owned"
          ariaLabel="Portfolio context (server-owned)"
          accent
        >
          <PortfolioContextContent context={data.portfolio_context} />
        </DisclosureSection>
      )}

      <DeterministicDisclosures
        review={data.deterministic_review}
        hasOptionsSafetyCaveat={hasOptionsSafetyCaveat}
      />

      <DisclosureSection
        title="Risk-rule violations"
        tag="deterministic"
        ariaLabel="Deterministic risk-rule violations"
        count={data.deterministic_review.risk_rule_violations.length}
      >
        <ViolationsContent violations={data.deterministic_review.risk_rule_violations} />
      </DisclosureSection>

      <DisclosureSection
        title="Missing / stale data warnings"
        tag="deterministic"
        ariaLabel="Missing or stale data warnings"
        count={data.deterministic_review.missing_data_warnings.length}
      >
        <WarningsContent warnings={data.deterministic_review.missing_data_warnings} />
      </DisclosureSection>

      {/* ── Tier 3: always-visible at bottom ──────────────────────────── */}
      {data.agent_orchestration && <AgentOrchestrationBlock summary={data.agent_orchestration} />}
      {data.report_output && <AnalysisOnlyReportBlock report={data.report_output} />}
    </div>
  );
}

/* ── Disclosure wrapper ─────────────────────────────────────────────────── */

function DisclosureSection({
  title,
  tag,
  ariaLabel,
  defaultOpen = false,
  accent,
  count,
  children,
}: {
  title: string;
  tag: string;
  ariaLabel?: string;
  defaultOpen?: boolean;
  accent?: boolean;
  count?: number;
  children: React.ReactNode;
}) {
  return (
    <details
      className="mp-disclosure"
      style={{ ...styles.card, ...(accent ? { borderLeft: "3px solid var(--mp-accent)" } : {}) }}
      open={defaultOpen || undefined}
      aria-label={ariaLabel}
    >
      <summary style={styles.disclosureSummary}>
        <MpIcon
          name="chevron-r"
          size={11}
          className="mp-disclosure-chevron"
          style={{ color: "var(--mp-mute)", flexShrink: 0 }}
        />
        <span style={styles.cardTitle}>{title}</span>
        {count !== undefined && (
          <span style={styles.countBadge}>{count}</span>
        )}
        <span style={styles.detTag}>{tag}</span>
      </summary>
      <div style={styles.disclosureBody}>
        {children}
      </div>
    </details>
  );
}

/* ── Actionability banner ───────────────────────────────────────────────── */

function ActionabilityBanner({ actionability }: { actionability: PortfolioActionabilityDecision }) {
  const status = actionability.review_actionability_status;
  const visual = actionabilityVisual(status);
  const label = actionabilityLabel(status);

  return (
    <section
      style={{ ...styles.banner, borderColor: visual.cssVar }}
      role="status"
      aria-label={`Review actionability: ${label}`}
    >
      <span style={{ ...styles.bannerIcon, color: visual.cssVar }}>
        <MpIcon name={visual.icon} size={18} />
      </span>
      <div>
        <p style={styles.bannerLabel}>{label}</p>
        <p style={styles.bannerSub}>
          Language tier: <span style={styles.mono}>{actionability.language_tier}</span> · Policy{" "}
          <span style={styles.mono}>{actionability.policy_version}</span> · Evaluated{" "}
          <span style={styles.mono}>{actionability.evaluated_at}</span>
        </p>
        {actionability.requires_user_confirmation && (
          <p style={styles.bannerNote}>
            Manual confirmation required before this can be treated as a normal review.
          </p>
        )}
        {actionability.reasons.length > 0 && (
          <ul style={styles.reasonList}>
            {actionability.reasons.map((r) => (
              <li key={r.code + r.scope} style={styles.reasonItem}>
                <span style={styles.scopeChip}>{r.scope}</span>
                <span style={{ ...styles.sevChip, color: cssColorForReason(r.severity) }}>
                  <MpIcon
                    name={r.severity === "blocker" ? "shield" : r.severity === "warning" ? "alert" : "info"}
                    size={10}
                    style={{ verticalAlign: "middle", marginRight: 2 }}
                  />
                  {r.severity}
                </span>
                <span style={styles.reasonMsg}>{r.message}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function cssColorForReason(sev: "info" | "warning" | "blocker"): string {
  if (sev === "blocker") return "var(--mp-block)";
  if (sev === "warning") return "var(--mp-stale)";
  return "var(--mp-mute)";
}

/* ── Trade intent summary ───────────────────────────────────────────────── */

function IntentSummary({ intent }: { intent: TradeIntentSummaryRead }) {
  return (
    <section style={styles.card} aria-label="Trade intent summary">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Trade intent</span>
        <span style={styles.detTag}>deterministic</span>
      </div>
      <ul style={styles.facts}>
        <FactRow k="Flow" v={intent.supported_flow} mono />
        <FactRow k="Asset class" v={intent.asset_class} mono />
        <FactRow k="Intent type" v={intent.intent_type} mono />
        <FactRow k="Status" v={intent.status} mono />
        {intent.symbol && <FactRow k="Symbol" v={intent.symbol} mono />}
        {intent.action && <FactRow k="Action" v={intent.action} mono />}
        {intent.quantity && <FactRow k="Quantity" v={intent.quantity} mono />}
        {intent.price_assumption && <FactRow k="Price assumption" v={intent.price_assumption} mono />}
        {intent.strategy_type && <FactRow k="Strategy type" v={intent.strategy_type} mono />}
        {intent.underlying_symbol && <FactRow k="Underlying" v={intent.underlying_symbol} mono />}
        <FactRow k="Intent id" v={intent.intent_id} mono />
      </ul>
      {intent.legs.length > 0 && (
        <ul style={styles.legList}>
          {intent.legs.map((leg, i) => (
            <li key={i} style={styles.legRow}>
              <span style={styles.mono}>
                {leg.leg_action} {leg.quantity} × {leg.underlying_symbol} {leg.option_type.toUpperCase()}{" "}
                {leg.expiration_date} @ {leg.strike}
              </span>
              <span style={styles.legMeta}>
                multiplier {leg.multiplier} · support {leg.support_status}
                {leg.premium ? ` · premium ${leg.premium}` : ""}
                {leg.unsupported_reason ? ` · reason: ${leg.unsupported_reason}` : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/* ── Freshness panel ────────────────────────────────────────────────────── */

function FreshnessPanel({ actionability }: { actionability: PortfolioActionabilityDecision }) {
  const b = actionability.broker_snapshot;
  const m = actionability.market_quotes;
  return (
    <section style={styles.card} aria-label="Freshness panel — broker and market quote scopes are distinct">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Freshness</span>
        <span style={styles.detTag}>two scopes — shown separately</span>
      </div>
      <div style={styles.freshnessGrid}>
        <div style={styles.freshnessCol}>
          <h3 style={styles.freshnessHead}>Broker snapshot</h3>
          <ul style={styles.facts}>
            <FactRow k="Source" v={b.source} mono />
            <FactRow k="Freshness status" v={b.freshness_status} mono />
            <FactRow k="Sync status" v={b.sync_status ?? "—"} mono />
            <FactRow k="As of" v={b.as_of ?? "—"} mono />
            <FactRow k="Last successful sync" v={b.last_successful_sync_at ?? "—"} mono />
            <FactRow k="Provider status" v={b.provider_status} mono />
            {b.sanitized_error_code && <FactRow k="Error code" v={b.sanitized_error_code} mono />}
          </ul>
        </div>
        <div style={styles.freshnessCol}>
          <h3 style={styles.freshnessHead}>Market quotes</h3>
          <ul style={styles.facts}>
            <FactRow k="Data mode" v={m.data_mode} mono />
            <FactRow k="Freshness status" v={m.freshness_status} mono />
            <FactRow k="Actionability" v={m.actionability_status} mono />
            <FactRow k="Provider status" v={m.provider_status} mono />
            <FactRow k="As of (min/max)" v={`${m.as_of_min ?? "—"} / ${m.as_of_max ?? "—"}`} mono />
            {m.sanitized_error_code && <FactRow k="Error code" v={m.sanitized_error_code} mono />}
          </ul>
        </div>
      </div>
      <p style={styles.cardFoot}>
        Broker snapshot freshness and market quote freshness are two different scopes; the
        backend keeps their severities independent and the UI presents them as-is.
      </p>
    </section>
  );
}

/* ── Caveats (always visible when present — safety-critical) ────────────── */

function CaveatsBlock({ caveats }: { caveats: WorkspaceCaveatRead[] }) {
  if (caveats.length === 0) return null;
  return (
    <section style={styles.card} aria-label="Workspace caveats">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Caveats</span>
        <span style={styles.detTag}>deterministic</span>
      </div>
      <ul style={styles.sevList}>
        {caveats.map((c) => {
          const meta = CAVEAT_META[c.severity] ?? CAVEAT_META.info;
          return (
            <li key={c.code + c.applies_to} style={styles.violation}>
              <div style={styles.violationTop}>
                <span style={{ ...styles.sevChip, color: meta.cssVar, borderColor: meta.cssVar }}>
                  <MpIcon name={meta.icon} size={10} style={{ verticalAlign: "middle", marginRight: 2 }} />
                  {meta.label}
                </span>
                <span style={styles.mono}>{c.code}</span>
                <span style={styles.scopeChip}>applies to: {c.applies_to}</span>
              </div>
              <p style={styles.violationMsg}>{c.message}</p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/* ── Portfolio context (disclosure content) ──────────────────────────────── */

function PortfolioContextContent({ context }: { context: PortfolioContextSummaryRead }) {
  const cashStateMeta: Record<
    PortfolioContextSummaryRead["cash_state"],
    { icon: MpIconName; cssVar: string; label: string }
  > = {
    available: { icon: "check", cssVar: "var(--mp-live)", label: "Available" },
    unavailable: { icon: "alert", cssVar: "var(--mp-stale)", label: "Unavailable" },
    not_exposed: { icon: "circle", cssVar: "var(--mp-mute)", label: "Not exposed" },
  };
  const brokerFresh = context.broker_snapshot.freshness_status;
  const brokerStale = ["stale", "unknown", "error", "reauth_required"].includes(brokerFresh);
  const cs = cashStateMeta[context.cash_state];
  return (
    <>
      {brokerStale && (
        <p style={styles.caveatInline} role="status">
          <MpIcon name="alert" size={12} style={{ color: "var(--mp-stale)", verticalAlign: "middle", marginRight: 4 }} />
          Broker snapshot for this context is{" "}
          <strong>{brokerFresh}</strong>. Treat the portfolio-backed review as
          stale; verify holdings in your broker before any manual action.
        </p>
      )}
      <ul style={styles.facts}>
        <FactRow k="Context reference (opaque)" v={context.context_reference} mono />
        <FactRow k="Context source" v={context.context_source} mono />
        <FactRow k="Selection mode" v={context.selection_mode} mono />
        <FactRow k="Label" v={context.label ?? "—"} mono />
        <FactRow k="Summary as of" v={context.summary_as_of ?? "—"} mono />
        <FactRow k="Latest snapshot as of" v={context.latest_snapshot_as_of ?? "—"} mono />
        <FactRow
          k="Broker snapshot freshness"
          v={`${context.broker_snapshot.source} · ${brokerFresh}`}
          mono
        />
        <FactRow
          k="Broker provider status"
          v={context.broker_snapshot.provider_status}
          mono
        />
        <FactRow k="Stock position count" v={String(context.stock_position_count)} mono />
        <FactRow k="Option position count" v={String(context.option_position_count)} mono />
        <li style={styles.factRow}>
          <span style={styles.factKey}>Cash state</span>
          <span
            style={{
              ...styles.sevChip,
              color: cs.cssVar,
              borderColor: cs.cssVar,
            }}
          >
            <MpIcon name={cs.icon} size={10} style={{ verticalAlign: "middle", marginRight: 2 }} />
            {cs.label}{" "}
            <span style={styles.mono}>({context.cash_state})</span>
          </span>
        </li>
      </ul>
      <p style={styles.cardFoot}>
        Only safe portfolio metadata is exposed here — counts and category labels, no
        holdings, no balances, no account / provider identifiers. Broker snapshot
        freshness shown above is a different scope from market quote freshness
        (see Freshness panel).
      </p>
    </>
  );
}

/* ── Deterministic sections (each in disclosure) ────────────────────────── */

function DeterministicDisclosures({
  review,
  hasOptionsSafetyCaveat,
}: {
  review: DeterministicTradeReviewRead;
  hasOptionsSafetyCaveat: boolean;
}) {
  return (
    <>
      <DisclosureSection
        title="Portfolio impact"
        tag="deterministic"
        ariaLabel="Portfolio impact summary (deterministic)"
      >
        <ul style={styles.facts}>
          <FactRow k="Broker freshness" v={review.portfolio_impact.broker_freshness_status} mono />
          <FactRow k="Market freshness" v={review.portfolio_impact.market_freshness_status} mono />
          <FactRow
            k="Market manual review required"
            v={String(review.portfolio_impact.market_manual_review_required)}
            mono
          />
          <FactRow
            k="Concentration symbol"
            v={review.portfolio_impact.concentration_symbol ?? "—"}
            mono
          />
        </ul>
        <NotesList notes={review.portfolio_impact.notes} />
      </DisclosureSection>

      <DisclosureSection
        title="Cash / collateral impact"
        tag="deterministic"
        ariaLabel="Cash / collateral impact (deterministic)"
      >
        <ul style={styles.facts}>
          <FactRow
            k="Estimated trade cash change"
            v={review.cash_collateral_impact.estimated_trade_cash_change ?? "—"}
            mono
          />
          <FactRow
            k="Estimated premium cash change"
            v={review.cash_collateral_impact.estimated_premium_cash_change ?? "—"}
            mono
          />
          <FactRow
            k="Estimated collateral requirement change"
            v={review.cash_collateral_impact.estimated_collateral_requirement_change ?? "—"}
            mono
          />
          <FactRow
            k="Projected free cash state"
            v={review.cash_collateral_impact.projected_free_cash_state}
            mono
          />
        </ul>
        <NotesList notes={review.cash_collateral_impact.notes} />
      </DisclosureSection>

      <DisclosureSection
        title="Concentration / allocation"
        tag="deterministic"
        ariaLabel="Concentration / allocation impact (deterministic)"
      >
        <ul style={styles.facts}>
          <FactRow
            k="Concentration symbol"
            v={review.concentration_allocation_impact.concentration_symbol ?? "—"}
            mono
          />
          <FactRow
            k="Concentration value change (est.)"
            v={review.concentration_allocation_impact.estimated_concentration_value_change ?? "—"}
            mono
          />
          <FactRow
            k="Allocation drift status"
            v={review.concentration_allocation_impact.allocation_drift_status}
            mono
          />
        </ul>
        <NotesList notes={review.concentration_allocation_impact.notes} />
      </DisclosureSection>

      <DisclosureSection
        title="Options exposure"
        tag="deterministic"
        ariaLabel="Options exposure (deterministic)"
        defaultOpen={hasOptionsSafetyCaveat}
      >
        <ul style={styles.facts}>
          <FactRow
            k="Underlying symbol"
            v={review.options_exposure.underlying_symbol ?? "—"}
            mono
          />
          <FactRow
            k="Assignment share delta"
            v={review.options_exposure.assignment_share_delta}
            mono
          />
          <FactRow
            k="Exercise share delta"
            v={review.options_exposure.exercise_share_delta}
            mono
          />
          <FactRow
            k="Covered-call coverage model"
            v={review.options_exposure.covered_call_coverage_model}
            mono
          />
          <FactRow
            k="CSP collateral model"
            v={review.options_exposure.cash_secured_put_collateral_model}
            mono
          />
        </ul>
        <NotesList notes={review.options_exposure.notes} />
        {review.options_exposure.covered_call_coverage_model === "not_fully_modelled" && (
          <p style={styles.caveatInline}>
            <MpIcon name="alert" size={12} style={{ color: "var(--mp-stale)", verticalAlign: "middle", marginRight: 4 }} />
            Covered-call stock coverage is <strong>not fully netted</strong> against existing
            long positions in Phase 18A. Confirm coverage in your broker before any manual action.
          </p>
        )}
        {review.options_exposure.cash_secured_put_collateral_model === "generic_rule_only" && (
          <p style={styles.caveatInline}>
            <MpIcon name="alert" size={12} style={{ color: "var(--mp-stale)", verticalAlign: "middle", marginRight: 4 }} />
            Cash-secured-put collateral here uses a <strong>generic deterministic rule</strong>,
            not your broker's margin treatment. Verify the actual collateral hold in the broker
            before any manual action.
          </p>
        )}
      </DisclosureSection>

      <DisclosureSection
        title="Scenario payoff"
        tag="deterministic"
        ariaLabel="Scenario payoff summary (deterministic)"
      >
        <ul style={styles.facts}>
          <FactRow k="Max loss" v={review.scenario_payoff_summary.max_loss ?? "—"} mono />
          <FactRow k="Max gain" v={review.scenario_payoff_summary.max_gain ?? "—"} mono />
        </ul>
        {review.scenario_payoff_summary.points.length > 0 && (
          <ul style={styles.payoffList}>
            {review.scenario_payoff_summary.points.map((p, i) => (
              <li key={i} style={styles.payoffRow}>
                <span style={styles.payoffLabel}>{p.label}</span>
                <span style={styles.mono}>
                  underlying {p.underlying_price} · net cash {p.net_cash_flow} · value{" "}
                  {p.scenario_value} · pnl {p.scenario_pnl}
                </span>
                {p.description && <span style={styles.payoffDesc}>{p.description}</span>}
              </li>
            ))}
          </ul>
        )}
        <NotesList notes={review.scenario_payoff_summary.calculation_notes} />
      </DisclosureSection>
    </>
  );
}

/* ── Risk-rule violations (disclosure content) ──────────────────────────── */

function ViolationsContent({ violations }: { violations: RiskRuleViolationSummaryRead[] }) {
  if (violations.length === 0) {
    return <p style={styles.emptyMsg}>No rule entries were produced.</p>;
  }
  const unexpected = violations.filter(
    (violation) => !SEVERITY_ORDER.includes(violation.severity as RiskSeverity),
  );
  return (
    <>
      {SEVERITY_ORDER.map((sev) => {
        const group = violations.filter((v) => v.severity === sev);
        if (group.length === 0) return null;
        const m = SEVERITY_META[sev];
        return (
          <div key={sev} style={styles.sevGroup}>
            <h3 style={{ ...styles.sevHeading, color: m.cssVar }}>
              <MpIcon name={m.icon} size={12} style={{ verticalAlign: "middle", marginRight: 4 }} />
              {m.label} ({group.length})
            </h3>
            <ul style={styles.sevList}>
              {group.map((v) => (
                <li key={v.code + (v.metric ?? "")} style={styles.violation}>
                  <div style={styles.violationTop}>
                    <span style={{ ...styles.sevChip, color: m.cssVar, borderColor: m.cssVar }}>
                      <MpIcon name={m.icon} size={10} style={{ verticalAlign: "middle", marginRight: 2 }} />
                      {m.label}
                    </span>
                    <span style={styles.mono}>{v.code}</span>
                  </div>
                  <p style={styles.violationMsg}>{v.message}</p>
                  <div style={styles.violationMeta}>
                    <span>source: <span style={styles.mono}>{v.source}</span></span>
                    {v.metric && <span>metric: <span style={styles.mono}>{v.metric}</span></span>}
                    {v.actual && <span>actual: <span style={styles.mono}>{v.actual}</span></span>}
                    {v.policy_label && (
                      <span>policy: <span style={styles.mono}>{v.policy_label}</span></span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
      {unexpected.length > 0 && (
        <div style={styles.sevGroup}>
          <h3 style={{ ...styles.sevHeading, color: "var(--mp-mute)" }}>
            <MpIcon name="info" size={12} style={{ verticalAlign: "middle", marginRight: 4 }} />
            Unexpected severity ({unexpected.length})
          </h3>
          <ul style={styles.sevList}>
            {unexpected.map((violation) => (
              <li key={violation.code + (violation.metric ?? "")} style={styles.violation}>
                <div style={styles.violationTop}>
                  <span
                    style={{
                      ...styles.sevChip,
                      color: "var(--mp-mute)",
                      borderColor: "var(--mp-mute)",
                    }}
                  >
                    <MpIcon name="info" size={10} style={{ verticalAlign: "middle", marginRight: 2 }} />
                    {String(violation.severity)}
                  </span>
                  <span style={styles.mono}>{violation.code}</span>
                </div>
                <p style={styles.violationMsg}>{violation.message}</p>
                <div style={styles.violationMeta}>
                  <span>source: <span style={styles.mono}>{violation.source}</span></span>
                  {violation.metric && <span>metric: <span style={styles.mono}>{violation.metric}</span></span>}
                  {violation.actual && <span>actual: <span style={styles.mono}>{violation.actual}</span></span>}
                  {violation.policy_label && (
                    <span>policy: <span style={styles.mono}>{violation.policy_label}</span></span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}

/* ── Missing data warnings (disclosure content) ─────────────────────────── */

function WarningsContent({ warnings }: { warnings: MissingDataWarningRead[] }) {
  if (warnings.length === 0) {
    return <p style={styles.emptyMsg}>No missing-data warnings.</p>;
  }
  return (
    <ul style={styles.sevList}>
      {warnings.map((w) => {
        const meta = CAVEAT_META[w.severity] ?? CAVEAT_META.info;
        return (
          <li key={w.code + w.scope} style={styles.violation}>
            <div style={styles.violationTop}>
              <span style={{ ...styles.sevChip, color: meta.cssVar, borderColor: meta.cssVar }}>
                <MpIcon name={meta.icon} size={10} style={{ verticalAlign: "middle", marginRight: 2 }} />
                {meta.label}
              </span>
              <span style={styles.mono}>{w.code}</span>
              <span style={styles.scopeChip}>{w.scope}</span>
            </div>
            <p style={styles.violationMsg}>{w.message}</p>
          </li>
        );
      })}
    </ul>
  );
}

/* ── Agent orchestration ────────────────────────────────────────────────── */

function AgentOrchestrationBlock({ summary }: { summary: AgentOrchestrationSummaryRead }) {
  return (
    <section
      style={{ ...styles.card, borderLeft: "3px solid var(--mp-mute)" }}
      aria-label="Agent orchestration summary (status only — no LLM text)"
    >
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Agent orchestration</span>
        <span style={styles.detTag}>status only</span>
      </div>
      <ul style={styles.facts}>
        <FactRow k="Run reference" v={summary.run_reference} mono />
        <FactRow k="Workflow version" v={summary.workflow_version} mono />
        <FactRow
          k="Review actionability"
          v={summary.review_actionability_status ?? "—"}
          mono
        />
        <FactRow k="Report composed" v={String(summary.report_composed)} mono />
        <FactRow k="Source agents" v={summary.source_agent_names.join(", ") || "—"} mono />
        <FactRow k="Stage order" v={summary.stage_order.join(" → ") || "—"} mono />
      </ul>
      {Object.keys(summary.stage_statuses).length > 0 && (
        <div style={styles.subBlock}>
          <h4 style={styles.subHead}>Stage statuses</h4>
          <ul style={styles.facts}>
            {Object.entries(summary.stage_statuses).map(([stage, st]) => (
              <FactRow key={stage} k={stage} v={st} mono />
            ))}
          </ul>
        </div>
      )}
      {Object.keys(summary.unavailable_stages).length > 0 && (
        <div style={styles.subBlock}>
          <h4 style={styles.subHead}>Unavailable stages</h4>
          <ul style={styles.facts}>
            {Object.entries(summary.unavailable_stages).map(([stage, reason]) => (
              <FactRow key={stage} k={stage} v={reason} mono />
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

/* ── Analysis-only report ───────────────────────────────────────────────── */

function AnalysisOnlyReportBlock({ report }: { report: AnalysisOnlyReportOutputRead }) {
  return (
    <section
      style={{ ...styles.card, borderLeft: "3px solid var(--mp-stale)" }}
      aria-label="Analysis-only report output (separate from deterministic facts)"
    >
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Analysis-only report</span>
        <span style={styles.detTag}>narrative · not actionable</span>
      </div>
      <p style={styles.reportTitle}>{report.title}</p>
      <p style={styles.reportNote}>
        Narrative output for analysis only. It is presented separately from deterministic facts
        and any future research evidence. Do not treat it as advice or as a recommendation.
      </p>
      <div style={styles.subBlock}>
        <h4 style={styles.subHead}>Deterministic sections</h4>
        <p style={styles.subBody}>{report.deterministic_sections.join(", ") || "—"}</p>
      </div>
      <div style={styles.subBlock}>
        <h4 style={styles.subHead}>LLM-generated sections</h4>
        <p style={styles.subBody}>{report.llm_generated_sections.join(", ") || "—"}</p>
      </div>
      <div style={styles.subBlock}>
        <h4 style={styles.subHead}>Source agents</h4>
        <p style={styles.subBody}>{report.source_agent_names.join(", ") || "—"}</p>
      </div>
      {report.content_markdown && (
        <details className="mp-disclosure" style={styles.markdownDetails}>
          <summary style={styles.markdownSummary}>
            <MpIcon
              name="chevron-r"
              size={10}
              className="mp-disclosure-chevron"
              style={{ color: "var(--mp-mute)", verticalAlign: "middle", marginRight: 4 }}
            />
            Show raw markdown
          </summary>
          <pre style={styles.markdownPre}>{report.content_markdown}</pre>
        </details>
      )}
    </section>
  );
}

/* ── Shared primitives ──────────────────────────────────────────────────── */

function FactRow({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <li style={styles.factRow}>
      <span style={styles.factKey}>{k}</span>
      <span style={mono ? styles.mono : undefined}>{v}</span>
    </li>
  );
}

function NotesList({ notes }: { notes: string[] }) {
  if (notes.length === 0) return null;
  return (
    <ul style={styles.noteList}>
      {notes.map((n, i) => (
        <li key={i} style={styles.note}>
          <span aria-hidden="true">· </span>
          {n}
        </li>
      ))}
    </ul>
  );
}

/* ── Styles ──────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  wrap: { display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0 },

  /* Actionability banner */
  banner: {
    display: "flex",
    gap: "var(--space-4)",
    alignItems: "flex-start",
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderLeftWidth: 4,
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
  },
  bannerIcon: { flexShrink: 0, lineHeight: 1 },
  bannerLabel: {
    fontWeight: 700,
    fontSize: "var(--font-size-base)",
    color: "var(--mp-ink)",
    margin: 0,
  },
  bannerSub: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: "var(--space-1) 0 0",
  },
  bannerNote: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-stale)",
    margin: "var(--space-2) 0 0",
    fontWeight: 600,
  },
  reasonList: { margin: "var(--space-2) 0 0", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  reasonItem: { display: "flex", gap: "var(--space-2)", fontSize: "var(--font-size-xs)", alignItems: "center", flexWrap: "wrap" },
  scopeChip: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 5px",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    color: "var(--mp-mute)",
  },
  sevChip: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid",
    borderRadius: "var(--radius-sm)",
    fontWeight: 700,
    display: "inline-flex",
    alignItems: "center",
  },
  reasonMsg: { color: "var(--mp-ink-2)" },

  /* Deterministic reference banner */
  deterministicBanner: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    backgroundColor: "var(--mp-paper-2)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-4)",
    margin: 0,
    lineHeight: 1.6,
  },

  /* Card (section container) */
  card: {
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    minWidth: 0,
  },
  cardHead: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-3)", flexWrap: "wrap" },
  cardTitle: { fontWeight: 700, fontSize: "var(--font-size-base)", color: "var(--mp-ink)" },
  detTag: {
    fontSize: "var(--font-size-xs)",
    padding: "1px 6px",
    border: "1px solid var(--mp-mute)",
    borderRadius: "var(--radius-sm)",
    color: "var(--mp-mute)",
    fontWeight: 600,
    letterSpacing: "0.04em",
    marginLeft: "auto",
  },
  cardFoot: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0, lineHeight: 1.6 },

  /* Disclosure section */
  disclosureSummary: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    flexWrap: "wrap",
    minWidth: 0,
    padding: "var(--space-1) 0",
    userSelect: "none",
  },
  disclosureBody: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    paddingTop: "var(--space-3)",
    borderTop: "1px solid var(--mp-rule)",
    marginTop: "var(--space-2)",
  },
  countBadge: {
    fontSize: "var(--font-size-xs)",
    fontWeight: 700,
    fontFamily: "var(--mp-font-mono, monospace)",
    color: "var(--mp-accent)",
    backgroundColor: "var(--mp-accent-soft)",
    border: "1px solid var(--mp-accent-line)",
    borderRadius: "var(--radius-sm)",
    padding: "0 5px",
    lineHeight: "18px",
    minWidth: 20,
    textAlign: "center",
  },

  /* Freshness */
  freshnessGrid: { display: "flex", gap: "var(--space-5)", flexWrap: "wrap" },
  freshnessCol: { flex: "1 1 260px", minWidth: "min(260px, 100%)", display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  freshnessHead: { fontSize: "var(--font-size-xs)", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--mp-mute)", margin: 0 },

  /* Fact rows */
  facts: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  factRow: { display: "flex", gap: "var(--space-4)", fontSize: "var(--font-size-xs)", alignItems: "baseline", flexWrap: "wrap", minWidth: 0 },
  factKey: { flex: "1 1 150px", minWidth: 0, color: "var(--mp-mute)" },
  mono: { fontFamily: "var(--mp-font-mono, monospace)", color: "var(--mp-ink-2)", overflowWrap: "anywhere", minWidth: 0 },

  /* Leg list */
  legList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  legRow: { display: "flex", flexDirection: "column", gap: "var(--space-1)", fontSize: "var(--font-size-xs)" },
  legMeta: { color: "var(--mp-mute)" },

  /* Inline caveat */
  caveatInline: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink-2)",
    margin: 0,
    padding: "var(--space-2) var(--space-3)",
    border: "1px solid var(--mp-stale)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
  },

  /* Severity groups */
  emptyMsg: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0 },
  sevGroup: { display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  sevHeading: { fontSize: "var(--font-size-sm)", fontWeight: 700, margin: 0, textTransform: "uppercase", letterSpacing: "0.04em" },
  sevList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  violation: {
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-3)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
  },
  violationTop: { display: "flex", gap: "var(--space-3)", alignItems: "center", flexWrap: "wrap" },
  violationMsg: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", margin: 0, lineHeight: 1.5 },
  violationMeta: {
    display: "flex",
    gap: "var(--space-4)",
    flexWrap: "wrap",
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
  },

  /* Payoff */
  payoffList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  payoffRow: { display: "flex", flexDirection: "column", gap: "var(--space-1)", fontSize: "var(--font-size-xs)" },
  payoffLabel: { fontWeight: 700, color: "var(--mp-ink-2)" },
  payoffDesc: { color: "var(--mp-mute)" },

  /* Notes */
  noteList: { margin: 0, padding: 0, listStyle: "none", fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  note: { lineHeight: 1.5 },

  /* Report */
  reportTitle: { fontWeight: 700, fontSize: "var(--font-size-sm)", color: "var(--mp-ink)", margin: 0 },
  reportNote: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0, lineHeight: 1.6 },
  subBlock: { display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  subHead: { fontSize: "var(--font-size-xs)", textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--mp-mute)", margin: 0 },
  subBody: { fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)", margin: 0 },
  markdownDetails: { fontSize: "var(--font-size-xs)" },
  markdownSummary: { cursor: "pointer", color: "var(--mp-mute)", display: "flex", alignItems: "center" },
  markdownPre: {
    margin: "var(--space-2) 0 0",
    padding: "var(--space-2) var(--space-3)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
    whiteSpace: "pre-wrap",
    color: "var(--mp-ink-2)",
    fontFamily: "var(--mp-font-mono, monospace)",
  },
};
