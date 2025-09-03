package handlers

import (
	"encoding/json"
	"net/http"
	"time"
	"log-processing-system/services/log-ingestion/models"
	"log-processing-system/services/log-ingestion/database"
	"log-processing-system/services/log-ingestion/logger"
)

var handlerLogger = logger.NewFromEnv("log-ingestion", "handlers")

func HandleLogIngestion(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	requestID := logger.GetRequestID(r.Context())
	
	handlerLogger.WithFields(map[string]interface{}{
		"request_id":    requestID,
		"content_type":  r.Header.Get("Content-Type"),
		"content_length": r.ContentLength,
	}).InfoContext(r.Context(), "Processing log ingestion request")

	// Read the request body
	var rawData map[string]interface{}
	
	if err := json.NewDecoder(r.Body).Decode(&rawData); err != nil {
		handlerLogger.WithFields(map[string]interface{}{
			"request_id": requestID,
			"error":      err.Error(),
		}).WarnContext(r.Context(), "Failed to decode JSON request body")
		
		http.Error(w, "Invalid JSON format", http.StatusBadRequest)
		return
	}

	var logEntry models.Log

	// Check if this is the new structured format or legacy format
	if message, hasMessage := rawData["message"]; hasMessage {
		// New structured format
		handlerLogger.WithField("request_id", requestID).DebugContext(r.Context(), "Processing structured log format")
		
		logData, _ := json.Marshal(rawData)
		if err := json.Unmarshal(logData, &logEntry); err != nil {
			handlerLogger.WithFields(map[string]interface{}{
				"request_id": requestID,
				"error":      err.Error(),
				"raw_data":   rawData,
			}).WarnContext(r.Context(), "Failed to unmarshal structured log entry")
			
			http.Error(w, "Invalid structured log entry", http.StatusBadRequest)
			return
		}
	} else if logText, hasLog := rawData["log"]; hasLog {
		// Legacy format - convert to structured format
		handlerLogger.WithField("request_id", requestID).DebugContext(r.Context(), "Processing legacy log format")
		
		logEntry = models.Log{
			Message:   logText.(string),
			Level:     "info", // default level for legacy entries
			Timestamp: time.Now(),
			Source:    "legacy_api",
		}
		
		handlerLogger.WithFields(map[string]interface{}{
			"request_id":    requestID,
			"message_length": len(logEntry.Message),
			"source":        logEntry.Source,
		}).InfoContext(r.Context(), "Converted legacy log entry to structured format")
	} else {
		handlerLogger.WithFields(map[string]interface{}{
			"request_id": requestID,
			"raw_data":   rawData,
		}).WarnContext(r.Context(), "Request missing required fields")
		
		http.Error(w, "Missing required fields: either 'message' or 'log' field required", http.StatusBadRequest)
		return
	}

	// Validate the log entry
	if err := logEntry.Validate(); err != nil {
		handlerLogger.WithFields(map[string]interface{}{
			"request_id":     requestID,
			"validation_error": err.Error(),
			"log_entry":      logEntry,
		}).WarnContext(r.Context(), "Log entry validation failed")
		
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Store the log entry in the database
	dbStart := time.Now()
	if err := database.StoreLog(logEntry); err != nil {
		dbDuration := time.Since(dbStart)
		
		handlerLogger.WithFields(map[string]interface{}{
			"request_id":    requestID,
			"error":         err.Error(),
			"log_entry":     logEntry,
			"db_duration_ms": dbDuration.Milliseconds(),
		}).ErrorContext(r.Context(), "Failed to store log entry in database")
		
		http.Error(w, "Failed to store log entry", http.StatusInternalServerError)
		return
	}
	dbDuration := time.Since(dbStart)

	// Log successful storage
	handlerLogger.WithFields(map[string]interface{}{
		"request_id":     requestID,
		"log_level":      logEntry.Level,
		"log_source":     logEntry.Source,
		"message_length": len(logEntry.Message),
		"db_duration_ms": dbDuration.Milliseconds(),
		"total_duration_ms": time.Since(start).Milliseconds(),
	}).InfoContext(r.Context(), "Log entry stored successfully")

	// Log business event
	handlerLogger.LogBusinessEvent("log_ingested", requestID, map[string]interface{}{
		"log_level":  logEntry.Level,
		"log_source": logEntry.Source,
		"timestamp":  logEntry.Timestamp,
	})

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(map[string]string{
		"status":     "accepted", 
		"message":    "Log entry stored successfully",
		"request_id": requestID,
	})
}

func HandleHealthCheck(w http.ResponseWriter, r *http.Request) {
	requestID := logger.GetRequestID(r.Context())
	
	// Check database connectivity
	if err := database.Ping(); err != nil {
		handlerLogger.WithFields(map[string]interface{}{
			"request_id": requestID,
			"error":      err.Error(),
		}).ErrorContext(r.Context(), "Health check failed - database connectivity issue")
		
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status":  "unhealthy",
			"error":   "database connectivity issue",
			"timestamp": time.Now().UTC(),
		})
		return
	}

	handlerLogger.WithField("request_id", requestID).DebugContext(r.Context(), "Health check passed")
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().UTC(),
		"service":   "log-ingestion",
		"version":   "1.0.0",
	})
}