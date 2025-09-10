# Dual Quality Scoring System Proposal

## Executive Summary

This proposal outlines a dual scoring system to replace the current single quality score with two separate, more accurate metrics:
1. **Reputation Score (0-100)**: Based on journalism awards, professional recognition, and industry standing
2. **Writing Quality Score (0-100)**: Based on automated linguistic analysis, readability, and journalistic standards

## Current System Limitations

The existing quality service uses a simple weighted approach:
- Authority (0-40): Basic outlet reputation
- Content length (0-25): Word count-based scoring  
- Title quality (0-20): Character count-based
- Recency (0-15): Publication date proximity

**Problems:**
- Conflates outlet reputation with article quality
- Oversimplified content assessment 
- No linguistic quality analysis
- Missing factual accuracy indicators
- Limited scalability across news sources

## Research Findings

### News Agency Reputation Metrics
Research identified four major journalism awards that serve as reputation indicators:

1. **Pulitzer Prize**: Most prestigious journalism award
2. **Edward R. Murrow Awards**: RTDNA awards for broadcast/digital journalism excellence
3. **Peabody Awards**: Excellence in broadcasting and media
4. **Emmy Awards**: Television journalism recognition

**Key Insights:**
- Awards serve as peer recognition within journalism community
- ProPublica example: 8 Pulitzers, 5 Peabodys, 8 Emmys, 16 George Polk Awards
- Fox News case study: High viewership but no major journalism awards
- Awards indicate professional validation distinct from commercial success

### Writing Quality Assessment Methods
Academic research revealed comprehensive frameworks for journalism quality:

**Readability Metrics:**
- **Flesch Reading Ease (0-100)**: Higher scores = easier to read
- **Flesch-Kincaid Grade Level**: US education level required to understand text
- **SMOG Index**: Simple Measure of Gobbledygook
- **Coleman-Liau Index**: Difficulty estimation

**Academic Quality Dimensions:**
- **Professional**: Journalistic norms, independence, gatekeeping
- **Content**: Objectivity, transparency, factual accuracy
- **Audience**: Engagement, civic value, democratic contribution

**Computational Methods:**
- BERT-based machine learning for large-scale analysis
- Linguistic analysis for clarity, completeness, relevance
- Factual verification and source credibility assessment

## Proposed Dual Scoring Architecture

### Score 1: Reputation Score (0-100)

**Purpose**: Measure the professional standing and credibility of the news organization

**Components:**

#### A. Awards & Recognition (0-60 points)
**Major Awards (10 points each, max 40):**
- Pulitzer Prize: 10 points per award (last 10 years)
- Edward R. Murrow Award: 10 points per award (last 5 years)
- Peabody Award: 10 points per award (last 10 years)  
- Emmy Award: 10 points per award (last 5 years)

**Regional/Specialized Awards (5 points each, max 20):**
- George Polk Award: 5 points per award (last 10 years)
- Alfred I. duPont Award: 5 points per award (last 10 years)
- Society of Professional Journalists awards: 2 points each (max 10)

#### B. Professional Standing (0-25 points)
- **Press Freedom Ranking**: Based on country/organization press freedom index
- **Industry Recognition**: Member of professional journalism organizations
- **Editorial Independence**: Assessment of ownership structure and editorial policies
- **Fact-Checking Standards**: Presence of correction policies and fact-checking processes

#### C. Credibility Indicators (0-15 points)
- **Correction Rate**: Lower rates indicate higher accuracy (inverse scoring)
- **Retraction History**: Frequency and severity of retractions
- **Source Transparency**: Disclosure of funding, ownership, potential conflicts
- **Ethical Standards**: Adherence to journalism codes of ethics

### Score 2: Writing Quality Score (0-100)

**Purpose**: Measure the linguistic quality, readability, and journalistic standards of individual articles

**Components:**

#### A. Readability & Clarity (0-30 points)
**Flesch Reading Ease (0-15 points):**
- 80-100 (Very easy): 15 points
- 70-80 (Easy): 12 points  
- 60-70 (Standard): 10 points
- 50-60 (Fairly difficult): 8 points
- 30-50 (Difficult): 5 points
- 0-30 (Very difficult): 2 points

**Flesch-Kincaid Grade Level (0-15 points):**
- Grade 8 or below (General audience): 15 points
- Grade 9-10: 12 points
- Grade 11-12: 10 points
- College level: 8 points
- Graduate level: 5 points

#### B. Journalistic Structure (0-35 points)
**Lead Quality (0-10 points):**
- Clear who, what, when, where in first paragraph: 10 points
- Missing 1-2 elements: 7 points
- Missing 3+ elements: 3 points

