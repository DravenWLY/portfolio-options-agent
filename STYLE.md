# Portfolio Copilot Skyframe

Status: target-state product style standard with migration guidance.
Owner: shared product/frontend design.
Applies to: the entire Portfolio Copilot app, with per-surface design docs allowed
when a feature needs deeper rules.

Portfolio Copilot Skyframe is the official visual and product style direction for
Portfolio Copilot. Use the full phrase `Portfolio Copilot Skyframe` in prompts,
frontend briefs, design reviews, and future UI tasks so agents can find this
standard quickly.

This guide does not replace `.claude/skills/frontend-design/SKILL.md` or
`.claude/skills/finance-dashboard-ux-review/SKILL.md`; it narrows Portfolio
Copilot's product style.

This document defines the target state. Existing screens may still be migrating.
When current UI conflicts with Skyframe, preserve reviewed contracts and safety
boundaries first, then move the screen toward this standard in small reviewed
slices.

## Product Posture

Portfolio Copilot is a broker-aware, portfolio-aware manual trade review
workspace for busy investors. It organizes account context, market context,
deterministic trade review, bounded Agent Team analysis, and saved reports so a
human can review decisions with better structure.

The product is not a broker dashboard clone, a trading terminal, an order-entry
system, a crypto exchange, an AI stock picker, or a learning app. It can explain
context where misunderstanding would be costly, but the core experience is an
asynchronous analyst desk.

Skyframe should feel:

- 80 percent analyst desk: calm, dense, evidence-oriented, repeatable.
- 20 percent explanatory support: concise context, optional depth, no classroom
  mood.
- Informative, elegant, interactive, and trustworthy.
- Modern and approachable for young users with limited investing knowledge.
- Read-only and manual-decision-support by default.

The central product idea:

> Portfolio Copilot is an asynchronous intelligence workspace that compresses
> market, portfolio, and expert analysis into a calm review while keeping the
> investor visibly in control.

## Audience

Design for young, busy investors who cannot watch market moves throughout market
hours and want a more value-investing-oriented review process. They may know the
basics, but they do not want a terminal, a broker power-user cockpit, or a
course. They need the app to gather evidence, separate uncertainty from facts,
and make review scope obvious without pushing them toward action.

This means:

- Prioritize scan speed and hierarchy over decoration.
- Keep repeated workflows efficient for returning users.
- Make unfamiliar context discoverable without turning every page into a guide.
- Never make the UI feel like it is urging a trade.

## Fintech References To Absorb, Not Copy

Skyframe borrows selectively from mature fintech products but must become its own
style.

- Coinbase: use the restraint, trust, clear spacing, and disciplined blue. Avoid
  becoming a Coinbase clone or feeling coldly institutional.
- Stripe: use system rigor, documentation quality, provenance, and polished
  hierarchy. Avoid purple mesh gradients and infrastructure-brand distance.
- Wise: use plain-language clarity and user empathy. Avoid payment-app simplicity
  and bright lime identity.
- Revolut: use surface polish and crisp contrast. Avoid black-card drama,
  superapp gloss, and gradient-heavy hero energy.
- Mastercard: use editorial warmth and human trust cues. Avoid beige dominance,
  consumer campaign layouts, and decorative orbital motifs.
- Kraken: use disciplined status systems and data density only where helpful.
  Avoid purple crypto-terminal identity.
- Binance: treat as an anti-pattern for urgency, speculation, and trading
  pressure; only borrow numeric/table discipline where it is calm.

## Color System

Sky blue/cyan/teal is the identity direction. It should feel clear, breathable,
and quietly intelligent, not generic SaaS blue and not crypto-exchange neon.

Light mode is the default. Dark and system themes remain supported.

Use the founder-approved sky ramp as a core identity source:

- `#BDE0FE` - soft sky surface and gentle gradient stop.
- `#A2D2FF` - brighter sky surface, hover tint, secondary data wash.
- `#8FC9FF` - active sky layer, chart support, illustrative highlight.

These pale sky values are usually surfaces, bands, or gradient stops. Do not use
them as small text on white. Pair them with deeper cyan/teal foreground colors
for accessible controls and status labels.

Existing MP tokens remain the migration base:

- Dark accent: `--mp-accent: #22D3EE`, `--mp-accent-ink: #67E8F9`.
- Light accent: `--mp-accent: #0E7490`, `--mp-accent-ink: #064E52`.
- Surfaces: `--mp-paper`, `--mp-card`, `--mp-card-2`.
- Rules: `--mp-rule`, `--mp-rule-2`, `--mp-rule-strong`.
- Status: `--mp-live`, `--mp-stale`, `--mp-block`, `--mp-info`.

