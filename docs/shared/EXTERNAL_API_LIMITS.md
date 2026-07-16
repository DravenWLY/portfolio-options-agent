# External API Limits And Runtime Guardrails

Official-documentation research date: 2026-07-16

This memo separates three different facts that must not be conflated:

1. **Provider-documented limit** - a limit or restriction published by the
   provider on an official page.
2. **App-enforced budget** - a smaller limit enforced by Portfolio Copilot code.
3. **Runtime observation** - behavior seen during an authorized run. No provider
   API was called or probed to prepare this memo, so there are no new runtime
   observations here.

Provider limits change. Before a live run, check the linked official page and,
where applicable, the provider dashboard for the active project or account.
Never place secret values, account identifiers, or private provider responses in
this document.

## SEC EDGAR

**Use and code lane**

- Company-profile metadata and recent-filing metadata for the saved-report
  public-evidence projection.
- Runtime boundary:
  `backend/app/services/reports/public_evidence.py`.
- Route resolution is all-or-nothing: both approved EDGAR metadata lanes must
  be configured before either lane is made available.

**Authentication or identification**

- EDGAR public data needs no API key.
- Automated requests must declare a descriptive User-Agent through
  `SEC_EDGAR_USER_AGENT`.
- Enablement is backend-only through `POA_EDGAR_REPORT_EVIDENCE_MODE`.

**Provider-documented limit and restrictions**

- Official documentation checked: 2026-07-16.
- SEC limits automated access to no more than **10 requests per second** in
  total and may temporarily limit an IP that exceeds the threshold.
- Automated access must follow SEC fair-access and security guidance and use a
  declared User-Agent.
