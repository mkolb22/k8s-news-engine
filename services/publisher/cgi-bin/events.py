#!/usr/bin/env python3
import os, sys, re, traceback
import psycopg2
import psycopg2.tz
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def ensure_timezone_aware(dt):
    """Ensure datetime is timezone aware - enhanced with better error handling"""
    if dt is None:
        return datetime.now(timezone.utc)
    
    # Handle timezone-naive datetime objects
    if dt.tzinfo is None:
        # Assume UTC for database datetimes
        return dt.replace(tzinfo=timezone.utc)
    
    # Handle timezone-aware datetime objects
    if dt.tzinfo is not None:
        # Convert to UTC if not already
        return dt.astimezone(timezone.utc) if dt.tzinfo != timezone.utc else dt
    
    return dt

def get_db_connection():
    """Get database connection with timezone configuration"""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
    
    # Create connection with timezone configuration
    conn = psycopg2.connect(db_url)
    
    # Set timezone to UTC for this connection
    with conn.cursor() as cur:
        cur.execute("SET timezone = 'UTC'")
        conn.commit()
    
    return conn

def clean_text(text, aggressive=True):
    """Clean text removing metadata while preserving readability"""
    if not text:
        return ""
    
    # Remove HTML entities and tags
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove URLs and web references
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    
    # Remove media references and captions
    text = re.sub(r'(?:Image|Photo|Picture|Photograph|Video|WATCH|Getty|Reuters|AP|AFP|EPA|BBC|CNN)[^.]*?\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[.*?\]', '', text)  # Remove bracketed content
    text = re.sub(r'\((?:Reuters|AP|AFP|Getty|Bloomberg)[^)]*\)', '', text, flags=re.IGNORECASE)
    
    # Remove metadata patterns at the beginning
    text = re.sub(r'^[^.!?]*?(?:Reuters|AP|AFP|Associated Press|By\s+\w+)[^.!?]*?[-–—]\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\w+\s*,\s*\w+\s*[-–—]\s*', '', text)  # Location, Country - 
    
    # Remove timestamps and date references
    text = re.sub(r'\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm|UTC|GMT))?', '', text)
    text = re.sub(r'\b\d{1,2}\s+(?:hours?|minutes?|days?|weeks?)\s+ago\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:Published On|Updated|Posted)\s+\d+\s+\w+\s+\d{4}', '', text, flags=re.IGNORECASE)
    
    # Remove byline patterns
    text = re.sub(r'^By\s+[A-Z][^.]+?(?=\s[A-Z][a-z]|\s+The|\s+A)', '', text, flags=re.MULTILINE)
    text = re.sub(r'By\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s*', '', text)
    
    # Remove social/sharing text
    text = re.sub(r'(?:Share|Follow|Subscribe|Comment|Like|Tweet|Post|Download|Watch|Listen|Read more|Click here|Advertisement|Sponsored)[^.]*?\.', '', text, flags=re.IGNORECASE)
    
    # Clean up spacing and normalize
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

def extract_entities_regex(text):
    """Extract named entities using regex patterns and NLTK"""
    if not text:
        return {'PERSON': [], 'ORG': [], 'GPE': [], 'LOC': []}
    
    entities = defaultdict(set)
    
    # Clean text first
    text = clean_text(text)
    
    # Extract potential person names (capitalized consecutive words)
    person_pattern = r'\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)\b'
    for match in re.finditer(person_pattern, text):
        name = match.group(1)
        # Filter out common non-names
        if not any(word in name.lower() for word in ['the', 'and', 'or', 'but', 'for']):
            entities['PERSON'].add(name.lower())
    
    # Extract organizations (words ending in common org suffixes)
    org_pattern = r'\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Inc|Corp|LLC|Ltd|Company|Organization|Department|Ministry|Agency|Commission|Committee|Council|Board|Authority|University|College|Institute|Hospital|Center|Bank|Group|Association|Federation|Union|Party|Court|Office|Bureau|Service|Force|Army|Navy|Police|NATO|UN|EU|WHO|IMF|FBI|CIA|NSA|FDA|CDC|FEMA|NASA))\b)'
    for match in re.finditer(org_pattern, text):
        entities['ORG'].add(match.group(1).lower())
    
    # Extract countries and cities (maintain a basic list)
    locations = {
        'countries': ['united states', 'america', 'china', 'russia', 'ukraine', 'israel', 'palestine', 'gaza', 'iran', 'iraq', 'syria', 'lebanon', 'egypt', 'saudi arabia', 'india', 'pakistan', 'afghanistan', 'france', 'germany', 'uk', 'britain', 'italy', 'spain', 'canada', 'mexico', 'brazil', 'japan', 'australia', 'turkey', 'poland', 'sweden', 'norway', 'finland'],
        'cities': ['washington', 'new york', 'los angeles', 'chicago', 'london', 'paris', 'berlin', 'moscow', 'beijing', 'shanghai', 'tokyo', 'kyiv', 'kiev', 'jerusalem', 'tel aviv', 'gaza city', 'damascus', 'baghdad', 'tehran', 'mumbai', 'delhi', 'cairo', 'istanbul', 'rome', 'madrid', 'toronto', 'sydney', 'melbourne']
    }
    
    text_lower = text.lower()
    for country in locations['countries']:
        if country in text_lower:
            entities['GPE'].add(country)
    
    for city in locations['cities']:
        if city in text_lower:
            entities['LOC'].add(city)
    
    # Extract quoted entities (often important names/terms)
    quote_pattern = r'["\']([^"\']*?)["\']'
    for match in re.finditer(quote_pattern, text):
        quoted = match.group(1)
        if 2 < len(quoted) < 50:  # Reasonable length for entity
            # Determine type based on context
            if any(word in quoted.lower() for word in ['said', 'told', 'stated']):
                continue  # Skip quotes that are speech
            elif quoted[0].isupper():
                entities['PERSON'].add(quoted.lower())
    
    return {k: list(v) for k, v in entities.items()}

