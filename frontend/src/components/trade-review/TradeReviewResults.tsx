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

/**
 * TradeReviewResults — renders the sanitized TradeReviewWorkspaceRead.
 *
 * Section vocabulary maps 1:1 to backend. Values are rendered verbatim
 * (no frontend financial computation). Three structural layers are kept
 * visually separated:
 *   1. Deterministic facts (always present)
 *   2. Agent orchestration summary (status only; no LLM text)
 *   3. Analysis-only report output (clearly labelled narrative)
 *
 * Severity / actionability are never color-only — icon + text are paired.
 */

const SEVERITY_META: Record<
  RiskSeverity,
  { icon: string; label: string; cssVar: string }
> = {
  info: { icon: "ⓘ", label: "Info", cssVar: "var(--mp-mute)" },
  warning: { icon: "△", label: "Warning", cssVar: "var(--mp-stale)" },
  violation: { icon: "✕", label: "Violation", cssVar: "var(--mp-block)" },
  blocker: { icon: "■", label: "Blocker", cssVar: "var(--mp-block)" },
};

const SEVERITY_ORDER: RiskSeverity[] = ["blocker", "violation", "warning", "info"];

const CAVEAT_META: Record<
  WorkspaceCaveatSeverity,
  { icon: string; label: string; cssVar: string }
