# P36-T7 Local Launch Runbook

## Purpose And Scope

This runbook is for a local P36-T7 Agent Team report generation run. It layers
the tracked launch overlay after the base Compose file and the dev-only
live-LLM image overlay.

## Standing Run Authority (founder grant, 2026-07-21)

The founder has granted Claude G and Codex B standing authority to create
reviews, prepare evidence, and run live Agent Team report generation without a
per-run authorization request. The grant covers operating the reviewed
pipeline. It does not cover changing a gate, threshold, validator, prompt,
source, provider, or schema; those keep their normal contract and review path.

Standing terms:

- One analytical attempt per target. Re-running after an infrastructure
  failure (wrapper crash, container failure) is permitted and is not a second
  attempt. A gate-driven drop is a result, not a reason to retry.
- Every run archives to `reports/<run-folder>/` with full parity:
  `run-metadata.json`, `agent-team-report.md`, and `agent-team-artifact.json`.
- Every run tears down what it started and leaves pre-existing listeners alone.
- Metadata review stays metadata-only. Report prose, account data, and `.env`
  remain outside reviewer scope; the founder reads the report itself.

### Run Archive Folder Naming

`/reports/` is gitignored, so folder names may carry trade parameters. They
must never be reproduced in tracked documents: plan records, contracts, and
committed relays refer to a run by a neutral id such as `p36-t7-l2-run-1`.

Order: UTC review-creation timestamp to the second, then symbol, then buy or
sell, then instrument type, then option expiration and strike where they
apply, then quantity, then price.

- Stock: `20260721T050904Z-AAPL-buy-stock-10sh-324.00`
- Option: `20260721T050904Z-AAPL-sell-option-20260815-C330-2ct-5.20`

Timestamps are UTC with a trailing `Z`. Use hyphens only; no spaces, colons, or
slashes. A multi-leg option strategy names the strategy and its primary leg;
extend this convention by contract rather than improvising a new shape.

**Naming metadata never comes from the frozen artifact.** Quantity and price
are not recoverable from a saved artifact by design: `quantity` is a forbidden
key and a digit-plus-`shares`/`contracts` span is a prohibited pattern in
saved-review payloads (`app/schemas/reports.py:135,295`). The artifact layer
rejects them rather than storing them. The run operator therefore takes the
naming parameters from the founder's review request at run time and uses them
only for the archive directory name. They must never be written into an
artifact, a report payload, a tracked document, or a commit — the payload
validator would reject them, and the tracked-document rule above forbids them
independently.

