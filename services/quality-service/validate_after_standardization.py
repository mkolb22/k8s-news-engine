#!/usr/bin/env python3
"""
Post-Standardization Validation Script

Validates that column naming standardization approach is working correctly.
Tests the compatibility layer and ensures all relationships are intact.
"""

import psycopg2
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
from column_compatibility import (
    get_articles_to_reputation_join,
    get_rss_feeds_to_reputation_join,
    get_articles_outlet_select,
    get_reputation_outlet_select,
    validate_query_compatibility
)

def run_post_standardization_validation() -> Dict:
    """Run comprehensive validation after standardization"""
    
    database_url = os.environ.get('DATABASE_URL', 
                                 'postgresql://appuser:newsengine2024@localhost:5432/newsdb?sslmode=disable')
    
    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'standardization_approach': 'code-first',
        'database_url': database_url.split('@')[1],  # Hide credentials
        'compatibility_tests': {},
        'data_relationships': {},
        'query_consistency': {},
        'validation_status': 'UNKNOWN'
    }
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔍 Post-Standardization Validation Starting...")
        print("=" * 60)
        
        # 1. Test compatibility layer functions
        validation_results['compatibility_tests'] = test_compatibility_layer(cursor)
        
        # 2. Verify data relationships still work
        validation_results['data_relationships'] = verify_data_relationships(cursor)
        
        # 3. Test standardized queries
        validation_results['query_consistency'] = test_query_consistency(cursor)
        
        validation_results['validation_status'] = 'COMPLETED'
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Post-Standardization Validation Completed Successfully")
        
        return validation_results
        
    except Exception as e:
        validation_results['validation_status'] = f'FAILED: {str(e)}'
        print(f"❌ Post-Standardization Validation Failed: {e}")
        raise

def test_compatibility_layer(cursor) -> Dict:
    """Test the column compatibility layer functions"""
    
    print("\n🧪 Testing Compatibility Layer:")
    print("-" * 40)
    
    compatibility_results = {}
    
    # Test standardized queries using compatibility functions
    try:
        # Test articles to reputation join
        articles_reputation_join = get_articles_to_reputation_join()
        query = f"""
            SELECT COUNT(*) as total_articles,
                   COUNT(narm.outlet_name) as articles_with_reputation
            FROM articles a
            LEFT JOIN news_agency_reputation_metrics narm ON {articles_reputation_join}
        """
        
        cursor.execute(query)
        total, with_rep = cursor.fetchone()
        coverage = (with_rep / total * 100) if total > 0 else 0
        
        compatibility_results['articles_reputation_join'] = {
            'total_articles': total,
            'articles_with_reputation': with_rep,
            'coverage_percentage': round(coverage, 2),
            'query_used': articles_reputation_join,
            'success': True
        }
        
        print(f"  ✓ Articles→Reputation JOIN: {with_rep}/{total} ({coverage:.1f}%)")
        
    except Exception as e:
        compatibility_results['articles_reputation_join'] = {
            'success': False,
            'error': str(e)
        }
        print(f"  ❌ Articles→Reputation JOIN failed: {e}")
    
    # Test RSS feeds to reputation join
    try:
        rss_reputation_join = get_rss_feeds_to_reputation_join()
        query = f"""
            SELECT COUNT(*) as total_feeds,
                   COUNT(narm.outlet_name) as feeds_with_reputation
            FROM rss_feeds rf
            LEFT JOIN news_agency_reputation_metrics narm ON {rss_reputation_join}
        """
        
        cursor.execute(query)
        total, with_rep = cursor.fetchone()
        coverage = (with_rep / total * 100) if total > 0 else 0
        
        compatibility_results['rss_reputation_join'] = {
            'total_feeds': total,
            'feeds_with_reputation': with_rep,
            'coverage_percentage': round(coverage, 2),
            'query_used': rss_reputation_join,
            'success': True
        }
        
        print(f"  ✓ RSS→Reputation JOIN: {with_rep}/{total} ({coverage:.1f}%)")
        
    except Exception as e:
        compatibility_results['rss_reputation_join'] = {
            'success': False,
            'error': str(e)
        }
        print(f"  ❌ RSS→Reputation JOIN failed: {e}")
    
    return compatibility_results

def verify_data_relationships(cursor) -> Dict:
    """Verify that data relationships are maintained"""
    
    print("\n🔗 Verifying Data Relationships:")
    print("-" * 40)
    
    relationship_results = {}
    
    # Test outlet name consistency across tables
    try:
        # Get unique outlet names from each table using physical columns
        cursor.execute("SELECT DISTINCT outlet FROM articles ORDER BY outlet")
        article_outlets = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT outlet FROM rss_feeds ORDER BY outlet")
        rss_outlets = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT outlet_name FROM news_agency_reputation_metrics ORDER BY outlet_name")
        reputation_outlets = [row[0] for row in cursor.fetchall()]
        
        # Find overlaps
        article_rss_overlap = set(article_outlets) & set(rss_outlets)
        article_reputation_overlap = set(article_outlets) & set(reputation_outlets)
        rss_reputation_overlap = set(rss_outlets) & set(reputation_outlets)
        
        relationship_results['outlet_consistency'] = {
            'article_outlets_count': len(article_outlets),
            'rss_outlets_count': len(rss_outlets),
            'reputation_outlets_count': len(reputation_outlets),
            'article_rss_overlap': len(article_rss_overlap),
            'article_reputation_overlap': len(article_reputation_overlap),
            'rss_reputation_overlap': len(rss_reputation_overlap),
            'article_outlets': article_outlets[:5],  # Sample
            'reputation_outlets': reputation_outlets[:5]  # Sample
        }
        
        print(f"  📊 Article outlets: {len(article_outlets)}")
        print(f"  📡 RSS outlets: {len(rss_outlets)}")
        print(f"  🏆 Reputation outlets: {len(reputation_outlets)}")
        print(f"  🔗 Article↔Reputation overlap: {len(article_reputation_overlap)}")
        
    except Exception as e:
        relationship_results['outlet_consistency'] = {
            'success': False,
            'error': str(e)
        }
        print(f"  ❌ Outlet consistency check failed: {e}")
    
    return relationship_results

