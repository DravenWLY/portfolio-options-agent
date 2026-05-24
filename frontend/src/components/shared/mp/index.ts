/**
 * P20A-T1 — Modern Portfolio Desk shared primitives.
 *
 * Translated (not pasted) from the typed prototype primitives in
 *   design/prototype/portfolio-copilot-modern-desk/Portfolio Copilot/components.tsx
 *
 * Broker-/data-agnostic. Consume --mp-* tokens only. No backend schema
 * coupling. No `window.*` globals or prototype-only state.
 */
export { default as Badge } from "./Badge";
export { default as Pill } from "./Pill";
export { default as Panel } from "./Panel";
export { default as KV } from "./KV";
export { default as Stat } from "./Stat";
export { default as FreshnessDial } from "./FreshnessDial";
export { default as PageHeader } from "./PageHeader";
export { default as SafetyStrip } from "./SafetyStrip";
export { default as DemoChip } from "./DemoChip";
export type { MpTone } from "./tokens";
