FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# System deps for mysqlclient, ML libraries, Playwright Chromium, and healthcheck curl
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       default-libmysqlclient-dev build-essential pkg-config curl \
       libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps via Poetry (no dev extras in image)
COPY pyproject.toml poetry.lock /app/
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root \
    && pip install yfinance

# Feature B extra deps (news scraping + AI research) — installed via pip so
# they work regardless of whether poetry.lock has been regenerated yet
RUN pip install playwright beautifulsoup4 "browser-use>=0.1.0" "langchain-openai>=0.1.0"

# Install Playwright Chromium browser
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright-browsers
RUN playwright install chromium --with-deps

# Copy application source
COPY . /app/

# Healthcheck — verify the bot process is alive via its HTTP health endpoint
# (nse_bot.py exposes no HTTP port; we verify the process instead)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import os, sys; sys.exit(0 if os.path.exists('/tmp/nse_bot.pid') else 1)" || exit 1

# Use exec-form so Python receives SIGTERM directly (not via shell)
CMD ["python", "/app/nse_bot.py"]
