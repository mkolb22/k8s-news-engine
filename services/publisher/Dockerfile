# REQUIRED: This service must always use Alpine Linux as the base image
# Alpine provides a minimal, secure foundation with a small attack surface
# Current LTS version: 3.20 (supported until 2026-04)
FROM alpine:3.20

# Install lighttpd, python3, postgresql client, and timezone data
RUN apk add --no-cache \
    lighttpd \
    python3 \
    py3-pip \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    tzdata

# Install psycopg2 and ML dependencies using Alpine package manager
RUN apk add --no-cache \
    py3-psycopg2 \
    py3-numpy \
    py3-scipy \
    py3-scikit-learn \
    py3-nltk

# Install additional Python packages via pip for NLP dependencies
RUN pip3 install --break-system-packages --no-cache-dir \
    nltk==3.8.1

# Download NLTK data including NER support
RUN python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('maxent_ne_chunker'); nltk.download('words'); nltk.download('averaged_perceptron_tagger')" || true

# Create directories including a writable run directory for PID files
RUN mkdir -p /var/www/htdocs \
    && mkdir -p /var/www/cgi-bin \
    && mkdir -p /var/log/lighttpd \
    && mkdir -p /app \
    && mkdir -p /tmp/run \
    && mkdir -p /var/run/lighttpd \
    && chmod 777 -R /tmp \
    && chmod o+t -R /tmp

# Copy web content and CGI scripts
COPY htdocs/ /var/www/htdocs/
COPY cgi-bin/ /var/www/cgi-bin/
COPY startup_health_check.py /app/startup_health_check.py
COPY start_lighttpd.sh /app/start_lighttpd.sh
RUN chmod +x /var/www/cgi-bin/* && chmod +x /app/startup_health_check.py && chmod +x /app/start_lighttpd.sh

# Create non-root user
RUN adduser -D -s /bin/sh -u 1000 publisher && \
    chown -R publisher:publisher /var/www /var/log/lighttpd /app /tmp/run /var/run/lighttpd

# Set timezone environment variable for consistent timezone handling
ENV TZ=UTC

# Note: lighttpd.conf will be mounted from ConfigMap at /etc/lighttpd/lighttpd.conf
EXPOSE 8080

# Switch to non-root user  
USER publisher

CMD ["sh", "-c", "python3 /app/startup_health_check.py && /app/start_lighttpd.sh"]
