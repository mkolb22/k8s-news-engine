-- Migration: Article Lifecycle Management System
-- Description: Implements configurable data retention and automated cleanup
-- Version: 002
-- Date: 2025-09-11

BEGIN;

-- Create system configuration table for lifecycle management
CREATE TABLE IF NOT EXISTS system_config (
    config_key VARCHAR(50) PRIMARY KEY,
    config_value VARCHAR(100) NOT NULL,
    description TEXT,
    config_type VARCHAR(20) DEFAULT 'string',
    min_value NUMERIC NULL,
    max_value NUMERIC NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default lifecycle configuration values
INSERT INTO system_config (config_key, config_value, description, config_type, min_value, max_value) VALUES 
    ('article_retention_hours', '168', '7 days article retention (168 hours)', 'integer', 24, 8760),
    ('event_retention_hours', '336', '14 days event retention (336 hours)', 'integer', 24, 8760),
    ('metrics_retention_hours', '720', '30 days metrics retention (720 hours)', 'integer', 168, 8760),
    ('cleanup_batch_size', '1000', 'Maximum records per cleanup batch', 'integer', 100, 10000),
    ('cleanup_enabled', 'true', 'Enable automated cleanup operations', 'boolean', NULL, NULL),
    ('publisher_page_size', '100', 'Default pagination size for publisher', 'integer', 10, 1000),
    ('max_display_articles', '500', 'Maximum articles to display without pagination', 'integer', 100, 2000)
ON CONFLICT (config_key) DO NOTHING;

-- Create cleanup log table to track cleanup operations
CREATE TABLE IF NOT EXISTS cleanup_log (
    id SERIAL PRIMARY KEY,
    cleanup_type VARCHAR(50) NOT NULL,
    records_deleted INTEGER DEFAULT 0,
    records_processed INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN completed_at IS NOT NULL 
            THEN EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER
            ELSE NULL 
        END
    ) STORED,
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT NULL,
    batch_count INTEGER DEFAULT 0
);

