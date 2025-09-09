# Development Standards

## Container Image Pull Policy

### Standard: Always Use `imagePullPolicy: Always` During Development

**MANDATORY**: All Kubernetes deployments in development environments MUST use `imagePullPolicy: Always`.

### Rationale
1. **Ensures Latest Code**: Forces Kubernetes to pull the most recent image, ensuring deployed code matches local changes
2. **Prevents Stale Deployments**: Eliminates issues where old cached images are used instead of rebuilt ones
3. **Development Consistency**: Ensures all team members see the same version after rebuilds
4. **Faster Debugging**: Reduces confusion when debugging issues that might be due to stale images

### Implementation
```yaml
spec:
  template:
    spec:
      containers:
      - name: service-name
        image: service-name:latest
        imagePullPolicy: Always  # REQUIRED for development
```

### Environment-Specific Policies
- **Development**: `imagePullPolicy: Always`
- **Staging**: `imagePullPolicy: IfNotPresent` (with proper tagging)
- **Production**: `imagePullPolicy: IfNotPresent` (with immutable tags)

### Commands for Updates
```bash
# Update existing deployment
kubectl patch deployment <deployment-name> -n <namespace> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","imagePullPolicy":"Always"}]}}}}'

# Force image update
kubectl set image deployment/<deployment-name> -n <namespace> <container-name>=<image>:latest

# Restart deployment after image rebuild
kubectl rollout restart deployment/<deployment-name> -n <namespace>
```

### Verification
```bash
# Check imagePullPolicy is set correctly
kubectl get deployment <deployment-name> -n <namespace> -o yaml | grep imagePullPolicy

# Verify image is being pulled
kubectl describe pod <pod-name> -n <namespace> | grep -A5 "Events:"
```

## Development Workflow
1. Make code changes
2. Build Docker image: `docker build -t service-name:latest .`
3. Update deployment: `kubectl rollout restart deployment/service-name -n namespace`
4. Verify deployment: `kubectl rollout status deployment/service-name -n namespace`

## Troubleshooting
- If changes don't appear, check `imagePullPolicy` is set to `Always`
- Verify Docker image was rebuilt successfully: `docker images | grep service-name`
- Force pod recreation: `kubectl delete pod -l app=service-name -n namespace`

---

**Note**: This standard applies to all microservices in the K8s News Engine project during development phases.