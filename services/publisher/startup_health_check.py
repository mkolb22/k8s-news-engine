#!/usr/bin/env python3
"""
Publisher Service Database Health Check at Startup
Validates database connectivity before starting lighttpd
"""
import os
import sys
import time
import psycopg2
from datetime import datetime, timezone

def perform_database_health_check():
    """Perform comprehensive database health check with retry logic"""
    db_url = os.environ.get('DATABASE_URL', 
                          'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
    
    print(f"Publisher Service Database Health Check")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Database URL: {db_url.split('@')[0]}@***")  # Hide password
    
    # Retry database connection with exponential backoff
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"Database connection attempt {attempt + 1}/{max_retries}")
            
            # Test database connection
            conn = psycopg2.connect(db_url)
            
            # Set timezone to UTC for this connection
            with conn.cursor() as cur:
                cur.execute("SET timezone = 'UTC'")
                conn.commit()
                
                # Test basic database operations
                cur.execute("SELECT COUNT(*) FROM articles")
                article_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM rss_feeds WHERE active = TRUE")
                feed_count = cur.fetchone()[0]
                
                # Test timezone functionality
                cur.execute("SELECT NOW() as current_time")
                db_time = cur.fetchone()[0]
                
                print(f"Database connection successful")
                print(f"Articles in database: {article_count}")
                print(f"Active RSS feeds: {feed_count}")
                print(f"Database timezone test: {db_time}")
                
            conn.close()
            print("Publisher database health check passed successfully")
            return True
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"FATAL: Database health check failed after {max_retries} attempts: {e}")
                return False
            else:
                wait_time = 2 ** attempt  # exponential backoff: 1s, 2s, 4s, 8s
                print(f"Database connection failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
    
    return False

def main():
    """Main startup health check"""
    print("=" * 60)
    print("PUBLISHER SERVICE STARTUP HEALTH CHECK")
    print("=" * 60)
    
    # Check environment variables
    print(f"TZ environment: {os.environ.get('TZ', 'Not set')}")
    print(f"DATABASE_URL configured: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
    
    # Perform database health check
    if perform_database_health_check():
        print("✅ All health checks passed - Publisher service ready to start")
        sys.exit(0)
    else:
        print("❌ Health checks failed - Publisher service startup aborted")
        sys.exit(1)

if __name__ == "__main__":
    main()