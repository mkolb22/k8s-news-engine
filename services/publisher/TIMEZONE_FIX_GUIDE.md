# Publisher Timezone Configuration Fix Guide

## Problem Description

The publisher application was experiencing timezone-related errors in the `events.py` CGI script with the error message:
```
can't subtract offset-naive and offset-aware datetimes
```

This error occurred when performing datetime arithmetic between database timestamps (timezone-aware) and Python datetime objects that were timezone-naive.

## Root Cause Analysis

1. **Alpine Linux Base Image**: The Alpine Linux container lacked proper timezone configuration and the `tzdata` package
2. **Missing Environment Variables**: No `TZ` environment variable was set to ensure consistent timezone handling
3. **Database Connection**: PostgreSQL connection did not explicitly set timezone to UTC
4. **Python Code**: While there was an `ensure_timezone_aware()` function, it wasn't robust enough to handle all edge cases

## Solution Implementation

### 1. Container-Level Fixes

#### Updated Dockerfile (`services/publisher/Dockerfile`)

**Added:**
- `tzdata` package installation for proper timezone support
- `TZ=UTC` environment variable

```dockerfile
# Install lighttpd, python3, postgresql client, and timezone data
RUN apk add --no-cache \
    lighttpd \
    python3 \
    py3-pip \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    tzdata

# Set timezone environment variable for consistent timezone handling
ENV TZ=UTC
```

### 2. Deployment Configuration

#### Updated deployment.yaml (`deployment/publisher/deployment.yaml`)

**Added environment variables:**
```yaml
env:
- name: DATABASE_URL
  value: "postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb"
- name: TZ
  value: "UTC"
- name: PGTZ
  value: "UTC"
```

**Updated health checks to use new timezone-aware health endpoint:**
```yaml
livenessProbe:
  httpGet:
    path: /cgi-bin/health.py
    port: 8080
```

### 3. Application-Level Improvements

#### Enhanced Database Connection (`services/publisher/cgi-bin/events.py`)

**Added explicit timezone setting:**
```python
def get_db_connection():
    """Get database connection with timezone configuration"""
    db_url = os.environ.get('DATABASE_URL', '...')
    conn = psycopg2.connect(db_url)
    
    # Set timezone to UTC for this connection
    with conn.cursor() as cur:
        cur.execute("SET timezone = 'UTC'")
        conn.commit()
    
    return conn
```

#### Improved `ensure_timezone_aware()` Function

**Enhanced with better error handling:**
```python
def ensure_timezone_aware(dt):
    """Ensure datetime is timezone aware - enhanced with better error handling"""
    if dt is None:
        return datetime.now(timezone.utc)
    
    # Handle timezone-naive datetime objects
    if dt.tzinfo is None:
        # Assume UTC for database datetimes
        return dt.replace(tzinfo=timezone.utc)
    
    # Handle timezone-aware datetime objects
    if dt.tzinfo is not None:
        # Convert to UTC if not already
        return dt.astimezone(timezone.utc) if dt.tzinfo != timezone.utc else dt
    
    return dt
```

#### Added Defensive Error Handling

**Critical datetime operations now include try-catch blocks:**
```python
try:
    now = datetime.now(timezone.utc)
    if event_articles[0][4]:  # published_at
        first_article_time = ensure_timezone_aware(event_articles[0][4])
        hours_ago = (now - first_article_time).total_seconds() / 3600
        # ... scoring logic
except Exception as e:
    print(f"<!-- Timezone error in recency calculation: {str(e)} -->", file=sys.stderr)
    recency_score = 10  # Default score if timezone calculation fails
```

### 4. Health Check and Monitoring

#### New Health Check Endpoint (`services/publisher/cgi-bin/health.py`)

**Comprehensive timezone validation:**
- System timezone configuration
- Database timezone settings
- Datetime arithmetic operations
- End-to-end integration testing

