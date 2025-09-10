#!/usr/bin/env python3
"""
Execute Database Migration Script

Runs the database schema standardization migration using psycopg2
"""

import psycopg2
import os
from datetime import datetime

def execute_migration():
    """Execute the database migration"""
    
    database_url = os.environ.get('DATABASE_URL', 
                                 'postgresql://appuser:newsengine2024@localhost:5432/newsdb?sslmode=disable')
    
    # Read the migration SQL
    with open('migrations/standardize_outlet_columns.sql', 'r') as f:
        migration_sql = f.read()
    
    try:
        print("🚀 Starting Database Schema Migration...")
        print("=" * 60)
        
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # Use explicit transaction control
        cursor = conn.cursor()
        
        # Execute migration SQL
        print("📝 Executing migration SQL...")
        cursor.execute(migration_sql)
        
        # Fetch any results from verification queries
        try:
            results = cursor.fetchall()
            if results:
                print("\n📊 Migration Verification Results:")
                for row in results:
                    print(f"  {row[0]:20} | Total: {row[1]:3d} | outlet_name: {row[2]:3d} | outlet: {row[3]:3d}")
        except psycopg2.ProgrammingError:
            # No results to fetch (normal for DDL statements)
            pass
        
        # Commit the transaction
        conn.commit()
        print("\n✅ Migration executed successfully and committed!")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("🎯 Database Migration Summary:")
        print("   ✓ Added outlet_name columns to articles and rss_feeds tables")
        print("   ✓ Migrated data from outlet to outlet_name columns")
        print("   ✓ Added NOT NULL constraints and indexes")
        print("   ✓ Updated mapping function for consistency")
        print("   ✓ Maintained backward compatibility with old columns")
        print("\n🔄 Next Steps:")
        print("   1. Update Quality Service code to use outlet_name")
        print("   2. Update other services one by one")
        print("   3. Run post-migration validation")
        print("   4. Remove old outlet columns after all services updated")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise

if __name__ == "__main__":
    os.environ['DATABASE_URL'] = 'postgresql://appuser:newsengine2024@localhost:5432/newsdb?sslmode=disable'
    execute_migration()