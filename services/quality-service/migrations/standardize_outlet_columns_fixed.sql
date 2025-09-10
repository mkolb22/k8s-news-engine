-- Database Column Standardization Migration (Fixed)
-- Standardizes all outlet-related columns to 'outlet_name' with VARCHAR(255)
-- Handles trigger compatibility issues

BEGIN;

-- Enable detailed logging
SET log_statement = 'all';

-- ============================================================================
-- PHASE 1: Add new outlet_name columns to tables that need them
-- ============================================================================

-- Add outlet_name to articles table
ALTER TABLE articles ADD COLUMN IF NOT EXISTS outlet_name VARCHAR(255);
COMMENT ON COLUMN articles.outlet_name IS 'Standardized outlet name (migrated from outlet TEXT)';

-- Add outlet_name to rss_feeds table
ALTER TABLE rss_feeds ADD COLUMN IF NOT EXISTS outlet_name VARCHAR(255);  
COMMENT ON COLUMN rss_feeds.outlet_name IS 'Standardized outlet name (migrated from outlet TEXT)';

-- Handle outlet_reputation_scores table carefully (has triggers)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'outlet_reputation_scores' 
               AND column_name = 'outlet') THEN
        
        -- Add new outlet_name column
        ALTER TABLE outlet_reputation_scores ADD COLUMN IF NOT EXISTS outlet_name VARCHAR(255);
        
        -- Disable trigger temporarily to avoid conflicts
        ALTER TABLE outlet_reputation_scores DISABLE TRIGGER trigger_update_outlet_reputation_timestamp;
        
        -- Copy data from outlet to outlet_name (only where outlet_name is NULL)
        UPDATE outlet_reputation_scores 
        SET outlet_name = outlet 
        WHERE outlet_name IS NULL;
        
        -- Re-enable trigger
        ALTER TABLE outlet_reputation_scores ENABLE TRIGGER trigger_update_outlet_reputation_timestamp;
        
        -- Add NOT NULL constraint
        ALTER TABLE outlet_reputation_scores ALTER COLUMN outlet_name SET NOT NULL;
        
        RAISE NOTICE 'Added outlet_name column to outlet_reputation_scores';
    END IF;
END $$;

-- ============================================================================
-- PHASE 2: Migrate data from old columns to new standardized columns
-- ============================================================================

-- Migrate articles.outlet -> articles.outlet_name
UPDATE articles 
SET outlet_name = outlet 
WHERE outlet_name IS NULL;

-- Migrate rss_feeds.outlet -> rss_feeds.outlet_name  
UPDATE rss_feeds 
SET outlet_name = outlet 
WHERE outlet_name IS NULL;

-- ============================================================================
-- PHASE 3: Add constraints and indexes for new columns
-- ============================================================================

-- Add NOT NULL constraints
ALTER TABLE articles ALTER COLUMN outlet_name SET NOT NULL;
ALTER TABLE rss_feeds ALTER COLUMN outlet_name SET NOT NULL;