def calculate_entity_overlap(entities1, entities2):
    """Calculate entity overlap score between two sets of entities"""
    if not entities1 or not entities2:
        return 0.0
    
    score = 0.0
    weights = {'PERSON': 0.3, 'ORG': 0.25, 'GPE': 0.2, 'LOC': 0.15, 'EVENT': 0.1}
    
    for entity_type, weight in weights.items():
        set1 = set(entities1.get(entity_type, []))
        set2 = set(entities2.get(entity_type, []))
        
        if set1 and set2:
            overlap = len(set1.intersection(set2))
            total = len(set1.union(set2))
            if total > 0:
                score += weight * (overlap / total)
    
    return score

def calculate_enhanced_content_similarity(text1, text2):
    """Enhanced content similarity using bi-gram TF-IDF and key phrase matching"""
    if not text1 or not text2:
        return 0.0
    
    # Clean texts
    clean_text1 = clean_text(text1)
    clean_text2 = clean_text(text2)
    
    if len(clean_text1) < 50 or len(clean_text2) < 50:
        return 0.0
    
    try:
        # Use bi-gram TF-IDF for better phrase matching
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 3),  # Unigrams, bigrams, and trigrams
            min_df=1
        )
        
        tfidf_matrix = vectorizer.fit_transform([clean_text1[:2000], clean_text2[:2000]])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # Boost score if key phrases match
        # Extract important phrases (consecutive capitalized words)
        phrase_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        phrases1 = set(re.findall(phrase_pattern, text1))
        phrases2 = set(re.findall(phrase_pattern, text2))
        
        if phrases1 and phrases2:
            phrase_overlap = len(phrases1.intersection(phrases2)) / min(len(phrases1), len(phrases2))
            similarity = similarity * 0.7 + phrase_overlap * 0.3
        
        return min(similarity, 1.0)
    except:
        return 0.0

def temporal_cluster_articles(articles, window_hours=12):
    """Pre-cluster articles by temporal proximity"""
    clusters = []
    
    try:
        # Sort articles by publication time
        sorted_articles = sorted(articles, key=lambda x: ensure_timezone_aware(x[4]))
        
        for article in sorted_articles:
            try:
                article_time = ensure_timezone_aware(article[4])
                
                # Find appropriate cluster or create new one
                placed = False
                for cluster in clusters:
                    try:
                        cluster_time = ensure_timezone_aware(cluster[0][4])
                        time_diff = abs((article_time - cluster_time).total_seconds() / 3600)
                        
                        if time_diff <= window_hours:
                            cluster.append(article)
                            placed = True
                            break
                    except Exception as e:
                        # Log timezone arithmetic error but continue
                        print(f"<!-- Timezone arithmetic error in clustering: {str(e)} -->", file=sys.stderr)
                        continue
                
                if not placed:
                    clusters.append([article])
                    
            except Exception as e:
                print(f"<!-- Error processing article time in clustering: {str(e)} -->", file=sys.stderr)
                # Skip this article and continue
                continue
        
        return clusters
        
    except Exception as e:
        print(f"<!-- Critical error in temporal clustering: {str(e)} -->", file=sys.stderr)
        # Return empty clusters to prevent complete failure
        return []

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

