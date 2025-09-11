-- Migration: Performance-Driven Configuration System
-- Date: 2025-09-11
-- Purpose: Create tables for performance-driven event grouping configuration

-- Main performance configuration snapshots table
CREATE TABLE performance_config_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Configuration Parameters (Runtime Tunable)
    min_shared_entities INTEGER NOT NULL DEFAULT 2,
    entity_overlap_threshold DECIMAL(4,3) NOT NULL DEFAULT 0.250,
    min_title_keywords INTEGER NOT NULL DEFAULT 0,
    title_keyword_bonus DECIMAL(4,3) NOT NULL DEFAULT 0.100,
    max_time_diff_hours INTEGER NOT NULL DEFAULT 48,
    allow_same_outlet BOOLEAN NOT NULL DEFAULT false,
    
    -- NER Quality Settings
    min_entity_length INTEGER NOT NULL DEFAULT 3,
    max_entity_length INTEGER NOT NULL DEFAULT 50,
    entity_noise_threshold DECIMAL(4,3) NOT NULL DEFAULT 0.200,
    
    -- Performance Metrics (Measured Results)
    articles_processed INTEGER NOT NULL DEFAULT 0,
    events_created INTEGER NOT NULL DEFAULT 0,
    processing_time_ms INTEGER NOT NULL DEFAULT 0,
    entities_extracted_total INTEGER NOT NULL DEFAULT 0,
    
    -- Calculated Quality Metrics  
    event_creation_rate DECIMAL(6,4) DEFAULT NULL, -- events / articles
    coverage_percentage DECIMAL(5,2) DEFAULT NULL, -- % articles in multi-article events
    avg_articles_per_event DECIMAL(4,1) DEFAULT NULL,
    singleton_events_count INTEGER DEFAULT 0,
    entities_per_article DECIMAL(4,1) DEFAULT NULL,
    
    -- Overall Performance Score (0-100)
    performance_score DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    
    -- Score Components (0-100 each)
    effectiveness_score DECIMAL(5,2) DEFAULT NULL, -- Event creation quality
    efficiency_score DECIMAL(5,2) DEFAULT NULL,    -- Processing performance  
    coverage_score DECIMAL(5,2) DEFAULT NULL,      -- Article grouping coverage
    precision_score DECIMAL(5,2) DEFAULT NULL,     -- Grouping accuracy
    
    -- Metadata
    config_source VARCHAR(50) NOT NULL DEFAULT 'runtime', -- 'startup', 'runtime', 'manual'
    service_instance VARCHAR(100) DEFAULT NULL,
    notes TEXT,
    
    -- Performance Trend Indicators
    score_trend VARCHAR(20) DEFAULT NULL, -- 'improving', 'declining', 'stable'
    config_generation INTEGER NOT NULL DEFAULT 1,
    
    UNIQUE(snapshot_timestamp, service_instance)
);

-- Configuration change events log
CREATE TABLE config_change_events (
    id SERIAL PRIMARY KEY,
    change_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- What Changed
    parameter_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    change_reason VARCHAR(200) DEFAULT NULL, -- 'performance_decline', 'startup', 'manual_override', 'auto_tune'
    
    -- Performance Context
    previous_score DECIMAL(5,2) DEFAULT NULL,
    target_improvement VARCHAR(100) DEFAULT NULL, -- 'increase_coverage', 'reduce_processing_time', etc.
    
    -- References  
    config_snapshot_id INTEGER REFERENCES performance_config_snapshots(id),
    triggered_by VARCHAR(100) NOT NULL DEFAULT 'system',
    
    -- Validation
    change_validated BOOLEAN DEFAULT false,
    validation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    validation_result TEXT
);

-- Performance baselines for comparison
CREATE TABLE performance_baselines (
    id SERIAL PRIMARY KEY,
    baseline_name VARCHAR(100) UNIQUE NOT NULL,
    
    -- Baseline Configuration
    config_snapshot_id INTEGER NOT NULL REFERENCES performance_config_snapshots(id),
    
    -- Target Performance Ranges
    min_acceptable_score DECIMAL(5,2) NOT NULL DEFAULT 60.0,
    target_score DECIMAL(5,2) NOT NULL DEFAULT 80.0,
    optimal_score DECIMAL(5,2) NOT NULL DEFAULT 90.0,
    
    -- Baseline Metrics
    baseline_event_rate DECIMAL(6,4) NOT NULL,
    baseline_coverage DECIMAL(5,2) NOT NULL,
    baseline_processing_time_ms INTEGER NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT true,
    description TEXT
);