> = {
  info: { icon: "ⓘ", label: "Info", cssVar: "var(--mp-mute)" },
  warning: { icon: "△", label: "Warning", cssVar: "var(--mp-stale)" },
  blocker: { icon: "■", label: "Blocker", cssVar: "var(--mp-block)" },
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

export default function TradeReviewResults({ data }: { data: TradeReviewWorkspaceRead }) {
  return (
    <div style={styles.wrap}>
      <ActionabilityBanner actionability={data.actionability} />
      <p style={styles.deterministicBanner} role="note">
        <span aria-hidden="true">∑ </span>
        Deterministic Python output — calculated facts, not advice, not a forecast.
        Review reference: <span style={styles.mono}>{data.review_reference}</span>; calculation version{" "}
        <span style={styles.mono}>{data.calculation_version}</span>; generated at{" "}
        <span style={styles.mono}>{data.generated_at}</span>.
      </p>
      {data.portfolio_context && <PortfolioContextBlock context={data.portfolio_context} />}
      <FreshnessPanel actionability={data.actionability} />
      <IntentSummary intent={data.trade_intent_summary} />
      <DeterministicSections review={data.deterministic_review} />
      <ViolationsBlock violations={data.deterministic_review.risk_rule_violations} />
      <WarningsBlock warnings={data.deterministic_review.missing_data_warnings} />
      <CaveatsBlock caveats={data.caveats} />
      {data.agent_orchestration && <AgentOrchestrationBlock summary={data.agent_orchestration} />}
      {data.report_output && <AnalysisOnlyReportBlock report={data.report_output} />}
    </div>
  );
}

function ActionabilityBanner({ actionability }: { actionability: PortfolioActionabilityDecision }) {
  const status = actionability.review_actionability_status;
  const isBlocked = status.startsWith("blocked_");
  const isManual = status === "manual_confirmation_required";
  const isAnalysisOnly = status === "analysis_only";
  let icon = "○";
  let cssVar = "var(--mp-mute)";
  if (isBlocked) {
    icon = "■";
    cssVar = "var(--mp-block)";
  } else if (isManual || isAnalysisOnly) {
    icon = "△";
    cssVar = "var(--mp-stale)";
  } else if (status === "normal_review") {
    icon = "●";
    cssVar = "var(--mp-live)";
  }
  return (
    <section
      style={{ ...styles.banner, borderColor: cssVar }}
      role="status"
      aria-label={`Review actionability: ${ACTIONABILITY_LABEL[status]}`}
    >
      <span style={{ ...styles.bannerIcon, color: cssVar }} aria-hidden="true">
        {icon}
      </span>
      <div>
        <p style={styles.bannerLabel}>{ACTIONABILITY_LABEL[status]}</p>
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

function PortfolioContextBlock({ context }: { context: PortfolioContextSummaryRead }) {
  const cashStateMeta: Record<
    PortfolioContextSummaryRead["cash_state"],
    { icon: string; cssVar: string; label: string }
  > = {
    available: { icon: "●", cssVar: "var(--mp-live)", label: "Available" },
    unavailable: { icon: "△", cssVar: "var(--mp-stale)", label: "Unavailable" },
    not_exposed: { icon: "○", cssVar: "var(--mp-mute)", label: "Not exposed" },
  };
  const brokerFresh = context.broker_snapshot.freshness_status;
  const brokerStale = ["stale", "unknown", "error", "reauth_required"].includes(brokerFresh);
  const cs = cashStateMeta[context.cash_state];
  return (
    <section
      style={{ ...styles.card, borderLeft: "3px solid var(--mp-accent)" }}
      aria-label="Portfolio context (server-owned; Phase 18C)"
    >
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Portfolio context</span>
        <span style={styles.detTag}>server-owned · Phase 18C</span>
      </div>
      {brokerStale && (
        <p style={styles.caveatInline} role="status">
          <span aria-hidden="true">△ </span>
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
            <span aria-hidden="true">{cs.icon} </span>
            {cs.label}{" "}
            <span style={styles.mono}>({context.cash_state})</span>
          </span>
        </li>
      </ul>
      <p style={styles.cardFoot}>
        Only safe portfolio metadata is exposed here — counts and category labels, no
        holdings, no balances, no account / provider identifiers. Broker snapshot
        freshness shown above is a different scope from market quote freshness
        (see Freshness panel below).
      </p>
    </section>
  );
}

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

function DeterministicSections({ review }: { review: DeterministicTradeReviewRead }) {
  return (
    <>
      <section style={styles.card} aria-label="Portfolio impact summary (deterministic)">
        <div style={styles.cardHead}>
          <span style={styles.cardTitle}>Portfolio impact</span>
          <span style={styles.detTag}>deterministic</span>
        </div>
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
      </section>

      <section style={styles.card} aria-label="Cash / collateral impact (deterministic)">
        <div style={styles.cardHead}>
          <span style={styles.cardTitle}>Cash / collateral impact</span>
          <span style={styles.detTag}>deterministic</span>
        </div>
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
      </section>

      <section style={styles.card} aria-label="Concentration / allocation impact (deterministic)">
        <div style={styles.cardHead}>
          <span style={styles.cardTitle}>Concentration / allocation impact</span>
          <span style={styles.detTag}>deterministic</span>
        </div>
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
      </section>

      <section style={styles.card} aria-label="Options exposure (deterministic)">
        <div style={styles.cardHead}>
          <span style={styles.cardTitle}>Options assignment / exercise / call-away exposure</span>
          <span style={styles.detTag}>deterministic</span>
        </div>
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
            <span aria-hidden="true">△ </span>
            Covered-call stock coverage is <strong>not fully netted</strong> against existing
            long positions in Phase 18A. Confirm coverage in your broker before any manual action.
          </p>
        )}
        {review.options_exposure.cash_secured_put_collateral_model === "generic_rule_only" && (
          <p style={styles.caveatInline}>
            <span aria-hidden="true">△ </span>
            Cash-secured-put collateral here uses a <strong>generic deterministic rule</strong>,
            not your broker's margin treatment. Verify the actual collateral hold in the broker
            before any manual action.
          </p>
        )}
      </section>

      <section style={styles.card} aria-label="Scenario payoff summary (deterministic)">
        <div style={styles.cardHead}>
          <span style={styles.cardTitle}>Scenario payoff</span>
          <span style={styles.detTag}>deterministic</span>
        </div>
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
      </section>
    </>
  );
}

function ViolationsBlock({ violations }: { violations: RiskRuleViolationSummaryRead[] }) {
  return (
    <section style={styles.card} aria-label="Deterministic risk-rule violations">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Risk-rule violations</span>
        <span style={styles.detTag}>deterministic</span>
      </div>
      {violations.length === 0 ? (
        <p style={styles.emptyMsg}>No rule entries were produced.</p>
      ) : (
        SEVERITY_ORDER.map((sev) => {
          const group = violations.filter((v) => v.severity === sev);
          if (group.length === 0) return null;
          const m = SEVERITY_META[sev];
          return (
            <div key={sev} style={styles.sevGroup}>
              <h3 style={{ ...styles.sevHeading, color: m.cssVar }}>
                <span aria-hidden="true">{m.icon} </span>
                {m.label} ({group.length})
              </h3>
              <ul style={styles.sevList}>
                {group.map((v) => (
                  <li key={v.code + (v.metric ?? "")} style={styles.violation}>
                    <div style={styles.violationTop}>
                      <span style={{ ...styles.sevChip, color: m.cssVar, borderColor: m.cssVar }}>
                        {m.icon} {m.label}
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
        })
      )}
    </section>
  );
}

function WarningsBlock({ warnings }: { warnings: MissingDataWarningRead[] }) {
  return (
    <section style={styles.card} aria-label="Missing or stale data warnings">
      <div style={styles.cardHead}>
        <span style={styles.cardTitle}>Missing / stale data warnings</span>
        <span style={styles.detTag}>deterministic</span>
      </div>
      {warnings.length === 0 ? (
        <p style={styles.emptyMsg}>No missing-data warnings.</p>
      ) : (
        <ul style={styles.sevList}>
          {warnings.map((w) => {
            const meta = CAVEAT_META[w.severity];
            return (
              <li key={w.code + w.scope} style={styles.violation}>
                <div style={styles.violationTop}>
                  <span style={{ ...styles.sevChip, color: meta.cssVar, borderColor: meta.cssVar }}>
                    {meta.icon} {meta.label}
                  </span>
                  <span style={styles.mono}>{w.code}</span>
                  <span style={styles.scopeChip}>{w.scope}</span>
                </div>
                <p style={styles.violationMsg}>{w.message}</p>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

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
          const meta = CAVEAT_META[c.severity];
          return (
            <li key={c.code + c.applies_to} style={styles.violation}>
              <div style={styles.violationTop}>
                <span style={{ ...styles.sevChip, color: meta.cssVar, borderColor: meta.cssVar }}>
                  {meta.icon} {meta.label}
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
        <details style={styles.markdownDetails}>
          <summary style={styles.markdownSummary}>Show raw markdown</summary>
          <pre style={styles.markdownPre}>{report.content_markdown}</pre>
        </details>
      )}
    </section>
  );
}

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

const styles: Record<string, React.CSSProperties> = {
  wrap: { display: "flex", flexDirection: "column", gap: "var(--space-4)" },
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
  bannerIcon: { fontSize: "var(--font-size-lg)", flexShrink: 0, lineHeight: 1.2 },
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
  reasonItem: { display: "flex", gap: "var(--space-2)", fontSize: "var(--font-size-xs)", alignItems: "baseline", flexWrap: "wrap" },
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
  },
  reasonMsg: { color: "var(--mp-ink-2)" },
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
  card: {
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
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
  },
  cardFoot: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0, lineHeight: 1.6 },
  freshnessGrid: { display: "flex", gap: "var(--space-5)", flexWrap: "wrap" },
  freshnessCol: { flex: "1 1 260px", minWidth: 260, display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  freshnessHead: { fontSize: "var(--font-size-xs)", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--mp-mute)", margin: 0 },
  facts: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  factRow: { display: "flex", gap: "var(--space-4)", fontSize: "var(--font-size-xs)", alignItems: "baseline" },
  factKey: { minWidth: 200, color: "var(--mp-mute)" },
  mono: { fontFamily: "var(--mp-font-mono, monospace)", color: "var(--mp-ink-2)" },
  legList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  legRow: { display: "flex", flexDirection: "column", gap: "var(--space-1)", fontSize: "var(--font-size-xs)" },
  legMeta: { color: "var(--mp-mute)" },
  caveatInline: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-ink-2)",
    margin: 0,
    padding: "var(--space-2) var(--space-3)",
    border: "1px solid var(--mp-stale)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
  },
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
  payoffList: { margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  payoffRow: { display: "flex", flexDirection: "column", gap: "var(--space-1)", fontSize: "var(--font-size-xs)" },
  payoffLabel: { fontWeight: 700, color: "var(--mp-ink-2)" },
  payoffDesc: { color: "var(--mp-mute)" },
  noteList: { margin: 0, padding: 0, listStyle: "none", fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  note: { lineHeight: 1.5 },
  reportTitle: { fontWeight: 700, fontSize: "var(--font-size-sm)", color: "var(--mp-ink)", margin: 0 },
  reportNote: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0, lineHeight: 1.6 },
  subBlock: { display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  subHead: { fontSize: "var(--font-size-xs)", textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--mp-mute)", margin: 0 },
  subBody: { fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)", margin: 0 },
  markdownDetails: { fontSize: "var(--font-size-xs)" },
  markdownSummary: { cursor: "pointer", color: "var(--mp-mute)" },
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
