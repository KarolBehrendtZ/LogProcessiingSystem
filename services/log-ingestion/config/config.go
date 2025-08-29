package config

import (
    "fmt"
    "os"
    "path/filepath"
    "strconv"

    "github.com/joho/godotenv"
)

type Config struct {
    Server   ServerConfig
    Database DatabaseConfig
    Log      LogConfig
}

type ServerConfig struct {
    Host string
    Port int
}

type DatabaseConfig struct {
    Host     string
    Port     int
    User     string
    Password string
    DBName   string
    URL      string
}

type LogConfig struct {
    Level  string
    Format string
}

// LoadConfig loads configuration from .env file and environment variables
func LoadConfig() (*Config, error) {
    // Load .env file from project root (two levels up from current directory)
    envPath := filepath.Join("..", "..", ".env")
    if err := godotenv.Load(envPath); err != nil {
        // If .env file doesn't exist, that's okay - we'll use system env vars
        fmt.Printf("Warning: Could not load .env file from %s: %v\n", envPath, err)
    }

    config := &Config{
        Server: ServerConfig{
            Host: getEnv("SERVER_HOST", "0.0.0.0"),
            Port: getEnvAsInt("SERVER_PORT", 8080),
        },
        Database: DatabaseConfig{
            Host:     getEnv("DB_HOST", "localhost"),
            Port:     getEnvAsInt("DB_PORT", 5432),
            User:     getEnv("DB_USER", ""),
            Password: getEnv("DB_PASSWORD", ""),
            DBName:   getEnv("DB_NAME", "log_processing_db"),
            URL:      getEnv("DATABASE_URL", ""),
        },
        Log: LogConfig{
            Level:  getEnv("LOG_LEVEL", "info"),
            Format: getEnv("LOG_FORMAT", "json"),
        },
    }

    // If DATABASE_URL is not provided, construct it from individual components
    if config.Database.URL == "" {
        config.Database.URL = fmt.Sprintf(
            "postgres://%s:%s@%s:%d/%s?sslmode=disable",
            config.Database.User,
            config.Database.Password,
            config.Database.Host,
            config.Database.Port,
            config.Database.DBName,
        )
    }

    return config, nil
}

// getEnv gets an environment variable with a fallback value
func getEnv(key, fallback string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return fallback
}

// getEnvAsInt gets an environment variable as integer with a fallback value
func getEnvAsInt(key string, fallback int) int {
    if value := os.Getenv(key); value != "" {
        if intVal, err := strconv.Atoi(value); err == nil {
            return intVal
        }
    }
    return fallback
}
