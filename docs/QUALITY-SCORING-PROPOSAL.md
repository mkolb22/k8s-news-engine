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

#### News Agency Reputation Metrics Table

The `news_agency_reputation_metrics` table serves as the comprehensive repository for journalism awards, professional recognition, and credibility indicators for news organizations. This table enables:

- **Detailed Award Tracking**: Maintains complete records of major journalism awards (Pulitzer, Murrow, Peabody, Emmy) with year tracking
- **Professional Assessment**: Captures industry memberships, editorial independence ratings, and fact-checking standards
- **Ethics & Transparency**: Documents correction policies, ownership transparency, and funding disclosure practices
- **Research Documentation**: Includes research notes and last update dates for maintainability

```sql
-- News Agency Reputation Metrics - Core journalism awards and professional recognition
CREATE TABLE news_agency_reputation_metrics (
    id BIGSERIAL PRIMARY KEY,
    outlet_name VARCHAR(255) NOT NULL UNIQUE,
    
    -- Major Journalism Awards (10 points each, max 40)
    pulitzer_awards INTEGER DEFAULT 0,
    pulitzer_years TEXT[], -- Array of years for awards tracking
    murrow_awards INTEGER DEFAULT 0,
    murrow_years TEXT[],
    peabody_awards INTEGER DEFAULT 0,
    peabody_years TEXT[],
    emmy_awards INTEGER DEFAULT 0,
    emmy_years TEXT[],
    
    -- Regional/Specialized Awards (5 points each, max 20)
    george_polk_awards INTEGER DEFAULT 0,
    duPont_awards INTEGER DEFAULT 0,
    spj_awards INTEGER DEFAULT 0, -- Society of Professional Journalists
    other_specialized_awards INTEGER DEFAULT 0,
    
    -- Professional Standing Metrics
    press_freedom_ranking INTEGER, -- Country/org press freedom index
    industry_memberships TEXT[], -- Professional journalism organizations
    editorial_independence_rating NUMERIC(3,1), -- 0-10 scale
    fact_checking_standards BOOLEAN DEFAULT FALSE,
    
    -- Credibility and Ethics
    correction_policy_exists BOOLEAN DEFAULT FALSE,
    retraction_transparency BOOLEAN DEFAULT FALSE,
    ownership_transparency BOOLEAN DEFAULT FALSE,
    funding_disclosure BOOLEAN DEFAULT FALSE,
    ethics_code_public BOOLEAN DEFAULT FALSE,
    
    -- Computed scores
    total_awards_score INTEGER DEFAULT 0,
    professional_standing_score INTEGER DEFAULT 0,
    credibility_score INTEGER DEFAULT 0,
    final_reputation_score NUMERIC(5,2) DEFAULT 0,
    
    -- Metadata
    last_research_date DATE,
    research_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Outlet reputation tracking (simplified version referencing detailed metrics)
CREATE TABLE outlet_reputation_scores (
    id BIGSERIAL PRIMARY KEY,
    outlet VARCHAR(255) NOT NULL UNIQUE,
    reputation_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    
    -- Reference to detailed metrics
    reputation_metrics_id BIGINT REFERENCES news_agency_reputation_metrics(id),
    
    -- Quick lookup fields (denormalized for performance)
    total_major_awards INTEGER DEFAULT 0,
    has_fact_checking BOOLEAN DEFAULT FALSE,
    press_freedom_tier VARCHAR(20), -- 'excellent', 'good', 'fair', 'poor'
    
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
    """Calculate reputation score for news outlet using detailed metrics table"""
    
    # Get detailed outlet data from news_agency_reputation_metrics table
    outlet_metrics = get_news_agency_metrics(outlet)
    
    if not outlet_metrics:
        # Fallback to basic outlet_authority table if no detailed metrics exist
        return get_basic_authority_score(outlet)
    
    scores = {}
    
    # Awards & Recognition (0-60 points)
    major_awards_score = min(40, (
        outlet_metrics.pulitzer_awards * 10 +
        outlet_metrics.murrow_awards * 10 +
        outlet_metrics.peabody_awards * 10 +
        outlet_metrics.emmy_awards * 10
    ))
    
    specialized_awards_score = min(20, (
        outlet_metrics.george_polk_awards * 5 +
        outlet_metrics.duPont_awards * 5 +
        outlet_metrics.spj_awards * 2 +
        outlet_metrics.other_specialized_awards * 2
    ))
    
    awards_score = major_awards_score + specialized_awards_score
    
    # Professional Standing (0-25 points)
    press_freedom_points = calculate_press_freedom_score(outlet_metrics.press_freedom_ranking)
    membership_points = len(outlet_metrics.industry_memberships or []) * 2  # 2 points per membership
    independence_points = outlet_metrics.editorial_independence_rating or 0
    fact_check_points = 5 if outlet_metrics.fact_checking_standards else 0
    
    professional_score = min(25, 
        press_freedom_points + membership_points + independence_points + fact_check_points
    )
    
    # Credibility & Ethics (0-15 points)
    credibility_factors = [
        outlet_metrics.correction_policy_exists,
        outlet_metrics.retraction_transparency, 
        outlet_metrics.ownership_transparency,
        outlet_metrics.funding_disclosure,
        outlet_metrics.ethics_code_public
    ]
    credibility_score = sum(3 for factor in credibility_factors if factor)  # 3 points each
    
    total_score = min(100, awards_score + professional_score + credibility_score)
    
    # Update the computed scores in database
    update_reputation_metrics_scores(outlet_metrics.id, {
        'total_awards_score': awards_score,
        'professional_standing_score': professional_score, 
        'credibility_score': credibility_score,
        'final_reputation_score': total_score
    })
    
    return total_score

def get_news_agency_metrics(outlet: str):
    """Fetch detailed reputation metrics from database"""
    query = """
    SELECT * FROM news_agency_reputation_metrics 
    WHERE outlet_name = %s
    """
    return db.fetch_one(query, [outlet])

def calculate_press_freedom_score(ranking: int) -> int:
    """Convert press freedom ranking to score points (0-10)"""
    if not ranking:
        return 5  # Default/unknown
    elif ranking <= 20:
        return 10  # Excellent
    elif ranking <= 50:
        return 8   # Good  
    elif ranking <= 100:
        return 6   # Fair
    elif ranking <= 150:
        return 4   # Poor
    else:
        return 2   # Very poor
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

## Programmatic Implementation

### Integration with Quality Service

The Writing Quality Score will be implemented as part of the existing quality-service, updating the current `quality_score` column in the articles table with the new comprehensive scoring algorithm.

```python
# Enhanced quality_service with Writing Quality Score
def calculate_comprehensive_quality_score(article_text: str, outlet: str, title: str) -> dict:
    """
    Calculate comprehensive quality score combining writing quality metrics
    Updates the articles.quality_score column directly
    """
    
    # Calculate writing quality components
    writing_scores = {
        'readability': calculate_readability_score(article_text),
        'structure': analyze_journalistic_structure(article_text, title),
        'linguistic': assess_linguistic_quality(article_text),
        'objectivity': evaluate_objectivity_balance(article_text)
    }
    
    # Calculate total writing quality score (0-100)
    total_writing_score = sum(writing_scores.values())
    
    # Get outlet reputation (fallback to existing authority system)
    outlet_reputation = get_outlet_reputation_score(outlet)
    
    # Composite score (60% writing quality + 40% reputation)
    composite_score = (total_writing_score * 0.6) + (outlet_reputation * 0.4)
    
    return {
        'writing_quality_score': total_writing_score,
        'reputation_score': outlet_reputation,
        'composite_score': composite_score,
        'components': writing_scores
    }