def verify_event_coherence(event_articles):
    """Post-process verification that all articles truly cover the same event"""
    if len(event_articles) <= 1:
        return event_articles
    
    # Extract entities from all articles
    all_entities = []
    for article in event_articles:
        entities = extract_key_entities(article[5])
        all_entities.append(entities)
    
    # Find core shared entities (must appear in at least half the articles)
    entity_counts = {}
    for entities in all_entities:
        for entity in entities:
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    min_appearances = max(2, len(event_articles) // 2)
    core_entities = {e for e, c in entity_counts.items() if c >= min_appearances}
    
    if not core_entities:
        # No shared entities - likely mismatched articles
        # Return only the first article as a single event
        return [event_articles[0]]
    
    # Verify each article shares core entities
    verified_articles = []
    for i, article in enumerate(event_articles):
        article_entities = all_entities[i]
        if article_entities & core_entities:  # Has at least one core entity
            verified_articles.append(article)
    
    return verified_articles if len(verified_articles) > 1 else []

def group_articles_into_events(articles):
    """High-precision event matching with post-verification and duplicate prevention"""
    events = []
    used_indices = set()
    
    for i, article1 in enumerate(articles):
        if i in used_indices:
            continue
        
        event_articles = [article1]
        used_indices.add(i)
        
        # Extract key information from article1
        title1 = article1[2].lower() if article1[2] else ""
        text1 = article1[5][:2000] if article1[5] else ""
        outlet1 = article1[3]
        time1 = ensure_timezone_aware(article1[4])
        entities1 = extract_key_entities(text1)
        
        # Extract title keywords
        title1_words = set(re.findall(r'\b[a-z]{3,}\b', title1))
        common = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
                 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
                 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did',
                 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'said', 'says', 'will'}
        title1_words = title1_words - common
        
        for j, article2 in enumerate(articles):
            # CRITICAL FIX: Check if article2 is already used in ANY capacity
            if j <= i or j in used_indices:
                continue
            
            # Don't group articles from same outlet
            if article2[3] == outlet1:
                continue
            
            # Additional safety check: ensure this isn't the same article by ID or URL
            if article1[0] == article2[0] or (article1[1] and article2[1] and article1[1] == article2[1]):
                continue
            
            title2 = article2[2].lower() if article2[2] else ""
            text2 = article2[5][:2000] if article2[5] else ""
            time2 = ensure_timezone_aware(article2[4])
            entities2 = extract_key_entities(text2)
            
            # Time check - must be within 24 hours
            if time1 and time2:
                time_diff = abs((time1 - time2).total_seconds() / 3600)
                if time_diff > 24:
                    continue
            
            # Must share significant entities (at least 4 AND 50% of smaller set)
            if entities1 and entities2:
                shared_entities = entities1 & entities2
                min_entities = min(len(entities1), len(entities2))
                
                # Much stricter requirements to prevent mismatches
                if len(shared_entities) < 4 or len(shared_entities) < min_entities * 0.5:
                    continue
            else:
                # If no entities extracted, skip
                continue
            
            # Title keywords must also overlap
            title2_words = set(re.findall(r'\b[a-z]{3,}\b', title2))
            title2_words = title2_words - common
            
            if title1_words and title2_words:
                title_overlap = len(title1_words & title2_words)
                if title_overlap < 3:  # At least 3 shared keywords
                    continue
            
            # If all checks pass, add to event and mark as used
            event_articles.append(article2)
            used_indices.add(j)  # CRITICAL FIX: Mark as used immediately
        
        # Verify coherence of grouped articles
        verified_articles = verify_event_coherence(event_articles)
        
        if len(verified_articles) > 1:
            events.append(verified_articles)
    
    return events

def generate_event_summary(event_articles):
    """Generate a clean, grammatical summary from the best article"""
    if not event_articles:
        return "No summary available."
    
    # Prefer articles from authoritative sources
    priority_outlets = ['Reuters', 'Associated Press', 'BBC News', 'BBC World', 'AP News', 'The Guardian', 'The New York Times', 'CNN', 'Al Jazeera', 'Deutsche Welle', 'NPR News']
    
    # Sort articles by priority and content quality
    sorted_articles = sorted(event_articles, 
                           key=lambda x: (x[3] in priority_outlets, len(x[5]) if x[5] else 0), 
                           reverse=True)
    
    for article in sorted_articles:
        text = article[5]
        if not text or len(text) < 100:
            continue
            
        # Clean the text while preserving sentence structure
        cleaned_text = clean_text(text)
        
        if not cleaned_text or len(cleaned_text) < 50:
            continue
        
        # Extract complete sentences with proper grammar
        sentences = extract_complete_sentences(cleaned_text)
        
        if sentences:
            # Select best sentences for summary
            summary_sentences = select_summary_sentences(sentences, article[2])  # Pass title for context
            
            if summary_sentences:
                final_summary = ' '.join(summary_sentences)
                
                # Clean up any remaining issues
                final_summary = fix_grammar_issues(final_summary)
                
                # Length check and truncation
                if len(final_summary) > 400:
                    final_summary = truncate_at_sentence_boundary(final_summary, 400)
                
                return final_summary
    
    # Fallback: Generate summary from titles if content is unavailable
    return generate_title_based_summary(event_articles)

