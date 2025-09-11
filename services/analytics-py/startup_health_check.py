#!/usr/bin/env python3
"""
Analytics Worker Database Health Check at Startup
Validates database connectivity and required tables before starting analytics processing
"""
import os
import sys
import time
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

def perform_database_health_check():
    """Perform comprehensive database health check with retry logic"""
    db_url = os.environ.get('DATABASE_URL', 
                          'postgresql+psycopg2://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb')
    
    print(f"Analytics Worker Database Health Check")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Database URL: {db_url.split('@')[0]}@***")  # Hide password
    
    # Retry database connection with exponential backoff
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"Database connection attempt {attempt + 1}/{max_retries}")
            
            # Test database connection using SQLAlchemy
            engine = create_engine(db_url)
            
            with engine.begin() as conn:
                # Test database operations relevant to analytics worker
                result = conn.execute(text("SELECT COUNT(*) FROM events"))
                event_count = result.fetchone()[0]
                
                result = conn.execute(text("SELECT COUNT(*) FROM articles"))
                article_count = result.fetchone()[0]
                
                # Check if event_metrics table exists and is accessible
                try:
                    result = conn.execute(text("SELECT COUNT(*) FROM event_metrics"))
                    metrics_count = result.fetchone()[0]
                    metrics_status = "accessible"
                except Exception as e:
                    metrics_count = 0
                    metrics_status = f"not accessible: {str(e)}"
                
                # Check for events that need metrics computation
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM events e 
                    LEFT JOIN event_metrics em ON e.id = em.event_id 
                    WHERE em.event_id IS NULL
                """))
                unprocessed_events = result.fetchone()[0]
                
                print(f"Database connection successful")
                print(f"Events in database: {event_count}")
                print(f"Articles in database: {article_count}")
                print(f"Event metrics table: {metrics_status}")
                if metrics_status == "accessible":
                    print(f"Existing event metrics: {metrics_count}")
                print(f"Unprocessed events (need metrics): {unprocessed_events}")
                
            print("Analytics worker database health check passed successfully")
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

def perform_analytics_dependencies_check():
    """Validate analytics dependencies are available"""
    print(f"Analytics Worker Dependencies Health Check")
    
    try:
        # Test importing required analytics libraries
        import pandas as pd
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import yaml
        
        print(f"Successfully imported: pandas {pd.__version__}, numpy {np.__version__}, scikit-learn")
        
        # Test basic operations
        test_data = pd.DataFrame({'text': ['test article one', 'test article two']})
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(test_data['text'])
        similarity = cosine_similarity(vectors).mean()
        
        print(f"Test TF-IDF analysis completed (similarity: {similarity:.3f})")
        
        # Test YAML config loading
        config_path = 'configs/metrics.yml'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print(f"Successfully loaded configuration from {config_path}")
        else:
            print(f"WARNING: Configuration file {config_path} not found, will use defaults")
        
        print(f"Analytics dependencies health check passed successfully")
        return True
        
    except ImportError as e:
        print(f"ERROR: Missing required dependency: {e}")
        return False
        
    except Exception as e:
        print(f"ERROR: Analytics dependencies health check failed: {e}")
        return False

def main():
    """Main startup health check"""
    print("=" * 60)
    print("ANALYTICS WORKER STARTUP HEALTH CHECK")
    print("=" * 60)
    
    # Check environment variables
    print(f"TZ environment: {os.environ.get('TZ', 'Not set')}")
    print(f"DATABASE_URL configured: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
    
    # Perform database health check
    db_check = perform_database_health_check()
    
    # Perform analytics dependencies health check
    deps_check = perform_analytics_dependencies_check()
    
    if db_check and deps_check:
        print("✅ All health checks passed - Analytics worker ready to start")
        sys.exit(0)
    else:
        print("❌ Health checks failed - Analytics worker startup aborted")
        sys.exit(1)

if __name__ == "__main__":
    main()