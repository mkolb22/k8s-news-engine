#!/usr/bin/env python3
"""
Test script to validate timezone configuration fixes
Run this script to verify that timezone handling is working correctly
"""
import os
import sys
import psycopg2
import psycopg2.tz
from datetime import datetime, timezone
import traceback

def test_system_timezone():
    """Test system-level timezone configuration"""
    print("=== System Timezone Tests ===")
    
    # Check TZ environment variable
    tz_env = os.environ.get('TZ', 'Not set')
    print(f"TZ environment variable: {tz_env}")
    
    # Check Python's understanding of system timezone
    now_utc = datetime.now(timezone.utc)
    now_local = datetime.now()
    
    print(f"UTC time: {now_utc.isoformat()}")
    print(f"Local time: {now_local.isoformat()}")
    print(f"Local timezone aware: {now_local.tzinfo is not None}")
    
    return tz_env == 'UTC'

def test_database_timezone():
    """Test database timezone configuration"""
    print("\n=== Database Timezone Tests ===")
    
    try:
        # Test database connection
        db_url = os.environ.get('DATABASE_URL', 
                               'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Set timezone to UTC
        cur.execute("SET timezone = 'UTC'")
        conn.commit()
        
        # Check timezone setting
        cur.execute("SHOW timezone")
        db_tz = cur.fetchone()[0]
        print(f"Database timezone: {db_tz}")
        
        # Test timezone-aware datetime retrieval
        cur.execute("SELECT NOW() as current_time")
        db_time = cur.fetchone()[0]
        
        print(f"Database current time: {db_time}")
        print(f"Database time has timezone: {db_time.tzinfo is not None}")
        
        if db_time.tzinfo is not None:
            print(f"Database timezone info: {db_time.tzinfo}")
        
        cur.close()
        conn.close()
        
        return db_tz == 'UTC' and db_time.tzinfo is not None
        
    except Exception as e:
        print(f"Database timezone test failed: {str(e)}")
        return False

def test_datetime_arithmetic():
    """Test datetime arithmetic operations"""
    print("\n=== Datetime Arithmetic Tests ===")
    
    try:
        # Test timezone-aware datetime creation
        now_utc = datetime.now(timezone.utc)
        print(f"Created timezone-aware datetime: {now_utc}")
        
        # Test timezone-naive to timezone-aware conversion
        now_naive = datetime.now()
        now_aware = now_naive.replace(tzinfo=timezone.utc)
        print(f"Converted naive to aware: {now_aware}")
        
        # Test datetime arithmetic
        time_diff = (now_utc - now_aware).total_seconds()
        print(f"Datetime arithmetic successful: {time_diff:.2f} seconds difference")
        
        # Test ensure_timezone_aware function (simulate from events.py)
        def ensure_timezone_aware(dt):
            if dt is None:
                return datetime.now(timezone.utc)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            if dt.tzinfo is not None:
                return dt.astimezone(timezone.utc) if dt.tzinfo != timezone.utc else dt
            return dt
        
        # Test with various datetime objects
        test_cases = [
            None,
            datetime.now(),  # naive
            datetime.now(timezone.utc),  # aware UTC
        ]
        
        for i, test_dt in enumerate(test_cases):
            result = ensure_timezone_aware(test_dt)
            print(f"Test case {i+1}: {test_dt} -> {result} (tz-aware: {result.tzinfo is not None})")
        
        return True
        
    except Exception as e:
        print(f"Datetime arithmetic test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_database_integration():
    """Test full database integration with timezone handling"""
    print("\n=== Database Integration Tests ===")
    
    try:
        db_url = os.environ.get('DATABASE_URL', 
                               'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
        
        conn = psycopg2.connect(db_url)
        
        # Set timezone to UTC for this connection
        with conn.cursor() as cur:
            cur.execute("SET timezone = 'UTC'")
            conn.commit()
        
        cur = conn.cursor()
        
        # Test querying actual articles table
        cur.execute("""
            SELECT id, published_at
            FROM articles 
            WHERE published_at IS NOT NULL
            ORDER BY published_at DESC 
            LIMIT 5
        """)
        
        articles = cur.fetchall()
        
        if not articles:
            print("No articles found for testing")
            cur.close()
            conn.close()
            return True
        
        print(f"Found {len(articles)} articles for testing")
        
        # Test timezone handling with real data
        for article_id, published_at in articles:
            print(f"Article {article_id}: {published_at} (tz-aware: {published_at.tzinfo is not None})")
            
            # Test datetime arithmetic with database data
            now_utc = datetime.now(timezone.utc)
            
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            
            time_diff = (now_utc - published_at).total_seconds() / 3600
            print(f"  Hours ago: {time_diff:.2f}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Database integration test failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all timezone tests"""
    print("Timezone Configuration Test Suite")
    print("=" * 50)
    
    tests = [
        ("System Timezone", test_system_timezone),
        ("Database Timezone", test_database_timezone),
        ("Datetime Arithmetic", test_datetime_arithmetic),
        ("Database Integration", test_database_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\nERROR in {test_name}: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")
    
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()