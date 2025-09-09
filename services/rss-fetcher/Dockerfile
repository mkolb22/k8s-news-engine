# Multi-stage Docker build for Go RSS Fetcher Service
# Stage 1: Build the Go binary
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY *.go ./

# Build the binary with optimizations for small size
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -a -installsuffix cgo \
    -ldflags="-w -s" \
    -o rss-fetcher .

# Stage 2: Create minimal runtime container
FROM alpine:3.18

# Install CA certificates and timezone data for HTTPS and time handling
RUN apk --no-cache add ca-certificates tzdata

# Create non-root user for security
RUN adduser -D -s /bin/sh rss-fetcher

# Set working directory
WORKDIR /app

# Copy the binary from builder stage
COPY --from=builder /app/rss-fetcher .

# Copy timezone data
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Change ownership to non-root user
RUN chown -R rss-fetcher:rss-fetcher /app

# Switch to non-root user
USER rss-fetcher

# Expose port (if needed for health checks)
EXPOSE 8080

# Set default environment variables
ENV TZ=UTC
ENV DATABASE_URL=postgresql://truth:truth@localhost:5432/truthdb
ENV FETCH_INTERVAL=300

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f rss-fetcher || exit 1

# Default command - run continuous mode
CMD ["./rss-fetcher"]