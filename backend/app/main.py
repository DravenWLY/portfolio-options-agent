from fastapi import FastAPI

from app.api.routes import accounts, users

app = FastAPI(
    title="portfolio-options-agent",
    description="Manual trading decision support API.",
    version="0.1.0",
)

app.include_router(users.router)
app.include_router(accounts.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
