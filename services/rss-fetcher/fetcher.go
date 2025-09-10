package main

import (
	"context"
	"database/sql"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/go-co-op/gocron"
	_ "github.com/lib/pq"
	"github.com/mmcdole/gofeed"
	"github.com/sirupsen/logrus"
)

type RSSFetcher struct {
	db     *sql.DB
	client *http.Client
	parser *gofeed.Parser
	log    *logrus.Logger
}

type RSSFeed struct {
	ID                   int       `json:"id"`
	URL                  string    `json:"url"`
	OutletName           string    `json:"outlet_name"`
	LastFetched          *time.Time `json:"last_fetched"`
	FetchIntervalMinutes *int      `json:"fetch_interval_minutes"`
}

type Article struct {
	ID          int       `json:"id"`
	URL         string    `json:"url"`
	OutletName  string    `json:"outlet_name"`
	Title       string    `json:"title"`
	PublishedAt *time.Time `json:"published_at"`
	Author      *string   `json:"author"`
	Text        string    `json:"text"`
	RawHTML     string    `json:"raw_html"`
	RSSFeedID   int       `json:"rss_feed_id"`
}

func NewRSSFetcher() (*RSSFetcher, error) {
	// Database connection
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgresql://appuser:newsengine2024@localhost:5432/newsdb"
	}

	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	// HTTP client with timeout
	client := &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        10,
			IdleConnTimeout:     30 * time.Second,
			DisableCompression:  false,
		},
	}

	// RSS parser
	parser := gofeed.NewParser()
	parser.Client = client

	logger := logrus.New()
	logger.SetFormatter(&logrus.JSONFormatter{})

	return &RSSFetcher{
		db:     db,
		client: client,
		parser: parser,
		log:    logger,
	}, nil
}

func (f *RSSFetcher) Close() {
	if f.db != nil {
		f.db.Close()
	}
}

func (f *RSSFetcher) GetActiveFeeds() ([]RSSFeed, error) {
	query := `
		SELECT id, url, outlet_name, last_fetched, fetch_interval_minutes 
		FROM rss_feeds 
		WHERE active = TRUE
	`
	
	rows, err := f.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query active feeds: %w", err)
	}
	defer rows.Close()

	var feeds []RSSFeed
	for rows.Next() {
		var feed RSSFeed
		err := rows.Scan(
			&feed.ID,
			&feed.URL,
			&feed.OutletName,
			&feed.LastFetched,
			&feed.FetchIntervalMinutes,
		)
		if err != nil {
			f.log.WithError(err).Error("Failed to scan feed row")
			continue
		}
		feeds = append(feeds, feed)
	}

	return feeds, rows.Err()
}

func (f *RSSFetcher) ShouldFetchFeed(feed RSSFeed) bool {
	if feed.LastFetched == nil {
		return true
	}

	interval := 30 // default 30 minutes
	if feed.FetchIntervalMinutes != nil {
		interval = *feed.FetchIntervalMinutes
	}

	nextFetch := feed.LastFetched.Add(time.Duration(interval) * time.Minute)
	return time.Now().UTC().After(nextFetch)
}

func (f *RSSFetcher) ParseFeed(feedURL string) (*gofeed.Feed, error) {
	f.log.WithField("url", feedURL).Debug("Parsing RSS feed")
	
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	feed, err := f.parser.ParseURLWithContext(feedURL, ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to parse feed %s: %w", feedURL, err)
	}

	return feed, nil
}

func (f *RSSFetcher) ExtractArticleContent(url string) (*Article, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")

	resp, err := f.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch article: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to parse HTML: %w", err)
	}

	// Extract text content
	doc.Find("script, style, nav, header, footer, aside").Remove()
	
	text := ""
	doc.Find("article, main, .content, .article-content, .post-content, p").Each(func(i int, s *goquery.Selection) {
		text += s.Text() + "\n"
	})

	// Fallback to body if no specific content found
	if strings.TrimSpace(text) == "" {
		text = doc.Find("body").Text()
	}

	// Clean up text
	lines := strings.Split(text, "\n")
	var cleanLines []string
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line != "" && len(line) > 10 { // Filter out very short lines
			cleanLines = append(cleanLines, line)
		}
	}
	text = strings.Join(cleanLines, "\n")

	// Limit text length
	if len(text) > 50000 {
		text = text[:50000]
	}

	// Get HTML
	html, _ := doc.Html()
	if len(html) > 100000 {
		html = html[:100000]
	}

	// Extract author from meta tags
	var author *string
	if authorText, exists := doc.Find(`meta[name="author"]`).Attr("content"); exists && authorText != "" {
		author = &authorText
	} else if authorText := doc.Find(".author, .byline, [rel='author']").First().Text(); authorText != "" {
		cleanAuthor := strings.TrimSpace(authorText)
		if cleanAuthor != "" {
			author = &cleanAuthor
		}
	}

	return &Article{
		Text:    text,
		RawHTML: html,
		Author:  author,
	}, nil
}

