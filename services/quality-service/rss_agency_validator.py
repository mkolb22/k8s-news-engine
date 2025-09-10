#!/usr/bin/env python3
"""
RSS Feed to News Agency Validator

Ensures RSS feeds have corresponding news agency reputation scores.
Provides validation, logging, and fallback mechanisms for data integrity.
"""

import psycopg2
import psycopg2.extras
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class RSSFeedValidation:
    """Container for RSS feed validation results"""
    rss_feed_id: int
    outlet_name: str
    url: str
    has_agency_mapping: bool
    agency_name: Optional[str]
    reputation_score: Optional[float]
    validation_status: str
    recommendations: List[str]

class RSSAgencyValidator:
    """Validates RSS feeds have corresponding news agency reputation scores"""
    
    def __init__(self):
        self.db_connection = None
        
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
                
            self.db_connection = psycopg2.connect(database_url)
            logger.info("Connected to RSS agency validation database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def validate_all_rss_feeds(self) -> List[RSSFeedValidation]:
        """
        Validate all RSS feeds have corresponding news agency reputation scores
        
        Returns:
            List of RSS feed validation results
        """
        
        if not self.db_connection:
            self.connect_to_database()
        
        validation_results = []
        
        try:
            with self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get all RSS feeds with their agency mappings
                query = """
                SELECT 
                    rf.id,
                    rf.outlet_name,
                    rf.url,
                    rf.active,
                    rf.news_agency_id,
                    narm.outlet_name as agency_name,
                    narm.final_reputation_score
                FROM rss_feeds rf
                LEFT JOIN news_agency_reputation_metrics narm ON rf.news_agency_id = narm.id
                WHERE rf.active = true
                ORDER BY rf.outlet
                """
                
                cursor.execute(query)
                rss_feeds = cursor.fetchall()
                
                for feed in rss_feeds:
                    validation = self._validate_single_feed(feed)
                    validation_results.append(validation)
                    
                    # Log issues
                    if not validation.has_agency_mapping:
                        logger.warning(f"RSS feed '{validation.outlet_name}' ({validation.url}) has no news agency mapping")
                    elif validation.reputation_score is None or validation.reputation_score == 0:
                        logger.info(f"RSS feed '{validation.outlet_name}' mapped to '{validation.agency_name}' but no reputation score computed")
                
        except Exception as e:
            logger.error(f"Error validating RSS feeds: {e}")
            
        return validation_results
    
    def _validate_single_feed(self, feed: Dict) -> RSSFeedValidation:
        """Validate a single RSS feed"""
        
        has_mapping = feed['news_agency_id'] is not None
        agency_name = feed['agency_name']
        reputation_score = float(feed['final_reputation_score']) if feed['final_reputation_score'] else None
        
        # Determine validation status
        if not has_mapping:
            status = "NO_AGENCY_MAPPING"
            recommendations = [
                "Add mapping in map_outlet_to_agency_name() function",
                f"Consider adding '{feed['outlet_name']}' to news_agency_reputation_metrics table",
                "RSS feed will use fallback outlet_authority scoring"
            ]
        elif reputation_score is None or reputation_score == 0:
            status = "AGENCY_MAPPED_NO_SCORE" 
            recommendations = [
                f"Populate reputation data for '{agency_name}' in news_agency_reputation_metrics",
                "Run reputation analyzer to compute scores",
                "Verify journalism awards and professional metrics data"
            ]
        else:
            status = "VALID"
            recommendations = []
            
        return RSSFeedValidation(
            rss_feed_id=feed['id'],
            outlet_name=feed['outlet_name'],
            url=feed['url'],
            has_agency_mapping=has_mapping,
            agency_name=agency_name,
            reputation_score=reputation_score,
            validation_status=status,
            recommendations=recommendations
        )
    
    def get_unmapped_rss_feeds(self) -> List[RSSFeedValidation]:
        """Get RSS feeds that don't have news agency mappings"""
        all_validations = self.validate_all_rss_feeds()
        return [v for v in all_validations if not v.has_agency_mapping]
    
    def get_mapped_but_unscored_feeds(self) -> List[RSSFeedValidation]:
        """Get RSS feeds mapped to agencies but without reputation scores"""
        all_validations = self.validate_all_rss_feeds()
        return [v for v in all_validations 
                if v.has_agency_mapping and (v.reputation_score is None or v.reputation_score == 0)]
    
    def get_validation_summary(self) -> Dict:
        """Get summary statistics of RSS feed validation"""
        
        validations = self.validate_all_rss_feeds()
        
        total_feeds = len(validations)
        mapped_feeds = len([v for v in validations if v.has_agency_mapping])
        scored_feeds = len([v for v in validations if v.reputation_score and v.reputation_score > 0])
        unmapped_feeds = total_feeds - mapped_feeds
        mapped_unscored = mapped_feeds - scored_feeds
        
        return {
            'total_rss_feeds': total_feeds,
            'mapped_to_agencies': mapped_feeds,
            'with_reputation_scores': scored_feeds,
            'unmapped_feeds': unmapped_feeds,
            'mapped_but_unscored': mapped_unscored,
            'mapping_percentage': round((mapped_feeds / total_feeds) * 100, 2) if total_feeds > 0 else 0,
            'scoring_percentage': round((scored_feeds / total_feeds) * 100, 2) if total_feeds > 0 else 0
        }
    
    def suggest_agency_mappings(self) -> List[Tuple[str, str]]:
        """
        Suggest potential news agency mappings for unmapped RSS feeds
        Based on outlet name similarity and common patterns
        """
        
        unmapped = self.get_unmapped_rss_feeds()
        existing_agencies = self._get_existing_agencies()
        
        suggestions = []
        
        for feed in unmapped:
            outlet = feed.outlet_name.lower()
            
            # Check for partial matches with existing agencies
            for agency in existing_agencies:
                agency_lower = agency.lower()
                
                # Direct substring match
                if any(word in outlet for word in agency_lower.split() if len(word) > 3):
                    suggestions.append((feed.outlet_name, agency))
                    break
                
                # Common abbreviations and variations
                elif self._check_outlet_variations(outlet, agency_lower):
                    suggestions.append((feed.outlet_name, agency))
                    break
        
        return suggestions
    
    def _get_existing_agencies(self) -> List[str]:
        """Get list of existing news agency names"""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT outlet_name FROM news_agency_reputation_metrics ORDER BY outlet_name")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching existing agencies: {e}")
            return []
    
    def _check_outlet_variations(self, outlet: str, agency: str) -> bool:
        """Check for common outlet name variations"""
        
        # Common patterns for news outlets
        patterns = {
            'bbc': ['bbc news', 'bbc world', 'bbc'],
            'cnn': ['cnn', 'cnn top stories', 'cnn.com'],
            'reuters': ['reuters', 'reuters top news', 'reuters.com'],
            'associated press': ['ap', 'ap news', 'associated press'],
            'the new york times': ['nyt', 'nytimes', 'new york times'],
            'npr': ['npr', 'npr news', 'national public radio'],
            'the washington post': ['washington post', 'washpost'],
            'the guardian': ['guardian', 'theguardian.com'],
            'fox news': ['fox', 'fox news', 'foxnews.com']
        }
        
        agency_key = agency.replace('the ', '').strip()
        
        if agency_key in patterns:
            return any(pattern in outlet for pattern in patterns[agency_key])
        
        return False
    
    def check_feed_has_agency_score(self, outlet_name: str) -> Tuple[bool, Optional[float], str]:
        """
        Application-level check for a specific RSS feed outlet
        
        Args:
            outlet_name: RSS feed outlet name
            
        Returns:
            Tuple of (has_score, reputation_score, status_message)
        """
        
        if not self.db_connection:
            self.connect_to_database()
        
        try:
            with self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Check if RSS feed has agency mapping and score
                query = """
                SELECT 
                    rf.outlet_name,
                    rf.news_agency_id,
                    narm.outlet_name as agency_name,
                    narm.final_reputation_score
                FROM rss_feeds rf
                LEFT JOIN news_agency_reputation_metrics narm ON rf.news_agency_id = narm.id
                WHERE LOWER(rf.outlet_name) = LOWER(%s) AND rf.active = true
                """
                
                cursor.execute(query, [outlet_name])
                result = cursor.fetchone()
                
                if not result:
                    return False, None, f"RSS feed '{outlet_name}' not found or inactive"
                
                if not result['news_agency_id']:
                    return False, None, f"RSS feed '{outlet_name}' has no news agency mapping"
                
                reputation_score = float(result['final_reputation_score']) if result['final_reputation_score'] else 0
                
                if reputation_score == 0:
                    return False, 0.0, f"RSS feed '{outlet_name}' mapped to '{result['agency_name']}' but no reputation score computed"
                
                return True, reputation_score, f"RSS feed '{outlet_name}' has valid reputation score: {reputation_score}"
                
        except Exception as e:
            logger.error(f"Error checking feed agency score for '{outlet_name}': {e}")
            return False, None, f"Database error checking '{outlet_name}'"
    
    def close(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()
            logger.info("Closed RSS agency validator database connection")

# Convenience functions for integration
def validate_rss_feed_mapping(outlet_name: str) -> Tuple[bool, Optional[float], str]:
    """
    Quick validation check for RSS feed to agency mapping
    
    Args:
        outlet_name: RSS feed outlet name
        
    Returns:
        Tuple of (has_valid_score, reputation_score, status_message)
    """
    validator = RSSAgencyValidator()
    try:
        validator.connect_to_database()
        return validator.check_feed_has_agency_score(outlet_name)
    finally:
        validator.close()

def get_rss_validation_report() -> Dict:
    """
    Generate comprehensive RSS feed validation report
    
    Returns:
        Dictionary with validation summary and recommendations
    """
    validator = RSSAgencyValidator()
    try:
        validator.connect_to_database()
        summary = validator.get_validation_summary()
        unmapped = validator.get_unmapped_rss_feeds()
        suggestions = validator.suggest_agency_mappings()
        
        return {
            'summary': summary,
            'unmapped_feeds': [
                {
                    'outlet': feed.outlet_name,
                    'url': feed.url,
                    'recommendations': feed.recommendations
                } for feed in unmapped
            ],
            'mapping_suggestions': [
                {'rss_outlet': rss_outlet, 'suggested_agency': agency}
                for rss_outlet, agency in suggestions
            ]
        }
    finally:
        validator.close()