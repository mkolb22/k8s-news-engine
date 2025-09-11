#!/usr/bin/env python3
"""
NER Test Runner
Validate NER improvements against test cases and performance thresholds
"""

import sys
import time
import json
from typing import Dict, List
from test_ner_improvements import NERImprovementTests, NERPerformanceThresholds, NERTestCase
from improved_ner import ImprovedNERExtractor


def run_performance_tests(extractor: ImprovedNERExtractor, test_cases: List[NERTestCase]) -> Dict:
    """Run performance tests and validate against thresholds"""
    results = {
        'passed': True,
        'total_cases': len(test_cases),
        'processing_times': [],
        'entity_counts': [],
        'noise_detected': [],
        'performance_metrics': {},
        'failures': []
    }
    
    print("Running NER Performance Tests...")
    print("=" * 50)
    
    total_entities = 0
    total_noise = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {case.description}")
        
        start_time = time.time()
        result = extractor.extract_entities(case.text, case.title)
        processing_time = time.time() - start_time
        
        results['processing_times'].append(processing_time)
        results['entity_counts'].append(result.total_entities)
        
        # Performance threshold checks
        if processing_time > NERPerformanceThresholds.MAX_PROCESSING_TIME_PER_ARTICLE:
            results['failures'].append(f"Case {i}: Processing time {processing_time:.3f}s exceeds threshold {NERPerformanceThresholds.MAX_PROCESSING_TIME_PER_ARTICLE}s")
            results['passed'] = False
        
        if result.total_entities < NERPerformanceThresholds.MIN_ENTITIES_PER_ARTICLE:
            results['failures'].append(f"Case {i}: Only {result.total_entities} entities extracted, minimum is {NERPerformanceThresholds.MIN_ENTITIES_PER_ARTICLE}")
            results['passed'] = False
        
        # Quality assessment (simplified)
        expected_total = len(case.expected_persons) + len(case.expected_organizations) + len(case.expected_locations) + len(case.expected_misc)
        extracted_total = result.total_entities
        
        # Check for obvious noise (very short entities, numbers, etc.)
        noise_count = 0
        all_entities = list(result.persons) + list(result.organizations) + list(result.locations) + list(result.misc)
        for entity in all_entities:
            if len(entity) <= 2 or entity.isdigit() or entity.lower() in ['who', 'said', 'told', 'the', 'and']:
                noise_count += 1
        
        noise_percentage = (noise_count / max(extracted_total, 1)) * 100
        results['noise_detected'].append(noise_percentage)
        
        if noise_percentage > NERPerformanceThresholds.MAX_NOISE_PERCENTAGE:
            results['failures'].append(f"Case {i}: Noise percentage {noise_percentage:.1f}% exceeds threshold {NERPerformanceThresholds.MAX_NOISE_PERCENTAGE}%")
            results['passed'] = False
        
        total_entities += extracted_total
        total_noise += noise_count
        
        print(f"  - Processing time: {processing_time:.3f}s")
        print(f"  - Entities extracted: {extracted_total}")
        print(f"  - Noise percentage: {noise_percentage:.1f}%")
        print(f"  - Persons: {len(result.persons)} | Orgs: {len(result.organizations)} | Locations: {len(result.locations)}")
        print()
    
    # Calculate overall metrics
    avg_processing_time = sum(results['processing_times']) / len(results['processing_times'])
    avg_entities = sum(results['entity_counts']) / len(results['entity_counts'])
    avg_noise = sum(results['noise_detected']) / len(results['noise_detected'])
    
    results['performance_metrics'] = {
        'avg_processing_time': avg_processing_time,
        'max_processing_time': max(results['processing_times']),
        'avg_entities_per_article': avg_entities,
        'avg_noise_percentage': avg_noise,
        'total_entities_extracted': total_entities,
        'total_noise_detected': total_noise
    }
    
    print("Overall Performance Metrics:")
    print(f"  - Average processing time: {avg_processing_time:.3f}s")
    print(f"  - Maximum processing time: {max(results['processing_times']):.3f}s") 
    print(f"  - Average entities per article: {avg_entities:.1f}")
    print(f"  - Average noise percentage: {avg_noise:.1f}%")
    print()
    
    return results


