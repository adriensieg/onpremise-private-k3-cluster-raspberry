# Works for linux/arm64 (Raspberry Pi k3s) and linux/amd64.
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ROOT_PATH=/scanning \
    DATA_FILE=/data/data.txt

WORKDIR /app

# Install dependencies first (better layer caching)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Writable data directory for the txt store
RUN mkdir -p /data

EXPOSE 8000

# Single worker is fine for a txt-file store (avoids write races across workers)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
