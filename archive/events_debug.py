#!/usr/bin/env python3
import os, sys, re, traceback
import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict
import json

def get_db_connection():
    """Get database connection from environment"""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
    return psycopg2.connect(db_url)

def extract_core_entities(text):
    """Extract the most important named entities from text"""
    if not text:
        return []
    
    # Extract capitalized proper nouns (people, places, organizations)
    pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
    entities = re.findall(pattern, text[:1000])  # Look at first 1000 chars
    
    # Filter out common non-entities
    non_entities = {'The', 'This', 'That', 'These', 'Those', 'There', 'Here', 'When', 'Where', 
                   'What', 'Who', 'Why', 'How', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
                   'Friday', 'Saturday', 'Sunday', 'January', 'February', 'March', 'April',
                   'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'}
    
    entities = [e for e in entities if e not in non_entities and len(e) > 2]
    
    # Count occurrences and return most frequent
    entity_counts = {}
    for entity in entities:
        entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    # Return entities that appear at least twice or are very specific
    core_entities = []
    for entity, count in entity_counts.items():
        if count >= 2 or (len(entity.split()) >= 2 and count >= 1):
            core_entities.append(entity)
    
    return core_entities[:10]  # Top 10 entities

def main():
    print("Content-Type: text/html\n")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get recent articles
        cur.execute("""
            SELECT id, url, title, outlet_name, published_at, text
            FROM articles 
            WHERE published_at > NOW() - INTERVAL '24 hours'
                AND text IS NOT NULL 
                AND LENGTH(text) > 100
            ORDER BY published_at DESC 
            LIMIT 50
        """)
        articles = cur.fetchall()
        
        cur.close()
        conn.close()
        
        print("""<!DOCTYPE html>
<html>
<head>
    <title>Event Matching Debug</title>
    <meta charset="utf-8">
    <style>
        body { font-family: monospace; margin: 20px; }
        .article { border: 1px solid #ccc; margin: 10px; padding: 10px; }
        .title { font-weight: bold; color: #2c3e50; }
        .entities { color: #27ae60; }
        .outlet { color: #3498db; }
        .mismatch { background: #ffe6e6; }
        .match { background: #e6ffe6; }
    </style>
</head>
<body>
    <h1>Article Entity Analysis</h1>""")
        
        # Analyze each article
        article_data = []
        for article in articles[:20]:  # First 20 articles
            entities = extract_core_entities(article[5])
            article_data.append({
                'title': article[2],
                'outlet': article[3],
                'entities': entities,
                'url': article[1]
            })
        
        # Show analysis
        for i, data in enumerate(article_data):
            print(f"""
    <div class="article">
        <div class="title">{i+1}. {data['title'][:100]}</div>
        <div class="outlet">Outlet: {data['outlet']}</div>
        <div class="entities">Key Entities: {', '.join(data['entities'][:5]) if data['entities'] else 'None found'}</div>
    </div>""")
        
        # Now show which would be grouped
        print("<h2>Grouping Analysis</h2>")
        
        used = set()
        groups = []
        
        for i, article1 in enumerate(article_data):
            if i in used:
                continue
                
            group = [article1]
            used.add(i)
            entities1 = set(article1['entities'])
            
            for j, article2 in enumerate(article_data):
                if j <= i or j in used:
                    continue
                    
                entities2 = set(article2['entities'])
                
                # Check entity overlap
                if entities1 and entities2:
                    overlap = entities1 & entities2
                    if len(overlap) >= 2:  # At least 2 shared entities
                        group.append(article2)
                        used.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        # Display groups
        for g_idx, group in enumerate(groups):
            print(f"<h3>Event Group {g_idx + 1}</h3>")
            shared_entities = set(group[0]['entities'])
            for article in group[1:]:
                shared_entities &= set(article['entities'])
            
            print(f"<p><strong>Shared Entities:</strong> {', '.join(shared_entities) if shared_entities else 'None'}</p>")
            
            for article in group:
                css_class = 'match' if shared_entities else 'mismatch'
                print(f"""
    <div class="article {css_class}">
        <div class="title">{article['title'][:100]}</div>
        <div class="outlet">{article['outlet']}</div>
        <div class="entities">Entities: {', '.join(article['entities'][:5])}</div>
    </div>""")
        
        print("""
</body>
</html>""")
        
    except Exception as e:
        print(f"<h1>Error</h1><pre>{str(e)}</pre>")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Content-Type: text/html\n")
        print(f"""<!DOCTYPE html>
<html>
<head>
    <title>Debug Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .error {{ background: #e74c3c; color: white; padding: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>Debug Error</h1>
        <p>Debug script error:</p>
        <pre>{traceback.format_exc()}</pre>
    </div>
</body>
</html>""")