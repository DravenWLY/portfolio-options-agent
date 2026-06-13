import { useEffect, useState, type FormEvent } from "react";
import type {
  SupportedTradeReviewFlow,
  TradeReviewWorkspacePreviewRequest,
  TradeReviewPortfolioPreviewRequest,
  TradeReviewPreviewOptionLeg,
  TradeReviewSubmission,
  PortfolioContextSelectionMode,
} from "../../types/tradeReview";
import type { AccountDetailAccountRead } from "../../types/accountDetails";
import SymbolAutocomplete from "./SymbolAutocomplete";
import { promoteSymbolRecent } from "../../lib/symbolRecents";
import { useAccountContext } from "../../context/useAccountContext";
import { accountDetailsApi } from "../../api/accountDetails";

/**
 * TradeReviewForm — collects manual inputs for the four Phase 18A flows.
 *
 * Hard constraints:
 *  - No order/execute/place/cancel/disconnect controls. This is a *preview*
 *    request only; the backend returns analysis, not an order.
 *  - No frontend financial computation. Inputs are validated for shape only.
 *  - Numeric inputs are serialized as strings to avoid JS float drift.
 *  - Backend validator forbids mixing stock-fields with option_leg; the form
 *    enforces the same branching here.
 *
 * Phase 18C: review mode toggles between portfolio-backed (default) and the
 * synthetic-only preview. The frontend never sends broker/market freshness,
 * provider status, cash, holdings, or thresholds — the backend owns those.
 * Context references are opaque demo refs only.
 */

type ReviewMode = "portfolio" | "synthetic";

const DEMO_CONTEXT_REFS: { value: string; label: string; help: string }[] = [
  { value: "ctx_demo_latest", label: "ctx_demo_latest", help: "Latest-like demo context (cash + positions present)" },
  { value: "ctx_demo_stale", label: "ctx_demo_stale", help: "Demo context with a stale broker snapshot" },
  { value: "ctx_demo_missing", label: "ctx_demo_missing", help: "Demo context with missing/unknown market quotes" },
  { value: "ctx_demo_empty", label: "ctx_demo_empty", help: "No portfolio context available (empty)" },
];

const FLOW_OPTIONS: {
  value: SupportedTradeReviewFlow | "stock_etf_buy" | "stock_etf_sell_trim";
  label: string;
}[] = [
  { value: "stock_etf_buy", label: "Stock / ETF buy" },
  { value: "stock_etf_sell_trim", label: "Stock / ETF sell or trim" },
  { value: "covered_call", label: "Covered call" },
  { value: "cash_secured_put", label: "Cash-secured put" },
];

type FlowGroup =
  | "stock_etf_buy"
  | "stock_etf_sell_trim"
  | "covered_call"
  | "cash_secured_put";

interface TradeReviewFormProps {
  onSubmit: (submission: TradeReviewSubmission) => void;
  busy: boolean;
  /** P19A-T6: when true, hide the synthetic-preview radio and force
   *  portfolio-backed submissions. Default false preserves the original
   *  TradeReviewPage UX. */
  hideSyntheticMode?: boolean;
}

