package main

import (
	"fmt"
	"io/ioutil"
	"os"

	"gopkg.in/yaml.v3"
	"github.com/sirupsen/logrus"
)

type FeedConfig struct {
	URL      string `yaml:"url"`
	Outlet   string `yaml:"outlet"`
	Interval int    `yaml:"interval"`
	Category string `yaml:"category"`
}

type FeedsConfig struct {
	Feeds    []FeedConfig    `yaml:"feeds"`
	Defaults DefaultsConfig  `yaml:"defaults"`
}

type DefaultsConfig struct {
	Interval  int    `yaml:"interval"`
	Timeout   int    `yaml:"timeout"`
	Retries   int    `yaml:"retries"`
	UserAgent string `yaml:"user_agent"`
}

// LoadFeedsConfig loads RSS feed configuration from a YAML file
func LoadFeedsConfig(path string) (*FeedsConfig, error) {
	// Default path if not specified
	if path == "" {
		path = "/config/feeds.yaml"
	}

	// Check if file exists
	if _, err := os.Stat(path); os.IsNotExist(err) {
		// Return default configuration if file doesn't exist
		return getDefaultConfig(), nil
	}

	// Read the file
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	// Parse YAML
	var config FeedsConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse YAML config: %w", err)
	}

	// Apply defaults where needed
	for i := range config.Feeds {
		if config.Feeds[i].Interval == 0 {
			config.Feeds[i].Interval = config.Defaults.Interval
			if config.Feeds[i].Interval == 0 {
				config.Feeds[i].Interval = 30 // Default 30 minutes
			}
		}
	}

	return &config, nil
}

// getDefaultConfig returns a default configuration when ConfigMap is not available
func getDefaultConfig() *FeedsConfig {
	return &FeedsConfig{
		Feeds: []FeedConfig{
			{
				URL:      "https://feeds.bbci.co.uk/news/world/rss.xml",
				Outlet:   "BBC World",
				Interval: 15,
				Category: "world",
			},
			{
				URL:      "https://rss.cnn.com/rss/cnn_topstories.rss",
				Outlet:   "CNN Top Stories",
				Interval: 15,
				Category: "general",
			},
			{
				URL:      "https://feeds.reuters.com/reuters/topNews",
				Outlet:   "Reuters Top News",
				Interval: 10,
				Category: "general",
			},
		},
		Defaults: DefaultsConfig{
			Interval:  30,
			Timeout:   30,
			Retries:   3,
			UserAgent: userAgent,
		},
	}
}

// SyncFeedsWithDatabase syncs ConfigMap feeds with database
func (f *RSSFetcher) SyncFeedsWithDatabase(config *FeedsConfig) error {
	// First, mark all feeds as inactive
	_, err := f.db.Exec("UPDATE rss_feeds SET active = FALSE")
	if err != nil {
		return fmt.Errorf("failed to deactivate feeds: %w", err)
	}

	// Insert or update feeds from config
	for _, feed := range config.Feeds {
		query := `
			INSERT INTO rss_feeds (url, outlet, fetch_interval_minutes, active)
			VALUES ($1, $2, $3, TRUE)
			ON CONFLICT (url) DO UPDATE SET
				outlet = EXCLUDED.outlet,
				fetch_interval_minutes = EXCLUDED.fetch_interval_minutes,
				active = TRUE
		`
		
		_, err := f.db.Exec(query, feed.URL, feed.Outlet, feed.Interval)
		if err != nil {
			f.log.WithError(err).WithField("url", feed.URL).Error("Failed to sync feed")
			continue
		}
		
		f.log.WithFields(logrus.Fields{
			"outlet":   feed.Outlet,
			"url":      feed.URL,
			"interval": feed.Interval,
		}).Debug("Synced feed configuration")
	}

	f.log.WithField("feed_count", len(config.Feeds)).Info("Synced feeds from ConfigMap")
	return nil
}