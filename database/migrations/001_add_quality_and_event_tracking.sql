-- Migration: Add quality scoring and event tracking to articles table
-- Adds quality_score and computed_event_id fields for optimized publisher performance

-- Add quality_score column to articles table
ALTER TABLE articles 
ADD COLUMN quality_score NUMERIC DEFAULT NULL,
ADD COLUMN computed_event_id BIGINT DEFAULT NULL,
ADD COLUMN quality_computed_at TIMESTAMPTZ DEFAULT NULL;

-- Index for quality score queries
CREATE INDEX idx_articles_quality_score ON articles(quality_score DESC) WHERE quality_score IS NOT NULL;

-- Index for event grouping queries
CREATE INDEX idx_articles_computed_event ON articles(computed_event_id) WHERE computed_event_id IS NOT NULL;

-- Index for recent articles with quality scores (publisher optimization)
CREATE INDEX idx_articles_publisher_optimized ON articles(published_at DESC, quality_score DESC) 
WHERE published_at > NOW() - INTERVAL '72 hours' 
AND quality_score IS NOT NULL 
AND computed_event_id IS NOT NULL;

-- Update schema version tracking
INSERT INTO schema_versions (version, description, applied_at) VALUES 
(1, 'Add quality scoring and event tracking fields', NOW())
ON CONFLICT DO NOTHING;

-- Comments for documentation
COMMENT ON COLUMN articles.quality_score IS 'Pre-computed article quality score (0-100) calculated by quality-service';
COMMENT ON COLUMN articles.computed_event_id IS 'Event ID assigned by quality-service for articles covering the same story';
COMMENT ON COLUMN articles.quality_computed_at IS 'Timestamp when quality score and event grouping were last computed';