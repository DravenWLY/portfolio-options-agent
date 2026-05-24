import { useState } from "react";
import { DemoChip, SafetyStrip } from "../components/shared/mp";
import { SectionH, MarketingFooter } from "../components/marketing";

type BillingPeriod = "monthly" | "annual";

interface PricingTier {
  key: string;
  name: string;
  blurb: string;
  price: Record<BillingPeriod, string>;
  priceSub?: Record<BillingPeriod, string>;
  caveat: string;
  cta: { label: string; tone: "live" | "accent" | "stale"; disabled?: boolean };
  featured: boolean;
  features: Array<readonly [string, string | boolean]>;
}

/**
 * PricingPage — P20A-T4 marketing placeholder.
 *
 * Translated (not pasted) from
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/pricing.tsx
 *
 * Safety:
 *   - Illustrative pricing tiers only. No checkout, no payment integration,
 *     no external links. CTAs are no-op buttons (disabled for inactive
 *     tiers; informative-only for the waitlist tier).
 *   - "Every tier is analysis-only" belt is rendered verbatim from the
 *     prototype's safety positioning.
 *   - No advice / outcome-guarantee / signal-feed wording.
 */
export default function PricingPage() {
  const [billing, setBilling] = useState<BillingPeriod>("monthly");

  return (
    <div className="mp-surface" style={styles.page}>
      {/* Header */}
      <section style={styles.header}>
        <div style={styles.inner}>
          <div style={styles.headerContent}>
            <div style={styles.eyebrow}>Pricing · 2026 alpha</div>
            <h1 className="mp-display" style={styles.h1}>
              One tier active.<br />
              <span style={styles.h1Accent}>Two more</span> on the way.
            </h1>
            <p style={styles.lede}>
              Portfolio Copilot is in private alpha. Pricing is shown honestly:
              what's available now, what is illustrative for beta, and what is
              still scoped on a roadmap. All amounts here are placeholders — no
              payment integration is wired and no checkout exists.
            </p>

            <div role="tablist" aria-label="Billing period" style={styles.toggleWrap}>
              {(["monthly", "annual"] as const).map((b) => {
                const active = billing === b;
                return (
                  <button
                    key={b}
                    type="button"
                    role="tab"
                    aria-selected={active}
                    onClick={() => setBilling(b)}
                    style={{
                      ...styles.toggleBtn,
                      backgroundColor: active ? "var(--mp-ink)" : "transparent",
                      color: active ? "var(--mp-card)" : "var(--mp-mute)",
                    }}
                  >
                    {b === "monthly" ? "Monthly" : "Annual"}
                    {b === "annual" && <span style={{ marginLeft: 8, fontSize: 10, opacity: 0.75 }}>save 2 mo</span>}
                  </button>
                );
              })}
            </div>
            <div style={{ marginTop: "var(--space-3)" }}><DemoChip /></div>
          </div>
        </div>
      </section>

      {/* Tiers */}
      <section style={styles.section}>
        <div style={styles.inner}>
          <div style={styles.tierGrid}>
            {TIERS.map((t) => (
              <div
                key={t.key}
                style={{
                  ...styles.tierCard,
                  borderColor: t.featured ? "var(--mp-ink)" : "var(--mp-rule)",
                  borderWidth: t.featured ? 1.5 : 1,
                  boxShadow: t.featured ? "0 4px 24px rgba(0,0,0,0.08)" : undefined,
                }}
              >
                {t.featured && (
                  <div style={styles.tierFlag}>Illustrative · recommended for beta</div>
                )}

                <div style={styles.tierEyebrow}>{t.key}</div>
                <h3 className="mp-display" style={styles.tierName}>{t.name}</h3>
                <p style={styles.tierBlurb}>{t.blurb}</p>

                <div style={styles.tierPriceRow}>
                  <span className="mp-display" style={styles.tierPrice}>{t.price[billing]}</span>
                  {t.priceSub && <span style={styles.tierPriceSub}>{t.priceSub[billing]}</span>}
                </div>
                <p style={styles.tierCaveat}>{t.caveat}</p>

                <button
                  type="button"
                  disabled={t.cta.disabled || t.cta.tone !== "live"}
                  aria-disabled={t.cta.disabled || t.cta.tone !== "live"}
                  title={
                    t.cta.tone === "live"
                      ? "Active during private alpha"
                      : "Not yet active — illustrative pricing only"
                  }
                  onClick={(e) => e.preventDefault()}
                  style={{
                    ...styles.tierCta,
                    ...(t.cta.tone === "accent"
                      ? { backgroundColor: "var(--mp-accent)", color: "var(--mp-card)", borderColor: "var(--mp-accent)" }
                      : t.cta.tone === "live"
                      ? { backgroundColor: "var(--mp-live-soft)", color: "var(--mp-live)", borderColor: "var(--mp-live)" }
                      : { backgroundColor: "transparent", color: "var(--mp-mute)", borderColor: "var(--mp-rule-strong)" }),
                    opacity: t.cta.tone !== "live" ? 0.85 : 1,
                    cursor: t.cta.tone === "live" ? "default" : "not-allowed",
                  }}
                >
                  {t.cta.label}
                </button>

                <div style={styles.tierDivider} />

                <ul style={styles.featureList}>
                  {t.features.map(([k, v]) => (
                    <li key={k} style={styles.featureRow}>
                      <span style={styles.featureKey}>{k}</span>
                      <span style={styles.featureVal}>
                        {v === true && <span style={{ color: "var(--mp-live)", fontSize: 14 }} aria-label="included">✓</span>}
                        {v === false && <span style={{ color: "var(--mp-mute-2)", fontSize: 14 }} aria-label="not included">—</span>}
                        {typeof v === "string" && (
                          <span style={{ fontFamily: "var(--mp-font-mono)", fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)" }}>{v}</span>
                        )}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Safety belt */}
      <section style={styles.beltOuter}>
        <div style={styles.inner}>
          <div style={styles.beltInner}>
            <div style={styles.beltGlyph} aria-hidden="true">◇</div>
            <div style={{ minWidth: 0 }}>
              <h3 className="mp-display" style={styles.beltTitle}>Every tier is analysis-only.</h3>
              <p style={styles.beltBody}>
                No tier of Portfolio Copilot places trades, sends orders, or
                makes recommendations. Higher tiers expand the breadth and
                depth of review — not the kind of action the product takes.
                Your broker is and remains the only place orders happen.
              </p>
              <div style={{ marginTop: "var(--space-2)" }}>
                <SafetyStrip items={[
                  "Analysis only",
                  "Manual review",
                  "No order placement",
                  "No payment integration on this page",
                ]} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison table */}
      <section style={styles.section}>
        <div style={styles.inner}>
          <SectionH
            num="—"
            kicker="Compare in detail"
            title="A full side-by-side, with the awkward bits visible."
          />
          <div style={styles.tableCard}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={{ ...styles.th, width: "32%" }}>Capability</th>
                  <th style={styles.th}>Personal Preview</th>
                  <th style={styles.th}>Active Investor</th>
                  <th style={styles.th}>Pro / Advisor Preview</th>
                </tr>
              </thead>
              <tbody>
                {COMPARISON.map((row) => (
                  <tr key={row[0]}>
                    <td style={{ ...styles.td, color: "var(--mp-mute)" }}>{row[0]}</td>
                    {row.slice(1).map((c, i) => (
                      <td key={i} style={{ ...styles.td, fontFamily: "var(--mp-font-mono)", fontSize: "var(--font-size-xs)" }}>{c}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={styles.tableFoot}>
            Pricing is private-alpha placeholder material and may change before
            general availability. No tier promises returns, signals, or
            recommendations. No price shown here will result in a charge — there
            is no checkout integration.
          </p>
        </div>
      </section>

      <MarketingFooter />
    </div>
  );
}

/* ---------------- Static content ---------------- */

const TIERS: PricingTier[] = [
  {
    key: "preview",
    name: "Personal Preview",
    blurb: "Founder / private alpha — single connected user.",
    price: { monthly: "Free", annual: "Free" },
    caveat: "Active during alpha · one SnapTrade-connected user only.",
    cta: { label: "Current tier", tone: "live", disabled: true },
    featured: false,
    features: [
      ["Connected brokers",      "1 user, read-only via SnapTrade"],
      ["Trade reviews / month",  "Unlimited (rate-limited)"],
      ["Agent team analysis",    "Mock provider only"],
      ["Saved reports",          "Last 50"],
      ["CSV positions fallback", true],
      ["Email export",           false],
      ["Multi-portfolio review", false],
      ["Priority support",       false],
    ],
  },
  {
    key: "active",
    name: "Active Investor",
    blurb: "For self-directed investors who review trades manually, often.",
    price: { monthly: "$24", annual: "$240" },
    priceSub: { monthly: "per month · illustrative", annual: "per year · illustrative · save 2 months" },
    caveat: "Illustrative tier — invitation-based during alpha. No checkout integration on this page.",
    cta: { label: "Join waitlist (not yet active)", tone: "accent", disabled: true },
    featured: true,
    features: [
      ["Connected brokers",      "Up to 3, read-only"],
      ["Trade reviews / month",  "Unlimited"],
      ["Agent team analysis",    "Real provider · 5 roles · full evidence"],
      ["Saved reports",          "Unlimited · 18 mo retention"],
      ["CSV positions fallback", true],
      ["Email export",           "Markdown · PDF"],
      ["Multi-portfolio review", false],
      ["Priority support",       "48h response"],
    ],
  },
  {
    key: "pro",
    name: "Pro / Advisor Preview",
    blurb: "Future tier — multi-portfolio review and exportable diligence.",
    price: { monthly: "TBD", annual: "TBD" },
    priceSub: { monthly: "not yet available", annual: "not yet available" },
    caveat: "Roadmap tier · pricing and scope are not finalized. No commitment implied.",
    cta: { label: "Coming soon", tone: "stale", disabled: true },
    featured: false,
    features: [
      ["Connected brokers",      "Up to 10, read-only"],
      ["Trade reviews / month",  "Unlimited"],
      ["Agent team analysis",    "Real provider + custom role weights"],
      ["Saved reports",          "Unlimited · 5 yr retention"],
      ["CSV positions fallback", true],
      ["Email export",           "Markdown · PDF · JSON"],
      ["Multi-portfolio review", "Cross-account synthesis"],
      ["Priority support",       "Same-day · video review"],
    ],
  },
];

const COMPARISON: ReadonlyArray<readonly string[]> = [
  ["Broker connection (read-only)",      "1 user",                       "Up to 3",                      "Up to 10"],
  ["Stock & ETF buy review",             "✓",                            "✓",                            "✓"],
  ["Stock & ETF sell / trim review",     "✓",                            "✓",                            "✓"],
  ["Covered call review",                "✓ (partial coverage netting)", "✓ (full coverage netting)",    "✓ (full + scenario branches)"],
  ["Cash-secured put review",            "✓ (generic rule)",             "✓ (broker-aware collateral)",  "✓ (broker-aware + multi-leg)"],
  ["Agent team analysis",                "Mock provider",                 "Real provider · 5 roles",     "Real provider + custom role weights"],
  ["Report retention",                   "50 most recent",                "Unlimited · 18 mo",           "Unlimited · 5 yr"],
  ["Email / PDF export",                 "—",                             "Markdown · PDF",              "Markdown · PDF · JSON"],
  ["Multi-portfolio synthesis",          "—",                             "—",                            "Cross-account review"],
  ["Order placement / execution",        "Never",                         "Never",                        "Never"],
];

/* ---------------- Styles ---------------- */

/** Shared inner container — constrains content to the prototype's editorial desk width. */
const INNER: React.CSSProperties = {
  maxWidth: 1120,
  width: "100%",
  margin: "0 auto",
  minWidth: 0,
};

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex", flexDirection: "column", color: "var(--mp-ink)",
    marginInline: "calc(-1 * var(--space-8))",
    marginTop: "calc(-1 * var(--space-8))",
    marginBottom: "calc(-1 * var(--space-8))",
  },

  inner: INNER,

  header: {
    padding: "60px 64px 32px",
    borderBottom: "1px solid var(--mp-rule)",
  },
  headerContent: {
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    alignItems: "center",
  },
  eyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.10em", fontWeight: 600 },
  h1: { fontSize: "clamp(40px, 5.5vw, 64px)", fontWeight: 500, letterSpacing: "-0.02em", lineHeight: 1.1, color: "var(--mp-ink)", margin: 0 },
  h1Accent: { color: "var(--mp-accent)", fontStyle: "italic", fontWeight: 400 },
  lede: { fontSize: 17, color: "var(--mp-ink-2)", maxWidth: 640, lineHeight: 1.6, margin: 0 },

  toggleWrap: {
    display: "inline-flex", marginTop: "var(--space-3)",
    padding: 4, backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule-strong)", borderRadius: 999,
  },
  toggleBtn: {
    padding: "8px 22px", borderRadius: 999, fontSize: "var(--font-size-xs)",
    fontWeight: 500, border: "none", cursor: "pointer",
  },

  section: { padding: "56px 64px", display: "flex", flexDirection: "column", gap: "var(--space-4)" },

  tierGrid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 },
  tierCard: {
    backgroundColor: "var(--mp-card)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)", padding: 28,
    display: "flex", flexDirection: "column", gap: "var(--space-2)",
    position: "relative", minWidth: 0,
  },
  tierFlag: {
    position: "absolute", top: -10, left: 28,
    padding: "2px 10px", backgroundColor: "var(--mp-ink)", color: "var(--mp-card)",
    fontFamily: "var(--mp-font-mono)", fontSize: 10, letterSpacing: "0.12em",
    textTransform: "uppercase", borderRadius: 2,
  },
  tierEyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 },
  tierName: { fontSize: 22, fontWeight: 500, letterSpacing: "-0.01em", color: "var(--mp-ink)", margin: 0 },
  tierBlurb: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", lineHeight: 1.5, margin: 0 },

  tierPriceRow: { display: "flex", alignItems: "baseline", gap: "var(--space-2)", marginTop: "var(--space-2)" },
  tierPrice: { fontSize: 44, letterSpacing: "-0.02em", color: "var(--mp-ink)", fontWeight: 500, lineHeight: 1 },
  tierPriceSub: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  tierCaveat: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.5, margin: 0, minHeight: 32 },

  tierCta: {
    width: "100%", padding: "10px 16px",
    fontSize: "var(--font-size-sm)", fontWeight: 600,
    border: "1px solid", borderRadius: "var(--radius-sm)",
    textAlign: "center" as const,
  },
  tierDivider: { height: 1, backgroundColor: "var(--mp-rule)", margin: "var(--space-3) -28px" },

  featureList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  featureRow: { display: "grid", gridTemplateColumns: "1fr auto", gap: 10, alignItems: "center", fontSize: "var(--font-size-sm)" },
  featureKey: { color: "var(--mp-mute)" },
  featureVal: { textAlign: "right" },

  beltOuter: {
    backgroundColor: "var(--mp-paper-2)",
    padding: "40px 64px",
    borderTop: "1px solid var(--mp-rule)",
    borderBottom: "1px solid var(--mp-rule)",
  },
  beltInner: { display: "grid", gridTemplateColumns: "auto 1fr", gap: 32, alignItems: "center" },
  beltGlyph: { fontSize: 32, color: "var(--mp-accent)", lineHeight: 1 },
  beltTitle: { fontSize: 20, fontWeight: 500, color: "var(--mp-ink)", margin: 0, marginBottom: "var(--space-2)" },
  beltBody: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.6, maxWidth: 880, margin: 0 },

  tableCard: {
    backgroundColor: "var(--mp-card)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)", overflow: "hidden",
  },
  table: { width: "100%", minWidth: 640, borderCollapse: "collapse", tableLayout: "fixed" },
  th: {
    textAlign: "left", padding: "var(--space-3) var(--space-4)",
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600,
    borderBottom: "1px solid var(--mp-rule)",
  },
  td: {
    padding: "var(--space-3) var(--space-4)",
    borderBottom: "1px solid var(--mp-rule)",
    fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", verticalAlign: "top" as const,
  },
  tableFoot: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0, marginTop: "var(--space-3)", lineHeight: 1.6 },
};
