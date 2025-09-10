#!/usr/bin/env python3
"""
Unit Tests for Writing Quality Analyzer
Comprehensive validation of quality scoring implementation
"""

import unittest
import sys
import os
from dataclasses import asdict

# Add the service directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from writing_quality_analyzer import WritingQualityAnalyzer, WritingQualityScores

class TestWritingQualityAnalyzer(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = WritingQualityAnalyzer()
        
        # High quality news article sample
        self.high_quality_article = """
        President Biden announced today a comprehensive infrastructure plan that will invest $2.3 trillion in American transportation, broadband, and manufacturing over the next eight years. Speaking at a press conference in Pittsburgh, Pennsylvania, the president outlined details of the proposal that has been months in development.

        "This is a once-in-a-generation investment in America," Biden said in remarks to reporters gathered at a steel manufacturing facility. "We're talking about fixing our roads and bridges, but also preparing our economy for the challenges of the 21st century."

        The plan includes $621 billion for transportation infrastructure, including roads, bridges, public transit, airports, and electric vehicle charging stations. According to White House officials, the package would create millions of jobs while addressing critical maintenance needs across the country.

        Transportation Secretary Pete Buttigieg told CNN that the administration expects bipartisan support for many elements of the proposal. "We've heard from Republicans and Democrats alike about the need to modernize our infrastructure," Buttigieg stated in an interview Tuesday.

        However, Senate Minority Leader Mitch McConnell expressed skepticism about the scope and cost of the proposal. "While we support infrastructure investment, this package includes spending on priorities that aren't truly infrastructure," McConnell said in a statement released by his office.

        The plan would be funded through a series of tax increases on corporations, including raising the corporate tax rate from 21% to 28%. Treasury Secretary Janet Yellen confirmed the tax provisions during testimony before the House Ways and Means Committee last week.

        Economic analysts predict the legislation will face significant challenges in Congress, where Democrats hold narrow majorities in both chambers. The proposal comes as the Biden administration continues implementation of the $1.9 trillion American Rescue Plan passed in March.
        """
        
        # Low quality article sample 
        self.low_quality_article = """
        This is shocking news that everyone should know about. The president said something today and it was incredible. Sources say that this will change everything but they don't want to tell us the details.

        Everyone knows this is obviously the most important announcement ever made. Officials supposedly confirmed this but apparently they're hiding the truth from the American people.

        This is devastating news for the opposition and incredible news for supporters. It seems like this will have amazing consequences.
        """
        
        # Technical article sample
        self.technical_article = """
        The Federal Reserve announced Wednesday that it will maintain its target federal funds rate at 0-0.25 percent, citing ongoing concerns about economic recovery from the COVID-19 pandemic. In a statement released following the conclusion of the Federal Open Market Committee meeting, the central bank indicated that monetary policy will remain accommodative until labor market conditions improve substantially.

        Federal Reserve Chair Jerome Powell explained during a press conference that the committee sees continued progress in vaccination distribution and fiscal support as key factors in the economic outlook. "We expect moderate growth in the coming quarters, but risks remain," Powell stated.

        The decision was unanimous among voting members of the FOMC. The committee also maintained its asset purchase program at $120 billion per month, split between $80 billion in Treasury securities and $40 billion in agency mortgage-backed securities.

        Economists surveyed by Reuters had expected the Fed to hold rates steady, with 85% predicting no change in the target rate. The central bank has kept rates near zero since March 2020, when the pandemic began affecting the U.S. economy.
        """
        
    def test_high_quality_article_analysis(self):
        """Test analysis of high quality news article"""
        
        scores = self.analyzer.analyze_article(self.high_quality_article, "Biden Announces Infrastructure Plan")
        
        # Verify overall score is high
        self.assertGreater(scores.total_score, 65, "High quality article should score above 65")
        
        # Verify component scores
        self.assertGreater(scores.readability_score, 15, "Should have good readability")
        self.assertGreater(scores.structure_score, 20, "Should have strong journalistic structure") 
        self.assertGreater(scores.linguistic_score, 12, "Should have good linguistic quality")
        self.assertGreater(scores.objectivity_score, 8, "Should show objectivity")
        
        # Check for multiple source attribution
        self.assertGreater(scores.source_attribution, 7, "Should have strong source attribution")
        
        # Check lead quality
        self.assertGreater(scores.lead_quality, 7, "Should have strong lead paragraph")
        
        # Verify low bias indicators
        self.assertLessEqual(len(scores.bias_indicators), 2, "Should have minimal bias indicators")
        
    def test_low_quality_article_analysis(self):
        """Test analysis of low quality article"""
        
        scores = self.analyzer.analyze_article(self.low_quality_article, "Shocking News")
        
        # Verify overall score is low
        self.assertLess(scores.total_score, 60, "Low quality article should score below 60")
        
        # Verify structural issues
        self.assertLess(scores.structure_score, 15, "Should have weak structure")
        self.assertLess(scores.source_attribution, 5, "Should have poor source attribution")
        
        # Check for bias indicators
        self.assertGreater(len(scores.bias_indicators), 3, "Should detect multiple bias indicators")
        
        # Check objectivity score
        self.assertLess(scores.objectivity_score, 5, "Should have low objectivity score")
        
    def test_technical_article_analysis(self):
        """Test analysis of technical/financial article"""
        
        scores = self.analyzer.analyze_article(self.technical_article, "Fed Holds Rates Steady")
        
        # Verify reasonable score range
        self.assertGreaterEqual(scores.total_score, 55, "Technical article should score reasonably")
        self.assertLessEqual(scores.total_score, 85, "But may not reach highest scores")
        
        # Should have good source attribution for technical content
        self.assertGreater(scores.source_attribution, 4, "Should cite sources")
        
        # Check readability (may be lower for technical content)
        self.assertGreaterEqual(scores.readability_score, 10, "Should be reasonably readable")
        
    def test_short_article_handling(self):
        """Test handling of articles too short for analysis"""
        
        short_text = "This is too short."
        scores = self.analyzer.analyze_article(short_text, "Short Title")
        
        # Should return default scores
        self.assertEqual(scores.total_score, 49, "Should return default neutral score")
        
    def test_empty_article_handling(self):
        """Test handling of empty articles"""
        
        scores = self.analyzer.analyze_article("", "Empty Article")
        
        # Should return default scores  
        self.assertEqual(scores.total_score, 49, "Should return default neutral score for empty text")
        
    def test_readability_scoring(self):
        """Test readability scoring component"""
        
        # Simple, readable text
        simple_text = "The cat sat on the mat. It was a sunny day. The children played in the park. Everyone had fun."
        simple_score = self.analyzer._calculate_readability_score(simple_text)
        
        # Complex, difficult text
        complex_text = "The methodological frameworks underlying contemporary epistemological discourse necessitate multifaceted analytical paradigms encompassing phenomenological hermeneutics."
        complex_score = self.analyzer._calculate_readability_score(complex_text)
        
        # Simple text should score higher than complex text
        self.assertGreater(simple_score, complex_score, "Simple text should score higher than complex text")
        
    def test_bias_detection(self):
        """Test bias indicator detection"""
        
        biased_text = "This is clearly outrageous and everyone knows it's devastating news that will shock the world."
        neutral_text = "The committee announced its decision following a thorough review of available data and stakeholder input."
        
        biased_score = self.analyzer._detect_bias_score(biased_text)
        neutral_score = self.analyzer._detect_bias_score(neutral_text)
        
        self.assertLess(biased_score, neutral_score, "Biased text should score lower than neutral text")
        
    def test_source_attribution_detection(self):
        """Test source attribution analysis"""
        
        well_sourced = 'According to John Smith, the CEO announced plans. "We are committed to growth," Smith said. Officials confirmed the details.'
        poorly_sourced = "Someone said something about plans. There might be growth. Things were confirmed."
        
        well_sourced_score = self.analyzer._analyze_source_attribution(well_sourced)
        poorly_sourced_score = self.analyzer._analyze_source_attribution(poorly_sourced)
        
        self.assertGreater(well_sourced_score, poorly_sourced_score, "Well-sourced content should score higher")
        
    def test_lead_quality_analysis(self):
        """Test lead paragraph quality analysis"""
        
        strong_lead = "President Biden announced Tuesday a $2 trillion infrastructure plan during a speech in Pittsburgh, targeting improvements to roads and bridges across the country."
        weak_lead = "Something important happened today and it might affect things."
        
        strong_score = self.analyzer._analyze_lead_quality(strong_lead)
        weak_score = self.analyzer._analyze_lead_quality(weak_lead)
        
        self.assertGreater(strong_score, weak_score, "Strong lead should score higher than weak lead")
        
    def test_multiple_perspectives_detection(self):
        """Test detection of multiple perspectives"""
        
        balanced_text = "Supporters argue the plan will create jobs. However, critics say the cost is too high. Meanwhile, economists suggest a middle approach."
        one_sided_text = "The plan is great and everyone supports it completely."
        
        balanced_score = self.analyzer._analyze_multiple_perspectives(balanced_text)
        one_sided_score = self.analyzer._analyze_multiple_perspectives(one_sided_text)
        
        self.assertGreater(balanced_score, one_sided_score, "Balanced content should score higher")
        
    def test_sentence_variety_analysis(self):
        """Test sentence variety scoring"""
        
        varied_sentences = "This is short. This is a medium-length sentence with some detail. This is a much longer sentence that contains multiple clauses and provides comprehensive information about the topic being discussed."
        monotone_sentences = "This is one sentence. This is another sentence. This is yet another sentence."
        
        varied_score = self.analyzer._analyze_sentence_variety(varied_sentences)
        monotone_score = self.analyzer._analyze_sentence_variety(monotone_sentences)
        
        self.assertGreaterEqual(varied_score, monotone_score, "Varied sentences should score equal or higher")
        
    def test_score_ranges(self):
        """Test that all scores fall within expected ranges"""
        
        scores = self.analyzer.analyze_article(self.high_quality_article, "Test Title")
        
        # Test individual component ranges
        self.assertGreaterEqual(scores.readability_score, 0)
        self.assertLessEqual(scores.readability_score, 30)
        
        self.assertGreaterEqual(scores.structure_score, 0) 
        self.assertLessEqual(scores.structure_score, 35)
        
        self.assertGreaterEqual(scores.linguistic_score, 0)
        self.assertLessEqual(scores.linguistic_score, 20)
        
        self.assertGreaterEqual(scores.objectivity_score, 0)
        self.assertLessEqual(scores.objectivity_score, 15)
        
        # Test total score range
        self.assertGreaterEqual(scores.total_score, 0)
        self.assertLessEqual(scores.total_score, 100)
        
    def test_scores_dataclass_structure(self):
        """Test that scores object has all expected fields"""
        
        scores = self.analyzer.analyze_article(self.high_quality_article, "Test")
        
        # Test all required fields are present
        required_fields = [
            'readability_score', 'structure_score', 'linguistic_score', 'objectivity_score',
            'total_score', 'flesch_reading_ease', 'flesch_kincaid_grade', 'lead_quality',
            'source_attribution', 'sentence_variety', 'grammar_quality', 'bias_indicators'
        ]
        
        scores_dict = asdict(scores)
        
        for field in required_fields:
            self.assertIn(field, scores_dict, f"Missing required field: {field}")

def run_comprehensive_validation():
    """
    Run comprehensive validation tests and return results
    """
    
    print("=" * 60)
    print("WRITING QUALITY ANALYZER - VALIDATION TESTS")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWritingQualityAnalyzer)
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
            
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
            
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    return result.wasSuccessful(), success_rate

if __name__ == '__main__':
    # Run comprehensive validation
    success, rate = run_comprehensive_validation()
    
    if success:
        print("\n✅ ALL TESTS PASSED - WRITING QUALITY ANALYZER VALIDATED")
        sys.exit(0)
    else:
        print(f"\n❌ VALIDATION FAILED - Success Rate: {rate:.1f}%") 
        sys.exit(1)