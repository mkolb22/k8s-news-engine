#!/usr/bin/env python3
import cgi, cgitb, os, sys
import psycopg2
from datetime import datetime
cgitb.enable()

def get_db_connection():
    """Get database connection from environment"""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
    return psycopg2.connect(db_url)

def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'

def main():
    print("Content-Type: text/html\n")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get recent articles using correct column names
        cur.execute("""
            SELECT url, title, published_at, text, outlet
            FROM articles 
            ORDER BY published_at DESC 
            LIMIT 50
        """)
        articles = cur.fetchall()
        
        # Get event count
        cur.execute("SELECT COUNT(*) FROM events")
        event_count = cur.fetchone()[0]
        
        # Get article count
        cur.execute("SELECT COUNT(*) FROM articles")
        article_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"""<!DOCTYPE html>
<html>
<head>
    <title>K8s News Engine - Collected Data</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; }}
        .stat-card h3 {{ margin: 0 0 10px 0; color: #2c3e50; }}
        .stat-card .number {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        .articles {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .article {{ border-bottom: 1px solid #eee; padding: 15px 0; }}
        .article:last-child {{ border-bottom: none; }}
        .article-title {{ font-size: 1.1em; font-weight: bold; color: #2c3e50; margin-bottom: 5px; }}
        .article-meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }}
        .article-preview {{ color: #34495e; }}
        .no-data {{ text-align: center; color: #7f8c8d; padding: 40px; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>K8s News Engine</h1>
        <p>Real-time news verification and truth analysis system</p>
        <div style="margin-top: 15px;">
            <a href="/cgi-bin/index.py" style="color: #ecf0f1; margin-right: 20px; text-decoration: none;">📰 All Articles</a>
            <a href="/cgi-bin/events.py" style="color: #ecf0f1; text-decoration: none;">🎯 Event Analysis</a>
        </div>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Events</h3>
            <div class="number">{event_count}</div>
        </div>
        <div class="stat-card">
            <h3>Articles</h3>
            <div class="number">{article_count}</div>
        </div>
        <div class="stat-card">
            <h3>Status</h3>
            <div style="color: #27ae60; font-weight: bold;">Active</div>
        </div>
    </div>
    
    <div class="articles">
        <h2>Recent Articles</h2>""")
        
        if articles:
            for article in articles:
                url, title, published_at, text, outlet = article
                # Create preview from text content
                content_preview = text[:300] + '...' if text and len(text) > 300 else text if text else "No content available"
                print(f"""
        <div class="article">
            <div class="article-title">
                <a href="{url if url else '#'}" target="_blank">{title if title else 'No title'}</a>
            </div>
            <div class="article-meta">
                <strong>{outlet if outlet else 'Unknown'}</strong> • {format_datetime(published_at)}
            </div>
            <div class="article-preview">
                {content_preview[:300] + '...' if content_preview and len(content_preview) > 300 else content_preview if content_preview else 'No preview available'}
            </div>
        </div>""")
        else:
            print("""
        <div class="no-data">
            <h3>No articles collected yet</h3>
            <p>The RSS fetcher is running and will collect articles shortly.</p>
        </div>""")
        
        print("""
    </div>
    
    <div style="margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 0.9em;">
        <p>K8s News Engine • Powered by Alpine Linux & Kubernetes</p>
    </div>
</body>
</html>""")
        
    except Exception as e:
        print(f"""<!DOCTYPE html>
<html>
<head>
    <title>K8s News Engine - Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .error {{ background: #e74c3c; color: white; padding: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>Database Connection Error</h1>
        <p>Could not connect to the database. The system may still be starting up.</p>
        <p>Error: {str(e)}</p>
    </div>
</body>
</html>""")

if __name__ == "__main__":
    main()