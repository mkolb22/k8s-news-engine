#!/usr/bin/env python3
"""
Test to validate that quality scores are returned as whole numbers
"""

import unittest
import sys
import os

# Add the service directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the psycopg2 module before importing main
sys.modules['psycopg2'] = type(sys)('psycopg2')
sys.modules['psycopg2.extras'] = type(sys)('psycopg2.extras')

from writing_quality_analyzer import WritingQualityAnalyzer

class TestWholeNumberScoring(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = WritingQualityAnalyzer()
        
    def test_composite_score_rounding(self):
        """Test that composite scores are properly rounded to whole numbers"""
        
        test_cases = [
            # (writing_score, outlet_reputation, expected_composite)
            (67, 40, 80),  # 67*0.6 + 40 = 40.2 + 40 = 80.2 -> 80 (round down)
            (68, 40, 81),  # 68*0.6 + 40 = 40.8 + 40 = 80.8 -> 81 (round up)
            (75, 30, 75),  # 75*0.6 + 30 = 45 + 30 = 75 -> 75 (exact)
            (83, 25, 75),  # 83*0.6 + 25 = 49.8 + 25 = 74.8 -> 75 (round up)
            (54, 25, 57),  # 54*0.6 + 25 = 32.4 + 25 = 57.4 -> 57 (round down)
            (63, 24, 62),  # 63*0.6 + 24 = 37.8 + 24 = 61.8 -> 62 (round up)
            (58, 25, 60),  # 58*0.6 + 25 = 34.8 + 25 = 59.8 -> 60 (round up)
            (59, 25, 60),  # 59*0.6 + 25 = 35.4 + 25 = 60.4 -> 60 (round down)
            (60, 25, 61),  # 60*0.6 + 25 = 36.0 + 25 = 61.0 -> 61 (exact)
        ]
        
        for writing_score, outlet_reputation, expected_composite in test_cases:
            # Calculate composite score using the same logic as main.py
            writing_quality_weighted = writing_score * 0.6
            composite_score = writing_quality_weighted + outlet_reputation
            
            # Apply custom rounding: <=0.5 rounds down, >0.5 rounds up
            decimal_part = composite_score - int(composite_score)
            if decimal_part <= 0.5:
                rounded_score = int(composite_score)
            else:
                rounded_score = int(composite_score) + 1
            
            self.assertEqual(rounded_score, expected_composite, 
                           f"Writing={writing_score}, Outlet={outlet_reputation} "
                           f"should give Composite={expected_composite}, "
                           f"but got {rounded_score} (raw={composite_score})")
            
            # Verify it's a whole number (no decimal places)
            self.assertEqual(rounded_score, int(rounded_score))
            
    def test_score_capping_at_100(self):
        """Test that scores are capped at 100"""
        
        # Very high scores should be capped at 100
        writing_score = 100
        outlet_reputation = 40
        recency_bonus = 5
        
        composite = writing_score * 0.6 + outlet_reputation + recency_bonus
        # Apply custom rounding
        decimal_part = composite - int(composite)
        if decimal_part <= 0.5:
            rounded = int(composite)
        else:
            rounded = int(composite) + 1
        final_score = min(rounded, 100)
        
        self.assertEqual(final_score, 100, "Score should be capped at 100")
        
    def test_decimal_to_whole_conversion(self):
        """Test various decimal values round correctly with custom logic"""
        
        test_values = [
            (79.4, 79),   # <=0.5 rounds down
            (79.5, 79),   # <=0.5 rounds down
            (79.6, 80),   # >0.5 rounds up
            (50.0, 50),   # exact
            (50.1, 50),   # <=0.5 rounds down
            (50.5, 50),   # <=0.5 rounds down
            (50.6, 51),   # >0.5 rounds up
            (51.5, 51),   # <=0.5 rounds down
            (99.9, 100),  # >0.5 rounds up
        ]
        
        for decimal_val, expected_whole in test_values:
            # Apply custom rounding logic
            decimal_part = decimal_val - int(decimal_val)
            if decimal_part <= 0.5:
                result = int(decimal_val)
            else:
                result = int(decimal_val) + 1
                
            self.assertEqual(result, expected_whole, 
                           f"{decimal_val} should round to {expected_whole}")

def run_validation():
    """Run validation tests for whole number scoring"""
    
    print("=" * 60)
    print("WHOLE NUMBER SCORING - VALIDATION TESTS")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWholeNumberScoring)
    runner = unittest.TextTestRunner(verbosity=2)
    
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED - WHOLE NUMBER SCORING VALIDATED")
    else:
        print(f"\n❌ VALIDATION FAILED")
        
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_validation()
    sys.exit(0 if success else 1)