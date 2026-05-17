# portfolio-options-agent

`portfolio-options-agent` is a full-stack portfolio-aware options income and risk management platform for manual traders. The goal is decision support: helping a trader review positions, risks, income opportunities, and research context without executing trades or promising outcomes.

## Safety Boundaries

- Manual trading decision support only.
- Does not automatically place trades.
- Does not connect to brokers to execute orders.
- Does not store broker usernames, passwords, or MFA secrets.
- Does not scrape Fidelity or other brokers through browser automation.
- Does not bypass MFA.
- Does not promise investment returns.
- Does not provide guaranteed financial advice.
- Does not include real account data, real trades, broker CSVs, private configs, or API keys.

## Current Status

This repository is at initial scaffold status. It contains a minimal FastAPI backend with a `/health` endpoint, placeholder folders for future backend domains, documentation stubs, frontend and script placeholders, and synthetic example YAML files only.

## Planned Architecture

The intended architecture is a full-stack application with:

- A FastAPI backend for APIs, calculations, data validation, report generation, and future adapter integrations.
- A future React or Next.js dashboard for portfolio review and manual decision workflows.
- Domain services for portfolio, options, risk, market data, broker import, reports, agents, and a TradingAgents adapter.
- Explicit, deterministic code for financial calculations and validation.
- An adapter layer for any future integration with `../TradingAgents`.

## Documentation Map

- `docs/current_roadmap.md`: short current direction and active phase.
- `docs/implementation_plan.md`: active and future tasks only.
- `docs/completed_phases_log.md`: archived completed phase history and verification notes.
- `docs/deferred_items.md`: known non-blocking follow-up work.
- `docs/agent_context/`: short Codex and Claude handoff briefs for context-efficient reviews.

## Relationship to `../TradingAgents`

`../TradingAgents` is a separate repository and should remain separate. This project may later integrate with it through an adapter layer or editable Python dependency, but this repository must not modify TradingAgents core files, copy its source code, vendor it as a subfolder, or add it as a git submodule for now.

## Local Backend Quickstart

From this repository:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Run Tests

```bash
cd backend
pytest
```

## Disclaimer

This project is not financial advice. It is not an automated trading system and does not execute trades. Any outputs should be reviewed by a human trader before any real-world action.