**Source Attribution (0-10 points):**
- Multiple named sources: 10 points
- Some named sources: 7 points
- Mostly anonymous sources: 4 points
- No source attribution: 0 points

**Factual Completeness (0-15 points):**
- Comprehensive coverage of key facts: 15 points
- Good coverage: 10 points
- Basic coverage: 6 points
- Minimal coverage: 2 points

#### C. Linguistic Quality (0-20 points)
**Sentence Variety (0-5 points):**
- Varied sentence lengths and structures: 5 points
- Some variety: 3 points
- Repetitive: 1 point

**Vocabulary Precision (0-5 points):**
- Precise, specific word choices: 5 points
- Generally good: 3 points
- Vague or repetitive: 1 point

**Grammar & Mechanics (0-10 points):**
- Error-free: 10 points
- 1-2 minor errors: 8 points
- 3-5 errors: 5 points
- Multiple errors: 2 points

#### D. Objectivity & Balance (0-15 points)
**Bias Detection (0-10 points):**
- Neutral tone and language: 10 points
- Slightly biased: 7 points
- Clearly biased: 3 points
- Heavily biased: 0 points

**Multiple Perspectives (0-5 points):**
- Presents multiple viewpoints: 5 points
- Some balance: 3 points
- One-sided: 1 point

## Database Schema Changes

### New Tables

```sql
-- Outlet reputation tracking
CREATE TABLE outlet_reputation_scores (
    id BIGSERIAL PRIMARY KEY,
    outlet VARCHAR(255) NOT NULL UNIQUE,
    reputation_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    
    -- Awards tracking
    pulitzer_awards INTEGER DEFAULT 0,
    murrow_awards INTEGER DEFAULT 0,
    peabody_awards INTEGER DEFAULT 0,
    emmy_awards INTEGER DEFAULT 0,
    other_awards INTEGER DEFAULT 0,
    
    -- Professional standing
    press_freedom_score NUMERIC(3,1),
    industry_membership_score INTEGER DEFAULT 0,
    editorial_independence_score INTEGER DEFAULT 0,
    fact_check_standards_score INTEGER DEFAULT 0,
    
    -- Credibility indicators
    correction_rate NUMERIC(4,3),
    retraction_count INTEGER DEFAULT 0,
    transparency_score INTEGER DEFAULT 0,
    ethics_score INTEGER DEFAULT 0,
    
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Writing quality cache for performance
CREATE TABLE article_writing_quality (
    article_id BIGINT PRIMARY KEY REFERENCES articles(id),
    writing_quality_score NUMERIC(5,2) NOT NULL,
    
    -- Readability metrics
    flesch_reading_ease NUMERIC(5,2),
    flesch_kincaid_grade NUMERIC(4,2),
    readability_score INTEGER,
    
    -- Journalistic structure
    lead_quality_score INTEGER,
    source_attribution_score INTEGER,
    factual_completeness_score INTEGER,
    
    -- Linguistic quality
    sentence_variety_score INTEGER,
    vocabulary_precision_score INTEGER,
    grammar_score INTEGER,
    
    -- Objectivity
    bias_score INTEGER,
    balance_score INTEGER,
    
    computed_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Updated Articles Table

```sql
-- Separate the two scores
ALTER TABLE articles 
ADD COLUMN reputation_score NUMERIC(5,2),
ADD COLUMN writing_quality_score NUMERIC(5,2),
ADD COLUMN composite_quality_score NUMERIC(5,2);

-- Keep existing quality_score for backwards compatibility
-- composite_quality_score = (reputation_score + writing_quality_score) / 2
```

## Implementation Algorithm

### Reputation Score Calculation

```python
def calculate_reputation_score(outlet: str) -> float:
    """Calculate reputation score for news outlet"""
    
    # Get outlet data from database
    outlet_data = get_outlet_reputation_data(outlet)
    
    score = 0.0
    
    # Awards & Recognition (0-60)
    awards_score = min(60, (
        outlet_data.pulitzer_awards * 10 +
        outlet_data.murrow_awards * 10 +
        outlet_data.peabody_awards * 10 +
        outlet_data.emmy_awards * 10 +
        outlet_data.other_awards * 5
    ))
    
    # Professional Standing (0-25)
    professional_score = (
        outlet_data.press_freedom_score +
        outlet_data.industry_membership_score +
        outlet_data.editorial_independence_score +
        outlet_data.fact_check_standards_score
    )
    
    # Credibility Indicators (0-15)
    credibility_score = calculate_credibility_score(outlet_data)
    
    return min(100, awards_score + professional_score + credibility_score)