#### Monitoring and Alerting (`deployment/publisher/monitoring.yaml`)

**Added Prometheus alerts:**
- `PublisherTimezoneFailure`: Critical alert for service failures
- `PublisherHealthCheckFailure`: Warning for health check issues
- `PublisherCGIErrors`: Warning for CGI script errors

## Deployment Steps

### 1. Build Updated Container

```bash
cd services/publisher
docker build -t k8s-news-engine/publisher:timezone-fix .
```

### 2. Apply Updated Deployment

```bash
kubectl apply -f deployment/publisher/deployment.yaml
kubectl apply -f deployment/publisher/monitoring.yaml
```

### 3. Verify Deployment

```bash
# Check pod status
kubectl get pods -n news-engine -l app=publisher

# Check health endpoint
kubectl exec -n news-engine deployment/publisher -- curl -s http://localhost:8080/cgi-bin/health.py

# Check logs
kubectl logs -n news-engine deployment/publisher
```

### 4. Run Integration Tests

```bash
# Copy test script to pod and run
kubectl cp services/publisher/test_timezone.py news-engine/publisher-pod:/tmp/
kubectl exec -n news-engine deployment/publisher -- python3 /tmp/test_timezone.py
```

## Testing and Validation

### Manual Testing

1. **Access Events Page**: Navigate to `/cgi-bin/events.py` and verify it loads without errors
2. **Check Health Endpoint**: Visit `/cgi-bin/health.py` for detailed timezone status
3. **Monitor Logs**: Watch for timezone-related error messages

### Automated Testing

Run the included test script:
```bash
python3 services/publisher/test_timezone.py
```

### Test Cases Covered

- [x] System timezone configuration (TZ=UTC)
- [x] Database timezone settings
- [x] Python datetime arithmetic operations
- [x] Database integration with real article data
- [x] Error handling for edge cases

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Publisher Pod Health**: `up{job="publisher"}`
2. **Health Check Success**: `probe_success{job="publisher-health"}`
3. **CGI Error Rate**: `lighttpd_requests_total{status=~"5.."}`

### Alert Responses

#### PublisherTimezoneFailure
1. Check pod logs for timezone-related errors
2. Verify TZ environment variables are set
3. Restart deployment if necessary

#### CGI Errors
1. Check for "timezone" or "datetime" error messages
2. Verify database connectivity
3. Review application logs for specific error patterns

## Prevention Measures

1. **Container Standards**: Ensure all containers include `tzdata` package and `TZ=UTC`
2. **Database Connections**: Always set explicit timezone for PostgreSQL connections
3. **Code Reviews**: Check for timezone-naive datetime operations
4. **Integration Tests**: Include timezone validation in CI/CD pipeline

## Rollback Plan

If issues occur, rollback steps:

```bash
# Rollback deployment
kubectl rollout undo deployment/publisher -n news-engine

# Remove monitoring if needed
kubectl delete -f deployment/publisher/monitoring.yaml
```

## Future Improvements

1. **Centralized Timezone Configuration**: Consider using a base container image with timezone pre-configured
2. **Automated Testing**: Integrate timezone tests into CI/CD pipeline
3. **Documentation**: Create timezone handling standards for all services
4. **Monitoring Enhancement**: Add more granular timezone-specific metrics

## Troubleshooting

### Common Issues

1. **Pod Won't Start**: Check if tzdata package is properly installed
2. **Health Check Fails**: Verify database connectivity and timezone settings
3. **Intermittent Errors**: Check for mixed timezone-aware/naive datetime operations

### Debug Commands

```bash
# Check timezone in pod
kubectl exec -n news-engine deployment/publisher -- date
kubectl exec -n news-engine deployment/publisher -- printenv TZ

# Test database connection
kubectl exec -n news-engine deployment/publisher -- python3 -c "
import psycopg2
import os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT NOW(), current_setting(\"timezone\")')
print(cur.fetchone())
"
```