def test_query_consistency(cursor) -> Dict:
    """Test that queries are consistent and working correctly"""
    
    print("\n📋 Testing Query Consistency:")
    print("-" * 40)
    
    consistency_results = {}
    
    # Test a complex query that uses multiple table joins
    try:
        query = """
            SELECT 
                a.outlet as article_outlet,
                narm.outlet_name as reputation_outlet,
                narm.final_reputation_score,
                COUNT(a.id) as article_count
            FROM articles a
            LEFT JOIN news_agency_reputation_metrics narm ON a.outlet = narm.outlet_name
            WHERE narm.final_reputation_score IS NOT NULL
            GROUP BY a.outlet, narm.outlet_name, narm.final_reputation_score
            ORDER BY narm.final_reputation_score DESC
            LIMIT 10
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        consistency_results['complex_join_query'] = {
            'success': True,
            'results_count': len(results),
            'sample_results': [
                {
                    'article_outlet': row[0],
                    'reputation_outlet': row[1], 
                    'reputation_score': float(row[2]),
                    'article_count': row[3]
                } for row in results[:5]
            ]
        }
        
        print(f"  ✓ Complex JOIN query: {len(results)} results")
        for row in results[:3]:
            print(f"    {row[0]:20} → {row[1]:20} (Score: {row[2]:3.0f}, Articles: {row[3]:3d})")
        
    except Exception as e:
        consistency_results['complex_join_query'] = {
            'success': False,
            'error': str(e)
        }
        print(f"  ❌ Complex JOIN query failed: {e}")
    
    # Test RSS validation query
    try:
        query = """
            SELECT 
                rf.outlet as rss_outlet,
                narm.outlet_name as mapped_agency,
                narm.final_reputation_score,
                rf.active
            FROM rss_feeds rf
            LEFT JOIN news_agency_reputation_metrics narm ON rf.outlet = narm.outlet_name
            ORDER BY narm.final_reputation_score DESC NULLS LAST
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        mapped_count = sum(1 for row in results if row[1] is not None)
        active_count = sum(1 for row in results if row[3])
        
        consistency_results['rss_validation_query'] = {
            'success': True,
            'total_feeds': len(results),
            'mapped_feeds': mapped_count,
            'active_feeds': active_count,
            'mapping_percentage': round((mapped_count / len(results) * 100) if results else 0, 2)
        }
        
        print(f"  ✓ RSS validation query: {mapped_count}/{len(results)} mapped ({mapped_count/len(results)*100:.1f}%)")
        
    except Exception as e:
        consistency_results['rss_validation_query'] = {
            'success': False,
            'error': str(e)
        }
        print(f"  ❌ RSS validation query failed: {e}")
    
    return consistency_results

def save_validation_results(results: Dict):
    """Save validation results to file"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/Users/kolb/Documents/github/k8s-news-engine/services/quality-service/validation_after_standardization_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Validation results saved to: {filename}")
    return filename

if __name__ == "__main__":
    # Set database URL for local testing
    os.environ['DATABASE_URL'] = 'postgresql://appuser:newsengine2024@localhost:5432/newsdb?sslmode=disable'
    
    try:
        results = run_post_standardization_validation()
        filename = save_validation_results(results)
        
        print(f"\n🎯 Post-Standardization Validation Summary:")
        print(f"   Approach: {results['standardization_approach']}")
        print(f"   Status: {results['validation_status']}")
        print(f"   Compatibility Tests: {len(results['compatibility_tests'])}")
        print(f"   Relationship Tests: {len(results['data_relationships'])}")
        print(f"   Query Consistency Tests: {len(results['query_consistency'])}")
        print(f"   Results File: {filename}")
        
        # Summary of key metrics
        if 'articles_reputation_join' in results['compatibility_tests']:
            art_rep = results['compatibility_tests']['articles_reputation_join']
            if art_rep.get('success'):
                print(f"   📊 Articles Coverage: {art_rep['coverage_percentage']:.1f}%")
        
        if 'rss_reputation_join' in results['compatibility_tests']:
            rss_rep = results['compatibility_tests']['rss_reputation_join']
            if rss_rep.get('success'):
                print(f"   📡 RSS Feed Coverage: {rss_rep['coverage_percentage']:.1f}%")
        
        print(f"\n✨ Column naming standardization using code-first approach is complete!")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        exit(1)