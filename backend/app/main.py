from fastapi import Depends, FastAPI

from app.api.routes import accounts, broker_sync, imports, portfolio, reports, users
from app.core.access_guard import require_local_access

app = FastAPI(
    title="portfolio-options-agent",
    description="Manual trading decision support API.",
    version="0.1.0",
)

protected = [Depends(require_local_access)]

app.include_router(users.router, dependencies=protected)
app.include_router(accounts.router, dependencies=protected)
app.include_router(portfolio.router, dependencies=protected)
app.include_router(broker_sync.router, dependencies=protected)
app.include_router(imports.router, dependencies=protected)
app.include_router(reports.router, dependencies=protected)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
