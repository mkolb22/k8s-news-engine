# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

K8s News Engine is a microservices-based news verification and truth analysis system. It processes news content to compute quality metrics, verify claims, and provide trustworthiness scores using the Event Quality & Impact Score (EQIS) algorithm.

## Architecture

The system consists of Python-based analytics services that:
1. **Fetch and parse** news articles from various sources
2. **Extract claims** and verify them against multiple sources
3. **Compute EQIS metrics** including coverage, coherence, and corroboration
4. **Publish verified content** through a lightweight HTTP service

### Key Components
- **analytics-py**: Python service computing EQIS scores using scikit-learn for TF-IDF analysis
- **publisher**: Lighttpd-based service with CGI scripts for content delivery
- **PostgreSQL database** with tables: events, articles, event_articles, claims, outlet_profiles, event_metrics

## Common Commands

```bash
# Build services
docker build -t eqis-analytics ./services/analytics-py
docker build -t publisher ./services/publisher

# Run locally
docker run --rm -e DATABASE_URL="postgresql+psycopg2://truth:truth@localhost:5432/truthdb" eqis-analytics
docker run -p 8080:80 publisher

# Deploy to Kubernetes
kubectl apply -f services/analytics-py/k8s/cronjob.yaml
kubectl apply -f services/publisher/k8s/

# Check analytics job status
kubectl get cronjobs
kubectl get jobs
kubectl logs -f job/<job-name>
```

## Development Guidelines

### Python Services (analytics-py)
- Uses SQLAlchemy for database operations
- Pandas/NumPy for data processing
- scikit-learn for TF-IDF coherence analysis
- Configuration via YAML files in `configs/`
- Runs as Kubernetes CronJob

### Database Schema
The service expects these tables to exist:
- `events`: News events to analyze
- `articles`: Individual news articles
- `event_articles`: Links events to articles
- `claims`: Extracted claims with verification status
- `outlet_profiles`: News source metadata (authority, correction rates)
- `event_metrics`: Computed EQIS scores and components

### EQIS Metrics Computed
1. **Days in news cycle**: Recency and persistence scoring
2. **Coverage**: Number of independent news outlets
3. **Coherence**: TF-IDF cosine similarity between articles
4. **Best source**: Authority + primacy + influence scoring
5. **Corroboration**: Verified vs contested claims ratio
6. **Correction risk**: Based on outlet historical correction rates

## Configuration

- Database connection: Set `DATABASE_URL` environment variable
- Metrics weights: Edit `services/analytics-py/configs/metrics.yml`
- CronJob schedule: Modify `services/analytics-py/k8s/cronjob.yaml`

## Documentation Standards

### Service Documentation
- **Required**: Each service must have a comprehensive `README.md` in its directory
- **Standard**: Follow the template in `docs/SERVICE-DOCUMENTATION-STANDARD.md`
- **Change Tracking**: Document all code changes in service changelog with version numbers
- **Testing**: Include validation results and testing methodology

### Current Documentation Status
- ✅ **quality-service**: Complete with NER feature documentation (v1.1.0)
- 🔄 **rss-fetcher**: Needs standardization
- 🔄 **publisher**: Needs standardization  
- 🔄 **analytics-py**: Needs standardization
- 🔄 **claim-extractor**: Needs standardization

### Development Workflow
1. **Local Testing**: Test all code changes outside containers first
2. **Semantic Versioning**: Use major.minor.patch for container versions (never "latest")
3. **Container Updates**: Update Kubernetes manifests with new image tags before deployment
4. **Documentation**: Update service README with every code change
5. **Validation**: Confirm functionality after deployment and document results