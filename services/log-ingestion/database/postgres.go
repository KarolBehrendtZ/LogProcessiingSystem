package database

import (
    "database/sql"
    "time"
    "log-processing-system/services/log-ingestion/models"
    "log-processing-system/services/log-ingestion/logger"

    _ "github.com/lib/pq"
)

var db *sql.DB
var dbLogger = logger.NewFromEnv("log-ingestion", "database")

// Connect initializes the connection to the PostgreSQL database
func Connect(connStr string) error {
    start := time.Now()
    
    var err error
    db, err = sql.Open("postgres", connStr)
    if err != nil {
        dbLogger.WithError(err).Error("Failed to open database connection")
        return err
    }

    // Configure connection pool
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)
    db.SetConnMaxLifetime(5 * time.Minute)

    if err = db.Ping(); err != nil {
        dbLogger.WithError(err).Error("Failed to ping database")
        return err
    }

    duration := time.Since(start)
    dbLogger.WithFields(map[string]interface{}{
        "duration_ms":     duration.Milliseconds(),
        "max_open_conns":  25,
        "max_idle_conns":  5,
        "conn_max_lifetime": "5m",
    }).Info("Successfully connected to database")

    return nil
}

// StoreLog stores a log entry into the logs table
func StoreLog(logEntry models.Log) error {
    start := time.Now()
    
    query := `INSERT INTO logs (level, message, timestamp, source) VALUES ($1, $2, $3, $4)`
    result, err := db.Exec(query, logEntry.Level, logEntry.Message, logEntry.Timestamp, logEntry.Source)
    
    duration := time.Since(start)
    
    if err != nil {
        dbLogger.WithFields(map[string]interface{}{
            "operation":    "INSERT",
            "table":        "logs",
            "level":        logEntry.Level,
            "source":       logEntry.Source,
            "duration_ms":  duration.Milliseconds(),
            "error":        err.Error(),
        }).Error("Failed to store log entry")
        return err
    }

    rowsAffected, _ := result.RowsAffected()
    
    dbLogger.LogDatabaseOperation("INSERT", "logs", duration, rowsAffected)
    
    if duration > 100*time.Millisecond {
        dbLogger.WithFields(map[string]interface{}{
            "operation":   "INSERT",
            "table":       "logs",
            "duration_ms": duration.Milliseconds(),
        }).Warn("Slow database operation detected")
    }

    return nil
}

// InsertLog inserts a new log entry into the logs table (legacy method)
func InsertLog(logData string) error {
    start := time.Now()
    
    dbLogger.WithField("data_length", len(logData)).Debug("Inserting legacy log data")
    
    query := `INSERT INTO logs (data) VALUES ($1)`
    result, err := db.Exec(query, logData)
    
    duration := time.Since(start)
    
    if err != nil {
        dbLogger.WithFields(map[string]interface{}{
            "operation":    "INSERT",
            "table":        "logs",
            "data_length":  len(logData),
            "duration_ms":  duration.Milliseconds(),
            "error":        err.Error(),
        }).Error("Failed to insert legacy log data")
        return err
    }

    rowsAffected, _ := result.RowsAffected()
    dbLogger.LogDatabaseOperation("INSERT_LEGACY", "logs", duration, rowsAffected)

    return nil
}

// Ping checks if the database connection is alive
func Ping() error {
    if db == nil {
        dbLogger.Error("Database connection is nil")
        return sql.ErrConnDone
    }
    
    start := time.Now()
    err := db.Ping()
    duration := time.Since(start)
    
    if err != nil {
        dbLogger.WithFields(map[string]interface{}{
            "duration_ms": duration.Milliseconds(),
            "error":       err.Error(),
        }).Error("Database ping failed")
        return err
    }
    
    dbLogger.WithField("duration_ms", duration.Milliseconds()).Debug("Database ping successful")
    return nil
}

// Close closes the database connection
func Close() {
    if db != nil {
        if err := db.Close(); err != nil {
            dbLogger.WithError(err).Error("Error closing database connection")
        } else {
            dbLogger.Info("Database connection closed successfully")
        }
    }
}

