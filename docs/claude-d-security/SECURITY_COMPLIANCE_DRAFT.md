# Security, Compliance, and Privacy Draft

This is a placeholder for Claude D. It is not legal advice and is not a complete compliance program.

## Broker Data Handling

- Treat balances, holdings, quantities, cost basis, option positions, account names/numbers, provider ids, raw payloads, transactions, reports, and screenshots as private user data.
- Agents should use synthetic or redacted data by default.
- Real brokerage data access requires explicit narrow permission.

## SnapTrade userSecret Handling

- Store encrypted at rest.
- Never send to frontend.
- Never log.
- Never include in prompts, tests, fixtures, docs, screenshots, or reports.

## Encryption

- Document encryption envelope and key requirements.
- Define rotation plan before production.
- Do not support plaintext fallback for real credentials.

## Logging Sensitive Data

- Do not log secrets, portal URLs, account numbers, provider ids, raw provider payloads, holdings, balances, or report contents.
- Error responses should be generic and structured.
- Add log redaction tests where practical.

## User Data Deletion and Export

- Future requirement before hosted beta.
- Define what data can be exported.
- Define deletion scope for users, broker credentials, normalized holdings, reports, agent runs, and logs.

## Access Control

- Local dev access guard exists.
- Hosted product needs real authentication and authorization.
- User/account ownership checks must protect every account-specific route.

## Financial Disclaimer

- Product is educational decision support and scenario analysis.
- No personalized financial advice claim.
- No guaranteed returns.
- No automatic trading.
- User remains responsible for trades placed outside the app.

## Educational vs Personalized Advice Boundary

- Avoid "you should buy/sell".
- Use "this review shows", "scenario analysis", "risk factor", and "manual review required".
- LLMs explain deterministic outputs; they do not invent metrics or make final decisions.

## Threat Model

Future threat model should cover:

- Secret leakage
- Broker data leakage to frontend/logs/prompts
- Unauthorized account access
- Prompt injection through report/research content
- Stale data presented as current
- Accidental destructive broker calls
- Supply-chain and dependency risks

## Privacy Policy Notes

- What data is collected.
- Why it is collected.
- Where it is stored.
- How long it is retained.
- How users delete/export data.
- Which third parties are involved.

## Engineering Review Framework Sections

Claude D should apply `docs/shared/ENGINEERING_REVIEW_FRAMEWORK.md` sections on security/privacy, reliability/failure handling, service dependency management, data model/persistence, documentation, and handoff readiness.