export default function TradeReviewForm({
  onSubmit,
  busy,
  hideSyntheticMode = false,
}: TradeReviewFormProps) {
  const { selectedUser } = useAccountContext();
  const userId = selectedUser?.id ?? null;

  const [reviewMode, setReviewMode] = useState<ReviewMode>("portfolio");
  const [contextMode, setContextMode] =
    useState<PortfolioContextSelectionMode>("latest_available");
  const [contextRef, setContextRef] = useState<string>(DEMO_CONTEXT_REFS[0].value);

  // Phase 27C: review-account selection. "" = no review account selected
  // (submits review_account_selection.mode="unselected"). Accounts come from
  // the reviewed Account Details overview; only the opaque account_reference is
  // ever submitted, and only display labels are shown.
  const [reviewAccountRef, setReviewAccountRef] = useState<string>("");
  const [accounts, setAccounts] = useState<AccountDetailAccountRead[]>([]);
  const [accountsStatus, setAccountsStatus] =
    useState<"idle" | "loading" | "ready" | "error">("idle");

  useEffect(() => {
    if (reviewMode !== "portfolio" || !userId) {
      setAccounts([]);
      setAccountsStatus("idle");
      return;
    }
    let cancelled = false;
    setAccountsStatus("loading");
    accountDetailsApi
      .get(userId)
      .then((res) => {
        if (cancelled) return;
        setAccounts(res.accounts);
        setAccountsStatus("ready");
        // Drop a stale selection if the account is no longer present.
        setReviewAccountRef((prev) =>
          res.accounts.some((a) => a.account_reference === prev) ? prev : "",
        );
      })
      .catch(() => {
        if (cancelled) return;
        setAccounts([]);
        setAccountsStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [reviewMode, userId]);
  const [flowGroup, setFlowGroup] = useState<FlowGroup>("stock_etf_buy");
  const [assetClass, setAssetClass] = useState<"stock" | "etf">("stock");

  // Stock/ETF fields
  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [priceAssumption, setPriceAssumption] = useState("");

  // Option fields (covered call / CSP)
  const [underlying, setUnderlying] = useState("");
  const [expiration, setExpiration] = useState("2026-06-19");
  const [strike, setStrike] = useState("45");
  const [optQuantity, setOptQuantity] = useState("1");
  const [premium, setPremium] = useState("1.85");
  const [multiplier, setMultiplier] = useState("100");

  const [validationError, setValidationError] = useState<string | null>(null);

  function resolveFlow(): SupportedTradeReviewFlow {
    if (flowGroup === "stock_etf_buy") return assetClass === "etf" ? "etf_buy" : "stock_buy";
    if (flowGroup === "stock_etf_sell_trim")
      return assetClass === "etf" ? "etf_sell_trim" : "stock_sell_trim";
    return flowGroup; // "covered_call" | "cash_secured_put"
  }

  function validate(): string | null {
    const sf = resolveFlow();
    const isStockEtf =
      sf === "stock_buy" || sf === "stock_sell_trim" || sf === "etf_buy" || sf === "etf_sell_trim";
    if (isStockEtf) {
      if (!symbol.trim()) return "Symbol is required.";
      if (!/^[A-Z0-9.\-_]+$/i.test(symbol.trim())) return "Symbol contains invalid characters.";
      if (!isPositiveDecimal(quantity)) return "Quantity must be a positive number.";
      if (!isPositiveDecimal(priceAssumption)) return "Price assumption must be a positive number.";
      return null;
    }
    if (!underlying.trim()) return "Underlying symbol is required.";
    if (!/^\d{4}-\d{2}-\d{2}$/.test(expiration)) return "Expiration must be YYYY-MM-DD.";
    if (!isPositiveDecimal(strike)) return "Strike must be a positive number.";
    if (!isPositiveDecimal(optQuantity)) return "Contracts must be a positive number.";
    if (premium.trim() !== "" && !isNonNegativeDecimal(premium))
      return "Premium must be a non-negative number.";
    if (!isPositiveDecimal(multiplier)) return "Multiplier must be a positive number.";
    return null;
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const err = validate();
    if (err) {
      setValidationError(err);
      return;
    }
    setValidationError(null);

    const sf = resolveFlow();
    const isStockEtf =
      sf === "stock_buy" || sf === "stock_sell_trim" || sf === "etf_buy" || sf === "etf_sell_trim";

    // On successful submit, promote an already-known browser-local recent to
    // the top (move-to-top only). We do not fabricate a new recent here:
    // creating one for a typed-but-never-selected symbol would require
    // validated display fields (name/exchange/etc.), which is deferred to a
    // future validate() wiring. Recents are still recorded on selection.
    promoteSymbolRecent((isStockEtf ? symbol : underlying).trim().toUpperCase());

    const intent: TradeReviewWorkspacePreviewRequest = isStockEtf
      ? {
          supported_flow: sf,
          symbol: symbol.trim().toUpperCase(),
          quantity: quantity.trim(),
          price_assumption: priceAssumption.trim(),
        }
      : {
          supported_flow: sf,
          option_leg: ((): TradeReviewPreviewOptionLeg => ({
            underlying_symbol: underlying.trim().toUpperCase(),
            option_type: sf === "covered_call" ? "call" : "put",
            leg_action: "sell_to_open",
            expiration_date: expiration,
            strike: strike.trim(),
            quantity: optQuantity.trim(),
            premium: premium.trim() === "" ? null : premium.trim(),
            multiplier: multiplier.trim(),
          }))(),
        };

    if (reviewMode === "synthetic") {
      onSubmit({ kind: "synthetic", payload: intent });
      return;
    }

    const portfolio: TradeReviewPortfolioPreviewRequest = {
      ...intent,
      review_account_selection:
        reviewAccountRef === ""
          ? { mode: "unselected" }
          : { mode: "selected_account", account_reference: reviewAccountRef },
      portfolio_context_selection:
        contextMode === "latest_available"
          ? { mode: "latest_available" }
          : { mode: "selected_context", context_reference: contextRef },
    };
    onSubmit({ kind: "portfolio", payload: portfolio });
  }

  const stockEtfActive = flowGroup === "stock_etf_buy" || flowGroup === "stock_etf_sell_trim";

  return (
    <form style={styles.form} onSubmit={handleSubmit} aria-label="Trade review preview inputs">
      {!hideSyntheticMode && (
        <fieldset style={styles.fieldset} aria-label="Review mode">
          <legend style={styles.legend}>Review mode</legend>
          <div style={styles.radioRow}>
            <label style={styles.radioOption}>
              <input
                type="radio"
                name="reviewMode"
                value="portfolio"
                checked={reviewMode === "portfolio"}
                onChange={() => setReviewMode("portfolio")}
                disabled={busy}
              />
              <span>
                <strong>Portfolio-backed</strong> — server-owned context (Phase 18C)
              </span>
            </label>
            <label style={styles.radioOption}>
              <input
                type="radio"
                name="reviewMode"
                value="synthetic"
                checked={reviewMode === "synthetic"}
                onChange={() => setReviewMode("synthetic")}
                disabled={busy}
              />
              <span>
                <strong>Synthetic preview</strong> — dev fallback, no portfolio context
              </span>
            </label>
          </div>
        </fieldset>
      )}

      {reviewMode === "portfolio" && (
        <fieldset style={styles.fieldset} aria-label="Review account selection">
          <legend style={styles.legend}>Review account</legend>
          <p style={styles.scopeLead}>
            The account where you would manually place this trade. Account-level
            feasibility context is only considered when a review account is selected.
          </p>
          {!userId ? (
            <p style={styles.contextNote}>
              Select a user in the account selector to load connected accounts.
            </p>
          ) : accountsStatus === "loading" ? (
            <p style={styles.contextNote}>Loading connected accounts…</p>
          ) : accountsStatus === "error" ? (
            <p style={styles.contextNote}>
              Connected accounts are unavailable right now. You can still run a review
              with no review account selected.
            </p>
          ) : (
            <>
              <label style={styles.fieldFull}>
                <span style={styles.labelText}>Review account</span>
                <select
                  style={{ ...styles.input, ...styles.selectFull }}
                  value={reviewAccountRef}
                  onChange={(e) => setReviewAccountRef(e.target.value)}
                  disabled={busy}
                >
                  <option value="">No review account selected</option>
                  {accounts.map((a) => (
                    <option key={a.account_reference} value={a.account_reference}>
                      {a.account_kind_label
                        ? `${a.display_label} · ${a.account_kind_label}`
                        : a.display_label}
                    </option>
                  ))}
                </select>
              </label>
              {accountsStatus === "ready" && accounts.length === 0 && (
                <p style={styles.contextNote}>No connected accounts found for this user.</p>
              )}
            </>
          )}
        </fieldset>
      )}

      {reviewMode === "portfolio" && (
        <fieldset style={styles.fieldset} aria-label="Broader portfolio context selection">
          <legend style={styles.legend}>Broader portfolio context</legend>
          <p style={styles.scopeLead}>
            The wider exposure context used for awareness — concentration, exposure,
            and data freshness. This is separate from the review account above and
            may cover more than one account.
          </p>
          <div style={styles.radioRow}>
            <label style={styles.radioOption}>
              <input
                type="radio"
                name="contextMode"
                value="latest_available"
                checked={contextMode === "latest_available"}
                onChange={() => setContextMode("latest_available")}
                disabled={busy}
              />
              <span>Latest available context</span>
            </label>
            <label style={styles.radioOption}>
              <input
                type="radio"
                name="contextMode"
                value="selected_context"
                checked={contextMode === "selected_context"}
                onChange={() => setContextMode("selected_context")}
                disabled={busy}
              />
              <span>Specific demo context reference</span>
            </label>
          </div>
          {contextMode === "selected_context" && (
            <label style={styles.fieldFull}>
              <span style={styles.labelText}>Demo context reference (opaque)</span>
              <select
                style={{ ...styles.input, ...styles.selectFull }}
                value={contextRef}
                onChange={(e) => setContextRef(e.target.value)}
                disabled={busy}
              >
                {DEMO_CONTEXT_REFS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label} — {o.help}
                  </option>
                ))}
              </select>
            </label>
          )}
          <p style={styles.contextNote}>
            Context references are opaque and server-owned. The frontend never sends
            broker freshness, market freshness, provider status, cash, holdings, or thresholds.
          </p>
        </fieldset>
      )}

      <div style={styles.row}>
        <label style={styles.label}>
          <span style={styles.labelText}>Flow</span>
          <select
            style={styles.input}
            value={flowGroup}
            onChange={(e) => setFlowGroup(e.target.value as FlowGroup)}
            disabled={busy}
          >
            {FLOW_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        {stockEtfActive && (
          <label style={styles.label}>
            <span style={styles.labelText}>Asset class</span>
            <select
              style={styles.input}
              value={assetClass}
              onChange={(e) => setAssetClass(e.target.value as "stock" | "etf")}
              disabled={busy}
            >
              <option value="stock">Stock</option>
              <option value="etf">ETF</option>
            </select>
          </label>
        )}
      </div>

      {stockEtfActive ? (
        <div style={styles.row}>
          <SymbolAutocomplete
            label="Symbol"
            value={symbol}
            onChange={setSymbol}
            disabled={busy}
            placeholder="Search symbols, names"
          />
          <TextField label="Quantity" value={quantity} onChange={setQuantity} disabled={busy} mono inputMode="decimal" />
          <TextField
            label={flowGroup === "stock_etf_buy" ? "Assumed buy price" : "Assumed sell price"}
            value={priceAssumption}
            onChange={setPriceAssumption}
            disabled={busy}
            mono
            inputMode="decimal"
          />
        </div>
      ) : (
        <>
          <div style={styles.row}>
            <SymbolAutocomplete
              label="Underlying"
              value={underlying}
              onChange={setUnderlying}
              disabled={busy}
              placeholder="Search symbols, names"
            />
            <TextField label="Expiration (YYYY-MM-DD)" value={expiration} onChange={setExpiration} disabled={busy} mono type="date" />
            <TextField label="Strike" value={strike} onChange={setStrike} disabled={busy} mono inputMode="decimal" />
          </div>
          <div style={styles.row}>
            <TextField label="Contracts" value={optQuantity} onChange={setOptQuantity} disabled={busy} mono inputMode="decimal" />
            <TextField label="Premium per share (optional)" value={premium} onChange={setPremium} disabled={busy} mono inputMode="decimal" />
            <TextField label="Multiplier" value={multiplier} onChange={setMultiplier} disabled={busy} mono inputMode="decimal" />
          </div>
          <p style={styles.optionNote}>
            Sell-to-open is assumed for both covered call and cash-secured put in Phase 18A.
          </p>
        </>
      )}

      {validationError && (
        <p style={styles.error} role="alert">
          <span aria-hidden="true">⚠ </span>
          {validationError}
        </p>
      )}

      <div style={styles.actions}>
        <button type="submit" style={styles.submit} disabled={busy}>
          {busy
            ? "Generating analysis…"
            : reviewMode === "portfolio"
              ? "Generate analysis"
              : "Generate synthetic analysis"}
        </button>
        <p style={styles.previewNote}>
          Manual review only. No order is placed. No broker action is taken.
        </p>
      </div>
    </form>
  );
}

function TextField({
  label,
  value,
  onChange,
  disabled,
  mono,
  inputMode,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  disabled: boolean;
  mono?: boolean;
  inputMode?: "decimal" | "numeric" | "text";
  type?: string;
}) {
  return (
    <label style={styles.label}>
      <span style={styles.labelText}>{label}</span>
      <input
        style={{ ...styles.input, ...(mono ? styles.inputMono : {}) }}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        inputMode={inputMode}
        type={type}
        autoComplete="off"
        spellCheck={false}
      />
    </label>
  );
}

function isPositiveDecimal(v: string): boolean {
  if (v.trim() === "") return false;
  const n = Number(v);
  return Number.isFinite(n) && n > 0;
}
function isNonNegativeDecimal(v: string): boolean {
  if (v.trim() === "") return false;
  const n = Number(v);
  return Number.isFinite(n) && n >= 0;
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
    minWidth: 0,
  },
  row: { display: "flex", gap: "var(--space-3)", flexWrap: "wrap" },
  label: { display: "flex", flexDirection: "column", gap: "var(--space-1)", minWidth: 180, flex: "1 1 180px" },
  labelText: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  input: {
    fontSize: "var(--font-size-sm)",
    padding: "var(--space-2) var(--space-3)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
    color: "var(--mp-ink)",
    boxSizing: "border-box",
    minWidth: 0,
    maxWidth: "100%",
  },
  inputMono: { fontFamily: "var(--font-mono, monospace)" },
  optionNote: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0 },
  error: {
    fontSize: "var(--font-size-sm)",
    color: "var(--mp-block)",
    margin: 0,
    fontWeight: 600,
  },
  actions: { display: "flex", alignItems: "center", gap: "var(--space-4)", flexWrap: "wrap" },
  submit: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    padding: "var(--space-2) var(--space-5)",
    border: "2px solid var(--mp-accent)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-accent)",
    color: "var(--mp-paper)",
    cursor: "pointer",
  },
  previewNote: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0, fontStyle: "italic" },
  fieldset: {
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-3)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
    margin: 0,
    minWidth: 0,
  },
  /* Full-width single-select field placed directly in a column fieldset.
     Unlike `label` (tuned for side-by-side rows with flex-basis 180px), this
     never grows on the vertical main axis and shrinks safely in the rail. */
  fieldFull: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1)",
    width: "100%",
    minWidth: 0,
  },
  selectFull: { width: "100%", maxWidth: "100%", minWidth: 0, boxSizing: "border-box" },
  legend: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    padding: "0 var(--space-1)",
  },
  radioRow: { display: "flex", gap: "var(--space-4)", flexWrap: "wrap" },
  radioOption: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-ink-2)",
  },
  contextNote: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    margin: 0,
    lineHeight: 1.6,
  },
  scopeLead: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-ink-2)",
    margin: 0,
    lineHeight: 1.6,
  },
};
