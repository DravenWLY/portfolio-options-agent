import { useState, useEffect, useRef, useCallback } from "react";
import { symbolsApi } from "../../api/symbols";
import {
  loadSymbolRecents,
  addSymbolRecent,
  type SymbolRecentItem,
} from "../../lib/symbolRecents";

/**
 * SymbolAutocomplete — typeahead symbol input backed by
 * GET /symbols/search (P23A-T2, search UX in P23A-T4, uppercase polish in
 * P23B-T3, browser-local recents in P23B-T6).
 *
 * Behavior:
 *   - Input is forced uppercase as the user types: onChange always emits an
 *     uppercased value, so the controlled value, the search query, and the
 *     submitted payload are uppercase (e.g. "nvda" → "NVDA", "nok" → "NOK").
 *   - Empty input on focus → browser-local "Recently viewed" LRU list (owned
 *     by the frontend, persisted under the single key `poa-symbol-recents`).
 *     The backend returns no recents/defaults for an empty query (result_mode
 *     "empty"), so we never display backend symbols for empty input. If there
 *     are no local recents we show a neutral empty state, never "Symbol Not
 *     Found".
 *   - Non-empty input → backend exact-first search results, rendered in
 *     backend order. No frontend ranking, sorting, filtering, or fuzzy
 *     matching.
 *   - A recent is recorded only when the user intentionally selects a
 *     suggestion — never from typing or from search-result display.
 *
 * Safety:
 *   - Read-only. No order/execute/place/cancel controls.
 *   - No quotes, prices, volume, or market data.
 *   - No frontend financial computation.
 *   - localStorage is used only for the UI-only public symbol recents key
 *     `poa-symbol-recents` (no prices, account, broker, or portfolio data).
 *   - Results are not ranked or reinterpreted as recommendations.
 *   - Backend-owned section labels and messages rendered verbatim.
 */

interface SymbolAutocompleteProps {
  /** Current field value (controlled). */
  value: string;
  /** Called when the user types or selects a suggestion. */
  onChange: (value: string) => void;
  /** Field label text. */
  label: string;
  /** Optional placeholder hint. Display-only; never submitted unless typed. */
  placeholder?: string;
  /** Disable interaction. */
  disabled?: boolean;
  /** Minimum query length before searching (default 1). */
  minQueryLength?: number;
}

/** Debounce delay in ms for search requests. */
const DEBOUNCE_MS = 250;

