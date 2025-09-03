# Structured Logging Documentation

## Overview

This document describes the comprehensive structured logging implementation across the log processing system. The logging framework provides consistent, structured, and searchable logs across all services.

## Architecture

### Go Service Logging
- **Framework**: Custom structured logger with JSON output
- **Location**: `services/log-ingestion/logger/logger.go`
- **Features**:
  - JSON and text formatting
  - Context-aware logging
  - Performance monitoring
  - HTTP request logging
  - Database operation logging
  - Business event logging

### Python Service Logging
- **Framework**: Custom structured logger built on Python's logging module
- **Location**: `services/analytics/structured_logger.py`
- **Features**:
  - JSON and text formatting
  - Thread-local context
  - Performance decorators
  - Exception handling
  - Business event logging

## Configuration

### Environment Variables

```bash
# Log Level (DEBUG, INFO, WARN, ERROR, FATAL)
LOG_LEVEL=INFO

# Log Format (JSON, TEXT)
LOG_FORMAT=JSON

# Log Output (stdout, stderr, or file path)
LOG_OUTPUT=stdout

# Environment identifier
ENVIRONMENT=development

# Service-specific log levels
GO_LOG_LEVEL=INFO
PYTHON_LOG_LEVEL=INFO
```

### Log Levels

1. **DEBUG**: Detailed diagnostic information
2. **INFO**: General operational information
3. **WARN**: Warning conditions that should be addressed
4. **ERROR**: Error conditions that need attention
5. **FATAL**: Critical errors that cause service termination

## Log Format

### JSON Structure

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "HTTP request completed",
  "service": "log-ingestion",
  "component": "http",
  "file": "handlers.go",
  "line": 42,
  "function": "HandleLogIngestion",
  "trace_id": "abc123-def456",
  "request_id": "req-789",
  "user_id": "user-123",
  "duration_ms": 150,
  "fields": {
    "http_method": "POST",
    "http_path": "/logs",
    "http_status_code": 200,
    "response_size": 1024
  }
}
```

### Text Format

```
[2024-01-15 10:30:45] INFO [log-ingestion/http] handlers.go:42 HandleLogIngestion - HTTP request completed [trace=abc123-def456] [request=req-789] fields={"http_method":"POST","http_path":"/logs","http_status_code":200}
```

## Usage Examples

### Go Service

#### Basic Logging
```go
logger := logger.NewFromEnv("log-ingestion", "handlers")

logger.Info("Processing request")
logger.WithField("user_id", "123").Info("User authenticated")
logger.WithError(err).Error("Failed to process request")
```

#### Context Logging
```go
ctx := logger.WithRequestID(context.Background(), "req-123")
logger.InfoContext(ctx, "Request started")
```

#### Performance Logging
```go
start := time.Now()
// ... operation ...
duration := time.Since(start)
logger.LogHTTPRequest("POST", "/logs", userAgent, remoteAddr, 200, duration)
```

#### Business Events
```go
logger.LogBusinessEvent("user_login", "user-123", map[string]interface{}{
    "login_method": "oauth",
    "ip_address": "192.168.1.1",
})
```

### Python Service

#### Basic Logging
```python
from structured_logger import create_logger_from_env

logger = create_logger_from_env("analytics", "analyzer")

logger.info("Starting analysis")
logger.warning("High error rate detected", error_rate=0.15)
```

#### Context Logging
```python
with logger.with_fields(analysis_id="analysis-123"):
    logger.info("Analysis started")
    # All logs within this context will include analysis_id
```

#### Performance Monitoring
```python
@performance_monitor(logger, "data_analysis")
def analyze_data(data):
    # Function execution time will be automatically logged
    pass
```

#### Exception Handling
```python
@exception_handler(logger)
def risky_operation():
    # Exceptions will be automatically logged with full context
    pass
```

## Middleware and Interceptors

### Go HTTP Middleware

The logging middleware automatically captures:
- Request/response details
- Performance metrics
- Security events
- Rate limiting events
- Recovery from panics

```go
loggingMiddleware := middleware.NewLoggingMiddleware(logger)
router.Use(loggingMiddleware.Handler)
```

### Python Context Managers

```python
with log_context(operation="data_processing", batch_id="batch-123"):
    # All operations here will include the context
    process_data()
