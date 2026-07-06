# Phase 34A-T10 — Live Gemini Model Selection / Quota-Avoidance Design

Status: design/review only (no implementation). Proposed task ids: T10 (this
design), T10A (Codex C backend slice).
Owner: Claude E. Reviewer: Codex B. Stop for Codex B review before coding.
Inputs: `provider_config.py`, `provider_factory.py`, `google_provider.py`,
`tool_mediated_report.py` (live seam), `test_gemini_live_smoke.py`,
`test_tool_mediated_route_live_smoke.py`; `../TradingAgents` v0.3.0
(`llm_clients/factory.py`, `model_catalog.py`, `default_config.py`,
`dataflows/interface.py` vendor routing) as reference only — nothing copied,
nothing modified.

Hard boundaries honored throughout: the LLM never chooses its model or tools;
validators untouched; no prompts/responses/keys in saved artifacts or logs;
no frontend; no LangGraph; no provider/source expansion beyond what is
already approved (google/openai).

---

## 1. Diagnosis — why one quota issue took down all five roles

1. **One resolution, one model, whole run.** `resolve_llm_provider` builds a
   single provider object bound to a single model; `run_tool_mediated_agent_team`
   uses that same object for every role sequentially. All role calls share one
   API key **and one model**, so they draw from the same per-model quota
   bucket. When `gemini-2.0-flash` returned `RESOURCE_EXHAUSTED`
   (`_google_client_error_status` → `quota_exceeded`), every subsequent role
   call hit the same exhausted bucket. Degradation was correct (deterministic
   floor preserved, roles marked unavailable — exactly the designed fail-safe)
   but total.
2. **No chain, no circuit breaker.** There is no second candidate to advance
   to, and each role still attempts the dead model, burning latency on four
   predictable failures.
3. **The standalone smoke's `provider_unavailable`** is consistent with one of
   two causes on the same path: `google.genai` import failure in
   `_build_default_client` (the `live-llm` extra not installed in that venv),
   or an unrecognized SDK error falling through `_google_client_error_status`'s
   default branch — both map to `provider_unavailable`. Worth one diagnostic
   re-run with the extra confirmed installed before blaming access.
4. **Stale default.** `DEFAULT_LIVE_MODEL = "gemini-1.5-flash"`
   (`provider_config.py:19`) is a retired model id; anyone running live
   without `POA_LLM_MODEL` set gets a guaranteed failure. Needs a refresh to a
   founder-verified current id regardless of everything else.

The founder's usage pattern (separate quota buckets per Gemini model) is
exactly the property an **ordered model chain** exploits: same provider, same
key, different buckets.

## 2. TradingAgents comparison (reference only)

| TA v0.3.0 pattern | What it does | Verdict for Portfolio Copilot |
| --- | --- | --- |
| Two-tier model config (`quick_think_llm` / `deep_think_llm`) | Cheap model for analysts, strong model for Research Manager/PM; per-tier, not per-role | The right *eventual* shape for role routing — defer (§4) |
| Env precedence (`TRADINGAGENTS_*` → config) | Env overrides config cleanly | Already how `POA_LLM_*` works — keep |
| **Vendor chain semantics** (`data_vendors`: "the configured value IS the exact chain — requests are NOT silently routed to vendors you didn't choose; for ordered fallback, list several") | Explicit ordered fallback; `VendorRateLimitError` → skip to next; per-vendor failures logged, not hidden | **Adopt — this is the model.** Applied to *models within one provider* rather than data vendors |
| Behavior-typed error taxonomy (`VendorError` sized by router reaction) | Retryable vs not decided by type | Already present as `LLMProviderStatus`; reuse for the retryable-status set |
| Model catalog with CLI dropdowns + "Custom model ID" | Interactive selection | Reject — no CLI product; backend env config only |
| Catalog warning about version-less auto-upgrading aliases | Aliases shift behavior when the vendor rotates the backing model | Adopt the *lesson*: candidates should be **versioned model ids**, frozen per role in `provider_runs`, so readback stays reproducible |
| Per-agent LLM objects bound at graph build; temperature exposure | Flexibility for prompt experimentation | Reject — PC keeps one gated provider seam, `temperature=0.0` |
| No LLM-model quota fallback (only data-vendor fallback + client retries) | — | PC would actually go one useful step further by chaining models |

