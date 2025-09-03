# Test Configuration for Log Processing System

## Overview
This directory contains comprehensive testing infrastructure for the log processing system, including unit tests, integration tests, performance benchmarks, and test runner scripts.

## Test Structure

### Go Tests (`services/log-ingestion/`)
- **logger_test.go** - Unit tests for structured logging framework
- **logging_test.go** - Middleware tests for HTTP logging and security
- **ingestion_test.go** - Integration tests for log ingestion handlers

### Python Tests (`services/analytics/`)
- **test_structured_logger.py** - Unit tests for Python structured logging
- **test_integration.py** - Integration tests for analytics pipeline

### System Tests
- **test_logging.py** - Comprehensive logging functionality tests
- **run_tests.py** - Python-based comprehensive test runner
- **run_tests.sh** - Bash script for Unix/Linux systems
- **run_tests.bat** - Batch script for Windows systems

## Running Tests

### Quick Start
```bash
# Unix/Linux/macOS
./run_tests.sh

# Windows
run_tests.bat

# Cross-platform Python runner
python run_tests.py
```

### Individual Test Suites

#### Go Tests
```bash
cd services/log-ingestion

# Run all tests with coverage
go test -v -cover ./...

# Run specific package tests
go test -v -cover ./logger
go test -v -cover ./middleware
go test -v -cover ./handlers

# Run benchmarks
go test -bench=. -benchmem ./...
```

#### Python Tests
```bash
cd services/analytics

# Run unit tests
python test_structured_logger.py

# Run integration tests
python test_integration.py

# Run with coverage
coverage run --source=. -m unittest discover
coverage report
coverage html
```

## Test Categories

### Unit Tests
- **Logger Tests** - Structured logging functionality
- **Formatter Tests** - Log format validation
- **Configuration Tests** - Environment and config loading
- **Utility Tests** - Helper function validation

### Integration Tests
- **HTTP Handler Tests** - End-to-end request handling
- **Database Tests** - PostgreSQL integration
- **Analytics Pipeline Tests** - Complete data flow
- **Service Communication Tests** - Inter-service messaging

### Performance Tests
- **Logging Benchmarks** - Log throughput and latency
- **Handler Benchmarks** - HTTP request processing speed
- **Database Benchmarks** - Query performance
- **Memory Usage Tests** - Resource consumption analysis

### Security Tests
- **Input Validation** - Malformed data handling
- **Authentication Tests** - Security middleware validation
- **Rate Limiting Tests** - DDoS protection verification
- **SQL Injection Prevention** - Database security

## Test Coverage Requirements

### Minimum Coverage Targets
- **Go Services**: 85% line coverage
- **Python Services**: 80% line coverage
- **Critical Paths**: 95% coverage (authentication, data processing)
- **Error Handling**: 90% coverage

### Coverage Reports
- **Go**: `test-reports/go_combined_coverage.html`
- **Python**: `test-reports/python_coverage_html/index.html`
- **Summary**: `test-reports/test_summary.txt`

## Test Data and Fixtures

### Sample Log Entries
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "test-service",
  "message": "Test log entry",
  "metadata": {
    "user_id": "test-user-123",
    "request_id": "req-456",
    "ip_address": "192.168.1.1"
  }
}
```

### Database Test Data
- **Test Users**: Predefined user accounts for testing
- **Sample Logs**: Various log formats and edge cases
- **Performance Data**: Large datasets for load testing

## Continuous Integration

### GitHub Actions Integration
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Go
        uses: actions/setup-go@v3
        with:
          go-version: 1.21
      - name: Setup Python
        uses: actions/setup-python@v3
        with:
          python-version: 3.11
      - name: Run Tests
        run: ./run_tests.sh
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Manual run
pre-commit run --all-files
```

## Environment Setup for Testing

### Required Environment Variables
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=log_processing_test
DB_USER=test_user
DB_PASSWORD=test_password

# Services
LOG_INGESTION_PORT=8080
ANALYTICS_PORT=8081

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=json
```

### Docker Test Environment
```bash
# Start test environment
docker-compose -f docker/docker-compose.test.yml up -d

# Run tests against Docker environment
DOCKER_TEST=true ./run_tests.sh

# Cleanup
docker-compose -f docker/docker-compose.test.yml down -v
```

## Test Debugging

### Common Issues and Solutions

#### Go Tests Failing
```bash
# Check Go module dependencies
go mod tidy
go mod verify

# Run with verbose output
go test -v -cover ./... -args -test.v

# Check for race conditions
go test -race ./...
```

#### Python Tests Failing
```bash
# Check dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run with verbose output
python -m unittest discover -v

# Debug specific test
python -m unittest test_module.TestClass.test_method -v
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432

# Test connection
psql -h localhost -p 5432 -U test_user -d log_processing_test

# Reset test database
dropdb log_processing_test
createdb log_processing_test
psql -d log_processing_test -f database/init.sql
```

## Performance Benchmarking

### Go Benchmarks
```bash
# Run all benchmarks
go test -bench=. -benchmem ./...

# Run specific benchmarks
go test -bench=BenchmarkLogger -benchmem ./logger

# Generate CPU profile
go test -bench=. -cpuprofile=cpu.prof ./...
go tool pprof cpu.prof
```

### Python Performance Tests
```bash
# Run performance tests
python -m pytest tests/performance/ -v

# Memory profiling
python -m memory_profiler test_integration.py

# Line profiling
kernprof -l -v test_integration.py
```

## Test Maintenance

### Regular Tasks
1. **Update test data** - Keep fixtures current with schema changes
2. **Review coverage** - Ensure new code has adequate test coverage
3. **Performance monitoring** - Track benchmark trends over time
4. **Dependency updates** - Keep test dependencies current

### Best Practices
- **Test Independence** - Each test should be able to run in isolation
- **Clear Naming** - Test names should describe what they verify
- **Minimal Setup** - Use minimal data needed for each test
- **Fast Execution** - Keep unit tests under 1 second each
- **Reliable Results** - Tests should be deterministic and stable

## Reporting and Metrics

### Test Reports Location
- **Coverage Reports**: `test-reports/`
- **Performance Results**: `test-reports/benchmarks/`
- **Test Logs**: `test-reports/logs/`
- **Summary**: `test-reports/test_summary.txt`

### Metrics Tracked
- **Test Execution Time** - Track performance trends
- **Coverage Percentage** - Ensure adequate coverage
- **Failure Rate** - Monitor test stability
- **Performance Benchmarks** - Track application performance

This comprehensive testing infrastructure ensures the reliability, performance, and maintainability of the log processing system across all components and environments.
