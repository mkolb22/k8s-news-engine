#!/usr/bin/env python3
"""
Event Analysis CGI Script
Uses pre-computed quality scores and event groupings from quality-service for fast performance
"""
import os
import sys
import traceback
import psycopg2
from datetime import datetime, timezone

def get_db_connection():
    """Get database connection with timezone configuration"""
    db_url = os.environ.get('DATABASE_URL', 
                          'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
    
    try:
        conn = psycopg2.connect(db_url)
        # Set timezone to UTC for this connection
        with conn.cursor() as cur:
            cur.execute("SET timezone = 'UTC'")
            conn.commit()
        return conn
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")

def ensure_timezone_aware(dt):
    """Ensure datetime is timezone aware"""
    if dt is None:
        return datetime.now(timezone.utc)
    
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc) if dt.tzinfo != timezone.utc else dt
    
    return dt

def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M')
    return 'N/A'

def calculate_eqis_score(event_articles):
    """Calculate Event Quality & Impact Score (EQIS) for an event using pre-computed scores"""
    if not event_articles:
        return 0.0
    
    # Coverage Score (0-30): Number of independent outlets
    outlets = set(article[3] for article in event_articles if article[3])
    coverage_score = min(len(outlets) * 6, 30)
    
    # Authority Score (0-20): Based on average quality scores
    quality_scores = [float(article[4]) for article in event_articles if article[4] is not None]
    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        authority_score = min(avg_quality * 0.2, 20)  # Scale to 0-20
    else:
        authority_score = 10
    
    # Recency Score (0-20): Based on publication time
    try:
        now = datetime.now(timezone.utc)
        if event_articles[0][5]:  # published_at
            first_article_time = ensure_timezone_aware(event_articles[0][5])
            hours_ago = (now - first_article_time).total_seconds() / 3600
            if hours_ago <= 2:
                recency_score = 20
            elif hours_ago <= 12:
                recency_score = 15
            elif hours_ago <= 24:
                recency_score = 10
            elif hours_ago <= 48:
                recency_score = 8
            else:
                recency_score = 5
        else:
            recency_score = 10
    except Exception as e:
        print(f"<!-- Timezone error in recency calculation: {str(e)} -->", file=sys.stderr)
        recency_score = 10
    
    # Diversity Score (0-15): Based on outlet diversity and article count
    diversity_score = min(len(outlets) * 3, 15)
    
    # Coherence Score (0-15): Based on event having multiple articles
    coherence_score = 15 if len(event_articles) > 2 else 10
    
    total_score = coverage_score + authority_score + recency_score + diversity_score + coherence_score
    return min(total_score, 100)

