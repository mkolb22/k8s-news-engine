-- Add foreign key relationship from RSS feeds to news agency reputation metrics
-- This creates the optimal many-to-one relationship: rss_feeds -> news_agency_reputation_metrics

-- Add the foreign key column to rss_feeds table
ALTER TABLE rss_feeds 
ADD COLUMN news_agency_id BIGINT REFERENCES news_agency_reputation_metrics(id);

-- Create index for performance
CREATE INDEX idx_rss_feeds_news_agency_id ON rss_feeds(news_agency_id);

-- Create a function to map RSS feed outlet names to news agency names
CREATE OR REPLACE FUNCTION map_outlet_to_agency_name(outlet_name TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Normalize outlet names to match agency reputation metrics
    -- Handle common variations and RSS feed naming conventions
    
    CASE LOWER(TRIM(outlet_name))
        -- BBC variations
        WHEN 'bbc news' THEN RETURN 'BBC News';
        WHEN 'bbc' THEN RETURN 'BBC News';
        
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
        
        -- Fox News variations
        WHEN 'fox news' THEN RETURN 'Fox News';
        WHEN 'fox' THEN RETURN 'Fox News';
        WHEN 'foxnews.com' THEN RETURN 'Fox News';
        
        -- ProPublica variations
        WHEN 'propublica' THEN RETURN 'ProPublica';
        WHEN 'pro publica' THEN RETURN 'ProPublica';
        
        -- CBS variations
        WHEN 'cbs news' THEN RETURN 'CBS News';
        WHEN 'cbs' THEN RETURN 'CBS News';
        
        -- NBC variations  
        WHEN 'nbc news' THEN RETURN 'NBC News';
        WHEN 'nbc' THEN RETURN 'NBC News';
        
        ELSE RETURN NULL; -- No mapping found
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Update existing RSS feeds to link to their corresponding news agencies
UPDATE rss_feeds 
SET news_agency_id = (
    SELECT narm.id 
    FROM news_agency_reputation_metrics narm 
    WHERE narm.outlet_name = map_outlet_to_agency_name(rss_feeds.outlet)
)
WHERE map_outlet_to_agency_name(rss_feeds.outlet) IS NOT NULL;

-- Add comment to document the relationship
COMMENT ON COLUMN rss_feeds.news_agency_id IS 'Foreign key to news_agency_reputation_metrics table - many RSS feeds can belong to one news agency';
COMMENT ON FUNCTION map_outlet_to_agency_name(TEXT) IS 'Maps RSS feed outlet names to standardized news agency names for foreign key relationships';