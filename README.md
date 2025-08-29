# Log Processing System

## Overview
The Log Processing System is a microservices-based architecture designed for efficient log ingestion, storage, and analysis. It consists of two main services: a log ingestion microservice built with Go and an analytics module implemented in Python. The system uses PostgreSQL for log storage and Docker for service orchestration.

## Project Structure
```
log-processing-system
├── services
│   ├── log-ingestion        # Log ingestion microservice
│   └── analytics            # Analytics module for log analysis
├── scripts                  # Scripts for log parsing and setup
├── database                 # Database initialization and migrations
├── docker                   # Docker configuration for services
├── config                   # Configuration files
└── README.md                # Project documentation
```

## Services

### Log Ingestion
- **Language**: Go
- **Entry Point**: `services/log-ingestion/main.go`
- **Functionality**: Initializes the HTTP server and sets up routes for log ingestion. It processes incoming log data and stores it in the PostgreSQL database.

### Analytics
- **Language**: Python
- **Entry Point**: `services/analytics/main.py`
- **Functionality**: Analyzes logs for patterns and anomalies. It includes functions for error frequency analysis and alerting mechanisms.

## Database
- **Database**: PostgreSQL
- **Migrations**: SQL scripts for creating necessary tables and initializing the database.

## Scripts
- **Log Parsing**: `scripts/parse_logs.sh` - A Bash script to parse log files and send them to the log ingestion API.
- **Setup**: `scripts/setup.sh` - A Bash script for environment setup, including database initialization.

## Docker
- **Docker Compose**: `docker/docker-compose.yml` - Defines services, networks, and volumes for orchestration.
- **Dockerfiles**: Separate Dockerfiles for the log ingestion and analytics services.

## Configuration
- **Config File**: `config/config.yml` - Contains application configuration settings, including database connection details.

## Getting Started
1. Clone the repository.
2. Navigate to the project directory.
3. Run the setup script to initialize the database and services:
   ```bash
   ./scripts/setup.sh
   ```
4. Use Docker Compose to start the services:
   ```bash
   docker-compose up
   ```

## Usage
- Send logs to the log ingestion service via the defined API endpoints.
- Access the analytics module to analyze logs and receive alerts for detected anomalies.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License.