## 3. Recommended architecture — **Option A: global ordered model fallback (chain), single provider, backend-only**

**Implement A now. Defer B (per-role routing). Not C, not D.**

### 3.1 Configuration

- New backend-only env: `POA_LLM_MODEL_CANDIDATES` — comma-separated ordered
  list of model ids for the configured provider, e.g.
  `POA_LLM_MODEL_CANDIDATES=gemini-3-flash,gemini-2.5-flash-lite,gemini-3.1-flash-lite`
  (exact ids to be founder-verified against the current Gemini lineup).
- Semantics (TA vendor-chain rule, verbatim in spirit): **the configured list
  IS the chain** — no silent additions, no provider mixing, order is priority.
- Precedence: if `POA_LLM_MODEL_CANDIDATES` is set, it defines the chain and
  `POA_LLM_MODEL` is ignored (config snapshot records both); if unset, chain =
  `[POA_LLM_MODEL]` — existing behavior, byte-identical.
- Parsing: trim, drop empties, dedupe preserving order, cap at 4 candidates
  (config error beyond that). All models must be plain ids (same validation
  as `model` today). Chain applies to the single configured provider only;
  a google+openai mixed chain is explicitly out of scope (Codex B decision D4).
- Refresh `DEFAULT_LIVE_MODEL` to a current founder-verified id in the same
  slice (it is a latent failure today).

### 3.2 Runtime behavior (`ChainedLLMProvider`)

A provider-layer wrapper implementing the existing `LLMProvider` protocol,
wrapping N `GoogleGeminiLLMProvider` (or OpenAI) instances in candidate
order. The runner, prompts, validators, and role logic are untouched — the
chain is invisible above the provider seam, which also preserves "the LLM
never chooses its model."

Per `complete()` call:

1. Try the current candidate (start = chain position 0).
2. On a **retryable availability status** — `quota_exceeded`, `rate_limited`,
   `provider_unavailable`, `provider_timeout` — advance to the next candidate
   and retry the same request once per remaining candidate.
3. On `provider_auth_error` — **abort the chain** (one key; auth failure hits
   every candidate; do not burn attempts).
4. On `safety_validation_failed` or any downstream hard block — **never
   retry with another model.** Unsafe output is a content problem, not an
   availability problem; model-shopping past safety failures is prohibited.
   (`invalid_response` — empty/malformed text — is proposed as retryable
   since no unsafe content exists; Codex B decision D2 confirms the exact
   split.)
5. **Sticky forward-only index per run:** when candidate *k* fails on
   availability, later roles in the same run start at *k+1* — exhausted
   buckets are not re-tried role after role (fixes the four-predictable-
   failures latency). The index never moves backward within a run.
6. All candidates exhausted → return the last availability failure; the
   existing role degradation path takes over unchanged (deterministic floor,
   `live_provider_*` warning codes).

Timeouts stay per-attempt (`timeout_seconds`); worst-case added latency is
bounded by (candidates − 1) extra attempts across the whole run thanks to the
sticky index. `max_retries` keeps meaning per-candidate transport retries,
distinct from chain advancement.

### 3.3 Freeze metadata (`provider_runs`) — reproducibility

Already frozen per role: `provider`, `model`, `prompt_version`, `status`,
tokens, `estimated_cost`, `is_mock` — so the model that actually authored
each role's prose is already recorded. Additive fields proposed (Codex B
decision D1, artifact vocabulary):

- `model_chain_position: int | None` — 0-based index of the serving model in
  the configured chain;
- `attempted_models: tuple[str, ...]` — model ids tried for this role in
  order, ending with the serving (or final failing) model. Model ids are safe
  metadata — never keys, prompts, or payloads.

