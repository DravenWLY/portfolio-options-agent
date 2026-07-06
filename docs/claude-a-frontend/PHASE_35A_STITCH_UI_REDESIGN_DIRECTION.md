# Phase 35A - Stitch UI Redesign Direction

Owner: Claude F (frontend redesign / Stitch collaboration / UI refinement)
Status: planning memo — design direction only; no implementation in this task
Date: 2026-06-30
Cites: `STYLE.md` / Portfolio Copilot Skyframe
Related: `docs/shared/frontend_design_change_playbook.md`,
`docs/claude-a-frontend/PHASE_29B_T4_CLAUDE_DESIGN_BRIEF.md` (the prior Claude
Design → Stitch handoff that this workflow is modeled on),
`docs/codex-b-architecture/PHASE_30A_GOLDEN_PATH_REVIEW_DESK_CONTRACT.md`,
`docs/codex-b-architecture/PHASE_31A_FOUNDER_DEMO_POLISH_CONTRACT.md`,
`docs/codex-b-architecture/PHASE_34A_LIVE_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md`

## Purpose

This is the onboarding/planning memo for Claude F. It inventories the current
frontend, defines how Stitch exploration should flow into safe implementation
prompts, sets industry-level UI principles scoped to Portfolio Copilot's
review-desk posture, and proposes a redesign sequence. Nothing here is an
implementation request. No code changed in this task.

## 1. Current Frontend Surface Inventory

Read directly from `frontend/src/pages/`, `frontend/src/components/trade-review/`,
`frontend/src/components/reports/`, `frontend/src/components/shared/mp/`,
`frontend/src/components/shared/SkyframeSurface.tsx`, and `frontend/src/styles/globals.css`.
Route map confirmed from `frontend/src/App.tsx`.

| Surface | Route | Key files | Skyframe surface wrap | Visual maturity |
| --- | --- | --- | --- | --- |
| Trade Review | `/trade-review` | `TradeReviewPage.tsx`, `components/trade-review/{TradeReviewForm,TradeReviewResults,SaveReviewSnapshot,SymbolAutocomplete}.tsx` | Yes — `SkyframeSurface maxWidth={1280}` | Solid tiered structure; form and results are dense, fully bespoke inline-styled blocks |
| Reports | `/reports` | `ReportsPage.tsx`, `components/reports/*` | Yes — `SkyframeSurface` + `reports-skyframe` token layer, default max-width (1320px) | Most mature surface in the app; the de facto Skyframe reference |
| Account Details | `/account-details` | `AccountDetailsPage.tsx` (1,993 lines, one file) | **No** — plain `<div className="mp-surface">`, no `SkyframeSurface`, no sky wash | Functionally the richest surface (two-pane, sticky tables, nickname editor, tax-lot expansion) but visually the furthest from Skyframe |
| Dashboard | `/` | `DashboardPage.tsx` | Yes — `SkyframeSurface maxWidth={1280}` | Disciplined `Panel`/`KV`/`Stat` reuse; lower redesign priority per roadmap |
| Agent Team Analysis (Agent Console foundation) | `/agent-team-analysis` | `AgentTeamAnalysisPage.tsx` | Not reviewed this pass | Composer stays disabled; explicitly out of scope now |
| Portfolio Context | `/portfolio-context` | `PortfolioContextPage.tsx` | Not reviewed this pass | Adjacent surface; P31A-T4 already did hygiene work here |
| Market Mood, Market Data, Risk Review, Broker Connection, Settings | various | — | Not reviewed this pass | Adjacent surfaces, not a priority for this phase |
| Auth, Pricing, Landing | `/auth`, `/pricing`, `/landing` | — | Not reviewed this pass | Pre-product/marketing pages; out of scope for a review-desk redesign focus |