def get_events_from_database(use_fallback=False):
    """Get pre-computed events with quality scores from database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get articles - with fallback to non-scored articles if needed
    if use_fallback:
        # Fallback: Get recent articles even without quality scores
        cur.execute("""
            SELECT 
                a.id, a.url, a.title, a.outlet_name, 
                COALESCE(a.quality_score, 50) as quality_score,  -- Default score of 50
                a.published_at, a.text, 
                COALESCE(a.computed_event_id, 0) as computed_event_id  -- Default event_id
            FROM articles a
            WHERE a.published_at > NOW() - INTERVAL '72 hours'
                AND a.text IS NOT NULL 
                AND LENGTH(a.text) > 100
            ORDER BY a.published_at DESC
            LIMIT 300
        """)
    else:
        # Try to get pre-computed quality scores first
        cur.execute("""
            SELECT 
                a.id, a.url, a.title, a.outlet_name, a.quality_score, a.published_at, 
                a.text, a.computed_event_id
            FROM articles a
            WHERE a.published_at > NOW() - INTERVAL '72 hours'
                AND a.quality_score IS NOT NULL 
                AND a.computed_event_id IS NOT NULL
                AND a.text IS NOT NULL 
                AND LENGTH(a.text) > 100
            ORDER BY a.quality_score DESC, a.published_at DESC
            LIMIT 300
        """)
    
    articles = cur.fetchall()
    
    # Get total counts for statistics
    cur.execute("SELECT COUNT(*) FROM events")
    event_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM articles WHERE published_at > NOW() - INTERVAL '72 hours'")
    article_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    # Group articles by computed_event_id or use fallback grouping
    if use_fallback:
        # Use simple grouping when quality service is unavailable
        events = group_articles_fallback(articles)
    else:
        # Group by pre-computed event IDs
        events_dict = {}
        for article in articles:
            event_id = article[7]  # computed_event_id
            if event_id not in events_dict:
                events_dict[event_id] = []
            events_dict[event_id].append(article)
        events = list(events_dict.values())
    
    # Sort events by EQIS score
    events_with_scores = []
    
    for event_articles in events:
        eqis_score = calculate_eqis_score(event_articles)
        events_with_scores.append((eqis_score, event_articles))
    
    events_with_scores.sort(key=lambda x: x[0], reverse=True)
    
    return events_with_scores, len(articles), event_count, article_count

def group_articles_fallback(articles):
    """Simple fallback grouping when quality service is unavailable"""
    import re
    from collections import defaultdict
    
    events = defaultdict(list)
    
    for article in articles:
        # Simple grouping by title similarity
        title = article[2].lower() if article[2] else ""
        
        # Extract key terms from title
        key_terms = set(re.findall(r'\b[a-z]{4,}\b', title))
        common_words = {'that', 'this', 'with', 'from', 'have', 'been', 'will', 'more', 'about', 'after'}
        key_terms = key_terms - common_words
        
        # Create a simple hash for grouping
        if key_terms:
            event_key = frozenset(list(key_terms)[:3])  # Use first 3 key terms
        else:
            event_key = article[0]  # Use article ID as unique event
        
        events[event_key].append(article)
    
    return list(events.values())

def get_best_article_for_title(event_articles):
    """Select the best article for title display (highest quality score)"""
    if not event_articles:
        return None
    
    # Articles are already sorted by quality score
    return max(event_articles, key=lambda x: float(x[4]) if x[4] is not None else 0)

def generate_event_summary(event_articles):
    """Generate summary from the best quality article"""
    if not event_articles:
        return "No summary available."
    
    # Get the highest quality article
    best_article = get_best_article_for_title(event_articles)
    if not best_article or not best_article[6]:  # text field
        return "Summary unavailable."
    
    text = best_article[6]
    
    # Simple summary extraction - first 2 sentences
    sentences = []
    for sentence in text.split('.'):
        sentence = sentence.strip()
        if sentence and len(sentence) > 30:
            if not sentence[0].isupper():
                sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            sentences.append(sentence)
            if len(sentences) >= 2:
                break
    
    if sentences:
        summary = '. '.join(sentences) + '.'
        if len(summary) > 400:
            summary = summary[:397] + '...'
        return summary
    
    # Fallback to title-based summary
    title = best_article[2] if best_article[2] else "Summary unavailable."
    if not title.endswith('.'):
        title += '.'
    return title

def main():
    print("Content-Type: text/html\n")
    
    try:
        # Try to get pre-computed events from database
        events_with_scores, source_articles, event_count, total_articles = get_events_from_database()
        
        # If no pre-computed events, try fallback mode
        if len(events_with_scores) == 0:
            events_with_scores, source_articles, event_count, total_articles = get_events_from_database(use_fallback=True)
        
        print(f"""<!DOCTYPE html>
