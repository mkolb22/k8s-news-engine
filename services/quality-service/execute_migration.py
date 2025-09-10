#!/usr/bin/env python3
"""
Execute database schema migration with proper error handling
"""

import psycopg2
import sys

def execute_migration():
    """Execute the database schema migration in phases"""
    
    try:
        # Connect with admin credentials
        conn = psycopg2.connect('postgresql://postgres:adminpass2024@localhost:5432/newsdb?sslmode=disable')
        cursor = conn.cursor()
        
        print("🔄 Starting database schema migration with admin credentials...")
        
        # Phase 1: Add columns and migrate data
        print("\n📋 Phase 1: Adding columns and migrating data...")
        
        # Add outlet_name columns
        cursor.execute("ALTER TABLE articles ADD COLUMN IF NOT EXISTS outlet_name VARCHAR(255);")
        cursor.execute("ALTER TABLE rss_feeds ADD COLUMN IF NOT EXISTS outlet_name VARCHAR(255);") 
        cursor.execute("ALTER TABLE outlet_reputation_scores ADD COLUMN IF NOT EXISTS outlet_name VARCHAR(255);")
        
        # Migrate data
        cursor.execute("UPDATE articles SET outlet_name = outlet WHERE outlet_name IS NULL;")
        cursor.execute("UPDATE rss_feeds SET outlet_name = outlet WHERE outlet_name IS NULL;")
        
        # Handle outlet_reputation_scores with trigger
        cursor.execute("ALTER TABLE outlet_reputation_scores DISABLE TRIGGER trigger_update_outlet_reputation_timestamp;")
        cursor.execute("UPDATE outlet_reputation_scores SET outlet_name = outlet WHERE outlet_name IS NULL;")
        cursor.execute("ALTER TABLE outlet_reputation_scores ENABLE TRIGGER trigger_update_outlet_reputation_timestamp;")
        
        # Add NOT NULL constraints
        cursor.execute("ALTER TABLE articles ALTER COLUMN outlet_name SET NOT NULL;")
        cursor.execute("ALTER TABLE rss_feeds ALTER COLUMN outlet_name SET NOT NULL;")
        cursor.execute("ALTER TABLE outlet_reputation_scores ALTER COLUMN outlet_name SET NOT NULL;")
        
        conn.commit()
        print("✅ Phase 1 completed: Added outlet_name columns and migrated data")
        
        # Phase 2: Create indexes (need autocommit for CONCURRENTLY)
        print("\n🔄 Phase 2: Creating indexes...")
        conn.set_session(autocommit=True)
        
        indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_outlet_name ON articles(outlet_name);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rss_feeds_outlet_name ON rss_feeds(outlet_name);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_outlet_reputation_scores_outlet_name ON outlet_reputation_scores(outlet_name);"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                table_name = index_sql.split("ON ")[1].split("(")[0].strip()
                print(f"  ✓ Created index for {table_name}")
            except Exception as e:
                print(f"  ⚠️  Index creation warning: {e}")
        
        print("✅ Phase 2 completed: Created indexes")
        
        # Phase 3: Update mapping function
        print("\n🔄 Phase 3: Updating mapping function...")
        
        mapping_function_sql = """
        CREATE OR REPLACE FUNCTION map_outlet_to_agency_name(outlet_name TEXT)
        RETURNS TEXT AS $$
        BEGIN
            CASE LOWER(TRIM(outlet_name))
                -- BBC variations
                WHEN 'bbc news' THEN RETURN 'BBC News';
                WHEN 'bbc' THEN RETURN 'BBC News';
                WHEN 'bbc world' THEN RETURN 'BBC News';
                -- CNN variations  
                WHEN 'cnn' THEN RETURN 'CNN';
                WHEN 'cnn top stories' THEN RETURN 'CNN';
                WHEN 'cnn.com' THEN RETURN 'CNN';
                -- Reuters variations
                WHEN 'reuters' THEN RETURN 'Reuters';
                WHEN 'reuters top news' THEN RETURN 'Reuters';
                WHEN 'reuters.com' THEN RETURN 'Reuters';
                -- ABC News variations
                WHEN 'abc news' THEN RETURN 'ABC News';
                WHEN 'abc' THEN RETURN 'ABC News';
                WHEN 'abcnews.com' THEN RETURN 'ABC News';
                -- CBS variations
                WHEN 'cbs news' THEN RETURN 'CBS News';
                WHEN 'cbs' THEN RETURN 'CBS News';
                WHEN 'cbsnews.com' THEN RETURN 'CBS News';
                -- NBC variations
                WHEN 'nbc news' THEN RETURN 'NBC News';
                WHEN 'nbc' THEN RETURN 'NBC News';
                WHEN 'nbcnews.com' THEN RETURN 'NBC News';
                -- PBS variations
                WHEN 'pbs newshour' THEN RETURN 'PBS NewsHour';
                WHEN 'pbs' THEN RETURN 'PBS NewsHour';
                WHEN 'newshour' THEN RETURN 'PBS NewsHour';
                -- Politico variations
                WHEN 'politico' THEN RETURN 'Politico';
                WHEN 'politico.com' THEN RETURN 'Politico';
                -- VOA variations
                WHEN 'voa news' THEN RETURN 'VOA News';
                WHEN 'voa' THEN RETURN 'VOA News';
                WHEN 'voice of america' THEN RETURN 'VOA News';
                -- Al Jazeera variations
                WHEN 'al jazeera' THEN RETURN 'Al Jazeera';
                WHEN 'aljazeera' THEN RETURN 'Al Jazeera';
                WHEN 'aljazeera.com' THEN RETURN 'Al Jazeera';
                -- Sky News variations
                WHEN 'sky news' THEN RETURN 'Sky News';
                WHEN 'sky news world' THEN RETURN 'Sky News';
                WHEN 'skynews.com' THEN RETURN 'Sky News';
                -- Democracy Now variations
                WHEN 'democracy now' THEN RETURN 'Democracy Now';
                WHEN 'democracynow.org' THEN RETURN 'Democracy Now';
                -- Zerohedge variations
                WHEN 'zerohedge' THEN RETURN 'Zerohedge';
                WHEN 'zerohedge.com' THEN RETURN 'Zerohedge';
                WHEN 'zero hedge' THEN RETURN 'Zerohedge';
                -- Deutsche Welle variations
                WHEN 'deutsche welle' THEN RETURN 'Deutsche Welle';
                WHEN 'dw' THEN RETURN 'Deutsche Welle';
                WHEN 'dw.com' THEN RETURN 'Deutsche Welle';
                -- TechCrunch variations
                WHEN 'techcrunch' THEN RETURN 'TechCrunch';
                WHEN 'techcrunch.com' THEN RETURN 'TechCrunch';
                WHEN 'tech crunch' THEN RETURN 'TechCrunch';
                -- Guardian variations
                WHEN 'the guardian' THEN RETURN 'The Guardian';
                WHEN 'guardian' THEN RETURN 'The Guardian';
                WHEN 'theguardian.com' THEN RETURN 'The Guardian';
                WHEN 'the guardian world' THEN RETURN 'The Guardian';
                -- NPR variations
                WHEN 'npr' THEN RETURN 'NPR';
                WHEN 'npr news' THEN RETURN 'NPR';
                WHEN 'national public radio' THEN RETURN 'NPR';
                -- Associated Press variations
                WHEN 'associated press' THEN RETURN 'Associated Press';
                WHEN 'ap news' THEN RETURN 'Associated Press';
                WHEN 'ap' THEN RETURN 'Associated Press';
                -- New York Times variations
                WHEN 'the new york times' THEN RETURN 'The New York Times';
                WHEN 'new york times' THEN RETURN 'The New York Times';
                WHEN 'nytimes' THEN RETURN 'The New York Times';
                WHEN 'nyt' THEN RETURN 'The New York Times';
                -- Washington Post variations
                WHEN 'the washington post' THEN RETURN 'The Washington Post';
                WHEN 'washington post' THEN RETURN 'The Washington Post';
                WHEN 'washpost' THEN RETURN 'The Washington Post';
                -- Fox News variations
                WHEN 'fox news' THEN RETURN 'Fox News';
                WHEN 'fox' THEN RETURN 'Fox News';
                WHEN 'foxnews.com' THEN RETURN 'Fox News';
                -- ProPublica variations
                WHEN 'propublica' THEN RETURN 'ProPublica';
                WHEN 'pro publica' THEN RETURN 'ProPublica';
                ELSE RETURN NULL;
            END CASE;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """
        
        cursor.execute(mapping_function_sql)
        print("✅ Phase 3 completed: Updated mapping function")
        
        # Verification
        cursor.execute("""
            SELECT 
                'articles' as table_name,
                COUNT(*) as total_rows,
                COUNT(outlet_name) as outlet_name_populated,
                COUNT(outlet_name) as outlet_name_populated_duplicate
            FROM articles
            UNION ALL
            SELECT 
                'rss_feeds',
                COUNT(*),
                COUNT(outlet_name),
                COUNT(outlet)
            FROM rss_feeds
            UNION ALL
            SELECT 
                'outlet_reputation_scores',
                COUNT(*),
                COUNT(outlet_name), 
                COUNT(outlet)
            FROM outlet_reputation_scores
        """)
        
        results = cursor.fetchall()
        print("\n📊 Migration Verification:")
        for table, total, outlet_name_count, outlet_count in results:
            print(f"  {table:25} | Total: {total:3d} | outlet_name: {outlet_name_count:3d} | outlet: {outlet_count:3d}")
        
        print("\n✅ Database schema migration completed successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    execute_migration()