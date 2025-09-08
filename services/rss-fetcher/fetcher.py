#!/usr/bin/env python3
import os
import sys
import time
import logging
import schedule
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from newspaper import Article
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://truth:truth@localhost:5432/truthdb")
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "300"))  # 5 minutes default
USER_AGENT = "K8s-News-Engine/1.0 (+https://github.com/k8s-news-engine)"

class RSSFetcher:
    def __init__(self):
        self.engine = create_engine(DB_URL)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        
    def get_active_feeds(self):
        """Retrieve active RSS feeds from database"""
        sql = """
            SELECT id, url, outlet, last_fetched, fetch_interval_minutes 
            FROM rss_feeds 
            WHERE active = TRUE
        """
        with self.engine.begin() as conn:
            feeds = conn.execute(text(sql)).mappings().all()
        return feeds
    
    def should_fetch_feed(self, feed):
        """Check if feed should be fetched based on interval"""
        if not feed['last_fetched']:
            return True
        
        interval = feed['fetch_interval_minutes'] or 30
        next_fetch = feed['last_fetched'] + timedelta(minutes=interval)
        return datetime.now(timezone.utc) >= next_fetch
    
    def parse_feed(self, feed_url):
        """Parse RSS feed and return entries"""
        try:
            parsed = feedparser.parse(feed_url)
            if parsed.bozo:
                logger.warning(f"Feed parsing issue for {feed_url}: {parsed.bozo_exception}")
            return parsed.entries
        except Exception as e:
            logger.error(f"Failed to parse feed {feed_url}: {e}")
            return []
    
    def extract_article_content(self, url):
        """Extract full article content from URL"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return {
                'text': article.text,
                'authors': ', '.join(article.authors) if article.authors else None,
                'published': article.publish_date,
                'html': article.html
            }
        except Exception as e:
            logger.warning(f"Failed to extract article {url}: {e}")
            # Fallback to basic request
            try:
                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                text = '\n'.join(line for line in lines if line)
                
                return {
                    'text': text[:50000],  # Limit to 50k chars
                    'authors': None,
                    'published': None,
                    'html': response.text[:100000]  # Limit HTML to 100k
                }
            except Exception as e2:
                logger.error(f"Fallback extraction failed for {url}: {e2}")
                return None
    
    def save_article(self, feed_id, outlet, entry):
        """Save article to database if not exists"""
        # Get article URL
        url = entry.get('link', '')
        if not url:
            return None
            
        # Check if article already exists
        with self.engine.begin() as conn:
            exists = conn.execute(
                text("SELECT id FROM articles WHERE url = :url"),
                {"url": url}
            ).first()
            
            if exists:
                logger.debug(f"Article already exists: {url}")
                return exists[0]
        
        # Extract article content
        content = self.extract_article_content(url)
        if not content:
            logger.warning(f"Could not extract content for {url}")
            content = {'text': entry.get('summary', ''), 'authors': None, 'published': None, 'html': ''}
        
        # Parse publication date
        published = None
        if 'published_parsed' in entry:
            try:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except:
                pass
        elif content['published']:
            published = content['published']
        
        # Insert article
        sql = """
            INSERT INTO articles (url, outlet, title, published_at, author, text, raw_html, rss_feed_id)
            VALUES (:url, :outlet, :title, :published, :author, :text, :html, :feed_id)
            ON CONFLICT (url) DO UPDATE SET
                text = COALESCE(EXCLUDED.text, articles.text),
                raw_html = COALESCE(EXCLUDED.raw_html, articles.raw_html)
            RETURNING id
        """
        
        with self.engine.begin() as conn:
            result = conn.execute(text(sql), {
                "url": url,
                "outlet": outlet,
                "title": entry.get('title', 'Untitled')[:500],
                "published": published,
                "author": content['authors'],
                "text": content['text'],
                "html": content['html'],
                "feed_id": feed_id
            })
            article_id = result.first()[0]
            logger.info(f"Saved article {article_id}: {entry.get('title', '')[:80]}")
            return article_id
    
    def link_article_to_events(self, article_id, title, text):
        """Simple keyword matching to link articles to events"""
        if not text:
            return
            
        sql = """
            SELECT id, title, description 
            FROM events 
            WHERE active = TRUE
        """
        
        with self.engine.begin() as conn:
            events = conn.execute(text(sql)).mappings().all()
            
            for event in events:
                # Simple keyword matching - can be improved with NLP
                event_keywords = (event['title'] + ' ' + (event['description'] or '')).lower().split()
                article_text = (title + ' ' + text).lower()
                
                matches = sum(1 for kw in event_keywords if len(kw) > 3 and kw in article_text)
                relevance = matches / max(len(event_keywords), 1)
                
                if relevance > 0.2:  # 20% keyword match threshold
                    conn.execute(text("""
                        INSERT INTO event_articles (event_id, article_id, relevance_score)
                        VALUES (:eid, :aid, :score)
                        ON CONFLICT DO NOTHING
                    """), {
                        "eid": event['id'],
                        "aid": article_id,
                        "score": min(relevance, 1.0)
                    })
                    logger.info(f"Linked article {article_id} to event {event['id']} (relevance: {relevance:.2f})")
    
    def update_feed_timestamp(self, feed_id):
        """Update last fetched timestamp for feed"""
        with self.engine.begin() as conn:
            conn.execute(
                text("UPDATE rss_feeds SET last_fetched = NOW() WHERE id = :id"),
                {"id": feed_id}
            )
    
    def process_feed(self, feed):
        """Process a single RSS feed"""
        logger.info(f"Processing feed: {feed['outlet']} - {feed['url']}")
        
        entries = self.parse_feed(feed['url'])
        if not entries:
            logger.warning(f"No entries found for {feed['outlet']}")
            return
        
        new_articles = 0
        for entry in entries[:20]:  # Process max 20 entries per feed
            article_id = self.save_article(feed['id'], feed['outlet'], entry)
            if article_id:
                new_articles += 1
                # Link to events
                with self.engine.begin() as conn:
                    article = conn.execute(
                        text("SELECT title, text FROM articles WHERE id = :id"),
                        {"id": article_id}
                    ).first()
                    if article:
                        self.link_article_to_events(article_id, article[0], article[1])
        
        self.update_feed_timestamp(feed['id'])
        logger.info(f"Processed {feed['outlet']}: {new_articles} new articles")
    
    def run_once(self):
        """Run a single fetch cycle"""
        feeds = self.get_active_feeds()
        logger.info(f"Found {len(feeds)} active feeds")
        
        for feed in feeds:
            if self.should_fetch_feed(feed):
                try:
                    self.process_feed(feed)
                except Exception as e:
                    logger.error(f"Error processing feed {feed['outlet']}: {e}")
                time.sleep(2)  # Rate limiting
    
    def run_continuous(self):
        """Run continuous fetching with schedule"""
        logger.info(f"Starting RSS fetcher (interval: {FETCH_INTERVAL}s)")
        
        # Run once immediately
        self.run_once()
        
        # Schedule periodic runs
        schedule.every(FETCH_INTERVAL).seconds.do(self.run_once)
        
        while True:
            schedule.run_pending()
            time.sleep(30)

def main():
    fetcher = RSSFetcher()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        fetcher.run_once()
    else:
        fetcher.run_continuous()

if __name__ == "__main__":
    main()