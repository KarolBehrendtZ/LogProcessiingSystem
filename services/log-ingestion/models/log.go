package models

import (
	"errors"
	"regexp"
	"time"
)

// Log represents the log data model
type Log struct {
	ID        int       `json:"id"`
	Message   string    `json:"message"`
	Level     string    `json:"level"`
	Timestamp time.Time `json:"timestamp"`
	Source    string    `json:"source"`
}

// Validate checks if the log data is valid
func (l *Log) Validate() error {
	if l.Message == "" {
		return errors.New("message cannot be empty")
	}
	if !isValidLogLevel(l.Level) {
		return errors.New("invalid log level")
	}
	if l.Timestamp.IsZero() {
		// Set current time if not provided
		l.Timestamp = time.Now()
	}
	if l.Source == "" {
		l.Source = "unknown"
	}
	return nil
}

// isValidLogLevel checks if the log level is valid
func isValidLogLevel(level string) bool {
	validLevels := []string{"DEBUG", "INFO", "WARN", "ERROR", "FATAL", "debug", "info", "warn", "error", "fatal"}
	for _, v := range validLevels {
		if level == v {
			return true
		}
	}
	return false
}

// isValidTimeFormat checks if the time format is valid (keeping for compatibility)
func isValidTimeFormat(timeStr string) bool {
	// Example regex for a simple time format check (RFC3339)
	re := regexp.MustCompile(`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`)
	return re.MatchString(timeStr)
}