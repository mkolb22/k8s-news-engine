-- Update RSS feed outlet mapping function to include new agencies
-- This adds mapping cases for all the newly created news agencies

CREATE OR REPLACE FUNCTION map_outlet_to_agency_name(outlet_name TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Normalize outlet names to match agency reputation metrics
    -- Handle common variations and RSS feed naming conventions
    
    CASE LOWER(TRIM(outlet_name))
        -- BBC variations
        WHEN 'bbc news' THEN RETURN 'BBC News';
        WHEN 'bbc' THEN RETURN 'BBC News';
        WHEN 'bbc world' THEN RETURN 'BBC News';  -- Map BBC World RSS to BBC News agency
        
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
        WHEN 'the guardian world' THEN RETURN 'The Guardian';  -- Map Guardian World RSS to Guardian agency
        
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
        
        ELSE RETURN NULL; -- No mapping found
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Update RSS feeds to use the new mappings
UPDATE rss_feeds 
SET news_agency_id = (
    SELECT narm.id 
    FROM news_agency_reputation_metrics narm 
    WHERE narm.outlet_name = map_outlet_to_agency_name(rss_feeds.outlet)
)
WHERE news_agency_id IS NULL
AND map_outlet_to_agency_name(rss_feeds.outlet) IS NOT NULL;