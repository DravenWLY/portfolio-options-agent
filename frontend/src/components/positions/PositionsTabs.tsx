import { useState } from "react";
import SectionCard from "../shared/SectionCard";
import CashPositionsView from "./CashPositionsView";
import StockPositionsView from "./StockPositionsView";
import OptionPositionsView from "./OptionPositionsView";

type Tab = "cash" | "stocks" | "options";

const TABS: { id: Tab; label: string }[] = [
  { id: "cash",    label: "Cash" },
  { id: "stocks",  label: "Stocks" },
  { id: "options", label: "Options" },
];

/**
 * PositionsTabs — tabbed panel containing Cash, Stock, and Option position views.
 *
 * Safety: no option chain, no screener, no trade execution, no market quote data.
 */
export default function PositionsTabs() {
  const [active, setActive] = useState<Tab>("cash");

  return (
    <SectionCard
      id="positions"
      label="Positions"
      headerRight={
        <TabBar active={active} onChange={setActive} />
      }
    >
      {active === "cash"    && <CashPositionsView />}
      {active === "stocks"  && <StockPositionsView />}
      {active === "options" && <OptionPositionsView />}
    </SectionCard>
  );
}

function TabBar({
  active,
  onChange,
}: {
  active: Tab;
  onChange: (t: Tab) => void;
}) {
  return (
    <div style={styles.tabBar} role="tablist" aria-label="Position type">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={active === tab.id}
          style={{
            ...styles.tab,
            ...(active === tab.id ? styles.tabActive : {}),
          }}
          onClick={() => onChange(tab.id)}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  tabBar: {
    display: "flex",
    gap: "var(--space-1)",
    backgroundColor: "var(--color-surface-2)",
    borderRadius: "var(--radius-sm)",
    padding: 3,
  },
  tab: {
    padding: "3px var(--space-3)",
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    backgroundColor: "transparent",
    border: "none",
    borderRadius: "var(--radius-sm)",
    cursor: "pointer",
    fontFamily: "var(--font-family)",
    transition: "background-color 100ms, color 100ms",
  },
  tabActive: {
    backgroundColor: "var(--color-surface)",
    color: "var(--color-text-primary)",
    fontWeight: 600,
    boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
  },
};
