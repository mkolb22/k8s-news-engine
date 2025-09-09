# News Engine Deployment

Complete deployment package for the K8s News Engine system including PostgreSQL database and RSS Fetcher service.

## Components

### PostgreSQL Database
- **Image**: postgres:15-alpine
- **Storage**: 10Gi persistent volume
- **Database**: newsdb
- **Users**: postgres (admin), appuser (application)
- **Auto-initialization**: Schema created on first deploy

### RSS Fetcher Service
- **Image**: k8s-news-engine/rss-fetcher:latest
- **Language**: Go with Alpine Linux
- **ConfigMap**: 14 public news RSS feeds
- **Resources**: 64-128Mi RAM, 50-200m CPU

## Prerequisites

1. Kubernetes cluster (1.19+)
2. kubectl configured
3. Storage class available (default: "standard")

## Quick Start

```bash
# Deploy everything
./deploy.sh

# Check status
./deploy.sh status

# Clean up
./deploy.sh cleanup
```

## Manual Deployment

```bash
# 1. Create namespace
kubectl apply -f namespace/

# 2. Deploy PostgreSQL
kubectl apply -f postgres/

# 3. Deploy RSS Fetcher
kubectl apply -f rss-fetcher/

# 4. Check status
kubectl get all -n news-engine
```

## Directory Structure

```
deployment/
├── namespace/
│   └── namespace.yaml      # Namespace definition
├── postgres/
│   ├── configmap-init.yaml  # Database schema
│   ├── secret.yaml          # Database credentials
│   ├── pvc.yaml            # Persistent storage
│   ├── deployment.yaml     # PostgreSQL deployment
│   └── service.yaml        # ClusterIP service
├── rss-fetcher/
│   ├── configmap.yaml      # RSS feed configuration
│   └── deployment.yaml     # RSS fetcher deployment
└── deploy.sh               # Deployment script
```

## Configuration

### Database Credentials
Edit `postgres/secret.yaml` to change passwords:
- postgres-password: Admin password
- app-password: Application password

### RSS Feeds
Edit `rss-fetcher/configmap.yaml` to modify feed sources.

### Storage
Edit `postgres/pvc.yaml` to change storage size or class.

## Accessing Services

### PostgreSQL
```bash
# Port forward for local access
kubectl port-forward -n news-engine svc/postgresql 5432:5432

# Connect with psql
psql -h localhost -U appuser -d newsdb
```

### View Logs
```bash
# RSS Fetcher logs
kubectl logs -n news-engine -l app=rss-fetcher -f

# PostgreSQL logs
kubectl logs -n news-engine -l app=postgresql -f
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod -n news-engine <pod-name>
kubectl logs -n news-engine <pod-name>
```

### Database connection issues
1. Check PostgreSQL is running: `kubectl get pods -n news-engine`
2. Verify service DNS: `kubectl get svc -n news-engine`
3. Check credentials in deployment match secret

### Storage issues
1. Check PVC status: `kubectl get pvc -n news-engine`
2. Verify storage class exists: `kubectl get storageclass`

## Security Notes

- Default passwords should be changed for production
- Consider using external secrets management
- Enable network policies for production
- Use RBAC for service accounts