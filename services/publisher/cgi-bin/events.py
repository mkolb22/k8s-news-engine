#!/usr/bin/env python3
import cgi, cgitb, os, sys, re
import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

cgitb.enable()

def get_db_connection():
    """Get database connection from environment"""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
    return psycopg2.connect(db_url)

def clean_text(text):
    """Clean and normalize text for comparison"""
    if not text:
        return ""
    # Remove URLs, image references, metadata
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'Image:.*?(?=\n|$)', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[.*?\]', '', text)  # Remove bracketed metadata
    text = re.sub(r'Photo:.*?(?=\n|$)', '', text, flags=re.MULTILINE)
    text = re.sub(r'Getty Images.*?(?=\n|$)', '', text, flags=re.MULTILINE)
    text = re.sub(r'Reuters.*?(?=\n|$)', '', text, flags=re.MULTILINE)
    text = re.sub(r'AP Photo.*?(?=\n|$)', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_keywords(title):
    """Extract meaningful keywords from article title"""
    try:
        # Initialize NLTK components (fallback if not available)
        try:
            stop_words = set(stopwords.words('english'))
        except:
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        
        # Clean and tokenize title
        title_clean = re.sub(r'[^\w\s]', ' ', title.lower())
        words = title_clean.split()
        
        # Filter meaningful keywords
        keywords = [word for word in words 
                   if len(word) > 2 and 
                   word not in stop_words and 
                   not word.isdigit()]
        
        return keywords[:8]  # Limit to top 8 keywords
    except Exception:
        # Fallback simple extraction
        words = re.findall(r'\b[A-Za-z]{3,}\b', title.lower())
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        return [w for w in words if w not in common_words][:8]

def calculate_title_similarity(title1, title2):
    """Calculate similarity between two titles using keyword overlap"""
    keywords1 = set(extract_keywords(title1))
    keywords2 = set(extract_keywords(title2))
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    # Jaccard similarity
    return len(intersection) / len(union) if union else 0.0

def calculate_content_similarity(text1, text2):
    """Calculate similarity between article content using TF-IDF"""
    try:
        if not text1 or not text2:
            return 0.0
        
        # Clean texts
        clean_text1 = clean_text(text1)
        clean_text2 = clean_text(text2)
        
        if len(clean_text1) < 50 or len(clean_text2) < 50:
            return 0.0
        
        # Use TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform([clean_text1, clean_text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            # Fallback to simple word overlap
            words1 = set(clean_text1.lower().split())
            words2 = set(clean_text2.lower().split())
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0
            
    except Exception:
        return 0.0

def group_articles_into_events(articles):
    """Group related articles into events using similarity matching"""
    events = []
    used_articles = set()
    
    for i, article1 in enumerate(articles):
        if i in used_articles:
            continue
            
        # Start a new event with this article
        event_articles = [article1]
        used_articles.add(i)
        
        # Find similar articles
        for j, article2 in enumerate(articles):
            if j <= i or j in used_articles:
                continue
                
            # Calculate similarities
            title_sim = calculate_title_similarity(article1[2], article2[2])  # title
            content_sim = calculate_content_similarity(article1[5], article2[5])  # text
            
            # Thresholds for grouping
            if title_sim > 0.3 or content_sim > 0.6:
                event_articles.append(article2)
                used_articles.add(j)
        
        if len(event_articles) >= 1:  # Include single articles as events
            events.append(event_articles)
    
    return events

def generate_event_summary(event_articles):
    """Generate a cleaned summary for an event from multiple articles"""
    if not event_articles:
        return ""
    
    # Get the longest, most detailed article
    best_article = max(event_articles, key=lambda x: len(x[5]) if x[5] else 0)
    
    summary = clean_text(best_article[5])
    
    # Limit length and clean up
    sentences = summary.split('. ')
    if len(sentences) > 3:
        summary = '. '.join(sentences[:3]) + '.'
    
    # Ensure reasonable length
    if len(summary) > 500:
        summary = summary[:497] + '...'
    
    return summary

def calculate_eqis_score(event_articles):
    """Calculate Event Quality & Impact Score (EQIS) for an event"""
    if not event_articles:
        return 0.0
    
    # Coverage Score (0-30): Number of independent outlets
    outlets = set(article[3] for article in event_articles)  # outlet
    coverage_score = min(len(outlets) * 6, 30)
    
    # Coherence Score (0-25): Average content similarity
    if len(event_articles) > 1:
        similarities = []
        for i in range(len(event_articles)):
            for j in range(i+1, len(event_articles)):
                sim = calculate_content_similarity(event_articles[i][5], event_articles[j][5])
                similarities.append(sim)
        coherence_score = (sum(similarities) / len(similarities)) * 25 if similarities else 15
    else:
        coherence_score = 15  # Default for single article
    
    # Recency Score (0-20): Based on publication time
    now = datetime.now()
    if event_articles[0][4]:  # published_at
        hours_ago = (now - event_articles[0][4]).total_seconds() / 3600
        if hours_ago <= 2:
            recency_score = 20
        elif hours_ago <= 12:
            recency_score = 15
        elif hours_ago <= 24:
            recency_score = 10
        else:
            recency_score = 5
    else:
        recency_score = 10
    
    # Authority Score (0-15): Based on outlet reputation
    authority_outlets = {
        'BBC News', 'BBC World', 'Reuters', 'Associated Press', 'AP News',
        'The Guardian', 'The New York Times', 'The Washington Post', 'CNN',
        'Al Jazeera', 'Deutsche Welle'
    }
    
    has_authority = any(article[3] in authority_outlets for article in event_articles)
    authority_score = 15 if has_authority else 8
    
    # Diversity Score (0-10): Outlet diversity
    diversity_score = min(len(outlets) * 2, 10)
    
    total_score = coverage_score + coherence_score + recency_score + authority_score + diversity_score
    return min(total_score, 100)

def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M')
    return 'N/A'

def main():
    print("Content-Type: text/html\n")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get recent articles
        cur.execute("""
            SELECT id, url, title, outlet, published_at, text, raw_html
            FROM articles 
            WHERE published_at > NOW() - INTERVAL '24 hours'
            ORDER BY published_at DESC 
            LIMIT 200
        """)
        articles = cur.fetchall()
        
        # Get total counts
        cur.execute("SELECT COUNT(*) FROM events")
        event_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM articles")
        article_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        # Group articles into events
        events = group_articles_into_events(articles)
        
        # Sort events by EQIS score
        events_with_scores = []
        for event_articles in events:
            eqis_score = calculate_eqis_score(event_articles)
            events_with_scores.append((eqis_score, event_articles))
        
        events_with_scores.sort(key=lambda x: x[0], reverse=True)
        
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
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>K8s News Engine - Event Analysis</h1>
        <p>AI-powered event detection and truth analysis with EQIS scoring</p>
        <div style="margin-top: 15px;">
            <a href="/cgi-bin/index.py" style="color: #ecf0f1; margin-right: 20px; text-decoration: none;">📰 All Articles</a>
            <a href="/cgi-bin/events.py" style="color: #ecf0f1; text-decoration: none;">🎯 Event Analysis</a>
        </div>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Detected Events</h3>
            <div class="number">{len(events)}</div>
        </div>
        <div class="stat-card">
            <h3>Source Articles</h3>
            <div class="number">{len(articles)}</div>
        </div>
        <div class="stat-card">
            <h3>Coverage Period</h3>
            <div style="color: #27ae60; font-weight: bold;">24 Hours</div>
        </div>
    </div>
    
    <div class="events">
        <h2>Recent Events by EQIS Score</h2>""")
        
        if events_with_scores:
            for eqis_score, event_articles in events_with_scores[:20]:  # Top 20 events
                # Get representative title (most common keywords)
                titles = [article[2] for article in event_articles]
                representative_title = max(titles, key=len)
                
                # Generate summary
                summary = generate_event_summary(event_articles)
                
                # Determine score class
                score_class = "score-excellent" if eqis_score >= 80 else "score-good" if eqis_score >= 60 else "score-fair"
                
                print(f"""
        <div class="event">
            <div class="event-title">{representative_title}</div>
            <div class="event-summary">{summary}</div>
            <div class="event-articles">
                <h4>Source Articles ({len(event_articles)}):</h4>""")
                
                for article in event_articles:
                    outlet = article[3] if article[3] else 'Unknown Source'
                    url = article[1] if article[1] else '#'
                    title = article[2] if article[2] else 'No title'
                    print(f'                <a href="{url}" target="_blank" class="article-link">• {outlet}: {title[:80]}{"..." if len(title) > 80 else ""}</a>')
                
                print(f"""
            </div>
            <div class="meta-info">
                <span class="eqis-score {score_class}">EQIS Score: {eqis_score:.1f}/100</span>
                <span style="margin-left: 15px;">Coverage: {len(set(article[3] for article in event_articles))} outlets</span>
                <span style="margin-left: 15px;">Latest: {format_datetime(max(article[4] for article in event_articles if article[4]))}</span>
            </div>
        </div>""")
        else:
            print("""
        <div class="no-events">
            <h3>No events detected in the last 24 hours</h3>
            <p>The system will analyze articles and group them into events as they are collected.</p>
        </div>""")
        
        print("""
    </div>
    
    <div style="margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 0.9em;">
        <p>Event Quality & Impact Score (EQIS) combines coverage, coherence, recency, authority, and diversity metrics</p>
        <p>K8s News Engine • Powered by AI Event Detection</p>
    </div>
</body>
</html>""")
        
    except Exception as e:
        print(f"""<!DOCTYPE html>
<html>
<head>
    <title>K8s News Engine - Event Analysis Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .error {{ background: #e74c3c; color: white; padding: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>Event Analysis Error</h1>
        <p>Could not process event analysis. The system may still be starting up.</p>
        <p>Error: {str(e)}</p>
        <p><a href="/cgi-bin/index.py" style="color: #ecf0f1;">← Back to Articles</a></p>
    </div>
</body>
</html>""")

if __name__ == "__main__":
    main()