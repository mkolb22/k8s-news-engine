#!/usr/bin/env python3
"""
Quality Scoring Microservice
Computes article quality scores and event groupings for optimized publisher performance
"""

import os
import sys
import time
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone, timedelta
import re
import hashlib
from typing import List, Tuple, Dict, Optional, Set
import json
import signal

# Import writing quality analyzer, reputation analyzer, and RSS validation
from writing_quality_analyzer import WritingQualityAnalyzer
from reputation_analyzer import ReputationAnalyzer
from rss_agency_validator import validate_rss_feed_mapping, get_rss_validation_report

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/quality-service.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class QualityService:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL', 
                                   'postgresql://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb?sslmode=disable')
        self.batch_size = int(os.environ.get('BATCH_SIZE', '50'))
        self.sleep_interval = int(os.environ.get('SLEEP_INTERVAL', '60'))  # seconds
        self.running = True
        
        # Authority scores will be loaded from database
        self.authority_outlets = {}
        self.load_authority_scores()
        
        # Initialize writing quality analyzer
        self.writing_analyzer = WritingQualityAnalyzer()
        
        # Initialize reputation analyzer
        self.reputation_analyzer = ReputationAnalyzer()
        self.reputation_analyzer.connect_to_database()
        
        # Log RSS feed to news agency validation summary
        try:
            validation_report = get_rss_validation_report()
            summary = validation_report['summary']
            logger.info(f"RSS Feed Validation Summary: {summary['total_rss_feeds']} feeds, "
                       f"{summary['mapped_to_agencies']} mapped ({summary['mapping_percentage']}%), "
                       f"{summary['with_reputation_scores']} scored ({summary['scoring_percentage']}%)")
            
            if summary['unmapped_feeds'] > 0:
                logger.warning(f"{summary['unmapped_feeds']} RSS feeds have no news agency mapping")
            
            if summary['mapped_but_unscored'] > 0:
                logger.warning(f"{summary['mapped_but_unscored']} RSS feeds mapped to agencies but no reputation scores")
                
        except Exception as e:
            logger.warning(f"Could not generate RSS validation report: {e}")
        
        logger.info(f"Quality Service initialized with {len(self.authority_outlets)} outlet authority scores, writing quality analyzer, and reputation analyzer")

    def get_db_connection(self):
        """Get database connection with timezone configuration"""
        try:
            conn = psycopg2.connect(self.db_url)
            # Set timezone to UTC for this connection
            with conn.cursor() as cur:
                cur.execute("SET timezone = 'UTC'")
                conn.commit()
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def load_authority_scores(self):
        """Load outlet authority scores from database"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT outlet_name, authority_score FROM outlet_authority")
            rows = cur.fetchall()
            
            self.authority_outlets = {}
            for outlet_name, score in rows:
                self.authority_outlets[outlet_name] = score
            
            cur.close()
            conn.close()
            
            logger.info(f"Loaded {len(self.authority_outlets)} authority scores from database")
            
        except Exception as e:
            logger.error(f"Failed to load authority scores from database: {e}")
            # Fallback to default scores if database fails
            self.authority_outlets = {
                'Reuters': 40, 'Associated Press': 38, 'AP News': 38, 'BBC News': 36, 'BBC World': 36,
                'The Guardian': 34, 'The New York Times': 34, 'The Washington Post': 32, 'CNN': 30,
                'Al Jazeera': 28, 'Deutsche Welle': 26, 'NPR News': 24, 'Zerohedge.com': 20,
                'Politico': 22, 'Sky News World': 20, 'ABC News': 25, 'NBC News': 25, 'CBS News': 25,
                'VOA News': 22, 'Democracy Now': 18, 'PBS NewsHour': 28
            }
            logger.warning(f"Using fallback authority scores: {len(self.authority_outlets)} outlets")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise

    def calculate_article_quality_score(self, article: Dict) -> float:
        """Calculate comprehensive quality score using Writing Quality Analysis"""
        try:
            # Get article content
            text = article.get('text', '')
            title = article.get('title', '')
            outlet = article.get('outlet', '')
            
            # Get writing quality scores (0-100)
            writing_scores = self.writing_analyzer.analyze_article(text, title)
            
            # Get outlet reputation score using comprehensive reputation analyzer (0-100 scale)
            # First validate RSS feed has news agency mapping, then get reputation score
            try:
                # Check if RSS feed has proper news agency mapping
                has_agency_score, reputation_score_full, validation_message = validate_rss_feed_mapping(outlet)
                
                if has_agency_score and reputation_score_full > 0:
                    # Use validated agency reputation score
                    outlet_reputation_full = reputation_score_full
                    # Scale down from 0-100 to 0-40 to maintain existing composite scoring balance
                    outlet_reputation = outlet_reputation_full * 0.4
                    logger.debug(f"Using agency reputation score for {outlet}: {outlet_reputation_full}/100 -> {outlet_reputation}/40")
                else:
                    # Log validation issue and fall back to reputation analyzer
                    logger.warning(f"RSS feed validation: {validation_message}")
                    outlet_reputation_full = self.reputation_analyzer.get_outlet_reputation(outlet)
                    outlet_reputation = outlet_reputation_full * 0.4
                    
            except Exception as e:
                logger.warning(f"Reputation system failed for {outlet}, using fallback authority: {e}")
                outlet_reputation = self.authority_outlets.get(outlet, 15)  # Default 15 for unknown outlets
            
            # Calculate composite score: 60% writing quality + 40% outlet reputation
            # This aligns with the quality scoring proposal
            writing_quality_weighted = writing_scores.total_score * 0.6  # Max 60
            reputation_weighted = outlet_reputation  # Max 40 (keeping existing scale)
            
            composite_score = writing_quality_weighted + reputation_weighted
            
            # Add small recency bonus (0-5) to maintain time sensitivity
            if article.get('published_at'):
                try:
                    now = datetime.now(timezone.utc)
                    pub_time = article['published_at']
                    if pub_time.tzinfo is None:
                        pub_time = pub_time.replace(tzinfo=timezone.utc)
                    
                    hours_ago = (now - pub_time).total_seconds() / 3600
                    
                    if hours_ago <= 6:
                        composite_score += 5
                    elif hours_ago <= 24:
                        composite_score += 3
                    elif hours_ago <= 48:
                        composite_score += 1
                    # No bonus for older articles
                except Exception as e:
                    logger.warning(f"Error calculating recency for article {article.get('id')}: {e}")
                    composite_score += 1  # Default if time calculation fails
            
            # Custom rounding: round down at .5 and below, round up at .6 and above
            decimal_part = composite_score - int(composite_score)
            if decimal_part <= 0.5:
                final_score = int(composite_score)  # Round down
            else:
                final_score = int(composite_score) + 1  # Round up
            
            # Log detailed scoring for debugging (first few articles)
            if hasattr(self, '_debug_count') and self._debug_count < 5:
                logger.info(f"Quality scoring breakdown for article {article.get('id')}: "
                           f"Writing={writing_scores.total_score}/100, "
                           f"Outlet={outlet_reputation}/40, "
                           f"Composite={final_score}")
                self._debug_count += 1
            elif not hasattr(self, '_debug_count'):
                self._debug_count = 1
                logger.info(f"Quality scoring breakdown for article {article.get('id')}: "
                           f"Writing={writing_scores.total_score}/100, "
                           f"Outlet={outlet_reputation}/40, "
                           f"Composite={final_score}")
            
            return float(min(final_score, 100))  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error in comprehensive quality analysis for article {article.get('id')}: {e}")
            # Fallback to simple scoring
            outlet = article.get('outlet', '')
            return min(self.authority_outlets.get(outlet, 15) + 35, 100)  # Simple fallback

    def extract_key_entities(self, text: str) -> Set[str]:
        """Extract key entities from article text - matches publisher service algorithm"""
        if not text or len(text) < 50:
            return set()
        
        # Clean text first - remove obvious metadata (same as publisher)
        text = text[:2000]  # Limit for performance
        
        # Temporarily disable metadata patterns to isolate regex issue
        # metadata_patterns = [
        #     r'published on.*?\n',
        #     r'recommended stories.*?\n', 
        #     r'related stories.*?\n',
        #     r'image.*?getty.*?\n',
        #     r'photograph.*?\n',
        #     r'(ap|reuters|afp).*?contributed.*?\n',
        #     r'view.*?comments.*?\n',
        #     r'read more.*?\n',
        #     r'click here.*?\n'
        # ]
        
        # for pattern in metadata_patterns:
        #     try:
        #         text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        #     except Exception as e:
        #         logger.warning(f"Error in metadata pattern '{pattern}': {str(e)}")
        #         continue
        
        entities = set()
        
        # Extract proper nouns (single words only)
        pattern = r'\b([A-Z][a-z]+)\b'
        matches = re.findall(pattern, text)
        
        # Same comprehensive non-entities list as publisher
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
        
        for match in matches:
            if match not in non_entities and len(match) > 3:
                entities.add(match.lower())
        
        return entities

    def extract_ner_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Named Entity Recognition data: Persons, Organizations, Locations, Dates, Others"""
        if not text or len(text) < 50:
            return {
                'persons': [],
                'organizations': [],
                'locations': [],
                'dates': [],
                'others': []
            }
        
        # Clean and limit text for processing
        text = text[:3000]  # Limit for performance
        
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'others': []
        }
        
        try:
            # Extract potential person names (Title + Name pattern)
            person_patterns = [
                r'\b(President|Prime Minister|Minister|CEO|Director|Pope|Doctor|Dr\.?|Mr\.?|Mrs\.?|Ms\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
                r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:said|announced|declared|stated|confirmed)\b',
            ]
            
            for pattern in person_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple):
                        # Handle title + name matches
                        if len(match) == 2 and match[1]:
                            name = match[1].strip()
                            if len(name) > 3 and name not in entities['persons']:
                                entities['persons'].append(name)
                        # Handle direct name matches
                        elif len(match) == 1:
                            name = match[0].strip()
                            if len(name) > 3 and name not in entities['persons']:
                                entities['persons'].append(name)
                    else:
                        name = match.strip()
                        if len(name) > 3 and name not in entities['persons']:
                            entities['persons'].append(name)
            
            # Extract organizations
            org_patterns = [
                r'\b(Catholic Church|Associated Press|Reuters|CNN|BBC|Fox News|ABC News|NBC News|CBS News|Sky News|Guardian|Washington Post|New York Times)\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Corporation|Corp|Company|Co|Inc|Ltd|University|College|Hospital|Department|Ministry|Agency)\b',
                r'\b(NATO|EU|UN|FBI|CIA|NSA|WHO|NASA|IMF|WTO)\b',
            ]
            
            for pattern in org_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    org = match.strip()
                    if len(org) > 2 and org not in entities['organizations']:
                        entities['organizations'].append(org)
            
            # Extract locations
            location_patterns = [
                r'\b(Washington|London|Paris|Berlin|Tokyo|Beijing|Moscow|Rome|Madrid|Amsterdam|Brussels|Geneva|Vienna|Dublin|Stockholm|Copenhagen|Oslo|Helsinki|Warsaw|Prague|Budapest|Zurich|Milan|Naples|Barcelona|Lisbon|Athens|Cairo|Tel Aviv|Dubai|Mumbai|Delhi|Bangkok|Jakarta|Manila|Seoul|Taipei|Hong Kong|Singapore|Sydney|Melbourne|Toronto|Vancouver|Montreal|New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose|Austin|Jacksonville|San Francisco|Columbus|Charlotte|Fort Worth|Detroit|El Paso|Memphis|Seattle|Denver|Washington DC|Boston|Nashville|Baltimore|Oklahoma City|Louisville|Portland|Las Vegas|Milwaukee|Albuquerque|Tucson|Fresno|Sacramento|Long Beach|Kansas City|Mesa|Virginia Beach|Atlanta|Colorado Springs|Raleigh|Omaha|Miami|Oakland|Minneapolis|Tulsa|Cleveland|Wichita|Arlington|New Orleans|Bakersfield|Tampa|Honolulu|Aurora|Anaheim|Santa Ana|St. Louis|Riverside|Corpus Christi|Lexington|Pittsburgh|Anchorage|Stockton|Cincinnati|St. Paul|Toledo|Greensboro|Newark|Plano|Henderson|Lincoln|Buffalo|Jersey City|Chula Vista|Fort Wayne|Orlando|St. Petersburg|Chandler|Laredo|Norfolk|Durham|Madison|Lubbock|Baton Rouge|North Las Vegas|Reno|Hialeah|Chesapeake|Scottsdale|North Hempstead|Fargo|Glendale|Waco|Cary|Savannah|Fremont|Bellevue|Spokane|Wayne|Fontana|Oxnard|Moreno Valley|Huntington Beach|Glendale|Santa Clarita|Grand Rapids|Peoria|Garden Grove|Oceanside|Huntsville|Sioux Falls|Ontario|McKinney|Elk Grove|Pembroke Pines|Salem|Corona|Eugene|Fort Lauderdale|Peoria|Frisco|Denton|Modesto|Pasadena|Plano|Garland|Irving|Richmond|Newport News|Cape Coral|Grand Prairie|Mission Viejo|Downey|Inglewood|Birmingham|Pueblo|Flint|Richmond|Murfreska|Portsmouth|Salinas|Yonkers|Fayetteville|Tuscaloosa|Carrollton|West Valley City|Fullerton|Surprise|Jackson|Thornton|Sunnyvale|Lakewood|Torrance|Pasadena|Syracuse|Naperville|McAllen|Mesquite|Dayton|Savannah|New Haven|Sterling Heights|Escondido|Roseville|Pomona|Alexandria|Orange|Rancho Cucamonga|Santa Rosa|Peoria|Miami Gardens|Manchester|Clarksville|Oceanside|Fort Collins|Lancaster|Palmdale|Salinas|Springfield|Columbus|Hayward|Corona|Paterson|Pasadena|Macon|Kansas City|Hollywood|Topeka|Vallejo|Flint|Lowell|Concord|Charleston|Cedar Rapids|Gainesville|Stamford|Thousand Oaks|Elizabeth|Rockford|Salem|Santa Clara|Hartford|Victorville|Visalia|Olathe|New London|Miami Beach|Norman|Columbia|Fargo|Sioux City|Independence|Provo|Lee\'s Summit|Inglewood|Fairfield|Abilene|Odessa|Tuscaloosa|Ann Arbor|College Station|Pearland|Richardson|League City|Sugar Land|Beaumont|Missouri City|Fort Smith|Amarillo|Grand Prairie|McKinney|Frisco|Denton|Killeen|Midland|Waco|Round Rock|Irving|Arlington|Tyler|Lewisville|Corpus Christi|Pearland|College Station|Pasadena|Houston|Brownsville|Grand Prairie|Richardson|Mesquite|Garland|Irving|Plano|Carrollton|Allen|Frisco|McKinney|The Colony|Flower Mound|Coppell|Southlake|Grapevine|Euless|Bedford|Hurst|North Richland Hills|Watauga|Haltom City|Fort Worth|Arlington|Grand Prairie|Dallas|Richardson|Plano|Garland|Irving|Mesquite|Carrollton|Allen|Frisco|McKinney|Lewisville|Denton|Flower Mound|Highland Village|Double Oak|Bartonville|Copper Canyon|Hickory Creek|Lake Dallas|Shady Shores|Corinth|Denton|Aubrey|Little Elm|Frisco|Prosper|Celina|Plano|Allen|McKinney|Anna|Melissa|Princeton|Farmersville|Nevada|Josephine|Caddo Mills|Greenville|Campbell|Commerce|Sulphur Springs|Paris|Bonham|Leonard|Wolfe City|Celeste|Quinlan|Point|Emory|Alba|Mineola|Quitman|Hawkins|Longview|Marshall|Carthage|DeBerry|Beckville|Tatum|Overton|Arp|Kilgore|Liberty City|Gladewater|White Oak|Clarksville City)', 
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+|[A-Z]{2})\b',  # City, State pattern
                r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "in Location"
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple):
                        for part in match:
                            if part and len(part) > 2 and part not in entities['locations']:
                                entities['locations'].append(part)
                    else:
                        location = match.strip()
                        if len(location) > 2 and location not in entities['locations']:
                            entities['locations'].append(location)
            
            # Extract dates
            date_patterns = [
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b\d{4}-\d{2}-\d{2}\b',
                r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    date = match.strip()
                    if date and date not in entities['dates']:
                        entities['dates'].append(date)
            
            # Remove duplicates and limit results
            for key in entities:
                entities[key] = list(set(entities[key]))[:10]  # Limit to 10 entities each
                
        except Exception as e:
            logger.warning(f"Error in NER extraction: {str(e)}")
            # Return empty results if extraction fails
            return {
                'persons': [],
                'organizations': [],
                'locations': [],
                'dates': [],
                'others': []
            }
        
        return entities

    def group_articles_into_events(self, articles: List[Dict]) -> Dict[int, List[Dict]]:
        """Group articles into events using similarity matching"""
        events = {}
        used_articles = set()
        event_id = 1
        
        logger.info(f"Grouping {len(articles)} articles into events")
        
        for i, article1 in enumerate(articles):
            if i in used_articles:
                continue
            
            # Start new event
            event_articles = [article1]
            used_articles.add(i)
            
            # Extract information from primary article
            title1 = (article1.get('title', '') or '').lower()
            text1 = (article1.get('text', '') or '')[:2000]
            outlet1 = article1.get('outlet', '')
            pub_time1 = article1.get('published_at')
            entities1 = self.extract_key_entities(text1)
            
            # Extract title keywords
            title1_words = set(re.findall(r'\b[a-z]{3,}\b', title1))
            common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
                           'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
                           'how', 'man', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did',
                           'its', 'let', 'put', 'say', 'she', 'too', 'use', 'said', 'says', 'will'}
            title1_words = title1_words - common_words
            
            # Look for matching articles
            for j, article2 in enumerate(articles):
                if j <= i or j in used_articles:
                    continue
                
                # Don't group articles from same outlet
                outlet2 = article2.get('outlet', '')
                if outlet2 == outlet1:
                    continue
                
                # Time check - must be within 24 hours for same event
                pub_time2 = article2.get('published_at')
                if pub_time1 and pub_time2:
                    try:
                        if pub_time1.tzinfo is None:
                            pub_time1 = pub_time1.replace(tzinfo=timezone.utc)
                        if pub_time2.tzinfo is None:
                            pub_time2 = pub_time2.replace(tzinfo=timezone.utc)
                        
                        time_diff = abs((pub_time1 - pub_time2).total_seconds() / 3600)
                        if time_diff > 24:
                            continue
                    except Exception:
                        continue
                
                # Entity matching
                title2 = (article2.get('title', '') or '').lower()
                text2 = (article2.get('text', '') or '')[:2000]
                entities2 = self.extract_key_entities(text2)
                
                if entities1 and entities2:
                    shared_entities = entities1 & entities2
                    min_entities = min(len(entities1), len(entities2))
                    
                    # Same requirements as publisher (4 entities AND 50% of smaller set)
                    if len(shared_entities) < 4 or len(shared_entities) < min_entities * 0.5:
                        continue
                else:
                    continue
                
                # Title keyword overlap
                title2_words = set(re.findall(r'\b[a-z]{3,}\b', title2))
                title2_words = title2_words - common_words
                
                if title1_words and title2_words:
                    title_overlap = len(title1_words & title2_words)
                    if title_overlap < 3:  # Same as publisher - at least 3 shared keywords
                        continue
                
                # If all checks pass, add to event
                event_articles.append(article2)
                used_articles.add(j)
            
            # Only create event if we have multiple articles
            if len(event_articles) > 1:
                events[event_id] = event_articles
                event_id += 1
        
        logger.info(f"Created {len(events)} events from {len(articles)} articles")
        return events

    def process_articles_batch(self) -> int:
        """Process a batch of articles that need quality scoring and event grouping"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get articles that need processing (last 72 hours, no quality score yet)
            cur.execute("""
                SELECT id, url, title, outlet, published_at, text
                FROM articles 
                WHERE published_at > NOW() - INTERVAL '72 hours'
                    AND text IS NOT NULL 
                    AND LENGTH(text) > 100
                    AND (quality_score IS NULL OR quality_computed_at < NOW() - INTERVAL '1 hour')
                ORDER BY published_at DESC 
                LIMIT %s
            """, (self.batch_size,))
            
            articles = cur.fetchall()
            
            if not articles:
                logger.info("No articles need processing")
                cur.close()
                conn.close()
                return 0
            
            logger.info(f"Processing {len(articles)} articles")
            
            # Calculate quality scores and extract NER data
            article_scores = {}
            article_ner_data = {}
            for article in articles:
                score = self.calculate_article_quality_score(dict(article))
                article_scores[article['id']] = score
                
                # Extract NER entities
                ner_entities = self.extract_ner_entities(article.get('text', ''))
                article_ner_data[article['id']] = ner_entities
            
            # Group articles into events
            events = self.group_articles_into_events([dict(a) for a in articles])
            
            # Update database with quality scores and event IDs
            processed_count = 0
            
            # First, update quality scores and NER data for all articles
            for article_id, quality_score in article_scores.items():
                ner_data = article_ner_data.get(article_id, {})
                cur.execute("""
                    UPDATE articles 
                    SET quality_score = %s, 
                        quality_computed_at = NOW(),
                        ner_persons = %s,
                        ner_organizations = %s,
                        ner_locations = %s,
                        ner_dates = %s,
                        ner_others = %s,
                        ner_extracted_at = NOW()
                    WHERE id = %s
                """, (
                    quality_score, 
                    json.dumps(ner_data.get('persons', [])),
                    json.dumps(ner_data.get('organizations', [])),
                    json.dumps(ner_data.get('locations', [])),
                    json.dumps(ner_data.get('dates', [])),
                    json.dumps(ner_data.get('others', [])),
                    article_id
                ))
                processed_count += 1
            
            # Then update event IDs for grouped articles
            for event_id, event_articles in events.items():
                article_ids = [a['id'] for a in event_articles]
                cur.execute("""
                    UPDATE articles 
                    SET computed_event_id = %s
                    WHERE id = ANY(%s)
                """, (event_id, article_ids))
                
                logger.info(f"Event {event_id}: grouped {len(event_articles)} articles")
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Successfully processed {processed_count} articles, created {len(events)} events")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing articles batch: {str(e)}")
            return 0

    def run(self):
        """Main service loop"""
        logger.info("Quality Service starting...")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        while self.running:
            try:
                processed = self.process_articles_batch()
                
                if processed == 0:
                    # No articles to process, sleep longer
                    sleep_time = self.sleep_interval * 2
                else:
                    sleep_time = self.sleep_interval
                
                logger.info(f"Batch complete. Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}")
                time.sleep(self.sleep_interval)
        
        logger.info("Quality Service stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False

if __name__ == "__main__":
    service = QualityService()
    service.run()