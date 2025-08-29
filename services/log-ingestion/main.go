package main

import (
    "context"
    "fmt"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
    "log-processing-system/services/log-ingestion/config"
    "log-processing-system/services/log-ingestion/database"
    "log-processing-system/services/log-ingestion/handlers"
    "log-processing-system/services/log-ingestion/logger"
    "log-processing-system/services/log-ingestion/middleware"
    "github.com/gorilla/mux"
)

func main() {
    // Initialize structured logger
    appLogger := logger.NewFromEnv("log-ingestion", "main")
    
    // Set up global context
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Load configuration from .env file
    cfg, err := config.LoadConfig()
    if err != nil {
        appLogger.WithError(err).Fatal("Failed to load configuration")
    }

    appLogger.WithFields(map[string]interface{}{
        "host":     cfg.Server.Host,
        "port":     cfg.Server.Port,
        "db_host":  cfg.Database.Host,
        "db_name":  cfg.Database.Name,
    }).Info("Configuration loaded successfully")

    // Initialize database connection
    if err := database.Connect(cfg.Database.URL); err != nil {
        appLogger.WithError(err).Fatal("Failed to connect to database")
    }
    defer database.Close()

    appLogger.WithField("db_host", cfg.Database.Host).Info("Database connection established")

    // Initialize middleware
    loggingMiddleware := middleware.NewLoggingMiddleware(appLogger.WithComponent("http"))

    // Setup router
    router := mux.NewRouter()
    
    // Apply middleware
    router.Use(loggingMiddleware.RecoveryMiddleware)
    router.Use(loggingMiddleware.SecurityHeadersMiddleware)
    router.Use(loggingMiddleware.CORSMiddleware)
    router.Use(loggingMiddleware.RateLimitMiddleware)
    router.Use(loggingMiddleware.HealthCheckMiddleware)

    // Setup routes
    router.HandleFunc("/ingest", handlers.HandleLogIngestion).Methods("POST")
    router.HandleFunc("/logs", handlers.HandleLogIngestion).Methods("POST") // Compatibility endpoint
    router.HandleFunc("/health", handlers.HandleHealthCheck).Methods("GET")
    router.HandleFunc("/healthz", handlers.HandleHealthCheck).Methods("GET")

    // Create HTTP server
    serverAddr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)
    server := &http.Server{
        Addr:         serverAddr,
        Handler:      router,
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 15 * time.Second,
        IdleTimeout:  60 * time.Second,
    }

    // Start server in a goroutine
    go func() {
        appLogger.WithFields(map[string]interface{}{
            "address": serverAddr,
            "env":     os.Getenv("ENVIRONMENT"),
        }).Info("Starting log ingestion service")

        if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            appLogger.WithError(err).Fatal("Could not start server")
        }
    }()

    // Wait for interrupt signal to gracefully shutdown the server
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    appLogger.Info("Shutting down server...")

    // Create context with timeout for graceful shutdown
    shutdownCtx, shutdownCancel := context.WithTimeout(ctx, 30*time.Second)
    defer shutdownCancel()

    // Shutdown server
    if err := server.Shutdown(shutdownCtx); err != nil {
        appLogger.WithError(err).Error("Server forced to shutdown")
    } else {
        appLogger.Info("Server shutdown completed")
    }
}