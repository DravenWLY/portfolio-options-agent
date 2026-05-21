import { useState, type FormEvent } from "react";
import type {
  SupportedTradeReviewFlow,
  TradeReviewWorkspacePreviewRequest,
  TradeReviewPreviewOptionLeg,
} from "../../types/tradeReview";

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
 */

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
  onSubmit: (request: TradeReviewWorkspacePreviewRequest) => void;
  busy: boolean;
}

export default function TradeReviewForm({ onSubmit, busy }: TradeReviewFormProps) {
  const [flowGroup, setFlowGroup] = useState<FlowGroup>("stock_etf_buy");
  const [assetClass, setAssetClass] = useState<"stock" | "etf">("stock");

  // Stock/ETF fields
  const [symbol, setSymbol] = useState("XYZ");
  const [quantity, setQuantity] = useState("100");
  const [priceAssumption, setPriceAssumption] = useState("50.00");

  // Option fields (covered call / CSP)
  const [underlying, setUnderlying] = useState("XYZ");
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

    if (isStockEtf) {
      onSubmit({
        supported_flow: sf,
        symbol: symbol.trim().toUpperCase(),
        quantity: quantity.trim(),
        price_assumption: priceAssumption.trim(),
      });
      return;
    }

    const leg: TradeReviewPreviewOptionLeg = {
      underlying_symbol: underlying.trim().toUpperCase(),
      option_type: sf === "covered_call" ? "call" : "put",
      leg_action: "sell_to_open",
      expiration_date: expiration,
      strike: strike.trim(),
      quantity: optQuantity.trim(),
      premium: premium.trim() === "" ? null : premium.trim(),
      multiplier: multiplier.trim(),
    };
    onSubmit({ supported_flow: sf, option_leg: leg });
  }

  const stockEtfActive = flowGroup === "stock_etf_buy" || flowGroup === "stock_etf_sell_trim";

  return (
    <form style={styles.form} onSubmit={handleSubmit} aria-label="Trade review preview inputs">
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
          <TextField label="Symbol" value={symbol} onChange={setSymbol} disabled={busy} mono />
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
            <TextField label="Underlying" value={underlying} onChange={setUnderlying} disabled={busy} mono />
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
          {busy ? "Generating preview…" : "Preview review"}
        </button>
        <p style={styles.previewNote}>
          Manual preview only. No order is placed. No broker action is taken.
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
    backgroundColor: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-md)",
    padding: "var(--space-4) var(--space-6)",
  },
  row: { display: "flex", gap: "var(--space-3)", flexWrap: "wrap" },
  label: { display: "flex", flexDirection: "column", gap: "var(--space-1)", minWidth: 180, flex: "1 1 180px" },
  labelText: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  input: {
    fontSize: "var(--font-size-sm)",
    padding: "var(--space-2) var(--space-3)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--color-surface-2)",
    color: "var(--color-text-primary)",
  },
  inputMono: { fontFamily: "var(--font-mono, monospace)" },
  optionNote: { fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", margin: 0 },
  error: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-error)",
    margin: 0,
    fontWeight: 600,
  },
  actions: { display: "flex", alignItems: "center", gap: "var(--space-4)", flexWrap: "wrap" },
  submit: {
    fontSize: "var(--font-size-sm)",
    fontWeight: 700,
    padding: "var(--space-2) var(--space-5)",
    border: "2px solid var(--color-accent)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--color-accent)",
    color: "var(--color-bg)",
    cursor: "pointer",
  },
  previewNote: { fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", margin: 0, fontStyle: "italic" },
};
