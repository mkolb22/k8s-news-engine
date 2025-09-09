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

# Install psycopg2 using Alpine package manager
RUN apk add --no-cache py3-psycopg2

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
