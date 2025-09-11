#!/bin/bash
set -e

# K8s News Engine Deployment Script
# Deploys PostgreSQL and all news engine services to Kubernetes

NAMESPACE_PG="postgresql"
NAMESPACE_APP="default"

echo "🚀 K8s News Engine Deployment"
echo "=============================="

# Check for kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please configure kubectl."
    exit 1
fi

echo "✅ Connected to cluster: $(kubectl config current-context)"

# Step 1: Deploy PostgreSQL using k8s-postgresql submodule
echo ""
echo "📦 Step 1: Deploying PostgreSQL..."
echo "----------------------------------"

# Apply PostgreSQL manifests in order
kubectl apply -f database/k8s-postgresql/manifests/core/postgresql-namespace.yaml
kubectl apply -f database/k8s-postgresql/manifests/config/postgresql-secrets.yaml
kubectl apply -f database/k8s-postgresql/manifests/config/postgresql-configmap.yaml
kubectl apply -f database/k8s-postgresql/manifests/security/postgresql-rbac.yaml

# Apply our custom schema ConfigMaps
kubectl apply -f database/k8s-postgresql/manifests/config/news-engine-schema.yaml
kubectl apply -f database/k8s-postgresql/manifests/config/news-engine-seed.yaml

# Apply our custom deployment with schema mounting
kubectl apply -f database/news-engine-deployment.yaml

# Apply services
kubectl apply -f database/k8s-postgresql/manifests/core/postgresql-services.yaml

echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n $NAMESPACE_PG --timeout=120s

echo "✅ PostgreSQL deployed and ready"

# Step 2: Build and load Docker images (for local clusters like kind/minikube)
echo ""
echo "🔨 Step 2: Building service images..."
echo "-------------------------------------"

# Detect if using kind
if kubectl config current-context | grep -q "kind"; then
    echo "📌 Detected kind cluster, will load images directly"
    
    # Build images
    docker build -t rss-fetcher:latest services/rss-fetcher/
    docker build -t claim-extractor:latest services/claim-extractor/
    docker build -t eqis-analytics:latest services/analytics-py/
    docker build -t publisher:latest services/publisher/
    
    # Load into kind
    KIND_CLUSTER=$(kubectl config current-context | sed 's/kind-//')
    kind load docker-image rss-fetcher:latest --name $KIND_CLUSTER
    kind load docker-image claim-extractor:latest --name $KIND_CLUSTER
    kind load docker-image eqis-analytics:latest --name $KIND_CLUSTER
    kind load docker-image publisher:latest --name $KIND_CLUSTER
    
elif kubectl config current-context | grep -q "minikube"; then
    echo "📌 Detected minikube, using minikube docker env"
    eval $(minikube docker-env)
    
    docker build -t rss-fetcher:latest services/rss-fetcher/
    docker build -t claim-extractor:latest services/claim-extractor/
    docker build -t eqis-analytics:latest services/analytics-py/
    docker build -t publisher:latest services/publisher/
else
    echo "⚠️  Using remote cluster. Make sure images are available in your registry."
    echo "   Update image references in Kubernetes manifests to use your registry."
fi

# Step 3: Deploy services
echo ""
echo "🚀 Step 3: Deploying news engine services..."
echo "--------------------------------------------"

# RSS Fetcher
kubectl apply -f services/rss-fetcher/k8s/deployment.yaml
echo "✅ RSS Fetcher deployed"

# Claim Extractor
kubectl apply -f services/claim-extractor/k8s/deployment.yaml 2>/dev/null || echo "⏭️  Claim extractor manifest not found, skipping"

# Analytics (as CronJob)
kubectl apply -f services/analytics-py/k8s/cronjob.yaml
echo "✅ Analytics CronJob deployed"

# Publisher
kubectl apply -f services/publisher/k8s/
echo "✅ Publisher service deployed"

# Step 4: Status check
echo ""
echo "📊 Deployment Status:"
echo "--------------------"

echo ""
echo "PostgreSQL namespace:"
kubectl get all -n $NAMESPACE_PG

echo ""
echo "Application services:"
kubectl get all -n $NAMESPACE_APP | grep -E "(rss-fetcher|claim-extractor|publisher|analytics)"

# Step 5: Connection info
echo ""
echo "🔗 Connection Information:"
echo "-------------------------"
echo "PostgreSQL (internal): postgresql.postgresql.svc.cluster.local:5432"
echo "PostgreSQL (external): kubectl port-forward -n postgresql svc/postgresql 5432:5432"
echo "Publisher (external):  kubectl port-forward -n default svc/publisher 8080:80"

echo ""
echo "📝 Useful commands:"
echo "------------------"
echo "View RSS fetcher logs:     kubectl logs -f deployment/rss-fetcher"
echo "View analytics job:        kubectl get cronjobs"
echo "Connect to PostgreSQL:     kubectl exec -it -n postgresql deployment/postgresql -c postgresql -- psql -U postgres -d newsdb"
echo "Trigger analytics job:     kubectl create job --from=cronjob/analytics-job analytics-manual-$(date +%s)"

echo ""
echo "✅ Deployment complete!"