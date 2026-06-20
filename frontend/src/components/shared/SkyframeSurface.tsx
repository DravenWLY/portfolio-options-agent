import type { CSSProperties, ReactNode } from "react";

interface SkyframeSurfaceProps {
  children: ReactNode;
  /**
   * Extra classes layered after `skyframe-surface` — e.g. a surface-specific
   * token scope like `reports-skyframe`, and/or `mp-surface` for the MP font
   * stack.
   */
  className?: string;
  /** Max content width; defaults to the standard workspace width. */
  maxWidth?: number | string;
  /** Style overrides merged last (use sparingly). */
  style?: CSSProperties;
}

/**
 * SkyframeSurface — the shared Portfolio Copilot Skyframe page surface: a framed
 * workspace container with a top-anchored sky wash that fades into the page
 * (surface atmosphere only, never a persistent full-page tint). Pages compose
 * their PageHeader and content inside it.
 *
 * The visual/token behavior lives in the `.skyframe-surface` rules in
 * globals.css (P29B-T6A); this component is the typed, reusable React boundary
 * plus the per-page max width. It is route-agnostic: it imports nothing
 * Reports-specific and reads only `--skyframe-*` / `--mp-*` tokens.
 *
 * Sky is surface atmosphere; controls, focus, links, and status must keep
 * contrast-safe MP/Skyframe accents (STYLE.md: "calm sky atmosphere, crisp
 * analyst structure").
 */
export default function SkyframeSurface({
  children,
  className,
  maxWidth = "var(--skyframe-page-max)",
  style,
}: SkyframeSurfaceProps) {
  const cls = className ? `skyframe-surface ${className}` : "skyframe-surface";
  return (
    <div className={cls} style={{ maxWidth, ...style }}>
      {children}
    </div>
  );
}
