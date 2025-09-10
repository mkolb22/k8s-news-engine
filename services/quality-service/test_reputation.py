#!/usr/bin/env python3
"""
Test Reputation Scoring System
"""

import os
import logging
from reputation_analyzer import ReputationAnalyzer

logging.basicConfig(level=logging.INFO)

def test_reputation_scoring():
    """Test reputation scoring for populated outlets"""
    
    os.environ['DATABASE_URL'] = "postgresql://appuser:newsengine2024@localhost:5432/newsdb"
    
    test_outlets = [
        'ProPublica', 'The New York Times', 'BBC News', 'Reuters', 
        'Associated Press', 'Fox News', 'CNN'
    ]
    
    analyzer = ReputationAnalyzer()
    analyzer.connect_to_database()
    
    print("=== REPUTATION SCORING TEST RESULTS ===")
    print()
    
    for outlet in test_outlets:
        try:
            score = analyzer.calculate_reputation_score(outlet)
            print(f"{outlet:20}: {score:6.1f}/100")
        except Exception as e:
            print(f"{outlet:20}: ERROR - {e}")
    
    analyzer.close()

if __name__ == "__main__":
    test_reputation_scoring()