Shared primitive layer (`components/shared/mp/`): `Badge`, `Pill`, `Panel`,
`KV`, `Stat`, `FreshnessDial`, `PageHeader`, `SafetyStrip`, `DemoChip`,
`MpIcon` (a typed 24×24 stroke-icon set, no emoji). All consume `--mp-*`
tokens only and are backend-agnostic. `SkyframeSurface.tsx` is the typed
wrapper around the `.skyframe-surface` CSS rule (top-anchored sky-wash
gradient that fades by ~280px, never a full-page tint).

Type system (`globals.css`, self-hosted under `/fonts/`): Newsreader
(display serif, `.mp-display`), Geist (`--mp-font-sans`, default UI face),
JetBrains Mono (`--mp-font-mono`, `.mp-mono`, used for evidence/timestamps/
values). Color: dark token set is the `:root` default, light is a
`[data-theme="light"]` override with hues darkened to clear WCAG-AA; Reports
layers an additional `--reports-*` token scope (`reports-trust-surface`,
`reports-evidence-surface`, etc.) on top of `--mp-*` rather than introducing
new raw colors.

**Concrete inconsistencies found while reading (not opinions — verified in code):**

- `AccountDetailsPage.tsx:1638` hardcodes `fontFamily: '"Hanken Grotesk", var(--mp-font-sans)'`
  on the page wrapper, and its `detailTitle` style (`AccountDetailsPage.tsx:1748-1752`)
  renders the selected-account name at `fontSize: 36, fontWeight: 800` — a
  heavier, larger, non-Skyframe headline treatment than `PageHeader`'s `h1`
  (`font-size-2xl`/weight 500) or Reports' `ReportDetail` title (same weight
  500). This is the single clearest type-system drift in the app.
- Page max-width is inconsistent: Trade Review and Dashboard pass
  `maxWidth={1280}` explicitly; Reports omits the prop and gets the
  `SkyframeSurface` default (`--skyframe-page-max: 1320px`); Account Details
  uses neither `SkyframeSurface` nor either of those values — its own `page`
  style caps at `1440`.
- `components/reports/ReportHistoryPlaceholder.tsx` is dead code — grep
  confirms it is not imported anywhere. Worth a housekeeping note, not a
  redesign blocker.

## 2. Stitch Collaboration Workflow

**Founder-confirmed process (2026-06-30):** the founder runs Stitch
themselves, outside Claude Code. Claude F does not drive the Stitch MCP tools
to generate concepts on the founder's behalf — that option was considered
(see the superseded tooling note below) and explicitly rejected in favor of
this workflow:

1. **Claude F identifies every component on the target page first** — not
   just the page file, but every component it renders, including
   nested/inline sub-components — and writes a single component-inventory
   prompt summarizing each one's role, current visual treatment, and the
   hard constraints that must survive any redesign (Section 3 below, and
   `STYLE.md` Skyframe rules). This prompt is the deliverable Claude F
   produces before Stitch has run at all.
2. **The founder feeds Stitch three things together:** Claude F's
   component-inventory prompt, the page's actual source code, and a
   screenshot of the current page. Stitch produces a redesign concept
   grounded in that real structure instead of a generic reimagining.
3. **The founder brings Stitch's output back.** Claude F compares it against
   reality, not the idealized concept:
   - re-read the current implementation of that route/component group;
   - check every visual idea against `STYLE.md` Skyframe rules and this
     memo's hard constraints;
   - classify the read-contract status of every data field the concept
     shows.
4. **Track A vs Track B labeling** (verbatim from the P29B-T4 brief, the
   approach already proven on Reports):
   - **Track A** — fields already in the reviewed read contract. Free to
     design and implement frontend-only.
   - **Track B** — anything the concept invents (new fields, new structured
     objects, new freshness/provenance granularity). Welcome to explore and
     mock with synthetic data, but every such element must be **labeled as a
     proposal** and routed to Codex C (contract) + Codex B (privacy/safety)
     before it can ship. The live UI never renders an unreviewed field or a
     fabricated value.
