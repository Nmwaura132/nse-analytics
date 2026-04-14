FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# System deps for mysqlclient, ML libraries, and healthcheck curl
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       default-libmysqlclient-dev build-essential pkg-config curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps via Poetry (no dev extras in image)
COPY pyproject.toml poetry.lock /app/
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --without dev \
    && pip install yfinance  # ensure yfinance is available for real NSE data

# Copy application source
COPY . /app/

# Healthcheck — verify the bot process is alive via its HTTP health endpoint
# (nse_bot.py exposes no HTTP port; we verify the process instead)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import os, sys; sys.exit(0 if os.path.exists('/tmp/nse_bot.pid') else 1)" || exit 1

# Use exec-form so Python receives SIGTERM directly (not via shell)
CMD ["python", "/app/nse_bot.py"]