def extract_complete_sentences(text):
    """Extract grammatically complete sentences"""
    # Split by sentence endings
    potential_sentences = re.split(r'[.!?]+', text)
    complete_sentences = []
    
    for sentence in potential_sentences:
        sentence = sentence.strip()
        
        # Skip if too short or doesn't look like a complete sentence
        if len(sentence) < 20:
            continue
            
        # Ensure sentence starts with capital letter
        if sentence and not sentence[0].isupper():
            sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
        
        # Check for basic sentence structure (subject + verb indicators)
        if has_sentence_structure(sentence):
            complete_sentences.append(sentence + '.')
        
        # Limit to prevent excessive processing
        if len(complete_sentences) >= 5:
            break
    
    return complete_sentences

def has_sentence_structure(sentence):
    """Check if sentence has basic grammatical structure"""
    sentence_lower = sentence.lower()
    
    # Must contain a verb indicator
    verb_indicators = [' is ', ' are ', ' was ', ' were ', ' has ', ' have ', ' will ', ' would ', 
                      ' said ', ' says ', ' told ', ' announced ', ' reported ', ' confirmed ',
                      ' killed ', ' died ', ' injured ', ' struck ', ' attacked ', ' launched ',
                      ' ordered ', ' decided ', ' voted ', ' approved ', ' rejected ']
    
    has_verb = any(indicator in sentence_lower for indicator in verb_indicators)
    
    # Should not start with conjunctions or fragments
    fragment_starts = ['and ', 'but ', 'or ', 'so ', 'however ', 'meanwhile ', 'also ', 'this ']
    starts_properly = not any(sentence_lower.startswith(start) for start in fragment_starts)
    
    return has_verb and starts_properly

def select_summary_sentences(sentences, title):
    """Select the most relevant sentences for the summary"""
    if not sentences:
        return []
    
    # Extract key terms from title for relevance scoring
    title_words = set(re.findall(r'\b\w{3,}\b', title.lower()))
    
    scored_sentences = []
    for sentence in sentences:
        # Score based on relevance to title and sentence quality
        sentence_words = set(re.findall(r'\b\w{3,}\b', sentence.lower()))
        relevance_score = len(title_words & sentence_words)
        
        # Prefer sentences that aren't too long or too short
        length_score = 1.0 if 50 <= len(sentence) <= 200 else 0.5
        
        total_score = relevance_score * length_score
        scored_sentences.append((sentence, total_score))
    
    # Sort by score and return top 2 sentences
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    return [sent[0] for sent in scored_sentences[:2]]

def fix_grammar_issues(text):
    """Fix common grammar and formatting issues"""
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.!?])', r'\1', text)
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common article issues
    text = re.sub(r'\ba\s+([aeiouAEIOU])', r'an \1', text)
    
    # Remove trailing periods before adding final period
    text = re.sub(r'\.+$', '.', text)
    
    return text.strip()

def truncate_at_sentence_boundary(text, max_length):
    """Truncate text at sentence boundary near max_length"""
    if len(text) <= max_length:
        return text
    
    # Find last sentence boundary before max_length
    truncate_point = text.rfind('.', 0, max_length)
    if truncate_point > max_length * 0.7:  # Don't truncate too aggressively
        return text[:truncate_point + 1]
    else:
        return text[:max_length - 3] + '...'

def generate_title_based_summary(event_articles):
    """Generate summary from article titles when content is unavailable"""
    if not event_articles:
        return "No summary available."
    
    # Get the most descriptive title
    titles = [article[2] for article in event_articles if article[2]]
    
    if not titles:
        return "Summary unavailable."
    
    # Find the longest, most descriptive title
    best_title = max(titles, key=len)
    
    # Clean and format as a summary
    summary = re.sub(r'[^\w\s.,!?-]', ' ', best_title)  # Remove special chars except basic punctuation
    summary = re.sub(r'\s+', ' ', summary).strip()
    
    # Ensure it ends with a period
    if summary and not summary.endswith(('.', '!', '?')):
        summary += '.'
    
    return summary