Skyframe should add or evolve tokens rather than hardcoding one-off colors.
Recommended future token families:

- `--skyframe-sky-100`, `--skyframe-sky-200`, `--skyframe-sky-300`.
- `--skyframe-accent`, `--skyframe-accent-strong`,
  `--skyframe-accent-soft`.
- `--skyframe-evidence`, `--skyframe-narrative`,
  `--skyframe-provenance`.

Avoid:

- One-note blue screens where every surface is the same hue family.
- Coinbase-like saturated blue buttons everywhere.
- Dominant purple gradients.
- Dark slate dominance that makes the product feel like a trading terminal.
- Beige/cream dominance.
- Decorative gradient blobs, bokeh, or orbs.

Gradients are allowed when they communicate structure. Use gentle sky-to-cyan
ramps for page headers, active analysis zones, selected scope bands, or report
reading depth. Gradients should be restrained, tokenized, and functional.

## Contrast And Separation

Skyframe uses medium-high structural contrast. On a 1-10 contrast dial, the
target is about 7: crisper than a soft SaaS pastel interface, calmer than a
broker terminal or crypto trading screen.

The contrast personality is:

> Calm sky atmosphere, crisp analyst structure.

Sky blue is an atmospheric surface color, not the hierarchy system by itself.
Pale sky-blue surfaces must not create a single low-contrast wash. Users should
be able to identify sections, cards, controls, selected states, evidence zones,
trust strips, and report surfaces at a glance.

Every major section must use at least one visible boundary system:

- Surface step, such as white or near-white cards on a light sky page wash.
- Rule or border with enough contrast to survive light and dark mode.
- Subtle shadow or elevation, without floaty generic SaaS card stacks.
- Spacing and typographic hierarchy.
- Accent rail, left edge, or selected-state line using deeper teal/cyan/blue.

Selected, focus, hover, and active states must use contrast-safe deeper
teal/cyan/blue text, borders, rails, or controls. Pale sky fill can support the
state, but pale sky alone is not enough.

Reports need the strongest hierarchy contrast in the app. Saved analyst memos
must preserve clear visual separation between synthesis, Agent narrative,
deterministic evidence, provenance/audit detail, public market context, and
primary portfolio-aware roles. Reports should feel calm and elegant, never foggy
or visually flattened.

Tables need strong scan contrast. Headers, sticky first columns, row dividers,
numeric columns, expanded details, and gain/loss fields should be easy to parse
without making the table feel like a trading terminal.

## Typography

Skyframe's long-term type identity is:

- Newsreader for editorial synthesis, report titles, memo headings, and humane
  moments.
- Geist for product UI, navigation, forms, labels, and compact explanation.
- JetBrains Mono for values, timestamps, evidence keys, provenance, and
  contract-like details.

Use Newsreader intentionally. It should make reports feel composed and
analytical, not decorative. Do not use large hero-scale serif type inside dense
controls, tables, sidebars, badges, or cards.

Use mono type to signal evidence, timestamps, and data provenance. Do not make
the whole product feel like code or a terminal.

Rules:

- Letter spacing should be zero for body text.
- Uppercase micro-labels may use modest tracking when already established.
- Do not scale font size directly with viewport width.
- Keep headings proportional to their container.
- Preserve readable line length in report prose.

## Density And Disclosure

Skyframe is dense, but not cramped. Users should be able to scan scope, status,
evidence, and narrative without opening five panels first.

Use a combined inline plus expandable model:

- Inline context: one short sentence, label, badge, or hint when it prevents
  misunderstanding.
- Expandable detail: deeper explanation, caveats, technical codes, provenance,
  and row-level secondary detail.

Beginner-specific teaching should be deferred until deployment. For now, write
for a smart but busy investor with basic knowledge.

Avoid:

- Repeated boilerplate.
- Permanent disclaimer walls.
- Raw contract grids.
- Huge empty cards.
- Nested card stacks.
- Repeating freshness or caveat text in every row.

## Layout Principles

The app should feel like an analyst workspace, not a marketing site.

Core patterns:

- Use master/detail layouts for browsing private account data and saved reports.
- Use compact rails and lists for selection.
- Show one focused detail surface at a time.
- Keep repeated tables dense, horizontally contained, and scannable.
- Use full-width bands or unframed layouts for page sections.
- Reserve cards for repeated items, modals, and intentionally framed tools.

Every data page should answer:

- What am I looking at?
- What scope was used?
- How fresh is it?
- What is deterministic evidence?
- What is Agent Team narrative?
- What is unavailable or limited?

## Reports Style

Reports are the flagship expression of Skyframe. They should feel like a saved
analyst memo, not a chat thread, a dashboard grid, or a raw run record.

Reports should include:

