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

# Start django from the correct sub-directory
WORKDIR /app/nse_backend
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
