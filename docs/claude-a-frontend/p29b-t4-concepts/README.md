# P29B-T4 Claude Design concepts — drop folder

Put the Claude Design output here so Claude A (Claude Code) can review it. Claude
Code reads images / PDFs / text / code from disk; it cannot open the Claude
Design tool or its share links.

## Preferred: screenshots (PNG/JPG)
Export per direction × key state × theme. Suggested naming:

    dirA-full-report-dark.png
    dirA-source-snapshot-dark.png
    dirA-partial-coverage-dark.png
    dirA-skipped-public-dark.png
    dirA-agent-unavailable-dark.png
    dirA-validation-failed-dark.png
    dirA-full-report-light.png        (one light shot per direction is enough)
    dirB-...   dirC-...

At minimum: one "full report with public roles" + one degraded state per
direction, in dark, plus one light shot per direction.

## Optional: exported code (reference only)
If Claude Design exports HTML/React/CSS, drop it in a subfolder here
(e.g. `dirA-export/`). It is **reference only** — do NOT replace anything in
`frontend/src/`. We treat tool output as a concept, then implement properly in
the real design system.

## Optional: the tool's written rationale
Paste each direction's rationale into `directions.md` here.

## Rules
- Synthetic/demo data only (the design used synthetic payloads — keep it that way).
- No secrets, no real account/broker data, nothing from `.env`/`data`/`reports`.
- This folder is concept scratch; it is not shipped UI.
