from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.api.routes import accounts, agent_team, broker_sync, imports, portfolio, reports, symbols, trade_reviews, users
from app.core.access_guard import require_local_access
from app.services.symbol_directory import run_symbol_directory_startup_refresh_if_enabled


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    run_symbol_directory_startup_refresh_if_enabled()
    yield


app = FastAPI(
    title="portfolio-options-agent",
    description="Manual trading decision support API.",
    version="0.1.0",
    lifespan=lifespan,
)

protected = [Depends(require_local_access)]

app.include_router(users.router, dependencies=protected)
app.include_router(accounts.router, dependencies=protected)
app.include_router(portfolio.router, dependencies=protected)
app.include_router(broker_sync.router, dependencies=protected)
app.include_router(imports.router, dependencies=protected)
app.include_router(reports.router, dependencies=protected)
app.include_router(trade_reviews.router, dependencies=protected)
app.include_router(agent_team.router, dependencies=protected)
app.include_router(symbols.router, dependencies=protected)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
