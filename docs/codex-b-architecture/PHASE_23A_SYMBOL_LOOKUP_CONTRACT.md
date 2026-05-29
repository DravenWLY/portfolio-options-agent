# Phase 23A Symbol Lookup / Instrument Reference Contract

Status: architecture contract for next backend slice
Owner: Codex B - Architecture / Systems / Integration
Date: 2026-05-27
Related plan task: `P23A-T1`

## Goal

Create a backend-owned symbol lookup and validation foundation for Trade Review
inputs and later Dashboard quick entry.

The first implementation must be provider-neutral, synthetic/replay-first, and
deterministic. It must improve user input ergonomics without introducing live
market-data claims, quote display, provider credentials, frontend financial
calculation, or broker execution behavior.

## Product Use Cases

Phase 23A supports:

- typeahead suggestions when a user enters a partial ticker such as `NV`;
- an empty-query non-search state that lets the frontend show only
  browser/user-local recent symbols when that separate UI state exists;
- exact-first broad search when a user enters a string such as `NOK`;
- exact symbol validation before a trade-review intent is submitted;
- a clear `Symbol Not Found` state when no supported match exists;
- later frontend wiring for Trade Review symbol fields and optional Dashboard
  quick entry.

It does not support:

- quotes, charts, price change, volume, option chains, or watchlists;
- investment recommendations or ranked "best" symbols;
- order entry, trading, broker execution, or account lookup;
- sending symbol lookup results to LLM agents by default.

## Endpoint Shape

Initial backend endpoints should be read-only and app-owned:

- `GET /symbols/search?q={query}`
- `GET /symbols/validate?symbol={symbol}`

Codex C may adjust exact path naming only if it documents the reason and keeps
the contract provider-neutral.

## Data Modes

The contract must explicitly expose data provenance:

- `synthetic`
- `replay`
- `provider_reference`
- `unavailable`

The initial task may emit only `synthetic` or `replay`. A real provider adapter
requires a later PM-approved task.

Symbol lookup data mode is not quote truth. It must not imply current price,
listing entitlement, tradability at a broker, or order eligibility.

## Conceptual Schemas

`SymbolSearchRead`

- `query`
- `normalized_query`
- `data_mode`
- `source_label`
- `as_of_label`
- `items`
- `no_match`
- `message`

`SymbolSearchItemRead`

- `symbol`
- `name`
- `asset_class`
- `exchange`
- `region`
- `currency`
- `is_supported`
- `match_type`
- `score_label`
- `source_label`
- `as_of_label`

`SymbolValidationRead`

- `symbol`
- `normalized_symbol`
- `is_found`
- `is_supported`
- `asset_class`
- `exchange`
- `name`
- `data_mode`
- `source_label`
- `as_of_label`
- `message`

Allowed `asset_class` values should start narrowly:

- `stock`
- `etf`
- `adr`
- `option`
- `index`
- `unknown`

Phase 23A may choose not to return options in autocomplete until an option
symbol identity contract is reviewed. Listed-option contract lookup is separate
from stock/ETF ticker lookup.

Allowed `match_type` values:

- `exact`
- `prefix`
- `contains`
- `alias`
- `not_found`

## Search Semantics For P23A-T3+

The initial P23A-T1/T2 implementation proved strict-prefix search against a
small synthetic fixture set. P23A-T3 may expand behavior while preserving the
provider-neutral contract:

- Empty query:
  - return an empty non-search state, not global default symbols;
  - do not infer recent symbols from private holdings, broker accounts, trade
    history, portfolio context, prompts, LLM context, or agent context;
  - true recent-symbol tracking belongs to a separately reviewed
    browser/user-local LRU layer, not backend global reference data.
- Non-empty query:
  - normalize case and whitespace in the backend;
  - return up to five or six suggestions;
  - place exact symbol matches first;
  - then place symbol-prefix matches;
  - then place symbol-contains and/or name-contains matches;
  - use deterministic tie-breakers such as supported status, asset-class
    priority, exchange/source priority, and symbol alphabetic order;
  - never use fuzzy/edit-distance matching unless a future task explicitly
    approves it.