5. **Claude F produces a narrow implementation prompt** in the
   `docs/shared/AGENT_REPORT_FORMAT.md` shape, scoped to one route or
   component group, naming exact files, exact fields, and exact forbidden
   patterns — for Claude A (primary) or Codex F (backup).
6. **Review gates are specified in the prompt itself** (see Section 6).
7. **Claude F does not implement** unless explicitly reassigned to do so.

*Superseded tooling note:* the Stitch MCP server (`mcp__stitch__*`:
`create_project`, `generate_screen_from_text`, `edit_screens`,
`generate_variants`, `list_screens`/`get_screen`, `create_design_system`,
`create_design_system_from_design_md`, `upload_design_md`,
`apply_design_system`, `update_design_system`, `list_design_systems`/
`list_projects`) is connected in this environment and could technically
drive Stitch generation directly, including seeding a design system from the
Skyframe tokens. Per the founder-confirmed process above, this is **not**
how Stitch gets used here — the founder runs Stitch manually with the inputs
in step 2. Recorded so a future session doesn't reintroduce it by default.

## 3. Industry-Level UI Principles For Portfolio Copilot

Synthesized from `STYLE.md`, `.claude/skills/finance-dashboard-ux-review/SKILL.md`,
and `docs/shared/frontend_design_change_playbook.md`, checked against what the
code actually does today.

1. **Analyst-desk calm, not marketing bold — this is a real tension to actively
   guard against.** The generic Claude Code `frontend-design` skill (available
   in this environment) instructs "commit to a BOLD aesthetic direction,"
   "maximalist chaos," "distinctive fonts," "gradient mesh, noise textures,"
   and "NEVER converge on common choices." That instinct is the opposite of
   what `STYLE.md` wants here. Any Stitch concept, or any reflex of my own,
   that leans toward "memorable/unexpected/striking" must be filtered through
   `STYLE.md` first — generic frontend-design taste is not the bar for this
   product. The Account Details headline (`Hanken Grotesk`, 36px/800) is a
   small real example of this drift already in the codebase.
2. **Contrast dial ~7/10.** Stepped surfaces (white/near-white cards on the
   sky wash), real rules, accent rails — never a single pastel wash carrying
   hierarchy by itself. Already well executed in Reports' card/rail/strip
   layering; the bar to hold every other surface to.
3. **Type discipline.** Newsreader only for synthesis/memo headlines
   (`ReportDetail`'s `FinalSynthesis` headline is the canonical example);
   Geist for UI/forms/nav; JetBrains Mono for evidence, timestamps, codes,
   values. No ad hoc `fontFamily` overrides — fix, don't extend, the Account
   Details exception.
4. **Evidence vs narrative must stay visually distinct everywhere.**
   `AgentRoleSection.tsx`'s explicit "Agent narrative · analysis only" zone
   vs "Deterministic evidence cited · backend-owned" zone is the reference
   pattern (`components/reports/AgentRoleSection.tsx:60-91`). Any new
   surface that mixes backend facts and agent/LLM text should be checked
   against this split before anything else.
5. **Density via tiering and disclosure, not via cramming or hiding.**
   Trade Review's Tier 1 (always visible) / Tier 2 (`<details>` disclosure,
   collapsed by default unless a safety caveat forces it open) / Tier 3
   (always visible at bottom) model, and Reports' primary/context role-band
   split, are the established shape. Extend this pattern to new surfaces
   rather than inventing a new one per page.
