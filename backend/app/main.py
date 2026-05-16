from fastapi import FastAPI

from app.api.routes import accounts, broker_sync, imports, portfolio, reports, users

app = FastAPI(
    title="portfolio-options-agent",
    description="Manual trading decision support API.",
    version="0.1.0",
)

app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(portfolio.router)
app.include_router(broker_sync.router)
app.include_router(imports.router)
app.include_router(reports.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
