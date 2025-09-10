#!/usr/bin/env python3
"""
Pre-Migration Validation Script

Validates current database state before standardizing outlet column names.
Creates comprehensive baseline for comparison after migration.
"""

import psycopg2
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

def run_pre_migration_validation() -> Dict:
    """Run comprehensive validation before migration"""
    
    database_url = os.environ.get('DATABASE_URL', 
                                 'postgresql://appuser:newsengine2024@localhost:5432/newsdb?sslmode=disable')
    
    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'database_url': database_url.split('@')[1],  # Hide credentials
        'table_analysis': {},
        'data_integrity': {},
        'cross_table_relationships': {},
        'validation_status': 'UNKNOWN'
    }
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔍 Pre-Migration Validation Starting...")
        print("=" * 60)
        
        # 1. Analyze current table structures
        validation_results['table_analysis'] = analyze_table_structures(cursor)
        
        # 2. Check data integrity
        validation_results['data_integrity'] = check_data_integrity(cursor)
        
        # 3. Verify cross-table relationships
        validation_results['cross_table_relationships'] = check_relationships(cursor)
        
        # 4. Summary and recommendations
        validation_results['validation_status'] = 'COMPLETED'
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Pre-Migration Validation Completed Successfully")
        
        return validation_results
        
    except Exception as e:
        validation_results['validation_status'] = f'FAILED: {str(e)}'
        print(f"❌ Pre-Migration Validation Failed: {e}")
        raise

def analyze_table_structures(cursor) -> Dict:
    """Analyze current table structures for outlet-related columns"""
    
    print("\n📋 Table Structure Analysis:")
    print("-" * 40)
    
    tables_with_outlet = [
        'articles', 'rss_feeds', 'outlet_reputation_scores',
        'news_agency_reputation_metrics', 'outlet_authority'
    ]
    
    table_analysis = {}
    
    for table in tables_with_outlet:
        try:
            # Get table structure
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND column_name LIKE '%outlet%'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            
            table_analysis[table] = {
                'outlet_columns': [
                    {
                        'name': col[0],
                        'type': col[1],
                        'nullable': col[2],
                        'default': col[3]
                    } for col in columns
                ],
                'row_count': row_count,
                'exists': True
            }
            
            print(f"  ✓ {table:30} | {row_count:6d} rows | Columns: {[col[0] for col in columns]}")
            
        except psycopg2.Error as e:
            table_analysis[table] = {
                'outlet_columns': [],
                'row_count': 0,
                'exists': False,
                'error': str(e)
            }
            print(f"  ❌ {table:30} | ERROR: {e}")
    
    return table_analysis

def check_data_integrity(cursor) -> Dict:
    """Check data integrity for outlet-related data"""
    
    print("\n📊 Data Integrity Analysis:")
    print("-" * 40)
    
    integrity_checks = {}
    
    # Check articles table
    try:
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT outlet) FROM articles")
        total_articles, unique_outlets = cursor.fetchone()
        
        cursor.execute("SELECT outlet, COUNT(*) FROM articles GROUP BY outlet ORDER BY COUNT(*) DESC LIMIT 10")
        top_outlets = cursor.fetchall()
        
        integrity_checks['articles'] = {
            'total_rows': total_articles,
            'unique_outlets': unique_outlets,
            'top_outlets': [{'outlet': outlet, 'count': count} for outlet, count in top_outlets],
            'null_outlets': 0  # NOT NULL constraint
        }
        
        print(f"  📰 Articles: {total_articles} total, {unique_outlets} unique outlets")
        
    except Exception as e:
        integrity_checks['articles'] = {'error': str(e)}
        print(f"  ❌ Articles analysis failed: {e}")
    
    # Check rss_feeds table
    try:
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT outlet) FROM rss_feeds")
        total_feeds, unique_outlets = cursor.fetchone()
        
        cursor.execute("SELECT outlet, COUNT(*) FROM rss_feeds GROUP BY outlet ORDER BY COUNT(*) DESC")
        outlet_distribution = cursor.fetchall()
        
        integrity_checks['rss_feeds'] = {
            'total_rows': total_feeds,
            'unique_outlets': unique_outlets,
            'outlet_distribution': [{'outlet': outlet, 'count': count} for outlet, count in outlet_distribution],
            'null_outlets': 0  # NOT NULL constraint
        }
        
        print(f"  📡 RSS Feeds: {total_feeds} total, {unique_outlets} unique outlets")
        
    except Exception as e:
        integrity_checks['rss_feeds'] = {'error': str(e)}
        print(f"  ❌ RSS Feeds analysis failed: {e}")
    
    # Check news agency reputation metrics
    try:
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT outlet_name) FROM news_agency_reputation_metrics")
        total_agencies, unique_names = cursor.fetchone()
        
        cursor.execute("SELECT outlet_name, final_reputation_score FROM news_agency_reputation_metrics ORDER BY final_reputation_score DESC")
        agency_scores = cursor.fetchall()
        
        integrity_checks['news_agency_reputation_metrics'] = {
            'total_rows': total_agencies,
            'unique_outlet_names': unique_names,
            'agency_scores': [{'outlet_name': name, 'score': float(score)} for name, score in agency_scores],
            'null_outlet_names': 0  # NOT NULL constraint
        }
        
        print(f"  🏆 Reputation Metrics: {total_agencies} agencies with scores")
        
    except Exception as e:
        integrity_checks['news_agency_reputation_metrics'] = {'error': str(e)}
        print(f"  ❌ Reputation Metrics analysis failed: {e}")
    
    return integrity_checks

