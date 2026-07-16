# P36-T7 Local Launch Runbook

## Purpose And Scope

This runbook is for one explicitly authorized, local P36-T7 Agent Team report
generation run. It layers the tracked launch overlay after the base Compose file
and the dev-only live-LLM image overlay. It does not authorize a run by itself.

The overlay controls only these backend environment knobs:

- `POA_P36_LIVE_LANES`
- `POA_AGENT_TEAM_REPORT_GENERATION_MODE`
- `POA_LLM_MODE`
- `POA_LLM_PROVIDER`
- `POA_MARKET_CONTEXT_MODE`
- `POA_EDGAR_REPORT_EVIDENCE_MODE`

Set approved values through the private runtime environment only. Do not add
keys, tokens, secrets, or copied environment values to commands, docs, logs, or
archives. `POA_P36_LIVE_LANES` is the one-agent-at-a-time dial; its supported
names are `risk`, `public`, and `pm`. Empty/unset preserves the legacy branch.

OpenAI use is paid. Gemini can hit quota or rate limits. A provider failure must
remain a safe backend degradation, never a reason to retry blindly or weaken a
gate.

## Compose Files

Every command below uses this exact file order. The block below is the shared
prefix shown for reference; it is not a runnable step by itself:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.live-llm.yml \
  -f docker-compose.p36-t7.yml
```

`docker-compose.live-llm.yml` supplies the dev-only image with the optional
provider SDKs. `docker-compose.p36-t7.yml` supplies only the six interpolated
P36-T7 mode knobs. `docker-compose.p36-t7.inert.yml` is validation-only and
must not be included in a launch. The ordinary two-file or base-only Compose
paths remain unchanged.

## Launch Checklist

1. Confirm written founder authorization for one run, including the approved
   live lane and any approved public-evidence mode.
2. Confirm with the environment owner that the private runtime environment
   was prepared with only the approved configuration; the step-3 preflight
   metadata output is the only permitted verification of its effect. Do not
   open, inspect, or print the environment file.
3. Run the inert Compose check and preflight below. Stop on a failed or
   unexpected result.
4. Check ports before starting services. Do not stop an unknown listener.
5. Build and start the local stack only after preflight passes.

## Inert Compose Check

Use a temporary, inert environment file outside the repository to validate
overlay syntax. It must contain placeholders for the base local access token and
database settings, plus non-live values for all six P36-T7 knobs. Never copy a
private runtime environment file for this check.

Include `docker-compose.p36-t7.inert.yml` only for this validation. It removes
the base backend `env_file` entry, so Compose cannot load the private `.env`
while checking the configuration. This does not start containers or call
providers:

```bash
docker compose --env-file <inert-env-file> \
  -f docker-compose.yml \
  -f docker-compose.live-llm.yml \
  -f docker-compose.p36-t7.yml \
  -f docker-compose.p36-t7.inert.yml \
  config --quiet
```

Delete the temporary inert environment file after the check. Never reuse it
for a launch.

## Preflight

Import `app.main` first during preflight to mirror Uvicorn startup. P36-T7-H1
separately covers the cold-import regression; do not use a naked service import
as the runtime preflight path.

After the approved runtime environment is available, run this metadata-only
check before any generation request:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.live-llm.yml \
  -f docker-compose.p36-t7.yml \
  run --rm --no-deps backend python -c '
import app.main
from app.core.config import get_settings
from app.services.market_data.eod_history import market_context_policy_from_environment
from app.services.reports.agent_team_report import (
    resolve_agent_team_report_provider_resolution,
    resolve_backend_agent_team_report_generation_mode,
    resolve_p36_live_lane_flags,
)
resolution = resolve_agent_team_report_provider_resolution()
risk, public, pm = resolve_p36_live_lane_flags()
settings = get_settings()
print({
    "report_generation_mode": resolve_backend_agent_team_report_generation_mode(),
    "p36_live_lanes": {"risk": risk, "public": public, "pm": pm},
    "provider": {
        "name": resolution.provider_name,
        "model": resolution.model,
        "status": resolution.status,
        "available": resolution.available,
        "error_code": resolution.error_code,
    },
    "market_context_mode": market_context_policy_from_environment().mode,
    "edgar_report_evidence_mode": settings.edgar_report_evidence_mode,
    "sec_edgar_user_agent_declared": bool(settings.sec_edgar_user_agent.strip()),
})
'
```

