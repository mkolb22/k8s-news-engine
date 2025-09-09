#!/usr/bin/env python3
"""
Health check endpoint for timezone and database connectivity validation
"""
import os
import sys
import json
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

def validate_timezone_handling():
    """Validate that timezone handling is working correctly"""
    checks = {
        'system_timezone': None,
        'python_timezone': None,
        'database_timezone': None,
        'datetime_operations': None,
        'overall_status': 'FAIL'
    }
    
    try:
        # Check system timezone
        system_tz = os.environ.get('TZ', 'Not set')
        checks['system_timezone'] = f"TZ={system_tz}"
        
        # Check Python timezone handling
        now_utc = datetime.now(timezone.utc)
        now_naive = datetime.now()
        checks['python_timezone'] = f"UTC: {now_utc.isoformat()}, Local: {now_naive.isoformat()}"
        
        # Check database timezone
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get database timezone setting
        cur.execute("SHOW timezone")
        db_tz = cur.fetchone()[0]
        checks['database_timezone'] = f"Database TZ: {db_tz}"
        
        # Test timezone-aware datetime operations
        cur.execute("SELECT NOW() as current_time")
        db_time = cur.fetchone()[0]
        
        # Ensure database time is timezone-aware
        if db_time.tzinfo is None:
            # If timezone-naive, assume UTC (this shouldn't happen with proper config)
            db_time_aware = db_time.replace(tzinfo=timezone.utc)
        else:
            db_time_aware = db_time.astimezone(timezone.utc)
        
        # Test datetime arithmetic (this is where the original error occurred)
        time_diff = (now_utc - db_time_aware).total_seconds()
        checks['datetime_operations'] = f"Time diff calculation successful: {time_diff:.2f}s"
        
        cur.close()
        conn.close()
        
        # If we get here, all checks passed
        checks['overall_status'] = 'OK'
        
    except Exception as e:
        checks['datetime_operations'] = f"ERROR: {str(e)}"
        
    return checks

def main():
    print("Content-Type: application/json\n")
    
    try:
        health_status = validate_timezone_handling()
        
        # Set HTTP status based on overall status
        if health_status['overall_status'] == 'OK':
            print("Status: 200 OK")
            status_code = 200
        else:
            print("Status: 500 Internal Server Error")
            status_code = 500
        
        # Return JSON response
        response = {
            'status': health_status['overall_status'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': health_status,
            'service': 'publisher'
        }
        
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        print("Status: 500 Internal Server Error")
        error_response = {
            'status': 'FAIL',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e),
            'traceback': traceback.format_exc(),
            'service': 'publisher'
        }
        print(json.dumps(error_response, indent=2))

if __name__ == "__main__":
    main()