-- Indexes for performance
CREATE INDEX idx_perf_snapshots_timestamp ON performance_config_snapshots(snapshot_timestamp DESC);
CREATE INDEX idx_perf_snapshots_score ON performance_config_snapshots(performance_score DESC);
CREATE INDEX idx_perf_snapshots_source ON performance_config_snapshots(config_source);
CREATE INDEX idx_config_changes_timestamp ON config_change_events(change_timestamp DESC);
CREATE INDEX idx_config_changes_parameter ON config_change_events(parameter_name);

-- Views for monitoring and analysis
CREATE VIEW current_performance_status AS
SELECT 
    snapshot_timestamp,
    performance_score,
    effectiveness_score,
    efficiency_score,  
    coverage_score,
    precision_score,
    articles_processed,
    events_created,
    event_creation_rate,
    coverage_percentage,
    CASE 
        WHEN articles_processed > 0 THEN processing_time_ms::DECIMAL / articles_processed 
        ELSE NULL 
    END as ms_per_article,
    config_source,
    service_instance
FROM performance_config_snapshots
WHERE snapshot_timestamp > NOW() - INTERVAL '1 hour'
ORDER BY snapshot_timestamp DESC;

CREATE VIEW performance_trends AS
SELECT 
    DATE_TRUNC('hour', snapshot_timestamp) as hour,
    AVG(performance_score) as avg_score,
    MAX(performance_score) as max_score,
    MIN(performance_score) as min_score,
    COUNT(*) as snapshots_count,
    AVG(event_creation_rate) as avg_event_rate,
    AVG(coverage_percentage) as avg_coverage
FROM performance_config_snapshots
WHERE snapshot_timestamp > NOW() - INTERVAL '24 hours'
    AND performance_score IS NOT NULL
GROUP BY DATE_TRUNC('hour', snapshot_timestamp)
ORDER BY hour DESC;

-- Insert default conservative configuration as baseline
INSERT INTO performance_config_snapshots (
    min_shared_entities,
    entity_overlap_threshold, 
    min_title_keywords,
    title_keyword_bonus,
    max_time_diff_hours,
    allow_same_outlet,
    min_entity_length,
    max_entity_length,
    entity_noise_threshold,
    config_source,
    service_instance,
    notes,
    config_generation,
    performance_score
) VALUES (
    2,           -- min_shared_entities (reduced from 4)
    0.250,       -- entity_overlap_threshold (reduced from 0.5) 
    0,           -- min_title_keywords (removed requirement)
    0.100,       -- title_keyword_bonus
    48,          -- max_time_diff_hours
    false,       -- allow_same_outlet
    3,           -- min_entity_length
    50,          -- max_entity_length
    0.200,       -- entity_noise_threshold
    'startup',   -- config_source
    'initial',   -- service_instance
    'Conservative default configuration for initial deployment - relaxed thresholds to ensure event creation',
    1,           -- config_generation
    75.0         -- estimated performance_score for balanced config
);

-- Create initial baseline from the default configuration
INSERT INTO performance_baselines (
    baseline_name,
    config_snapshot_id,
    min_acceptable_score,
    target_score, 
    optimal_score,
    baseline_event_rate,
    baseline_coverage,
    baseline_processing_time_ms,
    description
) 
SELECT 
    'default_conservative',
    id,
    60.0,  -- min_acceptable_score
    75.0,  -- target_score
    85.0,  -- optimal_score
    0.20,  -- baseline_event_rate (20% of articles should form events)
    40.0,  -- baseline_coverage (40% coverage target)
    5000,  -- baseline_processing_time_ms (5 seconds for 50 articles = 100ms/article)
    'Default conservative baseline for event grouping performance'
FROM performance_config_snapshots 
WHERE config_source = 'startup' 
    AND service_instance = 'initial'
ORDER BY id DESC 
LIMIT 1;

COMMENT ON TABLE performance_config_snapshots IS 'Stores configuration parameters and performance metrics for event grouping system';
COMMENT ON TABLE config_change_events IS 'Audit trail for all configuration parameter changes';
COMMENT ON TABLE performance_baselines IS 'Performance baselines for comparison and goal setting';