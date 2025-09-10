--
-- PostgreSQL database dump
--

\restrict uI1pj3WCCxwMlfP2nydnmWsUaMEcXQYgp4p65A5LwDbYK4D6dDBg05tulKCALal

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: map_outlet_to_agency_name(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.map_outlet_to_agency_name(outlet_name text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE
    AS $$
        BEGIN
            CASE LOWER(TRIM(outlet_name))
                -- BBC variations
                WHEN 'bbc news' THEN RETURN 'BBC News';
                WHEN 'bbc' THEN RETURN 'BBC News';
                WHEN 'bbc world' THEN RETURN 'BBC News';
                -- CNN variations  
                WHEN 'cnn' THEN RETURN 'CNN';
                WHEN 'cnn top stories' THEN RETURN 'CNN';
                WHEN 'cnn.com' THEN RETURN 'CNN';
                -- Reuters variations
                WHEN 'reuters' THEN RETURN 'Reuters';
                WHEN 'reuters top news' THEN RETURN 'Reuters';
                WHEN 'reuters.com' THEN RETURN 'Reuters';
                -- ABC News variations
                WHEN 'abc news' THEN RETURN 'ABC News';
                WHEN 'abc' THEN RETURN 'ABC News';
                WHEN 'abcnews.com' THEN RETURN 'ABC News';
                -- CBS variations
                WHEN 'cbs news' THEN RETURN 'CBS News';
                WHEN 'cbs' THEN RETURN 'CBS News';
                WHEN 'cbsnews.com' THEN RETURN 'CBS News';
                -- NBC variations
                WHEN 'nbc news' THEN RETURN 'NBC News';
                WHEN 'nbc' THEN RETURN 'NBC News';
                WHEN 'nbcnews.com' THEN RETURN 'NBC News';
                -- PBS variations
                WHEN 'pbs newshour' THEN RETURN 'PBS NewsHour';
                WHEN 'pbs' THEN RETURN 'PBS NewsHour';
                WHEN 'newshour' THEN RETURN 'PBS NewsHour';
                -- Politico variations
                WHEN 'politico' THEN RETURN 'Politico';
                WHEN 'politico.com' THEN RETURN 'Politico';
                -- VOA variations
                WHEN 'voa news' THEN RETURN 'VOA News';
                WHEN 'voa' THEN RETURN 'VOA News';
                WHEN 'voice of america' THEN RETURN 'VOA News';
                -- Al Jazeera variations
                WHEN 'al jazeera' THEN RETURN 'Al Jazeera';
                WHEN 'aljazeera' THEN RETURN 'Al Jazeera';
                WHEN 'aljazeera.com' THEN RETURN 'Al Jazeera';
                -- Sky News variations
                WHEN 'sky news' THEN RETURN 'Sky News';
                WHEN 'sky news world' THEN RETURN 'Sky News';
                WHEN 'skynews.com' THEN RETURN 'Sky News';
                -- Democracy Now variations
                WHEN 'democracy now' THEN RETURN 'Democracy Now';
                WHEN 'democracynow.org' THEN RETURN 'Democracy Now';
                -- Zerohedge variations
                WHEN 'zerohedge' THEN RETURN 'Zerohedge';
                WHEN 'zerohedge.com' THEN RETURN 'Zerohedge';
                WHEN 'zero hedge' THEN RETURN 'Zerohedge';
                -- Deutsche Welle variations
                WHEN 'deutsche welle' THEN RETURN 'Deutsche Welle';
                WHEN 'dw' THEN RETURN 'Deutsche Welle';
                WHEN 'dw.com' THEN RETURN 'Deutsche Welle';
                -- TechCrunch variations
                WHEN 'techcrunch' THEN RETURN 'TechCrunch';
                WHEN 'techcrunch.com' THEN RETURN 'TechCrunch';
                WHEN 'tech crunch' THEN RETURN 'TechCrunch';
                -- Guardian variations
                WHEN 'the guardian' THEN RETURN 'The Guardian';
                WHEN 'guardian' THEN RETURN 'The Guardian';
                WHEN 'theguardian.com' THEN RETURN 'The Guardian';
                WHEN 'the guardian world' THEN RETURN 'The Guardian';
                -- NPR variations
                WHEN 'npr' THEN RETURN 'NPR';
                WHEN 'npr news' THEN RETURN 'NPR';
                WHEN 'national public radio' THEN RETURN 'NPR';
                -- Associated Press variations
                WHEN 'associated press' THEN RETURN 'Associated Press';
                WHEN 'ap news' THEN RETURN 'Associated Press';
                WHEN 'ap' THEN RETURN 'Associated Press';
                -- New York Times variations
                WHEN 'the new york times' THEN RETURN 'The New York Times';
                WHEN 'new york times' THEN RETURN 'The New York Times';
                WHEN 'nytimes' THEN RETURN 'The New York Times';
                WHEN 'nyt' THEN RETURN 'The New York Times';
                -- Washington Post variations
                WHEN 'the washington post' THEN RETURN 'The Washington Post';
                WHEN 'washington post' THEN RETURN 'The Washington Post';
                WHEN 'washpost' THEN RETURN 'The Washington Post';
                -- Fox News variations
                WHEN 'fox news' THEN RETURN 'Fox News';
                WHEN 'fox' THEN RETURN 'Fox News';
                WHEN 'foxnews.com' THEN RETURN 'Fox News';
                -- ProPublica variations
                WHEN 'propublica' THEN RETURN 'ProPublica';
                WHEN 'pro publica' THEN RETURN 'ProPublica';
                ELSE RETURN NULL;
            END CASE;
        END;
        $$;


ALTER FUNCTION public.map_outlet_to_agency_name(outlet_name text) OWNER TO postgres;

--
-- Name: FUNCTION map_outlet_to_agency_name(outlet_name text); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.map_outlet_to_agency_name(outlet_name text) IS 'Maps RSS feed outlet names to standardized news agency names for foreign key relationships';


--
-- Name: update_reputation_metrics_timestamp(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_reputation_metrics_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_reputation_metrics_timestamp() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: article_writing_quality_cache; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.article_writing_quality_cache (
    article_id bigint NOT NULL,
    writing_quality_score numeric(5,2) NOT NULL,
    flesch_reading_ease numeric(5,2),
    flesch_kincaid_grade numeric(4,2),
    readability_score integer,
    lead_quality_score integer,
    source_attribution_score integer,
    factual_completeness_score integer,
    sentence_variety_score integer,
    vocabulary_precision_score integer,
    grammar_score integer,
    bias_score integer,
    balance_score integer,
    computed_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.article_writing_quality_cache OWNER TO postgres;

--
-- Name: TABLE article_writing_quality_cache; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.article_writing_quality_cache IS 'Performance cache for writing quality analysis results';


--
-- Name: articles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.articles (
    id bigint NOT NULL,
    url text,
    outlet_name character varying(255) NOT NULL,
    title text,
    published_at timestamp with time zone,
    author text,
    text text,
    raw_html text,
    fetched_at timestamp with time zone,
    rss_feed_id bigint,
    quality_score numeric,
    computed_event_id bigint,
    quality_computed_at timestamp with time zone,
    ner_persons jsonb,
    ner_organizations jsonb,
    ner_locations jsonb,
    ner_dates jsonb,
    ner_others jsonb,
    ner_extracted_at timestamp with time zone,
    reputation_score numeric,
    writing_quality_score numeric,
    composite_quality_score numeric
);


ALTER TABLE public.articles OWNER TO postgres;

--
-- Name: articles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.articles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.articles_id_seq OWNER TO postgres;

--
-- Name: articles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.articles_id_seq OWNED BY public.articles.id;


--
-- Name: claims; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.claims (
    id bigint NOT NULL,
    article_id bigint NOT NULL,
    claim_text text NOT NULL,
    claim_type text,
    verified_state text,
    verification_source text,
    extracted_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.claims OWNER TO postgres;

--
-- Name: claims_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.claims_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.claims_id_seq OWNER TO postgres;

--
-- Name: claims_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.claims_id_seq OWNED BY public.claims.id;


--
-- Name: event_articles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event_articles (
    event_id bigint NOT NULL,
    article_id bigint NOT NULL,
    relevance_score numeric DEFAULT 1.0,
    added_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.event_articles OWNER TO postgres;

--
-- Name: event_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event_metrics (
    event_id bigint NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    age_days numeric,
    coverage_sites integer,
    keyword_coherence numeric,
    best_source text,
    corroboration_ratio numeric,
    contradiction_rate numeric,
    correction_risk numeric,
    eqis_score numeric,
    components jsonb
);


ALTER TABLE public.event_metrics OWNER TO postgres;

--
-- Name: events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.events (
    id bigint NOT NULL,
    title text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    active boolean DEFAULT true
);


ALTER TABLE public.events OWNER TO postgres;

--
-- Name: events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.events_id_seq OWNER TO postgres;

--
-- Name: events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.events_id_seq OWNED BY public.events.id;


--
-- Name: news_agency_reputation_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.news_agency_reputation_metrics (
    id bigint NOT NULL,
    outlet_name character varying(255) NOT NULL,
    pulitzer_awards integer DEFAULT 0,
    pulitzer_years text[],
    murrow_awards integer DEFAULT 0,
    murrow_years text[],
    peabody_awards integer DEFAULT 0,
    peabody_years text[],
    emmy_awards integer DEFAULT 0,
    emmy_years text[],
    george_polk_awards integer DEFAULT 0,
    george_polk_years text[],
    dupont_awards integer DEFAULT 0,
    dupont_years text[],
    spj_awards integer DEFAULT 0,
    spj_years text[],
    other_specialized_awards integer DEFAULT 0,
    other_awards_details text[],
    press_freedom_ranking integer,
    industry_memberships text[],
    editorial_independence_rating numeric(3,1),
    fact_checking_standards boolean DEFAULT false,
    correction_policy_exists boolean DEFAULT false,
    retraction_transparency boolean DEFAULT false,
    ownership_transparency boolean DEFAULT false,
    funding_disclosure boolean DEFAULT false,
    ethics_code_public boolean DEFAULT false,
    total_awards_score integer DEFAULT 0,
    professional_standing_score integer DEFAULT 0,
    credibility_score integer DEFAULT 0,
    final_reputation_score numeric(5,2) DEFAULT 0,
    last_research_date date,
    research_notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.news_agency_reputation_metrics OWNER TO postgres;

--
-- Name: TABLE news_agency_reputation_metrics; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.news_agency_reputation_metrics IS 'Comprehensive repository for journalism awards, professional recognition, and credibility indicators for news organizations';


--
-- Name: news_agency_reputation_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.news_agency_reputation_metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.news_agency_reputation_metrics_id_seq OWNER TO postgres;

--
-- Name: news_agency_reputation_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.news_agency_reputation_metrics_id_seq OWNED BY public.news_agency_reputation_metrics.id;


--
-- Name: outlet_authority; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.outlet_authority (
    id integer NOT NULL,
    outlet_name character varying(255) NOT NULL,
    authority_score integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT outlet_authority_authority_score_check CHECK (((authority_score >= 0) AND (authority_score <= 40)))
);


ALTER TABLE public.outlet_authority OWNER TO postgres;

--
-- Name: outlet_authority_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.outlet_authority_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.outlet_authority_id_seq OWNER TO postgres;

--
-- Name: outlet_authority_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.outlet_authority_id_seq OWNED BY public.outlet_authority.id;


--
-- Name: outlet_reputation_scores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.outlet_reputation_scores (
    id bigint NOT NULL,
    outlet character varying NOT NULL,
    outlet_name character varying NOT NULL,
    reputation_score numeric DEFAULT 0 NOT NULL,
    reputation_metrics_id bigint,
    total_major_awards integer DEFAULT 0,
    has_fact_checking boolean DEFAULT false,
    press_freedom_tier character varying,
    last_updated timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.outlet_reputation_scores OWNER TO postgres;

--
-- Name: rss_feeds; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rss_feeds (
    id bigint NOT NULL,
    url text NOT NULL,
    outlet_name character varying(255) NOT NULL,
    last_fetched timestamp with time zone,
    active boolean,
    fetch_interval_minutes integer,
    category text,
    news_agency_id bigint
);


ALTER TABLE public.rss_feeds OWNER TO postgres;

--
-- Name: rss_feeds_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rss_feeds_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.rss_feeds_id_seq OWNER TO postgres;

--
-- Name: rss_feeds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rss_feeds_id_seq OWNED BY public.rss_feeds.id;


--
-- Name: articles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles ALTER COLUMN id SET DEFAULT nextval('public.articles_id_seq'::regclass);


--
-- Name: claims id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.claims ALTER COLUMN id SET DEFAULT nextval('public.claims_id_seq'::regclass);


--
-- Name: events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events ALTER COLUMN id SET DEFAULT nextval('public.events_id_seq'::regclass);


--
-- Name: news_agency_reputation_metrics id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.news_agency_reputation_metrics ALTER COLUMN id SET DEFAULT nextval('public.news_agency_reputation_metrics_id_seq'::regclass);


--
-- Name: outlet_authority id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.outlet_authority ALTER COLUMN id SET DEFAULT nextval('public.outlet_authority_id_seq'::regclass);


--
-- Name: rss_feeds id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rss_feeds ALTER COLUMN id SET DEFAULT nextval('public.rss_feeds_id_seq'::regclass);


--
-- Name: article_writing_quality_cache article_writing_quality_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_writing_quality_cache
    ADD CONSTRAINT article_writing_quality_cache_pkey PRIMARY KEY (article_id);


--
-- Name: articles articles_new_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_new_pkey PRIMARY KEY (id);


--
-- Name: claims claims_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.claims
    ADD CONSTRAINT claims_pkey PRIMARY KEY (id);


--
-- Name: event_articles event_articles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_articles
    ADD CONSTRAINT event_articles_pkey PRIMARY KEY (event_id, article_id);


--
-- Name: event_metrics event_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_metrics
    ADD CONSTRAINT event_metrics_pkey PRIMARY KEY (event_id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: news_agency_reputation_metrics news_agency_reputation_metrics_outlet_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.news_agency_reputation_metrics
    ADD CONSTRAINT news_agency_reputation_metrics_outlet_name_key UNIQUE (outlet_name);


--
-- Name: news_agency_reputation_metrics news_agency_reputation_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.news_agency_reputation_metrics
    ADD CONSTRAINT news_agency_reputation_metrics_pkey PRIMARY KEY (id);


--
-- Name: outlet_authority outlet_authority_outlet_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.outlet_authority
    ADD CONSTRAINT outlet_authority_outlet_name_key UNIQUE (outlet_name);


--
-- Name: outlet_authority outlet_authority_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.outlet_authority
    ADD CONSTRAINT outlet_authority_pkey PRIMARY KEY (id);


--
-- Name: outlet_reputation_scores outlet_reputation_scores_new_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.outlet_reputation_scores
    ADD CONSTRAINT outlet_reputation_scores_new_pkey PRIMARY KEY (id);


--
-- Name: rss_feeds rss_feeds_new_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rss_feeds
    ADD CONSTRAINT rss_feeds_new_pkey PRIMARY KEY (id);


--
-- Name: articles_url_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX articles_url_key ON public.articles USING btree (url);


--
-- Name: idx_articles_composite_quality_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_articles_composite_quality_score ON public.articles USING btree (composite_quality_score) WHERE (composite_quality_score IS NOT NULL);


--
-- Name: idx_articles_ner_locations; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_articles_ner_locations ON public.articles USING gin (ner_locations);


--
-- Name: idx_articles_ner_organizations; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_articles_ner_organizations ON public.articles USING gin (ner_organizations);


--
-- Name: idx_articles_ner_persons; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_articles_ner_persons ON public.articles USING gin (ner_persons);


--
-- Name: idx_articles_outlet_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_articles_outlet_name ON public.articles USING btree (outlet_name);


--
-- Name: idx_articles_published; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_articles_published ON public.articles USING btree (published_at);


--
-- Name: idx_articles_reputation_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_articles_reputation_score ON public.articles USING btree (reputation_score) WHERE (reputation_score IS NOT NULL);


--
-- Name: idx_articles_writing_quality_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_articles_writing_quality_score ON public.articles USING btree (writing_quality_score) WHERE (writing_quality_score IS NOT NULL);


--
-- Name: idx_claims_article; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_claims_article ON public.claims USING btree (article_id);


--
-- Name: idx_claims_state; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_claims_state ON public.claims USING btree (verified_state);


--
-- Name: idx_event_articles_article; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_event_articles_article ON public.event_articles USING btree (article_id);


--
-- Name: idx_event_articles_event; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_event_articles_event ON public.event_articles USING btree (event_id);


--
-- Name: idx_outlet_reputation_outlet; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outlet_reputation_outlet ON public.outlet_reputation_scores USING btree (outlet);


--
-- Name: idx_outlet_reputation_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outlet_reputation_score ON public.outlet_reputation_scores USING btree (reputation_score);


--
-- Name: idx_outlet_reputation_scores_outlet_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outlet_reputation_scores_outlet_name ON public.outlet_reputation_scores USING btree (outlet_name);


--
-- Name: idx_reputation_metrics_final_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reputation_metrics_final_score ON public.news_agency_reputation_metrics USING btree (final_reputation_score);


--
-- Name: idx_reputation_metrics_outlet_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reputation_metrics_outlet_name ON public.news_agency_reputation_metrics USING btree (outlet_name);


--
-- Name: idx_rss_feeds_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_rss_feeds_active ON public.rss_feeds USING btree (active) WHERE (active = true);


--
-- Name: idx_rss_feeds_outlet_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_rss_feeds_outlet_name ON public.rss_feeds USING btree (outlet_name);


--
-- Name: idx_rss_feedss_agency_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_rss_feedss_agency_id ON public.rss_feeds USING btree (news_agency_id);


--
-- Name: idx_writing_quality_cache_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_writing_quality_cache_score ON public.article_writing_quality_cache USING btree (writing_quality_score);


--
-- Name: outlet_reputation_scores_outlet_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX outlet_reputation_scores_outlet_key ON public.outlet_reputation_scores USING btree (outlet);


--
-- Name: rss_feeds_url_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX rss_feeds_url_key ON public.rss_feeds USING btree (url);


--
-- Name: outlet_reputation_scores trigger_update_outlet_reputation_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_update_outlet_reputation_timestamp BEFORE UPDATE ON public.outlet_reputation_scores FOR EACH ROW EXECUTE FUNCTION public.update_reputation_metrics_timestamp();


--
-- Name: news_agency_reputation_metrics trigger_update_reputation_metrics_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_update_reputation_metrics_timestamp BEFORE UPDATE ON public.news_agency_reputation_metrics FOR EACH ROW EXECUTE FUNCTION public.update_reputation_metrics_timestamp();


--
-- Name: event_articles event_articles_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_articles
    ADD CONSTRAINT event_articles_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id);


--
-- Name: event_metrics event_metrics_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_metrics
    ADD CONSTRAINT event_metrics_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id);


--
-- Name: outlet_reputation_scores outlet_reputation_scores_reputation_metrics_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.outlet_reputation_scores
    ADD CONSTRAINT outlet_reputation_scores_reputation_metrics_id_fkey FOREIGN KEY (reputation_metrics_id) REFERENCES public.news_agency_reputation_metrics(id);


--
-- Name: rss_feeds rss_feeds_news_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rss_feeds
    ADD CONSTRAINT rss_feeds_news_agency_id_fkey FOREIGN KEY (news_agency_id) REFERENCES public.news_agency_reputation_metrics(id);


--
-- Name: TABLE article_writing_quality_cache; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.article_writing_quality_cache TO appuser;


--
-- Name: TABLE articles; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.articles TO appuser;


--
-- Name: SEQUENCE articles_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.articles_id_seq TO appuser;


--
-- Name: TABLE claims; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.claims TO appuser;


--
-- Name: SEQUENCE claims_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.claims_id_seq TO appuser;


--
-- Name: TABLE event_articles; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.event_articles TO appuser;


--
-- Name: TABLE event_metrics; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.event_metrics TO appuser;


--
-- Name: TABLE events; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.events TO appuser;


--
-- Name: SEQUENCE events_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.events_id_seq TO appuser;


--
-- Name: TABLE news_agency_reputation_metrics; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.news_agency_reputation_metrics TO appuser;


--
-- Name: SEQUENCE news_agency_reputation_metrics_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.news_agency_reputation_metrics_id_seq TO appuser;


--
-- Name: TABLE outlet_authority; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.outlet_authority TO appuser;


--
-- Name: SEQUENCE outlet_authority_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.outlet_authority_id_seq TO appuser;


--
-- Name: TABLE outlet_reputation_scores; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.outlet_reputation_scores TO appuser;


--
-- Name: TABLE rss_feeds; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.rss_feeds TO appuser;


--
-- Name: SEQUENCE rss_feeds_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.rss_feeds_id_seq TO appuser;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES  TO appuser;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES  TO appuser;


--
-- PostgreSQL database dump complete
--

\unrestrict uI1pj3WCCxwMlfP2nydnmWsUaMEcXQYgp4p65A5LwDbYK4D6dDBg05tulKCALal

