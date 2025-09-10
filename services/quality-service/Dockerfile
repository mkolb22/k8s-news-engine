# Quality Service Dockerfile
# Lightweight Python service for computing article quality scores and event groupings

FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    musl-dev \
    tzdata

# Set timezone environment variable
ENV TZ=UTC

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create log directory
RUN mkdir -p /var/log

# Create non-root user
RUN adduser -D -s /bin/sh -u 1000 qualityuser

# Change ownership of app directory
RUN chown -R qualityuser:qualityuser /app /var/log

# Switch to non-root user
USER qualityuser

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD python3 -c "import psycopg2; import os; psycopg2.connect(os.environ['DATABASE_URL']).close()" || exit 1

# Run the service
CMD ["python3", "main.py"]