#!/usr/bin/env python3
"""
Performance Scorer for Event Grouping System
Calculates overall performance scores based on effectiveness, efficiency, coverage, and precision
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PerformanceScorer:
    """Calculates comprehensive performance scores for event grouping system"""
    
    def __init__(self):
        # Component weights (must sum to 1.0)
        self.weights = {
            'effectiveness': 0.35,  # Event creation success
            'efficiency': 0.25,     # Processing speed
            'coverage': 0.25,       # Article grouping rate
            'precision': 0.15       # Grouping accuracy
        }
        
        # Performance targets
        self.targets = {
            'event_rate_target': 0.30,         # 30% of articles should form events
            'coverage_target': 60.0,           # 60% coverage ideal
            'processing_time_target': 100,     # 100ms per article
            'articles_per_event_min': 2.0,     # Minimum articles per event
            'articles_per_event_max': 4.0,     # Maximum articles per event (optimal)
            'articles_per_event_limit': 6.0    # Upper acceptable limit
        }
        
        logger.info(f"PerformanceScorer initialized with weights: {self.weights}")
    
    def calculate_effectiveness_score(self, metrics: Dict) -> float:
        """
        Event creation effectiveness (35% of total score)
        Measures how well the system creates meaningful events
        """
        try:
            event_rate = metrics.get('event_creation_rate', 0.0)
            events_created = metrics.get('events_created', 0)
            articles_processed = metrics.get('articles_processed', 1)
            
            # Base score from event creation rate
            target_rate = self.targets['event_rate_target']
            if event_rate >= target_rate:
                rate_score = 100
            else:
                # Linear scaling up to target
                rate_score = (event_rate / target_rate) * 100
            
            # Bonus for creating multiple events (diversity)
            if events_created > 0:
                # Bonus based on number of events relative to articles
                diversity_ratio = events_created / articles_processed
                diversity_bonus = min(15, diversity_ratio * 50)  # Max 15 points
            else:
                diversity_bonus = 0
            
            # Penalty for too many singleton events
            singleton_count = metrics.get('singleton_events_count', 0)
            if events_created > 0:
                singleton_ratio = singleton_count / events_created
                singleton_penalty = singleton_ratio * 25  # Max 25 point penalty
            else:
                singleton_penalty = 0
            
            score = max(0, rate_score + diversity_bonus - singleton_penalty)
            score = min(100, score)
            
            logger.debug(f"Effectiveness: rate={rate_score:.1f}, diversity={diversity_bonus:.1f}, "
                        f"singleton_penalty={singleton_penalty:.1f}, final={score:.1f}")
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating effectiveness score: {e}")
            return 0.0
    
    def calculate_efficiency_score(self, metrics: Dict) -> float:
        """
        Processing efficiency (25% of total score)
        Measures processing speed and resource utilization
        """
        try:
            processing_time = metrics.get('processing_time_ms', 0)
            articles_processed = metrics.get('articles_processed', 1)
            
            if processing_time <= 0 or articles_processed <= 0:
                return 50.0  # Neutral score if no data
            
            # Calculate time per article
            time_per_article = processing_time / articles_processed
            target_time = self.targets['processing_time_target']
            
            if time_per_article <= target_time:
                score = 100
            elif time_per_article <= target_time * 2:
                # Linear decline from 100 to 50 between target and 2x target
                excess_ratio = (time_per_article - target_time) / target_time
                score = 100 - (excess_ratio * 50)
            else:
                # Steep decline after 2x target
                excess_ratio = (time_per_article - target_time * 2) / target_time
                score = max(10, 50 - (excess_ratio * 20))
            
            logger.debug(f"Efficiency: {time_per_article:.1f}ms/article (target: {target_time}ms), score={score:.1f}")
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"Error calculating efficiency score: {e}")
            return 50.0
    
    def calculate_coverage_score(self, metrics: Dict) -> float:
        """
        Article coverage in events (25% of total score)
        Measures what percentage of articles are successfully grouped
        """
        try:
            coverage_pct = metrics.get('coverage_percentage', 0.0)
            target_coverage = self.targets['coverage_target']
            
            if coverage_pct >= target_coverage:
                score = 100
            elif coverage_pct >= target_coverage * 0.67:  # 40% if target is 60%
                # Linear scale from 70 to 100 between 2/3 target and target
                progress = (coverage_pct - target_coverage * 0.67) / (target_coverage * 0.33)
                score = 70 + (progress * 30)
            else:
                # Linear scale from 0 to 70 up to 2/3 target
                score = (coverage_pct / (target_coverage * 0.67)) * 70
            
            score = min(100, max(0, score))
            
            logger.debug(f"Coverage: {coverage_pct:.1f}% (target: {target_coverage}%), score={score:.1f}")
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating coverage score: {e}")
            return 0.0
    
    def calculate_precision_score(self, metrics: Dict, validation_data: Dict = None) -> float:
        """
        Event grouping precision (15% of total score)
        Measures quality of article groupings within events
        """
        try:
            avg_articles = metrics.get('avg_articles_per_event', 1.0)
            
            # Optimal range scoring
            min_optimal = self.targets['articles_per_event_min']
            max_optimal = self.targets['articles_per_event_max']
            max_acceptable = self.targets['articles_per_event_limit']
            
            if min_optimal <= avg_articles <= max_optimal:
                # Perfect range
                base_score = 100
            elif avg_articles < min_optimal:
                # Too small (likely singleton events or poor grouping)
                if avg_articles >= 1.5:
                    base_score = 60 + ((avg_articles - 1.5) / (min_optimal - 1.5)) * 40
                else:
                    base_score = max(20, avg_articles * 40)  # Very poor grouping
            elif avg_articles <= max_acceptable:
                # Acceptable but not optimal (groups may be too large)
                excess = avg_articles - max_optimal
                max_excess = max_acceptable - max_optimal
                base_score = 100 - (excess / max_excess) * 30  # Lose up to 30 points
            else:
                # Too large (likely over-grouping different events)
                base_score = max(10, 70 - (avg_articles - max_acceptable) * 10)
            
            # Factor in manual validation if available
            if validation_data and 'precision_rating' in validation_data:
                manual_score = validation_data['precision_rating'] * 100
                # Weight: 70% algorithmic, 30% manual validation
                base_score = (base_score * 0.7) + (manual_score * 0.3)
            
            score = min(100, max(0, base_score))
            
            logger.debug(f"Precision: {avg_articles:.1f} articles/event "
                        f"(optimal: {min_optimal}-{max_optimal}), score={score:.1f}")
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating precision score: {e}")
            return 50.0
    
    def calculate_overall_score(self, metrics: Dict, validation_data: Dict = None) -> Dict:
        """
        Calculate overall performance score with detailed breakdown
        Returns dict with overall score and component scores
        """
        try:
            # Calculate component scores
            components = {
                'effectiveness': self.calculate_effectiveness_score(metrics),
                'efficiency': self.calculate_efficiency_score(metrics),
                'coverage': self.calculate_coverage_score(metrics),
                'precision': self.calculate_precision_score(metrics, validation_data)
            }
            
            # Calculate weighted overall score
            overall = sum(components[key] * self.weights[key] for key in components)
            overall = round(overall, 2)
            
            # Determine performance trend (requires historical data)
            trend = self._determine_trend(overall, metrics.get('previous_score'))
            
            result = {
                'overall_score': overall,
                'components': components,
                'weights': self.weights,
                'trend': trend,
                'targets': self.targets,
                'score_details': {
                    'event_creation_rate': metrics.get('event_creation_rate', 0),
                    'coverage_percentage': metrics.get('coverage_percentage', 0),
                    'avg_processing_time_ms': (
                        metrics.get('processing_time_ms', 0) / 
                        max(1, metrics.get('articles_processed', 1))
                    ),
                    'avg_articles_per_event': metrics.get('avg_articles_per_event', 0)
                }
            }
            
            logger.info(f"Performance Score: {overall:.1f}/100 "
                       f"[E:{components['effectiveness']:.1f} "
                       f"Ef:{components['efficiency']:.1f} "
                       f"C:{components['coverage']:.1f} "
                       f"P:{components['precision']:.1f}]")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating overall performance score: {e}")
            return {
                'overall_score': 0.0,
                'components': {k: 0.0 for k in self.weights.keys()},
                'weights': self.weights,
                'trend': 'unknown',
                'error': str(e)
            }
    
    def _determine_trend(self, current_score: float, previous_score: Optional[float]) -> str:
        """Determine if performance is improving, declining, or stable"""
        if previous_score is None:
            return 'initial'
        
        diff = current_score - previous_score
        
        if abs(diff) < 2.0:
            return 'stable'
        elif diff > 0:
            return 'improving'
        else:
            return 'declining'
    
    def get_score_interpretation(self, overall_score: float) -> Dict:
        """Get human-readable interpretation of performance score"""
        if overall_score >= 90:
            return {
                'grade': 'A+',
                'interpretation': 'Excellent performance - system operating at optimal levels',
                'action': 'maintain current configuration'
            }
        elif overall_score >= 80:
            return {
                'grade': 'A',
                'interpretation': 'Very good performance - minor optimizations possible',
                'action': 'fine-tune parameters'
            }
        elif overall_score >= 70:
            return {
                'grade': 'B',
                'interpretation': 'Good performance - some improvement opportunities',
                'action': 'analyze component scores for optimization'
            }
        elif overall_score >= 60:
            return {
                'grade': 'C',
                'interpretation': 'Acceptable performance - significant room for improvement',
                'action': 'review configuration and consider adjustments'
            }
        elif overall_score >= 50:
            return {
                'grade': 'D',
                'interpretation': 'Below acceptable performance - needs attention',
                'action': 'investigate issues and adjust configuration'
            }
        else:
            return {
                'grade': 'F',
                'interpretation': 'Poor performance - immediate action required',
                'action': 'reset to conservative defaults and debug system'
            }


# Helper function for testing
def test_performance_scorer():
    """Test the performance scorer with sample data"""
    scorer = PerformanceScorer()
    
    # Test data - decent performance
    test_metrics = {
        'articles_processed': 100,
        'events_created': 25,
        'event_creation_rate': 0.25,
        'coverage_percentage': 55.0,
        'avg_articles_per_event': 2.8,
        'singleton_events_count': 5,
        'processing_time_ms': 8000,  # 80ms per article
    }
    
    result = scorer.calculate_overall_score(test_metrics)
    print(f"Test Score: {result['overall_score']}")
    print(f"Components: {result['components']}")
    
    interpretation = scorer.get_score_interpretation(result['overall_score'])
    print(f"Grade: {interpretation['grade']} - {interpretation['interpretation']}")
    
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_performance_scorer()