package database

import (
    "database/sql"
    "log"
    "log-processing-system/services/log-ingestion/models"

    _ "github.com/lib/pq"
)

var db *sql.DB

// Connect initializes the connection to the PostgreSQL database
func Connect(connStr string) {
    var err error
    db, err = sql.Open("postgres", connStr)
    if err != nil {
        log.Fatalf("Error connecting to the database: %v", err)
    }

    if err = db.Ping(); err != nil {
        log.Fatalf("Error pinging the database: %v", err)
    }

    log.Println("Successfully connected to database")
}

// StoreLog stores a log entry into the logs table
func StoreLog(logEntry models.Log) error {
    query := `INSERT INTO logs (level, message, timestamp, source) VALUES ($1, $2, $3, $4)`
    _, err := db.Exec(query, logEntry.Level, logEntry.Message, logEntry.Timestamp, logEntry.Source)
    return err
}

// InsertLog inserts a new log entry into the logs table (legacy method)
func InsertLog(logData string) error {
    query := `INSERT INTO logs (data) VALUES ($1)`
    _, err := db.Exec(query, logData)
    return err
}

// Close closes the database connection
func Close() {
    if db != nil {
        if err := db.Close(); err != nil {
            log.Printf("Error closing the database: %v", err)
        } else {
            log.Println("Database connection closed")
        }
    }
}

// GetRecentLogs retrieves recent log entries for analysis
func GetRecentLogs(limit int) ([]models.Log, error) {
    query := `SELECT id, level, message, timestamp, source FROM logs ORDER BY timestamp DESC LIMIT $1`
    rows, err := db.Query(query, limit)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var logs []models.Log
    for rows.Next() {
        var logEntry models.Log
        err := rows.Scan(&logEntry.ID, &logEntry.Level, &logEntry.Message, &logEntry.Timestamp, &logEntry.Source)
        if err != nil {
            return nil, err
        }
        logs = append(logs, logEntry)
    }

    return logs, nil
}

// GetLogsByTimeRange retrieves logs within a specific time range
func GetLogsByTimeRange(startTime, endTime string) ([]models.Log, error) {
    query := `SELECT id, level, message, timestamp, source FROM logs WHERE timestamp BETWEEN $1 AND $2 ORDER BY timestamp DESC`
    rows, err := db.Query(query, startTime, endTime)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var logs []models.Log
    for rows.Next() {
        var logEntry models.Log
        err := rows.Scan(&logEntry.ID, &logEntry.Level, &logEntry.Message, &logEntry.Timestamp, &logEntry.Source)
        if err != nil {
            return nil, err
        }
        logs = append(logs, logEntry)
    }

    return logs, nil
}

// GetLogsByLevel retrieves logs by specific level
func GetLogsByLevel(level string) ([]models.Log, error) {
    query := `SELECT id, level, message, timestamp, source FROM logs WHERE level = $1 ORDER BY timestamp DESC`
    rows, err := db.Query(query, level)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var logs []models.Log
    for rows.Next() {
        var logEntry models.Log
        err := rows.Scan(&logEntry.ID, &logEntry.Level, &logEntry.Message, &logEntry.Timestamp, &logEntry.Source)
        if err != nil {
            return nil, err
        }
        logs = append(logs, logEntry)
    }

    return logs, nil
}