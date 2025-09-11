# K8s News Engine

A Kubernetes-based news verification and truth analysis system that scrapes news sources, verifies claims, and provides analytics on news quality and trustworthiness.

## Architecture

This project implements a microservices architecture for processing and analyzing news content:

- **Analytics Service** (Python): Computes Event Quality & Impact Score (EQIS) metrics
- **Publisher Service** (Lighttpd + CGI): Web publishing endpoint for verified content

## Services

### analytics-py
Event Quality & Impact Score (EQIS) computation service that analyzes:
- Days in news cycle (recency + persistence)
- Outlet coverage (independent site count)
- Keyword coherence (TF-IDF cosine similarity)
- Best source determination (authority + primacy + influence)
- Claim corroboration (verified vs total; contradictions)
- Correction risk (outlet correction history)

### publisher
Lightweight HTTP server for publishing verified news content via CGI endpoints.

## Project Structure

```
k8s-news-engine/
├── services/
│   ├── analytics-py/        # EQIS analytics service
│   │   ├── configs/         # Configuration files
│   │   ├── k8s/            # Kubernetes manifests
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── worker.py
│   └── publisher/          # Publishing service
│       ├── cgi-bin/        # CGI scripts
│       ├── k8s/            # Kubernetes manifests
│       ├── Dockerfile
│       └── lighttpd.conf
└── docs/                   # Documentation
```

## Prerequisites

- Kubernetes cluster
- PostgreSQL database
- Docker for building images

## Database Schema

The system expects the following tables:
- `events`: News events
- `articles`: News articles
- `event_articles`: Event-article associations
- `claims`: Extracted claims from articles
- `outlet_profiles`: News outlet metadata
- `event_metrics`: Computed EQIS metrics

## Deployment

### Local Development

```bash
# Build analytics service
docker build -t eqis-analytics ./services/analytics-py

# Run analytics service locally
docker run --rm -e DATABASE_URL="postgresql+psycopg2://appuser:newsengine2024@localhost:5432/newsdb" eqis-analytics

# Build publisher service
docker build -t publisher ./services/publisher

# Run publisher service locally
docker run -p 8080:80 publisher
```

### Kubernetes Deployment

```bash
# Deploy analytics as CronJob
kubectl apply -f services/analytics-py/k8s/cronjob.yaml

# Deploy publisher service
kubectl apply -f services/publisher/k8s/
```

## Configuration

### Analytics Service
- Edit `services/analytics-py/configs/metrics.yml` to adjust weights and thresholds
- Set `DATABASE_URL` environment variable or Kubernetes secret

### Publisher Service
- Configure via `services/publisher/lighttpd.conf`
- Modify CGI scripts in `services/publisher/cgi-bin/`

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql+psycopg2://user:pass@host:port/db`)

## Development Notes

This project originated from a conceptual discussion about news verification and truth analysis, evolving into a microservices-based implementation for processing news content at scale.