-- Add indexes for performance (outlet columns were likely indexed)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_outlet_name ON articles(outlet_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rss_feeds_outlet_name ON rss_feeds(outlet_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_outlet_reputation_scores_outlet_name ON outlet_reputation_scores(outlet_name);

-- ============================================================================
-- PHASE 4: Update the RSS feed mapping function to use new column names
-- ============================================================================

-- Update the mapping function to be consistent with new column naming
CREATE OR REPLACE FUNCTION map_outlet_to_agency_name(outlet_name TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Normalize outlet names to match agency reputation metrics
    -- Handle common variations and RSS feed naming conventions
    
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
        
        -- Associated Press variations
        WHEN 'associated press' THEN RETURN 'Associated Press';
        WHEN 'ap news' THEN RETURN 'Associated Press';
        WHEN 'ap' THEN RETURN 'Associated Press';
        
        -- New York Times variations
        WHEN 'the new york times' THEN RETURN 'The New York Times';
        WHEN 'new york times' THEN RETURN 'The New York Times';
        WHEN 'nytimes' THEN RETURN 'The New York Times';
        WHEN 'nyt' THEN RETURN 'The New York Times';
        
        -- NPR variations
        WHEN 'npr' THEN RETURN 'NPR';
        WHEN 'npr news' THEN RETURN 'NPR';
        WHEN 'national public radio' THEN RETURN 'NPR';
        
        -- Washington Post variations
        WHEN 'the washington post' THEN RETURN 'The Washington Post';
        WHEN 'washington post' THEN RETURN 'The Washington Post';
        WHEN 'washpost' THEN RETURN 'The Washington Post';
        
        -- Guardian variations
        WHEN 'the guardian' THEN RETURN 'The Guardian';
        WHEN 'guardian' THEN RETURN 'The Guardian';
        WHEN 'theguardian.com' THEN RETURN 'The Guardian';
        WHEN 'the guardian world' THEN RETURN 'The Guardian';
        
        -- Fox News variations
        WHEN 'fox news' THEN RETURN 'Fox News';
        WHEN 'fox' THEN RETURN 'Fox News';
        WHEN 'foxnews.com' THEN RETURN 'Fox News';
        
        -- ProPublica variations
        WHEN 'propublica' THEN RETURN 'ProPublica';
        WHEN 'pro publica' THEN RETURN 'ProPublica';
        
        -- ABC News variations (NEW)
        WHEN 'abc news' THEN RETURN 'ABC News';
        WHEN 'abc' THEN RETURN 'ABC News';
        WHEN 'abcnews.com' THEN RETURN 'ABC News';
        
        -- CBS variations (NEW)
        WHEN 'cbs news' THEN RETURN 'CBS News';
        WHEN 'cbs' THEN RETURN 'CBS News';
        WHEN 'cbsnews.com' THEN RETURN 'CBS News';
        
        -- NBC variations (NEW)
        WHEN 'nbc news' THEN RETURN 'NBC News';
        WHEN 'nbc' THEN RETURN 'NBC News';
        WHEN 'nbcnews.com' THEN RETURN 'NBC News';
        
        -- PBS variations (NEW)
        WHEN 'pbs newshour' THEN RETURN 'PBS NewsHour';
        WHEN 'pbs' THEN RETURN 'PBS NewsHour';
        WHEN 'newshour' THEN RETURN 'PBS NewsHour';
        
        -- Politico variations (NEW)
        WHEN 'politico' THEN RETURN 'Politico';
        WHEN 'politico.com' THEN RETURN 'Politico';
        
        -- VOA variations (NEW)
        WHEN 'voa news' THEN RETURN 'VOA News';
        WHEN 'voa' THEN RETURN 'VOA News';
        WHEN 'voice of america' THEN RETURN 'VOA News';
        
        -- Al Jazeera variations (NEW)
        WHEN 'al jazeera' THEN RETURN 'Al Jazeera';
        WHEN 'aljazeera' THEN RETURN 'Al Jazeera';
        WHEN 'aljazeera.com' THEN RETURN 'Al Jazeera';
        
        -- Sky News variations (NEW)
        WHEN 'sky news' THEN RETURN 'Sky News';
        WHEN 'sky news world' THEN RETURN 'Sky News';
        WHEN 'skynews.com' THEN RETURN 'Sky News';
        
        -- Democracy Now variations (NEW)
        WHEN 'democracy now' THEN RETURN 'Democracy Now';
        WHEN 'democracynow.org' THEN RETURN 'Democracy Now';
        
        -- Zerohedge variations (NEW)
        WHEN 'zerohedge' THEN RETURN 'Zerohedge';
        WHEN 'zerohedge.com' THEN RETURN 'Zerohedge';
        WHEN 'zero hedge' THEN RETURN 'Zerohedge';
        
        -- Deutsche Welle variations (NEW)
        WHEN 'deutsche welle' THEN RETURN 'Deutsche Welle';
        WHEN 'dw' THEN RETURN 'Deutsche Welle';
        WHEN 'dw.com' THEN RETURN 'Deutsche Welle';
        
        -- TechCrunch variations (NEW)
        WHEN 'techcrunch' THEN RETURN 'TechCrunch';
        WHEN 'techcrunch.com' THEN RETURN 'TechCrunch';
        WHEN 'tech crunch' THEN RETURN 'TechCrunch';
        
        ELSE RETURN NULL; -- No mapping found
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- PHASE 5: Verification and logging
-- ============================================================================

-- Log migration results
DO $$
DECLARE
    articles_count INTEGER;
    rss_feeds_count INTEGER;
    reputation_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO articles_count FROM articles WHERE outlet_name IS NOT NULL;
    SELECT COUNT(*) INTO rss_feeds_count FROM rss_feeds WHERE outlet_name IS NOT NULL;
    SELECT COUNT(*) INTO reputation_count FROM outlet_reputation_scores WHERE outlet_name IS NOT NULL;
    
    RAISE NOTICE '=== Migration Results ===';
    RAISE NOTICE 'Articles with outlet_name: %', articles_count;
    RAISE NOTICE 'RSS Feeds with outlet_name: %', rss_feeds_count;  
    RAISE NOTICE 'Reputation Scores with outlet_name: %', reputation_count;
    RAISE NOTICE '========================';
END $$;

-- Verify data integrity
SELECT 'articles' as table_name, 
       COUNT(*) as total_rows,
       COUNT(outlet_name) as outlet_name_populated,
       COUNT(outlet) as outlet_populated
FROM articles
UNION ALL
SELECT 'rss_feeds' as table_name,
       COUNT(*) as total_rows, 
       COUNT(outlet_name) as outlet_name_populated,
       COUNT(outlet) as outlet_populated
FROM rss_feeds
UNION ALL
SELECT 'outlet_reputation_scores' as table_name,
       COUNT(*) as total_rows, 
       COUNT(outlet_name) as outlet_name_populated,
       COUNT(outlet) as outlet_populated
FROM outlet_reputation_scores;

COMMIT;