#!/usr/bin/env python3
import os
import re
import logging
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
import spacy
from textblob import TextBlob

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://appuser:newsengine2024@localhost:5432/newsdb")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

class ClaimExtractor:
    def __init__(self):
        self.engine = create_engine(DB_URL)
        logger.info("Loading spaCy model...")
        self.nlp = spacy.load("en_core_web_sm")
        
        # Claim indicator patterns
        self.claim_indicators = [
            r"according to",
            r"studies show",
            r"research indicates",
            r"data suggests",
            r"statistics reveal",
            r"surveys found",
            r"reports indicate",
            r"analysis shows",
            r"evidence suggests",
            r"experts say",
            r"officials confirmed",
            r"sources claim",
            r"it is estimated",
            r"approximately \d+",
            r"\d+\s*percent",
            r"\d+\s*%",
            r"increased by",
            r"decreased by",
            r"rose to",
            r"fell to",
        ]
        
        self.claim_pattern = re.compile('|'.join(self.claim_indicators), re.IGNORECASE)
    
    def get_unprocessed_articles(self):
        """Get articles that haven't had claims extracted"""
        sql = """
            SELECT a.id, a.title, a.text, a.outlet
            FROM articles a
            LEFT JOIN claims c ON c.article_id = a.id
            WHERE a.text IS NOT NULL 
              AND LENGTH(a.text) > 100
              AND c.id IS NULL
            ORDER BY a.fetched_at DESC
            LIMIT :batch_size
        """
        with self.engine.begin() as conn:
            articles = conn.execute(text(sql), {"batch_size": BATCH_SIZE}).mappings().all()
        return articles
    
    def classify_claim_type(self, claim_text):
        """Classify claim as fact, opinion, or prediction"""
        claim_lower = claim_text.lower()
        
        # Prediction indicators
        if any(word in claim_lower for word in ['will', 'could', 'might', 'expected', 'forecast', 'predict', 'future', 'likely']):
            return 'prediction'
        
        # Opinion indicators
        if any(word in claim_lower for word in ['believe', 'think', 'feel', 'seems', 'appears', 'arguably', 'perhaps', 'maybe']):
            return 'opinion'
        
        # Fact indicators (numbers, dates, specific claims)
        if re.search(r'\d+', claim_text) or any(word in claim_lower for word in ['data', 'study', 'research', 'report', 'confirmed']):
            return 'fact'
        
        # Use TextBlob for sentiment - high subjectivity suggests opinion
        blob = TextBlob(claim_text)
        if blob.sentiment.subjectivity > 0.5:
            return 'opinion'
        
        return 'fact'
    
    def extract_claims_from_text(self, text, title=""):
        """Extract factual claims from article text"""
        if not text:
            return []
        
        # Combine title and text for context
        full_text = f"{title}\n\n{text}"
        
        # Process with spaCy
        doc = self.nlp(full_text[:100000])  # Limit to 100k chars for performance
        
        claims = []
        processed_claims = set()  # Avoid duplicates
        
        # Extract sentences with claim indicators
        for sent in doc.sents:
            sent_text = sent.text.strip()
            
            # Skip very short or very long sentences
            if len(sent_text) < 30 or len(sent_text) > 500:
                continue
            
            # Check for claim indicators
            if self.claim_pattern.search(sent_text):
                # Clean and normalize
                claim_text = re.sub(r'\s+', ' ', sent_text)
                claim_text = claim_text.strip()
                
                # Skip if already processed (or very similar)
                claim_key = claim_text.lower()[:100]
                if claim_key in processed_claims:
                    continue
                processed_claims.add(claim_key)
                
                # Classify the claim
                claim_type = self.classify_claim_type(claim_text)
                
                claims.append({
                    'text': claim_text,
                    'type': claim_type,
                    'confidence': 0.8 if self.claim_pattern.search(sent_text) else 0.5
                })
        
        # Also extract sentences with numerical claims
        for sent in doc.sents:
            sent_text = sent.text.strip()
            
            # Look for numerical claims not already captured
            if re.search(r'\b\d+[\d,]*\.?\d*\s*(percent|%|million|billion|thousand)', sent_text):
                claim_key = sent_text.lower()[:100]
                if claim_key not in processed_claims:
                    processed_claims.add(claim_key)
                    claims.append({
                        'text': sent_text,
                        'type': 'fact',
                        'confidence': 0.9
                    })
        
        # Limit to most confident claims
        claims.sort(key=lambda x: x['confidence'], reverse=True)
        return claims[:20]  # Max 20 claims per article
    
    def verify_claim_basic(self, claim_text, outlet):
        """Basic claim verification (placeholder for more sophisticated verification)"""
        # This is a simplified verification - in production, you'd:
        # 1. Cross-reference with fact-checking databases
        # 2. Compare with other articles
        # 3. Check against authoritative sources
        # 4. Use ML models for verification
        
        # For now, use simple heuristics
        claim_lower = claim_text.lower()
        
        # High confidence outlets get benefit of doubt
        high_confidence_outlets = ['reuters.com', 'apnews.com', 'bbc.co.uk']
        if outlet in high_confidence_outlets:
            if 'allegedly' in claim_lower or 'reportedly' in claim_lower:
                return 'unverified', None
            return 'verified', outlet
        
        # Check for hedging language
        if any(word in claim_lower for word in ['allegedly', 'reportedly', 'claimed', 'accused']):
            return 'unverified', None
        
        # Check for disputed topics (simplified)
        if any(word in claim_lower for word in ['controversial', 'disputed', 'debate', 'conflicting']):
            return 'contested', None
        
        # Default to unverified
        return 'unverified', None
    
    def save_claims(self, article_id, claims, outlet):
        """Save extracted claims to database"""
        if not claims:
            return 0
        
        saved = 0
        with self.engine.begin() as conn:
            for claim in claims:
                verified_state, source = self.verify_claim_basic(claim['text'], outlet)
                
                sql = """
                    INSERT INTO claims (article_id, claim_text, claim_type, verified_state, verification_source)
                    VALUES (:article_id, :text, :type, :state, :source)
                    ON CONFLICT DO NOTHING
                """
                
                conn.execute(text(sql), {
                    "article_id": article_id,
                    "text": claim['text'][:1000],  # Limit to 1000 chars
                    "type": claim['type'],
                    "state": verified_state,
                    "source": source
                })
                saved += 1
        
        return saved
    
    def process_article(self, article):
        """Process a single article for claim extraction"""
        logger.info(f"Processing article {article['id']}: {article['title'][:80]}")
        
        claims = self.extract_claims_from_text(article['text'], article['title'])
        
        if claims:
            saved = self.save_claims(article['id'], claims, article['outlet'])
            logger.info(f"Extracted {len(claims)} claims, saved {saved} for article {article['id']}")
        else:
            # Save empty claim record to mark as processed
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO claims (article_id, claim_text, claim_type, verified_state)
                    VALUES (:id, 'No claims extracted', 'none', 'unverified')
                """), {"id": article['id']})
            logger.info(f"No claims found for article {article['id']}")
    
    def run_batch(self):
        """Process a batch of articles"""
        articles = self.get_unprocessed_articles()
        
        if not articles:
            logger.info("No unprocessed articles found")
            return False
        
        logger.info(f"Processing batch of {len(articles)} articles")
        
        for article in articles:
            try:
                self.process_article(article)
            except Exception as e:
                logger.error(f"Error processing article {article['id']}: {e}")
        
        return True
    
    def run_continuous(self):
        """Run continuous claim extraction"""
        logger.info("Starting claim extractor service")
        
        import time
        while True:
            has_work = self.run_batch()
            if not has_work:
                logger.info("No work available, sleeping for 60 seconds")
                time.sleep(60)
            else:
                time.sleep(5)  # Brief pause between batches

def main():
    import sys
    
    extractor = ClaimExtractor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--batch':
        extractor.run_batch()
    else:
        extractor.run_continuous()

if __name__ == "__main__":
    main()