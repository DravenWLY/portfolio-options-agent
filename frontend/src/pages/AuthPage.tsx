import { useState } from "react";
import { Badge, SafetyStrip } from "../components/shared/mp";
import { MarketingFooter } from "../components/marketing";

type AuthMode = "signin" | "signup";

/**
 * AuthPage — P20A-T4 marketing placeholder.
 *
 * Translated (not pasted) from
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/screens/auth.tsx
 *
 * Safety:
 *   - No real auth flow. There is no backend client call from this page.
 *   - The submit button is a no-op: it does not call any API, does not
 *     navigate, and does not write to localStorage or sessionStorage.
 *   - Email / password inputs are uncontrolled, marked `autoComplete="off"`,
 *     and visually wrapped in a `private alpha · sign-in not yet active`
 *     banner so users understand nothing is being persisted.
 *   - "Continue with magic link" is included as a visual placeholder only —
 *     also a no-op.
 *   - No password reset wire. No social auth. No tokens. No cookies.
 */
export default function AuthPage() {
  const [mode, setMode] = useState<AuthMode>("signin");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Intentional no-op. We never call the backend, never store credentials,
    // never navigate. Show the user a clear "not yet active" acknowledgement.
    setSubmitted(true);
  }

  return (
    <div className="mp-surface" style={styles.page}>
      <section style={styles.split}>
        {/* Left — form */}
        <div style={styles.leftCol}>
          <div style={styles.formCard}>
            <div style={styles.eyebrow}>
              {mode === "signin" ? "Sign in" : "Create account"}
            </div>
            <h1 className="mp-display" style={styles.h1}>
              {mode === "signin" ? "Welcome back." : "Join the alpha."}
            </h1>
            <p style={styles.sub}>
              Portfolio Copilot is currently in private alpha. This screen is a
              visual placeholder — broker connection limits are summarized to
              the right.
            </p>

            <div role="status" aria-live="polite" style={styles.alphaBanner}>
              <Badge tone="info" dot>Private alpha · sign-in not yet active</Badge>
              <span style={styles.alphaBannerText}>
                Nothing on this page is wired to a backend. The form below
                will not submit, store, or transmit any value you type.
              </span>
            </div>

            <form onSubmit={handleSubmit} autoComplete="off" noValidate>
              <div style={styles.field}>
                <label htmlFor="auth-email" style={styles.label}>Email</label>
                <input
                  id="auth-email"
                  name="email"
                  type="email"
                  placeholder="founder@example.com"
                  autoComplete="off"
                  spellCheck={false}
                  style={styles.input}
                />
              </div>
              <div style={styles.field}>
                <label htmlFor="auth-password" style={styles.label}>
                  {mode === "signin" ? "Password" : "Create password"}
                </label>
                <input
                  id="auth-password"
                  name="password"
                  type="password"
                  placeholder="••••••••••"
                  autoComplete="new-password"
                  style={styles.input}
                />
                <p style={styles.fieldHelp}>
                  Visual placeholder · values are not stored, not transmitted,
                  and not persisted in browser storage.
                </p>
              </div>

              {mode === "signin" && (
                <div style={styles.rowBetween}>
                  <label style={styles.checkLabel}>
                    <input type="checkbox" disabled aria-disabled="true" />
                    <span>Stay signed in (not yet active)</span>
                  </label>
                  <span style={styles.linkMuted}>
                    Reset password — not yet available
                  </span>
                </div>
              )}

              {mode === "signup" && (
                <div style={styles.signupNote}>
                  <span aria-hidden="true" style={styles.signupGlyph}>ⓘ</span>
                  <span style={styles.signupNoteText}>
                    Sign-up is gated during private alpha. This screen does not
                    queue a real account; it does not transmit your input.
                  </span>
                </div>
              )}

              <button
                type="submit"
                style={styles.primaryBtn}
                aria-disabled="true"
                title="Sign-in is not yet active during private alpha."
              >
                {mode === "signin" ? "Sign in" : "Request access"}
                <span aria-hidden="true">→</span>
              </button>

              {submitted && (
                <p role="status" aria-live="polite" style={styles.submittedNote}>
                  Sign-in is not yet active during private alpha. Your input
                  was not stored or transmitted.
                </p>
              )}

              <div style={styles.hairline}>
                <span style={styles.hairlineLine} />
                <span style={styles.hairlineText}>or</span>
                <span style={styles.hairlineLine} />
              </div>

              <button
                type="button"
                style={styles.secondaryBtn}
                onClick={() => setSubmitted(true)}
                aria-disabled="true"
                title="Magic-link flow is a visual placeholder."
              >
                <span aria-hidden="true">◇</span>
                Continue with magic link (not yet active)
              </button>
            </form>

            <p style={styles.swap}>
              {mode === "signin" ? "No account yet?" : "Already have an account?"}{" "}
              <button
                type="button"
                style={styles.swapBtn}
                onClick={() => {
                  setMode(mode === "signin" ? "signup" : "signin");
                  setSubmitted(false);
                }}
              >
                {mode === "signin" ? "Request access" : "Sign in"}
              </button>
            </p>
          </div>
        </div>

        {/* Right — alpha context */}
        <aside style={styles.rightCol} aria-label="Private alpha details">
          <div>
            <div style={styles.eyebrow}>Private alpha · what to expect</div>
            <h2 className="mp-display" style={styles.rightTitle}>
              Honest constraints while we test this carefully.
            </h2>

            <ul style={styles.contextList}>
              {CONTEXT.map((c, i) => (
                <li key={c.h} style={styles.contextItem}>
                  <span style={styles.contextNum}>{String(i + 1).padStart(2, "0")}</span>
                  <div>
                    <h4 style={styles.contextH}>{c.h}</h4>
                    <p style={styles.contextB}>{c.b}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div style={styles.rightFoot}>
            <SafetyStrip items={[
              "Read-only",
              "Analysis-only",
              "No execution controls",
              "No credential capture",
            ]} />
            <p style={styles.disclaim}>
              Portfolio Copilot is an analysis tool, not a broker. It is not
              investment advice and does not guarantee any outcome. No values
              you type on this page are stored or transmitted.
            </p>
          </div>
        </aside>
      </section>

      <MarketingFooter />
    </div>
  );
}

const CONTEXT: Array<{ h: string; b: string }> = [
  {
    h: "One connected broker user, for now",
    b: "Our SnapTrade plan supports a single connected user during private alpha. The session preserves that connection until we expand.",
  },
  {
    h: "Reviews stay scoped",
    b: "Reviewing stock/ETF buy or sell-trim, covered calls, and cash-secured puts. Complex multi-leg strategies arrive later.",
  },
  {
    h: "Live LLM behind a feature flag",
    b: "By default agent analyses run on a mock provider. Real provider calls are toggled per-account by the operator.",
  },
  {
    h: "Nothing executes from this app",
    b: "There is no order ticket, no buy, no sell, no submit, no cancel — by design. You always act in your broker.",
  },
];

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex", flexDirection: "column", color: "var(--mp-ink)",
    marginInline: "calc(-1 * var(--space-8))",
    marginTop: "calc(-1 * var(--space-8))",
    marginBottom: "calc(-1 * var(--space-8))",
  },

  split: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    minHeight: "calc(100vh - var(--topbar-height))",
  },

  leftCol: { padding: "0 64px", display: "flex", alignItems: "center", justifyContent: "center", minWidth: 0 },
  formCard: { width: "100%", maxWidth: 420, display: "flex", flexDirection: "column", gap: 14 },

  eyebrow: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", textTransform: "uppercase", letterSpacing: "0.10em", fontWeight: 600 },
  h1: { fontSize: "clamp(32px, 4.2vw, 48px)", fontWeight: 500, letterSpacing: "-0.02em", lineHeight: 1.1, color: "var(--mp-ink)", margin: 0 },
  sub: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", lineHeight: 1.6, margin: 0 },

  alphaBanner: {
    display: "flex", alignItems: "flex-start", gap: "var(--space-2)",
    flexWrap: "wrap",
    padding: "var(--space-3)",
    backgroundColor: "var(--mp-info-soft)",
    border: "1px solid var(--mp-info)",
    borderRadius: "var(--radius-sm)",
    marginTop: "var(--space-2)",
  },
  alphaBannerText: { fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)", lineHeight: 1.5, flex: 1, minWidth: 200 },

  field: { display: "flex", flexDirection: "column", gap: 6, marginTop: "var(--space-3)" },
  label: { fontSize: 10.5, color: "var(--mp-mute)", fontFamily: "var(--mp-font-mono)", fontWeight: 500, letterSpacing: "0.12em", textTransform: "uppercase", display: "block", marginBottom: 6 },
  input: {
    appearance: "none",
    display: "block",
    width: "100%",
    height: 36,
    padding: "0 12px",
    fontSize: 13,
    color: "var(--mp-ink)",
    backgroundColor: "var(--mp-paper-2)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    outline: "none",
    fontFamily: "var(--mp-font-mono)",
    letterSpacing: 0,
  },
  fieldHelp: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", margin: 0, lineHeight: 1.4 },

  rowBetween: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap", marginTop: "var(--space-3)" },
  checkLabel: { display: "flex", alignItems: "center", gap: 8, fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  linkMuted: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },

  signupNote: {
    marginTop: "var(--space-3)",
    padding: "var(--space-3)",
    backgroundColor: "var(--mp-paper-2)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    display: "flex",
    gap: 10,
    alignItems: "flex-start",
  },
  signupGlyph: { color: "var(--mp-info)", fontSize: 16, lineHeight: 1, marginTop: 2 },
  signupNoteText: { fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)", lineHeight: 1.5 },

  primaryBtn: {
    marginTop: "var(--space-4)",
    width: "100%", justifyContent: "center",
    fontSize: "var(--font-size-sm)", fontWeight: 600, padding: "12px 18px",
    backgroundColor: "var(--mp-accent)", color: "var(--mp-card)",
    border: "1px solid var(--mp-accent)", borderRadius: "var(--radius-sm)",
    cursor: "not-allowed",
    display: "inline-flex", alignItems: "center", gap: 8,
    opacity: 0.92,
  },
  submittedNote: { fontSize: "var(--font-size-xs)", color: "var(--mp-stale)", marginTop: "var(--space-2)", lineHeight: 1.5 },

  hairline: { display: "flex", alignItems: "center", gap: 12, margin: "24px 0", color: "var(--mp-mute)" },
  hairlineLine: { flex: 1, height: 1, backgroundColor: "var(--mp-rule)" },
  hairlineText: { fontSize: "var(--font-size-xs)", textTransform: "uppercase", letterSpacing: "0.12em", fontFamily: "var(--mp-font-mono)", fontWeight: 500 },

  secondaryBtn: {
    width: "100%", display: "inline-flex", justifyContent: "center", alignItems: "center", gap: 10,
    padding: "10px 16px",
    fontSize: "var(--font-size-sm)", fontWeight: 600,
    backgroundColor: "var(--mp-card)", color: "var(--mp-ink-2)",
    border: "1px solid var(--mp-rule-strong)", borderRadius: "var(--radius-sm)",
    cursor: "not-allowed", opacity: 0.92,
  },

  swap: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", marginTop: "var(--space-5)", textAlign: "center" },
  swapBtn: {
    background: "transparent", border: "none", padding: 0, cursor: "pointer",
    color: "var(--mp-accent)", fontWeight: 600, fontSize: "var(--font-size-xs)",
    textDecoration: "underline",
  },

  rightCol: {
    backgroundColor: "var(--mp-paper-2)",
    padding: "60px 64px",
    borderLeft: "1px solid var(--mp-rule)",
    display: "flex", flexDirection: "column", justifyContent: "space-between", gap: 32,
    minWidth: 0,
  },
  rightTitle: { fontSize: "clamp(22px, 3vw, 28px)", fontWeight: 500, letterSpacing: "-0.01em", color: "var(--mp-ink)", margin: 0, marginTop: 14, marginBottom: 20, lineHeight: 1.2 },

  contextList: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 18 },
  contextItem: { display: "grid", gridTemplateColumns: "32px 1fr", gap: 14, minWidth: 0 },
  contextNum: { fontFamily: "var(--mp-font-mono)", fontSize: "var(--font-size-xs)", color: "var(--mp-accent)", paddingTop: 3 },
  contextH: { fontSize: "var(--font-size-sm)", fontWeight: 500, color: "var(--mp-ink)", margin: 0, marginBottom: 4 },
  contextB: { fontSize: "var(--font-size-sm)", color: "var(--mp-mute)", lineHeight: 1.6, margin: 0 },

  rightFoot: { display: "flex", flexDirection: "column", gap: "var(--space-2)", marginTop: 40 },
  disclaim: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", lineHeight: 1.6, margin: 0, marginTop: "var(--space-3)" },
};
