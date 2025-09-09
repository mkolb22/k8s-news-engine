#!/usr/bin/env python3
import cgi, cgitb, os, sys, json
import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict
import re
import hashlib
cgitb.enable()

def get_db_connection():
    """Get database connection from environment"""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
    return psycopg2.connect(db_url)

def extract_keywords_from_title(title):
    """Extract significant keywords from article title for event grouping"""
    if not title:
        return set()
    
    # Focus on title-based keywords for better event detection
    title = title.lower()
    words = re.findall(r'\b[a-z]{3,}\b', title)
    
    # Enhanced stop words list with focus on keeping important news terms
    stop_words = {'the', 'and', 'for', 'are', 'with', 'they', 'this', 'that', 'from', 'has', 'had', 'was', 'were', 'been', 'have', 'will', 'said', 'says', 'about', 'after', 'all', 'also', 'any', 'can', 'could', 'did', 'does', 'each', 'get', 'got', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'she', 'use', 'her', 'him', 'his', 'out', 'day', 'man', 'oil', 'sit', 'set', 'run', 'eat', 'far', 'sea', 'eye', 'ask', 'own', 'more', 'over', 'back', 'come', 'call', 'work', 'down', 'well', 'just', 'good', 'make', 'take', 'time', 'year', 'most', 'some', 'then', 'only', 'know', 'than', 'find', 'look', 'first', 'right', 'think', 'like', 'give', 'want', 'last', 'long', 'great'}
    
    # Keep important geographical, political, and news-worthy terms
    important_terms = {'ukraine', 'russia', 'china', 'israel', 'gaza', 'palestinian', 'trump', 'biden', 'election', 'court', 'judge', 'military', 'police', 'attack', 'strike', 'drone', 'missile', 'war', 'peace', 'deal', 'agreement', 'treaty', 'summit', 'meeting', 'visit', 'death', 'dies', 'killed', 'injured', 'fire', 'explosion', 'crash', 'accident', 'storm', 'hurricane', 'earthquake', 'flood', 'climate', 'energy', 'oil', 'gas', 'economy', 'market', 'stock', 'price', 'inflation', 'bank', 'company', 'business', 'technology', 'tech', 'apple', 'google', 'microsoft', 'amazon', 'meta', 'tesla', 'space', 'nasa', 'mars', 'moon', 'satellite'}
    
    keywords = set()
    for word in words:
        if len(word) > 2:  # Allow 3+ character words
            if word in important_terms or (len(word) > 4 and word not in stop_words):
                keywords.add(word)
    
    return keywords

def extract_summary_keywords(summary_text):
    """Extract keywords from RSS feed summary/description for matching"""
    if not summary_text:
        return set()
    
    text = summary_text.lower()
    # Look for sentences or key phrases
    words = re.findall(r'\b[a-z]{4,}\b', text)  # 4+ chars for summary keywords
    
    stop_words = {'this', 'that', 'with', 'from', 'they', 'have', 'will', 'said', 'says', 'about', 'after', 'also', 'been', 'were', 'more', 'than', 'when', 'where', 'what', 'which', 'while', 'would', 'could', 'should', 'their', 'there', 'these', 'those', 'through'}
    
    keywords = set()
    for word in words:
        if word not in stop_words:
            keywords.add(word)
    
    return keywords

