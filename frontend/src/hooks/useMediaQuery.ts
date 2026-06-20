import { useEffect, useState } from "react";

/**
 * useMediaQuery — subscribe to a CSS media query.
 *
 * Used by the Reports rail to switch between the wide two-column rail (sticky,
 * internally scrolling) and the ≤1100px single-column disclosure so the reading
 * pane is never pushed off-screen. SPA-only (window always present).
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia(query).matches : false,
  );

  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = () => setMatches(mql.matches);
    onChange();
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, [query]);

  return matches;
}