- A concise saved-scope and provenance trust strip.
- A synthesis-led reading column.
- Clear separation between deterministic evidence and Agent Team narrative.
- Portfolio-aware roles as primary.
- Public market context roles as secondary when available.
- Compact coverage notes for skipped, unavailable, partial, or validation-held
  narrative.
- Expandable audit and technical provenance.

The basic report form should be strong now and allow richer components later.
Future report components may include richer role comparisons, section-level
provenance, coverage summaries, narrative annotations, and better public-evidence
grouping, but only after reviewed backend fields exist.

Agent teammates should feel like people with roles, not anonymous cards. Use the
most relevant typed icon first. Defer bespoke teammate identities until the role
system is stable.

Do not make reports feel like:

- A broker statement.
- A trading terminal.
- A generated blog post.
- A recommendation card.
- A legal document.
- A chat transcript.

## Dashboard And Market Context

Dashboard and market context surfaces should be compact cockpit views for
awareness and readiness. They provide context, not instructions.

Use:

- Focused status strips.
- Compact charts with honest axes and source labels.
- Clear unavailable states.
- Freshness and source labels that distinguish source update time from backend
  checked time.
- Calm selected states and accessible focus rings.

Do not use:

- Live-market urgency.
- Risk-on/risk-off phrasing.
- Provider branding treatments or cloned provider pages.
- Large generic dashboard cards that repeat the same contract shape.

## Account Details

Account Details is a private selected-account workspace, not a holdings mirror
and not a broker clone.

Use:

- Account rail plus selected-account detail.
- Backend-owned display labels only.
- Compact cash/readiness summaries.
- Brokerage-style position tables when backend safe display rows exist.
- Row expansion for secondary details and tax-lot display rows.
- Quiet data notes and technical disclosures.

Avoid:

- Raw refs, account IDs, provider IDs, account numbers, raw balances, raw
  holdings, raw quantities, transactions, raw payloads, and broker action
  controls.
- Showing all accounts as full detail cards at once.
- Prominent repeated "cached", "as of", "freshness", or caveat columns.
- Frontend financial calculations.

## Trade Review

Trade Review is deterministic review plus selected scope context. It must keep
review account, portfolio context, scope caveats, and backend feasibility labels
clear without turning the form into a broker workflow.

Use:

- Distinct review-account selector and broader portfolio context selector.
- Backend-owned scope labels in results.
- Deterministic sections before narrative or agent commentary.
- Clear unavailable, partial, and caveated states.

Avoid:

- Order-entry controls.
- Account refs or context refs in visible UI.
- Copy that implies the app has made a trade decision.
- Frontend recomputation of backend finance outputs.

## Agent Console

Agent Console is read-only analysis status and narrative. Composer remains
disabled unless a future reviewed contract changes that.

Use:

- Compact scope banner from lossy backend summary fields.
- Clear distinction between account-level feasibility evaluated vs not
  evaluated.
- Generic copy when labels are unavailable.
- Narrative zones that show role, evidence scope, provider status, and caveats.

Do not send account labels, raw private detail, or scope labels into Agent Team
evidence. Only reviewed lossy/sanitized scope summaries may be used when an
approved backend contract explicitly permits them.

## Evidence, Narrative, Freshness, And Provenance

Skyframe must make epistemic boundaries visible.

Deterministic evidence:

- Backend-owned.
- Structured.
- Uses mono or compact factual styling.
- Owns calculations, labels, scope, freshness, and caveats.

Agent Team narrative:

- Bounded and role-separated.
- Clearly labeled as analysis narrative.
- Cannot invent metrics, citations, facts, timestamps, or recommendations.
- Must visually sit apart from deterministic evidence.

Freshness:

- Show source update time as source update time.
- Show backend checked time as backend checked time.
- Never imply page refresh equals source update.
- Never use "live" or "real-time" unless the reviewed backend contract and
  source semantics support it.

Provenance:

- Keep compact trust information visible.
- Put full audit detail in disclosure.
- Use timestamps, provider/status labels, evidence references, and scope labels
  only when they are backend-owned and safe to display.

## Components And Interaction

Use established MP primitives and tokens where possible:

- `Panel`, `Badge`, `KV`, `Stat`, scoped tables, compact rails, and detail
  disclosures.
- Icon buttons should use typed icons from the existing icon library.
- Segmented controls for modes.
- Toggles or checkboxes for binary settings.
- Menus for option sets.
- Tabs for view switching.
- Tooltips for icon-only or unfamiliar controls.

Interaction principles:

- Keyboard focus must be visible and token-based.
- Mouse clicks should not leave harsh browser-default black outlines.
- Hover, selected, active, loading, disabled, error, empty, and unavailable
  states must be designed.
