/**
 * MpIcon — typed monochrome semantic icon system for the Modern Portfolio Desk.
 *
 * Stroke-based SVGs using currentColor. No emoji, no platform-dependent
 * pictograms, no external icon dependencies.
 *
 * All icons render in a 24×24 viewBox with configurable display size,
 * stroke width, and styling. They inherit color from their parent via
 * currentColor, so icon color is controlled by the container.
 */

export type MpIconName =
  | "overview"
  | "review"
  | "agent"
  | "reports"
  | "portfolio"
  | "settings"
  | "lock"
  | "logo"
  | "broker"
  | "clock"
  | "shield"
  | "info"
  | "check"
  | "x"
  | "chevron-r"
  | "chevron-d"
  | "arrow-r"
  | "alert"
  | "spark"
  | "sun"
  | "moon"
  | "circle"
  | "menu"
  | "search"
  | "send";

interface MpIconProps {
  name: MpIconName;
  size?: number;
  strokeWidth?: number;
  style?: React.CSSProperties;
  className?: string;
}

export default function MpIcon({
  name,
  size = 14,
  strokeWidth = 1.5,
  style,
  className,
}: MpIconProps) {
  const svg = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    style: { flexShrink: 0, ...style } as React.CSSProperties,
    className,
    "aria-hidden": true as const,
  };

  switch (name) {
    case "overview":
      return (
        <svg {...svg}>
          <rect x="3" y="3" width="7" height="9" />
          <rect x="14" y="3" width="7" height="5" />
          <rect x="14" y="12" width="7" height="9" />
          <rect x="3" y="16" width="7" height="5" />
        </svg>
      );
    case "review":
      return (
        <svg {...svg}>
          <path d="M4 7h13M4 12h10M4 17h7" />
          <path d="M17 14l3 3-6 6h-3v-3z" />
        </svg>
      );
    case "agent":
      return (
        <svg {...svg}>
          <circle cx="12" cy="8" r="4" />
          <path d="M5 21c0-3.9 3.1-7 7-7s7 3.1 7 7" />
          <path d="M9 8h6" />
        </svg>
      );
    case "reports":
      return (
        <svg {...svg}>
          <path d="M7 3h10l3 3v14a1 1 0 01-1 1H5a1 1 0 01-1-1V4a1 1 0 011-1h2z" />
          <path d="M8 12h8M8 16h5M8 8h4" />
        </svg>
      );
    case "portfolio":
      return (
        <svg {...svg}>
          <path d="M3 21V8l9-5 9 5v13" />
          <path d="M9 21v-7h6v7" />
        </svg>
      );
    case "settings":
      return (
        <svg {...svg}>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15l1.5 2.6-2 1.2-1.7-.7a7 7 0 01-2.4 1.4L14 21h-4l-.8-2.5a7 7 0 01-2.4-1.4l-1.7.7-2-1.2L4.6 15a7 7 0 010-6L3.1 6.4l2-1.2 1.7.7A7 7 0 019.2 4.5L10 3h4l.8 2.5a7 7 0 012.4 1.4l1.7-.7 2 1.2L19.4 9a7 7 0 010 6z" />
        </svg>
      );
    case "lock":
      return (
        <svg {...svg}>
          <rect x="4" y="11" width="16" height="10" rx="1.5" />
          <path d="M8 11V7a4 4 0 018 0v4" />
        </svg>
      );
    case "logo":
      return (
        <svg {...svg}>
          <path d="M4 18L10 6l4 8 6-12" />
          <circle cx="10" cy="6" r="1.4" fill="currentColor" stroke="none" />
          <circle cx="14" cy="14" r="1.4" fill="currentColor" stroke="none" />
        </svg>
      );
    case "broker":
      return (
        <svg {...svg}>
          <rect x="3" y="9" width="18" height="12" rx="1" />
          <path d="M3 12h18M7 9V5a3 3 0 016 0v4" />
        </svg>
      );
    case "clock":
      return (
        <svg {...svg}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </svg>
      );
    case "shield":
      return (
        <svg {...svg}>
          <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z" />
        </svg>
      );
    case "info":
      return (
        <svg {...svg}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v.5M12 11v5" />
        </svg>
      );
    case "check":
      return (
        <svg {...svg}>
          <path d="M5 12l4 4L19 6" />
        </svg>
      );
    case "x":
      return (
        <svg {...svg}>
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      );
    case "chevron-r":
      return (
        <svg {...svg}>
          <path d="M9 6l6 6-6 6" />
        </svg>
      );
    case "chevron-d":
      return (
        <svg {...svg}>
          <path d="M6 9l6 6 6-6" />
        </svg>
      );
    case "arrow-r":
      return (
        <svg {...svg}>
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      );
    case "alert":
      return (
        <svg {...svg}>
          <path d="M12 3l10 18H2L12 3z" />
          <path d="M12 10v5M12 18.5v.5" />
        </svg>
      );
    case "spark":
      return (
        <svg {...svg}>
          <path d="M3 14l4-6 4 4 5-9 5 14" />
        </svg>
      );
    case "sun":
      return (
        <svg {...svg}>
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      );
    case "moon":
      return (
        <svg {...svg}>
          <path d="M20 14A8 8 0 1110 4a7 7 0 0010 10z" />
        </svg>
      );
    case "circle":
      return (
        <svg {...svg}>
          <circle cx="12" cy="12" r="9" />
        </svg>
      );
    case "menu":
      return (
        <svg {...svg}>
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      );
    case "search":
      return (
        <svg {...svg}>
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.5-4.5" />
        </svg>
      );
    case "send":
      return (
        <svg {...svg}>
          <path d="M3 12l18-8-7 18-3-8z" />
        </svg>
      );
    default:
      return null;
  }
}