def test_problematic_cases(extractor: ImprovedNERExtractor) -> bool:
    """Test the specific problematic cases from our database"""
    print("Testing Known Problematic Cases...")
    print("=" * 40)
    
    problematic_cases = [
        {
            "title": "News Wrap: Democrats release birthday message Trump allegedly sent to Jeffrey Epstein",
            "text": "House Democrats on Monday released what they described as a birthday message from Trump to Jeffrey Epstein. The message was part of documents released by Congress in New York.",
            "current_problems": {
                "orgs": ["who"],  # Should not extract "who" as organization
                "locations": ["House", "Monday", "Congress", "New York"]  # "Monday" should not be location
            },
            "expected_improvements": {
                "should_extract": {"Trump", "Jeffrey Epstein", "Democrats", "Congress", "New York"},
                "should_not_extract": {"who", "Monday", "House"}  # "House" alone without "White House" context
            }
        },
        {
            "title": "Attorney says detained Korean Hyundai workers had special skills for short-term jobs",
            "text": "Associated Press reporters Kate Brumback and Russ Bynum contributed to this report from Georgia, Atlanta, and Savannah. Jin Kim also contributed.",
            "current_problems": {
                "orgs": ["But immigration lawyer Kuck said no", "who"],
                "locations": ["Press\nKate Brumback", "Russ Bynum", "Press\nRuss Bynum", "Associated"]  # Names wrongly classified as locations
            },
            "expected_improvements": {
                "should_extract": {"Kate Brumback", "Russ Bynum", "Jin Kim", "Associated Press", "Georgia", "Atlanta", "Savannah"},
                "should_not_extract": {"who", "Press", "Associated"}  # "Associated" alone without "Press"
            }
        }
    ]
    
    all_passed = True
    
    for i, case in enumerate(problematic_cases, 1):
        print(f"Problematic Case {i}: {case['title'][:50]}...")
        
        result = extractor.extract_entities(case["text"], case["title"])
        
        all_extracted = set()
        all_extracted.update(e.lower() for e in result.persons)
        all_extracted.update(e.lower() for e in result.organizations)
        all_extracted.update(e.lower() for e in result.locations)
        all_extracted.update(e.lower() for e in result.misc)
        
        # Check improvements
        should_extract = {e.lower() for e in case["expected_improvements"]["should_extract"]}
        should_not_extract = {e.lower() for e in case["expected_improvements"]["should_not_extract"]}
        
        missing = should_extract - all_extracted
        wrong_extractions = should_not_extract & all_extracted
        
        case_passed = len(missing) == 0 and len(wrong_extractions) == 0
        
        print(f"  - Extracted: {result.persons | result.organizations | result.locations}")
        print(f"  - Missing expected: {missing}")
        print(f"  - Wrong extractions: {wrong_extractions}")
        print(f"  - Status: {'✓ PASSED' if case_passed else '✗ FAILED'}")
        print()
        
        if not case_passed:
            all_passed = False
    
    return all_passed