func (f *RSSFetcher) SaveArticle(feedID int, outlet string, item *gofeed.Item) (*int, error) {
	if item.Link == "" {
		return nil, fmt.Errorf("article has no link")
	}

	// Check if article already exists
	var existingID int
	err := f.db.QueryRow("SELECT id FROM articles WHERE url = $1", item.Link).Scan(&existingID)
	if err == nil {
		f.log.WithField("url", item.Link).Debug("Article already exists")
		return &existingID, nil
	} else if err != sql.ErrNoRows {
		return nil, fmt.Errorf("failed to check existing article: %w", err)
	}

	// Extract article content
	content, err := f.ExtractArticleContent(item.Link)
	if err != nil {
		f.log.WithError(err).WithField("url", item.Link).Warn("Failed to extract article content, using RSS content")
		// Fallback to RSS content
		content = &Article{
			Text:    item.Description,
			RawHTML: item.Description,
		}
	}

	// Parse publication date
	var publishedAt *time.Time
	if item.PublishedParsed != nil {
		publishedAt = item.PublishedParsed
	}

	// Combine authors
	var author *string
	if content.Author != nil {
		author = content.Author
	} else if len(item.Authors) > 0 {
		authors := make([]string, len(item.Authors))
		for i, a := range item.Authors {
			authors[i] = a.Name
		}
		authorStr := strings.Join(authors, ", ")
		author = &authorStr
	}

	// Insert article
	query := `
		INSERT INTO articles (url, outlet_name, title, published_at, author, text, raw_html, rss_feed_id)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		ON CONFLICT (url) DO UPDATE SET
			text = COALESCE(EXCLUDED.text, articles.text),
			raw_html = COALESCE(EXCLUDED.raw_html, articles.raw_html)
		RETURNING id
	`

	var articleID int
	err = f.db.QueryRow(
		query,
		item.Link,
		outlet,
		truncateString(item.Title, 500),
		publishedAt,
		author,
		content.Text,
		content.RawHTML,
		feedID,
	).Scan(&articleID)

	if err != nil {
		return nil, fmt.Errorf("failed to save article: %w", err)
	}

	f.log.WithFields(logrus.Fields{
		"article_id": articleID,
		"title":      truncateString(item.Title, 80),
		"url":        item.Link,
	}).Info("Saved article")

	return &articleID, nil
}

func (f *RSSFetcher) LinkArticleToEvents(articleID int, title, text string) error {
	// Get active events
	query := `SELECT id, title, description FROM events WHERE active = TRUE`
	rows, err := f.db.Query(query)
	if err != nil {
		return fmt.Errorf("failed to query events: %w", err)
	}
	defer rows.Close()

	articleContent := strings.ToLower(title + " " + text)

	for rows.Next() {
		var eventID int
		var eventTitle string
		var eventDescription sql.NullString

		err := rows.Scan(&eventID, &eventTitle, &eventDescription)
		if err != nil {
			f.log.WithError(err).Error("Failed to scan event row")
			continue
		}

		// Simple keyword matching
		eventText := eventTitle
		if eventDescription.Valid {
			eventText += " " + eventDescription.String
		}
		
		eventKeywords := strings.Fields(strings.ToLower(eventText))
		
		// Count meaningful keyword matches (words longer than 3 characters)
		matches := 0
		meaningfulKeywords := 0
		for _, keyword := range eventKeywords {
			if len(keyword) > 3 {
				meaningfulKeywords++
				if strings.Contains(articleContent, keyword) {
					matches++
				}
			}
		}

		if meaningfulKeywords == 0 {
			continue
		}

		relevance := float64(matches) / float64(meaningfulKeywords)
		
		// Link if relevance > 20%
		if relevance > 0.2 {
			_, err := f.db.Exec(`
				INSERT INTO event_articles (event_id, article_id, relevance_score)
				VALUES ($1, $2, $3)
				ON CONFLICT DO NOTHING
			`, eventID, articleID, relevance)
			
			if err != nil {
				f.log.WithError(err).Error("Failed to link article to event")
			} else {
				f.log.WithFields(logrus.Fields{
					"article_id": articleID,
					"event_id":   eventID,
					"relevance":  relevance,
				}).Info("Linked article to event")
			}
		}
	}

	return rows.Err()
}

