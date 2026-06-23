# Phase 30B Founder Demo Script

Status: backend/docs draft for P30B-T4 handoff.

This script uses the stable synthetic Golden Path demo seed. It is separate from
Skyframe fixtures and should exercise real app routes/storage. Do not use real
brokerage accounts, real saved reports, provider payloads, logs, screenshots
with private data, LLM calls, TradingAgents, or external providers for this demo.

## Setup

1. Start the local app against a disposable/local database.
2. Seed the synthetic demo rows:

   ```bash
   cd backend
   python3 scripts/manual/seed_golden_path_demo.py --apply --reset-saved-outputs
   ```

3. Open the app with the seeded demo user.
4. Confirm Account Details shows one synthetic connected review account.
5. Confirm Reports is empty or contains only the intended synthetic demo state.

## Demo Positioning

Say:

- "This is a read-only review desk for manual decisions."
- "The backend saves generation-time evidence so the report can be reopened as a
  historical snapshot."
- "Agent Team generation is explicit. Saving a snapshot does not automatically
  generate a report."
- "Account-level feasibility and collateral remain caveated unless explicitly
  reviewed."

Do not say:

- advice, recommendation, buy, sell, hold, order, execution, safe to trade,
  ready to trade, guaranteed return, or similar action wording.

## Flow A - Stock/ETF Review

Use a simple stock/ETF-style input:

- Symbol: `XYZ`
- Quantity: `3`
- Price assumption: `50`
- Portfolio context: latest available synthetic demo context
- Review account: seeded synthetic review account

Steps:

1. Open Trade Review.
2. Select the seeded review account.
3. Enter the stock/ETF review inputs.
4. Run portfolio-backed preview.
5. Point out:
   - deterministic review status;
   - broker snapshot freshness;
   - market quote freshness;
   - scope metadata;
   - caveats;
   - manual/read-only boundary.
6. Save the evidence snapshot.
7. Open Reports.
8. Select the saved report.
9. Explicitly generate the Agent Team briefing.
10. Reopen the report detail and show:
    - synthesis first;
    - role-separated flags;
    - deterministic facts;
    - provenance and timestamps;
    - caveats;
    - no hidden recomputation from current selector state.

Expected story:

"The review desk preserves what the backend knew when the snapshot was saved.
The report is a historical briefing, not a live account mirror."

## Flow B - Cash-Secured Put Review

Use a simple options input:

- Underlying: `XYZ`
- Option type: `put`
- Leg action: `sell_to_open`
- Expiration: `2026-12-18`
- Strike: `50`
- Quantity: `1`
- Premium: `2`
- Portfolio context: latest available synthetic demo context
- Review account: seeded synthetic review account

Steps:

1. Return to Trade Review.
2. Keep the seeded review account selected.
3. Enter the cash-secured put review inputs.
4. Run portfolio-backed preview.
5. Point out:
   - option-specific caveats;
   - collateral is not treated as verified;
   - account-level feasibility remains caveated;
   - no order/execution behavior exists.
6. Save the evidence snapshot.
7. Open Reports.
8. Explicitly generate the Agent Team briefing.
9. Reopen the saved report.
10. Confirm the report uses saved evidence and does not refresh/reinterpret
    current account state.

Expected story:

"The options review shows assignment/collateral caveats as context only. The
system does not turn those caveats into a trade instruction."

## Smoke Checklist

- The seeded demo can be rerun without duplicate synthetic accounts.
- Skyframe fixture headers are not used for this route-driven demo.
- Saving a snapshot creates a saved review source/artifact.
- Agent Team report generation happens only after the explicit Generate action.
- Report detail shows historical scope/evidence.
- Regeneration preserves the saved source snapshot and updates only report
  generation timing/output.
- No raw provider IDs, account numbers, balances, buying power, holdings,
  quantities, provider payloads, prompts, traces, URLs, or private report data
  appear.
- No advice/action wording appears in UI copy or generated report text.

## Handoff Notes

P30B-T5 should run this script in a disposable/local environment with the stable
seed applied. Any frontend polish should be limited to clarifying the read-only
review-desk loop, explicit generation, saved-evidence provenance, and caveat
display. Do not introduce frontend mocks or route around backend storage.