This ordering is a usability ranking only. It must not be described as a
recommendation, popularity signal, liquidity signal, broker tradability signal,
or expected performance signal.

## Safety And Privacy

Symbol lookup is public reference data and must not include:

- broker holdings or positions;
- user account values, cash, buying power, or account identifiers;
- raw provider payloads;
- provider entitlement metadata;
- provider credentials or secrets;
- order eligibility or broker routing instructions;
- "buy", "sell", "recommended", "top pick", "safe to trade", or
  "ready to trade" language.

The frontend may display `Symbol Not Found`, but backend should own the
canonical message so copy remains consistent across pages.

## Provider Boundary

The initial task must not add a live provider, SDK, credentials, or network
call. It may use static synthetic fixtures checked into tests or a small app
fixture module designed for deterministic tests.

P23A-T3 may add a parser/importer for Nasdaq-style symbol directory files, but
default tests must remain offline and use synthetic fixture files. Do not fetch
Nasdaq, broker, Yahoo, Alpaca, or paid-provider files during tests. Do not
commit raw provider payloads or any source file whose redistribution terms have
not been reviewed. The app-facing service should consume normalized
provider-neutral records, not raw file rows.

P23A-T5 may add a personal-demo scheduled refresh path for Nasdaq Symbol
Directory files. That path must:

- keep `/symbols/search` and `/symbols/validate` provider-neutral;
- download only public symbol-reference files, not quotes, prices, options
  chains, broker data, or market-data feeds;
- run through an explicit backend scheduler/job boundary rather than blocking
  app startup;
- keep using the last good normalized snapshot if refresh fails;
- expose safe provenance through existing source/as-of labels;
- preserve synthetic/local fixture tests as the default test path;
- avoid frontend provider URLs, credentials, API keys, raw file payloads, and
  provider-specific row shapes.

For the personal demo, scheduled refresh may be enabled by app configuration or
local deployment wiring. Commercial/public use still requires a later licensing
and provider review.

Future source candidates may include exchange/security master providers or a
licensed market-data vendor, but provider selection is out of scope here.
Yahoo Finance, Alpaca, or other public sources are not approved as default app
backends by this contract.

## Phase 23B Completion Direction

After P23A-T5, the remaining personal-demo completion work is Phase 23B:

- persist only the normalized last-good `SymbolDirectorySnapshot`, not raw
  downloaded files or raw source rows;
- restore a valid last-good normalized snapshot on backend startup without
  fetching;
- keep synthetic fallback active when no persisted snapshot exists or when a
  persisted snapshot is malformed;
- add opt-in local refresh wiring that can fetch public Nasdaq Symbol Directory
  files only when explicitly invoked or enabled;
- keep default tests and default app startup network-free;
- preserve `/symbols/search` and `/symbols/validate` response shapes;
- require the frontend to uppercase symbol inputs for display/submission while
  still letting the backend normalize defensively.

Phase 23B still does not authorize quote data, price display, volume, option
chains, watchlists, screeners, broker tradability claims, recommendation
language, agent ingestion, or commercial/public data-use claims.

## Frontend Boundary

No frontend work is authorized by `P23A-T1`.

After Codex B reviews the backend contract, Claude A may wire:

- Trade Review symbol autocomplete;
- exact validation messages;
- `Symbol Not Found` display;
- optional keyboard navigation and accessibility polish.

Frontend must not rank suggestions as recommendations or compute symbol support
from raw provider fields.

## Agent Boundary

Symbol lookup results must not be added to LLM prompts or TradingAgents inputs
by default. Any future agent-safe public-symbol context requires a separate
approved evidence contract.

## Acceptance Direction

The first implementation should prove:

- deterministic prefix search;
- exact validation;
- no-match behavior;
- unsupported symbol behavior;
- case/whitespace normalization;
- safe source/as-of labels;
- forbidden-field tests;
- no external calls in default tests.
