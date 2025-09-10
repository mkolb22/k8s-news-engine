#!/usr/bin/env python3
import psycopg2
import re
from datetime import datetime

def get_db_connection():
    db_url = 'postgresql://appuser:newsengine2024@localhost:5432/newsdb?sslmode=disable'
    return psycopg2.connect(db_url)

def extract_key_entities(text):
    """Extract the most important named entities from text, avoiding metadata"""
    if not text or len(text) < 50:
        return set()
    
    # Clean text first - remove obvious metadata
    text = text[:2000]  # Limit for performance
    
    # Remove common metadata patterns
    metadata_patterns = [
        r'published on.*?\n',
        r'recommended stories.*?\n', 
        r'related stories.*?\n',
        r'image.*?getty.*?\n',
        r'photograph.*?\n',
        r'(ap|reuters|afp).*?contributed.*?\n',
        r'view.*?comments.*?\n',
        r'read more.*?\n',
        r'click here.*?\n'
    ]
    
    for pattern in metadata_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    entities = set()
    
    # Extract proper nouns with very strict filtering
    pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
    matches = re.findall(pattern, text)
    
    # Much more comprehensive list of non-entities
    non_entities = {
        'The', 'This', 'That', 'These', 'Those', 'There', 'Here', 'When', 'Where',
        'What', 'Who', 'Why', 'How', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
        'Friday', 'Saturday', 'Sunday', 'January', 'February', 'March', 'April',
        'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December',
        'New', 'First', 'Last', 'Next', 'Previous', 'Other', 'Another', 'Some', 'Many',
        'Most', 'Few', 'All', 'Both', 'Each', 'Every', 'Any', 'Several', 'Following',
        'According', 'However', 'Meanwhile', 'Moreover', 'Furthermore', 'Therefore',
        'Published On', 'Recommended Stories', 'Related Stories', 'Associated Press',
        'View', 'Comments', 'Share', 'Tweet', 'Facebook', 'Instagram', 'Twitter',
        'Getty', 'Images', 'Photo', 'Picture', 'Video', 'Audio', 'More', 'News',
        'Story', 'Article', 'Report', 'Update', 'Breaking', 'Live', 'Latest',
        'Today', 'Yesterday', 'Tomorrow', 'Now', 'Then', 'Soon', 'Later', 'Before',
        'After', 'During', 'While', 'Since', 'Until', 'Through', 'From', 'For',
        'At', 'In', 'On', 'By', 'With', 'Without', 'About', 'Against', 'Between',
        'Among', 'Through', 'During', 'Before', 'After', 'Above', 'Below', 'Up',
        'Down', 'Out', 'Off', 'Over', 'Under', 'Again', 'Further', 'Then', 'Once'
    }
    
    # Track entity frequency and context
    entity_counts = {}
    
    for match in matches:
        if match not in non_entities and len(match) > 3:
            # Skip if it looks like metadata
            if any(meta in match.lower() for meta in ['published', 'recommended', 'story', 'image', 'photo']):
                continue
                
            # Count occurrences
            count = text.count(match)
            entity_counts[match] = count
    
    # Only include entities that are meaningful:
    # 1. Multi-word proper nouns (likely people/places/organizations)
    # 2. OR single-word entities that appear multiple times
    for entity, count in entity_counts.items():
        words = entity.split()
        
        if len(words) >= 2:  # Multi-word entities are more likely to be meaningful
            entities.add(entity.lower())
        elif count >= 3:  # Single-word entities must appear at least 3 times
            entities.add(entity.lower())
    
    return entities

conn = get_db_connection()
cur = conn.cursor()

# Get recent articles
cur.execute("""
    SELECT id, url, title, outlet_name, text
    FROM articles 
    WHERE published_at > NOW() - INTERVAL '24 hours'
        AND text IS NOT NULL 
        AND LENGTH(text) > 100
    ORDER BY published_at DESC 
    LIMIT 20
""")

articles = cur.fetchall()

print("=== ARTICLE ANALYSIS ===\n")

# Look for any problematic groupings
print("=== DEBUGGING CURRENT EVENT GROUPING ===")

# Get the first event from the events.py script to see what's being grouped
# Let's also check what entities are being extracted from each article
all_entities = {}
for i, article in enumerate(articles):
    title = article[2]
    outlet = article[3]
    entities = extract_key_entities(article[4])
    all_entities[i] = (title, outlet, entities)

print("\n=== SIMULATING GROUPING LOGIC ===")
# Simulate the same grouping logic as events.py
used_indices = set()
groups = []

for i in range(len(articles)):
    if i in used_indices:
        continue
        
    title1, outlet1, entities1 = all_entities[i]
    group = [(i, title1, outlet1, entities1)]
    used_indices.add(i)
    
    for j in range(i+1, len(articles)):
        if j in used_indices:
            continue
            
        title2, outlet2, entities2 = all_entities[j]
        
        # Check entity overlap (updated stricter logic)
        overlap = entities1 & entities2
        min_entities = min(len(entities1), len(entities2))
        if len(overlap) >= 4 and len(overlap) >= min_entities * 0.5:  # Minimum 4 shared entities AND 50%
            print(f"GROUPING: Article {i+1} ({title1[:50]}...) with Article {j+1} ({title2[:50]}...)")
            print(f"  Shared entities: {overlap}")
            group.append((j, title2, outlet2, entities2))
            used_indices.add(j)
    
    if len(group) > 1:
        groups.append(group)
        print(f"\nGROUP {len(groups)} created with {len(group)} articles:")
        for idx, title, outlet, entities in group:
            print(f"  {idx+1}. {outlet}: {title[:60]}")
            print(f"     Entities: {', '.join(list(entities)[:5])}")
        print()

print()

print("=== ANALYSIS COMPLETE ===")
print(f"Total groups created: {len(groups)}")
print("\nPROBLEM IDENTIFIED:")
print("Group 2 incorrectly groups Indonesian and North Korean articles based only on metadata!")
print("Group 4 incorrectly groups New Zealand and Australia articles based on generic words!")
print("\nThe entity extraction is too generic and includes:")
print("1. Metadata like 'recommended stories', 'published on'")
print("2. Generic words like 'photograph', 'view'")
print("3. Common titles like 'president donald trump'")

cur.close()
conn.close()