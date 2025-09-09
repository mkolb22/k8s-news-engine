# Code Style and Conventions

## General Principles
- Prefer editing existing files over creating new ones
- Follow security best practices - never expose secrets/keys
- Use existing libraries and patterns within the codebase

## Python (analytics-py)
- **Database**: SQLAlchemy ORM with explicit table definitions
- **Configuration**: YAML files in `configs/` directory
- **Environment Variables**: `DATABASE_URL` for database connections
- **Data Processing**: pandas/NumPy for data manipulation, scikit-learn for ML
- **Structure**: Main logic in `worker.py`, configs separate

## Go (rss-fetcher)
- **Go 1.21** with modules (`go.mod`)
- **Multi-stage Docker builds**: Builder + minimal Alpine runtime
- **Security**: Non-root containers, minimal attack surface
- **Configuration**: YAML-based with Kubernetes ConfigMaps
- **Logging**: Structured logging with logrus
- **Database**: Direct PostgreSQL with lib/pq driver
- **Error Handling**: Graceful shutdown and proper error propagation

## Docker
- **Multi-stage builds**: Separate build and runtime stages
- **Alpine Linux**: Minimal base images for production
- **Non-root users**: Security-hardened containers
- **Health checks**: Built-in container health monitoring
- **Environment variables**: Clear defaults and documentation

## Kubernetes
- **Resource organization**: Separate directories (`k8s/`) for manifests
- **ConfigMaps**: External configuration management
- **CronJobs**: For scheduled analytics tasks
- **Deployments**: For continuous services
- **Namespacing**: Proper resource isolation

## Database
- **PostgreSQL**: Primary database with proper connection pooling
- **Schema consistency**: Shared tables across services (events, articles, etc.)
- **Connection strings**: Environment variable based configuration