from fastapi import FastAPI

app = FastAPI(
    title="portfolio-options-agent",
    description="Manual trading decision support API.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
