import { useNavigate } from "react-router-dom";
import { Badge, DemoChip, MpIcon, Pill, SafetyStrip } from "../components/shared/mp";
import { SectionH, MarketingFooter } from "../components/marketing";

/**
 * LandingPage — P20A-T4 marketing placeholder.
 *
 * Translated (not pasted) from
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/landing.tsx
 *
 * Safety:
 *   - Analysis-only positioning throughout. No execution-action, automated-
 *     execution, signal-feed, stock-picking, or outcome-guarantee language.
 *   - CTAs navigate inside this app only; no external submission, no
 *     payment integration, no auth side-effects.
 *   - Static placeholder data — every preview card carries an explicit
 *     `demo · not yet connected` chip.
 */
export default function LandingPage() {
  const nav = useNavigate();
  return (
    <div className="mp-surface" style={styles.page}>
      {/* Hero */}
      <section style={styles.hero}>
        <div style={styles.inner}>
          <div style={styles.heroGrid}>
            <div style={styles.heroLeft}>
              <div style={styles.heroEyebrowRow}>
                <span style={styles.alphaTag}>v0.7 · Private alpha</span>
                <span style={styles.heroEyebrowText}>
                  For self-directed investors · Read-only · Analysis-only
                </span>
              </div>
              <h1 className="mp-display" style={styles.heroTitle}>
                A second pair of eyes,<br />
                <span style={styles.heroAccent}>before</span> you place the trade yourself.
              </h1>
              <p style={styles.heroSub}>
                Portfolio Copilot reviews stock, ETF, and options trades against your
                portfolio before you place them manually in your broker. It reads
                connected broker accounts read-only, runs deterministic risk checks,
                and lets a small team of analyst agents debate the proposal — so you
                understand exactly what hits your portfolio when you act outside the app.
              </p>
              <div style={styles.heroCtas}>
                <button type="button" style={styles.primaryBtn} onClick={() => nav("/trade-review")}>
                  Open trade review <span aria-hidden="true">→</span>
                </button>
                <button type="button" style={styles.ghostBtn} onClick={() => nav("/pricing")}>
                  View pricing
                </button>
              </div>
              <SafetyStrip items={[
                "Read-only broker sync",
                "No order placement",
                "No execution buttons",
                "Deterministic facts + agent commentary, kept separate",
              ]} />
            </div>

            {/* Hero preview pane — static screenshot-style mock */}
            <div style={styles.heroRight}>
              <div style={styles.previewCard}>
                <div style={styles.previewChrome}>
                  <div style={styles.previewDots}>
                    <span style={styles.previewDot} />
                    <span style={styles.previewDot} />
                    <span style={styles.previewDot} />
                  </div>
                  <span style={styles.previewUrl}>portfoliocopilot.app/review/r_demo_xyz</span>
                </div>
                <HeroPreview />
              </div>
              <div style={styles.previewBadge}>
                <Badge tone="info" dot>Static preview</Badge>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Numbers strip */}
      <section style={styles.numbersStrip}>
        <div style={styles.inner}>
          <div style={styles.numbersGrid}>
            {NUMBERS.map((n, i) => (
              <div key={n.label} style={styles.numCell}>
                <span style={styles.numEyebrow}>{n.label}</span>
                <span style={{ ...styles.giantNum, color: i === 3 ? "var(--mp-accent)" : "var(--mp-ink)" }}>{n.value}</span>
                <span style={styles.numSub}>{n.sub}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section style={styles.section}>
        <div style={styles.inner}>
          <SectionH
            num="01 —"
            kicker="How it works"
            title="From a proposed trade to a portfolio-aware verdict — in a few minutes."
          />
          <div style={styles.howGrid}>
            {HOW_STEPS.map((s) => (
              <div key={s.n} style={styles.howStep}>
                <div style={styles.howNum}>{s.n}</div>
                <h3 className="mp-display" style={styles.howTitle}>{s.t}</h3>
                <p style={styles.howBody}>{s.b}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <hr style={styles.rule} />

      {/* Core features */}
      <section style={styles.section}>
        <div style={styles.inner}>
          <SectionH
            num="02 —"
            kicker="Core features"
            title="What Portfolio Copilot tells you, exactly."
          />
          <div style={styles.featureGrid}>
            {FEATURES.map((f, i) => (
              <div
                key={f.t}
                style={{
                  ...styles.featureCell,
                  borderRight: i % 4 !== 3 ? "1px solid var(--mp-rule)" : "none",
                  borderBottom: i < 4 ? "1px solid var(--mp-rule)" : "none",
                }}
              >
                <div style={styles.featureIcon} aria-hidden="true">{f.icon}</div>
                <h4 className="mp-display" style={styles.featureTitle}>{f.t}</h4>
                <p style={styles.featureBody}>{f.b}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <hr style={styles.rule} />

      {/* Supported reviews */}
      <section style={styles.section}>
        <div style={styles.inner}>
          <SectionH
            num="03 —"
            kicker="Supported trade reviews"
            title="Four flows. Each with its own check sheet."
          />
          <div style={styles.flowsGrid}>
            {FLOWS.map((f) => (
              <div key={f.t} style={styles.flowCard}>
                <Pill tone="accent">{f.tag}</Pill>
                <h3 className="mp-display" style={styles.flowTitle}>{f.t}</h3>
                <ul style={styles.flowList}>
                  {f.checks.map((c) => (
                    <li key={c} style={styles.flowItem}>
                      <span aria-hidden="true" style={styles.flowBullet}>·</span>
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      <hr style={styles.rule} />

      {/* Safety positioning */}
      <section style={styles.safetyOuter}>
        <div style={styles.inner}>
          <SectionH
            num="04 —"
            kicker="Safety & positioning"
            title="What this product is — and what it deliberately is not."
          />
          <div style={styles.safetyGrid}>
            <div style={styles.safetyCard}>
              <div style={{ ...styles.safetyHead, color: "var(--mp-live)" }}><MpIcon name="check" size={12} style={{ verticalAlign: "middle", marginRight: 4 }} /> Is</div>
              {SAFETY_IS.map(([h, b]) => (
                <div key={h} style={styles.safetyItem}>
                  <h4 style={styles.safetyItemTitle}>{h}</h4>
                  <p style={styles.safetyItemBody}>{b}</p>
                </div>
              ))}
              <div style={styles.safetyTail}>
                · read-only broker integration · CSV fallback · per-review reproducible report
              </div>
            </div>
            <div style={styles.safetyCard}>
              <div style={{ ...styles.safetyHead, color: "var(--mp-block)" }}><MpIcon name="x" size={12} style={{ verticalAlign: "middle", marginRight: 4 }} /> Is not</div>
              {SAFETY_ISNT.map(([h, b]) => (
                <div key={h} style={styles.safetyItem}>
                  <h4 style={styles.safetyItemTitle}>{h}</h4>
                  <p style={styles.safetyItemBody}>{b}</p>
                </div>
              ))}
              <div style={styles.safetyTail}>
                · no execution · no recommendations · no return guarantees
              </div>
            </div>
          </div>
        </div>
      </section>

      <hr style={styles.rule} />

      {/* Pricing preview */}
      <section style={styles.section}>
        <div style={styles.inner}>
          <SectionH
            num="05 —"
            kicker="Pricing preview"
            title="Honest tiers — including one that doesn't exist yet."
            right={
              <button type="button" style={styles.ghostBtnSm} onClick={() => nav("/pricing")}>
                See full pricing <span aria-hidden="true">→</span>
              </button>
            }
          />
          <div style={styles.priceMiniGrid}>
            {PRICING_PREVIEW.map((p) => (
              <div
                key={p.t}
                style={{
                  ...styles.priceMiniCard,
                  borderColor: p.featured ? "var(--mp-ink)" : "var(--mp-rule)",
                }}
              >
                <div style={styles.priceMiniHead}>
                  <span style={styles.priceMiniEyebrow}>{p.t}</span>
                  <Badge tone={p.tone} dot>{p.cta}</Badge>
                </div>
                <div className="mp-display" style={styles.priceMiniNum}>{p.p}</div>
                <p style={styles.priceMiniSub}>{p.sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <hr style={styles.rule} />

      {/* FAQ */}
      <section style={styles.section}>
        <div style={styles.inner}>
          <SectionH
            num="06 —"
            kicker="Frequently asked"
            title="Direct answers, in plain English."
          />
          <div style={styles.faqGrid}>
            {FAQ.map((f, i) => (
              <div
                key={f.q}
                style={{
                  ...styles.faqItem,
                  borderRight: i % 2 === 0 ? "1px solid var(--mp-rule)" : undefined,
                  paddingRight: i % 2 === 0 ? "var(--space-5)" : 0,
                  paddingLeft: i % 2 === 1 ? "var(--space-5)" : 0,
                }}
              >
                <div style={styles.faqQ}>Q{String(i + 1).padStart(2, "0")}</div>
                <h4 className="mp-display" style={styles.faqTitle}>{f.q}</h4>
                <p style={styles.faqBody}>{f.a}</p>
              </div>
            ))}
          </div>

          <div style={styles.endCta}>
            <div style={styles.endEyebrow}>Ready when you are</div>
            <h2 className="mp-display" style={styles.endTitle}>Set up a review in under a minute.</h2>
            <button type="button" style={styles.primaryBtn} onClick={() => nav("/trade-review")}>
              Open the workspace <span aria-hidden="true">→</span>
            </button>
            <div style={{ marginTop: "var(--space-4)" }}><DemoChip /></div>
          </div>
        </div>
      </section>

      <MarketingFooter />
    </div>
  );
}

/* ---------------- Hero preview ---------------- */

function HeroPreview() {
  return (
    <div style={previewStyles.body}>
      <div style={previewStyles.head}>
        <div>
          <div style={previewStyles.eyebrow}>Trade Review · in progress</div>
          <div className="mp-display" style={previewStyles.headTitle}>
            Covered call · XYZ · 2026-06-19 / 460C × 2
          </div>
        </div>
        <Badge tone="stale" dot>Manual confirmation</Badge>
      </div>

      <div style={previewStyles.metrics}>
        {[
          { k: "Coverage", v: "200 / 200", sub: "shares · fully covered", tone: "live" as const },
          { k: "Call-away", v: "−$92.0k", sub: "at $460 strike", tone: "mute" as const },
          { k: "Premium credit", v: "+$370", sub: "est., before fees", tone: "live" as const },
        ].map((m) => (
          <div key={m.k} style={previewStyles.metric}>
            <div style={previewStyles.eyebrow}>{m.k}</div>
            <div
              style={{
                ...previewStyles.metricNum,
                color: m.tone === "live" ? "var(--mp-live)" : "var(--mp-ink)",
              }}
            >{m.v}</div>
            <div style={previewStyles.metricSub}>{m.sub}</div>
          </div>
        ))}
      </div>

      <div style={previewStyles.agents}>
        {AGENT_LINES.map((a) => (
          <div
            key={a.name}
            style={{
              ...previewStyles.agentRow,
              borderLeft: `2px solid ${a.tone === "live" ? "var(--mp-live)" : a.tone === "info" ? "var(--mp-info)" : "var(--mp-rule-strong)"}`,
            }}
          >
            <span style={previewStyles.agentName}>{a.name}</span>
            <Badge tone={a.tone} dot>{a.status}</Badge>
            <span style={previewStyles.agentExcerpt}>{a.excerpt}</span>
          </div>
        ))}
      </div>

      <div style={previewStyles.foot}>
        <span style={previewStyles.eyebrow}>Analysis only · Not an order recommendation</span>
        <span style={previewStyles.refMono}>r_demo_covered_call</span>
      </div>
      <div style={{ marginTop: "var(--space-2)" }}><DemoChip tight /></div>
    </div>
  );
}

/* ---------------- Static content ---------------- */

const NUMBERS: Array<{ label: string; value: string; sub: string }> = [
  { label: "Deterministic checks", value: "21", sub: "rule families + freshness gates" },
  { label: "Agent roles per run", value: "5", sub: "analysts → risk → portfolio manager" },
  { label: "Trade flows reviewed", value: "4", sub: "stock/ETF buy · sell/trim · CC · CSP" },
  { label: "Orders this product places", value: "0", sub: "by design · always" },
];

const HOW_STEPS: Array<{ n: string; t: string; b: string }> = [
  {
    n: "i.",
    t: "Connect your broker, read-only",
    b: "Portfolio Copilot uses SnapTrade's read-only API to pull positions, cash, and option lots. It never places, cancels, modifies, or holds any order. A CSV fallback exists for brokers that aren't supported.",
  },
  {
    n: "ii.",
    t: "Describe the trade you're considering",
    b: "Pick a flow — buy, sell/trim, covered call, cash-secured put — and enter the symbol, size, and an assumed price. Inputs validate for shape only; the backend owns the math.",
  },
  {
    n: "iii.",
    t: "Review impact, risk, and analyst opinions",
    b: "Get a deterministic impact summary (cash, collateral, concentration, exposure), explicit freshness scopes, and role-separated agent commentary — then go act in your own broker.",
  },
];

const FEATURES: Array<{ icon: React.ReactNode; t: string; b: string }> = [
  { icon: <MpIcon name="lock" size={14} />,      t: "Read-only broker sync",   b: "Pull positions, cash, and options via SnapTrade's read-only OAuth. Portfolio Copilot never sees your broker credentials." },
  { icon: <MpIcon name="spark" size={14} />,      t: "Deterministic impact",    b: "Cash + collateral, concentration delta, allocation drift, and options exposure are all computed in Python services, not the LLM." },
  { icon: <MpIcon name="clock" size={14} />,      t: "Two-scope freshness",     b: "Broker snapshot freshness and market quote freshness are tracked separately and surfaced where they matter." },
  { icon: <MpIcon name="alert" size={14} />,      t: "Risk-rule violations",    b: "Position-size, concentration, assignment burden, and other deterministic rule families. Severity is paired with icon + text — never color-only." },
  { icon: <MpIcon name="agent" size={14} />,      t: "Role-separated agents",   b: "Five agents debate the proposal in fixed order; their commentary sits next to — never replaces — the deterministic facts." },
  { icon: <MpIcon name="shield" size={14} />,     t: "Stale-data guardrails",   b: "If the broker snapshot or market quotes are stale, the workspace switches to analysis-only and flags it without alarm." },
  { icon: <MpIcon name="portfolio" size={14} />,  t: "CSV fallback",            b: "No broker, no problem — upload a positions CSV. Reviews still run, with the extra freshness caveats clearly displayed." },
  { icon: <MpIcon name="reports" size={14} />,    t: "Reproducible reports",    b: "Every review gets a stable reference, a calculation version, and a saved snapshot of inputs, evidence, and verdict." },
];

const FLOWS: Array<{ t: string; tag: string; checks: string[] }> = [
  { t: "Stock / ETF buy",          tag: "long add",     checks: ["Cash availability", "Concentration delta", "Allocation drift", "Position-size rules"] },
  { t: "Stock / ETF sell or trim", tag: "long reduce",  checks: ["Lot-level coverage hint", "Realized P&L language", "Concentration delta", "Wash-sale flag (advisory)"] },
  { t: "Covered call",             tag: "options · sto", checks: ["Stock coverage netting", "Strike vs. cost basis", "Call-away exposure", "Earnings / ex-div proximity"] },
  { t: "Cash-secured put",         tag: "options · sto", checks: ["Collateral hold", "Assignment cash burden", "Strike vs. price", "Position-size rules"] },
];

const SAFETY_IS: ReadonlyArray<readonly [string, string]> = [
  ["A review workspace", "Open it, paste a trade, get a verdict, close it. Go act in your own broker."],
  ["Read-only on your broker", "We can read positions and cash. We cannot place, cancel, modify, or hold any order."],
  ["Deterministic on the math", "Cash impact, concentration delta, exposure — all computed by deterministic Python services, not the LLM."],
  ["Explicit about freshness", "Broker snapshot freshness and market quote freshness are tracked as two separate scopes, surfaced everywhere it matters."],
];

const SAFETY_ISNT: ReadonlyArray<readonly [string, string]> = [
  ["A trading terminal", "There is no buy button. There is no sell button. There is no order ticket of any kind."],
  ["A stock-picker or signal feed", "No curated picks, no AI signals, no automated strategies, no scoreboards."],
  ["A guarantor of outcomes", "Past, present, or future. Nothing here promises a return or claims to be advice."],
  ["A replacement for your broker", "Your broker remains the source of truth and the only place you act."],
];

const PRICING_PREVIEW: Array<{
  t: string;
  p: string;
  sub: string;
  cta: string;
  tone: "live" | "info" | "stale";
  featured?: boolean;
}> = [
  { t: "Personal Preview",      p: "Free",      sub: "Founder / private alpha — single connected user.",                          cta: "Currently active", tone: "live" },
  { t: "Active Investor",       p: "$24 / mo",  sub: "Read-only broker sync · unlimited reviews · full agent team. Illustrative.", cta: "Join waitlist",    tone: "info", featured: true },
  { t: "Pro / Advisor Preview", p: "TBD",       sub: "Multi-portfolio review and exportable reports — not yet available.",         cta: "Coming soon",      tone: "stale" },
];

const FAQ: Array<{ q: string; a: string }> = [
  { q: "Does Portfolio Copilot execute anything on my behalf?", a: "No. The product is analysis-only and read-only by design. You always act in your own broker. There are no execution buttons anywhere in the product." },
  { q: "How fresh is the data?", a: "Broker snapshot freshness and market quote freshness are tracked as two separate scopes. Both are surfaced on every review with their status (live / stale / unavailable) and last-sync timestamps." },
  { q: "What does the agent team actually do?", a: "Five role-separated agents — fundamentals, news, technicals, risk, and portfolio manager — produce structured commentary on top of the deterministic facts. The deterministic Python services remain the source of truth for numbers." },
  { q: "Will my broker credentials be stored?", a: "We use SnapTrade's read-only OAuth flow. We never see, store, or transmit your broker login. You can disconnect from the broker side at any time." },
  { q: "What if my broker isn't supported?", a: "You can use the CSV fallback to upload a manual positions snapshot. The same review workspace runs on it, with extra freshness caveats clearly displayed." },
  { q: "Is this financial advice?", a: "No. Nothing in Portfolio Copilot is investment advice, a recommendation, or a forecast. It is a structured review tool. You make every decision and you act in your own broker." },
];

const AGENT_LINES: Array<{ name: string; status: string; tone: "live" | "info" | "mute"; excerpt: string }> = [
  { name: "Fundamentals", status: "complete", tone: "live", excerpt: "Demo excerpt · cleared structural checks against demo holdings." },
  { name: "News",         status: "complete", tone: "live", excerpt: "Demo excerpt · no scheduled binary events flagged in window." },
  { name: "Technicals",   status: "running",  tone: "info", excerpt: "Demo excerpt · drafting commentary on range vs. strike." },
  { name: "Risk",         status: "queued",   tone: "mute", excerpt: "Awaiting upstream roles." },
  { name: "Portfolio Mgr", status: "queued",  tone: "mute", excerpt: "Synthesis pending — will reconcile coverage and exposure." },
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
    display: "flex", flexDirection: "column", gap: 0, color: "var(--mp-ink)",
    marginInline: "calc(-1 * var(--space-8))",
    marginTop: "calc(-1 * var(--space-8))",
    marginBottom: "calc(-1 * var(--space-8))",
  },

  inner: INNER,

  hero: { padding: "60px 64px 72px", borderBottom: "1px solid var(--mp-rule)" },
  heroGrid: { display: "grid", gridTemplateColumns: "minmax(0, 1.05fr) minmax(0, 1fr)", gap: 56, alignItems: "start" },
  heroLeft: { display: "flex", flexDirection: "column", gap: 20, minWidth: 0 },
  heroEyebrowRow: { display: "flex", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap" },
  alphaTag: {
    fontSize: "var(--font-size-xs)", fontWeight: 600, letterSpacing: "0.04em",
    color: "var(--mp-accent)", backgroundColor: "var(--mp-accent-soft)",
    border: "1px solid var(--mp-accent-line)", borderRadius: "var(--radius-sm)",
    padding: "3px 8px",
  },
  heroEyebrowText: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.06em",
  },
  heroTitle: { fontSize: "clamp(40px, 5.5vw, 72px)", fontWeight: 500, lineHeight: 1.05, letterSpacing: "-0.02em", margin: 0, color: "var(--mp-ink)" },
  heroAccent: { color: "var(--mp-accent)", fontStyle: "italic", fontWeight: 400 },
  heroSub: { fontSize: 18, color: "var(--mp-ink-2)", lineHeight: 1.55, maxWidth: 560, margin: 0 },
  heroCtas: { display: "flex", gap: "var(--space-3)", flexWrap: "wrap", marginTop: 4 },
  primaryBtn: {
    fontSize: "var(--font-size-sm)", fontWeight: 600, padding: "10px 18px",
    backgroundColor: "var(--mp-accent)", color: "var(--mp-card)",
    border: "1px solid var(--mp-accent)", borderRadius: "var(--radius-sm)",
    cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 8,
  },
  ghostBtn: {
    fontSize: "var(--font-size-sm)", fontWeight: 600, padding: "10px 18px",
    backgroundColor: "transparent", color: "var(--mp-ink)",
    border: "1px solid var(--mp-rule-strong)", borderRadius: "var(--radius-sm)",
    cursor: "pointer",
  },
  ghostBtnSm: {
    fontSize: "var(--font-size-xs)", fontWeight: 600, padding: "6px 12px",
    backgroundColor: "transparent", color: "var(--mp-ink-2)",
    border: "1px solid var(--mp-rule)", borderRadius: "var(--radius-sm)",
    cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 6,
  },

  heroRight: { position: "relative", minWidth: 0 },
  previewCard: {
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)",
    overflow: "hidden",
    boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
  },
  previewChrome: {
    display: "flex", alignItems: "center", gap: 10,
    padding: "10px 14px",
    borderBottom: "1px solid var(--mp-rule)",
    backgroundColor: "var(--mp-paper-2)",
  },
  previewDots: { display: "flex", gap: 5 },
  previewDot: { width: 8, height: 8, borderRadius: 999, backgroundColor: "var(--mp-rule-strong)" },
  previewUrl: { fontFamily: "var(--mp-font-mono)", fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  previewBadge: { position: "absolute", bottom: -16, right: 12, padding: "10px 14px", backgroundColor: "var(--mp-card)", border: "1px solid var(--mp-rule)", borderRadius: "var(--radius-sm)", boxShadow: "0 4px 12px rgba(0,0,0,0.06)" },

  numbersStrip: {
    padding: "48px 64px",
    backgroundColor: "var(--mp-paper-2)",
    borderBottom: "1px solid var(--mp-rule)",
  },
  numbersGrid: {
    display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
    gap: 40,
  },
  numCell: { display: "flex", flexDirection: "column", gap: 8 },
  numEyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.10em", fontWeight: 600 },
  giantNum: { fontFamily: "var(--mp-font-display)", fontSize: "clamp(48px, 6vw, 80px)", letterSpacing: "-0.04em", lineHeight: 0.92, fontWeight: 400 },
  numSub: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.4 },

  section: { padding: "56px 64px", display: "flex", flexDirection: "column", gap: "var(--space-4)" },
  rule: { border: "none", borderTop: "1px solid var(--mp-rule)", margin: 0 },

  howGrid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24, marginTop: 8 },
  howStep: { borderLeft: "1px solid var(--mp-rule-strong)", paddingLeft: 22, display: "flex", flexDirection: "column", gap: "var(--space-2)" },
  howNum: { fontFamily: "var(--mp-font-mono)", fontSize: "var(--font-size-xs)", color: "var(--mp-accent)" },
  howTitle: { fontSize: 22, fontWeight: 500, letterSpacing: "-0.01em", color: "var(--mp-ink)", margin: 0, lineHeight: 1.2, fontFamily: "var(--mp-font-display)" },
  howBody: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.65, margin: 0 },

  featureGrid: {
    display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
    border: "1px solid var(--mp-rule)", borderRadius: "var(--radius-md)",
    overflow: "hidden", backgroundColor: "var(--mp-card)",
  },
  featureCell: { padding: 24, display: "flex", flexDirection: "column", gap: 10, minWidth: 0 },
  featureIcon: {
    width: 28, height: 28, borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-accent-soft)", color: "var(--mp-accent)",
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 14, lineHeight: 1,
  },
  featureTitle: { fontSize: 16, fontWeight: 500, letterSpacing: "-0.005em", color: "var(--mp-ink)", margin: 0, fontFamily: "var(--mp-font-display)" },
  featureBody: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", lineHeight: 1.6, margin: 0 },

  flowsGrid: { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginTop: 8 },
  flowCard: {
    backgroundColor: "var(--mp-card)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)", padding: 18,
    display: "flex", flexDirection: "column", gap: "var(--space-3)", minWidth: 0,
  },
  flowTitle: { fontSize: 18, fontWeight: 500, letterSpacing: "-0.005em", color: "var(--mp-ink)", margin: 0, fontFamily: "var(--mp-font-display)" },
  flowList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 6 },
  flowItem: { display: "flex", alignItems: "baseline", gap: 8, fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)" },
  flowBullet: { color: "var(--mp-accent)" },

  safetyOuter: { padding: "56px 64px", backgroundColor: "var(--mp-paper-2)" },
  safetyGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32, marginTop: 8 },
  safetyCard: {
    backgroundColor: "var(--mp-card)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-md)", padding: 24,
    display: "flex", flexDirection: "column",
  },
  safetyHead: {
    fontSize: "var(--font-size-xs)", textTransform: "uppercase", letterSpacing: "0.10em",
    fontWeight: 700, marginBottom: "var(--space-3)",
  },
  safetyItem: { paddingBottom: "var(--space-3)", marginBottom: "var(--space-3)", borderBottom: "1px solid var(--mp-rule)" },
  safetyItemTitle: { fontSize: "var(--font-size-sm)", fontWeight: 500, color: "var(--mp-ink)", margin: 0, marginBottom: 4 },
  safetyItemBody: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", lineHeight: 1.6, margin: 0 },
  safetyTail: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },

  priceMiniGrid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginTop: 8 },
  priceMiniCard: {
    backgroundColor: "var(--mp-card)", border: "1px solid",
    borderRadius: "var(--radius-md)", padding: 22,
    display: "flex", flexDirection: "column", gap: "var(--space-2)", minWidth: 0,
  },
  priceMiniHead: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" },
  priceMiniEyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 },
  priceMiniNum: { fontSize: 36, letterSpacing: "-0.02em", color: "var(--mp-ink)", fontWeight: 500, lineHeight: 1 },
  priceMiniSub: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", lineHeight: 1.6, margin: 0 },

  faqGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0, marginTop: 8 },
  faqItem: { padding: "20px 0", borderBottom: "1px solid var(--mp-rule)" },
  faqQ: { fontFamily: "var(--mp-font-mono)", fontSize: "var(--font-size-xs)", color: "var(--mp-accent)", marginBottom: 8 },
  faqTitle: { fontSize: 18, fontWeight: 500, color: "var(--mp-ink)", margin: 0, marginBottom: 8, letterSpacing: "-0.005em", fontFamily: "var(--mp-font-display)" },
  faqBody: { fontSize: "var(--font-size-sm)", color: "var(--mp-ink-2)", lineHeight: 1.65, margin: 0 },

  endCta: { textAlign: "center", display: "flex", flexDirection: "column", gap: 16, alignItems: "center", marginTop: 64, paddingBottom: 24 },
  endEyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.12em", fontWeight: 600 },
  endTitle: { fontSize: "clamp(32px, 4.5vw, 48px)", fontWeight: 400, letterSpacing: "-0.02em", color: "var(--mp-ink)", margin: 0, lineHeight: 1.05 },
};

const previewStyles: Record<string, React.CSSProperties> = {
  body: { padding: 20, display: "flex", flexDirection: "column", gap: "var(--space-3)" },
  head: { display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--space-3)" },
  eyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 },
  headTitle: { fontSize: 18, fontWeight: 500, color: "var(--mp-ink)", fontFamily: "var(--mp-font-display)" },
  metrics: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "var(--space-2)" },
  metric: { padding: "10px 12px", backgroundColor: "var(--mp-paper-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--mp-rule)", minWidth: 0 },
  metricNum: { fontFamily: "var(--mp-font-mono)", fontSize: 18, marginTop: 2 },
  metricSub: { fontSize: 10.5, color: "var(--mp-mute)" },
  agents: { display: "flex", flexDirection: "column", gap: 8 },
  agentRow: { display: "grid", gridTemplateColumns: "130px 90px 1fr", gap: 12, alignItems: "center", padding: "8px 10px", backgroundColor: "var(--mp-paper-2)", borderRadius: 3 },
  agentName: { fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)", fontWeight: 500 },
  agentExcerpt: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  foot: { display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "var(--space-2)", borderTop: "1px solid var(--mp-rule)" },
  refMono: { fontFamily: "var(--mp-font-mono)", fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
};