def group_articles_by_title_similarity(articles):
    """Group articles by title keyword similarity to create events"""
    groups = []
    
    for article in articles:
        article_id, url, title, published_at, text, outlet = article
        # Focus primarily on title keywords
        title_keywords = extract_keywords_from_title(title)
        # Use text sparingly for context
        summary_keywords = extract_summary_keywords(text[:200] if text else "")  # First 200 chars only
        
        # Combined keywords with title having more weight
        article_keywords = title_keywords.union(summary_keywords)
        
        # Find existing group with similar title-based keywords
        matched_group = None
        best_match_score = 0
        
        for group in groups:
            # Calculate keyword similarity based on existing group articles
            group_title_keywords = set()
            group_summary_keywords = set()
            
            for existing_article in group['articles']:
                existing_title = existing_article[2]
                existing_text = existing_article[4]
                
                group_title_keywords.update(extract_keywords_from_title(existing_title))
                if existing_text:
                    group_summary_keywords.update(extract_summary_keywords(existing_text[:200]))
            
            # Title keyword matching is more important
            title_matches = title_keywords.intersection(group_title_keywords)
            summary_matches = summary_keywords.intersection(group_summary_keywords)
            
            # Score: title matches count double
            match_score = len(title_matches) * 2 + len(summary_matches)
            
            # Require at least 2 title keyword matches OR 1 title + 2 summary matches
            if (len(title_matches) >= 2) or (len(title_matches) >= 1 and len(summary_matches) >= 2):
                if match_score > best_match_score:
                    best_match_score = match_score
                    matched_group = group
        
        if matched_group:
            matched_group['articles'].append(article)
            matched_group['outlets'].add(outlet)
            matched_group['title_keywords'].update(title_keywords)
            matched_group['summary_keywords'].update(summary_keywords)
        else:
            # Create new group
            groups.append({
                'articles': [article],
                'outlets': {outlet},
                'title_keywords': title_keywords,
                'summary_keywords': summary_keywords,
                'keywords': article_keywords  # Keep for backward compatibility
            })
    
    # Filter groups to only those with 2+ different outlets
    multi_source_groups = []
    for group in groups:
        if len(group['outlets']) >= 2:
            multi_source_groups.append(group)
    
    return multi_source_groups

def generate_readable_summary(group):
    """Generate readable cross-verified summary focusing on matching details"""
    articles = group['articles']
    
    # Use the most descriptive title from articles with the most keywords
    title_scores = []
    for article in articles:
        title_keywords = extract_keywords_from_title(article[2])
        common_with_group = title_keywords.intersection(group['title_keywords'])
        title_scores.append((article[2], len(common_with_group), article))
    
    # Sort by keyword relevance and pick the best title
    title_scores.sort(key=lambda x: x[1], reverse=True)
    event_title = title_scores[0][0] if title_scores else "News Event"
    
    # Extract and analyze summaries/descriptions from RSS feeds
    contributing_sources = []
    summary_texts = []
    common_facts = []
    
    for article in articles:
        article_id, url, title, published_at, text, outlet = article
        
        # Use RSS description/summary (usually first 200-300 chars)
        if text:
            rss_summary = text[:300].strip()  # RSS summaries are typically short
            if rss_summary:
                summary_texts.append(rss_summary)
                contributing_sources.append({
                    'outlet': outlet,
                    'url': url,
                    'title': title,
                    'summary': rss_summary
                })
    
    # Find common themes and facts across summaries
    if len(summary_texts) >= 2:
        # Simple approach: find sentences/phrases that appear in multiple summaries
        all_words = []
        for text in summary_texts:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            all_words.extend(words)
        
        # Count word frequency across summaries
        word_count = {}
        for word in all_words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Get most common significant words mentioned in multiple sources
        common_words = [word for word, count in word_count.items() if count >= 2]
        
        # Build readable summary focusing on verified facts
        verified_facts = []
        
        # Look for key patterns and common information
        for text in summary_texts:
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 30:  # Substantial sentences
                    # Check if sentence contains common keywords
                    sentence_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', sentence.lower()))
                    if len(sentence_words.intersection(set(common_words))) >= 2:
                        verified_facts.append(sentence)
        
        # Remove duplicates and create coherent summary
        unique_facts = list(set(verified_facts))
        
        if unique_facts:
            # Take the most informative facts, limit to 3 sentences for readability
            selected_facts = unique_facts[:3]
            summary = ". ".join(selected_facts)
            if not summary.endswith('.'):
                summary += "."
        else:
            # Fallback: create summary from most common themes
            theme_words = [word for word, count in sorted(word_count.items(), key=lambda x: x[1], reverse=True)][:10]
            summary = f"Multiple sources report developments involving {', '.join(theme_words[:5])}. "
            summary += f"This story has been verified across {len(contributing_sources)} different news outlets."
    else:
        summary = f"Single source reporting: {event_title}"
    
    # Ensure readability: proper capitalization and flow
    summary = improve_summary_readability(summary)
    
    # Limit to 500 words while maintaining readability
    words = summary.split()
    if len(words) > 500:
        # Cut at sentence boundary near 500 words
        truncated = " ".join(words[:500])
        last_period = truncated.rfind('.')
        if last_period > 400:  # Keep if we're close to full length
            summary = truncated[:last_period + 1]
        else:
            summary = truncated + "..."
    
    return {
        'title': event_title,
        'summary': summary,
        'sources': contributing_sources,  # Only sources that contributed to the summary
        'outlet_count': len(group['outlets']),
        'verified_facts_count': len(contributing_sources)
    }