- Official references:
  [SEC accessing EDGAR data and fair-access guidance](https://www.sec.gov/os/accessing-edgar-data),
  [SEC rate-control notice](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits),
  [SEC data APIs](https://data.sec.gov/), and
  [SEC developer resources](https://www.sec.gov/developer).

**App-enforced budget**

- `P36_EDGAR_MAX_REQUESTS_PER_SECOND = 1`, one tenth of the published ceiling.
- Shared process budget: `P36_EDGAR_DAILY_REQUEST_BUDGET = 60` requests per UTC
  day.
- Each lane has `request_budget_per_run = 2`: ticker-directory lookup plus one
  submissions request. With both independent clients active, one report can
  make at most **4 EDGAR HTTP requests**.
- Timeout: 5 seconds per request; response cap: 1,000,000 bytes; no retry loop.
- Only normalized identity and filing metadata are frozen. Raw URLs, paths,
  accession data, filing bodies, and provider payloads are discarded.

**Headroom**

- The app's one-request-per-second ceiling is 90% below SEC's documented
  10-request-per-second ceiling. A four-request report is serialized by that
  process throttle; the 60-request daily cap is app-owned, not an SEC-published
  daily quota.

**Current safeguards**

- Default off; incomplete policy or client construction disables both lanes
  before any source call.
- One-request-per-second process throttle, daily counter, per-run counter,
  normalized-field allowlists, frozen readback, and fail-closed unavailable
  sections.

**Future improvement**

- Share the ticker-directory and submissions response between the two approved
  lanes so one report needs two source requests rather than four. Preserve the
  current normalized-only freeze and last-known-safe failure behavior.

## Financial Modeling Prep (FMP)

**Use and code lanes**

- Active approved lane: end-of-day OHLCV history used to freeze market context
  for deterministic calculations.
- Optional local/internal lane: company-profile classification for the
  deterministic exposure review. It is a separate, cached-per-symbol FMP call,
  not an Agent Team evidence lane.
- Dormant lane: normalized reported-statement fundamentals; no route-ready live
  client is currently enabled.
- Runtime boundaries:
  `backend/app/services/market_data/eod_history.py` and
  `backend/app/services/trade_review/exposure_engine.py`, with the dormant
  statement provider in `backend/app/services/reports/source_snapshots.py`.
- `backend/app/services/economic_calendar.py` also contains an unselected FMP
  calendar helper; the current refresh route selects the FRED runner instead.

**Authentication or identification**

- Backend API key: `FMP_API_KEY`.
- EOD enablement: `POA_MARKET_CONTEXT_MODE`.
- Company-profile classification uses the same `POA_MARKET_CONTEXT_MODE` gate.
- Fundamentals enablement: `POA_FMP_FUNDAMENTALS_MODE`.
- Fundamentals daily cap: `P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET`.

**Provider-documented limit and restrictions**

- Official documentation checked: 2026-07-16. The pricing page lists **250
  calls per day** plus end-of-day and profile/reference data for its Basic row.
  It separately lists **500 MB per trailing 30 days** for its Free plan. The
  code cannot establish which label or entitlement applies to any account.
- Endpoint availability, history range, symbol coverage, and fundamentals
  access are plan-specific. Free-tier or Basic-tier fundamentals coverage is
  **not confirmed in public official documentation for this project** and must
  be verified before activation.
- Display or redistribution may require a separate FMP data-display and
  licensing agreement.
- Official references:
  [FMP pricing and plan comparison](https://site.financialmodelingprep.com/developer/docs/pricing),
  [FMP API quickstart](https://site.financialmodelingprep.com/developer/docs/quickstart), and
  [FMP terms](https://site.financialmodelingprep.com/developer/docs/terms-of-service).

**App-enforced budget**

- EOD: normally one request per symbol and saved package, cached in the package
  execution context; hard cap 2 requests per run; 15-second timeout; 512,000
  byte response cap; no retry loop; up to 260 normalized daily bars.
- Company-profile classification: at most 30 requests per review context, one
  per unique single-name symbol; successful and unavailable classifications are
  cached in that context. Timeout is 15 seconds, response cap is 256,000 bytes,
  and there is no retry loop.
- Fundamentals: three source operations per uncached symbol (income statement,
  balance sheet, cash flow); the saved-package provider caches each symbol and
  has a 10-request UTC-day process cap. It retains two comparable fiscal
  periods. The lane is dormant until a reviewed live client and endpoint-access
  check exist.
- The unselected FMP economic-calendar helper has no route-selected operational
  budget. It must not be treated as an enabled source path.

**Headroom**

- If, and only if, the documented 250-calls-per-day Basic limit applies, the
  EOD cap is 0.8% of it and the classification cap is 12%. Their independent
  maximums sum to 32 calls (12.8%) in one day. The dormant fundamentals cap is
  4%. These are arithmetic comparisons, not proof of endpoint entitlement.

**Current safeguards**

- All active FMP paths default off and require explicit backend mode plus a
  configured client/key. Fundamentals has no production HTTP client.
- Normalization occurs before an evidence freeze; raw FMP payloads and URLs are
  not saved. Classification failure returns no guessed sector/industry label.
- Missing, malformed, denied, or rate-limited evidence becomes an honest
  unavailable section. No fallback source is selected silently.

**Future improvement**

- Add process-wide EOD reuse keyed by symbol and as-of date, and retain the
  existing once-per-package freeze. Before fundamentals activation, run one
  explicit opt-in endpoint-access check and record plan coverage without
  recording provider content.

## Google Gemini

**Use and code lane**

- Optional live LLM provider for bounded Agent Team role analysis and PM
  synthesis. The backend remains responsible for evidence selection,
  calculations, output validation, and frozen readback.
- Runtime boundary: `backend/app/services/agent_team/llm_clients/` plus the
  bounded loops in
  `backend/app/services/agent_team/orchestration/tool_mediated_runner.py`.

**Authentication or identification**

- Backend API key: `GOOGLE_API_KEY`.
- Backend-only controls include `POA_LLM_MODE`, `POA_LLM_PROVIDER`,
  `POA_LLM_MODEL`, `POA_LLM_MODEL_CANDIDATES`,
  `POA_LLM_TIMEOUT_SECONDS`, `POA_LLM_MAX_RETRIES`, and
  `POA_LLM_TOKEN_BUDGET_PER_RUN`.

**Provider-documented limit and restrictions**

- Official documentation checked: 2026-07-16.
- Gemini evaluates usage by requests per minute (RPM), input tokens per minute
  (TPM), and requests per day (RPD). Limits are per project, not per API key;
  RPD resets at midnight Pacific time.
- Active limits vary by model, project, and usage tier. Google directs users to
  AI Studio for the current per-model values and states that specified limits
  are not guaranteed. Therefore this memo does not hardcode RPM/TPM/RPD values
  that may not match the founder's active project.
- Free and preview-model limits are more constrained. A `429
  RESOURCE_EXHAUSTED` indicates a quota or rate boundary.
- Official references:
  [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits),
  [Gemini models](https://ai.google.dev/gemini-api/docs/models), and
  [Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key).

**App-enforced budget and declared configuration**

- Design constants declare a typical budget of 10 logical LLM calls and a
  nominal hard cap of 19. The current per-role loop bounds allow at most 14
  logical calls (risk 3 + three public roles at 3 each + PM 2), so the current
  graph stays below 19 by construction; there is not yet a shared run-wide call
  counter.
- Risk: at most 3 provider calls, 2,000 output tokens per call, and 90 seconds.
- Each public role: at most 3 provider calls, 2,000 output tokens per call, and
  90 seconds.
- PM: at most 2 provider calls, 1,600 output tokens per call, and 60 seconds.
- The role ceilings reserve at most 27,200 output tokens in aggregate. The
  provider config also declares a default 4,000-token run budget, but the runner
  does not consume that config value today; it must not be treated as an
  enforced global token ceiling.
- Provider config declares a 30-second timeout and zero retries. The Google
  adapter currently does not pass either setting into the SDK call, so they are
  intended settings rather than proven transport limits. There is no app-owned
  retry loop, but SDK-internal behavior is not pinned by this code.
- The code default live model is `gemini-2.5-flash-lite`. The ordered candidate
  chain is deployer configuration and was intentionally not inspected; code
  allows at most four distinct same-provider candidates.
- The 19-call cap counts logical provider completions. A model-candidate chain
  can make more than one HTTP attempt for one logical completion when an
  availability-shaped failure advances the chain; this network-attempt total is
  not separately capped today.

**Headroom**

- A numeric comparison is not possible without the active project's per-model
  RPM, TPM, RPD, and spend limits. Admission must therefore confirm capacity for
  at least 14 logical calls and the role token ceilings; the nominal 19-call cap
  does not bound candidate-chain network attempts.

**Current safeguards**

- Mock by default; live mode requires explicit backend configuration and key
  availability.
- Same-provider ordered model chain only; auth and safety failures do not shop
  across models; exhausted models are skipped for later roles through a sticky
  forward-only index.
- Sanitized prompts, backend-owned citations, strict output gates,
  deterministic fallback, no provider payload persistence, and no provider
  re-run on saved readback.

**Future improvement**

- Wire the timeout and retry policy explicitly into the Google SDK, enforce the
  configured global token and call budgets, and add a run-wide network-attempt
  counter across the model chain. Add quota-aware scheduling from safe response
  metadata. Keep project-specific active quotas in an operator checklist rather
  than source control.

## OpenAI

**Use and code lane**

- Optional paid live LLM provider behind the same app-owned provider protocol.
  It is not the default provider and is not used by normal tests.
- Runtime boundary: `backend/app/services/agent_team/llm_clients/openai.py` and
  the same bounded Agent Team runner.

**Authentication or identification**

- Backend API key: `OPENAI_API_KEY`.
- The same `POA_LLM_*` controls apply, with `POA_LLM_PROVIDER=openai`.

**Provider-documented limit and restrictions**

- Official documentation checked: 2026-07-16.
- All API use is rate-limited. Active request/token limits depend on model,
  project, organization, and paid usage tier and must be checked on the
  platform Limits page.
- Responses expose rate-limit headers such as request/token limits, remaining
  capacity, and reset times. This app does not currently persist those headers.
- Official references:
  [OpenAI rate-limit overview](https://help.openai.com/en/articles/5955598),
  [OpenAI rate-limit practices](https://help.openai.com/en/articles/6891753), and
  [OpenAI API reference](https://platform.openai.com/docs/api-reference).

**App-enforced budget and declared configuration**

- Same P36 structure as Gemini: nominal typical 10 and hard cap 19; the current
  per-role bounds allow at most 14 logical calls.
- OpenAI receives the configured timeout (default 30 seconds). The config
  declares zero retries, but the adapter does not pass `max_retries` into the
  OpenAI SDK, so SDK-default retry behavior may still occur.
- The configured 4,000-token run budget is not consumed by the runner; enforced
  per-role output ceilings total at most 27,200 tokens. At most four explicitly
  configured OpenAI model candidates are allowed.
- The code default model is `gpt-4o-mini`. Any ordered candidate chain is
  deployer configuration and was intentionally not inspected.

**Headroom**

- A numeric comparison is not possible without the active project's model and
  usage-tier limits. Before a run, confirm capacity for at least 14 logical
  calls and the role token ceilings; candidate-chain network attempts are not
  separately capped.

**Current safeguards**

- Live use is explicit and backend-only. Missing credentials fail closed.
- Raw exceptions, responses, request bodies, prompts, and keys are not frozen.
- Rate limits and provider failures preserve deterministic evidence and produce
  partial, safely labeled output.

**Future improvement**

- Pass an explicit retry setting to the SDK, enforce the global call/token
  budgets, and read safe rate-limit response headers into ephemeral scheduling
  state. Add bounded jittered backoff only after a separate retry contract. Do
  not add automatic paid-provider fallback from Gemini.

## FRED

**Use and code lane**

- The report-evidence lane defines six approved macro series in
  `backend/app/services/reports/source_snapshots.py`. It is default off and has
  no wired production HTTP client, so it remains dormant pending founder
  activation and source review.
- A separate explicit local economic-calendar refresh uses
  `FredEconomicCalendarHttpClient` in
  `backend/app/services/economic_calendar.py`, reached only through the
  protected `POST /economic-calendar/refresh` route in
  `backend/app/api/routes/economic_calendar.py` when the backend has a key.
  Normal reads otherwise use a restored snapshot or synthetic fixture.

**Authentication or identification**

- Backend API key: `FRED_API_KEY`.
- Enablement: `POA_FRED_MACRO_SERIES_MODE`.
- Daily cap: `P36_FRED_SERIES_DAILY_REQUEST_BUDGET`.

**Provider-documented limit and restrictions**

- Official documentation checked: 2026-07-16.
- FRED requires a registered API key. The official terms reserve the right to
  impose or change transaction and bandwidth limits; the error documentation
  identifies HTTP 429 for rate limiting but does not publish a stable numeric
  ceiling.
- Third-party copyrighted series retain their own restrictions. Public use
  requires the FRED non-endorsement notice specified by the terms.
- Official references:
  [FRED API terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html),
  [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html), and
  [FRED API errors](https://fred.stlouisfed.org/docs/api/fred/errors.html).

**App-enforced budget**

- Report evidence: six source requests per uncached saved package, one per
  approved series; process cap 18 per UTC day; two labeled observations per
  series; package-local reuse. There is no wired runtime client, timeout, or
  retry loop for this dormant lane.
- Economic-calendar refresh: seven configured release-specific requests are
  expected for a non-paginated annual refresh. Each page has a 15-second
  timeout, 1.1-second minimum interval, and up to two retries on throttling.
  Pagination is not globally capped, so an unusually large response can exceed
  seven requests; this path has no app-owned daily or total request counter.
- The refreshed calendar stores normalized records and preserves the last-good
  snapshot when no usable refresh is produced.

**Headroom**

- FRED does not publicly publish a stable numeric ceiling, so numerical
  headroom cannot be calculated. The report lane's 18-per-day cap and the
  calendar interval/retry settings are app choices, not provider quotas.

**Current safeguards**

- The report lane is default off, uses an injected-client boundary and an
  approved-series allowlist, and freezes normalized-only evidence with an
  honest unavailable state and no fallback source.
- The calendar route is unconfigured without `FRED_API_KEY`; its client
  sanitizes transport failures and 429s, includes FRED's required
  non-endorsement notice in its normalized snapshot, and does not expose raw
  provider payloads.

**Future improvement**

- Give the calendar refresh an explicit total/daily request counter and bounded
  pagination, then add a reviewed report-evidence client with the same
  constraints. Review each series for third-party copyright before user-facing
  activation.

## SnapTrade

**Use and code lane**

- Read-only brokerage connection management and account snapshot sync.
- Runtime boundaries:
  `backend/app/services/broker_import/providers/snaptrade_sdk_client.py`,
  `backend/app/services/broker_import/refresh_connections.py`, and
  `backend/app/services/broker_import/sync.py`.

**Authentication or identification**

- Backend integration credentials: `SNAPTRADE_CLIENT_ID` and
  `SNAPTRADE_CONSUMER_KEY`.
- Environment and encryption controls: `SNAPTRADE_ENVIRONMENT` and
  `SNAPTRADE_SECRET_ENCRYPTION_KEY`.
- Per-user provider credentials remain encrypted backend data; they are never
  frontend configuration.

**Provider-documented limit and restrictions**

- Official documentation checked: 2026-07-16.
- Customer-level default: **250 requests per minute** across the client ID.
- Personal-account data endpoints also have a default **10 requests per minute
  per account** rolling limit. A request must pass both limits.
- SnapTrade recommends background Holdings polling no more than four times per
  day per user and Activities no more than once per account per 24 hours.
- Official references:
  [SnapTrade rate limiting](https://docs.snaptrade.com/docs/ratelimiting),
  [SnapTrade launch guide](https://docs.snaptrade.com/docs/launch-guide), and
  [SnapTrade authentication terminology](https://docs.snaptrade.com/docs/terminology).

**App-enforced operation budget**

- Connection refresh: one list-connections request plus one list-accounts
  request for each returned connection.
- Account sync: three account-data requests - balances, equity positions, and
  option holdings. The current `refresh_account` method is a local completion
  record and makes no provider request.
- The app does not currently define an explicit SnapTrade per-run counter,
  timeout, retry, or reset-header backoff policy above the SDK boundary.

**Headroom**

- One account sync makes three account-data calls, leaving seven of the
  documented 10-per-minute Personal-account bucket if no concurrent request
  uses that account. It uses 1.2% of the 250-per-minute client bucket in
  isolation; the app has no scheduler that reserves this headroom globally.

**Current safeguards**

- Read-only connection type, manual sync route, one active sync per account,
  backend-only credentials, normalized persistence, sanitized provider errors,
  and fail-closed 503 behavior when the integration is incomplete.

**Future improvement**

- Add an app-owned request budget and explicit timeout, capture only safe
  rate-limit reset metadata, and schedule account refreshes across users instead
  of polling one account repeatedly.

## Nasdaq Trader Symbol Directory

**Use and code lane**

- Public symbol-reference snapshot for ticker/name/exchange lookup. It does not
  provide quotes, positions, trade eligibility, or recommendations.
- Runtime boundary: `backend/app/services/symbol_directory.py`.

**Authentication or identification**

- No API key. The HTTP client uses an app User-Agent.
- Optional startup refresh flag: `SYMBOL_DIRECTORY_REFRESH_ON_STARTUP`.

**Provider-documented limit and restrictions**

- Official documentation checked: 2026-07-16.
- Nasdaq documents the public symbol-directory files and states that they are
  updated periodically during the day. It does not publish a numeric request
  rate for these public files on the directory page.
- The Symbol Lookup page states that Nasdaq Fund Network data is for internal
  non-commercial use unless separately licensed. This app's default source is
  the general `nasdaqtraded.txt` directory, not the mutual-fund directory, but
  future source additions must re-check licensing.
- Official references:
  [Nasdaq symbol-directory definitions](https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs)
  and [Nasdaq Symbol Lookup](https://www.nasdaqtrader.com/trader.aspx?id=symbollookup).

**App-enforced operation budget**

- Default refresh fetches one file: `nasdaqtraded.txt`.
- Startup refresh is disabled unless explicitly enabled. A valid persisted or
  in-memory snapshot younger than one day suppresses the fetch.
- HTTP timeout: 15 seconds; no retry loop; failed refresh preserves the last-good
  normalized snapshot.

**Headroom**

- Nasdaq Trader does not publish a numeric request ceiling for the directory
  files, so numerical headroom is not confirmed in public official
  documentation. The app's once-per-day freshness rule is a conservative local
  cadence, not a provider guarantee.

**Current safeguards**

- Optional/manual refresh, one-day cache, normalized parsing, atomic last-good
  activation, sanitized errors, and no app-startup failure on source outage.

**Future improvement**

- Add conditional HTTP requests if Nasdaq exposes stable validators, retain a
  strict once-per-day ceiling, and separately review licensing before enabling
  more directory families.

## Pre-Run Summary

| Provider | Current lane status | Authentication / identification | Documented limit | Current per-run usage | Primary safeguard | Scale-up action |
| --- | --- | --- | --- | --- | --- | --- |
| SEC EDGAR | Approved; default off | `SEC_EDGAR_USER_AGENT` | 10 requests/sec; fair access | Up to 4/report; 1/sec, 60/day, 5 sec, no retry | All-or-nothing resolver and frozen normalized metadata | Share ticker/submissions lookups |
| FMP | EOD/classification opt-in; fundamentals and calendar helper dormant | `FMP_API_KEY` | Basic 250 calls/day; Free 500 MB/30 days; entitlement plan-specific | EOD max 2/report; classification max 30/review; fundamentals max 10/day | Default-off gates, caches, normalization, no guessed classification | Confirm plan coverage; add process-wide cache |
| Gemini | Optional live; mock default | `GOOGLE_API_KEY` | Per-project, per-model, tier-specific RPM/TPM/RPD | Max 14 logical role calls; up to 27,200 role output tokens; max 4 candidates | Explicit live gate, same-provider chain, output gates | Enforce global call/token and network-attempt caps |
| OpenAI | Optional paid live; mock default | `OPENAI_API_KEY` | Project/model/usage-tier-specific | Max 14 logical role calls; up to 27,200 role output tokens; max 4 candidates | Explicit live gate and deterministic partial fallback | Pin SDK retries; capture safe headers |
| FRED | Calendar refresh explicit; report-evidence lane dormant | `FRED_API_KEY` | Numeric ceiling not publicly fixed; 429 when limited | Calendar normally 7 pages, 15 sec/1.1 sec/2 retries; report lane 6/package, 18/day | Unconfigured route fails safe; normalized snapshots/last good | Bound pagination and add total/daily budget |
| SnapTrade | Read-only manual sync | `SNAPTRADE_CLIENT_ID`, `SNAPTRADE_CONSUMER_KEY`; encrypted user credential data | 250/min/client; Personal 10/min/account | 3 account-data calls/account sync | Read-only portal, one active sync/account, sanitized errors | Add scheduler, timeout, and safe reset handling |
| Nasdaq Trader | Optional startup/manual directory refresh | App User-Agent; no key | No numeric public-file rate published | One file/refresh; at most daily; 15 sec, no retry | One-day cache and atomic last-good snapshot | Add conditional fetch after licensing review |
