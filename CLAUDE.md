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
- **quality-service**: NER processing service using spaCy for entity extraction and event grouping
- **rss-fetcher**: Go-based RSS feed processing service with duplicate detection
- **PostgreSQL database** with tables: events, articles, event_articles, claims, outlet_profiles, event_metrics

## Common Commands

```bash
# Build services
docker build -t eqis-analytics ./services/analytics-py
docker build -t publisher ./services/publisher

# Run locally (credentials now managed via Kubernetes secrets)
docker run --rm -e DATABASE_URL="postgresql+psycopg2://appuser:newsengine2024@localhost:5432/newsdb" eqis-analytics
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

## Directory Structure Guidelines

### Working Directories
- **`./services/`**: Active service development and Kubernetes manifests
- All Kubernetes manifests are located in `./services/*/k8s/` directories
- Service source code and configurations are in respective service directories

### Archive Directory
- **`./archive/`**: Contains historical deployment configurations and deprecated files
- **DO NOT** work in or modify the `./archive/` directory unless explicitly requested
- Archive directory is preserved for reference only and should remain untouched

## Configuration

### Database Credentials (Security Enhanced)
- **Production**: Credentials managed via Kubernetes secret `postgres-secret` in `news-engine` namespace
- **Environment Variables**: DATABASE_URL constructed dynamically from individual secret components
- **Runtime Access Only**: Database passwords never stored in deployment manifests
- **Secret Components**: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
- **Credential Rotation**: Update `postgres-secret` to rotate credentials across all services

### Other Configuration
- Metrics weights: Edit `services/analytics-py/configs/metrics.yml`
- CronJob schedule: Modify `services/analytics-py/k8s/cronjob.yaml`

## Documentation Standards

### Service Documentation
- **Required**: Each service must have a comprehensive `README.md` in its directory
- **Standard**: Follow the template in `docs/SERVICE-DOCUMENTATION-STANDARD.md`
- **Change Tracking**: Document all code changes in service changelog with version numbers
- **Testing**: Include validation results and testing methodology

### Current Documentation Status
- ✅ **quality-service**: Complete with NER feature documentation (v1.5.2)
- 🔄 **rss-fetcher**: Needs standardization (v2.1.0)
- 🔄 **publisher**: Needs standardization (v1.1.0)
- 🔄 **analytics-py**: Needs standardization (v2.0.2)
- 🔄 **claim-extractor**: Needs standardization

### Development Workflow
1. **Local Testing**: Test all code changes outside containers first
2. **Semantic Versioning**: Use major.minor.patch for container versions (never "latest")
3. **Container Updates**: Update Kubernetes manifests with new image tags before deployment
4. **Documentation**: Update service README with every code change
5. **Validation**: Confirm functionality after deployment and document results

## Security Implementation

### Database Credential Management
All services implement secure database credential management using Kubernetes secrets:

**Implementation Pattern:**
```yaml
command: ["/bin/sh"]
args: ["-c", "export DATABASE_URL=\"postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}\" && [start_command]"]
env:
- name: DB_USER
  valueFrom:
    secretKeyRef:
      name: postgres-secret
      key: app-user
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: postgres-secret
      key: app-password
```

**Security Benefits:**
- ✅ **Runtime-only credential access**: Passwords only available during container execution
- ✅ **No hardcoded credentials**: Zero secrets in deployment manifests or source code
- ✅ **Centralized management**: Single `postgres-secret` serves all services
- ✅ **Easy rotation**: Update secret once, affects all services automatically
- ✅ **Audit trail**: Kubernetes RBAC tracks all secret access

**Services Using Secure Credentials:**
- analytics-py (v2.0.2) - CronJob with startup health checks
- publisher (v1.1.0) - Web service with runtime credential injection  
- quality-service (v1.5.2) - Background processing with NER validation
- rss-fetcher (v2.1.0) - Go binary with shell-based credential construction