#!/usr/bin/env python3
"""
Performance Configuration Manager for Event Grouping System
Manages loading, saving, and optimizing configuration based on performance metrics
"""
import os
import sys
import json
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Any, Tuple

# Import performance scorer
from performance_scorer import PerformanceScorer

logger = logging.getLogger(__name__)


class PerformanceConfigurationManager:
    """
    Manages performance-driven configuration for event grouping system
    
    Key features:
    - Load best-performing configuration on startup
    - Save performance snapshots during runtime
    - Auto-tune parameters based on performance metrics
    - Maintain audit trail of all configuration changes
    """
    
    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
        self.current_config = None
        self.scorer = PerformanceScorer()
        self.performance_threshold = 70.0  # Minimum acceptable score
        self.service_instance = os.environ.get('HOSTNAME', 'unknown')
        self.last_performance_check = None
        self.config_generation = 1
        
        logger.info(f"PerformanceConfigurationManager initialized for instance: {self.service_instance}")
    
    def get_db_connection(self):
        """Get database connection with timezone configuration"""
        try:
            conn = psycopg2.connect(self.db_connection_string)
            # Set timezone to UTC for this connection
            with conn.cursor() as cur:
                cur.execute("SET timezone = 'UTC'")
                conn.commit()
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def load_startup_configuration(self) -> Dict:
        """
        Load configuration from best performing historical record or conservative defaults
        This is called once at service startup
        """
        try:
            logger.info("Loading startup configuration from performance history...")
            
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get the highest-scoring configuration from last 30 days
            query = """
                SELECT * FROM performance_config_snapshots 
                WHERE snapshot_timestamp > NOW() - INTERVAL '30 days'
                    AND performance_score IS NOT NULL
                    AND performance_score >= %s
                    AND config_source IN ('runtime', 'manual')
                ORDER BY performance_score DESC, snapshot_timestamp DESC 
                LIMIT 1
            """
            
            cur.execute(query, (self.performance_threshold,))
            best_config = cur.fetchone()
            
            if best_config:
                config = self._extract_config_parameters(dict(best_config))
                logger.info(f"Loaded high-performing startup config (score: {best_config['performance_score']:.1f})")
                self.config_generation = best_config.get('config_generation', 1) + 1
            else:
                # No high-performing config found, get the default/latest
                cur.execute("""
                    SELECT * FROM performance_config_snapshots 
                    ORDER BY id DESC 
                    LIMIT 1
                """)
                
                fallback_config = cur.fetchone()
                if fallback_config:
                    config = self._extract_config_parameters(dict(fallback_config))
                    logger.info(f"No high-scoring config found, using latest available config "
                               f"(score: {fallback_config.get('performance_score', 'N/A')})")
                else:
                    config = self._get_conservative_defaults()
                    logger.info("No configuration history found, using conservative defaults")
            
            cur.close()
            conn.close()
            
            # Save startup snapshot
            self.current_config = config
            self._save_startup_snapshot()
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load startup configuration: {e}")
            logger.info("Falling back to conservative defaults")
            config = self._get_conservative_defaults()
            self.current_config = config
            return config
    
    def _extract_config_parameters(self, snapshot_record: Dict) -> Dict:
        """Extract configuration parameters from database record"""
        config_keys = [
            'min_shared_entities', 'entity_overlap_threshold', 'min_title_keywords',
            'title_keyword_bonus', 'max_time_diff_hours', 'allow_same_outlet',
            'min_entity_length', 'max_entity_length', 'entity_noise_threshold'
        ]
        
        return {key: snapshot_record[key] for key in config_keys if key in snapshot_record}
    
    def _get_conservative_defaults(self) -> Dict:
        """Conservative default configuration for safe startup"""
        return {
            'min_shared_entities': 2,           # Reduced from original 4
            'entity_overlap_threshold': 0.250,  # Reduced from original 0.5
            'min_title_keywords': 0,            # Removed requirement
            'title_keyword_bonus': 0.100,      # Small bonus for title matches
            'max_time_diff_hours': 48,         # 48-hour window
            'allow_same_outlet': False,        # Don't group same outlet articles
            'min_entity_length': 3,            # Minimum entity length
            'max_entity_length': 50,           # Maximum entity length
            'entity_noise_threshold': 0.200    # Threshold for filtering noisy entities
        }
    
    def _save_startup_snapshot(self):
        """Save initial configuration snapshot on startup"""
        try:
            snapshot_data = {
                **self.current_config,
                'config_source': 'startup',
                'service_instance': self.service_instance,
                'notes': f'Startup configuration loaded for instance {self.service_instance}',
                'config_generation': self.config_generation
            }
            
            self._save_config_snapshot(snapshot_data)
            logger.info("Startup configuration snapshot saved")
            
        except Exception as e:
            logger.error(f"Failed to save startup snapshot: {e}")
    
    def save_performance_snapshot(self, performance_metrics: Dict) -> int:
        """
        Save current configuration and performance metrics as snapshot
        Returns snapshot ID
        """
        try:
            # Calculate performance scores
            score_data = self.scorer.calculate_overall_score(performance_metrics)
            
            # Build complete snapshot record
            snapshot_data = {
                **self.current_config,
                **performance_metrics,
                'performance_score': score_data['overall_score'],
                'effectiveness_score': score_data['components']['effectiveness'],
                'efficiency_score': score_data['components']['efficiency'],
                'coverage_score': score_data['components']['coverage'],
                'precision_score': score_data['components']['precision'],
                'score_trend': score_data.get('trend', 'unknown'),
                'config_source': 'runtime',
                'service_instance': self.service_instance,
                'config_generation': self.config_generation,
                'notes': f"Runtime performance snapshot - {score_data.get('trend', 'unknown')} trend"
            }
            
            snapshot_id = self._save_config_snapshot(snapshot_data)
            
            # Log performance summary
            logger.info(f"Performance snapshot saved (ID: {snapshot_id}): "
                       f"Score {score_data['overall_score']:.1f}/100, "
                       f"Trend: {score_data.get('trend', 'unknown')}")
            
            # Check if auto-tuning is needed
            if score_data['overall_score'] < self.performance_threshold:
                self._consider_auto_tuning(score_data, snapshot_id)
            
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Failed to save performance snapshot: {e}")
            return -1
    
    def _save_config_snapshot(self, snapshot_data: Dict) -> int:
        """Save configuration snapshot to database"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Insert snapshot record
            insert_query = """
                INSERT INTO performance_config_snapshots (
                    min_shared_entities, entity_overlap_threshold, min_title_keywords,
                    title_keyword_bonus, max_time_diff_hours, allow_same_outlet,
                    min_entity_length, max_entity_length, entity_noise_threshold,
                    articles_processed, events_created, processing_time_ms, entities_extracted_total,
                    event_creation_rate, coverage_percentage, avg_articles_per_event,
                    singleton_events_count, entities_per_article,
                    performance_score, effectiveness_score, efficiency_score, coverage_score, precision_score,
                    config_source, service_instance, notes, score_trend, config_generation
                ) VALUES (
                    %(min_shared_entities)s, %(entity_overlap_threshold)s, %(min_title_keywords)s,
                    %(title_keyword_bonus)s, %(max_time_diff_hours)s, %(allow_same_outlet)s,
                    %(min_entity_length)s, %(max_entity_length)s, %(entity_noise_threshold)s,
                    %(articles_processed)s, %(events_created)s, %(processing_time_ms)s, %(entities_extracted_total)s,
                    %(event_creation_rate)s, %(coverage_percentage)s, %(avg_articles_per_event)s,
                    %(singleton_events_count)s, %(entities_per_article)s,
                    %(performance_score)s, %(effectiveness_score)s, %(efficiency_score)s, %(coverage_score)s, %(precision_score)s,
                    %(config_source)s, %(service_instance)s, %(notes)s, %(score_trend)s, %(config_generation)s
                ) RETURNING id
            """
            
            # Ensure all required fields have default values
            snapshot_data.setdefault('articles_processed', 0)
            snapshot_data.setdefault('events_created', 0)
            snapshot_data.setdefault('processing_time_ms', 0)
            snapshot_data.setdefault('entities_extracted_total', 0)
            snapshot_data.setdefault('performance_score', 0.0)
            
            cur.execute(insert_query, snapshot_data)
            snapshot_id = cur.fetchone()[0]
            
            conn.commit()
            cur.close()
            conn.close()
            
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Failed to save configuration snapshot: {e}")
            raise
    
    def _consider_auto_tuning(self, score_data: Dict, snapshot_id: int):
        """Consider automatic configuration adjustments based on performance"""
        try:
            # Only auto-tune if performance is significantly below threshold
            if score_data['overall_score'] >= self.performance_threshold - 10:
                logger.info(f"Performance {score_data['overall_score']:.1f} below threshold but within tolerance")
                return
            
            logger.warning(f"Performance {score_data['overall_score']:.1f} significantly below threshold "
                          f"{self.performance_threshold}, considering auto-tune")
            
            # Analyze which component is performing worst
            components = score_data['components']
            worst_component = min(components, key=components.get)
            worst_score = components[worst_component]
            
            logger.info(f"Worst performing component: {worst_component} ({worst_score:.1f})")
            
            # Generate suggested adjustments
            adjustments = self._generate_auto_tune_adjustments(worst_component, score_data)
            
            if adjustments:
                logger.info(f"Auto-tune suggestions for {worst_component}: {adjustments}")
                
                # For now, just log the suggestions
                # In a more advanced implementation, we could apply them automatically
                # or add them to a review queue
                self._log_auto_tune_suggestion(snapshot_id, worst_component, adjustments)
            
        except Exception as e:
            logger.error(f"Error in auto-tuning consideration: {e}")
    
    def _generate_auto_tune_adjustments(self, worst_component: str, score_data: Dict) -> Dict:
        """Generate configuration adjustment suggestions based on worst performing component"""
        adjustments = {}
        
        try:
            if worst_component == 'effectiveness':
                # Low event creation - relax matching requirements
                if score_data['score_details'].get('event_creation_rate', 0) < 0.15:
                    if self.current_config['min_shared_entities'] > 1:
                        adjustments['min_shared_entities'] = max(1, self.current_config['min_shared_entities'] - 1)
                    
                    if self.current_config['entity_overlap_threshold'] > 0.150:
                        adjustments['entity_overlap_threshold'] = max(0.150, self.current_config['entity_overlap_threshold'] - 0.050)
                    
                    if self.current_config['max_time_diff_hours'] < 72:
                        adjustments['max_time_diff_hours'] = min(72, self.current_config['max_time_diff_hours'] + 12)
            
            elif worst_component == 'efficiency':
                # Slow processing - optimize for speed
                if self.current_config['max_entity_length'] > 30:
                    adjustments['max_entity_length'] = 30  # Shorter entities for faster processing
                
                if self.current_config['entity_noise_threshold'] < 0.300:
                    adjustments['entity_noise_threshold'] = 0.300  # Filter more aggressively
            
            elif worst_component == 'coverage':
                # Low coverage - make grouping more inclusive
                if self.current_config['min_shared_entities'] > 1:
                    adjustments['min_shared_entities'] = self.current_config['min_shared_entities'] - 1
                
                if self.current_config['entity_overlap_threshold'] > 0.200:
                    adjustments['entity_overlap_threshold'] = max(0.200, self.current_config['entity_overlap_threshold'] - 0.030)
            
            elif worst_component == 'precision':
                # Poor precision - tighten matching requirements
                avg_articles = score_data['score_details'].get('avg_articles_per_event', 2.0)
                if avg_articles < 1.8:
                    # Too many singletons - relax to allow more grouping
                    adjustments = self._generate_auto_tune_adjustments('coverage', score_data)
                elif avg_articles > 4.5:
                    # Groups too large - tighten requirements
                    if self.current_config['min_shared_entities'] < 3:
                        adjustments['min_shared_entities'] = self.current_config['min_shared_entities'] + 1
                    
                    if self.current_config['entity_overlap_threshold'] < 0.350:
                        adjustments['entity_overlap_threshold'] = min(0.350, self.current_config['entity_overlap_threshold'] + 0.050)
            
            return adjustments
            
        except Exception as e:
            logger.error(f"Error generating auto-tune adjustments: {e}")
            return {}
    
    def _log_auto_tune_suggestion(self, snapshot_id: int, component: str, adjustments: Dict):
        """Log auto-tune suggestions for review"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            for param, new_value in adjustments.items():
                old_value = self.current_config.get(param)
                
                cur.execute("""
                    INSERT INTO config_change_events (
                        parameter_name, old_value, new_value, change_reason,
                        previous_score, target_improvement, config_snapshot_id, triggered_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    param, str(old_value), str(new_value), 
                    f'auto_tune_suggestion_{component}',
                    None, f'improve_{component}', 
                    snapshot_id, f'auto_tuner_{self.service_instance}'
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log auto-tune suggestion: {e}")
    
    def get_current_config(self) -> Dict:
        """Get current configuration"""
        if self.current_config is None:
            self.current_config = self.load_startup_configuration()
        return self.current_config.copy()
    
    def update_configuration(self, updates: Dict, reason: str = 'manual_update') -> bool:
        """Update configuration with new values"""
        try:
            if not updates:
                return True
            
            # Validate updates
            valid_params = set(self._get_conservative_defaults().keys())
            invalid_params = set(updates.keys()) - valid_params
            
            if invalid_params:
                logger.error(f"Invalid configuration parameters: {invalid_params}")
                return False
            
            # Apply updates
            old_config = self.current_config.copy()
            self.current_config.update(updates)
            self.config_generation += 1
            
            # Log changes
            for param, new_value in updates.items():
                old_value = old_config.get(param)
                logger.info(f"Config update: {param} {old_value} -> {new_value} ({reason})")
            
            # Save updated configuration snapshot
            snapshot_data = {
                **self.current_config,
                'config_source': 'manual' if reason.startswith('manual') else 'auto_tune',
                'service_instance': self.service_instance,
                'config_generation': self.config_generation,
                'notes': f'Configuration updated: {reason}'
            }
            
            self._save_config_snapshot(snapshot_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
    
    def get_performance_summary(self, hours: int = 24) -> Dict:
        """Get performance summary for the last N hours"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cur.execute("""
                SELECT 
                    COUNT(*) as snapshot_count,
                    AVG(performance_score) as avg_score,
                    MAX(performance_score) as max_score,
                    MIN(performance_score) as min_score,
                    AVG(event_creation_rate) as avg_event_rate,
                    AVG(coverage_percentage) as avg_coverage,
                    MAX(config_generation) as latest_generation
                FROM performance_config_snapshots
                WHERE snapshot_timestamp > NOW() - INTERVAL '%s hours'
                    AND service_instance = %s
                    AND performance_score IS NOT NULL
            """, (hours, self.service_instance))
            
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result and result['snapshot_count'] > 0:
                return dict(result)
            else:
                return {'snapshot_count': 0, 'message': 'No performance data available'}
                
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {'error': str(e)}


# Helper functions for testing
def test_config_manager():
    """Test the configuration manager"""
    db_url = os.environ.get('DATABASE_URL', 
        'postgresql://appuser:newsengine2024@localhost:5432/newsdb')
    
    try:
        manager = PerformanceConfigurationManager(db_url)
        config = manager.load_startup_configuration()
        
        print("Loaded configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        # Test performance snapshot
        test_metrics = {
            'articles_processed': 50,
            'events_created': 12,
            'event_creation_rate': 0.24,
            'coverage_percentage': 48.0,
            'avg_articles_per_event': 2.1,
            'singleton_events_count': 3,
            'processing_time_ms': 4500,
            'entities_extracted_total': 150,
            'entities_per_article': 3.0
        }
        
        snapshot_id = manager.save_performance_snapshot(test_metrics)
        print(f"Test performance snapshot saved with ID: {snapshot_id}")
        
        return manager
        
    except Exception as e:
        print(f"Test failed: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_config_manager()