```

### Writing Quality Score Calculation

```python
def calculate_writing_quality_score(article_text: str) -> dict:
    """Calculate writing quality score for article"""
    
    scores = {}
    
    # Readability & Clarity (0-30)
    flesch_ease = calculate_flesch_reading_ease(article_text)
    flesch_grade = calculate_flesch_kincaid_grade(article_text)
    
    scores['readability'] = (
        get_flesch_ease_points(flesch_ease) +
        get_flesch_grade_points(flesch_grade)
    )
    
    # Journalistic Structure (0-35)
    scores['structure'] = (
        analyze_lead_quality(article_text) +
        analyze_source_attribution(article_text) +
        analyze_factual_completeness(article_text)
    )
    
    # Linguistic Quality (0-20)
    scores['linguistic'] = (
        analyze_sentence_variety(article_text) +
        analyze_vocabulary_precision(article_text) +
        analyze_grammar_mechanics(article_text)
    )
    
    # Objectivity & Balance (0-15)
    scores['objectivity'] = (
        analyze_bias_detection(article_text) +
        analyze_multiple_perspectives(article_text)
    )
    
    total_score = sum(scores.values())
    return {'total': total_score, 'components': scores}
```

## Implementation Roadmap

### Phase 1: Research & Data Collection (4 weeks)
1. **Awards Database Creation**
   - Compile journalism awards database for major outlets
   - Historical award tracking (last 5-10 years)
   - API integration for award databases where available

2. **Outlet Profiling**
   - Create comprehensive outlet profiles with reputation metrics
   - Press freedom rankings integration
   - Fact-checking standards assessment

### Phase 2: Writing Quality Engine (6 weeks)
1. **Readability Implementation**
   - Implement Flesch-Kincaid, SMOG, Coleman-Liau algorithms
   - Python libraries: textstat, py-readability-metrics
   - Performance optimization for real-time scoring

2. **Journalistic Structure Analysis**
   - Lead quality detection algorithms
   - Source attribution pattern recognition
   - Factual completeness heuristics

3. **Advanced Linguistic Analysis**
   - Sentence variety analysis
   - Vocabulary precision scoring
   - Grammar/mechanics checking (LanguageTool integration)

4. **Bias Detection**
   - Implement bias detection algorithms
   - Sentiment analysis for objectivity assessment
   - Multiple perspective identification

### Phase 3: Database & Backend Integration (3 weeks)
1. **Schema Implementation**
   - Create new database tables
   - Migrate existing data
   - Performance optimization with proper indexing

2. **Quality Service Updates**
   - Refactor existing quality calculation
   - Implement dual scoring system
   - Batch processing optimization

### Phase 4: Testing & Validation (3 weeks)
1. **Algorithm Validation**
   - Test against manually scored articles
   - Cross-validation with journalism experts
   - Performance benchmarking

2. **System Integration**
   - End-to-end testing
   - Performance monitoring
   - Error handling and fallbacks

### Phase 5: Deployment & Monitoring (2 weeks)
1. **Production Deployment**
   - Gradual rollout with feature flags
   - Monitoring and alerting setup
   - Documentation updates

2. **Continuous Improvement**
   - User feedback integration
   - Machine learning model training
   - Regular algorithm updates

## Technical Requirements

### Python Libraries
```python
# Readability analysis
textstat>=0.7.0
py-readability-metrics>=1.4.5

# Natural language processing
spacy>=3.4.0
nltk>=3.7
textblob>=0.17.1

# Grammar and style checking
language-tool-python>=2.7.1

# Machine learning (future phases)
scikit-learn>=1.1.0
transformers>=4.21.0  # For BERT-based analysis
```

### Performance Considerations
- Cache reputation scores (updated monthly)
- Async processing for writing quality analysis
- Database indexing for fast score retrieval
- Rate limiting for external API calls

## Success Metrics

### Accuracy Metrics
- Correlation with manual expert ratings (target: >0.8)
- Precision/recall for bias detection (target: >0.75)
- User satisfaction with score accuracy

### Performance Metrics
- Processing time per article (target: <5 seconds)
- System uptime and reliability
- Database query performance

### Business Impact
- Improved user engagement with quality content
- Better content recommendation accuracy
- Enhanced credibility of the platform

## Conclusion

This dual scoring system provides:
1. **Clear separation** between outlet reputation and article quality
2. **Objective, measurable criteria** based on academic research
3. **Scalable implementation** using proven algorithms
4. **Continuous improvement** through machine learning
5. **Industry-standard metrics** for journalism quality assessment

The system addresses current limitations while providing a foundation for advanced quality analysis that can evolve with the platform's needs and the journalism industry's standards.