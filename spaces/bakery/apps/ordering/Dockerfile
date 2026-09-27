# Bakery ordering MCP server — image for K3s on Raspberry Pi (arm64).
#
# Build context is this directory (spaces/bakery/apps/ordering), matching the
# repo's buildx convention. python:3.12-slim is multi-arch, so the same
# Dockerfile builds for linux/arm64.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

# Dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application package (includes the widget .html/.css/.js assets).
COPY app ./app

EXPOSE 8000

# Single process: carts and order numbers live in-process (see app/mcp/runtime.py),
# so the Deployment runs exactly one replica. Scaling out needs a shared store.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