def update_article_quality_score(article_id: int, scores: dict):
    """Update articles table with new quality score"""
    query = """
    UPDATE articles 
    SET quality_score = %s,
        quality_computed_at = NOW()
    WHERE id = %s
    """
    cursor.execute(query, [scores['composite_score'], article_id])
```

### Batch Processing for Existing Articles

```python
def recompute_all_quality_scores(batch_size: int = 100):
    """
    Recompute quality scores for all articles in database
    Processes articles in batches to manage memory usage
    """
    
    offset = 0
    total_processed = 0
    
    while True:
        # Get batch of articles without quality scores or old scores
        articles = get_articles_for_scoring(batch_size, offset)
        
        if not articles:
            break
            
        for article in articles:
            try:
                # Skip articles without sufficient text content
                if not article.text or len(article.text) < 100:
                    continue
                    
                # Calculate quality scores
                scores = calculate_comprehensive_quality_score(
                    article.text, 
                    article.outlet, 
                    article.title
                )
                
                # Update database
                update_article_quality_score(article.id, scores)
                total_processed += 1
                
                if total_processed % 50 == 0:
                    print(f"Processed {total_processed} articles...")
                    
            except Exception as e:
                print(f"Error processing article {article.id}: {e}")
                continue
                
        offset += batch_size
        
    print(f"Quality score recomputation complete. Processed {total_processed} articles.")
```

### Validation and Testing Framework

```python
def validate_quality_scoring():
    """
    Comprehensive validation of quality scoring implementation
    Tests various article types and edge cases
    """
    
    test_cases = [
        {
            'name': 'High Quality News Article',
            'text': get_sample_high_quality_article(),
            'expected_min_score': 70,
            'outlet': 'BBC World'
        },
        {
            'name': 'Low Quality Content',
            'text': get_sample_low_quality_article(), 
            'expected_max_score': 40,
            'outlet': 'Unknown Source'
        },
        {
            'name': 'Technical Article',
            'text': get_sample_technical_article(),
            'expected_readability_range': (40, 70),
            'outlet': 'Reuters'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        scores = calculate_comprehensive_quality_score(
            test_case['text'], 
            test_case['outlet'], 
            'Test Article Title'
        )
        
        # Validate expectations
        test_result = {
            'name': test_case['name'],
            'scores': scores,
            'passed': True,
            'issues': []
        }
        
        # Check score ranges
        if 'expected_min_score' in test_case:
            if scores['composite_score'] < test_case['expected_min_score']:
                test_result['passed'] = False
                test_result['issues'].append(f"Score too low: {scores['composite_score']}")
                
        if 'expected_max_score' in test_case:
            if scores['composite_score'] > test_case['expected_max_score']:
                test_result['passed'] = False
                test_result['issues'].append(f"Score too high: {scores['composite_score']}")
        
        results.append(test_result)
    
    return results
```

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