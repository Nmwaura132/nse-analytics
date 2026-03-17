FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies for mysqlclient and ML libraries
RUN apt-get update \
    && apt-get install -y default-libmysqlclient-dev build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Create necessary directories for models and database
RUN mkdir -p /app/backend /app/brain

# Start django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
