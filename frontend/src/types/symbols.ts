/**
 * TypeScript mirror of backend symbol lookup read schemas
 * (P23A-T1 base; P23B-T5 replaced the backend "recent" result mode with a
 * truthful "empty" mode — the backend no longer returns a global default
 * symbol list. True "Recently viewed" recents are browser-local LRU state
 * owned by the frontend, see src/lib/symbolRecents.ts, P23B-T6).
 *
 * Mirrors:
 *   backend/app/schemas/symbols.py
 *     SymbolSearchItemRead, SymbolSearchRead, SymbolValidationRead
 *
 * Strictly mirror the backend. The frontend never invents fields, never
 * ranks symbols as recommendations, never shows prices/quotes/volume,
 * and never performs financial calculations.
 */

/* ── Enum literals ─────────────────────────────────────────────────────── */

export type SymbolLookupDataMode =
  | "synthetic"
  | "replay"
  | "provider_reference"
  | "unavailable";

export type SymbolAssetClass =
  | "stock"
  | "etf"
  | "adr"
  | "option"
  | "index"
  | "unknown";

export type SymbolMatchType =
  | "exact"
  | "prefix"
  | "contains"
  | "alias"
  | "not_found";

export type SymbolSearchResultMode =
  | "empty"
  | "search"
  | "no_match"
  | "unavailable";

/* ── Search response ───────────────────────────────────────────────────── */

export interface SymbolSearchItemRead {
  symbol: string;
  name: string;
  asset_class: SymbolAssetClass;
  exchange: string;
  region: string;
  currency: string;
  is_supported: boolean;
  match_type: SymbolMatchType;
  score_label: string;
  source_label: string;
  as_of_label: string;
}

export interface SymbolSearchRead {
  query: string;
  normalized_query: string;
  data_mode: SymbolLookupDataMode;
  result_mode: SymbolSearchResultMode;
  section_label: string;
  source_label: string;
  as_of_label: string;
  items: SymbolSearchItemRead[];
  no_match: boolean;
  message: string;
}

/* ── Validation response ───────────────────────────────────────────────── */

export interface SymbolValidationRead {
  symbol: string;
  normalized_symbol: string;
  is_found: boolean;
  is_supported: boolean;
  asset_class: SymbolAssetClass;
  exchange: string | null;
  name: string | null;
  data_mode: SymbolLookupDataMode;
  source_label: string;
  as_of_label: string;
  message: string;
}
