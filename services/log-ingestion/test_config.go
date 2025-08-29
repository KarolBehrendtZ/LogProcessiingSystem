package main

import (
    "fmt"
    "log"
    "log-processing-system/services/log-ingestion/config"
)

func main() {
    fmt.Println("Testing configuration loading...")
    
    cfg, err := config.LoadConfig()
    if err != nil {
        log.Fatalf("Failed to load configuration: %v", err)
    }
    
    fmt.Printf("Server will run on: %s:%d\n", cfg.Server.Host, cfg.Server.Port)
    fmt.Printf("Database URL: %s\n", cfg.Database.URL)
    fmt.Printf("Log Level: %s\n", cfg.Log.Level)
    fmt.Printf("Log Format: %s\n", cfg.Log.Format)
    
    fmt.Println("Configuration loaded successfully!")
}