6. **Status and severity: icon + text, never color alone.** Already
   consistent (`SEVERITY_META`/`CAVEAT_META` in `TradeReviewResults.tsx`,
   `roleStatusIcon`/`roleStatusMeta` in `reportStatus.ts`, the gain/loss
   glyph-before-color rule in `AccountDetailsPage.tsx`'s `gainLossSign`).
   Preserve this in every redesign slice; it's also a hard accessibility
   requirement, not just a style preference.
7. **Watch for "cards inside cards" — but weigh it against the evidence/
   narrative separation rule when the two pull in different directions.**
   `AgentRoleSection`'s bordered `evidenceZone` sits inside the bordered
   `primaryCard`. That reads as nested cards, but it exists specifically to
   keep evidence visually walled off from narrative (principle 4), which
   `STYLE.md` ranks above the "no cards in cards" rule. Treat this as the
   one sanctioned exception shape, not a license to nest boxes generally.
8. **Tables: sticky first column, dense rows, conditional columns.**
   `AccountDetailsPage.tsx`'s equity/option tables already do this correctly
   (columns only render when at least one row has data — see
   `showLastPrice`/`showMarketValue`/etc. in `EquityRows`). A Skyframe
   redesign of this page should restyle, not rearchitect, these tables.
9. **Backend-owned copy only, translated through one friendly-label layer.**
   `scopeNoteLabel` / `evidenceKeyLabel` / `humanizeCode` in
   `components/reports/reportStatus.ts` is the established pattern for
   turning backend codes into display copy while keeping the raw code in
   `title`/audit. Reuse this pattern; don't invent a parallel one per
   surface.
10. **Demo/placeholder honesty.** `DemoChip` ("demo · not yet connected") is
    mandatory on any unconnected data card; already used correctly across
    Dashboard and Account Details.

## 4. Page-By-Page Redesign Priorities

### 4.1 Trade Review composition polish — top recommended slice

Files: `TradeReviewPage.tsx`, `TradeReviewForm.tsx` (1,016 lines),
`TradeReviewResults.tsx` (1,187 lines), `SaveReviewSnapshot.tsx`.

What's already right: the Tier 1/2/3 model, the actionability banner leading
with icon+text, the explicit "Save evidence snapshot → Reports → generate
briefing" handoff copy in `SaveReviewSnapshot.tsx`.

What needs polish:
- `TradeReviewForm.tsx` is ~1,000 lines of fully bespoke inline-styled
  fields, fieldsets, and a hand-built combobox (`ReviewAccountCombobox`) —
  there is no shared form-field primitive, so every label/input pairing is
  restyled per call site. A small `FormField`/`Select` primitive (alongside
  the existing `mp/` set) would cut this duplication and give Account
  Details' future nickname/edit affordances something to reuse too.
- `ScopeMetadataPanel` and `FreshnessPanel` in `TradeReviewResults.tsx`
  render as two visually near-identical bordered "card" blocks stacked
  before any disclosure — both lead with a `cardTitle`/`detTag` header and a
  `FactRow` key/value list. Reports solved an analogous problem with
  `ReportTrustStrip`: one compact, always-visible strip instead of two full
  cards. A similar compact "scope + freshness" strip at the top of Trade
  Review results would shorten the scan path before Tier 2 detail.
- The Tier 1/2 `FactRow` lists are functionally correct deterministic
  evidence but, at full length, risk reading as the "raw contract grid"
  `STYLE.md` explicitly warns against. Worth checking real content length in
  the browser before deciding whether any rows move into disclosure.

### 4.2 Reports detail briefing hierarchy polish — already the reference surface

Files: `ReportsPage.tsx`, `ReportDetail.tsx`, `AgentRoleSection.tsx`,
`ReportProvenance.tsx`, `ReportTrustStrip.tsx`, `ToolMediatedEvidence.tsx`.

This is the most mature surface in the app and matches `STYLE.md`'s Reports
section closely: trust strip → state banner → final synthesis (serif lede)
→ primary/context role bands → provenance → tool-mediated evidence. Redesign
work here should be incremental, not structural:
- `ReportProvenance` and `ToolMediatedEvidence` are adjacent, both
  `--reports-soft-surface` bordered blocks with a `<details>` disclosure —
  at the bottom of a long report they currently read as near-twins. Worth a
  visual-rhythm pass (spacing, accent weight) once real tool-mediated data
  exists (P34A-T3B/T7) rather than now, since today's content is still the
  mock/offline P33A-T6B safe subset.
- `ReportHistoryPlaceholder.tsx` (unused) should be deleted as cleanup
  whenever a Reports task is in progress — flagging here, not actioning it.

### 4.3 Account Details selected-account workspace polish — largest concrete gap

Files: `AccountDetailsPage.tsx` only (one 1,993-line file; no
`components/account-details/` split exists yet).

This is functionally the richest surface (two-pane rail/detail, sticky
tables, conditional columns, tax-lot "Purchase history" expansion, a fully
accessible nickname editor with focus-return/`aria-describedby`/`role=alert`),
but it is the furthest from Skyframe visually, for reasons Section 1 already
named precisely: no `SkyframeSurface` wrap, a non-Skyframe font override at
36px/800-weight, and a one-off 1440px max-width. The net effect is that it
reads closer to a brokerage back-office admin panel than the calm analyst
desk Reports achieves — even though the underlying data architecture and
accessibility work are arguably the best in the app.

`docs/shared/implementation_plan.md` already names this gap directly: P29B-T7
shipped Skyframe to "Reports, Trade Review, Dashboard, Settings, Market Data,
Risk, and Market Mood... Account Details and Agent Console remain explicitly
deferred as higher-scrutiny surfaces." This redesign slice is that deferred
work, now due.

Scoped fix (presentation-only, no field/contract change):
- wrap the page in `SkyframeSurface` (drop the plain `mp-surface` div);
- remove the `Hanken Grotesk` override and the 36px/800 title style; adopt
  the same title treatment `PageHeader`/`ReportDetail` use;
- normalize max-width to 1280 (matching Trade Review/Dashboard) or 1320
  (matching Reports' default) — pick one and make all four surfaces match;
- re-skin the existing table/card structure onto Skyframe surface tokens
  (`--reports-*`-style scoping if a dedicated token layer is useful, or
  plain `--mp-*` if not) without changing row logic, expansion behavior, or
  the privacy/`amounts_hidden` rules.

### 4.4 Tool-mediated evidence / audit band refinement

File: `ToolMediatedEvidence.tsx`. Already covered under 4.2 — defer the
visual pass until real tool data lands per P34A-T3B/T7 rather than
redesigning around today's mock/offline content.

### 4.5 Dashboard — only if it directly supports the golden path

`DashboardPage.tsx` already has the most disciplined primitive reuse in the
app (consistent `Panel`/`KV`/`Stat`/`Badge` usage, vs. Account Details' fully
bespoke styles). Leave it alone unless Trade Review polish surfaces a
concrete entry-point need (e.g., the "New trade review →" CTA).

### 4.6 Agent Console — explicitly not now

`AgentTeamAnalysisPage.tsx` exists as foundation only. Composer/chat stays
disabled per `docs/shared/current_roadmap.md` ("Paused / Deferred"). No
redesign work in this phase.

## 5. Proposed Task Sequence

| Task | Scope | Owner | Reviewer |
| --- | --- | --- | --- |
| P35A-T0 | This memo | Claude F | — (status: done, this document) |
| P35A-T1 | Trade Review component-inventory prompt (for founder to run in Stitch with source + screenshot) | Claude F | none required (prep artifact, not implementation) |
| P35A-T2 | Founder runs Stitch; Claude F translates the output into Track A/B findings + a narrow implementation prompt for Trade Review composition | Claude F (with founder + Stitch) | Claude B + Codex B rail-check before founder picks a direction (mirrors P29B-T4) |
| P35A-T3 | Trade Review polish implementation | Claude A (Codex F backup) | Claude B required; Codex B only if scope-note/evidence semantics or any field changes |
| P35A-T4 | Account Details component-inventory prompt + Track A/B translation once founder runs Stitch | Claude F | Claude B + Codex B rail-check before implementation (account-data surface) |
| P35A-T5 | Account Details Skyframe migration implementation | Claude A | Claude B required; Codex B required (named higher-scrutiny surface in P29B-T7 — narrow confirmation that the change stays presentation/wrapper-only) |
| P35A-T6 | Reports visual-rhythm polish (provenance vs tool-mediated bands) | Claude F → Claude A | Claude B only, unless content changes once P34A-T3B/T7 land |
| P35A-T7 | Tool-mediated evidence band visual refinement | Claude F → Claude A | Bundle with P34A live-data landing; do not do speculatively against mock content |

This is a recommendation, not a commitment — Codex A/founder can reorder.

## 6. Contract / Privacy Review Triggers (Codex B)

Per this onboarding's standing instructions, require Codex B before
implementation whenever a redesign slice:

- needs new backend/read fields;
- changes report/status/evidence/provenance semantics;
- changes privacy exposure;
- changes saved-report readback behavior;
- changes account data display scope;
- adds source/freshness/availability claims;
- touches Agent Team evidence boundaries;
- could imply advice, recommendation, execution, or product-managed
  decisions.

None of the four priority slices in Section 4 currently need new fields. The
Account Details slice (4.3) is presentation-only by design, but because the
roadmap already names Account Details as higher-scrutiny, I'm routing it
through Codex B anyway as a narrow confirmation step rather than skipping it
on a technicality.

## 7. Visual / UX Review Gates (Claude B)

Every implementation slice in Section 5 goes to Claude B for:

- visual hierarchy;
- responsive behavior at 1024/1280/1440;
- accessibility (keyboard, focus-visible, contrast, icon+text status);
- safety-copy (no advice/order/execution/guaranteed-return wording);
- overflow (no horizontal page overflow);
- dark/light mode parity;
- product tone (analyst desk, not dashboard/terminal/AI-picker).

## 8. What Should Remain Deferred

- Agent Console composer/chat activation.
- Dashboard expansion beyond direct golden-path support.
- New data providers or public evidence sources.
- New report fields beyond the already-approved P33A-T6A safe subset, until
  P34A-T3B through T7 land real tool data.
- New financial calculations of any kind (frontend never computes).
- Auth/Pricing/Landing marketing redesign — out of this phase's review-desk
  focus, and `STYLE.md` explicitly warns against "oversized in-app marketing
  hero layouts," so these pages need their own framing discussion before any
  Stitch exploration touches them.
- Broker Connection, Market Data, Risk Review, Portfolio Context, Settings —
  adjacent surfaces, untouched until the four priority surfaces have had at
  least one redesign pass.

## 9. First Recommended Implementation Slice

**Trade Review page composition polish** (Section 4.1), scoped narrowly to:

- a compact "scope + freshness" trust strip at the top of
  `TradeReviewResults.tsx`, replacing the two near-identical
  `ScopeMetadataPanel`/`FreshnessPanel` cards with one glanceable strip
  (mirroring `ReportTrustStrip`'s already-validated pattern), with full
  detail demoted into existing/adjacent disclosure;
- optionally, extracting the repeated label/input pairing in
  `TradeReviewForm.tsx` into a small shared field primitive, if it can be
  done without changing any validation or submission behavior.

Rationale: zero new backend fields (100% presentation over the existing
`TradeReviewWorkspaceRead` contract), lowest contract risk of any candidate,
highest visual payoff since it's the entry point of the golden path, and it
directly extends a pattern (trust strip) already founder-accepted in
Reports.

**Lower-risk alternative**, if the founder wants something even narrower to
start: the Account Details `SkyframeSurface` wrap + font-system fix
(Section 4.3's scoped fix). It is a smaller, more mechanical change with a
named, pre-existing roadmap gap to point to, but it touches the
higher-scrutiny Account Details surface, so it carries a mandatory (if
narrow) Codex B step that Trade Review polish does not strictly need.

I'd suggest Trade Review first per the order this onboarding brief itself
recommended, with Account Details queued immediately after.

## Verification

This task is docs-only. Verification is `git diff --check` inside
`portfolio-options-agent`, run after this file was written.
