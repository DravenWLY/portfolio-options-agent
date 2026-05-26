import { useEffect, useState, useCallback } from "react";
import { Badge, DemoChip, KV, MpIcon, PageHeader, Panel, Pill, SafetyStrip } from "../components/shared/mp";
import { LoadingSkeleton, ErrorState, EmptyState } from "../components/shared/StateViews";
import { useAccountContext } from "../context/useAccountContext";
import { portfolioContextApi } from "../api/portfolioContext";
import { ApiRequestError } from "../api/client";
import type {
  PortfolioContextListRead,
  PortfolioContextRead,
  PortfolioContextDetailRead,
  PortfolioContextFreshnessRead,
} from "../types/portfolioContext";
import type { MpTone } from "../components/shared/mp";

/**
 * PortfolioContextPage — Modern Portfolio Desk standalone context page.
 *
 * P20B-T4 wiring: backend-backed demo read surface.
 *
 * Approved endpoints consumed:
 *   GET /api/users/{uid}/portfolio-contexts
 *   GET /api/users/{uid}/portfolio-context/{ctx_ref}
 *
 * Safety:
 *   - Read-only. No order ticket / execute / cancel / buy / sell.
 *   - Renders only backend-provided safe fields. No frontend financial
 *     computation. No raw holdings, balances, account/provider ids.
 *   - Demo labeling is visible whenever data_mode is "synthetic_demo".
 *   - Broker snapshot freshness and market quote freshness are separate.
 *   - No localStorage / sessionStorage writes.
 */

type ListStatus = "idle" | "loading" | "success" | "empty" | "error";
type DetailStatus = "idle" | "loading" | "success" | "error";

