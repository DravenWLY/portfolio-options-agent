# LLM Provider Keys & Live Smoke Tests (Phase 25A)

Status: backend-only, opt-in. **Mock is the default.** Normal app behavior and
the default test suite make **no** live provider calls and need **no** keys.
Owner: Claude E. Boundary record: ADR 0008 / ADR 0005.

## Keys (`.env`, backend-only) — two separate keys

- `GOOGLE_API_KEY` — **Gemini** live provider. Free-tier / Flash friendly; the
  routine manual provider smoke path.
- `OPENAI_API_KEY` — **OpenAI** live provider (implemented). **Paid API usage.**

Rules: backend-only; never `VITE_*`; never bundle to the browser; never commit
real keys; never print or inspect key values; **no frontend provider/model
selection**.

> **Key handling (important):** the founder / local terminal may export
> `GOOGLE_API_KEY` and `OPENAI_API_KEY` however they prefer. **Agents and
> reviewers must not read, print, source, or inspect `.env`** (or the key
> values). All commands below **assume the relevant key is already exported** in
> the shell environment; do not paste a key inline (it lands in shell history).

`.env.example` lists **only the keys**. Internal knobs (`POA_LLM_MODE`,
`POA_LLM_PROVIDER`, `POA_LLM_MODEL`, `POA_LLM_TIMEOUT_SECONDS`,
`POA_LLM_MAX_RETRIES`, `POA_LLM_TOKEN_BUDGET_PER_RUN`,
`POA_LLM_RATE_LIMIT_FALLBACK`, `POA_LLM_LIVE_TESTS`, `POA_LLM_OPENAI_LIVE`)
remain backend defaults / test-only configuration and are intentionally not
normal setup requirements.

## Mock vs live

- **Default:** `MockLLMProvider` — no network, no key. `POA_LLM_MODE` defaults to
  `mock`. Neither Gemini nor OpenAI is ever the default.
- **Live (opt-in, backend-only):** Gemini or OpenAI via the app-owned
  `LLMProvider` Protocol and the ADR-0005 provider gate. Live output still passes
  the existing output-safety and `agent_eval` boundaries; output that trips
  safety degrades to a safe partial run (deterministic evidence survives).

## Provider SDKs (install once before a *real* live call)

Live provider SDKs are declared as the **`live-llm` optional-dependency extra** in
`backend/pyproject.toml` (PEP 621), kept **out of** the core dependencies on
purpose: mock is default, the default offline/mock test suite needs no provider
SDK, and the adapters import these lazily only when a live provider is explicitly
configured — so the base install and CI stay lean. Install them with one command
(from `backend/`):

```
./.venv/bin/pip install ".[live-llm]"
```

Without them, the adapter degrades safely to `provider_unavailable` and the smoke
test passes via the safe path **without** reaching the provider (a fast pass and
no real response is the tell). Any future provider SDK is added to the same
`live-llm` extra.

The smoke commands below assume the relevant key (`GOOGLE_API_KEY` /
`OPENAI_API_KEY`) is **already exported** in your shell — they contain no inline
key. Use your real key (not the literal `<...>` placeholder). How you export it is
your choice; agents/reviewers must not read or source `.env`.

## Dev-only Docker runtime for Agent Console

The default Compose backend image stays lean, offline, and mock-default. For
local development of the existing read-only Agent Console route with live
provider SDKs installed, use the explicit override:

```
docker compose -f docker-compose.yml -f docker-compose.live-llm.yml build backend
docker compose -f docker-compose.yml -f docker-compose.live-llm.yml up -d postgres backend
```

The override builds `portfolio-options-agent-backend:live-llm` with the
`live-llm` extra installed. It still defaults to `POA_LLM_MODE=mock`; live mode
only activates when backend env gates are explicitly configured in a private
`.env` or shell environment. Do not put API keys inline in commands. OpenAI is
paid; Gemini/Flash may hit quota or rate limits, and those provider failures are
handled as safe degradation.

## Gemini live smoke (free-tier friendly, routine)

`backend/tests/services/agent_team/test_gemini_live_smoke.py` is marked
`external`/`slow` (excluded from the default suite via `pytest.ini` `addopts`)
**and** skipped unless opted in. Gemini free tier / Flash models can still hit
rate limits — `rate_limited` / `quota_exceeded` / `provider_unavailable` are
treated as **safe, non-blocking** provider failures (deterministic evidence
survives, no secret/raw provider data leaks), not safety failures.

Requires `GOOGLE_API_KEY` already exported in the shell (no inline key):

```
cd backend
POA_LLM_LIVE_TESTS=1 \
  ./.venv/bin/python -m pytest tests/services/agent_team/test_gemini_live_smoke.py -m external -q
```

Uses synthetic data only; never logs the key. Asserts: a run state is produced;
output is live (not mock); `eval_flags` present; no forbidden private keys/values;
and broker-snapshot vs market-quote freshness stay separate.

## OpenAI live smoke (⚠️ PAID — requires explicit founder approval)

`backend/tests/services/agent_team/test_openai_live_smoke.py` makes a **paid**
OpenAI call. **Do not run it without explicit founder approval.** It is gated
more strictly than Gemini: `external`/`slow` marker exclusion **plus** BOTH
`POA_LLM_LIVE_TESTS=1` and the dedicated paid-usage acknowledgement
`POA_LLM_OPENAI_LIVE=1`, **plus** `OPENAI_API_KEY`. The extra
`POA_LLM_OPENAI_LIVE` gate ensures enabling the free-tier Gemini smoke never
triggers a paid OpenAI call by accident.

Requires `OPENAI_API_KEY` already exported in the shell (no inline key), plus the
two opt-in flags below — and **explicit founder approval** because it is paid:

```
cd backend
POA_LLM_LIVE_TESTS=1 POA_LLM_OPENAI_LIVE=1 \
  ./.venv/bin/python -m pytest tests/services/agent_team/test_openai_live_smoke.py -m external -q
```

Model: configurable via `POA_LLM_MODEL`; falls back to the adapter default
`gpt-4o-mini`. You may set e.g. `POA_LLM_MODEL=gpt-5-nano` if your account
supports it (no pricing claims here — check your own account/model availability).
Uses synthetic data only; never logs the key. Accepts safe terminal statuses
(`completed` / `partially_completed` / `failed_safe`) and handles
`safety_validation_failed` / `provider_auth_error` / `rate_limited` /
`quota_exceeded` / `provider_unavailable` safely.

## Boundaries

No frontend, routes, persistence, DB, Agent Console composer, MCP, LangGraph,
**OpenAI Agents SDK**, or TradingAgents. The OpenAI path uses only the plain
OpenAI chat client behind the app-owned `LLMProvider` Protocol. Deterministic
services own all metrics. The runner sends only sanitized, tier-scoped evidence
to a provider — **never** raw private brokerage/account data.
