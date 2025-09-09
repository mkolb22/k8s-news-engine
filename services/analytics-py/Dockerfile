FROM python:3.11-alpine

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies required for NumPy/SciPy/scikit-learn
# Note: These packages require compilation and may take time to build
RUN apk add --no-cache \
    gcc \
    g++ \
    gfortran \
    musl-dev \
    linux-headers \
    openblas-dev \
    lapack-dev \
    libffi-dev \
    postgresql-dev

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Clean up build dependencies to reduce image size
RUN apk del gcc g++ gfortran musl-dev linux-headers postgresql-dev

# Install runtime dependencies
RUN apk add --no-cache libpq openblas lapack

# Copy application code
COPY worker.py ./
COPY configs ./configs

# Create non-root user
RUN adduser -D -s /bin/sh -u 1000 analytics && \
    chown -R analytics:analytics /app

# Switch to non-root user
USER analytics

# Default: run once and exit (good for CronJob)
CMD ["python", "worker.py"]