<html>
<head>
    <title>K8s News Engine - Event Analysis</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; }}
        .stat-card h3 {{ margin: 0 0 10px 0; color: #2c3e50; }}
        .stat-card .number {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        .events {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .event {{ border-bottom: 2px solid #ecf0f1; padding: 20px 0; margin-bottom: 20px; }}
        .event:last-child {{ border-bottom: none; }}
        .event-title {{ font-size: 1.3em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .event-summary {{ color: #34495e; margin-bottom: 15px; line-height: 1.6; }}
        .event-articles {{ margin-bottom: 10px; }}
        .event-articles h4 {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 8px; }}
        .article-link {{ display: block; color: #3498db; text-decoration: none; margin-bottom: 3px; font-size: 0.9em; }}
        .article-link:hover {{ text-decoration: underline; }}
        .eqis-score {{ display: inline-block; background: linear-gradient(45deg, #3498db, #2980b9); color: white; padding: 8px 15px; border-radius: 20px; font-weight: bold; font-size: 0.9em; }}
        .score-excellent {{ background: linear-gradient(45deg, #27ae60, #229954) !important; }}
        .score-good {{ background: linear-gradient(45deg, #f39c12, #e67e22) !important; }}
        .score-fair {{ background: linear-gradient(45deg, #e74c3c, #c0392b) !important; }}
        .meta-info {{ color: #7f8c8d; font-size: 0.8em; margin-top: 10px; }}
        .no-events {{ text-align: center; color: #7f8c8d; padding: 40px; }}
        .optimization-badge {{ background: #27ae60; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7em; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>K8s News Engine - Event Analysis</h1>
        <p>AI-powered event detection powered by quality-service</p>
        <div style="margin-top: 15px;">
            <a href="/cgi-bin/index.py" style="color: #ecf0f1; margin-right: 20px; text-decoration: none;">📰 All Articles</a>
            <a href="/cgi-bin/events_legacy.py" style="color: #ecf0f1; text-decoration: none;">🎯 Event Analysis (Legacy)</a>
        </div>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Detected Events</h3>
            <div class="number">{len(events_with_scores)}</div>
        </div>
        <div class="stat-card">
            <h3>Source Articles</h3>
            <div class="number">{source_articles}</div>
        </div>
        <div class="stat-card">
            <h3>Coverage Period</h3>
            <div style="color: #27ae60; font-weight: bold;">72 Hours</div>
        </div>
        <div class="stat-card">
            <h3>Performance</h3>
            <div style="color: #27ae60; font-weight: bold;">Pre-computed</div>
        </div>
    </div>
    
    <div class="events">
        <h2>Recent Events by EQIS Score (Quality-Service Powered)</h2>""")
        
        if events_with_scores:
            for eqis_score, event_articles in events_with_scores[:20]:  # Top 20 events
                # Get best article for title and source link
                best_article = get_best_article_for_title(event_articles)
                representative_title = best_article[2] if best_article and best_article[2] else "No title available"
                best_source_url = best_article[1] if best_article and best_article[1] else "#"
                best_source_outlet = best_article[3] if best_article and best_article[3] else "Unknown Source"
                
                # Generate summary
                summary = generate_event_summary(event_articles)
                
                # Determine score class
                score_class = "score-excellent" if eqis_score >= 80 else "score-good" if eqis_score >= 60 else "score-fair"
                
                print(f"""
        <div class="event">
            <div class="event-title"><a href="{best_source_url}" target="_blank" style="color: #3498db; text-decoration: none;">[{best_source_outlet}]</a> {representative_title}</div>
            <div class="event-summary">{summary}</div>
            <div class="event-articles">
                <h4>Source Articles ({len(event_articles)}) - Quality Ranked:</h4>""")
                
                # Sort articles by quality score for display (highest first)
                sorted_articles = sorted(event_articles, key=lambda x: float(x[4]) if x[4] is not None else 0, reverse=True)
                
                for article in sorted_articles:
                    outlet = article[3] if article[3] else 'Unknown Source'
                    url = article[1] if article[1] else '#'
                    title = article[2] if article[2] else 'No title'
                    quality_score = float(article[4]) if article[4] is not None else 0
                    print(f'                <a href="{url}" target="_blank" class="article-link"><span style="background: #e8f5e8; padding: 2px 6px; border-radius: 10px; font-size: 0.7em; margin-right: 5px; color: #2c5f2d;">{quality_score:.0f}</span>• {outlet}: {title[:80]}{"..." if len(title) > 80 else ""}</a>')
                
                print(f"""
            </div>
            <div class="meta-info">
                <span class="eqis-score {score_class}">EQIS Score: {eqis_score:.1f}/100</span>
                <span style="margin-left: 15px;">Coverage: {len(set(article[3] for article in event_articles if article[3]))} outlets</span>
                <span style="margin-left: 15px;">Latest: {format_datetime(max(article[5] for article in event_articles if article[5]))}</span>
                <span style="margin-left: 15px; background: #3498db; color: white; padding: 2px 6px; border-radius: 8px; font-size: 0.7em;">Event ID: {event_articles[0][7]}</span>
            </div>
        </div>""")
        else:
            print("""
        <div class="no-events">
            <h3>No pre-computed events available</h3>
            <p>The quality-service may still be processing articles. Check back shortly.</p>
        </div>""")
        
        print("""
    </div>
    
    <div style="margin-top: 30px; padding: 15px; background: #ecf0f1; border-radius: 5px; text-align: center; color: #7f8c8d; font-size: 0.9em;">
        <strong>Performance Notice:</strong> This page uses pre-computed quality scores and event groupings from the Quality Service for optimal performance.
        Event groupings are updated every minute by the background service.
    </div>
</body>
</html>""")
    
    except Exception as e:
        print(f"""
<!DOCTYPE html>
<html>
<head><title>Error - Event Analysis</title></head>
<body>
<h1>Error</h1>
<p>An error occurred while processing the request:</p>
<pre>{str(e)}</pre>
<p><a href="/cgi-bin/events_legacy.py">Try Legacy Event Analysis</a></p>
</body>
</html>""")
        print(f"<!-- Error details: {traceback.format_exc()} -->", file=sys.stderr)

if __name__ == "__main__":
    main()