def run_comparison_test(extractor: ImprovedNERExtractor) -> Dict:
    """Compare new NER with old regex-based approach"""
    print("Comparison Test: New vs Old NER")
    print("=" * 35)
    
    test_text = """President Joe Biden met with Israeli Prime Minister Benjamin Netanyahu 
    at the White House on Tuesday. The meeting was reported by the Associated Press and CNN.
    According to sources who spoke to reporters, the discussion focused on Gaza and regional security.
    Photos by Getty Images showed the two leaders shaking hands."""
    
    # Test new system
    new_result = extractor.extract_entities(test_text)
    
    # Test old regex approach (simplified version)
    import re
    old_entities = set()
    pattern = r'\b([A-Z][a-z]+)\b'
    matches = re.findall(pattern, test_text)
    
    old_non_entities = {'The', 'Who', 'According', 'Photos', 'Getty', 'Images', 'Tuesday'}
    for match in matches:
        if match not in old_non_entities and len(match) > 3:
            old_entities.add(match.lower())
    
    new_all = set()
    new_all.update(e.lower() for e in new_result.persons)
    new_all.update(e.lower() for e in new_result.organizations)
    new_all.update(e.lower() for e in new_result.locations)
    
    print("Old Regex Approach:")
    print(f"  Entities: {sorted(old_entities)}")
    print(f"  Count: {len(old_entities)}")
    print()
    
    print("New spaCy Approach:")
    print(f"  Persons: {sorted(new_result.persons)}")
    print(f"  Organizations: {sorted(new_result.organizations)}")
    print(f"  Locations: {sorted(new_result.locations)}")
    print(f"  Count: {new_result.total_entities}")
    print(f"  Processing time: {new_result.processing_time:.3f}s")
    print()
    
    # Quality assessment
    expected_good_entities = {"joe biden", "benjamin netanyahu", "white house", "associated press", "cnn", "gaza"}
    expected_bad_entities = {"who", "according", "photos", "getty", "images", "tuesday"}
    
    new_good_found = len(expected_good_entities & new_all)
    new_bad_found = len(expected_bad_entities & new_all)
    old_good_found = len(expected_good_entities & old_entities)
    old_bad_found = len(expected_bad_entities & old_entities)
    
    improvement = {
        'new_precision': new_good_found / max(new_result.total_entities, 1),
        'old_precision': old_good_found / max(len(old_entities), 1),
        'new_good_entities': new_good_found,
        'old_good_entities': old_good_found,
        'new_bad_entities': new_bad_found, 
        'old_bad_entities': old_bad_found
    }
    
    print("Quality Comparison:")
    print(f"  New system - Good entities: {new_good_found}/{len(expected_good_entities)}, Bad entities: {new_bad_found}")
    print(f"  Old system - Good entities: {old_good_found}/{len(expected_good_entities)}, Bad entities: {old_bad_found}")
    print(f"  Precision improvement: {improvement['new_precision']:.2f} vs {improvement['old_precision']:.2f}")
    print()
    
    return improvement


def main():
    """Main test runner"""
    print("NER Improvement Test Suite")
    print("=" * 60)
    print()
    
    # Initialize the improved NER extractor
    extractor = ImprovedNERExtractor()
    
    # Display system info
    stats = extractor.get_statistics()
    print("System Information:")
    print(f"  - spaCy available: {stats['spacy_available']}")
    print(f"  - Model: {stats['model_name']}")
    print()
    
    # Create test cases
    test_suite = NERImprovementTests()
    test_suite.setUp()
    test_cases = test_suite.test_cases
    
    # Run performance tests
    perf_results = run_performance_tests(extractor, test_cases)
    
    # Test problematic cases
    problematic_passed = test_problematic_cases(extractor)
    
    # Run comparison test
    comparison_results = run_comparison_test(extractor)
    
    # Final assessment
    print("FINAL ASSESSMENT")
    print("=" * 40)
    
    overall_passed = (
        perf_results['passed'] and 
        problematic_passed and
        comparison_results['new_precision'] > comparison_results['old_precision']
    )
    
    print(f"Performance Tests: {'✓ PASSED' if perf_results['passed'] else '✗ FAILED'}")
    print(f"Problematic Cases: {'✓ PASSED' if problematic_passed else '✗ FAILED'}")
    print(f"Comparison Test: {'✓ IMPROVED' if comparison_results['new_precision'] > comparison_results['old_precision'] else '✗ NO IMPROVEMENT'}")
    print()
    print(f"Overall Result: {'✓ READY FOR DEPLOYMENT' if overall_passed else '✗ NEEDS MORE WORK'}")
    
    if perf_results['failures']:
        print("\nFailures:")
        for failure in perf_results['failures']:
            print(f"  - {failure}")
    
    # Export results for documentation
    full_results = {
        'timestamp': time.time(),
        'system_info': stats,
        'performance_results': perf_results,
        'problematic_cases_passed': problematic_passed,
        'comparison_results': comparison_results,
        'overall_passed': overall_passed,
        'ready_for_deployment': overall_passed
    }
    
    with open('/tmp/ner_test_results.json', 'w') as f:
        json.dump(full_results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: /tmp/ner_test_results.json")
    
    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())