export default function PortfolioContextPage() {
  const { selectedUser } = useAccountContext();
  const userId = selectedUser?.id ?? null;

  /* ── List state ──────────────────────────────────────────────────────── */
  const [listStatus, setListStatus] = useState<ListStatus>("idle");
  const [listData, setListData] = useState<PortfolioContextListRead | null>(null);
  const [listError, setListError] = useState<string | null>(null);

  /* ── Detail state ────────────────────────────────────────────────────── */
  const [detailStatus, setDetailStatus] = useState<DetailStatus>("idle");
  const [detailData, setDetailData] = useState<PortfolioContextDetailRead | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [selectedRef, setSelectedRef] = useState<string | null>(null);

  /* ── Load list ───────────────────────────────────────────────────────── */
  const loadList = useCallback(() => {
    if (!userId) return;
    setListStatus("loading");
    setListError(null);
    portfolioContextApi
      .list(userId)
      .then((res) => {
        setListData(res);
        setListStatus(res.items.length > 0 ? "success" : "empty");
      })
      .catch((err: unknown) => {
        const msg =
          err instanceof ApiRequestError ? err.detail :
          err instanceof Error ? err.message :
          "Failed to load portfolio contexts.";
        setListError(msg);
        setListStatus("error");
      });
  }, [userId]);

  useEffect(() => {
    if (userId) loadList();
  }, [userId, loadList]);

  /* ── Load detail ─────────────────────────────────────────────────────── */
  const loadDetail = useCallback(
    (ctxRef: string) => {
      if (!userId) return;
      setSelectedRef(ctxRef);
      setDetailStatus("loading");
      setDetailError(null);
      portfolioContextApi
        .detail(userId, ctxRef)
        .then((res) => {
          setDetailData(res);
          setDetailStatus("success");
        })
        .catch((err: unknown) => {
          const msg =
            err instanceof ApiRequestError ? err.detail :
            err instanceof Error ? err.message :
            "Failed to load portfolio context detail.";
          setDetailError(msg);
          setDetailStatus("error");
        });
    },
    [userId],
  );

  /* ── Demo notice ─────────────────────────────────────────────────────── */
  const isDemoMode = listData?.data_mode === "synthetic_demo";
  const demoNotice = listData?.demo_notice ?? null;

  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Workspace · portfolio context"
        title="Portfolio context"
        sub="Server-owned portfolio-context references used by Trade Review and Agent Console. The frontend never sends broker freshness, market freshness, provider status, cash, holdings, or thresholds. This page lists only safe metadata."
        right={isDemoMode ? <DemoChip /> : undefined}
      />

      {/* ── No user selected ───────────────────────────────────────────── */}
      {!userId && (
        <EmptyState
          title="No user selected"
          body="Select a user from the developer account selector to load portfolio context."
        />
      )}

      {/* ── List loading ───────────────────────────────────────────────── */}
      {userId && listStatus === "loading" && (
        <LoadingSkeleton rows={4} label="Loading portfolio contexts…" />
      )}

      {/* ── List error ─────────────────────────────────────────────────── */}
      {userId && listStatus === "error" && (
        <ErrorState
          message={listError ?? "Failed to load portfolio contexts."}
          onRetry={loadList}
        />
      )}

      {/* ── List empty ─────────────────────────────────────────────────── */}
      {userId && listStatus === "empty" && (
        <Panel title="Portfolio contexts" right={isDemoMode ? <DemoChip /> : undefined}>
          <EmptyState
            title="No portfolio contexts available"
            body="No portfolio context references have been created yet."
          />
          {demoNotice && <DemoNotice notice={demoNotice} />}
        </Panel>
      )}

      {/* ── List success ───────────────────────────────────────────────── */}
      {userId && listStatus === "success" && listData && (
        <>
          <Panel
            title="Context references"
            tag="opaque · server-owned"
            right={isDemoMode ? <DemoChip /> : undefined}
          >
            <table style={styles.tbl}>
              <thead>
                <tr>
                  <Th>Reference</Th>
                  <Th>Label</Th>
                  <Th>Source</Th>
                  <Th>Positions</Th>
                  <Th>Cash</Th>
                  <Th>Actionability</Th>
                  <Th align="right">Detail</Th>
                </tr>
              </thead>
              <tbody>
                {listData.items.map((ctx) => (
                  <tr
                    key={ctx.context_reference}
                    style={
                      selectedRef === ctx.context_reference
                        ? styles.selectedRow
                        : undefined
                    }
                  >
                    <Td mono>{ctx.context_reference}</Td>
                    <Td>{ctx.context_label}</Td>
                    <Td mono>{ctx.source_kind}</Td>
                    <Td mono>
                      {ctx.portfolio_shape.stock_position_count} stock ·{" "}
                      {ctx.portfolio_shape.option_position_count} options
                    </Td>
                    <Td mono>{ctx.cash_state_label}</Td>
                    <Td>
                      <Pill tone={actionabilityTone(ctx)}>
                        {ctx.actionability_preview.display_label}
                      </Pill>
                    </Td>
                    <Td align="right">
                      <button
                        type="button"
                        style={styles.viewBtn}
                        onClick={() => loadDetail(ctx.context_reference)}
                      >
                        View
                      </button>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
            {demoNotice && <DemoNotice notice={demoNotice} />}
          </Panel>

          {/* ── Detail panel ──────────────────────────────────────────── */}
          {detailStatus === "loading" && (
            <LoadingSkeleton rows={4} label="Loading context detail…" />
          )}
          {detailStatus === "error" && (
            <ErrorState
              message={detailError ?? "Failed to load detail."}
              onRetry={() => selectedRef && loadDetail(selectedRef)}
            />
          )}
          {detailStatus === "success" && detailData && (
            <ContextDetailView detail={detailData} />
          )}
        </>
      )}

      {/* ── Disclaimer ─────────────────────────────────────────────────── */}
      <Panel title="What this screen does and does not show">
        <ul style={styles.disclaimerList}>
          <li>Shows: safe context metadata only — opaque reference, source label, position counts, cash-state category, freshness scopes, actionability preview.</li>
          <li>Does not show: raw holdings, balances, account values, account/provider ids, OAuth tokens, raw provider payloads, or trade-journal entries.</li>
          <li>Does not perform any frontend financial computation.</li>
        </ul>
      </Panel>

      <SafetyStrip items={[
        "Analysis only",
        "Manual review",
        "Not an order recommendation",
        "Data freshness may affect review quality",
      ]} />
    </div>
  );
}

/* ── Context detail view ──────────────────────────────────────────────── */

function ContextDetailView({ detail }: { detail: PortfolioContextDetailRead }) {
  const ctx = detail.context;
  const isDemoMode = detail.data_mode === "synthetic_demo";

  return (
    <div style={styles.detailGrid}>
      {/* Summary panel */}
      <Panel
        title={ctx.context_label}
        tag={ctx.context_reference}
        right={isDemoMode ? <DemoChip /> : undefined}
      >
        <KV rows={[
          ["Source", ctx.source_kind],
          ["Stock positions (count)", String(ctx.portfolio_shape.stock_position_count)],
          ["Option positions (count)", String(ctx.portfolio_shape.option_position_count)],
          ["Cash state", ctx.cash_state_label],
        ]} />
        {ctx.available_flows.length > 0 && (
          <div style={styles.flowsRow}>
            <span style={styles.flowsLabel}>Available review flows</span>
            <div style={styles.flowsWrap}>
              {ctx.available_flows.map((f) => (
                <Badge key={f} tone="mute" dot={false}>{flowLabel(f)}</Badge>
              ))}
            </div>
          </div>
        )}
        {ctx.caveat_codes.length > 0 && (
          <div style={styles.caveatsRow}>
            <span style={styles.flowsLabel}>Caveat codes</span>
            <div style={styles.flowsWrap}>
              {ctx.caveat_codes.map((c) => (
                <Badge key={c} tone="stale" dot={false}>{c}</Badge>
              ))}
            </div>
          </div>
        )}
        {detail.demo_notice && <DemoNotice notice={detail.demo_notice} />}
      </Panel>

      {/* Broker snapshot freshness */}
      <FreshnessPanel
        freshness={ctx.broker_snapshot_freshness}
        label="Broker snapshot freshness"
        isDemoMode={isDemoMode}
      />

      {/* Market quote freshness */}
      {ctx.market_quote_freshness ? (
        <FreshnessPanel
          freshness={ctx.market_quote_freshness}
          label="Market quote freshness"
          isDemoMode={isDemoMode}
        />
      ) : (
        <Panel title="Market quote freshness" tag="unavailable">
          <div style={styles.unavailableWrap}>
            <MpIcon name="alert" size={16} style={{ color: "var(--mp-block)", flexShrink: 0, marginTop: 2 }} />
            <div>
              <p style={styles.unavailableTitle}>Market data unavailable</p>
              <p style={styles.unavailableBody}>
                No market quote freshness is available for this context.
                Reviews using this context operate in analysis-only mode for
                market-dependent checks.
              </p>
            </div>
          </div>
          {isDemoMode && (
            <div style={{ marginTop: "var(--space-2)" }}><DemoChip /></div>
          )}
        </Panel>
      )}

      {/* Actionability preview */}
      <Panel
        title="Actionability preview"
        tag="analysis-only"
        right={
          <Pill tone={actionabilityTone(ctx)}>
            {ctx.actionability_preview.overall_review_mode}
          </Pill>
        }
      >
        <KV rows={[
          ["Review actionability", ctx.actionability_preview.review_actionability_status],
          ["Overall review mode", ctx.actionability_preview.overall_review_mode],
          ["Display label", ctx.actionability_preview.display_label],
          ["Is blocking", ctx.actionability_preview.is_blocking ? "Yes" : "No"],
        ]} />
        {isDemoMode && (
          <div style={{ marginTop: "var(--space-2)" }}><DemoChip /></div>
        )}
      </Panel>
    </div>
  );
}

/* ── Freshness panel ──────────────────────────────────────────────────── */

function FreshnessPanel({
  freshness,
  label,
  isDemoMode,
}: {
  freshness: PortfolioContextFreshnessRead;
  label: string;
  isDemoMode: boolean;
}) {
  const tone = freshnessTone(freshness);
  return (
    <Panel
      title={label}
      tag={freshness.freshness_scope}
      right={<Pill tone={tone}>{freshness.status}</Pill>}
    >
      <KV rows={[
        ["Status", freshness.status],
        ["Display label", freshness.display_label],
        ["As of", freshness.as_of_label ?? "—"],
        ["Is blocking", freshness.is_blocking ? "Yes — blocking" : "No"],
      ]} />
      {freshness.reason_codes.length > 0 && (
        <div style={styles.caveatsRow}>
          <span style={styles.flowsLabel}>Reason codes</span>
          <div style={styles.flowsWrap}>
            {freshness.reason_codes.map((c) => (
              <Badge key={c} tone={tone} dot={false}>{c}</Badge>
            ))}
          </div>
        </div>
      )}
      {isDemoMode && (
        <div style={{ marginTop: "var(--space-2)" }}><DemoChip /></div>
      )}
    </Panel>
  );
}

/* ── Helpers ──────────────────────────────────────────────────────────── */

function DemoNotice({ notice }: { notice: string }) {
  return (
    <p style={styles.demoNotice}>
      <Badge tone="info" dot>synthetic demo</Badge>{" "}
      <span>{notice}</span>
    </p>
  );
}

function actionabilityTone(ctx: PortfolioContextRead): MpTone {
  if (ctx.actionability_preview.is_blocking) return "block";
  switch (ctx.actionability_preview.overall_review_mode) {
    case "normal_review": return "live";
    case "analysis_only": return "info";
    case "manual_confirmation_required": return "stale";
    case "blocked": return "block";
    default: return "mute";
  }
}

function freshnessTone(f: PortfolioContextFreshnessRead): MpTone {
  if (f.is_blocking) return "block";
  switch (f.status) {
    case "fresh": return "live";
    case "manual_review": return "stale";
    case "stale": return "block";
    case "unknown":
    case "unavailable": return "mute";
    default: return "mute";
  }
}

function flowLabel(flow: string): string {
  return flow.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ── Local sub-components ─────────────────────────────────────────────── */

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

/* ── Styles ───────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", gap: "var(--space-5)", maxWidth: 1280, margin: "0 auto", color: "var(--mp-ink)" },
  tbl: { width: "100%", borderCollapse: "collapse" },
  disclaimerList: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.6, margin: 0, paddingLeft: "var(--space-5)", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  demoNotice: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", marginTop: "var(--space-2)", display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" },
  selectedRow: { backgroundColor: "var(--mp-accent-soft)" },
  viewBtn: {
    background: "transparent", border: "1px solid var(--mp-rule-strong)",
    borderRadius: "var(--radius-sm)", padding: "3px 10px",
    fontSize: "var(--font-size-xs)", fontWeight: 600,
    color: "var(--mp-accent)", cursor: "pointer",
    fontFamily: "var(--mp-font-mono)",
  },
  detailGrid: { display: "flex", flexDirection: "column", gap: "var(--space-4)" },
  flowsRow: { marginTop: "var(--space-3)", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  caveatsRow: { marginTop: "var(--space-2)", display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  flowsLabel: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 },
  flowsWrap: { display: "flex", gap: "var(--space-1)", flexWrap: "wrap" },
  unavailableWrap: { display: "flex", gap: "var(--space-3)", alignItems: "flex-start" },
  unavailableTitle: { fontSize: "var(--font-size-sm)", fontWeight: 600, color: "var(--mp-block)", margin: 0, marginBottom: 4 },
  unavailableBody: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.6, margin: 0 },
};