-- Create index for cleanup log queries
CREATE INDEX IF NOT EXISTS idx_cleanup_log_type_completed ON cleanup_log(cleanup_type, completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_cleanup_log_status ON cleanup_log(status, started_at DESC);

-- Function to get configuration values with type casting
CREATE OR REPLACE FUNCTION get_config_value(key_name VARCHAR, default_val VARCHAR DEFAULT NULL)
RETURNS VARCHAR AS $$
DECLARE
    result VARCHAR;
BEGIN
    SELECT config_value INTO result 
    FROM system_config 
    WHERE config_key = key_name;
    
    IF result IS NULL THEN
        RETURN default_val;
    END IF;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to get integer configuration values
CREATE OR REPLACE FUNCTION get_config_int(key_name VARCHAR, default_val INTEGER DEFAULT 0)
RETURNS INTEGER AS $$
BEGIN
    RETURN get_config_value(key_name, default_val::VARCHAR)::INTEGER;
EXCEPTION
    WHEN OTHERS THEN
        RETURN default_val;
END;
$$ LANGUAGE plpgsql;

-- Function to get boolean configuration values
CREATE OR REPLACE FUNCTION get_config_bool(key_name VARCHAR, default_val BOOLEAN DEFAULT FALSE)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_config_value(key_name, default_val::VARCHAR)::BOOLEAN;
EXCEPTION
    WHEN OTHERS THEN
        RETURN default_val;
END;
$$ LANGUAGE plpgsql;

-- Function to update configuration with validation
CREATE OR REPLACE FUNCTION update_config(
    key_name VARCHAR, 
    new_value VARCHAR,
    validate_range BOOLEAN DEFAULT TRUE
)
RETURNS BOOLEAN AS $$
DECLARE
    config_type VARCHAR;
    min_val NUMERIC;
    max_val NUMERIC;
    numeric_value NUMERIC;
BEGIN
    -- Get configuration metadata
    SELECT config_type, min_value, max_value 
    INTO config_type, min_val, max_val
    FROM system_config 
    WHERE config_key = key_name;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Configuration key % not found', key_name;
    END IF;
    
    -- Validate numeric ranges if enabled
    IF validate_range AND config_type IN ('integer', 'numeric') THEN
        BEGIN
            numeric_value := new_value::NUMERIC;
            
            IF min_val IS NOT NULL AND numeric_value < min_val THEN
                RAISE EXCEPTION 'Value % is below minimum % for %', new_value, min_val, key_name;
            END IF;
            
            IF max_val IS NOT NULL AND numeric_value > max_val THEN
                RAISE EXCEPTION 'Value % is above maximum % for %', new_value, max_val, key_name;
            END IF;
        EXCEPTION
            WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'Invalid numeric value % for %', new_value, key_name;
        END;
    END IF;
    
    -- Update the configuration
    UPDATE system_config 
    SET config_value = new_value, updated_at = NOW()
    WHERE config_key = key_name;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Safe batch cleanup procedure for articles
CREATE OR REPLACE PROCEDURE cleanup_old_articles()
LANGUAGE plpgsql AS $$
DECLARE
    batch_size INT;
    retention_hours INT;
    cleanup_enabled BOOLEAN;
    deleted_count INT := 0;
    total_deleted INT := 0;
    batch_count INT := 0;
    log_id INT;
    start_time TIMESTAMP := NOW();
BEGIN
    -- Check if cleanup is enabled
    cleanup_enabled := get_config_bool('cleanup_enabled', FALSE);
    IF NOT cleanup_enabled THEN
        RAISE NOTICE 'Cleanup is disabled in system configuration';
        RETURN;
    END IF;
    
    -- Get configuration values
    retention_hours := get_config_int('article_retention_hours', 168);
    batch_size := get_config_int('cleanup_batch_size', 1000);
    
    -- Create cleanup log entry
    INSERT INTO cleanup_log (cleanup_type, started_at, status)
    VALUES ('articles', start_time, 'running')
    RETURNING id INTO log_id;
    
    RAISE NOTICE 'Starting article cleanup: retention=% hours, batch_size=%', retention_hours, batch_size;
    
    -- Batch deletion loop
    LOOP
        -- Delete articles older than retention period
        WITH deleted_articles AS (
            DELETE FROM articles 
            WHERE published_at < NOW() - INTERVAL '1 hour' * retention_hours
            AND id IN (
                SELECT id FROM articles 
                WHERE published_at < NOW() - INTERVAL '1 hour' * retention_hours
                ORDER BY published_at ASC 
                LIMIT batch_size
            )
            RETURNING id
        )
        SELECT COUNT(*) INTO deleted_count FROM deleted_articles;
        
        total_deleted := total_deleted + deleted_count;
        batch_count := batch_count + 1;
        
        EXIT WHEN deleted_count = 0;
        
        -- Brief pause between batches to avoid overwhelming the database
        PERFORM pg_sleep(0.1);
        
        -- Safety check: limit maximum batches
        IF batch_count >= 100 THEN
            RAISE NOTICE 'Maximum batch limit reached, stopping cleanup';
            EXIT;
        END IF;
    END LOOP;
    
    -- Update cleanup log
    UPDATE cleanup_log 
    SET 
        records_deleted = total_deleted,
        records_processed = total_deleted,
        completed_at = NOW(),
        status = 'completed',
        batch_count = batch_count
    WHERE id = log_id;
    
    RAISE NOTICE 'Article cleanup completed: % articles deleted in % batches', total_deleted, batch_count;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Log error
        UPDATE cleanup_log 
        SET 
            completed_at = NOW(),
            status = 'error',
            error_message = SQLERRM,
            records_deleted = total_deleted,
            batch_count = batch_count
        WHERE id = log_id;
        
        RAISE;
END;
$$;

-- Safe batch cleanup procedure for events
CREATE OR REPLACE PROCEDURE cleanup_old_events()
LANGUAGE plpgsql AS $$
DECLARE
    batch_size INT;
    retention_hours INT;
    cleanup_enabled BOOLEAN;
    deleted_count INT := 0;
    total_deleted INT := 0;
    batch_count INT := 0;
    log_id INT;
    start_time TIMESTAMP := NOW();
BEGIN
    -- Check if cleanup is enabled
    cleanup_enabled := get_config_bool('cleanup_enabled', FALSE);
    IF NOT cleanup_enabled THEN
        RAISE NOTICE 'Cleanup is disabled in system configuration';
        RETURN;
    END IF;
    
    -- Get configuration values
    retention_hours := get_config_int('event_retention_hours', 336);
    batch_size := get_config_int('cleanup_batch_size', 1000);
    
    -- Create cleanup log entry
    INSERT INTO cleanup_log (cleanup_type, started_at, status)
    VALUES ('events', start_time, 'running')
    RETURNING id INTO log_id;
    
    RAISE NOTICE 'Starting event cleanup: retention=% hours, batch_size=%', retention_hours, batch_size;
    
    -- Batch deletion loop
    LOOP
        -- Delete events older than retention period
        WITH deleted_events AS (
            DELETE FROM events 
            WHERE created_at < NOW() - INTERVAL '1 hour' * retention_hours
            AND id IN (
                SELECT id FROM events 
                WHERE created_at < NOW() - INTERVAL '1 hour' * retention_hours
                ORDER BY created_at ASC 
                LIMIT batch_size
            )
            RETURNING id
        )
        SELECT COUNT(*) INTO deleted_count FROM deleted_events;
        
        total_deleted := total_deleted + deleted_count;
        batch_count := batch_count + 1;
        
        EXIT WHEN deleted_count = 0;
        
        -- Brief pause between batches
        PERFORM pg_sleep(0.1);
        
        -- Safety check: limit maximum batches
        IF batch_count >= 100 THEN
            RAISE NOTICE 'Maximum batch limit reached, stopping cleanup';
            EXIT;
        END IF;
    END LOOP;
    
    -- Update cleanup log
    UPDATE cleanup_log 
    SET 
        records_deleted = total_deleted,
        records_processed = total_deleted,
        completed_at = NOW(),
        status = 'completed',
        batch_count = batch_count
    WHERE id = log_id;
    
    RAISE NOTICE 'Event cleanup completed: % events deleted in % batches', total_deleted, batch_count;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Log error
        UPDATE cleanup_log 
        SET 
            completed_at = NOW(),
            status = 'error',
            error_message = SQLERRM,
            records_deleted = total_deleted,
            batch_count = batch_count
        WHERE id = log_id;
        
        RAISE;
END;
$$;

-- Safe batch cleanup procedure for old performance metrics
CREATE OR REPLACE PROCEDURE cleanup_old_metrics()
LANGUAGE plpgsql AS $$
DECLARE
    batch_size INT;
    retention_hours INT;
    cleanup_enabled BOOLEAN;
    deleted_count INT := 0;
    total_deleted INT := 0;
    batch_count INT := 0;
    log_id INT;
    start_time TIMESTAMP := NOW();
BEGIN
    -- Check if cleanup is enabled
    cleanup_enabled := get_config_bool('cleanup_enabled', FALSE);
    IF NOT cleanup_enabled THEN
        RAISE NOTICE 'Cleanup is disabled in system configuration';
        RETURN;
    END IF;
    
    -- Get configuration values
    retention_hours := get_config_int('metrics_retention_hours', 720);
    batch_size := get_config_int('cleanup_batch_size', 1000);
    
    -- Create cleanup log entry
    INSERT INTO cleanup_log (cleanup_type, started_at, status)
    VALUES ('metrics', start_time, 'running')
    RETURNING id INTO log_id;
    
    RAISE NOTICE 'Starting metrics cleanup: retention=% hours, batch_size=%', retention_hours, batch_size;
    
    -- Clean up old performance config snapshots (keep recent high-performing ones)
    LOOP
        WITH deleted_metrics AS (
            DELETE FROM performance_config_snapshots 
            WHERE snapshot_timestamp < NOW() - INTERVAL '1 hour' * retention_hours
            AND performance_score < 70  -- Keep high-performing configurations longer
            AND id IN (
                SELECT id FROM performance_config_snapshots 
                WHERE snapshot_timestamp < NOW() - INTERVAL '1 hour' * retention_hours
                AND performance_score < 70
                ORDER BY snapshot_timestamp ASC 
                LIMIT batch_size
            )
            RETURNING id
        )
        SELECT COUNT(*) INTO deleted_count FROM deleted_metrics;
        
        total_deleted := total_deleted + deleted_count;
        batch_count := batch_count + 1;
        
        EXIT WHEN deleted_count = 0;
        
        -- Brief pause between batches
        PERFORM pg_sleep(0.1);
        
        -- Safety check
        IF batch_count >= 50 THEN
            RAISE NOTICE 'Maximum batch limit reached, stopping cleanup';
            EXIT;
        END IF;
    END LOOP;
    
    -- Update cleanup log
    UPDATE cleanup_log 
    SET 
        records_deleted = total_deleted,
        records_processed = total_deleted,
        completed_at = NOW(),
        status = 'completed',
        batch_count = batch_count
    WHERE id = log_id;
    
    RAISE NOTICE 'Metrics cleanup completed: % records deleted in % batches', total_deleted, batch_count;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Log error
        UPDATE cleanup_log 
        SET 
            completed_at = NOW(),
            status = 'error',
            error_message = SQLERRM,
            records_deleted = total_deleted,
            batch_count = batch_count
        WHERE id = log_id;
        
        RAISE;
END;
$$;

-- Comprehensive cleanup procedure that runs all cleanups
CREATE OR REPLACE PROCEDURE run_all_cleanup()
LANGUAGE plpgsql AS $$
BEGIN
    RAISE NOTICE 'Starting comprehensive cleanup process';
    
    -- Run article cleanup
    CALL cleanup_old_articles();
    
    -- Run event cleanup
    CALL cleanup_old_events();
    
    -- Run metrics cleanup
    CALL cleanup_old_metrics();
    
    RAISE NOTICE 'Comprehensive cleanup process completed';
END;
$$;

-- Create view for cleanup statistics
CREATE OR REPLACE VIEW cleanup_statistics AS
SELECT 
    cleanup_type,
    COUNT(*) as total_runs,
    SUM(records_deleted) as total_records_deleted,
    AVG(records_deleted) as avg_records_per_run,
    AVG(duration_seconds) as avg_duration_seconds,
    MAX(completed_at) as last_cleanup,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_count
FROM cleanup_log 
WHERE completed_at IS NOT NULL
GROUP BY cleanup_type;

-- Create trigger to automatically update system_config.updated_at
CREATE OR REPLACE FUNCTION update_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_config_timestamp ON system_config;
CREATE TRIGGER trigger_update_config_timestamp
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_config_timestamp();

-- Grant permissions
GRANT SELECT ON system_config TO appuser;
GRANT SELECT ON cleanup_log TO appuser;
GRANT SELECT ON cleanup_statistics TO appuser;

COMMIT;

-- Display configuration after setup
SELECT 'Lifecycle Management Configuration' as info;
SELECT config_key, config_value, description FROM system_config ORDER BY config_key;

SELECT 'Setup completed successfully' as status;