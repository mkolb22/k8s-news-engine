#!/usr/bin/env python3
"""
Test RSS Agency Validation

Quick test script to verify RSS feed to news agency validation is working properly
"""

import os
import sys
from rss_agency_validator import validate_rss_feed_mapping, get_rss_validation_report

def test_validation():
    """Test the RSS feed validation functionality"""
    
    # Set up database connection
    os.environ['DATABASE_URL'] = 'postgresql://appuser:newsengine2024@localhost:5432/newsdb?sslmode=disable'
    
    print("=== RSS Feed to News Agency Validation Test ===\n")
    
    # Test specific outlet validations
    test_outlets = [
        'BBC News',
        'CNN Top Stories',
        'Reuters Top News',
        'NPR News',
        'CBS News',
        'The Guardian World'
    ]
    
    print("Testing specific outlet validations:")
    print("-" * 50)
    
    for outlet in test_outlets:
        try:
            has_score, reputation_score, message = validate_rss_feed_mapping(outlet)
            status = "✓ VALID" if has_score and reputation_score > 0 else "✗ INVALID"
            score_display = f"{reputation_score:.1f}" if reputation_score else "None"
            print(f"{status:10} | {outlet:20} | Score: {score_display:6} | {message}")
        except Exception as e:
            print(f"ERROR     | {outlet:20} | Error: {e}")
    
    print("\n" + "=" * 70)
    
    # Generate validation report
    print("\nGenerating comprehensive validation report...")
    try:
        report = get_rss_validation_report()
        summary = report['summary']
        
        print(f"\n📊 RSS Feed Validation Summary:")
        print(f"   Total RSS Feeds: {summary['total_rss_feeds']}")
        print(f"   Mapped to Agencies: {summary['mapped_to_agencies']} ({summary['mapping_percentage']}%)")
        print(f"   With Reputation Scores: {summary['with_reputation_scores']} ({summary['scoring_percentage']}%)")
        print(f"   Unmapped Feeds: {summary['unmapped_feeds']}")
        print(f"   Mapped but Unscored: {summary['mapped_but_unscored']}")
        
        if summary['unmapped_feeds'] > 0:
            print(f"\n⚠️  Unmapped RSS Feeds:")
            for feed in report['unmapped_feeds'][:5]:  # Show first 5
                print(f"   - {feed['outlet']} ({feed['url']})")
            if len(report['unmapped_feeds']) > 5:
                print(f"   ... and {len(report['unmapped_feeds']) - 5} more")
                
        if report['mapping_suggestions']:
            print(f"\n💡 Suggested Mappings:")
            for suggestion in report['mapping_suggestions'][:5]:
                print(f"   - '{suggestion['rss_outlet']}' → '{suggestion['suggested_agency']}'")
                
    except Exception as e:
        print(f"Error generating validation report: {e}")
    
    print("\n" + "=" * 70)
    print("Test completed!")

if __name__ == "__main__":
    test_validation()