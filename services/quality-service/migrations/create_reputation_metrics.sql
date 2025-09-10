-- News Agency Reputation Metrics Database Schema
-- Implementation of comprehensive journalism awards and professional recognition tracking
-- Based on QUALITY-SCORING-PROPOSAL.md Section: Agency Reputation Metrics

-- News Agency Reputation Metrics - Core journalism awards and professional recognition
CREATE TABLE IF NOT EXISTS news_agency_reputation_metrics (
    id BIGSERIAL PRIMARY KEY,
    outlet_name VARCHAR(255) NOT NULL UNIQUE,
    
    -- Major Journalism Awards (10 points each, max 40)
    pulitzer_awards INTEGER DEFAULT 0,
    pulitzer_years TEXT[], -- Array of years for awards tracking
    murrow_awards INTEGER DEFAULT 0,
    murrow_years TEXT[],
    peabody_awards INTEGER DEFAULT 0,
    peabody_years TEXT[],
    emmy_awards INTEGER DEFAULT 0,
    emmy_years TEXT[],
    
    -- Regional/Specialized Awards (5 points each, max 20)
    george_polk_awards INTEGER DEFAULT 0,
    george_polk_years TEXT[],
    dupont_awards INTEGER DEFAULT 0,
    dupont_years TEXT[],
    spj_awards INTEGER DEFAULT 0, -- Society of Professional Journalists
    spj_years TEXT[],
    other_specialized_awards INTEGER DEFAULT 0,
    other_awards_details TEXT[], -- Details of other awards
    
    -- Professional Standing Metrics (0-25 points)
    press_freedom_ranking INTEGER, -- Country/org press freedom index
    industry_memberships TEXT[], -- Professional journalism organizations
    editorial_independence_rating NUMERIC(3,1), -- 0-10 scale
    fact_checking_standards BOOLEAN DEFAULT FALSE,
    
    -- Credibility and Ethics (0-15 points)
    correction_policy_exists BOOLEAN DEFAULT FALSE,
    retraction_transparency BOOLEAN DEFAULT FALSE,
    ownership_transparency BOOLEAN DEFAULT FALSE,
    funding_disclosure BOOLEAN DEFAULT FALSE,
    ethics_code_public BOOLEAN DEFAULT FALSE,
    
    -- Computed scores (cached for performance)
    total_awards_score INTEGER DEFAULT 0,
    professional_standing_score INTEGER DEFAULT 0,
    credibility_score INTEGER DEFAULT 0,
    final_reputation_score NUMERIC(5,2) DEFAULT 0,
    
    -- Metadata
    last_research_date DATE,
    research_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast outlet lookup
CREATE INDEX IF NOT EXISTS idx_reputation_metrics_outlet_name 
ON news_agency_reputation_metrics(outlet_name);

-- Create index for reputation score queries
CREATE INDEX IF NOT EXISTS idx_reputation_metrics_final_score 
ON news_agency_reputation_metrics(final_reputation_score);

-- Outlet reputation tracking (simplified version referencing detailed metrics)
CREATE TABLE IF NOT EXISTS outlet_reputation_scores (
    id BIGSERIAL PRIMARY KEY,
    outlet VARCHAR(255) NOT NULL UNIQUE,
    reputation_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    
    -- Reference to detailed metrics
    reputation_metrics_id BIGINT REFERENCES news_agency_reputation_metrics(id),
    
    -- Quick lookup fields (denormalized for performance)
    total_major_awards INTEGER DEFAULT 0,
    has_fact_checking BOOLEAN DEFAULT FALSE,
    press_freedom_tier VARCHAR(20), -- 'excellent', 'good', 'fair', 'poor'
    
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast outlet reputation lookup
CREATE INDEX IF NOT EXISTS idx_outlet_reputation_outlet 
ON outlet_reputation_scores(outlet);

-- Create index for reputation score queries
CREATE INDEX IF NOT EXISTS idx_outlet_reputation_score 
ON outlet_reputation_scores(reputation_score);

-- Writing quality cache for performance (separate from main articles table)
CREATE TABLE IF NOT EXISTS article_writing_quality_cache (
    article_id BIGINT PRIMARY KEY REFERENCES articles(id),
    writing_quality_score NUMERIC(5,2) NOT NULL,
    
    -- Readability metrics
    flesch_reading_ease NUMERIC(5,2),
    flesch_kincaid_grade NUMERIC(4,2),
    readability_score INTEGER,
    
    -- Journalistic structure
    lead_quality_score INTEGER,
    source_attribution_score INTEGER,
    factual_completeness_score INTEGER,
    
    -- Linguistic quality
    sentence_variety_score INTEGER,
    vocabulary_precision_score INTEGER,
    grammar_score INTEGER,
    
    -- Objectivity
    bias_score INTEGER,
    balance_score INTEGER,
    
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for writing quality lookups
CREATE INDEX IF NOT EXISTS idx_writing_quality_cache_score 
ON article_writing_quality_cache(writing_quality_score);

-- Update articles table to support dual scoring system
-- Add new columns for reputation and writing quality separation
DO $$
BEGIN
    -- Add reputation score column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='articles' AND column_name='reputation_score'
    ) THEN
        ALTER TABLE articles ADD COLUMN reputation_score NUMERIC(5,2);
    END IF;
    
    -- Add writing quality score column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='articles' AND column_name='writing_quality_score'
    ) THEN
        ALTER TABLE articles ADD COLUMN writing_quality_score NUMERIC(5,2);
    END IF;
    
    -- Add composite quality score column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='articles' AND column_name='composite_quality_score'
    ) THEN
        ALTER TABLE articles ADD COLUMN composite_quality_score NUMERIC(5,2);
    END IF;
END $$;

-- Create indexes for new article columns
CREATE INDEX IF NOT EXISTS idx_articles_reputation_score 
ON articles(reputation_score) WHERE reputation_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_articles_writing_quality_score 
ON articles(writing_quality_score) WHERE writing_quality_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_articles_composite_quality_score 
ON articles(composite_quality_score) WHERE composite_quality_score IS NOT NULL;

-- Create trigger to update timestamp on reputation metrics changes
CREATE OR REPLACE FUNCTION update_reputation_metrics_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_reputation_metrics_timestamp
    BEFORE UPDATE ON news_agency_reputation_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_reputation_metrics_timestamp();

-- Create trigger to update timestamp on outlet reputation changes  
CREATE TRIGGER trigger_update_outlet_reputation_timestamp
    BEFORE UPDATE ON outlet_reputation_scores
    FOR EACH ROW
    EXECUTE FUNCTION update_reputation_metrics_timestamp();

-- Insert comment for documentation
COMMENT ON TABLE news_agency_reputation_metrics IS 'Comprehensive repository for journalism awards, professional recognition, and credibility indicators for news organizations';
COMMENT ON TABLE outlet_reputation_scores IS 'Simplified outlet reputation tracking with references to detailed metrics';
COMMENT ON TABLE article_writing_quality_cache IS 'Performance cache for writing quality analysis results';