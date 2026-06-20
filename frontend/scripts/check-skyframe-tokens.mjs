#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();
const srcRoot = path.join(repoRoot, "src");
const legacyColorTokenPattern = /var\(--color-[^)]+\)/g;
const rawHexPattern = /#[0-9A-Fa-f]{3,8}\b/g;

// Migration baseline captured in P29B-T6C. Keep this list shrinking as
// surfaces move to --mp-* / --skyframe-* tokens. The guard is warning-only
// during migration; it catches new drift without blocking intentional legacy.
const legacyColorUsageBaseline = new Map([
  ["src/components/account/AccountSelector.tsx", 10],
  ["src/components/broker/BrokerAccountRow.tsx", 22],
  ["src/components/broker/BrokerConnectionList.tsx", 22],
  ["src/components/broker/ConnectFlowPanel.tsx", 22],
  ["src/components/broker/SafetyNoticePanel.tsx", 6],
  ["src/components/broker/SyncRunStatus.tsx", 6],
  ["src/components/freshness/BrokerFreshnessBar.tsx", 22],
  ["src/components/freshness/PortfolioWarningsPanel.tsx", 19],
  ["src/components/layout/AppearanceControl.tsx", 6],
  ["src/components/marketdata/MarketDataStatusPanel.tsx", 8],
  ["src/components/portfolio/PortfolioSummaryCard.tsx", 8],
  ["src/components/positions/CashPositionsView.tsx", 15],
  ["src/components/positions/OptionPositionsView.tsx", 22],
  ["src/components/positions/PositionsTabs.tsx", 4],
  ["src/components/positions/StockPositionsView.tsx", 18],
  ["src/components/risk/RiskReviewPanel.tsx", 36],
  ["src/pages/BrokerConnectionPage.tsx", 12],
  ["src/pages/MarketDataPage.tsx", 8],
  ["src/pages/RiskReviewPage.tsx", 11],
  ["src/styles/globals.css", 7],
]);

const rawHexAllowedFiles = new Set(["src/styles/globals.css"]);

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return walk(fullPath);
    }
    return /\.(css|tsx?|jsx?)$/.test(entry.name) ? [fullPath] : [];
  });
}

function relativePath(filePath) {
  return path.relative(repoRoot, filePath).split(path.sep).join("/");
}

function matchesByLine(source, pattern) {
  const findings = [];
  const lines = source.split(/\r?\n/);
  for (const [idx, line] of lines.entries()) {
    const matches = line.match(pattern);
    if (matches) {
      findings.push({ line: idx + 1, matches });
    }
  }
  return findings;
}

const legacyFindings = new Map();
const rawHexFindings = [];

for (const filePath of walk(srcRoot)) {
  const rel = relativePath(filePath);
  const source = fs.readFileSync(filePath, "utf8");
  const legacy = matchesByLine(source, legacyColorTokenPattern);
  const rawHex = matchesByLine(source, rawHexPattern);

  if (legacy.length > 0) {
    const count = legacy.reduce((sum, finding) => sum + finding.matches.length, 0);
    legacyFindings.set(rel, { count, lines: legacy.map((finding) => finding.line) });
  }

  if (rawHex.length > 0 && !rawHexAllowedFiles.has(rel)) {
    rawHexFindings.push({
      file: rel,
      lines: rawHex.map((finding) => finding.line),
    });
  }
}

const warnings = [];

for (const [file, finding] of legacyFindings) {
  const baseline = legacyColorUsageBaseline.get(file);
  if (baseline === undefined) {
    warnings.push(`${file}: ${finding.count} legacy --color-* use(s) outside the migration baseline`);
  } else if (finding.count > baseline) {
    warnings.push(
      `${file}: ${finding.count} legacy --color-* use(s), above baseline ${baseline}`
    );
  }
}

for (const [file, baseline] of legacyColorUsageBaseline) {
  const current = legacyFindings.get(file)?.count ?? 0;
  if (current < baseline) {
    console.log(
      `[skyframe-token-guard] ${file}: legacy --color-* count dropped from ${baseline} to ${current}; update the baseline when this migration slice is accepted.`
    );
  }
}

for (const finding of rawHexFindings) {
  warnings.push(`${finding.file}: raw hex color outside globals.css on line(s) ${finding.lines.join(", ")}`);
}

if (warnings.length > 0) {
  console.warn("[skyframe-token-guard] Warning-only during migration. Review these token drift findings:");
  for (const warning of warnings) {
    console.warn(`- ${warning}`);
  }
  console.warn("[skyframe-token-guard] Prefer --mp-* / --skyframe-* tokens or update the documented baseline after review.");
} else {
  console.log("[skyframe-token-guard] No new raw hex or legacy --color-* drift outside the P29B-T6C baseline.");
}