func (f *RSSFetcher) UpdateFeedTimestamp(feedID int) error {
	_, err := f.db.Exec("UPDATE rss_feeds SET last_fetched = NOW() WHERE id = $1", feedID)
	if err != nil {
		return fmt.Errorf("failed to update feed timestamp: %w", err)
	}
	return nil
}

func (f *RSSFetcher) ProcessFeed(feed RSSFeed) error {
	f.log.WithFields(logrus.Fields{
		"outlet": feed.OutletName,
		"url":    feed.URL,
	}).Info("Processing RSS feed")

	// Parse RSS feed
	parsedFeed, err := f.ParseFeed(feed.URL)
	if err != nil {
		return fmt.Errorf("failed to parse feed: %w", err)
	}

	if len(parsedFeed.Items) == 0 {
		f.log.WithField("outlet", feed.OutletName).Warn("No items found in feed")
		return nil
	}

	// Process items (limit to 20 most recent)
	itemsToProcess := parsedFeed.Items
	if len(itemsToProcess) > 20 {
		itemsToProcess = itemsToProcess[:20]
	}

	newArticles := 0
	for _, item := range itemsToProcess {
		articleID, err := f.SaveArticle(feed.ID, feed.OutletName, item)
		if err != nil {
			f.log.WithError(err).WithField("url", item.Link).Error("Failed to save article")
			continue
		}

		if articleID != nil {
			newArticles++
			// Link to events
			err = f.LinkArticleToEvents(*articleID, item.Title, item.Description)
			if err != nil {
				f.log.WithError(err).Error("Failed to link article to events")
			}
		}

		// Rate limiting
		time.Sleep(100 * time.Millisecond)
	}

	// Update feed timestamp
	if err := f.UpdateFeedTimestamp(feed.ID); err != nil {
		f.log.WithError(err).Error("Failed to update feed timestamp")
	}

	f.log.WithFields(logrus.Fields{
		"outlet":       feed.OutletName,
		"total_items":  len(itemsToProcess),
		"new_articles": newArticles,
	}).Info("Completed processing feed")

	return nil
}

func (f *RSSFetcher) RunOnce() error {
	// Get active feeds directly from database
	feeds, err := f.GetActiveFeeds()
	if err != nil {
		return fmt.Errorf("failed to get active feeds: %w", err)
	}

	f.log.WithField("feed_count", len(feeds)).Info("Retrieved active feeds")

	for _, feed := range feeds {
		if f.ShouldFetchFeed(feed) {
			if err := f.ProcessFeed(feed); err != nil {
				f.log.WithError(err).WithField("outlet", feed.OutletName).Error("Failed to process feed")
			}
			// Rate limiting between feeds
			time.Sleep(2 * time.Second)
		} else {
			f.log.WithField("outlet", feed.OutletName).Debug("Skipping feed (not due for fetch)")
		}
	}

	return nil
}

func (f *RSSFetcher) RunContinuous(ctx context.Context) error {
	// Get fetch interval from environment
	fetchInterval := defaultFetchInterval
	if intervalStr := os.Getenv("FETCH_INTERVAL"); intervalStr != "" {
		if interval, err := strconv.Atoi(intervalStr); err == nil {
			fetchInterval = interval
		}
	}

	f.log.WithField("interval", fetchInterval).Info("Starting continuous RSS fetching")

	// Run once immediately
	if err := f.RunOnce(); err != nil {
		f.log.WithError(err).Error("Initial run failed")
	}

	// Setup scheduler
	s := gocron.NewScheduler(time.UTC)
	_, err := s.Every(fetchInterval).Seconds().Do(func() {
		if err := f.RunOnce(); err != nil {
			f.log.WithError(err).Error("Scheduled run failed")
		}
	})
	if err != nil {
		return fmt.Errorf("failed to schedule RSS fetching: %w", err)
	}

	// Start scheduler
	s.StartAsync()

	// Wait for context cancellation
	<-ctx.Done()
	
	f.log.Info("Shutting down RSS fetcher")
	s.Stop()
	
	return nil
}

func truncateString(s string, length int) string {
	if len(s) <= length {
		return s
	}
	return s[:length]
}