This preflight may report only safe configuration metadata. It must not print
environment values, keys, account data, symbols, prompts, report content, raw
provider payloads, or request/response bodies. It does not call an LLM, market
provider, EDGAR, broker, or report-generation route.

## Fresh Report Thread From A Saved Review Source

Use this procedure only when the approved run requires a new frozen public-
evidence package. An older report remains historical evidence and must not be
modified or treated as a place to acquire newly enabled source lanes.

1. Resolve the existing `source_reference` through an already reviewed,
   app-owned saved-review selection path. Keep the user, source, artifact, and
   thread references in process memory only. Do not print, list, or archive
   them.
2. Record the current report-thread identifiers in process memory, then call
   `POST /users/<user-id>/reports/from-trade-review` with synthetic-shaped
   request fields:

   ```json
   {
     "source_kind": "trade_review_workspace",
     "source_reference": "<approved-saved-source-reference>",
     "title": "<generic-run-label>",
     "report_type": "trade_review"
   }
   ```

   This creates a new DB-backed artifact and report thread with
   `public_evidence=null`. It is a save operation, not Agent Team generation,
   and does not consume the separately authorized generation attempt.
3. Require HTTP `201`, `status=saved`, and `public_evidence_is_none=true`.
   Identify the new thread in-process by taking the single set difference
   between the reviewed report list before and after the save. Emit only the
   safe metadata `new_thread_count=1`; never print or archive the thread,
   artifact, source, user, account, or report references.
4. Leave the older report and its frozen evidence unchanged. Do not recompute
   from current Account Details or selectors, and do not acquire any source
   evidence during this save step.
5. Stop after the save and request explicit founder authorization for exactly
   one generation attempt on the new thread. Creating the thread does not
   authorize generation.

Any helper used for this procedure must pass the local access token through
in-container environment expansion only. It must not read or print `.env`,
response bodies, report content, account data, or identifiers. The metadata
archive may record only the approved booleans and counts above.

## Port Checks And Launch

Before launch, inspect only listening processes on the loopback ports:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:5173 -sTCP:LISTEN
lsof -nP -iTCP:5432 -sTCP:LISTEN
```

If a port is occupied by an unknown process, pause this runbook and resolve
ownership before continuing. Do not kill it from this runbook.

After authorization and a passing preflight, build and start the local stack:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.live-llm.yml \
  -f docker-compose.p36-t7.yml \
  up -d --build postgres backend frontend
```

Record the UTC start time at launch; the metadata archive requires it.

Confirm the backend is healthy with `curl -i http://localhost:8000/health`
only. Do not probe data routes (for example `/users`) from this runbook; the
stack may hold real synced account data, and health is the only confirmation
this step needs.

Confirm service state with:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.live-llm.yml \
  -f docker-compose.p36-t7.yml \
  ps
```

A generation request remains separate and requires the specific founder
authorization; this runbook does not provide a request body or invoke a live
generation.

## Metadata-Only Archive

After an authorized run, archive only operational metadata outside private
artifacts: UTC start/end time, task/run label, git revision, image tag or digest,
Compose file names, selected lane names, safe mode/status categories, exit code,
and duration.

Task/run labels must be generic - a task id plus a sequence number - never
symbols, account nicknames, or trade descriptions. Archive categorized error
codes only, never provider error message strings, which can echo request
fragments.

Never archive report text, prompts, role outputs, request or response bodies,
raw logs, account or report identifiers, user identifiers, symbols, trade
details, provider payloads,
environment dumps, keys, tokens, or secrets. If a needed record cannot be made
without one of those fields, do not archive it; request a reviewed safe metadata
shape instead.

Record the archived metadata in the run's `implementation_plan.md`
execution-log entry - the established redacted pattern. Full private run
artifacts remain under the gitignored `reports/` folder; do not create ad hoc
archive locations.

## Teardown And Port Confirmation

When the approved work is complete, stop the stack without deleting volumes:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.live-llm.yml \
  -f docker-compose.p36-t7.yml \
  down
```

Do not add `-v` unless a separate approval explicitly authorizes volume removal.
Then repeat the three `lsof` port checks. A listener owned by another process is
not evidence of failed teardown and must not be terminated from this runbook.
