# Frontend Design Change Playbook

Status: active guidance
Owner: shared, with Codex B architecture and Claude A frontend
Last updated: 2026-05-23

Use this playbook before any major frontend redesign, prototype adoption, Figma/Claude Design integration, or visual system migration. It exists because prototype-to-product integration can become expensive when the design is translated before contracts, tokens, and component boundaries are clear.

## Core Rule

Treat frontend redesign as a design-system migration, not as a copy/paste of a prototype into the app.

The prototype is a visual and interaction reference. The application remains a typed React/TypeScript product with existing backend contracts, privacy boundaries, product-safety rules, and route ownership.

## When To Use

Use this playbook when:

- A Claude Design, Figma, or other prototype should influence the app UI.
- A page, shell, sidebar, dashboard, workspace, or marketing surface is being redesigned.
- A new design introduces placeholder data, fake screenshots, or visual examples.
- Frontend work could affect API shape, TypeScript types, state management, routing, storage, or backend/frontend seams.
- Stakeholders request "make it look exactly like the prototype."

## Required Design Integration Contract

Before implementation, Codex B and Claude A should define a short contract that answers:

- Which routes and components are affected?
- Which backend contracts must remain unchanged?
- Which prototype fields are visual-only placeholders?
- Which prototype fields are forbidden because the backend does not expose them?
- Which existing TypeScript types and API clients must be reused?
- Which elements are out of scope for this slice?
- Which safety/product phrases must be removed or rewritten?
- Which browser widths and states must be visually checked?
- Which follow-up backend tasks are needed to replace placeholders with real data?

Keep this contract in `docs/shared/implementation_plan.md` for the active phase or in a short architecture handoff if the change is broad.

## Prototype Requirements

Prefer prototypes that are close to the production stack:

- React/TypeScript-shaped components (`.tsx`) over plain HTML/JavaScript.
- Typed props over loose objects.
- CSS variables or design tokens over one-off styles.
- No fake API clients.
- No global application state that duplicates the real app.
- No invented financial fields presented as real data.
- No prototype JavaScript pasted directly into the app.

If the prototype is not TypeScript/React, translate it manually into app-native components. Do not paste prototype scripts into production code.

## Migration Order

Use this order for major redesigns:

1. Define design integration contract.
2. Extract visual tokens.
3. Build or update shared primitives.
4. Migrate shell/topology.
5. Migrate one route or workspace slice at a time.
6. Replace placeholder cards only when backend contracts exist.
7. Run frontend contract review and browser smoke tests.

Avoid one giant rewrite unless the app is being intentionally replaced.

## Tokenize First

Extract the design into stable tokens before page work:

- Color palette.
- Typography stacks.
- Spacing scale.
- Border radius.
- Borders and rules.
- Shadows.
- Status colors.
- Light/dark theme behavior.
- Card/panel surfaces.

Use app-scoped token names when migrating alongside an existing design system. For example, the Modern Portfolio Desk migration used `--mp-*` tokens so legacy `--color-*` consumers could coexist during the transition.

## Shared Primitives Before Pages

Translate repeated visual patterns into reusable primitives first:

- `Panel`
- `Badge`
- `Pill`
- `KV`
- `Stat`
- `PageHeader`
- `SafetyStrip`
- `FreshnessPanel`
- `DemoChip`

Pages should compose these primitives instead of duplicating prototype markup. This makes future redesign and backend wiring cheaper.

## Backend Contract Boundaries

Frontend redesign must not change backend contracts unless explicitly authorized.

Claude A must preserve:

- Existing API clients.
- Existing TypeScript types.
- Existing backend field names.
- Decimal/string serialization semantics.
- Existing actionability vocabulary.
- Broker snapshot freshness and market quote freshness as separate concepts.
- Deterministic facts and LLM/agent commentary as separate concepts.

Claude A must not:

- Invent backend fields.
- Add frontend-only financial calculations.
- Normalize broker freshness and market freshness into one status.
- Convert placeholder values into implied real data.
- Create new network calls without a backend task and review.
- Store portfolio, review, broker, provider, prompt, credential, or account data in browser storage.

## Placeholder Data Rules

Placeholder screens are allowed only when they are clearly labeled and safe.

Every data-bearing card without a backend contract must show a visible label such as `demo · not yet connected`.

Placeholder data must:

