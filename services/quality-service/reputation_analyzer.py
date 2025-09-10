#!/usr/bin/env python3
"""
Reputation Score Analyzer
Implements comprehensive journalism awards and professional recognition scoring
Based on QUALITY-SCORING-PROPOSAL.md Agency Reputation Metrics
"""

import psycopg2
import psycopg2.extras
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import os

logger = logging.getLogger(__name__)

@dataclass
class ReputationMetrics:
    """Container for reputation score components"""
    outlet_name: str
    total_awards_score: int
    professional_standing_score: int  
    credibility_score: int
    final_reputation_score: float
    
    # Award details
    pulitzer_awards: int
    murrow_awards: int
    peabody_awards: int
    emmy_awards: int
    specialized_awards: int
    
    # Professional indicators
    press_freedom_ranking: Optional[int]
    fact_checking_standards: bool
    editorial_independence_rating: Optional[float]

class ReputationAnalyzer:
    """Comprehensive reputation analyzer for news organizations"""
    
    def __init__(self):
        self.db_connection = None
        
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
                
            self.db_connection = psycopg2.connect(database_url)
            logger.info("Connected to reputation metrics database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def calculate_reputation_score(self, outlet: str) -> float:
        """
        Calculate reputation score for news outlet using detailed metrics table
        Based on QUALITY-SCORING-PROPOSAL.md algorithm
        
        Args:
            outlet: Name of news outlet
            
        Returns:
            Reputation score (0-100)
        """
        
        if not self.db_connection:
            self.connect_to_database()
        
        # Get detailed outlet data from news_agency_reputation_metrics table
        outlet_metrics = self.get_news_agency_metrics(outlet)
        
        if not outlet_metrics:
            # Fallback to basic outlet_authority table if no detailed metrics exist
            return self.get_basic_authority_score(outlet)
        
        # Awards & Recognition (0-60 points)
        awards_score = self._calculate_awards_score(outlet_metrics)
        
        # Professional Standing (0-25 points)
        professional_score = self._calculate_professional_standing(outlet_metrics)
        
        # Credibility & Ethics (0-15 points)
        credibility_score = self._calculate_credibility_score(outlet_metrics)
        
        total_score = min(100, awards_score + professional_score + credibility_score)
        
        # Update the computed scores in database
        self._update_reputation_metrics_scores(outlet_metrics['id'], {
            'total_awards_score': awards_score,
            'professional_standing_score': professional_score,
            'credibility_score': credibility_score,
            'final_reputation_score': total_score
        })
        
        # Update or insert into outlet_reputation_scores table for fast lookup
        self._update_outlet_reputation_cache(outlet, outlet_metrics, total_score)
        
        logger.info(f"Reputation score for {outlet}: {total_score} (Awards: {awards_score}, Professional: {professional_score}, Credibility: {credibility_score})")
        
        return total_score
    
    def _calculate_awards_score(self, metrics: Dict) -> int:
        """Calculate awards and recognition score (0-60 points)"""
        
        # Major Awards (10 points each, max 40)
        major_awards_score = min(40, (
            (metrics.get('pulitzer_awards', 0) * 10) +
            (metrics.get('murrow_awards', 0) * 10) +
            (metrics.get('peabody_awards', 0) * 10) +
            (metrics.get('emmy_awards', 0) * 10)
        ))
        
        # Regional/Specialized Awards (5 points each for major, 2 for others, max 20)
        specialized_awards_score = min(20, (
            (metrics.get('george_polk_awards', 0) * 5) +
            (metrics.get('dupont_awards', 0) * 5) +
            (metrics.get('spj_awards', 0) * 2) +
            (metrics.get('other_specialized_awards', 0) * 2)
        ))
        
        return major_awards_score + specialized_awards_score
    
    def _calculate_professional_standing(self, metrics: Dict) -> int:
        """Calculate professional standing score (0-25 points)"""
        
        score = 0
        
        # Press Freedom Ranking (0-10 points)
        press_freedom_points = self._calculate_press_freedom_score(metrics.get('press_freedom_ranking'))
        score += press_freedom_points
        
        # Industry Memberships (2 points each, max 6)
        memberships = metrics.get('industry_memberships', []) or []
        membership_points = min(6, len(memberships) * 2)
        score += membership_points
        
        # Editorial Independence Rating (0-10 scale, max 4 points)
        independence_rating = metrics.get('editorial_independence_rating', 0) or 0
        independence_points = min(4, int(float(independence_rating) * 0.4))  # Convert 0-10 to 0-4
        score += independence_points
        
        # Fact-Checking Standards (5 points)
        fact_check_points = 5 if metrics.get('fact_checking_standards') else 0
        score += fact_check_points
        
        return min(25, score)
    
    def _calculate_credibility_score(self, metrics: Dict) -> int:
        """Calculate credibility and ethics score (0-15 points)"""
        
        # Each credibility factor worth 3 points
        credibility_factors = [
            metrics.get('correction_policy_exists', False),
            metrics.get('retraction_transparency', False),
            metrics.get('ownership_transparency', False),
            metrics.get('funding_disclosure', False),
            metrics.get('ethics_code_public', False)
        ]
        
        return sum(3 for factor in credibility_factors if factor)
    
    def _calculate_press_freedom_score(self, ranking: Optional[int]) -> int:
        """Convert press freedom ranking to score points (0-10)"""
        if not ranking:
            return 5  # Default/unknown
        elif ranking <= 20:
            return 10  # Excellent
        elif ranking <= 50:
            return 8   # Good  
        elif ranking <= 100:
            return 6   # Fair
        elif ranking <= 150:
            return 4   # Poor
        else:
            return 2   # Very poor
    
    def get_news_agency_metrics(self, outlet: str) -> Optional[Dict]:
        """Fetch detailed reputation metrics from database"""
        try:
            with self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                query = """
                SELECT * FROM news_agency_reputation_metrics 
                WHERE LOWER(outlet_name) = LOWER(%s)
                """
                cursor.execute(query, [outlet])
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error fetching news agency metrics for {outlet}: {e}")
            return None
    
    def get_basic_authority_score(self, outlet: str) -> float:
        """Fallback to basic outlet authority if detailed metrics don't exist"""
        try:
            with self.db_connection.cursor() as cursor:
                query = """
                SELECT authority FROM outlet_authority 
                WHERE LOWER(outlet) = LOWER(%s)
                """
                cursor.execute(query, [outlet])
                result = cursor.fetchone()
                
                if result:
                    # Convert 0-40 authority scale to 0-100 reputation scale
                    return min(100, result[0] * 2.5)
                else:
                    # Default score for unknown outlets
                    return 30.0
                    
        except Exception as e:
            logger.error(f"Error fetching basic authority for {outlet}: {e}")
            return 30.0
    
    def _update_reputation_metrics_scores(self, metrics_id: int, scores: Dict):
        """Update computed scores in news_agency_reputation_metrics table"""
        try:
            with self.db_connection.cursor() as cursor:
                query = """
                UPDATE news_agency_reputation_metrics
                SET total_awards_score = %s,
                    professional_standing_score = %s,
                    credibility_score = %s,
                    final_reputation_score = %s,
                    updated_at = NOW()
                WHERE id = %s
                """
                cursor.execute(query, [
                    scores['total_awards_score'],
                    scores['professional_standing_score'],
                    scores['credibility_score'],
                    scores['final_reputation_score'],
                    metrics_id
                ])
                self.db_connection.commit()
        except Exception as e:
            logger.error(f"Error updating reputation metrics scores: {e}")
            self.db_connection.rollback()
    
    def _update_outlet_reputation_cache(self, outlet: str, metrics: Dict, reputation_score: float):
        """Update or insert outlet reputation cache for fast lookup"""
        try:
            with self.db_connection.cursor() as cursor:
                # Determine press freedom tier
                press_freedom_tier = self._get_press_freedom_tier(metrics.get('press_freedom_ranking'))
                
                # Calculate total major awards
                total_major_awards = (
                    (metrics.get('pulitzer_awards', 0)) +
                    (metrics.get('murrow_awards', 0)) +
                    (metrics.get('peabody_awards', 0)) +
                    (metrics.get('emmy_awards', 0))
                )
                
                query = """
                INSERT INTO outlet_reputation_scores 
                (outlet, reputation_score, reputation_metrics_id, total_major_awards, 
                 has_fact_checking, press_freedom_tier, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (outlet) 
                DO UPDATE SET
                    reputation_score = EXCLUDED.reputation_score,
                    reputation_metrics_id = EXCLUDED.reputation_metrics_id,
                    total_major_awards = EXCLUDED.total_major_awards,
                    has_fact_checking = EXCLUDED.has_fact_checking,
                    press_freedom_tier = EXCLUDED.press_freedom_tier,
                    last_updated = NOW()
                """
                
                cursor.execute(query, [
                    outlet,
                    reputation_score,
                    metrics['id'],
                    total_major_awards,
                    metrics.get('fact_checking_standards', False),
                    press_freedom_tier
                ])
                self.db_connection.commit()
                
        except Exception as e:
            logger.error(f"Error updating outlet reputation cache: {e}")
            self.db_connection.rollback()
    
    def _get_press_freedom_tier(self, ranking: Optional[int]) -> str:
        """Convert press freedom ranking to tier"""
        if not ranking:
            return 'unknown'
        elif ranking <= 20:
            return 'excellent'
        elif ranking <= 50:
            return 'good'
        elif ranking <= 100:
            return 'fair'
        else:
            return 'poor'
    
    def get_outlet_reputation(self, outlet: str) -> float:
        """
        Get outlet reputation score with caching
        First checks cache, then calculates if needed
        """
        # Check cache first
        cached_score = self._get_cached_reputation_score(outlet)
        if cached_score is not None:
            return cached_score
            
        # Calculate and cache if not found
        return self.calculate_reputation_score(outlet)
    
    def _get_cached_reputation_score(self, outlet: str) -> Optional[float]:
        """Get cached reputation score from outlet_reputation_scores table"""
        try:
            with self.db_connection.cursor() as cursor:
                query = """
                SELECT reputation_score FROM outlet_reputation_scores 
                WHERE LOWER(outlet) = LOWER(%s)
                """
                cursor.execute(query, [outlet])
                result = cursor.fetchone()
                return float(result[0]) if result else None
        except Exception as e:
            logger.error(f"Error fetching cached reputation for {outlet}: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()
            logger.info("Closed reputation analyzer database connection")

# Factory function for easy integration
def get_reputation_analyzer() -> ReputationAnalyzer:
    """Create and return configured reputation analyzer instance"""
    analyzer = ReputationAnalyzer()
    analyzer.connect_to_database()
    return analyzer