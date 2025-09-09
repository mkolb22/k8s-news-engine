# RSS Fetcher Service

A high-performance RSS feed fetcher written in Go that processes news articles and stores them in PostgreSQL.

## Features

- **ConfigMap-based feed management**: RSS feeds are configured via Kubernetes ConfigMap
- **Efficient Go implementation**: Low memory footprint with Alpine Linux container
- **Database integration**: PostgreSQL backend for article storage
- **Event linking**: Automatic linking of articles to events based on keyword matching
- **Content extraction**: Full article text extraction from RSS feed URLs
- **Graceful shutdown**: Proper signal handling for Kubernetes deployments

## Configuration

### Feed Configuration (ConfigMap)

RSS feeds are configured in `k8s/configmap.yaml`:

```yaml
feeds:
  - url: "https://feeds.bbci.co.uk/news/world/rss.xml"
    outlet: "BBC World"
    interval: 15  # minutes
    category: "world"
```

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `FETCH_INTERVAL`: Global fetch interval in seconds (default: 300)
- `FEEDS_CONFIG_PATH`: Path to feeds config file (default: /config/feeds.yaml)

## Deployment

### Local Development

```bash
# Build the binary
go build -o rss-fetcher .

# Run once
./rss-fetcher --once

# Run continuous
./rss-fetcher
```

### Kubernetes Deployment

```bash
# Apply ConfigMap
kubectl apply -f k8s/configmap.yaml

# Deploy the service
kubectl apply -f k8s/deployment.yaml

# Check logs
kubectl logs -f deployment/rss-fetcher
```

### Docker Build

```bash
# Build the container
docker build -t k8s-news-engine/rss-fetcher:latest .

# Run locally
docker run --rm \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  k8s-news-engine/rss-fetcher:latest
```

## Database Schema

The service expects these tables:

- `rss_feeds`: Feed URLs and metadata
- `articles`: Stored articles with full text
- `events`: News events for article linking
- `event_articles`: Links between events and articles

## Architecture

- **Multi-stage Docker build**: Compiles in golang:alpine, runs in minimal Alpine
- **Non-root container**: Security hardened with restricted permissions
- **ConfigMap integration**: Dynamic feed updates without rebuilding
- **Resource efficient**: 64-128MB memory, 50-200m CPU

## Feed Management

Feeds are automatically synced from ConfigMap to database on startup:
1. Loads feeds from mounted ConfigMap
2. Deactivates feeds not in ConfigMap
3. Inserts/updates feeds from ConfigMap
4. Processes only active feeds