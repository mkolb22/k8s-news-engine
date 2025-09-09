# Task Completion Checklist

## Before Deployment
1. **Local Testing**
   - Build Docker images successfully
   - Test containers locally with proper environment variables
   - Verify database connectivity and schema compatibility

2. **Code Quality**
   - Follow existing code patterns and conventions
   - Ensure security best practices (no exposed secrets)
   - Use appropriate logging levels and structured logging

## Service-Specific Checks

### Analytics Service (Python)
- Validate YAML configuration files in `configs/`
- Test database queries with SQLAlchemy
- Verify EQIS metric calculations
- Check CronJob schedule and resource limits

### RSS Fetcher Service (Go)
- Test RSS feed parsing and content extraction
- Verify ConfigMap integration
- Test database insertion and event linking
- Ensure graceful shutdown handling

### Publisher Service
- Validate CGI script functionality
- Test Lighttpd configuration
- Verify content serving and routing

## Kubernetes Deployment
1. **Resource Definitions**
   - Apply ConfigMaps first (if used)
   - Apply Deployments/CronJobs
   - Verify resource limits and requests

2. **Post-Deployment**
   - Check pod status: `kubectl get pods`
   - Monitor logs: `kubectl logs -f <pod-name>`
   - Verify service connectivity
   - Test end-to-end functionality

## Git Workflow
1. Commit changes with clear messages
2. Push to feature branch
3. Create pull request with description
4. Test in staging environment before merge