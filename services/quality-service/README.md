# Quality Service

Microservice for computing article quality scores and event groupings to optimize publisher performance.

## Overview

The Quality Service processes news articles to:
- Calculate comprehensive quality scores (0-100) based on authority, content quality, title descriptiveness, and recency
- Group related articles into events using entity extraction and similarity matching
- Store pre-computed results in the database to optimize publisher queries

## Architecture

- **Language**: Python 3.11
- **Database**: PostgreSQL with psycopg2
- **Deployment**: Kubernetes with Alpine Linux container
- **Processing**: Batch processing with configurable intervals

## Quality Scoring Algorithm

### Authority Score (0-40)
Based on outlet reputation with predefined authority weights:
- Reuters, AP: 38-40 points
- BBC, Guardian, NYT: 34-36 points
- CNN, Al Jazeera: 28-30 points
- Alternative sources: 15-20 points

### Content Quality (0-25)
Based on article text length and structure:
- >2000 chars: 25 points
- >1000 chars: 20 points  
- >500 chars: 15 points
- >200 chars: 10 points

### Title Quality (0-20)
Based on title descriptiveness:
- >100 chars: 20 points
- >60 chars: 15 points
- >30 chars: 10 points

### Recency Bonus (0-15)
Recent articles get higher priority:
- <6 hours: 15 points
- <24 hours: 10 points
- <48 hours: 5 points

## Event Grouping Logic

Articles are grouped into events when they:
1. Are from different outlets (no same-source grouping)
2. Are published within 24 hours of each other
3. Share at least 4 entities AND 50% of entities overlap
4. Have at least 3 shared title keywords
5. Pass coherence verification

## Configuration

Environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `BATCH_SIZE`: Articles to process per batch (default: 50)
- `SLEEP_INTERVAL`: Seconds between batches (default: 60)
- `TZ`: Timezone setting (default: UTC)

## Database Schema

The service requires these additional columns on the `articles` table:
```sql
ALTER TABLE articles 
ADD COLUMN quality_score NUMERIC DEFAULT NULL,
ADD COLUMN computed_event_id BIGINT DEFAULT NULL,
ADD COLUMN quality_computed_at TIMESTAMPTZ DEFAULT NULL;
```

## Deployment

Build and deploy:
```bash
# Build image
docker build -t k8s-news-engine/quality-service:latest .

# Deploy to Kubernetes
kubectl apply -f k8s/deployment.yaml
```

## Monitoring

- Health checks via database connectivity tests
- Logs written to `/var/log/quality-service.log`
- Graceful shutdown on SIGTERM/SIGINT
- Resource limits: 512Mi memory, 500m CPU

## Performance

- Processes 50 articles per batch by default
- Optimized for 72-hour rolling window
- Supports concurrent processing with publisher service
- Minimal memory footprint with Alpine Linux base

## Named Entity Recognition (NER)

### Overview
The service extracts structured entity data from article text content using regex-based pattern matching.

### Entity Types Extracted
- **Persons**: Names with titles (President, CEO, etc.) and speech attribution patterns
- **Organizations**: News outlets, companies, agencies, government bodies
- **Locations**: Cities, states, countries, landmarks  
- **Dates**: Multiple date formats and temporal references
- **Others**: Reserved for future entity types

### NER Processing
- **Source**: Article `text` field (first 3000 characters for performance)
- **Patterns**: Comprehensive regex patterns for each entity type
- **Limits**: Maximum 10 entities per category to prevent data bloat
- **Storage**: JSONB arrays in database columns

### Database Schema for NER
```sql
-- NER columns added to articles table
ALTER TABLE articles 
ADD COLUMN ner_persons JSONB DEFAULT '[]'::jsonb,
ADD COLUMN ner_organizations JSONB DEFAULT '[]'::jsonb,
ADD COLUMN ner_locations JSONB DEFAULT '[]'::jsonb,
ADD COLUMN ner_dates JSONB DEFAULT '[]'::jsonb,
ADD COLUMN ner_others JSONB DEFAULT '[]'::jsonb,
ADD COLUMN ner_extracted_at TIMESTAMPTZ DEFAULT NULL;

-- GIN indexes for fast entity searches
CREATE INDEX idx_articles_ner_persons ON articles USING gin (ner_persons);
CREATE INDEX idx_articles_ner_organizations ON articles USING gin (ner_organizations);
CREATE INDEX idx_articles_ner_locations ON articles USING gin (ner_locations);
```

### Entity Extraction Examples
```json
{
  "persons": ["Trump", "Joe Biden", "Lisa Cook"],
  "organizations": ["CBS News", "Federal Reserve", "WHO"],
  "locations": ["Washington", "Brussels", "New York"],
  "dates": ["January 15, 2025", "Monday", "2025-01-01"]
}
```

## Integration

The publisher service queries pre-computed results with NER data:
```sql
SELECT id, title, outlet, quality_score, computed_event_id,
       ner_persons, ner_organizations, ner_locations
FROM articles 
WHERE published_at > NOW() - INTERVAL '72 hours'
  AND quality_score IS NOT NULL
  AND ner_extracted_at IS NOT NULL
ORDER BY quality_score DESC;
```

## Change Log

### v1.1.0 (2025-09-10)
**Major Feature: Named Entity Recognition Implementation**

#### New Features
- ✅ **NER Extraction**: Comprehensive entity extraction from article text
  - Persons: Title + name patterns, speech attribution
  - Organizations: News outlets, companies, agencies
  - Locations: Cities, states, countries
  - Dates: Multiple temporal formats
- ✅ **Database Integration**: JSONB storage with GIN indexes
- ✅ **Processing Pipeline**: Integrated NER into quality processing workflow
- ✅ **Performance Optimized**: Text limited to 3000 chars, max 10 entities per type

#### Technical Implementation
- **Function**: `extract_ner_entities(text: str) -> Dict[str, List[str]]` in main.py
- **Container**: Semantic versioned `k8s-news-engine-quality-service:v1.1.0`
- **Validation**: Local testing before deployment, real-time database verification
- **Standards**: Follows established development workflow with testing and documentation

#### Validation Results
- Successfully extracts entities from real articles
- Proper JSONB database storage and indexing
- Integrated processing pipeline working correctly
- Service processes articles continuously with NER data

### v1.0.x (Previous)
- Basic quality score calculation and event grouping
- Database integration and Kubernetes deployment