- Be synthetic.
- Use neutral names such as `Trader` or `Demo brokerage`.
- Avoid real broker account labels unless the backend already provides sanitized labels.
- Avoid precise real-looking account values.
- Avoid raw holdings, raw positions, cash balances, buying power, account values, broker/provider ids, raw payloads, trade journal entries, and account-specific thresholds.

When in doubt, show an empty state, a dash, or a demo chip instead of inventing realistic financial data.

## Product Safety Rules

Design changes must preserve Portfolio Copilot's product boundaries:

- No broker order placement.
- No order cancellation.
- No destructive broker actions.
- No execution-style UI.
- No "Buy now", "Sell now", "Place trade", "Submit order", "Confirm trade", "auto-trade", "safe to trade", "ready to trade", guaranteed-return, AI-picked, or "you should buy/sell" wording.
- No raw private brokerage data exposure.
- No frontend financial computation.
- No LLM-generated financial metrics.
- No advice wording disguised as UI microcopy.

Portfolio Copilot is a read-only, analysis-only, manual trade-review copilot.

## Slice Discipline

Prefer small redesign slices:

- Shell/navigation.
- Trade Review workspace.
- Agent Console.
- Dashboard placeholders.
- Reports placeholders.
- Portfolio Context placeholders.
- Settings/Auth/Marketing placeholders.
- Font and typography fidelity.

Each slice should have:

- A task block in `docs/shared/implementation_plan.md`.
- Files expected to change.
- Acceptance criteria.
- Rollback notes.
- Typecheck/lint/build verification.
- Browser smoke expectations.
- Review gate owner.

## Browser Smoke Expectations

For frontend visual changes, verify at minimum:

- 1024, 1280, and 1440 px viewport widths.
- Light and dark themes.
- Expanded and collapsed sidebar states.
- No horizontal overflow.
- No overlapping text or hidden controls.
- Route-specific topbar/sidebar state.
- Only approved network calls.
- No new storage keys beyond approved UI-only keys.
- Demo chips visible on non-backend-bound data cards.

For Trade Review and Agent Console, also verify:

- Broker snapshot freshness and market quote freshness remain visually separate.
- Deterministic review facts are visually separate from agent commentary.
- No execution controls appear.
- Actionability status uses text plus icon, not color alone.

## Figma / Claude Design Workflow

For future work with Figma MCP or Claude Design:

- Use design tools to clarify tokens, layout, states, and component variants before implementation.
- Ask for TypeScript/React-friendly output when possible.
- Ask design tools to separate visual examples from real data fields.
- Create a prototype-to-app mapping before coding.
- Do not assume every prototype screen should become a production route.
- Do not assume every prototype datum should become a backend field.

Recommended mapping format:

| Prototype Element | App Component | Backend Source | Status |
| --- | --- | --- | --- |
| Shell sidebar | `components/layout/Sidebar.tsx` | none | implement |
| Trade review result panel | `components/trade-review/*` | existing trade review contract | implement |
| Dashboard recent reviews | future dashboard endpoint | missing | demo only |
| Auth form | future auth flow | missing | static placeholder only |

## Review Gates

Use `docs/shared/agent_workflows.md` and run `portfolio-frontend-contract-review` for significant frontend changes.

Recommended gates:

- Claude A implements the frontend slice.
- Claude B reviews UX, safety language, accessibility, and visible quality.
- Codex B reviews frontend/backend contracts, integration boundaries, privacy, actionability/freshness semantics, and product-safety scope.
- Human stakeholder performs visual fidelity review when the design target is subjective.

Do not mark a redesign slice complete until the relevant review gate passes.

## What Not To Do

Do not:

- Paste prototype JavaScript into the app.
- Use `any` adapters to force mismatched data into TypeScript.
- Add fields to frontend types before backend contracts exist.
- Hide prototype placeholders as if they were real.
- Build broad dashboards from invented local constants without demo labels.
- Use CDN fonts without PM approval.
- Change backend behavior as a side effect of visual work.
- Collapse architecture review into visual review.
- Let a redesign create a second task source of truth outside `docs/shared/implementation_plan.md`.

## Follow-Up Backend Tasks

When a redesign reveals missing backend contracts, create follow-up backend tasks instead of inventing frontend data.

Common examples:

- Recent trade reviews list.
- Persisted agent-team runs.
- Reports list/detail endpoints.
- Portfolio context summary/detail endpoints.
- Readiness aggregate endpoint.
- User/profile display endpoint.
- Settings/preferences endpoint.

Until those tasks land, keep the frontend card visibly marked as demo/not connected.