def calculate_article_quality_score(article):
    """Calculate quality score for an article based on multiple factors"""
    score = 0.0
    
    # Authority score (0-40): Based on outlet reputation
    authority_outlets = {
        'Reuters': 40, 'Associated Press': 38, 'AP News': 38, 'BBC News': 36, 'BBC World': 36,
        'The Guardian': 34, 'The New York Times': 34, 'The Washington Post': 32, 'CNN': 30,
        'Al Jazeera': 28, 'Deutsche Welle': 26, 'NPR News': 24, 'Zerohedge.com': 20
    }
    outlet = article[3] if article[3] else ''
    score += authority_outlets.get(outlet, 15)  # Default 15 for unknown outlets
    
    # Content quality score (0-25): Based on text length and structure
    text = article[5] if article[5] else ''
    if len(text) > 2000:
        score += 25
    elif len(text) > 1000:
        score += 20
    elif len(text) > 500:
        score += 15
    elif len(text) > 200:
        score += 10
    else:
        score += 5
    
    # Title quality score (0-20): Based on title descriptiveness
    title = article[2] if article[2] else ''
    if len(title) > 100:
        score += 20
    elif len(title) > 60:
        score += 15
    elif len(title) > 30:
        score += 10
    else:
        score += 5
    
    # Recency bonus (0-15): More recent articles get higher scores
    if article[4]:  # published_at
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            pub_time = ensure_timezone_aware(article[4])
            hours_ago = (now - pub_time).total_seconds() / 3600
            
            if hours_ago <= 6:
                score += 15
            elif hours_ago <= 24:
                score += 10
            elif hours_ago <= 48:
                score += 5
            # No bonus for older articles
        except:
            score += 5  # Default if time calculation fails
    
    return min(score, 100)  # Cap at 100

def get_best_article_for_title(event_articles):
    """Select the best written article for title display"""
    if not event_articles:
        return None
    
    # Calculate quality scores for all articles
    scored_articles = []
    for article in event_articles:
        quality_score = calculate_article_quality_score(article)
        scored_articles.append((quality_score, article))
    
    # Sort by quality score (highest first)
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    
    # Return the best article
    return scored_articles[0][1]

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
    try:
        now = datetime.now(timezone.utc)
        if event_articles[0][4]:  # published_at
            first_article_time = ensure_timezone_aware(event_articles[0][4])
            hours_ago = (now - first_article_time).total_seconds() / 3600
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
    except Exception as e:
        print(f"<!-- Timezone error in recency calculation: {str(e)} -->", file=sys.stderr)
        recency_score = 10  # Default score if timezone calculation fails
    
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
            WHERE published_at > NOW() - INTERVAL '72 hours'
                AND text IS NOT NULL 
                AND LENGTH(text) > 100
            ORDER BY published_at DESC 
            LIMIT 300
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
            <div style="color: #27ae60; font-weight: bold;">72 Hours</div></div>
        </div>
    </div>
    
    <div class="events">
        <h2>Recent Events by EQIS Score</h2>""")
        
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
                <h4>Source Articles ({len(event_articles)}):</h4>""")
                
                # Sort articles by quality score for display
                scored_articles = []
                for article in event_articles:
                    quality_score = calculate_article_quality_score(article)
                    scored_articles.append((quality_score, article))
                
                scored_articles.sort(key=lambda x: x[0], reverse=True)
                
                for quality_score, article in scored_articles:
                    outlet = article[3] if article[3] else 'Unknown Source'
                    url = article[1] if article[1] else '#'
                    title = article[2] if article[2] else 'No title'
                    print(f'                <a href="{url}" target="_blank" class="article-link"><span style="background: #e8f5e8; padding: 2px 6px; border-radius: 10px; font-size: 0.7em; margin-right: 5px; color: #2c5f2d;">{quality_score:.0f}</span>• {outlet}: {title[:80]}{"..." if len(title) > 80 else ""}</a>')
                
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
    try:
        main()
    except Exception as e:
        print("Content-Type: text/html\n")
        print(f"""<!DOCTYPE html>
<html>
<head>
    <title>Event Analysis Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .error {{ background: #e74c3c; color: white; padding: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>Event Analysis Error</h1>
        <p>Could not process event analysis:</p>
        <pre>{traceback.format_exc()}</pre>
        <p><a href="/cgi-bin/index.py" style="color: #ecf0f1;">← Back to Articles</a></p>
    </div>
</body>
</html>""")