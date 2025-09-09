#!/bin/bash
set -e

# K8s News Engine - Events Analysis Monitoring Script
# This script performs comprehensive health checks for the events analysis functionality

echo "🔍 K8s News Engine - Events Analysis Health Check"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC}: $message"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    else
        echo -e "${YELLOW}⚠️  WARN${NC}: $message"
    fi
}

# Initialize counter
FAILED_CHECKS=0

echo ""
echo "🏗️  Infrastructure Health Checks"
echo "--------------------------------"

# Check if namespace exists
if kubectl get namespace news-engine &>/dev/null; then
    print_status "PASS" "news-engine namespace exists"
else
    print_status "FAIL" "news-engine namespace missing"
fi

# Check deployment status
DEPLOYMENT_STATUS=$(kubectl get deployment publisher -n news-engine -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "NotFound")
if [ "$DEPLOYMENT_STATUS" = "True" ]; then
    print_status "PASS" "Publisher deployment is available"
    
    # Check replicas
    READY_REPLICAS=$(kubectl get deployment publisher -n news-engine -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    DESIRED_REPLICAS=$(kubectl get deployment publisher -n news-engine -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")
    
    if [ "$READY_REPLICAS" -eq "$DESIRED_REPLICAS" ]; then
        print_status "PASS" "All replicas are ready ($READY_REPLICAS/$DESIRED_REPLICAS)"
    else
        print_status "FAIL" "Not all replicas ready ($READY_REPLICAS/$DESIRED_REPLICAS)"
    fi
else
    print_status "FAIL" "Publisher deployment not available or not found"
fi

# Check service status
if kubectl get service publisher -n news-engine &>/dev/null; then
    print_status "PASS" "Publisher service exists"
    
    # Get service endpoint
    SERVICE_IP=$(kubectl get service publisher -n news-engine -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
    if [ "$SERVICE_IP" = "null" ] || [ "$SERVICE_IP" = "" ]; then
        SERVICE_IP="localhost"
    fi
    print_status "PASS" "Service endpoint: $SERVICE_IP"
else
    print_status "FAIL" "Publisher service not found"
fi

echo ""
echo "🔌 Connectivity Health Checks"
echo "-----------------------------"

# Test basic connectivity
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/cgi-bin/index.py 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    print_status "PASS" "Main index page accessible (HTTP $HTTP_STATUS)"
else
    print_status "FAIL" "Main index page failed (HTTP $HTTP_STATUS)"
fi

# Test events analysis page
EVENTS_HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 60 http://localhost/cgi-bin/events.py 2>/dev/null || echo "000")
if [ "$EVENTS_HTTP_STATUS" = "200" ]; then
    print_status "PASS" "Events analysis page accessible (HTTP $EVENTS_HTTP_STATUS)"
else
    print_status "FAIL" "Events analysis page failed (HTTP $EVENTS_HTTP_STATUS)"
fi

# Test events debug page
EVENTS_DEBUG_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/cgi-bin/events_debug.py 2>/dev/null || echo "000")
if [ "$EVENTS_DEBUG_STATUS" = "200" ]; then
    print_status "PASS" "Events debug page accessible (HTTP $EVENTS_DEBUG_STATUS)"
else
    print_status "FAIL" "Events debug page failed (HTTP $EVENTS_DEBUG_STATUS)"
fi

echo ""
echo "💾 Database Health Checks"
echo "-------------------------"

# Test database connectivity from pod
DB_TEST_RESULT=$(kubectl exec deployment/publisher -n news-engine -- python3 -c "
import os
import psycopg2
db_url = os.environ.get('DATABASE_URL', 'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM articles WHERE published_at > NOW() - INTERVAL \\'24 hours\\'')
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f'Recent articles: {count}')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)

if [[ "$DB_TEST_RESULT" == *"Recent articles:"* ]]; then
    print_status "PASS" "Database connectivity working - $DB_TEST_RESULT"
else
    print_status "FAIL" "Database connectivity failed - $DB_TEST_RESULT"
fi

echo ""
echo "📊 Performance & Content Checks"
echo "-------------------------------"

# Test response time for events page
START_TIME=$(date +%s.%N)
EVENTS_RESPONSE=$(curl -s -m 60 http://localhost/cgi-bin/events.py 2>/dev/null || echo "TIMEOUT")
END_TIME=$(date +%s.%N)
RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "unknown")

if [[ "$EVENTS_RESPONSE" != "TIMEOUT" ]] && [[ "$EVENTS_RESPONSE" == *"K8s News Engine - Event Analysis"* ]]; then
    if (( $(echo "$RESPONSE_TIME < 30" | bc -l 2>/dev/null) )); then
        print_status "PASS" "Events page loads within 30s (${RESPONSE_TIME}s)"
    else
        print_status "WARN" "Events page slow (${RESPONSE_TIME}s)"
    fi
    
    # Check content
    RESPONSE_SIZE=$(echo -n "$EVENTS_RESPONSE" | wc -c)
    if [ "$RESPONSE_SIZE" -gt 10000 ]; then
        print_status "PASS" "Events page has substantial content (${RESPONSE_SIZE} bytes)"
    else
        print_status "WARN" "Events page content seems limited (${RESPONSE_SIZE} bytes)"
    fi
    
    # Check for detected events
    if [[ "$EVENTS_RESPONSE" == *"Detected Events"* ]]; then
        EVENTS_COUNT=$(echo "$EVENTS_RESPONSE" | grep -o 'Detected Events</h3>[^<]*<div[^>]*>[^<]*' | grep -o '[0-9]\+' | head -1 || echo "0")
        if [ "$EVENTS_COUNT" -gt 0 ] 2>/dev/null; then
            print_status "PASS" "Events detection working ($EVENTS_COUNT events detected)"
        else
            print_status "WARN" "No events detected (may be normal if no recent activity)"
        fi
    else
        print_status "FAIL" "Events page missing expected content structure"
    fi
else
    print_status "FAIL" "Events page not loading properly or timeout"
fi

echo ""
echo "🏥 Pod Health Checks"
echo "-------------------"

# Check pod status
POD_STATUS=$(kubectl get pods -n news-engine -l app=publisher -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")
if [ "$POD_STATUS" = "Running" ]; then
    print_status "PASS" "Publisher pod is running"
    
    # Check restart count
    RESTART_COUNT=$(kubectl get pods -n news-engine -l app=publisher -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}' 2>/dev/null || echo "unknown")
    if [ "$RESTART_COUNT" = "0" ]; then
        print_status "PASS" "No recent pod restarts"
    elif [ "$RESTART_COUNT" -lt 3 ] 2>/dev/null; then
        print_status "WARN" "Pod has restarted $RESTART_COUNT times"
    else
        print_status "FAIL" "Pod has restarted $RESTART_COUNT times (may indicate issues)"
    fi
    
    # Check resource usage
    CPU_USAGE=$(kubectl top pod -n news-engine -l app=publisher --no-headers 2>/dev/null | awk '{print $2}' || echo "unknown")
    MEMORY_USAGE=$(kubectl top pod -n news-engine -l app=publisher --no-headers 2>/dev/null | awk '{print $3}' || echo "unknown")
    
    if [ "$CPU_USAGE" != "unknown" ] && [ "$MEMORY_USAGE" != "unknown" ]; then
        print_status "PASS" "Resource usage: CPU: $CPU_USAGE, Memory: $MEMORY_USAGE"
    else
        print_status "WARN" "Unable to retrieve resource usage metrics"
    fi
else
    print_status "FAIL" "Publisher pod not running (status: $POD_STATUS)"
fi

# Check logs for errors
LOG_ERRORS=$(kubectl logs deployment/publisher -n news-engine --tail=50 2>/dev/null | grep -i "error\|exception\|failed\|timeout" | wc -l || echo "0")
if [ "$LOG_ERRORS" -eq 0 ]; then
    print_status "PASS" "No errors in recent logs"
else
    print_status "WARN" "$LOG_ERRORS error messages in recent logs"
fi

echo ""
echo "📋 Summary Report"
echo "=================="

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED${NC}"
    echo "The K8s News Engine events analysis functionality is healthy and operational."
    EXIT_CODE=0
else
    echo -e "${RED}⚠️  $FAILED_CHECKS CHECK(S) FAILED${NC}"
    echo "Issues detected with the K8s News Engine events analysis functionality."
    EXIT_CODE=1
fi

echo ""
echo "Monitoring completed at $(date)"
echo "For detailed logs: kubectl logs deployment/publisher -n news-engine"
echo "For pod status: kubectl get pods -n news-engine -l app=publisher"

exit $EXIT_CODE