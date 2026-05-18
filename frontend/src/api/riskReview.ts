/**
 * Deterministic risk review — STUBBED DATA SOURCE.
 *
 * There is NO backend risk API route yet (P13 shipped the contract/services,
 * not an HTTP endpoint). This module returns synthetic data shaped exactly
 * like `DeterministicRiskReportRead` so the read-only UI can be built and
 * verified against the typed contract. It performs NO network calls and
 * stores nothing in browser storage. When a backend route lands, replace
 * `fetchRiskReportStub` with a real `apiClient.get<DeterministicRiskReportRead>`
 * call — the component tree and types stay unchanged.
 *
 * All values here are synthetic placeholders (symbol "XYZ"), never real
 * holdings or account data.
 */
import type {
  DeterministicRiskReportRead,
  MarketDataSnapshotReferenceRead,
} from "../types/api";

export const RISK_REVIEW_STUB_NOTICE =
  "Synthetic sample — no backend risk endpoint is connected yet. Values are " +
  "placeholders to illustrate the deterministic contract, not real holdings.";

export type RiskReviewScenario =
  | "ok"
  | "blocker"
  | "empty"
  | "loading"
  | "missing_market"
  | "stale_quote"
  | "broker_stale"
  | "error";

function quoteRef(
  overrides: Partial<MarketDataSnapshotReferenceRead> = {},
): MarketDataSnapshotReferenceRead {
  return {
    snapshot_id: "snap_stub_0001",
    kind: "option_quote",
    purpose: "report_input_snapshot",
    provider: "manual",
    stable_key: "XYZ|2026-06-19|45|P",
    captured_at: "2026-05-17T14:30:00Z",
    quote_time: "2026-05-17T14:28:00Z",
    freshness_scope: "market_quote",
    data_mode: "manual",
    freshness_status: "manual",
    actionability_status: "analysis_only",
    ...overrides,
  };
}

function baseReport(): DeterministicRiskReportRead {
  return {
    generated_at: "2026-05-17T14:30:05Z",
    calculation_version: "risk.v1 (synthetic stub)",
    sections: [
      {
        title: "Option Metrics",
        facts: {
          underlying_symbol: "XYZ",
          contract: "XYZ 2026-06-19 P45",
          premium_per_contract: "1.85",
          breakeven_price: "43.15",
          max_loss_per_contract: "4315.00",
          simple_annualized_roi: "0.214",
          days_to_expiration: 33,
        },
      },
      {
        title: "Collateral",
        facts: {
          collateral_requirement: "4500.00",
          collateral_method: "short_option_cash_reserve",
          contracts: 1,
        },
      },
      {
        title: "Assignment / Exercise Scenarios",
        facts: {
          assignment_shares: 100,
          assignment_cost_basis: "43.15",
          scenario: "if assigned at expiration and held",
        },
      },
      {
        title: "Allocation Impact",
        facts: {
          position_notional: "4500.00",
          allocation_note: "deterministic; broker cash not included in this report",
        },
      },
    ],
    risk_rule_violations: [
      {
        code: "INFO_DTE_WINDOW",
        severity: "info",
        message: "Days to expiration is within the configured analysis window.",
        source: "violations",
        metric: "days_to_expiration",
        actual: "33",
        threshold: "7..45",
      },
      {
        code: "WARN_COLLATERAL_CONCENTRATION",
        severity: "warning",
        message: "Single-position collateral exceeds the soft concentration guide.",
        source: "collateral",
        metric: "collateral_requirement",
        actual: "4500.00",
        threshold: "4000.00",
      },
      {
        code: "VIOLATION_ROI_BELOW_FLOOR",
        severity: "violation",
        message:
          "Simple annualized ROI is below the configured deterministic floor.",
        source: "report",
        metric: "simple_annualized_roi",
        actual: "0.214",
        threshold: "0.250",
      },
    ],
    highest_severity: "violation",
    has_blocker: false,
    input_snapshot: {
      report_input_snapshot_id: "ris_stub_0001",
      quote_references: [quoteRef()],
      chain_references: [
        quoteRef({
          kind: "option_chain",
          snapshot_id: "snap_stub_chain",
          // Option-chain references use underlying:expiration semantics,
          // not the per-contract underlying|exp|strike|type quote key.
          stable_key: "XYZ:2026-06-19",
        }),
      ],
      captured_at: "2026-05-17T14:30:00Z",
      uses_current_quotes: false,
    },
    markdown: "(deterministic markdown omitted in stub)",
  };
}

/**
 * Returns a synthetic report (or simulates a state) for the given scenario.
 * `loading` never resolves; `error` rejects; `empty` resolves to null.
 */
export function fetchRiskReportStub(
  scenario: RiskReviewScenario,
): Promise<DeterministicRiskReportRead | null> {
  if (scenario === "loading") {
    return new Promise(() => {
      /* intentionally pending to exercise the loading state */
    });
  }
  if (scenario === "error") {
    return Promise.reject(new Error("Stubbed risk-report fetch failure (no backend route)."));
  }
  if (scenario === "empty") {
    return Promise.resolve(null);
  }

  const report = baseReport();

  if (scenario === "blocker") {
    report.risk_rule_violations = [
      ...report.risk_rule_violations,
      {
        code: "BLOCKER_MISSING_REQUIRED_INPUT",
        severity: "blocker",
        message:
          "A required deterministic input is missing; report cannot be relied upon.",
        source: "report",
        metric: null,
        actual: null,
        threshold: null,
      },
    ];
    report.highest_severity = "blocker";
    report.has_blocker = true;
  }

  if (scenario === "missing_market") {
    report.input_snapshot = null;
  }

  if (scenario === "stale_quote") {
    report.input_snapshot = {
      ...report.input_snapshot!,
      quote_references: [
        quoteRef({ data_mode: "delayed", freshness_status: "stale" }),
      ],
    };
  }

  if (scenario === "broker_stale") {
    // Broker-portfolio staleness is a separate scope; the deterministic risk
    // report itself stays market-scoped. Surface it as an advisory banner
    // input rather than mutating market-quote provenance.
    report.sections = report.sections.map((sec) =>
      sec.title === "Allocation Impact"
        ? {
            ...sec,
            facts: {
              ...sec.facts,
              broker_portfolio_freshness: "stale (broker sync) — separate scope",
            },
          }
        : sec,
    );
  }

  return Promise.resolve(report);
}
