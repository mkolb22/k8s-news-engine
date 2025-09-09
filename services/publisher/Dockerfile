FROM alpine:3.20

# Install lighttpd, python3, and postgresql client
RUN apk add --no-cache \
    lighttpd \
    python3 \
    py3-pip \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev

# Install psycopg2 and ML dependencies using Alpine package manager
RUN apk add --no-cache \
    py3-psycopg2 \
    py3-numpy \
    py3-scipy \
    py3-scikit-learn \
    py3-nltk

# Install additional Python packages via pip for missing dependencies
RUN pip3 install --break-system-packages --no-cache-dir \
    nltk==3.8.1

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')" || true

# Create directories
RUN mkdir -p /var/www/htdocs \
    && mkdir -p /var/www/cgi-bin \
    && mkdir -p /var/log/lighttpd

# Copy web content and CGI scripts
COPY htdocs/ /var/www/htdocs/
COPY cgi-bin/ /var/www/cgi-bin/
RUN chmod +x /var/www/cgi-bin/*

# Create non-root user
RUN adduser -D -s /bin/sh -u 1000 publisher && \
    chown -R publisher:publisher /var/www /var/log/lighttpd

# Note: lighttpd.conf will be mounted from ConfigMap at /etc/lighttpd/lighttpd.conf
EXPOSE 8080

# Switch to non-root user  
USER publisher

CMD ["lighttpd", "-D", "-f", "/etc/lighttpd/lighttpd.conf"]
