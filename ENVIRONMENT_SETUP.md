# Environment Setup Guide

## Prerequisites
- Go 1.18+ installed
- PostgreSQL database
- Docker and Docker Compose (optional)

## Environment Configuration

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Update the `.env` file with your actual values:**
   - Database credentials
   - Email SMTP settings
   - Slack webhook URL
   - Server configuration

## Configuration Variables

### Database Configuration
- `DB_HOST`: Database hostname (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name (default: log_processing_db)
- `DATABASE_URL`: Complete database connection string (optional, will be constructed from above if not provided)

### Server Configuration
- `SERVER_HOST`: Server bind address (default: 0.0.0.0)
- `SERVER_PORT`: Server port (default: 8080)
- `INGESTION_API_URL`: Full URL for log ingestion API

### Email Configuration
- `SENDER_EMAIL`: Email address for sending alerts
- `RECEIVER_EMAIL`: Email address for receiving alerts
- `EMAIL_PASSWORD`: Password for sender email
- `SMTP_SERVER`: SMTP server hostname
- `SMTP_PORT`: SMTP server port (default: 587)

### Slack Configuration
- `SLACK_WEBHOOK_URL`: Slack webhook URL for sending alerts

### Analytics Configuration
- `ALERT_THRESHOLD`: Number of errors that trigger an alert (default: 5)
- `LOG_LEVEL`: Logging level (default: info)
- `LOG_FORMAT`: Log format (default: json)

## Running the Services

### With Docker Compose (Recommended)
```bash
docker-compose -f docker/docker-compose.yml up
```

### Manually

1. **Start the database** (ensure PostgreSQL is running and configured)

2. **Run database migrations:**
   ```bash
   psql -h localhost -U your_username -d log_processing_db -f database/migrations/001_create_logs_table.sql
   ```

3. **Start the Go log ingestion service:**
   ```bash
   cd services/log-ingestion
   go run main.go
   ```

4. **Start the Python analytics service:**
   ```bash
   cd services/analytics
   python main.py
   ```

## Testing Configuration

You can test if the configuration is loading correctly by running:
```bash
cd services/log-ingestion
go run test_config.go
```

This will display the loaded configuration values and verify the .env file is being read properly.
