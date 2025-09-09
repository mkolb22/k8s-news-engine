# K8s News Engine - Project Overview

## Purpose
A Kubernetes-based microservices system for news verification and truth analysis. It processes news content to compute quality metrics, verify claims, and provide trustworthiness scores using the Event Quality & Impact Score (EQIS) algorithm.

## Architecture
Microservices architecture with the following services:

### Core Services
- **analytics-py**: Python service computing EQIS scores using scikit-learn for TF-IDF analysis
- **rss-fetcher**: Go service for fetching and processing RSS feeds (recently migrated from Python)
- **publisher**: Lighttpd-based service with CGI scripts for content delivery
- **claim-extractor**: Service for extracting claims from news articles

### Infrastructure
- **PostgreSQL database** with tables: events, articles, event_articles, claims, outlet_profiles, event_metrics, rss_feeds
- **Kubernetes**: Container orchestration and deployment
- **Docker**: Containerization of all services

## Current State
- Project is actively being developed with RSS fetcher recently migrated from Python to Go
- Services are containerized and have Kubernetes deployment configurations
- Database schema supports comprehensive news analysis workflow