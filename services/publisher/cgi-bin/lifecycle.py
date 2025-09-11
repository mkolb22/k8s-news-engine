#!/usr/bin/env python3
"""
Lifecycle Management Dashboard
Shows database retention settings, cleanup history, and system health
"""
import os
import sys
import traceback
import psycopg2
from datetime import datetime, timezone

def get_db_connection():
    """Get database connection with timezone configuration"""
    db_url = os.environ.get('DATABASE_URL', 
                          'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
    
    try:
        conn = psycopg2.connect(db_url)
        # Set timezone to UTC for this connection
        with conn.cursor() as cur:
            cur.execute("SET timezone = 'UTC'")
            conn.commit()
        return conn
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")

def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    return 'N/A'

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds is None:
        return 'N/A'
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m {seconds%60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def get_lifecycle_stats():
    """Get comprehensive lifecycle management statistics"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get system configuration
    cur.execute("""
        SELECT config_key, config_value, description, updated_at
        FROM system_config 
        ORDER BY 
            CASE 
                WHEN config_key LIKE '%retention%' THEN 1
                WHEN config_key LIKE '%cleanup%' THEN 2
                WHEN config_key LIKE '%publisher%' THEN 3
                ELSE 4
            END,
            config_key
    """)
    config_data = cur.fetchall()
    
    # Get cleanup history (last 30 days)
    cur.execute("""
        SELECT 
            cleanup_type,
            records_deleted,
            batch_count,
            EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER as duration_seconds,
            status,
            started_at,
            completed_at,
            error_message
        FROM cleanup_log 
        WHERE started_at > NOW() - INTERVAL '30 days'
        ORDER BY started_at DESC 
        LIMIT 50
    """)
    cleanup_history = cur.fetchall()
    
    # Get cleanup summary statistics
    cur.execute("""
        SELECT 
            cleanup_type,
            COUNT(*) as total_runs,
            SUM(records_deleted) as total_deleted,
            AVG(records_deleted) as avg_deleted,
            MAX(records_deleted) as max_deleted,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_runs,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed_runs,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
            MAX(completed_at) as last_cleanup
        FROM cleanup_log 
        WHERE started_at > NOW() - INTERVAL '30 days'
        GROUP BY cleanup_type
        ORDER BY cleanup_type
    """)
    cleanup_summary = cur.fetchall()
    
    # Get current database statistics
    cur.execute("""
        SELECT 
            'Articles' as table_name,
            COUNT(*) as total_records,
            COUNT(CASE WHEN published_at > NOW() - INTERVAL '1 hour' * (
                SELECT config_value::INTEGER FROM system_config WHERE config_key = 'article_retention_hours'
            ) THEN 1 END) as within_retention,
            COUNT(CASE WHEN published_at <= NOW() - INTERVAL '1 hour' * (
                SELECT config_value::INTEGER FROM system_config WHERE config_key = 'article_retention_hours'
            ) THEN 1 END) as outside_retention,
            MIN(published_at) as oldest_record,
            MAX(published_at) as newest_record
        FROM articles
        UNION ALL
        SELECT 
            'Events' as table_name,
            COUNT(*) as total_records,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' * (
                SELECT config_value::INTEGER FROM system_config WHERE config_key = 'event_retention_hours'
            ) THEN 1 END) as within_retention,
            COUNT(CASE WHEN created_at <= NOW() - INTERVAL '1 hour' * (
                SELECT config_value::INTEGER FROM system_config WHERE config_key = 'event_retention_hours'
            ) THEN 1 END) as outside_retention,
            MIN(created_at) as oldest_record,
            MAX(created_at) as newest_record
        FROM events
        UNION ALL
        SELECT 
            'Performance Metrics' as table_name,
            COUNT(*) as total_records,
            COUNT(CASE WHEN snapshot_timestamp > NOW() - INTERVAL '1 hour' * (
                SELECT config_value::INTEGER FROM system_config WHERE config_key = 'metrics_retention_hours'
            ) THEN 1 END) as within_retention,
            COUNT(CASE WHEN snapshot_timestamp <= NOW() - INTERVAL '1 hour' * (
                SELECT config_value::INTEGER FROM system_config WHERE config_key = 'metrics_retention_hours'
            ) THEN 1 END) as outside_retention,
            MIN(snapshot_timestamp) as oldest_record,
            MAX(snapshot_timestamp) as newest_record
        FROM performance_config_snapshots
    """)
    database_stats = cur.fetchall()
    
    # Get upcoming cleanup estimate
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN published_at <= NOW() - INTERVAL '1 hour' * (
                SELECT config_value::INTEGER FROM system_config WHERE config_key = 'article_retention_hours'
            ) THEN 1 END) as articles_to_cleanup
        FROM articles
    """)
    cleanup_estimate = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return {
        'config': config_data,
        'cleanup_history': cleanup_history,
        'cleanup_summary': cleanup_summary,
        'database_stats': database_stats,
        'cleanup_estimate': cleanup_estimate[0] if cleanup_estimate else 0
    }

