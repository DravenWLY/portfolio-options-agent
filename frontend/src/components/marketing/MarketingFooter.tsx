/**
 * MarketingFooter — small wordmark + version + disclaimer footer used at the
 * bottom of Landing/Pricing/Auth placeholder screens.
 *
 * Translated from the `<footer>` block in
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/landing.tsx
 *
 * Safety: disclaimer copy explicitly negates broker / advice / order-placement
 * framing. No external links. No analytics. No tokens.
 */
export default function MarketingFooter() {
  return (
    <footer style={styles.foot}>
      <div style={styles.row}>
        <div style={styles.left}>
          <BrandMark size={20} />
          <span className="mp-display" style={styles.wordmark}>Portfolio Copilot</span>
          <span aria-hidden="true" style={styles.sep}>·</span>
          <span style={styles.version}>v0.7.3-alpha · 2026</span>
        </div>
        <p style={styles.disclaim}>
          Portfolio Copilot is an analysis tool, not a broker. It is not
          investment advice. All trades are placed manually by you in your
          own broker.
        </p>
      </div>
    </footer>
  );
}

function BrandMark({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={{ color: "var(--mp-accent)", flexShrink: 0 }} aria-hidden="true">
      <rect x="0.5" y="0.5" width="23" height="23" rx="3" fill="none" stroke="currentColor" strokeWidth="1.2" />
      <path d="M5 16L9 10L13 13L19 6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="9" cy="10" r="1.2" fill="currentColor" />
      <circle cx="13" cy="13" r="1.2" fill="currentColor" />
      <circle cx="19" cy="6" r="1.2" fill="currentColor" />
    </svg>
  );
}

const styles: Record<string, React.CSSProperties> = {
  foot: {
    borderTop: "1px solid var(--mp-rule)",
    backgroundColor: "var(--mp-paper-2)",
    padding: "var(--space-5) var(--space-6)",
    marginTop: "var(--space-6)",
  },
  row: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "var(--space-4)",
    flexWrap: "wrap",
  },
  left: { display: "flex", alignItems: "center", gap: "var(--space-3)" },
  wordmark: { fontSize: "var(--font-size-md)", color: "var(--mp-ink)", fontWeight: 500 },
  sep: { color: "var(--mp-rule-strong)" },
  version: { fontFamily: "var(--mp-font-mono)", fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  disclaim: {
    margin: 0,
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    lineHeight: 1.6,
    maxWidth: 560,
    textAlign: "right",
  },
};
