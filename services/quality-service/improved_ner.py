#!/usr/bin/env python3
"""
Improved NER (Named Entity Recognition) System
High-quality entity extraction using spaCy with post-processing validation
"""

import re
import logging
from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass
import time
from functools import lru_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EntityResult:
    """Result of entity extraction"""
    persons: Set[str]
    organizations: Set[str] 
    locations: Set[str]
    dates: Set[str]
    misc: Set[str]
    processing_time: float
    confidence_scores: Dict[str, float]
    total_entities: int


class ImprovedNERExtractor:
    """Improved NER system using spaCy with validation and filtering"""
    
    def __init__(self):
        self.nlp = None
        self._initialize_spacy()
        self._load_entity_rules()
        
        # Comprehensive filters for noise removal
        self.noise_patterns = self._build_noise_patterns()
        self.news_metadata_patterns = self._build_news_metadata_patterns()
        
    def _initialize_spacy(self):
        """Initialize spaCy with error handling and fallback"""
        try:
            import spacy
            
            # Try to load the model
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Successfully loaded en_core_web_sm spaCy model")
            except OSError:
                logger.warning("en_core_web_sm not found, using blank model")
                self.nlp = spacy.blank("en")
                
            # Add EntityRuler for news-specific patterns (updated for spaCy v3+)
            if "entity_ruler" not in self.nlp.pipe_names:
                self.nlp.add_pipe("entity_ruler", before="ner" if "ner" in self.nlp.pipe_names else None)
                
        except ImportError:
            logger.error("spaCy not available, falling back to regex-only extraction")
            self.nlp = None
            
    def _load_entity_rules(self):
        """Load custom rules for news-specific entities"""
        if not self.nlp or "entity_ruler" not in self.nlp.pipe_names:
            return
            
        ruler = self.nlp.get_pipe("entity_ruler")
        
        # News-specific organization patterns
        patterns = [
            {"label": "ORG", "pattern": "Associated Press"},
            {"label": "ORG", "pattern": "Reuters"},
            {"label": "ORG", "pattern": "CNN"},
            {"label": "ORG", "pattern": "BBC"},
            {"label": "ORG", "pattern": "Fox News"},
            {"label": "ORG", "pattern": "New York Times"},
            {"label": "ORG", "pattern": "Washington Post"},
            {"label": "ORG", "pattern": "Wall Street Journal"},
            
            # Government entities
            {"label": "ORG", "pattern": "White House"},
            {"label": "ORG", "pattern": "State Department"},
            {"label": "ORG", "pattern": "Department of Defense"},
            {"label": "ORG", "pattern": "Supreme Court"},
            {"label": "ORG", "pattern": "Congress"},
            {"label": "ORG", "pattern": "Senate"},
            {"label": "ORG", "pattern": "House of Representatives"},
            
            # International organizations
            {"label": "ORG", "pattern": "United Nations"},
            {"label": "ORG", "pattern": "European Union"},
            {"label": "ORG", "pattern": "NATO"},
            {"label": "ORG", "pattern": "World Health Organization"},
            {"label": "ORG", "pattern": "International Monetary Fund"},
        ]
        
        ruler.add_patterns(patterns)
        
    def _build_noise_patterns(self) -> List[str]:
        """Build patterns to identify and filter noise entities"""
        return [
            # Common words that shouldn't be entities
            r'^(the|this|that|these|those|there|here|when|where|what|who|why|how)$',
            r'^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$',
            r'^(january|february|march|april|may|june|july|august|september|october|november|december)$',
            r'^(new|first|last|next|previous|other|another|some|many|most|few|all|both|each|every|any)$',
            r'^(according|however|meanwhile|moreover|furthermore|therefore|published|recommended)$',
            r'^(view|comments|share|tweet|facebook|instagram|twitter|more|news|story|article|report)$',
            r'^(today|yesterday|tomorrow|now|then|soon|later|before|after|during|while|since)$',
            r'^(photo|picture|video|audio|image|getty|images)$',
            
            # Single letters or very short words
            r'^.{1,2}$',
            
            # Numbers only
            r'^\d+$',
            
            # Common metadata fragments
            r'^(said|told|from|with|about|against|between|among|through|during)$',
            r'.*\n.*',  # Contains newlines (likely metadata fragments)
            r'who$',    # Often appears as fragment
        ]
        
    def _build_news_metadata_patterns(self) -> List[str]:
        """Build patterns to identify and remove news metadata from text"""
        return [
            # Publication metadata
            r'published\s+on.*?\n',
            r'recommended\s+stories.*?\n',
            r'related\s+stories.*?\n',
            r'view\s+\d+\s+comments.*?\n',
            r'read\s+more.*?\n',
            r'click\s+here.*?\n',
            r'share\s+on.*?\n',
            
            # Photo/media credits
            r'photo\s+by.*?\n',
            r'image.*?getty.*?\n',
            r'photograph.*?\n',
            r'(ap|reuters|afp).*?contributed.*?\n',
            
            # Social media references  
            r'follow\s+us\s+on.*?\n',
            r'@\w+.*?\n',
            r'#\w+.*?\n',
            
            # Common article footers/headers
            r'©.*?\n',
            r'all\s+rights\s+reserved.*?\n',
            r'breaking\s*:?\s*',
            r'update\s*:?\s*',
            r'exclusive\s*:?\s*',
        ]
        
    def _clean_text(self, text: str) -> str:
        """Clean text by removing metadata and noise"""
        if not text:
            return ""
            
        # Limit text length for performance
        text = text[:3000]
        
        # Remove news metadata patterns
        for pattern in self.news_metadata_patterns:
            try:
                text = re.sub(pattern, ' ', text, flags=re.IGNORECASE | re.MULTILINE)
            except re.error as e:
                logger.warning(f"Regex error in pattern '{pattern}': {e}")
                continue
                
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def _is_valid_entity(self, entity_text: str, entity_type: str) -> bool:
        """Validate if an entity should be kept based on various filters"""
        if not entity_text or len(entity_text.strip()) < 2:
            return False
            
        entity_lower = entity_text.lower().strip()
        
        # Check against noise patterns
        for pattern in self.noise_patterns:
            try:
                if re.match(pattern, entity_lower, re.IGNORECASE):
                    return False
            except re.error:
                continue
                
        # Entity-specific validation
        if entity_type == "PERSON":
            # Persons should not be common words or obviously not names
            invalid_persons = {
                'who', 'said', 'told', 'according', 'press', 'news', 'report',
                'breaking', 'update', 'exclusive', 'story', 'article'
            }
            if entity_lower in invalid_persons:
                return False
                
        elif entity_type == "ORG":
            # Organizations should not be fragments or common words
            invalid_orgs = {
                'who', 'said', 'told', 'but', 'and', 'the', 'from', 'with',
                'including', 'according', 'however', 'meanwhile'
            }
            if entity_lower in invalid_orgs:
                return False
                
        elif entity_type in ["GPE", "LOC"]:  # Geopolitical entities / Locations
            # Locations should not be temporal or common words
            invalid_locations = {
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                'january', 'february', 'march', 'april', 'may', 'june', 'july', 
                'august', 'september', 'october', 'november', 'december',
                'today', 'yesterday', 'tomorrow', 'now', 'then', 'white', 'house'
            }
            # Special case: "White House" is valid as a compound, but "White" or "House" alone are not
            if entity_lower in invalid_locations and entity_lower not in ["white house"]:
                return False
                
        # Length constraints
        if len(entity_text) > 50:  # Likely metadata or malformed text
            return False
            
        return True
        
    def _extract_with_spacy(self, text: str) -> EntityResult:
        """Extract entities using spaCy NLP pipeline"""
        start_time = time.time()
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        persons = set()
        organizations = set()
        locations = set()
        dates = set()
        misc = set()
        confidence_scores = {}
        
        for ent in doc.ents:
            entity_text = ent.text.strip()
            confidence = getattr(ent, 'confidence', 0.9)  # Default confidence if not available
            
            # Validate entity before categorizing
            if not self._is_valid_entity(entity_text, ent.label_):
                continue
                
            confidence_scores[entity_text] = confidence
            
            # Categorize entities
            if ent.label_ == "PERSON":
                persons.add(entity_text)
            elif ent.label_ in ["ORG"]:
                organizations.add(entity_text)
            elif ent.label_ in ["GPE", "LOC"]:  # Geopolitical entities, Locations
                locations.add(entity_text)
            elif ent.label_ in ["DATE", "TIME"]:
                dates.add(entity_text)
            else:
                # Other entity types (MONEY, PERCENT, etc.)
                misc.add(entity_text)
                
        processing_time = time.time() - start_time
        total_entities = len(persons) + len(organizations) + len(locations) + len(dates) + len(misc)
        
        return EntityResult(
            persons=persons,
            organizations=organizations,
            locations=locations,
            dates=dates,
            misc=misc,
            processing_time=processing_time,
            confidence_scores=confidence_scores,
            total_entities=total_entities
        )
        
    def _extract_with_regex_fallback(self, text: str) -> EntityResult:
        """Fallback regex-based entity extraction (enhanced version of current system)"""
        start_time = time.time()
        
        entities = set()
        
        # Enhanced regex for proper nouns (same as current system but with better filtering)
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.findall(pattern, text)
        
        # Much more comprehensive filtering than current system
        comprehensive_non_entities = {
            # Current system's non-entities plus many more
            'The', 'This', 'That', 'These', 'Those', 'There', 'Here', 'When', 'Where',
            'What', 'Who', 'Why', 'How', 'According', 'However', 'Meanwhile', 'Moreover',
            'Furthermore', 'Therefore', 'Published', 'Recommended', 'Related', 'Associated',
            'View', 'Comments', 'Share', 'Tweet', 'Facebook', 'Instagram', 'Twitter',
            'Getty', 'Images', 'Photo', 'Picture', 'Video', 'Audio', 'More', 'News',
            'Story', 'Article', 'Report', 'Update', 'Breaking', 'Live', 'Latest',
            # Days and months
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
            'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
            'September', 'October', 'November', 'December',
            # Common problematic extractions from our data
            'Said', 'Told', 'From', 'With', 'About', 'Against', 'Between', 'Among',
            'Through', 'During', 'Before', 'After', 'Including', 'But', 'And', 'Or',
            'For', 'At', 'In', 'On', 'By', 'With', 'Without',
        }
        
        for match in matches:
            # Apply same validation as spaCy version
            if self._is_valid_entity(match, "UNKNOWN") and match not in comprehensive_non_entities:
                entities.add(match.lower())
                
        processing_time = time.time() - start_time
        
        # For regex fallback, we can't reliably categorize entities, so put them all as misc
        return EntityResult(
            persons=set(),
            organizations=set(),
            locations=set(),
            dates=set(),
            misc=entities,
            processing_time=processing_time,
            confidence_scores={e: 0.5 for e in entities},  # Lower confidence for regex
            total_entities=len(entities)
        )
        
    @lru_cache(maxsize=1000)
    def extract_entities(self, text: str, title: str = "") -> EntityResult:
        """
        Extract entities from text with caching
        
        Args:
            text: Article text to process
            title: Article title (can provide additional context)
            
        Returns:
            EntityResult with categorized entities and metadata
        """
        if not text:
            return EntityResult(set(), set(), set(), set(), set(), 0.0, {}, 0)
            
        # Combine title and text for better context
        full_text = f"{title}. {text}" if title else text
        
        # Clean the text
        cleaned_text = self._clean_text(full_text)
        
        if not cleaned_text:
            return EntityResult(set(), set(), set(), set(), set(), 0.0, {}, 0)
            
        # Use spaCy if available, otherwise fallback to regex
        if self.nlp:
            return self._extract_with_spacy(cleaned_text)
        else:
            return self._extract_with_regex_fallback(cleaned_text)
            
    def extract_key_entities_for_grouping(self, text: str) -> Set[str]:
        """
        Extract entities specifically for event grouping (backward compatible)
        Returns a set of normalized entity strings for similarity matching
        """
        result = self.extract_entities(text)
        
        # Combine all entity types for grouping, normalized to lowercase
        all_entities = set()
        all_entities.update(e.lower() for e in result.persons)
        all_entities.update(e.lower() for e in result.organizations)
        all_entities.update(e.lower() for e in result.locations)
        all_entities.update(e.lower() for e in result.misc)
        
        return all_entities
        
    def get_statistics(self) -> Dict:
        """Get statistics about the NER system"""
        return {
            'spacy_available': self.nlp is not None,
            'model_name': self.nlp.meta.get('name', 'unknown') if self.nlp else 'regex_fallback',
            'cache_info': self.extract_entities.cache_info()._asdict(),
        }


# Global instance for backward compatibility
_ner_extractor = None

def get_ner_extractor() -> ImprovedNERExtractor:
    """Get or create the global NER extractor instance"""
    global _ner_extractor
    if _ner_extractor is None:
        _ner_extractor = ImprovedNERExtractor()
    return _ner_extractor


# Backward-compatible function for existing code
def extract_key_entities(text: str) -> Set[str]:
    """
    Backward-compatible function for existing event grouping code
    """
    extractor = get_ner_extractor()
    return extractor.extract_key_entities_for_grouping(text)


if __name__ == "__main__":
    # Simple test
    extractor = ImprovedNERExtractor()
    
    test_text = """President Joe Biden met with Israeli Prime Minister Benjamin Netanyahu 
    at the White House. The Associated Press reported that who said the meeting was productive."""
    
    result = extractor.extract_entities(test_text)
    
    print("Extracted Entities:")
    print(f"Persons: {result.persons}")
    print(f"Organizations: {result.organizations}")
    print(f"Locations: {result.locations}")
    print(f"Processing time: {result.processing_time:.3f}s")
    print(f"Total entities: {result.total_entities}")
    print(f"Statistics: {extractor.get_statistics()}")