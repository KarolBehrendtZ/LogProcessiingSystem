package main

import (
    "fmt"
    "log"
    "net/http"
    "log-processing-system/services/log-ingestion/config"
    "log-processing-system/services/log-ingestion/database"
    "log-processing-system/services/log-ingestion/handlers"
)

func main() {
    // Load configuration from .env file
    cfg, err := config.LoadConfig()
    if err != nil {
        log.Fatalf("Failed to load configuration: %v", err)
    }

    // Initialize database connection
    database.Connect(cfg.Database.URL)
    defer database.Close()

    // Setup routes
    http.HandleFunc("/ingest", handlers.HandleLogIngestion)
    http.HandleFunc("/logs", handlers.HandleLogIngestion) // Also support /logs endpoint for compatibility

    serverAddr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)
    log.Printf("Starting log ingestion service on %s", serverAddr)
    log.Printf("Database connected to: %s", cfg.Database.Host)
    
    if err := http.ListenAndServe(serverAddr, nil); err != nil {
        log.Fatalf("Could not start server: %s\n", err)
    }
}