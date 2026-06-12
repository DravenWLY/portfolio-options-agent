import { useUIPreference } from "../../context/useUIPreference";
import type { AppearanceMode } from "../../context/uiPreferenceContextDef";

/**
 * AppearanceControl — segmented System / Light / Dark selector.
 *
 * "System" follows prefers-color-scheme; Light/Dark explicitly override it.
 * No trade, market-price, or guaranteed-return language anywhere here.
 */
const OPTIONS: { mode: AppearanceMode; label: string; icon: string }[] = [
  { mode: "system", label: "System", icon: "◐" },
  { mode: "light", label: "Light", icon: "☀" },
  { mode: "dark", label: "Dark", icon: "☾" },
];

export default function AppearanceControl({ compact = false }: { compact?: boolean }) {
  const { appearance, setAppearance } = useUIPreference();

  return (
    <div style={{ ...styles.group, ...(compact ? styles.groupCompact : {}) }} role="group" aria-label="Appearance">
      {OPTIONS.map(({ mode, label, icon }) => {
        const active = appearance === mode;
        return (
          <button
            key={mode}
            type="button"
            onClick={() => setAppearance(mode)}
            aria-pressed={active}
            title={`Appearance: ${label}`}
            style={{ ...styles.btn, ...(compact ? styles.btnCompact : {}), ...(active ? styles.btnActive : {}) }}
          >
            <span aria-hidden="true" style={styles.icon}>
              {icon}
            </span>
            {!compact && <span style={styles.label}>{label}</span>}
          </button>
        );
      })}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  group: {
    display: "flex",
    alignItems: "center",
    gap: "1px",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    overflow: "hidden",
    backgroundColor: "var(--color-border-subtle)",
  },
  groupCompact: {
    flexDirection: "column",
    width: 36,
    marginInline: "auto",
  },
  btn: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-1)",
    padding: "var(--space-1) var(--space-2)",
    border: "none",
    backgroundColor: "var(--color-surface)",
    color: "var(--color-text-muted)",
    fontSize: "var(--font-size-xs)",
    fontFamily: "var(--font-family)",
    cursor: "pointer",
    letterSpacing: "0.02em",
  },
  btnCompact: {
    width: 34,
    height: 30,
    justifyContent: "center",
    padding: 0,
  },
  btnActive: {
    backgroundColor: "var(--color-accent-dim)",
    color: "var(--color-accent)",
    fontWeight: 700,
  },
  icon: {
    fontSize: "var(--font-size-sm)",
    lineHeight: 1,
  },
  label: {
    lineHeight: 1,
  },
};
