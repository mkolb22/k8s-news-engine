#!/usr/bin/env python3
"""
Writing Quality Analyzer
Implements comprehensive writing quality scoring based on the Quality Scoring Proposal
"""

import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import quality analysis libraries
try:
    import textstat
    from textblob import TextBlob
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
        
except ImportError as e:
    logging.warning(f"Writing quality libraries not available: {e}")
    textstat = None
    TextBlob = None

logger = logging.getLogger(__name__)

@dataclass
class WritingQualityScores:
    """Container for writing quality score components"""
    readability_score: int
    structure_score: int
    linguistic_score: int
    objectivity_score: int
    total_score: int
    
    # Component details
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    lead_quality: int
    source_attribution: int
    sentence_variety: int
    grammar_quality: int
    bias_indicators: List[str]
    
class WritingQualityAnalyzer:
    """Comprehensive writing quality analyzer for news articles"""
    
    def __init__(self):
        self.bias_indicators = [
            # Political bias indicators
            'allegedly', 'reportedly', 'supposedly', 'it seems', 'apparently',
            # Emotional language
            'shocking', 'outrageous', 'devastating', 'incredible', 'amazing',
            # Absolute statements without attribution
            'everyone knows', 'it is obvious', 'clearly', 'undoubtedly', 'certainly'
        ]
        
        self.quality_indicators = [
            # Source attribution phrases
            'according to', 'said in an interview', 'told reporters', 'stated',
            'confirmed', 'sources said', 'officials said', 'experts believe'
        ]
    
    def analyze_article(self, text: str, title: str = "") -> WritingQualityScores:
        """
        Analyze article writing quality and return comprehensive scores
        
        Args:
            text: Article text content
            title: Article title
            
        Returns:
            WritingQualityScores object with detailed scoring
        """
        
        if not text or len(text) < 100:
            return self._get_default_scores("Text too short for analysis")
            
        if not textstat:
            return self._get_default_scores("Analysis libraries not available")
        
        try:
            # Calculate readability scores
            readability = self._calculate_readability_score(text)
            
            # Analyze journalistic structure
            structure = self._analyze_journalistic_structure(text, title)
            
            # Assess linguistic quality
            linguistic = self._assess_linguistic_quality(text)
            
            # Evaluate objectivity and balance
            objectivity = self._evaluate_objectivity_balance(text)
            
            # Calculate total score
            total = min(100, readability + structure + linguistic + objectivity)
            
            return WritingQualityScores(
                readability_score=readability,
                structure_score=structure,
                linguistic_score=linguistic,
                objectivity_score=objectivity,
                total_score=total,
                flesch_reading_ease=textstat.flesch_reading_ease(text),
                flesch_kincaid_grade=textstat.flesch_kincaid_grade(text),
                lead_quality=self._analyze_lead_quality(text),
                source_attribution=self._analyze_source_attribution(text),
                sentence_variety=self._analyze_sentence_variety(text),
                grammar_quality=self._assess_grammar_quality(text),
                bias_indicators=self._detect_bias_indicators(text)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing article quality: {e}")
            return self._get_default_scores(f"Analysis error: {str(e)}")
    
    def _calculate_readability_score(self, text: str) -> int:
        """Calculate readability & clarity score (0-30 points)"""
        
        flesch_ease = textstat.flesch_reading_ease(text)
        flesch_grade = textstat.flesch_kincaid_grade(text)
        
        # Flesch Reading Ease scoring (0-15 points) - More generous for news articles
        if flesch_ease >= 70:      # Easy to very easy
            ease_points = 15
        elif flesch_ease >= 60:    # Standard
            ease_points = 13
        elif flesch_ease >= 50:    # Fairly difficult
            ease_points = 11
        elif flesch_ease >= 40:    # Difficult
            ease_points = 9
        elif flesch_ease >= 30:    # More difficult
            ease_points = 7
        else:                      # Very difficult
            ease_points = 5
            
        # Flesch-Kincaid Grade Level scoring (0-15 points) - More generous for news
        if flesch_grade <= 10:     # Grade 10 and below
            grade_points = 15
        elif flesch_grade <= 12:   # Grade 11-12
            grade_points = 13
        elif flesch_grade <= 14:   # Grade 13-14
            grade_points = 11
        elif flesch_grade <= 16:   # College level
            grade_points = 9
        else:                      # Graduate level
            grade_points = 7
            
        return min(30, ease_points + grade_points)
    
    def _analyze_journalistic_structure(self, text: str, title: str) -> int:
        """Analyze journalistic structure (0-35 points)"""
        
        structure_score = 0
        
        # Lead quality analysis (0-10 points)
        structure_score += self._analyze_lead_quality(text)
        
        # Source attribution analysis (0-10 points) 
        structure_score += self._analyze_source_attribution(text)
        
        # Factual completeness (0-15 points)
        structure_score += self._analyze_factual_completeness(text)
        
        return min(35, structure_score)
    
    def _analyze_lead_quality(self, text: str) -> int:
        """Analyze lead paragraph quality (0-10 points)"""
        
        sentences = sent_tokenize(text)
        if not sentences:
            return 0
            
        first_paragraph = sentences[0]
        
        # Check for 5 W's and H elements
        who_indicators = len(re.findall(r'\b(president|minister|official|spokesman|spokesperson|ceo|director|[A-Z][a-z]+ [A-Z][a-z]+)\b', first_paragraph, re.IGNORECASE))
        what_indicators = len(re.findall(r'\b(announced|said|declared|confirmed|revealed|reported|stated)\b', first_paragraph, re.IGNORECASE))
        when_indicators = len(re.findall(r'\b(today|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2}\/\d{1,2}\/\d{4})\b', first_paragraph, re.IGNORECASE))
        where_indicators = len(re.findall(r'\b([A-Z][a-z]+ [A-Z][a-z]+|Washington|London|Paris|Berlin|Tokyo|Beijing|Moscow|New York|Los Angeles)\b', first_paragraph))
        
        # Check for specificity - vague words reduce quality
        vague_words = len(re.findall(r'\b(something|things|stuff|important|affect|happened)\b', first_paragraph, re.IGNORECASE))
        
        elements_found = min(4, who_indicators + what_indicators + when_indicators + where_indicators)
        
        if elements_found >= 3 and vague_words == 0:
            return 10
        elif elements_found >= 2 and vague_words <= 1:
            return 7
        elif elements_found >= 1 and vague_words <= 2:
            return 4
        elif vague_words >= 3:
            return 1
        else:
            return 2
    
    def _analyze_source_attribution(self, text: str) -> int:
        """Analyze source attribution (0-10 points)"""
        
        # Count different types of source attribution
        named_sources = len(re.findall(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\s+(said|told|confirmed|stated|announced)', text))
        official_sources = len(re.findall(r'\b(officials?|spokesman|spokesperson|representative|minister|secretary)\s+(said|told|confirmed|stated)', text, re.IGNORECASE))
        attributed_quotes = len(re.findall(r'"[^"]*",?\s*(said|told|confirmed|stated|according to)', text, re.IGNORECASE))
        
        total_attribution = named_sources + official_sources + attributed_quotes
        
        if total_attribution >= 4:
            return 10
        elif total_attribution >= 2:
            return 8
        elif total_attribution >= 1:
            return 6
        else:
            return 2
    
    def _analyze_factual_completeness(self, text: str) -> int:
        """Analyze factual completeness (0-15 points)"""
        
        # Check for comprehensive coverage indicators
        word_count = len(word_tokenize(text))
        sentence_count = len(sent_tokenize(text))
        
        # Length-based completeness
        if word_count >= 500:
            length_score = 5
        elif word_count >= 300:
            length_score = 3
        elif word_count >= 150:
            length_score = 2
        else:
            length_score = 0
            
        # Detail indicators
        numbers_data = len(re.findall(r'\b\d+(\.\d+)?\s*(percent|million|billion|dollars?|people|years?|days?|months?)\b', text, re.IGNORECASE))
        context_indicators = len(re.findall(r'\b(background|context|previously|earlier|according to|data shows|statistics|research)\b', text, re.IGNORECASE))
        
        detail_score = min(10, (numbers_data + context_indicators) * 2)
        
        return min(15, length_score + detail_score)
    
    def _assess_linguistic_quality(self, text: str) -> int:
        """Assess linguistic quality (0-20 points)"""
        
        linguistic_score = 0
        
        # Sentence variety (0-5 points)
        linguistic_score += self._analyze_sentence_variety(text)
        
        # Vocabulary precision (0-5 points)
        linguistic_score += self._analyze_vocabulary_precision(text)
        
        # Grammar & mechanics (0-10 points)
        linguistic_score += self._assess_grammar_quality(text)
        
        return min(20, linguistic_score)
    
    def _analyze_sentence_variety(self, text: str) -> int:
        """Analyze sentence variety (0-5 points)"""
        
        sentences = sent_tokenize(text)
        if len(sentences) < 3:
            return 1
            
        # Calculate sentence length variety
        lengths = [len(word_tokenize(sentence)) for sentence in sentences]
        if not lengths:
            return 0
            
        avg_length = sum(lengths) / len(lengths)
        length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        
        # Higher variance indicates better variety
        if length_variance > 30:
            return 5
        elif length_variance > 15:
            return 4
        elif length_variance > 5:
            return 3
        else:
            return 2
    
    def _analyze_vocabulary_precision(self, text: str) -> int:
        """Analyze vocabulary precision (0-5 points)"""
        
        words = word_tokenize(text.lower())
        if len(words) < 50:
            return 1
            
        # Calculate lexical diversity (unique words / total words)
        unique_words = set(words)
        lexical_diversity = len(unique_words) / len(words)
        
        # Check for specific, precise terms
        specific_terms = len(re.findall(r'\b(specifically|particularly|precisely|exactly|detailed|comprehensive|thorough)\b', text, re.IGNORECASE))
        
        if lexical_diversity > 0.6 and specific_terms > 1:
            return 5
        elif lexical_diversity > 0.5 or specific_terms > 0:
            return 4
        elif lexical_diversity > 0.4:
            return 3
        else:
            return 2
    
    def _assess_grammar_quality(self, text: str) -> int:
        """Assess grammar and mechanics (0-10 points)"""
        
        # Simple grammar checks using patterns
        issues = 0
        
        # Check for common issues
        issues += len(re.findall(r'\b(it\'s)\s+(own|impact|affect)', text, re.IGNORECASE))  # its vs it's
        issues += len(re.findall(r'\b(their|there|they\'re)\b', text, re.IGNORECASE)) * 0.1  # Common confusion words
        issues += len(re.findall(r'[.!?]\s+[a-z]', text))  # Missing capitalization after sentences
        issues += len(re.findall(r'\s+,|\s+\.', text))  # Spacing issues with punctuation
        
        # Deduct points based on issues found - more lenient scoring
        grammar_score = max(5, 10 - int(issues))
        
        return grammar_score
    
    def _evaluate_objectivity_balance(self, text: str) -> int:
        """Evaluate objectivity and balance (0-15 points)"""
        
        objectivity_score = 0
        
        # Bias detection (0-10 points)
        objectivity_score += self._detect_bias_score(text)
        
        # Multiple perspectives (0-5 points)
        objectivity_score += self._analyze_multiple_perspectives(text)
        
        return min(15, objectivity_score)
    
    def _detect_bias_score(self, text: str) -> int:
        """Detect bias indicators and score objectivity (0-10 points)"""
        
        bias_count = 0
        text_lower = text.lower()
        
        for indicator in self.bias_indicators:
            bias_count += text_lower.count(indicator)
        
        # Emotional language detection
        emotional_words = re.findall(r'\b(shocking|outrageous|devastating|incredible|amazing|terrible|wonderful|fantastic|horrible)\b', text, re.IGNORECASE)
        bias_count += len(emotional_words)
        
        # Score based on bias indicators found
        if bias_count == 0:
            return 10
        elif bias_count <= 2:
            return 7
        elif bias_count <= 5:
            return 3
        else:
            return 0
    
    def _analyze_multiple_perspectives(self, text: str) -> int:
        """Analyze presence of multiple perspectives (0-5 points)"""
        
        # Look for perspective indicators
        perspective_indicators = len(re.findall(r'\b(however|meanwhile|on the other hand|alternatively|critics say|supporters argue|opponents claim)\b', text, re.IGNORECASE))
        contrasting_sources = len(re.findall(r'\b(but [A-Z][a-z]+ [A-Z][a-z]+ said|while .+ argued|however .+ stated)\b', text))
        
        total_perspectives = perspective_indicators + contrasting_sources
        
        if total_perspectives >= 3:
            return 5
        elif total_perspectives >= 1:
            return 3
        else:
            return 1
    
    def _detect_bias_indicators(self, text: str) -> List[str]:
        """Detect and return list of bias indicators found"""
        
        found_indicators = []
        text_lower = text.lower()
        
        for indicator in self.bias_indicators:
            if indicator in text_lower:
                found_indicators.append(indicator)
        
        return found_indicators
    
    def _get_default_scores(self, reason: str) -> WritingQualityScores:
        """Return default scores when analysis cannot be performed"""
        
        logger.warning(f"Using default scores: {reason}")
        
        return WritingQualityScores(
            readability_score=15,  # Default neutral scores
            structure_score=17,
            linguistic_score=10,
            objectivity_score=7,
            total_score=49,  # Neutral score
            flesch_reading_ease=60.0,
            flesch_kincaid_grade=10.0,
            lead_quality=5,
            source_attribution=5,
            sentence_variety=2,
            grammar_quality=5,
            bias_indicators=[]
        )