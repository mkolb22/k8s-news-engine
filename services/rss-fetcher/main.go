package main

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/joho/godotenv"
	"github.com/sirupsen/logrus"
)

const (
	defaultFetchInterval = 300 // 5 minutes
	userAgent           = "K8s-News-Engine-Go/1.0 (+https://github.com/k8s-news-engine)"
)

func main() {
	// Load environment variables
	_ = godotenv.Load()

	// Configure logging
	logrus.SetFormatter(&logrus.JSONFormatter{
		TimestampFormat: time.RFC3339,
	})
	logrus.SetLevel(logrus.InfoLevel)

	// Initialize fetcher
	fetcher, err := NewRSSFetcher()
	if err != nil {
		logrus.WithError(err).Fatal("Failed to initialize RSS fetcher")
	}
	defer fetcher.Close()

	// Check for --once flag
	runOnce := len(os.Args) > 1 && os.Args[1] == "--once"

	if runOnce {
		logrus.Info("Running RSS fetcher once")
		if err := fetcher.RunOnce(); err != nil {
			logrus.WithError(err).Fatal("Failed to run RSS fetcher")
		}
		return
	}

	// Run continuous fetching
	logrus.Info("Starting RSS fetcher service")
	
	// Setup graceful shutdown
	ctx, cancel := setupGracefulShutdown()
	defer cancel()

	// Start scheduler
	if err := fetcher.RunContinuous(ctx); err != nil {
		logrus.WithError(err).Fatal("RSS fetcher failed")
	}

	logrus.Info("RSS fetcher service stopped")
}

func setupGracefulShutdown() (context.Context, context.CancelFunc) {
	ctx, cancel := context.WithCancel(context.Background())
	
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	
	go func() {
		<-c
		logrus.Info("Received shutdown signal")
		cancel()
	}()
	
	return ctx, cancel
}