Config `public_snapshot()` additionally reports `model_candidates` (names
only). Saved reports and logs gain no secrets, no prompts, no raw responses.

### 3.4 Per-role model routing (Option B) — defer, with a named trigger

Premature now: PM synthesis is deterministic in M1, role prose is one
connective sentence post-T9B, so there is no quality gradient to exploit —
only added config surface and eval matrix growth. Revisit (as a T-numbered
design task) when either trigger fires: (a) per-role token/cost data from
frozen `provider_runs` shows a meaningfully expensive role, or (b) a future
slice gives risk/PM materially longer live prose. The eventual shape is TA's
two-tier split (lite model for public roles, stronger for risk/PM) expressed
as backend config — never per-request.

## 4. Answers to the numbered questions

1. Single resolution → one model+key for all roles; per-model quota bucket
   exhausted ⇒ every role's call fails identically; degradation correct but
   total (§1).
2. **Ordered model fallback now; per-role routing deferred** (§3.4).
3. Global, backend env only, resolved once per run; never per-request, never
   client-supplied, never LLM-chosen. Per-run chain progression (sticky
   index) is runtime state, not config.
4. Chain advances only on availability statuses; auth aborts; safety failures
   never advance (§3.2 — the founder's example sequence is exactly the
   intended behavior for `quota_exceeded`).
5. Serving model per role (already frozen) + additive `model_chain_position`
   and `attempted_models` (§3.3).
6. Injected fake clients scripted per model — no live keys (§5).
7. Yes — `POA_LLM_MODEL_CANDIDATES` exactly as proposed, read by config
   loading, honored by both smokes.
8. Premature — defer with the two named triggers (§3.4).
9. Adopt: explicit chain semantics, behavior-typed retryability, versioned
   model ids, env precedence. Reject: CLI catalogs/dropdowns, auto-upgrading
   aliases, per-agent LLM binding, temperature exposure, and everything
   signal/decision-shaped (§2).

## 5. Test plan

**Offline (default CI, injected fakes, no keys):**

| ID | Case | Assertion |
| --- | --- | --- |
| M1 | Chain advance | candidate1 → `quota_exceeded`, candidate2 → ok ⇒ role completes; `provider_runs` records serving model, `model_chain_position=1`, `attempted_models=(c1,c2)` |
| M2 | Sticky index | role1 exhausts c1; roles 2–4 call c2 directly (fake counts prove c1 called exactly once) |
| M3 | Auth abort | c1 → `provider_auth_error` ⇒ no further candidates tried; roles degrade with existing warning codes |
| M4 | Safety no-shop | c1 returns advice/invented-metric content ⇒ hard block, **no** c2 attempt, deterministic floor intact, eval flag recorded |
| M5 | All-exhausted | every candidate `quota_exceeded` ⇒ behavior identical to today's single-model quota failure (floor + `live_provider_quota_exceeded`) |
| M6 | Config parsing | trim/dedupe/cap-4/empty-item handling; candidates-set ⇒ `POA_LLM_MODEL` ignored; candidates-unset ⇒ byte-identical legacy behavior |
| M7 | Freeze/readback | saved report readback shows chain metadata without re-running provider; artifact validators accept the additive fields |
| M8 | No-secret sweep | `find_secret_like_values` / forbidden-key checks over config snapshots and frozen artifacts with chain fields present |

**Live smoke retry plan (opt-in, founder-authorized, synthetic evidence):**

1. Re-run the standalone Gemini smoke with the `live-llm` extra confirmed
   installed to disambiguate the `provider_unavailable` cause (§1.3).
2. Re-run both smokes with `POA_LLM_MODEL` set to one founder-verified
   current model to re-establish a single-model baseline.
3. After T10A lands: run the route-backed smoke with
   `POA_LLM_MODEL_CANDIDATES=<founder's three models>` and, if quota permits,
   deliberately pick a first candidate known to be near quota to observe a
   real chain advance; verify frozen `attempted_models` in the saved report
   readback. Disposable DB, no `.env` reads, key via the same temporary
   bridge pattern as T7D, torn down after.