def check_relationships(cursor) -> Dict:
    """Check cross-table relationships and referential integrity"""
    
    print("\n🔗 Cross-Table Relationship Analysis:")
    print("-" * 40)
    
    relationships = {}
    
    # Articles to Reputation Metrics mapping
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_articles,
                COUNT(narm.outlet_name) as articles_with_reputation,
                COUNT(*) - COUNT(narm.outlet_name) as articles_without_reputation
            FROM articles a
            LEFT JOIN news_agency_reputation_metrics narm ON a.outlet = narm.outlet_name
        """)
        
        total, with_rep, without_rep = cursor.fetchone()
        coverage_percent = (with_rep / total * 100) if total > 0 else 0
        
        relationships['articles_to_reputation'] = {
            'total_articles': total,
            'articles_with_reputation': with_rep,
            'articles_without_reputation': without_rep,
            'coverage_percentage': round(coverage_percent, 2)
        }
        
        print(f"  📊 Articles-Reputation: {with_rep}/{total} ({coverage_percent:.1f}%) coverage")
        
    except Exception as e:
        relationships['articles_to_reputation'] = {'error': str(e)}
        print(f"  ❌ Articles-Reputation mapping failed: {e}")
    
    # RSS Feeds to News Agencies mapping
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_feeds,
                COUNT(narm.outlet_name) as feeds_with_reputation,
                COUNT(rf.news_agency_id) as feeds_with_agency_id
            FROM rss_feeds rf
            LEFT JOIN news_agency_reputation_metrics narm ON rf.outlet = narm.outlet_name
        """)
        
        total_feeds, feeds_with_rep, feeds_with_id = cursor.fetchone()
        feed_coverage = (feeds_with_rep / total_feeds * 100) if total_feeds > 0 else 0
        
        relationships['rss_feeds_to_reputation'] = {
            'total_feeds': total_feeds,
            'feeds_with_reputation': feeds_with_rep,
            'feeds_with_agency_id': feeds_with_id,
            'coverage_percentage': round(feed_coverage, 2)
        }
        
        print(f"  📡 RSS-Reputation: {feeds_with_rep}/{total_feeds} ({feed_coverage:.1f}%) coverage")
        
    except Exception as e:
        relationships['rss_feeds_to_reputation'] = {'error': str(e)}
        print(f"  ❌ RSS-Reputation mapping failed: {e}")
    
    # Outlet Authority consistency
    try:
        cursor.execute("SELECT COUNT(*) FROM outlet_authority")
        authority_count = cursor.fetchone()[0]
        
        relationships['outlet_authority'] = {
            'total_entries': authority_count,
            'table_exists': True
        }
        
        print(f"  🏛️  Outlet Authority: {authority_count} entries")
        
    except Exception as e:
        relationships['outlet_authority'] = {
            'total_entries': 0,
            'table_exists': False,
            'error': str(e)
        }
        print(f"  ❌ Outlet Authority check failed: {e}")
    
    return relationships

def save_validation_results(results: Dict):
    """Save validation results to file"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/Users/kolb/Documents/github/k8s-news-engine/services/quality-service/validation_before_migration_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Validation results saved to: {filename}")
    return filename

if __name__ == "__main__":
    # Set database URL for local testing
    os.environ['DATABASE_URL'] = 'postgresql://appuser:newsengine2024@localhost:5432/newsdb?sslmode=disable'
    
    try:
        results = run_pre_migration_validation()
        filename = save_validation_results(results)
        
        print(f"\n🎯 Pre-Migration Validation Summary:")
        print(f"   Database Status: {results['validation_status']}")
        print(f"   Total Tables Analyzed: {len(results['table_analysis'])}")
        print(f"   Integrity Checks: {len(results['data_integrity'])}")
        print(f"   Relationship Checks: {len(results['cross_table_relationships'])}")
        print(f"   Results File: {filename}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        exit(1)