#!/bin/bash

# K8s News Engine Deployment Script
# Deploys all components in the correct order

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="news-engine"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    log_info "kubectl found: $(kubectl version --client --short)"
}

create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    kubectl apply -f "$SCRIPT_DIR/namespace/namespace.yaml"
    
    # Wait for namespace to be active
    kubectl wait --for=condition=Active namespace/$NAMESPACE --timeout=30s 2>/dev/null || true
    log_info "Namespace $NAMESPACE is ready"
}

deploy_postgres() {
    log_info "Deploying PostgreSQL database..."
    
    # Deploy in order
    kubectl apply -f "$SCRIPT_DIR/postgres/secret.yaml"
    kubectl apply -f "$SCRIPT_DIR/postgres/configmap-init.yaml"
    kubectl apply -f "$SCRIPT_DIR/postgres/pvc.yaml"
    kubectl apply -f "$SCRIPT_DIR/postgres/deployment.yaml"
    kubectl apply -f "$SCRIPT_DIR/postgres/service.yaml"
    
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --namespace=$NAMESPACE \
        --for=condition=ready pod \
        --selector=app=postgresql \
        --timeout=120s
    
    log_info "PostgreSQL is ready"
}

deploy_rss_fetcher() {
    log_info "Deploying RSS Fetcher service..."
    
    # Deploy ConfigMap and Deployment
    kubectl apply -f "$SCRIPT_DIR/rss-fetcher/configmap.yaml"
    kubectl apply -f "$SCRIPT_DIR/rss-fetcher/deployment.yaml"
    
    log_info "Waiting for RSS Fetcher to be ready..."
    kubectl wait --namespace=$NAMESPACE \
        --for=condition=ready pod \
        --selector=app=rss-fetcher \
        --timeout=120s || {
        log_warn "RSS Fetcher is taking longer to start. Check logs with:"
        echo "  kubectl logs -n $NAMESPACE -l app=rss-fetcher"
    }
    
    log_info "RSS Fetcher deployment complete"
}

deploy_analytics() {
    log_info "Deploying Analytics service..."
    
    # Deploy CronJob
    kubectl apply -f "$SCRIPT_DIR/analytics-py/cronjob.yaml"
    
    log_info "Analytics CronJob deployed (runs every 15 minutes)"
    log_info "Note: Analytics service uses Alpine container - first build may take 10-15 minutes"
}

deploy_publisher() {
    log_info "Deploying Publisher service..."
    
    # Deploy ConfigMap, Deployment, and Service
    kubectl apply -f "$SCRIPT_DIR/publisher/"
    
    log_info "Waiting for Publisher to be ready..."
    kubectl wait --namespace=$NAMESPACE \
        --for=condition=ready pod \
        --selector=app=publisher \
        --timeout=120s || {
        log_warn "Publisher is taking longer to start. Check logs with:"
        echo "  kubectl logs -n $NAMESPACE -l app=publisher"
    }
    
    log_info "Publisher deployment complete"
}

show_status() {
    log_info "Deployment Status:"
    echo ""
    echo "=== Pods ==="
    kubectl get pods -n $NAMESPACE
    echo ""
    echo "=== Services ==="
    kubectl get services -n $NAMESPACE
    echo ""
    echo "=== PersistentVolumeClaims ==="
    kubectl get pvc -n $NAMESPACE
    echo ""
    echo "=== ConfigMaps ==="
    kubectl get configmaps -n $NAMESPACE
    echo ""
    echo "=== CronJobs ==="
    kubectl get cronjobs -n $NAMESPACE
}

show_connection_info() {
    log_info "Connection Information:"
    echo ""
    echo "PostgreSQL:"
    echo "  Internal: postgresql.$NAMESPACE.svc.cluster.local:5432"
    echo "  Database: newsdb"
    echo "  App User: appuser"
    echo ""
    echo "Publisher Website:"
    PUBLISHER_IP=$(kubectl get svc publisher -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
    PUBLISHER_PORT=$(kubectl get svc publisher -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}' 2>/dev/null || echo "80")
    echo "  URL: http://$PUBLISHER_IP:$PUBLISHER_PORT"
    echo "  LoadBalancer Service: publisher.$NAMESPACE.svc.cluster.local"
    echo ""
    echo "To connect to PostgreSQL from your local machine:"
    echo "  kubectl port-forward -n $NAMESPACE svc/postgresql 5432:5432"
    echo ""
    echo "To view RSS Fetcher logs:"
    echo "  kubectl logs -n $NAMESPACE -l app=rss-fetcher -f"
    echo ""
    echo "To view PostgreSQL logs:"
    echo "  kubectl logs -n $NAMESPACE -l app=postgresql -f"
    echo ""
    echo "To view Analytics CronJob logs:"
    echo "  kubectl logs -n $NAMESPACE -l app=analytics-worker"
    echo ""
    echo "To view Publisher logs:"
    echo "  kubectl logs -n $NAMESPACE -l app=publisher -f"
    echo ""
    echo "To manually trigger Analytics job:"
    echo "  kubectl create job --from=cronjob/analytics-worker analytics-manual -n $NAMESPACE"
}

cleanup() {
    log_warn "Cleaning up News Engine deployment..."
    read -p "Are you sure you want to delete all resources? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete namespace $NAMESPACE --wait=true
        log_info "Cleanup complete"
    else
        log_info "Cleanup cancelled"
    fi
}

# Main execution
main() {
    case "${1:-}" in
        cleanup|clean|delete)
            cleanup
            ;;
        status)
            show_status
            ;;
        *)
            log_info "Starting K8s News Engine deployment..."
            check_kubectl
            create_namespace
            deploy_postgres
            deploy_rss_fetcher
            deploy_analytics
            deploy_publisher
            show_status
            show_connection_info
            log_info "Deployment complete!"
            ;;
    esac
}

# Run main function
main "$@"