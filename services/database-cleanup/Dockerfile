# Database Cleanup CronJob Container
FROM alpine:3.19

# Install PostgreSQL client
RUN apk add --no-cache postgresql-client

# Create cleanup script
COPY cleanup.sh /usr/local/bin/cleanup.sh
RUN chmod +x /usr/local/bin/cleanup.sh

# Create non-root user
RUN adduser -D -s /bin/sh cleanup

USER cleanup

ENTRYPOINT ["/usr/local/bin/cleanup.sh"]