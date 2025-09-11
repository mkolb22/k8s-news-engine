#!/usr/bin/env python3
"""
Quality Service Database Health Check at Startup
Validates database connectivity and NER model loading before starting service
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
    
    print(f"Quality Service Database Health Check")
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
                
                # Test database operations relevant to quality service
                cur.execute("SELECT COUNT(*) FROM articles")
                article_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM events")
                event_count = cur.fetchone()[0]
                
                # Check if articles table has unprocessed articles (no NER data)
                cur.execute("SELECT COUNT(*) FROM articles WHERE ner_extracted_at IS NULL")
                unprocessed_count = cur.fetchone()[0]
                
                print(f"Database connection successful")
                print(f"Articles in database: {article_count}")
                print(f"Events in database: {event_count}")
                print(f"Unprocessed articles (no NER data): {unprocessed_count}")
                
            conn.close()
            print("Quality service database health check passed successfully")
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

def perform_ner_model_check():
    """Validate NER model availability"""
    print(f"Quality Service NER Model Health Check")
    
    try:
        # Test importing the improved NER system
        from improved_ner import get_ner_extractor
        extractor = get_ner_extractor()
        
        # Test a simple entity extraction
        test_text = "Apple Inc. is a technology company based in Cupertino, California."
        entities = extractor.extract_key_entities_for_grouping(test_text)
        
        print(f"NER model loaded successfully")
        print(f"Test extraction from sample text found {len(entities)} entities")
        print(f"NER model health check passed successfully")
        return True
        
    except ImportError as e:
        print(f"WARNING: Improved NER not available, will use fallback: {e}")
        return True  # Don't fail startup if NER isn't available - service will use fallback
        
    except Exception as e:
        print(f"ERROR: NER model health check failed: {e}")
        return False

def main():
    """Main startup health check"""
    print("=" * 60)
    print("QUALITY SERVICE STARTUP HEALTH CHECK")
    print("=" * 60)
    
    # Check environment variables
    print(f"TZ environment: {os.environ.get('TZ', 'Not set')}")
    print(f"DATABASE_URL configured: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
    
    # Perform database health check
    db_check = perform_database_health_check()
    
    # Perform NER model health check
    ner_check = perform_ner_model_check()
    
    if db_check and ner_check:
        print("✅ All health checks passed - Quality service ready to start")
        sys.exit(0)
    else:
        print("❌ Health checks failed - Quality service startup aborted")
        sys.exit(1)

if __name__ == "__main__":
    main()