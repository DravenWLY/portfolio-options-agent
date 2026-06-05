FROM python:3.11-slim

WORKDIR /app

ARG UV_VERSION=0.11.18
ARG INSTALL_LIVE_LLM=false

# Install locked core runtime dependencies first for reproducible image builds.
# Provider SDKs are optional `live-llm` extras and are intentionally not exported
# by default: mock is the default and adapters import live-provider SDKs lazily.
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir "uv==${UV_VERSION}" \
    && if [ "$INSTALL_LIVE_LLM" = "true" ]; then export UV_EXTRA_ARGS="--extra live-llm"; else export UV_EXTRA_ARGS=""; fi \
    && uv --quiet export --frozen --no-dev --no-emit-project ${UV_EXTRA_ARGS} --format requirements.txt --output-file /tmp/requirements.lock \
    && pip install --no-cache-dir -r /tmp/requirements.lock \
    && rm /tmp/requirements.lock

COPY . .

# Install the backend package itself without resolving dependencies again; the
# locked runtime dependencies were installed in the layer above.
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8000

# Run migrations then start the server. DATABASE_URL is injected by docker-compose.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