**Historical archives keep their neutral ids.** Archives created before this
convention (`p36-t7-l1-run-1`, `p36-t7-j5d-run-1`,
`p36-t7-j3-live-five-agent-1`, `p36-t6-2026-07-14`) cannot be converted,
because the parameters were never retained anywhere. Do not rename them and do
not reconstruct a name from partial data. Mock and smoke-test archives
(`p36-t7-mock-run-1`, `p36-t7-mock-rehearsal-1`, `agent-team-test-results`)
have no reviewed trade intent and stay outside this convention permanently.

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
   unexpected result. Every configured P36 lane must also be effective; a
   configured-but-not-effective lane is a hard stop because that run would
   silently fall back to deterministic output. For a five-role validation,
   additionally require all three lanes to be both configured and effective.
   This does not block a separately authorized single-lane run whose sole
   configured lane is effective.
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
from app.api.routes import reports as report_routes
from app.core.config import get_settings
from app.services.market_data.eod_history import market_context_policy_from_environment
from app.services.reports.agent_team_report import (
    resolve_agent_team_report_provider_resolution,
    resolve_backend_agent_team_report_generation_mode,
    resolve_p36_live_lane_flags,
)
resolution = resolve_agent_team_report_provider_resolution()
risk, public, pm = resolve_p36_live_lane_flags()
provider_enables_live_lanes = resolution.provider is not None and resolution.provider_name != "mock"
p36_effective_live_lanes = {
    "risk": risk and provider_enables_live_lanes,
    "public": public and provider_enables_live_lanes,
    "pm": pm and provider_enables_live_lanes,
}
settings = get_settings()
eod_policy, eod_context = report_routes._resolve_fmp_eod_history_generation_context()
fundamentals_policy, fundamentals_context = report_routes._resolve_fmp_fundamentals_generation_context()
edgar_profile_policy, edgar_profile_client, edgar_filings_policy, edgar_filings_client = (
    report_routes._resolve_edgar_report_evidence_generation_context()
)
print({
    "report_generation_mode": resolve_backend_agent_team_report_generation_mode(),
    "p36_live_lanes": {"risk": risk, "public": public, "pm": pm},
    "p36_effective_live_lanes": p36_effective_live_lanes,
    "provider": {
        "name": resolution.provider_name,
        "model": resolution.model,
        "status": resolution.status,
        "available": resolution.available,
        "error_code": resolution.error_code,
    },
    "market_context_mode": market_context_policy_from_environment().mode,
    "source_lane_resolution": {
        "eod_policy_resolved": eod_policy is not None,
        "eod_context_resolved": eod_context is not None and eod_context.client is not None,
        "fundamentals_policy_resolved": fundamentals_policy is not None,
        "fundamentals_context_resolved": (
            fundamentals_context is not None and fundamentals_context.client is not None
        ),
        "edgar_profile_resolved": edgar_profile_policy is not None and edgar_profile_client is not None,
        "edgar_filings_resolved": edgar_filings_policy is not None and edgar_filings_client is not None,
    },
    "edgar_report_evidence_mode": settings.edgar_report_evidence_mode,
    "sec_edgar_user_agent_declared": bool(settings.sec_edgar_user_agent.strip()),
})
'
```

This preflight may report only safe configuration metadata. It must not print
environment values, keys, account data, symbols, prompts, report content, raw
provider payloads, or request/response bodies. It does not call an LLM, market
provider, EDGAR, broker, or report-generation route.

`p36_effective_live_lanes` deliberately reimplements the runner's current
provider-and-lane conjunction. It can drift if that runtime expression changes.
The durable fix is a separate backend slice: export one shared helper for the
runner and preflight, with a parity test, after Codex B and Claude G review.

For a five-role acceptance run, all six `source_lane_resolution` booleans must
be `true`. These booleans prove only that the reviewed clients are configured;
they do not prove that a particular reviewed symbol is available from each
source. A prior source-only compatibility check requires its own founder
authorization because it calls external providers.

## Target Resolution

Resolve a saved-review target with one read-only, metadata-only query before a
separately authorized generation. Do not use a report title, `report_type`,
`status`, `agent_summary`, or `public_evidence` as the structural predicate:
those fields are client-supplied, fixed at insertion, or may legitimately be
present or absent before generation.

Three distinct `symbol_or_underlying` fields exist in the schemas. For saved
artifacts and saved-review sources, the canonical persisted symbol is the
top-level deterministic-summary field:

- `report_threads.saved_artifact_json -> 'deterministic_summary' ->> 'symbol_or_underlying'`
- `saved_review_sources.deterministic_summary_json ->> 'symbol_or_underlying'`

The nested `trade_intent.symbol_or_underlying` field belongs to the evidence
package and is not a valid saved-artifact lookup path. A valid saved artifact
has `saved_artifact_json` present and `source_kind=trade_review_workspace`.
Use the presence of `agent_summary.tool_run_artifact` whose
`artifact_schema_version` is `p36_tool_run_freeze_v1` as the generation marker;
do not treat `agent_summary` presence alone as generation.

The lookup may emit only: aggregate match count, saved-review-source match
count, distinct user count, saved-artifact total count, distinct-symbol count,
whether the newest match belongs to the prior run user, and for the newest
unambiguous match only its UTC creation time, public-evidence-prepared boolean,
generation boolean, provider mode, final-synthesis author, instrument kind,
instrument-resolution status,
`report_type_matches_saved_review_artifact`, and `status_matches_completed`.
Never emit user, thread, artifact, account, or source identifiers, titles,
symbols other than the supplied target, quantities, prices, evidence, or report
content.

Stop if multiple candidates share the newest creation timestamp, if the query
errors, or if no target meets the reviewed predicate. Do not widen the query,
prepare evidence, refresh a package, or generate a report. A target-resolution
query never authorizes preparation or generation. Stop if the newest match
already carries a frozen tool-run artifact. A generated artifact is never a
valid target for a new run, because frozen evidence is never replaced in place;
use the fresh-report-thread procedure below instead.

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

The approved generation wrapper must capture these fields at call time, before
any response reconstruction: `generation_started_at_utc` (UTC ISO timestamp),
`elapsed_seconds` (numeric), `exit_code` (integer), and `http_status`
(integer; use `0` only when no HTTP response was received). The metadata
writer must never substitute nulls or diagnostic strings for those values.
For a tool-mediated run, it also records the frozen artifact's
`pm_fallback_reason` as one of `gate_drop`, `unavailable`, or null. This is
safe categorical metadata only; it is not provider output or a diagnostic
message.

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