## 6. Exact Codex C implementation prompt

```text
Agent: Codex C
Task: P34A-T10A - Ordered Gemini model-candidate fallback for the live Agent Team
Mode: backend implementation; one task; stop for Codex B review after.

Design reference: docs/claude-e-agentic/PHASE_34A_T10_LIVE_MODEL_SELECTION_QUOTA_DESIGN.md
(sections 3 and 5, binding).

Scope (backend only; no frontend, schema/read-contract, runner, prompt, or
validator changes):

1. provider_config.py: parse POA_LLM_MODEL_CANDIDATES (comma-separated, trim,
   drop empties, dedupe preserving order, cap 4, same per-model validation as
   POA_LLM_MODEL; configuration error on violation). If set, it defines the
   ordered chain and POA_LLM_MODEL is ignored; if unset, chain =
   [POA_LLM_MODEL] with behavior byte-identical to today. Add model_candidates
   (names only) to public_snapshot(). Refresh DEFAULT_LIVE_MODEL from retired
   "gemini-1.5-flash" to the founder-verified current id recorded in the
   design review.
2. provider_factory.py: when the chain has >1 candidate, resolve a
   ChainedLLMProvider implementing the existing LLMProvider protocol over
   per-candidate provider instances (same provider name and key for all).
   Chain rules (binding): advance to the next candidate only on
   quota_exceeded, rate_limited, provider_unavailable, provider_timeout, and
   (if Codex B confirms D2) invalid_response; abort the whole chain on
   provider_auth_error; NEVER advance past safety_validation_failed or any
   hard-blocked content; sticky forward-only candidate index shared across a
   run (later roles start at the last-serving candidate); all-exhausted
   returns the final availability failure so existing role degradation is
   unchanged.
3. Freeze metadata: additive per-role provider_runs fields
   model_chain_position (int, 0-based) and attempted_models (tuple of model id
   strings, in order). No prompts, responses, keys, or raw payloads. Update
   validate_saved_tool_freeze_payload allowlists only as needed for the two
   additive fields.
4. Live smokes: test_gemini_live_smoke.py and
   test_tool_mediated_route_live_smoke.py read POA_LLM_MODEL_CANDIDATES when
   set (fall back to POA_LLM_MODEL); print only model ids/statuses, never
   prompts/keys.
5. Tests: implement offline cases M1-M8 from the design memo section 5 using
   injected fake clients scripted per model id (no live calls, no keys, no
   .env). Existing suites must pass unmodified in single-model mode.

Boundaries: LLM never selects model/tools; no validator weakening; no
advice/execution wording anywhere; no secrets/prompts/traces in artifacts,
snapshots, or test output; no new providers/sources; no LangGraph/MCP/
TradingAgents; saved readback stays frozen and never re-runs providers.

Verification: cd backend && pytest (report counts for provider config/factory
suites, test_tool_mediated_report.py, test_tool_mediated_eval.py, report
schema tests); git diff --check.

Return per docs/shared/AGENT_REPORT_FORMAT.md with PASS/BLOCKED ask for Codex B.
```

## 7. Codex B decisions needed before implementation

- **D1** — approve additive `provider_runs` fields `model_chain_position` +
  `attempted_models` in the frozen artifact vocabulary (reproducibility
  metadata, names only).
- **D2** — confirm the retryable-status set; specifically whether
  `invalid_response` may advance the chain (recommended yes) while
  `safety_validation_failed` never does (non-negotiable).
- **D3** — approve the candidates cap (4) and the `POA_LLM_MODEL_CANDIDATES`
  ⇒ `POA_LLM_MODEL`-ignored precedence rule.
- **D4** — confirm single-provider chains only (no google↔openai mixing) for
  this slice.
- **D5** — founder verifies the exact current Gemini model ids for the
  default and the smoke chain (design deliberately avoids hardcoding them
  from memory).
