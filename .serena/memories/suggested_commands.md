# Suggested Commands

## Docker Commands

### Build Services
```bash
# Analytics service
docker build -t eqis-analytics ./services/analytics-py

# RSS Fetcher service  
docker build -t k8s-news-engine/rss-fetcher:latest ./services/rss-fetcher

# Publisher service
docker build -t publisher ./services/publisher
```

### Local Development
```bash
# Run analytics service
docker run --rm -e DATABASE_URL="postgresql+psycopg2://appuser:newsengine2024@localhost:5432/newsdb" eqis-analytics

# Run RSS fetcher once
docker run --rm -e DATABASE_URL="postgresql://user:pass@host:5432/db" k8s-news-engine/rss-fetcher:latest ./rss-fetcher --once

# Run publisher service
docker run -p 8080:80 publisher
```

## Kubernetes Commands

### Deployment
```bash
# Deploy analytics as CronJob
kubectl apply -f services/analytics-py/k8s/cronjob.yaml

# Deploy RSS fetcher
kubectl apply -f services/rss-fetcher/k8s/namespace.yaml
kubectl apply -f services/rss-fetcher/k8s/configmap.yaml
kubectl apply -f services/rss-fetcher/k8s/deployment.yaml

# Deploy publisher service
kubectl apply -f services/publisher/k8s/
```

### Monitoring
```bash
# Check CronJobs
kubectl get cronjobs
kubectl get jobs

# Check RSS fetcher logs
kubectl logs -f deployment/rss-fetcher

# Check job logs
kubectl logs -f job/<job-name>
```

## Go Commands (RSS Fetcher)
```bash
# In services/rss-fetcher directory:
go build -o rss-fetcher .
./rss-fetcher --once    # Run once
./rss-fetcher          # Run continuously
```

## Development Workflow
```bash
# Check git status
git status

# Build and test locally before deployment
docker build -t <service-name> ./services/<service>/

# Deploy to Kubernetes after testing
kubectl apply -f services/<service>/k8s/
```