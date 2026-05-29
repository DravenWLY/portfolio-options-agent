/**
 * symbolRecents — browser-local "Recently viewed" symbol list (P23B-T6).
 *
 * After P23B-T5 the backend no longer returns a global/fake "Recently viewed"
 * list. True recents are user/browser-local LRU state owned entirely by the
 * frontend and persisted in localStorage under a single UI-only key.
 *
 * Safety / scope:
 *   - Stores ONLY public symbol reference fields needed to render a row.
 *   - Never stores prices, quotes, volume, account context, portfolio context,
 *     broker data, prompts, LLM context, or trade history.
 *   - Uses exactly one storage key: `poa-symbol-recents`. No other key.
 *   - Updated only on intentional actions (selecting a suggestion, or
 *     promoting an already-known symbol on form submit) — never from typing,
 *     search-result display, holdings, or any inferred source.
 *   - All access is wrapped so unavailable/blocked storage degrades to an
 *     empty list rather than throwing.
 */
import type { SymbolAssetClass } from "../types/symbols";

/** Minimal public symbol reference stored for a recent row. */
export interface SymbolRecentItem {
  symbol: string;
  name: string;
  asset_class: SymbolAssetClass;
  exchange: string;
  region: string;
  currency: string;
  is_supported: boolean;
}

/** UI-only localStorage key. Do not add any other storage key. */
export const SYMBOL_RECENTS_KEY = "poa-symbol-recents";

/** Maximum number of recents kept (newest first). */
export const SYMBOL_RECENTS_CAPACITY = 5;

const ASSET_CLASSES: readonly SymbolAssetClass[] = [
  "stock",
  "etf",
  "adr",
  "option",
  "index",
  "unknown",
];

/** Coerce arbitrary input into a safe, field-restricted recent (or null). */
function sanitize(raw: unknown): SymbolRecentItem | null {
  if (typeof raw !== "object" || raw === null) return null;
  const r = raw as Record<string, unknown>;
  const symbol = typeof r.symbol === "string" ? r.symbol.trim() : "";
  if (!symbol) return null;
  const assetClass =
    typeof r.asset_class === "string" && ASSET_CLASSES.includes(r.asset_class as SymbolAssetClass)
      ? (r.asset_class as SymbolAssetClass)
      : "unknown";
  return {
    // Whitelist only the public reference fields — never persist extra fields
    // (e.g. score/source/as-of labels, prices, or any non-listed property).
    symbol,
    name: typeof r.name === "string" ? r.name : "",
    asset_class: assetClass,
    exchange: typeof r.exchange === "string" ? r.exchange : "",
    region: typeof r.region === "string" ? r.region : "",
    currency: typeof r.currency === "string" ? r.currency : "",
    is_supported: Boolean(r.is_supported),
  };
}

function readStorage(): SymbolRecentItem[] {
  try {
    if (typeof window === "undefined" || !window.localStorage) return [];
    const raw = window.localStorage.getItem(SYMBOL_RECENTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    const out: SymbolRecentItem[] = [];
    const seen = new Set<string>();
    for (const entry of parsed) {
      const item = sanitize(entry);
      if (!item || seen.has(item.symbol)) continue;
      seen.add(item.symbol);
      out.push(item);
      if (out.length >= SYMBOL_RECENTS_CAPACITY) break;
    }
    return out;
  } catch {
    return [];
  }
}

function writeStorage(items: SymbolRecentItem[]): void {
  try {
    if (typeof window === "undefined" || !window.localStorage) return;
    window.localStorage.setItem(SYMBOL_RECENTS_KEY, JSON.stringify(items));
  } catch {
    // Storage unavailable / quota exceeded — recents are best-effort only.
  }
}

/** Load the current browser-local recents (newest first). */
export function loadSymbolRecents(): SymbolRecentItem[] {
  return readStorage();
}

/**
 * Record an intentionally-chosen symbol as the most-recent entry.
 * Dedupes by symbol (moving an existing entry to the top), caps at capacity,
 * and persists only the whitelisted public fields. Returns the updated list.
 */
export function addSymbolRecent(item: SymbolRecentItem): SymbolRecentItem[] {
  const sanitized = sanitize(item);
  if (!sanitized) return readStorage();
  const existing = readStorage().filter((r) => r.symbol !== sanitized.symbol);
  const next = [sanitized, ...existing].slice(0, SYMBOL_RECENTS_CAPACITY);
  writeStorage(next);
  return next;
}

/**
 * Promote an already-known symbol to the top of recents if it exists.
 * Used on successful form submit so a submitted (previously-selected) symbol
 * becomes most-recent. Does NOT fabricate a new entry for an unknown symbol —
 * creating recents for never-selected typed symbols would require validated
 * display fields and is intentionally deferred.
 */
export function promoteSymbolRecent(symbol: string): SymbolRecentItem[] {
  const normalized = symbol.trim();
  if (!normalized) return readStorage();
  const current = readStorage();
  const match = current.find((r) => r.symbol === normalized);
  if (!match) return current;
  const next = [match, ...current.filter((r) => r.symbol !== normalized)].slice(
    0,
    SYMBOL_RECENTS_CAPACITY,
  );
  writeStorage(next);
  return next;
}