def improve_summary_readability(text):
    """Improve summary readability with proper formatting and flow"""
    if not text:
        return text
    
    # Ensure proper sentence capitalization
    sentences = re.split(r'([.!?]+)', text)
    improved_sentences = []
    
    for i, part in enumerate(sentences):
        if i % 2 == 0 and part.strip():  # Sentence content (not punctuation)
            # Capitalize first letter and clean up
            part = part.strip()
            if part:
                part = part[0].upper() + part[1:] if len(part) > 1 else part.upper()
                improved_sentences.append(part)
        elif part.strip():  # Punctuation
            improved_sentences.append(part)
    
    # Join and clean up spacing
    result = ''.join(improved_sentences)
    result = re.sub(r'\s+', ' ', result)  # Remove extra spaces
    result = re.sub(r'\s+([.!?])', r'\1', result)  # Fix spacing before punctuation
    
    return result.strip()

def calculate_eqis_score(group):
    """Calculate simplified EQIS score based on coverage and recency"""
    articles = group['articles']
    
    # Coverage score (number of different outlets)
    coverage_score = min(len(group['outlets']) / 5.0, 1.0)  # Max at 5 outlets
    
    # Recency score (how recent are the articles)
    now = datetime.now()
    recency_scores = []
    
    for article in articles:
        published_at = article[3]
        if published_at:
            if isinstance(published_at, str):
                # Handle string dates
                continue
            days_old = (now - published_at.replace(tzinfo=None)).days
            recency_score = max(0, 1.0 - (days_old / 7.0))  # Decay over a week
            recency_scores.append(recency_score)
    
    avg_recency = sum(recency_scores) / len(recency_scores) if recency_scores else 0.5
    
    # Coherence score (simplified - based on title similarity)
    coherence_score = 0.7  # Default moderate coherence
    
    # Combine scores using EQIS weights
    weights = {
        'coverage': 0.4,
        'recency': 0.3, 
        'coherence': 0.3
    }
    
    eqis = (coverage_score * weights['coverage'] + 
            avg_recency * weights['recency'] + 
            coherence_score * weights['coherence'])
    
    return round(eqis * 100, 1)  # Return as percentage

def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        if isinstance(dt, str):
            return dt
        return dt.strftime('%Y-%m-%d %H:%M')
    return 'N/A'

