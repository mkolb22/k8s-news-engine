# Quality Service Dockerfile
# Lightweight Python service for computing article quality scores and event groupings
#
# Version History:
# v1.0.0 - Initial release with basic quality scoring
# v1.1.0 - Added outlet authority from database
# v1.2.0 - Added comprehensive Writing Quality Analysis
# v1.2.1 - Changed quality scores to whole numbers (round down ≤0.5, round up >0.5)
# v1.3.0 - Added comprehensive Agency Reputation Metrics system with awards tracking
# v1.4.0 - Added RSS feed to news agency validation and relationship enforcement
# v1.5.0 - Added improved NER system with spaCy for better event grouping
# v1.5.1 - Added startup database health check with NER model validation
# v1.5.2 - Fixed health check to use correct NER column names (ner_extracted_at)
#
# Build command: docker build -t k8s-news-engine/quality-service:v1.5.2 .

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

# Download spaCy English model
RUN python3 -m spacy download en_core_web_sm

# Copy application code
COPY main.py .
COPY writing_quality_analyzer.py .
COPY reputation_analyzer.py .
COPY rss_agency_validator.py .
COPY improved_ner.py .
COPY startup_health_check.py .

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
CMD ["sh", "-c", "python3 startup_health_check.py && python3 main.py"]