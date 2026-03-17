FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies for mysqlclient and ML libraries
RUN apt-get update \
    && apt-get install -y default-libmysqlclient-dev build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies via Poetry
COPY pyproject.toml poetry.lock /app/
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy the entire nse_pro project
COPY . /app/

# Environment variable to include /app in python path (for imports like comprehensive_analyzer)
ENV PYTHONPATH=/app

# Collect static files
WORKDIR /app/nse_backend
RUN python manage.py collectstatic --noinput

# Run with gunicorn in production (4 workers)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