def main():
    print("Content-Type: text/html\n")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get recent articles from the last 7 days
        cur.execute("""
            SELECT id, url, title, published_at, text, outlet
            FROM articles 
            WHERE published_at > NOW() - INTERVAL '7 days'
            ORDER BY published_at DESC 
            LIMIT 100
        """)
        articles = cur.fetchall()
        
        # Group articles into events based on title similarity
        event_groups = group_articles_by_title_similarity(articles)
        
        # Generate readable summaries and scores
        events = []
        for group in event_groups[:10]:  # Show top 10 events
            summary_data = generate_readable_summary(group)
            eqis_score = calculate_eqis_score(group)
            
            events.append({
                'summary': summary_data,
                'eqis_score': eqis_score,
                'article_count': len(group['articles'])
            })
        
        # Sort events by EQIS score
        events.sort(key=lambda x: x['eqis_score'], reverse=True)
        
        cur.close()
        conn.close()
        
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
        .event {{ border-bottom: 2px solid #eee; padding: 20px 0; margin-bottom: 20px; }}
        .event:last-child {{ border-bottom: none; }}
        .event-title {{ font-size: 1.3em; font-weight: bold; color: #2c3e50; margin-bottom: 15px; }}
        .event-summary {{ color: #34495e; margin-bottom: 15px; line-height: 1.6; }}
        .event-sources {{ margin-bottom: 10px; }}
        .source-link {{ display: inline-block; margin: 5px 10px 5px 0; }}
        .source-link a {{ color: #3498db; text-decoration: none; font-weight: bold; }}
        .source-link a:hover {{ text-decoration: underline; }}
        .eqis-score {{ font-weight: bold; padding: 8px 12px; border-radius: 4px; display: inline-block; }}
        .eqis-high {{ background: #27ae60; color: white; }}
        .eqis-medium {{ background: #f39c12; color: white; }}
        .eqis-low {{ background: #e74c3c; color: white; }}
        .event-meta {{ font-size: 0.9em; color: #7f8c8d; margin-bottom: 10px; }}
        .no-data {{ text-align: center; color: #7f8c8d; padding: 40px; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>K8s News Engine - Event Analysis</h1>
        <p>Cross-verified news events with EQIS scoring</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Events Found</h3>
            <div class="number">{len(events)}</div>
        </div>
        <div class="stat-card">
            <h3>Total Articles</h3>
            <div class="number">{len(articles)}</div>
        </div>
        <div class="stat-card">
            <h3>Multi-Source Events</h3>
            <div class="number">{len(event_groups)}</div>
        </div>
    </div>
    
    <div class="events">
        <h2>Cross-Verified News Events</h2>""")
        
        if events:
            for event in events:
                summary = event['summary']
                eqis_score = event['eqis_score']
                
                # Determine EQIS score class
                if eqis_score >= 70:
                    score_class = "eqis-high"
                elif eqis_score >= 40:
                    score_class = "eqis-medium"
                else:
                    score_class = "eqis-low"
                
                print(f"""
        <div class="event">
            <div class="event-title">{summary['title']}</div>
            <div class="event-meta">Verified by {summary['outlet_count']} sources • {event['article_count']} articles</div>
            <div class="event-summary">{summary['summary']}</div>
            <div class="event-sources">
                <strong>Sources:</strong> """)
                
                for source in summary['sources']:
                    print(f"""<span class="source-link"><a href="{source['url']}" target="_blank">{source['outlet']}</a></span>""")
                
                print(f"""
            </div>
            <div class="eqis-score {score_class}">EQIS Score: {eqis_score}%</div>
        </div>""")
        else:
            print("""
        <div class="no-data">
            <h3>No cross-verified events found</h3>
            <p>Events require articles from 2+ different sources on the same topic.</p>
        </div>""")
        
        print("""
    </div>
    
    <div style="margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 0.9em;">
        <p>Event Quality & Impact Score (EQIS) based on coverage, recency, and coherence</p>
        <p>K8s News Engine • Powered by Alpine Linux & Kubernetes</p>
    </div>
</body>
</html>""")
        
    except Exception as e:
        print(f"""<!DOCTYPE html>
<html>
<head>
    <title>K8s News Engine - Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .error {{ background: #e74c3c; color: white; padding: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>Event Analysis Error</h1>
        <p>Could not analyze events from the database.</p>
        <p>Error: {str(e)}</p>
    </div>
</body>
</html>""")

if __name__ == "__main__":
    main()