# EQIS Analytics Service (Event Quality & Impact Score)

This microservice computes per-event metrics and a composite **EQIS** score:
- Days in news cycle (recency + persistence)
- Outlet coverage (independent site count)
- Keyword coherence (TF-IDF cosine)
- Best source (authority + primacy + influence)
- Claim corroboration (verified vs total; contradictions)
- Correction risk (outlet correction history)

> Generated: 2025-09-08T08:09:40.312191Z

## Run locally
```bash
docker build -t eqis-analytics ./services/analytics-py
docker run --rm -e DATABASE_URL="postgresql+psycopg2://truth:truth@localhost:5432/truthdb" eqis-analytics
```

## Kubernetes (as a CronJob)
Edit `k8s/cronjob.yaml` to set your `DATABASE_URL` Secret and schedule, then:
```bash
kubectl apply -f services/analytics-py/k8s/cronjob.yaml
```

## Configuration
- `configs/metrics.yml` controls weights and thresholds.
- The service will create the `event_metrics` and `outlet_profiles` tables if they don't exist.