```

## Database Logging

### Go Database Operations
```go
start := time.Now()
result, err := db.Exec(query, params...)
duration := time.Since(start)

if err != nil {
    logger.LogDatabaseOperation("INSERT", "logs", duration, 0)
} else {
    rowsAffected, _ := result.RowsAffected()
    logger.LogDatabaseOperation("INSERT", "logs", duration, rowsAffected)
}
```

### Python Database Operations
```python
start = time.time()
cursor.execute(query, params)
duration = time.time() - start

logger.log_database_operation("SELECT", "logs", duration, cursor.rowcount)
```

## Monitoring and Alerting

### Key Metrics Logged

1. **Performance Metrics**
   - Request/response times
   - Database operation times
   - Function execution times

2. **Business Metrics**
   - User actions
   - System events
   - Error rates

3. **System Metrics**
   - Resource usage
   - Connection pool stats
   - Health check results

### Alert Triggers

- Error rate exceeding threshold
- Slow response times
- Database connection issues
- Authentication failures
- Rate limit violations

## Log Aggregation

### ELK Stack Integration

The JSON format is compatible with Elasticsearch, Logstash, and Kibana:

```json
{
  "@timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "service": "log-ingestion",
  "component": "http",
  "message": "Request processed",
  "fields": {
    "duration_ms": 150,
    "status_code": 200
  }
}
```

### Splunk Integration

Logs can be indexed in Splunk with custom fields:

```
index=app_logs source=log-ingestion component=http level=INFO
```

## Security Considerations

### Sensitive Data Handling

1. **Never Log**:
   - Passwords
   - API keys
   - Personal identification numbers
   - Credit card information

2. **Sanitize**:
   - User input
   - SQL queries
   - File paths

3. **Mask**:
   - Email addresses (partially)
   - IP addresses (if required)
   - User IDs (in production)

### Example Sanitization

```go
// Good
logger.WithField("email_domain", strings.Split(email, "@")[1]).Info("User registered")

// Bad
logger.WithField("email", email).Info("User registered")
```

## Troubleshooting

### Common Issues

1. **Missing Logs**
   - Check LOG_LEVEL environment variable
   - Verify logger initialization
   - Check output destination

2. **Performance Impact**
   - Use appropriate log levels
   - Avoid logging in tight loops
   - Consider async logging for high volume

3. **JSON Parsing Errors**
   - Ensure proper escaping
   - Validate JSON structure
   - Handle special characters

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
```

## Best Practices

1. **Consistent Structure**
   - Use standard field names
   - Follow naming conventions
   - Include relevant context

2. **Meaningful Messages**
   - Be descriptive but concise
   - Include action being performed
   - Provide enough context

3. **Performance Conscious**
   - Log appropriately for environment
   - Use structured fields instead of string interpolation
   - Defer expensive operations

4. **Security Aware**
   - Never log sensitive information
   - Sanitize user input
   - Consider data retention policies

## Deployment Considerations

### Development Environment
- LOG_LEVEL=DEBUG
- LOG_FORMAT=TEXT (for readability)
- LOG_OUTPUT=stdout

### Production Environment
- LOG_LEVEL=INFO
- LOG_FORMAT=JSON (for parsing)
- LOG_OUTPUT=stdout (for container logs)

### Log Rotation

For file-based logging, implement log rotation:

```bash
# Example logrotate configuration
/var/log/app/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 0644 app app
}
```

## Integration Examples

### Docker Logging Driver

```yaml
services:
  log-ingestion:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"
```

### Kubernetes Integration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: logging-config
data:
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "JSON"
  LOG_OUTPUT: "stdout"
```

## Future Enhancements

1. **Distributed Tracing**
   - OpenTelemetry integration
   - Jaeger/Zipkin support
   - Cross-service correlation

2. **Metrics Integration**
   - Prometheus metrics
   - Custom metric extraction
   - Alert manager integration

3. **Enhanced Security**
   - Log signing/verification
   - Encrypted log transport
   - Audit trail compliance

This documentation provides a comprehensive guide to the structured logging implementation in the log processing system. Regular updates should be made as the system evolves.
