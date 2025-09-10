import os, math, yaml, json, sys
from datetime import datetime, timezone
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://appuser:newsengine2024@postgresql.news-engine.svc.cluster.local:5432/newsdb")

def load_config():
    with open("configs/metrics.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_tables(engine):
    ddl = '''
    CREATE TABLE IF NOT EXISTS event_metrics (
      event_id BIGINT PRIMARY KEY,
      computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
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
    '''
    with engine.begin() as conn:
        for stmt in ddl.strip().split(';'):
            s = stmt.strip()
            if s:
                conn.execute(text(s))

def fetch_event_article_data(engine, event_id):
    sql = '''
    SELECT ar.id, ar.url, ar.outlet_name, ar.title, ar.published_at, ar.text
    FROM articles ar
    JOIN event_articles ea ON ea.article_id = ar.id
    WHERE ea.event_id = :eid
    ORDER BY ar.published_at NULLS LAST, ar.id ASC
    '''
    with engine.begin() as conn:
        rows = conn.execute(text(sql), {"eid": event_id}).mappings().all()
    return rows

def fetch_event_claims(engine, event_id):
    sql = '''
    SELECT c.id, c.article_id, c.claim_text, c.verified_state
    FROM claims c
    JOIN event_articles ea ON ea.article_id = c.article_id
    WHERE ea.event_id = :eid
    '''
    with engine.begin() as conn:
        rows = conn.execute(text(sql), {"eid": event_id}).mappings().all()
    return rows

def fetch_outlet_profiles(engine):
    # Use outlet_authority table instead of the dropped outlet_profiles table
    sql = 'SELECT outlet_name as domain, authority_score/100.0 as authority_weight FROM outlet_authority'
    with engine.begin() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    prof = {}
    for r in rows:
        prof[r["domain"]] = {"authority_weight": float(r["authority_weight"] or 0.8),
                             "correction_rate": 0.02,  # Default correction rate
                             "group": r["domain"]}  # Use domain as group
    return prof

def default_group(domain):
    d = (domain or "").lower()
    for p in ("www.", "m.", "mobile."):
        d = d.replace(p, "")
    return d

def score_days(articles, params):
    if not articles:
        return 0.0, 0.0, 0.0
    pub_times = [r["published_at"] for r in articles if r["published_at"]]
    if not pub_times:
        return 0.0, 0.0, 0.0
    first = min(pub_times)
    last  = max(pub_times)
    now = datetime.now(timezone.utc)
    age_days = (now - first).total_seconds()/86400.0
    unique_days = len(set(pd.to_datetime(pub_times).date))
    tau = float(params.get("recency_tau_days", 5))
    recency = math.exp(-max(0.0, (now - last).total_seconds()/86400.0)/tau)
    persistence = math.log(1+unique_days) / math.log(1+14)
    score = 100.0 * (0.6*recency + 0.4*persistence)
    return score, age_days, unique_days

def score_coverage(articles, outlet_profiles, params):
    if not articles:
        return 0.0, 0
    groups = set()
    for r in articles:
        dom = (r["outlet_name"] or "").lower()
        grp = outlet_profiles.get(dom, {}).get("group") or default_group(dom)
        groups.add(grp)
    coverage = len(groups)
    sat = float(params.get("coverage_saturation", 20))
    score = 100.0 * min(1.0, coverage/sat)
    return score, coverage

def score_coherence(articles, params):
    texts = [ (r["text"] or "").strip() for r in articles if (r.get("text") or "").strip() ]
    if len(texts) < int(params.get("coherence_min_articles", 2)):
        return 0.0
    # Use TF-IDF over all article texts (simple English stop words via scikit-learn)
    vec = TfidfVectorizer(stop_words="english", max_features=5000)
    X = vec.fit_transform(texts)
    # Average pairwise cosine
    sim = cosine_similarity(X)
    n = sim.shape[0]
    if n <= 1:
        return 0.0
    upper = sim[np.triu_indices(n, k=1)]
    coherence = float(np.mean(upper)) if upper.size else 0.0
    return 100.0 * coherence

def score_best_source(articles, claims, outlet_profiles):
    if not articles:
        return "", 0.0
    # Primacy: in first quartile of time
    pubs = [r["published_at"] for r in articles if r["published_at"]]
    if not pubs:
        return "", 0.0
    q1 = np.quantile([pd.Timestamp(p).value for p in pubs], 0.25)
    earliest_cut = pd.Timestamp(q1)

    # Aggregate per outlet
    per = defaultdict(lambda: {"verified":0, "total":0, "primacy":0.0})
    art_by_id = {r["id"]: r for r in articles}
    for c in claims:
        o = (art_by_id.get(c["article_id"], {}).get("outlet_name") or "").lower()
        if not o: 
            continue
        per[o]["total"] += 1
        if (c["verified_state"] or "").lower() == "verified":
            per[o]["verified"] += 1
    for r in articles:
        dom = (r["outlet_name"] or "").lower()
        if r["published_at"] and pd.Timestamp(r["published_at"]) <= earliest_cut:
            per[dom]["primacy"] += 1

    best_dom, best_score = "", -1.0
    for dom, stats in per.items():
        aw = float(outlet_profiles.get(dom, {}).get("authority_weight", 0.8))
        total = max(1, stats["total"])
        verified_share = stats["verified"]/total
        # Normalize primacy by number of articles from that outlet
        outlet_articles = sum(1 for r in articles if (r["outlet_name"] or "").lower()==dom)
        primacy = (stats["primacy"]/max(1,outlet_articles))
        s = 0.6*aw + 0.2*primacy + 0.2*verified_share
        if s > best_score:
            best_score = s
            best_dom = dom
    return best_dom, float(best_score)

def score_corroboration(claims):
    if not claims:
        return 0.0, 0.0, 0.0
    total = len(claims)
    verified = sum(1 for c in claims if (c["verified_state"] or "").lower()=="verified")
    contested = sum(1 for c in claims if (c["verified_state"] or "").lower()=="contested")
    contradiction_rate = contested/total
    ratio = verified/total
    score = 100.0 * ratio * (1.0 - contradiction_rate)
    return score, ratio, contradiction_rate

def score_correction_risk(articles, outlet_profiles, params):
    if not articles:
        return 0.0, 0.0
    counts = Counter((r["outlet_name"] or "").lower() for r in articles)
    total = sum(counts.values())
    risk = 0.0
    for dom, n in counts.items():
        rate = float(outlet_profiles.get(dom, {}).get("correction_rate", 0.02))
        share = n/total
        risk += share*rate
    cap = float(params.get("high_risk_cap", 0.05))
    score = 100.0 * (1.0 - min(1.0, risk/cap))
    return score, float(risk)

def compute_eqis(components, weights):
    # components are already 0..100 subscores
    return sum(weights.get(k,0.0)*components.get(k,0.0) for k in components.keys())

def list_events(engine):
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id FROM events ORDER BY id ASC")).fetchall()
    return [r[0] for r in rows]

def save_metrics(engine, event_id, comps, facts, eqis):
    payload = {
        "days": comps["days"],
        "coverage": comps["coverage"],
        "coherence": comps["coherence"],
        "best_source": comps["best_source"],
        "corroboration": comps["corroboration"],
        "correction_risk": comps["correction_risk"],
        "eqis": eqis,
        "facts": facts,
    }
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO event_metrics (event_id, age_days, coverage_sites, keyword_coherence,
              best_source, corroboration_ratio, contradiction_rate, correction_risk, eqis_score, components, computed_at)
            VALUES (:eid, :age, :sites, :coh, :best, :corr, :contr, :risk, :eqis, :components, now())
            ON CONFLICT (event_id) DO UPDATE SET
              age_days=EXCLUDED.age_days, coverage_sites=EXCLUDED.coverage_sites,
              keyword_coherence=EXCLUDED.keyword_coherence, best_source=EXCLUDED.best_source,
              corroboration_ratio=EXCLUDED.corroboration_ratio, contradiction_rate=EXCLUDED.contradiction_rate,
              correction_risk=EXCLUDED.correction_risk, eqis_score=EXCLUDED.eqis_score,
              components=EXCLUDED.components, computed_at=now()
        """), {
            "eid": event_id,
            "age": facts["age_days"],
            "sites": facts["site_count"],
            "coh": facts["coherence"],
            "best": facts["best_source"],
            "corr": facts["corroboration_ratio"],
            "contr": facts["contradiction_rate"],
            "risk": facts["correction_risk"],
            "eqis": eqis,
            "components": json.dumps({
                "days": comps["days"], "coverage": comps["coverage"], "coherence": comps["coherence"],
                "best_source": comps["best_source_score"], "corroboration": comps["corroboration"],
                "correction_risk": comps["correction_risk"]
            }),
        })

def main():
    cfg = load_config()
    weights = cfg.get("weights", {})
    params = cfg.get("params", {})
    engine = create_engine(DB_URL, future=True)
    ensure_tables(engine)

    events = list_events(engine)
    if not events:
        print("No events found. Exiting.")
        return

    outlet_profiles = fetch_outlet_profiles(engine)

    for eid in events:
        arts = fetch_event_article_data(engine, eid)
        cls  = fetch_event_claims(engine, eid)

        days_score, age_days, unique_days = score_days(arts, params)
        cov_score, site_count = score_coverage(arts, outlet_profiles, params)
        coh_score = score_coherence(arts, params)
        best_dom, best_dom_score = score_best_source(arts, cls, outlet_profiles)
        cor_score, cor_ratio, contr_rate = score_corroboration(cls)
        risk_score, risk_raw = score_correction_risk(arts, outlet_profiles, params)

        components = {
            "days": days_score,
            "coverage": cov_score,
            "coherence": coh_score,
            "best_source": best_dom,            # name only; not part of numeric combining
            "best_source_score": best_dom_score, # numeric part to combine if you want
            "corroboration": cor_score,
            "correction_risk": risk_score,
        }

        # Combine numeric components using weights; include best_source_score as numeric
        numeric = {
            "days": days_score,
            "coverage": cov_score,
            "coherence": coh_score,
            "best_source": best_dom_score,
            "corroboration": cor_score,
            "correction_risk": risk_score,
        }
        eqis = compute_eqis(numeric, weights)

        facts = {
            "age_days": age_days,
            "site_count": site_count,
            "coherence": coh_score,
            "best_source": best_dom,
            "corroboration_ratio": cor_ratio,
            "contradiction_rate": contr_rate,
            "correction_risk": risk_raw,
        }

        save_metrics(engine, eid, components, facts, eqis)
        print(f"Event {eid}: EQIS={eqis:.2f} comps={json.dumps(numeric)} best_source={best_dom}({best_dom_score:.2f})")

if __name__ == "__main__":
    main()