- Loading should be local where possible; avoid full-page flashing for local
  refreshes.
- Keep table scroll inside the panel and preserve sticky first columns where it
  improves scanability.

Avoid:

- Pills everywhere.
- Cards inside cards.
- Text buttons where a standard icon is clearer.
- Decorative UI elements that look interactive.
- Hidden state changes with no text label.

## Copy And Tone

Voice: calm, precise, and human. The product should sound like a thoughtful
analyst teammate, not a broker, coach, influencer, or compliance wall.

Use:

- "Review scope"
- "Saved scope"
- "Data notes"
- "Source updated"
- "Backend checked"
- "Narrative unavailable"
- "Analysis only"
- "Manual review"

Avoid:

- Advice or recommendation language.
- Urgency language.
- "AI-picked", "best trade", "safe to trade", "ready to trade",
  "risk-on", "risk-off", "execute", "order", "submit order",
  "buy now", "sell now", "guaranteed".
- Raw backend jargon as primary user-facing copy.
- Repeating "private detail" or "amounts hidden" in every surface.

## Accessibility

Skyframe cannot rely on color alone. Pair color with text, icons, shape, or
position.

Requirements:

- Maintain readable contrast in light and dark mode.
- Meet WCAG AA text contrast at minimum; aim higher for primary body text,
  key values, controls, selected states, and trust/freshness/caveat labels.
- Text must fit within its container at 1024, 1280, and 1440 widths.
- Tables must avoid horizontal page overflow.
- Tooltips and disclosures should be keyboard accessible.
- Focus-visible styling must be clear and brand-aligned.
- Motion should be subtle and nonessential.

## Privacy And Safety Boundaries

All UI work must preserve the repo safety rules.

Do not display or persist:

- Raw account IDs, account references, context references, scope references,
  broker IDs, provider IDs, account numbers, raw provider payloads, prompts,
  traces, secrets, raw balances, raw holdings, raw positions, raw quantities,
  transactions, orders, or broker action controls.

Do not add:

- Frontend financial calculations.
- Provider, broker, market-data, LLM, or TradingAgents calls from the frontend.
- Storage writes for sensitive data.
- Order placement, execution, cancellation, transfer, or broker-action flows.
  Broker disconnect/delete/account-management flows require a separate
  product/security contract and are not style decisions.

Synthetic/demo examples must be clearly synthetic.

## Forbidden Visual Patterns

Do not use:

- Broker dashboard clones.
- Trading terminal layouts.
- Crypto exchange urgency.
- Gamified confetti, achievement, dopamine, or streak mechanics.
- AI stock-picker visuals.
- Oversized in-app marketing hero layouts.
- Decorative gradient blobs, orbs, bokeh, or pasted SVG illustration systems.
- Dominant purple gradients, beige/cream, dark slate, brown/orange, or one-note
  blue palettes.
- Provider logos or brand treatments unless rights and product review approve
  them.
- Execution-style controls or affordances.

## Migration Guidance

Adopt Skyframe progressively:

1. Preserve reviewed backend contracts and product-safety boundaries.
2. Tokenize before broad visual changes.
3. Reuse or extend MP primitives before creating new component families.
4. Migrate one route or component group at a time.
5. Keep current working states intact while improving hierarchy.
6. Use synthetic fixtures and reviewed mock data for design exploration.
7. Run visual, contract, privacy, and safety review for meaningful UI changes.

Do not pause useful product work waiting for a complete style-system rewrite.
Every touched screen should move a little closer to Skyframe.

## Design Tool Workflow

Claude Design may explore concepts and propose additive fields when explicitly
framed as design exploration. Proposed fields are not product facts and must be
labeled as future contract needs.

Stitch or implementation accelerators should be introduced only after:

- The Skyframe direction is accepted for the relevant surface.
- The founder chooses a concept direction.
- Track A vs Track B fields are labeled.
- Codex B/Codex C review any additive backend contract needs.
- The implementation prompt includes the exact reviewed fields and safety rails.

Implementation agents must not ship unreviewed fields or fabricated values just
because a concept mock displayed them.

## Per-Surface Design Docs

This root `STYLE.md` leads the whole app. Feature-specific docs may refine it:

- Reports design docs may specify memo hierarchy, role grouping, evidence
  placement, and provenance variants.
- Account Details docs may specify selected-account table density, row
  expansion, and private display rules.
- Trade Review docs may specify form/result hierarchy and scope metadata display.
- Market Context docs may specify chart, source, and freshness semantics.
- Agent Console docs may specify lossy scope banners and read-only agent status.

Per-surface docs must cite `Portfolio Copilot Skyframe` and cannot override its
privacy, safety, evidence, or manual-decision-support boundaries.
