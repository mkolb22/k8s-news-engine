#!/bin/sh
#
# Database Cleanup Script
# Runs automated cleanup procedures using the configured lifecycle settings
#

set -e

echo "$(date): Starting database cleanup process"

# Check if cleanup is enabled
CLEANUP_ENABLED=$(psql "$DATABASE_URL" -t -c "SELECT get_config_value('cleanup_enabled', 'false');" 2>/dev/null | tr -d '[:space:]' || echo "false")

if [ "$CLEANUP_ENABLED" != "true" ]; then
    echo "$(date): Cleanup is disabled in system configuration (cleanup_enabled=false)"
    exit 0
fi

echo "$(date): Cleanup is enabled, proceeding with cleanup operations"

# Run article cleanup
echo "$(date): Running article cleanup procedure"
psql "$DATABASE_URL" -c "CALL cleanup_old_articles();" || {
    echo "$(date): ERROR: Article cleanup failed"
    exit 1
}

# Run event cleanup (if events exist)
EVENT_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM events;" 2>/dev/null | tr -d '[:space:]' || echo "0")
if [ "$EVENT_COUNT" -gt "0" ]; then
    echo "$(date): Running event cleanup procedure"
    psql "$DATABASE_URL" -c "CALL cleanup_old_events();" || {
        echo "$(date): WARNING: Event cleanup failed, continuing"
    }
else
    echo "$(date): Skipping event cleanup (no events in database)"
fi

# Run metrics cleanup (if performance tables exist)
PERF_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM performance_config_snapshots;" 2>/dev/null | tr -d '[:space:]' || echo "0")
if [ "$PERF_COUNT" -gt "0" ]; then
    echo "$(date): Running metrics cleanup procedure"
    psql "$DATABASE_URL" -c "CALL cleanup_old_metrics();" || {
        echo "$(date): WARNING: Metrics cleanup failed, continuing"
    }
else
    echo "$(date): Skipping metrics cleanup (no performance data)"
fi

# Show cleanup statistics
echo "$(date): Cleanup statistics:"
psql "$DATABASE_URL" -c "
SELECT 
    cleanup_type,
    records_deleted,
    batch_count,
    status,
    started_at,
    completed_at
FROM cleanup_log 
WHERE started_at > NOW() - INTERVAL '1 day'
ORDER BY started_at DESC 
LIMIT 10;
" || {
    echo "$(date): WARNING: Could not retrieve cleanup statistics"
}

# Show current database size info
echo "$(date): Current database status:"
psql "$DATABASE_URL" -c "
SELECT 
    'Articles' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN published_at > NOW() - INTERVAL '1 hour' * get_config_int('article_retention_hours', 168) THEN 1 END) as within_retention
FROM articles
UNION ALL
SELECT 
    'Events' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' * get_config_int('event_retention_hours', 336) THEN 1 END) as within_retention  
FROM events;
" || {
    echo "$(date): WARNING: Could not retrieve database status"
}

echo "$(date): Database cleanup process completed successfully"