export default function SymbolAutocomplete({
  value,
  onChange,
  label,
  placeholder,
  disabled = false,
  minQueryLength = 1,
}: SymbolAutocompleteProps) {
  /**
   * Rendered rows. Backend search items (which carry extra fields) are
   * structurally assignable to the minimal recent shape; both render the
   * same row. Recents store only the whitelisted public fields.
   */
  const [suggestions, setSuggestions] = useState<SymbolRecentItem[]>([]);
  const [noMatchMessage, setNoMatchMessage] = useState<string | null>(null);
  /**
   * Section heading. "Recently viewed" is frontend-owned (browser-local
   * recents); for non-empty search it is the backend-owned section_label.
   */
  const [sectionLabel, setSectionLabel] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  /** True when empty input has no browser-local recents (neutral empty state). */
  const [isRecentsEmpty, setIsRecentsEmpty] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  /** Track whether the current value was set by selecting a suggestion. */
  const justSelectedRef = useRef(false);
  /** Only start searching after the user has interacted with the input. */
  const hasInteractedRef = useRef(false);

  /** Stable id linking the input (combobox) to its listbox for ARIA. */
  const listboxId = `symbol-ac-${label.replace(/\s+/g, "-").toLowerCase()}`;

  /* ── Search on prefix change ────────────────────────────────────────── */

  /** Ref mirrors the `disabled` prop so async callbacks can read it. */
  const disabledRef = useRef(disabled);
  disabledRef.current = disabled;

  /* ── Close & cancel everything when disabled ───────────────────────── */

  useEffect(() => {
    if (!disabled) return;
    if (debounceRef.current) { clearTimeout(debounceRef.current); debounceRef.current = null; }
    setIsOpen(false);
    setActiveIndex(-1);
    setSuggestions([]);
    setNoMatchMessage(null);
    setSectionLabel(null);
    setIsLoading(false);
    setErrorMsg(null);
    setIsRecentsEmpty(false);
  }, [disabled]);

  /* ── Browser-local recents (empty input) ───────────────────────────── */

  /** Show the browser-local "Recently viewed" LRU list, or a neutral empty
   *  state when there are none. Never calls the backend (empty query returns
   *  no symbols), so backend default symbols can never be displayed here. */
  const showRecents = useCallback(() => {
    if (disabledRef.current) return;
    if (debounceRef.current) { clearTimeout(debounceRef.current); debounceRef.current = null; }
    const recents = loadSymbolRecents();
    setIsLoading(false);
    setErrorMsg(null);
    setNoMatchMessage(null);
    setSuggestions(recents);
    setSectionLabel(recents.length > 0 ? "Recently viewed" : null);
    setIsRecentsEmpty(recents.length === 0);
    setActiveIndex(-1);
    setIsOpen(true);
  }, []);

  /** Search non-empty queries through the backend, rendering its items,
   *  ordering, section label, and message verbatim. */
  const doSearch = useCallback(async (rawQuery: string) => {
    if (disabledRef.current) return;
    const query = rawQuery.trim();
    if (!query) return; // empty handled by showRecents(), not the backend
    setIsRecentsEmpty(false);
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const result = await symbolsApi.search(query);
      // Drop results if disabled while the request was in flight.
      if (disabledRef.current) return;
      // Render backend items, ordering, section label, and message verbatim.
      setSuggestions(result.items);
      setSectionLabel(result.section_label || null);
      setNoMatchMessage(result.no_match ? result.message : null);
      setIsOpen(true);
      setActiveIndex(-1);
    } catch (err) {
      if (disabledRef.current) return;
      setSuggestions([]);
      setNoMatchMessage(null);
      setSectionLabel(null);
      setErrorMsg(err instanceof Error ? err.message : "Symbol search failed.");
      setIsOpen(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Don't search until the user has typed or focused the input
    if (!hasInteractedRef.current) return;
    // Don't search if the user just selected from dropdown
    if (justSelectedRef.current) {
      justSelectedRef.current = false;
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    // Empty input while focused/interacting → browser-local recents only.
    if (!value.trim()) {
      showRecents();
      return;
    }
    // Partial non-empty input below the minimum length → close, no search.
    if (value.trim().length < minQueryLength) {
      setSuggestions([]);
      setNoMatchMessage(null);
      setSectionLabel(null);
      setIsRecentsEmpty(false);
      setIsOpen(false);
      return;
    }
    debounceRef.current = setTimeout(() => doSearch(value), DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [value, doSearch, showRecents, minQueryLength]);

  /* ── Selection ──────────────────────────────────────────────────────── */

  function selectItem(item: SymbolRecentItem) {
    if (disabled) return;
    justSelectedRef.current = true;
    // Intentional selection is the only signal that records a recent.
    addSymbolRecent(item);
    onChange(item.symbol);
    setIsOpen(false);
    setSuggestions([]);
    setNoMatchMessage(null);
    setSectionLabel(null);
    setIsRecentsEmpty(false);
    setActiveIndex(-1);
    inputRef.current?.focus();
  }

  /* ── Keyboard navigation ────────────────────────────────────────────── */

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!isOpen) return;

    const itemCount = suggestions.length;
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((i) => (i < itemCount - 1 ? i + 1 : 0));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((i) => (i > 0 ? i - 1 : itemCount - 1));
        break;
      case "Enter":
        if (activeIndex >= 0 && activeIndex < itemCount) {
          e.preventDefault();
          selectItem(suggestions[activeIndex]);
        }
        break;
      case "Escape":
        e.preventDefault();
        setIsOpen(false);
        setActiveIndex(-1);
        break;
    }
  }

  /* ── Scroll active item into view ───────────────────────────────────── */

  useEffect(() => {
    if (activeIndex < 0 || !listRef.current) return;
    // Target the option by its stable id; a section-header row may occupy
    // the first child slot, so positional indexing is not reliable.
    const active = listRef.current.querySelector<HTMLElement>(`#${CSS.escape(`${listboxId}-${activeIndex}`)}`);
    active?.scrollIntoView({ block: "nearest" });
  }, [activeIndex, listboxId]);

  /* ── Close on outside click ─────────────────────────────────────────── */

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  /* ── Dropdown content ───────────────────────────────────────────────── */

  const showDropdown =
    isOpen && (suggestions.length > 0 || !!noMatchMessage || isLoading || !!errorMsg || isRecentsEmpty);

  return (
    <div ref={containerRef} style={acStyles.container}>
      <label style={acStyles.label}>
        <span style={acStyles.labelText}>{label}</span>
        <input
          ref={inputRef}
          style={acStyles.input}
          value={value}
          onChange={(e) => { hasInteractedRef.current = true; onChange(e.target.value.toUpperCase()); }}
          placeholder={placeholder}
          onFocus={() => {
            hasInteractedRef.current = true;
            if (disabled) return;
            // Empty field on focus → show browser-local recents (no backend).
            if (!value.trim()) {
              showRecents();
            } else if (suggestions.length > 0 || noMatchMessage) {
              setIsOpen(true);
            }
          }}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          autoComplete="off"
          spellCheck={false}
          role="combobox"
          aria-expanded={showDropdown || false}
          aria-autocomplete="list"
          aria-controls={showDropdown ? listboxId : undefined}
          aria-activedescendant={activeIndex >= 0 ? `${listboxId}-${activeIndex}` : undefined}
        />
      </label>

      {showDropdown && (
        <ul
          ref={listRef}
          id={listboxId}
          role="listbox"
          style={acStyles.dropdown}
        >
          {isLoading && (
            <li style={acStyles.statusItem} role="option" aria-selected={false}>
              Searching…
            </li>
          )}

          {!isLoading && errorMsg && (
            <li style={{ ...acStyles.statusItem, color: "var(--mp-block)" }} role="option" aria-selected={false}>
              {errorMsg}
            </li>
          )}

          {!isLoading && !errorMsg && noMatchMessage && (
            <li style={acStyles.statusItem} role="option" aria-selected={false}>
              {noMatchMessage}
            </li>
          )}

          {!isLoading && !errorMsg && !noMatchMessage && isRecentsEmpty && suggestions.length === 0 && (
            <li style={acStyles.statusItem} role="option" aria-selected={false}>
              No recent symbols yet. Start typing to search.
            </li>
          )}

          {!isLoading && !errorMsg && sectionLabel && suggestions.length > 0 && (
            <li style={acStyles.sectionHeader} role="presentation" aria-hidden="true">
              {sectionLabel}
            </li>
          )}

          {!isLoading && !errorMsg && suggestions.map((item, idx) => (
            <li
              key={`${item.symbol}-${idx}`}
              id={`${listboxId}-${idx}`}
              role="option"
              aria-selected={idx === activeIndex}
              style={{
                ...acStyles.item,
                ...(idx === activeIndex ? acStyles.itemActive : {}),
              }}
              onMouseDown={(e) => {
                e.preventDefault(); // prevent blur before selection
                if (!disabled) selectItem(item);
              }}
              onMouseEnter={() => { if (!disabled) setActiveIndex(idx); }}
            >
              <div style={acStyles.itemRow}>
                <span style={acStyles.itemSymbol}>{item.symbol}</span>
                <span style={acStyles.itemClass}>{item.asset_class}</span>
              </div>
              <div style={acStyles.itemName}>{item.name}</div>
              <div style={acStyles.itemMeta}>
                {item.exchange}
                {!item.is_supported && (
                  <span style={acStyles.unsupported}> · not supported</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ── Styles ───────────────────────────────────────────────────────────── */

const acStyles: Record<string, React.CSSProperties> = {
  container: { position: "relative", display: "flex", flexDirection: "column", gap: "var(--space-1)", minWidth: 180, flex: "1 1 180px" },
  label: { display: "flex", flexDirection: "column", gap: "var(--space-1)" },
  labelText: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", fontWeight: 600,
    textTransform: "uppercase", letterSpacing: "0.04em",
  },
  input: {
    fontSize: "var(--font-size-sm)",
    padding: "var(--space-2) var(--space-3)",
    border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)",
    color: "var(--mp-ink)",
    fontFamily: "var(--font-mono, monospace)",
  },
  dropdown: {
    position: "absolute", top: "100%", left: 0, right: 0,
    zIndex: 50,
    margin: 0, padding: 0, listStyle: "none",
    maxHeight: 240, overflowY: "auto",
    backgroundColor: "var(--mp-card)",
    border: "1px solid var(--mp-rule)",
    borderTop: "none",
    borderRadius: "0 0 var(--radius-sm) var(--radius-sm)",
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
  },
  statusItem: {
    padding: "var(--space-2) var(--space-3)",
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    fontStyle: "italic",
  },
  sectionHeader: {
    padding: "var(--space-2) var(--space-3)",
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
    backgroundColor: "var(--mp-paper-2)",
    borderBottom: "1px solid var(--mp-rule)",
  },
  item: {
    padding: "var(--space-2) var(--space-3)",
    cursor: "pointer",
    borderBottom: "1px solid var(--mp-rule)",
    display: "flex", flexDirection: "column", gap: 2,
  },
  itemActive: {
    backgroundColor: "var(--mp-accent-soft)",
  },
  itemRow: {
    display: "flex", justifyContent: "space-between", alignItems: "center", gap: "var(--space-2)",
  },
  itemSymbol: {
    fontFamily: "var(--font-mono, monospace)",
    fontSize: "var(--font-size-sm)",
    fontWeight: 600,
    color: "var(--mp-ink)",
  },
  itemClass: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-mute)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  itemName: {
    fontSize: "var(--font-size-xs)",
    color: "var(--mp-ink-2)",
    lineHeight: 1.3,
  },
  itemMeta: {
    fontSize: 10,
    color: "var(--mp-mute)",
    fontFamily: "var(--font-mono, monospace)",
  },
  unsupported: {
    color: "var(--mp-stale)",
    fontWeight: 600,
  },
};