// GetRecentLogs retrieves recent log entries for analysis
func GetRecentLogs(limit int) ([]models.Log, error) {
    start := time.Now()
    
    dbLogger.WithField("limit", limit).Debug("Retrieving recent logs")
    
    query := `SELECT id, level, message, timestamp, source FROM logs ORDER BY timestamp DESC LIMIT $1`
    rows, err := db.Query(query, limit)
    if err != nil {
        duration := time.Since(start)
        dbLogger.WithFields(map[string]interface{}{
            "operation":   "SELECT",
            "table":       "logs",
            "limit":       limit,
            "duration_ms": duration.Milliseconds(),
            "error":       err.Error(),
        }).Error("Failed to retrieve recent logs")
        return nil, err
    }
    defer rows.Close()

    var logs []models.Log
    for rows.Next() {
        var logEntry models.Log
        err := rows.Scan(&logEntry.ID, &logEntry.Level, &logEntry.Message, &logEntry.Timestamp, &logEntry.Source)
        if err != nil {
            dbLogger.WithError(err).Error("Failed to scan log entry")
            return nil, err
        }
        logs = append(logs, logEntry)
    }

    duration := time.Since(start)
    dbLogger.LogDatabaseOperation("SELECT", "logs", duration, int64(len(logs)))

    return logs, nil
}

// GetLogsByTimeRange retrieves logs within a specific time range
func GetLogsByTimeRange(startTime, endTime string) ([]models.Log, error) {
    start := time.Now()
    
    dbLogger.WithFields(map[string]interface{}{
        "start_time": startTime,
        "end_time":   endTime,
    }).Debug("Retrieving logs by time range")
    
    query := `SELECT id, level, message, timestamp, source FROM logs WHERE timestamp BETWEEN $1 AND $2 ORDER BY timestamp DESC`
    rows, err := db.Query(query, startTime, endTime)
    if err != nil {
        duration := time.Since(start)
        dbLogger.WithFields(map[string]interface{}{
            "operation":   "SELECT",
            "table":       "logs",
            "start_time":  startTime,
            "end_time":    endTime,
            "duration_ms": duration.Milliseconds(),
            "error":       err.Error(),
        }).Error("Failed to retrieve logs by time range")
        return nil, err
    }
    defer rows.Close()

    var logs []models.Log
    for rows.Next() {
        var logEntry models.Log
        err := rows.Scan(&logEntry.ID, &logEntry.Level, &logEntry.Message, &logEntry.Timestamp, &logEntry.Source)
        if err != nil {
            dbLogger.WithError(err).Error("Failed to scan log entry")
            return nil, err
        }
        logs = append(logs, logEntry)
    }

    duration := time.Since(start)
    dbLogger.LogDatabaseOperation("SELECT_TIME_RANGE", "logs", duration, int64(len(logs)))

    return logs, nil
}

// GetLogsByLevel retrieves logs by specific level
func GetLogsByLevel(level string) ([]models.Log, error) {
    start := time.Now()
    
    dbLogger.WithField("level", level).Debug("Retrieving logs by level")
    
    query := `SELECT id, level, message, timestamp, source FROM logs WHERE level = $1 ORDER BY timestamp DESC`
    rows, err := db.Query(query, level)
    if err != nil {
        duration := time.Since(start)
        dbLogger.WithFields(map[string]interface{}{
            "operation":   "SELECT",
            "table":       "logs",
            "level":       level,
            "duration_ms": duration.Milliseconds(),
            "error":       err.Error(),
        }).Error("Failed to retrieve logs by level")
        return nil, err
    }
    defer rows.Close()

    var logs []models.Log
    for rows.Next() {
        var logEntry models.Log
        err := rows.Scan(&logEntry.ID, &logEntry.Level, &logEntry.Message, &logEntry.Timestamp, &logEntry.Source)
        if err != nil {
            dbLogger.WithError(err).Error("Failed to scan log entry")
            return nil, err
        }
        logs = append(logs, logEntry)
    }

    duration := time.Since(start)
    dbLogger.LogDatabaseOperation("SELECT_BY_LEVEL", "logs", duration, int64(len(logs)))

    return logs, nil
}

// GetDatabaseStats returns database statistics for monitoring
func GetDatabaseStats() (map[string]interface{}, error) {
    start := time.Now()
    
    stats := make(map[string]interface{})
    
    // Get connection stats
    dbStats := db.Stats()
    stats["open_connections"] = dbStats.OpenConnections
    stats["in_use"] = dbStats.InUse
    stats["idle"] = dbStats.Idle
    stats["wait_count"] = dbStats.WaitCount
    stats["wait_duration"] = dbStats.WaitDuration.String()
    stats["max_idle_closed"] = dbStats.MaxIdleClosed
    stats["max_lifetime_closed"] = dbStats.MaxLifetimeClosed
    
    // Get table stats
    var count int64
    err := db.QueryRow("SELECT COUNT(*) FROM logs").Scan(&count)
    if err != nil {
        dbLogger.WithError(err).Error("Failed to get log count")
        return nil, err
    }
    stats["total_logs"] = count
    
    duration := time.Since(start)
    dbLogger.WithFields(map[string]interface{}{
        "duration_ms": duration.Milliseconds(),
        "stats":       stats,
    }).Debug("Retrieved database statistics")
    
    return stats, nil
}