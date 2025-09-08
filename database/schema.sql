-- K8s News Engine Database Schema
-- PostgreSQL schema for news verification and truth analysis system

-- News events (topics/stories being tracked)
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

-- RSS feed sources to monitor
CREATE TABLE IF NOT EXISTS rss_feeds (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    outlet TEXT NOT NULL,
    last_fetched TIMESTAMPTZ,
    active BOOLEAN DEFAULT TRUE,
    fetch_interval_minutes INT DEFAULT 30
);

-- Individual news articles
CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    outlet TEXT NOT NULL,
    title TEXT NOT NULL,
    published_at TIMESTAMPTZ,
    author TEXT,
    text TEXT,
    raw_html TEXT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rss_feed_id BIGINT REFERENCES rss_feeds(id)
);

-- Link events to articles (many-to-many)
CREATE TABLE IF NOT EXISTS event_articles (
    event_id BIGINT NOT NULL REFERENCES events(id),
    article_id BIGINT NOT NULL REFERENCES articles(id),
    relevance_score NUMERIC DEFAULT 1.0,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (event_id, article_id)
);

-- Extracted claims from articles
CREATE TABLE IF NOT EXISTS claims (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT NOT NULL REFERENCES articles(id),
    claim_text TEXT NOT NULL,
    claim_type TEXT, -- 'fact', 'opinion', 'prediction'
    verified_state TEXT, -- 'verified', 'contested', 'unverified'
    verification_source TEXT,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- News outlet profiles for authority scoring
CREATE TABLE IF NOT EXISTS outlet_profiles (
    domain TEXT PRIMARY KEY,
    authority_weight NUMERIC DEFAULT 0.8,
    correction_rate NUMERIC DEFAULT 0.02,
    independence_group TEXT,
    bias_rating TEXT, -- 'left', 'center-left', 'center', 'center-right', 'right'
    factual_reporting_score NUMERIC -- 0.0 to 1.0
);

-- Computed EQIS metrics (created by analytics service)
CREATE TABLE IF NOT EXISTS event_metrics (
    event_id BIGINT PRIMARY KEY REFERENCES events(id),
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    age_days NUMERIC,
    coverage_sites INT,
    keyword_coherence NUMERIC,
    best_source TEXT,
    corroboration_ratio NUMERIC,
    contradiction_rate NUMERIC,
    correction_risk NUMERIC,
    eqis_score NUMERIC,
    components JSONB
);

-- Indexes for performance
CREATE INDEX idx_articles_outlet ON articles(outlet);
CREATE INDEX idx_articles_published ON articles(published_at);
CREATE INDEX idx_event_articles_event ON event_articles(event_id);
CREATE INDEX idx_event_articles_article ON event_articles(article_id);
CREATE INDEX idx_claims_article ON claims(article_id);
CREATE INDEX idx_claims_state ON claims(verified_state);
CREATE INDEX idx_rss_feeds_active ON rss_feeds(active) WHERE active = TRUE;