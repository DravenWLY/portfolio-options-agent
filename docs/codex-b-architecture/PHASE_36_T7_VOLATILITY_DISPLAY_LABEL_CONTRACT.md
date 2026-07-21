# Phase 36 T7 Volatility Display-Label Contract

Status: approved — Claude G architecture/privacy/safety review PASS
(2026-07-20), no required changes; cleared for Codex C implementation

## Trigger

The P36-T7-K2B active-lane label audit correctly stopped before a user-facing
report could fail document output safety. The path is:

`prompt_fact_labels_for_tool_result` -> `calc_volatility_stats` ->
`annualized_volatility_percent` -> current display label `annualized volatility`.

`annualized` is intentionally prohibited in rendered report prose. It must not
be broadly exempted, because that would weaken the existing document safety
boundary for generated language.

## Binding Decision

Retain `annualized_volatility_percent` as an approved C9 calculation fact in
the technical analyst's frozen tool result and prompt fact-label projection.
Do not exclude it from prompt fact labels.

Its only approved user-visible label is:

`Realized volatility (annual basis)`

This label preserves the metric's time-basis meaning without exposing the
prohibited token. It is a presentation label only; it does not change the
calculation, value, units, tool name, evidence tier, frozen artifact, numeric
provenance rule, or source lane.

## Rendering Boundary

- `display_label_for_code("annualized_volatility_percent")` must return the
  approved label above.
- A prompt fact-label projection may retain the internal fact key for backend
  validation, but any report/table/debugging rendering must use only the
  approved label.
- The internal fact key and calculation method label remain envelope/audit
  data. They are never a user-facing report label.
- The technical role prompt continues to describe the metric as a volatility
  calculation and must not use the prohibited term in generated prose.
- No general `annualized` allowlist, regex exception, scanner change, source
  change, or label rewrite beyond this fact key is authorized.

## Safety and Privacy Boundaries

This is a one-key display mapping. It must not add or render raw provider
payloads, URLs, prompts, traces, secrets, account/provider/broker identifiers,
account numbers, balances, buying power, holdings, positions, quantities, lots,
or current-state data. It introduces no advice, recommendation, order,
execution, safe-to-trade, ready-to-trade, or guaranteed-return language.

Frozen historical readback remains read-only: no source/provider call,
recalculation, or reclassification is permitted to render this label.

## Codex C Implementation Scope

After Claude G PASS, make the smallest mapping/test change:

1. Change the existing `FACT_DISPLAY_LABELS` value for
   `annualized_volatility_percent` to the approved label.
2. Add focused tests that prove the exact mapping and the prompt fact-label
   projection use it.
3. Run the K2B synthetic active-lane full-document canary. It must pass with
   this label while the existing document validator continues to reject the
   literal prohibited token in ordinary generated report prose.
4. Re-run frozen readback tests and confirm zero provider/source calls.

If any other active-lane label conflicts with document safety, stop and return
that key for its own contract. Do not broaden this decision by analogy.

## Review and Acceptance

Claude G reviews this contract first. Codex C implements only the scoped mapping
after that PASS. Codex B then reviews contract/readback behavior, and Claude G
performs final architecture/privacy/safety review. K2B remains blocked until
this slice lands and its label-audit canary passes.
