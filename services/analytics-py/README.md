# Analytics Service - EQIS Computation

Python service that computes Event Quality & Impact Score (EQIS) metrics for news articles.

## Container Requirements

This service uses the **official Python Alpine container** (`python:3.11-alpine`) for consistency with other services.

**Important Build Notes:**
- Build time: 10-15 minutes due to compiling NumPy, SciPy, and scikit-learn from source
- Alpine packages like `openblas-dev`, `lapack-dev`, and `gfortran` are required for numerical libraries
- The Dockerfile uses multi-layer optimization to minimize final image size

## EQIS Metrics Computed

1. **Days in News Cycle** (20%): Recency and persistence scoring
2. **Coverage** (25%): Number of independent news outlets reporting
3. **Coherence** (15%): TF-IDF cosine similarity between articles
4. **Best Source** (10%): Authority + primacy + influence scoring  
5. **Corroboration** (20%): Verified vs contested claims ratio
6. **Correction Risk** (10%): Based on outlet historical correction rates

## Dependencies

- **SQLAlchemy**: Database ORM
- **psycopg2**: PostgreSQL driver
- **NumPy/Pandas**: Data processing
- **scikit-learn**: TF-IDF vectorization and cosine similarity
- **PyYAML**: Configuration parsing

## Configuration

Metrics weights and parameters are configured in `configs/metrics.yml`:

```yaml
weights:
  days: 0.20
  coverage: 0.25
  coherence: 0.15
  best_source: 0.10
  corroboration: 0.20
  correction_risk: 0.10
```

## Database Schema

The service reads from and writes to these tables:
- `events`: News events to analyze
- `articles`: Article content and metadata
- `event_articles`: Links between events and articles
- `outlet_profiles`: News source authority weights
- `event_metrics`: Computed EQIS scores (output)

## Deployment

### Kubernetes CronJob
Runs every 15 minutes as a CronJob:

```yaml
spec:
  schedule: "*/15 * * * *"
  concurrencyPolicy: Forbid
```

### Environment Variables (Kubernetes Secrets)
**Production Deployment:**
Credentials managed via Kubernetes secret `postgres-secret`:
- `DB_USER`: Database username (from secret)
- `DB_PASSWORD`: Database password (from secret)  
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_NAME`: Database name (from secret)
- `DATABASE_URL`: Constructed dynamically at runtime

**Security Features:**
- ✅ Runtime-only credential access
- ✅ No hardcoded passwords in manifests
- ✅ Automatic startup health checks

### Build Requirements
- Docker with sufficient memory (4GB+ recommended)
- Extended build timeout for Alpine compilation
- Network access for PyPI packages

## Local Development

```bash
# Build image (takes 10-15 minutes)
docker build -t k8s-news-engine/analytics-py:latest .

# Run once
docker run --rm \
  -e DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/db" \
  k8s-news-engine/analytics-py:latest

# Test with local PostgreSQL (development only)
docker run --rm --network host \
  -e DATABASE_URL="postgresql+psycopg2://appuser:newsengine2024@localhost:5432/newsdb" \
  k8s-news-engine/analytics-py:v2.0.2

# Production deployment uses Kubernetes secrets for credential management
```

## Performance Notes

- Memory usage: ~200-400MB during execution
- CPU: Intensive during TF-IDF computation
- Execution time: 30-120 seconds depending on article volume
- Designed for batch processing, not real-time

## Version History

- **v2.0.2**: Added secure database credential management with Kubernetes secrets
- **v2.0.1**: Enhanced startup health checks with database and analytics dependencies validation
- **v2.0.0**: Initial analytics worker with EQIS computation