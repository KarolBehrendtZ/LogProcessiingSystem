package handlers

import (
	"encoding/json"
	"net/http"
	"time"
	"log-processing-system/services/log-ingestion/models"
	"log-processing-system/services/log-ingestion/database"
)

func HandleLogIngestion(w http.ResponseWriter, r *http.Request) {
	// Read the request body
	var rawData map[string]interface{}
	
	if err := json.NewDecoder(r.Body).Decode(&rawData); err != nil {
		http.Error(w, "Invalid JSON format", http.StatusBadRequest)
		return
	}

	var logEntry models.Log

	// Check if this is the new structured format or legacy format
	if message, hasMessage := rawData["message"]; hasMessage {
		// New structured format
		logData, _ := json.Marshal(rawData)
		if err := json.Unmarshal(logData, &logEntry); err != nil {
			http.Error(w, "Invalid structured log entry", http.StatusBadRequest)
			return
		}
	} else if logText, hasLog := rawData["log"]; hasLog {
		// Legacy format - convert to structured format
		logEntry = models.Log{
			Message:   logText.(string),
			Level:     "info", // default level for legacy entries
			Timestamp: time.Now(),
			Source:    "legacy_api",
		}
	} else {
		http.Error(w, "Missing required fields: either 'message' or 'log' field required", http.StatusBadRequest)
		return
	}

	// Validate the log entry
	if err := logEntry.Validate(); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Store the log entry in the database
	if err := database.StoreLog(logEntry); err != nil {
		http.Error(w, "Failed to store log entry", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(map[string]string{"status": "accepted", "message": "Log entry stored successfully"})
}