def main():
    print("Content-Type: text/html\n")
    
    try:
        stats = get_lifecycle_stats()
        
        print(f"""<!DOCTYPE html>
<html>
<head>
    <title>K8s News Engine - Lifecycle Management</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="300">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .nav-links {{ margin-top: 15px; }}
        .nav-links a {{ color: #ecf0f1; margin-right: 20px; text-decoration: none; }}
        .nav-links a:hover {{ text-decoration: underline; }}
        .section {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .section h2 {{ margin-top: 0; color: #2c3e50; }}
        .config-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
        .config-item {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }}
        .config-key {{ font-weight: bold; color: #2c3e50; }}
        .config-value {{ font-size: 1.2em; color: #27ae60; margin: 5px 0; }}
        .config-desc {{ color: #7f8c8d; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; color: #2c3e50; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status-success {{ color: #27ae60; font-weight: bold; }}
        .status-error {{ color: #e74c3c; font-weight: bold; }}
        .status-running {{ color: #f39c12; font-weight: bold; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; text-align: center; }}
        .metric-number {{ font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }}
        .metric-label {{ opacity: 0.9; }}
        .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .success {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
        .grid-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .cleanup-badge {{ display: inline-block; padding: 3px 8px; border-radius: 10px; font-size: 0.8em; font-weight: bold; }}
        .cleanup-success {{ background: #d4edda; color: #155724; }}
        .cleanup-error {{ background: #f8d7da; color: #721c24; }}
        .auto-refresh {{ float: right; color: #7f8c8d; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>K8s News Engine - Lifecycle Management Dashboard</h1>
        <p>Database retention, cleanup monitoring, and system health</p>
        <div class="auto-refresh">Auto-refresh every 5 minutes</div>
        <div class="nav-links">
            <a href="/cgi-bin/index.py">📰 All Articles</a>
            <a href="/cgi-bin/events.py">🎯 Event Analysis</a>
            <a href="/cgi-bin/lifecycle.py">🔄 Lifecycle Management</a>
        </div>
    </div>
    
    <!-- System Configuration -->
    <div class="section">
        <h2>📋 System Configuration</h2>
        <div class="config-grid">""")
        
        for config_key, config_value, description, updated_at in stats['config']:
            # Determine config type for styling
            if 'retention' in config_key:
                border_color = '#e74c3c'  # Red for retention
                icon = '⏰'
            elif 'cleanup' in config_key:
                border_color = '#f39c12'  # Orange for cleanup
                icon = '🧹'
            elif 'publisher' in config_key:
                border_color = '#3498db'  # Blue for publisher
                icon = '📄'
            else:
                border_color = '#95a5a6'  # Gray for others
                icon = '⚙️'
            
            print(f"""
            <div class="config-item" style="border-left-color: {border_color};">
                <div class="config-key">{icon} {config_key.replace('_', ' ').title()}</div>
                <div class="config-value">{config_value}</div>
                <div class="config-desc">{description}</div>
                <div style="font-size: 0.7em; color: #bdc3c7; margin-top: 5px;">
                    Updated: {format_datetime(updated_at) if updated_at else 'Default'}
                </div>
            </div>""")
        
        print("""
        </div>
    </div>
    
    <!-- Database Statistics -->
    <div class="section">
        <h2>📊 Database Statistics</h2>
        <div class="grid-3">""")
        
        for table_name, total_records, within_retention, outside_retention, oldest_record, newest_record in stats['database_stats']:
            retention_pct = (within_retention / total_records * 100) if total_records > 0 else 0
            cleanup_needed = outside_retention > 0
            
            print(f"""
            <div class="metric-card" style="background: {'linear-gradient(135deg, #ff7b7b 0%, #ff416c 100%)' if cleanup_needed else 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'};">
                <div class="metric-number">{total_records:,}</div>
                <div class="metric-label">{table_name}</div>
                <div style="margin-top: 15px; font-size: 0.9em;">
                    <div>✅ Within retention: {within_retention:,} ({retention_pct:.1f}%)</div>
                    <div>{'⚠️' if cleanup_needed else '✅'} Outside retention: {outside_retention:,}</div>
                    <div style="margin-top: 10px; font-size: 0.8em; opacity: 0.9;">
                        Oldest: {format_datetime(oldest_record) if oldest_record else 'None'}<br>
                        Newest: {format_datetime(newest_record) if newest_record else 'None'}
                    </div>
                </div>
            </div>""")
        
        print("""
        </div>""")
        
        # Cleanup estimate alert
        if stats['cleanup_estimate'] > 0:
            print(f"""
        <div class="alert">
            <strong>⚠️ Cleanup Recommended:</strong> {stats['cleanup_estimate']} articles are outside the retention period and can be cleaned up.
            Next scheduled cleanup: Daily at 2:00 AM UTC
        </div>""")
        else:
            print("""
        <div class="alert success">
            <strong>✅ System Healthy:</strong> All data is within configured retention periods. No cleanup needed.
        </div>""")
        
        print("""
    </div>
    
    <!-- Cleanup Summary -->
    <div class="section">
        <h2>📈 Cleanup Summary (Last 30 Days)</h2>""")
        
        if stats['cleanup_summary']:
            print("""
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Total Runs</th>
                    <th>Success Rate</th>
                    <th>Records Deleted</th>
                    <th>Avg per Run</th>
                    <th>Avg Duration</th>
                    <th>Last Cleanup</th>
                </tr>
            </thead>
            <tbody>""")
            
            for (cleanup_type, total_runs, total_deleted, avg_deleted, max_deleted, 
                 successful_runs, failed_runs, avg_duration_seconds, last_cleanup) in stats['cleanup_summary']:
                
                success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
                avg_deleted_display = f"{avg_deleted:.1f}" if avg_deleted else "0"
                
                print(f"""
                <tr>
                    <td><strong>{cleanup_type.title()}</strong></td>
                    <td>{total_runs}</td>
                    <td>
                        <span class="{'status-success' if success_rate >= 95 else 'status-error' if success_rate < 80 else 'status-running'}">
                            {success_rate:.1f}%
                        </span>
                        <small>({successful_runs}✅ / {failed_runs}❌)</small>
                    </td>
                    <td>{total_deleted:,}</td>
                    <td>{avg_deleted_display}</td>
                    <td>{format_duration(int(avg_duration_seconds)) if avg_duration_seconds else 'N/A'}</td>
                    <td>{format_datetime(last_cleanup)}</td>
                </tr>""")
            
            print("""
            </tbody>
        </table>""")
        else:
            print("""
        <div class="alert">
            <strong>ℹ️ No cleanup history found.</strong> Cleanup jobs haven't run yet or history is older than 30 days.
        </div>""")
        
        print("""
    </div>
    
    <!-- Recent Cleanup History -->
    <div class="section">
        <h2>📋 Recent Cleanup History</h2>""")
        
        if stats['cleanup_history']:
            print("""
        <table>
            <thead>
                <tr>
                    <th>Started</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Records Deleted</th>
                    <th>Duration</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>""")
            
            for (cleanup_type, records_deleted, batch_count, duration_seconds, status, 
                 started_at, completed_at, error_message) in stats['cleanup_history'][:20]:
                
                status_class = 'status-success' if status == 'completed' else 'status-error' if status == 'error' else 'status-running'
                
                print(f"""
                <tr>
                    <td>{format_datetime(started_at)}</td>
                    <td><span class="cleanup-badge cleanup-{'success' if status == 'completed' else 'error'}">{cleanup_type.title()}</span></td>
                    <td><span class="{status_class}">{status.title()}</span></td>
                    <td>{records_deleted:,}</td>
                    <td>{format_duration(duration_seconds)}</td>
                    <td>
                        {f'Batches: {batch_count}' if batch_count else ''}
                        {f'<br><small style="color: #e74c3c;">Error: {error_message}</small>' if error_message else ''}
                    </td>
                </tr>""")
            
            print("""
            </tbody>
        </table>""")
        else:
            print("""
        <div class="alert">
            <strong>ℹ️ No recent cleanup history.</strong> Cleanup jobs haven't run in the last 30 days.
        </div>""")
        
        print(f"""
    </div>
    
    <div style="margin-top: 30px; padding: 15px; background: #ecf0f1; border-radius: 5px; text-align: center; color: #7f8c8d; font-size: 0.9em;">
        <strong>Lifecycle Management Status:</strong> System is actively managing data retention and cleanup operations.<br>
        <small>Dashboard updates every 5 minutes • Generated at {format_datetime(datetime.now(timezone.utc))}</small>
    </div>
</body>
</html>""")
    
    except Exception as e:
        print(f"""
<!DOCTYPE html>
<html>
<head><title>Error - Lifecycle Management</title></head>
<body>
<h1>Lifecycle Management Dashboard Error</h1>
<p>An error occurred while generating the dashboard:</p>
<pre>{str(e)}</pre>
<p><a href="/cgi-bin/events.py">← Back to Event Analysis</a></p>
</body>
</html>""")
        print(f"<!-- Error details: {traceback.format_exc()} -->", file=sys.stderr)

if __name__ == "__main__":
    main()